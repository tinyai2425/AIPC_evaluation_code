#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import json
import sys
from pathlib import Path

class ConfigError(RuntimeError):
    pass

def load_json(path: Path):
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        raise ConfigError(f"文件不存在：{path}")
    except json.JSONDecodeError as e:
        raise ConfigError(f"JSON 解析失败：{path}\n{e}")

def save_json(path: Path, data):
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    tmp.replace(path)

def find_api_config(dir_path: Path):
    api_path = dir_path / "api_config.json"
    if not api_path.is_file():
        raise ConfigError(f"未找到 api_config.json：{api_path}")
    return api_path

def verify_modelpath_omc(dir_path: Path, api_cfg):
    model_path = api_cfg.get("modelPath")
    if not isinstance(model_path, str) or not model_path.strip():
        raise ConfigError("api_config.json 中缺少或非法的字段：modelPath")
    omc_path = dir_path / model_path
    if not omc_path.is_file():
        raise ConfigError(f"modelPath 指向的 .omc 文件不存在：{omc_path}")
    if omc_path.suffix.lower() != ".omc":
        raise ConfigError(f"modelPath 不是 .omc 文件：{omc_path.name}")
    return omc_path.name

def get_required_int(d, key):
    if key not in d:
        raise ConfigError(f"缺少必要字段：{key}")
    try:
        return int(d[key])
    except Exception:
        raise ConfigError(f"字段 {key} 不是整数：{d[key]}")

def load_model_side_json(dir_path: Path, omc_filename: str):
    stem = Path(omc_filename).stem
    model_json_path = dir_path / f"{stem}.json"
    if not model_json_path.is_file():
        raise ConfigError(f"未找到与 OMC 同名的 JSON：{model_json_path}")
    return load_json(model_json_path)

def verify_constraints(api_cfg, model_json):
    init_token_len = get_required_int(api_cfg, "initTokenLen")
    if init_token_len != 2048:
        raise ConfigError(f"api_config.json 校验失败：initTokenLen={init_token_len}，要求 2048")

    kv_cache_max_len = get_required_int(model_json, "kv_cache_max_len")
    if kv_cache_max_len != 4096:
        raise ConfigError(f"模型 JSON 校验失败：kv_cache_max_len={kv_cache_max_len}，要求 4096")

    max_io_tokens = get_required_int(model_json, "max_io_tokens")
    if max_io_tokens != 32768:
        raise ConfigError(f"模型 JSON 校验失败：max_io_tokens={max_io_tokens}，要求 32768")

def get_optional_int(d, key):
    if key not in d:
        return None
    try:
        return int(d[key])
    except Exception:
        raise ConfigError(f"字段 {key} 不是整数：{d[key]}")

def extract_params(model_json):
    hidden_size = get_required_int(model_json, "hidden_size")
    intermediate_size = get_required_int(model_json, "intermediate_size")
    num_attention_heads = get_required_int(model_json, "num_attention_heads")
    num_hidden_layers = get_required_int(model_json, "num_hidden_layers")

    head_dim = get_optional_int(model_json, "head_dim")
    if head_dim is None:
        head_dim = get_optional_int(model_json, "num_attention_head_dims")
    if head_dim is None:
        if hidden_size % num_attention_heads != 0:
            raise ConfigError("无法推断 head_dim：缺少 head_dim/num_attention_head_dims 且 hidden_size 不能被 num_attention_heads 整除。")
        head_dim = hidden_size // num_attention_heads

    num_kv_heads = get_optional_int(model_json, "num_key_value_heads")
    if num_kv_heads is None:
        num_kv_heads = get_optional_int(model_json, "num_attention_kv_heads")
    if num_kv_heads is None:
        raise ConfigError("缺少 num_key_value_heads/num_attention_kv_heads。")

    return {
        "hidden_size": hidden_size,
        "intermediate_size": intermediate_size,
        "num_attention_heads": num_attention_heads,
        "num_hidden_layers": num_hidden_layers,
        "head_dim": head_dim,
        "num_key_value_heads": num_kv_heads,
    }

def compute_lora_size(p, rank):
    eff_rank = 16 if int(rank) == 8 else int(rank)
    base = (
        p["hidden_size"] * 4
        + p["head_dim"] * p["num_attention_heads"] * 5
        + p["head_dim"] * p["num_key_value_heads"] * 2
        + p["intermediate_size"] * 3
    )
    return int(base * p["num_hidden_layers"] * eff_rank * 2)

def update_lora_ranks(api_cfg, params):
    ranks = api_cfg.get("lora_rank")
    if not isinstance(ranks, list) or not ranks:
        raise ConfigError("api_config.json 中缺少 lora_rank 数组或内容为空。")
    for item in ranks:
        if not isinstance(item, dict) or "rank" not in item:
            raise ConfigError(f"lora_rank 项非法：{item}")
        try:
            r = int(item["rank"])
        except Exception:
            raise ConfigError(f"lora_rank 中的 rank 非法：{item.get('rank')}")
        if r <= 0:
            raise ConfigError(f"lora_rank 中的 rank 必须为正整数：{r}")
        item["size"] = compute_lora_size(params, r)

def main():
    parser = argparse.ArgumentParser(description="计算并写回 LoRA size 到 api_config.json。")
    parser.add_argument("dir", help="包含 api_config.json / *.omc / 同名模型JSON 的目录，例如 ./qwen25_4K")
    args = parser.parse_args()

    dir_path = Path(args.dir).resolve()
    if not dir_path.is_dir():
        print(f"目标不是有效目录：{dir_path}", file=sys.stderr)
        sys.exit(2)

    try:
        api_path = find_api_config(dir_path)
        api_cfg = load_json(api_path)
        omc_filename = verify_modelpath_omc(dir_path, api_cfg)
        model_json = load_model_side_json(dir_path, omc_filename)

        # 新增三项硬校验
        verify_constraints(api_cfg, model_json)

        params = extract_params(model_json)
        update_lora_ranks(api_cfg, params)
        save_json(api_path, api_cfg)

        print(f"[OK] 已更新：{api_path}")
        print(f"     使用模型：{omc_filename}")
        print("     已写回 lora_rank[*].size。")

    except ConfigError as e:
        print(f"[错误] {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"[异常] 未预期的错误：{e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()

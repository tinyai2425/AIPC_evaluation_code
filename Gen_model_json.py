#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import hashlib
import re
import json
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse

sys.path.append(os.path.abspath("Function"))
import download_link_scraper  # 修改为新的模块名
import mod_time


class ConfigError(RuntimeError):
    pass


SAFE_NAME_RE = re.compile(r"[A-Za-z0-9_\-]+$")


def sha256_file(path: Path) -> str:
    if not path.exists():
        raise ConfigError(f"本地模型文件不存在：{path}")
    if not path.is_file():
        raise ConfigError(f"本地模型路径不是文件：{path}")
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def extract_filename_from_url(url: str) -> str:
    try:
        p = urlparse(url)
    except Exception as e:
        raise ConfigError(f"无法解析 model_cloud_path URL：{url}（{e}）")
    if p.scheme not in ("http", "https"):
        raise ConfigError(f"model_cloud_path 必须是 http/https 链接：{url}")
    filename = Path(p.path).name
    if not filename:
        raise ConfigError(f"无法从链接中解析文件名：{url}")
    return filename


def name_variants(name: str) -> set:
    """
    生成允许的 'B 尺寸等价' 变体：
      - 15B <-> 1.5B
      - 70B <-> 7.0B
    规则：如果匹配到 [整数或一位小数]+B，则提供点前后一位移动的一对等价形式。
    仅对最后一个 '...B' 片段生效（常见命名中通常只有一个）。
    """
    variants = {name}
    # 找最后一个以 B 结尾的数值片段
    m_iter = list(re.finditer(r"(\d+(?:\.\d+)?)B", name))
    if not m_iter:
        return variants
    m = m_iter[-1]
    num = m.group(1)
    start, end = m.span(1)  # 只替换数字部分

    def replace_num(new_num: str) -> str:
        return name[:start] + new_num + name[end:]

    if "." in num:
        # 1.5 -> 15（仅当小数位为1位时更有意义）
        int_part, frac = num.split(".", 1)
        if len(frac) == 1:
            collapsed = int_part + frac  # 1.5 -> 15
            variants.add(replace_num(collapsed))
    else:
        # 15 -> 1.5（仅对长度>=2时做一位小数）
        if len(num) >= 2:
            dotted = num[:-1] + "." + num[-1]
            variants.add(replace_num(dotted))
        # 7 -> 7.0（也加入一个 7.0 形式，覆盖 70B <-> 7.0B 的互通）
        if len(num) == 1:
            dotted0 = num + ".0"
            variants.add(replace_num(dotted0))

    return variants


def validate_model_paths(model_info: dict):
    """
    1) 校验 model_name 合法字符
    2) 校验本地/云端 zip 文件名完全一致
    3) 文件名与 model_name 的基本匹配（以 '{model_name}-' 开头；若 omc 则包含 '-OMC-'）
    4) 目录匹配：允许 '15B' 与 '1.5B'（及 '7B' 与 '7.0B'）等价，
       只要本地父目录或云端 URL 路径段中，'等于' model_name 的任一变体即可。
    """
    required_keys = [
        "model_name", "model_local_path", "model_cloud_path",
        "model_format"
    ]
    for k in required_keys:
        if k not in model_info or not str(model_info[k]).strip():
            raise ConfigError(f"缺少必要字段或为空：{k}")

    model_name = str(model_info["model_name"]).strip()
    local_path = Path(model_info["model_local_path"]).expanduser()
    cloud_url = str(model_info["model_cloud_path"]).strip()
    model_format = str(model_info["model_format"]).strip().lower()

    # 1) model_name 字符检查
    if not SAFE_NAME_RE.fullmatch(model_name):
        raise ConfigError(f"非法的 model_name: {model_name}（只允许字母、数字、-、_）")

    # 2) 文件名一致
    local_filename = local_path.name
    cloud_filename = extract_filename_from_url(cloud_url)
    if local_filename != cloud_filename:
        raise ConfigError(
            f"本地与云端文件名不一致：\n"
            f"  local : {local_filename}\n"
            f"  cloud : {cloud_filename}\n"
            f"要求二者完全一致（例如：Qwen25-7B-Instruct-OMC-20251024.zip）"
        )
    if not local_filename.lower().endswith(".zip"):
        raise ConfigError(f"模型归档必须为 .zip 文件，当前：{local_filename}")

    # 3) 文件名与 model_name 的基本匹配（强约束）
    if not local_filename.startswith(f"{model_name}-"):
        raise ConfigError(
            f"文件名与 model_name 不匹配：\n"
            f"  model_name: {model_name}\n"
            f"  filename  : {local_filename}\n"
            f"要求文件名以 '{model_name}-' 开头"
        )
    if model_format == "omc" and "-OMC-" not in local_filename.upper():
        raise ConfigError(
            f"model_format=omc 时，文件名需包含 '-OMC-' 片段：{local_filename}"
        )

    # 4) 目录匹配（宽松变体匹配）
    #   允许 15B <-> 1.5B, 7B <-> 7.0B 等价形式
    acceptable_names = name_variants(model_name)

    parents_names = {p.name for p in local_path.parents}  # 本地父目录集合
    local_ok = any(cand in parents_names for cand in acceptable_names)

    cloud_parts = [part for part in Path(urlparse(cloud_url).path).parts if part not in ("/", "")]
    cloud_ok = any(cand in cloud_parts for cand in acceptable_names)

    if not local_ok:
        raise ConfigError(
            "本地路径父目录中未发现等于以下任一允许名称的目录：\n"
            f"  允许名称集合：{sorted(acceptable_names)}\n"
            f"  本地路径     ：{local_path}"
        )
    if not cloud_ok:
        raise ConfigError(
            "云端链接路径中未发现等于以下任一允许名称的目录段：\n"
            f"  允许名称集合：{sorted(acceptable_names)}\n"
            f"  云端链接     ：{cloud_url}"
        )

    if not local_path.exists():
        raise ConfigError(f"本地模型文件不存在：{local_path}")

    return local_path, cloud_filename


def process_model_info(model_info):
    # 先做路径与命名检查
    local_path, filename = validate_model_paths(model_info)

    # 仅获取下载链接
    model_page_link = model_info["model_cloud_path"]
    download_link = download_link_scraper.get_download_link(model_page_link)
    if not download_link:
        raise ConfigError("获取下载直链失败：请检查 model_cloud_path 源页面是否可访问/结构是否变化")

    # 计算本地文件的SHA256
    file_digest = sha256_file(local_path)
    print("Finish hash value compute")

    model_name = model_info["model_name"]
    file_size = os.path.getsize(local_path)
    modified_time = mod_time.get_iso8601_time_with_ns()

    model_json = {
        "name": model_name,
        "model_version": model_info.get("model_version", ""),
        "ddk_version": model_info.get("ddk_version", ""),
        "download": download_link,
        "modified_at": modified_time,
        "owned_by": model_info.get("owner", ""),
        "size": file_size,
        "digest": file_digest,
        "details": {
            "format": model_info.get("model_format", ""),
            "family": model_info.get("family", ""),
            "families": model_info.get("families", []),
            "parameter_size": model_info.get("parameter_size", ""),
            "quantization_level": model_info.get("quantization_level", "")
        }
    }

    output_dir = "model_json_out"
    os.makedirs(output_dir, exist_ok=True)

    today = datetime.now().strftime("%Y%m%d")
    input_filename = Path(sys.argv[1]).stem
    if not input_filename.endswith("-in"):
        raise ConfigError(f"输入文件名必须以 '-in' 结尾，但收到：{input_filename}")
    base_name = input_filename[:-3]

    output_base = f"{base_name}-{today}"
    output_filename = f"{output_base}.json"
    counter = 0
    while os.path.exists(os.path.join(output_dir, output_filename)):
        counter += 1
        output_filename = f"{output_base}_{counter}.json"

    output_path = os.path.join(output_dir, output_filename)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(model_json, f, indent=4, ensure_ascii=False)

    print(f"Successfully saved to: {output_path}")


def main():
    if len(sys.argv) != 2:
        print("Usage: python gen_model_json.py file-in.json")
        sys.exit(1)

    input_file = sys.argv[1]
    if not input_file.endswith(".json"):
        print("Error: Input file must be a JSON file")
        sys.exit(1)

    try:
        with open(input_file, "r", encoding="utf-8") as f:
            model_info = json.load(f)
        process_model_info(model_info)
    except FileNotFoundError:
        print(f"Error: File '{input_file}' not found")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON format in '{input_file}'")
        sys.exit(1)
    except ConfigError as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

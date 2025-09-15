#!/usr/bin/env bash
# zip_model.sh
# 用法: ./zip_model.sh <dir_to_zip>
# 例子: ./zip_model.sh ../../Share/qwen25_4K

set -euo pipefail

# --- 帮助与参数检查 ---
if [[ $# -lt 1 ]]; then
  echo "用法: $0 <dir_to_zip>"
  exit 1
fi

INPUT_DIR="$1"

# 允许相对路径，需确保存在且为目录
if [[ ! -d "$INPUT_DIR" ]]; then
  echo "错误: 目录不存在: $INPUT_DIR"
  exit 2
fi

# 规范化目录末尾的斜杠（去掉）
INPUT_DIR="${INPUT_DIR%/}"

BASENAME="$(basename "$INPUT_DIR")"
PARENT_DIR="$(cd "$(dirname "$INPUT_DIR")" && pwd)"
TARGET_ZIP="$PARENT_DIR/$BASENAME.zip"

# --- 关键文件检查（在目录顶层） ---
REQUIRED_FILES=( "tokenizer.json" "api_config.json" )
for f in "${REQUIRED_FILES[@]}"; do
  if [[ ! -f "$INPUT_DIR/$f" ]]; then
    echo "错误: 缺少关键文件: $f （应位于 $INPUT_DIR/ 下）"
    exit 3
  else
    echo "检测到关键文件: $f"
  fi
done

# --- 检查 zip 命令 ---
if ! command -v zip >/dev/null 2>&1; then
  echo "错误: 系统未找到 'zip' 命令。"
  echo "请先安装 zip（例如：在 WSL 里用 sudo apt install zip）。"
  exit 4
fi

# --- 如果同名 zip 已存在则报错退出 ---
if [[ -f "$TARGET_ZIP" ]]; then
  echo "错误: 已存在同名文件 $TARGET_ZIP ，请先删除或改名再运行。"
  exit 5
fi

# --- 打包 ---
echo "正在打包: $INPUT_DIR -> $TARGET_ZIP"
(
  cd "$INPUT_DIR"
  zip -r -9 -q "../$BASENAME.zip" .
)

# --- 校验结果 ---
if [[ -f "$TARGET_ZIP" ]]; then
  echo "完成: $TARGET_ZIP"
  exit 0
else
  echo "失败: 未生成 $TARGET_ZIP"
  exit 6
fi

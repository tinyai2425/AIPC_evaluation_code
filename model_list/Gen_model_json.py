import sys
import os
import hashlib
import re
import json
from pathlib import Path
from datetime import datetime

sys.path.append(os.path.abspath("Function"))
import sha256_scraper
import mod_time

def process_model_info(model_info):
    download_link = model_info["model_cloud_path"]
    SHA256_compute = hashlib.sha256(open(model_info["model_local_path"], "rb").read()).hexdigest() 
    print("Finish hash value compute")
    SHA256_cloud_fetch = sha256_scraper.get_sha256(download_link)
    
    if SHA256_compute == SHA256_cloud_fetch:
        print("Hash value match")
        file_Digest = SHA256_compute
    else: 
        print("Error: Hash value do not match!")
        sys.exit(1)

    MODEL_NAME = model_info["model_name"]
    file_size = os.path.getsize(model_info["model_local_path"])
    modified_time = mod_time.get_iso8601_time_with_ns()

    if not re.fullmatch(r"[A-Za-z0-9_\-]+", MODEL_NAME):
        raise ValueError(f"非法的 MODEL_NAME: {MODEL_NAME}，只能包含字母、数字、- 和 _")
        
    model_json = {
        "name": MODEL_NAME,
        "model_version": model_info["model_version"],
        "ddk_version": model_info["ddk_version"],
        "download": download_link,
        "modified_at": modified_time,
        "owned_by": model_info["owner"],
        "size": file_size,
        "digest": file_Digest,
        "details": {
            "format": model_info["model_format"],
            "family": model_info["family"],
            "families": model_info["families"],
            "parameter_size": model_info["parameter_size"],
            "quantization_level": model_info["quantization_level"]
        }
    }

    output_dir = "model_json_out"
    os.makedirs(output_dir, exist_ok=True)

    # 获取当前日期（格式为YYYYMMDD）
    today = datetime.now().strftime("%Y%m%d")  # 修改这里
    
    # 处理输入文件名
    input_filename = Path(sys.argv[1]).stem
    if not input_filename.endswith("-in"):
        print(f"Error: Input filename must end with '-in', but got '{input_filename}'")
        sys.exit(1)
    base_name = input_filename[:-3]  # 去掉最后的-in
    
    # 构造输出文件名
    output_base = f"{base_name}-{today}"  # 这里会自动使用新格式的日期
    output_filename = f"{output_base}.json"
    counter = 0
    
    # 检查文件是否存在并确定最终文件名
    while os.path.exists(os.path.join(output_dir, output_filename)):
        counter += 1
        output_filename = f"{output_base}_{counter}.json"
    
    output_path = os.path.join(output_dir, output_filename)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(model_json, f, indent=4, ensure_ascii=False)

    print(f"Successfully saved to: {output_path}")

if __name__ == "__main__":
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
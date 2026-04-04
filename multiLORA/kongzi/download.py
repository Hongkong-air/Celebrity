# download_model.py
"""
下载Qwen2.5-3B-Instruct模型到本地（适合4090 GPU，约6GB显存）
运行方式：python download_model.py
"""

import os
from transformers import AutoModelForCausalLM, AutoTokenizer

def download_model():
    # 使用3B模型以节省显存（4090 GPU有24GB显存，3B模型约6GB）
    model_name = "Qwen/Qwen2.5-3B-Instruct"
    # 其他可选模型：
    # model_name = "Qwen/Qwen2.5-1.5B-Instruct"  # 约3GB显存
    
    save_path = "./models/qwen2.5-3b-instruct"
    
    print(f"正在下载模型: {model_name}")
    print(f"保存路径: {save_path}")
    
    # 下载tokenizer
    print("1/2 下载tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(
        model_name,
        trust_remote_code=True,
        cache_dir=save_path
    )
    
    # 下载模型（使用4bit量化减少显存占用）
    print("2/2 下载模型（4bit量化版本）...")
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype="auto",
        device_map="auto",
        trust_remote_code=True,
        load_in_4bit=True,  # 4bit量化，显存占用约3-4GB
        cache_dir=save_path
    )
    
    # 保存到本地
    print(f"保存模型到 {save_path}...")
    model.save_pretrained(save_path)
    tokenizer.save_pretrained(save_path)
    
    print("✅ 模型下载完成！")
    print(f"模型位置: {os.path.abspath(save_path)}")

if __name__ == "__main__":
    download_model()
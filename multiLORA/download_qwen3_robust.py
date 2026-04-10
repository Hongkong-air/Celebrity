#!/usr/bin/env python3
"""
Robust Qwen3-4B-RPG-Roleplay-V2 模型下载脚本 with retry logic
"""

import os
import time
import argparse
from huggingface_hub import snapshot_download
from pathlib import Path

def download_with_retry(model_repo, local_dir, max_retries=3, retry_delay=5):
    """Download model with retry logic"""
    print(f"正在从Hugging Face下载模型: {model_repo}")
    print(f"本地保存路径: {local_dir}")
    
    # Create directory if it doesn't exist
    os.makedirs(local_dir, exist_ok=True)
    
    for attempt in range(max_retries):
        try:
            print(f"尝试下载 (第 {attempt + 1} 次)...")
            snapshot_download(
                repo_id=model_repo,
                local_dir=local_dir,
                resume_download=True,
                token=None  # Use anonymous access first
            )
            print("✅ 模型下载完成！")
            return True
            
        except Exception as e:
            print(f"❌ 下载失败 (第 {attempt + 1} 次): {e}")
            if attempt < max_retries - 1:
                print(f"等待 {retry_delay} 秒后重试...")
                time.sleep(retry_delay)
            else:
                print("❌ 所有重试都失败了")
                return False

def check_existing_files(local_dir):
    """Check if model files already exist"""
    local_path = Path(local_dir)
    if local_path.exists():
        files = list(local_path.glob("*"))
        if files:
            print(f"📁 目录已存在 {len(files)} 个文件:")
            for file in sorted(files)[:10]:
                print(f"  - {file.name}")
            if len(files) > 10:
                print(f"  ... 还有 {len(files) - 10} 个文件")
            return True
    return False

def main():
    parser = argparse.ArgumentParser(description="下载Qwen3-4B-RPG-Roleplay-V2模型 (带重试)")
    parser.add_argument("--repo", type=str, 
                       default="Hongkong-air/Qwen3-4B-RPG-Roleplay-V2",
                       help="模型仓库ID")
    parser.add_argument("--local_dir", type=str, 
                       default="./models/Qwen3-4B-RPG-Roleplay-V2",
                       help="本地保存目录")
    parser.add_argument("--max_retries", type=int, default=3,
                       help="最大重试次数")
    parser.add_argument("--retry_delay", type=int, default=10,
                       help="重试间隔秒数")
    
    args = parser.parse_args()
    
    # Check if files already exist
    if check_existing_files(args.local_dir):
        response = input("目录已存在文件，是否继续下载覆盖? (y/N): ")
        if response.lower() != 'y':
            print("取消下载")
            return
    
    # Attempt download
    success = download_with_retry(
        args.repo, 
        args.local_dir, 
        args.max_retries, 
        args.retry_delay
    )
    
    if success:
        # Verify download
        required_files = ['config.json', 'generation_config.json']
        local_path = Path(args.local_dir)
        if local_path.exists():
            files = list(local_path.glob("*"))
            config_found = any(f.name == 'config.json' for f in files)
            weights_found = any(f.suffix in ['.safetensors', '.bin'] for f in files)
            
            if config_found and weights_found:
                print("✅ 模型验证成功: 找到配置文件和权重文件")
            else:
                print("⚠️  模型可能不完整: 缺少关键文件")
    else:
        print("❌ 下载失败，请检查网络连接或尝试其他下载方式")
        print("\n替代方案:")
        print("1. 手动从 https://huggingface.co/Hongkong-air/Qwen3-4B-RPG-Roleplay-V2 下载")
        print("2. 使用 ModelScope: pip install modelscope")
        print("3. 检查网络代理设置")

if __name__ == "__main__":
    main()
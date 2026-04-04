#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Lightweight transfer script to convert 孔子家语论语.txt to JSONL format for LoRA training.
This version doesn't require loading large models, making it suitable for CPU-only environments.
"""

import json
import os
import re
from typing import List, Dict


def clean_text(text: str) -> str:
    """Clean and normalize text."""
    # Remove extra whitespace and normalize
    text = re.sub(r'\s+', ' ', text.strip())
    return text if text else ""


def parse_confucius_text(file_path: str) -> List[str]:
    """
    Parse the Confucius text file and extract individual quotes/teachings.
    Each non-empty line is treated as a separate teaching.
    """
    teachings = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except UnicodeDecodeError:
        # Try GBK encoding if UTF-8 fails
        with open(file_path, 'r', encoding='gbk') as f:
            lines = f.readlines()
    
    for line in lines:
        cleaned = clean_text(line)
        if cleaned and len(cleaned) > 10:  # Only keep meaningful lines
            teachings.append(cleaned)
    
    return teachings


def create_jsonl_dataset(teachings: List[str], output_path: str):
    """
    Create JSONL dataset in the format expected by LoRA training scripts.
    Format: {"messages": [{"role": "system", ...}, {"role": "user", ...}, {"role": "assistant", ...}]}
    """
    system_prompt = "你是孔子，名丘，字仲尼，春秋鲁国人。温和严谨，循循善诱，常引用《诗》《书》。"
    
    with open(output_path, 'w', encoding='utf-8') as f:
        for teaching in teachings:
            # Create a simple Q&A format
            # User asks a general question, assistant responds with the teaching
            entry = {
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": "夫子，请教我为人处世之道。"},
                    {"role": "assistant", "content": teaching}
                ]
            }
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')


def main():
    input_file = "/root/autodl-tmp/.autodl/multiLORA/kongzi/孔子家语论语.txt"
    output_file = "/root/autodl-tmp/.autodl/multiLORA/kongzi/output/kongzi_dataset.jsonl"
    
    if not os.path.exists(input_file):
        print(f"错误: 输入文件 '{input_file}' 不存在!")
        return
    
    print(f"正在处理文件: {input_file}")
    
    # Parse the text file
    teachings = parse_confucius_text(input_file)
    print(f"提取到 {len(teachings)} 条孔子语录")
    
    if len(teachings) == 0:
        print("警告: 没有提取到有效的语录!")
        return
    
    # Create JSONL dataset
    create_jsonl_dataset(teachings, output_file)
    print(f"成功创建数据集: {output_file}")
    
    # Validate against project requirements
    if len(teachings) >= 800:
        print("✓ 符合孔子语录样本要求 (≥800 条)")
    elif len(teachings) >= 500:
        print("⚠ 样本数量充足 (≥500) 但未达到孔子最优目标 (800条)")
    else:
        print("⚠ 样本数量不足! LoRA训练建议至少500-800条样本")
    
    # Show example
    print("\n示例数据:")
    if teachings:
        example = {
            "messages": [
                {"role": "system", "content": "你是孔子，名丘，字仲尼，春秋鲁国人。温和严谨，循循善诱，常引用《诗》《书》。"},
                {"role": "user", "content": "夫子，请教我为人处世之道。"},
                {"role": "assistant", "content": teachings[0]}
            ]
        }
        print(json.dumps(example, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
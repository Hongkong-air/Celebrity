#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
李白数字人数据集生成测试脚本 - 只处理第一个窗口用于调试
"""

import sys
import os
sys.path.append('/root/autodl-tmp')

from generate_lora_dataset import LiBaiDatasetGenerator

def test_single_window():
    """测试单个窗口的处理"""
    print("测试李白数字人数据集生成（仅第一个窗口）...")
    
    # 创建生成器
    generator = LiBaiDatasetGenerator(
        model_path='/root/autodl-tmp/models/qwen/Qwen2___5-7B-Instruct',
        device='cuda'
    )
    
    # 读取第一个markdown文件
    md_file = '/root/autodl-tmp/.autodl/multiLORA/Libai/MinerU_markdown_李白传（文学性、严谨性兼具的李白传记；内涵李白传世书法真迹高清插图）_(安旗)_(z-library.sk,_1lib.sk,_z-lib.sk)_2039902407647023104.md'
    
    with open(md_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print(f"读取文件: {os.path.basename(md_file)} ({len(content)} 字符)")
    
    # 创建滑动窗口
    windows = generator.create_sliding_windows(content, window_size=300, slide_step=200)
    print(f"创建了 {len(windows)} 个滑动窗口")
    
    if windows:
        # 只处理第一个窗口
        window_lines = windows[0]
        window_content = '\n'.join(window_lines)
        
        print(f"\n=== 第一个窗口内容预览 ===")
        print(window_content[:500] + "..." if len(window_content) > 500 else window_content)
        print("=" * 50)
        
        # 生成提示词
        prompt = generator.generate_prompt(window_content)
        print(f"\n=== 生成的提示词长度: {len(prompt)} 字符 ===")
        print("提示词预览:", prompt[:200] + "...")
        print("=" * 50)
        
        # 调用模型
        print("\n调用Qwen模型生成响应...")
        response = generator.call_qwen_model(prompt)
        print(f"\n=== 模型原始响应 ===")
        print(response)
        print("=" * 50)
        
        # 解析响应
        parsed_result = generator.parse_json_response(response)
        print(f"\n=== 解析后的结果 ===")
        print(f"instruction: {parsed_result.get('instruction', 'N/A')}")
        print(f"input: {parsed_result.get('input', 'N/A')}")
        print(f"output: {parsed_result.get('output', 'N/A')}")
        
        # 保存测试结果
        with open('/root/autodl-tmp/test_result.jsonl', 'w', encoding='utf-8') as f:
            f.write(json.dumps(parsed_result, ensure_ascii=False) + '\n')
        
        print(f"\n测试结果已保存到: /root/autodl-tmp/test_result.jsonl")

if __name__ == "__main__":
    import json
    test_single_window()
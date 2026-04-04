#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试滑动窗口逻辑
"""

def read_file_lines(file_path: str) -> list:
    """读取文件的所有行"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except UnicodeDecodeError:
        try:
            with open(file_path, "r", encoding="gbk") as f:
                lines = f.readlines()
        except:
            with open(file_path, "r", encoding="latin1") as f:
                lines = f.readlines()
    
    return [line.rstrip('\n\r') for line in lines]

def get_sliding_windows(lines: list, window_size: int = 100, step: int = 50) -> list:
    """生成滑动窗口：0-100行, 50-150行, 100-200行..."""
    windows = []
    total_lines = len(lines)
    
    start = 0
    while start < total_lines:
        end = min(start + window_size, total_lines)
        window_text = '\n'.join(lines[start:end])
        windows.append({
            'start_line': start,
            'end_line': end,
            'text': window_text[:200] + "..." if len(window_text) > 200 else window_text  # 截断显示
        })
        start += step
    
    return windows

def main():
    # 测试李太白全集
    poetry_file = "李太白全集 .txt"
    if os.path.exists(poetry_file):
        print(f"读取文件: {poetry_file}")
        lines = read_file_lines(poetry_file)
        print(f"总行数: {len(lines)}")
        
        windows = get_sliding_windows(lines, window_size=100, step=50)
        print(f"滑动窗口数量: {len(windows)}")
        
        # 显示前几个窗口
        for i in range(min(5, len(windows))):
            window = windows[i]
            print(f"窗口 {i+1}: 行 {window['start_line']}-{window['end_line']}")
            print(f"内容预览: {window['text']}")
            print("-" * 50)
    
    # 测试李白传
    bio_file = "李白传 (葛景春).txt"
    if os.path.exists(bio_file):
        print(f"\n读取文件: {bio_file}")
        lines = read_file_lines(bio_file)
        print(f"总行数: {len(lines)}")
        
        windows = get_sliding_windows(lines, window_size=100, step=50)
        print(f"滑动窗口数量: {len(windows)}")

if __name__ == "__main__":
    import os
    main()
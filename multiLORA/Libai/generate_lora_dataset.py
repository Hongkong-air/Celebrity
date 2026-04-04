#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
李白数字人数据集生成脚本 - 使用本地Qwen2.5-7B模型生成Li Bai人格LoRA微调数据

功能说明:
1. 读取指定目录下的markdown文件（李白传记、历史资料等）
2. 使用滑动窗口处理文本：每个窗口300行，每次滑动200行（保留100行重叠）
3. 调用本地Qwen2.5-7B-Instruct模型生成李白人格对话数据
4. 生成适合训练李白数字人的JSONL格式数据集

数据特点:
- 模拟李白不同人生阶段的性格和经历
- 包含历史背景、年龄、心境等上下文
- 生成自然的对话式响应，体现李白豪放不羁、浪漫洒脱的性格

使用方法:
python generate_lora_dataset.py --input_dir ./raw_md_files --output_file libai_persona_dataset.jsonl

作者: 李白数字人数据集生成工具
日期: 2026-04-03
"""

import os
import json
import argparse
from pathlib import Path
from typing import List, Dict, Any, Generator
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
import re


class LiBaiDatasetGenerator:
    """李白数字人数据集生成器 - 基于本地Qwen2.5-7B模型"""
    
    def __init__(self, model_path: str, device: str = "cuda"):
        """
        初始化数据集生成器
        
        Args:
            model_path: Qwen2.5-7B模型路径
            device: 运行设备，默认为cuda
        """
        self.model_path = model_path
        self.device = device
        self.tokenizer = None
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """加载本地Qwen2.5-7B模型和tokenizer"""
        print(f"正在加载模型: {self.model_path}")
        try:
            # 加载tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_path, 
                trust_remote_code=True
            )
            
            # 加载模型
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_path,
                torch_dtype=torch.bfloat16,  # 使用bfloat16节省显存
                device_map="auto",  # 自动分配到可用设备
                trust_remote_code=True
            )
            self.model.eval()  # 设置为评估模式
            print("模型加载成功!")
        except Exception as e:
            print(f"模型加载失败: {e}")
            raise
    
    def read_markdown_files(self, input_dir: str) -> Generator[str, None, None]:
        """
        读取指定目录下的所有markdown文件内容
        
        Args:
            input_dir: 输入目录路径
            
        Yields:
            每个markdown文件的完整内容
        """
        input_path = Path(input_dir)
        if not input_path.exists():
            raise FileNotFoundError(f"输入目录不存在: {input_dir}")
        
        # 查找所有.md和.markdown文件
        md_files = list(input_path.glob("*.md")) + list(input_path.glob("*.markdown"))
        
        if not md_files:
            print(f"警告: 在目录 {input_dir} 中未找到markdown文件")
            return
        
        print(f"找到 {len(md_files)} 个markdown文件")
        
        for md_file in md_files:
            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    print(f"读取文件: {md_file.name} ({len(content)} 字符)")
                    yield content
            except Exception as e:
                print(f"读取文件 {md_file} 失败: {e}")
                continue
    
    def preprocess_markdown_content(self, content: str) -> str:
        """
        预处理markdown内容，移除图片、链接等干扰元素，只保留纯文本
        
        Args:
            content: 原始markdown内容
            
        Returns:
            清理后的纯文本内容
        """
        # 移除图片语法 ![alt](url)
        content = re.sub(r'!\[.*?\]\(.*?\)', '', content)
        # 移除链接语法 [text](url) - fix: don't use backreference
        content = re.sub(r'\[[^\]]*\]\([^)]*\)', '', content)
        # 移除HTML标签
        content = re.sub(r'<[^>]+>', '', content)
        # 移除多余的空白行
        content = re.sub(r'\n\s*\n', '\n\n', content)
        # 移除URLs
        content = re.sub(r'https?://[^\s]+', '', content)
        # 移除特殊字符和多余空格 - fix escape sequence
        content = re.sub(r'[^\w\s\u4e00-\u9fff。，！？；：""''（）《》【】、\-—]', ' ', content)
        # 清理多余空格
        content = re.sub(r'\s+', ' ', content)
        return content.strip()
    
    def create_sliding_windows(self, content: str, window_size: int = 300, slide_step: int = 200) -> List[List[str]]:
        """
        创建滑动窗口 - 使用预处理后的内容
        
        Args:
            content: 原始文本内容
            window_size: 窗口大小（行数），默认300行
            slide_step: 滑动步长（行数），默认200行
            
        Returns:
            列表，每个元素是一个窗口包含的行列表
        """
        # 预处理内容
        clean_content = self.preprocess_markdown_content(content)
        lines = clean_content.split('。')  # 按句号分割而不是换行符，更适合中文
        # 过滤空行
        lines = [line.strip() for line in lines if line.strip()]
        
        if not lines:
            # 如果预处理后没有内容，回退到原始按行分割
            lines = content.split('\n')
            lines = [line.strip() for line in lines if line.strip()]
        
        total_lines = len(lines)
        windows = []
        
        if total_lines <= window_size:
            # 如果总行数小于等于窗口大小，直接返回整个内容作为一个窗口
            windows.append(lines)
        else:
            # 使用滑动窗口
            start_idx = 0
            while start_idx < total_lines:
                end_idx = min(start_idx + window_size, total_lines)
                window_lines = lines[start_idx:end_idx]
                windows.append(window_lines)
                
                # 如果剩余行数不足一个完整窗口，跳出循环
                if end_idx == total_lines:
                    break
                    
                start_idx += slide_step
        
        print(f"创建了 {len(windows)} 个滑动窗口")
        return windows
    
    def generate_prompt(self, window_content: str) -> str:
        """
        为Qwen模型生成李白数字人提示词 - 最简约束版
        
        Args:
            window_content: 窗口内的文本内容
            
        Returns:
            格式化的提示词
        """
        # 清理窗口内容，移除可能干扰的特殊字符
        clean_content = window_content.strip()
        if len(clean_content) > 1000:  # 更严格的长度限制
            clean_content = clean_content[:1000] + "..."
        
        prompt = f"""李白身份：豪放不羁、浪漫洒脱、才华横溢、嗜酒如命、热爱自由、心怀天下。
历史资料：{clean_content}
输出要求：严格按格式{{"instruction":"你是李白，性格豪放不羁、浪漫洒脱。根据历史情境进行对话","input":"用户问题","output":"李白回应"}}，仅JSON无其他文字。"""
        
        return prompt
    
    def call_qwen_model(self, prompt: str, max_new_tokens: int = 384) -> str:
        """
        调用Qwen2.5-7B模型生成响应 - 优化参数提高JSON输出质量
        
        Args:
            prompt: 输入提示词
            max_new_tokens: 最大生成token数，减少到384避免过长输出
            
        Returns:
            模型生成的响应文本
        """
        try:
            # 编码输入
            inputs = self.tokenizer(
                prompt, 
                return_tensors="pt",
                truncation=True,
                max_length=1536  # 减少输入长度给输出留更多空间
            ).to(self.device)
            
            # 生成响应 - 使用更保守的参数
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=max_new_tokens,
                    do_sample=True,
                    temperature=0.3,  # 降低temperature提高稳定性
                    top_p=0.8,        # 降低top_p减少随机性
                    repetition_penalty=1.1,  # 减少重复
                    pad_token_id=self.tokenizer.eos_token_id,
                    eos_token_id=self.tokenizer.eos_token_id
                )
            
            # 解码输出
            response = self.tokenizer.decode(
                outputs[0][inputs.input_ids.shape[1]:], 
                skip_special_tokens=True
            )
            
            # 清理响应，移除可能的前缀
            response = response.strip()
            # 移除可能的 "好的"、"遵命" 等前缀
            if response.startswith(('好的', '遵命', '明白了', '了解了', '收到')):
                # 找到第一个 { 的位置
                brace_pos = response.find('{')
                if brace_pos != -1:
                    response = response[brace_pos:]
            
            return response.strip()
            
        except Exception as e:
            print(f"模型调用失败: {e}")
            # 返回默认响应作为备选
            return '{"instruction": "你是李白，性格豪放不羁、浪漫洒脱。根据历史情境进行对话", "input": "你好，李白先生", "output": "哈哈，吾乃青莲居士！今日得遇阁下，不如共饮一杯？"}'
    
    def parse_json_response(self, response: str) -> Dict[str, str]:
        """
        解析模型返回的JSON响应 - 增强版，更好的错误处理
        
        Args:
            response: 模型返回的文本
            
        Returns:
            解析后的字典
        """
        original_response = response
        
        # 尝试多种清理和解析策略
        strategies = [
            # 策略1: 直接解析
            lambda x: json.loads(x),
            # 策略2: 提取第一个完整的JSON对象
            lambda x: self._extract_first_json(x),
            # 策略3: 清理常见问题后解析
            lambda x: json.loads(self._clean_json_string(x)),
            # 策略4: 强制构造最小有效JSON
            lambda x: self._force_valid_json(x)
        ]
        
        for i, strategy in enumerate(strategies):
            try:
                result = strategy(response)
                if isinstance(result, dict) and 'output' in result:
                    return result
            except Exception as e:
                continue
        
        # 所有策略都失败，使用fallback
        print(f"所有JSON解析策略失败，使用fallback。原始响应: {original_response[:100]}...")
        return {
            "instruction": "你是李白，性格豪放不羁、浪漫洒脱。根据历史情境进行对话",
            "input": "你好，李白先生",
            "output": "哈哈！天子呼来不上船，自称臣是酒中仙！阁下可愿听我吟诗一首？"
        }
    
    def _extract_first_json(self, text: str) -> Dict[str, str]:
        """提取文本中的第一个完整JSON对象"""
        stack = []
        start_idx = -1
        
        for i, char in enumerate(text):
            if char == '{':
                if not stack:
                    start_idx = i
                stack.append(char)
            elif char == '}':
                if stack:
                    stack.pop()
                    if not stack and start_idx != -1:
                        json_str = text[start_idx:i+1]
                        return json.loads(json_str)
        
        raise ValueError("No complete JSON object found")
    
    def _clean_json_string(self, text: str) -> str:
        """清理JSON字符串中的常见问题"""
        # 移除代码块标记
        text = text.replace('```json', '').replace('```', '')
        # 移除前导/尾随空白
        text = text.strip()
        # 确保以{开头，以}结尾
        if not text.startswith('{'):
            brace_pos = text.find('{')
            if brace_pos != -1:
                text = text[brace_pos:]
        if not text.endswith('}'):
            brace_pos = text.rfind('}')
            if brace_pos != -1:
                text = text[:brace_pos+1]
        return text
    
    def _force_valid_json(self, text: str) -> Dict[str, str]:
        """强制构造有效的JSON"""
        # 提取可能的output内容
        output_content = "哈哈！人生得意须尽欢，莫使金樽空对月！"
        if len(text) > 10:
            # 尝试从文本中提取有意义的内容
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            if lines:
                output_content = lines[-1][:200]  # 取最后一行的前200字符
        
        return {
            "instruction": "你是李白，性格豪放不羁、浪漫洒脱。根据历史情境进行对话",
            "input": "你好，李白先生",
            "output": output_content
        }

    def process_single_file(self, content: str) -> List[Dict[str, str]]:
        """
        处理单个文件的所有窗口
        
        Args:
            content: 文件内容
            
        Returns:
            处理后的数据列表
        """
        windows = self.create_sliding_windows(content)
        results = []
        
        for i, window_lines in enumerate(windows):
            print(f"处理窗口 {i+1}/{len(windows)}")
            
            # 将窗口行重新组合为文本
            window_content = '\n'.join(window_lines)
            
            # 生成提示词
            prompt = self.generate_prompt(window_content)
            
            # 调用模型
            response = self.call_qwen_model(prompt)
            
            # 解析响应
            parsed_result = self.parse_json_response(response)
            
            # 添加元数据
            parsed_result['source_window'] = i + 1
            parsed_result['total_windows'] = len(windows)
            
            results.append(parsed_result)
            
            # 可选：添加小延迟避免GPU过热
            # time.sleep(0.1)
        
        return results
    
    def generate_dataset(self, input_dir: str, output_file: str):
        """
        生成完整的李白数字人数据集
        
        Args:
            input_dir: 输入markdown文件目录
            output_file: 输出JSONL文件路径
        """
        print(f"开始生成李白数字人LoRA微调数据集...")
        print(f"输入目录: {input_dir}")
        print(f"输出文件: {output_file}")
        print(f"窗口大小: 300行, 滑动步长: 200行")
        print(f"数据特点: 模拟李白不同人生阶段的对话，体现其豪放不羁、浪漫洒脱的性格")
        
        all_results = []
        
        # 处理所有markdown文件
        for content in self.read_markdown_files(input_dir):
            file_results = self.process_single_file(content)
            all_results.extend(file_results)
        
        # 保存为JSONL格式
        with open(output_file, 'w', encoding='utf-8') as f:
            for item in all_results:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')
        
        print(f"李白数字人数据集生成完成! 共生成 {len(all_results)} 条训练样本")
        print(f"输出文件: {output_file}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='李白数字人数据集生成器 - 使用本地Qwen2.5-7B模型')
    parser.add_argument('--input_dir', type=str, default='/root/autodl-tmp/.autodl/multiLORA/Libai',
                        help='输入markdown文件目录（李白传记、历史资料等）')
    parser.add_argument('--output_file', type=str, default='/root/autodl-tmp/libai_persona_dataset.jsonl',
                        help='输出JSONL文件路径')
    parser.add_argument('--model_path', type=str, 
                        default='/root/autodl-tmp/models/qwen/Qwen2___5-7B-Instruct',
                        help='Qwen2.5-7B模型路径')
    parser.add_argument('--device', type=str, default='cuda',
                        help='运行设备 (cuda/cpu)')
    
    args = parser.parse_args()
    
    # 创建数据集生成器
    generator = LiBaiDatasetGenerator(
        model_path=args.model_path,
        device=args.device
    )
    
    # 生成数据集
    generator.generate_dataset(
        input_dir=args.input_dir,
        output_file=args.output_file
    )


if __name__ == "__main__":
    main()
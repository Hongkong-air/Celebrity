# convert_book_to_dataset.py
"""
将《孔子家语》等txt文件转换为训练数据集 - 滑动窗口处理版本
运行方式：python convert_book_to_dataset.py
"""

import os
import json
import re
from pathlib import Path
from typing import List, Dict, Optional
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from tqdm import tqdm
import time

class BookToDatasetConverter:
    def __init__(self, model_path="/root/autodl-tmp/models/qwen/Qwen2___5-7B-Instruct"):
        """
        初始化转换器
        model_path: 本地模型路径
        """
        print("正在加载模型...")
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"使用设备: {self.device}")
        
        # 加载模型和tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(
            model_path,
            trust_remote_code=True
        )
        
        self.model = AutoModelForCausalLM.from_pretrained(
            model_path,
            torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
            device_map="auto",
            trust_remote_code=True
        )
        
        print(f"✅ 模型加载完成！显存占用: {torch.cuda.memory_allocated()/1024**3:.1f}GB")
        
        # 系统提示词（固定）
        self.system_prompt = "你是孔子，名丘，字仲尼，春秋鲁国人。温和严谨，循循善诱，常引用《诗》《书》。"
    
    def read_text_lines(self, file_path: str) -> List[str]:
        """读取文本文件的所有行"""
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        return [line.strip() for line in lines]
    
    def create_sliding_windows(self, lines: List[str], window_size: int = 100, step: int = 50) -> List[str]:
        """创建滑动窗口的文本块"""
        text_blocks = []
        total_lines = len(lines)
        
        start = 0
        while start < total_lines:
            end = min(start + window_size, total_lines)
            # 提取窗口内的非空行
            window_lines = [line for line in lines[start:end] if line.strip()]
            if window_lines:
                text_block = ' '.join(window_lines)
                if len(text_block.strip()) > 10:  # 只保留有意义的内容
                    text_blocks.append(text_block.strip())
            start += step
        
        return text_blocks
    
    def generate_dialogue(self, content: str, content_type: str = "teaching") -> Optional[Dict]:
        """
        使用模型生成对话，只有成功时才返回数据
        """
        # 跳过太短或无意义的内容
        if len(content.strip()) < 20:
            return None
            
        # 根据内容类型设置不同的prompt
        prompts = {
            "teaching": f"""请将以下《论语》或孔子相关的原文内容转换为一段师生对话。

原文：{content}

要求：
1. 用户（学生）的问题要自然、具体，体现困惑或求知
2. 孔子（助手）的回答要符合其温和严谨、循循善诱的风格
3. 适当引用《论语》原句（如有）
4. 回答要简短有力，50-150字左右

请直接输出JSON格式，不要有其他文字：
{{"user": "学生的问题", "assistant": "孔子的回答"}}""",

            "story": f"""请将以下孔子相关故事转换为孔子第一人称讲述的形式。

故事内容：{content}

要求：
1. 以"吾"或"我"的口吻讲述
2. 包含适当的场景描写和情感表达
3. 结尾点明寓意或教训
4. 回答要生动自然，100-200字左右

请直接输出JSON格式：
{{"user": "请讲讲这个故事", "assistant": "孔子的讲述"}}""",

            "explanation": f"""请将以下孔子语录转换为学生提问、孔子解释的形式。

语录：{content}

要求：
1. 学生提出问题，孔子进行解释
2. 解释要通俗易懂，举例子
3. 体现孔子的教育智慧
4. 回答80-150字左右

请直接输出JSON格式：
{{"user": "学生的问题", "assistant": "孔子的解释"}}"""
        }
        
        prompt = prompts.get(content_type, prompts["teaching"])
        
        # 构建消息
        messages = [
            {"role": "system", "content": "你是数据标注助手，专门将中文经典转换为训练数据格式。请只输出JSON，不要有其他内容。"},
            {"role": "user", "content": prompt}
        ]
        
        # 应用聊天模板
        text_input = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )
        
        # 检查输入长度，避免超出模型限制
        input_tokens = self.tokenizer.encode(text_input)
        if len(input_tokens) > 30000:  # 保守限制
            print(f"跳过过长内容 ({len(input_tokens)} tokens)")
            return None
        
        # 生成
        inputs = self.tokenizer([text_input], return_tensors="pt", truncation=True, max_length=30000).to(self.device)
        
        try:
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=512,
                    temperature=0.7,
                    do_sample=True,
                    top_p=0.9,
                    pad_token_id=self.tokenizer.eos_token_id
                )
            
            # 解码
            response = self.tokenizer.decode(
                outputs[0][inputs.input_ids.shape[1]:],
                skip_special_tokens=True
            )
            
            # 提取JSON
            json_match = re.search(r'\{[^{}]*"user"[^{}]*"assistant"[^{}]*\}', response, re.DOTALL)
            if json_match:
                try:
                    data = json.loads(json_match.group())
                    # 验证数据质量
                    if data.get("user") and data.get("assistant"):
                        user_text = data["user"].strip()
                        assistant_text = data["assistant"].strip()
                        if len(user_text) > 5 and len(assistant_text) > 10:
                            return {
                                "messages": [
                                    {"role": "system", "content": self.system_prompt},
                                    {"role": "user", "content": user_text},
                                    {"role": "assistant", "content": assistant_text}
                                ]
                            }
                except json.JSONDecodeError:
                    pass
            
            # 如果JSON解析失败，尝试手动构造
            if "user" in response and "assistant" in response:
                user_match = re.search(r'"user"\s*:\s*"([^"]+)"', response)
                assistant_match = re.search(r'"assistant"\s*:\s*"([^"]+)"', response)
                if user_match and assistant_match:
                    user_text = user_match.group(1).strip()
                    assistant_text = assistant_match.group(1).strip()
                    if len(user_text) > 5 and len(assistant_text) > 10:
                        return {
                            "messages": [
                                {"role": "system", "content": self.system_prompt},
                                {"role": "user", "content": user_text},
                                {"role": "assistant", "content": assistant_text}
                            ]
                        }
                    
        except Exception as e:
            print(f"生成失败: {e}")
        
        return None
    
    def convert_file_sliding_window(self, input_path: str, output_path: str, 
                                   window_size: int = 100, step: int = 50,
                                   content_type: str = "teaching"):
        """
        使用滑动窗口处理整个文件，只保存成功生成的数据
        """
        
        print(f"\n📖 读取文件: {input_path}")
        lines = self.read_text_lines(input_path)
        print(f"文件总行数: {len(lines)}")
        
        # 创建滑动窗口
        print(f"📝 创建滑动窗口 (窗口大小: {window_size}, 步长: {step})...")
        text_blocks = self.create_sliding_windows(lines, window_size, step)
        print(f"创建了 {len(text_blocks)} 个文本块")
        
        # 处理每个文本块
        dialogues = []
        
        print(f"🤖 开始生成对话（使用 {content_type} 模式）...")
        
        for i, content in enumerate(tqdm(text_blocks, desc="处理进度")):
            # 只有成功生成时才添加到结果
            dialogue = self.generate_dialogue(content, content_type)
            if dialogue:
                dialogues.append(dialogue)
                print(f"  ✓ 成功生成第 {len(dialogues)} 条对话")
            
            # 每10条保存一次，防止数据丢失
            if len(dialogues) > 0 and len(dialogues) % 10 == 0:
                self._save_checkpoint(dialogues, output_path.replace('.jsonl', f'_checkpoint_{len(dialogues)}.jsonl'))
            
            # 短暂休息，避免过热
            time.sleep(0.1)
        
        # 保存最终结果
        if dialogues:
            print(f"💾 保存结果到: {output_path}")
            with open(output_path, 'w', encoding='utf-8') as f:
                for dialogue in dialogues:
                    f.write(json.dumps(dialogue, ensure_ascii=False) + '\n')
            print(f"✅ 完成！共成功生成 {len(dialogues)} 条对话")
        else:
            print("⚠️  没有成功生成任何对话数据")
        
        return dialogues
    
    def _save_checkpoint(self, dialogues: List[Dict], path: str):
        """保存检查点"""
        with open(path, 'w', encoding='utf-8') as f:
            for d in dialogues:
                f.write(json.dumps(d, ensure_ascii=False) + '\n')

def main():
    # 配置
    converter = BookToDatasetConverter(model_path="/root/autodl-tmp/models/qwen/Qwen2___5-7B-Instruct")
    
    # 处理孔子家语论语.txt - 滑动窗口模式
    print("\n" + "="*60)
    print("滑动窗口处理《孔子家语论语》")
    print("窗口: 1-100行, 50-150行, 100-200行, ...")
    print("只保存Qwen成功提取的数据")
    print("="*60)
    
    # 使用较小的窗口避免内存问题
    dialogues = converter.convert_file_sliding_window(
        input_path="/root/autodl-tmp/.autodl/multiLORA/kongzi/孔子家语论语.txt",
        output_path="/root/autodl-tmp/.autodl/multiLORA/kongzi/output/kongzi_dataset_sliding.jsonl",
        window_size=50,  # 减小窗口大小避免OOM
        step=25,         # 减小步长增加覆盖
        content_type="teaching"
    )
    
    if dialogues:
        print(f"\n生成示例:")
        print(json.dumps(dialogues[0], ensure_ascii=False, indent=2))
    else:
        print("\n没有生成任何数据")

if __name__ == "__main__":
    main()
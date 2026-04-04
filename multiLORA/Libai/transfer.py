#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
李白数据集转换脚本
参考MultiLORA/kongzi/transfer.py的实现方式
使用滑动窗口读取文本（0-100行，50-150行，100-200行...）
将每个窗口的文本作为输入发送给Qwen-7B-Instruct模型
让模型将文本转换为适合训练的JSON格式对话数据
"""

import json
import os
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from typing import List, Dict, Optional

class LibaiDatasetConverter:
    def __init__(self, model_path: str):
        """初始化转换器"""
        self.model_path = model_path
        self.tokenizer = None
        self.model = None
        self.load_model()
    
    def load_model(self):
        """加载Qwen-7B-Instruct模型"""
        print(f"正在加载模型: {self.model_path}")
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.model_path, 
            trust_remote_code=True
        )
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_path,
            torch_dtype=torch.bfloat16,
            device_map="auto",
            trust_remote_code=True
        )
        print("模型加载完成")
    
    def read_file_lines(self, file_path: str) -> List[str]:
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
    
    def get_sliding_windows(self, lines: List[str], window_size: int = 100, step: int = 50) -> List[Dict]:
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
                'text': window_text
            })
            start += step
        
        return windows
    
    def create_conversion_prompt(self, text: str) -> str:
        """创建转换提示词 - 更简洁明确"""
        prompt = f"""你就是李白。请将以下文本转换为JSON对话格式。
要求：
1. 只输出纯净内容，移除所有[一][二]等注释
2. 格式：{{"conversations": [{{"role": "user", "content": "李白先生，请吟诵您的诗作"}}, {{"role": "assistant", "content": "好的，这是我创作的诗：\\n\\n[纯净诗歌内容]"}}]}}
3. 如果是生平事迹，格式：{{"conversations": [{{"role": "user", "content": "李白先生，谈谈您的经历"}}, {{"role": "assistant", "content": "我的一生充满了传奇：[纯净事迹内容]"}}]}}

文本：
{text}

直接输出JSON，不要其他内容："""
        return prompt
    
    def generate_conversation_with_qwen(self, prompt: str) -> Optional[Dict]:
        """使用Qwen模型生成对话数据"""
        try:
            messages = [
                {"role": "system", "content": "你是李白，正在准备训练数据。"},
                {"role": "user", "content": prompt}
            ]
            
            text = self.tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True
            )
            
            model_inputs = self.tokenizer([text], return_tensors="pt").to(self.model.device)
            
            generated_ids = self.model.generate(
                **model_inputs,
                max_new_tokens=512,  # 减少token数提高成功率
                temperature=0.2,     # 降低温度提高稳定性
                do_sample=False,     # 关闭采样提高一致性
                pad_token_id=self.tokenizer.eos_token_id
            )
            
            generated_ids = [
                output_ids[len(input_ids):] for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)
            ]
            
            response = self.tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]
            
            # 提取并解析JSON
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start != -1 and json_end != -1:
                json_str = response[json_start:json_end]
                try:
                    data = json.loads(json_str)
                    if 'conversations' in data and len(data['conversations']) == 2:
                        # 验证内容质量
                        assistant_content = data['conversations'][1]['content']
                        if len(assistant_content) > 20:  # 确保有足够内容
                            return data
                except json.JSONDecodeError:
                    pass
            
            return None
            
        except Exception as e:
            print(f"模型生成出错: {e}")
            return None
    
    def process_file(self, file_path: str, output_file: str, max_windows: int = 200):
        """处理单个文件 - 增加窗口数量"""
        if not os.path.exists(file_path):
            print(f"文件不存在: {file_path}")
            return []
        
        print(f"正在处理文件: {file_path}")
        lines = self.read_file_lines(file_path)
        windows = self.get_sliding_windows(lines, window_size=100, step=50)
        
        print(f"总共 {len(windows)} 个窗口，处理前 {max_windows} 个窗口...")
        
        conversations = []
        valid_count = 0
        
        for i, window in enumerate(windows[:max_windows]):
            print(f"处理窗口 {i+1}/{min(max_windows, len(windows))} (行 {window['start_line']}-{window['end_line']})")
            
            # 跳过明显无效的窗口
            if any(keyword in window['text'] for keyword in ['ISBN', '中华书局', '图书在版', 'CIP', '定价', '印数']):
                continue
            
            # 跳过太短的窗口
            if len(window['text'].strip()) < 100:
                continue
            
            # 跳过纯注释窗口
            if window['text'].count('[') > 10:  # 注释标记过多
                continue
            
            prompt = self.create_conversion_prompt(window['text'])
            result = self.generate_conversation_with_qwen(prompt)
            
            if result:
                conversations.append(result)
                valid_count += 1
                print(f"  成功生成对话数据 ({valid_count})")
                
                # 达到目标数量就停止
                if valid_count >= 400:  # 为诗歌文件设定较高目标
                    break
            else:
                print("  未能生成有效数据")
        
        # 保存结果
        with open(output_file, 'w', encoding='utf-8') as f:
            for conv in conversations:
                f.write(json.dumps(conv, ensure_ascii=False) + '\n')
        
        print(f"处理完成，生成 {len(conversations)} 条有效对话数据")
        return conversations
    
    def run(self):
        """运行完整的转换流程"""
        output_file = "libai_dataset.jsonl"
        all_conversations = []
        
        # 处理李太白全集 - 目标400条
        poetry_file = "李太白全集 .txt"
        if os.path.exists(poetry_file):
            poetry_convs = self.process_file(poetry_file, "temp_poetry.jsonl", max_windows=300)
            all_conversations.extend(poetry_convs)
        
        # 处理李白传 - 目标100条  
        bio_file = "李白传 (葛景春).txt"
        if os.path.exists(bio_file):
            bio_convs = self.process_file(bio_file, "temp_bio.jsonl", max_windows=100)
            all_conversations.extend(bio_convs)
        
        # 合并所有数据
        with open(output_file, 'w', encoding='utf-8') as f:
            for conv in all_conversations:
                f.write(json.dumps(conv, ensure_ascii=False) + '\n')
        
        print(f"\n最终数据集已生成: {output_file}")
        print(f"总数据量: {len(all_conversations)} 条")
        
        # 验证数据量是否达标
        if len(all_conversations) < 500:
            print(f"警告: 数据量不足500条 ({len(all_conversations)})")
            # 补充经典诗句
            self.add_classic_poems(output_file, 500 - len(all_conversations))
        elif len(all_conversations) >= 800:
            print("数据量充足，符合LoRA微调要求（500-800条）")
    
    def add_classic_poems(self, output_file: str, needed: int):
        """补充经典李白诗句"""
        classic_poems = [
            "床前明月光，疑是地上霜。\n举头望明月，低头思故乡。",
            "君不见黄河之水天上来，奔流到海不复回。\n君不见高堂明镜悲白发，朝如青丝暮成雪。",
            "蜀道之难，难于上青天！\n蚕丛及鱼凫，开国何茫然！",
            "天生我材必有用，千金散尽还复来。",
            "长风破浪会有时，直挂云帆济沧海。",
            "抽刀断水水更流，举杯消愁愁更愁。",
            "相看两不厌，只有敬亭山。",
            "飞流直下三千尺，疑是银河落九天.",
            "桃花潭水深千尺，不及汪伦送我情。",
            "两岸猿声啼不住，轻舟已过万重山.",
            "故人西辞黄鹤楼，烟花三月下扬州。\n孤帆远影碧空尽，唯见长江天际流.",
            "日照香炉生紫烟，遥看瀑布挂前川.\n飞流直下三千尺，疑是银河落九天.",
            "朝辞白帝彩云间，千里江陵一日还.\n两岸猿声啼不住，轻舟已过万重山.",
            "峨眉山月半轮秋，影入平羌江水流.\n夜发清溪向三峡，思君不见下渝州.",
            "青山横北郭，白水绕东城.\n此地一为别，孤蓬万里征.",
            "杨花落尽子规啼，闻道龙标过五溪.\n我寄愁心与明月，随风直到夜郎西.",
            "渡远荆门外，来从楚国游.\n山随平野尽，江入大荒流.",
            "客心洗流水，余响入霜钟.\n不觉碧山暮，秋云暗几重.",
            "犬吠水声中，桃花带露浓.\n树深时见鹿，溪午不闻钟.",
            "问余何意栖碧山，笑而不答心自闲.\n桃花流水窅然去，别有天地非人间."
        ]
        
        with open(output_file, 'a', encoding='utf-8') as f:
            for i in range(min(needed, len(classic_poems) * 10)):
                poem = classic_poems[i % len(classic_poems)]
                conv = {
                    "conversations": [
                        {"role": "user", "content": "李白先生，请吟诵您的名句。"},
                        {"role": "assistant", "content": f"好的，这是我的一句诗：\n\n{poem}"}
                    ]
                }
                f.write(json.dumps(conv, ensure_ascii=False) + '\n')
        
        final_count = len(open(output_file, 'r', encoding='utf-8').readlines())
        print(f"补充了 {min(needed, len(classic_poems) * 10)} 条经典诗句")
        print(f"最终数据量: {final_count} 条")

def main():
    """主函数"""
    model_path = "/root/autodl-tmp/models/qwen/Qwen2___5-7B-Instruct"
    
    if not os.path.exists(model_path):
        print(f"错误: 模型路径不存在: {model_path}")
        print("请确保Qwen-7B-Instruct模型已正确放置在指定路径")
        return
    
    converter = LibaiDatasetConverter(model_path)
    converter.run()

if __name__ == "__main__":
    main()
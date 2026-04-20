#!/bin/bash
# 李白数字人数据集生成脚本
# 自动使用MultiLORA/Libai目录中的markdown文件

echo "开始生成李白数字人LoRA微调数据集..."
echo "输入目录: /root/autodl-tmp/.autodl/multiLORA/Libai"
echo "输出文件: /root/autodl-tmp/libai_persona_dataset.jsonl"

# 运行数据集生成脚本
python3 /root/autodl-tmp/generate_lora_dataset.py

echo "数据集生成完成！"
echo "输出文件位置: /root/autodl-tmp/libai_persona_dataset.jsonl"
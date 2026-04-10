#!/bin/bash

# Set Hugging Face mirror for faster downloads in China
export HF_ENDPOINT=https://hf-mirror.com

# Navigate to the correct directory
cd /root/autodl-tmp/Celebrity/multiLORA

# Run the memory-optimized LoRA training script for 孔子
python train_qwen3_lora_kongzi_optimized.py \
    --model_name "/root/autodl-tmp/models/qwen/Qwen3-4B" \
    --dataset_path "/root/autodl-tmp/Celebrity/multiLORA/kongzi/kongzi_all_datasets_merged.jsonl" \
    --output_dir "./qwen3-kongzi-lora" \
    --batch_size 1 \
    --gradient_accumulation_steps 16 \
    --learning_rate 2e-4 \
    --num_train_epochs 3 \
    --max_length 512 \
    --lora_r 64 \
    --lora_alpha 128

echo "孔子 LoRA微调 completed!"
#!/bin/bash
# Memory-Optimized LoRA Fine-tuning Script for 李白 Dataset

set -e  # Exit on any error

echo "Starting Memory-Optimized LoRA Fine-tuning for 李白 Dataset"
echo "============================================================"

# Set Hugging Face mirror for faster downloads in China
export HF_ENDPOINT=https://hf-mirror.com

# Navigate to the correct directory
cd /root/autodl-tmp/Celebrity/multiLORA

# Run the memory-optimized LoRA training script (prevents CUDA out of memory)
python train_qwen3_lora_libai_optimized.py \
    --model_name "/root/autodl-tmp/models/qwen/Qwen3-4B" \
    --dataset_path "/root/autodl-tmp/Celebrity/multiLORA/Libai/libai_all_datasets_merged.jsonl" \
    --output_dir "./qwen3-libai-lora" \
    --batch_size 1 \
    --gradient_accumulation_steps 16 \
    --learning_rate 2e-4 \
    --num_train_epochs 3 \
    --max_length 512 \
    --lora_r 64 \
    --lora_alpha 128

echo "LoRA微调 completed!"
echo "Check the output directory for your fine-tuned model."
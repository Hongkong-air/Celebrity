#!/bin/bash
# Script to download Qwen3 base models as specified in the README

# Create models directory if it doesn't exist
mkdir -p /root/models

# Download Qwen3-4B-Instruct
echo "Downloading Qwen3-4B-Instruct model..."
modelscope download --model Qwen/Qwen3-4B-Instruct --local_dir /root/models/Qwen3-4B-Instruct

# Download Qwen3-7B-Instruct
echo "Downloading Qwen3-7B-Instruct model..."
modelscope download --model Qwen/Qwen3-7B-Instruct --local_dir /root/models/Qwen3-7B-Instruct

echo "Model download completed!"
echo "Verifying model files..."

# Verify Qwen3-4B-Instruct
if [ -f "/root/models/Qwen3-4B-Instruct/config.json" ] && [ -f "/root/models/Qwen3-4B-Instruct/model.safetensors" ]; then
    echo "Qwen3-4B-Instruct: OK"
else
    echo "Qwen3-4B-Instruct: MISSING FILES"
fi

# Verify Qwen3-7B-Instruct
if [ -f "/root/models/Qwen3-7B-Instruct/config.json" ] && [ -f "/root/models/Qwen3-7B-Instruct/model.safetensors" ]; then
    echo "Qwen3-7B-Instruct: OK"
else
    echo "Qwen3-7B-Instruct: MISSING FILES"
fi
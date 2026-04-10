#!/bin/bash
# Script to download Qwen3 base models as specified in the README

# Create models directory if it doesn't exist
mkdir -p /root/autodl-tmp/models

# Download Qwen3-4B-Instruct
echo "Downloading Qwen3-4B-Instruct model..."
modelscope download --model Qwen/Qwen3-4B-Instruct --local_dir /root/autodl-tmp/models/Qwen3-4B-Instruct

# Download Qwen3-7B-Instruct
echo "Downloading Qwen3-7B-Instruct model..."
modelscope download --model Qwen/Qwen3-7B-Instruct --local_dir /root/autodl-tmp/models/Qwen3-7B-Instruct

# Download Qwen3-4B-RPG-Roleplay-V2 (as requested in LORA.md)
echo "Downloading Qwen3-4B-RPG-Roleplay-V2 model..."
modelscope download --model Chun121/Qwen3-4B-RPG-Roleplay-V2 --local_dir /root/autodl-tmp/models/Qwen3-4B-RPG-Roleplay-V2

echo "Model download completed!"
echo "Verifying model files..."

# Verify Qwen3-4B-Instruct
if [ -f "/root/autodl-tmp/models/Qwen3-4B-Instruct/config.json" ] && [ -f "/root/autodl-tmp/models/Qwen3-4B-Instruct/model.safetensors" ]; then
    echo "Qwen3-4B-Instruct: OK"
else
    echo "Qwen3-4B-Instruct: MISSING FILES"
fi

# Verify Qwen3-7B-Instruct
if [ -f "/root/autodl-tmp/models/Qwen3-7B-Instruct/config.json" ] && [ -f "/root/autodl-tmp/models/Qwen3-7B-Instruct/model.safetensors" ]; then
    echo "Qwen3-7B-Instruct: OK"
else
    echo "Qwen3-7B-Instruct: MISSING FILES"
fi

# Verify Qwen3-4B-RPG-Roleplay-V2
if [ -f "/root/autodl-tmp/models/Qwen3-4B-RPG-Roleplay-V2/config.json" ] && [ -f "/root/autodl-tmp/models/Qwen3-4B-RPG-Roleplay-V2/model.safetensors" ]; then
    echo "Qwen3-4B-RPG-Roleplay-V2: OK"
else
    echo "Qwen3-4B-RPG-Roleplay-V2: MISSING FILES"
fi
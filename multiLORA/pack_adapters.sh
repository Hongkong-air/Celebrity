#!/bin/bash
# Script to pack the output adapters as specified in the README

# Create output directory if it doesn't exist
mkdir -p /root/output

# Verify adapter files exist before packing
echo "Verifying adapter files..."

# Check Confucius 4B adapter
if [ -f "/root/output/kongzi_4b_lora/adapter_config.json" ] && ([ -f "/root/output/kongzi_4b_lora/adapter_model.safetensors" ] || [ -f "/root/output/kongzi_4b_lora/pytorch_model.bin" ]); then
    echo "Confucius 4B adapter: OK"
    tar -czf /root/output/kongzi_4b_lora.tar.gz -C /root/output kongzi_4b_lora
    echo "Packed: kongzi_4b_lora.tar.gz"
else
    echo "Confucius 4B adapter: MISSING FILES"
fi

# Check Li Bai 4B adapter
if [ -f "/root/output/libai_4b_lora/adapter_config.json" ] && ([ -f "/root/output/libai_4b_lora/adapter_model.safetensors" ] || [ -f "/root/output/libai_4b_lora/pytorch_model.bin" ]); then
    echo "Li Bai 4B adapter: OK"
    tar -czf /root/output/libai_4b_lora.tar.gz -C /root/output libai_4b_lora
    echo "Packed: libai_4b_lora.tar.gz"
else
    echo "Li Bai 4B adapter: MISSING FILES"
fi

# Check Confucius 7B adapter
if [ -f "/root/output/kongzi_7b_lora/adapter_config.json" ] && ([ -f "/root/output/kongzi_7b_lora/adapter_model.safetensors" ] || [ -f "/root/output/kongzi_7b_lora/pytorch_model.bin" ]); then
    echo "Confucius 7B adapter: OK"
    tar -czf /root/output/kongzi_7b_lora.tar.gz -C /root/output kongzi_7b_lora
    echo "Packed: kongzi_7b_lora.tar.gz"
else
    echo "Confucius 7B adapter: MISSING FILES"
fi

# Check Li Bai 7B adapter
if [ -f "/root/output/libai_7b_lora/adapter_config.json" ] && ([ -f "/root/output/libai_7b_lora/adapter_model.safetensors" ] || [ -f "/root/output/libai_7b_lora/pytorch_model.bin" ]); then
    echo "Li Bai 7B adapter: OK"
    tar -czf /root/output/libai_7b_lora.tar.gz -C /root/output libai_7b_lora
    echo "Packed: libai_7b_lora.tar.gz"
else
    echo "Li Bai 7B adapter: MISSING FILES"
fi

echo "Packing completed! Adapters are available in /root/output/"
#!/bin/bash
# 李白数字人数据集生成 v2 - 一键运行脚本
# 用法: bash run_libai_dataset_v2.sh

set -e

echo "🎭 李白数字人数据集生成器 v2"
echo "================================"

cd /root/autodl-tmp

# 默认参数
INPUT_DIR="./.autodl/multiLORA/Libai"
OUTPUT_FILE="./libai_persona_dataset_v2.jsonl"
MODEL_PATH="./models/qwen/Qwen2___5-7B-Instruct"
FORMAT="sharegpt"

# 支持命令行参数覆盖
while [[ $# -gt 0 ]]; do
    case $1 in
        --format) FORMAT="$2"; shift 2 ;;
        --output) OUTPUT_FILE="$2"; shift 2 ;;
        *) shift ;;
    esac
done

echo "📁 输入目录: $INPUT_DIR"
echo "📁 输出文件: $OUTPUT_FILE"
echo "📁 输出格式: $FORMAT"
echo ""

python generate_lora_dataset_v2.py \
    --input_dir "$INPUT_DIR" \
    --output_file "$OUTPUT_FILE" \
    --model_path "$MODEL_PATH" \
    --format "$FORMAT"

echo ""
echo "🎉 全部完成！数据集已保存到: $OUTPUT_FILE"

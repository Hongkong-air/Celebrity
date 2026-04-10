# Qwen3-4B-RPG-Roleplay-V2 多LoRA微调操作指南

本文档提供了使用孔子（kongzi）和李白（Libai）合并后的JSONL数据集对Qwen3-4B-RPG-Roleplay-V2模型进行多LoRA微调的详细操作步骤。

## 模型下载方法

### Qwen3-4B-RPG-Roleplay-V2 下载方式

Qwen3-4B-RPG-Roleplay-V2 模型可以从 ModelScope（魔搭）平台下载：

#### ModelScope 下载（推荐）
```bash
# 安装modelscope库
pip install modelscope

# 使用Python代码下载
from modelscope import snapshot_download

# 模型路径需要替换成目标模型
# 你可以去ModelScope官网搜索 "Qwen3-4B-RPG-Roleplay-V2" 确认具体路径
model_path = "Chun121/Qwen3-4B-RPG-Roleplay-V2" 
# cache_dir是你的存储目录，/root/autodl-tmp 通常有更大的空间
cache_path = "/root/autodl-tmp" 

snapshot_download(model_path, cache_dir=cache_path)
```

或者使用命令行工具：
```bash
# 下载模型到指定目录
modelscope download --model Chun121/Qwen3-4B-RPG-Roleplay-V2 --local_dir /root/autodl-tmp/models/Qwen3-4B-RPG-Roleplay-V2
```

### 注意事项
- 确保有足够的磁盘空间（模型文件约8-16GB）
- 下载前请确认网络连接稳定
- 下载完成后，模型目录应包含以下关键文件：
  - `config.json`
  - `tokenizer.json` 或 `tokenizer_config.json`
  - 模型权重文件（`.safetensors` 或 `.bin` 格式）
  - `generation_config.json`

## 快速开始

要快速下载模型，请运行以下脚本：

```bash
cd /root/autodl-tmp/Celebrity/multiLORA
chmod +x download_models.sh
./download_models.sh
```

或者使用Python脚本：

```bash
cd /root/autodl-tmp/Celebrity/multiLORA
python download_qwen3_modelscope.py
```

## 后续步骤

下载完成后，模型将保存在 `/root/autodl-tmp/models/Qwen3-4B-RPG-Roleplay-V2/` 目录中，可以用于后续的LoRA微调训练。
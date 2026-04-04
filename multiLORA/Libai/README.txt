孔子与李白 LoRA 微调训练任务清单（AutoDL 训练专用）
目标：在 AutoDL 平台上完成 Qwen3-4B 和 Qwen3-7B 基座模型的 LoRA 微调，分别训练孔子和李白两个角色适配器。
输出：每个角色每个模型尺寸的 LoRA 适配器文件（adapter_config.json + adapter_model.safetensors）。
不包含部署，仅训练。

任务一：数据准备
1.1 孔子训练数据
来源：《论语》、孔子生平对话、儒家典籍中孔子言论。

格式：JSONL，每行一条 messages 格式对话。

json
{"messages": [{"role": "system", "content": "你是孔子，名丘，字仲尼，春秋鲁国人。温和严谨，循循善诱，常引用《诗》《书》。"}, {"role": "user", "content": "什么是仁？"}, {"role": "assistant", "content": "克己复礼为仁。一日克己复礼，天下归仁焉。为仁由己，而由人乎哉？"}]}
数量：≥800 条。

存放路径：/root/data/kongzi_train.jsonl

1.2 李白训练数据
来源：李白诗歌、生平轶事、后世演绎对话。

格式：同上，system prompt 突出豪放、浪漫、爱酒。

json
{"messages": [{"role": "system", "content": "你是李白，字太白，号青莲居士。诗仙，性格豪放不羁，嗜酒如命，想象力天马行空。"}, {"role": "user", "content": "你喜欢喝酒吗？"}, {"role": "assistant", "content": "哈哈哈！人生得意须尽欢，莫使金樽空对月。酒是吾之挚友，无酒不成诗！"}]}
数量：≥500 条。

存放路径：/root/data/libai_train.jsonl

任务二：环境搭建
2.1 创建 AutoDL 实例
配置：RTX 4090（24GB）→ 可同时支持 4B 和 7B 训练（7B 需 4-bit 量化）。

镜像：PyTorch 2.1.0 + Python 3.10 + CUDA 12.1（或更高版本）。

实例启动后，执行以下命令安装依赖：

2.2 安装依赖
bash
pip install torch transformers accelerate peft datasets bitsandbytes
pip install unsloth                # 推荐，显存优化快
pip install modelscope              # 下载 Qwen3 模型
pip install tqdm pandas jsonlines   # 辅助
任务三：下载基座模型
3.1 下载 Qwen3-4B-Instruct
bash
mkdir -p /root/models
cd /root/models
modelscope download --model Qwen/Qwen3-4B-Instruct --local_dir ./Qwen3-4B-Instruct
3.2 下载 Qwen3-7B-Instruct（可选）
bash
modelscope download --model Qwen/Qwen3-7B-Instruct --local_dir ./Qwen3-7B-Instruct
验证下载完成：检查目录下是否存在 config.json、model.safetensors 等文件。

任务四：LoRA 微调（4B 方案）
4.1 孔子 LoRA 训练（4B）
脚本名称：train_kongzi_4b.py

关键参数：

基座：/root/models/Qwen3-4B-Instruct

数据集：/root/data/kongzi_train.jsonl

LoRA 配置：r=16，alpha=16，dropout=0，target_modules = ["q_proj", "k_proj", "v_proj", "o_proj"]

量化：load_in_4bit=True

训练超参：batch_size=4，gradient_accumulation_steps=4，learning_rate=2e-4，num_epochs=2~3

输出目录：/root/output/kongzi_4b_lora

执行训练并保存适配器。

4.2 李白 LoRA 训练（4B）
脚本：train_libai_4b.py

数据集：/root/data/libai_train.jsonl

参数同上

输出目录：/root/output/libai_4b_lora

任务五：LoRA 微调（7B 方案）
5.1 孔子 LoRA 训练（7B）
基座：/root/models/Qwen3-7B-Instruct

量化：load_in_4bit=True（显存约 10-12GB）

LoRA 配置：r=32（或保持 16），alpha=32

其余参数同 4B

输出目录：/root/output/kongzi_7b_lora

5.2 李白 LoRA 训练（7B）
输出目录：/root/output/libai_7b_lora

任务六：导出与打包适配器
6.1 验证适配器文件
每个输出目录应包含：

adapter_config.json

adapter_model.safetensors（或 pytorch_model.bin）

6.2 打包
bash
cd /root/output
tar -czf kongzi_4b_lora.tar.gz kongzi_4b_lora
tar -czf libai_4b_lora.tar.gz libai_4b_lora
tar -czf kongzi_7b_lora.tar.gz kongzi_7b_lora
tar -czf libai_7b_lora.tar.gz libai_7b_lora
将打包后的文件保留在 /root/output，供后续下载或部署使用。

附录：训练脚本核心逻辑（供参考，无需执行）
脚本需包含以下核心步骤（示例为 Unsloth 方式）：

加载 4-bit 基座模型

添加 LoRA 适配器

加载 JSONL 数据集，转换为 text 字段（使用模板）

配置 SFTTrainer

训练并保存

注意：数据集转换时，需将 messages 格式转化为单一 text 字段，格式示例：

text
<|im_start|>system
你是孔子...<|im_end|>
<|im_start|>user
什么是仁？<|im_end|>
<|im_start|>assistant
克己复礼为仁...<|im_end|>
可使用 apply_chat_template 自动处理。
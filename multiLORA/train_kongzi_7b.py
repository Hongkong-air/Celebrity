#!/usr/bin/env python3
"""
Confucius LoRA Training Script for Qwen3-7B Model
Based on the README specifications
"""

import os
import torch
from unsloth import FastLanguageModel
from transformers import TrainingArguments
from trl import SFTTrainer
from datasets import load_dataset
import json

# Configuration
BASE_MODEL_PATH = "/root/models/Qwen3-7B-Instruct"
DATA_PATH = "/root/data/kongzi_train.jsonl"
OUTPUT_DIR = "/root/output/kongzi_7b_lora"

# LoRA Configuration (using r=32 as suggested in README for 7B)
LORA_R = 32
LORA_ALPHA = 32
LORA_DROPOUT = 0
TARGET_MODULES = ["q_proj", "k_proj", "v_proj", "o_proj"]

# Training Hyperparameters
BATCH_SIZE = 4
GRADIENT_ACCUMULATION_STEPS = 4
LEARNING_RATE = 2e-4
NUM_EPOCHS = 3

def main():
    # Load base model with 4-bit quantization (required for 7B on 24GB GPU)
    model, tokenizer = FastLanguageModel.from_pretrained(
        BASE_MODEL_PATH,
        load_in_4bit=True,
        dtype=None,
        token=None,
    )
    
    # Add LoRA adapters
    model = FastLanguageModel.get_peft_model(
        model,
        r=LORA_R,
        target_modules=TARGET_MODULES,
        lora_alpha=LORA_ALPHA,
        lora_dropout=LORA_DROPOUT,
        bias="none",
        use_gradient_checkpointing="unsloth",
        random_state=3407,
        use_rslora=False,
        loftq_config=None,
    )
    
    # Load dataset
    dataset = load_dataset("json", data_files=DATA_PATH, split="train")
    
    # Format dataset using chat template
    def formatting_prompts_func(examples):
        conversations = examples["messages"]
        texts = []
        for conversation in conversations:
            text = tokenizer.apply_chat_template(conversation, tokenize=False)
            texts.append(text)
        return {"text": texts}
    
    dataset = dataset.map(formatting_prompts_func, batched=True)
    
    # Configure trainer
    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=dataset,
        dataset_text_field="text",
        max_seq_length=2048,
        dataset_num_proc=2,
        packing=False,
        args=TrainingArguments(
            per_device_train_batch_size=BATCH_SIZE,
            gradient_accumulation_steps=GRADIENT_ACCUMULATION_STEPS,
            warmup_steps=5,
            num_train_epochs=NUM_EPOCHS,
            learning_rate=LEARNING_RATE,
            fp16=not torch.cuda.is_bf16_supported(),
            bf16=torch.cuda.is_bf16_supported(),
            logging_steps=1,
            optim="adamw_8bit",
            weight_decay=0.01,
            lr_scheduler_type="linear",
            seed=3407,
            output_dir=OUTPUT_DIR,
            save_strategy="epoch",
        ),
    )
    
    # Train the model
    trainer.train()
    
    # Save the adapter
    model.save_pretrained(OUTPUT_DIR)
    tokenizer.save_pretrained(OUTPUT_DIR)
    
    print(f"Training completed! Adapter saved to {OUTPUT_DIR}")

if __name__ == "__main__":
    main()
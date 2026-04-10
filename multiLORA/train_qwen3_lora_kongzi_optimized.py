import os
import json
import torch
from torch.utils.data import Dataset
from transformers import (
    AutoTokenizer, 
    AutoModelForCausalLM, 
    TrainingArguments, 
    Trainer
)
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
import argparse

class KongziDataset(Dataset):
    def __init__(self, file_path, tokenizer, max_length=512):
        self.tokenizer = tokenizer
        self.max_length = max_length
        self.data = []
        
        # Load dataset with robust error handling
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                    
                try:
                    item = json.loads(line)
                    
                    # Handle 孔子 dataset format: {"messages": [{"role": "system", ...}, {"role": "user", ...}, {"role": "assistant", ...}]}
                    if "messages" in item:
                        messages = item["messages"]
                        # Ensure we have at least system + user + assistant
                        if len(messages) >= 3:
                            system_msg = messages[0].get("content", "") if messages[0].get("role") == "system" else ""
                            user_msg = messages[1].get("content", "") if messages[1].get("role") == "user" else ""
                            assistant_msg = messages[2].get("content", "") if messages[2].get("role") == "assistant" else ""
                            if system_msg and user_msg and assistant_msg:
                                self.data.append((system_msg, user_msg, assistant_msg))
                    elif "conversations" in item:
                        # Alternative format (like 李白 dataset)
                        messages = item["conversations"]
                        if len(messages) >= 2:
                            user_msg = messages[0].get("content", "") if messages[0].get("role") == "user" else ""
                            assistant_msg = messages[1].get("content", "") if messages[1].get("role") == "assistant" else ""
                            if user_msg and assistant_msg:
                                # Use empty system message for consistency
                                self.data.append(("", user_msg, assistant_msg))
                    elif "instruction" in item and "output" in item:
                        # Format: {"instruction": "...", "output": "..."}
                        self.data.append(("", item["instruction"], item["output"]))
                        
                except (json.JSONDecodeError, KeyError) as e:
                    print(f"Skipping malformed line {line_num}: {e}")
                    continue
        
        print(f"Loaded {len(self.data)} valid samples from {file_path}")

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        system_msg, user_input, assistant_output = self.data[idx]
        
        # Apply Qwen3 chat template with system message
        if system_msg:
            messages = [
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_input},
                {"role": "assistant", "content": assistant_output}
            ]
        else:
            messages = [
                {"role": "user", "content": user_input},
                {"role": "assistant", "content": assistant_output}
            ]
        
        text = self.tokenizer.apply_chat_template(
            messages, 
            tokenize=False, 
            add_generation_prompt=False
        )
        
        # Tokenize with truncation only (no padding - handled by collator)
        encodings = self.tokenizer(
            text,
            truncation=True,
            max_length=self.max_length,
            padding=False,
            return_tensors=None
        )
        
        input_ids = encodings['input_ids']
        attention_mask = encodings['attention_mask']
        labels = input_ids.copy()
        
        return {
            'input_ids': input_ids,
            'attention_mask': attention_mask,
            'labels': labels
        }

# Custom data collator for memory efficiency
def custom_data_collator(features):
    max_len = max(len(feature['input_ids']) for feature in features)
    padded_features = []
    
    for feature in features:
        input_ids = feature['input_ids']
        attention_mask = feature['attention_mask']
        labels = feature['labels']
        
        pad_len = max_len - len(input_ids)
        padded_input_ids = input_ids + [0] * pad_len
        padded_attention_mask = attention_mask + [0] * pad_len
        padded_labels = labels + [-100] * pad_len
        
        padded_features.append({
            'input_ids': torch.tensor(padded_input_ids, dtype=torch.long),
            'attention_mask': torch.tensor(padded_attention_mask, dtype=torch.long),
            'labels': torch.tensor(padded_labels, dtype=torch.long)
        })
    
    batch = {
        'input_ids': torch.stack([f['input_ids'] for f in padded_features]),
        'attention_mask': torch.stack([f['attention_mask'] for f in padded_features]),
        'labels': torch.stack([f['labels'] for f in padded_features])
    }
    
    return batch

def main():
    parser = argparse.ArgumentParser(description="Memory-optimized LoRA training for Qwen3-4B - 孔子")
    parser.add_argument("--model_name", type=str, default="/root/autodl-tmp/models/qwen/Qwen3-4B", help="Path to Qwen3-4B model")
    parser.add_argument("--dataset_path", type=str, default="/root/autodl-tmp/Celebrity/multiLORA/kongzi/kongzi_all_datasets_merged.jsonl", help="Path to 孔子 dataset")
    parser.add_argument("--output_dir", type=str, default="./qwen3-kongzi-lora", help="Output directory")
    parser.add_argument("--batch_size", type=int, default=1, help="Reduced batch size for memory efficiency")
    parser.add_argument("--gradient_accumulation_steps", type=int, default=16, help="Increased gradient accumulation")
    parser.add_argument("--learning_rate", type=float, default=2e-4, help="Learning rate")
    parser.add_argument("--num_train_epochs", type=int, default=3, help="Number of epochs")
    parser.add_argument("--max_length", type=int, default=512, help="Max sequence length")
    parser.add_argument("--lora_r", type=int, default=64, help="LoRA rank")
    parser.add_argument("--lora_alpha", type=int, default=128, help="LoRA alpha")
    parser.add_argument("--dry_run", action="store_true", help="Dry run test")
    
    args = parser.parse_args()
    
    os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'
    
    print("Loading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(args.model_name, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    
    print("Loading dataset...")
    train_dataset = KongziDataset(args.dataset_path, tokenizer, max_length=args.max_length)
    
    if args.dry_run:
        print("Dry run completed successfully!")
        return
    
    print("Loading model with memory optimization...")
    # Load model with memory-efficient settings
    model = AutoModelForCausalLM.from_pretrained(
        args.model_name,
        dtype=torch.bfloat16,
        device_map="auto",
        trust_remote_code=True,
        use_cache=False  # Disable cache for training
    )
    
    # Enable gradient checkpointing to save memory
    model.gradient_checkpointing_enable()
    
    # Prepare model for LoRA training
    model = prepare_model_for_kbit_training(model)
    
    # Configure LoRA
    lora_config = LoraConfig(
        r=args.lora_r,
        lora_alpha=args.lora_alpha,
        target_modules=[
            "q_proj", "k_proj", "v_proj", "o_proj",
            "gate_proj", "up_proj", "down_proj"
        ],
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM"
    )
    
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()
    
    # Memory-optimized training arguments
    training_args = TrainingArguments(
        output_dir=args.output_dir,
        per_device_train_batch_size=args.batch_size,  # Reduced to 1
        gradient_accumulation_steps=args.gradient_accumulation_steps,  # Increased to 16
        learning_rate=args.learning_rate,
        num_train_epochs=args.num_train_epochs,
        logging_steps=10,
        save_strategy="epoch",
        save_total_limit=2,
        fp16=False,
        bf16=True,
        dataloader_num_workers=0,  # Reduce workers to save memory
        remove_unused_columns=False,
        report_to="none",
        optim="adamw_torch",
        # Additional memory saving options
        gradient_checkpointing=True,
        ddp_find_unused_parameters=False,
        # Reduce logging to save memory
        logging_first_step=True,
    )
    
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        data_collator=custom_data_collator
    )
    
    print("Starting memory-optimized 孔子 training...")
    trainer.train()
    
    print("Saving final 孔子 model...")
    trainer.save_model()
    tokenizer.save_pretrained(args.output_dir)
    
    print(f"孔子 LoRA微调 completed! Model saved to {args.output_dir}")

if __name__ == "__main__":
    main()
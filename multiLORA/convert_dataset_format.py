#!/usr/bin/env python3
"""
Convert dataset from conversations format to instruction/output format.
This addresses the KeyError: 'role' issue by providing a compatible format.
"""

import json
import sys
from pathlib import Path

def convert_conversations_to_instruction_output(input_file, output_file):
    """
    Convert JSONL file from conversations format to instruction/output format.
    
    Input format: {"conversations": [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]}
    Output format: {"instruction": "...", "input": "", "output": "..."}
    """
    converted_count = 0
    error_count = 0
    
    with open(input_file, 'r', encoding='utf-8') as infile, \
         open(output_file, 'w', encoding='utf-8') as outfile:
        
        for line_num, line in enumerate(infile, 1):
            try:
                # Parse the original line
                original_data = json.loads(line.strip())
                
                # Check if it has conversations field
                if "conversations" not in original_data:
                    print(f"Warning: Line {line_num} missing 'conversations' field, skipping")
                    error_count += 1
                    continue
                
                conversations = original_data["conversations"]
                
                # Validate conversations structure
                if len(conversations) < 2:
                    print(f"Warning: Line {line_num} has less than 2 messages, skipping")
                    error_count += 1
                    continue
                
                # Find the first user message and first assistant message after it
                user_content = ""
                assistant_content = ""
                
                for msg in conversations:
                    if "role" in msg and "content" in msg:
                        if msg["role"] == "user" and not user_content:
                            user_content = msg["content"]
                        elif msg["role"] == "assistant" and user_content and not assistant_content:
                            assistant_content = msg["content"]
                            break
                
                if not user_content or not assistant_content:
                    print(f"Warning: Line {line_num} missing user/assistant pair, skipping")
                    error_count += 1
                    continue
                
                # Create the converted format
                converted_data = {
                    "instruction": user_content,
                    "input": "",  # Empty input field (commonly used for context)
                    "output": assistant_content
                }
                
                outfile.write(json.dumps(converted_data, ensure_ascii=False) + '\n')
                converted_count += 1
                
            except json.JSONDecodeError as e:
                print(f"Error parsing JSON on line {line_num}: {e}")
                error_count += 1
            except Exception as e:
                print(f"Unexpected error on line {line_num}: {e}")
                error_count += 1
    
    print(f"Conversion complete!")
    print(f"Converted: {converted_count} records")
    print(f"Errors: {error_count} records")
    return converted_count

if __name__ == "__main__":
    input_path = "/root/autodl-tmp/Celebrity/multiLORA/Libai/libai_all_datasets_merged.jsonl"
    output_path = "/root/autodl-tmp/Celebrity/multiLORA/Libai/libai_all_datasets_converted.jsonl"
    
    if len(sys.argv) >= 3:
        input_path = sys.argv[1]
        output_path = sys.argv[2]
    elif len(sys.argv) == 2:
        input_path = sys.argv[1]
    
    print(f"Converting dataset:")
    print(f"Input: {input_path}")
    print(f"Output: {output_path}")
    
    convert_conversations_to_instruction_output(input_path, output_path)
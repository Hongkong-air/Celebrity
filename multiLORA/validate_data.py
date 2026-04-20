#!/usr/bin/env python3
"""
Data validation script to verify JSONL format compliance for LoRA training.
"""

import json
import sys

def validate_jsonl(file_path, expected_system_prompt_keywords):
    """Validate JSONL file format and content."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        valid_count = 0
        for i, line in enumerate(lines):
            line_num = i + 1
            try:
                # Parse JSON
                data = json.loads(line.strip())
                
                # Check required structure
                if 'messages' not in data:
                    print(f"Line {line_num}: Missing 'messages' field")
                    continue
                
                messages = data['messages']
                if not isinstance(messages, list) or len(messages) != 3:
                    print(f"Line {line_num}: Expected 3 messages (system, user, assistant), got {len(messages)}")
                    continue
                
                # Check message roles
                roles = [msg.get('role') for msg in messages]
                expected_roles = ['system', 'user', 'assistant']
                if roles != expected_roles:
                    print(f"Line {line_num}: Expected roles {expected_roles}, got {roles}")
                    continue
                
                # Check system prompt contains expected keywords
                system_content = messages[0].get('content', '')
                if not any(keyword in system_content for keyword in expected_system_prompt_keywords):
                    print(f"Line {line_num}: System prompt doesn't contain expected keywords")
                    continue
                
                # Check user and assistant have content
                if not messages[1].get('content') or not messages[2].get('content'):
                    print(f"Line {line_num}: User or assistant content is empty")
                    continue
                
                valid_count += 1
                
            except json.JSONDecodeError as e:
                print(f"Line {line_num}: Invalid JSON - {e}")
                continue
        
        print(f"\nValidation complete for {file_path}")
        print(f"Total lines: {len(lines)}")
        print(f"Valid entries: {valid_count}")
        print(f"Invalid entries: {len(lines) - valid_count}")
        
        return valid_count
        
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        return 0
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return 0

def main():
    # Validate Confucius data
    kongzi_keywords = ['孔子', '名丘', '字仲尼', '春秋', '鲁国', '温和', '严谨', '《诗》', '《书》']
    kongzi_valid = validate_jsonl('/root/data/kongzi_train.jsonl', kongzi_keywords)
    
    print("\n" + "="*50 + "\n")
    
    # Validate Li Bai data  
    libai_keywords = ['李白', '字太白', '青莲居士', '诗仙', '豪放', '不羁', '嗜酒', '浪漫', '想象力']
    libai_valid = validate_jsonl('/root/data/libai_train.jsonl', libai_keywords)
    
    # Check minimum requirements
    print(f"\nMinimum requirements check:")
    print(f"Confucius: {kongzi_valid}/800 (minimum required)")
    print(f"Li Bai: {libai_valid}/500 (minimum required)")
    
    if kongzi_valid >= 800 and libai_valid >= 500:
        print("\n✅ All requirements met! Ready for training.")
    else:
        print(f"\n⚠️  Warning: Minimum requirements not met.")
        if kongzi_valid < 800:
            print(f"   - Confucius needs {800 - kongzi_valid} more entries")
        if libai_valid < 500:
            print(f"   - Li Bai needs {500 - libai_valid} more entries")

if __name__ == "__main__":
    main()
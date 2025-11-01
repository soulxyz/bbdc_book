#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
调试 .env 文件解析问题
"""

import os
from env_loader import get_env_file_paths, check_env_file_exists

def debug_env_file():
    """调试 .env 文件内容"""
    print("\n" + "=" * 80)
    print("🔍 .env 文件调试工具")
    print("=" * 80)
    
    # 查找 .env 文件
    exists, found_path, _ = check_env_file_exists()
    
    if not exists:
        print("❌ 未找到 .env 文件")
        return
    
    print(f"\n✅ 找到 .env 文件: {found_path}\n")
    
    # 读取文件内容
    try:
        with open(found_path, 'rb') as f:
            raw_content = f.read()
        
        # 检查 BOM
        if raw_content.startswith(b'\xef\xbb\xbf'):
            print("⚠️  检测到 UTF-8 BOM（可能导致解析问题）")
        
        # 按行读取并分析
        print("\n" + "=" * 80)
        print("📄 文件内容分析（每一行）")
        print("=" * 80)
        
        with open(found_path, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f, 1):
                # 显示原始内容
                line_repr = repr(line)
                print(f"\n行 {i}: {line_repr}")
                
                # 分析这一行
                stripped = line.strip()
                if not stripped:
                    print("  → 空行")
                elif stripped.startswith('#'):
                    print("  → 注释行")
                elif '=' in stripped:
                    key, value = stripped.split('=', 1)
                    key = key.strip()
                    value_stripped = value.strip().strip('"').strip("'")
                    
                    print(f"  → 键值对:")
                    print(f"     Key: '{key}' (长度: {len(key)})")
                    print(f"     Value: '{value_stripped[:50]}...' (长度: {len(value_stripped)})")
                    
                    # 检查特殊字符
                    if '\r' in line:
                        print("  ⚠️  包含 \\r (回车符)")
                    if '\n' in line:
                        print("  ✓ 包含 \\n (换行符)")
                    
                    # 检查是否是 SILICONFLOW_API_KEY
                    if key == 'SILICONFLOW_API_KEY':
                        if value_stripped:
                            print(f"  ✅ SILICONFLOW_API_KEY 有值")
                        else:
                            print(f"  ❌ SILICONFLOW_API_KEY 值为空！")
                            print(f"     原始值: {repr(value)}")
                else:
                    print(f"  ⚠️  无法解析的行")
        
        print("\n" + "=" * 80)
        print("📊 解析结果测试")
        print("=" * 80)
        
        # 测试解析
        from env_loader import load_env_variable
        
        test_keys = [
            'SILICONFLOW_API_KEY',
            'SILICONFLOW_MODEL', 
            'SILICONFLOW_BASE_URL',
            'MINERU_API_TOKEN'
        ]
        
        for key in test_keys:
            value = load_env_variable(key)
            if value:
                print(f"✅ {key}: {value[:20]}... (长度: {len(value)})")
            else:
                print(f"❌ {key}: 未加载")
        
    except Exception as e:
        print(f"❌ 读取文件失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    debug_env_file()



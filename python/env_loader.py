#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
统一的环境变量加载模块
用于从 .env 文件或环境变量中加载配置
"""

import os
import sys


def load_env_variable(key: str, default: str = "") -> str:
    """
    统一加载环境变量
    优先级：环境变量 > .env 文件 > 默认值
    
    参数:
        key: 环境变量名
        default: 默认值
    
    返回:
        str: 环境变量的值
    """
    # 1. 优先从环境变量读取
    value = os.environ.get(key)
    if value:
        return value
    
    # 2. 尝试从多个可能的 .env 文件位置读取
    possible_paths = get_env_file_paths()
    
    for env_file in possible_paths:
        if os.path.exists(env_file):
            try:
                value = _read_key_from_file(env_file, key)
                if value:
                    return value
            except Exception:
                continue
    
    # 3. 返回默认值
    return default


def get_env_file_paths():
    """
    获取所有可能的 .env 文件路径
    
    返回:
        list: .env 文件路径列表
    """
    possible_paths = []
    
    # 1. 当前工作目录
    possible_paths.append(os.path.join(os.getcwd(), '.env'))
    
    # 2. exe 所在目录（打包后）
    if getattr(sys, 'frozen', False):
        # 打包后的 exe
        exe_dir = os.path.dirname(sys.executable)
        possible_paths.append(os.path.join(exe_dir, '.env'))
    else:
        # 开发环境：脚本所在目录
        script_dir = os.path.dirname(os.path.abspath(__file__))
        possible_paths.append(os.path.join(script_dir, '.env'))
    
    # 去重（保持顺序）
    seen = set()
    unique_paths = []
    for path in possible_paths:
        normalized = os.path.normpath(path)
        if normalized not in seen:
            seen.add(normalized)
            unique_paths.append(path)
    
    return unique_paths


def _read_key_from_file(env_file: str, key: str) -> str:
    """
    从 .env 文件中读取指定的键值
    
    参数:
        env_file: .env 文件路径
        key: 要读取的键名
    
    返回:
        str: 键对应的值，如果不存在返回空字符串
    """
    try:
        with open(env_file, 'r', encoding='utf-8-sig') as f:  # utf-8-sig 自动处理 BOM
            for line in f:
                line = line.strip()
                # 跳过空行和注释
                if not line or line.startswith('#'):
                    continue
                # 解析键值对
                if '=' in line:
                    k, v = line.split('=', 1)
                    k = k.strip()
                    v = v.strip().strip('"').strip("'")
                    if k == key and v:
                        return v
    except Exception:
        pass
    
    return ""


def check_env_file_exists() -> tuple:
    """
    检查 .env 文件是否存在
    
    返回:
        tuple: (是否存在, 文件路径, 所有搜索路径)
    """
    possible_paths = get_env_file_paths()
    
    for path in possible_paths:
        if os.path.exists(path):
            return (True, path, possible_paths)
    
    return (False, None, possible_paths)


def print_env_file_status():
    """
    打印 .env 文件的状态信息（用于调试）
    """
    exists, found_path, all_paths = check_env_file_exists()
    
    print("\n" + "=" * 60)
    print("🔍 .env 文件查找状态")
    print("=" * 60)
    
    if exists:
        print(f"✅ 找到 .env 文件:")
        print(f"   {found_path}")
    else:
        print("❌ 未找到 .env 文件")
        print("\n已搜索以下位置:")
        for i, path in enumerate(all_paths, 1):
            print(f"   {i}. {path}")
    
    print("=" * 60 + "\n")


def load_all_env_variables():
    """
    加载所有环境变量到一个字典
    
    返回:
        dict: 所有环境变量
    """
    env_vars = {}
    
    # 常用的环境变量键
    common_keys = [
        'MINERU_API_TOKEN',
        'SILICONFLOW_API_KEY',
        'SILICONFLOW_BASE_URL',
        'SILICONFLOW_MODEL'
    ]
    
    for key in common_keys:
        value = load_env_variable(key)
        if value:
            env_vars[key] = value
    
    return env_vars


if __name__ == '__main__':
    # 测试代码
    print("测试环境变量加载模块\n")
    
    # 检查 .env 文件状态
    print_env_file_status()
    
    # 加载所有环境变量
    env_vars = load_all_env_variables()
    
    if env_vars:
        print("✅ 已加载的环境变量:")
        for key, value in env_vars.items():
            # 隐藏敏感信息
            masked_value = value[:10] + "..." if len(value) > 10 else value
            print(f"   {key}: {masked_value}")
    else:
        print("⚠️  未加载任何环境变量")
    
    print()



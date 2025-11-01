#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
GUI演示脚本
展示不背单词单词本制作工具的主要功能
"""

import os
import sys
from pathlib import Path

def print_banner():
    """打印程序横幅"""
    print("\n" + "="*60)
    print("    📚 不背单词单词本制作工具 - GUI版本演示")
    print("="*60)
    print()

def check_environment():
    """检查运行环境"""
    print("🔍 检查运行环境...")
    
    # 检查Python版本
    python_version = sys.version_info
    if python_version >= (3, 6):
        print(f"✅ Python版本: {python_version.major}.{python_version.minor}.{python_version.micro}")
    else:
        print(f"❌ Python版本过低: {python_version.major}.{python_version.minor}.{python_version.micro}")
        print("   需要Python 3.6或更高版本")
        return False
    
    # 检查tkinter
    try:
        import tkinter
        print("✅ tkinter模块可用")
    except ImportError:
        print("❌ tkinter模块不可用")
        print("   请安装tkinter支持")
        return False
    
    # 检查依赖包
    required_packages = ['requests', 'beautifulsoup4']
    missing_packages = []
    
    for package in required_packages:
        try:
            if package == 'beautifulsoup4':
                import bs4
            else:
                __import__(package)
            print(f"✅ {package} 已安装")
        except ImportError:
            print(f"❌ {package} 未安装")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n⚠️  缺少依赖包: {', '.join(missing_packages)}")
        print("   请运行: pip install -r requirements.txt")
        return False
    
    return True

def check_files():
    """检查必要文件"""
    print("\n📁 检查文件...")
    
    required_files = [
        'gui_app.py',
        'extract_words.py', 
        'bbdc_word_checker.py',
        'requirements.txt'
    ]
    
    missing_files = []
    for file in required_files:
        if os.path.exists(file):
            print(f"✅ {file}")
        else:
            print(f"❌ {file} 不存在")
            missing_files.append(file)
    
    if missing_files:
        print(f"\n⚠️  缺少文件: {', '.join(missing_files)}")
        return False
    
    return True

def show_example_files():
    """显示示例文件"""
    print("\n📋 示例文件:")
    
    example_files = [
        '南山阅读营·题干生词背诵本（英二）2010-2025_MinerU__20251015122204.md',
        '南山阅读营10-25题干生词英二.txt',
        '单词检查报告.txt'
    ]
    
    for file in example_files:
        if os.path.exists(file):
            size = os.path.getsize(file)
            print(f"✅ {file} ({size} 字节)")
        else:
            print(f"❌ {file} 不存在")

def show_usage():
    """显示使用说明"""
    print("\n🚀 使用方法:")
    print("1. 启动GUI版本:")
    print("   双击 运行GUI.bat")
    print("   或运行: python gui_app.py")
    print()
    print("2. 使用命令行版本:")
    print("   python extract_words.py")
    print("   python bbdc_word_checker.py")
    print()
    print("3. 查看详细说明:")
    print("   阅读 README.md")
    print("   阅读 GUI使用指南.md")

def main():
    """主函数"""
    print_banner()
    
    # 检查环境
    if not check_environment():
        print("\n❌ 环境检查失败，请解决上述问题后重试")
        return
    
    # 检查文件
    if not check_files():
        print("\n❌ 文件检查失败，请确保所有必要文件存在")
        return
    
    print("\n✅ 环境检查通过！")
    
    # 显示示例文件
    show_example_files()
    
    # 显示使用方法
    show_usage()
    
    print("\n" + "="*60)
    print("🎉 准备就绪！现在可以启动GUI程序了")
    print("="*60)
    
    # 询问是否启动GUI
    try:
        choice = input("\n是否现在启动GUI程序？(y/n): ").strip().lower()
        if choice == 'y':
            print("\n🚀 正在启动GUI程序...")
            os.system("python gui_app.py")
        else:
            print("\n👋 稍后可以手动启动GUI程序")
    except KeyboardInterrupt:
        print("\n\n👋 程序已退出")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 程序已退出")

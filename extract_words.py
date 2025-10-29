#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
从markdown格式的单词本中提取单词
"""

import re
import os
import sys
from bs4 import BeautifulSoup
import argparse
from pathlib import Path
import requests
import json
import time


class BBDCWordChecker:
    """不背单词词书核对类"""
    
    def __init__(self):
        self.submit_url = "https://bbdc.cn/lexis/book/file/submit"
        self.session = requests.Session()
        
        # 设置请求头
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36 Edg/141.0.0.0',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6,zh-TW;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            'Origin': 'https://bbdc.cn',
            'Referer': 'https://bbdc.cn/lexis_book_index',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'X-Requested-With': 'XMLHttpRequest',
            'Connection': 'keep-alive'
        })
    
    def upload_word_file(self, file_path, filename=None):
        """上传单词文件进行核对"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        if not filename:
            filename = os.path.basename(file_path)
        
        try:
            with open(file_path, 'rb') as f:
                files = {
                    'file': (filename, f, 'text/plain')
                }
                
                response = self.session.post(
                    self.submit_url,
                    files=files,
                    timeout=30
                )
            
            if response.status_code == 200:
                try:
                    return response.json()
                except json.JSONDecodeError:
                    return {"error": "Invalid JSON response", "content": response.text}
            else:
                return {"error": f"HTTP {response.status_code}", "content": response.text}
                
        except requests.exceptions.Timeout:
            return {"error": "Request timeout"}
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}
    
    def parse_result(self, result):
        """解析核对结果"""
        if "error" in result:
            return result
        
        try:
            data_body = result.get("data_body", {})
            unknow_list = data_body.get("unknowList", "")
            know_list = data_body.get("knowList", "")
            
            # 分割单词列表
            unrecognized_words = [word.strip() for word in unknow_list.split(',') if word.strip()]
            recognized_words = [word.strip() for word in know_list.split(',') if word.strip()]
            
            return {
                "unrecognized_words": unrecognized_words,
                "recognized_words": recognized_words,
                "unrecognized_count": len(unrecognized_words),
                "recognized_count": len(recognized_words),
                "total_count": len(unrecognized_words) + len(recognized_words)
            }
        except Exception as e:
            return {"error": f"解析结果失败: {e}"}


def find_word_info_in_markdown(file_path, word):
    """
    在markdown文件中查找单词的行号和含义
    
    参数:
        file_path: markdown文件路径
        word: 要查找的单词
    
    返回:
        dict: 包含行号和含义的字典
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        soup = BeautifulSoup(''.join(lines), 'html.parser')
        tables = soup.find_all('table')
        
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cols = row.find_all('td')
                if len(cols) >= 3:
                    word_text = cols[1].get_text(strip=True)
                    if word_text.lower() == word.lower():
                        meaning = cols[2].get_text(strip=True)
                        # 查找原始行号
                        row_html = str(row)
                        for i, line in enumerate(lines):
                            if row_html in line:
                                return {
                                    'line_number': i + 1,
                                    'meaning': meaning,
                                    'word': word_text
                                }
        
        return None
    except Exception as e:
        print(f"查找单词 {word} 信息时出错: {e}")
        return None


def check_words_with_bbdc(file_path, words_list, original_md_file):
    """
    使用不背单词核对单词列表
    
    参数:
        file_path: 临时单词文件路径
        words_list: 单词列表
        original_md_file: 原始markdown文件路径
    
    返回:
        dict: 核对结果
    """
    print("\n🔄 正在使用不背单词核对单词...")
    
    checker = BBDCWordChecker()
    result = checker.upload_word_file(file_path)
    
    if "error" in result:
        print(f"❌ 核对失败: {result['error']}")
        return None
    
    parsed_result = checker.parse_result(result)
    
    if "error" in parsed_result:
        print(f"❌ 解析结果失败: {parsed_result['error']}")
        return None
    
    # 为识别不成功的单词查找详细信息
    unrecognized_details = []
    for word in parsed_result['unrecognized_words']:
        word_info = find_word_info_in_markdown(original_md_file, word)
        if word_info:
            unrecognized_details.append(word_info)
        else:
            unrecognized_details.append({
                'line_number': '未知',
                'meaning': '未找到',
                'word': word
            })
    
    parsed_result['unrecognized_details'] = unrecognized_details
    parsed_result['original_file'] = original_md_file
    return parsed_result


def extract_words_from_markdown(file_path, output_file=None, include_phrases=False):
    """
    从markdown文件中提取单词
    
    参数:
        file_path: markdown文件路径
        output_file: 输出文件路径（可选）
        include_phrases: 是否包含短语（默认False）
    
    返回:
        words_list: 提取的单词列表
    """
    # 读取文件
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 使用BeautifulSoup解析HTML表格
    soup = BeautifulSoup(content, 'html.parser')
    
    # 查找所有表格
    tables = soup.find_all('table')
    
    words_data = []  # 存储单词及其信息
    phrases_data = []  # 存储短语及其信息
    
    for table in tables:
        rows = table.find_all('tr')
        
        # 跳过表头和空行
        is_phrase_table = False
        for row in rows:
            cols = row.find_all('td')
            
            # 至少需要3列：序号、单词/短语、词义
            if len(cols) >= 3:
                # 检查是否是表头
                col1_text = cols[0].get_text(strip=True)
                col2_text = cols[1].get_text(strip=True)
                
                # 跳过表头行和补充区
                if col1_text in ['NO.', ''] or '补充区' in col1_text:
                    continue
                
                # 判断是短语表还是单词表
                if col2_text in ['单词', '短语']:
                    if col2_text == '短语':
                        is_phrase_table = True
                    continue
                
                # 提取数据
                try:
                    number = col1_text
                    word_or_phrase = col2_text
                    meaning = cols[2].get_text(strip=True)
                    
                    # 跳过空行或无效数据
                    if not word_or_phrase or not number.isdigit():
                        continue
                    
                    # 判断是单词还是短语（通过空格判断）
                    if ' ' in word_or_phrase or '-' in word_or_phrase:
                        phrases_data.append({
                            'number': number,
                            'phrase': word_or_phrase,
                            'meaning': meaning
                        })
                    else:
                        words_data.append({
                            'number': number,
                            'word': word_or_phrase,
                            'meaning': meaning
                        })
                except:
                    continue
    
    # 打印统计信息
    print(f"提取到 {len(words_data)} 个单词")
    print(f"提取到 {len(phrases_data)} 个短语")
    
    # 保存结果
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            # 写入单词
            f.write("=" * 50 + "\n")
            f.write("单词列表\n")
            f.write("=" * 50 + "\n\n")
            for item in words_data:
                f.write(f"{item['number']}. {item['word']}\t{item['meaning']}\n")
            
            if include_phrases:
                f.write("\n" + "=" * 50 + "\n")
                f.write("短语列表\n")
                f.write("=" * 50 + "\n\n")
                for item in phrases_data:
                    f.write(f"{item['number']}. {item['phrase']}\t{item['meaning']}\n")
        
        print(f"\n结果已保存到: {output_file}")
    
    # 返回结果
    if include_phrases:
        return words_data, phrases_data
    else:
        return words_data


def extract_words_only(file_path, output_file=None, unique=True, auto_check=True):
    """
    仅提取单词（不包含词义），每行一个单词
    
    参数:
        file_path: markdown文件路径
        output_file: 输出文件路径（可选）
        unique: 是否去重（默认True）
        auto_check: 是否自动进行不背单词核对（默认True）
    
    返回:
        words_list: 单词列表
    """
    words_data = extract_words_from_markdown(file_path)
    
    # 提取所有单词
    words_list = [item['word'] for item in words_data]
    
    # 去重（保持顺序）
    if unique:
        seen = set()
        unique_words = []
        for word in words_list:
            if word.lower() not in seen:
                seen.add(word.lower())
                unique_words.append(word)
        words_list = unique_words
        print(f"去重后剩余 {len(words_list)} 个单词")
    
    # 保存结果
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            for word in words_list:
                f.write(word + '\n')
        print(f"结果已保存到: {output_file}")
        
        # 自动进行不背单词核对
        if auto_check and len(words_list) > 0:
            check_result = check_words_with_bbdc(output_file, words_list, file_path)
            if check_result:
                print_check_result(check_result, output_file)
    
    return words_list


def print_check_result(check_result, output_file):
    """
    打印不背单词核对结果
    
    参数:
        check_result: 核对结果
        output_file: 输出文件路径
    """
    print("\n" + "=" * 60)
    print("📊 不背单词词书核对结果")
    print("=" * 60)
    
    print(f"\n📈 统计信息:")
    print(f"  总单词数: {check_result['total_count']}")
    print(f"  识别成功: {check_result['recognized_count']}")
    print(f"  识别不成功: {check_result['unrecognized_count']}")
    print(f"  识别成功率: {check_result['recognized_count']/check_result['total_count']*100:.1f}%")
    
    # 显示识别成功的单词（前10个）
    if check_result['recognized_words']:
        print(f"\n✅ 识别成功的单词（前10个）:")
        for i, word in enumerate(check_result['recognized_words'][:10], 1):
            print(f"  {i:2d}. {word}")
        
        if len(check_result['recognized_words']) > 10:
            print(f"  ... 还有 {len(check_result['recognized_words']) - 10} 个识别成功的单词")
    
    # 显示识别不成功的单词（详细信息）
    if check_result['unrecognized_details']:
        source_file = os.path.basename(check_result.get('original_file', '未知文件'))
        word_file = os.path.basename(output_file)
        print(f"\n\n检查这些单词是否有误,你可以通过标明的行数直接阅读该行前后以确定其位置，不用阅读整个文件,如果发现错别字等情况、请询问我得到同意后，对单词文本文件进行修正。\n 识别不成功的单词（详细信息）,源文件【{source_file}】，单词文本文件【{word_file}】:")
        for i, detail in enumerate(check_result['unrecognized_details'], 1):
            print(f"  {i:2d}. {detail['word']:<15} 第{detail['line_number']}行  {detail['meaning']}")
    
    # 询问是否保存详细结果
    save_choice = input("\n💾 是否保存详细结果到文件？(y/n): ").strip().lower()
    if save_choice == 'y':
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        detail_output = f"bbdc_check_detail_{timestamp}.txt"
        
        try:
            with open(detail_output, 'w', encoding='utf-8') as f:
                f.write("=" * 60 + "\n")
                f.write("不背单词词书核对详细结果\n")
                f.write("=" * 60 + "\n\n")
                
                f.write(f"📊 统计信息:\n")
                f.write(f"  总单词数: {check_result['total_count']}\n")
                f.write(f"  识别成功: {check_result['recognized_count']}\n")
                f.write(f"  识别不成功: {check_result['unrecognized_count']}\n")
                f.write(f"  识别成功率: {check_result['recognized_count']/check_result['total_count']*100:.1f}%\n\n")
                
                f.write("=" * 30 + " 识别成功的单词 " + "=" * 30 + "\n")
                for i, word in enumerate(check_result['recognized_words'], 1):
                    f.write(f"{i:3d}. {word}\n")
                
                f.write("\n" + "=" * 30 + " 识别不成功的单词（详细信息） " + "=" * 30 + "\n")
                f.write(f"源文件: {os.path.basename(check_result.get('original_file', '未知文件'))}\n")
                f.write(f"单词文本文件: {os.path.basename(output_file)}\n\n")
                for i, detail in enumerate(check_result['unrecognized_details'], 1):
                    f.write(f"{i:3d}. {detail['word']:<20} 第{detail['line_number']}行  {detail['meaning']}\n")
            
            print(f"💾 详细结果已保存到: {detail_output}")
            
        except Exception as e:
            print(f"❌ 保存详细结果失败: {e}")


def print_header():
    """打印程序头部"""
    print("\n" + "=" * 60)
    print("           📚 单词提取工具 - Word Extractor")
    print("=" * 60)
    print()


def print_menu():
    """打印主菜单"""
    print("\n请选择操作模式：")
    print("  [1] 提取单词（仅单词，每行一个）+ 自动核对")
    print("  [2] 提取单词（包含词义）")
    print("  [3] 提取单词和短语（包含词义）")
    print("  [4] 批量处理多个文件")
    print("  [0] 退出")
    print()


def get_choice(prompt, valid_choices):
    """获取用户选择"""
    while True:
        choice = input(prompt).strip()
        if choice in valid_choices:
            return choice
        print(f"❌ 无效的选择，请输入 {', '.join(valid_choices)} 中的一个")


def get_input_file():
    """获取输入文件路径"""
    print("\n📂 请输入文件路径：")
    print("  提示：可以直接拖拽文件到此窗口，或输入完整路径")
    
    while True:
        file_path = input("文件路径: ").strip().strip('"').strip("'")
        
        if not file_path:
            print("❌ 路径不能为空，请重新输入")
            continue
        
        if not os.path.exists(file_path):
            print(f"❌ 文件不存在: {file_path}")
            retry = input("是否重新输入？(y/n): ").strip().lower()
            if retry != 'y':
                return None
            continue
        
        if not file_path.endswith('.md'):
            print("⚠️  警告：文件不是 .md 格式，是否继续？(y/n): ", end='')
            if input().strip().lower() != 'y':
                continue
        
        return file_path


def get_output_file(default_name):
    """获取输出文件路径"""
    print(f"\n💾 输出文件名（直接回车使用默认: {default_name}）: ", end='')
    output = input().strip().strip('"').strip("'")
    
    if not output:
        return default_name
    
    # 确保有文件扩展名
    if not output.endswith('.txt'):
        output += '.txt'
    
    # 如果文件已存在，询问是否覆盖
    if os.path.exists(output):
        print(f"⚠️  文件 {output} 已存在，是否覆盖？(y/n): ", end='')
        if input().strip().lower() != 'y':
            return get_output_file(default_name)
    
    return output


def preview_results(words_data, phrases_data=None, limit=10):
    """预览提取结果"""
    print("\n" + "=" * 60)
    print("📋 提取结果预览（前 {} 项）".format(limit))
    print("=" * 60)
    
    if words_data:
        print("\n【单词】")
        for i, item in enumerate(words_data[:limit], 1):
            if isinstance(item, dict):
                word = item.get('word', '')
                meaning = item.get('meaning', '')
                print(f"  {i}. {word:<20} {meaning}")
            else:
                print(f"  {i}. {item}")
        
        if len(words_data) > limit:
            print(f"  ... 还有 {len(words_data) - limit} 个单词未显示")
    
    if phrases_data:
        print("\n【短语】")
        for i, item in enumerate(phrases_data[:limit], 1):
            phrase = item.get('phrase', '')
            meaning = item.get('meaning', '')
            print(f"  {i}. {phrase:<30} {meaning}")
        
        if len(phrases_data) > limit:
            print(f"  ... 还有 {len(phrases_data) - limit} 个短语未显示")
    
    print()


def find_markdown_files(directory='.'):
    """查找当前目录下的所有markdown文件"""
    md_files = list(Path(directory).glob('*.md'))
    return [str(f) for f in md_files]


def batch_process():
    """批量处理多个文件"""
    print("\n📁 批量处理模式")
    print("正在搜索当前目录下的 .md 文件...")
    
    md_files = find_markdown_files()
    
    if not md_files:
        print("❌ 未找到任何 .md 文件")
        return
    
    print(f"\n找到 {len(md_files)} 个文件：")
    for i, file in enumerate(md_files, 1):
        print(f"  [{i}] {file}")
    
    print("\n是否处理所有文件？(y/n): ", end='')
    if input().strip().lower() != 'y':
        return
    
    mode = get_choice("\n选择提取模式：\n  [1] 仅单词\n  [2] 单词+词义\n  [3] 单词+短语+词义\n模式: ", ['1', '2', '3'])
    
    success_count = 0
    for file in md_files:
        try:
            print(f"\n处理: {file}")
            base_name = Path(file).stem
            
            if mode == '1':
                output = f"{base_name}_单词.txt"
                extract_words_only(file, output, unique=True)
            elif mode == '2':
                output = f"{base_name}_单词词义.txt"
                extract_words_from_markdown(file, output, include_phrases=False)
            else:
                output = f"{base_name}_完整.txt"
                extract_words_from_markdown(file, output, include_phrases=True)
            
            success_count += 1
        except Exception as e:
            print(f"❌ 处理失败: {e}")
    
    print(f"\n✅ 批量处理完成！成功处理 {success_count}/{len(md_files)} 个文件")


def interactive_mode():
    """交互式模式"""
    print_header()
    
    while True:
        print_menu()
        print("默认选择选项1（提取单词+自动核对）")
        choice = input("请选择 [0-4]（直接回车选择1）: ").strip()
        
        # 如果用户直接回车，默认选择1
        if not choice:
            choice = '1'
            print("已选择选项1")
        
        if choice not in ['0', '1', '2', '3', '4']:
            print("❌ 无效的选择，请输入 0, 1, 2, 3, 4 中的一个")
            continue
        
        if choice == '0':
            print("\n👋 再见！")
            break
        
        if choice == '4':
            batch_process()
            input("\n按回车键继续...")
            continue
        
        # 获取输入文件
        input_file = get_input_file()
        if not input_file:
            continue
        
        # 根据模式设置默认输出文件名
        base_name = Path(input_file).stem
        
        if choice == '1':
            # 仅单词模式 + 自动核对
            default_output = f"{base_name}_单词.txt"
            output_file = get_output_file(default_output)
            
            print("\n是否去重？(y/n，默认y): ", end='')
            unique = input().strip().lower() != 'n'
            
            print("\n🔄 正在提取单词...")
            try:
                words = extract_words_only(input_file, output_file, unique, auto_check=True)
                print(f"\n✅ 成功！共提取 {len(words)} 个单词")
                
                # 预览（如果已经进行了核对，这里就不需要再预览了）
                if not os.path.exists(output_file.replace('.txt', '_check_detail_').replace('.txt', '') + '*.txt'):
                    print("\n前10个单词：")
                    for i, word in enumerate(words[:10], 1):
                        print(f"  {i}. {word}")
                    if len(words) > 10:
                        print(f"  ... 还有 {len(words) - 10} 个")
                
            except Exception as e:
                print(f"\n❌ 提取失败: {e}")
        
        elif choice == '2':
            # 单词+词义模式
            default_output = f"{base_name}_单词词义.txt"
            output_file = get_output_file(default_output)
            
            print("\n🔄 正在提取单词...")
            try:
                words_data = extract_words_from_markdown(input_file, output_file, include_phrases=False)
                print(f"\n✅ 成功！")
                preview_results(words_data)
            except Exception as e:
                print(f"\n❌ 提取失败: {e}")
        
        elif choice == '3':
            # 单词+短语+词义模式
            default_output = f"{base_name}_完整.txt"
            output_file = get_output_file(default_output)
            
            print("\n🔄 正在提取单词和短语...")
            try:
                words_data, phrases_data = extract_words_from_markdown(input_file, output_file, include_phrases=True)
                print(f"\n✅ 成功！")
                preview_results(words_data, phrases_data)
            except Exception as e:
                print(f"\n❌ 提取失败: {e}")
        
        input("\n✨ 按回车键继续...")


if __name__ == '__main__':
    # 检查是否有命令行参数
    if len(sys.argv) > 1:
        # 命令行模式
        parser = argparse.ArgumentParser(description='从markdown格式的单词本中提取单词')
        parser.add_argument('input_file', help='输入的markdown文件路径')
        parser.add_argument('-o', '--output', help='输出文件路径')
        parser.add_argument('-m', '--mode', choices=['full', 'words_only'], default='full',
                            help='提取模式：full=完整信息，words_only=仅单词')
        parser.add_argument('-p', '--phrases', action='store_true',
                            help='是否包含短语（仅在full模式下有效）')
        parser.add_argument('--no-unique', action='store_true',
                            help='不去重（仅在words_only模式下有效）')
        
        args = parser.parse_args()
        
        # 设置默认输出文件名
        if not args.output:
            if args.mode == 'full':
                args.output = 'extracted_words_full.txt'
            else:
                args.output = 'extracted_words.txt'
        
        # 执行提取
        if args.mode == 'full':
            extract_words_from_markdown(args.input_file, args.output, args.phrases)
        else:
            extract_words_only(args.input_file, args.output, not args.no_unique)
        
        print("\n提取完成！")
    else:
        # 交互式模式
        try:
            interactive_mode()
        except KeyboardInterrupt:
            print("\n\n👋 程序已退出")


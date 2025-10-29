
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
不背单词词书核对工具
自动上传单词文件到不背单词网站进行核对
"""

import requests
import os
import sys
import json
import time
from pathlib import Path
import argparse


class BBDCWordChecker:
    """不背单词词书核对类"""
    
    def __init__(self):
        self.base_url = "https://bbdc.cn"
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
    
    # def set_cookies(self, jsessionid=None, hanhan=None, acw_tc=None):
    #     """
    #     设置cookies（已注释，cookies为可选）
    #     
    #     参数:
    #         jsessionid: JSESSIONID cookie值
    #         hanhan: hanhan cookie值
    #         acw_tc: acw_tc cookie值
    #     """
    #     cookies = {}
    #     
    #     if jsessionid:
    #         cookies['JSESSIONID'] = jsessionid
    #     if hanhan:
    #         cookies['hanhan'] = hanhan
    #     if acw_tc:
    #         cookies['acw_tc'] = acw_tc
    #     
    #     # 更新session的cookies
    #     for name, value in cookies.items():
    #         self.session.cookies.set(name, value)
    #     
    #     print(f"✅ 已设置cookies: {list(cookies.keys())}")
    
    def upload_word_file(self, file_path, filename=None):
        """
        上传单词文件进行核对
        
        参数:
            file_path: 要上传的文件路径
            filename: 自定义文件名（可选）
        
        返回:
            dict: 服务器响应结果
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        # 如果没有指定文件名，使用原文件名
        if not filename:
            filename = os.path.basename(file_path)
        
        print(f"📤 正在上传文件: {filename}")
        print(f"📁 文件路径: {file_path}")
        
        try:
            # 准备multipart/form-data
            with open(file_path, 'rb') as f:
                files = {
                    'file': (filename, f, 'text/plain')
                }
                
                # 发送POST请求
                response = self.session.post(
                    self.submit_url,
                    files=files,
                    timeout=30
                )
            
            # 检查响应状态
            if response.status_code == 200:
                try:
                    result = response.json()
                    print("✅ 上传成功！")
                    return result
                except json.JSONDecodeError:
                    print("⚠️  响应不是有效的JSON格式")
                    print(f"响应内容: {response.text[:500]}...")
                    return {"error": "Invalid JSON response", "content": response.text}
            else:
                print(f"❌ 上传失败，状态码: {response.status_code}")
                print(f"响应内容: {response.text[:500]}...")
                return {"error": f"HTTP {response.status_code}", "content": response.text}
                
        except requests.exceptions.Timeout:
            print("❌ 请求超时")
            return {"error": "Request timeout"}
        except requests.exceptions.RequestException as e:
            print(f"❌ 请求失败: {e}")
            return {"error": str(e)}
    
    def parse_result(self, result):
        """
        解析核对结果
        
        参数:
            result: 服务器返回的结果
        
        返回:
            dict: 解析后的结果
        """
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
    
    def save_result(self, parsed_result, output_file=None):
        """
        保存核对结果到文件
        
        参数:
            parsed_result: 解析后的结果
            output_file: 输出文件路径（可选）
        """
        if "error" in parsed_result:
            print(f"❌ 无法保存结果: {parsed_result['error']}")
            return
        
        if not output_file:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            output_file = f"bbdc_check_result_{timestamp}.txt"
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write("=" * 60 + "\n")
                f.write("不背单词词书核对结果\n")
                f.write("=" * 60 + "\n\n")
                
                f.write(f"📊 统计信息:\n")
                f.write(f"  总单词数: {parsed_result['total_count']}\n")
                f.write(f"  识别成功: {parsed_result['recognized_count']}\n")
                f.write(f"  识别不成功: {parsed_result['unrecognized_count']}\n")
                f.write(f"  识别成功率: {parsed_result['recognized_count']/parsed_result['total_count']*100:.1f}%\n\n")
                
                f.write("=" * 30 + " 识别不成功的单词 " + "=" * 30 + "\n")
                for i, word in enumerate(parsed_result['unrecognized_words'], 1):
                    f.write(f"{i:3d}. {word}\n")
                
                f.write("\n" + "=" * 30 + " 识别成功的单词 " + "=" * 30 + "\n")
                for i, word in enumerate(parsed_result['recognized_words'], 1):
                    f.write(f"{i:3d}. {word}\n")
            
            print(f"💾 结果已保存到: {output_file}")
            
        except Exception as e:
            print(f"❌ 保存文件失败: {e}")
    
    def print_result(self, parsed_result):
        """
        打印核对结果
        
        参数:
            parsed_result: 解析后的结果
        """
        if "error" in parsed_result:
            print(f"❌ 处理失败: {parsed_result['error']}")
            return
        
        print("\n" + "=" * 60)
        print("📊 不背单词词书核对结果")
        print("=" * 60)
        
        print(f"\n📈 统计信息:")
        print(f"  总单词数: {parsed_result['total_count']}")
        print(f"  识别成功: {parsed_result['recognized_count']}")
        print(f"  识别不成功: {parsed_result['unrecognized_count']}")
        print(f"  识别成功率: {parsed_result['recognized_count']/parsed_result['total_count']*100:.1f}%")
        
        # 显示识别不成功的单词（前20个）
        if parsed_result['unrecognized_words']:
            print(f"\n❓ 识别不成功的单词（前20个）:")
            for i, word in enumerate(parsed_result['unrecognized_words'][:20], 1):
                print(f"  {i:2d}. {word}")
            
            if len(parsed_result['unrecognized_words']) > 20:
                print(f"  ... 还有 {len(parsed_result['unrecognized_words']) - 20} 个识别不成功的单词")
        
        print()


def print_header():
    """打印程序头部"""
    print("\n" + "=" * 60)
    print("           📚 不背单词词书核对工具")
    print("=" * 60)
    print()


# def get_cookies_from_user():
#     """从用户输入获取cookies（已注释，cookies为可选）"""
#     print("\n🍪 请输入cookies信息（可选，直接回车跳过）:")
#     print("提示：从浏览器开发者工具的Network标签页中复制cookies")
#     
#     jsessionid = input("JSESSIONID: ").strip()
#     hanhan = input("hanhan: ").strip()
#     acw_tc = input("acw_tc: ").strip()
#     
#     return jsessionid, hanhan, acw_tc


def get_file_path():
    """获取要上传的文件路径"""
    print("\n📂 请输入要上传的单词文件路径:")
    print("提示：可以直接拖拽文件到此窗口，或输入完整路径")
    
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
        
        return file_path


def interactive_mode():
    """交互式模式"""
    print_header()
    
    # 创建核对器实例
    checker = BBDCWordChecker()
    
    # 获取文件路径
    file_path = get_file_path()
    if not file_path:
        print("❌ 未选择文件，程序退出")
        return
    
    # 上传文件
    print("\n🔄 正在上传文件...")
    result = checker.upload_word_file(file_path)
    
    if "error" in result:
        print(f"❌ 上传失败: {result['error']}")
        return
    
    # 解析结果
    parsed_result = checker.parse_result(result)
    
    # 显示结果
    checker.print_result(parsed_result)
    
    # 保存结果
    save_choice = input("\n💾 是否保存结果到文件？(y/n): ").strip().lower()
    if save_choice == 'y':
        output_file = input("输出文件名（直接回车使用默认）: ").strip()
        if not output_file:
            output_file = None
        checker.save_result(parsed_result, output_file)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='不背单词词书核对工具')
    parser.add_argument('file_path', nargs='?', help='要上传的单词文件路径')
    parser.add_argument('-o', '--output', help='输出结果文件路径')
    
    args = parser.parse_args()
    
    # 创建核对器实例
    checker = BBDCWordChecker()
    
    if args.file_path:
        # 命令行模式
        if not os.path.exists(args.file_path):
            print(f"❌ 文件不存在: {args.file_path}")
            sys.exit(1)
        
        print(f"📤 正在上传文件: {args.file_path}")
        result = checker.upload_word_file(args.file_path)
        
        if "error" in result:
            print(f"❌ 上传失败: {result['error']}")
            sys.exit(1)
        
        parsed_result = checker.parse_result(result)
        checker.print_result(parsed_result)
        
        if args.output:
            checker.save_result(parsed_result, args.output)
        else:
            checker.save_result(parsed_result)
    else:
        # 交互式模式
        try:
            interactive_mode()
        except KeyboardInterrupt:
            print("\n\n👋 程序已退出")


if __name__ == '__main__':
    main()

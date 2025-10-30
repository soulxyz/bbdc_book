#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Mineru API 集成模块
支持通过 Mineru API 上传 PDF 文件，自动获取 markdown 解析结果
并提取单词进行不背单词核对
"""

import requests
import os
import sys
import json
import time
import zipfile
import io
from pathlib import Path
from typing import Optional, Dict, List
import argparse

# 尝试导入 tqdm 进度条库
try:
    from tqdm import tqdm
    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False


class MineruAPIClient:
    """Mineru API 客户端"""
    
    def __init__(self, api_token=None):
        """
        初始化 Mineru API 客户端
        
        参数:
            api_token: Mineru API Token，如果不提供则从环境变量或.env文件读取
        """
        self.api_token = api_token or self._load_token()
        self.base_url = "https://mineru.net/api/v4"
        self.session = requests.Session()
        
        if not self.api_token:
            # 显示查找过的路径
            search_paths = [
                os.path.join(os.getcwd(), '.env'),
                os.path.join(os.path.dirname(sys.executable if getattr(sys, 'frozen', False) else __file__), '.env'),
            ]
            paths_info = '\n'.join([f"  - {p}" for p in search_paths])
            
            raise ValueError(
                "❌ 未设置 Mineru API Token！\n\n"
                f"已查找以下位置但未找到 .env 文件：\n{paths_info}\n\n"
                "请通过以下方式之一设置：\n"
                "1. 在 exe 所在目录创建 .env 文件，添加: MINERU_API_TOKEN=your_token_here\n"
                "2. 设置环境变量: MINERU_API_TOKEN\n"
                "3. 在代码中直接传入 api_token 参数\n\n"
                "Token 获取地址: https://mineru.net/"
            )
        
        # 设置请求头
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_token}',
            'Accept': '*/*'
        })
    
    def _load_token(self):
        """从环境变量或.env文件加载API Token"""
        # 先尝试从环境变量读取
        token = os.environ.get('MINERU_API_TOKEN', '')
        if token:
            return token
        
        # 尝试多个可能的 .env 文件位置
        possible_paths = [
            # 1. 当前工作目录
            os.path.join(os.getcwd(), '.env'),
            # 2. exe 所在目录（打包后）
            os.path.join(os.path.dirname(sys.executable if getattr(sys, 'frozen', False) else __file__), '.env'),
            # 3. 脚本所在目录（开发环境）
            os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env'),
        ]
        
        for env_file in possible_paths:
            if os.path.exists(env_file):
                try:
                    with open(env_file, 'r', encoding='utf-8') as f:
                        for line in f:
                            line = line.strip()
                            if line and not line.startswith('#') and '=' in line:
                                key, value = line.split('=', 1)
                                key = key.strip()
                                value = value.strip().strip('"').strip("'")
                                if key == 'MINERU_API_TOKEN' and value:
                                    return value
                except Exception as e:
                    print(f"⚠️  读取 {env_file} 失败: {e}")
                    continue
        
        return None
    
    def create_task_from_url(self, pdf_url: str, **kwargs) -> Dict:
        """
        从 URL 创建解析任务
        
        参数:
            pdf_url: PDF 文件的 URL
            **kwargs: 其他可选参数
                - is_ocr: 是否启用OCR，默认True
                - enable_formula: 是否开启公式识别，默认True
                - enable_table: 是否开启表格识别，默认True
                - language: 文档语言，默认'ch'
                - data_id: 数据ID
                - callback: 回调URL
                - seed: 随机字符串
                - extra_formats: 额外导出格式列表
                - page_ranges: 页码范围
                - model_version: 模型版本，pipeline或vlm
        
        返回:
            dict: 包含 task_id 的响应结果
        """
        url = f"{self.base_url}/extract/task"
        
        # 构建请求数据
        data = {
            "url": pdf_url,
            "is_ocr": kwargs.get('is_ocr', True),
            "enable_formula": kwargs.get('enable_formula', True),
            "enable_table": kwargs.get('enable_table', True),
            "language": kwargs.get('language', 'ch')
        }
        
        # 添加可选参数
        optional_params = ['data_id', 'callback', 'seed', 'extra_formats', 'page_ranges', 'model_version']
        for param in optional_params:
            if param in kwargs:
                data[param] = kwargs[param]
        
        try:
            response = self.session.post(url, json=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('code') == 0:
                    return {
                        'success': True,
                        'task_id': result['data']['task_id'],
                        'trace_id': result.get('trace_id'),
                        'message': 'Task created successfully'
                    }
                else:
                    return {
                        'success': False,
                        'error': result.get('msg', 'Unknown error'),
                        'code': result.get('code')
                    }
            else:
                return {
                    'success': False,
                    'error': f'HTTP {response.status_code}',
                    'content': response.text[:500]
                }
        
        except requests.exceptions.Timeout:
            return {'success': False, 'error': 'Request timeout'}
        except requests.exceptions.RequestException as e:
            return {'success': False, 'error': str(e)}
    
    def upload_local_file(self, file_path: str, **kwargs) -> Dict:
        """
        上传本地文件（先获取上传URL，然后上传文件，自动创建解析任务）
        
        参数:
            file_path: 本地文件路径
            **kwargs: 其他可选参数（同 create_task_from_url）
        
        返回:
            dict: 包含 batch_id 和文件上传结果
        """
        if not os.path.exists(file_path):
            return {'success': False, 'error': f'File not found: {file_path}'}
        
        filename = os.path.basename(file_path)
        url = f"{self.base_url}/file-urls/batch"
        
        # 构建请求数据
        file_info = {
            "name": filename,
            "is_ocr": kwargs.get('is_ocr', True)
        }
        
        # 添加文件级别的可选参数
        if 'data_id' in kwargs:
            file_info['data_id'] = kwargs['data_id']
        if 'page_ranges' in kwargs:
            file_info['page_ranges'] = kwargs['page_ranges']
        
        data = {
            "enable_formula": kwargs.get('enable_formula', True),
            "enable_table": kwargs.get('enable_table', True),
            "language": kwargs.get('language', 'ch'),
            "files": [file_info]
        }
        
        # 添加全局可选参数
        if 'callback' in kwargs:
            data['callback'] = kwargs['callback']
        if 'seed' in kwargs:
            data['seed'] = kwargs['seed']
        if 'extra_formats' in kwargs:
            data['extra_formats'] = kwargs['extra_formats']
        if 'model_version' in kwargs:
            data['model_version'] = kwargs['model_version']
        
        try:
            # 第一步：获取上传URL
            response = self.session.post(url, json=data, timeout=30)
            
            if response.status_code != 200:
                return {
                    'success': False,
                    'error': f'Failed to get upload URL: HTTP {response.status_code}',
                    'content': response.text[:500]
                }
            
            result = response.json()
            if result.get('code') != 0:
                return {
                    'success': False,
                    'error': result.get('msg', 'Unknown error'),
                    'code': result.get('code')
                }
            
            batch_id = result['data']['batch_id']
            upload_url = result['data']['file_urls'][0]
            
            # 第二步：上传文件
            print(f"📤 正在上传文件到 Mineru...")
            with open(file_path, 'rb') as f:
                upload_response = requests.put(upload_url, data=f, timeout=300)
            
            if upload_response.status_code == 200:
                return {
                    'success': True,
                    'batch_id': batch_id,
                    'message': 'File uploaded successfully, task will be created automatically'
                }
            else:
                return {
                    'success': False,
                    'error': f'File upload failed: HTTP {upload_response.status_code}'
                }
        
        except requests.exceptions.Timeout:
            return {'success': False, 'error': 'Request timeout'}
        except requests.exceptions.RequestException as e:
            return {'success': False, 'error': str(e)}
    
    def get_task_status(self, task_id: str) -> Dict:
        """
        获取任务状态
        
        参数:
            task_id: 任务ID
        
        返回:
            dict: 任务状态信息
        """
        url = f"{self.base_url}/extract/task/{task_id}"
        
        try:
            response = self.session.get(url, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('code') == 0:
                    data = result['data']
                    return {
                        'success': True,
                        'task_id': data.get('task_id'),
                        'state': data.get('state'),  # done, pending, running, failed, converting
                        'full_zip_url': data.get('full_zip_url'),
                        'err_msg': data.get('err_msg'),
                        'extract_progress': data.get('extract_progress'),
                        'data_id': data.get('data_id')
                    }
                else:
                    return {
                        'success': False,
                        'error': result.get('msg', 'Unknown error'),
                        'code': result.get('code')
                    }
            else:
                return {
                    'success': False,
                    'error': f'HTTP {response.status_code}',
                    'content': response.text[:500]
                }
        
        except requests.exceptions.RequestException as e:
            return {'success': False, 'error': str(e)}
    
    def get_batch_status(self, batch_id: str) -> Dict:
        """
        获取批量任务状态
        
        参数:
            batch_id: 批次ID
        
        返回:
            dict: 批量任务状态信息
        """
        url = f"{self.base_url}/extract-results/batch/{batch_id}"
        
        try:
            response = self.session.get(url, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('code') == 0:
                    return {
                        'success': True,
                        'batch_id': result['data']['batch_id'],
                        'extract_result': result['data']['extract_result']
                    }
                else:
                    return {
                        'success': False,
                        'error': result.get('msg', 'Unknown error'),
                        'code': result.get('code')
                    }
            else:
                return {
                    'success': False,
                    'error': f'HTTP {response.status_code}',
                    'content': response.text[:500]
                }
        
        except requests.exceptions.RequestException as e:
            return {'success': False, 'error': str(e)}
    
    def wait_for_task_completion(self, task_id: str, check_interval=10, max_wait_time=600) -> Dict:
        """
        等待任务完成
        
        参数:
            task_id: 任务ID
            check_interval: 检查间隔（秒），默认10秒
            max_wait_time: 最大等待时间（秒），默认600秒（10分钟）
        
        返回:
            dict: 最终任务状态
        """
        print(f"⏳ 等待任务完成 (任务ID: {task_id})...")
        start_time = time.time()
        pbar = None
        last_state = None
        
        while True:
            elapsed_time = time.time() - start_time
            
            if elapsed_time > max_wait_time:
                if pbar:
                    pbar.close()
                return {
                    'success': False,
                    'error': f'Task timeout after {max_wait_time} seconds'
                }
            
            status = self.get_task_status(task_id)
            
            if not status.get('success'):
                if pbar:
                    pbar.close()
                return status
            
            state = status.get('state')
            
            if state == 'done':
                if pbar:
                    pbar.close()
                print(f"✅ 任务完成！")
                return status
            elif state == 'failed':
                if pbar:
                    pbar.close()
                print(f"❌ 任务失败: {status.get('err_msg')}")
                return {
                    'success': False,
                    'error': status.get('err_msg', 'Task failed')
                }
            elif state == 'running':
                progress = status.get('extract_progress', {})
                if progress:
                    extracted = progress.get('extracted_pages', 0)
                    total = progress.get('total_pages', 0)
                    
                    # 使用进度条（如果可用）
                    if TQDM_AVAILABLE:
                        if pbar is None:
                            # 初始化进度条
                            pbar = tqdm(
                                total=total,
                                desc="📄 PDF 解析进度",
                                unit="页",
                                ncols=80,
                                bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} 页 [{elapsed}<{remaining}]'
                            )
                        pbar.n = extracted
                        pbar.refresh()
                    else:
                        # 无进度条库时使用文本显示
                        percentage = (extracted / total * 100) if total > 0 else 0
                        print(f"⏳ 正在解析... ({extracted}/{total} 页, {percentage:.1f}%)")
                    
                    last_state = 'running'
            elif state == 'pending':
                if last_state != 'pending':
                    print(f"⏳ 排队中...")
                    last_state = 'pending'
            elif state == 'converting':
                if last_state != 'converting':
                    if pbar:
                        pbar.close()
                        pbar = None
                    print(f"⏳ 格式转换中...")
                    last_state = 'converting'
            
            time.sleep(check_interval)
    
    def wait_for_batch_completion(self, batch_id: str, check_interval=10, max_wait_time=600) -> Dict:
        """
        等待批量任务完成
        
        参数:
            batch_id: 批次ID
            check_interval: 检查间隔（秒），默认10秒
            max_wait_time: 最大等待时间（秒），默认600秒（10分钟）
        
        返回:
            dict: 最终批量任务状态
        """
        print(f"⏳ 等待批量任务完成 (批次ID: {batch_id})...")
        start_time = time.time()
        pbars = {}  # 每个文件一个进度条
        
        while True:
            elapsed_time = time.time() - start_time
            
            if elapsed_time > max_wait_time:
                for pbar in pbars.values():
                    if pbar:
                        pbar.close()
                return {
                    'success': False,
                    'error': f'Batch task timeout after {max_wait_time} seconds'
                }
            
            status = self.get_batch_status(batch_id)
            
            if not status.get('success'):
                for pbar in pbars.values():
                    if pbar:
                        pbar.close()
                return status
            
            results = status.get('extract_result', [])
            
            # 检查所有任务是否完成
            all_done = True
            has_failed = False
            
            for result in results:
                state = result.get('state')
                file_name = result.get('file_name')
                
                if state == 'done':
                    # 关闭该文件的进度条
                    if file_name in pbars and pbars[file_name]:
                        pbars[file_name].close()
                        pbars[file_name] = None
                    continue
                elif state == 'failed':
                    has_failed = True
                    if file_name in pbars and pbars[file_name]:
                        pbars[file_name].close()
                        pbars[file_name] = None
                    print(f"❌ 文件 {file_name} 解析失败: {result.get('err_msg')}")
                elif state in ['pending', 'running', 'converting', 'waiting-file']:
                    all_done = False
                    if state == 'running':
                        progress = result.get('extract_progress', {})
                        if progress:
                            extracted = progress.get('extracted_pages', 0)
                            total = progress.get('total_pages', 0)
                            
                            # 使用进度条（如果可用）
                            if TQDM_AVAILABLE:
                                if file_name not in pbars or pbars[file_name] is None:
                                    # 初始化进度条
                                    pbars[file_name] = tqdm(
                                        total=total,
                                        desc=f"📄 {file_name}",
                                        unit="页",
                                        ncols=80,
                                        position=len(pbars),
                                        bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} 页'
                                    )
                                pbars[file_name].n = extracted
                                pbars[file_name].refresh()
                            else:
                                # 无进度条库时使用文本显示
                                percentage = (extracted / total * 100) if total > 0 else 0
                                print(f"⏳ {file_name} 正在解析... ({extracted}/{total} 页, {percentage:.1f}%)")
            
            if all_done:
                for pbar in pbars.values():
                    if pbar:
                        pbar.close()
                if has_failed:
                    print(f"⚠️  部分任务失败")
                else:
                    print(f"✅ 所有任务完成！")
                return status
            
            time.sleep(check_interval)
    
    def download_and_extract_zip(self, zip_url: str, output_dir=None) -> Dict:
        """
        下载并解压结果ZIP文件
        
        参数:
            zip_url: ZIP文件URL
            output_dir: 输出目录，默认为当前目录
        
        返回:
            dict: 包含解压文件信息
        """
        if not output_dir:
            output_dir = os.getcwd()
        
        print(f"📥 正在下载解析结果...")
        
        try:
            response = requests.get(zip_url, timeout=300)
            
            if response.status_code != 200:
                return {
                    'success': False,
                    'error': f'Failed to download ZIP: HTTP {response.status_code}'
                }
            
            # 解压ZIP文件
            print(f"📦 正在解压文件...")
            zip_file = zipfile.ZipFile(io.BytesIO(response.content))
            
            extracted_files = []
            markdown_files = []
            
            for file_info in zip_file.filelist:
                filename = file_info.filename
                
                # 跳过目录
                if filename.endswith('/'):
                    continue
                
                # 解压文件
                zip_file.extract(file_info, output_dir)
                extracted_path = os.path.join(output_dir, filename)
                extracted_files.append(extracted_path)
                
                # 记录markdown文件
                if filename.endswith('.md'):
                    markdown_files.append(extracted_path)
                    print(f"  ✓ {filename}")
            
            return {
                'success': True,
                'output_dir': output_dir,
                'extracted_files': extracted_files,
                'markdown_files': markdown_files,
                'message': f'Extracted {len(extracted_files)} files'
            }
        
        except zipfile.BadZipFile:
            return {'success': False, 'error': 'Invalid ZIP file'}
        except requests.exceptions.RequestException as e:
            return {'success': False, 'error': str(e)}


class MineruWordExtractor:
    """Mineru 单词提取器 - 集成 Mineru API 和单词提取功能"""
    
    def __init__(self, api_token=None):
        """
        初始化 Mineru 单词提取器
        
        参数:
            api_token: Mineru API Token
        """
        self.client = MineruAPIClient(api_token)
    
    def process_pdf_url(self, pdf_url: str, output_dir=None, auto_extract_words=True, **kwargs) -> Dict:
        """
        处理 PDF URL：创建任务 -> 等待完成 -> 下载结果 -> 提取单词
        
        参数:
            pdf_url: PDF 文件的 URL
            output_dir: 输出目录
            auto_extract_words: 是否自动提取单词
            **kwargs: 其他 Mineru API 参数
        
        返回:
            dict: 处理结果
        """
        print(f"\n{'='*60}")
        print(f"📄 处理 PDF: {pdf_url}")
        print(f"{'='*60}\n")
        
        # 1. 创建任务
        print("📤 创建解析任务...")
        task_result = self.client.create_task_from_url(pdf_url, **kwargs)
        
        if not task_result.get('success'):
            return task_result
        
        task_id = task_result['task_id']
        print(f"✅ 任务创建成功！任务ID: {task_id}")
        
        # 2. 等待任务完成
        status = self.client.wait_for_task_completion(task_id)
        
        if not status.get('success'):
            return status
        
        zip_url = status.get('full_zip_url')
        if not zip_url:
            return {'success': False, 'error': 'No ZIP URL in response'}
        
        # 3. 下载并解压
        extract_result = self.client.download_and_extract_zip(zip_url, output_dir)
        
        if not extract_result.get('success'):
            return extract_result
        
        # 4. 自动提取单词（如果需要）
        if auto_extract_words:
            markdown_files = extract_result.get('markdown_files', [])
            if markdown_files:
                return self._extract_words_from_markdown_files(markdown_files, extract_result)
        
        return extract_result
    
    def process_local_pdf(self, file_path: str, output_dir=None, auto_extract_words=True, **kwargs) -> Dict:
        """
        处理本地 PDF：上传 -> 等待完成 -> 下载结果 -> 提取单词
        
        参数:
            file_path: 本地PDF文件路径
            output_dir: 输出目录
            auto_extract_words: 是否自动提取单词
            **kwargs: 其他 Mineru API 参数
        
        返回:
            dict: 处理结果
        """
        print(f"\n{'='*60}")
        print(f"📄 处理本地 PDF: {file_path}")
        print(f"{'='*60}\n")
        
        # 1. 上传文件
        upload_result = self.client.upload_local_file(file_path, **kwargs)
        
        if not upload_result.get('success'):
            return upload_result
        
        batch_id = upload_result['batch_id']
        print(f"✅ 文件上传成功！批次ID: {batch_id}")
        print(f"ℹ️  系统将自动创建解析任务")
        
        # 2. 等待批量任务完成
        status = self.client.wait_for_batch_completion(batch_id)
        
        if not status.get('success'):
            return status
        
        # 3. 获取第一个成功任务的ZIP URL
        results = status.get('extract_result', [])
        zip_url = None
        
        for result in results:
            if result.get('state') == 'done':
                zip_url = result.get('full_zip_url')
                break
        
        if not zip_url:
            return {'success': False, 'error': 'No completed task found'}
        
        # 4. 下载并解压
        extract_result = self.client.download_and_extract_zip(zip_url, output_dir)
        
        if not extract_result.get('success'):
            return extract_result
        
        # 5. 自动提取单词（如果需要）
        if auto_extract_words:
            markdown_files = extract_result.get('markdown_files', [])
            if markdown_files:
                return self._extract_words_from_markdown_files(markdown_files, extract_result)
        
        return extract_result
    
    def _extract_words_from_markdown_files(self, markdown_files: List[str], base_result: Dict) -> Dict:
        """
        从 markdown 文件中提取单词
        
        参数:
            markdown_files: markdown 文件列表
            base_result: 基础结果字典
        
        返回:
            dict: 更新后的结果
        """
        print(f"\n{'='*60}")
        print(f"📖 开始提取单词")
        print(f"{'='*60}\n")
        
        # 尝试导入 extract_words 模块
        try:
            from extract_words import extract_words_only
        except ImportError:
            print("⚠️  无法导入 extract_words 模块，跳过单词提取")
            return base_result
        
        words_results = []
        
        for md_file in markdown_files:
            try:
                print(f"📝 处理文件: {os.path.basename(md_file)}")
                
                # 生成输出文件名
                base_name = Path(md_file).stem
                output_file = os.path.join(
                    os.path.dirname(md_file),
                    f"{base_name}_单词.txt"
                )
                
                # 提取单词
                words = extract_words_only(
                    md_file,
                    output_file=output_file,
                    unique=True,
                    auto_check=True  # 自动进行不背单词核对
                )
                
                words_results.append({
                    'markdown_file': md_file,
                    'words_file': output_file,
                    'words_count': len(words)
                })
                
                print(f"✅ 提取完成：{len(words)} 个单词")
                
            except Exception as e:
                print(f"❌ 提取失败: {e}")
                words_results.append({
                    'markdown_file': md_file,
                    'error': str(e)
                })
        
        base_result['words_extraction'] = words_results
        return base_result


def print_header():
    """打印程序头部"""
    print("\n" + "=" * 60)
    print("           📚 Mineru PDF 单词提取工具")
    print("=" * 60)
    print()


def print_menu():
    """打印主菜单"""
    print("\n请选择处理方式：")
    print("  [1] 处理在线 PDF（通过 URL）")
    print("  [2] 处理本地 PDF 文件")
    print("  [0] 退出")
    print()


def get_choice(prompt, valid_choices):
    """获取用户选择"""
    while True:
        choice = input(prompt).strip()
        if choice in valid_choices:
            return choice
        print(f"❌ 无效的选择，请输入 {', '.join(valid_choices)} 中的一个")


def interactive_mode():
    """交互式模式"""
    print_header()
    
    # 检查 API Token
    try:
        extractor = MineruWordExtractor()
    except ValueError as e:
        print(str(e))
        return
    
    while True:
        print_menu()
        choice = input("请选择 [0-2]: ").strip()
        
        if choice not in ['0', '1', '2']:
            print("❌ 无效的选择")
            continue
        
        if choice == '0':
            print("\n👋 再见！")
            break
        
        if choice == '1':
            # 处理在线 PDF
            pdf_url = input("\n请输入 PDF URL: ").strip()
            if not pdf_url:
                print("❌ URL 不能为空")
                continue
            
            output_dir = input("输出目录（直接回车使用当前目录）: ").strip()
            if not output_dir:
                output_dir = None
            
            # 可选参数
            is_ocr = input("是否启用 OCR？(y/n，默认y): ").strip().lower() != 'n'
            
            try:
                result = extractor.process_pdf_url(
                    pdf_url,
                    output_dir=output_dir,
                    auto_extract_words=True,
                    is_ocr=is_ocr
                )
                
                if result.get('success'):
                    print(f"\n✅ 处理完成！")
                    print(f"📂 输出目录: {result.get('output_dir')}")
                    if 'words_extraction' in result:
                        print(f"\n📊 单词提取结果:")
                        for item in result['words_extraction']:
                            if 'error' not in item:
                                print(f"  ✓ {item['words_count']} 个单词 -> {item['words_file']}")
                else:
                    print(f"\n❌ 处理失败: {result.get('error')}")
            
            except Exception as e:
                print(f"\n❌ 发生错误: {e}")
        
        elif choice == '2':
            # 处理本地 PDF
            file_path = input("\n请输入 PDF 文件路径（可拖拽文件到此窗口）: ").strip().strip('"').strip("'")
            
            if not file_path or not os.path.exists(file_path):
                print("❌ 文件不存在")
                continue
            
            output_dir = input("输出目录（直接回车使用当前目录）: ").strip()
            if not output_dir:
                output_dir = None
            
            # 可选参数
            is_ocr = input("是否启用 OCR？(y/n，默认y): ").strip().lower() != 'n'
            
            try:
                result = extractor.process_local_pdf(
                    file_path,
                    output_dir=output_dir,
                    auto_extract_words=True,
                    is_ocr=is_ocr
                )
                
                if result.get('success'):
                    print(f"\n✅ 处理完成！")
                    print(f"📂 输出目录: {result.get('output_dir')}")
                    if 'words_extraction' in result:
                        print(f"\n📊 单词提取结果:")
                        for item in result['words_extraction']:
                            if 'error' not in item:
                                print(f"  ✓ {item['words_count']} 个单词 -> {item['words_file']}")
                else:
                    print(f"\n❌ 处理失败: {result.get('error')}")
            
            except Exception as e:
                print(f"\n❌ 发生错误: {e}")
        
        input("\n按回车键继续...")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='Mineru PDF 单词提取工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 处理在线 PDF
  python mineru_api.py --url https://example.com/sample.pdf
  
  # 处理本地 PDF
  python mineru_api.py --file path/to/your.pdf
  
  # 指定输出目录
  python mineru_api.py --file your.pdf --output ./results
  
  # 禁用自动单词提取
  python mineru_api.py --file your.pdf --no-extract-words
        """
    )
    
    parser.add_argument('--url', help='在线 PDF 文件的 URL')
    parser.add_argument('--file', help='本地 PDF 文件路径')
    parser.add_argument('-o', '--output', help='输出目录（默认为当前目录）')
    parser.add_argument('--no-extract-words', action='store_true', help='不自动提取单词')
    parser.add_argument('--no-ocr', action='store_true', help='禁用 OCR')
    parser.add_argument('--token', help='Mineru API Token（也可通过环境变量设置）')
    
    args = parser.parse_args()
    
    # 如果没有参数，进入交互模式
    if not args.url and not args.file:
        try:
            interactive_mode()
        except KeyboardInterrupt:
            print("\n\n👋 程序已退出")
        return
    
    # 命令行模式
    try:
        extractor = MineruWordExtractor(api_token=args.token)
        
        if args.url:
            print(f"处理在线 PDF: {args.url}")
            result = extractor.process_pdf_url(
                args.url,
                output_dir=args.output,
                auto_extract_words=not args.no_extract_words,
                is_ocr=not args.no_ocr
            )
        elif args.file:
            print(f"处理本地 PDF: {args.file}")
            result = extractor.process_local_pdf(
                args.file,
                output_dir=args.output,
                auto_extract_words=not args.no_extract_words,
                is_ocr=not args.no_ocr
            )
        
        if result.get('success'):
            print(f"\n✅ 处理完成！")
            if 'words_extraction' in result:
                print(f"\n单词提取结果:")
                for item in result['words_extraction']:
                    if 'error' not in item:
                        print(f"  - {item['words_file']}: {item['words_count']} 个单词")
        else:
            print(f"\n❌ 处理失败: {result.get('error')}")
            sys.exit(1)
    
    except ValueError as e:
        print(str(e))
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n👋 程序已退出")
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()


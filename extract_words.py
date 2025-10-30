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
from typing import List, Dict, Optional
from env_loader import load_env_variable, check_env_file_exists


class LLMWordCorrector:
    """LLM单词更正类 - 调用硅基流动平台"""
    
    def __init__(self, api_key=None):
        """
        初始化LLM更正器
        
        参数:
            api_key: 硅基流动API密钥，如果不提供则从环境变量SILICONFLOW_API_KEY读取
        """
        # 使用统一的环境变量加载
        self.api_key = api_key or load_env_variable('SILICONFLOW_API_KEY')
        self.base_url = load_env_variable('SILICONFLOW_BASE_URL', "https://api.siliconflow.cn/v1/chat/completions")
        self.model = load_env_variable('SILICONFLOW_MODEL', "moonshotai/Kimi-K2-Instruct-0905")
        
        if not self.api_key:
            # 检查 .env 文件状态
            exists, found_path, search_paths = check_env_file_exists()
            
            print("⚠️  警告: 未设置 SILICONFLOW_API_KEY，LLM自动更正功能将被禁用")
            if exists:
                print(f"💡 提示: 找到 .env 文件 ({found_path})，但其中没有 SILICONFLOW_API_KEY 配置")
            else:
                print(f"💡 提示: 未找到 .env 文件，请在 exe 所在目录创建 .env 文件")
            print("   在 .env 文件中添加: SILICONFLOW_API_KEY=your_key_here")
            print("   获取地址: https://cloud.siliconflow.cn/")
    
    
    def is_enabled(self):
        """检查LLM功能是否启用"""
        return bool(self.api_key)
    
    def correct_word(self, word, meaning="", context=""):
        """
        使用LLM更正单词
        
        参数:
            word: 原始单词（可能有错误）
            meaning: 单词的中文释义
            context: 上下文信息
        
        返回:
            dict: {
                'success': bool,
                'original': str,
                'corrected': str,
                'confidence': str,
                'reason': str
            }
        """
        if not self.is_enabled():
            return {
                'success': False,
                'original': word,
                'corrected': word,
                'confidence': 'none',
                'reason': 'LLM功能未启用'
            }
        
        # 构建提示词
        prompt = self._build_prompt(word, meaning, context)
        
        try:
            response = requests.post(
                self.base_url,
                headers={
                    'Authorization': f'Bearer {self.api_key}',
                    'Content-Type': 'application/json'
                },
                json={
                    'model': self.model,
                    'messages': [
                        {
                            'role': 'system',
                            'content': '你是一个专业的英语单词拼写检查助手。你的任务是识别和修正英语单词中的拼写错误。只返回JSON格式的结果。'
                        },
                        {
                            'role': 'user',
                            'content': prompt
                        }
                    ],
                    'temperature': 0.3,
                    'max_tokens': 200
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result.get('choices', [{}])[0].get('message', {}).get('content', '')
                return self._parse_llm_response(word, content)
            else:
                return {
                    'success': False,
                    'original': word,
                    'corrected': word,
                    'confidence': 'none',
                    'reason': f'API调用失败: HTTP {response.status_code}'
                }
        
        except Exception as e:
            return {
                'success': False,
                'original': word,
                'corrected': word,
                'confidence': 'none',
                'reason': f'调用LLM时出错: {str(e)}'
            }
    
    def _build_prompt(self, word, meaning, context):
        """构建提示词"""
        prompt = f"""请检查以下英语单词是否有拼写错误，如果有错误请给出正确的拼写。

原始单词: {word}
中文释义: {meaning}
{f'上下文: {context}' if context else ''}

请以JSON格式返回结果，包含以下字段：
- corrected: 更正后的单词（如果没有错误则返回原单词）
- confidence: 置信度，可选值为 "high"（高）、"medium"（中）、"low"（低）
- reason: 简短说明更正的原因或判断没有错误的依据

示例输出：
{{"corrected": "example", "confidence": "high", "reason": "原单词拼写正确"}}
或
{{"corrected": "receive", "confidence": "high", "reason": "修正了i和e的顺序"}}

只返回JSON，不要有其他内容。"""
        return prompt
    
    def _parse_llm_response(self, original_word, content):
        """解析LLM返回的结果"""
        try:
            # 尝试提取JSON内容
            content = content.strip()
            
            # 如果包含markdown代码块，提取其中的JSON
            if '```json' in content:
                content = content.split('```json')[1].split('```')[0].strip()
            elif '```' in content:
                content = content.split('```')[1].split('```')[0].strip()
            
            # 解析JSON
            result = json.loads(content)
            
            corrected = result.get('corrected', original_word).strip()
            confidence = result.get('confidence', 'low')
            reason = result.get('reason', '无说明')
            
            return {
                'success': True,
                'original': original_word,
                'corrected': corrected,
                'confidence': confidence,
                'reason': reason
            }
        
        except json.JSONDecodeError:
            # 如果无法解析JSON，尝试从文本中提取单词
            words = content.split()
            if words:
                return {
                    'success': True,
                    'original': original_word,
                    'corrected': words[0].strip('",.:;'),
                    'confidence': 'low',
                    'reason': '从响应中提取的单词'
                }
            else:
                return {
                    'success': False,
                    'original': original_word,
                    'corrected': original_word,
                    'confidence': 'none',
                    'reason': '无法解析LLM响应'
                }
        except Exception as e:
            return {
                'success': False,
                'original': original_word,
                'corrected': original_word,
                'confidence': 'none',
                'reason': f'解析响应时出错: {str(e)}'
            }
    
    def batch_correct(self, words_with_meanings, max_workers=3):
        """
        批量更正单词
        
        参数:
            words_with_meanings: 单词及释义列表 [{'word': str, 'meaning': str}, ...]
            max_workers: 最大并发数
        
        返回:
            list: 更正结果列表
        """
        results = []
        for item in words_with_meanings:
            word = item.get('word', '')
            meaning = item.get('meaning', '')
            result = self.correct_word(word, meaning)
            results.append(result)
            time.sleep(0.5)  # 避免API限流
        
        return results
    
    def generate_word_candidates(self, word, meaning):
        """
        生成单词的候选词（词根、派生词等）
        
        参数:
            word: 原始单词
            meaning: 单词释义
        
        返回:
            dict: 候选词信息
        """
        if not self.is_enabled():
            return {
                'success': False,
                'candidates': [],
                'reason': 'LLM功能未启用'
            }
        
        prompt = f"""对于无法识别的英语单词"{word}"（释义：{meaning}），请生成3-5个可能的候选词。

候选词可以是：
1. 该单词的词根或基础形式
2. 该单词去掉前缀/后缀后的形式
3. 意思相近的常见单词
4. 可能的正确拼写（如果原词有拼写错误）

要求：
- 候选词必须是真实存在的常见英语单词
- 优先选择更基础、更常用的词汇
- 保持与原释义的相关性

请以JSON格式返回，包含：
- candidates: 候选词列表（每个包含word和reason字段）

示例输出：
{{
  "candidates": [
    {{"word": "system", "reason": "supersystem的词根"}},
    {{"word": "efficient", "reason": "ineffectively的反义词根"}},
    {{"word": "finance", "reason": "finanzially的词根"}}
  ]
}}

只返回JSON，不要其他内容。"""

        try:
            response = requests.post(
                self.base_url,
                headers={
                    'Authorization': f'Bearer {self.api_key}',
                    'Content-Type': 'application/json'
                },
                json={
                    'model': self.model,
                    'messages': [
                        {
                            'role': 'system',
                            'content': '你是一个专业的英语词汇助手。你的任务是为给定的单词生成合适的候选词。只返回JSON格式的结果。'
                        },
                        {
                            'role': 'user',
                            'content': prompt
                        }
                    ],
                    'temperature': 0.5,
                    'max_tokens': 300
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result.get('choices', [{}])[0].get('message', {}).get('content', '')
                return self._parse_candidates_response(word, content)
            else:
                return {
                    'success': False,
                    'candidates': [],
                    'reason': f'API调用失败: HTTP {response.status_code}'
                }
        
        except Exception as e:
            return {
                'success': False,
                'candidates': [],
                'reason': f'调用LLM时出错: {str(e)}'
            }
    
    def _parse_candidates_response(self, original_word, content):
        """解析候选词响应"""
        try:
            content = content.strip()
            
            if '```json' in content:
                content = content.split('```json')[1].split('```')[0].strip()
            elif '```' in content:
                content = content.split('```')[1].split('```')[0].strip()
            
            result = json.loads(content)
            candidates = result.get('candidates', [])
            
            return {
                'success': True,
                'original': original_word,
                'candidates': candidates,
                'reason': 'success'
            }
        
        except Exception as e:
            return {
                'success': False,
                'candidates': [],
                'reason': f'解析响应失败: {str(e)}'
            }
    
    def select_best_candidate(self, original_word, meaning, candidates_with_status):
        """
        从候选词中选择最有代表性的一个
        
        参数:
            original_word: 原始单词
            meaning: 原始释义
            candidates_with_status: 候选词及其验证状态 [{'word': str, 'verified': bool, 'reason': str}, ...]
        
        返回:
            dict: 最佳候选词信息
        """
        if not self.is_enabled():
            return {
                'success': False,
                'selected': None,
                'reason': 'LLM功能未启用'
            }
        
        # 只考虑验证通过的候选词
        verified_candidates = [c for c in candidates_with_status if c.get('verified', False)]
        
        if not verified_candidates:
            return {
                'success': False,
                'selected': None,
                'reason': '没有验证通过的候选词'
            }
        
        if len(verified_candidates) == 1:
            return {
                'success': True,
                'selected': verified_candidates[0]['word'],
                'reason': '只有一个验证通过的候选词',
                'confidence': 'high'
            }
        
        # 构建候选词列表字符串
        candidates_str = '\n'.join([
            f"{i+1}. {c['word']} - {c.get('reason', '无说明')}"
            for i, c in enumerate(verified_candidates)
        ])
        
        prompt = f"""原单词：{original_word}
释义：{meaning}

以下候选词都是有效的英语单词：
{candidates_str}

请从中选择最有代表性、最值得学习的一个单词。选择标准：
1. 使用频率更高的词
2. 更基础、更核心的词
3. 能覆盖更多派生词的词根
4. 与原释义最相关的词

请以JSON格式返回：
{{
  "selected": "选中的单词",
  "reason": "选择理由",
  "confidence": "high/medium/low"
}}

只返回JSON，不要其他内容。"""

        try:
            response = requests.post(
                self.base_url,
                headers={
                    'Authorization': f'Bearer {self.api_key}',
                    'Content-Type': 'application/json'
                },
                json={
                    'model': self.model,
                    'messages': [
                        {
                            'role': 'system',
                            'content': '你是一个专业的英语教学专家。帮助选择最值得学习的单词。只返回JSON格式的结果。'
                        },
                        {
                            'role': 'user',
                            'content': prompt
                        }
                    ],
                    'temperature': 0.3,
                    'max_tokens': 200
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result.get('choices', [{}])[0].get('message', {}).get('content', '')
                return self._parse_selection_response(content)
            else:
                # 如果API调用失败，返回第一个候选词
                return {
                    'success': True,
                    'selected': verified_candidates[0]['word'],
                    'reason': 'API调用失败，返回第一个候选词',
                    'confidence': 'low'
                }
        
        except Exception as e:
            return {
                'success': True,
                'selected': verified_candidates[0]['word'],
                'reason': f'选择失败: {str(e)}，返回第一个候选词',
                'confidence': 'low'
            }
    
    def _parse_selection_response(self, content):
        """解析选择响应"""
        try:
            content = content.strip()
            
            if '```json' in content:
                content = content.split('```json')[1].split('```')[0].strip()
            elif '```' in content:
                content = content.split('```')[1].split('```')[0].strip()
            
            result = json.loads(content)
            
            return {
                'success': True,
                'selected': result.get('selected', ''),
                'reason': result.get('reason', '无说明'),
                'confidence': result.get('confidence', 'medium')
            }
        
        except Exception as e:
            return {
                'success': False,
                'selected': None,
                'reason': f'解析响应失败: {str(e)}'
            }


def batch_verify_candidates(bbdc_checker, candidates_list):
    """
    批量验证候选词
    
    参数:
        bbdc_checker: 不背单词核对器实例
        candidates_list: 候选词列表
    
    返回:
        dict: 验证结果，key为单词，value为是否验证通过
    """
    if not candidates_list:
        return {}
    
    # 创建临时文件
    temp_file = 'temp_candidates_verify.txt'
    try:
        with open(temp_file, 'w', encoding='utf-8') as f:
            for word in candidates_list:
                f.write(word + '\n')
        
        # 验证
        result = bbdc_checker.upload_word_file(temp_file)
        
        if "error" not in result:
            parsed = bbdc_checker.parse_result(result)
            if "error" not in parsed:
                recognized = set(w.lower() for w in parsed.get('recognized_words', []))
                return {word: (word.lower() in recognized) for word in candidates_list}
        
        return {word: False for word in candidates_list}
        
    finally:
        if os.path.exists(temp_file):
            os.remove(temp_file)


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


def apply_corrections_to_file(file_path, corrections):
    """
    将验证通过的更正应用到文件
    
    参数:
        file_path: 单词文件路径
        corrections: 更正列表
    
    返回:
        bool: 是否成功
    """
    try:
        # 读取文件内容
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 创建备份
        backup_path = file_path + '.backup'
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"📦 已创建备份文件: {os.path.basename(backup_path)}")
        
        # 应用更正
        lines = content.split('\n')
        correction_count = 0
        
        for correction in corrections:
            original = correction['original']
            corrected = correction['corrected']
            
            # 在文件中查找并替换
            for i, line in enumerate(lines):
                if line.strip() == original:
                    lines[i] = corrected
                    correction_count += 1
                    print(f"  ✓ 第{i+1}行: {original} → {corrected}")
        
        # 写回文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        
        print(f"\n✅ 成功替换 {correction_count} 处错误")
        return True
        
    except Exception as e:
        print(f"❌ 应用更正失败: {e}")
        return False


def auto_correct_with_llm(parsed_result, unrecognized_details, llm_corrector, bbdc_checker, original_file_path):
    """
    使用LLM自动更正识别失败的单词，并重新验证
    
    参数:
        parsed_result: 原始核对结果
        unrecognized_details: 识别失败的单词详细信息
        llm_corrector: LLM更正器实例
        bbdc_checker: 不背单词核对器实例
        original_file_path: 原始单词文件路径
    
    返回:
        dict: 更新后的核对结果
    """
    correction_results = []
    corrected_words = []  # 更正后需要验证的单词
    
    print("\n" + "=" * 60)
    print("🤖 LLM自动更正处理")
    print("=" * 60)
    
    # 逐个处理识别失败的单词
    for i, detail in enumerate(unrecognized_details, 1):
        word = detail['word']
        meaning = detail.get('meaning', '')
        
        print(f"\n[{i}/{len(unrecognized_details)}] 处理单词: {word}")
        
        # 调用LLM更正
        correction = llm_corrector.correct_word(word, meaning)
        correction['original_meaning'] = meaning
        correction['line_number'] = detail.get('line_number', '未知')
        correction_results.append(correction)
        
        if correction['success']:
            corrected_word = correction['corrected']
            print(f"  原单词: {word}")
            print(f"  更正为: {corrected_word}")
            print(f"  置信度: {correction['confidence']}")
            print(f"  原因: {correction['reason']}")
            
            # 如果单词被更正了（不同于原单词）
            if corrected_word.lower() != word.lower():
                corrected_words.append(corrected_word)
        else:
            print(f"  ❌ 更正失败: {correction['reason']}")
    
    # 如果有更正后的单词，进行二次验证
    verified_corrections = []
    if corrected_words:
        print(f"\n\n🔍 正在对 {len(corrected_words)} 个更正后的单词进行验证...")
        
        # 创建临时文件包含更正后的单词
        temp_file = original_file_path.replace('.txt', '_llm_corrected_temp.txt')
        try:
            with open(temp_file, 'w', encoding='utf-8') as f:
                for word in corrected_words:
                    f.write(word + '\n')
            
            # 使用不背单词API验证更正后的单词
            verify_result = bbdc_checker.upload_word_file(temp_file)
            
            if "error" not in verify_result:
                verify_parsed = bbdc_checker.parse_result(verify_result)
                
                if "error" not in verify_parsed:
                    verified_recognized = set(w.lower() for w in verify_parsed.get('recognized_words', []))
                    
                    # 标记哪些更正后的单词被成功识别
                    for correction in correction_results:
                        if correction['success']:
                            corrected_word = correction['corrected']
                            if corrected_word.lower() in verified_recognized:
                                correction['verified'] = True
                                correction['verification_status'] = '✅ 验证通过'
                                verified_corrections.append(correction)
                            else:
                                correction['verified'] = False
                                correction['verification_status'] = '❌ 验证失败'
                        else:
                            correction['verified'] = False
                            correction['verification_status'] = '⚠️  未更正'
                else:
                    print(f"⚠️  验证结果解析失败: {verify_parsed.get('error', '未知错误')}")
            else:
                print(f"⚠️  验证请求失败: {verify_result.get('error', '未知错误')}")
            
            # 清理临时文件
            if os.path.exists(temp_file):
                os.remove(temp_file)
                
        except Exception as e:
            print(f"⚠️  验证过程出错: {e}")
    
    # 更新结果
    parsed_result['llm_corrections'] = correction_results
    parsed_result['verified_corrections'] = verified_corrections
    
    # 统计信息
    total_corrections = len(correction_results)
    successful_corrections = sum(1 for c in correction_results if c.get('verified', False))
    failed_corrections = [c for c in correction_results if not c.get('verified', False)]
    
    print("\n" + "=" * 60)
    print(f"📊 LLM更正统计:")
    print(f"  尝试更正: {total_corrections} 个单词")
    print(f"  验证通过: {successful_corrections} 个单词")
    print(f"  验证失败: {len(failed_corrections)} 个单词")
    if total_corrections > 0:
        print(f"  成功率: {successful_corrections/total_corrections*100:.1f}%")
    print("=" * 60)
    
    # 对验证失败的单词自动进行二次处理（生成候选词）
    second_round_results = []
    if failed_corrections and successful_corrections < total_corrections:
        print(f"\n\n🔄 自动对 {len(failed_corrections)} 个验证失败的单词进行二次处理（生成候选词）...")
        
        second_round_results = process_failed_corrections(
            failed_corrections, 
            llm_corrector, 
            bbdc_checker
        )
        
        if second_round_results:
            parsed_result['second_round_corrections'] = second_round_results
            # 将二次处理成功的结果也加入verified_corrections
            for result in second_round_results:
                if result.get('selected_word'):
                    verified_corrections.append({
                        'original': result['original'],
                        'corrected': result['selected_word'],
                        'verified': True,
                        'verification_status': '✅ 二次处理验证通过',
                        'confidence': result.get('confidence', 'medium'),
                        'reason': result.get('reason', ''),
                        'original_meaning': result.get('original_meaning', ''),
                        'line_number': result.get('line_number', '未知')
                    })
    
    # 如果有验证通过的更正，自动应用
    all_corrections_to_apply = verified_corrections
    
    if all_corrections_to_apply:
        print(f"\n\n✅ 共有 {len(all_corrections_to_apply)} 个单词可以更正！")
        print("\n更正列表：")
        for i, correction in enumerate(all_corrections_to_apply, 1):
            status_icon = "🔧" if "二次处理" in correction.get('verification_status', '') else "✓"
            print(f"  {status_icon} {i}. {correction['original']} → {correction['corrected']}")
            if "二次处理" in correction.get('verification_status', ''):
                print(f"      说明: {correction.get('reason', '')}")
        
        print("\n🔧 正在自动应用更正到文件...")
        success = apply_corrections_to_file(original_file_path, all_corrections_to_apply)
        if success:
            parsed_result['corrections_applied'] = True
            print("✅ 更正已成功应用到文件！")
        else:
            parsed_result['corrections_applied'] = False
            print("❌ 应用更正失败")
    
    return parsed_result


def process_failed_corrections(failed_corrections, llm_corrector, bbdc_checker):
    """
    处理验证失败的更正，生成候选词并选择最佳候选
    
    参数:
        failed_corrections: 验证失败的更正列表
        llm_corrector: LLM更正器实例
        bbdc_checker: 不背单词核对器实例
    
    返回:
        list: 二次处理结果
    """
    results = []
    
    print("\n" + "=" * 60)
    print("🔄 二次处理 - 生成候选词")
    print("=" * 60)
    
    for i, correction in enumerate(failed_corrections, 1):
        word = correction['original']
        meaning = correction.get('original_meaning', '')
        
        print(f"\n[{i}/{len(failed_corrections)}] 处理单词: {word}")
        print(f"  释义: {meaning}")
        
        # 生成候选词
        candidates_result = llm_corrector.generate_word_candidates(word, meaning)
        
        if not candidates_result['success'] or not candidates_result['candidates']:
            print(f"  ⚠️  生成候选词失败: {candidates_result.get('reason', '未知原因')}")
            continue
        
        candidates = candidates_result['candidates']
        print(f"  📝 生成了 {len(candidates)} 个候选词:")
        for j, cand in enumerate(candidates, 1):
            print(f"     {j}. {cand['word']} - {cand.get('reason', '')}")
        
        # 提取候选词列表
        candidate_words = [c['word'] for c in candidates]
        
        # 批量验证候选词
        print(f"  🔍 验证候选词...")
        verification_results = batch_verify_candidates(bbdc_checker, candidate_words)
        
        # 标记验证结果
        candidates_with_status = []
        verified_count = 0
        for cand in candidates:
            word_text = cand['word']
            is_verified = verification_results.get(word_text, False)
            candidates_with_status.append({
                'word': word_text,
                'verified': is_verified,
                'reason': cand.get('reason', '')
            })
            if is_verified:
                verified_count += 1
                print(f"     ✓ {word_text} - 验证通过")
            else:
                print(f"     ✗ {word_text} - 验证失败")
        
        if verified_count == 0:
            print(f"  ❌ 所有候选词都验证失败")
            continue
        
        # 选择最佳候选词
        print(f"  🤖 AI选择最有代表性的单词...")
        selection_result = llm_corrector.select_best_candidate(word, meaning, candidates_with_status)
        
        if selection_result['success'] and selection_result['selected']:
            selected = selection_result['selected']
            print(f"  ✅ 选择: {selected}")
            print(f"     理由: {selection_result.get('reason', '')}")
            print(f"     置信度: {selection_result.get('confidence', '')}")
            
            results.append({
                'original': word,
                'selected_word': selected,
                'candidates': candidates_with_status,
                'reason': selection_result.get('reason', ''),
                'confidence': selection_result.get('confidence', ''),
                'original_meaning': meaning,
                'line_number': correction.get('line_number', '未知')
            })
        else:
            print(f"  ⚠️  选择失败: {selection_result.get('reason', '')}")
        
        time.sleep(0.5)  # 避免API限流
    
    print("\n" + "=" * 60)
    print(f"📊 二次处理统计:")
    print(f"  处理单词: {len(failed_corrections)} 个")
    print(f"  成功选择: {len(results)} 个")
    if len(failed_corrections) > 0:
        print(f"  成功率: {len(results)/len(failed_corrections)*100:.1f}%")
    print("=" * 60)
    
    return results


def check_words_with_bbdc(file_path, words_list, original_md_file, use_llm=True):
    """
    使用不背单词核对单词列表
    
    参数:
        file_path: 临时单词文件路径
        words_list: 单词列表
        original_md_file: 原始markdown文件路径
        use_llm: 是否使用LLM自动更正识别失败的单词
    
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
    
    # 使用LLM自动更正识别失败的单词
    if use_llm and parsed_result['unrecognized_details']:
        print(f"\n🤖 检测到 {len(parsed_result['unrecognized_details'])} 个识别失败的单词，正在使用LLM尝试自动更正...")
        llm_corrector = LLMWordCorrector()
        
        if llm_corrector.is_enabled():
            parsed_result = auto_correct_with_llm(
                parsed_result, 
                unrecognized_details, 
                llm_corrector, 
                checker, 
                file_path
            )
        else:
            print("⚠️  LLM功能未启用，跳过自动更正")
    
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
    
    # 显示LLM更正统计
    if 'llm_corrections' in check_result:
        corrections = check_result['llm_corrections']
        verified = check_result.get('verified_corrections', [])
        second_round = check_result.get('second_round_corrections', [])
        
        print(f"\n🤖 LLM自动更正:")
        print(f"  尝试更正: {len(corrections)} 个单词")
        first_round_verified = len([v for v in verified if '二次处理' not in v.get('verification_status', '')])
        print(f"  验证通过: {first_round_verified} 个单词")
        
        if second_round:
            print(f"\n🔄 二次处理（候选词）:")
            print(f"  处理单词: {len([c for c in corrections if not c.get('verified', False)])} 个")
            print(f"  成功选择: {len(second_round)} 个单词")
        
        if check_result.get('corrections_applied'):
            print(f"\n  ✅ 已应用更正到文件")
    
    # 显示识别成功的单词（前10个）
    if check_result['recognized_words']:
        print(f"\n✅ 识别成功的单词（前10个）:")
        for i, word in enumerate(check_result['recognized_words'][:10], 1):
            print(f"  {i:2d}. {word}")
        
        if len(check_result['recognized_words']) > 10:
            print(f"  ... 还有 {len(check_result['recognized_words']) - 10} 个识别成功的单词")
    
    # 显示LLM更正详情
    if 'llm_corrections' in check_result and check_result['llm_corrections']:
        print(f"\n\n🤖 LLM更正详情:")
        print("=" * 80)
        for i, correction in enumerate(check_result['llm_corrections'], 1):
            status = correction.get('verification_status', '未验证')
            print(f"\n  [{i}] {correction['original']} → {correction['corrected']}")
            print(f"      状态: {status}")
            print(f"      置信度: {correction.get('confidence', 'unknown')}")
            print(f"      原因: {correction.get('reason', '无')}")
            print(f"      释义: {correction.get('original_meaning', '无')}")
            print(f"      行号: 第{correction.get('line_number', '未知')}行")
        print("=" * 80)
    
    # 显示二次处理详情
    if 'second_round_corrections' in check_result and check_result['second_round_corrections']:
        print(f"\n\n🔄 二次处理（候选词选择）详情:")
        print("=" * 80)
        for i, result in enumerate(check_result['second_round_corrections'], 1):
            print(f"\n  [{i}] {result['original']} → {result['selected_word']}")
            print(f"      候选词:")
            for cand in result.get('candidates', []):
                status = "✓" if cand.get('verified') else "✗"
                print(f"        {status} {cand['word']} - {cand.get('reason', '')}")
            print(f"      AI选择: {result['selected_word']}")
            print(f"      理由: {result.get('reason', '无')}")
            print(f"      置信度: {result.get('confidence', 'unknown')}")
            print(f"      释义: {result.get('original_meaning', '无')}")
            print(f"      行号: 第{result.get('line_number', '未知')}行")
        print("=" * 80)
    
    # 显示识别不成功的单词（详细信息）
    if check_result['unrecognized_details']:
        source_file = os.path.basename(check_result.get('original_file', '未知文件'))
        word_file = os.path.basename(output_file)
        print(f"\n\n检查这些单词是否有误,你可以通过标明的行数直接阅读该行前后以确定其位置，不用阅读整个文件,如果发现错别字等情况、请询问我得到同意后，对单词文本文件进行修正。\n 识别不成功的单词（详细信息）,源文件【{source_file}】，单词文本文件【{word_file}】:")
        for i, detail in enumerate(check_result['unrecognized_details'], 1):
            print(f"  {i:2d}. {detail['word']:<15} 第{detail['line_number']}行  {detail['meaning']}")
    
    # 自动保存详细结果
    if check_result.get('llm_corrections') or check_result['unrecognized_count'] > 0:
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        detail_output = f"bbdc_check_detail_{timestamp}.txt"
        
        print(f"\n💾 自动保存详细结果到: {detail_output}")
        
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
                
                # 保存LLM更正信息
                if 'llm_corrections' in check_result and check_result['llm_corrections']:
                    f.write("\n" + "=" * 30 + " LLM自动更正详情 " + "=" * 30 + "\n\n")
                    if check_result.get('corrections_applied'):
                        f.write("✅ 更正已应用到文件\n\n")
                    for i, correction in enumerate(check_result['llm_corrections'], 1):
                        f.write(f"{i:3d}. {correction['original']} → {correction['corrected']}\n")
                        f.write(f"     状态: {correction.get('verification_status', '未验证')}\n")
                        f.write(f"     置信度: {correction.get('confidence', 'unknown')}\n")
                        f.write(f"     原因: {correction.get('reason', '无')}\n")
                        f.write(f"     释义: {correction.get('original_meaning', '无')}\n")
                        f.write(f"     行号: 第{correction.get('line_number', '未知')}行\n\n")
                
                f.write("=" * 30 + " 识别成功的单词 " + "=" * 30 + "\n")
                for i, word in enumerate(check_result['recognized_words'], 1):
                    f.write(f"{i:3d}. {word}\n")
                
                f.write("\n" + "=" * 30 + " 识别不成功的单词（详细信息） " + "=" * 30 + "\n")
                f.write(f"源文件: {os.path.basename(check_result.get('original_file', '未知文件'))}\n")
                f.write(f"单词文本文件: {os.path.basename(output_file)}\n\n")
                for i, detail in enumerate(check_result['unrecognized_details'], 1):
                    f.write(f"{i:3d}. {detail['word']:<20} 第{detail['line_number']}行  {detail['meaning']}\n")
            
            print(f"✅ 详细结果已保存")
            
        except Exception as e:
            print(f"❌ 保存详细结果失败: {e}")
    else:
        print("\n💡 提示: 所有单词都已识别成功，无需保存详细报告")


def print_header():
    """打印程序头部"""
    print("\n" + "=" * 60)
    print("           📚 单词提取工具 - Word Extractor")
    print("           支持 PDF 和 Markdown 文件")
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
    print("  支持格式：PDF、Markdown (.md)")
    
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
        
        # 支持 PDF 和 MD 格式
        if not (file_path.lower().endswith('.md') or file_path.lower().endswith('.pdf')):
            print("⚠️  警告：文件不是 .md 或 .pdf 格式，是否继续？(y/n): ", end='')
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


def process_pdf_file(pdf_path, output_dir=None):
    """
    处理 PDF 文件：通过 Mineru API 转换为 Markdown 并提取单词
    
    参数:
        pdf_path: PDF 文件路径
        output_dir: 输出目录
    
    返回:
        str: 生成的 markdown 文件路径，如果失败返回 None
    """
    try:
        from mineru_api import MineruWordExtractor
    except ImportError:
        print("❌ 无法导入 mineru_api 模块，请确保 mineru_api.py 文件存在")
        return None
    
    print(f"\n{'='*60}")
    print(f"📄 检测到 PDF 文件，将通过 Mineru API 处理")
    print(f"{'='*60}\n")
    
    try:
        # 创建 Mineru 提取器
        extractor = MineruWordExtractor()
        
        # 处理 PDF
        result = extractor.process_local_pdf(
            pdf_path,
            output_dir=output_dir,
            auto_extract_words=True,
            is_ocr=True
        )
        
        if result.get('success'):
            # 获取生成的 markdown 文件
            markdown_files = result.get('markdown_files', [])
            if markdown_files:
                return markdown_files[0]  # 返回第一个 markdown 文件
        else:
            print(f"❌ PDF 处理失败: {result.get('error')}")
            return None
    
    except ValueError as e:
        print(f"❌ {str(e)}")
        print("\n💡 请在 .env 文件中配置 MINERU_API_TOKEN")
        print("   Token 获取地址: https://mineru.net/")
        return None
    except Exception as e:
        print(f"❌ 处理 PDF 时出错: {e}")
        return None


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
        
        # 检查文件类型
        is_pdf = input_file.lower().endswith('.pdf')
        
        # 如果是 PDF，先转换为 Markdown
        if is_pdf:
            print("\n🔄 正在通过 Mineru API 处理 PDF...")
            markdown_file = process_pdf_file(input_file)
            
            if not markdown_file:
                print("❌ PDF 处理失败")
                input("\n按回车键继续...")
                continue
            
            print(f"✅ PDF 已转换为 Markdown: {os.path.basename(markdown_file)}")
            print(f"ℹ️  单词已自动提取和核对，查看生成的文件")
            input("\n按回车键继续...")
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
        parser = argparse.ArgumentParser(description='从 PDF 或 Markdown 文件中提取单词')
        parser.add_argument('input_file', help='输入文件路径（支持 PDF 和 Markdown）')
        parser.add_argument('-o', '--output', help='输出文件路径')
        parser.add_argument('-m', '--mode', choices=['full', 'words_only'], default='words_only',
                            help='提取模式：full=完整信息，words_only=仅单词（默认）')
        parser.add_argument('-p', '--phrases', action='store_true',
                            help='是否包含短语（仅在full模式下有效）')
        parser.add_argument('--no-unique', action='store_true',
                            help='不去重（仅在words_only模式下有效）')
        
        args = parser.parse_args()
        
        # 检查文件是否存在
        if not os.path.exists(args.input_file):
            print(f"❌ 文件不存在: {args.input_file}")
            sys.exit(1)
        
        # 检查文件类型
        is_pdf = args.input_file.lower().endswith('.pdf')
        
        if is_pdf:
            # 处理 PDF 文件
            print(f"📄 检测到 PDF 文件，将通过 Mineru API 处理...")
            markdown_file = process_pdf_file(args.input_file, args.output)
            if markdown_file:
                print("\n✅ PDF 处理完成！单词已自动提取和核对")
            else:
                print("\n❌ PDF 处理失败")
                sys.exit(1)
        else:
            # 处理 Markdown 文件
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


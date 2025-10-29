#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
不背单词单词本制作工具 - 优化版GUI
快速启动 + 美观配色
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import os
import sys
from pathlib import Path
import time
from datetime import datetime

# 延迟导入，减少启动时间
def lazy_import():
    """延迟导入模块"""
    global extract_words_from_markdown, extract_words_only, check_words_with_bbdc, find_markdown_files, BBDCWordChecker
    from extract_words import (
        extract_words_from_markdown, 
        extract_words_only, 
        check_words_with_bbdc,
        find_markdown_files
    )
    from bbdc_word_checker import BBDCWordChecker


class FastGUI:
    """快速启动的GUI界面"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("📚 不背单词单词本制作工具")
        self.root.geometry("900x650")
        self.root.minsize(700, 500)
        
        # 更美观的配色方案 - 深色主题
        self.colors = {
            'primary': '#FF6B35',      # 主色调 - 活力橙
            'secondary': '#004E89',   # 辅助色 - 深蓝
            'success': '#2ECC71',     # 成功色 - 绿色
            'warning': '#E74C3C',     # 警告色 - 红色
            'info': '#3498DB',        # 信息色 - 蓝色
            'background': '#2C3E50',  # 背景色 - 深灰蓝
            'surface': '#34495E',     # 表面色 - 中灰
            'surface_alt': '#2C3E50', # 备用表面色
            'text': '#ECF0F1',       # 文字色 - 浅色
            'text_light': '#BDC3C7',  # 浅文字色 - 中浅色
            'border': '#7F8C8D',     # 边框色 - 中灰
            'hover': '#34495E'       # 悬停色
        }
        
        # 设置窗口样式
        self.setup_window()
        
        # 创建界面（简化版）
        self.create_simple_widgets()
        
        # 状态变量
        self.current_file = None
        self.processing = False
        self.status_var = tk.StringVar(value="就绪")
        self.time_var = tk.StringVar()
        
        # 延迟加载模块
        self.modules_loaded = False
        
        # 更新时间
        self.update_time()
        
    def setup_window(self):
        """设置窗口样式"""
        # 设置窗口背景色
        self.root.configure(bg=self.colors['background'])
        
        # 设置窗口图标（如果有的话）
        try:
            # 这里可以添加图标文件
            pass
        except:
            pass
            
    def create_simple_widgets(self):
        """创建简化的界面组件"""
        # 主容器
        main_frame = tk.Frame(self.root, bg=self.colors['background'], padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        title_label = tk.Label(main_frame, text="📚 不背单词单词本制作工具", 
                              font=('Microsoft YaHei', 18, 'bold'),
                              fg=self.colors['primary'],
                              bg=self.colors['background'])
        title_label.pack(pady=(0, 20))
        
        # 创建选项卡
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        # 配置选项卡样式
        style = ttk.Style()
        style.configure('TNotebook', background=self.colors['background'])
        style.configure('TNotebook.Tab', padding=[15, 8], background=self.colors['surface'])
        
        # 单词提取选项卡
        self.create_extract_tab()
        
        # 词书核对选项卡
        self.create_check_tab()
        
        # 状态栏
        self.create_status_bar(main_frame)
        
    def create_extract_tab(self):
        """创建单词提取选项卡"""
        extract_frame = tk.Frame(self.notebook, bg=self.colors['background'])
        self.notebook.add(extract_frame, text="📝 单词提取")
        
        # 文件选择区域
        file_frame = tk.LabelFrame(extract_frame, text="📂 文件选择", 
                                 font=('Microsoft YaHei', 12, 'bold'),
                                 fg=self.colors['text'],
                                 bg=self.colors['surface'],
                                 padx=15, pady=15)
        file_frame.pack(fill=tk.X, padx=20, pady=(20, 10))
        
        tk.Label(file_frame, text="Markdown文件:", 
                font=('Microsoft YaHei', 10),
                fg=self.colors['text'],
                bg=self.colors['surface']).pack(anchor=tk.W)
        
        file_input_frame = tk.Frame(file_frame, bg=self.colors['surface'])
        file_input_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.file_var = tk.StringVar()
        self.file_entry = tk.Entry(file_input_frame, textvariable=self.file_var, 
                                  state='readonly',
                                  font=('Microsoft YaHei', 10),
                                  bg=self.colors['background'],
                                  fg=self.colors['text'],
                                  insertbackground=self.colors['text'])
        self.file_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        tk.Button(file_input_frame, text="📁 浏览", 
                 command=self.select_file,
                 font=('Microsoft YaHei', 10, 'bold'),
                 bg=self.colors['primary'],
                 fg='white',
                 relief=tk.FLAT,
                 padx=20).pack(side=tk.RIGHT)
        
        # 提取选项区域
        options_frame = tk.LabelFrame(extract_frame, text="⚙️ 提取选项", 
                                    font=('Microsoft YaHei', 12, 'bold'),
                                    fg=self.colors['text'],
                                    bg=self.colors['surface'],
                                    padx=15, pady=15)
        options_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # 提取模式
        mode_frame = tk.Frame(options_frame, bg=self.colors['surface'])
        mode_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(mode_frame, text="提取模式:", 
                font=('Microsoft YaHei', 10),
                fg=self.colors['text'],
                bg=self.colors['surface']).pack(anchor=tk.W)
        
        self.extract_mode = tk.StringVar(value="words_only")
        
        modes_frame = tk.Frame(mode_frame, bg=self.colors['surface'])
        modes_frame.pack(fill=tk.X, pady=(5, 0))
        
        tk.Radiobutton(modes_frame, text="仅单词（每行一个）", 
                      variable=self.extract_mode, value="words_only",
                      font=('Microsoft YaHei', 9),
                      fg=self.colors['text'],
                      bg=self.colors['surface'],
                      selectcolor=self.colors['primary'],
                      activebackground=self.colors['surface']).pack(anchor=tk.W)
        
        tk.Radiobutton(modes_frame, text="单词+词义", 
                      variable=self.extract_mode, value="words_with_meaning",
                      font=('Microsoft YaHei', 9),
                      fg=self.colors['text'],
                      bg=self.colors['surface'],
                      selectcolor=self.colors['primary'],
                      activebackground=self.colors['surface']).pack(anchor=tk.W)
        
        tk.Radiobutton(modes_frame, text="单词+短语+词义", 
                      variable=self.extract_mode, value="full",
                      font=('Microsoft YaHei', 9),
                      fg=self.colors['text'],
                      bg=self.colors['surface'],
                      selectcolor=self.colors['primary'],
                      activebackground=self.colors['surface']).pack(anchor=tk.W)
        
        # 其他选项
        options_frame2 = tk.Frame(options_frame, bg=self.colors['surface'])
        options_frame2.pack(fill=tk.X, pady=(10, 0))
        
        self.unique_var = tk.BooleanVar(value=True)
        tk.Checkbutton(options_frame2, text="去重", 
                      variable=self.unique_var,
                      font=('Microsoft YaHei', 9),
                      fg=self.colors['text'],
                      bg=self.colors['surface'],
                      selectcolor=self.colors['primary'],
                      activebackground=self.colors['surface']).pack(side=tk.LEFT, padx=(0, 20))
        
        self.auto_check_var = tk.BooleanVar(value=True)
        tk.Checkbutton(options_frame2, text="自动核对", 
                      variable=self.auto_check_var,
                      font=('Microsoft YaHei', 9),
                      fg=self.colors['text'],
                      bg=self.colors['surface'],
                      selectcolor=self.colors['primary'],
                      activebackground=self.colors['surface']).pack(side=tk.LEFT)
        
        # 输出设置
        output_frame = tk.LabelFrame(extract_frame, text="💾 输出设置", 
                                   font=('Microsoft YaHei', 12, 'bold'),
                                   fg=self.colors['text'],
                                   bg=self.colors['surface'],
                                   padx=15, pady=15)
        output_frame.pack(fill=tk.X, padx=20, pady=10)
        
        tk.Label(output_frame, text="输出文件:", 
                font=('Microsoft YaHei', 10),
                fg=self.colors['text'],
                bg=self.colors['surface']).pack(anchor=tk.W)
        
        output_input_frame = tk.Frame(output_frame, bg=self.colors['surface'])
        output_input_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.output_var = tk.StringVar()
        self.output_entry = tk.Entry(output_input_frame, textvariable=self.output_var,
                                    font=('Microsoft YaHei', 10),
                                    bg=self.colors['background'],
                                    fg=self.colors['text'],
                                    insertbackground=self.colors['text'])
        self.output_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        tk.Button(output_input_frame, text="📁 浏览", 
                 command=self.select_output_file,
                 font=('Microsoft YaHei', 10, 'bold'),
                 bg=self.colors['secondary'],
                 fg='white',
                 relief=tk.FLAT,
                 padx=20).pack(side=tk.RIGHT)
        
        # 操作按钮
        button_frame = tk.Frame(extract_frame, bg=self.colors['background'])
        button_frame.pack(fill=tk.X, padx=20, pady=20)
        
        self.extract_btn = tk.Button(button_frame, text="🚀 开始提取", 
                                    command=self.start_extract,
                                    font=('Microsoft YaHei', 12, 'bold'),
                                    bg=self.colors['primary'],
                                    fg='white',
                                    relief=tk.FLAT,
                                    padx=30, pady=10)
        self.extract_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        tk.Button(button_frame, text="📋 预览结果", 
                 command=self.preview_result,
                 font=('Microsoft YaHei', 12, 'bold'),
                 bg=self.colors['success'],
                 fg='white',
                 relief=tk.FLAT,
                 padx=30, pady=10).pack(side=tk.LEFT, padx=(0, 10))
        
        tk.Button(button_frame, text="🗑️ 清空", 
                 command=self.clear_extract,
                 font=('Microsoft YaHei', 12, 'bold'),
                 bg=self.colors['warning'],
                 fg='white',
                 relief=tk.FLAT,
                 padx=30, pady=10).pack(side=tk.LEFT)
        
        # 结果显示区域
        result_frame = tk.LabelFrame(extract_frame, text="📊 提取结果", 
                                   font=('Microsoft YaHei', 12, 'bold'),
                                   fg=self.colors['text'],
                                   bg=self.colors['surface'],
                                   padx=15, pady=15)
        result_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))
        
        self.result_text = scrolledtext.ScrolledText(result_frame, 
                                                    font=('Consolas', 10),
                                                    bg=self.colors['background'],
                                                    fg=self.colors['text'],
                                                    insertbackground=self.colors['text'],
                                                    wrap=tk.WORD,
                                                    width=80,
                                                    height=15)
        self.result_text.pack(fill=tk.BOTH, expand=True)
        
    def create_check_tab(self):
        """创建词书核对选项卡"""
        check_frame = tk.Frame(self.notebook, bg=self.colors['background'])
        self.notebook.add(check_frame, text="🔍 词书核对")
        
        # 文件选择区域
        file_frame = tk.LabelFrame(check_frame, text="📂 文件选择", 
                                 font=('Microsoft YaHei', 12, 'bold'),
                                 fg=self.colors['text'],
                                 bg=self.colors['surface'],
                                 padx=15, pady=15)
        file_frame.pack(fill=tk.X, padx=20, pady=(20, 10))
        
        tk.Label(file_frame, text="单词文件:", 
                font=('Microsoft YaHei', 10),
                fg=self.colors['text'],
                bg=self.colors['surface']).pack(anchor=tk.W)
        
        file_input_frame = tk.Frame(file_frame, bg=self.colors['surface'])
        file_input_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.check_file_var = tk.StringVar()
        self.check_file_entry = tk.Entry(file_input_frame, textvariable=self.check_file_var, 
                                        state='readonly',
                                        font=('Microsoft YaHei', 10),
                                        bg=self.colors['background'],
                                        fg=self.colors['text'],
                                        insertbackground=self.colors['text'])
        self.check_file_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        tk.Button(file_input_frame, text="📁 浏览", 
                 command=self.select_check_file,
                 font=('Microsoft YaHei', 10, 'bold'),
                 bg=self.colors['primary'],
                 fg='white',
                 relief=tk.FLAT,
                 padx=20).pack(side=tk.RIGHT)
        
        # 操作按钮
        button_frame = tk.Frame(check_frame, bg=self.colors['background'])
        button_frame.pack(fill=tk.X, padx=20, pady=20)
        
        self.check_btn = tk.Button(button_frame, text="🔍 开始核对", 
                                 command=self.start_check,
                                 font=('Microsoft YaHei', 12, 'bold'),
                                 bg=self.colors['info'],
                                 fg='white',
                                 relief=tk.FLAT,
                                 padx=30, pady=10)
        self.check_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        tk.Button(button_frame, text="🗑️ 清空", 
                 command=self.clear_check,
                 font=('Microsoft YaHei', 12, 'bold'),
                 bg=self.colors['warning'],
                 fg='white',
                 relief=tk.FLAT,
                 padx=30, pady=10).pack(side=tk.LEFT)
        
        # 结果显示区域
        result_frame = tk.LabelFrame(check_frame, text="📊 核对结果", 
                                   font=('Microsoft YaHei', 12, 'bold'),
                                   fg=self.colors['text'],
                                   bg=self.colors['surface'],
                                   padx=15, pady=15)
        result_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))
        
        self.check_result_text = scrolledtext.ScrolledText(result_frame, 
                                                          font=('Consolas', 10),
                                                          bg=self.colors['background'],
                                                          fg=self.colors['text'],
                                                          insertbackground=self.colors['text'])
        self.check_result_text.pack(fill=tk.BOTH, expand=True)
        
    def create_status_bar(self, parent):
        """创建状态栏"""
        status_frame = tk.Frame(parent, bg=self.colors['background'])
        status_frame.pack(fill=tk.X, pady=(20, 0))
        
        self.status_var = tk.StringVar(value="就绪")
        tk.Label(status_frame, textvariable=self.status_var, 
                font=('Microsoft YaHei', 9),
                fg=self.colors['text_light'],
                bg=self.colors['background']).pack(side=tk.LEFT)
        
        # 时间显示
        self.time_var = tk.StringVar()
        tk.Label(status_frame, textvariable=self.time_var, 
                font=('Microsoft YaHei', 9),
                fg=self.colors['text_light'],
                bg=self.colors['background']).pack(side=tk.RIGHT)
        
    def update_time(self):
        """更新时间显示"""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.time_var.set(current_time)
        self.root.after(1000, self.update_time)
        
    def load_modules(self):
        """延迟加载模块"""
        if not self.modules_loaded:
            try:
                lazy_import()
                self.modules_loaded = True
                self.status_var.set("模块加载完成")
            except Exception as e:
                messagebox.showerror("错误", f"模块加载失败: {str(e)}")
                return False
        return True
        
    def select_file(self):
        """选择文件"""
        file_path = filedialog.askopenfilename(
            title="选择Markdown文件",
            filetypes=[("Markdown files", "*.md"), ("All files", "*.*")]
        )
        if file_path:
            self.file_var.set(file_path)
            self.current_file = file_path
            self.update_output_filename()
            self.status_var.set(f"已选择文件: {os.path.basename(file_path)}")
            
    def select_check_file(self):
        """选择核对文件"""
        file_path = filedialog.askopenfilename(
            title="选择单词文件",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if file_path:
            self.check_file_var.set(file_path)
            self.status_var.set(f"已选择核对文件: {os.path.basename(file_path)}")
            
    def select_output_file(self):
        """选择输出文件"""
        file_path = filedialog.asksaveasfilename(
            title="保存输出文件",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if file_path:
            self.output_var.set(file_path)
            
    def update_output_filename(self):
        """更新输出文件名"""
        if self.current_file:
            base_name = Path(self.current_file).stem
            mode = self.extract_mode.get()
            
            if mode == "words_only":
                default_name = f"{base_name}_单词.txt"
            elif mode == "words_with_meaning":
                default_name = f"{base_name}_单词词义.txt"
            else:  # full
                default_name = f"{base_name}_完整.txt"
                
            self.output_var.set(default_name)
            
    def start_extract(self):
        """开始提取"""
        if not self.load_modules():
            return
            
        if not self.file_var.get():
            messagebox.showerror("错误", "请先选择Markdown文件")
            return
            
        if not self.output_var.get():
            messagebox.showerror("错误", "请设置输出文件路径")
            return
            
        # 在新线程中执行提取
        self.processing = True
        self.extract_btn.config(state='disabled')
        self.status_var.set("正在提取单词...")
        
        thread = threading.Thread(target=self.extract_worker)
        thread.daemon = True
        thread.start()
        
    def extract_worker(self):
        """提取工作线程"""
        try:
            input_file = self.file_var.get()
            output_file = self.output_var.get()
            mode = self.extract_mode.get()
            unique = self.unique_var.get()
            auto_check = self.auto_check_var.get()
            
            # 执行提取
            if mode == "words_only":
                words = extract_words_only(input_file, output_file, unique, auto_check)
                result_text = f"✅ 提取完成！\n共提取 {len(words)} 个单词\n\n前20个单词:\n"
                for i, word in enumerate(words[:20], 1):
                    result_text += f"{i:2d}. {word}\n"
                if len(words) > 20:
                    result_text += f"... 还有 {len(words) - 20} 个单词"
                    
            elif mode == "words_with_meaning":
                words_data = extract_words_from_markdown(input_file, output_file, include_phrases=False)
                result_text = f"✅ 提取完成！\n共提取 {len(words_data)} 个单词\n\n前10个单词:\n"
                for i, item in enumerate(words_data[:10], 1):
                    result_text += f"{i:2d}. {item['word']:<15} {item['meaning']}\n"
                if len(words_data) > 10:
                    result_text += f"... 还有 {len(words_data) - 10} 个单词"
                    
            else:  # full
                words_data, phrases_data = extract_words_from_markdown(input_file, output_file, include_phrases=True)
                result_text = f"✅ 提取完成！\n共提取 {len(words_data)} 个单词，{len(phrases_data)} 个短语\n\n"
                result_text += "前10个单词:\n"
                for i, item in enumerate(words_data[:10], 1):
                    result_text += f"{i:2d}. {item['word']:<15} {item['meaning']}\n"
                if len(words_data) > 10:
                    result_text += f"... 还有 {len(words_data) - 10} 个单词\n"
                    
                if phrases_data:
                    result_text += "\n前5个短语:\n"
                    for i, item in enumerate(phrases_data[:5], 1):
                        result_text += f"{i:2d}. {item['phrase']:<20} {item['meaning']}\n"
                    if len(phrases_data) > 5:
                        result_text += f"... 还有 {len(phrases_data) - 5} 个短语"
            
            # 更新UI
            self.root.after(0, lambda: self.extract_complete(result_text))
            
        except Exception as e:
            error_msg = f"❌ 提取失败: {str(e)}"
            self.root.after(0, lambda: self.extract_complete(error_msg))
            
    def extract_complete(self, result_text):
        """提取完成"""
        self.processing = False
        self.extract_btn.config(state='normal')
        self.status_var.set("提取完成")
        
        # 显示结果
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(1.0, result_text)
        
        # 显示完成消息
        messagebox.showinfo("完成", "单词提取完成！")
        
    def preview_result(self):
        """预览结果"""
        if not self.output_var.get() or not os.path.exists(self.output_var.get()):
            messagebox.showwarning("警告", "请先完成提取或选择有效的输出文件")
            return
            
        try:
            with open(self.output_var.get(), 'r', encoding='utf-8') as f:
                content = f.read()
                
            # 显示前500个字符
            preview_content = content[:500]
            if len(content) > 500:
                preview_content += "\n\n... (内容已截断，完整内容请查看文件)"
                
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(1.0, f"📋 文件预览:\n\n{preview_content}")
            
        except Exception as e:
            messagebox.showerror("错误", f"预览失败: {str(e)}")
            
    def clear_extract(self):
        """清空提取区域"""
        self.file_var.set("")
        self.output_var.set("")
        self.result_text.delete(1.0, tk.END)
        self.current_file = None
        self.status_var.set("已清空")
        
    def start_check(self):
        """开始核对"""
        if not self.load_modules():
            return
            
        if not self.check_file_var.get():
            messagebox.showerror("错误", "请先选择单词文件")
            return
            
        # 在新线程中执行核对
        self.processing = True
        self.check_btn.config(state='disabled')
        self.status_var.set("正在核对单词...")
        
        thread = threading.Thread(target=self.check_worker)
        thread.daemon = True
        thread.start()
        
    def check_worker(self):
        """核对工作线程"""
        try:
            file_path = self.check_file_var.get()
            checker = BBDCWordChecker()
            
            # 上传文件
            result = checker.upload_word_file(file_path)
            
            if "error" in result:
                error_msg = f"❌ 核对失败: {result['error']}"
                self.root.after(0, lambda: self.check_complete(error_msg))
                return
                
            # 解析结果
            parsed_result = checker.parse_result(result)
            
            if "error" in parsed_result:
                error_msg = f"❌ 解析失败: {parsed_result['error']}"
                self.root.after(0, lambda: self.check_complete(error_msg))
                return
                
            # 格式化结果
            result_text = f"📊 不背单词词书核对结果\n"
            result_text += "=" * 50 + "\n\n"
            result_text += f"📈 统计信息:\n"
            result_text += f"  总单词数: {parsed_result['total_count']}\n"
            result_text += f"  识别成功: {parsed_result['recognized_count']}\n"
            result_text += f"  识别不成功: {parsed_result['unrecognized_count']}\n"
            result_text += f"  识别成功率: {parsed_result['recognized_count']/parsed_result['total_count']*100:.1f}%\n\n"
            
            # 显示识别成功的单词（前20个）
            if parsed_result['recognized_words']:
                result_text += "✅ 识别成功的单词（前20个）:\n"
                for i, word in enumerate(parsed_result['recognized_words'][:20], 1):
                    result_text += f"  {i:2d}. {word}\n"
                if len(parsed_result['recognized_words']) > 20:
                    result_text += f"  ... 还有 {len(parsed_result['recognized_words']) - 20} 个\n\n"
            
            # 显示识别不成功的单词（前20个）
            if parsed_result['unrecognized_words']:
                result_text += "❓ 识别不成功的单词（前20个）:\n"
                for i, word in enumerate(parsed_result['unrecognized_words'][:20], 1):
                    result_text += f"  {i:2d}. {word}\n"
                if len(parsed_result['unrecognized_words']) > 20:
                    result_text += f"  ... 还有 {len(parsed_result['unrecognized_words']) - 20} 个"
            
            # 保存结果
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            output_file = f"bbdc_check_result_{timestamp}.txt"
            checker.save_result(parsed_result, output_file)
            result_text += f"\n\n💾 结果已保存到: {output_file}"
            
            # 更新UI
            self.root.after(0, lambda: self.check_complete(result_text))
            
        except Exception as e:
            error_msg = f"❌ 核对失败: {str(e)}"
            self.root.after(0, lambda: self.check_complete(error_msg))
            
    def check_complete(self, result_text):
        """核对完成"""
        self.processing = False
        self.check_btn.config(state='normal')
        self.status_var.set("核对完成")
        
        # 显示结果
        self.check_result_text.delete(1.0, tk.END)
        self.check_result_text.insert(1.0, result_text)
        
        # 显示完成消息
        messagebox.showinfo("完成", "词书核对完成！")
        
    def clear_check(self):
        """清空核对区域"""
        self.check_file_var.set("")
        self.check_result_text.delete(1.0, tk.END)
        self.status_var.set("已清空")
        
    def run(self):
        """运行GUI"""
        self.root.mainloop()


def main():
    """主函数"""
    try:
        app = FastGUI()
        app.run()
    except Exception as e:
        messagebox.showerror("错误", f"程序启动失败: {str(e)}")


if __name__ == '__main__':
    main()

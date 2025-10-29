# 不背单词词书制作工具

一个帮助你从 Markdown 文件中提取单词，并自动核对的小工具。最近加入了 AI 自动更正功能，可以智能识别并修正拼写错误。

## 快速开始

### 安装

```bash
pip install -r requirements.txt
```

### 基础使用

直接运行程序，按提示操作：

```bash
python extract_words.py
```

程序会提示你选择 Markdown 文件，然后自动提取单词并核对。

## 主要功能

### 单词提取

从 Markdown 表格中提取单词，支持：
- 自动识别单词和短语
- 去除重复单词
- 批量处理多个文件

### 自动核对

提取后自动对接不背单词 API 进行核对，告诉你哪些单词识别成功，哪些识别失败。

### AI 智能更正（新功能）

对于识别失败的单词，程序会：

1. **第一轮更正**：使用 AI 分析拼写错误并自动修正
2. **第二轮处理**：如果第一轮失败，AI 会生成候选词（比如词根、派生词）
3. **智能选择**：从多个候选词中自动选择最值得学习的
4. **自动替换**：验证通过后直接更新文件（会自动备份）

**举个例子**：

```
supersystem（无法识别）
  → AI分析：这是个复合词
  → 生成候选：system, super, systematic
  → 验证通过：都能识别
  → AI选择：system（最基础的词根）
  → 自动替换：supersystem → system
```

## 配置 AI 功能

需要硅基流动平台的 API 密钥（免费注册：https://siliconflow.cn）

在项目目录创建 `.env` 文件：

```env
SILICONFLOW_API_KEY=你的密钥
```

或者设置环境变量：

```bash
# Windows
set SILICONFLOW_API_KEY=你的密钥

# Linux/Mac  
export SILICONFLOW_API_KEY=你的密钥
```

## 工作流程

完整的处理流程是这样的：

1. 从 Markdown 提取单词 → 保存到 txt 文件
2. 自动调用不背单词 API 核对
3. 识别失败的单词 → AI 尝试修正
4. 修正失败的 → AI 生成词根等候选词
5. 全部验证通过后 → 自动替换并备份

整个过程全自动，你只需要在最开始选择文件。

## 文件说明

- `extract_words.py` - 主程序（命令行版）
- `fast_gui.py` - GUI 图形界面版本
- `bbdc_word_checker.py` - 不背单词核对模块
- `requirements.txt` - 依赖包列表

## 使用建议

- 第一次用建议先测试小文件
- AI 处理需要时间，耐心等待
- 查看生成的详细报告了解所有更正
- 如果不满意，可以用 .backup 备份文件恢复

## 注意事项

- 需要网络连接（调用 API）
- 文件编码需要是 UTF-8
- AI 更正不是 100% 准确，建议复核结果
- 不背单词 API 有时会超时，重试即可

## 技术栈

- Python 3.6+
- BeautifulSoup4 - HTML 解析
- Requests - HTTP 请求
- Kimi AI - 智能更正（可选）

---

有问题欢迎提 Issue，觉得好用的话给个 Star 吧~ ⭐

# BBDC Word Tool - Python版本

不背单词词书制作工具的Python实现版本。

## 特性

- ✅ 功能完整，已验证稳定
- 🎨 支持GUI和CLI两种界面
- 🤖 集成LLM自动更正
- 📄 支持PDF转Markdown（需要Mineru API）
- 🔍 自动核对单词

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量（可选）

创建 `.env` 文件：

```env
# LLM自动更正功能（可选）
SILICONFLOW_API_KEY=your_key_here

# PDF处理功能（可选）
MINERU_API_TOKEN=your_token_here
```

### 3. 运行程序

**命令行版本：**
```bash
python extract_words.py
```

**GUI版本：**
```bash
python fast_gui.py
```

## 一键构建

双击运行 `build.bat` 即可：
- 自动安装依赖
- 可选打包为exe文件

## 打包为可执行文件

```bash
# 使用build.bat（推荐）
build.bat

# 或手动打包
pyinstaller --onefile --name bbdc_word_tool extract_words.py
```

生成的exe文件在 `dist/` 目录下。

## 使用说明

### 命令行模式

```bash
# 交互模式
python extract_words.py

# 提取单词
python extract_words.py input.md -o output.txt

# 提取单词+词义
python extract_words.py input.md -m full
```

### GUI模式

```bash
python fast_gui.py
```

图形界面提供：
- 文件选择
- 提取选项配置
- 实时结果预览
- 自动核对

## 文件说明

| 文件 | 说明 |
|------|------|
| `extract_words.py` | 主程序（CLI） |
| `fast_gui.py` | GUI界面 |
| `bbdc_word_checker.py` | 不背单词API核对模块 |
| `env_loader.py` | 环境变量加载 |
| `mineru_api.py` | Mineru API对接（PDF处理） |
| `requirements.txt` | 依赖列表 |
| `build.bat` | 构建脚本 |

## 依赖

- Python 3.6+
- beautifulsoup4
- requests
- lxml
- tqdm

## 优点

- ✅ 开发快速，迭代方便
- ✅ 功能完整，久经验证
- ✅ GUI界面成熟
- ✅ 跨平台支持好

## 缺点

- ⚠️  启动速度较慢（~1-2秒）
- ⚠️  需要Python环境或打包后体积较大（~30MB）
- ⚠️  性能中等

## 与Rust版本对比

| 特性 | Python版本 | Rust版本 |
|------|-----------|----------|
| 启动速度 | ~1-2秒 | <0.1秒 |
| 内存占用 | ~50MB | ~5MB |
| 开发效率 | 高 | 中 |
| 性能 | 中 | 高 |
| 二进制大小 | ~30MB | ~8MB |
| GUI | 完整 | 开发中 |

## 故障排除

### 导入错误

```bash
# 重新安装依赖
pip install -r requirements.txt --force-reinstall
```

### 编码错误

确保文件是UTF-8编码。

### API超时

检查网络连接，或增加超时时间。

## 贡献

欢迎提交Issue和Pull Request！

## 许可证

MIT License




# BBDC Word Tool - 不背单词词书制作工具

从 Markdown 提取单词并自动核对。提供 **Python** 和 **Rust** 两个版本。

## 快速开始

### Python 版本（推荐新手）
```bash
cd python
pip install -r requirements.txt
python extract_words.py           # CLI
python fast_gui.py                # GUI
```

### Rust 版本（推荐性能）
```bash
cd rust
cargo build --release
.\target\release\bbdc_word_tool.exe --help
```

## 版本对比

| 特性 | Python | Rust |
|------|--------|------|
| 启动速度 | ~1-2秒 | **<0.1秒** |
| 内存占用 | ~50MB | **~5MB** |
| GUI界面 | ✅ 完整 | ❌ |
| PDF处理 | ✅ | ❌ |

## 核心功能

- 📝 从 Markdown 表格提取单词
- 🔍 不背单词 API 自动核对
- 🤖 LLM 智能更正（可选）

## 配置（可选）

创建 `.env` 文件：
```env
SILICONFLOW_API_KEY=your_key_here  # LLM更正
MINERU_API_TOKEN=your_token_here   # PDF处理（Python版）
```

## 使用示例

**Python:**
```bash
python extract_words.py input.md
```

**Rust:**
```bash
bbdc_word_tool extract input.md
```

## 文档

- [Python 版本](python/README.md)
- [Rust 版本](rust/README.md)

## 许可证

MIT License

---

⭐ 觉得有用？给个 Star！

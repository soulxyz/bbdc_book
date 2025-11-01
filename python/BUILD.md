# 打包说明

本项目支持自动打包成 Windows 可执行文件 (.exe)，无需 Python 环境即可运行。

## 🚀 自动打包（GitHub Actions）

### 触发方式

1. **推送到主分支**：每次 push 到 `main` 或 `master` 分支都会自动构建
2. **创建版本标签**：
   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   ```
   会自动创建 Release 并上传打包文件

3. **手动触发**：在 GitHub 仓库的 Actions 页面手动运行

### 产物下载

- **开发构建**：在 Actions 页面的 Artifacts 中下载（保留 30 天）
  - bbdc_word_tool.exe
  - .env.example
- **正式版本**：在 Releases 页面下载（两个独立文件，无需解压）
  - 💡 exe 使用英文名避免编码问题，下载后可重命名为中文

## 🔨 本地打包

### 手动打包

```bash
# 安装 PyInstaller
pip install pyinstaller

# 打包主程序（带控制台，使用英文名避免问题）
pyinstaller --onefile --console --name=bbdc_word_tool ^
  --hidden-import=bs4 ^
  --hidden-import=lxml ^
  --hidden-import=requests ^
  --hidden-import=tqdm ^
  --hidden-import=env_loader ^
  --collect-all tqdm ^
  extract_words.py

# 打包后的文件在 dist/bbdc_word_tool.exe
# 可以手动重命名为中文名
```

打包后的文件在 `dist/` 目录下。

**重要注意事项**：
- ✅ 必须使用 `--console` 参数（否则程序无法接收用户输入）
- ✅ 必须添加 `--hidden-import=tqdm` 和 `--collect-all tqdm`（进度条支持）
- ⚠️ 建议使用英文文件名打包，避免中文编码问题

## 📦 打包内容

Release 页面提供的文件：

```
Release Assets:
├── bbdc_word_tool.exe           # 主程序（支持 PDF 和 Markdown）
└── .env.example                 # 配置文件示例
```

**简洁设计**：
- ✅ 只有必需的两个文件
- ✅ 无需解压缩
- ✅ 下载即用
- ✅ 使用英文名避免编码问题（可自行重命名为中文）

## ⚙️ 配置

打包后的程序仍需要配置 `.env` 文件：

1. 将 `.env.example` 重命名为 `.env`
2. **重要**：将 `.env` 文件放在 **exe 所在目录**（与 exe 同级）
3. 填入你的 API Token：
   ```
   MINERU_API_TOKEN=your_token_here
   SILICONFLOW_API_KEY=your_key_here
   ```

**文件结构示例**：
```
你的文件夹/
├── bbdc_word_tool.exe      ← 主程序（可重命名为中文）
└── .env                    ← 配置文件（从 .env.example 重命名）
```

**查找顺序**：程序会按以下顺序查找 .env 文件：
1. 当前工作目录
2. exe 所在目录
3. 脚本所在目录（开发环境）

## 🐛 常见问题

### Q: 打包失败？
A: 确保已安装所有依赖：
```bash
pip install -r requirements.txt
pip install pyinstaller
```

### Q: 打包出来的是 default.exe？
A: 这是因为 `--name` 参数中的中文字符导致的。解决方法：
- 使用英文名打包：`--name=bbdc_word_tool`
- 打包完成后手动重命名

### Q: exe 运行一闪而过，没有任何反应？
A: 可能的原因：
1. **缺少 hidden-import**：确保添加了所有必需的 hidden-import 参数
   ```bash
   --hidden-import=tqdm --collect-all tqdm
   ```
2. **缺少 console 参数**：必须使用 `--console` 而不是 `--windowed`
3. **依赖缺失**：在 CMD 中运行查看错误信息：
   ```cmd
   cd dist
   .\bbdc_word_tool.exe
   ```

### Q: exe 文件太大？
A: 这是正常的，PyInstaller 会打包 Python 运行时和所有依赖库（通常 15-30 MB）。

### Q: 出现 "input(): lost sys.stdin" 错误？
A: 打包时必须使用 `--console` 参数，不能使用 `--windowed` 或 `--noconsole`。

### Q: 杀毒软件报毒？
A: 这是 PyInstaller 打包的 exe 常见误报，可以添加白名单。或使用官方 Release 的文件。

### Q: 提示找不到 .env 文件或 API Token？
A: 
1. **确保 .env 文件与 exe 在同一目录下**
2. 检查文件名是否正确（是 `.env` 不是 `.env.txt`）
3. 在 Windows 中显示文件扩展名：文件资源管理器 → 查看 → 勾选"文件扩展名"
4. 程序会显示它查找过的路径，根据提示放置 .env 文件

### Q: 无法运行？
A: 
1. 检查是否配置了 `.env` 文件（处理 PDF 必须）
2. 确保有网络连接（调用 API 需要）
3. 查看控制台输出的错误信息和提示

## 📝 版本发布流程

1. 更新代码并测试
2. 更新 README.md 中的版本信息
3. 提交代码：
   ```bash
   git add .
   git commit -m "Release v1.0.0"
   git push
   ```
4. 创建标签：
   ```bash
   git tag -a v1.0.0 -m "Release version 1.0.0"
   git push origin v1.0.0
   ```
5. GitHub Actions 会自动构建并创建 Release
   - 构建 bbdc_word_tool.exe
   - 上传到 Release 页面

## 🔗 相关链接

- PyInstaller 文档: https://pyinstaller.org/
- GitHub Actions 文档: https://docs.github.com/actions


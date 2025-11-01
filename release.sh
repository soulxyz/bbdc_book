#!/bin/bash
# 快速发布脚本 (Linux/macOS)

set -e

VERSION=$1

if [ -z "$VERSION" ]; then
    echo "❌ 错误: 请提供版本号"
    echo "用法: ./release.sh 0.0.2"
    exit 1
fi

# 验证版本格式
if ! [[ $VERSION =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo "❌ 错误: 版本号格式不正确，应为 x.y.z 格式"
    exit 1
fi

echo "🚀 准备发布版本 v$VERSION"
echo ""

# 1. 更新 VERSION 文件
echo "[1/6] 更新 VERSION 文件..."
echo -n "$VERSION" > VERSION

# 2. 更新 Cargo.toml
echo "[2/6] 更新 Cargo.toml..."
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    sed -i '' "s/version = \"[0-9]*\.[0-9]*\.[0-9]*\"/version = \"$VERSION\"/" rust/Cargo.toml
else
    # Linux
    sed -i "s/version = \"[0-9]*\.[0-9]*\.[0-9]*\"/version = \"$VERSION\"/" rust/Cargo.toml
fi

# 3. 检查 Git 状态
echo "[3/6] 检查 Git 状态..."
if [[ -n $(git status --porcelain) ]]; then
    echo "有未提交的更改:"
    git status --short
    echo ""
fi

# 4. 提交更改
echo "[4/6] 提交更改..."
git add .
git commit -m "chore: bump version to $VERSION"

# 5. 推送到远程
echo "[5/6] 推送到远程..."
git push

# 6. 创建并推送标签
echo "[6/6] 创建并推送标签 v$VERSION..."
git tag "v$VERSION"
git push origin "v$VERSION"

echo ""
echo "✅ 版本 v$VERSION 发布成功！"
echo ""
echo "🔗 GitHub Actions 正在构建..."
echo "   查看进度: https://github.com/soulxyz/bbdc_book/actions"
echo ""
echo "📦 构建完成后，Release 将自动创建:"
echo "   https://github.com/soulxyz/bbdc_book/releases/tag/v$VERSION"
echo ""


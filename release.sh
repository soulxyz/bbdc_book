#!/bin/bash
# 快速发布脚本 (Linux/macOS)

set -e

VERSION=$1
FORCE=$2

if [ -z "$VERSION" ]; then
    echo "❌ 错误: 请提供版本号"
    echo "用法: ./release.sh 0.0.2 [--force]"
    exit 1
fi

# 验证版本格式
if ! [[ $VERSION =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo "❌ 错误: 版本号格式不正确，应为 x.y.z 格式"
    exit 1
fi

echo "🚀 准备发布版本 v$VERSION"
echo ""

# 检查Git仓库
if ! git remote -v > /dev/null 2>&1; then
    echo "❌ 错误: 不是Git仓库或未配置远程仓库"
    exit 1
fi

# 检查tag是否已存在
if git rev-parse "v$VERSION" >/dev/null 2>&1; then
    if [ "$FORCE" != "--force" ]; then
        echo "⚠️  警告: 标签 v$VERSION 已存在"
        echo ""
        echo "这可能是因为之前的发布失败了。你可以："
        echo "  1. 使用 --force 参数强制重新发布"
        echo "     ./release.sh $VERSION --force"
        echo ""
        echo "  2. 手动删除tag后重试："
        echo "     git tag -d v$VERSION"
        echo "     git push origin :refs/tags/v$VERSION"
        echo ""
        exit 1
    fi
    
    echo "🗑️  删除已存在的标签..."
    
    # 删除本地tag
    git tag -d "v$VERSION" 2>/dev/null || true
    
    # 删除远程tag
    echo "   删除远程标签..."
    git push origin ":refs/tags/v$VERSION" 2>/dev/null || true
    
    echo "   ✅ 旧标签已删除"
    echo ""
    
    # 等待GitHub处理
    echo "   等待GitHub处理..."
    sleep 3
fi

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
    echo "   有未提交的更改:"
    git status --short
    echo ""
fi

# 4. 提交更改
echo "[4/6] 提交更改..."
git add .
if ! git commit -m "chore: bump version to $VERSION" 2>/dev/null; then
    echo "   ⚠️  没有新的更改需要提交（可能版本已更新）"
fi

# 5. 推送到远程
echo "[5/6] 推送到远程..."
if ! git push 2>/dev/null; then
    echo "   ⚠️  推送失败，尝试继续..."
fi

# 6. 创建并推送标签
echo "[6/6] 创建并推送标签 v$VERSION..."
if ! git tag "v$VERSION"; then
    echo "❌ 创建标签失败"
    exit 1
fi

if ! git push origin "v$VERSION"; then
    echo "❌ 推送标签失败"
    echo ""
    echo "💡 提示: 如果tag已存在于远程，使用 --force 参数重试"
    echo "   ./release.sh $VERSION --force"
    exit 1
fi

echo ""
echo "✅ 版本 v$VERSION 发布成功！"
echo ""
echo "📋 发布信息:"
echo "   版本: v$VERSION"
echo "   仓库: https://github.com/soulxyz/bbdc_book"
echo ""
echo "🔗 GitHub Actions 正在构建..."
echo "   查看进度: https://github.com/soulxyz/bbdc_book/actions"
echo ""
echo "📦 预计构建时间:"
echo "   - Rust (Windows): ~10分钟"
echo "   - Rust (Linux):   ~8分钟"
echo "   - Rust (macOS):   ~12分钟"
echo "   - Python:         ~5分钟"
echo ""
echo "📦 构建完成后，Release 将自动创建:"
echo "   https://github.com/soulxyz/bbdc_book/releases/tag/v$VERSION"
echo ""

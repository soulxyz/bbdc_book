#!/bin/bash
# 清理失败的发布 (Linux/macOS)

VERSION=$1

if [ -z "$VERSION" ]; then
    echo "❌ 错误: 请提供版本号"
    echo "用法: ./cleanup-release.sh 0.0.2"
    exit 1
fi

# 验证版本格式
if ! [[ $VERSION =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo "❌ 错误: 版本号格式不正确，应为 x.y.z 格式"
    exit 1
fi

TAG_NAME="v$VERSION"

echo "🗑️  清理失败的发布 $TAG_NAME"
echo ""

echo "📋 将要执行的操作:"
echo "  1. 删除本地 tag: $TAG_NAME"
echo "  2. 删除远程 tag: $TAG_NAME"
echo "  3. 删除 GitHub Release: $TAG_NAME（需要手动确认）"
echo ""

echo "⚠️  警告: 这将删除所有与 $TAG_NAME 相关的内容"
echo ""

# 确认
read -p "是否继续? (输入 YES 确认): " confirmation
if [ "$confirmation" != "YES" ]; then
    echo "❌ 操作已取消"
    exit 0
fi

echo ""

# 1. 删除本地 tag
echo "[1/3] 删除本地 tag..."
if git rev-parse "$TAG_NAME" >/dev/null 2>&1; then
    git tag -d "$TAG_NAME"
    if [ $? -eq 0 ]; then
        echo "  ✅ 本地 tag 已删除"
    else
        echo "  ⚠️  删除本地 tag 失败"
    fi
else
    echo "  ℹ️  本地不存在该 tag"
fi

# 2. 删除远程 tag
echo "[2/3] 删除远程 tag..."
git push origin ":refs/tags/$TAG_NAME" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "  ✅ 远程 tag 已删除"
else
    echo "  ⚠️  删除远程 tag 失败（可能不存在）"
fi

# 3. 提示删除 GitHub Release
echo "[3/3] 删除 GitHub Release..."
echo "  ℹ️  请手动删除 Release:"
echo "     1. 打开: https://github.com/soulxyz/bbdc_book/releases"
echo "     2. 找到 Release $TAG_NAME"
echo "     3. 点击 'Delete' 删除"
echo ""

# 4. 回退版本号（可选）
echo "💡 提示:"
echo "  - tag 和 Release 已清理"
echo "  - 现在可以重新发布 $TAG_NAME"
echo "  - 或者继续使用 $TAG_NAME 发布"
echo ""

# 检查是否需要回退 VERSION 文件
if [ -f "VERSION" ]; then
    CURRENT_VERSION=$(cat VERSION)
    
    if [ "$CURRENT_VERSION" = "$VERSION" ]; then
        echo "❓ VERSION 文件当前是 $CURRENT_VERSION"
        read -p "   是否回退到上一个版本? (y/n): " rollback
        
        if [ "$rollback" = "y" ]; then
            # 简单的版本回退逻辑
            IFS='.' read -r major minor patch <<< "$VERSION"
            if [ "$patch" -gt 0 ]; then
                patch=$((patch - 1))
                PREV_VERSION="$major.$minor.$patch"
                echo -n "$PREV_VERSION" > VERSION
                
                echo "  ✅ VERSION 已回退到: $PREV_VERSION"
                
                # 回退 Cargo.toml
                if [ -f "rust/Cargo.toml" ]; then
                    if [[ "$OSTYPE" == "darwin"* ]]; then
                        sed -i '' "s/version = \"[0-9]*\.[0-9]*\.[0-9]*\"/version = \"$PREV_VERSION\"/" rust/Cargo.toml
                    else
                        sed -i "s/version = \"[0-9]*\.[0-9]*\.[0-9]*\"/version = \"$PREV_VERSION\"/" rust/Cargo.toml
                    fi
                    echo "  ✅ Cargo.toml 已回退到: $PREV_VERSION"
                fi
                
                echo ""
                echo "💡 建议:"
                echo "   git add ."
                echo "   git commit -m 'chore: rollback to $PREV_VERSION'"
                echo "   git push"
            else
                echo "  ⚠️  无法回退版本 (已经是 x.x.0)"
            fi
        fi
    fi
fi

echo ""
echo "✅ 清理完成！"
echo ""
echo "📝 后续操作:"
echo "  1. 修复导致构建失败的问题"
echo "  2. 重新发布: ./release.sh $VERSION"
echo ""


# 清理失败的发布 (Windows PowerShell)

param(
    [Parameter(Mandatory=$true)]
    [string]$Version
)

Write-Host "🗑️  清理失败的发布 v$Version" -ForegroundColor Yellow
Write-Host ""

# 验证版本格式
if ($Version -notmatch '^\d+\.\d+\.\d+$') {
    Write-Host "❌ 错误: 版本号格式不正确，应为 x.y.z 格式" -ForegroundColor Red
    exit 1
}

$tagName = "v$Version"

Write-Host "📋 将要执行的操作:" -ForegroundColor Cyan
Write-Host "  1. 删除本地 tag: $tagName" -ForegroundColor Gray
Write-Host "  2. 删除远程 tag: $tagName" -ForegroundColor Gray
Write-Host "  3. 删除 GitHub Release: $tagName（需要手动确认）" -ForegroundColor Gray
Write-Host ""

Write-Host "⚠️  警告: 这将删除所有与 $tagName 相关的内容" -ForegroundColor Yellow
Write-Host ""

# 确认
$confirmation = Read-Host "是否继续? (输入 YES 确认)"
if ($confirmation -ne "YES") {
    Write-Host "❌ 操作已取消" -ForegroundColor Red
    exit 0
}

Write-Host ""

# 1. 删除本地 tag
Write-Host "[1/3] 删除本地 tag..." -ForegroundColor Yellow
$localTag = git tag -l $tagName
if ($localTag) {
    git tag -d $tagName
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✅ 本地 tag 已删除" -ForegroundColor Green
    } else {
        Write-Host "  ⚠️  删除本地 tag 失败" -ForegroundColor Yellow
    }
} else {
    Write-Host "  ℹ️  本地不存在该 tag" -ForegroundColor Gray
}

# 2. 删除远程 tag
Write-Host "[2/3] 删除远程 tag..." -ForegroundColor Yellow
git push origin ":refs/tags/$tagName" 2>&1 | Out-Null
if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✅ 远程 tag 已删除" -ForegroundColor Green
} else {
    Write-Host "  ⚠️  删除远程 tag 失败（可能不存在）" -ForegroundColor Yellow
}

# 3. 提示删除 GitHub Release
Write-Host "[3/3] 删除 GitHub Release..." -ForegroundColor Yellow
Write-Host "  ℹ️  请手动删除 Release:" -ForegroundColor Cyan
Write-Host "     1. 打开: https://github.com/soulxyz/bbdc_book/releases" -ForegroundColor Gray
Write-Host "     2. 找到 Release $tagName" -ForegroundColor Gray
Write-Host "     3. 点击 'Delete' 删除" -ForegroundColor Gray
Write-Host ""

# 4. 回退版本号（可选）
Write-Host "💡 提示:" -ForegroundColor Cyan
Write-Host "  - tag 和 Release 已清理" -ForegroundColor Gray
Write-Host "  - 现在可以重新发布 v$Version" -ForegroundColor Gray
Write-Host "  - 或者继续使用 v$Version 发布" -ForegroundColor Gray
Write-Host ""

# 检查是否需要回退 VERSION 文件
if (Test-Path "VERSION") {
    $currentVersion = Get-Content "VERSION" -Raw
    $currentVersion = $currentVersion.Trim()
    
    if ($currentVersion -eq $Version) {
        Write-Host "❓ VERSION 文件当前是 $currentVersion" -ForegroundColor Yellow
        Write-Host "   是否回退到上一个版本? (y/n): " -NoNewline -ForegroundColor Yellow
        $rollback = Read-Host
        
        if ($rollback -eq 'y') {
            # 简单的版本回退逻辑
            $parts = $Version.Split('.')
            $patch = [int]$parts[2]
            if ($patch -gt 0) {
                $patch--
                $prevVersion = "$($parts[0]).$($parts[1]).$patch"
                $prevVersion | Out-File -FilePath VERSION -Encoding utf8 -NoNewline
                
                Write-Host "  ✅ VERSION 已回退到: $prevVersion" -ForegroundColor Green
                
                # 回退 Cargo.toml
                if (Test-Path "rust\Cargo.toml") {
                    $cargoContent = Get-Content rust\Cargo.toml -Raw
                    $cargoContent = $cargoContent -replace 'version = "\d+\.\d+\.\d+"', "version = `"$prevVersion`""
                    $cargoContent | Out-File -FilePath rust\Cargo.toml -Encoding utf8 -NoNewline
                    Write-Host "  ✅ Cargo.toml 已回退到: $prevVersion" -ForegroundColor Green
                }
                
                Write-Host ""
                Write-Host "💡 建议:" -ForegroundColor Cyan
                Write-Host "   git add ." -ForegroundColor Gray
                Write-Host "   git commit -m 'chore: rollback to $prevVersion'" -ForegroundColor Gray
                Write-Host "   git push" -ForegroundColor Gray
            } else {
                Write-Host "  ⚠️  无法回退版本 (已经是 x.x.0)" -ForegroundColor Yellow
            }
        }
    }
}

Write-Host ""
Write-Host "✅ 清理完成！" -ForegroundColor Green
Write-Host ""
Write-Host "📝 后续操作:" -ForegroundColor Cyan
Write-Host "  1. 修复导致构建失败的问题" -ForegroundColor Gray
Write-Host "  2. 重新发布: .\release.ps1 $Version" -ForegroundColor Gray
Write-Host ""


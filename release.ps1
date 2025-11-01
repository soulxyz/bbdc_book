# 快速发布脚本 (Windows PowerShell)

param(
    [Parameter(Mandatory=$true)]
    [string]$Version,
    
    [Parameter(Mandatory=$false)]
    [switch]$Force  # 强制重新发布（删除已存在的tag）
)

Write-Host "🚀 准备发布版本 v$Version" -ForegroundColor Cyan
Write-Host ""

# 验证版本格式
if ($Version -notmatch '^\d+\.\d+\.\d+$') {
    Write-Host "❌ 错误: 版本号格式不正确，应为 x.y.z 格式" -ForegroundColor Red
    exit 1
}

# 检查Git仓库
$gitRemote = git remote -v 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ 错误: 不是Git仓库或未配置远程仓库" -ForegroundColor Red
    exit 1
}

# 检查tag是否已存在
$existingTag = git tag -l "v$Version" 2>&1
if ($existingTag -and !$Force) {
    Write-Host "⚠️  警告: 标签 v$Version 已存在" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "这可能是因为之前的发布失败了。你可以：" -ForegroundColor Yellow
    Write-Host "  1. 使用 -Force 参数强制重新发布" -ForegroundColor Cyan
    Write-Host "     .\release.ps1 $Version -Force" -ForegroundColor Gray
    Write-Host ""
    Write-Host "  2. 手动删除tag后重试：" -ForegroundColor Cyan
    Write-Host "     git tag -d v$Version" -ForegroundColor Gray
    Write-Host "     git push origin :refs/tags/v$Version" -ForegroundColor Gray
    Write-Host ""
    exit 1
}

# 如果使用Force，删除已存在的tag
if ($existingTag -and $Force) {
    Write-Host "🗑️  删除已存在的标签..." -ForegroundColor Yellow
    
    # 删除本地tag
    git tag -d "v$Version" 2>&1 | Out-Null
    
    # 删除远程tag（如果存在）
    Write-Host "   删除远程标签..." -ForegroundColor Gray
    git push origin ":refs/tags/v$Version" 2>&1 | Out-Null
    
    Write-Host "   ✅ 旧标签已删除" -ForegroundColor Green
    Write-Host ""
    
    # 等待几秒让GitHub处理
    Write-Host "   等待GitHub处理..." -ForegroundColor Gray
    Start-Sleep -Seconds 3
}

# 1. 更新 VERSION 文件
Write-Host "[1/6] 更新 VERSION 文件..." -ForegroundColor Yellow
$Version | Out-File -FilePath VERSION -Encoding utf8 -NoNewline

# 2. 更新 Cargo.toml
Write-Host "[2/6] 更新 Cargo.toml..." -ForegroundColor Yellow
$cargoContent = Get-Content rust\Cargo.toml -Raw
$cargoContent = $cargoContent -replace 'version = "\d+\.\d+\.\d+"', "version = `"$Version`""
$cargoContent | Out-File -FilePath rust\Cargo.toml -Encoding utf8 -NoNewline

# 3. 检查 Git 状态
Write-Host "[3/6] 检查 Git 状态..." -ForegroundColor Yellow
$gitStatus = git status --porcelain
if ($gitStatus) {
    Write-Host "   有未提交的更改:" -ForegroundColor Yellow
    git status --short
    Write-Host ""
}

# 4. 提交更改
Write-Host "[4/6] 提交更改..." -ForegroundColor Yellow
git add .
git commit -m "chore: bump version to $Version"

if ($LASTEXITCODE -ne 0) {
    Write-Host "   ⚠️  没有新的更改需要提交（可能版本已更新）" -ForegroundColor Yellow
}

# 5. 推送到远程
Write-Host "[5/6] 推送到远程..." -ForegroundColor Yellow
git push

if ($LASTEXITCODE -ne 0) {
    Write-Host "   ⚠️  推送失败，尝试继续..." -ForegroundColor Yellow
}

# 6. 创建并推送标签
Write-Host "[6/6] 创建并推送标签 v$Version..." -ForegroundColor Yellow
git tag "v$Version"

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ 创建标签失败" -ForegroundColor Red
    exit 1
}

git push origin "v$Version"

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ 推送标签失败" -ForegroundColor Red
    Write-Host ""
    Write-Host "💡 提示: 如果tag已存在于远程，使用 -Force 参数重试" -ForegroundColor Cyan
    Write-Host "   .\release.ps1 $Version -Force" -ForegroundColor Gray
    exit 1
}

Write-Host ""
Write-Host "✅ 版本 v$Version 发布成功！" -ForegroundColor Green
Write-Host ""
Write-Host "📋 发布信息:" -ForegroundColor Cyan
Write-Host "   版本: v$Version" -ForegroundColor Gray
Write-Host "   仓库: https://github.com/soulxyz/bbdc_book" -ForegroundColor Gray
Write-Host ""
Write-Host "🔗 GitHub Actions 正在构建..." -ForegroundColor Cyan
Write-Host "   查看进度: https://github.com/soulxyz/bbdc_book/actions" -ForegroundColor Gray
Write-Host ""
Write-Host "📦 预计构建时间:" -ForegroundColor Cyan
Write-Host "   - Rust (Windows): ~10分钟" -ForegroundColor Gray
Write-Host "   - Rust (Linux):   ~8分钟" -ForegroundColor Gray
Write-Host "   - Rust (macOS):   ~12分钟" -ForegroundColor Gray
Write-Host "   - Python:         ~5分钟" -ForegroundColor Gray
Write-Host ""
Write-Host "📦 构建完成后，Release 将自动创建:" -ForegroundColor Cyan
Write-Host "   https://github.com/soulxyz/bbdc_book/releases/tag/v$Version" -ForegroundColor Gray
Write-Host ""

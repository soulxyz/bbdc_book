# 快速发布脚本 (Windows PowerShell)

param(
    [Parameter(Mandatory=$true)]
    [string]$Version
)

Write-Host "🚀 准备发布版本 v$Version" -ForegroundColor Cyan
Write-Host ""

# 验证版本格式
if ($Version -notmatch '^\d+\.\d+\.\d+$') {
    Write-Host "❌ 错误: 版本号格式不正确，应为 x.y.z 格式" -ForegroundColor Red
    exit 1
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
    Write-Host "有未提交的更改:" -ForegroundColor Yellow
    git status --short
    Write-Host ""
}

# 4. 提交更改
Write-Host "[4/6] 提交更改..." -ForegroundColor Yellow
git add .
git commit -m "chore: bump version to $Version"

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Git 提交失败" -ForegroundColor Red
    exit 1
}

# 5. 推送到远程
Write-Host "[5/6] 推送到远程..." -ForegroundColor Yellow
git push

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Git 推送失败" -ForegroundColor Red
    exit 1
}

# 6. 创建并推送标签
Write-Host "[6/6] 创建并推送标签 v$Version..." -ForegroundColor Yellow
git tag "v$Version"
git push origin "v$Version"

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ 标签推送失败" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "✅ 版本 v$Version 发布成功！" -ForegroundColor Green
Write-Host ""
Write-Host "🔗 GitHub Actions 正在构建..." -ForegroundColor Cyan
Write-Host "   查看进度: https://github.com/soulxyz/bbdc_book/actions" -ForegroundColor Gray
Write-Host ""
Write-Host "📦 构建完成后，Release 将自动创建:" -ForegroundColor Cyan
Write-Host "   https://github.com/soulxyz/bbdc_book/releases/tag/v$Version" -ForegroundColor Gray
Write-Host ""


# ZM Manuel Release Script (Windows PowerShell)
# =============================================
# Kullanım: .\scripts\release.ps1 -Version 1.2.3
#
# Bu script GitHub CLI (gh) ile manuel release oluşturur.
# Normalde .github/workflows/release.yml otomatik yapar,
# bu script yedek olarak kullanılır.

param(
    [Parameter(Mandatory=$true)]
    [string]$Version
)

$ErrorActionPreference = "Stop"
$Tag = "v$Version"

# gh CLI kontrol
$gh = Get-Command gh -ErrorAction SilentlyContinue
if (-not $gh) {
    Write-Host "❌ 'gh' CLI bulunamadı. Kur: https://cli.github.com/" -ForegroundColor Red
    exit 1
}

# Repo root
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Split-Path -Parent $ScriptDir
Set-Location $RepoRoot

# Doğrulama
Write-Host "🔍 Doğrulama çalıştırılıyor..." -ForegroundColor Cyan
python scripts/validate_data.py
if ($LASTEXITCODE -ne 0) {
    exit 1
}

# Manifest versiyon kontrolü
$ManifestVersion = (Get-Content manifest.json -Raw | ConvertFrom-Json).version
if ($ManifestVersion -ne $Version) {
    Write-Host "❌ manifest.json versiyonu ($ManifestVersion) ile argüman ($Version) eşleşmiyor" -ForegroundColor Red
    Write-Host "   Önce: python scripts/bump_version.py --set $Version" -ForegroundColor Yellow
    exit 1
}

# Tag var mı?
$tagExists = git rev-parse $Tag 2>$null
if ($tagExists) {
    Write-Host "⚠️  Tag $Tag zaten mevcut, kullanılıyor" -ForegroundColor Yellow
} else {
    Write-Host "🏷️  Tag oluşturuluyor: $Tag" -ForegroundColor Cyan
    git tag $Tag
}

# Release oluştur
Write-Host "🚀 GitHub release oluşturuluyor..." -ForegroundColor Cyan

$notes = @"
## ZM $Version

Bu release aşağıdaki dosyaları içerir:
- manifest.json
- data/esma.json
- data/tesbihat.json

Detaylı değişiklikler için [CHANGELOG](../blob/main/docs/CHANGELOG.md) dosyasına bakın.
"@

gh release create $Tag `
    --title "ZM $Version" `
    --notes $notes `
    --target main `
    manifest.json `
    data/esma.json `
    data/tesbihat.json

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✅ Release başarıyla oluşturuldu: https://github.com/powerfulsoftware/ZM/releases/tag/$Tag" -ForegroundColor Green
    Write-Host ""
    Write-Host "📋 Sonraki adım:" -ForegroundColor Cyan
    Write-Host "   git push origin $Tag"
}
#!/usr/bin/env bash
# ZM Manuel Release Script (Linux/macOS)
# =====================================
# Kullanım: ./scripts/release.sh 1.2.3
#
# Bu script GitHub CLI (gh) ile manuel release oluşturur.
# Normalde .github/workflows/release.yml otomatik yapar,
# bu script yedek olarak kullanılır.

set -euo pipefail

if [ $# -lt 1 ]; then
    echo "Kullanım: $0 <version>"
    echo "Örnek:   $0 1.2.3"
    exit 1
fi

VERSION="$1"
TAG="v${VERSION}"

# gh CLI kontrol
if ! command -v gh &> /dev/null; then
    echo "❌ 'gh' CLI bulunamadı. Kur: https://cli.github.com/"
    exit 1
fi

# Repo root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

# Doğrulama
echo "🔍 Doğrulama çalıştırılıyor..."
python3 scripts/validate_data.py

# Manifest versiyon kontrolü
MANIFEST_VERSION=$(python3 -c "import json; print(json.load(open('manifest.json'))['version'])")
if [ "${MANIFEST_VERSION}" != "${VERSION}" ]; then
    echo "❌ manifest.json versiyonu (${MANIFEST_VERSION}) ile argüman (${VERSION}) eşleşmiyor"
    echo "   Önce: python3 scripts/bump_version.py --set ${VERSION}"
    exit 1
fi

# Tag var mı?
if git rev-parse "${TAG}" >/dev/null 2>&1; then
    echo "⚠️  Tag ${TAG} zaten mevcut, kullanılıyor"
else
    echo "🏷️  Tag oluşturuluyor: ${TAG}"
    git tag "${TAG}"
fi

# Release oluştur
echo "🚀 GitHub release oluşturuluyor..."

NOTES=$(cat <<EOF
## ZM v${VERSION}

Bu release aşağıdaki dosyaları içerir:
- manifest.json
- data/esma.json
- data/tesbihat.json

Detaylı değişiklikler için [CHANGELOG](../blob/main/docs/CHANGELOG.md) dosyasına bakın.
EOF
)

gh release create "${TAG}" \
    --title "ZM v${VERSION}" \
    --notes "${NOTES}" \
    --target main \
    manifest.json \
    data/esma.json \
    data/tesbihat.json

echo ""
echo "✅ Release başarıyla oluşturuldu: https://github.com/powerfulsoftware/ZM/releases/tag/${TAG}"
echo ""
echo "📋 Sonraki adım:"
echo "   git push origin ${TAG}"
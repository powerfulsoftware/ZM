#!/usr/bin/env python3
"""
ZM Versiyon Yükseltici
=======================
manifest.json içindeki versiyonu artırır, publishedAt'i günceller,
checksum'ları yeniden hesaplar ve CHANGELOG.md'ye yeni bölüm ekler.

Kullanım:
    python scripts/bump_version.py patch
    python scripts/bump_version.py minor
    python scripts/bump_version.py major
    python scripts/bump_version.py --set 1.2.3

Script, değişiklik yaptıktan sonra çalıştırıcıya listeler. Commit'leme
yapmaz, sadece dosyaları düzenler.
"""

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# Windows konsol encoding güvenliği
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

REPO_ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = REPO_ROOT / "manifest.json"
ESMA_PATH = REPO_ROOT / "data" / "esma.json"
TESBIHAT_PATH = REPO_ROOT / "data" / "tesbihat.json"
CHANGELOG_PATH = REPO_ROOT / "docs" / "CHANGELOG.md"

SEMVER_RE = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")


def compute_sha256(path: Path) -> str:
    import hashlib

    sha = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha.update(chunk)
    return f"sha256-{sha.hexdigest()}"


def parse_version(version: str) -> tuple[int, int, int]:
    m = SEMVER_RE.match(version.strip())
    if not m:
        raise ValueError(f"Geçersiz semver: '{version}' (örn: 1.2.3)")
    return int(m.group(1)), int(m.group(2)), int(m.group(3))


def bump(parsed: tuple[int, int, int], bump_type: str) -> tuple[int, int, int]:
    major, minor, patch = parsed
    if bump_type == "major":
        return major + 1, 0, 0
    if bump_type == "minor":
        return major, minor + 1, 0
    if bump_type == "patch":
        return major, minor, patch + 1
    raise ValueError(f"Bilinmeyen bump tipi: {bump_type}")


def format_version(parsed: tuple[int, int, int]) -> str:
    return ".".join(str(x) for x in parsed)


def load_manifest() -> dict:
    if not MANIFEST_PATH.exists():
        print(f"❌ manifest.json bulunamadı: {MANIFEST_PATH}", file=sys.stderr)
        sys.exit(2)
    with MANIFEST_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_manifest(manifest: dict) -> None:
    with MANIFEST_PATH.open("w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
        f.write("\n")


def update_changelog(new_version: str) -> None:
    if not CHANGELOG_PATH.exists():
        print(f"⚠️  CHANGELOG.md bulunamadı, atlanıyor: {CHANGELOG_PATH}")
        return

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    new_section = f"\n## [{new_version}] - {today}\n\n### Değişen\n- \n"

    content = CHANGELOG_PATH.read_text(encoding="utf-8")
    if f"## [{new_version}]" in content:
        print(f"⚠️  CHANGELOG.md zaten [{new_version}] bölümünü içeriyor")
        return

    # İlk '## [' satırından önce ekle (en üste)
    lines = content.split("\n")
    out_lines = []
    inserted = False
    for line in lines:
        if not inserted and line.startswith("## ["):
            out_lines.append(new_section.rstrip("\n"))
            out_lines.append("")
            inserted = True
        out_lines.append(line)
    if not inserted:
        # Hiç sürüm bölümü yoksa sona ekle
        out_lines.append(new_section.rstrip("\n"))

    CHANGELOG_PATH.write_text("\n".join(out_lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="ZM versiyon yükseltici")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("bump_type", nargs="?", choices=["major", "minor", "patch"])
    group.add_argument("--set", help="Doğrudan versiyon ayarla (örn: 1.2.3)")
    args = parser.parse_args()

    manifest = load_manifest()
    current_str = manifest.get("version", "0.0.0")
    current = parse_version(current_str)

    if args.set:
        new = parse_version(args.set)
    else:
        new = bump(current, args.bump_type)

    new_str = format_version(new)

    print(f"📦 Versiyon: {current_str} → {new_str}")
    print()

    # Manifest güncelle
    manifest["version"] = new_str
    manifest["publishedAt"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # Checksum'ları yeniden hesapla
    print("🔐 Checksum hesaplanıyor...")
    if ESMA_PATH.exists():
        manifest.setdefault("checksums", {})["esma"] = compute_sha256(ESMA_PATH)
        print(f"   • esma.json: {manifest['checksums']['esma'][:32]}...")
    if TESBIHAT_PATH.exists():
        manifest.setdefault("checksums", {})["tesbihat"] = compute_sha256(TESBIHAT_PATH)
        print(f"   • tesbihat.json: {manifest['checksums']['tesbihat'][:32]}...")

    save_manifest(manifest)
    print(f"\n✅ manifest.json güncellendi")

    # CHANGELOG
    update_changelog(new_str)
    print(f"✅ docs/CHANGELOG.md'ye [{new_str}] bölümü eklendi")

    # Sonraki adımlar
    print(f"\n📋 Sonraki adımlar:")
    print(f"   git add manifest.json data/ docs/CHANGELOG.md")
    print(f"   git commit -m \"chore(release): v{new_str}\"")
    print(f"   git tag v{new_str}")
    print(f"   git push origin main --tags")
    print()
    print(f"💡 Tag push'landığında GitHub Actions otomatik release oluşturacak.")

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except ValueError as e:
        print(f"❌ Hata: {e}", file=sys.stderr)
        sys.exit(1)
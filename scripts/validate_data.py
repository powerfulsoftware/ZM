#!/usr/bin/env python3
"""
ZM Veri Doğrulayıcı
====================
data/ klasöründeki JSON dosyalarını ve manifest.json'ı şema kurallarına göre doğrular.

Kullanım:
    python scripts/validate_data.py
    python scripts/validate_data.py --esma
    python scripts/validate_data.py --tesbihat
    python scripts/validate_data.py --manifest
    python scripts/validate_data.py --recompute-checksums

Exit codes:
    0 → başarılı
    1 → doğrulama hatası
    2 → dosya okuma hatası
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

# Windows konsol encoding güvenliği (cp1254 vs.)
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Sabitler
REPO_ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = REPO_ROOT / "manifest.json"
ESMA_PATH = REPO_ROOT / "data" / "esma.json"
TESBIHAT_PATH = REPO_ROOT / "data" / "tesbihat.json"

EXPECTED_LANGUAGES = ["tr", "en", "ar", "az", "ru", "es"]

REQUIRED_ESMA_FIELDS = {"id", "sira", "hedef", "translations"}
REQUIRED_TESBIHAT_FIELDS = {"id", "hedef", "translations"}
REQUIRED_TRANSLATION_FIELDS_ESMA = {"isim", "anlami"}
REQUIRED_TRANSLATION_FIELDS_TESBIHAT = {"isim", "aciklama"}


class ValidationError:
    def __init__(self, file: str, message: str):
        self.file = file
        self.message = message

    def __str__(self) -> str:
        return f"[{self.file}] {self.message}"


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Dosya bulunamadı: {path}")
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def compute_sha256(path: Path) -> str:
    sha = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha.update(chunk)
    return f"sha256-{sha.hexdigest()}"


def validate_manifest(recompute: bool = False) -> list[ValidationError]:
    errors: list[ValidationError] = []
    try:
        manifest = load_json(MANIFEST_PATH)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        return [ValidationError("manifest.json", str(e))]

    # schemaVersion
    sv = manifest.get("schemaVersion")
    if sv is None:
        errors.append(ValidationError("manifest.json", "schemaVersion eksik"))
    elif not isinstance(sv, int):
        errors.append(ValidationError("manifest.json", "schemaVersion integer olmalı"))
    elif sv < 1:
        errors.append(ValidationError("manifest.json", f"schemaVersion >= 1 olmalı (şu an {sv})"))

    # version
    version = manifest.get("version")
    if not version or not isinstance(version, str):
        errors.append(ValidationError("manifest.json", "version string olmalı"))

    # publishedAt
    pub = manifest.get("publishedAt")
    if not pub or not isinstance(pub, str):
        errors.append(ValidationError("manifest.json", "publishedAt ISO 8601 string olmalı"))

    # minAppVersion
    min_app = manifest.get("minAppVersion")
    if not min_app or not isinstance(min_app, str):
        errors.append(ValidationError("manifest.json", "minAppVersion string olmalı"))

    # parts
    parts = manifest.get("parts")
    if not isinstance(parts, dict) or not parts:
        errors.append(ValidationError("manifest.json", "parts object olmalı ve dolu olmalı"))
    else:
        if "esma" not in parts:
            errors.append(ValidationError("manifest.json", "parts.esma eksik"))
        if "tesbihat" not in parts:
            errors.append(ValidationError("manifest.json", "parts.tesbihat eksik"))

    # languages
    langs = manifest.get("languages")
    if not isinstance(langs, list) or not langs:
        errors.append(ValidationError("manifest.json", "languages array olmalı"))
    else:
        for expected in EXPECTED_LANGUAGES:
            if expected not in langs:
                errors.append(
                    ValidationError("manifest.json", f"languages içinde '{expected}' eksik")
                )

    # checksums (varsa)
    checksums = manifest.get("checksums", {})
    if checksums:
        for key in ["esma", "tesbihat"]:
            expected = checksums.get(key)
            if not expected:
                errors.append(ValidationError("manifest.json", f"checksums.{key} eksik"))
                continue

            file_path = ESMA_PATH if key == "esma" else TESBIHAT_PATH
            if not file_path.exists():
                continue

            actual = compute_sha256(file_path)
            if actual != expected:
                msg = (
                    f"checksums.{key} eşleşmiyor (beklenen: {expected[:20]}..., "
                    f"gerçek: {actual[:20]}...)"
                )
                if recompute:
                    print(f"   ⚠️  {msg}")
                    print(f"   💡 Yeniden hesaplanan: {actual}")
                else:
                    errors.append(ValidationError("manifest.json", msg))

    return errors


def validate_esma() -> list[ValidationError]:
    errors: list[ValidationError] = []
    try:
        data = load_json(ESMA_PATH)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        return [ValidationError("esma.json", str(e))]

    items = data.get("esmaulHusna")
    if not isinstance(items, list) or not items:
        return [ValidationError("esma.json", "esmaulHusna boş veya array değil")]

    # Unique ID kontrolü
    seen_ids = set()
    seen_sira = set()
    languages_per_record = []

    for idx, item in enumerate(items):
        prefix = f"esmaulHusna[{idx}]"

        if not isinstance(item, dict):
            errors.append(ValidationError("esma.json", f"{prefix} object değil"))
            continue

        # Zorunlu alanlar
        missing = REQUIRED_ESMA_FIELDS - set(item.keys())
        if missing:
            errors.append(ValidationError("esma.json", f"{prefix} eksik alanlar: {missing}"))

        # id
        item_id = item.get("id")
        if not isinstance(item_id, str):
            errors.append(ValidationError("esma.json", f"{prefix}.id string olmalı"))
        elif item_id in seen_ids:
            errors.append(ValidationError("esma.json", f"{prefix}.id duplicate: '{item_id}'"))
        else:
            seen_ids.add(item_id)
            if not item_id.startswith("eh-"):
                errors.append(
                    ValidationError("esma.json", f"{prefix}.id 'eh-' ile başlamalı: '{item_id}'")
                )
            # eh-<n> formatında n pozitif integer mı
            suffix = item_id[3:] if item_id.startswith("eh-") else ""
            if not suffix.isdigit() or int(suffix) <= 0:
                errors.append(
                    ValidationError(
                        "esma.json",
                        f"{prefix}.id geçersiz format: '{item_id}' (beklenen: eh-<n>)",
                    )
                )

        # sira
        sira = item.get("sira")
        if not isinstance(sira, int):
            errors.append(ValidationError("esma.json", f"{prefix}.sira integer olmalı"))
        else:
            if sira in seen_sira:
                errors.append(ValidationError("esma.json", f"{prefix}.sira duplicate: {sira}"))
            seen_sira.add(sira)

        # hedef
        hedef = item.get("hedef")
        if not isinstance(hedef, int) or hedef <= 0:
            errors.append(
                ValidationError("esma.json", f"{prefix}.hedef pozitif integer olmalı")
            )

        # translations
        translations = item.get("translations")
        if not isinstance(translations, dict) or not translations:
            errors.append(
                ValidationError("esma.json", f"{prefix}.translations object olmalı")
            )
            continue

        languages_per_record.append(set(translations.keys()))

        for lang, tr in translations.items():
            if not isinstance(tr, dict):
                errors.append(
                    ValidationError(
                        "esma.json", f"{prefix}.translations.{lang} object değil"
                    )
                )
                continue
            missing_fields = REQUIRED_TRANSLATION_FIELDS_ESMA - set(tr.keys())
            if missing_fields:
                errors.append(
                    ValidationError(
                        "esma.json",
                        f"{prefix}.translations.{lang} eksik alanlar: {missing_fields}",
                    )
                )
            for field in ["isim", "anlami"]:
                val = tr.get(field)
                if not isinstance(val, str) or not val.strip():
                    errors.append(
                        ValidationError(
                            "esma.json",
                            f"{prefix}.translations.{lang}.{field} boş olmamalı",
                        )
                    )

    # Tüm kayıtlarda aynı dil kümesi
    if languages_per_record:
        first = languages_per_record[0]
        for idx, langs in enumerate(languages_per_record[1:], start=1):
            if langs != first:
                errors.append(
                    ValidationError(
                        "esma.json",
                        f"esmaulHusna[{idx}] dil kümesi farklı: {langs} vs {first}",
                    )
                )

    # Sıra 1..N ardışık mı
    if seen_sira:
        expected_sira = set(range(1, len(items) + 1))
        if seen_sira != expected_sira:
            missing = expected_sira - seen_sira
            extra = seen_sira - expected_sira
            if missing:
                errors.append(
                    ValidationError(
                        "esma.json", f"Eksik sira numaraları: {sorted(missing)}"
                    )
                )
            if extra:
                errors.append(
                    ValidationError(
                        "esma.json", f"Fazladan sira numaraları: {sorted(extra)}"
                    )
                )

    return errors


def validate_tesbihat() -> list[ValidationError]:
    errors: list[ValidationError] = []
    try:
        data = load_json(TESBIHAT_PATH)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        return [ValidationError("tesbihat.json", str(e))]

    items = data.get("tesbihat")
    if not isinstance(items, list) or not items:
        return [ValidationError("tesbihat.json", "tesbihat boş veya array değil")]

    seen_ids = set()
    languages_per_record = []

    for idx, item in enumerate(items):
        prefix = f"tesbihat[{idx}]"

        if not isinstance(item, dict):
            errors.append(ValidationError("tesbihat.json", f"{prefix} object değil"))
            continue

        missing = REQUIRED_TESBIHAT_FIELDS - set(item.keys())
        if missing:
            errors.append(ValidationError("tesbihat.json", f"{prefix} eksik alanlar: {missing}"))

        item_id = item.get("id")
        if not isinstance(item_id, str):
            errors.append(ValidationError("tesbihat.json", f"{prefix}.id string olmalı"))
        elif item_id in seen_ids:
            errors.append(
                ValidationError("tesbihat.json", f"{prefix}.id duplicate: '{item_id}'")
            )
        else:
            seen_ids.add(item_id)
            if not item_id.startswith("tes-"):
                errors.append(
                    ValidationError(
                        "tesbihat.json",
                        f"{prefix}.id 'tes-' ile başlamalı: '{item_id}'",
                    )
                )
            # tes-<n> formatında n pozitif integer mı
            suffix = item_id[4:] if item_id.startswith("tes-") else ""
            if not suffix.isdigit() or int(suffix) <= 0:
                errors.append(
                    ValidationError(
                        "tesbihat.json",
                        f"{prefix}.id geçersiz format: '{item_id}' (beklenen: tes-<n>)",
                    )
                )

        hedef = item.get("hedef")
        if not isinstance(hedef, int) or hedef <= 0:
            errors.append(
                ValidationError("tesbihat.json", f"{prefix}.hedef pozitif integer olmalı")
            )

        translations = item.get("translations")
        if not isinstance(translations, dict) or not translations:
            errors.append(
                ValidationError("tesbihat.json", f"{prefix}.translations object olmalı")
            )
            continue

        languages_per_record.append(set(translations.keys()))

        for lang, tr in translations.items():
            if not isinstance(tr, dict):
                errors.append(
                    ValidationError(
                        "tesbihat.json", f"{prefix}.translations.{lang} object değil"
                    )
                )
                continue
            missing_fields = REQUIRED_TRANSLATION_FIELDS_TESBIHAT - set(tr.keys())
            if missing_fields:
                errors.append(
                    ValidationError(
                        "tesbihat.json",
                        f"{prefix}.translations.{lang} eksik alanlar: {missing_fields}",
                    )
                )
            for field in ["isim", "aciklama"]:
                val = tr.get(field)
                if not isinstance(val, str) or not val.strip():
                    errors.append(
                        ValidationError(
                            "tesbihat.json",
                            f"{prefix}.translations.{lang}.{field} boş olmamalı",
                        )
                    )

    if languages_per_record:
        first = languages_per_record[0]
        for idx, langs in enumerate(languages_per_record[1:], start=1):
            if langs != first:
                errors.append(
                    ValidationError(
                        "tesbihat.json",
                        f"tesbihat[{idx}] dil kümesi farklı: {langs} vs {first}",
                    )
                )

    return errors


def print_summary(
    label: str, ok: bool, error_count: int = 0, extra: str = ""
) -> None:
    icon = "✅" if ok else "❌"
    status = "OK" if ok else f"{error_count} hata"
    msg = f"   {icon} {label}"
    if extra:
        msg += f" — {extra}"
    msg += f" ({status})"
    print(msg)


def main() -> int:
    parser = argparse.ArgumentParser(description="ZM veri doğrulayıcı")
    parser.add_argument("--esma", action="store_true", help="Sadece esma.json doğrula")
    parser.add_argument("--tesbihat", action="store_true", help="Sadece tesbihat.json doğrula")
    parser.add_argument("--manifest", action="store_true", help="Sadece manifest.json doğrula")
    parser.add_argument(
        "--recompute-checksums",
        action="store_true",
        help="Checksum hatalarını göster, hesaplanmış değeri yazdır",
    )
    args = parser.parse_args()

    run_all = not (args.esma or args.tesbihat or args.manifest)

    print("🔍 ZM Veri Doğrulayıcı v1.0\n")

    all_errors: list[ValidationError] = []

    if run_all or args.manifest:
        errors = validate_manifest(recompute=args.recompute_checksums)
        all_errors.extend(errors)
        try:
            manifest = load_json(MANIFEST_PATH)
            extras = []
            if manifest.get("schemaVersion"):
                extras.append(f"schemaVersion: {manifest['schemaVersion']}")
            if manifest.get("version"):
                extras.append(f"version: {manifest['version']}")
            if manifest.get("parts"):
                extras.append(f"{len(manifest['parts'])} parça")
            if manifest.get("languages"):
                extras.append(f"{len(manifest['languages'])} dil")
            print_summary("manifest.json", not errors, len(errors), " | ".join(extras))
        except Exception as e:
            print_summary("manifest.json", False, 1, str(e))

    if run_all or args.esma:
        errors = validate_esma()
        all_errors.extend(errors)
        try:
            data = load_json(ESMA_PATH)
            items = data.get("esmaulHusna", [])
            extras = f"{len(items)} kayıt"
            print_summary("data/esma.json", not errors, len(errors), extras)
        except Exception:
            print_summary("data/esma.json", False, len(errors))

    if run_all or args.tesbihat:
        errors = validate_tesbihat()
        all_errors.extend(errors)
        try:
            data = load_json(TESBIHAT_PATH)
            items = data.get("tesbihat", [])
            extras = f"{len(items)} kayıt"
            print_summary("data/tesbihat.json", not errors, len(errors), extras)
        except Exception:
            print_summary("data/tesbihat.json", False, len(errors))

    print()
    if all_errors:
        print(f"❌ {len(all_errors)} doğrulama hatası:")
        for err in all_errors:
            print(f"   • {err}")
        return 1

    print("✅ Tüm doğrulamalar geçti")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except FileNotFoundError as e:
        print(f"❌ Dosya hatası: {e}", file=sys.stderr)
        sys.exit(2)
    except json.JSONDecodeError as e:
        print(f"❌ JSON parse hatası: {e}", file=sys.stderr)
        sys.exit(2)
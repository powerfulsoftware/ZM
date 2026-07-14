# Yeni Sürüm Yayınlama Rehberi

Bu rehber, ZM repo'sunda yeni bir sürüm yayınlamak için gereken adımları gösterir.

## Ön Koşullar

- Python 3.8+
- Git
- ZM repo'suna **push** yetkisi
- GitHub hesabı (release oluşturmak için)

## İş Akışı

### 1. Değişikliği Yap

`data/esma.json` veya `data/tesbihat.json` dosyalarını düzenle. Örnek:

```bash
# eh-12'deki çeviri hatasını düzeltmek
code data/esma.json   # VS Code
```

> ⚠️ **ID'leri asla değiştirme veya silme!** Yeni kayıt ekleyebilirsin ama ID kalıcıdır.

### 2. Doğrula

Değişikliklerden sonra her zaman doğrulama scriptini çalıştır:

```bash
python scripts/validate_data.py
```

Çıktı "✅ Tüm doğrulamalar geçti" demeli. Hata varsa düzelt ve tekrar çalıştır.

### 3. Versiyonu Artır + Manifest Güncelle

```bash
# Patch: çeviri düzeltmesi, küçük içerik
python scripts/bump_version.py patch

# Minor: yeni zikir eklendi
python scripts/bump_version.py minor

# Major: geriye uyumsuz şema değişikliği (nadir)
python scripts/bump_version.py major
```

Bu script otomatik olarak:
- `manifest.json`'daki `version` alanını günceller
- `publishedAt`'i şu anki zamana ayarlar
- Checksum'ları hesaplar (esma.json + tesbihat.json SHA-256)
- `CHANGELOG.md`'ye yeni boş `[X.Y.Z] - YYYY-AA-GG` bölümü ekler

### 4. Değişiklikleri Commit'le

```bash
git add .
git commit -m "fix(esma): eh-12 'anlami' düzeltildi"
git push origin main
```

### 5. Tag Oluştur ve Push'la

```bash
git tag v1.0.1
git push origin v1.0.1
```

Bu, `.github/workflows/release.yml` workflow'unu tetikler. Workflow otomatik olarak:

1. Tüm JSON dosyalarını validate eder
2. Release'i GitHub'da oluşturur
3. Asset olarak `manifest.json`, `esma.json`, `tesbihat.json` yükler

> 💡 **İlk kez yayınlıyorsan** `.github/workflows/release.yml` repo'da mevcut olmalı. Bu repo şablonu zaten içeriyor.

### 6. Doğrula

GitHub'da `https://github.com/powerfulsoftware/ZM/releases/latest` adresine git. Yeni release görünmeli ve asset'ler indirilebilir olmalı.

---

## Manuel Release (Workflow Çalışmazsa)

`scripts/release.sh` veya `scripts/release.ps1` script'lerinden birini kullan:

**Linux/macOS:**
```bash
chmod +x scripts/release.sh
./scripts/release.sh 1.0.1
```

**Windows (PowerShell):**
```powershell
.\scripts\release.ps1 -Version 1.0.1
```

Bu script `gh` CLI kullanır (`brew install gh` veya https://cli.github.com/).

---

## Yayın Sıklığı

- **Patch**: İhtiyaç oldukça (çeviri düzeltmesi)
- **Minor**: Ayda 1-2 kez (yeni tesbihat ekleme)
- **Major**: Çok nadir (yılda 1 veya hiç)

---

## Sık Yapılan Hatalar

### ❌ ID değiştirmek
```diff
- "id": "eh-12"
+ "id": "eh-12-fixed"
```
**Sonuç**: Kullanıcının mevcut sayacı kaybolur. **Asla yapma.**

### ✅ ID aynı, sadece çeviri düzeltmek
```diff
{
  "id": "eh-12",
  "sira": 12,
- "translations": { "tr": { "anlami": "Eksik açıklama" } }
+ "translations": { "tr": { "anlami": "Doğru ve tam açıklama" } }
}
```

### ❌ Silinen kaydın ID'sini yeniden kullanmak
```diff
- { "id": "eh-12", ... }
+ { "id": "eh-12", "sira": 100, ... }
```
**Sonuç**: Uygulama aynı ID'ye sahip iki kayıt görür ve kullanıcı sayacı yanlış kayda bağlanır.

### ✅ Silinen kaydın ID'sini yeniden kullanmamak
```diff
- { "id": "eh-12", ... }
+ { "id": "eh-100", "sira": 100, ... }
```

---

## Acil Durum: Geri Çekme

Yanlış bir release yayınlandıysa:

1. **Yayını silme** (kullanıcılar cache'lemiş olabilir)
2. Yeni bir **patch** release yap: `bump_version.py patch`
3. Düzeltmeleri uygula, yeni release yayınla

Uygulama tarafı cache'inde `manifestVersion` karşılaştırması yapıldığı için eski release'i kullanan kullanıcılar bir sonraki güncellemede yeni sürüme geçer.
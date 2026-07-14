# ZM – ZikirMatik Remote Library

Bu repo, **ZikirMatik** mobil uygulamasının uzaktan güncellediği zikir kütüphanesini içerir.

## Genel Bakış

ZikirMatik uygulaması, Esmaül Hüsna ve tesbihat listelerini bu repo üzerinden **GitHub Releases** aracılığıyla indirir. Yeni içerik eklemek, çeviri düzeltmek veya hedef sayıları güncellemek için tek yapılması gereken yeni bir release yayınlamaktır.

## İçerik

- `data/esma.json` – 99 Esmaül Hüsna (6 dilde)
- `data/tesbihat.json` – Tesbihat listesi (6 dilde)
- `manifest.json` – Şema ve sürüm bilgisi
- `scripts/bump_version.py` – Versiyon ve manifest güncelleme scripti
- `scripts/validate_data.py` – JSON şema doğrulayıcı
- `docs/SCHEMA.md` – Veri şeması detayları
- `docs/RELEASE_GUIDE.md` – Yeni sürüm yayınlama adımları
- `docs/CHANGELOG.md` – Sürüm geçmişi

## Hızlı Başlangıç

### Yeni içerik yayınlama (en kolay yol)

```bash
# 1. Değişikliği yap
# 2. Versiyonu artır + manifest güncelle
python scripts/bump_version.py patch

# 3. Değişiklikleri commit'le
git add .
git commit -m "feat(esma): eh-12 düzeltildi"
git push origin main

# 4. Tag oluştur ve push'la (GitHub Actions otomatik release yapar)
git tag v1.0.1
git push origin v1.0.1
```

Daha fazla bilgi: [docs/RELEASE_GUIDE.md](docs/RELEASE_GUIDE.md)

## Desteklenen Diller

| Kod | Dil      |
|-----|----------|
| tr  | Türkçe   |
| en  | İngilizce |
| ar  | Arapça   |
| az  | Azerbaycanca |
| ru  | Rusça    |
| es  | İspanyolca |

## Lisans

MIT — bkz. [LICENSE](LICENSE)
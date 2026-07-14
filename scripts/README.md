# ZM Veri Doğrulayıcı

`data/` klasöründeki JSON dosyalarını ve `manifest.json`'ı şema kurallarına göre doğrular.

## Kullanım

```bash
# Tüm dosyaları doğrula
python scripts/validate_data.py

# Sadece belirli bir dosyayı doğrula
python scripts/validate_data.py --esma
python scripts/validate_data.py --tesbihat
python scripts/validate_data.py --manifest

# Manifest'teki checksum'ları yeniden hesapla
python scripts/validate_data.py --recompute-checksums
```

## Kontrol Listesi

- ✅ JSON sözdizimi geçerli
- ✅ Üst düzey alanlar doğru tipte (array)
- ✅ Zorunlu alanlar mevcut
- ✅ ID alanları unique
- ✅ Sıra numaraları 1-N ardışık (esma için)
- ✅ Tüm kayıtlarda aynı dil kümeleri
- ✅ Manifest'teki dil listesi tutarlı
- ✅ Hedef değerleri pozitif integer
- ✅ Manifest checksum'ları dosya ile eşleşiyor (varsa)

## Çıktı

```
🔍 ZM Veri Doğrulayıcı v1.0

📄 manifest.json
   ✅ schemaVersion: 1
   ✅ version: 1.0.0
   ✅ parts: 2 dosya
   ✅ languages: 6 dil

📄 data/esma.json
   ✅ 99 kayıt
   ✅ ID'ler unique (eh-1..eh-99)
   ✅ Sıra: 1-99 ardışık
   ✅ Tüm kayıtlarda 6 dil mevcut

📄 data/tesbihat.json
   ✅ 6 kayıt
   ✅ ID'ler unique
   ✅ Tüm kayıtlarda 6 dil mevcut

✅ Tüm doğrulamalar geçti
```

Hata varsa exit code `1` döner, CI/CD'de kullanılabilir.

## CI Entegrasyonu

GitHub Actions workflow her PR'da bu scripti çalıştırır. Hata varsa PR merge edilemez.
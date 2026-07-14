# Veri Şeması

Bu doküman `ZM` repo'sunda yayınlanan JSON veri yapılarını tanımlar.

## Üst Düzey Yapı

```
ZM/
├── manifest.json       # sürüm + parça listesi + checksum
└── data/
    ├── esma.json       # Esmaül Hüsna
    └── tesbihat.json   # Tesbihat listesi
```

## schemaVersion

`schemaVersion` alanı uyumluluk kontrolü için kullanılır. ZikirMatik uygulaması `schemaVersion`'u tanımıyorsa güncelleme reddedilir ve kullanıcı bilgilendirilir ("Lütfen uygulamayı güncelleyin").

### Uyumluluk Kuralları

| schemaVersion uygulamada | manifest'te | Sonuç |
|--------------------------|-------------|-------|
| Yok                      | 1           | ✅ Güncelle |
| 1                        | 1           | ✅ Güncelle |
| 1                        | 2           | ❌ Reddet (uygulama eski) |
| 1                        | 0           | ❌ Reddet (manifest geçersiz) |

### Yeni Sürüm Politikası

- **Major (X.0.0) → yeni schemaVersion**: Şemada geriye uyumsuz değişiklik (alan adı değişimi, kaldırılması, yapısal kırılma).
- **Minor (0.X.0) → schemaVersion sabit**: Yeni alanlar eklenebilir (geriye uyumlu).
- **Patch (0.0.X) → schemaVersion sabit**: Çeviri düzeltmesi, içerik düzeltmesi.

---

## manifest.json

```json
{
  "schemaVersion": 1,
  "version": "1.2.0",
  "publishedAt": "2026-07-14T11:00:00Z",
  "minAppVersion": "1.0.0",
  "parts": {
    "esma": "esma.json",
    "tesbihat": "tesbihat.json"
  },
  "checksums": {
    "esma": "sha256-abc123...",
    "tesbihat": "sha256-def456..."
  },
  "languages": ["tr", "en", "ar", "az", "ru", "es"]
}
```

| Alan            | Tip    | Zorunlu | Açıklama |
|-----------------|--------|---------|----------|
| `schemaVersion` | int    | evet    | Uyumluluk anahtarı. Şu an `1`. |
| `version`       | string | evet    | Semver (`1.2.3`). Kullanıcıya gösterilir. |
| `publishedAt`   | string | evet    | ISO 8601 UTC. |
| `minAppVersion` | string | evet    | Manifest'i okuyabilecek en düşük uygulama versiyonu. |
| `parts`         | object | evet    | Her parça için dosya adı. |
| `checksums`     | object | hayır   | SHA-256 (opsiyonel, gelecekte zorunlu olabilir). |
| `languages`     | array  | evet    | Desteklenen dil kodları. |

---

## data/esma.json

```json
{
  "esmaulHusna": [
    {
      "id": "eh-1",
      "sira": 1,
      "hedef": 99,
      "translations": {
        "tr": { "isim": "Allah", "anlami": "İlahiyet sahibi, gerçek ilah" },
        "en": { "isim": "Allah", "anlami": "The God, the true deity" }
      }
    }
  ]
}
```

| Alan                  | Tip   | Zorunlu | Açıklama |
|-----------------------|-------|---------|----------|
| `esmaulHusna`         | array | evet    | Tüm esma kayıtları. |
| `esmaulHusna[].id`    | string | evet   | **Değişmez** kimlik. Uygulama bunu primary key olarak kullanır. Bir kez atanır, bir daha değiştirilmez. |
| `esmaulHusna[].sira`  | int    | evet   | 1-99 arası sıra numarası. |
| `esmaulHusna[].hedef` | int    | evet   | Varsayılan hedef sayısı. Kullanıcı override edebilir. |
| `esmaulHusna[].translations` | object | evet | Dil koduna göre çeviri. |
| `translations.<lang>.isim`   | string | evet | Görünen ad. |
| `translations.<lang>.anlami` | string | evet | Anlam açıklaması. |

### ID Kuralları

- ID kalıcıdır. Bir kez `eh-12` olan kayıt her zaman `eh-12` kalır.
- Yeni esma eklenirse en sona `eh-100`, `eh-101` vb. verilir (boşluklar doldurulmaz).
- Silinen esma'nın ID'si **asla yeniden kullanılmaz** (güvenlik).
- **Önemli**: ID formatı `<prefix>-<n>` şeklindedir (`eh-1`, `tes-1` vb.). Mevcut ID'ler değiştirilemez; kullanıcının sayaç verisi bu ID'lere bağlıdır.

---

## data/tesbihat.json

```json
{
  "tesbihat": [
    {
      "id": "tesbihat-subhanallah",
      "hedef": 33,
      "translations": {
        "tr": { "isim": "Sübhanallah", "aciklama": "Allah'ı tüm noksanlıklardan tenzih ederiz" },
        "en": { "isim": "SubhanAllah", "aciklama": "Glory be to Allah" }
      }
    }
  ]
}
```

| Alan                  | Tip   | Zorunlu | Açıklama |
|-----------------------|-------|---------|----------|
| `tesbihat`            | array | evet    | Tüm tesbihat kayıtları. |
| `tesbihat[].id`       | string | evet   | **Değişmez** kimlik. `tes-<n>` formatında (örn: `tes-1`). |
| `tesbihat[].hedef`    | int    | evet   | Varsayılan hedef (genelde 33, 100 veya 1000). |
| `tesbihat[].translations` | object | evet | Dil koduna göre çeviri. |
| `translations.<lang>.isim`     | string | evet | Görünen ad. |
| `translations.<lang>.aciklama` | string | evet | Açıklama metni. |

---

## Geçerlilik Kuralları (Doğrulama)

`scripts/validate_data.py` scripti her release öncesi çalıştırılmalıdır. Kontrol ettiği kurallar:

1. ✅ JSON parse edilebilir
2. ✅ Üst düzey alanlar (`esmaulHusna` veya `tesbihat`) array
3. ✅ Her kayıt zorunlu alanlara sahip
4. ✅ `id` alanı unique
5. ✅ `sira` alanı 1-N (N=eleman sayısı) ardışık
6. ✅ Tüm kayıtlarda **aynı dil kümeleri** mevcut (bir kayıtta `tr`, `en` varsa hepsinde olmalı)
7. ✅ Manifest'teki `languages` array'inde belirtilen tüm dillerde çeviri var
8. ✅ ID formatı doğru (`eh-<n>` veya `tesbihat-<slug>`)
9. ✅ `hedef` > 0 ve integer
10. ✅ ID formatı: esma için `eh-<n>`, tesbihat için `tes-<n>`

---

## Cache Uygulama Sözleşmesi (Uygulama Tarafı)

- Kullanıcının sayaç verisi (`state.zikirler`, `state.tarihce`) **asla** remote veri tarafından değiştirilmez.
- Remote veri **sadece** şablondur (isim, çeviri, varsayılan hedef).
- Kullanıcının `hedef` override'ı korunur (örn. 99 → 1000).
- Silinen bir `id` artık görünmez ama kullanıcının sayacı korunur.
- Yeni `id` kütüphane listesinde `sayi=0` ile görünür; kullanıcı seçince eklenir.
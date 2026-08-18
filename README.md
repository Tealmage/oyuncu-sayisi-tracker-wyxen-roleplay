# Wyxen Roleplay Oyuncu Takip Sistemi

Garry's Mod sunucunuz için tamamen ücretsiz, otomatik oyuncu istatistik sistemi.

## Ne Yapar?

Bu sistem Wyxen Roleplay Garry's Mod sunucunuzu düzenli aralıklarla sorgular ve oyuncu istatistiklerini otomatik olarak toplar. Tamamen ücretsiz ve GitHub üzerinde çalışır.

**Özellikler:**
- ✅ Her 5 dakikada bir otomatik sunucu sorgusu
- ✅ Oyuncu oynama sürelerini takip eder
- ✅ Haftalık, aylık ve tüm zamanlar istatistikleri
- ✅ Tamamen ücretsiz (GitHub Actions kullanır)
- ✅ Web sitenizden JSON olarak erişilebilir
- ✅ Bilgisayarınızın açık olmasına gerek yok

## Önemli Bilgiler

**SINIRLAMALAR:**
- A2S protokolü genellikle SteamID vermez, sadece oyuncu ismi verir
- Bu nedenle oyuncu takibi oyuncu ismine göre yapılır (isim değişirse takip devam eder)
- GitHub Actions tam 5 dakikada bir çalışmaz, birkaç dakika gecikebilir
- İlk günden geçmiş veri olmaz, sistem çalıştıkça veri birikir
- Oyuncu süreleri "yaklaşık" değerlerdir (±5 dakika hata payı)

## GitHub'da Kurulum (Adım Adım)

### Adım 1: Repository'ye Dosyaları Yükle

1. GitHub'da `wyxen-player-tracker` repository'nize gidin
2. Ana sayfada yeşil **"Add file"** butonuna tıklayın
3. **"Create new file"** seçin

### Adım 2: İlk Dosya - Workflow

1. Dosya adı alanına şunu yazın: `.github/workflows/tracker.yml`
2. İçeriğe `tracker.yml` dosyasının kodunu yapıştırın (yukarıda verildi)
3. Sayfanın altındaki yeşil **"Commit new file"** butonuna tıklayın

### Adım 3: İkinci Dosya - Python Script

1. Tekrar **"Add file"** > **"Create new file"**
2. Dosya adı: `tracker.py`
3. İçeriğe `tracker.py` kodunu yapıştırın
4. **"Commit new file"**

### Adım 4: Üçüncü Dosya - Requirements

1. **"Add file"** > **"Create new file"**
2. Dosya adı: `requirements.txt`
3. İçerik: `python-a2s==1.3.0`
4. **"Commit new file"**

### Adım 5: Dördüncü Dosya - Data

1. **"Add file"** > **"Create new file"**
2. Dosya adı: `data/stats.json`
3. İçeriğe `stats.json` başlangıç kodunu yapıştırın
4. **"Commit new file"**

### Adım 6: Beşinci Dosya - .gitignore

1. **"Add file"** > **"Create new file"**
2. Dosya adı: `.gitignore`
3. İçeriğe `.gitignore` kodunu yapıştırın
4. **"Commit new file"**

### Adım 7: GitHub Actions'ı Etkinleştir

1. Repository'nizde üstteki **"Actions"** sekmesine tıklayın
2. "I understand my workflows" yazısı varsa yeşil butona tıklayın
3. Sol tarafta **"Wyxen Player Tracker"** workflow'unu göreceksiniz

### Adım 8: İlk Çalıştırmayı Yapın (Test)

1. Actions sekmesinde, sol tarafta **"Wyxen Player Tracker"** üzerine tıklayın
2. Sağ tarafta mavi **"Run workflow"** butonu görünecek
3. Butona tıklayın ve açılan menüde tekrar yeşil **"Run workflow"** butonuna tıklayın
4. Sayfa yenilenecek, birkaç saniye bekleyin
5. Sarı nokta görünecek (çalışıyor demek)

### Adım 9: Sonucu Kontrol Edin

1. Sarı nokta yeşil tik ✅ olduğunda tıklayın
2. **"track-players"** job'una tıklayın
3. Logları açın ve şunları kontrol edin:
   - `[INFO] Querying 185.213.240.239:27015`
   - `[INFO] Server: Wyxen Roleplay` (veya sunucu adınız)
   - `[INFO] Players online: X`
   - `[INFO] Saved data/stats.json`
   - `[INFO] === Tracker Completed Successfully ===`

4. Eğer bunları görüyorsanız **BAŞARILI!** 🎉

### Adım 10: JSON Dosyasını Görüntüle

1. Repository ana sayfasına dönün
2. `data` klasörüne tıklayın
3. `stats.json` dosyasına tıklayın
4. Sunucu ve oyuncu verilerini göreceksiniz

## Otomatik Çalışma

Artık sistem her 5 dakikada bir otomatik çalışacak. Actions sekmesinden geçmişi görebilirsiniz.

**NOT:** GitHub Actions'ın cron sistemi kesin zamanlı değildir. Bazen 6-8 dakika gecikebilir.

## Web Sitenizde Kullanım

JSON dosyasına şu şekilde erişebilirsiniz:

```
https://raw.githubusercontent.com/KULLANICI_ADINIZ/wyxen-player-tracker/main/data/stats.json
```

**JavaScript Örneği:**
```javascript
fetch('https://raw.githubusercontent.com/KULLANICI_ADINIZ/wyxen-player-tracker/main/data/stats.json')
  .then(response => response.json())
  .then(data => {
    console.log('Sunucu:', data.server.name);
    console.log('Online Oyuncular:', data.server.players);
    console.log('Toplam Takip Edilen:', Object.keys(data.players).length);
  });
```

**ÖNEMLİ - CORS:** GitHub raw dosyaları CORS header'ı vermeyebilir. Bu durumda şu alternatifler var:
- jsDelivr CDN kullanın: `https://cdn.jsdelivr.net/gh/KULLANICI_ADINIZ/wyxen-player-tracker@main/data/stats.json`
- GitHub Pages etkinleştirin
- Kendi backend'inizden proxy yapın

## Veri Yapısı

```json
{
  "server": {
    "online": true,
    "players": 42,
    "name": "Wyxen Roleplay",
    "map": "rp_downtown_v4c_v2"
  },
  "players": {
    "name:Ahmet": {
      "name": "Ahmet",
      "total_minutes": 1234,
      "first_seen": "2026-08-18T10:00:00",
      "last_seen": "2026-08-18T12:30:00",
      "weekly_stats": {
        "2026-08-12T00:00:00": 450
      },
      "monthly_stats": {
        "2026-08-01T00:00:00": 1234
      }
    }
  }
}
```

## Sorun Giderme

### Actions Çalışmıyor
1. Actions sekmesine gidin
2. Workflow'u seçin
3. Kırmızı X varsa tıklayın ve hatayı okuyun
4. `permissions: contents: write` olduğundan emin olun

### A2S Timeout Hatası
- Sunucu geçici olarak offline olabilir
- Bu normal, bir sonraki sorguda düzelecek
- Sürekli hata alıyorsanız sunucu IP/port'unu kontrol edin

### JSON Güncellenmiyor
1. Actions loglarına bakın
2. "nothing to commit" yazıyorsa değişiklik yok demektir
3. Sunucuda oyuncu varsa ve sistem çalışıyorsa güncellenmelidir

### Permission Denied
1. Repository Settings > Actions > General
2. "Workflow permissions" kısmında "Read and write permissions" seçili olmalı

## Sistem Nasıl Çalışır?

1. **GitHub Actions** her 5 dakikada tracker.py'yi çalıştırır
2. **tracker.py** sunucuyu A2S ile sorgular
3. Online oyuncuları tespit eder
4. Son sorgudan bu yana geçen süreyi hesaplar
5. Her online oyuncuya bu süreyi ekler
6. Haftalık/aylık istatistikleri günceller
7. JSON'u kaydeder ve GitHub'a commit eder

## Lisans

Bu proje tamamen ücretsizdir ve istediğiniz gibi kullanabilirsiniz.

---

**Hazırlayan:** Wyxen Player Tracker System
**Sunucu:** Wyxen Roleplay (185.213.240.239:27015)
**Versiyon:** 1.0

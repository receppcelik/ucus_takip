import time
from datetime import datetime
import requests

# --- TELEGRAM BİLGİLERİNİZ ---
TELEGRAM_TOKEN = "8917847840:AAF9WhTKkQpzwdKFqsjJ0G37I_ocgmo5dlY"
TELEGRAM_CHAT_ID = "1438895909"

# --- TARAMA PARAMETRELERİ ---
MAKS_FIYAT = 15000  # İlk bildirimlerin gelebilmesi için limiti yüksek tutuyoruz
HEDEF_TARIHLER = ["14/09/2026", "21/09/2026", "28/09/2026"]


def telegram_mesaj_gonder(mesaj):
    """Belirtilen Telegram hesabına doğrudan bildirim gönderir."""
    url = f"https://telegram.org{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": mesaj, "parse_mode": "Markdown"}
    try:
        response = requests.post(url, json=payload, timeout=12)
        print(f"Telegram Gönderim Durumu: {response.status_code}")
    except Exception as e:
        print(f"Telegram Bağlantı Hatası: {e}")


def ucus_tara():
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Tarama başlatıldı...")
    
    # 🚨 ZORUNLU TELEGRAM BAĞLANTI TESTİ 🚨
    # Sistem her çalıştığında, uçuş listesinden bağımsız olarak Telegram hattınızı test eder.
    telegram_mesaj_gonder("🤖 *Uçuş Takip Sistemi Bildirimi:* GitHub otomasyonu başarıyla tetiklendi, veri taraması yapılıyor...")

    for tarih in HEDEF_TARIHLER:
        # Resmi API standartlarına uygun, hata payı olmayan güvenli URL yapısı
        api_url = "https://skypicker.com"
        parametreler = {
            "flyFrom": "SAW",
            "to": "ERZ",
            "dateFrom": tarih,
            "dateTo": tarih,
            "partner": "picky",
            "curr": "TRY"
        }
        
        # Turna.com yönlendirme satın alma link formatı
        gun, ay, yil = tarih.split("/")
        satinalma_url = f"https://turna.com{gun}-{ay}-{yil}"

        try:
            # Parametreleri URL içine gömmek yerine güvenli requests yapısıyla gönderiyoruz
            response = requests.get(api_url, params=parametreler, timeout=15)
            print(f"API Yanıt Kodu ({tarih}): {response.status_code}")
            
            if response.status_code == 200:
                veri = response.json()
                if veri.get("data") and len(veri["data"]) > 0:
                    en_ucuz_ucus = min(veri["data"], key=lambda x: x["price"])
                    fiyat = int(en_ucuz_ucus["price"])
                    havayolu = en_ucuz_ucus.get("airlines", ["Bilinmiyor"])

                    print(f"-> {tarih} Tarihli En Düşük Fiyat: {fiyat} TL")

                    if fiyat <= MAKS_FIYAT:
                        mesaj = (
                            f"🚨 **UCUZ UÇUŞ ALERMİ!** 🚨\n\n"
                            f"✈️ **Rota:** İstanbul (SAW) -> Erzurum (ERZ)\n"
                            f"📅 **Tarih:** {tarih}\n"
                            f"💺 **Havayolu:** {havayolu}\n"
                            f"💰 **Fiyat:** {fiyat} TL\n\n"
                            f"🛒 [Satın Almak İçin Tıklayın]({satinalma_url})"
                        )
                        telegram_mesaj_gonder(mesaj)
                else:
                    print(f"⚠️ {tarih} tarihi için veri havuzunda aktif uçuş bulunamadı.")
            else:
                print(f"❌ API Sunucu Hatası: Kod {response.status_code}")
        except Exception as e:
            print(f"⚠️ {tarih} taranırken internet bağlantı hatası oluştu: {e}")

        time.sleep(4)


if __name__ == "__main__":
    ucus_tara()

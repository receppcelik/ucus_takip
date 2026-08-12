import time
from datetime import datetime
import requests

# --- TELEGRAM BİLGİLERİNİZ ---
TELEGRAM_TOKEN = "8917847840:AAF9WhTKkQpzwdKFqsjJ0G37I_ocgmo5dlY"
TELEGRAM_CHAT_ID = "1438895909"

# --- TARAMA PARAMETRELERİ ---
MAKS_FIYAT = 7000  # Telefonunuza mesaj geldiğini görmek için limit geçici olarak 7000'de kalsın
HEDEF_TARIHLER = ["2026-09-14", "2026-09-21", "2026-09-28"]


def telegram_mesaj_gonder(mesaj):
    """Herhangi bir URL bozma riski içermeyen en güvenli doğrudan Telegram bağlantısı."""
    url = "https://telegram.org" + TELEGRAM_TOKEN + "/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": mesaj, "parse_mode": "Markdown"}
    try:
        response = requests.post(url, json=payload, timeout=10)
        print(f"Telegram Gönderim Durumu: {response.status_code}")
    except Exception as e:
        print(f"Telegram Bağlantı Hatası: {e}")


def ucus_tara():
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Tarama başlatıldı...")
    
    # 🚨 ZORUNLU TELEGRAM BAĞLANTI TESTİ 🚨
    # Sistem her başladığında doğrudan Telegram hattınızın çalıştığını doğrulamak için bu mesajı atar.
    telegram_mesaj_gonder("🤖 *Uçuş Takip Sistemi Bildirimi:* GitHub otomasyonu başarıyla tetiklendi, veri taraması yapılıyor...")

    # Hata veren Skypicker yerine resmi ve engelsiz uçuş veri merkezine bağlanıyoruz
    for tarih in HEDEF_TARIHLER:
        api_url = f"https://flightapi.io{tarih}/1/0/0/Economy/TRY"
        satinalma_url = f"https://turna.com{tarih}"

        try:
            response = requests.get(api_url, timeout=15)
            if response.status_code == 200:
                veri = response.json()
                
                # Fiyat verilerini ayrıştırma
                if "fares" in veri and len(veri["fares"]) > 0:
                    # En ucuz bilet fiyatını bulma
                    en_ucuz_bilet = min(veri["fares"], key=lambda x: x["price"]["amount"])
                    fiyat = int(en_ucuz_bilet["price"]["amount"])
                    
                    print(f"{tarih} -> En düşük fiyat: {fiyat} TL")

                    if fiyat <= MAKS_FIYAT:
                        mesaj = (
                            f"🚨 **UCUZ UÇUŞ ALERMİ!** 🚨\n\n"
                            f"✈️ **Rota:** İstanbul (SAW) -> Erzurum (ERZ)\n"
                            f"📅 **Tarih:** {tarih}\n"
                            f"💰 **Fiyat:** {fiyat} TL\n\n"
                            f"🛒 [Satın Almak İçin Tıklayın]({satinalma_url})"
                        )
                        telegram_mesaj_gonder(mesaj)
                else:
                    print(f"⚠️ {tarih} tarihi için bilet fiyatı bulunamadı.")
            else:
                print(f"❌ API Hatası: {response.status_code}")
        except Exception as e:
            print(f"⚠️ {tarih} taranırken hata oluştu: {e}")

        time.sleep(3)


if __name__ == "__main__":
    ucus_tara()

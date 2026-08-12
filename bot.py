import time
from datetime import datetime
import requests

# --- TELEGRAM BİLGİLERİNİZ ---
TELEGRAM_TOKEN = "8917847840:AAF9WhTKkQpzwdKFqsjJ0G37I_ocgmo5dlY"
TELEGRAM_CHAT_ID = "1438895909"

# --- TARAMA PARAMETRELERİ ---
MAKS_FIYAT = 15000
HEDEF_TARIHLER = ["2026-09-14", "2026-09-21", "2026-09-28"]


def telegram_mesaj_gonder(mesaj):
    url = f"https://telegram.org{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": mesaj, "parse_mode": "Markdown"}
    try:
        response = requests.post(url, json=payload, timeout=10)
        print(f"Telegram Yanıtı: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Telegram Bağlantı Hatası: {e}")


def ucus_tara():
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Tarama başlatıldı...")
    
    # 🚨 ZORUNLU BAĞLANTI TESTİ 🚨
    # API çalışmasa bile Telegram hattınızın aktif olduğunu görmek için her açılışta bu mesajı atar.
    telegram_mesaj_gonder("🤖 *Uçuş Takip Botu Bağlantı Testi:* GitHub sistemi başarıyla tetiklendi, Telegram bağlantısı aktif!")

    for tarih in HEDEF_TARIHLER:
        api_url = f"https://skypicker.com{tarih.replace('-', '/')}&dateTo={tarih.replace('-', '/')}&partner=picky&curr=TRY"
        satinalma_url = f"https://turna.com{tarih}"

        try:
            response = requests.get(api_url, timeout=15)
            print(f"API Yanıt Kodu ({tarih}): {response.status_code}")
            
            if response.status_code == 200:
                veri = response.json()
                if veri.get("data") and len(veri["data"]) > 0:
                    en_ucuz_ucus = min(veri["data"], key=lambda x: x["price"])
                    fiyat = int(en_ucuz_ucus["price"])
                    havayolu = en_ucuz_ucus.get("airlines", ["Bilinmiyor"])

                    print(f"Bulunan Fiyat ({tarih}): {fiyat} TL")

                    if fiyat <= MAKS_FIYAT:
                        mesaj = (
                            f"🚨 **UCUZ UÇUŞ BULDUM!** 🚨\n\n"
                            f"✈️ **Rota:** Sabiha Gökçen (SAW) -> Erzurum (ERZ)\n"
                            f"📅 **Tarih:** {tarih}\n"
                            f"💺 **Havayolu:** {havayolu}\n"
                            f"💰 **Fiyat:** {fiyat} TL\n\n"
                            f"🛒 [Satın Almak İçin Tıklayın]({satinalma_url})"
                        )
                        telegram_mesaj_gonder(mesaj)
                else:
                    print(f"⚠️ {tarih} için API boş veri döndü (Uçuş bulunamadı).")
            else:
                print(f"❌ API Hatası: {response.status_code}")
        except Exception as e:
            print(f"Bağlantı hatası: {e}")

        time.sleep(3)


if __name__ == "__main__":
    ucus_tara()

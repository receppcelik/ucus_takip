import time
from datetime import datetime
import requests

# --- TELEGRAM BİLGİLERİNİZ ---
TELEGRAM_TOKEN = "8917847840:AAF9WhTKkQpzwdKFqsjJ0G37I_ocgmo5dlY"
TELEGRAM_CHAT_ID = "1438895909"

# --- TARAMA PARAMETRELERİ ---
MAKS_FIYAT = 2000
HEDEF_TARIHLER = ["2026-09-14", "2026-09-21", "2026-09-28"]


def telegram_mesaj_gonder(mesaj):
    url = f"https://telegram.org{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": mesaj, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Telegram hatası: {e}")


def ucus_tara():
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Tarama başlatıldı...")

    for tarih in HEDEF_TARIHLER:
        # GitHub üzerinden doğrudan çalışan engelsiz API bağlantısı
        api_url = f"https://skypicker.com{tarih.replace('-', '/')}&dateTo={tarih.replace('-', '/')}&partner=picky&curr=TRY"
        satinalma_url = f"https://turna.com{tarih}"

        try:
            response = requests.get(api_url, timeout=15)
            if response.status_code == 200:
                veri = response.json()
                if veri.get("data"):
                    en_ucuz_ucus = min(veri["data"], key=lambda x: x["price"])
                    fiyat = int(en_ucuz_ucus["price"])
                    havayolu = en_ucuz_ucus.get("airlines", ["Bilinmiyor"])[0]

                    print(f"{tarih} -> En düşük fiyat: {fiyat} TL")

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
                    print(f"⚠️ {tarih} için bilet bulunamadı.")
            else:
                print(f"❌ API Hatası: {response.status_code}")
        except Exception as e:
            print(f"Bağlantı hatası: {e}")

        time.sleep(3)


if __name__ == "__main__":
    # GitHub Actions her tetiklendiğinde bir kez tarama yapar
    ucus_tara()

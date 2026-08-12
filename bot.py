import requests

# --- TELEGRAM BİLGİLERİNİZ ---
TOKEN = "8917847840:AAF9WhTKkQpzwdKFqsjJ0G37I_ocgmo5dlY"
CHAT_ID = "1438895909"

def test_mesaji_gonder():
    print("Telegram testi başlatılıyor...")
    # Hiçbir dinamik adres birleştirmesi içermeyen, tamamen düz metin URL yapısı
    url = "https://telegram.org"
    payload = {
        "chat_id": "1438895909",
        "text": "🚨 **UÇUŞ TAKİP SİSTEMİ ÇALIŞIYOR!** 🚨\n\nGitHub otomasyonunuz başarıyla tetiklendi. Telegram bağlantınız aktif hale getirildi ve botunuz şu an 7/24 çalışıyor!",
        "parse_mode": "Markdown"
    }
    try:
        response = requests.post(url, json=payload, timeout=10)
        print(f"Sonuç: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Bağlantı Hatası: {e}")

if __name__ == "__main__":
    test_mesaji_gonder()

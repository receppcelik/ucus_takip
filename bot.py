import os
import time
import json
from datetime import date, timedelta

import requests


# =========================================================
# AYARLAR
# =========================================================

ORIGIN = "SAW"
DESTINATION = "ERZ"

# 5.000 TL'nin altındaki fiyatlarda bildirim
PRICE_LIMIT = 5000

# Eylül 2026
START_DATE = date(2026, 9, 1)
END_DATE = date(2026, 9, 30)

# 10 dakika
CHECK_INTERVAL = 600

AMADEUS_URL = "https://api.amadeus.com"

STATE_FILE = "sent_prices.json"


# =========================================================
# GİZLİ BİLGİLER
# =========================================================

AMADEUS_CLIENT_ID = os.environ["AMADEUS_CLIENT_ID"]
AMADEUS_CLIENT_SECRET = os.environ["AMADEUS_CLIENT_SECRET"]

TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]


# =========================================================
# AMADEUS TOKEN AL
# =========================================================

def get_amadeus_token():

    url = f"{AMADEUS_URL}/v1/security/oauth2/token"

    data = {
        "grant_type": "client_credentials",
        "client_id": AMADEUS_CLIENT_ID,
        "client_secret": AMADEUS_CLIENT_SECRET,
    }

    response = requests.post(
        url,
        data=data,
        timeout=30
    )

    response.raise_for_status()

    return response.json()["access_token"]


# =========================================================
# UÇUŞLARI ARA
# =========================================================

def search_flights(token, departure_date):

    url = f"{AMADEUS_URL}/v2/shopping/flight-offers"

    params = {
        "originLocationCode": ORIGIN,
        "destinationLocationCode": DESTINATION,
        "departureDate": departure_date.isoformat(),
        "adults": 1,
        "currencyCode": "TRY",
        "max": 50,
    }

    headers = {
        "Authorization": f"Bearer {token}",
    }

    response = requests.get(
        url,
        params=params,
        headers=headers,
        timeout=45
    )

    if response.status_code != 200:

        print(
            f"[API HATASI] "
            f"{departure_date} "
            f"{response.status_code}"
        )

        print(response.text[:500])

        return []

    return response.json().get("data", [])


# =========================================================
# EN UCUZ UÇUŞU BUL
# =========================================================

def find_cheapest_offer(offers):

    cheapest = None

    for offer in offers:

        try:

            price = float(
                offer["price"]["grandTotal"]
            )

            if cheapest is None:

                cheapest = (
                    price,
                    offer
                )

            elif price < cheapest[0]:

                cheapest = (
                    price,
                    offer
                )

        except (
            KeyError,
            TypeError,
            ValueError
        ):

            continue

    return cheapest


# =========================================================
# TELEGRAM MESAJI GÖNDER
# =========================================================

def send_telegram(message):

    url = (
        f"https://api.telegram.org/"
        f"bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    )

    data = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
    }

    response = requests.post(
        url,
        data=data,
        timeout=30
    )

    response.raise_for_status()

    print("[TELEGRAM] Bildirim gönderildi.")


# =========================================================
# BİLDİRİM GEÇMİŞİNİ OKU
# =========================================================

def load_state():

    if not os.path.exists(STATE_FILE):

        return {}

    try:

        with open(
            STATE_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            return json.load(file)

    except Exception:

        return {}


# =========================================================
# BİLDİRİM GEÇMİŞİNİ KAYDET
# =========================================================

def save_state(state):

    with open(
        STATE_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            state,
            file,
            ensure_ascii=False,
            indent=2
        )


# =========================================================
# UÇUŞ DETAYLARI
# =========================================================

def get_flight_details(offer):

    itineraries = offer.get(
        "itineraries",
        []
    )

    if not itineraries:

        return {
            "departure": "?",
            "arrival": "?",
            "airlines": "?",
            "stops": "?"
        }

    segments = itineraries[0].get(
        "segments",
        []
    )

    if not segments:

        return {
            "departure": "?",
            "arrival": "?",
            "airlines": "?",
            "stops": "?"
        }

    first_segment = segments[0]
    last_segment = segments[-1]

    departure = first_segment[
        "departure"
    ].get(
        "at",
        "?"
    )

    arrival = last_segment[
        "arrival"
    ].get(
        "at",
        "?"
    )

    airlines = []

    for segment in segments:

        airline = segment.get(
            "carrierCode"
        )

        if (
            airline
            and airline not in airlines
        ):

            airlines.append(airline)

    stops = len(segments) - 1

    if stops == 0:

        stop_text = "Direkt"

    else:

        stop_text = f"{stops} aktarma"

    return {
        "departure": departure.replace(
            "T",
            " "
        ),

        "arrival": arrival.replace(
            "T",
            " "
        ),

        "airlines": ", ".join(
            airlines
        ),

        "stops": stop_text
    }


# =========================================================
# TELEGRAM MESAJI OLUŞTUR
# =========================================================

def create_message(
    departure_date,
    price,
    offer
):

    details = get_flight_details(
        offer
    )

    return (
        "🚨 UCUZ UÇAK BİLETİ!\n\n"

        "✈️ SAW → ERZ\n"

        f"📅 Tarih: "
        f"{departure_date.strftime('%d.%m.%Y')}\n"

        f"💰 Fiyat: "
        f"{price:,.0f} TL\n"

        f"🏷️ Havayolu: "
        f"{details['airlines']}\n"

        f"🔄 Uçuş: "
        f"{details['stops']}\n"

        f"🛫 Kalkış: "
        f"{details['departure']}\n"

        f"🛬 Varış: "
        f"{details['arrival']}\n\n"

        "⚠️ Fiyat satın alma sırasında "
        "değişebilir."
    )


# =========================================================
# EYLÜL'Ü TARA
# =========================================================

def scan_september():

    print()
    print("=" * 60)
    print("✈️ SAW → ERZ UÇUŞ KONTROLÜ")
    print("=" * 60)

    print(
        f"Tarih: "
        f"{START_DATE.strftime('%d.%m.%Y')} "
        f"- "
        f"{END_DATE.strftime('%d.%m.%Y')}"
    )

    print(
        f"Fiyat limiti: "
        f"{PRICE_LIMIT} TL"
    )

    print("=" * 60)

    token = get_amadeus_token()

    state = load_state()

    best_price = None
    best_date = None
    best_offer = None

    current_date = START_DATE

    while current_date <= END_DATE:

        print(
            f"[ARANIYOR] "
            f"{current_date.strftime('%d.%m.%Y')}"
        )

        try:

            offers = search_flights(
                token,
                current_date
            )

            result = find_cheapest_offer(
                offers
            )

            if result:

                price, offer = result

                print(
                    f"   En ucuz: "
                    f"{price:.2f} TL"
                )

                if (
                    best_price is None
                    or price < best_price
                ):

                    best_price = price
                    best_date = current_date
                    best_offer = offer

            else:

                print(
                    "   Uçuş bulunamadı."
                )

        except Exception as error:

            print(
                f"   Hata: {error}"
            )

        current_date += timedelta(
            days=1
        )

        # API çağrıları arasında bekle
        time.sleep(1)

    # -----------------------------------------------------
    # SONUÇ
    # -----------------------------------------------------

    if best_price is None:

        print()
        print(
            "❌ Hiç uçuş bulunamadı."
        )

        return

    print()
    print(
        f"💰 Eylül'deki en ucuz fiyat: "
        f"{best_price:.2f} TL"
    )

    print(
        f"📅 Tarih: "
        f"{best_date.strftime('%d.%m.%Y')}"
    )

    # -----------------------------------------------------
    # 5.000 TL KONTROLÜ
    # -----------------------------------------------------

    if best_price >= PRICE_LIMIT:

        print(
            "ℹ️ Fiyat 5.000 TL'nin altında değil."
        )

        return

    # -----------------------------------------------------
    # AYNI FİYATI TEKRAR GÖNDERME
    # -----------------------------------------------------

    price_key = (
        f"{best_date.isoformat()}_"
        f"{best_price:.2f}"
    )

    if price_key in state:

        print(
            "ℹ️ Bu fiyat daha önce Telegram'a "
            "gönderildi."
        )

        return

    # -----------------------------------------------------
    # TELEGRAM
    # -----------------------------------------------------

    message = create_message(
        best_date,
        best_price,
        best_offer
    )

    send_telegram(message)

    state[price_key] = {
        "date": best_date.isoformat(),
        "price": best_price
    }

    save_state(state)


# =========================================================
# ANA DÖNGÜ
# =========================================================

def main():

    print()
    print("🚀 Uçuş takip sistemi başladı.")
    print("📍 SAW → ERZ")
    print("📅 Eylül 2026")
    print("💰 Limit: 5.000 TL")
    print("⏱️ Kontrol: 10 dakikada bir")
    print()

    while True:

        try:

            scan_september()

        except Exception as error:

            print()
            print(
                f"❌ KRİTİK HATA: {error}"
            )

        print()
        print(
            "💤 10 dakika bekleniyor..."
        )

        time.sleep(
            CHECK_INTERVAL
        )


# =========================================================
# PROGRAMI BAŞLAT
# =========================================================

if __name__ == "__main__":
    main()

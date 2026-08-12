import os
import time
import json
from datetime import date, timedelta

import requests


# =========================================================
# AYARLAR
# =========================================================

ORIGIN = "SAW"          # Sabiha Gökçen
DESTINATION = "ERZ"     # Erzurum

PRICE_LIMIT = 5000      # 5.000 TL altı bildirim

START_DATE = date(2026, 9, 1)
END_DATE = date(2026, 9, 30)

CHECK_INTERVAL = 600     # 600 saniye = 10 dakika

AMADEUS_URL = "https://api.amadeus.com"

STATE_FILE = "sent_prices.json"


# =========================================================
# SECRET'LAR
# =========================================================

AMADEUS_CLIENT_ID = os.environ["AMADEUS_CLIENT_ID"]
AMADEUS_CLIENT_SECRET = os.environ["AMADEUS_CLIENT_SECRET"]

TELEGRAM_BOT_TOKEN = os.environ["8917847840:AAF9WhTKkQpzwdKFqsjJ0G37I_ocgmo5dlY"]
TELEGRAM_CHAT_ID = os.environ["1438895909"]


# =========================================================
# AMADEUS TOKEN
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
# UÇUŞ ARAMA
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
            f"[HATA] {departure_date} "
            f"{response.status_code}: "
            f"{response.text[:300]}"
        )

        return []

    return response.json().get("data", [])


# =========================================================
# EN UCUZ UÇUŞ
# =========================================================

def find_cheapest_offer(offers):

    cheapest = None

    for offer in offers:

        try:

            price = float(
                offer["price"]["grandTotal"]
            )

            if cheapest is None or price < cheapest[0]:

                cheapest = (
                    price,
                    offer
                )

        except (KeyError, TypeError, ValueError):

            continue

    return cheapest


# =========================================================
# TELEGRAM
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

    print("[OK] Telegram bildirimi gönderildi.")


# =========================================================
# BİLDİRİM GEÇMİŞİ
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
# UÇUŞ BİLGİLERİ
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

    itinerary = itineraries[0]

    segments = itinerary.get(
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

    first = segments[0]
    last = segments[-1]

    departure = first["departure"].get(
        "at",
        "?"
    )

    arrival = last["arrival"].get(
        "at",
        "?"
    )

    airlines = []

    for segment in segments:

        airline = segment.get(
            "carrierCode"
        )

        if airline and airline not in airlines:

            airlines.append(airline)

    stops = len(segments) - 1

    if stops == 0:

        stop_text = "Direkt"

    else:

        stop_text = f"{stops} aktarma"

    return {
        "departure": departure.replace("T", " "),
        "arrival": arrival.replace("T", " "),
        "airlines": ", ".join(airlines),
        "stops": stop_text
    }


# =========================================================
# MESAJ OLUŞTUR
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
        "🚨 UCUZ UÇAK BİLETİ BULUNDU!\n\n"

        "✈️ Rota: SAW → ERZ\n"

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

        "⚠️ Fiyat anlık olarak değişebilir."
    )


# =========================================================
# TÜM EYLÜLÜ TARA
# =========================================================

def scan_september():

    print()
    print("=" * 60)

    print(
        "SAW → ERZ UÇUŞ KONTROLÜ"
    )

    print(
        f"Tarih: {START_DATE} → {END_DATE}"
    )

    print(
        f"Limit: {PRICE_LIMIT} TL"
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
                    f"    En ucuz: "
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
                    "    Uçuş bulunamadı."
                )

        except Exception as error:

            print(
                f"    Hata: {error}"
            )

        current_date += timedelta(
            days=1
        )

        # API'yi arka arkaya zorlamamak için
        time.sleep(1)

    print()

    if best_price is None:

        print(
            "[SONUÇ] Uçuş bulunamadı."
        )

        return

    print(
        f"[SONUÇ] En ucuz: "
        f"{best_price:.2f} TL"
    )

    print(
        f"[SONUÇ] Tarih: "
        f"{best_date}"
    )

    # -----------------------------------------------------
    # FİYAT LİMİT ALTINDAYSA
    # -----------------------------------------------------

    if best_price >= PRICE_LIMIT:

        print(
            "[BİLDİRİM YOK] "
            "Fiyat limitin altında değil."
        )

        return

    # Aynı tarih + fiyat tekrar bildirilmesin
    price_key = (
        f"{best_date.isoformat()}_"
        f"{best_price:.2f}"
    )

    if price_key in state:

        print(
            "[BİLDİRİM YOK] "
            "Bu fiyat daha önce gönderildi."
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
    print("🚀 Uçuş takip sistemi başlatıldı.")
    print("⏱️ Kontrol aralığı: 10 dakika")
    print("🌙 Sistem 24 saat çalışacak.")
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


if __name__ == "__main__":

    main()

import os
import smtplib
import requests

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import date, timedelta


# =========================================================
# AYARLAR
# =========================================================

ORIGIN = "SAW"
DESTINATION = "ERZ"

PRICE_LIMIT = 5000

START_DATE = date(2026, 9, 1)
END_DATE = date(2026, 9, 30)

AMADEUS_URL = "https://api.amadeus.com"


# =========================================================
# GİZLİ BİLGİLER
# =========================================================

AMADEUS_CLIENT_ID = os.environ["AMADEUS_CLIENT_ID"]
AMADEUS_CLIENT_SECRET = os.environ["AMADEUS_CLIENT_SECRET"]

EMAIL_USERNAME = os.environ["EMAIL_USERNAME"]
EMAIL_PASSWORD = os.environ["EMAIL_PASSWORD"]
EMAIL_TO = os.environ["EMAIL_TO"]


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
            f"API HATASI: "
            f"{departure_date} "
            f"{response.status_code}"
        )

        print(response.text[:500])

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

        except (
            KeyError,
            TypeError,
            ValueError
        ):

            continue

    return cheapest


# =========================================================
# UÇUŞ DETAYLARI
# =========================================================

def get_flight_details(offer):

    itineraries = offer.get(
        "itineraries",
        []
    )

    if not itineraries:

        return "Bilgi yok"

    segments = itineraries[0].get(
        "segments",
        []
    )

    if not segments:

        return "Bilgi yok"

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

    return (
        f"Havayolu: {', '.join(airlines)}\n"
        f"Uçuş: {stop_text}\n"
        f"Kalkış: {departure.replace('T', ' ')}\n"
        f"Varış: {arrival.replace('T', ' ')}"
    )


# =========================================================
# E-POSTA GÖNDER
# =========================================================

def send_email(
    departure_date,
    price,
    offer
):

    details = get_flight_details(
        offer
    )

    subject = (
        f"✈️ Ucuz Bilet! "
        f"SAW → ERZ - "
        f"{price:,.0f} TL"
    )

    body = f"""
Ucuz uçak bileti bulundu!

✈️ Rota:
Sabiha Gökçen (SAW) → Erzurum (ERZ)

📅 Tarih:
{departure_date.strftime('%d.%m.%Y')}

💰 Fiyat:
{price:,.0f} TL

{details}

----------------------------

Fiyat 5.000 TL'nin altında bulundu.

⚠️ Uçuş fiyatı satın alma sırasında
değişebilir. Satın almadan önce
güncel fiyatı kontrol et.
"""

    message = MIMEMultipart()

    message["From"] = EMAIL_USERNAME
    message["To"] = EMAIL_TO
    message["Subject"] = subject

    message.attach(
        MIMEText(
            body,
            "plain",
            "utf-8"
        )
    )

    print("E-posta gönderiliyor...")

    with smtplib.SMTP_SSL(
        "smtp.gmail.com",
        465
    ) as server:

        server.login(
            EMAIL_USERNAME,
            EMAIL_PASSWORD
        )

        server.sendmail(
            EMAIL_USERNAME,
            EMAIL_TO,
            message.as_string()
        )

    print("✅ E-posta gönderildi!")


# =========================================================
# EYLÜLÜ TARA
# =========================================================

def scan_september():

    print("=" * 60)
    print("✈️ SAW → ERZ UÇUŞ KONTROLÜ")
    print("=" * 60)

    print(
        f"Tarih: "
        f"{START_DATE} - {END_DATE}"
    )

    print(
        f"Limit: "
        f"{PRICE_LIMIT} TL"
    )

    print("=" * 60)

    token = get_amadeus_token()

    best_price = None
    best_date = None
    best_offer = None

    current_date = START_DATE

    while current_date <= END_DATE:

        print(
            f"Kontrol ediliyor: "
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
                    f"En ucuz: "
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
                    "Uçuş bulunamadı."
                )

        except Exception as error:

            print(
                f"Hata: {error}"
            )

        current_date += timedelta(
            days=1
        )

    print()

    if best_price is None:

        print(
            "Hiç uçuş bulunamadı."
        )

        return

    print(
        f"Eylül ayındaki en ucuz: "
        f"{best_price:.2f} TL"
    )

    print(
        f"Tarih: "
        f"{best_date}"
    )

    # 5.000 TL altındaysa mail gönder
    if best_price < PRICE_LIMIT:

        send_email(
            best_date,
            best_price,
            best_offer
        )

    else:

        print(
            "Fiyat 5.000 TL altına inmedi."
        )


# =========================================================
# PROGRAM
# =========================================================

def main():

    print()
    print("🚀 Uçuş kontrolü başladı.")
    print()

    scan_september()

    print()
    print("✅ Kontrol tamamlandı.")


if __name__ == "__main__":
    main()

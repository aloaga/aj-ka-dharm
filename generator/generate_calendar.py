import os
import json
import calendar
from datetime import date, datetime, timedelta

import requests


# ============================================================
# AJ KA DHARM — MONTHLY CALENDAR DATA ENGINE
# ============================================================

API_URL = "https://api.navamsha.in/api/v1/panchang"

LATITUDE = 22.5726
LONGITUDE = 88.3639
TIMEZONE = 5.5
TIMEZONE_NAME = "Asia/Kolkata"

OUTPUT_FILE = "calendar_data.json"


# ============================================================
# HINDI NAMES
# ============================================================

WEEKDAYS_HI = {
    0: "सोमवार",
    1: "मंगलवार",
    2: "बुधवार",
    3: "गुरुवार",
    4: "शुक्रवार",
    5: "शनिवार",
    6: "रविवार",
}

MONTHS_HI = {
    1: "जनवरी",
    2: "फरवरी",
    3: "मार्च",
    4: "अप्रैल",
    5: "मई",
    6: "जून",
    7: "जुलाई",
    8: "अगस्त",
    9: "सितम्बर",
    10: "अक्टूबर",
    11: "नवम्बर",
    12: "दिसम्बर",
}

TITHI_HI = {
    "Pratipada": "प्रतिपदा",
    "Dwitiya": "द्वितीया",
    "Tritiya": "तृतीया",
    "Chaturthi": "चतुर्थी",
    "Panchami": "पंचमी",
    "Shashthi": "षष्ठी",
    "Saptami": "सप्तमी",
    "Ashtami": "अष्टमी",
    "Navami": "नवमी",
    "Dashami": "दशमी",
    "Ekadashi": "एकादशी",
    "Dwadashi": "द्वादशी",
    "Trayodashi": "त्रयोदशी",
    "Chaturdashi": "चतुर्दशी",
    "Purnima": "पूर्णिमा",
    "Amavasya": "अमावस्या",
}

PAKSHA_HI = {
    "Shukla": "शुक्ल",
    "Krishna": "कृष्ण",
}


# ============================================================
# BASIC TITHI-BASED FESTIVALS / VRATS
# ============================================================

def get_basic_festival(
    tithi_name,
    paksha_name,
):
    """
    Returns a basic festival/vrat label when it can be
    determined directly from the tithi and paksha.

    More complex festivals will be added later using
    year-specific rules.
    """

    # Ekadashi occurs twice in a lunar month.
    if tithi_name == "Ekadashi":
        return "एकादशी व्रत"

    # Purnima
    if tithi_name == "Purnima":
        return "पूर्णिमा व्रत"

    # Amavasya
    if tithi_name == "Amavasya":
        return "अमावस्या"

    # Pradosh is associated with Trayodashi.
    if tithi_name == "Trayodashi":
        return "प्रदोष व्रत"

    # Chaturthi is traditionally observed as a vrat.
    if tithi_name == "Chaturthi":
        if paksha_name == "Krishna":
            return "संकष्टी चतुर्थी"
        else:
            return "चतुर्थी व्रत"

    # Ashtami
    if tithi_name == "Ashtami":
        return "अष्टमी व्रत"

    # Chaturdashi
    if tithi_name == "Chaturdashi":
        if paksha_name == "Krishna":
            return "मासिक शिवरात्रि"
        else:
            return "चतुर्दशी व्रत"

    return ""


# ============================================================
# NAVAMSHA API HELPER
# ============================================================

def api_post(endpoint, payload, api_key):

    url = f"{API_URL}/{endpoint}"

    response = requests.post(
        url,
        headers={
            "X-API-Key": api_key,
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=30,
    )

    response.raise_for_status()

    data = response.json()

    if data.get("statusCode") != 200:
        raise RuntimeError(
            f"Navamsha API error: "
            f"{json.dumps(data, ensure_ascii=False)}"
        )

    return data["output"]


# ============================================================
# SUNRISE / SUNSET
# ============================================================

def get_sun_times(day, api_key):

    payload = {
        "year": day.year,
        "month": day.month,
        "date": day.day,
        "hours": 6,
        "minutes": 0,
        "latitude": LATITUDE,
        "longitude": LONGITUDE,
        "timezone": TIMEZONE,
    }

    return api_post(
        "sun-times",
        payload,
        api_key,
    )


# ============================================================
# MOONRISE / MOONSET
# ============================================================

def get_moon_times(day, api_key):

    payload = {
        "year": day.year,
        "month": day.month,
        "date": day.day,
        "hours": 6,
        "minutes": 0,
        "latitude": LATITUDE,
        "longitude": LONGITUDE,
        "timezone": TIMEZONE,
    }

    return api_post(
        "moon-times",
        payload,
        api_key,
    )


# ============================================================
# PANCHANG AT SUNRISE
# ============================================================

def get_panchang_at_sunrise(
    day,
    sunrise_local,
    api_key,
):

    sunrise_time = datetime.strptime(
        sunrise_local,
        "%H:%M",
    )

    check_time = sunrise_time + timedelta(
        minutes=1
    )

    payload = {
        "year": day.year,
        "month": day.month,
        "date": day.day,
        "hours": check_time.hour,
        "minutes": check_time.minute,
        "latitude": LATITUDE,
        "longitude": LONGITUDE,
        "timezone": TIMEZONE,
    }

    return api_post(
        "full",
        payload,
        api_key,
    )


# ============================================================
# FORMAT TIME
# ============================================================

def extract_time(value):

    if not value:
        return ""

    value = str(value)

    if "T" in value:
        return value.split("T")[1][:5]

    return value[:5]


# ============================================================
# BUILD ONE CALENDAR DAY
# ============================================================

def build_day(day, api_key):

    print(
        f"  Fetching {day.isoformat()}..."
    )

    # --------------------------------------------------------
    # Sun
    # --------------------------------------------------------

    sun = get_sun_times(
        day,
        api_key,
    )

    sunrise = extract_time(
        sun["rise"]["local_datetime"]
    )

    sunset = extract_time(
        sun["set"]["local_datetime"]
    )

    # --------------------------------------------------------
    # Panchang
    # --------------------------------------------------------

    panchang = get_panchang_at_sunrise(
        day,
        sunrise,
        api_key,
    )

    tithi = panchang["tithi"]

    tithi_name = tithi.get(
        "name",
        "",
    )

    paksha_name = tithi.get(
        "paksha",
        "",
    )

    # --------------------------------------------------------
    # Moon
    # --------------------------------------------------------

    moon = get_moon_times(
        day,
        api_key,
    )

    moonrise = ""

    moonset = ""

    if moon.get("rise"):

        moonrise = extract_time(
            moon["rise"].get(
                "local_datetime"
            )
        )

    if moon.get("set"):

        moonset = extract_time(
            moon["set"].get(
                "local_datetime"
            )
        )

    # --------------------------------------------------------
    # Festival / vrat
    # --------------------------------------------------------

    festival = get_basic_festival(
        tithi_name,
        paksha_name,
    )

    # --------------------------------------------------------
    # Final record
    # --------------------------------------------------------

    return {

        "date": day.isoformat(),

        "day": day.day,

        "weekday": WEEKDAYS_HI[
            day.weekday()
        ],

        "month": day.month,

        "year": day.year,

        "tithi": TITHI_HI.get(
            tithi_name,
            tithi_name,
        ),

        "paksha": PAKSHA_HI.get(
            paksha_name,
            paksha_name,
        ),

        "sunrise": sunrise,

        "sunset": sunset,

        "moonrise": moonrise,

        "moonset": moonset,

        "festival": festival,
    }


# ============================================================
# MAIN
# ============================================================

def main():

    api_key = os.environ.get(
        "NAVAMSHA_API_KEY"
    )

    if not api_key:

        raise RuntimeError(
            "NAVAMSHA_API_KEY GitHub secret "
            "was not found."
        )

    today = datetime.now().date()

    year = today.year

    month = today.month

    days_in_month = calendar.monthrange(
        year,
        month,
    )[1]

    print()

    print(
        "========================================"
    )

    print(
        "AJ KA DHARM — CALENDAR DATA"
    )

    print(
        "========================================"
    )

    print(
        f"Month: {MONTHS_HI[month]} {year}"
    )

    print(
        "Location: Kolkata"
    )

    print(
        f"Days: {days_in_month}"
    )

    print()

    days = []

    for day_number in range(
        1,
        days_in_month + 1,
    ):

        day = date(
            year,
            month,
            day_number,
        )

        days.append(
            build_day(
                day,
                api_key,
            )
        )

    calendar_data = {

        "year": year,

        "month": month,

        "month_hindi": MONTHS_HI[
            month
        ],

        "timezone": TIMEZONE_NAME,

        "location": {

            "city": "Kolkata",

            "latitude": LATITUDE,

            "longitude": LONGITUDE,
        },

        "days": days,
    }

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            calendar_data,
            file,
            ensure_ascii=False,
            indent=2,
        )

    print()

    print(
        "========================================"
    )

    print(
        "CALENDAR DATA CREATED"
    )

    print(
        "========================================"
    )

    print(
        f"Output: {OUTPUT_FILE}"
    )

    print(
        f"Days generated: {len(days)}"
    )

    print()

    # --------------------------------------------------------
    # Show festival results
    # --------------------------------------------------------

    print(
        "Festival / vrat dates:"
    )

    for item in days:

        if item["festival"]:

            print(
                f"{item['date']} | "
                f"{item['paksha']} "
                f"{item['tithi']} | "
                f"{item['festival']}"
            )

    print()

    print(
        "Calendar data generated successfully."
    )


if __name__ == "__main__":

    main()

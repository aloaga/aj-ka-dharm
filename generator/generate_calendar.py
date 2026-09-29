import os
import json
import calendar
from datetime import date, datetime, timedelta

import requests


# ============================================================
# AJ KA DHARM — MONTHLY CALENDAR DATA ENGINE
# LOCATION: KOLKATA
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
# KOLKATA — SEPTEMBER 2026 FESTIVAL DATA
#
# Verified against the Kolkata September 2026 Panchang.
#
# These are major observances suitable for the small calendar
# cells. Generic tithi-based vrats are handled separately.
# ============================================================

FESTIVALS_2026 = {

    "2026-09-02": "हल षष्ठी",

    "2026-09-04": "जन्माष्टमी",

    "2026-09-05": "दही हांडी",

    "2026-09-07": "अजा एकादशी",

    "2026-09-08": "भौम प्रदोष",

    "2026-09-10": "पिठोरी अमावस्या",

    "2026-09-11": "भाद्रपद अमावस्या",

    "2026-09-12": "चन्द्र दर्शन",

    "2026-09-13": "वराह जयंती",

    "2026-09-14": "गणेश चतुर्थी",

    "2026-09-15": "ऋषि पंचमी",

    "2026-09-17": "विश्वकर्मा पूजा",

    "2026-09-18": "दूर्वा अष्टमी",

    "2026-09-19": "राधा अष्टमी",

    "2026-09-22": "पार्श्व एकादशी",

    "2026-09-23": "वामन जयंती",

    "2026-09-24": "गुरु प्रदोष",

    "2026-09-25": "अनंत चतुर्दशी",

    "2026-09-26": "भाद्रपद पूर्णिमा",

    "2026-09-27": "पितृपक्ष प्रारम्भ",

    "2026-09-29": "विघ्नराज संकष्टी",
}


# ============================================================
# GENERIC TITHI-BASED OBSERVANCES
# ============================================================

def get_basic_festival(
    day,
    tithi_name,
    paksha_name,
):
    """
    Provides a generic observance only when there is no
    named festival for that date.

    Named festival data always takes priority.
    """

    date_key = day.isoformat()

    # A named festival already exists.
    if date_key in FESTIVALS_2026:
        return FESTIVALS_2026[date_key]

    if tithi_name == "Ekadashi":
        return "एकादशी व्रत"

    if tithi_name == "Purnima":
        return "पूर्णिमा व्रत"

    if tithi_name == "Amavasya":
        return "अमावस्या"

    if tithi_name == "Trayodashi":
        return "प्रदोष व्रत"

    if tithi_name == "Chaturthi":

        if paksha_name == "Krishna":
            return "संकष्टी चतुर्थी"

        return "चतुर्थी व्रत"

    if tithi_name == "Chaturdashi":

        if paksha_name == "Krishna":
            return "मासिक शिवरात्रि"

        return "चतुर्दशी व्रत"

    return ""


# ============================================================
# NAVAMSHA API
# ============================================================

def api_post(
    endpoint,
    payload,
    api_key,
):
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
            "Navamsha API error: "
            + json.dumps(
                data,
                ensure_ascii=False,
            )
        )

    return data["output"]


# ============================================================
# SUN TIMES
# ============================================================

def get_sun_times(
    day,
    api_key,
):
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
# MOON TIMES
# ============================================================

def get_moon_times(
    day,
    api_key,
):
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
# TIME FORMATTER
# ============================================================

def extract_time(value):

    if not value:
        return ""

    value = str(value)

    if "T" in value:
        return value.split("T")[1][:5]

    return value[:5]


# ============================================================
# ONE DAY
# ============================================================

def build_day(
    day,
    api_key,
):
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
    # Festival
    # --------------------------------------------------------

    festival = get_basic_festival(
        day,
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

    # --------------------------------------------------------
    # Calendar data
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # Save JSON
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # Print festival report
    # --------------------------------------------------------

    print()
    print(
        "========================================"
    )
    print(
        "FESTIVAL / VRAT REPORT"
    )
    print(
        "========================================"
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

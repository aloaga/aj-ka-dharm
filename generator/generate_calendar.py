import os
import json
import calendar
from datetime import date, datetime, timedelta

import requests


# ============================================================
# AJ KA DHARM — MONTHLY CALENDAR DATA ENGINE
# STEP 3: Panchang data only
# ============================================================

API_URL = "https://api.navamsha.in/api/v1/panchang"

LATITUDE = 22.5726
LONGITUDE = 88.3639
TIMEZONE = 5.5
TIMEZONE_NAME = "Asia/Kolkata"

OUTPUT_FILE = "calendar_data.json"


# ------------------------------------------------------------
# Hindi names
# ------------------------------------------------------------

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


# ------------------------------------------------------------
# API helper
# ------------------------------------------------------------

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
            f"Navamsha API error: {json.dumps(data, ensure_ascii=False)}"
        )

    return data["output"]


# ------------------------------------------------------------
# Sunrise
# ------------------------------------------------------------

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

    return api_post("sun-times", payload, api_key)


# ------------------------------------------------------------
# Panchang at sunrise
# ------------------------------------------------------------

def get_panchang_at_sunrise(day, sunrise_local, api_key):
    sunrise_time = datetime.strptime(sunrise_local, "%H:%M")

    # Ask for Panchang one minute after sunrise.
    # This keeps the calendar aligned with the sunrise-based
    # Panchang convention.
    check_time = sunrise_time + timedelta(minutes=1)

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

    return api_post("full", payload, api_key)


# ------------------------------------------------------------
# One calendar date
# ------------------------------------------------------------

def build_day(day, api_key):
    sun = get_sun_times(day, api_key)

    sunrise = sun["rise"]["local_datetime"][11:16]
    sunset = sun["set"]["local_datetime"][11:16]

    panchang = get_panchang_at_sunrise(
        day,
        sunrise,
        api_key,
    )

    tithi = panchang["tithi"]

    tithi_name = tithi.get("name", "")
    paksha_name = tithi.get("paksha", "")

    return {
        "date": day.isoformat(),
        "day": day.day,
        "weekday": WEEKDAYS_HI[day.weekday()],
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

        # Festival will be added in the next step.
        "festival": "",
    }


# ------------------------------------------------------------
# Main
# ------------------------------------------------------------

def main():
    api_key = os.environ.get("NAVAMSHA_API_KEY")

    if not api_key:
        raise RuntimeError(
            "NAVAMSHA_API_KEY GitHub secret was not found."
        )

    today = datetime.now().date()

    year = today.year
    month = today.month

    days_in_month = calendar.monthrange(
        year,
        month,
    )[1]

    print(
        f"Generating calendar data for "
        f"{MONTHS_HI[month]} {year}..."
    )

    days = []

    for day_number in range(1, days_in_month + 1):
        day = date(
            year,
            month,
            day_number,
        )

        print(
            f"  {day.isoformat()}..."
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
        "month_hindi": MONTHS_HI[month],
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
        f"Created {OUTPUT_FILE}"
    )
    print(
        f"Days generated: {len(days)}"
    )


if __name__ == "__main__":
    main()

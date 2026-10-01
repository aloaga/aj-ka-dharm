import os
import json
import calendar
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import requests


# ============================================================
# AJ KA DHARM — MONTHLY CALENDAR DATA ENGINE
# ============================================================
# Panchang source : Navamsha
# Festival source : TathaAstu
# Festival style  : North Indian / Hindi
# Location        : Kolkata
# ============================================================


# ============================================================
# NAVAMSHA API
# ============================================================

NAVAMSHA_API_URL = (
    "https://api.navamsha.in/api/v1/panchang"
)


# ============================================================
# TATHAASTU FESTIVAL API
# ============================================================

TATHAASTU_FESTIVAL_URL = (
    "https://api.tathaastuapi.com/v1/festivals/month"
)

TATHAASTU_REGION = "NORTH_INDIA"


# ============================================================
# LOCATION
# ============================================================

LATITUDE = 22.5726
LONGITUDE = 88.3639

TIMEZONE = 5.5
TIMEZONE_NAME = "Asia/Kolkata"


# ============================================================
# OUTPUT
# ============================================================

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
# GENERIC TITHI-BASED OBSERVANCES
# ============================================================

def get_basic_festival(
    tithi_name,
    paksha_name,
):
    """
    Fallback observance used only when TathaAstu does not
    provide a named festival for that date.
    """

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
# TATHAASTU FESTIVAL DATA
# ============================================================

def get_tathaastu_festivals(
    year,
    month,
    api_key,
):
    """
    Fetch the complete festival/vrat list for one month.

    TathaAstu calculates festival dates using its festival
    rule engine. We do not maintain annual festival tables.
    """

    print()
    print(
        "Fetching festival data from TathaAstu..."
    )

    params = {
        "year": year,
        "month": month,
        "region": TATHAASTU_REGION,
        "lang": "hi",
    }

    response = requests.get(
        TATHAASTU_FESTIVAL_URL,
        headers={
            "X-API-Key": api_key,
        },
        params=params,
        timeout=30,
    )

    response.raise_for_status()

    data = response.json()

    festivals = data.get(
        "festivals"
    )

    if not isinstance(
        festivals,
        list,
    ):
        raise RuntimeError(
            "TathaAstu API response did not contain "
            "a valid 'festivals' list."
        )

    print(
        f"TathaAstu returned "
        f"{len(festivals)} festival/vrat entries."
    )

    # --------------------------------------------------------
    # Group festivals by observation date.
    # --------------------------------------------------------

    festivals_by_date = {}

    for item in festivals:

        festival_date = (
            item.get("observation_date")
            or item.get("date")
        )

        if not festival_date:
            continue

        festival_name = (
            item.get("display_name_local")
            or item.get("name_local")
            or item.get("display_name")
            or item.get("name")
            or ""
        )

        festival_name = str(
            festival_name
        ).strip()

        if not festival_name:
            continue

        entry = {
            "name": festival_name,
            "primary": bool(
                item.get("primary", False)
            ),
            "priority": item.get(
                "priority",
                0,
            ),
            "confidence": item.get(
                "confidence",
                0,
            ),
            "festival_key": item.get(
                "festival_key",
                "",
            ),
        }

        festivals_by_date.setdefault(
            festival_date,
            [],
        ).append(entry)

    return festivals_by_date


# ============================================================
# SELECT FESTIVAL FOR CALENDAR CELL
# ============================================================

def choose_festival_for_date(
    day,
    festivals_by_date,
    tithi_name,
    paksha_name,
):
    """
    Select the most important festival for the small
    calendar cell.

    When multiple observances fall on the same date,
    prefer:

      1. primary festival
      2. higher priority
      3. higher confidence

    This keeps the visual design clean without losing
    the full festival calculation behind the scenes.
    """

    date_key = day.isoformat()

    entries = festivals_by_date.get(
        date_key,
        [],
    )

    if entries:

        entries = sorted(
            entries,
            key=lambda item: (
                item["primary"],
                item["priority"],
                item["confidence"],
            ),
            reverse=True,
        )

        return entries[0]["name"]

    # --------------------------------------------------------
    # No named festival from TathaAstu.
    #
    # Keep our existing generic fallback so that important
    # recurring tithi observances still appear.
    # --------------------------------------------------------

    return get_basic_festival(
        tithi_name,
        paksha_name,
    )


# ============================================================
# NAVAMSHA API
# ============================================================

def api_post(
    endpoint,
    payload,
    api_key,
):
    url = (
        f"{NAVAMSHA_API_URL}/{endpoint}"
    )

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

    check_time = (
        sunrise_time
        + timedelta(minutes=1)
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
    festivals_by_date,
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

    panchang = (
        get_panchang_at_sunrise(
            day,
            sunrise,
            api_key,
        )
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

    festival = (
        choose_festival_for_date(
            day,
            festivals_by_date,
            tithi_name,
            paksha_name,
        )
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

    # --------------------------------------------------------
    # API keys
    # --------------------------------------------------------

    navamsha_api_key = os.environ.get(
        "NAVAMSHA_API_KEY"
    )

    if not navamsha_api_key:

        raise RuntimeError(
            "NAVAMSHA_API_KEY GitHub secret "
            "was not found."
        )

    tathaastu_api_key = os.environ.get(
        "TATHAASTU_API_KEY"
    )

    if not tathaastu_api_key:

        raise RuntimeError(
            "TATHAASTU_API_KEY GitHub secret "
            "was not found."
        )

    # --------------------------------------------------------
    # Kolkata current date/time
    # --------------------------------------------------------

    kolkata_now = datetime.now(
        ZoneInfo(TIMEZONE_NAME)
    )

    today = kolkata_now.date()

    # --------------------------------------------------------
    # IMPORTANT:
    # Generate TOMORROW'S calendar.
    # --------------------------------------------------------

    target_date = (
        today
        + timedelta(days=1)
    )

    year = target_date.year
    month = target_date.month

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
        f"Kolkata date: {today.isoformat()}"
    )

    print(
        f"Target date: {target_date.isoformat()}"
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

    print(
        f"Festival rules: {TATHAASTU_REGION}"
    )

    print()

    # --------------------------------------------------------
    # Fetch festival data ONCE for the entire month.
    #
    # This is important because we don't want to make a
    # separate festival API request for every day.
    # --------------------------------------------------------

    festivals_by_date = (
        get_tathaastu_festivals(
            year,
            month,
            tathaastu_api_key,
        )
    )

    print(
        f"Festival dates received: "
        f"{len(festivals_by_date)}"
    )

    print()

    # --------------------------------------------------------
    # Build every day of the target month.
    # --------------------------------------------------------

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
                navamsha_api_key,
                festivals_by_date,
            )
        )

    # --------------------------------------------------------
    # Calendar data
    # --------------------------------------------------------

    calendar_data = {

        "year": year,

        "month": month,

        "target_date": (
            target_date.isoformat()
        ),

        "month_hindi": MONTHS_HI[
            month
        ],

        "timezone": TIMEZONE_NAME,

        "location": {
            "city": "Kolkata",
            "latitude": LATITUDE,
            "longitude": LONGITUDE,
        },

        "festival_source": {
            "provider": "TathaAstu",
            "region": TATHAASTU_REGION,
            "language": "hi",
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
    # Festival / Vrat report
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


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()

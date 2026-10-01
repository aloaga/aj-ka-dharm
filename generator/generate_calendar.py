import os
import json
import calendar
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import requests


# ============================================================
# AJ KA DHARM — MONTHLY CALENDAR DATA ENGINE
# ============================================================
#
# Panchang source : TathaAstu
# Festival source : TathaAstu
# Astronomical     : Navamsha
# Festival style   : North Indian / Hindi
# Location         : Kolkata
#
# IMPORTANT:
# Tithi, Paksha, Hindu lunar month and Vikram Samvat are
# dynamically obtained from TathaAstu.
#
# There are NO annual Hindu-month or Tithi lookup tables.
# ============================================================


# ============================================================
# TATHAASTU PANCHANG API
# ============================================================

TATHAASTU_PANCHANG_URL = (
    "https://api.tathaastuapi.com/v1/panchang"
)


# ============================================================
# TATHAASTU FESTIVAL API
# ============================================================

TATHAASTU_FESTIVAL_URL = (
    "https://api.tathaastuapi.com/v1/festivals/month"
)

TATHAASTU_REGION = "NORTH_INDIA"


# ============================================================
# NAVAMSHA API
# ============================================================

NAVAMSHA_API_URL = (
    "https://api.navamsha.in/api/v1/panchang"
)


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
# GREGORIAN MONTH NAMES
#
# These are only used for the GitHub Actions log.
# They are NOT used for the Hindu calendar header.
# ============================================================

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


# ============================================================
# WEEKDAYS
#
# These are calendar UI labels and are not Hindu-calendar
# calculations.
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

    This is NOT a calendar calculation table.
    It is only a generic visual fallback for recurring
    tithi observances.
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

    TathaAstu calculates festival dates using its rule engine.
    We do not maintain annual festival tables.
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
                item.get(
                    "primary",
                    False,
                )
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
    the festival calculation behind the scenes.
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
    # Keep generic recurring tithi observances visible.
    # --------------------------------------------------------

    return get_basic_festival(
        tithi_name,
        paksha_name,
    )


# ============================================================
# TATHAASTU PANCHANG
# ============================================================

def get_tathaastu_panchang(
    day,
    api_key,
):
    """
    Get the perpetual Panchang data from TathaAstu.

    This is now the authoritative source for:

      - Tithi
      - Paksha
      - Hindi Tithi name
      - Hindu lunar month
      - Vikram Samvat

    We explicitly provide Kolkata coordinates and timezone so
    the calculation is tied to the same location used by the
    rest of this project.
    """

    params = {
        "date": day.isoformat(),
        "lat": LATITUDE,
        "lon": LONGITUDE,
        "tz": TIMEZONE_NAME,
        "lang": "hi",
    }

    response = requests.get(
        TATHAASTU_PANCHANG_URL,
        headers={
            "X-API-Key": api_key,
        },
        params=params,
        timeout=30,
    )

    response.raise_for_status()

    data = response.json()

    if not isinstance(
        data,
        dict,
    ):
        raise RuntimeError(
            "TathaAstu Panchang response was not a JSON object."
        )

    if "tithi" not in data:
        raise RuntimeError(
            "TathaAstu Panchang response did not contain "
            "the expected 'tithi' section."
        )

    if "hindu_calendar" not in data:
        raise RuntimeError(
            "TathaAstu Panchang response did not contain "
            "the expected 'hindu_calendar' section."
        )

    return data


# ============================================================
# EXTRACT HINDI FIELD
# ============================================================

def get_hindi_field(
    obj,
    base_name,
):
    """
    TathaAstu uses companion *_hi fields for Hindi.

    Example:

        name      -> English/canonical value
        name_hi   -> Hindi display value

    Return an empty string if the companion is unavailable.
    """

    if not isinstance(
        obj,
        dict,
    ):
        return ""

    value = obj.get(
        f"{base_name}_hi"
    )

    if value is None:
        return ""

    return str(
        value
    ).strip()


# ============================================================
# HINDU MONTH NAME EXTRACTION
# ============================================================

def get_hindu_month_name_hi(
    hindu_calendar,
    month_type,
):
    """
    Extract a Hindi lunar month name from TathaAstu.

    TathaAstu documentation exposes Hindu lunar calendar
    identity and localized companion fields.

    We support both naming forms that may occur between
    endpoint versions:

        purnimanta_month_hi
        purnimanta_hi

    and:

        amanta_month_hi
        amanta_hi
    """

    if not isinstance(
        hindu_calendar,
        dict,
    ):
        return ""

    if month_type == "purnimanta":

        candidates = [
            "purnimanta_month_hi",
            "purnimanta_hi",
        ]

    else:

        candidates = [
            "amanta_month_hi",
            "amanta_hi",
        ]

    for key in candidates:

        value = hindu_calendar.get(
            key
        )

        if value:
            return str(
                value
            ).strip()

    return ""


# ============================================================
# NAVAMSHA API POST
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

    if data.get(
        "statusCode"
    ) != 200:

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
# TIME FORMATTER
# ============================================================

def extract_time(value):

    if not value:
        return ""

    value = str(
        value
    )

    if "T" in value:
        return value.split(
            "T"
        )[1][:5]

    return value[:5]


# ============================================================
# ONE DAY
# ============================================================

def build_day(
    day,
    navamsha_api_key,
    tathaastu_api_key,
    festivals_by_date,
):
    print(
        f"  Fetching {day.isoformat()}..."
    )

    # ========================================================
    # TATHAASTU PANCHANG
    #
    # This is now the source for:
    #   - Tithi
    #   - Paksha
    #   - Hindi Tithi
    #   - Hindu month
    #   - Vikram Samvat
    # ========================================================

    tathaastu_panchang = (
        get_tathaastu_panchang(
            day,
            tathaastu_api_key,
        )
    )

    tithi = tathaastu_panchang.get(
        "tithi",
        {},
    )

    hindu_calendar = (
        tathaastu_panchang.get(
            "hindu_calendar",
            {},
        )
    )

    tithi_name = tithi.get(
        "name",
        "",
    )

    paksha_name = tithi.get(
        "paksha",
        "",
    )

    # --------------------------------------------------------
    # Hindi Tithi
    #
    # Normally TathaAstu provides:
    #
    #   tithi.name_hi
    #
    # We do not maintain our own translation table.
    # --------------------------------------------------------

    tithi_name_hi = get_hindi_field(
        tithi,
        "name",
    )

    if not tithi_name_hi:

        full_name_hi = get_hindi_field(
            tithi,
            "full_name",
        )

        if full_name_hi:

            # Example:
            # "शुक्ल पक्ष चतुर्दशी"
            #
            # The final word is the actual Tithi name.
            pieces = full_name_hi.split()

            if pieces:
                tithi_name_hi = pieces[-1]

    if not tithi_name_hi:
        raise RuntimeError(
            "TathaAstu did not provide a Hindi Tithi name "
            f"for {day.isoformat()}."
        )

    # --------------------------------------------------------
    # Hindi Paksha
    # --------------------------------------------------------

    paksha_name_hi = get_hindi_field(
        tithi,
        "paksha",
    )

    # --------------------------------------------------------
    # Hindu lunar month
    # --------------------------------------------------------

    purnimanta_month_hi = (
        get_hindu_month_name_hi(
            hindu_calendar,
            "purnimanta",
        )
    )

    amanta_month_hi = (
        get_hindu_month_name_hi(
            hindu_calendar,
            "amanta",
        )
    )

    # --------------------------------------------------------
    # Vikram Samvat
    #
    # This number is supplied by TathaAstu.
    # We do NOT calculate it from Gregorian year.
    # --------------------------------------------------------

    samvat = hindu_calendar.get(
        "samvat"
    )

    if samvat is None:
        raise RuntimeError(
            "TathaAstu did not provide Vikram Samvat "
            f"for {day.isoformat()}."
        )

    # ========================================================
    # SUN
    #
    # Kept on Navamsha so the existing astronomical timing
    # behavior remains unchanged.
    # ========================================================

    sun = get_sun_times(
        day,
        navamsha_api_key,
    )

    sunrise = extract_time(
        sun["rise"]["local_datetime"]
    )

    sunset = extract_time(
        sun["set"]["local_datetime"]
    )

    # ========================================================
    # MOON
    #
    # Kept on Navamsha.
    # ========================================================

    moon = get_moon_times(
        day,
        navamsha_api_key,
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

    # ========================================================
    # FESTIVAL
    # ========================================================

    festival = (
        choose_festival_for_date(
            day,
            festivals_by_date,
            tithi_name,
            paksha_name,
        )
    )

    # ========================================================
    # FINAL DAY RECORD
    # ========================================================

    return {

        "date": day.isoformat(),

        "day": day.day,

        "weekday": WEEKDAYS_HI[
            day.weekday()
        ],

        "month": day.month,

        "year": day.year,

        # ----------------------------------------------------
        # Dynamic Hindu calendar values
        # ----------------------------------------------------

        "tithi": tithi_name_hi,

        "tithi_key": tithi_name,

        "paksha": (
            paksha_name_hi
            or paksha_name
        ),

        "paksha_key": paksha_name,

        "hindu_month_purnimanta": (
            purnimanta_month_hi
        ),

        "hindu_month_amanta": (
            amanta_month_hi
        ),

        "vikram_samvat": int(
            samvat
        ),

        # ----------------------------------------------------
        # Astronomical timings
        # ----------------------------------------------------

        "sunrise": sunrise,

        "sunset": sunset,

        "moonrise": moonrise,

        "moonset": moonset,

        # ----------------------------------------------------
        # Festival
        # ----------------------------------------------------

        "festival": festival,
    }


# ============================================================
# BUILD HEADER HINDU MONTH LABEL
# ============================================================

def build_hindu_month_header(
    days,
):
    """
    Build the header dynamically from the Hindu month values
    returned by TathaAstu.

    We use the Purnimanta month because this is the North Indian
    convention used for the calendar header.

    If the Gregorian month crosses a Hindu lunar-month boundary,
    both month names are shown:

        आश्विन — कार्तिक

    If it stays within one lunar month, only one name appears.
    """

    names = []

    for item in days:

        name = item.get(
            "hindu_month_purnimanta",
            "",
        )

        if name and name not in names:
            names.append(name)

    if names:
        return " — ".join(names)

    

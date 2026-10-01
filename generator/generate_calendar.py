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
# Tithi, Paksha, Hindu lunar month and Vikram Samvat
# are dynamically obtained from TathaAstu.
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
# TATHAASTU FALLBACK CALENDAR APIs
# ============================================================

TATHAASTU_HINDU_MONTH_URL = (
    "https://api.tathaastuapi.com/v1/hindu-month"
)

TATHAASTU_SAMVATSARA_URL = (
    "https://api.tathaastuapi.com/v1/samvatsara"
)


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

    This is NOT an annual calendar table.
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

    # --------------------------------------------------------
    # Be tolerant if the API wraps the payload in "data".
    # --------------------------------------------------------

    if (
        isinstance(data, dict)
        and isinstance(data.get("data"), dict)
        and "festivals" not in data
    ):
        data = data["data"]

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

    Priority:
      1. primary
      2. higher priority
      3. higher confidence
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
    Get perpetual Panchang data from TathaAstu.
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
            "TathaAstu Panchang response was not "
            "a JSON object."
        )

    # --------------------------------------------------------
    # Some API responses may be wrapped in "data".
    # --------------------------------------------------------

    if (
        isinstance(data.get("data"), dict)
        and "tithi" not in data
    ):
        data = data["data"]

    if "tithi" not in data:

        raise RuntimeError(
            "TathaAstu Panchang response did not contain "
            "the expected 'tithi' section. "
            f"Top-level keys: {sorted(data.keys())}"
        )

    if "hindu_calendar" not in data:

        raise RuntimeError(
            "TathaAstu Panchang response did not contain "
            "the expected 'hindu_calendar' section. "
            f"Top-level keys: {sorted(data.keys())}"
        )

    return data


# ============================================================
# GENERIC NESTED VALUE SEARCH
# ============================================================

def find_nested_value(
    obj,
    candidate_keys,
):
    """
    Recursively search a JSON object for one of the supplied
    keys.

    This is deliberately used only for compatibility with
    harmless API response-shape changes.
    """

    if isinstance(
        obj,
        dict,
    ):

        for key in candidate_keys:

            if key in obj:

                value = obj[key]

                if value not in (
                    None,
                    "",
                ):

                    return value

        for value in obj.values():

            result = find_nested_value(
                value,
                candidate_keys,
            )

            if result not in (
                None,
                "",
            ):

                return result

    elif isinstance(
        obj,
        list,
    ):

        for item in obj:

            result = find_nested_value(
                item,
                candidate_keys,
            )

            if result not in (
                None,
                "",
            ):

                return result

    return None


# ============================================================
# LOCALIZED FIELD
# ============================================================

def get_localized_field(
    obj,
    base_name,
):
    """
    TathaAstu localization uses <field>_local when lang=hi
    is requested.
    """

    if not isinstance(
        obj,
        dict,
    ):
        return ""

    candidates = [
        f"{base_name}_local",
        f"{base_name}_hi",
    ]

    for key in candidates:

        value = obj.get(
            key
        )

        if value not in (
            None,
            "",
        ):

            return str(
                value
            ).strip()

    return ""


# ============================================================
# HINDU MONTH NAME EXTRACTION
# ============================================================

def get_hindu_month_name_hi(
    hindu_calendar,
    month_type,
):
    """
    Extract the Hindi lunar month name.

    TathaAstu's current contract uses canonical fields:

        purnimanta
        amanta

    and localized values:

        purnimanta_local
        amanta_local

    Compatibility field names are also accepted.
    """

    if not isinstance(
        hindu_calendar,
        dict,
    ):
        return ""

    if month_type == "purnimanta":

        candidates = [
            "purnimanta_local",
            "purnimanta_month_local",
            "purnimanta_hi",
            "purnimanta_month_hi",
        ]

    else:

        candidates = [
            "amanta_local",
            "amanta_month_local",
            "amanta_hi",
            "amanta_month_hi",
        ]

    for key in candidates:

        value = hindu_calendar.get(
            key
        )

        if value not in (
            None,
            "",
        ):

            return str(
                value
            ).strip()

    # --------------------------------------------------------
    # Last compatibility possibility:
    #
    # Some older responses may use a nested object.
    # --------------------------------------------------------

    nested = find_nested_value(
        hindu_calendar,
        candidates,
    )

    if nested not in (
        None,
        "",
    ):

        return str(
            nested
        ).strip()

    return ""


# ============================================================
# TATHAASTU HINDU MONTH FALLBACK
# ============================================================

def get_tathaastu_hindu_month(
    day,
    api_key,
):
    """
    Fallback to TathaAstu's dedicated Hindu-month endpoint
    if the normal Panchang response does not contain a
    localized month name.
    """

    params = {
        "date": day.isoformat(),
        "lat": LATITUDE,
        "lon": LONGITUDE,
        "lang": "hi",
        "region": TATHAASTU_REGION,
    }

    response = requests.get(
        TATHAASTU_HINDU_MONTH_URL,
        headers={
            "X-API-Key": api_key,
        },
        params=params,
        timeout=30,
    )

    response.raise_for_status()

    data = response.json()

    if (
        isinstance(data, dict)
        and isinstance(data.get("data"), dict)
    ):
        data = data["data"]

    if not isinstance(
        data,
        dict,
    ):
        raise RuntimeError(
            "TathaAstu Hindu-month response was not "
            "a JSON object."
        )

    return data


# ============================================================
# TATHAASTU SAMVATSARA FALLBACK
# ============================================================

def get_tathaastu_samvatsara(
    day,
    api_key,
):
    """
    Fallback to TathaAstu's dedicated Samvatsara endpoint.

    We search only for fields whose names explicitly identify
    Samvat, avoiding any calculation from the Gregorian year.
    """

    print(
        f"    Fetching Samvat fallback for "
        f"{day.isoformat()}..."
    )

    params = {
        "date": day.isoformat(),
        "lat": LATITUDE,
        "lon": LONGITUDE,
        "region": TATHAASTU_REGION,
    }

    response = requests.get(
        TATHAASTU_SAMVATSARA_URL,
        headers={
            "X-API-Key": api_key,
        },
        params=params,
        timeout=30,
    )

    response.raise_for_status()

    data = response.json()

    if (
        isinstance(data, dict)
        and isinstance(data.get("data"), dict)
    ):
        data = data["data"]

    if not isinstance(
        data,
        dict,
    ):
        raise RuntimeError(
            "TathaAstu Samvatsara response was not "
            "a JSON object."
        )

    value = find_nested_value(
        data,
        [
            "vikram_samvat",
            "vikrama_samvat",
            "samvat",
            "vikramSamvat",
            "vikramaSamvat",
        ],
    )

    if value is None:

        raise RuntimeError(
            "TathaAstu did not provide Vikram Samvat "
            f"for {day.isoformat()}. "
            f"Samvatsara response keys: "
            f"{sorted(data.keys())}"
        )

    try:

        return int(
            value
        )

    except (
        TypeError,
        ValueError,
    ):

        raise RuntimeError(
            "TathaAstu returned an invalid Vikram Samvat "
            f"value for {day.isoformat()}: "
            f"{value!r}"
        )


# ============================================================
# VIKRAM SAMVAT EXTRACTION
# ============================================================

def get_vikram_samvat(
    panchang,
    day,
    api_key,
):
    """
    Prefer Samvat directly from the Panchang response.

    If unavailable, use the dedicated TathaAstu Samvatsara
    endpoint.

    No Gregorian-year arithmetic is performed.
    """

    hindu_calendar = panchang.get(
        "hindu_calendar",
        {},
    )

    value = find_nested_value(
        hindu_calendar,
        [
            "vikram_samvat",
            "vikrama_samvat",
            "samvat",
            "vikramSamvat",
            "vikramaSamvat",
        ],
    )

    if value is not None:

        try:

            return int(
                value
            )

        except (
            TypeError,
            ValueError,
        ):

            pass

    return get_tathaastu_samvatsara(
        day,
        api_key,
    )


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

def extract_time(
    value,
):

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

    # ========================================================
    # TITHI
    # ========================================================

    tithi_name = tithi.get(
        "name",
        "",
    )

    paksha_name = tithi.get(
        "paksha",
        "",
    )

    tithi_name_hi = (
        get_localized_field(
            tithi,
            "name",
        )
    )

    if not tithi_name_hi:

        raise RuntimeError(
            "TathaAstu did not provide a Hindi/localized "
            "Tithi name for "
            f"{day.isoformat()}."
        )

    # ========================================================
    # PAKSHA
    # ========================================================

    paksha_name_hi = paksha_name

    # ========================================================
    # HINDU LUNAR MONTH
    # ========================================================

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
    # If the normal Panchang response does not expose the
    # localized month names, use the dedicated endpoint.
    # --------------------------------------------------------

    if (
        not purnimanta_month_hi
        or not amanta_month_hi
    ):

        month_data = (
            get_tathaastu_hindu_month(
                day,
                tathaastu_api_key,
            )
        )

        if not purnimanta_month_hi:

            purnimanta_month_hi = (
                get_hindu_month_name_hi(
                    month_data,
                    "purnimanta",
                )
            )

        if not amanta_month_hi:

            amanta_month_hi = (
                get_hindu_month_name_hi(
                    month_data,
                    "amanta",
                )
            )

    if not purnimanta_month_hi:

        raise RuntimeError(
            "TathaAstu did not provide a Hindi/localized "
            "Purnimanta month for "
            f"{day.isoformat()}."
        )

    # ========================================================
    # VIKRAM SAMVAT
    # ========================================================

    samvat = get_vikram_samvat(
        tathaastu_panchang,
        day,
        tathaastu_api_key,
    )

    # ========================================================
    # SUN
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
    Build the header dynamically from TathaAstu values.

    We use the Purnimanta month because this is the North
    Indian convention used for the calendar header.

    If the Gregorian month crosses a Hindu lunar-month
    boundary, both month names are shown.
    """

    names = []

    for item in days:

        name = item.get(
            "hindu_month_purnimanta",
            "",
        )

        if name and name not in names:

            names.append(
                name
            )

    if names:

        return " — ".join(
            names
        )

    return ""


# ============================================================
# MAIN
# ============================================================

def build_calendar_output(
    calendar_date,
    highlighted_date,
    navamsha_api_key,
    tathaastu_api_key,
    festivals_by_date,
    now,
):
    """
    Build one complete monthly calendar.

    calendar_date:
        Any date inside the Gregorian month that should be
        displayed.

    highlighted_date:
        The date whose cell should be highlighted by the
        renderer.
    """

    year = calendar_date.year
    month = calendar_date.month

    print()
    print(
        f"Building calendar month: "
        f"{MONTHS_HI[month]} {year}"
    )

    print(
        f"Highlighted date: "
        f"{highlighted_date.isoformat()}"
    )

    # --------------------------------------------------------
    # MONTH RANGE
    # --------------------------------------------------------

    first_day = date(
        year,
        month,
        1,
    )

    days_in_month = calendar.monthrange(
        year,
        month,
    )[1]

    last_day = date(
        year,
        month,
        days_in_month,
    )

    # --------------------------------------------------------
    # FESTIVALS
    #
    # Festival data is supplied for this Gregorian month.
    # --------------------------------------------------------

    month_festivals = festivals_by_date

    # --------------------------------------------------------
    # BUILD EVERY DAY
    # --------------------------------------------------------

    days = []

    current_day = first_day

    while current_day <= last_day:

        day_record = build_day(
            current_day,
            navamsha_api_key,
            tathaastu_api_key,
            month_festivals,
        )

        days.append(
            day_record
        )

        current_day += timedelta(
            days=1
        )

    if not days:

        raise RuntimeError(
            "No calendar days were generated."
        )

    # --------------------------------------------------------
    # HINDU MONTH HEADER
    # --------------------------------------------------------

    hindu_month_header = (
        build_hindu_month_header(
            days
        )
    )

    if not hindu_month_header:

        raise RuntimeError(
            "Unable to build Hindu month header."
        )

    # --------------------------------------------------------
    # FIND HIGHLIGHTED DATE RECORD
    # --------------------------------------------------------

    highlighted_record = None

    for item in days:

        if (
            item["date"]
            == highlighted_date.isoformat()
        ):

            highlighted_record = item

            break

    if highlighted_record is None:

        raise RuntimeError(
            "Highlighted date "
            f"{highlighted_date.isoformat()} "
            "does not belong to calendar month "
            f"{year}-{month:02d}."
        )

    # --------------------------------------------------------
    # VIKRAM SAMVAT
    #
    # Use the value belonging to the highlighted date.
    # --------------------------------------------------------

    vikram_samvat = highlighted_record[
        "vikram_samvat"
    ]

    # --------------------------------------------------------
    # FINAL OUTPUT
    # --------------------------------------------------------

    output = {

        "generated_at": now.isoformat(),

        # ----------------------------------------------------
        # IMPORTANT:
        #
        # The renderer uses this field to decide which date
        # receives the black highlight.
        # ----------------------------------------------------

        "target_date": (
            highlighted_date.isoformat()
        ),

        "year": year,

        "month": month,

        # ----------------------------------------------------
        # Gregorian month name retained for compatibility.
        # ----------------------------------------------------

        "month_hindi": MONTHS_HI[
            month
        ],

        # ----------------------------------------------------
        # PERPETUAL HINDU CALENDAR VALUES
        # ----------------------------------------------------

        "hindu_month": (
            hindu_month_header
        ),

        "vikram_samvat": int(
            vikram_samvat
        ),

        # ----------------------------------------------------
        # SOURCE INFORMATION
        # ----------------------------------------------------

        "hindu_calendar_source": {
            "provider": "TathaAstu",
            "region": TATHAASTU_REGION,
            "language": "hi",
        },

        "festival_source": {
            "provider": "TathaAstu",
            "region": TATHAASTU_REGION,
            "language": "hi",
        },

        "astronomical_source": {
            "provider": "Navamsha",
            "latitude": LATITUDE,
            "longitude": LONGITUDE,
            "timezone": TIMEZONE_NAME,
        },

        # ----------------------------------------------------
        # DAILY DATA
        # ----------------------------------------------------

        "days": days,
    }

    return output


def main():

    print()
    print("========================================")
    print("AJ KA DHARM — CALENDAR GENERATOR")
    print("========================================")

    # --------------------------------------------------------
    # API KEYS
    # --------------------------------------------------------

    navamsha_api_key = os.environ.get(
        "NAVAMSHA_API_KEY"
    )

    tathaastu_api_key = os.environ.get(
        "TATHAASTU_API_KEY"
    )

    if not navamsha_api_key:

        raise RuntimeError(
            "NAVAMSHA_API_KEY environment variable is missing."
        )

    if not tathaastu_api_key:

        raise RuntimeError(
            "TATHAASTU_API_KEY environment variable is missing."
        )

    # --------------------------------------------------------
    # CURRENT / TARGET DATES
    #
    # We now generate BOTH:
    #
    #   1. today's calendar
    #   2. tomorrow's calendar
    #
    # This fixes the reset/highlight problem while preserving
    # the existing tomorrow-at-23:30 GitHub generation model.
    # --------------------------------------------------------

    now = datetime.now(
        ZoneInfo(TIMEZONE_NAME)
    )

    today = now.date()

    tomorrow = (
        today
        + timedelta(days=1)
    )

    print(
        f"Current local date : "
        f"{today.isoformat()}"
    )

    print(
        f"Today highlight    : "
        f"{today.isoformat()}"
    )

    print(
        f"Tomorrow highlight : "
        f"{tomorrow.isoformat()}"
    )

    # --------------------------------------------------------
    # DETERMINE WHICH GREGORIAN MONTHS ARE REQUIRED
    # --------------------------------------------------------

    required_months = {}

    required_months[
        (
            today.year,
            today.month,
        )
    ] = True

    required_months[
        (
            tomorrow.year,
            tomorrow.month,
        )
    ] = True

    # --------------------------------------------------------
    # FETCH FESTIVALS ONCE PER REQUIRED MONTH
    # --------------------------------------------------------

    festivals_by_month = {}

    for (
        month_year,
        _
    ) in required_months.items():

        month_year_year = month_year[0]
        month_year_month = month_year[1]

        festivals_by_month[
            month_year
        ] = get_tathaastu_festivals(
            month_year_year,
            month_year_month,
            tathaastu_api_key,
        )

    # --------------------------------------------------------
    # BUILD TODAY'S CALENDAR
    # --------------------------------------------------------

    today_month_key = (
        today.year,
        today.month,
    )

    today_output = build_calendar_output(
        calendar_date=today,
        highlighted_date=today,
        navamsha_api_key=navamsha_api_key,
        tathaastu_api_key=tathaastu_api_key,
        festivals_by_date=festivals_by_month[
            today_month_key
        ],
        now=now,
    )

    # --------------------------------------------------------
    # BUILD TOMORROW'S CALENDAR
    #
    # If tomorrow is in a new Gregorian month, the correct
    # next month's calendar is generated automatically.
    # --------------------------------------------------------

    tomorrow_month_key = (
        tomorrow.year,
        tomorrow.month,
    )

    tomorrow_output = build_calendar_output(
        calendar_date=tomorrow,
        highlighted_date=tomorrow,
        navamsha_api_key=navamsha_api_key,
        tathaastu_api_key=tathaastu_api_key,
        festivals_by_date=festivals_by_month[
            tomorrow_month_key
        ],
        now=now,
    )

    # --------------------------------------------------------
    # WRITE TODAY'S DATA
    # --------------------------------------------------------

    today_output_file = (
        "calendar_data_today.json"
    )

    with open(
        today_output_file,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            today_output,
            file,
            ensure_ascii=False,
            indent=2,
        )

    # --------------------------------------------------------
    # WRITE TOMORROW'S DATA
    #
    # This remains calendar_data.json so the existing
    # renderer/workflow continues to recognize it.
    # --------------------------------------------------------

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            tomorrow_output,
            file,
            ensure_ascii=False,
            indent=2,
        )

    # --------------------------------------------------------
    # LOG
    # --------------------------------------------------------

    print()
    print("========================================")
    print("CALENDAR DATA GENERATION COMPLETE")
    print("========================================")

    print(
        "Today's calendar:"
    )

    print(
        f"  Month: "
        f"{MONTHS_HI[today.month]} "
        f"{today.year}"
    )

    print(
        f"  Highlight: "
        f"{today.isoformat()}"
    )

    print(
        f"  Hindu month: "
        f"{today_output['hindu_month']}"
    )

    print(
        f"  Vikram Samvat: "
        f"{today_output['vikram_samvat']}"
    )

    print(
        f"  Output: "
        f"{today_output_file}"
    )

    print()

    print(
        "Tomorrow's calendar:"
    )

    print(
        f"  Month: "
        f"{MONTHS_HI[tomorrow.month]} "
        f"{tomorrow.year}"
    )

    print(
        f"  Highlight: "
        f"{tomorrow.isoformat()}"
    )

    print(
        f"  Hindu month: "
        f"{tomorrow_output['hindu_month']}"
    )

    print(
        f"  Vikram Samvat: "
        f"{tomorrow_output['vikram_samvat']}"
    )

    print(
        f"  Output: "
        f"{OUTPUT_FILE}"
    )

    print("========================================")


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()

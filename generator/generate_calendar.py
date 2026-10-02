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
# Panchang source : TathaAstu monthly calendar API
# Festival source : TathaAstu
# Astronomical     : Navamsha
# Festival style   : North Indian / Hindi
# Location         : Kolkata
#
# IMPORTANT:
#
# The old version called TathaAstu /v1/panchang once for
# every single day.
#
# This version uses /v1/calendar/month instead.
#
# This dramatically reduces TathaAstu usage and keeps the
# project within the Free 500-request/month allowance.
# ============================================================


# ============================================================
# TATHAASTU MONTHLY CALENDAR API
# ============================================================

TATHAASTU_CALENDAR_MONTH_URL = (
    "https://api.tathaastuapi.com/v1/calendar/month"
)


# ============================================================
# TATHAASTU FESTIVAL API
# ============================================================

TATHAASTU_FESTIVAL_URL = (
    "https://api.tathaastuapi.com/v1/festivals/month"
)

TATHAASTU_REGION = "NORTH_INDIA"


# ============================================================
# TATHAASTU HINDU MONTH API
# ============================================================

TATHAASTU_HINDU_MONTH_URL = (
    "https://api.tathaastuapi.com/v1/hindu-month"
)


# ============================================================
# TATHAASTU SAMVATSARA API
# ============================================================

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
# TITHI HINDI NAMES
#
# These are language mappings only.
# They are NOT an annual calendar table.
# ============================================================

TITHI_HI = {
    "Pratipada": "प्रतिपदा",
    "Prathama": "प्रतिपदा",

    "Dwitiya": "द्वितीया",
    "Dvitiya": "द्वितीया",

    "Tritiya": "तृतीया",

    "Chaturthi": "चतुर्थी",

    "Panchami": "पंचमी",

    "Shashthi": "षष्ठी",
    "Shashti": "षष्ठी",

    "Saptami": "सप्तमी",

    "Ashtami": "अष्टमी",

    "Navami": "नवमी",

    "Dashami": "दशमी",

    "Ekadashi": "एकादशी",
    "Ekadasi": "एकादशी",

    "Dwadashi": "द्वादशी",
    "Dvadashi": "द्वादशी",

    "Trayodashi": "त्रयोदशी",

    "Chaturdashi": "चतुर्दशी",

    "Purnima": "पूर्णिमा",

    "Amavasya": "अमावस्या",
}


# ============================================================
# GENERIC TITHI-BASED OBSERVANCES
# ============================================================

def get_basic_festival(
    tithi_name,
    paksha_name,
):
    """
    Fallback observance used only when the festival API does
    not provide a named festival for that date.
    """

    name = str(
        tithi_name
    ).strip().lower()

    paksha = str(
        paksha_name
    ).strip().lower()

    if name in {
        "ekadashi",
        "ekadasi",
    }:
        return "एकादशी व्रत"

    if name == "purnima":
        return "पूर्णिमा व्रत"

    if name == "amavasya":
        return "अमावस्या"

    if name == "trayodashi":
        return "प्रदोष व्रत"

    if name == "chaturthi":

        if paksha == "krishna":
            return "संकष्टी चतुर्थी"

        return "चतुर्थी व्रत"

    if name == "chaturdashi":

        if paksha == "krishna":
            return "मासिक शिवरात्रि"

        return "चतुर्दशी व्रत"

    return ""


# ============================================================
# GENERIC TATHAASTU REQUEST
# ============================================================

def request_tathaastu_json(
    url,
    api_key,
    params,
):
    response = requests.get(
        url,
        headers={
            "X-API-Key": api_key,
        },
        params=params,
        timeout=30,
    )

    response.raise_for_status()

    data = response.json()

    # TathaAstu sometimes wraps the useful payload in "data".
    if (
        isinstance(data, dict)
        and isinstance(
            data.get("data"),
            dict,
        )
    ):
        return data["data"]

    return data


# ============================================================
# TATHAASTU MONTHLY PANCHANG
# ============================================================

def get_tathaastu_calendar_month(
    year,
    month,
    api_key,
):
    """
    Fetch the complete Panchang calendar for one Gregorian
    month in a single TathaAstu request.
    """

    print(
        f"  Fetching TathaAstu monthly Panchang: "
        f"{year}-{month:02d}"
    )

    params = {
        "year": year,
        "month": month,
        "lat": LATITUDE,
        "lon": LONGITUDE,
    }

    data = request_tathaastu_json(
        TATHAASTU_CALENDAR_MONTH_URL,
        api_key,
        params,
    )

    if not isinstance(
        data,
        dict,
    ):
        raise RuntimeError(
            "TathaAstu /calendar/month response was not "
            "a JSON object."
        )

    days = data.get(
        "days"
    )

    if not isinstance(
        days,
        list,
    ):
        raise RuntimeError(
            "TathaAstu /calendar/month did not contain "
            "a 'days' list. "
            f"Top-level keys: {sorted(data.keys())}"
        )

    days_by_date = {}

    for item in days:

        if not isinstance(
            item,
            dict,
        ):
            continue

        raw_date = (
            item.get("date")
            or item.get("day_date")
        )

        if (
            not raw_date
            and isinstance(
                item.get("day"),
                int,
            )
        ):
            raw_date = (
                f"{year:04d}-"
                f"{month:02d}-"
                f"{item['day']:02d}"
            )

        if not raw_date:
            continue

        day_key = str(
            raw_date
        )[:10]

        # ----------------------------------------------------
        # TITHI
        # ----------------------------------------------------

        tithi = item.get(
            "tithi",
            "",
        )

        tithi_name = ""
        tithi_name_hi = ""
        tithi_number = None
        paksha = ""

        if isinstance(
            tithi,
            dict,
        ):

            tithi_name = (
                tithi.get("name")
                or tithi.get("key")
                or ""
            )

            tithi_name_hi = (
                tithi.get("name_local")
                or tithi.get("name_hi")
                or tithi.get("local")
                or ""
            )

            tithi_number = (
                tithi.get("number")
            )

            paksha = (
                tithi.get("paksha")
                or ""
            )

        else:

            tithi_name = str(
                tithi
            ).strip()

            tithi_name_hi = (
                item.get("tithi_local")
                or item.get("tithi_hi")
                or ""
            )

            tithi_number = (
                item.get("tithi_number")
            )

            paksha = (
                item.get("paksha")
                or ""
            )

        # ----------------------------------------------------
        # Some monthly responses may put paksha at top level.
        # ----------------------------------------------------

        if not paksha:

            paksha = (
                item.get("paksha")
                or ""
            )

        # ----------------------------------------------------
        # Hindi Tithi
        # ----------------------------------------------------

        if not tithi_name_hi:

            tithi_name_hi = (
                TITHI_HI.get(
                    tithi_name,
                    "",
                )
            )

        # If TathaAstu already returned Hindi, preserve it.
        if (
            not tithi_name_hi
            and any(
                ord(char) > 127
                for char in tithi_name
            )
        ):
            tithi_name_hi = tithi_name

        if not tithi_name:

            raise RuntimeError(
                "TathaAstu monthly response did not "
                f"provide a Tithi for {day_key}."
            )

        if not tithi_name_hi:

            raise RuntimeError(
                "TathaAstu monthly response did not "
                "provide a Hindi Tithi name for "
                f"{day_key}.\n"
                f"Available item keys: "
                f"{sorted(item.keys())}"
            )

        days_by_date[day_key] = {
            "tithi_name": tithi_name,
            "tithi_name_hi": tithi_name_hi,
            "tithi_number": tithi_number,
            "paksha": paksha,
            "raw": item,
        }

    if not days_by_date:

        raise RuntimeError(
            "TathaAstu monthly response contained no "
            f"usable calendar days for {year}-{month:02d}."
        )

    print(
        f"  Monthly Panchang days loaded: "
        f"{len(days_by_date)}"
    )

    return days_by_date


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

    print(
        f"  Fetching festival data: "
        f"{year}-{month:02d}"
    )

    params = {
        "year": year,
        "month": month,
        "region": TATHAASTU_REGION,
        "lang": "hi",
    }

    data = request_tathaastu_json(
        TATHAASTU_FESTIVAL_URL,
        api_key,
        params,
    )

    festivals = data.get(
        "festivals"
    )

    if not isinstance(
        festivals,
        list,
    ):
        raise RuntimeError(
            "TathaAstu festival response did not "
            "contain a valid 'festivals' list."
        )

    festivals_by_date = {}

    for item in festivals:

        if not isinstance(
            item,
            dict,
        ):
            continue

        festival_date = (
            item.get("observation_date")
            or item.get("date")
        )

        festival_name = (
            item.get(
                "display_name_local"
            )
            or item.get(
                "name_local"
            )
            or item.get(
                "display_name"
            )
            or item.get(
                "name"
            )
            or ""
        )

        if not festival_date:
            continue

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
        }

        festivals_by_date.setdefault(
            str(festival_date)[:10],
            [],
        ).append(
            entry
        )

    print(
        f"  Festival entries: "
        f"{len(festivals)}"
    )

    return festivals_by_date


# ============================================================
# SELECT FESTIVAL
# ============================================================

def choose_festival_for_date(
    day,
    festivals_by_date,
    tithi_name,
    paksha_name,
):
    entries = festivals_by_date.get(
        day.isoformat(),
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
# TATHAASTU HINDU MONTH
# ============================================================

def get_tathaastu_hindu_month(
    day,
    api_key,
):
    """
    Fetch Hindu month information for one date.

    We deliberately call this only for the first and last
    day of each required Gregorian month.

    This is enough to detect a Purnimanta month transition
    inside a Gregorian month without making daily API calls.
    """

    print(
        f"  Fetching Hindu month: "
        f"{day.isoformat()}"
    )

    params = {
        "date": day.isoformat(),
        "lat": LATITUDE,
        "lon": LONGITUDE,
        "lang": "hi",
        "region": TATHAASTU_REGION,
    }

    data = request_tathaastu_json(
        TATHAASTU_HINDU_MONTH_URL,
        api_key,
        params,
    )

    if not isinstance(
        data,
        dict,
    ):
        raise RuntimeError(
            "TathaAstu Hindu-month response was not "
            "a JSON object."
        )

    purnimanta = (
        data.get(
            "purnimanta_month_local"
        )
        or data.get(
            "purnimanta_local"
        )
        or data.get(
            "purnimanta_month"
        )
        or data.get(
            "purnimanta"
        )
        or ""
    )

    amanta = (
        data.get(
            "amanta_month_local"
        )
        or data.get(
            "amanta_local"
        )
        or data.get(
            "amanta_month"
        )
        or data.get(
            "amanta"
        )
        or ""
    )

    return {
        "purnimanta": str(
            purnimanta
        ).strip(),

        "amanta": str(
            amanta
        ).strip(),
    }


# ============================================================
# TATHAASTU SAMVATSARA
# ============================================================

def find_nested_value(
    obj,
    candidate_keys,
):
    """
    Recursively search JSON for an explicitly named field.
    """

    if isinstance(
        obj,
        dict,
    ):

        for key in candidate_keys:

            if obj.get(
                key
            ) not in (
                None,
                "",
            ):
                return obj[key]

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

        for value in obj:

            result = find_nested_value(
                value,
                candidate_keys,
            )

            if result not in (
                None,
                "",
            ):
                return result

    return None


def get_tathaastu_samvat(
    day,
    api_key,
):
    print(
        f"  Fetching Vikram Samvat: "
        f"{day.isoformat()}"
    )

    params = {
        "date": day.isoformat(),
        "lat": LATITUDE,
        "lon": LONGITUDE,
        "region": TATHAASTU_REGION,
    }

    data = request_tathaastu_json(
        TATHAASTU_SAMVATSARA_URL,
        api_key,
        params,
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
            f"for {day.isoformat()}."
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
            "TathaAstu returned an invalid Vikram "
            f"Samvat value for {day.isoformat()}: "
            f"{value!r}"
        )


# ============================================================
# NAVAMSHA POST
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
            "T",
            1,
        )[1][:5]

    return value[:5]


# ============================================================
# BUILD ONE DAY
# ============================================================

def build_day(
    day,
    monthly_data,
    navamsha_api_key,
    festivals_by_date,
    hindu_month_name,
    samvat,
    astronomical_cache,
):
    day_key = day.isoformat()

    monthly_record = monthly_data.get(
        day_key
    )

    if monthly_record is None:

        raise RuntimeError(
            "Monthly TathaAstu data has no entry "
            f"for {day_key}."
        )

    # ========================================================
    # NAVAMSHA
    #
    # Cache this so today's and tomorrow's calendars do not
    # request the same astronomical data twice.
    # ========================================================

    if day_key not in astronomical_cache:

        print(
            f"    Fetching Navamsha times: "
            f"{day_key}"
        )

        sun = get_sun_times(
            day,
            navamsha_api_key,
        )

        moon = get_moon_times(
            day,
            navamsha_api_key,
        )

        astronomical_cache[day_key] = {

            "sunrise": extract_time(
                sun["rise"]["local_datetime"]
            ),

            "sunset": extract_time(
                sun["set"]["local_datetime"]
            ),

            "moonrise": (
                extract_time(
                    moon["rise"].get(
                        "local_datetime"
                    )
                )
                if moon.get("rise")
                else ""
            ),

            "moonset": (
                extract_time(
                    moon["set"].get(
                        "local_datetime"
                    )
                )
                if moon.get("set")
                else ""
            ),
        }

    astronomical = (
        astronomical_cache[day_key]
    )

    # ========================================================
    # FESTIVAL
    # ========================================================

    festival = choose_festival_for_date(
        day,
        festivals_by_date,
        monthly_record["tithi_name"],
        monthly_record["paksha"],
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
        # Dynamic Panchang data
        # ----------------------------------------------------

        "tithi": monthly_record[
            "tithi_name_hi"
        ],

        "tithi_key": monthly_record[
            "tithi_name"
        ],

        "paksha": monthly_record[
            "paksha"
        ],

        "paksha_key": monthly_record[
            "paksha"
        ],

        # ----------------------------------------------------
        # Hindu calendar
        # ----------------------------------------------------

        "hindu_month_purnimanta": (
            hindu_month_name[
                "purnimanta"
            ]
        ),

        "hindu_month_amanta": (
            hindu_month_name[
                "amanta"
            ]
        ),

        "vikram_samvat": int(
            samvat
        ),

        # ----------------------------------------------------
        # Astronomical timings
        # ----------------------------------------------------

        "sunrise": astronomical[
            "sunrise"
        ],

        "sunset": astronomical[
            "sunset"
        ],

        "moonrise": astronomical[
            "moonrise"
        ],

        "moonset": astronomical[
            "moonset"
        ],

        # ----------------------------------------------------
        # Festival
        # ----------------------------------------------------

        "festival": festival,
    }


# ============================================================
# BUILD MONTH
# ============================================================

def build_calendar_output(
    calendar_date,
    highlighted_date,
    navamsha_api_key,
    month_cache,
    festivals_cache,
    hindu_month_cache,
    samvat_cache,
    astronomical_cache,
    now,
):
    year = calendar_date.year
    month = calendar_date.month

    month_key = (
        year,
        month,
    )

    print()
    print(
        f"Building calendar month: "
        f"{MONTHS_HI[month]} {year}"
    )

    print(
        f"Highlighted date: "
        f"{highlighted_date.isoformat()}"
    )

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

    monthly_data = month_cache[
        month_key
    ]

    festivals_by_date = festivals_cache[
        month_key
    ]

    hindu_month_data = hindu_month_cache[
        month_key
    ]

    samvat = samvat_cache[
        month_key
    ]

    # ========================================================
    # BUILD EVERY DAY
    # ========================================================

    days = []

    current_day = first_day

    while current_day <= last_day:

        # ----------------------------------------------------
        # Use the first/last-day Hindu month values only where
        # they exist.
        #
        # For all middle dates, use the first-day value.
        #
        # If first and last differ, the header will contain
        # both names, preserving the existing calendar design.
        # ----------------------------------------------------

        hindu_month_name = (
            hindu_month_data[
                "names_by_date"
            ].get(
                current_day.isoformat(),
                hindu_month_data[
                    "default"
                ],
            )
        )

        day_record = build_day(
            current_day,
            monthly_data,
            navamsha_api_key,
            festivals_by_date,
            hindu_month_name,
            samvat,
            astronomical_cache,
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

    # ========================================================
    # HINDU MONTH HEADER
    # ========================================================

    hindu_month_names = []

    for item in days:

        name = item.get(
            "hindu_month_purnimanta",
            "",
        )

        if (
            name
            and name not in hindu_month_names
        ):

            hindu_month_names.append(
                name
            )

    hindu_month_header = " — ".join(
        hindu_month_names
    )

    if not hindu_month_header:

        raise RuntimeError(
            "Unable to build Hindu month header."
        )

    # ========================================================
    # FIND HIGHLIGHTED DATE
    # ========================================================

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

    # ========================================================
    # FINAL OUTPUT
    # ========================================================

    return {

        "generated_at": now.isoformat(),

        "target_date": (
            highlighted_date.isoformat()
        ),

        "year": year,

        "month": month,

        "month_hindi": MONTHS_HI[
            month
        ],

        "hindu_month": (
            hindu_month_header
        ),

        "vikram_samvat": int(
            highlighted_record[
                "vikram_samvat"
            ]
        ),

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

        "days": days,
    }


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("========================================")
    print("AJ KA DHARM — CALENDAR GENERATOR")
    print("========================================")

    # ========================================================
    # API KEYS
    # ========================================================

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

    # ========================================================
    # CURRENT / TARGET DATES
    # ========================================================

    now = datetime.now(
        ZoneInfo(
            TIMEZONE_NAME
        )
    )

    today = now.date()

    tomorrow = (
        today
        + timedelta(
            days=1
        )
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

    # ========================================================
    # REQUIRED MONTHS
    # ========================================================

    required_months = {
        (
            today.year,
            today.month,
        ),
        (
            tomorrow.year,
            tomorrow.month,
        ),
    }

    # ========================================================
    # CACHES
    #
    # These caches are for THIS workflow run.
    #
    # They prevent today's and tomorrow's calendar builds
    # from requesting the same month/astronomical data twice.
    # ========================================================

    month_cache = {}

    festivals_cache = {}

    hindu_month_cache = {}

    samvat_cache = {}

    astronomical_cache = {}

    # ========================================================
    # FETCH DATA ONCE PER REQUIRED MONTH
    # ========================================================

    for month_key in sorted(
        required_months
    ):

        year = month_key[0]
        month = month_key[1]

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

        # ----------------------------------------------------
        # ONE monthly Panchang request
        # ----------------------------------------------------

        month_cache[
            month_key
        ] = get_tathaastu_calendar_month(
            year,
            month,
            tathaastu_api_key,
        )

        # ----------------------------------------------------
        # ONE festival request
        # ----------------------------------------------------

        festivals_cache[
            month_key
        ] = get_tathaastu_festivals(
            year,
            month,
            tathaastu_api_key,
        )

        # ----------------------------------------------------
        # TWO Hindu-month requests:
        #
        # first day + last day
        #
        # This lets us detect a lunar-month transition while
        # avoiding daily Hindu-month API calls.
        # ----------------------------------------------------

        first_month = (
            get_tathaastu_hindu_month(
                first_day,
                tathaastu_api_key,
            )
        )

        last_month = (
            get_tathaastu_hindu_month(
                last_day,
                tathaastu_api_key,
            )
        )

        if not first_month[
            "purnimanta"
        ]:

            raise RuntimeError(
                "TathaAstu did not provide a "
                f"Purnimanta month for {first_day}."
            )

        names_by_date = {

            first_day.isoformat():
                first_month,

            last_day.isoformat():
                last_month,
        }

        hindu_month_cache[
            month_key
        ] = {

            "names_by_date":
                names_by_date,

            "default":
                first_month,
        }

        # ----------------------------------------------------
        # Vikram Samvat
        #
        # Use the relevant highlighted date for this month.
        # ----------------------------------------------------

        if month_key == (
            today.year,
            today.month,
        ):

            samvat_reference = today

        else:

            samvat_reference = tomorrow

        samvat_cache[
            month_key
        ] = get_tathaastu_samvat(
            samvat_reference,
            tathaastu_api_key,
        )

    # ========================================================
    # BUILD TODAY'S CALENDAR
    # ========================================================

    today_output = build_calendar_output(
        calendar_date=today,

        highlighted_date=today,

        navamsha_api_key=navamsha_api_key,

        month_cache=month_cache,

        festivals_cache=festivals_cache,

        hindu_month_cache=hindu_month_cache,

        samvat_cache=samvat_cache,

        astronomical_cache=astronomical_cache,

        now=now,
    )

    # ========================================================
    # BUILD TOMORROW'S CALENDAR
    # ========================================================

    tomorrow_output = build_calendar_output(
        calendar_date=tomorrow,

        highlighted_date=tomorrow,

        navamsha_api_key=navamsha_api_key,

        month_cache=month_cache,

        festivals_cache=festivals_cache,

        hindu_month_cache=hindu_month_cache,

        samvat_cache=samvat_cache,

        astronomical_cache=astronomical_cache,

        now=now,
    )

    # ========================================================
    # WRITE TODAY'S DATA
    # ========================================================

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

    # ========================================================
    # WRITE TOMORROW'S DATA
    #
    # Existing workflow expects calendar_data.json.
    # ========================================================

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

    # ========================================================
    # FINAL LOG
    # ========================================================

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
    main()6*

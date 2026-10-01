import json
import os
from datetime import datetime
from zoneinfo import ZoneInfo

from PIL import Image, ImageDraw, ImageFont


# ============================================================
# AJ KA DHARM
# 800 x 480 MONOCHROME CALENDAR RENDERER
# ============================================================

WIDTH = 800
HEIGHT = 480

INPUT_FILE = "calendar_data.json"
OUTPUT_FILE = "dashboard.bin"

TIMEZONE = ZoneInfo("Asia/Kolkata")


# ============================================================
# FONT PATHS
# ============================================================

DEVANAGARI_DIR = "/usr/share/fonts/truetype/noto"

FONT_DEV_REGULAR = os.path.join(
    DEVANAGARI_DIR,
    "NotoSansDevanagari-Regular.ttf",
)

FONT_DEV_BOLD = os.path.join(
    DEVANAGARI_DIR,
    "NotoSansDevanagari-Bold.ttf",
)

FONT_LATIN_BOLD = (
    "/usr/share/fonts/truetype/dejavu/"
    "DejaVuSans-Bold.ttf"
)


# ============================================================
# FONT LOADER
# ============================================================

def load_font(path, size):
    return ImageFont.truetype(
        path,
        size,
    )


# ============================================================
# TEXT HELPERS
# ============================================================

def center_text(
    draw,
    box,
    text,
    font,
    fill=0,
):
    x1, y1, x2, y2 = box

    bbox = draw.textbbox(
        (0, 0),
        text,
        font=font,
    )

    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]

    x = (
        x1
        + ((x2 - x1) - tw) // 2
    )

    y = (
        y1
        + ((y2 - y1) - th) // 2
        - bbox[1]
    )

    draw.text(
        (x, y),
        text,
        font=font,
        fill=fill,
    )


def fit_text(
    draw,
    text,
    font,
    max_width,
):
    if not text:
        return ""

    bbox = draw.textbbox(
        (0, 0),
        text,
        font=font,
    )

    if (
        bbox[2] - bbox[0]
        <= max_width
    ):
        return text

    while len(text) > 1:

        text = text[:-1]

        candidate = (
            text + "…"
        )

        bbox = draw.textbbox(
            (0, 0),
            candidate,
            font=font,
        )

        if (
            bbox[2] - bbox[0]
            <= max_width
        ):
            return candidate

    return "…"


def format_time_12h(value):
    if not value:
        return ""

    hour, minute = value.split(":")

    hour = int(hour)

    suffix = (
        "AM"
        if hour < 12
        else "PM"
    )

    hour12 = hour % 12

    if hour12 == 0:
        hour12 = 12

    return (
        f"{hour12:02d}:{minute} "
        f"{suffix}"
    )


# ============================================================
# SUN ICON
# ============================================================

def draw_sun_icon(
    draw,
    x,
    y,
):
    cx = x + 14
    cy = y + 14

    radius = 7

    draw.ellipse(
        (
            cx - radius,
            cy - radius,
            cx + radius,
            cy + radius,
        ),
        outline=0,
        width=2,
    )

    rays = [
        (
            cx,
            cy - 17,
            cx,
            cy - 11,
        ),
        (
            cx,
            cy + 11,
            cx,
            cy + 17,
        ),
        (
            cx - 17,
            cy,
            cx - 11,
            cy,
        ),
        (
            cx + 11,
            cy,
            cx + 17,
            cy,
        ),
        (
            cx - 12,
            cy - 12,
            cx - 8,
            cy - 8,
        ),
        (
            cx + 8,
            cy + 8,
            cx + 12,
            cy + 12,
        ),
        (
            cx + 8,
            cy - 8,
            cx + 12,
            cy - 12,
        ),
        (
            cx - 12,
            cy + 12,
            cx - 8,
            cy + 8,
        ),
    ]

    for x1, y1, x2, y2 in rays:

        draw.line(
            (
                x1,
                y1,
                x2,
                y2,
            ),
            fill=0,
            width=2,
        )


# ============================================================
# MOON ICON
# ============================================================

def draw_moon_icon(
    draw,
    x,
    y,
):
    cx = x + 13
    cy = y + 13

    draw.ellipse(
        (
            cx - 12,
            cy - 12,
            cx + 12,
            cy + 12,
        ),
        fill=0,
    )

    draw.ellipse(
        (
            cx - 4,
            cy - 12,
            cx + 15,
            cy + 12,
        ),
        fill=1,
    )


# ============================================================
# BUILD SUNDAY-FIRST CALENDAR GRID
# ============================================================

def build_grid(days):

    if not days:
        return []

    first_date = (
        datetime.fromisoformat(
            days[0]["date"]
        ).date()
    )

    sunday_offset = (
        first_date.weekday()
        + 1
    ) % 7

    grid = [
        None
    ] * sunday_offset

    grid.extend(days)

    while len(grid) % 7:

        grid.append(None)

    return [
        grid[i:i + 7]
        for i in range(
            0,
            len(grid),
            7,
        )
    ]


# ============================================================
# MAIN
# ============================================================

def main():

    # ========================================================
    # LOAD DATA
    # ========================================================

    print(
        "Loading calendar data..."
    )

    with open(
        INPUT_FILE,
        "r",
        encoding="utf-8",
    ) as file:

        data = json.load(file)

    days = data["days"]

    year = data["year"]
    month = data["month"]

    # --------------------------------------------------------
    # These are now supplied dynamically by TathaAstu through
    # generate_calendar.py.
    # --------------------------------------------------------

    hindu_month = data[
        "hindu_month"
    ]

    vikram_samvat = data[
        "vikram_samvat"
    ]

    target_date = data.get(
        "target_date",
        datetime.now(
            TIMEZONE
        ).date().isoformat(),
    )

    # ========================================================
    # CANVAS
    # ========================================================

    image = Image.new(
        "1",
        (
            WIDTH,
            HEIGHT,
        ),
        1,
    )

    draw = ImageDraw.Draw(
        image
    )

    # ========================================================
    # FONTS
    # ========================================================

    time_font = load_font(
        FONT_LATIN_BOLD,
        14,
    )

    weekday_font = load_font(
        FONT_DEV_BOLD,
        15,
    )

    date_font = load_font(
        FONT_LATIN_BOLD,
        20,
    )

    tithi_font = load_font(
        FONT_DEV_REGULAR,
        15,
    )

    festival_font = load_font(
        FONT_DEV_REGULAR,
        15,
    )

    header_font = load_font(
        FONT_DEV_BOLD,
        22,
    )

    # ========================================================
    # HEADER
    # ========================================================
    #
    # Dynamic:
    #
    #   hindu_month
    #   vikram_samvat
    #
    # Both come from TathaAstu via calendar_data.json.
    # ========================================================

    samvat_text = (
        f"विक्रम संवत "
        f"{vikram_samvat}"
    )

    hindu_bbox = draw.textbbox(
        (0, 0),
        hindu_month,
        font=header_font,
    )

    samvat_bbox = draw.textbbox(
        (0, 0),
        samvat_text,
        font=header_font,
    )

    hindu_width = (
        hindu_bbox[2]
        - hindu_bbox[0]
    )

    samvat_width = (
        samvat_bbox[2]
        - samvat_bbox[0]
    )

    center_gap = 24

    combined_width = (
        hindu_width
        + center_gap
        + samvat_width
    )

    start_x = (
        WIDTH
        - combined_width
    ) // 2

    center_y = 47

    hindu_height = (
        hindu_bbox[3]
        - hindu_bbox[1]
    )

    samvat_height = (
        samvat_bbox[3]
        - samvat_bbox[1]
    )

    draw.text(
        (
            start_x,
            center_y
            - hindu_height // 2,
        ),
        hindu_month,
        font=header_font,
        fill=0,
    )

    draw.text(
        (
            start_x
            + hindu_width
            + center_gap,
            center_y
            - samvat_height // 2,
        ),
        samvat_text,
        font=header_font,
        fill=0,
    )

    # ========================================================
    # SUN / MOON TIMES
    # ========================================================

    sunrise = format_time_12h(
        days[0].get(
            "sunrise",
            "",
        )
    )

    sunset = format_time_12h(
        days[0].get(
            "sunset",
            "",
        )
    )

    moonrise = format_time_12h(
        days[0].get(
            "moonrise",
            "",
        )
    )

    moonset = format_time_12h(
        days[0].get(
            "moonset",
            "",
        )
    )

    # --------------------------------------------------------
    # SUN
    # --------------------------------------------------------

    draw_sun_icon(
        draw,
        45,
        35,
    )

    draw.text(
        (
            82,
            35,
        ),
        sunrise,
        font=time_font,
        fill=0,
    )

    draw.text(
        (
            82,
            62,
        ),
        sunset,
        font=time_font,
        fill=0,
    )

    # --------------------------------------------------------
    # MOON
    # --------------------------------------------------------

    draw_moon_icon(
        draw,
        663,
        35,
    )

    draw.text(
        (
            700,
            35,
        ),
        moonrise,
        font=time_font,
        fill=0,
    )

    draw.text(
        (
            700,
            62,
        ),
        moonset,
        font=time_font,
        fill=0,
    )

    # ========================================================
    # EDGE-TO-EDGE CALENDAR GEOMETRY
    # ========================================================

    grid_y = 91

    weekday_h = 30

    calendar_bottom = 477

    calendar_height = (
        calendar_bottom
        - grid_y
        - weekday_h
    )

    # --------------------------------------------------------
    # Full 800px width.
    #
    # Seven columns are distributed across exactly 800 pixels.
    #
    # There is NO outer left/right vertical border.
    # Only six internal vertical separators exist.
    # --------------------------------------------------------

    column_edges = [
        round(
            i * WIDTH / 7
        )
        for i in range(8)
    ]

    weekdays = [
        "रविवार",
        "सोमवार",
        "मंगलवार",
        "बुधवार",
        "गुरुवार",
        "शुक्रवार",
        "शनिवार",
    ]

    # ========================================================
    # EDGE-TO-EDGE BLACK WEEKDAY HEADER
    # ========================================================

    for column, weekday in enumerate(
        weekdays
    ):

        x1 = column_edges[
            column
        ]

        x2 = column_edges[
            column + 1
        ]

        draw.rectangle(
            (
                x1,
                grid_y,
                x2 - 1,
                grid_y
                + weekday_h
                - 1,
            ),
            fill=0,
        )

        center_text(
            draw,
            (
                x1,
                grid_y,
                x2,
                grid_y
                + weekday_h,
            ),
            weekday,
            weekday_font,
            fill=1,
        )

    # ========================================================
    # BUILD GRID
    # ========================================================

    grid = build_grid(
        days
    )

    row_count = len(
        grid
    )

    cell_h = (
        calendar_height
        // row_count
    )

    body_top = (
        grid_y
        + weekday_h
    )

    # ========================================================
    # DRAW CELLS
    #
    # IMPORTANT:
    #
    # We deliberately do NOT draw grid lines yet.
    #
    # This lets us draw the black target-day highlight first.
    # The grid lines are drawn afterward, guaranteeing that
    # the highlight can never cover them.
    # ========================================================

    for row_index, row in enumerate(
        grid
    ):

        y = (
            body_top
            + row_index * cell_h
        )

        if (
            row_index
            == row_count - 1
        ):

            row_y2 = (
                calendar_bottom
            )

        else:

            row_y2 = (
                body_top
                + (
                    row_index + 1
                )
                * cell_h
            )

        actual_cell_h = (
            row_y2
            - y
        )

        for column, item in enumerate(
            row
        ):

            cell_left = (
                column_edges[
                    column
                ]
            )

            cell_right = (
                column_edges[
                    column + 1
                ]
            )

            if item is None:
                continue

            item_date = item[
                "date"
            ]

            is_target = (
                item_date
                == target_date
            )

            # =================================================
            # TARGET-DAY BLACK HIGHLIGHT
            #
            # White breathing space:
            #
            #   left   = 1px
            #   right  = 1px
            #   top    = 1px
            #   bottom = 1px
            #
            # The grid itself is drawn afterward.
            # =================================================

            if is_target:

                draw.rectangle(
                    (
                        cell_left + 2,
                        y + 2,
                        cell_right - 2,
                        row_y2 - 2,
                    ),
                    fill=0,
                )

                text_fill = 1

            else:

                text_fill = 0

            # =================================================
            # DATE
            # =================================================

            date_x = (
                cell_left
                + 7
            )

            draw.text(
                (
                    date_x,
                    y + 4,
                ),
                str(
                    item["day"]
                ),
                font=date_font,
                fill=text_fill,
            )

            # =================================================
            # TITHI
            # =================================================

            tithi = item.get(
                "tithi",
                "",
            )

            tithi_bbox = (
                draw.textbbox(
                    (0, 0),
                    tithi,
                    font=tithi_font,
                )
            )

            tithi_width = (
                tithi_bbox[2]
                - tithi_bbox[0]
            )

            tithi_x = (
                cell_right
                - 7
                - tithi_width
            )

            minimum_tithi_x = (
                date_x
                + 38
            )

            if (
                tithi_x
                < minimum_tithi_x
            ):

                tithi_x = (
                    minimum_tithi_x
                )

            draw.text(
                (
                    tithi_x,
                    y + 8,
                ),
                tithi,
                font=tithi_font,
                fill=text_fill,
            )

            # =================================================
            # FESTIVAL
            # =================================================

            festival = item.get(
                "festival",
                "",
            )

            if festival:

                available_width = (
                    (
                        cell_right
                        - 7
                    )
                    - (
                        cell_left
                        + 7
                    )
                )

                festival_text = fit_text(
                    draw,
                    festival,
                    festival_font,
                    available_width,
                )

                festival_bbox = (
                    draw.textbbox(
                        (0, 0),
                        festival_text,
                        font=festival_font,
                    )
                )

                festival_width = (
                    festival_bbox[2]
                    - festival_bbox[0]
                )

                festival_x = (
                    cell_left
                    + (
                        (
                            cell_right
                            - cell_left
                        )
                        - festival_width
                    )
                    // 2
                )

                festival_y = (
                    y
                    + min(
                        36,
                        actual_cell_h
                        - 23,
                    )
                )

                draw.text(
                    (
                        festival_x,
                        festival_y,
                    ),
                    festival_text,
                    font=festival_font,
                    fill=text_fill,
                )

    # ========================================================
    # HORIZONTAL GRID LINES
    #
    # Draw AFTER the cell contents and black highlight.
    #
    # Every horizontal line is exactly 1 pixel.
    # ========================================================

    for row_index in range(
        row_count + 1
    ):

        if (
            row_index
            == row_count
        ):

            y_line = (
                calendar_bottom
                - 1
            )

        else:

            y_line = (
                body_top
                + row_index * cell_h
            )

        draw.line(
            (
                0,
                y_line,
                WIDTH - 1,
                y_line,
            ),
            fill=0,
            width=1,
        )

    # ========================================================
    # INTERNAL VERTICAL GRID LINES
    #
    # ONLY six internal separators.
    #
    # No line at x=0.
    # No line at x=799.
    #
    # Every separator is exactly 1 pixel.
    # ========================================================

    for column in range(
        1,
        7,
    ):

        x_line = (
            column_edges[
                column
            ]
        )

        draw.line(
            (
                x_line,
                body_top,
                x_line,
                calendar_bottom - 1,
            ),
            fill=0,
            width=1,
        )

    # ========================================================
    # RAW 1-BIT BITMAP
    # ========================================================

    raw = image.convert(
        "1"
    ).tobytes()

    expected_size = (
        WIDTH
        * HEIGHT
        // 8
    )

    if len(raw) != expected_size:

                raise RuntimeError(
            "Invalid bitmap size: "
            f"{len(raw)} bytes; "
            f"expected {expected_size} bytes."
                )

import json
import os
import base64
from io import BytesIO
from datetime import datetime
from zoneinfo import ZoneInfo

from PIL import Image, ImageDraw, ImageFont


WIDTH = 800
HEIGHT = 480

INPUT_FILE = os.environ.get(
    "CALENDAR_INPUT_FILE",
    "calendar_data.json",
)

OUTPUT_FILE = os.environ.get(
    "CALENDAR_OUTPUT_FILE",
    "dashboard.bin",
)

TIMEZONE = ZoneInfo("Asia/Kolkata")


# ============================================================
# FONTS
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

def load_font(path, size):
    return ImageFont.truetype(path, size)


# ============================================================
# TEXT HELPERS
# ============================================================

def center_text(draw, box, text, font, fill=0):
    x1, y1, x2, y2 = box

    bbox = draw.textbbox(
        (0, 0),
        text,
        font=font,
    )

    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]

    x = x1 + ((x2 - x1) - tw) // 2

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


def fit_text(draw, text, font, max_width):
    if not text:
        return ""

    bbox = draw.textbbox(
        (0, 0),
        text,
        font=font,
    )

    if bbox[2] - bbox[0] <= max_width:
        return text

    while len(text) > 1:
        text = text[:-1]

        candidate = text + "…"

        bbox = draw.textbbox(
            (0, 0),
            candidate,
            font=font,
        )

        if bbox[2] - bbox[0] <= max_width:
            return candidate

    return "…"


def format_time_12h(value):
    if not value:
        return ""

    hour, minute = value.split(":")
    hour = int(hour)

    suffix = "AM" if hour < 12 else "PM"

    hour12 = hour % 12

    if hour12 == 0:
        hour12 = 12

    return f"{hour12:02d}:{minute} {suffix}"


# ============================================================
# SUN ICON
# ============================================================

def draw_sun_icon(draw, x, y):
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
        (cx, cy - 17, cx, cy - 11),
        (cx, cy + 11, cx, cy + 17),
        (cx - 17, cy, cx - 11, cy),
        (cx + 11, cy, cx + 17, cy),
        (cx - 12, cy - 12, cx - 8, cy - 8),
        (cx + 8, cy + 8, cx + 12, cy + 12),
        (cx + 8, cy - 8, cx + 12, cy - 12),
        (cx - 12, cy + 12, cx - 8, cy + 8),
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

# Monochrome bitmap of the actual 🌙 emoji silhouette, extracted
# from the Noto Color Emoji artwork and embedded here so the
# GitHub renderer does not depend on Pillow being able to render
# color emoji fonts directly.
MOON_EMOJI_PNG_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAABwAAAAcAQAAAABaduI5AAAAWElEQVR42kXJsQ3CQBQFwbknZBEQuASXQE1U4JLohAtc0AUEBLY+ETjb0bbyPsIklICqfVW13/+cg/P68SzCRxiCOTypMmc5LHls6Kw6w9BGriKTm0vrL19QAx8ZIvI3KwAAAABJRU5ErkJggg=="
)

def draw_moon_icon(draw, x, y):
    icon_data = base64.b64decode(MOON_EMOJI_PNG_B64)

    icon = Image.open(
        BytesIO(icon_data)
    ).convert("1")

    # Invert the monochrome emoji so the moon is black
    # on a white background.
    icon = Image.eval(
        icon,
        lambda pixel: 1 - pixel
    )

    draw.bitmap(
        (x, y),
        icon,
        fill=0,
    )


# ============================================================
# BUILD SUNDAY-FIRST GRID
# ============================================================

def build_grid(days):
    if not days:
        return []

    first_date = datetime.fromisoformat(
        days[0]["date"]
    ).date()

    sunday_offset = (
        first_date.weekday() + 1
    ) % 7

    grid = [None] * sunday_offset

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

    print("Loading calendar data...")

    with open(
        INPUT_FILE,
        "r",
        encoding="utf-8",
    ) as file:
        data = json.load(file)

    days = data["days"]

    year = data["year"]
    month = data["month"]

    # ========================================================
    # PERPETUAL HINDU CALENDAR DATA
    #
    # These values now come from the calendar generator/API
    # instead of a hard-coded year/month table or calculation.
    # ========================================================

    hindu_month = data["hindu_month"]

    samvat_year = data["vikram_samvat"]

    month_hindi = hindu_month

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

    draw = ImageDraw.Draw(image)

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

    samvat_text = (
        f"विक्रम संवत {samvat_year}"
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

    # Keep both icon centers vertically aligned at the same
    # header center, and center the two timing lines around them.
    #
    # The sun icon starts 45px from the left edge.
    # The right edge of the moon timings is also 45px from the
    # right edge of the display (x = 755), giving equal margins.
    #
    # The moon icon is the actual Unicode character 🌙 rendered
    # monochrome with Noto Sans Symbols 2.

    draw_sun_icon(
        draw,
        48,
        35,
    )

    time_y_top = 30
    time_y_bottom = 50

    draw.text(
        (82, time_y_top),
        sunrise,
        font=time_font,
        fill=0,
    )

    draw.text(
        (82, time_y_bottom),
        sunset,
        font=time_font,
        fill=0,
    )

    draw_moon_icon(
        draw,
        635,
        35,
    )

    moon_time_right = 755

    moonrise_bbox = draw.textbbox(
        (0, 0),
        moonrise,
        font=time_font,
    )

    moonset_bbox = draw.textbbox(
        (0, 0),
        moonset,
        font=time_font,
    )

    moonrise_width = (
        moonrise_bbox[2] - moonrise_bbox[0]
    )

    moonset_width = (
        moonset_bbox[2] - moonset_bbox[0]
    )

    draw.text(
        (
            moon_time_right - moonrise_width - moonrise_bbox[0],
            time_y_top,
        ),
        moonrise,
        font=time_font,
        fill=0,
    )

    draw.text(
        (
            moon_time_right - moonset_width - moonset_bbox[0],
            time_y_bottom,
        ),
        moonset,
        font=time_font,
        fill=0,
    )

    # ========================================================
    # EDGE-TO-EDGE CALENDAR GEOMETRY
    #
    # Full 800px width.
    #
    # NO left outer vertical line.
    # NO right outer vertical line.
    #
    # Only six internal vertical separators.
    # ========================================================

    grid_x = 0
    grid_y = 91
    grid_w = WIDTH

    weekday_h = 30

    calendar_bottom = 477

    calendar_height = (
        calendar_bottom
        - grid_y
        - weekday_h
    )

    # Seven columns distributed across exactly 800 pixels.
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

        x1 = column_edges[column]
        x2 = column_edges[column + 1]

        draw.rectangle(
            (
                x1,
                grid_y,
                x2 - 1,
                grid_y + weekday_h - 1,
            ),
            fill=0,
        )

        center_text(
            draw,
            (
                x1,
                grid_y,
                x2,
                grid_y + weekday_h,
            ),
            weekday,
            weekday_font,
            fill=1,
        )

    # ========================================================
    # BUILD CALENDAR
    # ========================================================

    grid = build_grid(days)

    row_count = len(grid)

    cell_h = (
        calendar_height
        // row_count
    )

    body_top = (
        grid_y
        + weekday_h
    )

    # ========================================================
    # CALENDAR CELLS
    #
    # IMPORTANT:
    #
    # We draw the cell contents FIRST.
    #
    # Grid lines are intentionally NOT drawn yet.
    # This is what allows the final grid lines to remain
    # visible over today's black highlight.
    # ========================================================

    for row_index, row in enumerate(
        grid
    ):

        if row_index == row_count - 1:
            row_y2 = calendar_bottom
        else:
            row_y2 = (
                body_top
                + (row_index + 1)
                * cell_h
            )

        y = (
            body_top
            + row_index * cell_h
        )

        actual_cell_h = (
            row_y2
            - y
        )

        for column, item in enumerate(
            row
        ):

            cell_left = column_edges[column]
            cell_right = column_edges[column + 1]

            if item is None:
                continue

            item_date = item["date"]

            is_target = (
                item_date
                == target_date
            )

            # =================================================
            # TARGET DAY BLACK HIGHLIGHT
            #
            # Leave a 1px white gap around the highlight.
            # The actual grid lines will be drawn afterward.
            # =================================================

            if is_target:

                draw.rectangle(
                    (
                        cell_left + 4,
                        y + 4,
                        cell_right - 4,
                        row_y2 - 4,
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
                str(item["day"]),
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

            tithi_bbox = draw.textbbox(
                (0, 0),
                tithi,
                font=tithi_font,
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

            if tithi_x < minimum_tithi_x:
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

                festival_bbox = draw.textbbox(
                    (0, 0),
                    festival_text,
                    font=festival_font,
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
                        actual_cell_h - 23,
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
    # FINAL HORIZONTAL GRID LINES
    #
    # These are drawn AFTER all cell contents and AFTER the
    # black target-day highlight.
    #
    # Therefore the highlight can NEVER cover these lines.
    #
    # Every horizontal line is exactly 1px.
    # ========================================================

    for row_index in range(
        row_count + 1
    ):

        if row_index == row_count:

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
    # FINAL INTERNAL VERTICAL GRID LINES
    #
    # Draw ONLY the six internal separators.
    #
    # NO line at x=0.
    # NO line at x=799.
    #
    # These are drawn AFTER the black target-day highlight.
    # Therefore they always remain clearly visible.
    # ========================================================

    for column in range(1, 7):

        x_line = column_edges[column]

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
            f"Invalid bitmap size: "
            f"{len(raw)} bytes; "
            f"expected {expected_size}"
        )

    # ========================================================
    # SAVE
    # ========================================================

    with open(
        OUTPUT_FILE,
        "wb",
    ) as file:
        file.write(raw)

    print()
    print("========================================")
    print("CALENDAR RENDER COMPLETE")
    print("========================================")
    print(
        f"Month: {month_hindi} {year}"
    )
    print(
        f"Target date: {target_date}"
    )
    print(
        f"Rows: {row_count}"
    )
    print(
        f"Column edges: {column_edges}"
    )
    print(
        f"Output: {OUTPUT_FILE}"
    )
    print(
        f"Size: {len(raw)} bytes"
    )
    print(
        "Expected: 48000 bytes"
    )
    print("========================================")


if __name__ == "__main__":
    main()

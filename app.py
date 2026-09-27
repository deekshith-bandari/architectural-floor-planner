import streamlit as st
import math
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Arc
from io import BytesIO


# ============================================================
# PAGE SETTINGS
# ============================================================

st.set_page_config(
    page_title="ArchPlan AI",
    page_icon="🏠",
    layout="wide"
)


# ============================================================
# CSS - LIGHT + DARK THEME SUPPORT
# ============================================================

st.markdown(
    """
    <style>

    /* Main background */
    .stApp {
        background-color: #f5f7fa;
    }

    /* Main title */
    .main-title {
        background: linear-gradient(135deg, #0f172a, #1e3a8a);
        padding: 30px;
        border-radius: 20px;
        color: white;
        margin-bottom: 25px;
    }

    .main-title h1 {
        font-size: 42px;
        margin-bottom: 5px;
        color: white !important;
    }

    .main-title p {
        font-size: 17px;
        color: #dbeafe !important;
    }

    /* Section headings */
    .section-title {
        font-size: 28px;
        font-weight: bold;
        color: #172554;
        margin-top: 15px;
        margin-bottom: 15px;
    }

    /* Dark mode readability */
    @media (prefers-color-scheme: dark) {

        .stApp {
            background-color: #0e1117;
        }

        .section-title {
            color: #dbeafe !important;
        }

        h1, h2, h3, h4, h5, h6 {
            color: #f8fafc !important;
        }

        p, label, span, div {
            color: inherit;
        }

        .stMarkdown p {
            color: #e5e7eb;
        }

        [data-testid="stMetricLabel"] {
            color: #cbd5e1 !important;
        }

        [data-testid="stMetricValue"] {
            color: #f8fafc !important;
        }

        .stNumberInput label,
        .stSelectbox label,
        .stRadio label,
        .stCheckbox label {
            color: #f8fafc !important;
        }

        input {
            color: #f8fafc !important;
        }

        .stAlert {
            color: #f8fafc !important;
        }
    }

    /* Navigation buttons */
    .nav-note {
        text-align: center;
        color: #64748b;
        margin-bottom: 15px;
    }

    /* Footer */
    .footer {
        text-align: center;
        padding: 25px;
        color: #64748b;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# HEADER
# ============================================================

st.markdown(
    """
    <div class="main-title">

        <h1>🏠 ArchPlan AI</h1>

        <p>
        Automated Residential Architectural Planning System
        </p>

        <p>
        Generate conceptual residential floor plans based on
        plot dimensions, room requirements, orientation and
        Vastu-based zoning.
        </p>

    </div>
    """,
    unsafe_allow_html=True
)


# ============================================================
# SESSION STATE
# ============================================================

if "page" not in st.session_state:
    st.session_state.page = "plot"

if "plot" not in st.session_state:
    st.session_state.plot = None

if "rooms" not in st.session_state:
    st.session_state.rooms = {}

if "custom" not in st.session_state:
    st.session_state.custom = {}

if "generated" not in st.session_state:
    st.session_state.generated = False


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def go_to(page_name):
    st.session_state.page = page_name


def triangle_area(a, b, c):
    """Calculate triangle area using Heron's formula."""

    s = (a + b + c) / 2

    value = s * (s - a) * (s - b) * (s - c)

    if value <= 0:
        return 0.0

    return math.sqrt(value)


def parse_dimension(value):
    """
    Convert strings such as:
    1000 × 2100 mm
    into metres.
    """

    try:
        first = value.split("×")[0].strip()
        return float(first) / 1000.0
    except Exception:
        return 1.0


def room_enabled(room_name, rooms):
    """Check whether a room should be shown."""

    if room_name == "Master Bedroom":
        return rooms.get("master_type", "Master Bedroom") in [
            "Master Bedroom",
            "Master Bedroom + Attached Bathroom"
        ]

    if room_name == "Kids Bedroom":
        return rooms.get("kids_type", "Kids Bedroom") in [
            "Kids Bedroom",
            "Kids Bedroom + Attached Bathroom"
        ]

    if room_name == "Guest Bedroom":
        return rooms.get("additional_type", "") in [
            "Guest Bedroom",
            "Guest Bedroom + Attached Bathroom"
        ]

    if room_name == "Master Toilet":
        return rooms.get("master_type") == \
            "Master Bedroom + Attached Bathroom"

    if room_name == "Kids Bathroom":
        return rooms.get("kids_type") == \
            "Kids Bedroom + Attached Bathroom"

    if room_name == "Guest Bathroom":
        return rooms.get("additional_type") == \
            "Guest Bedroom + Attached Bathroom"

    if room_name == "Store Room":
        return rooms.get("store_room", False)

    if room_name == "Pooja Room":
        return rooms.get("pooja_room", False)

    if room_name == "Parking":
        return rooms.get("parking", False)

    if room_name == "Staircase":
        return rooms.get("staircase", False)

    return True


# ============================================================
# VASTU ZONES
# ============================================================

VASTU_RULES = {
    "North": [
        "Living Room",
        "Office Room"
    ],

    "North-East": [
        "Pooja Room",
        "Service Room"
    ],

    "East": [
        "Hall",
        "Balcony",
        "Porch",
        "Veranda"
    ],

    "South-East": [
        "Kitchen",
        "Bathroom",
        "Staircase",
        "Water Storage Sump"
    ],

    "South": [
        "Overhead Tank",
        "Staircase"
    ],

    "South-West": [
        "Master Bedroom",
        "Staircase",
        "Store Room",
        "Bathroom"
    ],

    "West": [
        "Dining",
        "Study Room",
        "Kids Bedroom",
        "Staircase"
    ],

    "North-West": [
        "Guest Bedroom",
        "Kitchen",
        "Living Room"
    ],

    "Center": [
        "Hall"
    ]
}


# ============================================================
# GET VASTU POSITION
# ============================================================

def get_vastu_position(room_name):

    for direction, rooms in VASTU_RULES.items():

        for item in rooms:

            if item.lower() == room_name.lower():

                return direction

    return "Flexible"


# ============================================================
# ROOM SIZE GENERATION
# ============================================================

def get_room_sizes(option_number):

    # Different room dimensions for each plan.
    # All dimensions are in metres.

    variations = [

        {
            "Hall": (4.0, 5.0),
            "Kitchen": (3.0, 3.5),
            "Master Bedroom": (4.0, 5.0),
            "Master Toilet": (1.8, 2.4),
            "Kids Bedroom": (3.5, 4.0),
            "Kids Bathroom": (1.5, 2.2),
            "Guest Bedroom": (3.5, 4.0),
            "Guest Bathroom": (1.5, 2.2),
            "Common Toilet": (1.5, 2.0),
            "Pooja Room": (1.5, 1.5),
            "Store Room": (1.5, 2.0),
            "Parking": (3.0, 5.0),
            "Staircase": (2.5, 4.0)
        },

        {
            "Hall": (4.5, 4.0),
            "Kitchen": (3.2, 3.5),
            "Master Bedroom": (4.5, 4.5),
            "Master Toilet": (1.8, 2.3),
            "Kids Bedroom": (3.2, 4.2),
            "Kids Bathroom": (1.5, 2.0),
            "Guest Bedroom": (3.2, 4.0),
            "Guest Bathroom": (1.5, 2.0),
            "Common Toilet": (1.5, 2.0),
            "Pooja Room": (1.4, 1.6),
            "Store Room": (1.6, 2.0),
            "Parking": (3.0, 5.2),
            "Staircase": (2.5, 3.8)
        },

        {
            "Hall": (5.0, 4.0),
            "Kitchen": (3.0, 4.0),
            "Master Bedroom": (5.0, 4.0),
            "Master Toilet": (2.0, 2.2),
            "Kids Bedroom": (4.0, 4.0),
            "Kids Bathroom": (1.5, 2.2),
            "Guest Bedroom": (4.0, 3.5),
            "Guest Bathroom": (1.5, 2.2),
            "Common Toilet": (1.5, 2.0),
            "Pooja Room": (1.5, 1.5),
            "Store Room": (1.5, 2.2),
            "Parking": (3.0, 5.0),
            "Staircase": (2.6, 4.0)
        },

        {
            "Hall": (4.0, 4.5),
            "Kitchen": (3.5, 3.5),
            "Master Bedroom": (4.5, 5.0),
            "Master Toilet": (2.0, 2.4),
            "Kids Bedroom": (3.5, 4.5),
            "Kids Bathroom": (1.6, 2.2),
            "Guest Bedroom": (3.5, 4.0),
            "Guest Bathroom": (1.5, 2.0),
            "Common Toilet": (1.5, 2.0),
            "Pooja Room": (1.4, 1.5),
            "Store Room": (1.5, 2.0),
            "Parking": (3.0, 5.0),
            "Staircase": (2.5, 4.0)
        },

        {
            "Hall": (4.5, 5.0),
            "Kitchen": (3.0, 3.5),
            "Master Bedroom": (4.0, 5.0),
            "Master Toilet": (1.8, 2.5),
            "Kids Bedroom": (3.5, 4.5),
            "Kids Bathroom": (1.5, 2.2),
            "Guest Bedroom": (3.5, 4.2),
            "Guest Bathroom": (1.5, 2.0),
            "Common Toilet": (1.5, 2.0),
            "Pooja Room": (1.5, 1.6),
            "Store Room": (1.6, 2.0),
            "Parking": (3.0, 5.0),
            "Staircase": (2.5, 4.0)
        }
    ]

    return variations[(option_number - 1) % 5]


# ============================================================
# CREATE ROOM LIST
# ============================================================

def get_active_rooms(rooms, option_number):

    sizes = get_room_sizes(option_number)

    active = []

    # Fixed rooms
    active.append("Hall")
    active.append("Kitchen")
    active.append("Common Toilet")

    # Bedrooms
    if room_enabled("Master Bedroom", rooms):
        active.append("Master Bedroom")

    if room_enabled("Master Toilet", rooms):
        active.append("Master Toilet")

    if room_enabled("Kids Bedroom", rooms):
        active.append("Kids Bedroom")

    if room_enabled("Kids Bathroom", rooms):
        active.append("Kids Bathroom")

    if room_enabled("Guest Bedroom", rooms):
        active.append("Guest Bedroom")

    if room_enabled("Guest Bathroom", rooms):
        active.append("Guest Bathroom")

    # Optional
    if rooms.get("store_room", False):
        active.append("Store Room")

    if rooms.get("pooja_room", False):
        active.append("Pooja Room")

    # Other requirements
    if rooms.get("parking", False):
        active.append("Parking")

    if rooms.get("staircase", False):
        active.append("Staircase")

    return [(room, sizes.get(room, (3.0, 3.0))) for room in active]


# ============================================================
# CAD-STYLE DRAWING ENGINE
# ============================================================

# The generator below deliberately draws the plan as a wall network
# instead of a collection of thin room rectangles.
# - Outer and inner wall thickness are visible.
# - Doors create real openings in the wall and show the swing arc.
# - Attached bathrooms are carved INSIDE the bedroom footprint.
# - Windows are drawn only on the four external walls.
# ============================================================


def _draw_wall_segment(ax, x1, y1, x2, y2, linewidth=7):
    """
    Draw a wall as a strong outer line plus a fine parallel inner line.
    This gives the plan the double-line wall appearance of a CAD drawing
    without making the walls look like solid black blocks.
    """
    ax.plot(
        [x1, x2], [y1, y2],
        color="black",
        linewidth=linewidth,
        solid_capstyle="butt",
        zorder=5
    )

    # White inset line creates the visible wall thickness.
    inset = max(0.035, linewidth / 180)

    if abs(y2 - y1) < 1e-9:       # horizontal
        mid_y = (y1 + y2) / 2
        ax.plot(
            [x1, x2],
            [mid_y + inset, mid_y + inset],
            color="white",
            linewidth=max(1.0, linewidth - 2.2),
            solid_capstyle="butt",
            zorder=6
        )
        ax.plot(
            [x1, x2],
            [mid_y - inset, mid_y - inset],
            color="black",
            linewidth=0.8,
            solid_capstyle="butt",
            zorder=7
        )
    else:                        # vertical
        mid_x = (x1 + x2) / 2
        ax.plot(
            [mid_x + inset, mid_x + inset],
            [y1, y2],
            color="white",
            linewidth=max(1.0, linewidth - 2.2),
            solid_capstyle="butt",
            zorder=6
        )
        ax.plot(
            [mid_x - inset, mid_x - inset],
            [y1, y2],
            color="black",
            linewidth=0.8,
            solid_capstyle="butt",
            zorder=7
        )


def _mask_wall(ax, x1, y1, x2, y2, linewidth=11):
    """White-out a small wall section to create an opening."""
    ax.plot([x1, x2], [y1, y2], color="white",
            linewidth=linewidth, solid_capstyle="butt", zorder=8)


def draw_wall_rect(ax, x, y, w, h, wall_lw=7,
                   door=None, windows=None):
    """
    Draw a rectangular room boundary with optional wall openings.

    door:
        {"side": "bottom/top/left/right", "center": float, "width": float}
        center is measured along the selected side.
    windows:
        list of {"side": ..., "center": ..., "width": ...}
        Used mainly for special external-wall rooms. The main external
        windows are handled separately by draw_external_windows().
    """
    windows = windows or []

    # Base walls
    _draw_wall_segment(ax, x, y, x + w, y, wall_lw)             # bottom
    _draw_wall_segment(ax, x, y + h, x + w, y + h, wall_lw)     # top
    _draw_wall_segment(ax, x, y, x, y + h, wall_lw)             # left
    _draw_wall_segment(ax, x + w, y, x + w, y + h, wall_lw)     # right

    openings = []
    if door:
        openings.append(("door", door))
    for win in windows:
        openings.append(("window", win))

    # Cut openings from walls
    for kind, op in openings:
        side = op["side"]
        center = op["center"]
        ow = op["width"]

        if side in ("bottom", "top"):
            x1 = center - ow / 2
            x2 = center + ow / 2
            yy = y if side == "bottom" else y + h
            _mask_wall(ax, x1, yy, x2, yy, wall_lw + 3)
        else:
            y1 = center - ow / 2
            y2 = center + ow / 2
            xx = x if side == "left" else x + w
            _mask_wall(ax, xx, y1, xx, y2, wall_lw + 3)

    # Door symbols are drawn after the wall opening.
    if door:
        draw_door(
            ax,
            x, y, w, h,
            side=door["side"],
            center=door["center"],
            width=door["width"],
            swing=door.get("swing", "in")
        )

    # Window symbols
    for win in windows:
        draw_window(
            ax,
            x, y, w, h,
            side=win["side"],
            center=win["center"],
            width=win["width"]
        )


def draw_door(ax, x, y, w, h, side="bottom",
              center=None, width=0.9, swing="in"):
    """Draw a visible door leaf + opening arc on any wall."""
    width = min(width, max(0.55, min(w, h) * 0.55))

    if side in ("bottom", "top"):
        if center is None:
            center = x + w / 2

        center = max(x + width / 2, min(x + w - width / 2, center))
        hinge_x = center - width / 2

        if side == "bottom":
            hinge_y = y
            # wall opening already exists
            ax.plot(
                [hinge_x, hinge_x],
                [hinge_y, hinge_y + width],
                color="black", linewidth=1.6, zorder=11
            )
            ax.add_patch(
                Arc(
                    (hinge_x, hinge_y),
                    width * 2, width * 2,
                    angle=0, theta1=0, theta2=90,
                    linewidth=1.2, color="black", zorder=11
                )
            )
        else:
            hinge_y = y + h
            ax.plot(
                [hinge_x, hinge_x],
                [hinge_y, hinge_y - width],
                color="black", linewidth=1.6, zorder=11
            )
            ax.add_patch(
                Arc(
                    (hinge_x, hinge_y),
                    width * 2, width * 2,
                    angle=0, theta1=270, theta2=360,
                    linewidth=1.2, color="black", zorder=11
                )
            )

    else:
        if center is None:
            center = y + h / 2

        center = max(y + width / 2, min(y + h - width / 2, center))
        hinge_y = center - width / 2

        if side == "left":
            hinge_x = x
            ax.plot(
                [hinge_x, hinge_x + width],
                [hinge_y, hinge_y],
                color="black", linewidth=1.6, zorder=11
            )
            ax.add_patch(
                Arc(
                    (hinge_x, hinge_y),
                    width * 2, width * 2,
                    angle=0, theta1=0, theta2=90,
                    linewidth=1.2, color="black", zorder=11
                )
            )
        else:
            hinge_x = x + w
            ax.plot(
                [hinge_x, hinge_x - width],
                [hinge_y, hinge_y],
                color="black", linewidth=1.6, zorder=11
            )
            ax.add_patch(
                Arc(
                    (hinge_x, hinge_y),
                    width * 2, width * 2,
                    angle=0, theta1=90, theta2=180,
                    linewidth=1.2, color="black", zorder=11
                )
            )


def draw_window(ax, x, y, w, h, side="bottom",
                center=None, width=1.2):
    """Draw a CAD-like double-line window in an existing wall opening."""
    width = min(width, max(0.7, min(w, h) * 0.45))

    if side in ("bottom", "top"):
        if center is None:
            center = x + w / 2

        center = max(x + width / 2, min(x + w - width / 2, center))
        x1 = center - width / 2
        x2 = center + width / 2

        yy = y if side == "bottom" else y + h

        # Window sill/frame
        offset = 0.045
        ax.plot([x1, x2], [yy - offset, yy - offset],
                color="black", linewidth=1.5, zorder=12)
        ax.plot([x1, x2], [yy + offset, yy + offset],
                color="black", linewidth=1.5, zorder=12)

        # Short end marks
        ax.plot([x1, x1], [yy - 0.10, yy + 0.10],
                color="black", linewidth=1.2, zorder=12)
        ax.plot([x2, x2], [yy - 0.10, yy + 0.10],
                color="black", linewidth=1.2, zorder=12)

    else:
        if center is None:
            center = y + h / 2

        center = max(y + width / 2, min(y + h - width / 2, center))
        y1 = center - width / 2
        y2 = center + width / 2

        xx = x if side == "left" else x + w
        offset = 0.045

        ax.plot([xx - offset, xx - offset], [y1, y2],
                color="black", linewidth=1.5, zorder=12)
        ax.plot([xx + offset, xx + offset], [y1, y2],
                color="black", linewidth=1.5, zorder=12)

        ax.plot([xx - 0.10, xx + 0.10], [y1, y1],
                color="black", linewidth=1.2, zorder=12)
        ax.plot([xx - 0.10, xx + 0.10], [y2, y2],
                color="black", linewidth=1.2, zorder=12)


def _fit_room_in_zone(zone_x, zone_y, zone_w, zone_h,
                      desired_w, desired_h):
    """Fit a room into a zone while preserving its requested aspect ratio."""
    desired_w = max(float(desired_w), 1.0)
    desired_h = max(float(desired_h), 1.0)

    ratio = desired_w / desired_h

    if zone_w / zone_h > ratio:
        h = zone_h
        w = h * ratio
    else:
        w = zone_w
        h = w / ratio

    x = zone_x + (zone_w - w) / 2
    y = zone_y + (zone_h - h) / 2

    return x, y, w, h


def _room_label(ax, name, x, y, w, h, room_l, room_b,
                bath=False):
    """Place a clean architectural room label."""
    if bath:
        label = name
    else:
        label = name

    # Avoid putting labels into very small attached toilets.
    if w * h < 3.0:
        fs = 7
    elif w * h < 6.0:
        fs = 8
    else:
        fs = 9

    ax.text(
        x + w / 2,
        y + h / 2 + 0.15,
        label,
        ha="center",
        va="center",
        fontsize=fs,
        fontweight="bold",
        zorder=20
    )

    if not bath:
        ax.text(
            x + w / 2,
            y + h / 2 - 0.20,
            f"{room_l:.2f} m × {room_b:.2f} m",
            ha="center",
            va="center",
            fontsize=max(fs - 2, 6),
            zorder=20
        )


def draw_attached_bathroom(ax, bedroom_x, bedroom_y,
                           bedroom_w, bedroom_h,
                           bath_w, bath_h,
                           room_name,
                           toilet_door_width,
                           position="right_bottom",
                           wall_lw=6.5):
    """
    Carve an attached bathroom INSIDE the bedroom footprint.

    The bedroom keeps its outer boundary. The bathroom is a smaller
    internal rectangle attached to one side/corner of that bedroom.
    Its door is on the internal partition, so it opens from bedroom
    into bathroom.
    """
    # Keep a small clearance from the bedroom outer wall.
    gap = 0.03

    bath_w = min(bath_w, bedroom_w * 0.42)
    bath_h = min(bath_h, bedroom_h * 0.42)

    if position == "right_bottom":
        bx = bedroom_x + bedroom_w - bath_w
        by = bedroom_y
        door_side = "left"
        door_center = by + bath_h * 0.52

    elif position == "right_top":
        bx = bedroom_x + bedroom_w - bath_w
        by = bedroom_y + bedroom_h - bath_h
        door_side = "left"
        door_center = by + bath_h * 0.48

    elif position == "left_bottom":
        bx = bedroom_x
        by = bedroom_y
        door_side = "right"
        door_center = by + bath_h * 0.52

    else:  # left_top
        bx = bedroom_x
        by = bedroom_y + bedroom_h - bath_h
        door_side = "right"
        door_center = by + bath_h * 0.48

    # The bathroom's outside edges sit exactly on the bedroom footprint
    # where appropriate. Only the internal partition needs to be added.
    if position in ("right_bottom", "right_top"):
        # Right wall and top/bottom edge are already bedroom external
        # walls. Draw only the internal partition and the necessary
        # return wall.
        partition_x = bx
        _draw_wall_segment(
            ax, partition_x, by, partition_x, by + bath_h, wall_lw
        )

        # For the corner, reinforce the top/bottom boundary only where
        # it is not already the bedroom perimeter.
        if position == "right_bottom":
            _draw_wall_segment(
                ax, bx, by + bath_h,
                bedroom_x + bedroom_w, by + bath_h, wall_lw
            )
        else:
            _draw_wall_segment(
                ax, bx, by,
                bedroom_x + bedroom_w, by, wall_lw
            )

    else:
        partition_x = bx + bath_w
        _draw_wall_segment(
            ax, partition_x, by, partition_x, by + bath_h, wall_lw
        )

        if position == "left_bottom":
            _draw_wall_segment(
                ax, bedroom_x, by + bath_h,
                partition_x, by + bath_h, wall_lw
            )
        else:
            _draw_wall_segment(
                ax, bedroom_x, by,
                partition_x, by, wall_lw
            )

    # Open the internal partition for the bathroom door.
    if door_side == "left":
        _mask_wall(
            ax,
            partition_x,
            door_center - toilet_door_width / 2,
            partition_x,
            door_center + toilet_door_width / 2,
            wall_lw + 3
        )
    else:
        _mask_wall(
            ax,
            partition_x,
            door_center - toilet_door_width / 2,
            partition_x,
            door_center + toilet_door_width / 2,
            wall_lw + 3
        )

    draw_door(
        ax,
        bx, by, bath_w, bath_h,
        side=door_side,
        center=door_center,
        width=toilet_door_width,
        swing="in"
    )

    # Bathroom label
    ax.text(
        bx + bath_w / 2,
        by + bath_h / 2,
        "ATTACHED\nTOILET",
        ha="center",
        va="center",
        fontsize=6.5,
        fontweight="bold",
        zorder=20
    )

    return bx, by, bath_w, bath_h


def draw_external_windows(ax, bx, by, bw, bh, window_width,
                          main_door_side="bottom"):
    """
    Put windows only on the external building walls.
    Each window is centred between the corners and kept away from
    the corner/door area.
    """
    ww = min(window_width, bw * 0.28, bh * 0.28)
    ww = max(ww, 0.75)

    corner_margin = max(0.45, ww * 0.65)

    # Helper: create the actual opening first, then draw the window frame.
    def external_window(side, center):
        if side in ("bottom", "top"):
            yy = by if side == "bottom" else by + bh
            x1 = center - ww / 2
            x2 = center + ww / 2
            _mask_wall(ax, x1, yy, x2, yy, 10)
        else:
            xx = bx if side == "left" else bx + bw
            y1 = center - ww / 2
            y2 = center + ww / 2
            _mask_wall(ax, xx, y1, xx, y2, 10)

        draw_window(
            ax, bx, by, bw, bh,
            side=side, center=center, width=ww
        )

    # Bottom wall - leave a clear distance from the main entrance.
    if main_door_side == "bottom":
        external_window("bottom", bx + bw * 0.20)

    # Top, left and right external walls each get a window.
    external_window("top", bx + bw * 0.70)
    external_window("left", by + bh * 0.50)
    external_window("right", by + bh * 0.50)


def _build_cad_layout(build_x, build_y, build_w, build_h,
                      active_rooms, custom):
    """
    Create a stable architectural arrangement rather than placing rooms
    on a blind 3x4 grid.

    The layout resembles a practical CAD plan:
        left side  -> bedrooms
        right side -> hall/kitchen
        upper/central -> pooja/common spaces
    """
    names = {name for name, _ in active_rooms}

    # Main zones are percentages of the usable building rectangle.
    left_x = build_x
    left_w = build_w * 0.46

    right_x = build_x + build_w * 0.54
    right_w = build_w * 0.46

    mid_x = build_x + build_w * 0.46
    mid_w = build_w * 0.08

    bottom_y = build_y
    top_y = build_y + build_h

    # Heights
    bottom_h = build_h * 0.29
    lower_mid_h = build_h * 0.25
    upper_mid_h = build_h * 0.24
    top_h = build_h * 0.22

    zones = {}

    # LEFT / BEDROOM WING
    if "Master Bedroom" in names:
        zones["Master Bedroom"] = (
            left_x,
            bottom_y,
            left_w,
            bottom_h
        )

    if "Kids Bedroom" in names:
        zones["Kids Bedroom"] = (
            left_x,
            bottom_y + bottom_h,
            left_w,
            lower_mid_h
        )

    if "Guest Bedroom" in names:
        zones["Guest Bedroom"] = (
            left_x,
            bottom_y + bottom_h + lower_mid_h,
            left_w,
            upper_mid_h
        )

    # RIGHT / PUBLIC WING
    if "Kitchen" in names:
        zones["Kitchen"] = (
            right_x,
            bottom_y,
            right_w,
            bottom_h * 0.90
        )

    if "Hall" in names:
        zones["Hall"] = (
            right_x,
            bottom_y + bottom_h * 0.90,
            right_w,
            lower_mid_h + 0.02
        )

    # TOP / FLEXIBLE ZONE
    if "Pooja Room" in names:
        zones["Pooja Room"] = (
            right_x,
            bottom_y + bottom_h + lower_mid_h,
            right_w * 0.48,
            upper_mid_h
        )

    if "Common Toilet" in names:
        zones["Common Toilet"] = (
            right_x + right_w * 0.52,
            bottom_y + bottom_h + lower_mid_h,
            right_w * 0.48,
            upper_mid_h * 0.72
        )

    if "Store Room" in names:
        zones["Store Room"] = (
            right_x + right_w * 0.52,
            bottom_y + bottom_h + lower_mid_h + upper_mid_h * 0.72,
            right_w * 0.48,
            top_h
        )

    # If there is unused space, parking/staircase get a reserved zone.
    if "Parking" in names:
        zones["Parking"] = (
            left_x,
            top_y - top_h,
            left_w * 0.55,
            top_h
        )

    if "Staircase" in names:
        zones["Staircase"] = (
            left_x + left_w * 0.55,
            top_y - top_h,
            left_w * 0.45,
            top_h
        )

    return zones


# ============================================================
# CREATE PLAN
# ============================================================

def create_plan(
    width,
    height,
    rooms,
    custom,
    option_number
):
    # ========================================================
    # FIGURE
    # ========================================================

    fig, ax = plt.subplots(figsize=(13, 10))

    # ========================================================
    # BUILDING AREA WITH SETBACK
    # ========================================================

    setback = rooms.get("setback", rooms.get("Setback", 0.30))

    build_width = width - (2 * setback)
    build_height = height - (2 * setback)

    if build_width <= 2:
        build_width = width
        setback_x = 0
    else:
        setback_x = setback

    if build_height <= 2:
        build_height = height
        setback_y = 0
    else:
        setback_y = setback

    # ========================================================
    # WALL SETTINGS
    # ========================================================

    outer_wall_mm = rooms.get("Outer Wall", 230)
    inner_wall_mm = rooms.get("Inner Wall", 115)

    # Scale line widths for a clean CAD-like visual.
    outer_lw = 6.5
    inner_lw = 4.5

    # ========================================================
    # OUTER PLOT
    # ========================================================

    ax.add_patch(
        Rectangle(
            (0, 0),
            width,
            height,
            fill=False,
            linewidth=3,
            edgecolor="black",
            zorder=1
        )
    )

    # ========================================================
    # BUILDING OUTER WALL
    # ========================================================

    bx = setback_x
    by = setback_y
    bw = build_width
    bh = build_height

    # Two visible lines represent wall thickness.
    wall_offset = max(0.08, outer_wall_mm / 1000 / 2)

    ax.add_patch(
        Rectangle(
            (bx, by),
            bw,
            bh,
            fill=False,
            linewidth=outer_lw,
            edgecolor="black",
            zorder=4
        )
    )

    ax.add_patch(
        Rectangle(
            (
                bx + wall_offset,
                by + wall_offset
            ),
            max(0.1, bw - 2 * wall_offset),
            max(0.1, bh - 2 * wall_offset),
            fill=False,
            linewidth=1.5,
            edgecolor="black",
            zorder=4
        )
    )

    # ========================================================
    # ACTIVE ROOMS
    # ========================================================

    active_rooms_all = get_active_rooms(rooms, option_number)

    # An attached toilet is NOT a separate room rectangle. It is carved
    # into its bedroom later by draw_attached_bathroom().
    attached_toilet_names = set()
    if rooms.get("master_type") == "Master Bedroom + Attached Bathroom":
        attached_toilet_names.add("Master Toilet")
    if rooms.get("kids_type") == "Kids Bedroom + Attached Bathroom":
        attached_toilet_names.add("Kids Bathroom")
    if rooms.get("additional_type") == "Guest Bedroom + Attached Bathroom":
        attached_toilet_names.add("Guest Bathroom")

    active_rooms = [
        item for item in active_rooms_all
        if item[0] not in attached_toilet_names
    ]
    names = {name for name, _ in active_rooms}

    zones = _build_cad_layout(
        bx, by, bw, bh,
        active_rooms,
        custom
    )

    # ========================================================
    # DRAW ROOM WALLS
    # ========================================================

    room_rects = {}

    for room_name, (room_l, room_b) in active_rooms:
        if room_name not in zones:
            continue

        # Custom dimension
        if room_name in custom:
            room_l = custom[room_name]["length"]
            room_b = custom[room_name]["width"]

        zx, zy, zw, zh = zones[room_name]

        # Fit requested room proportions into its architectural zone.
        x, y, draw_w, draw_h = _fit_room_in_zone(
            zx + 0.03,
            zy + 0.03,
            max(0.5, zw - 0.06),
            max(0.5, zh - 0.06),
            room_l,
            room_b
        )

        room_rects[room_name] = {
            "x": x,
            "y": y,
            "w": draw_w,
            "h": draw_h,
            "room_l": room_l,
            "room_b": room_b
        }

        # Every room has a real door opening.
        door_width = parse_dimension(
            rooms.get("Room Door", "900 × 2100 mm")
        )

        if "Toilet" in room_name or "Bathroom" in room_name:
            door_width = parse_dimension(
                rooms.get("Toilet Door", "750 × 2100 mm")
            )

        # Doors are placed on the bottom wall for regular rooms.
        # Attached bathrooms get their own internal door later.
        draw_wall_rect(
            ax,
            x, y, draw_w, draw_h,
            wall_lw=inner_lw
        )

        draw_door(
            ax,
            x, y, draw_w, draw_h,
            side="bottom",
            center=x + draw_w * 0.50,
            width=door_width,
            swing="in"
        )

        # Room label. For an attached bedroom, the label is placed
        # later in the remaining bedroom area so it does not overlap
        # the attached toilet.
        is_attached_bedroom = (
            (room_name == "Master Bedroom" and
             rooms.get("master_type") == "Master Bedroom + Attached Bathroom")
            or
            (room_name == "Kids Bedroom" and
             rooms.get("kids_type") == "Kids Bedroom + Attached Bathroom")
            or
            (room_name == "Guest Bedroom" and
             rooms.get("additional_type") == "Guest Bedroom + Attached Bathroom")
        )

        if not is_attached_bedroom:
            _room_label(
                ax,
                room_name,
                x, y, draw_w, draw_h,
                room_l, room_b
            )

    # ========================================================
    # ATTACHED BATHROOMS
    # ========================================================

    toilet_width = parse_dimension(
        rooms.get("Toilet Door", "750 × 2100 mm")
    )

    attached_map = {
        "Master Bedroom": (
            "Master Bedroom + Attached Bathroom",
            "Master Toilet"
        ),
        "Kids Bedroom": (
            "Kids Bedroom + Attached Bathroom",
            "Kids Bathroom"
        ),
        "Guest Bedroom": (
            "Guest Bedroom + Attached Bathroom",
            "Guest Bathroom"
        )
    }

    for bedroom, (selection, bathroom_name) in attached_map.items():
        if bedroom not in room_rects:
            continue

        if rooms.get(
            {
                "Master Bedroom": "master_type",
                "Kids Bedroom": "kids_type",
                "Guest Bedroom": "additional_type"
            }.get(bedroom, ""),
            ""
        ) != selection:
            continue

        br = room_rects[bedroom]

        # Use the selected/generated bathroom size.
        bath_size = get_room_sizes(option_number).get(
            bathroom_name,
            (1.5, 2.2)
        )

        if bathroom_name in custom:
            bath_l = custom[bathroom_name]["length"]
            bath_b = custom[bathroom_name]["width"]
        else:
            bath_l, bath_b = bath_size

        draw_attached_bathroom(
            ax,
            br["x"],
            br["y"],
            br["w"],
            br["h"],
            bath_l,
            bath_b,
            bedroom,
            toilet_width,
            position="right_bottom",
            wall_lw=inner_lw
        )

        # Redraw the bedroom label in the remaining area so it never
        # falls underneath the attached toilet.
        bath_fraction = 0.30
        label_x = br["x"] + br["w"] * (1 - bath_fraction) / 2

        ax.text(
            label_x,
            br["y"] + br["h"] * 0.58,
            bedroom,
            ha="center",
            va="center",
            fontsize=7.5,
            fontweight="bold",
            zorder=21
        )

        ax.text(
            label_x,
            br["y"] + br["h"] * 0.48,
            f"{br['room_l']:.2f} m × {br['room_b']:.2f} m",
            ha="center",
            va="center",
            fontsize=6.5,
            zorder=21
        )

    # ========================================================
    # MAIN ENTRANCE
    # ========================================================

    main_door_width = parse_dimension(
        rooms.get("Main Door", "1000 × 2100 mm")
    )

    # Put the main entrance on the bottom external wall.
    main_center = bx + bw * 0.50
    _mask_wall(
        ax,
        main_center - main_door_width / 2,
        by,
        main_center + main_door_width / 2,
        by,
        outer_lw + 3
    )

    draw_door(
        ax,
        bx, by, bw, bh,
        side="bottom",
        center=main_center,
        width=main_door_width,
        swing="in"
    )

    ax.text(
        main_center,
        by - 0.22,
        "MAIN ENTRY",
        ha="center",
        va="top",
        fontsize=7,
        fontweight="bold",
        zorder=20
    )

    # ========================================================
    # EXTERNAL WINDOWS ONLY
    # ========================================================

    window_width = parse_dimension(
        rooms.get("Window", "1200 × 1200 mm")
    )

    draw_external_windows(
        ax,
        bx, by, bw, bh,
        window_width,
        main_door_side="bottom"
    )

    # ========================================================
    # NORTH DIRECTION
    # ========================================================

    north = rooms.get(
        "north",
        "A → B"
    )

    ax.annotate(
        f"N\n{north}",
        xy=(
            width * 0.88,
            height * 0.90
        ),
        xytext=(
            width * 0.88,
            height * 1.04
        ),
        ha="center",
        fontsize=11,
        fontweight="bold",
        arrowprops=dict(
            arrowstyle="->",
            linewidth=2,
            color="black"
        )
    )

    # ========================================================
    # PLOT DIMENSIONS
    # ========================================================

    ax.text(
        width / 2,
        -0.45,
        f"A → B: {rooms.get('AB', width):.2f} m",
        ha="center",
        fontsize=9
    )

    ax.text(
        width + 0.4,
        height / 2,
        f"B → C: {rooms.get('BC', height):.2f} m",
        rotation=90,
        va="center",
        fontsize=9
    )

    # ========================================================
    # TITLE
    # ========================================================

    ax.set_title(
        f"Residential Architectural Plan - Option {option_number}",
        fontsize=16,
        fontweight="bold"
    )

    # ========================================================
    # USER NAME
    # ========================================================

    ax.text(
        width,
        -1.25,
        "B. Dikshith",
        ha="right",
        fontsize=10,
        fontweight="bold"
    )

    # ========================================================
    # AXIS
    # ========================================================

    margin_x = max(width * 0.15, 1.2)
    margin_y = max(height * 0.20, 1.8)

    ax.set_xlim(
        -margin_x,
        width + margin_x
    )

    ax.set_ylim(
        -margin_y,
        height + margin_y
    )

    ax.set_aspect("equal")
    ax.axis("off")

    return fig


# ============================================================
# NAVIGATION HEADER
# ============================================================

st.markdown(
    """
    <div class="nav-note">
    Step-by-step residential planning workflow
    </div>
    """,
    unsafe_allow_html=True
)


# ============================================================
# PAGE 1 - PLOT INFORMATION
# ============================================================

if st.session_state.page == "plot":

    st.markdown(
        '<div class="section-title">📐 1. Plot Information</div>',
        unsafe_allow_html=True
    )

    st.write(
        "Enter the dimensions of the four-sided plot."
    )

    st.markdown("### Plot Dimensions")

    col1, col2 = st.columns(2)

    with col1:

        AB = st.number_input(
            "A → B (m)",
            min_value=1.0,
            value=10.0,
            step=0.1
        )

        BC = st.number_input(
            "B → C (m)",
            min_value=1.0,
            value=15.0,
            step=0.1
        )

        CD = st.number_input(
            "C → D (m)",
            min_value=1.0,
            value=10.0,
            step=0.1
        )

        DA = st.number_input(
            "D → A (m)",
            min_value=1.0,
            value=15.0,
            step=0.1
        )

    with col2:

        AC = st.number_input(
            "A → C (Diagonal) (m)",
            min_value=1.0,
            value=18.03,
            step=0.1
        )

        BD = st.number_input(
            "B → D (Diagonal) (m)",
            min_value=1.0,
            value=18.03,
            step=0.1
        )

        st.markdown("### 🧭 North Direction")

        north_direction = st.selectbox(
            "Which point or side is North?",
            [
                "A",
                "B",
                "C",
                "D",
                "A → B",
                "B → C",
                "C → D",
                "D → A"
            ]
        )

    # ========================================================
    # AREA
    # ========================================================

    area_1 = triangle_area(
        AB,
        BC,
        AC
    )

    area_2 = triangle_area(
        CD,
        DA,
        AC
    )

    area_m2 = area_1 + area_2

    area_sqft = area_m2 * 10.7639

    st.markdown("---")

    st.markdown("### 📊 Calculated Plot Area")

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "Area (m²)",
        f"{area_m2:.2f}"
    )

    c2.metric(
        "Area (sq.ft)",
        f"{area_sqft:.2f}"
    )

    c3.metric(
        "North",
        north_direction
    )

    # ========================================================
    # SETBACK
    # ========================================================

    st.markdown("---")

    st.markdown("### 📏 Setback")

    setback = st.number_input(
        "Setback from plot boundary (m)",
        min_value=0.0,
        value=0.30,
        step=0.05
    )

    st.info(
        "Setback can be increased according to the user's "
        "requirements. Actual statutory setbacks should be "
        "checked according to applicable local regulations."
    )

    # ========================================================
    # SAVE
    # ========================================================

    if st.button(
        "💾 Save Plot Information & Continue →",
        type="primary",
        use_container_width=True
    ):

        if area_m2 <= 0:

            st.error(
                "❌ Please enter valid plot dimensions."
            )

        else:

            st.session_state.plot = {

                "AB": AB,
                "BC": BC,
                "CD": CD,
                "DA": DA,
                "AC": AC,
                "BD": BD,

                "area_m2": area_m2,
                "area_sqft": area_sqft,

                "north": north_direction,

                "setback": setback
            }

            st.session_state.page = "rooms"

            st.rerun()


# ============================================================
# PAGE 2 - ROOM REQUIREMENTS
# ============================================================

elif st.session_state.page == "rooms":

    st.markdown(
        '<div class="section-title">🛏️ 2. Room Requirements</div>',
        unsafe_allow_html=True
    )

    st.write(
        "Select the required rooms and building standards."
    )

    # ========================================================
    # FIXED ROOMS
    # ========================================================

    st.markdown("### Fixed Requirements")

    fixed_rooms = [
        "Hall",
        "Kitchen",
        "Common Toilet"
    ]

    fixed_text = " • ".join(fixed_rooms)

    st.info(
        f"Fixed rooms: {fixed_text}"
    )

    # ========================================================
    # BEDROOMS
    # ========================================================

    st.markdown("---")

    st.markdown("### 🛏️ Bedrooms")

    master_type = st.selectbox(
        "Master Bedroom",
        [
            "Master Bedroom",
            "Master Bedroom + Attached Bathroom"
        ]
    )

    kids_type = st.selectbox(
        "Kids Bedroom",
        [
            "Kids Bedroom",
            "Kids Bedroom + Attached Bathroom"
        ]
    )

    additional_type = st.selectbox(
        "Additional Bedroom",
        [
            "None",
            "Master Bedroom",
            "Kids Bedroom",
            "Guest Bedroom",
            "Master Bedroom + Attached Bathroom",
            "Kids Bedroom + Attached Bathroom",
            "Guest Bedroom + Attached Bathroom"
        ]
    )

    # ========================================================
    # OPTIONAL ROOMS
    # ========================================================

    st.markdown("---")

    st.markdown("### 🚪 Optional Rooms")

    optional_col1, optional_col2 = st.columns(2)

    with optional_col1:

        store_room = st.checkbox(
            "Store Room"
        )

    with optional_col2:

        pooja_room = st.checkbox(
            "Pooja Room"
        )

    # ========================================================
    # OTHER REQUIREMENTS
    # ========================================================

    st.markdown("---")

    st.markdown("### 🏗️ Other Requirements")

    parking = st.selectbox(
        "Parking",
        [
            "No",
            "Yes"
        ]
    )

    staircase = st.selectbox(
        "Staircase",
        [
            "No",
            "Yes"
        ]
    )

    # ========================================================
    # BUILDING STANDARDS
    # ========================================================

    st.markdown("---")

    st.markdown("### 🧱 Building Standards")

    col1, col2, col3 = st.columns(3)

    with col1:

        outer_wall = st.number_input(
            "Outer Wall Thickness (mm)",
            min_value=100,
            max_value=500,
            value=230,
            step=10
        )

    with col2:

        inner_wall = st.number_input(
            "Inner Wall Thickness (mm)",
            min_value=75,
            max_value=300,
            value=115,
            step=5
        )

    with col3:

        partition_wall = st.number_input(
            "Partition Wall Thickness (mm)",
            min_value=50,
            max_value=200,
            value=100,
            step=5
        )

    roof_height = st.number_input(
        "Roof / Floor Height (m)",
        min_value=2.5,
        max_value=5.0,
        value=3.0,
        step=0.1
    )

    # ========================================================
    # STAIRCASE WIDTH ONLY IF YES
    # ========================================================

    staircase_width = None

    if staircase == "Yes":

        staircase_width = st.number_input(
            "Staircase Width (m)",
            min_value=0.8,
            max_value=2.0,
            value=1.0,
            step=0.1
        )

    # ========================================================
    # DOORS & WINDOWS
    # ========================================================

    st.markdown("---")

    st.markdown("### 🚪 Doors & Windows")

    col1, col2 = st.columns(2)

    with col1:

        main_door = st.selectbox(
            "Main Door",
            [
                "1000 × 2100 mm",
                "1200 × 2100 mm"
            ]
        )

        room_door = st.selectbox(
            "Room Door",
            [
                "900 × 2100 mm",
                "1000 × 2100 mm"
            ]
        )

    with col2:

        toilet_door = st.selectbox(
            "Bathroom / Toilet Door",
            [
                "750 × 2100 mm",
                "800 × 2100 mm"
            ]
        )

        window = st.selectbox(
            "Window",
            [
                "1200 × 1200 mm",
                "1500 × 1200 mm",
                "1800 × 1200 mm"
            ]
        )

    # ========================================================
    # SAVE
    # ========================================================

    if st.button(
        "💾 Save Room Requirements & Generate Plans →",
        type="primary",
        use_container_width=True
    ):

        st.session_state.rooms = {

            "master_type": master_type,
            "kids_type": kids_type,
            "additional_type": additional_type,

            "store_room": store_room,
            "pooja_room": pooja_room,

            "parking": parking == "Yes",
            "staircase": staircase == "Yes",

            "Outer Wall": outer_wall,
            "Inner Wall": inner_wall,
            "Partition Wall": partition_wall,

            "Roof Height": roof_height,

            "Staircase Width":
                staircase_width if staircase_width else 0,

            "Main Door": main_door,
            "Room Door": room_door,
            "Toilet Door": toilet_door,
            "Window": window,

            "north":
                st.session_state.plot["north"],

            "AB":
                st.session_state.plot["AB"],

            "BC":
                st.session_state.plot["BC"],

            "setback":
                st.session_state.plot["setback"]
        }

        st.session_state.page = "generate"

        st.rerun()


# ============================================================
# PAGE 3 - GENERATE PLANS
# ============================================================

elif st.session_state.page == "generate":

    st.markdown(
        '<div class="section-title">🏗️ 3. Generate Architectural Plans</div>',
        unsafe_allow_html=True
    )

    if st.session_state.plot is None:

        st.warning(
            "⚠️ Please complete Plot Information first."
        )

        if st.button("← Back to Plot Information"):

            st.session_state.page = "plot"
            st.rerun()

    elif not st.session_state.rooms:

        st.warning(
            "⚠️ Please complete Room Requirements first."
        )

        if st.button("← Back to Room Requirements"):

            st.session_state.page = "rooms"
            st.rerun()

    else:

        plot = st.session_state.plot

        rooms = st.session_state.rooms

        custom = st.session_state.custom

        # ====================================================
        # PROJECT SUMMARY
        # ====================================================

        st.markdown("### 📊 Project Summary")

        c1, c2, c3, c4 = st.columns(4)

        c1.metric(
            "Plot Area",
            f"{plot['area_sqft']:.0f} sq.ft"
        )

        c2.metric(
            "North",
            plot["north"]
        )

        c3.metric(
            "Setback",
            f"{plot['setback']:.2f} m"
        )

        c4.metric(
            "Floor Height",
            f"{rooms.get('Roof Height', 3.0):.1f} m"
        )

        # ====================================================
        # PLOT DIMENSIONS
        # ====================================================

        st.markdown("---")

        st.markdown("### 📐 Plot Dimensions")

        d1, d2, d3, d4 = st.columns(4)

        d1.metric(
            "A → B",
            f"{plot['AB']:.2f} m"
        )

        d2.metric(
            "B → C",
            f"{plot['BC']:.2f} m"
        )

        d3.metric(
            "C → D",
            f"{plot['CD']:.2f} m"
        )

        d4.metric(
            "D → A",
            f"{plot['DA']:.2f} m"
        )

        # ====================================================
        # VASTU
        # ========================================================

        st.markdown("---")

        st.markdown("### 🧭 Vastu Planning")

        st.info(
            """
            The conceptual plans use the Vastu zoning rules
            specified for this project.

            North:
            Living Room / Office Room

            North-East:
            Pooja Room / Service Room

            East:
            Hall / Balcony / Porch / Veranda

            South-East:
            Kitchen / Bathroom / Staircase / Water Storage Sump

            South:
            Overhead Tank / Staircase

            South-West:
            Master Bedroom / Staircase / Store Room / Bathroom

            West:
            Dining / Study Room / Kids Bedroom / Staircase

            North-West:
            Guest Bedroom / Kitchen / Living Room

            Center:
            Hall
            """
        )

        # ====================================================
        # GENERATE 5 PLANS
        # ====================================================

        if st.button(
            "🏠 GENERATE 5 ARCHITECTURAL PLANS",
            type="primary",
            use_container_width=True
        ):

            st.session_state.generated = True

        if st.session_state.generated:

            # ------------------------------------------------
            # Working dimensions
            # ------------------------------------------------

            width = max(
                plot["AB"],
                plot["CD"]
            )

            height = max(
                plot["BC"],
                plot["DA"]
            )

            st.success(
                "✅ 5 conceptual plan options generated."
            )

            # =================================================
            # FIVE OPTIONS
            # =================================================

            for i in range(1, 6):

                st.markdown(
                    f"## 🏠 Plan Option {i}"
                )

                st.caption(
                    f"Room dimensions vary for Option {i} "
                    f"while using the selected Vastu zoning."
                )

                fig = create_plan(
                    width,
                    height,
                    rooms,
                    custom,
                    i
                )

                st.pyplot(
                    fig,
                    use_container_width=True
                )

                # =================================================
                # DOOR / WINDOW SCHEDULE
                # =================================================

                st.markdown(
                    "### 🚪 Door & Window Schedule"
                )

                schedule_col1, schedule_col2 = st.columns(2)

                with schedule_col1:

                    st.write(
                        f"**Main Door:** "
                        f"{rooms['Main Door']}"
                    )

                    st.write(
                        f"**Room Door:** "
                        f"{rooms['Room Door']}"
                    )

                    st.write(
                        f"**Bathroom / Toilet Door:** "
                        f"{rooms['Toilet Door']}"
                    )

                with schedule_col2:

                    st.write(
                        f"**Window:** "
                        f"{rooms['Window']}"
                    )

                    st.write(
                        f"**Outer Wall:** "
                        f"{rooms['Outer Wall']} mm"
                    )

                    st.write(
                        f"**Inner Wall:** "
                        f"{rooms['Inner Wall']} mm"
                    )

                    st.write(
                        f"**Partition Wall:** "
                        f"{rooms['Partition Wall']} mm"
                    )

                # =================================================
                # DOWNLOAD
                # =================================================

                buffer = BytesIO()

                fig.savefig(
                    buffer,
                    format="png",
                    dpi=300,
                    bbox_inches="tight"
                )

                buffer.seek(0)

                st.download_button(
                    label=f"⬇️ Download Plan {i}",
                    data=buffer.getvalue(),
                    file_name=f"ArchPlan_Option_{i}.png",
                    mime="image/png",
                    key=f"download_plan_{i}"
                )

                plt.close(fig)
# =================================================
            # CUSTOMIZE BUTTON
            # =================================================

            st.markdown("---")

            st.markdown(
                "### 🎨 Customize Your Plan"
            )

            st.write(
                "Want to change individual room dimensions?"
            )

            if st.button(
                "🎨 CUSTOMIZE YOUR PLAN",
                use_container_width=True
            ):

                st.session_state.page = "customize"

                st.rerun()


# ============================================================
# PAGE 4 - CUSTOMIZE
# ============================================================

elif st.session_state.page == "customize":

    st.markdown(
        '<div class="section-title">🎨 Customize Your Plan</div>',
        unsafe_allow_html=True
    )

    st.write(
        "Enter your preferred room dimensions for individual rooms."
    )

    st.info(
        "Select Yes for a room if you want to manually change "
        "its dimensions. Dimensions must be entered in metres."
    )

    plot = st.session_state.plot

    rooms = st.session_state.rooms

    # ========================================================
    # AVAILABLE ROOMS
    # ========================================================

    customize_rooms = [
        "Hall",
        "Master Bedroom",
        "Master Toilet",
        "Kids Bedroom",
        "Kids Bathroom",
        "Guest Bedroom",
        "Guest Bathroom",
        "Kitchen",
        "Common Toilet",
        "Store Room",
        "Pooja Room",
        "Parking",
        "Staircase"
    ]

    # ========================================================
    # ROOM CUSTOMIZATION
    # ========================================================

    for room in customize_rooms:

        # Don't show rooms that aren't selected
        if room == "Store Room" and \
           not rooms.get("store_room", False):
            continue

        if room == "Pooja Room" and \
           not rooms.get("pooja_room", False):
            continue

        if room == "Parking" and \
           not rooms.get("parking", False):
            continue

        if room == "Staircase" and \
           not rooms.get("staircase", False):
            continue

        if room == "Master Toilet" and \
           not room_enabled("Master Toilet", rooms):
            continue

        if room == "Kids Bathroom" and \
           not room_enabled("Kids Bathroom", rooms):
            continue

        if room == "Guest Bedroom" and \
           not room_enabled("Guest Bedroom", rooms):
            continue

        if room == "Guest Bathroom" and \
           not room_enabled("Guest Bathroom", rooms):
            continue

        st.markdown("---")

        st.markdown(
            f"### {room}"
        )

        customize = st.radio(
            f"Customize {room}?",
            [
                "No",
                "Yes"
            ],
            horizontal=True,
            key=f"custom_yes_no_{room}"
        )

        if customize == "Yes":

            current = st.session_state.custom.get(
                room,
                {
                    "length": 3.0,
                    "width": 3.0
                }
            )

            c1, c2 = st.columns(2)

            with c1:

                length = st.number_input(
                    f"{room} Length (m)",
                    min_value=1.0,
                    max_value=20.0,
                    value=float(
                        current["length"]
                    ),
                    step=0.1,
                    key=f"custom_length_{room}"
                )

            with c2:

                breadth = st.number_input(
                    f"{room} Width / Breadth (m)",
                    min_value=1.0,
                    max_value=20.0,
                    value=float(
                        current["width"]
                    ),
                    step=0.1,
                    key=f"custom_width_{room}"
                )

            # =================================================
            # BASIC AREA CHECK
            # =================================================

            room_area = length * breadth

            plot_area = plot["area_m2"]

            if room_area > plot_area:

                st.error(
                    f"❌ {room} dimension is larger than "
                    f"the entire plot area. "
                    f"Change the dimensions."
                )

            elif room_area > plot_area * 0.60:

                st.warning(
                    f"⚠️ {room} occupies "
                    f"{room_area:.2f} m², which is a large "
                    f"portion of the total plot area. "
                    f"Consider reducing the dimensions."
                )

            else:

                st.success(
                    f"Area: {room_area:.2f} m²"
                )

            # =================================================
            # SAVE ROOM
            # =================================================

            if st.button(
                f"💾 Save {room} Dimensions",
                key=f"save_custom_{room}"
            ):

                if room_area > plot_area:

                    st.error(
                        "❌ Cannot save. "
                        "The requested room area exceeds "
                        "the total plot area."
                    )

                else:

                    st.session_state.custom[room] = {

                        "length": length,
                        "width": breadth
                    }

                    st.success(
                        f"✅ {room} dimensions saved."
                    )

    # ========================================================
    # CURRENT CUSTOM DIMENSIONS
    # ========================================================

    if st.session_state.custom:

        st.markdown("---")

        st.markdown(
            "### 📐 Current Customized Dimensions"
        )

        for room, values in \
                st.session_state.custom.items():

            st.write(
                f"**{room}:** "
                f"{values['length']:.2f} m × "
                f"{values['width']:.2f} m"
            )

    # ========================================================
    # BUTTONS
    # ========================================================

    st.markdown("---")

    c1, c2 = st.columns(2)

    with c1:

        if st.button(
            "← Back to Generated Plans",
            use_container_width=True
        ):

            st.session_state.page = "generate"

            st.rerun()

    with c2:

        if st.button(
            "🔄 Regenerate 5 Plans",
            type="primary",
            use_container_width=True
        ):

            st.session_state.generated = True

            st.session_state.page = "generate"

            st.rerun()


# ============================================================
# FOOTER
# ============================================================

st.markdown("---")

st.markdown(
    """
    <div class="footer">

    🏠 <b>ArchPlan AI</b><br>

    Conceptual Residential Architectural Planning System<br><br>

    <small>
    B. Dikshith
    </small><br><br>

    <small>
    This application generates conceptual layouts.
    Final architectural, structural and statutory drawings
    should be prepared and verified by qualified professionals.
    </small>

    </div>
    """,
    unsafe_allow_html=True
)
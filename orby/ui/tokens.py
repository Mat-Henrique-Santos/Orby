from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ColorPalette:
    # Cores Principais da Marca (Frutiger Aero Aqua)
    PRIMARY: str
    PRIMARY_HOVER: str
    PRIMARY_ACTIVE: str
    PRIMARY_LIGHT: str
    PRIMARY_CONTAINER: str

    # Cores Secundárias e Acentos
    SECONDARY: str
    SECONDARY_HOVER: str
    ACCENT_CYAN: str
    ACCENT_TEAL: str

    # Cores Semânticas de Estado
    SUCCESS: str
    SUCCESS_HOVER: str
    SUCCESS_LIGHT: str
    SUCCESS_TEXT: str

    WARNING: str
    WARNING_HOVER: str
    WARNING_LIGHT: str
    WARNING_TEXT: str

    ERROR: str
    ERROR_HOVER: str
    ERROR_LIGHT: str
    ERROR_TEXT: str

    INFO: str
    INFO_LIGHT: str
    INFO_TEXT: str

    # Superfícies e Vidros (Aero Glass)
    WINDOW_BG: str
    WINDOW_GRADIENT_START: str
    WINDOW_GRADIENT_MID1: str
    WINDOW_GRADIENT_MID2: str
    WINDOW_GRADIENT_END: str

    SURFACE: str
    SURFACE_ELEVATED: str
    SURFACE_TRANSLUCENT: str
    SURFACE_INPUT: str
    SURFACE_INPUT_FOCUS: str
    SURFACE_HOVER: str
    SURFACE_ACTIVE: str

    # Bordas e Brilhos Especulares
    BORDER: str
    BORDER_LIGHT: str
    BORDER_GLOW: str
    BORDER_FOCUS: str
    BORDER_SUBTLE: str

    # Tipografia e Contrastes
    TEXT_PRIMARY: str
    TEXT_SECONDARY: str
    TEXT_MUTED: str
    TEXT_ON_PRIMARY: str
    TEXT_ON_DARK: str
    TEXT_ON_LIGHT: str

    # Tabelas
    TABLE_BG: str
    TABLE_ALT_BG: str
    TABLE_HEADER_BG_START: str
    TABLE_HEADER_BG_END: str
    TABLE_HEADER_TEXT: str
    TABLE_SELECTION_BG: str
    TABLE_SELECTION_TEXT: str
    TABLE_GRID: str

    # Scrollbars
    SCROLLBAR_BG: str
    SCROLLBAR_HANDLE_START: str
    SCROLLBAR_HANDLE_END: str
    SCROLLBAR_HANDLE_HOVER: str


# ==========================================
# TEMA LIGHT (Corporate Aero Glass)
# ==========================================
LIGHT_PALETTE = ColorPalette(
    PRIMARY="#0284c7",
    PRIMARY_HOVER="#0369a1",
    PRIMARY_ACTIVE="#075985",
    PRIMARY_LIGHT="#e0f2fe",
    PRIMARY_CONTAINER="rgba(2, 132, 199, 0.10)",

    SECONDARY="#0369a1",
    SECONDARY_HOVER="#075985",
    ACCENT_CYAN="#0284c7",
    ACCENT_TEAL="#0d9488",

    SUCCESS="#059669",
    SUCCESS_HOVER="#047857",
    SUCCESS_LIGHT="#ecfdf5",
    SUCCESS_TEXT="#065f46",

    WARNING="#d97706",
    WARNING_HOVER="#b45309",
    WARNING_LIGHT="#fffbeb",
    WARNING_TEXT="#78350f",

    ERROR="#dc2626",
    ERROR_HOVER="#b91c1c",
    ERROR_LIGHT="#fef2f2",
    ERROR_TEXT="#7f1d1d",

    INFO="#0284c7",
    INFO_LIGHT="#f0f9ff",
    INFO_TEXT="#075985",

    WINDOW_BG="#e6edf5",
    WINDOW_GRADIENT_START="#f4f7fb",
    WINDOW_GRADIENT_MID1="#e8f0f8",
    WINDOW_GRADIENT_MID2="#dfeaf4",
    WINDOW_GRADIENT_END="#d4e4f0",

    SURFACE="rgba(255, 255, 255, 0.94)",
    SURFACE_ELEVATED="#ffffff",
    SURFACE_TRANSLUCENT="rgba(255, 255, 255, 0.78)",
    SURFACE_INPUT="#ffffff",
    SURFACE_INPUT_FOCUS="#ffffff",
    SURFACE_HOVER="rgba(2, 132, 199, 0.06)",
    SURFACE_ACTIVE="rgba(2, 132, 199, 0.12)",

    BORDER="#cbd5e1",
    BORDER_LIGHT="#e2e8f0",
    BORDER_GLOW="#0284c7",
    BORDER_FOCUS="#0284c7",
    BORDER_SUBTLE="#e2e8f0",

    TEXT_PRIMARY="#0f172a",
    TEXT_SECONDARY="#334155",
    TEXT_MUTED="#64748b",
    TEXT_ON_PRIMARY="#ffffff",
    TEXT_ON_DARK="#ffffff",
    TEXT_ON_LIGHT="#0f172a",

    TABLE_BG="#ffffff",
    TABLE_ALT_BG="#f8fafc",
    TABLE_HEADER_BG_START="#f8fafc",
    TABLE_HEADER_BG_END="#edf2f7",
    TABLE_HEADER_TEXT="#0f172a",
    TABLE_SELECTION_BG="#e0f2fe",
    TABLE_SELECTION_TEXT="#0369a1",
    TABLE_GRID="#e2e8f0",

    SCROLLBAR_BG="rgba(241, 245, 249, 0.7)",
    SCROLLBAR_HANDLE_START="#cbd5e1",
    SCROLLBAR_HANDLE_END="#94a3b8",
    SCROLLBAR_HANDLE_HOVER="#0284c7",
)


# ==========================================
# TEMA DARK (Midnight Aero Glass)
# ==========================================
DARK_PALETTE = ColorPalette(
    PRIMARY="#38bdf8",
    PRIMARY_HOVER="#0ea5e9",
    PRIMARY_ACTIVE="#0284c7",
    PRIMARY_LIGHT="rgba(56, 189, 248, 0.15)",
    PRIMARY_CONTAINER="rgba(56, 189, 248, 0.20)",

    SECONDARY="#22d3ee",
    SECONDARY_HOVER="#06b6d4",
    ACCENT_CYAN="#38bdf8",
    ACCENT_TEAL="#2dd4bf",

    SUCCESS="#34d399",
    SUCCESS_HOVER="#10b981",
    SUCCESS_LIGHT="rgba(52, 211, 153, 0.15)",
    SUCCESS_TEXT="#a7f3d0",

    WARNING="#fbbf24",
    WARNING_HOVER="#f59e0b",
    WARNING_LIGHT="rgba(251, 191, 36, 0.15)",
    WARNING_TEXT="#fde68a",

    ERROR="#f87171",
    ERROR_HOVER="#ef4444",
    ERROR_LIGHT="rgba(248, 113, 113, 0.15)",
    ERROR_TEXT="#fecaca",

    INFO="#38bdf8",
    INFO_LIGHT="rgba(56, 189, 248, 0.15)",
    INFO_TEXT="#bae6fd",

    WINDOW_BG="#051622",
    WINDOW_GRADIENT_START="#051622",
    WINDOW_GRADIENT_MID1="#0a2540",
    WINDOW_GRADIENT_MID2="#0f3057",
    WINDOW_GRADIENT_END="#001220",

    SURFACE="rgba(15, 23, 42, 0.80)",
    SURFACE_ELEVATED="rgba(30, 41, 59, 0.90)",
    SURFACE_TRANSLUCENT="rgba(15, 23, 42, 0.60)",
    SURFACE_INPUT="#0f172a",
    SURFACE_INPUT_FOCUS="rgba(30, 41, 59, 0.95)",
    SURFACE_HOVER="rgba(30, 41, 59, 0.70)",
    SURFACE_ACTIVE="rgba(56, 189, 248, 0.25)",

    BORDER="rgba(56, 189, 248, 0.40)",
    BORDER_LIGHT="rgba(125, 211, 252, 0.60)",
    BORDER_GLOW="#38bdf8",
    BORDER_FOCUS="#38bdf8",
    BORDER_SUBTLE="rgba(51, 65, 85, 0.80)",

    TEXT_PRIMARY="#f8fafc",
    TEXT_SECONDARY="#cbd5e1",
    TEXT_MUTED="#94a3b8",
    TEXT_ON_PRIMARY="#ffffff",
    TEXT_ON_DARK="#f8fafc",
    TEXT_ON_LIGHT="#0f172a",

    TABLE_BG="rgba(15, 23, 42, 0.85)",
    TABLE_ALT_BG="rgba(30, 41, 59, 0.75)",
    TABLE_HEADER_BG_START="#1e293b",
    TABLE_HEADER_BG_END="#0f172a",
    TABLE_HEADER_TEXT="#38bdf8",
    TABLE_SELECTION_BG="#0284c7",
    TABLE_SELECTION_TEXT="#ffffff",
    TABLE_GRID="#1e293b",

    SCROLLBAR_BG="rgba(15, 23, 42, 0.40)",
    SCROLLBAR_HANDLE_START="#0284c7",
    SCROLLBAR_HANDLE_END="#0369a1",
    SCROLLBAR_HANDLE_HOVER="#38bdf8",
)


# ==========================================
# ESPACAMENTOS (Spacing Tokens)
# ==========================================
@dataclass(frozen=True)
class SpacingTokens:
    NONE: int = 0
    XXS: int = 2
    XS: int = 4
    SM: int = 8
    MD: int = 12
    LG: int = 16
    XL: int = 20
    XXL: int = 24
    XXXL: int = 32
    SECTION: int = 40


SPACING = SpacingTokens()


# ==========================================
# BORDAS E RAIOS (Border Radius Tokens)
# ==========================================
@dataclass(frozen=True)
class RadiusTokens:
    NONE: int = 0
    XS: int = 4
    SM: int = 8
    MD: int = 12
    LG: int = 16
    XL: int = 18
    XXL: int = 20
    PILL: int = 999


RADIUS = RadiusTokens()


# ==========================================
# TIPOGRAFIA (Typography Tokens)
# ==========================================
@dataclass(frozen=True)
class TypographyTokens:
    FONT_FAMILY: str = '"Segoe UI"'
    FONT_FAMILY_MONO: str = '"Consolas"'

    # Tamanhos em pixels (conforme solicitado)
    SIZE_KPI: int = 28
    SIZE_TITLE: int = 22
    SIZE_SUBTITLE: int = 16
    SIZE_BODY: int = 13
    SIZE_SMALL: int = 12
    SIZE_CAPTION: int = 11

    # Pesos
    WEIGHT_NORMAL: int = 400
    WEIGHT_MEDIUM: int = 500
    WEIGHT_SEMIBOLD: int = 600
    WEIGHT_BOLD: int = 700
    WEIGHT_EXTRABOLD: int = 800
    WEIGHT_BLACK: int = 900


TYPOGRAPHY = TypographyTokens()


# ==========================================
# TAMANHOS E DIMENSOES PADRAO
# ==========================================
@dataclass(frozen=True)
class DimensionTokens:
    INPUT_HEIGHT: int = 36
    BUTTON_HEIGHT: int = 36
    BUTTON_SMALL_HEIGHT: int = 28
    NAV_BUTTON_HEIGHT: int = 40
    DOCK_TILE_SIZE: int = 38
    SIDEBAR_WIDTH: int = 240
    LOGO_SIZE: int = 72
    METRIC_CARD_MIN_HEIGHT: int = 115
    METRIC_CARD_MIN_WIDTH: int = 180
    TABLE_ROW_HEIGHT: int = 36
    TABLE_HEADER_HEIGHT: int = 38
    STATUS_BADGE_HEIGHT: int = 26
    STATUS_BADGE_RADIUS: int = 13


DIMENSIONS = DimensionTokens()


# ==========================================
# TAMANHOS DE ICONES
# ==========================================
@dataclass(frozen=True)
class IconSizeTokens:
    SM: int = 14
    MD: int = 18
    LG: int = 22
    XL: int = 26
    XXL: int = 32


ICON_SIZES = IconSizeTokens()

from __future__ import annotations

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication

from .tokens import (
    ColorPalette,
    DARK_PALETTE,
    DIMENSIONS,
    ICON_SIZES,
    LIGHT_PALETTE,
    RADIUS,
    SPACING,
    TYPOGRAPHY,
)

THEME_STATE = {"dark_mode": False}


def get_current_palette() -> ColorPalette:
    return DARK_PALETTE if THEME_STATE.get("dark_mode", False) else LIGHT_PALETTE


def is_dark_mode() -> bool:
    return THEME_STATE.get("dark_mode", False)


def generate_qss(c: ColorPalette) -> str:
    """Gera o StyleSheet QSS completo dinamicamente a partir dos tokens do Design System."""
    is_dark = THEME_STATE.get("dark_mode", False)
    sidebar_bg = (
        f"qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(15, 23, 42, 0.90), stop:1.0 rgba(10, 18, 35, 0.95))"
        if is_dark
        else f"qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #ffffff, stop:1.0 #f1f5f9)"
    )
    header_badge_bg = "rgba(30, 41, 59, 0.85)" if is_dark else "#ffffff"

    return f"""
/* ==========================================================================
   ORBY DESIGN SYSTEM — Frutiger Aero Corporativo + Software Moderno
   ========================================================================== */

* {{
    font-family: {TYPOGRAPHY.FONT_FAMILY};
    color: {c.TEXT_PRIMARY};
}}

QMainWindow {{
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:1,
        stop:0 {c.WINDOW_GRADIENT_START},
        stop:0.35 {c.WINDOW_GRADIENT_MID1},
        stop:0.70 {c.WINDOW_GRADIENT_MID2},
        stop:1.0 {c.WINDOW_GRADIENT_END}
    );
}}

QDialog {{
    background: {c.SURFACE_ELEVATED};
}}

QWidget#CentralWidget {{
    background: transparent;
}}

/* --- Barra Lateral (Floating Glass Dock) --- */
QFrame#Sidebar {{
    background: {sidebar_bg};
    border: 1px solid {c.BORDER};
    border-radius: {RADIUS.XXL}px;
}}

QLabel#LogoTitle {{
    font-size: 24px;
    font-weight: {TYPOGRAPHY.WEIGHT_BLACK};
    color: {c.PRIMARY};
    letter-spacing: 2px;
}}

QLabel#LogoSubtitle {{
    font-size: {TYPOGRAPHY.SIZE_CAPTION}px;
    font-weight: {TYPOGRAPHY.WEIGHT_BOLD};
    color: {c.TEXT_SECONDARY};
    text-transform: uppercase;
    letter-spacing: 1.5px;
}}

QLabel#DockSectionLabel {{
    font-size: {TYPOGRAPHY.SIZE_CAPTION - 1}px;
    font-weight: {TYPOGRAPHY.WEIGHT_EXTRABOLD};
    color: {c.TEXT_MUTED};
    letter-spacing: 1px;
}}

QLabel#VersionLabel {{
    color: {c.TEXT_MUTED};
    font-size: {TYPOGRAPHY.SIZE_CAPTION - 1}px;
    font-weight: {TYPOGRAPHY.WEIGHT_SEMIBOLD};
}}

/* --- Badges de Cabeçalho Superior --- */
QLabel#HeaderBadge {{
    background: {header_badge_bg};
    border: 1px solid {c.BORDER};
    border-radius: {RADIUS.MD}px;
    padding: {SPACING.XS}px {SPACING.MD}px;
    font-weight: {TYPOGRAPHY.WEIGHT_BOLD};
    color: {c.PRIMARY};
    font-size: {TYPOGRAPHY.SIZE_CAPTION + 0.5}px;
}}

QLabel#OnlineBadge {{
    background: {c.SUCCESS_LIGHT};
    border: 1px solid {c.SUCCESS};
    border-radius: {RADIUS.MD}px;
    padding: {SPACING.XS}px {SPACING.MD}px;
    font-weight: {TYPOGRAPHY.WEIGHT_BOLD};
    color: {c.SUCCESS_TEXT};
    font-size: {TYPOGRAPHY.SIZE_CAPTION + 0.5}px;
}}

QFrame#UserBadge {{
    background: {c.SURFACE_ELEVATED};
    border: 1px solid {c.BORDER};
    border-radius: {RADIUS.MD}px;
}}

/* --- Títulos e Subtítulos Padronizados --- */
QLabel#SectionTitle {{
    font-size: {TYPOGRAPHY.SIZE_TITLE}px;
    font-weight: {TYPOGRAPHY.WEIGHT_EXTRABOLD};
    color: {c.TEXT_PRIMARY};
}}

QLabel#SectionSubtitle {{
    font-size: {TYPOGRAPHY.SIZE_SUBTITLE}px;
    font-weight: {TYPOGRAPHY.WEIGHT_BOLD};
    color: {c.TEXT_PRIMARY};
}}

QLabel#SummaryLabel {{
    font-size: {TYPOGRAPHY.SIZE_BODY}px;
    font-weight: {TYPOGRAPHY.WEIGHT_MEDIUM};
    color: {c.TEXT_SECONDARY};
}}

QLabel#MetricTitle {{
    font-size: {TYPOGRAPHY.SIZE_BODY}px;
    font-weight: {TYPOGRAPHY.WEIGHT_BOLD};
    color: {c.PRIMARY};
}}

QLabel#MetricValue {{
    font-size: {TYPOGRAPHY.SIZE_KPI}px;
    font-weight: {TYPOGRAPHY.WEIGHT_BLACK};
    color: {c.TEXT_PRIMARY};
}}

/* --- Cartões e Painéis de Conteúdo --- */
QFrame#ContentCard, QFrame#MetricCard {{
    background: {c.SURFACE_ELEVATED};
    border: 1px solid {c.BORDER};
    border-radius: {RADIUS.LG}px;
}}

/* --- Botões de Navegação da Barra Lateral --- */
QPushButton#NavButton {{
    background: {c.SURFACE_ELEVATED};
    border: 1px solid {c.BORDER_SUBTLE};
    border-radius: {RADIUS.MD}px;
    padding: {SPACING.SM}px {SPACING.LG}px;
    font-size: {TYPOGRAPHY.SIZE_BODY}px;
    font-weight: {TYPOGRAPHY.WEIGHT_BOLD};
    color: {c.TEXT_PRIMARY};
    text-align: left;
    min-height: {DIMENSIONS.NAV_BUTTON_HEIGHT - 16}px;
}}

QPushButton#NavButton:hover {{
    background: {c.SURFACE_HOVER};
    border: 1px solid {c.PRIMARY};
    color: {c.PRIMARY};
}}

QPushButton#NavButton:checked, QPushButton#NavButton[active="true"] {{
    background: qlineargradient(
        x1:0, y1:0, x2:0, y2:1,
        stop:0 #38bdf8,
        stop:0.48 {c.PRIMARY},
        stop:0.50 {c.PRIMARY_HOVER},
        stop:1.0 {c.PRIMARY_ACTIVE}
    );
    border: 1px solid {c.PRIMARY_ACTIVE};
    color: #ffffff;
}}

/* --- Botões Gerais de Ação --- */
QPushButton {{
    background: {c.SURFACE_ELEVATED};
    border: 1px solid {c.BORDER};
    border-radius: {RADIUS.SM + 2}px;
    padding: {SPACING.SM - 2}px {SPACING.LG}px;
    font-weight: {TYPOGRAPHY.WEIGHT_BOLD};
    font-size: {TYPOGRAPHY.SIZE_BODY}px;
    color: {c.TEXT_PRIMARY};
    min-height: {DIMENSIONS.BUTTON_HEIGHT - 16}px;
}}

QPushButton:hover {{
    background: {c.SURFACE_HOVER};
    border: 1px solid {c.PRIMARY};
    color: {c.PRIMARY};
}}

QPushButton:pressed {{
    background: {c.PRIMARY_LIGHT};
    color: {c.PRIMARY_ACTIVE};
}}

/* --- Botão Primário Destacado --- */
QPushButton#PrimaryButton {{
    background: qlineargradient(
        x1:0, y1:0, x2:0, y2:1,
        stop:0 #38bdf8,
        stop:0.48 {c.PRIMARY},
        stop:0.50 {c.PRIMARY_HOVER},
        stop:1.0 {c.PRIMARY_ACTIVE}
    );
    border: 1px solid {c.PRIMARY_ACTIVE};
    border-radius: {RADIUS.SM + 2}px;
    color: #ffffff;
    font-weight: {TYPOGRAPHY.WEIGHT_BOLD};
    padding: {SPACING.SM - 2}px {SPACING.LG}px;
}}

QPushButton#PrimaryButton:hover {{
    background: qlineargradient(
        x1:0, y1:0, x2:0, y2:1,
        stop:0 #7dd3fc,
        stop:0.48 {c.PRIMARY_HOVER},
        stop:0.50 {c.PRIMARY_ACTIVE},
        stop:1.0 {c.PRIMARY_ACTIVE}
    );
    border: 1px solid {c.PRIMARY_ACTIVE};
}}

/* --- Botões de Mini Dock --- */
QPushButton#DockTile {{
    background: {c.SURFACE_ELEVATED};
    border: 1px solid {c.BORDER};
    border-radius: {RADIUS.MD}px;
    min-width: {DIMENSIONS.DOCK_TILE_SIZE}px;
    max-width: {DIMENSIONS.DOCK_TILE_SIZE}px;
    min-height: {DIMENSIONS.DOCK_TILE_SIZE}px;
    max-height: {DIMENSIONS.DOCK_TILE_SIZE}px;
}}

QPushButton#DockTile:hover {{
    background: {c.SURFACE_HOVER};
    border: 1.5px solid {c.PRIMARY};
}}

/* --- Entradas de Texto e Busca --- */
QLineEdit#GlobalSearch, QLineEdit#PillSearch {{
    background: {c.SURFACE_ELEVATED};
    border: 1px solid {c.BORDER};
    border-radius: {RADIUS.LG}px;
    padding: {SPACING.SM - 1}px {SPACING.LG}px;
    font-size: {TYPOGRAPHY.SIZE_BODY}px;
    font-weight: {TYPOGRAPHY.WEIGHT_NORMAL};
    color: {c.TEXT_PRIMARY};
}}

QLineEdit#GlobalSearch:focus, QLineEdit#PillSearch:focus {{
    background: {c.SURFACE_INPUT_FOCUS};
    border: 2px solid {c.PRIMARY};
    color: {c.TEXT_PRIMARY};
}}

QLineEdit, QTextEdit, QComboBox, QDoubleSpinBox, QSpinBox {{
    background: {c.SURFACE_INPUT};
    border: 1px solid {c.BORDER};
    border-radius: {RADIUS.SM}px;
    padding: {SPACING.SM - 2}px {SPACING.MD}px;
    font-size: {TYPOGRAPHY.SIZE_BODY}px;
    color: {c.TEXT_PRIMARY};
    min-height: {DIMENSIONS.INPUT_HEIGHT - 16}px;
}}

QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QDoubleSpinBox:focus, QSpinBox:focus {{
    border: 2px solid {c.PRIMARY};
    background: {c.SURFACE_INPUT_FOCUS};
}}

QComboBox::drop-down {{
    border: none;
    width: {SPACING.XXL}px;
}}

/* --- Tabelas de Alta Densidade e Legibilidade --- */
QTableWidget {{
    background: {c.TABLE_BG};
    border: 1px solid {c.BORDER};
    border-radius: {RADIUS.MD}px;
    gridline-color: {c.TABLE_GRID};
    font-size: {TYPOGRAPHY.SIZE_BODY}px;
    color: {c.TEXT_PRIMARY};
    alternate-background-color: {c.TABLE_ALT_BG};
    selection-background-color: {c.TABLE_SELECTION_BG};
    selection-color: {c.TABLE_SELECTION_TEXT};
}}

QHeaderView::section {{
    background: qlineargradient(
        x1:0, y1:0, x2:0, y2:1,
        stop:0 {c.TABLE_HEADER_BG_START},
        stop:1.0 {c.TABLE_HEADER_BG_END}
    );
    color: {c.TABLE_HEADER_TEXT};
    font-weight: {TYPOGRAPHY.WEIGHT_BOLD};
    font-size: {TYPOGRAPHY.SIZE_SMALL}px;
    padding: {SPACING.SM + 1}px {SPACING.SM}px;
    border: none;
    border-bottom: 2px solid {c.PRIMARY};
}}

/* --- Scrollbars --- */
QScrollBar:vertical {{
    border: none;
    background: {c.SCROLLBAR_BG};
    width: 8px;
    border-radius: 4px;
}}

QScrollBar::handle:vertical {{
    background: {c.SCROLLBAR_HANDLE_START};
    min-height: 24px;
    border-radius: 4px;
}}

QScrollBar::handle:vertical:hover {{
    background: {c.SCROLLBAR_HANDLE_HOVER};
}}
"""


def apply_frutiger_aero_theme(app: QApplication, dark_mode: bool = False) -> None:
    THEME_STATE["dark_mode"] = dark_mode
    font = QFont("Segoe UI", TYPOGRAPHY.SIZE_SMALL - 2)
    app.setFont(font)
    palette = DARK_PALETTE if dark_mode else LIGHT_PALETTE
    qss = generate_qss(palette)
    app.setStyleSheet(qss)


def toggle_theme(app: QApplication) -> bool:
    new_state = not THEME_STATE.get("dark_mode", False)
    apply_frutiger_aero_theme(app, dark_mode=new_state)
    return new_state

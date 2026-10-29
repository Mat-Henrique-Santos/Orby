from __future__ import annotations

from PySide6.QtGui import QColor, QFont, QPalette
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

QLabel#UserBadgeLabel {{
    color: {c.TEXT_PRIMARY};
    font-size: {TYPOGRAPHY.SIZE_CAPTION + 1}px;
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

/* --- Customização de Listas de Seleção (QComboBox) --- */
QComboBox {{
    padding-right: {SPACING.XXL}px;
}}

QComboBox::drop-down {{
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: {SPACING.XXL}px;
    border-left: 1px solid {c.BORDER};
    border-top-right-radius: {RADIUS.SM}px;
    border-bottom-right-radius: {RADIUS.SM}px;
    background: {c.SURFACE_ELEVATED};
}}

QComboBox::down-arrow {{
    width: 0px;
    height: 0px;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid {c.TEXT_PRIMARY};
    margin: auto;
}}

QComboBox QAbstractItemView {{
    background-color: {c.SURFACE_ELEVATED};
    color: {c.TEXT_PRIMARY};
    selection-background-color: {c.PRIMARY};
    selection-color: #ffffff;
    border: 1px solid {c.BORDER};
    border-radius: {RADIUS.SM}px;
    padding: {SPACING.XS}px;
    outline: none;
}}

/* --- Customização de Campos Numéricos (QDoubleSpinBox / QSpinBox) --- */
QDoubleSpinBox, QSpinBox {{
    padding-right: {SPACING.XL + 2}px;
}}

QDoubleSpinBox::up-button, QSpinBox::up-button {{
    subcontrol-origin: border;
    subcontrol-position: top right;
    width: {SPACING.XL}px;
    border-left: 1px solid {c.BORDER};
    border-bottom: 0.5px solid {c.BORDER};
    background: {c.SURFACE_ELEVATED};
    border-top-right-radius: {RADIUS.SM}px;
}}

QDoubleSpinBox::up-button:hover, QSpinBox::up-button:hover {{
    background: {c.SURFACE_HOVER};
}}

QDoubleSpinBox::up-arrow, QSpinBox::up-arrow {{
    width: 0px;
    height: 0px;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-bottom: 5px solid {c.TEXT_PRIMARY};
    margin: auto;
}}

QDoubleSpinBox::down-button, QSpinBox::down-button {{
    subcontrol-origin: border;
    subcontrol-position: bottom right;
    width: {SPACING.XL}px;
    border-left: 1px solid {c.BORDER};
    border-top: 0.5px solid {c.BORDER};
    background: {c.SURFACE_ELEVATED};
    border-bottom-right-radius: {RADIUS.SM}px;
}}

QDoubleSpinBox::down-button:hover, QSpinBox::down-button:hover {{
    background: {c.SURFACE_HOVER};
}}

QDoubleSpinBox::down-arrow, QSpinBox::down-arrow {{
    width: 0px;
    height: 0px;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid {c.TEXT_PRIMARY};
    margin: auto;
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

/* --- CheckBox Estilizado --- */
QCheckBox {{
    font-size: {TYPOGRAPHY.SIZE_BODY}px;
    color: {c.TEXT_PRIMARY};
    spacing: {SPACING.SM}px;
}}

QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border-radius: {RADIUS.SM}px;
    border: 1px solid {c.BORDER};
    background: {c.SURFACE_ELEVATED};
}}

QCheckBox::indicator:hover {{
    border-color: {c.PRIMARY};
}}

QCheckBox::indicator:checked {{
    background: {c.PRIMARY};
    border-color: {c.PRIMARY_ACTIVE};
}}

/* --- Scrollbars e Áreas de Rolagem --- */
QScrollArea,
QScrollArea#PageScrollArea,
QScrollArea > QWidget#qt_scrollarea_viewport,
QWidget#PageScrollContent {{
    background: transparent;
    border: none;
}}

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

QScrollBar:horizontal {{
    border: none;
    background: {c.SCROLLBAR_BG};
    height: 8px;
    border-radius: 4px;
}}

QScrollBar::handle:horizontal {{
    background: {c.SCROLLBAR_HANDLE_START};
    min-width: 24px;
    border-radius: 4px;
}}

QScrollBar::handle:horizontal:hover {{
    background: {c.SCROLLBAR_HANDLE_HOVER};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    border: none;
    background: none;
    width: 0px;
    height: 0px;
}}
"""


def apply_frutiger_aero_theme(app: QApplication, dark_mode: bool = False) -> None:
    THEME_STATE["dark_mode"] = dark_mode
    font = QFont("Segoe UI", TYPOGRAPHY.SIZE_SMALL - 2)
    app.setFont(font)
    palette = DARK_PALETTE if dark_mode else LIGHT_PALETTE

    # Sincroniza a QPalette do sistema com o tema Frutiger Aero, evitando vazamentos de fundo preto do Windows
    app_palette = QPalette()
    app_palette.setColor(QPalette.Window, QColor(palette.WINDOW_GRADIENT_START))
    app_palette.setColor(QPalette.WindowText, QColor(palette.TEXT_PRIMARY))
    app_palette.setColor(QPalette.Base, QColor(palette.SURFACE_ELEVATED))
    app_palette.setColor(QPalette.AlternateBase, QColor(palette.WINDOW_GRADIENT_MID1))
    app_palette.setColor(QPalette.ToolTipBase, QColor(palette.SURFACE_ELEVATED))
    app_palette.setColor(QPalette.ToolTipText, QColor(palette.TEXT_PRIMARY))
    app_palette.setColor(QPalette.Text, QColor(palette.TEXT_PRIMARY))
    app_palette.setColor(QPalette.Button, QColor(palette.SURFACE_ELEVATED))
    app_palette.setColor(QPalette.ButtonText, QColor(palette.TEXT_PRIMARY))
    app_palette.setColor(QPalette.Highlight, QColor(palette.PRIMARY))
    app_palette.setColor(QPalette.HighlightedText, QColor(palette.TEXT_ON_PRIMARY))
    app.setPalette(app_palette)

    qss = generate_qss(palette)
    app.setStyleSheet(qss)


def toggle_theme(app: QApplication) -> bool:
    new_state = not THEME_STATE.get("dark_mode", False)
    apply_frutiger_aero_theme(app, dark_mode=new_state)
    return new_state

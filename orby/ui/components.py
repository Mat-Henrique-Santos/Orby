from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import (
    QBrush,
    QColor,
    QFont,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QRadialGradient,
)
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from .icons import IconWidget, get_icon, get_pixmap
from .theme import get_current_palette
from .tokens import DIMENSIONS, ICON_SIZES, RADIUS, SPACING, TYPOGRAPHY


class OrbLogoWidget(QWidget):
    """Logotipo 3D Esférico Frutiger Aero com reflexo vítreo especular gerado com tokens."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedSize(DIMENSIONS.LOGO_SIZE, DIMENSIONS.LOGO_SIZE)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        rect = QRectF(4, 4, 64, 64)

        # 1. Sombra suave inferior
        shadow_rect = QRectF(8, 52, 56, 14)
        shadow_grad = QRadialGradient(QPointF(36, 59), 28)
        shadow_grad.setColorAt(0.0, QColor(0, 40, 80, 100))
        shadow_grad.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(shadow_grad))
        painter.drawEllipse(shadow_rect)

        # 2. Esfera base 3D (Gradiente radial ciano/azul oceano vibrante)
        sphere_grad = QRadialGradient(QPointF(26, 24), 38)
        sphere_grad.setColorAt(0.0, QColor(100, 255, 245))  # Ponto de luz turquesa brilhante
        sphere_grad.setColorAt(0.35, QColor(0, 190, 230))   # Ciano Aero
        sphere_grad.setColorAt(0.70, QColor(2, 110, 185))   # Azul oceano
        sphere_grad.setColorAt(1.0, QColor(1, 45, 95))      # Sombra inferior da esfera

        painter.setBrush(QBrush(sphere_grad))
        painter.setPen(QPen(QColor(255, 255, 255, 180), 1.5))
        painter.drawEllipse(rect)

        # 3. Anel orbital estilizado da marca Orby
        orbit_rect = QRectF(8, 22, 56, 26)
        painter.save()
        painter.translate(36, 36)
        painter.rotate(-24)
        painter.translate(-36, -36)
        orbit_pen = QPen(QColor(255, 255, 255, 200), 2.2)
        painter.setPen(orbit_pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(orbit_rect)
        painter.restore()

        # 4. Brilho especular superior (Glossy Highlight)
        gloss_rect = QRectF(14, 8, 44, 24)
        gloss_grad = QLinearGradient(QPointF(36, 8), QPointF(36, 32))
        gloss_grad.setColorAt(0.0, QColor(255, 255, 255, 220))
        gloss_grad.setColorAt(0.5, QColor(255, 255, 255, 90))
        gloss_grad.setColorAt(1.0, QColor(255, 255, 255, 0))

        painter.setBrush(QBrush(gloss_grad))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(gloss_rect)


class ContentCard(QFrame):
    """Painel de vidro translúcido Aero padronizado pelo Design System."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("ContentCard")


class MetricCard(QFrame):
    """Cartão de KPI/Métrica padronizado com ícone vetorial SVG Lucide."""

    def __init__(
        self,
        title: str,
        initial_value: str = "0",
        icon_name: str = "chart",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("MetricCard")
        self.setMinimumHeight(DIMENSIONS.METRIC_CARD_MIN_HEIGHT)
        self.setMinimumWidth(DIMENSIONS.METRIC_CARD_MIN_WIDTH)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING.LG, SPACING.MD + 2, SPACING.LG, SPACING.MD + 2)
        layout.setSpacing(SPACING.XS + 2)

        header_layout = QHBoxLayout()
        header_layout.setSpacing(SPACING.SM)

        self.icon_widget = IconWidget(icon_name, size=ICON_SIZES.LG)
        self.title_label = QLabel(title)
        self.title_label.setObjectName("MetricTitle")

        header_layout.addWidget(self.icon_widget)
        header_layout.addWidget(self.title_label)
        header_layout.addStretch()

        self.value_label = QLabel(initial_value)
        self.value_label.setObjectName("MetricValue")

        layout.addLayout(header_layout)
        layout.addWidget(self.value_label)
        layout.addStretch()

    def set_value(self, value: str) -> None:
        self.value_label.setText(value)


class StatusBadge(QLabel):
    """Badge em formato de pílula vítrea gelatinosa orientada a tokens semânticos."""

    STATUS_STYLES = {
        "Aberta": (
            "background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #f0f9ff, stop:1 #e0f2fe); "
            "color: #0369a1; border: 1px solid #7dd3fc;"
        ),
        "Em Diagnóstico": (
            "background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #fff7ed, stop:1 #ffedd5); "
            "color: #c2410c; border: 1px solid #fdba74;"
        ),
        "Aguardando Aprovação": (
            "background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #fefce8, stop:1 #fef9c3); "
            "color: #854d0e; border: 1px solid #fde047;"
        ),
        "Em Reparo": (
            "background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #f0fdfa, stop:1 #ccfbf1); "
            "color: #0f766e; border: 1px solid #5eead4;"
        ),
        "Aguardando Retirada": (
            "background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #faf5ff, stop:1 #f3e8ff); "
            "color: #7e22ce; border: 1px solid #d8b4fe;"
        ),
        "Finalizada": (
            "background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #f0fdf4, stop:1 #dcfce7); "
            "color: #15803d; border: 1px solid #86efac;"
        ),
        "Cancelada": (
            "background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #fff1f2, stop:1 #ffe4e6); "
            "color: #be123c; border: 1px solid #fda4af;"
        ),
    }

    def __init__(self, status: str, parent: QWidget | None = None) -> None:
        super().__init__(status, parent)
        self.setAlignment(Qt.AlignCenter)
        self.setContentsMargins(SPACING.SM + 2, SPACING.XS, SPACING.SM + 2, SPACING.XS)
        self.setFixedHeight(DIMENSIONS.STATUS_BADGE_HEIGHT)
        self.update_status(status)

    def update_status(self, status: str) -> None:
        self.setText(status)
        style = self.STATUS_STYLES.get(
            status,
            "background: #f1f5f9; color: #475569; border: 1px solid #cbd5e1;",
        )
        self.setStyleSheet(
            f"border-radius: {DIMENSIONS.STATUS_BADGE_RADIUS}px; font-size: {TYPOGRAPHY.SIZE_CAPTION + 0.5}px; "
            f"font-weight: {TYPOGRAPHY.WEIGHT_EXTRABOLD}; padding: 2px {SPACING.SM + 2}px; {style}"
        )


class ModernTableWidget(QTableWidget):
    """Tabela customizada com alternância de cores, dimensões e cabeçalho ajustável."""

    def __init__(self, rows: int, cols: int, parent: QWidget | None = None) -> None:
        super().__init__(rows, cols, parent)
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QTableWidget.SelectRows)
        self.setEditTriggers(QTableWidget.NoEditTriggers)
        self.setShowGrid(False)
        self.verticalHeader().setVisible(False)
        self.verticalHeader().setDefaultSectionSize(DIMENSIONS.TABLE_ROW_HEIGHT)
        self.horizontalHeader().setFixedHeight(DIMENSIONS.TABLE_HEADER_HEIGHT)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.horizontalHeader().setHighlightSections(False)


class TimelineDialog(QDialog):
    """Janela visual de auditoria e linha do tempo da Ordem de Serviço com ícones SVG."""

    def __init__(self, parent: QWidget | None, order_id: int, history: list[dict], order_info: dict | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"Linha do Tempo e Auditoria — OS #{order_id:04d}")
        self.resize(650, 480)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING.XXL - 2, SPACING.XL, SPACING.XXL - 2, SPACING.XL)
        layout.setSpacing(SPACING.MD + 2)

        header_card = ContentCard()
        h_layout = QVBoxLayout(header_card)
        h_layout.setContentsMargins(SPACING.LG, SPACING.MD, SPACING.LG, SPACING.MD)
        h_layout.setSpacing(SPACING.XS)

        if order_info:
            title = QLabel(f"Ordem de Serviço #{order_id:04d} — {order_info.get('cliente_nome', '')}")
            title.setStyleSheet(f"font-size: {TYPOGRAPHY.SIZE_SUBTITLE}px; font-weight: {TYPOGRAPHY.WEIGHT_EXTRABOLD}; color: {get_current_palette().PRIMARY};")
            desc = QLabel(f"Equipamento: {order_info.get('equipamento_nome', '')} | Status Atual: {order_info.get('status', '')}")
            desc.setStyleSheet(f"font-size: {TYPOGRAPHY.SIZE_SMALL}px; font-weight: {TYPOGRAPHY.WEIGHT_SEMIBOLD}; color: {get_current_palette().TEXT_SECONDARY};")
            h_layout.addWidget(title)
            h_layout.addWidget(desc)

        layout.addWidget(header_card)

        info_box = QHBoxLayout()
        info_box.setSpacing(SPACING.SM)
        info_icon = IconWidget("clock", size=ICON_SIZES.MD)
        info_lbl = QLabel("Trilha Cronológica de Auditoria (Registro Imutável)")
        info_lbl.setStyleSheet(f"font-size: {TYPOGRAPHY.SIZE_BODY}px; font-weight: {TYPOGRAPHY.WEIGHT_BOLD}; color: {get_current_palette().PRIMARY};")
        info_box.addWidget(info_icon)
        info_box.addWidget(info_lbl)
        info_box.addStretch()
        layout.addLayout(info_box)

        self.table = ModernTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Data / Hora", "Status Anterior", "Novo Status", "Observação / Evento"])

        for entry in history:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(entry.get("criado_em", "")[:19]))
            self.table.setItem(row, 1, QTableWidgetItem(entry.get("status_anterior") or "—"))
            badge = StatusBadge(entry.get("status_novo", "Aberta"))
            self.table.setCellWidget(row, 2, badge)
            self.table.setItem(row, 3, QTableWidgetItem(entry.get("observacao") or ""))

        layout.addWidget(self.table, 1)

        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        close_btn = buttons.button(QDialogButtonBox.Close)
        if close_btn:
            close_btn.setText(" Fechar")
            close_btn.setIcon(get_icon("x-circle", color=get_current_palette().TEXT_PRIMARY, size=16))
        buttons.rejected.connect(self.accept)
        layout.addWidget(buttons)

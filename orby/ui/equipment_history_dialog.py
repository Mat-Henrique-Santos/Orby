from __future__ import annotations

from PySide6.QtCore import Qt, QSize
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from .components import ContentCard, ModernTableWidget
from .icons import get_icon
from .theme import get_current_palette
from .tokens import DIMENSIONS, ICON_SIZES, RADIUS, SPACING, TYPOGRAPHY


def format_currency(valor: float | int | None) -> str:
    v = float(valor or 0.0)
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


class EquipmentHistoryDialog(QDialog):
    """Diálogo Frutiger Aero para visualização do histórico completo de manutenções de um aparelho."""

    def __init__(
        self,
        equipment: dict,
        orders_history: list[dict],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.equipment = equipment
        self.orders = orders_history

        eq_nome = " ".join(
            part for part in [equipment.get("tipo"), equipment.get("marca"), equipment.get("modelo")] if part
        ) or "Equipamento"

        self.setWindowTitle(f"Orby — Histórico de Manutenções: {eq_nome}")
        self.resize(780, 520)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        pal = get_current_palette()

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(SPACING.XL, SPACING.XL, SPACING.XL, SPACING.XL)
        main_layout.setSpacing(SPACING.MD)

        # Card de Identificação do Aparelho
        info_card = ContentCard()
        info_layout = QVBoxLayout(info_card)
        info_layout.setContentsMargins(SPACING.LG, SPACING.MD, SPACING.LG, SPACING.MD)
        info_layout.setSpacing(SPACING.XS)

        title_box = QHBoxLayout()
        title_box.setSpacing(SPACING.SM)
        icon_lbl = QLabel()
        icon_lbl.setPixmap(get_icon("laptop", color=pal.PRIMARY, size=ICON_SIZES.LG).pixmap(24, 24))
        title_box.addWidget(icon_lbl)

        eq_title = QLabel(f"<b>{eq_nome}</b>")
        eq_title.setStyleSheet(f"font-size: 16px; color: {pal.TEXT_PRIMARY};")
        title_box.addWidget(eq_title)
        title_box.addStretch()

        serial = equipment.get("numero_serie") or "Não informado"
        serial_lbl = QLabel(f"<b>Nº de Série / IMEI:</b> {serial}")
        serial_lbl.setStyleSheet(f"font-size: {TYPOGRAPHY.SIZE_SMALL}px; color: {pal.TEXT_SECONDARY};")
        title_box.addWidget(serial_lbl)
        info_layout.addLayout(title_box)

        total_os = len(self.orders)
        plural = "manutenções registradas" if total_os != 1 else "manutenção registrada"
        resumo_lbl = QLabel(f"Este equipamento possui um total de <b>{total_os} {plural}</b> nesta oficina.")
        resumo_lbl.setStyleSheet(f"font-size: {TYPOGRAPHY.SIZE_SMALL}px; color: {pal.TEXT_MUTED};")
        info_layout.addWidget(resumo_lbl)

        main_layout.addWidget(info_card)

        # Tabela de Manutenções Anteriores
        table_card = ContentCard()
        table_layout = QVBoxLayout(table_card)
        table_layout.setContentsMargins(SPACING.LG, SPACING.MD, SPACING.LG, SPACING.MD)
        table_layout.setSpacing(SPACING.SM)

        table_header = QLabel("Linha do Tempo de Atendimentos Anteriores")
        table_header.setObjectName("SectionSubtitle")
        table_layout.addWidget(table_header)

        self.table = ModernTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels([
            "Nº OS", "Data Entrada", "Status", "Defeito Relatado", "Diagnóstico Técnico", "Valor Total", "Conclusão"
        ])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeToContents)

        self.populate_table()
        table_layout.addWidget(self.table)
        main_layout.addWidget(table_card, 1)

        # Botão Fechar
        btn_box = QHBoxLayout()
        btn_box.addStretch()
        btn_close = QPushButton("Fechar Histórico")
        btn_close.setObjectName("PrimaryButton")
        btn_close.setIcon(get_icon("circle-check", color="#ffffff", size=ICON_SIZES.SM))
        btn_close.setIconSize(QSize(ICON_SIZES.SM, ICON_SIZES.SM))
        btn_close.clicked.connect(self.accept)
        btn_box.addWidget(btn_close)
        main_layout.addLayout(btn_box)

    def populate_table(self) -> None:
        self.table.setRowCount(0)
        for order in self.orders:
            row = self.table.rowCount()
            self.table.insertRow(row)

            # OS ID
            item_id = QTableWidgetItem(f"OS-{order['id']:04d}")
            item_id.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 0, item_id)

            # Data Abertura
            data_ab = str(order.get("data_abertura") or "—")[:10]
            item_dt = QTableWidgetItem(data_ab)
            item_dt.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 1, item_dt)

            # Status
            status_text = order.get("status", "Aberta")
            item_st = QTableWidgetItem(status_text)
            item_st.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 2, item_st)

            # Defeito
            desc = order.get("descricao") or "—"
            item_desc = QTableWidgetItem(desc)
            item_desc.setToolTip(desc)
            self.table.setItem(row, 3, item_desc)

            # Diagnóstico
            diag = order.get("diagnostico") or "—"
            item_diag = QTableWidgetItem(diag)
            item_diag.setToolTip(diag)
            self.table.setItem(row, 4, item_diag)

            # Valor
            valor_fmt = format_currency(order.get("valor", 0.0))
            item_val = QTableWidgetItem(valor_fmt)
            item_val.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(row, 5, item_val)

            # Data Finalização
            data_fim = str(order.get("data_finalizacao") or "Em aberto")[:10]
            item_fim = QTableWidgetItem(data_fim)
            item_fim.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 6, item_fim)

from __future__ import annotations

import os
import re

from PySide6.QtCore import QLocale, QSize, Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QCheckBox,
    QApplication,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from .core.models import (
    FORMA_PAGAMENTO_OPCOES,
    StatusOS,
    validar_documento,
    validar_email,
    validar_telefone,
)
from .core.backup import BackupManager, InvalidBackupFileError
from .importer import read_table, validate_customers
from .repository import PermissionDeniedError, Repository
from .ui.user_dialog import UserDialog, PasswordDialog
from .ui.equipment_history_dialog import EquipmentHistoryDialog
from .ui.components import (
    ContentCard,
    MetricCard,
    ModernTableWidget,
    OrbLogoWidget,
    StatusBadge,
    TimelineDialog,
)
from .ui.icons import IconWidget, clear_icon_cache, get_icon, get_pixmap
from .ui.theme import get_current_palette, is_dark_mode, toggle_theme
from .ui.tokens import DIMENSIONS, ICON_SIZES, SPACING, TYPOGRAPHY


def formatar_moeda(valor: float | int | None) -> str:
    """Formata valores numéricos para o padrão monetário brasileiro R$ 0.000,00."""
    v = float(valor or 0.0)
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


class CustomerDialog(QDialog):
    def __init__(self, parent, customer: dict | None = None):
        super().__init__(parent)
        self.setWindowTitle("Editar Cliente" if customer else "Novo Cliente")
        self.resize(520, 380)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING.XXL, SPACING.XXL, SPACING.XXL, SPACING.XXL)
        layout.setSpacing(SPACING.MD)

        form = QFormLayout()
        form.setSpacing(SPACING.SM + 2)

        self.name = QLineEdit(customer["nome"] if customer else "")
        self.phone = QLineEdit(customer["telefone"] if customer else "")
        self.email = QLineEdit(customer.get("email") or "" if customer else "")
        self.document = QLineEdit(customer.get("documento") or "" if customer else "")
        self.address = QLineEdit(customer.get("endereco") or "" if customer else "")

        self.name.setPlaceholderText("Nome completo ou Razão Social")
        self.phone.setPlaceholderText("(00) 00000-0000")
        self.email.setPlaceholderText("email@exemplo.com")
        self.document.setPlaceholderText("CPF ou CNPJ")
        self.address.setPlaceholderText("Rua, Número, Bairro, Cidade")

        form.addRow("Nome *", self.name)
        form.addRow("Telefone *", self.phone)
        form.addRow("E-mail", self.email)
        form.addRow("CPF / CNPJ", self.document)
        form.addRow("Endereço", self.address)
        layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        save_btn = buttons.button(QDialogButtonBox.Save)
        save_btn.setText("Salvar Cliente")
        save_btn.setObjectName("PrimaryButton")
        save_btn.setIcon(get_icon("circle-check", color="#ffffff", size=ICON_SIZES.SM))
        cancel_btn = buttons.button(QDialogButtonBox.Cancel)
        cancel_btn.setText("Cancelar")
        cancel_btn.setIcon(get_icon("x-circle", color=get_current_palette().TEXT_PRIMARY, size=ICON_SIZES.SM))

        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def values(self) -> tuple[str, str, str, str, str]:
        return (
            self.name.text(),
            self.phone.text(),
            self.email.text(),
            self.document.text(),
            self.address.text(),
        )

    def accept(self) -> None:
        nome = self.name.text().strip()
        telefone = self.phone.text().strip()
        email = self.email.text().strip()
        documento = self.document.text().strip()

        if not nome or not telefone:
            QMessageBox.warning(self, "Campos Obrigatórios", "Informe ao menos o nome e o telefone do cliente.")
            return

        if not validar_telefone(telefone):
            QMessageBox.warning(
                self,
                "Telefone Inválido",
                "O telefone deve conter DDD + 8 ou 9 dígitos numéricos (ex: 11987654321 ou (11) 98765-4321).",
            )
            return

        if email and not validar_email(email):
            QMessageBox.warning(
                self,
                "E-mail Inválido",
                f"O e-mail '{email}' não possui um formato válido (ex: contato@empresa.com).",
            )
            return

        if documento and not validar_documento(documento):
            QMessageBox.warning(
                self,
                "Documento Inválido",
                f"O CPF ou CNPJ informado ('{documento}') é inválido.",
            )
            return

        super().accept()


class OrderDialog(QDialog):
    def __init__(self, parent, customers: list[dict], order: dict | None = None):
        super().__init__(parent)
        self.parent_window = parent
        self.order = order
        self.setWindowTitle(f"Editar OS #{order['id']:04d}" if order else "Nova Ordem de Serviço")
        self.resize(640, 600)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING.XXL, SPACING.XXL, SPACING.XXL, SPACING.XXL)
        layout.setSpacing(SPACING.MD)

        form = QFormLayout()
        form.setSpacing(SPACING.SM + 2)

        self.customer = QComboBox()
        self.equipment = QComboBox()
        self.equipment.currentIndexChanged.connect(self.on_equipment_changed)

        self.btn_history = QPushButton("📋 Histórico do Aparelho")
        self.btn_history.setIcon(get_icon("clock", size=ICON_SIZES.SM))
        self.btn_history.setIconSize(QSize(ICON_SIZES.SM, ICON_SIZES.SM))
        self.btn_history.setVisible(False)
        self.btn_history.clicked.connect(self.view_equipment_history)

        for item in customers:
            self.customer.addItem(item["nome"], item["id"])
        self.customer.currentIndexChanged.connect(self.load_equipment)

        self.description = QTextEdit(order["descricao"] if order else "")
        self.description.setPlaceholderText("Defeito relatado pelo cliente no balcão...")
        self.description.setFixedHeight(55)

        is_atendente = hasattr(parent, "perfil") and parent.perfil == "Atendente"
        is_tecnico = hasattr(parent, "perfil") and parent.perfil == "Técnico"

        self.diagnosis = QTextEdit(order.get("diagnostico") or "" if order else "")
        self.diagnosis.setFixedHeight(55)
        if is_atendente:
            self.diagnosis.setReadOnly(True)
            self.diagnosis.setPlaceholderText("Laudo técnico preenchido exclusivamente pelo Técnico...")
        else:
            self.diagnosis.setPlaceholderText("Laudo técnico / defeito constatado...")

        tec_default = parent.current_user.get("nome", "") if (is_tecnico and not order and hasattr(parent, "current_user")) else (order.get("tecnico") or "" if order else "")
        self.technician = QLineEdit(tec_default)
        self.technician.setPlaceholderText("Nome do técnico responsável")
        if is_atendente:
            self.technician.setReadOnly(True)

        self.status = QComboBox()
        self.status.addItems(StatusOS.all_values())
        if is_atendente:
            if order:
                self.status.setEnabled(False)
            else:
                self.status.clear()
                self.status.addItem(StatusOS.ABERTA.value)
                self.status.setEnabled(False)

        # Discriminação de Valores Financeiros com formato brasileiro
        loc_br = QLocale(QLocale.Portuguese, QLocale.Brazil)

        self.valor_servico = QDoubleSpinBox()
        self.valor_servico.setLocale(loc_br)
        self.valor_servico.setMaximum(9_999_999.99)
        self.valor_servico.setPrefix("R$ ")
        self.valor_servico.setDecimals(2)
        self.valor_servico.setValue(float(order.get("valor_servico") or 0.0) if order else 0.0)
        self.valor_servico.valueChanged.connect(self.recalc_total)

        self.valor_pecas = QDoubleSpinBox()
        self.valor_pecas.setLocale(loc_br)
        self.valor_pecas.setMaximum(9_999_999.99)
        self.valor_pecas.setPrefix("R$ ")
        self.valor_pecas.setDecimals(2)
        self.valor_pecas.setValue(float(order.get("valor_pecas") or 0.0) if order else 0.0)
        self.valor_pecas.valueChanged.connect(self.recalc_total)

        self.value = QDoubleSpinBox()
        self.value.setLocale(loc_br)
        self.value.setMaximum(9_999_999.99)
        self.value.setPrefix("R$ ")
        self.value.setDecimals(2)
        self.value.setValue(float(order["valor"]) if order else 0.0)

        if is_atendente:
            self.valor_servico.setReadOnly(True)
            self.valor_pecas.setReadOnly(True)
            self.value.setReadOnly(True)

        self.forma_pagamento = QComboBox()
        self.forma_pagamento.addItems(FORMA_PAGAMENTO_OPCOES)
        if order and order.get("forma_pagamento"):
            self.forma_pagamento.setCurrentText(order["forma_pagamento"])
        if is_atendente:
            self.forma_pagamento.setEnabled(False)

        self.notes = QTextEdit(order.get("observacoes") or "" if order else "")
        self.notes.setPlaceholderText("Observações internas / prazos acordados...")
        self.notes.setFixedHeight(50)

        if order:
            self.customer.setCurrentIndex(self.customer.findData(order["cliente_id"]))
            self.load_equipment()
            self.equipment.setCurrentIndex(self.equipment.findData(order.get("equipamento_id")))
            self.status.setCurrentText(order["status"])
        else:
            self.load_equipment()

        form.addRow("Cliente *", self.customer)
        form.addRow("Equipamento *", self.equipment)
        form.addRow("", self.btn_history)
        form.addRow("Problema Relatado *", self.description)
        form.addRow("Diagnóstico Técnico", self.diagnosis)
        form.addRow("Técnico", self.technician)
        form.addRow("Status", self.status)
        form.addRow("Mão de Obra (Serviço)", self.valor_servico)
        form.addRow("Peças / Componentes", self.valor_pecas)
        form.addRow("Valor Total (R$)", self.value)
        form.addRow("Forma de Pagamento", self.forma_pagamento)
        form.addRow("Observações", self.notes)
        layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        save_btn = buttons.button(QDialogButtonBox.Save)
        save_btn.setText("Salvar Ordem de Serviço")
        save_btn.setObjectName("PrimaryButton")
        save_btn.setIcon(get_icon("circle-check", color="#ffffff", size=ICON_SIZES.SM))
        cancel_btn = buttons.button(QDialogButtonBox.Cancel)
        cancel_btn.setText("Cancelar")
        cancel_btn.setIcon(get_icon("x-circle", color=get_current_palette().TEXT_PRIMARY, size=ICON_SIZES.SM))

        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def recalc_total(self) -> None:
        calc = self.valor_servico.value() + self.valor_pecas.value()
        if calc > 0:
            self.value.setValue(calc)

    def load_equipment(self) -> None:
        self.equipment.blockSignals(True)
        self.equipment.clear()
        cust_id = self.customer.currentData()
        if cust_id:
            items = self.parent_window.repository.equipment(cust_id)
            for item in items:
                label = " ".join(part for part in [item["tipo"], item.get("marca"), item.get("modelo")] if part)
                if item.get("numero_serie"):
                    label += f" (S/N: {item['numero_serie']})"
                self.equipment.addItem(label, item["id"])
        self.equipment.blockSignals(False)
        self.on_equipment_changed()

    def on_equipment_changed(self) -> None:
        eq_id = self.equipment.currentData()
        if eq_id and hasattr(self.parent_window, "repository"):
            history = self.parent_window.repository.orders_by_equipment(eq_id)
            current_id = self.order["id"] if self.order else None
            prev_orders = [o for o in history if o["id"] != current_id]
            if prev_orders:
                count = len(prev_orders)
                plural = "manutenções anteriores" if count > 1 else "manutenção anterior"
                self.btn_history.setText(f"📋 Ver Histórico: {count} {plural} deste aparelho")
                self.btn_history.setVisible(True)
            else:
                self.btn_history.setVisible(False)
        else:
            self.btn_history.setVisible(False)

    def view_equipment_history(self) -> None:
        eq_id = self.equipment.currentData()
        if not eq_id:
            return
        eq = self.parent_window.repository.single_equipment(eq_id)
        if not eq:
            return
        history = self.parent_window.repository.orders_by_equipment(eq_id)
        from .ui.equipment_history_dialog import EquipmentHistoryDialog
        dlg = EquipmentHistoryDialog(eq, history, self)
        dlg.exec()

    def values(self) -> tuple[int, int, str, str, float, float, float, str, str, str, str]:
        return (
            self.customer.currentData(),
            self.equipment.currentData(),
            self.description.toPlainText(),
            self.status.currentText(),
            self.value.value(),
            self.valor_servico.value(),
            self.valor_pecas.value(),
            self.forma_pagamento.currentText(),
            self.notes.toPlainText(),
            self.diagnosis.toPlainText(),
            self.technician.text(),
        )

    def accept(self) -> None:
        status = self.status.currentText()
        if status == StatusOS.FINALIZADA.value:
            if self.value.value() <= 0:
                QMessageBox.warning(self, "Valor Obrigatório", "Para finalizar a OS, o valor total deve ser maior que zero.")
                return
            if self.forma_pagamento.currentText() == "Não Definido":
                QMessageBox.warning(self, "Pagamento Obrigatório", "Selecione a forma de pagamento antes de finalizar a OS.")
                return
        super().accept()


class EquipmentDialog(QDialog):
    def __init__(self, parent, customers: list[dict], equipment: dict | None = None):
        super().__init__(parent)
        self.setWindowTitle(f"Editar Equipamento #{equipment['id']}" if equipment else "Novo Equipamento")
        self.resize(520, 440)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING.XXL, SPACING.XXL, SPACING.XXL, SPACING.XXL)
        layout.setSpacing(SPACING.MD)

        form = QFormLayout()
        form.setSpacing(SPACING.SM + 2)

        self.customer = QComboBox()
        for item in customers:
            self.customer.addItem(item["nome"], item["id"])
        if equipment:
            idx = self.customer.findData(equipment["cliente_id"])
            if idx >= 0:
                self.customer.setCurrentIndex(idx)

        self.type = QLineEdit(equipment["tipo"] if equipment else "")
        self.type.setPlaceholderText("Ex: Notebook, Máquina de Solda, Ar-Condicionado, Motor, Celular")
        self.brand = QLineEdit(equipment.get("marca") or "" if equipment else "")
        self.brand.setPlaceholderText("Ex: Dell, Makita, Consul, WEG, Samsung")
        self.model = QLineEdit(equipment.get("modelo") or "" if equipment else "")
        self.model.setPlaceholderText("Ex: Inspiron 15, Inverter 12k, Trifásico, LaserJet")
        self.serial = QLineEdit(equipment.get("numero_serie") or "" if equipment else "")
        self.serial.setPlaceholderText("Número de Série ou IMEI")
        self.accessories = QLineEdit(equipment.get("acessorios") or "" if equipment else "")
        self.accessories.setPlaceholderText("Ex: Carregador, Cabo, Capa")
        self.condition = QLineEdit(equipment.get("condicao_entrada") or "" if equipment else "")
        self.condition.setPlaceholderText("Ex: Riscos na tampa, tela trincada")
        self.notes = QTextEdit(equipment.get("observacoes") or "" if equipment else "")
        self.notes.setPlaceholderText("Observações técnicas adicionais...")
        self.notes.setFixedHeight(60)

        form.addRow("Cliente *", self.customer)
        form.addRow("Tipo *", self.type)
        form.addRow("Marca", self.brand)
        form.addRow("Modelo", self.model)
        form.addRow("Nº de Série", self.serial)
        form.addRow("Acessórios entregues", self.accessories)
        form.addRow("Condição de entrada", self.condition)
        form.addRow("Observações", self.notes)
        layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        save_btn = buttons.button(QDialogButtonBox.Save)
        save_btn.setText("Salvar Equipamento" if equipment else "Cadastrar Equipamento")
        save_btn.setObjectName("PrimaryButton")
        save_btn.setIcon(get_icon("circle-check", color="#ffffff", size=ICON_SIZES.SM))
        cancel_btn = buttons.button(QDialogButtonBox.Cancel)
        cancel_btn.setText("Cancelar")
        cancel_btn.setIcon(get_icon("x-circle", color=get_current_palette().TEXT_PRIMARY, size=ICON_SIZES.SM))

        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def values(self):
        return (
            self.customer.currentData(),
            self.type.text(),
            self.brand.text(),
            self.model.text(),
            self.serial.text(),
            self.accessories.text(),
            self.condition.text(),
            self.notes.toPlainText(),
        )

    def accept(self) -> None:
        if not self.type.text().strip():
            QMessageBox.warning(self, "Campo Obrigatório", "Informe o tipo do equipamento.")
            return
        super().accept()


class ImportDialog(QDialog):
    def __init__(self, parent, repository: Repository):
        super().__init__(parent)
        self.repository = repository
        self.headers: list[str] = []
        self.rows: list[dict] = []
        self.approved: list[dict] = []
        self.setWindowTitle("Importar Clientes (CSV / XLSX)")
        self.resize(880, 640)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING.XXL, SPACING.XXL, SPACING.XXL, SPACING.XXL)
        layout.setSpacing(SPACING.MD + 2)

        header_box = QHBoxLayout()
        header_box.setSpacing(SPACING.SM)
        icon = IconWidget("file-up", size=ICON_SIZES.LG)
        desc = QLabel("Selecione um arquivo de planilha para importar cadastros de clientes com validação automática.")
        desc.setWordWrap(True)
        desc.setObjectName("SummaryLabel")
        header_box.addWidget(icon)
        header_box.addWidget(desc, 1)
        layout.addLayout(header_box)

        select_btn = QPushButton("Selecionar Arquivo CSV ou XLSX")
        select_btn.setObjectName("PrimaryButton")
        select_btn.setIcon(get_icon("file-up", color="#ffffff", size=ICON_SIZES.SM))
        select_btn.clicked.connect(self.select_file)
        layout.addWidget(select_btn)

        mapping_frame = ContentCard()
        mapping = QFormLayout(mapping_frame)
        mapping.setContentsMargins(SPACING.LG, SPACING.MD, SPACING.LG, SPACING.MD)
        mapping.setSpacing(SPACING.SM + 2)

        self.name_column = QComboBox()
        self.phone_column = QComboBox()
        self.email_column = QComboBox()
        self.document_column = QComboBox()
        self.address_column = QComboBox()

        for combo in (self.name_column, self.phone_column, self.email_column, self.document_column, self.address_column):
            combo.currentTextChanged.connect(self.review)

        mapping.addRow("Coluna Nome *:", self.name_column)
        mapping.addRow("Coluna Telefone *:", self.phone_column)
        mapping.addRow("Coluna E-mail:", self.email_column)
        mapping.addRow("Coluna CPF/CNPJ:", self.document_column)
        mapping.addRow("Coluna Endereço:", self.address_column)
        layout.addWidget(mapping_frame)

        self.summary = QLabel("Nenhum arquivo selecionado.")
        self.summary.setObjectName("SummaryLabel")
        layout.addWidget(self.summary)

        self.table = ModernTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Linha", "Nome", "Telefone", "Resultado / Validação"])
        self.table.setMinimumHeight(200)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.table.setColumnWidth(1, 160)
        self.table.setColumnWidth(2, 140)
        layout.addWidget(self.table, 1)

        self.buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        self.save_btn = self.buttons.button(QDialogButtonBox.Save)
        self.save_btn.setText("Confirmar e Gravar")
        self.save_btn.setObjectName("PrimaryButton")
        self.save_btn.setIcon(get_icon("circle-check", color="#ffffff", size=ICON_SIZES.SM))
        self.save_btn.setEnabled(False)
        cancel_btn = self.buttons.button(QDialogButtonBox.Cancel)
        cancel_btn.setText("Cancelar")
        cancel_btn.setIcon(get_icon("x-circle", color=get_current_palette().TEXT_PRIMARY, size=ICON_SIZES.SM))

        self.buttons.accepted.connect(self.commit)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)

    def select_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Selecionar Arquivo", "", "Planilhas (*.csv *.xlsx)")
        if not path:
            return
        try:
            self.headers, self.rows = read_table(path)
        except Exception as error:
            QMessageBox.critical(self, "Erro ao ler arquivo", str(error))
            return

        for combo in (self.name_column, self.phone_column, self.email_column, self.document_column, self.address_column):
            combo.blockSignals(True)
            combo.clear()
            combo.addItem("")
            combo.addItems(self.headers)
            combo.blockSignals(False)

        self._select_likely(self.name_column, ["nome", "name", "cliente", "razao_social", "razao social"])
        self._select_likely(self.phone_column, ["telefone", "celular", "fone", "phone", "tel"])
        self._select_likely(self.email_column, ["email", "e-mail", "mail"])
        self._select_likely(self.document_column, ["cpf", "cnpj", "documento", "doc"])
        self._select_likely(self.address_column, ["endereco", "endereço", "rua", "address"])
        self.review()

    @staticmethod
    def _select_likely(combo: QComboBox, candidates: list[str]) -> None:
        for index in range(combo.count()):
            if combo.itemText(index).strip().casefold() in candidates:
                combo.setCurrentIndex(index)
                return

    def review(self) -> None:
        if not self.rows:
            return
        mapping = {
            "nome": self.name_column.currentText(),
            "telefone": self.phone_column.currentText(),
            "email": self.email_column.currentText(),
            "documento": self.document_column.currentText(),
            "endereco": self.address_column.currentText(),
        }
        self.approved, rejected = validate_customers(self.rows, mapping, self.repository.customer_duplicate)
        self.table.setRowCount(0)
        preview = [(item["linha"], item["dados"], f"Rejeitado: {item['motivo']}") for item in rejected]
        preview += [("-", item, "Aprovado: Pronto para importar") for item in self.approved]

        for line, item, result in preview[:250]:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(str(line)))
            self.table.setItem(row, 1, QTableWidgetItem(str(item.get("nome", ""))))
            self.table.setItem(row, 2, QTableWidgetItem(str(item.get("telefone", ""))))
            self.table.setItem(row, 3, QTableWidgetItem(str(result)))

        self.summary.setText(
            f"{len(self.rows)} registros analisados: {len(self.approved)} válidos e {len(rejected)} com avisos/rejeitados."
        )
        self.save_btn.setEnabled(bool(self.approved))

    def commit(self) -> None:
        if QMessageBox.question(
            self,
            "Confirmar Importação",
            f"Deseja gravar {len(self.approved)} clientes no banco de dados?",
        ) != QMessageBox.Yes:
            return
        count = self.repository.import_customers(self.approved)
        QMessageBox.information(self, "Sucesso", f"{count} clientes foram importados com sucesso!")
        self.accept()


class MainWindow(QMainWindow):
    def __init__(self, database, current_user: dict | None = None):
        super().__init__()
        self.current_user = current_user or {"id": 1, "nome": "Administrador", "perfil": "Gestor"}
        self.perfil = self.current_user.get("perfil", "Gestor")
        self.repository = Repository(database, current_user=self.current_user)
        self.requested_logout = False

        self.setWindowTitle("Orby — Gestão Operacional para Pequenas Empresas e Serviços")
        self.resize(1300, 840)
        self.setMinimumSize(960, 540)

        root = QWidget()
        root.setObjectName("CentralWidget")
        self.setCentralWidget(root)

        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(SPACING.LG + 2, SPACING.LG, SPACING.LG + 2, SPACING.LG)
        root_layout.setSpacing(SPACING.MD + 2)

        # --- Top Header Bar com Barra de Pesquisa Oval Flutuante ---
        top_header = QHBoxLayout()
        top_header.setSpacing(SPACING.MD + 2)

        header_badge = QLabel("ORBY 2.0")
        header_badge.setObjectName("HeaderBadge")
        top_header.addWidget(header_badge)

        self.global_search = QLineEdit()
        self.global_search.setObjectName("GlobalSearch")
        self.global_search.addAction(get_icon("search", color=get_current_palette().TEXT_SECONDARY, size=16), QLineEdit.LeadingPosition)
        self.global_search.setPlaceholderText("Pesquisar em todo o sistema (clientes, OS, equipamentos)...")
        self.global_search.textChanged.connect(self.on_global_search)
        top_header.addWidget(self.global_search, 1)

        # Crachá do Operador Logado com Perfil RBAC
        user_frame = QFrame()
        user_frame.setObjectName("UserBadge")
        user_layout = QHBoxLayout(user_frame)
        user_layout.setContentsMargins(SPACING.SM + 2, SPACING.XS, SPACING.SM + 2, SPACING.XS)
        user_layout.setSpacing(SPACING.SM)
        badge_icon = "shield" if self.perfil == "Gestor" else ("wrench" if self.perfil == "Técnico" else "user")
        user_layout.addWidget(IconWidget(badge_icon, size=ICON_SIZES.SM))
        user_lbl = QLabel(f"<b>{self.current_user.get('nome', 'Usuário')}</b> ({self.perfil})")
        user_lbl.setObjectName("UserBadgeLabel")
        user_layout.addWidget(user_lbl)
        top_header.addWidget(user_frame)

        # Badge de Sistema Online com ícone SVG
        online_frame = QFrame()
        online_frame.setObjectName("OnlineBadge")
        online_layout = QHBoxLayout(online_frame)
        online_layout.setContentsMargins(SPACING.SM, SPACING.XS, SPACING.SM + 2, SPACING.XS)
        online_layout.setSpacing(SPACING.XS + 2)
        online_icon = IconWidget("circle-check", color=get_current_palette().SUCCESS, size=ICON_SIZES.SM)
        online_text = QLabel("Sistema Operacional Pronto")
        online_layout.addWidget(online_icon)
        online_layout.addWidget(online_text)
        top_header.addWidget(online_frame)

        root_layout.addLayout(top_header)

        # --- Corpo Principal (Sidebar Flutuante + Conteúdo Glass) ---
        body_layout = QHBoxLayout()
        body_layout.setSpacing(SPACING.LG)

        # Barra lateral Frutiger Aero (Estilo Dock com proporções responsivas)
        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(DIMENSIONS.SIDEBAR_WIDTH)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(SPACING.MD, SPACING.LG, SPACING.MD, SPACING.MD)
        sidebar_layout.setSpacing(SPACING.XS + 2)

        # Topo da Sidebar com Ícone Esférico 3D adaptativo
        logo_box = QHBoxLayout()
        logo_box.setSpacing(SPACING.SM)
        self.orb_logo = OrbLogoWidget()
        self.orb_logo.setFixedSize(50, 50)
        logo_text_box = QVBoxLayout()
        logo_text_box.setSpacing(0)
        logo_title = QLabel("ORBY")
        logo_title.setObjectName("LogoTitle")
        logo_title.setStyleSheet(f"font-size: 20px; font-weight: {TYPOGRAPHY.WEIGHT_EXTRABOLD}; letter-spacing: 1.5px;")
        logo_sub = QLabel("Gestão & Serviços")
        logo_sub.setObjectName("LogoSubtitle")
        logo_sub.setStyleSheet(f"font-size: 10px; font-weight: {TYPOGRAPHY.WEIGHT_BOLD}; letter-spacing: 1px;")
        logo_text_box.addWidget(logo_title)
        logo_text_box.addWidget(logo_sub)
        logo_box.addWidget(self.orb_logo)
        logo_box.addLayout(logo_text_box)
        logo_box.addStretch()

        sidebar_layout.addLayout(logo_box)
        sidebar_layout.addSpacing(SPACING.SM)

        # Botões de Navegação em Pílula com Ícones Lucide SVG
        self.nav_buttons: list[QPushButton] = []
        nav_items = [
            ("Dashboard", "layout-dashboard", 0),
            ("Financeiro", "chart", 1),
            ("Clientes", "users", 2),
            ("Equipamentos", "laptop", 3),
            ("Ordens de Serviço", "clipboard", 4),
            ("Configurações", "settings", 5),
        ]

        for text, icon_name, index in nav_items:
            btn = QPushButton(f"  {text}")
            btn.setObjectName("NavButton")
            btn.setIcon(get_icon(icon_name, size=ICON_SIZES.MD))
            btn.setIconSize(QSize(ICON_SIZES.MD, ICON_SIZES.MD))
            btn.setFixedHeight(36)
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked=False, i=index: self.open_page(i))
            sidebar_layout.addWidget(btn)
            self.nav_buttons.append(btn)

        sidebar_layout.addStretch()

        # Grade Mini Dock de Ações Rápidas (Organizado em 2 linhas harmônicas — sem sobreposição!)
        dock_label = QLabel("AÇÕES RÁPIDAS")
        dock_label.setObjectName("DockSectionLabel")
        dock_label.setAlignment(Qt.AlignCenter)
        sidebar_layout.addWidget(dock_label)

        # Linha 1 do Dock: Atualizar, Importar, Alternar Tema
        dock_row1 = QHBoxLayout()
        dock_row1.setSpacing(SPACING.SM + 2)
        dock_row1.setAlignment(Qt.AlignCenter)

        btn_refresh = QPushButton()
        btn_refresh.setObjectName("DockTile")
        btn_refresh.setIcon(get_icon("refresh-cw", size=ICON_SIZES.MD))
        btn_refresh.setIconSize(QSize(ICON_SIZES.MD, ICON_SIZES.MD))
        btn_refresh.setToolTip("Atualizar todos os dados do sistema")
        btn_refresh.clicked.connect(self.refresh_all)

        self.btn_import = QPushButton()
        self.btn_import.setObjectName("DockTile")
        self.btn_import.setIcon(get_icon("file-up", size=ICON_SIZES.MD))
        self.btn_import.setIconSize(QSize(ICON_SIZES.MD, ICON_SIZES.MD))
        self.btn_import.setToolTip("Importar planilha de clientes")
        self.btn_import.clicked.connect(self.import_customers)

        self.btn_theme = QPushButton()
        self.btn_theme.setObjectName("DockTile")
        self.update_theme_button_icon()
        self.btn_theme.setToolTip("Alternar modo escuro / claro")
        self.btn_theme.clicked.connect(self.toggle_dark_mode)

        dock_row1.addWidget(btn_refresh)
        dock_row1.addWidget(self.btn_import)
        dock_row1.addWidget(self.btn_theme)
        sidebar_layout.addLayout(dock_row1)

        # Linha 2 do Dock: Sobre e Encerrar Sessão
        dock_row2 = QHBoxLayout()
        dock_row2.setSpacing(SPACING.SM + 2)
        dock_row2.setAlignment(Qt.AlignCenter)

        btn_about = QPushButton()
        btn_about.setObjectName("DockTile")
        btn_about.setIcon(get_icon("info", size=ICON_SIZES.MD))
        btn_about.setIconSize(QSize(ICON_SIZES.MD, ICON_SIZES.MD))
        btn_about.setToolTip("Sobre o Orby")
        btn_about.clicked.connect(self.show_about)

        self.btn_logout = QPushButton()
        self.btn_logout.setObjectName("DockTile")
        self.btn_logout.setIcon(get_icon("log-out", size=ICON_SIZES.MD))
        self.btn_logout.setIconSize(QSize(ICON_SIZES.MD, ICON_SIZES.MD))
        self.btn_logout.setToolTip("Encerrar Sessão / Trocar Usuário")
        self.btn_logout.clicked.connect(self.logout)

        dock_row2.addWidget(btn_about)
        dock_row2.addWidget(self.btn_logout)
        sidebar_layout.addLayout(dock_row2)

        sidebar_layout.addSpacing(SPACING.XS)

        version_label = QLabel("Orby Desktop • v2.0")
        version_label.setObjectName("VersionLabel")
        version_label.setAlignment(Qt.AlignCenter)
        sidebar_layout.addWidget(version_label)

        body_layout.addWidget(sidebar)

        # Área de Conteúdo
        content_area = QWidget()
        content_layout = QVBoxLayout(content_area)
        content_layout.setContentsMargins(0, 0, 0, 0)

        self.pages = QStackedWidget()
        self.pages.addWidget(self._wrap_scroll(self.make_dashboard()))
        self.pages.addWidget(self._wrap_scroll(self.make_finance()))
        self.pages.addWidget(self.make_customers())
        self.pages.addWidget(self.make_equipment())
        self.pages.addWidget(self.make_orders())
        self.pages.addWidget(self._wrap_scroll(self.make_settings()))

        content_layout.addWidget(self.pages)
        body_layout.addWidget(content_area, 1)

        root_layout.addLayout(body_layout, 1)

        self._apply_permissions()
        self.open_page(0)

    def _wrap_scroll(self, widget: QWidget) -> QScrollArea:
        """Envolve uma página em QScrollArea para permitir rolagem suave em resoluções menores (1024x600 / 1366x768)."""
        scroll = QScrollArea()
        scroll.setObjectName("PageScrollArea")
        widget.setObjectName("PageScrollContent")
        scroll.setWidget(widget)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        # Desativa autoFillBackground que causava fundo preto em sistemas com Windows Dark Mode
        scroll.setAutoFillBackground(False)
        scroll.setAttribute(Qt.WA_TranslucentBackground, True)
        if scroll.viewport():
            scroll.viewport().setAutoFillBackground(False)
            scroll.viewport().setAttribute(Qt.WA_TranslucentBackground, True)
            scroll.viewport().setStyleSheet("background: transparent; border: none;")

        scroll.setStyleSheet(
            "QScrollArea#PageScrollArea, "
            "QScrollArea#PageScrollArea > QWidget#qt_scrollarea_viewport, "
            "QWidget#PageScrollContent { "
            "   background: transparent; "
            "   border: none; "
            "}"
        )
        widget.setStyleSheet("background: transparent;")
        return scroll

    def update_theme_button_icon(self) -> None:
        icon_name = "sun" if is_dark_mode() else "moon"
        self.btn_theme.setIcon(get_icon(icon_name, size=ICON_SIZES.MD))
        self.btn_theme.setIconSize(QSize(ICON_SIZES.MD, ICON_SIZES.MD))

    def on_global_search(self, text: str) -> None:
        term = text.strip()
        idx = self.pages.currentIndex()
        if idx == 2 and hasattr(self, "customer_search"):
            self.customer_search.setText(term)
        elif idx == 3 and hasattr(self, "equipment_search"):
            self.equipment_search.setText(term)
        elif idx == 4 and hasattr(self, "order_search"):
            self.order_search.setText(term)
        elif idx in (0, 1) and term:
            # Se o usuário digitou no Dashboard ou Financeiro, navegar para a tela mais relevante com base no perfil
            if self.perfil == "Técnico":
                target_page = 4  # Ordens de Serviço
            else:
                target_page = 2  # Clientes (Gestor/Atendente)
            self.open_page(target_page)
            if target_page == 2 and hasattr(self, "customer_search"):
                self.customer_search.setText(term)
            elif target_page == 4 and hasattr(self, "order_search"):
                self.order_search.setText(term)

    def toggle_dark_mode(self) -> None:
        app = QApplication.instance()
        if app:
            clear_icon_cache()
            toggle_theme(app)
            self.update_theme_button_icon()
            self.refresh_page(self.pages.currentIndex())

    def _apply_permissions(self) -> None:
        if self.perfil == "Técnico":
            self.nav_buttons[1].setVisible(False)  # Financeiro
            self.nav_buttons[2].setVisible(False)  # Clientes
            self.btn_import.setVisible(False)
            if len(self.nav_buttons) > 5:
                self.nav_buttons[5].setVisible(False)  # Configurações (Gestor exclusivo)
            if hasattr(self, "delete_equipment_btn"):
                self.delete_equipment_btn.setVisible(False)
            if hasattr(self, "delete_order_btn"):
                self.delete_order_btn.setVisible(False)
        elif self.perfil == "Atendente":
            self.nav_buttons[1].setVisible(False)  # Financeiro
            if len(self.nav_buttons) > 5:
                self.nav_buttons[5].setVisible(False)  # Configurações (Gestor exclusivo)
            if hasattr(self, "delete_customer_btn"):
                self.delete_customer_btn.setVisible(False)
            if hasattr(self, "delete_equipment_btn"):
                self.delete_equipment_btn.setVisible(False)
            if hasattr(self, "delete_order_btn"):
                self.delete_order_btn.setVisible(False)

    def logout(self) -> None:
        reply = QMessageBox.question(
            self,
            "Encerrar Sessão",
            f"Deseja desconectar a conta de {self.current_user.get('nome', 'Usuário')} e retornar à tela de login?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self.requested_logout = True
            self.close()

    def show_about(self) -> None:
        QMessageBox.information(
            self,
            "Sobre o Orby",
            "<h3>Orby — Gestão Operacional para Pequenas Empresas</h3>"
            "<p>Software corporativo completo para <b>prestadores de serviços, oficinas e assistências técnicas</b>.</p>"
            "<p>Design System Frutiger Aero • Controle de Acesso Baseado em Perfis (RBAC) • Auditoria Imutável • SQLite Local.</p>"
            f"<p><b>Operador Atual:</b> {self.current_user.get('nome', '')} ({self.perfil})<br>Versão 2.0 (2026)</p>",
        )

    def open_page(self, index: int) -> None:
        self.pages.setCurrentIndex(index)
        for i, btn in enumerate(self.nav_buttons):
            btn.setChecked(i == index)
            btn.setProperty("active", "true" if i == index else "false")
            btn.style().unpolish(btn)
            btn.style().polish(btn)
        self.refresh_page(index)

    def refresh_page(self, index: int) -> None:
        if index == 0:
            self.refresh_dashboard()
        elif index == 1:
            self.refresh_finance()
        elif index == 2:
            self.refresh_customers()
        elif index == 3:
            self.refresh_equipment()
        elif index == 4:
            self.refresh_orders()
        elif index == 5:
            self.refresh_settings()

    def make_dashboard(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(SPACING.MD + 2)

        # Painel de Métricas Operacionais com Ícones Lucide SVG
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(SPACING.MD + 2)

        self.card_abertas = MetricCard("OS em Aberto", "0", "clock")
        self.card_reparo = MetricCard("Em Reparo", "0", "wrench")
        self.card_atrasadas = MetricCard("OS Paradas / Alerta", "0", "alert-circle")
        self.card_finalizadas = MetricCard("Finalizadas", "0", "circle-check")
        self.card_faturamento = MetricCard("Faturamento (OS)", "R$ 0,00", "dollar-sign")

        cards_layout.addWidget(self.card_abertas)
        cards_layout.addWidget(self.card_reparo)
        cards_layout.addWidget(self.card_atrasadas)
        cards_layout.addWidget(self.card_finalizadas)
        cards_layout.addWidget(self.card_faturamento)
        layout.addLayout(cards_layout)

        # Container Glass para Tabela Recente
        table_card = ContentCard()
        table_layout = QVBoxLayout(table_card)
        table_layout.setContentsMargins(SPACING.LG + 2, SPACING.LG, SPACING.LG + 2, SPACING.LG)
        table_layout.setSpacing(SPACING.MD)

        header_box = QHBoxLayout()
        title = QLabel("Últimas Ordens de Serviço em Andamento")
        title.setObjectName("SectionSubtitle")
        header_box.addWidget(title)
        header_box.addStretch()

        new_os_btn = QPushButton("Abrir Nova OS")
        new_os_btn.setObjectName("PrimaryButton")
        new_os_btn.setIcon(get_icon("plus", color="#ffffff", size=ICON_SIZES.SM))
        new_os_btn.setIconSize(QSize(ICON_SIZES.SM, ICON_SIZES.SM))
        new_os_btn.clicked.connect(self.add_order)
        header_box.addWidget(new_os_btn)
        table_layout.addLayout(header_box)

        self.dash_table = ModernTableWidget(0, 6)
        self.dash_table.setHorizontalHeaderLabels(["OS", "Cliente", "Equipamento", "Status", "Valor Total", "Abertura"])
        self.dash_table.cellDoubleClicked.connect(lambda *_: self.edit_order_from_dashboard())
        table_layout.addWidget(self.dash_table)

        layout.addWidget(table_card, 1)
        return page

    def make_finance(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(SPACING.MD + 2)

        # Painel de Filtro e Título Financeiro
        header_card = ContentCard()
        h_layout = QHBoxLayout(header_card)
        h_layout.setContentsMargins(SPACING.LG + 2, SPACING.MD, SPACING.LG + 2, SPACING.MD)
        h_layout.setSpacing(SPACING.MD)

        title = QLabel("Painel Financeiro e Fechamento de Caixa")
        title.setObjectName("SectionSubtitle")
        h_layout.addWidget(title)
        h_layout.addStretch()

        lbl_periodo = QLabel("Período:")
        lbl_periodo.setObjectName("SummaryLabel")
        h_layout.addWidget(lbl_periodo)

        self.finance_period = QComboBox()
        self.finance_period.addItem("Todo o Período", "all")
        self.finance_period.addItem("Mês Atual", "month")
        self.finance_period.addItem("Últimos 7 Dias", "7days")
        self.finance_period.addItem("Hoje", "today")
        self.finance_period.currentIndexChanged.connect(self.refresh_finance)
        h_layout.addWidget(self.finance_period)

        btn_export_pdf = QPushButton("Exportar PDF")
        btn_export_pdf.setIcon(get_icon("chart", size=ICON_SIZES.SM))
        btn_export_pdf.setIconSize(QSize(ICON_SIZES.SM, ICON_SIZES.SM))
        btn_export_pdf.setToolTip("Exportar demonstrativo financeiro e fechamento em PDF")
        btn_export_pdf.clicked.connect(self.export_finance_pdf)
        h_layout.addWidget(btn_export_pdf)

        btn_export_csv = QPushButton("Exportar Excel (CSV)")
        btn_export_csv.setIcon(get_icon("clipboard", size=ICON_SIZES.SM))
        btn_export_csv.setIconSize(QSize(ICON_SIZES.SM, ICON_SIZES.SM))
        btn_export_csv.setToolTip("Exportar extrato analítico para planilha Excel (.csv)")
        btn_export_csv.clicked.connect(self.export_finance_csv)
        h_layout.addWidget(btn_export_csv)

        layout.addWidget(header_card)

        # Cartões de Métricas Financeiras com Ícones Lucide SVG
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(SPACING.MD + 2)

        self.card_fat_realizado = MetricCard("Faturamento Realizado", "R$ 0,00", "dollar-sign")
        self.card_rec_prevista = MetricCard("Receita Prevista (Aberto)", "R$ 0,00", "trending-up")
        self.card_ticket_medio = MetricCard("Ticket Médio por OS", "R$ 0,00", "tag")
        self.card_lucro_servicos = MetricCard("Mão de Obra (Serviços)", "R$ 0,00", "wrench")

        cards_layout.addWidget(self.card_fat_realizado)
        cards_layout.addWidget(self.card_rec_prevista)
        cards_layout.addWidget(self.card_ticket_medio)
        cards_layout.addWidget(self.card_lucro_servicos)
        layout.addLayout(cards_layout)

        # Corpo Central Dividido: Formas de Pagamento (Esq) + Extrato de Fechamento (Dir)
        mid_layout = QHBoxLayout()
        mid_layout.setSpacing(SPACING.MD + 2)

        # Quadro Formas de Pagamento
        pay_card = ContentCard()
        pay_card.setMinimumWidth(250)
        pay_card.setMaximumWidth(320)
        pay_layout = QVBoxLayout(pay_card)
        pay_layout.setContentsMargins(SPACING.LG, SPACING.MD + 2, SPACING.LG, SPACING.MD + 2)
        pay_layout.setSpacing(SPACING.SM + 2)

        pay_header = QHBoxLayout()
        pay_header.setSpacing(SPACING.SM)
        pay_icon = IconWidget("credit-card", size=ICON_SIZES.MD)
        pay_title = QLabel("Por Forma de Pagamento")
        pay_title.setObjectName("SectionSubtitle")
        pay_header.addWidget(pay_icon)
        pay_header.addWidget(pay_title)
        pay_header.addStretch()
        pay_layout.addLayout(pay_header)

        self.pay_table = ModernTableWidget(0, 3)
        self.pay_table.setHorizontalHeaderLabels(["Forma", "Qtd", "Total"])
        self.pay_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.pay_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.pay_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        pay_layout.addWidget(self.pay_table)
        mid_layout.addWidget(pay_card)

        # Quadro Extrato de Transações Finalizadas
        extrato_card = ContentCard()
        extrato_layout = QVBoxLayout(extrato_card)
        extrato_layout.setContentsMargins(SPACING.LG + 2, SPACING.MD + 2, SPACING.LG + 2, SPACING.MD + 2)
        extrato_layout.setSpacing(SPACING.SM + 2)

        ext_header = QHBoxLayout()
        ext_header.setSpacing(SPACING.SM)
        ext_icon = IconWidget("clipboard", size=ICON_SIZES.MD)
        ext_title = QLabel("Extrato de Ordens Finalizadas (Receita Realizada)")
        ext_title.setObjectName("SectionSubtitle")
        ext_header.addWidget(ext_icon)
        ext_header.addWidget(ext_title)
        ext_header.addStretch()
        extrato_layout.addLayout(ext_header)

        self.extrato_table = ModernTableWidget(0, 7)
        self.extrato_table.setHorizontalHeaderLabels(["OS", "Cliente", "Equipamento", "Serviço", "Peças", "Total", "Pagamento"])
        self.extrato_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.extrato_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.extrato_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.extrato_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.extrato_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.extrato_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.extrato_table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeToContents)
        extrato_layout.addWidget(self.extrato_table)
        mid_layout.addWidget(extrato_card, 1)

        layout.addLayout(mid_layout, 1)
        return page

    def make_customers(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(SPACING.MD + 2)

        card = ContentCard()
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(SPACING.XL, SPACING.LG + 2, SPACING.XL, SPACING.LG + 2)
        card_layout.setSpacing(SPACING.MD + 2)

        header = QHBoxLayout()
        title = QLabel("Gestão de Clientes")
        title.setObjectName("SectionTitle")
        header.addWidget(title)
        header.addStretch()

        add_btn = QPushButton("Novo Cliente")
        add_btn.setObjectName("PrimaryButton")
        add_btn.setIcon(get_icon("plus", color="#ffffff", size=ICON_SIZES.SM))
        add_btn.setIconSize(QSize(ICON_SIZES.SM, ICON_SIZES.SM))
        add_btn.clicked.connect(self.add_customer)

        import_btn = QPushButton("Importar Planilha")
        import_btn.setIcon(get_icon("file-up", size=ICON_SIZES.SM))
        import_btn.setIconSize(QSize(ICON_SIZES.SM, ICON_SIZES.SM))
        import_btn.clicked.connect(self.import_customers)

        header.addWidget(add_btn)
        header.addWidget(import_btn)
        card_layout.addLayout(header)

        self.customer_search = QLineEdit()
        self.customer_search.setObjectName("PillSearch")
        self.customer_search.addAction(get_icon("search", color=get_current_palette().TEXT_SECONDARY, size=14), QLineEdit.LeadingPosition)
        self.customer_search.setPlaceholderText("Filtrar clientes por nome, telefone, e-mail ou documento...")
        self.customer_search.textChanged.connect(self.refresh_customers)
        card_layout.addWidget(self.customer_search)

        self.customer_table = ModernTableWidget(0, 5)
        self.customer_table.setHorizontalHeaderLabels(["ID", "Nome", "Telefone", "E-mail", "CPF/CNPJ"])
        self.customer_table.cellDoubleClicked.connect(lambda *_: self.edit_customer())
        card_layout.addWidget(self.customer_table)

        actions = QHBoxLayout()
        edit_btn = QPushButton("Editar Cliente")
        edit_btn.setIcon(get_icon("pencil", size=ICON_SIZES.SM))
        edit_btn.setIconSize(QSize(ICON_SIZES.SM, ICON_SIZES.SM))
        edit_btn.clicked.connect(self.edit_customer)

        self.delete_customer_btn = QPushButton("Excluir Cliente")
        self.delete_customer_btn.setIcon(get_icon("trash", size=ICON_SIZES.SM))
        self.delete_customer_btn.setIconSize(QSize(ICON_SIZES.SM, ICON_SIZES.SM))
        self.delete_customer_btn.clicked.connect(self.delete_customer)

        actions.addWidget(edit_btn)
        actions.addWidget(self.delete_customer_btn)
        actions.addStretch()
        card_layout.addLayout(actions)

        layout.addWidget(card, 1)
        return page

    def make_equipment(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(SPACING.MD + 2)

        card = ContentCard()
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(SPACING.XL, SPACING.LG + 2, SPACING.XL, SPACING.LG + 2)
        card_layout.setSpacing(SPACING.MD + 2)

        header = QHBoxLayout()
        title = QLabel("Equipamentos em Atendimento")
        title.setObjectName("SectionTitle")
        header.addWidget(title)
        header.addStretch()

        add_btn = QPushButton("Novo Equipamento")
        add_btn.setObjectName("PrimaryButton")
        add_btn.setIcon(get_icon("plus", color="#ffffff", size=ICON_SIZES.SM))
        add_btn.setIconSize(QSize(ICON_SIZES.SM, ICON_SIZES.SM))
        add_btn.clicked.connect(self.add_equipment)
        header.addWidget(add_btn)
        card_layout.addLayout(header)

        filter_bar = QHBoxLayout()
        self.equipment_search = QLineEdit()
        self.equipment_search.setObjectName("PillSearch")
        self.equipment_search.addAction(get_icon("search", color=get_current_palette().TEXT_SECONDARY, size=14), QLineEdit.LeadingPosition)
        self.equipment_search.setPlaceholderText("Filtrar por tipo, marca, modelo, série ou cliente...")
        self.equipment_search.textChanged.connect(self.refresh_equipment)
        filter_bar.addWidget(self.equipment_search)
        card_layout.addLayout(filter_bar)

        self.equipment_table = ModernTableWidget(0, 5)
        self.equipment_table.setHorizontalHeaderLabels(["ID", "Cliente", "Tipo", "Marca / Modelo", "Nº de Série"])
        self.equipment_table.cellDoubleClicked.connect(lambda *_: self.edit_equipment())
        card_layout.addWidget(self.equipment_table)

        actions = QHBoxLayout()
        self.edit_equipment_btn = QPushButton("Editar Equipamento")
        self.edit_equipment_btn.setIcon(get_icon("edit", size=ICON_SIZES.SM))
        self.edit_equipment_btn.setIconSize(QSize(ICON_SIZES.SM, ICON_SIZES.SM))
        self.edit_equipment_btn.clicked.connect(self.edit_equipment)
        actions.addWidget(self.edit_equipment_btn)

        self.history_equipment_btn = QPushButton("Histórico de Manutenções")
        self.history_equipment_btn.setIcon(get_icon("clock", size=ICON_SIZES.SM))
        self.history_equipment_btn.setIconSize(QSize(ICON_SIZES.SM, ICON_SIZES.SM))
        self.history_equipment_btn.setToolTip("Ver todas as ordens de serviço anteriores deste aparelho")
        self.history_equipment_btn.clicked.connect(self.show_equipment_orders_history)
        actions.addWidget(self.history_equipment_btn)

        self.delete_equipment_btn = QPushButton("Excluir Equipamento")
        self.delete_equipment_btn.setIcon(get_icon("trash", size=ICON_SIZES.SM))
        self.delete_equipment_btn.setIconSize(QSize(ICON_SIZES.SM, ICON_SIZES.SM))
        self.delete_equipment_btn.clicked.connect(self.delete_equipment)
        actions.addWidget(self.delete_equipment_btn)
        actions.addStretch()
        card_layout.addLayout(actions)

        layout.addWidget(card, 1)
        return page

    def make_orders(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(SPACING.MD + 2)

        card = ContentCard()
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(SPACING.XL, SPACING.LG + 2, SPACING.XL, SPACING.LG + 2)
        card_layout.setSpacing(SPACING.MD + 2)

        header = QHBoxLayout()
        title = QLabel("Ordens de Serviço")
        title.setObjectName("SectionTitle")
        header.addWidget(title)
        header.addStretch()

        add_btn = QPushButton("Nova OS")
        add_btn.setObjectName("PrimaryButton")
        add_btn.setIcon(get_icon("plus", color="#ffffff", size=ICON_SIZES.SM))
        add_btn.setIconSize(QSize(ICON_SIZES.SM, ICON_SIZES.SM))
        add_btn.clicked.connect(self.add_order)
        header.addWidget(add_btn)
        card_layout.addLayout(header)

        filter_bar = QHBoxLayout()
        self.order_search = QLineEdit()
        self.order_search.setObjectName("PillSearch")
        self.order_search.addAction(get_icon("search", color=get_current_palette().TEXT_SECONDARY, size=14), QLineEdit.LeadingPosition)
        self.order_search.setPlaceholderText("Filtrar por código da OS, cliente, equipamento ou serviço...")
        self.order_search.textChanged.connect(self.refresh_orders)

        self.status_filter = QComboBox()
        self.status_filter.addItem("Todos os Status", "")
        self.status_filter.addItem("⚠️ Paradas / Atrasadas (>5 dias)", "delayed")
        for status in StatusOS.all_values():
            self.status_filter.addItem(status, status)
        self.status_filter.currentIndexChanged.connect(self.refresh_orders)

        filter_bar.addWidget(self.order_search, 2)
        filter_bar.addWidget(self.status_filter, 1)
        card_layout.addLayout(filter_bar)

        self.order_table = ModernTableWidget(0, 8)
        self.order_table.setHorizontalHeaderLabels(["OS", "Cliente", "Equipamento", "Descrição", "Status", "Serviço", "Peças", "Total (R$)"])
        self.order_table.cellDoubleClicked.connect(lambda *_: self.edit_order())
        card_layout.addWidget(self.order_table)

        actions = QHBoxLayout()
        edit_btn = QPushButton("Editar OS")
        edit_btn.setIcon(get_icon("pencil", size=ICON_SIZES.SM))
        edit_btn.setIconSize(QSize(ICON_SIZES.SM, ICON_SIZES.SM))
        edit_btn.clicked.connect(self.edit_order)

        timeline_btn = QPushButton("Linha do Tempo / Histórico")
        timeline_btn.setIcon(get_icon("clock", size=ICON_SIZES.SM))
        timeline_btn.setIconSize(QSize(ICON_SIZES.SM, ICON_SIZES.SM))
        timeline_btn.clicked.connect(self.show_timeline)

        self.delete_order_btn = QPushButton("Excluir OS")
        self.delete_order_btn.setIcon(get_icon("trash", size=ICON_SIZES.SM))
        self.delete_order_btn.setIconSize(QSize(ICON_SIZES.SM, ICON_SIZES.SM))
        self.delete_order_btn.clicked.connect(self.delete_order)

        btn_print_entry = QPushButton("Comprovante de Entrada")
        btn_print_entry.setIcon(get_icon("file-up", size=ICON_SIZES.SM))
        btn_print_entry.setIconSize(QSize(ICON_SIZES.SM, ICON_SIZES.SM))
        btn_print_entry.setToolTip("Emitir comprovante de entrada para assinatura do cliente")
        btn_print_entry.clicked.connect(self.print_entry_receipt)

        btn_print_exit = QPushButton("Recibo / Laudo de Saída")
        btn_print_exit.setIcon(get_icon("circle-check", size=ICON_SIZES.SM))
        btn_print_exit.setIconSize(QSize(ICON_SIZES.SM, ICON_SIZES.SM))
        btn_print_exit.setToolTip("Emitir recibo de saída, laudo técnico e termo de garantia")
        btn_print_exit.clicked.connect(self.print_exit_receipt)

        btn_order_history = QPushButton("Histórico do Aparelho")
        btn_order_history.setIcon(get_icon("laptop", size=ICON_SIZES.SM))
        btn_order_history.setIconSize(QSize(ICON_SIZES.SM, ICON_SIZES.SM))
        btn_order_history.setToolTip("Ver manutenções anteriores do mesmo equipamento")
        btn_order_history.clicked.connect(self.show_selected_order_equipment_history)

        actions.addWidget(edit_btn)
        actions.addWidget(timeline_btn)
        actions.addWidget(btn_order_history)
        actions.addWidget(btn_print_entry)
        actions.addWidget(btn_print_exit)
        actions.addWidget(self.delete_order_btn)
        actions.addStretch()
        card_layout.addLayout(actions)

        layout.addWidget(card, 1)
        return page

    def refresh_all(self) -> None:
        self.refresh_dashboard()
        self.refresh_finance()
        self.refresh_customers()
        self.refresh_equipment()
        self.refresh_orders()

    def refresh_dashboard(self) -> None:
        data = self.repository.dashboard()
        self.card_abertas.set_value(str(data.get("abertas") or 0))
        self.card_reparo.set_value(str(data.get("em_reparo") or 0))
        self.card_finalizadas.set_value(str(data.get("finalizadas") or 0))

        atrasadas = data.get("atrasadas") or 0
        self.card_atrasadas.set_value(str(atrasadas))
        if atrasadas > 0:
            self.card_atrasadas.value_label.setStyleSheet(f"font-size: 20px; font-weight: {TYPOGRAPHY.WEIGHT_BLACK}; color: #e11d48;")
        else:
            self.card_atrasadas.value_label.setStyleSheet(f"font-size: 20px; font-weight: {TYPOGRAPHY.WEIGHT_BLACK}; color: {get_current_palette().TEXT_PRIMARY};")

        if self.perfil != "Gestor":
            self.card_faturamento.set_value("Restrito")
        else:
            self.card_faturamento.set_value(formatar_moeda(data.get("faturamento")))

        # Filtrar apenas OS realmente em andamento (excluindo Finalizadas e Canceladas)
        orders = [o for o in self.repository.orders() if o["status"] not in ("Finalizada", "Cancelada")][:10]
        self.dash_table.setRowCount(0)
        for item in orders:
            row = self.dash_table.rowCount()
            self.dash_table.insertRow(row)

            os_txt = f"OS-{item['id']:04d}"
            if item.get("em_atraso"):
                os_txt += " ⚠️"
            os_item = QTableWidgetItem(os_txt)
            os_item.setData(Qt.UserRole, int(item["id"]))
            if item.get("em_atraso"):
                os_item.setToolTip(f"⚠️ ATENÇÃO: Parada há {item.get('dias_parada', 0)} dias sem atualização de status!")
            self.dash_table.setItem(row, 0, os_item)
            self.dash_table.setItem(row, 1, QTableWidgetItem(item["cliente_nome"]))
            self.dash_table.setItem(row, 2, QTableWidgetItem(item["equipamento_nome"]))
            badge = StatusBadge(
                item["status"],
                is_delayed=item.get("em_atraso", False),
                days_delayed=item.get("dias_parada", 0),
            )
            self.dash_table.setCellWidget(row, 3, badge)
            valor_texto = "Restrito" if self.perfil == "Técnico" else formatar_moeda(item["valor"])
            self.dash_table.setItem(row, 4, QTableWidgetItem(valor_texto))
            self.dash_table.setItem(row, 5, QTableWidgetItem(item["data_abertura"][:10]))

    def refresh_finance(self) -> None:
        period = self.finance_period.currentData() if hasattr(self, "finance_period") else "all"
        fin = self.repository.financial_dashboard(period)

        self.card_fat_realizado.set_value(formatar_moeda(fin["faturamento_realizado"]))
        self.card_rec_prevista.set_value(formatar_moeda(fin["receita_prevista"]))
        self.card_ticket_medio.set_value(formatar_moeda(fin["ticket_medio"]))
        self.card_lucro_servicos.set_value(formatar_moeda(fin["total_servicos"]))

        # Formas de pagamento
        self.pay_table.setRowCount(0)
        for item in fin["formas_pagamento"]:
            row = self.pay_table.rowCount()
            self.pay_table.insertRow(row)
            self.pay_table.setItem(row, 0, QTableWidgetItem(item["forma"]))
            self.pay_table.setItem(row, 1, QTableWidgetItem(str(item["qtd"])))
            self.pay_table.setItem(row, 2, QTableWidgetItem(formatar_moeda(item["total"])))

        # Extrato
        self.extrato_table.setRowCount(0)
        for item in fin["extrato"]:
            row = self.extrato_table.rowCount()
            self.extrato_table.insertRow(row)
            self.extrato_table.setItem(row, 0, QTableWidgetItem(f"OS-{item['id']:04d}"))
            self.extrato_table.setItem(row, 1, QTableWidgetItem(item["cliente_nome"]))
            self.extrato_table.setItem(row, 2, QTableWidgetItem(item["equipamento_nome"]))
            self.extrato_table.setItem(row, 3, QTableWidgetItem(formatar_moeda(item.get("valor_servico"))))
            self.extrato_table.setItem(row, 4, QTableWidgetItem(formatar_moeda(item.get("valor_pecas"))))
            self.extrato_table.setItem(row, 5, QTableWidgetItem(formatar_moeda(item["valor"])))
            self.extrato_table.setItem(row, 6, QTableWidgetItem(item.get("forma_pagamento") or "—"))

    def refresh_customers(self) -> None:
        term = self.customer_search.text() if hasattr(self, "customer_search") else ""
        rows = self.repository.customers(term)
        self.customer_table.setRowCount(0)
        for item in rows:
            row = self.customer_table.rowCount()
            self.customer_table.insertRow(row)
            id_item = QTableWidgetItem(str(item["id"]))
            id_item.setData(Qt.UserRole, int(item["id"]))
            self.customer_table.setItem(row, 0, id_item)
            self.customer_table.setItem(row, 1, QTableWidgetItem(item["nome"]))
            self.customer_table.setItem(row, 2, QTableWidgetItem(item["telefone"]))
            self.customer_table.setItem(row, 3, QTableWidgetItem(item.get("email") or "—"))
            self.customer_table.setItem(row, 4, QTableWidgetItem(item.get("documento") or "—"))

    def refresh_orders(self) -> None:
        term = self.order_search.text() if hasattr(self, "order_search") else ""
        status = self.status_filter.currentData() if hasattr(self, "status_filter") else ""
        rows = self.repository.orders(term, status)
        self.order_table.setRowCount(0)
        for item in rows:
            row = self.order_table.rowCount()
            self.order_table.insertRow(row)

            os_txt = f"OS-{item['id']:04d}"
            if item.get("em_atraso"):
                os_txt += " ⚠️"
            os_item = QTableWidgetItem(os_txt)
            os_item.setData(Qt.UserRole, int(item["id"]))
            if item.get("em_atraso"):
                os_item.setToolTip(f"⚠️ ATENÇÃO: Esta OS está aberta há {item.get('dias_parada', 0)} dias sem movimentação de status!")
            self.order_table.setItem(row, 0, os_item)
            self.order_table.setItem(row, 1, QTableWidgetItem(item["cliente_nome"]))
            self.order_table.setItem(row, 2, QTableWidgetItem(item["equipamento_nome"]))
            self.order_table.setItem(row, 3, QTableWidgetItem(item["descricao"]))

            badge = StatusBadge(
                item["status"],
                is_delayed=item.get("em_atraso", False),
                days_delayed=item.get("dias_parada", 0),
            )
            self.order_table.setCellWidget(row, 4, badge)

            if self.perfil == "Técnico":
                self.order_table.setItem(row, 5, QTableWidgetItem("Restrito"))
                self.order_table.setItem(row, 6, QTableWidgetItem("Restrito"))
                self.order_table.setItem(row, 7, QTableWidgetItem("Restrito"))
            else:
                self.order_table.setItem(row, 5, QTableWidgetItem(formatar_moeda(item.get("valor_servico"))))
                self.order_table.setItem(row, 6, QTableWidgetItem(formatar_moeda(item.get("valor_pecas"))))
                self.order_table.setItem(row, 7, QTableWidgetItem(formatar_moeda(item["valor"])))

    def refresh_equipment(self) -> None:
        term = self.equipment_search.text() if hasattr(self, "equipment_search") else ""
        rows = self.repository.equipment(term=term)
        self.equipment_table.setRowCount(0)
        for item in rows:
            row = self.equipment_table.rowCount()
            self.equipment_table.insertRow(row)
            marca_modelo = " ".join(p for p in [item.get("marca"), item.get("modelo")] if p)
            id_item = QTableWidgetItem(str(item["id"]))
            id_item.setData(Qt.UserRole, int(item["id"]))
            self.equipment_table.setItem(row, 0, id_item)
            self.equipment_table.setItem(row, 1, QTableWidgetItem(item["cliente_nome"]))
            self.equipment_table.setItem(row, 2, QTableWidgetItem(item["tipo"]))
            self.equipment_table.setItem(row, 3, QTableWidgetItem(marca_modelo or "—"))
            self.equipment_table.setItem(row, 4, QTableWidgetItem(item.get("numero_serie") or "—"))

    def show_selected_order_equipment_history(self) -> None:
        order_id = self.selected_id(self.order_table)
        if not order_id:
            return
        order = self.repository.order(order_id)
        if not order or not order.get("equipamento_id"):
            QMessageBox.information(self, "Sem Equipamento", "Esta OS não possui equipamento vinculado.")
            return

        eq_id = order["equipamento_id"]
        eq = self.repository.single_equipment(eq_id)
        if not eq:
            QMessageBox.warning(self, "Não Encontrado", "Equipamento não localizado no sistema.")
            return

        history = self.repository.orders_by_equipment(eq_id)
        dlg = EquipmentHistoryDialog(eq, history, self)
        dlg.exec()

    def show_equipment_orders_history(self) -> None:
        eq_id = self.selected_id(self.equipment_table)
        if not eq_id:
            return

        eq = self.repository.single_equipment(eq_id)
        if not eq:
            QMessageBox.warning(self, "Não Encontrado", "Equipamento não localizado no sistema.")
            return

        history = self.repository.orders_by_equipment(eq_id)
        dlg = EquipmentHistoryDialog(eq, history, self)
        dlg.exec()

    def edit_equipment(self) -> None:
        item_id = self.selected_id(self.equipment_table)
        if item_id is None:
            return
        customers = self.repository.customers()
        equipment = self.repository.single_equipment(item_id)
        if not equipment:
            return
        dialog = EquipmentDialog(self, customers, equipment=equipment)
        if dialog.exec():
            try:
                self.repository.update_equipment(item_id, *dialog.values())
                self.refresh_all()
            except PermissionDeniedError as error:
                QMessageBox.critical(self, "Acesso Negado", str(error))
            except ValueError as error:
                QMessageBox.warning(self, "Equipamento Inválido", str(error))

    def edit_order_from_dashboard(self) -> None:
        item_id = self.selected_id(self.dash_table)
        if item_id is None:
            return
        order = self.repository.order(item_id)
        if not order:
            return
        dialog = OrderDialog(self, self.repository.customers(), order)
        if dialog.exec():
            try:
                self.repository.update_order(item_id, *dialog.values())
                self.refresh_all()
            except PermissionDeniedError as error:
                QMessageBox.critical(self, "Acesso Negado", str(error))
            except ValueError as error:
                QMessageBox.warning(self, "OS Inválida", str(error))

    def selected_id(self, table: QTableWidget) -> int | None:
        row = table.currentRow()
        if row < 0:
            selected_items = table.selectedItems()
            if selected_items:
                row = selected_items[0].row()
            else:
                selected_indexes = table.selectedIndexes()
                if selected_indexes:
                    row = selected_indexes[0].row()

        if row < 0 or row >= table.rowCount():
            QMessageBox.information(self, "Seleção Necessária", "Por favor, selecione uma linha na tabela para continuar.")
            return None

        item = table.item(row, 0)
        if not item:
            return None

        # 1. Recupera ID armazenado diretamente em UserRole
        val = item.data(Qt.UserRole)
        if val is not None:
            try:
                return int(val)
            except (ValueError, TypeError):
                pass

        # 2. Extrai dígitos mesmo com prefixo ('OS-'), sufixos e emojis ('⚠️')
        raw_text = item.text().strip()
        match = re.search(r"\d+", raw_text)
        if match:
            return int(match.group(0))

        QMessageBox.warning(self, "Registro Inválido", "Não foi possível identificar o código do registro selecionado.")
        return None

    def add_customer(self) -> None:
        dialog = CustomerDialog(self)
        if dialog.exec():
            try:
                self.repository.add_customer(*dialog.values())
                self.refresh_all()
            except ValueError as error:
                QMessageBox.warning(self, "Cadastro Inválido", str(error))

    def edit_customer(self) -> None:
        item_id = self.selected_id(self.customer_table)
        if item_id is None:
            return
        customer_data = self.repository.customer(item_id)
        if not customer_data:
            return
        dialog = CustomerDialog(self, customer_data)
        if dialog.exec():
            try:
                self.repository.update_customer(item_id, *dialog.values())
                self.refresh_all()
            except ValueError as error:
                QMessageBox.warning(self, "Erro ao Atualizar", str(error))

    def delete_customer(self) -> None:
        item_id = self.selected_id(self.customer_table)
        if item_id is None:
            return
        if QMessageBox.question(self, "Confirmar Exclusão", "Deseja realmente excluir o cliente selecionado?") != QMessageBox.Yes:
            return
        try:
            ok, message = self.repository.delete_customer(item_id)
            (QMessageBox.information if ok else QMessageBox.warning)(self, "Clientes", message)
            self.refresh_all()
        except PermissionDeniedError as error:
            QMessageBox.critical(self, "Acesso Negado", str(error))

    def import_customers(self) -> None:
        if ImportDialog(self, self.repository).exec():
            self.refresh_all()

    def add_equipment(self) -> None:
        customers = self.repository.customers()
        if not customers:
            QMessageBox.information(self, "Clientes Necessários", "Cadastre ao menos um cliente antes de registrar um equipamento.")
            return
        dialog = EquipmentDialog(self, customers)
        if dialog.exec():
            try:
                self.repository.add_equipment(*dialog.values())
                self.refresh_all()
            except PermissionDeniedError as error:
                QMessageBox.critical(self, "Acesso Negado", str(error))
            except ValueError as error:
                QMessageBox.warning(self, "Equipamento Inválido", str(error))

    def delete_equipment(self) -> None:
        item_id = self.selected_id(self.equipment_table)
        if item_id is None:
            return
        if QMessageBox.question(
            self,
            "Confirmar Exclusão",
            "Deseja realmente excluir o equipamento selecionado?",
        ) != QMessageBox.Yes:
            return
        try:
            ok, message = self.repository.delete_equipment(item_id)
            (QMessageBox.information if ok else QMessageBox.warning)(self, "Equipamentos", message)
            self.refresh_all()
        except PermissionDeniedError as error:
            QMessageBox.critical(self, "Acesso Negado", str(error))

    def add_order(self) -> None:
        customers = self.repository.customers()
        if not customers or not self.repository.equipment():
            QMessageBox.information(self, "Cadastros Necessários", "É necessário ter ao menos um cliente e um equipamento cadastrados para abrir uma OS.")
            return
        dialog = OrderDialog(self, customers)
        if dialog.exec():
            try:
                self.repository.add_order(*dialog.values())
                self.refresh_all()
            except PermissionDeniedError as error:
                QMessageBox.critical(self, "Acesso Negado", str(error))
            except ValueError as error:
                QMessageBox.warning(self, "OS Inválida", str(error))

    def edit_order(self) -> None:
        item_id = self.selected_id(self.order_table)
        if item_id is None:
            return
        order = self.repository.order(item_id)
        if not order:
            return
        dialog = OrderDialog(self, self.repository.customers(), order)
        if dialog.exec():
            try:
                self.repository.update_order(item_id, *dialog.values())
                self.refresh_all()
            except PermissionDeniedError as error:
                QMessageBox.critical(self, "Acesso Negado", str(error))
            except ValueError as error:
                QMessageBox.warning(self, "OS Inválida", str(error))

    def show_timeline(self) -> None:
        item_id = self.selected_id(self.order_table)
        if item_id is None:
            return
        history = self.repository.order_history(item_id)
        order_info = self.repository.order(item_id)
        TimelineDialog(self, item_id, history, order_info).exec()

    def delete_order(self) -> None:
        item_id = self.selected_id(self.order_table)
        if item_id is None:
            return
        if QMessageBox.question(self, "Confirmar Exclusão", f"Deseja realmente excluir a OS-{item_id:04d}?") != QMessageBox.Yes:
            return
        try:
            self.repository.delete_order(item_id)
            self.refresh_all()
        except PermissionDeniedError as error:
            QMessageBox.critical(self, "Acesso Negado", str(error))

    def closeEvent(self, event) -> None:
        try:
            auto_bck = self.repository.database.get_setting("auto_backup_on_exit", "true").lower() == "true"
            if auto_bck:
                manager = BackupManager(db_path=self.repository.database.path)
                manager.perform_auto_backup_on_exit()
        except Exception:
            pass
        event.accept()

    def make_settings(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(SPACING.MD)

        # Cabeçalho da Seção com Sub-abas de Navegação
        header_card = ContentCard()
        h_layout = QHBoxLayout(header_card)
        h_layout.setContentsMargins(SPACING.LG + 2, SPACING.MD, SPACING.LG + 2, SPACING.MD)
        h_layout.setSpacing(SPACING.MD)

        title_box = QVBoxLayout()
        title_box.setSpacing(SPACING.XXS)
        title = QLabel("Painel Administrativo & Configurações")
        title.setObjectName("SectionTitle")
        subtitle = QLabel("Gestão de Segurança, Cópias de Backup, Usuários (RBAC) e Dados Comerciais")
        subtitle.setObjectName("SummaryLabel")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        h_layout.addLayout(title_box)
        h_layout.addStretch()

        # Botões de alternância de sub-aba
        self.settings_tab_buttons = []
        tabs_info = [
            ("Backup & Banco", "database", 0),
            ("Usuários & Acessos", "users", 1),
            ("Dados da Empresa", "settings", 2),
        ]
        for label, icon_name, idx in tabs_info:
            btn = QPushButton(f"  {label}")
            btn.setIcon(get_icon(icon_name, size=ICON_SIZES.SM))
            btn.setIconSize(QSize(ICON_SIZES.SM, ICON_SIZES.SM))
            btn.setCheckable(True)
            btn.setChecked(idx == 0)
            if idx == 0:
                btn.setObjectName("PrimaryButton")
            btn.clicked.connect(lambda checked=False, i=idx: self.switch_settings_tab(i))
            h_layout.addWidget(btn)
            self.settings_tab_buttons.append(btn)

        layout.addWidget(header_card)

        # QStackedWidget contendo as 3 páginas de configurações
        self.settings_stack = QStackedWidget()
        self.settings_stack.addWidget(self._make_settings_backup_page())
        self.settings_stack.addWidget(self._make_settings_users_page())
        self.settings_stack.addWidget(self._make_settings_company_page())

        layout.addWidget(self.settings_stack, 1)
        return page

    def switch_settings_tab(self, index: int) -> None:
        self.settings_stack.setCurrentIndex(index)
        for i, btn in enumerate(self.settings_tab_buttons):
            is_active = (i == index)
            btn.setChecked(is_active)
            btn.setObjectName("PrimaryButton" if is_active else "SecondaryButton")
            btn.style().unpolish(btn)
            btn.style().polish(btn)

        if index == 0:
            self.refresh_settings_backup()
        elif index == 1:
            self.refresh_users()
        elif index == 2:
            self.load_company_settings()

    def _make_settings_backup_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(SPACING.MD)

        # 1. Status do Banco de Dados
        db_card = ContentCard()
        db_layout = QVBoxLayout(db_card)
        db_layout.setContentsMargins(SPACING.XL, SPACING.LG, SPACING.XL, SPACING.LG)
        db_layout.setSpacing(SPACING.SM + 2)

        db_title = QLabel("Status do Banco de Dados Local (SQLite)")
        db_title.setObjectName("SectionSubtitle")
        db_layout.addWidget(db_title)

        self.lbl_db_path = QLabel("Localização: %APPDATA%/Orby/orby.db")
        self.lbl_db_path.setStyleSheet("font-family: Consolas, monospace; color: #0284c7; font-weight: bold;")
        db_layout.addWidget(self.lbl_db_path)

        self.lbl_db_stats = QLabel("Tamanho: Calculando... • Última Modificação: Calculando...")
        self.lbl_db_stats.setObjectName("SummaryLabel")
        db_layout.addWidget(self.lbl_db_stats)

        self.lbl_db_counts = QLabel("Clientes: 0 • Equipamentos: 0 • Ordens de Serviço: 0 • Usuários: 0")
        self.lbl_db_counts.setObjectName("SummaryLabel")
        db_layout.addWidget(self.lbl_db_counts)

        layout.addWidget(db_card)

        # 2. Ações de Backup
        action_card = ContentCard()
        action_layout = QVBoxLayout(action_card)
        action_layout.setContentsMargins(SPACING.XL, SPACING.LG, SPACING.XL, SPACING.LG)
        action_layout.setSpacing(SPACING.MD)

        act_title = QLabel("Rotinas de Backup e Proteção")
        act_title.setObjectName("SectionSubtitle")
        action_layout.addWidget(act_title)

        btns_layout = QHBoxLayout()
        btns_layout.setSpacing(SPACING.MD)

        btn_backup_manual = QPushButton("Fazer Backup Manual (.zip / .db)")
        btn_backup_manual.setObjectName("PrimaryButton")
        btn_backup_manual.setIcon(get_icon("file-up", color="#ffffff", size=ICON_SIZES.SM))
        btn_backup_manual.setIconSize(QSize(ICON_SIZES.SM, ICON_SIZES.SM))
        btn_backup_manual.clicked.connect(self.do_manual_backup)
        btns_layout.addWidget(btn_backup_manual)

        btn_backup_quick = QPushButton("Backup Rápido (1 Clique)")
        btn_backup_quick.setIcon(get_icon("shield", size=ICON_SIZES.SM))
        btn_backup_quick.setIconSize(QSize(ICON_SIZES.SM, ICON_SIZES.SM))
        btn_backup_quick.clicked.connect(self.do_quick_backup)
        btns_layout.addWidget(btn_backup_quick)

        btn_restore = QPushButton("Restaurar Cópia de Segurança...")
        btn_restore.setIcon(get_icon("refresh-cw", size=ICON_SIZES.SM))
        btn_restore.setIconSize(QSize(ICON_SIZES.SM, ICON_SIZES.SM))
        btn_restore.clicked.connect(lambda: self.do_restore_backup())
        btns_layout.addWidget(btn_restore)

        btn_folder = QPushButton("Abrir Pasta de Backups")
        btn_folder.setIcon(get_icon("database", size=ICON_SIZES.SM))
        btn_folder.setIconSize(QSize(ICON_SIZES.SM, ICON_SIZES.SM))
        btn_folder.clicked.connect(self.open_backup_folder)
        btns_layout.addWidget(btn_folder)

        btns_layout.addStretch()
        action_layout.addLayout(btns_layout)

        # Checkbox Auto-backup
        self.chk_auto_backup = QCheckBox("Criar cópia de segurança automática (.zip) na pasta padrão sempre que o sistema for fechado")
        auto_enabled = self.repository.database.get_setting("auto_backup_on_exit", "true").lower() == "true"
        self.chk_auto_backup.setChecked(auto_enabled)
        self.chk_auto_backup.stateChanged.connect(self.on_auto_backup_toggled)
        action_layout.addWidget(self.chk_auto_backup)

        layout.addWidget(action_card)

        # 3. Tabela de Backups
        table_card = ContentCard()
        table_layout = QVBoxLayout(table_card)
        table_layout.setContentsMargins(SPACING.XL, SPACING.LG, SPACING.XL, SPACING.LG)
        table_layout.setSpacing(SPACING.MD)

        th_box = QHBoxLayout()
        t_title = QLabel("Cópias de Segurança Disponíveis na Pasta Padrão")
        t_title.setObjectName("SectionSubtitle")
        th_box.addWidget(t_title)
        th_box.addStretch()
        btn_refresh_bck = QPushButton("Atualizar Lista")
        btn_refresh_bck.setIcon(get_icon("refresh-cw", size=ICON_SIZES.SM))
        btn_refresh_bck.setIconSize(QSize(ICON_SIZES.SM, ICON_SIZES.SM))
        btn_refresh_bck.clicked.connect(self.refresh_settings_backup)
        th_box.addWidget(btn_refresh_bck)
        table_layout.addLayout(th_box)

        self.backup_table = ModernTableWidget(0, 5)
        self.backup_table.setHorizontalHeaderLabels(["Arquivo de Backup", "Data / Hora", "Tamanho", "Formato", "Ação"])
        self.backup_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.backup_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.backup_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.backup_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.backup_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        table_layout.addWidget(self.backup_table)

        layout.addWidget(table_card, 1)
        return page

    def _make_settings_users_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(SPACING.MD)

        # 1. Controles e Ações de Usuários
        u_card = ContentCard()
        u_layout = QVBoxLayout(u_card)
        u_layout.setContentsMargins(SPACING.XL, SPACING.LG, SPACING.XL, SPACING.LG)
        u_layout.setSpacing(SPACING.MD)

        top_row = QHBoxLayout()
        u_title_box = QVBoxLayout()
        u_title_box.setSpacing(SPACING.XXS)
        u_title = QLabel("Gestão de Colaboradores e Controle de Acesso (RBAC)")
        u_title.setObjectName("SectionSubtitle")
        u_sub = QLabel("Segurança com derivação de chave scrypt e salt criptográfico individual de 128 bits")
        u_sub.setObjectName("SummaryLabel")
        u_title_box.addWidget(u_title)
        u_title_box.addWidget(u_sub)
        top_row.addLayout(u_title_box)
        top_row.addStretch()
        u_layout.addLayout(top_row)

        # Botões de Ação
        btn_row = QHBoxLayout()
        btn_row.setSpacing(SPACING.SM)

        btn_new_user = QPushButton("Novo Colaborador")
        btn_new_user.setObjectName("PrimaryButton")
        btn_new_user.setIcon(get_icon("plus", color="#ffffff", size=ICON_SIZES.SM))
        btn_new_user.setIconSize(QSize(ICON_SIZES.SM, ICON_SIZES.SM))
        btn_new_user.clicked.connect(self.open_new_user_dialog)
        btn_row.addWidget(btn_new_user)

        btn_edit_user = QPushButton("Editar Dados")
        btn_edit_user.setIcon(get_icon("pencil", size=ICON_SIZES.SM))
        btn_edit_user.setIconSize(QSize(ICON_SIZES.SM, ICON_SIZES.SM))
        btn_edit_user.clicked.connect(self.open_edit_user_dialog)
        btn_row.addWidget(btn_edit_user)

        btn_change_pwd = QPushButton("Alterar Senha")
        btn_change_pwd.setIcon(get_icon("lock", size=ICON_SIZES.SM))
        btn_change_pwd.setIconSize(QSize(ICON_SIZES.SM, ICON_SIZES.SM))
        btn_change_pwd.clicked.connect(self.open_change_password_dialog)
        btn_row.addWidget(btn_change_pwd)

        btn_toggle_status = QPushButton("Desativar / Reativar")
        btn_toggle_status.setIcon(get_icon("shield", size=ICON_SIZES.SM))
        btn_toggle_status.setIconSize(QSize(ICON_SIZES.SM, ICON_SIZES.SM))
        btn_toggle_status.clicked.connect(self.toggle_user_status_action)
        btn_row.addWidget(btn_toggle_status)

        btn_refresh_u = QPushButton("Atualizar Lista")
        btn_refresh_u.setIcon(get_icon("refresh-cw", size=ICON_SIZES.SM))
        btn_refresh_u.setIconSize(QSize(ICON_SIZES.SM, ICON_SIZES.SM))
        btn_refresh_u.clicked.connect(self.refresh_users)
        btn_row.addWidget(btn_refresh_u)

        btn_row.addStretch()
        u_layout.addLayout(btn_row)

        # Modo Produção
        self.chk_modo_producao = QCheckBox(
            "Modo Produção Comercial (ocultar botões de atalho rápido na tela de login)"
        )
        prod_active = self.repository.database.get_setting("modo_producao", "false").lower() == "true"
        self.chk_modo_producao.setChecked(prod_active)
        self.chk_modo_producao.stateChanged.connect(self.on_modo_producao_toggled)
        u_layout.addWidget(self.chk_modo_producao)

        layout.addWidget(u_card)

        # 2. Tabela de Usuários
        tbl_card = ContentCard()
        tbl_layout = QVBoxLayout(tbl_card)
        tbl_layout.setContentsMargins(SPACING.XL, SPACING.LG, SPACING.XL, SPACING.LG)
        tbl_layout.setSpacing(SPACING.MD)

        tbl_title = QLabel("Colaboradores Cadastrados no Sistema")
        tbl_title.setObjectName("SectionSubtitle")
        tbl_layout.addWidget(tbl_title)

        self.users_table = ModernTableWidget(0, 6)
        self.users_table.setHorizontalHeaderLabels([
            "ID", "Nome Completo", "Login de Acesso", "Perfil de Acesso", "Status", "Cadastrado em"
        ])
        self.users_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.users_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.users_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.users_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.users_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.users_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.users_table.doubleClicked.connect(self.open_edit_user_dialog)
        tbl_layout.addWidget(self.users_table)

        layout.addWidget(tbl_card, 1)
        return page

    def _make_settings_company_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(SPACING.MD)

        card = ContentCard()
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(SPACING.XL, SPACING.LG, SPACING.XL, SPACING.LG)
        card_layout.setSpacing(SPACING.MD)

        c_title = QLabel("Dados Comerciais da Empresa / Assistência Técnica")
        c_title.setObjectName("SectionSubtitle")
        card_layout.addWidget(c_title)

        c_desc = QLabel(
            "Estes dados são preenchidos automaticamente no cabeçalho e rodapé dos Comprovantes de Entrada, "
            "Recibos/Laudos de Saída e Relatórios Financeiros emitidos em PDF."
        )
        c_desc.setObjectName("SummaryLabel")
        card_layout.addWidget(c_desc)

        form_layout = QGridLayout()
        form_layout.setSpacing(SPACING.MD)

        # Razão Social / Nome Fantasia
        lbl_nome = QLabel("Razão Social / Nome Fantasia *")
        lbl_nome.setStyleSheet(f"font-weight: {TYPOGRAPHY.WEIGHT_BOLD};")
        self.input_emp_nome = QLineEdit()
        self.input_emp_nome.setObjectName("PillSearch")
        self.input_emp_nome.setPlaceholderText("Ex: Orby Assistência Técnica e Serviços")
        form_layout.addWidget(lbl_nome, 0, 0)
        form_layout.addWidget(self.input_emp_nome, 1, 0)

        # CNPJ / CPF
        lbl_cnpj = QLabel("CNPJ ou CPF *")
        lbl_cnpj.setStyleSheet(f"font-weight: {TYPOGRAPHY.WEIGHT_BOLD};")
        self.input_emp_cnpj = QLineEdit()
        self.input_emp_cnpj.setObjectName("PillSearch")
        self.input_emp_cnpj.setPlaceholderText("Ex: 12.345.678/0001-90")
        form_layout.addWidget(lbl_cnpj, 0, 1)
        form_layout.addWidget(self.input_emp_cnpj, 1, 1)

        # Telefone / WhatsApp
        lbl_tel = QLabel("Telefone / WhatsApp de Contato *")
        lbl_tel.setStyleSheet(f"font-weight: {TYPOGRAPHY.WEIGHT_BOLD};")
        self.input_emp_tel = QLineEdit()
        self.input_emp_tel.setObjectName("PillSearch")
        self.input_emp_tel.setPlaceholderText("Ex: (11) 98765-4321")
        form_layout.addWidget(lbl_tel, 2, 0)
        form_layout.addWidget(self.input_emp_tel, 3, 0)

        # Endereço Completo
        lbl_end = QLabel("Endereço Completo da Oficina *")
        lbl_end.setStyleSheet(f"font-weight: {TYPOGRAPHY.WEIGHT_BOLD};")
        self.input_emp_end = QLineEdit()
        self.input_emp_end.setObjectName("PillSearch")
        self.input_emp_end.setPlaceholderText("Ex: Rua das Flores, 120, Sala 3 — Centro")
        form_layout.addWidget(lbl_end, 2, 1)
        form_layout.addWidget(self.input_emp_end, 3, 1)

        card_layout.addLayout(form_layout)

        # Termos de Garantia / Condições Padrão
        lbl_termos = QLabel("Termos de Garantia e Condições Gerais (Impressos nos Comprovantes)")
        lbl_termos.setStyleSheet(f"font-weight: {TYPOGRAPHY.WEIGHT_BOLD};")
        card_layout.addWidget(lbl_termos)

        self.input_emp_termos = QTextEdit()
        self.input_emp_termos.setPlaceholderText("Digite os termos de garantia, prazos e condições aplicáveis às ordens de serviço...")
        self.input_emp_termos.setMinimumHeight(100)
        card_layout.addWidget(self.input_emp_termos)

        btn_save_emp = QPushButton("Salvar Informações da Empresa")
        btn_save_emp.setObjectName("PrimaryButton")
        btn_save_emp.setIcon(get_icon("circle-check", color="#ffffff", size=ICON_SIZES.SM))
        btn_save_emp.setIconSize(QSize(ICON_SIZES.SM, ICON_SIZES.SM))
        btn_save_emp.clicked.connect(self.save_company_settings)
        card_layout.addWidget(btn_save_emp, 0, Qt.AlignLeft)

        layout.addWidget(card)
        layout.addStretch()
        return page

    def refresh_settings(self) -> None:
        if hasattr(self, "settings_stack"):
            current_idx = self.settings_stack.currentIndex()
            if current_idx == 0:
                self.refresh_settings_backup()
            elif current_idx == 1:
                self.refresh_users()
            elif current_idx == 2:
                self.load_company_settings()
        else:
            self.refresh_settings_backup()

    def refresh_settings_backup(self) -> None:
        manager = BackupManager(db_path=self.repository.database.path)
        info = manager.get_database_info()

        if hasattr(self, "lbl_db_path"):
            self.lbl_db_path.setText(f"Caminho do Arquivo: {info['path']}")
            self.lbl_db_stats.setText(f"Tamanho em Disco: {info['size_formatted']} • Última Modificação: {info['last_modified']}")
            counts = info.get("counts", {})
            self.lbl_db_counts.setText(
                f"Clientes: {counts.get('clientes', 0)} • "
                f"Equipamentos: {counts.get('equipamentos', 0)} • "
                f"Ordens de Serviço: {counts.get('ordens_servico', 0)} • "
                f"Usuários: {counts.get('usuarios', 0)}"
            )

        if hasattr(self, "backup_table"):
            backups = manager.list_backups()
            self.backup_table.setRowCount(0)
            for b in backups:
                row = self.backup_table.rowCount()
                self.backup_table.insertRow(row)
                self.backup_table.setItem(row, 0, QTableWidgetItem(b["filename"]))
                self.backup_table.setItem(row, 1, QTableWidgetItem(b["date_formatted"]))
                self.backup_table.setItem(row, 2, QTableWidgetItem(b["size_formatted"]))
                fmt = "Compactado (.zip)" if b["is_compressed"] else "Banco SQLite (.db)"
                self.backup_table.setItem(row, 3, QTableWidgetItem(fmt))

                btn_rst = QPushButton("Restaurar")
                btn_rst.setObjectName("SecondaryButton")
                btn_rst.clicked.connect(lambda checked=False, p=b["path"]: self.do_restore_backup(p))
                self.backup_table.setCellWidget(row, 4, btn_rst)

    def refresh_users(self) -> None:
        if not hasattr(self, "users_table"):
            return
        users = self.repository.users()
        self.users_table.setRowCount(0)
        for u in users:
            row = self.users_table.rowCount()
            self.users_table.insertRow(row)

            # ID
            item_id = QTableWidgetItem(str(u["id"]))
            item_id.setTextAlignment(Qt.AlignCenter)
            self.users_table.setItem(row, 0, item_id)

            # Nome
            item_nome = QTableWidgetItem(u["nome"])
            self.users_table.setItem(row, 1, item_nome)

            # Login
            item_login = QTableWidgetItem(u["login"])
            self.users_table.setItem(row, 2, item_login)

            # Perfil
            item_perfil = QTableWidgetItem(u["perfil"])
            item_perfil.setTextAlignment(Qt.AlignCenter)
            self.users_table.setItem(row, 3, item_perfil)

            # Status (Ativo / Inativo)
            is_active = bool(u.get("ativo", 1))
            status_text = "Ativo" if is_active else "Desativado"
            item_status = QTableWidgetItem(status_text)
            item_status.setTextAlignment(Qt.AlignCenter)
            self.users_table.setItem(row, 4, item_status)

            # Cadastrado em
            dt_criado = u.get("criado_em", "—")
            item_dt = QTableWidgetItem(str(dt_criado)[:19])
            item_dt.setTextAlignment(Qt.AlignCenter)
            self.users_table.setItem(row, 5, item_dt)

    def _get_selected_user(self) -> dict | None:
        if not hasattr(self, "users_table"):
            return None
        selected = self.users_table.selectedItems()
        if not selected:
            return None
        row = selected[0].row()
        user_id = int(self.users_table.item(row, 0).text())
        users = self.repository.users()
        for u in users:
            if u["id"] == user_id:
                return u
        return None

    def open_new_user_dialog(self) -> None:
        dialog = UserDialog(self)
        if dialog.exec():
            data = dialog.get_data()
            try:
                self.repository.add_user(
                    nome=data["nome"],
                    login=data["login"],
                    password=data["password"],
                    perfil=data["perfil"],
                )
                QMessageBox.information(
                    self,
                    "Colaborador Cadastrado",
                    f"O colaborador '{data['nome']}' foi cadastrado com sucesso!",
                )
                self.refresh_users()
            except Exception as e:
                QMessageBox.critical(self, "Erro ao Cadastrar", str(e))

    def open_edit_user_dialog(self) -> None:
        user = self._get_selected_user()
        if not user:
            QMessageBox.warning(self, "Atenção", "Selecione um colaborador na tabela para editar.")
            return

        dialog = UserDialog(self, user_data=user)
        if dialog.exec():
            data = dialog.get_data()
            try:
                self.repository.update_user(
                    user_id=user["id"],
                    nome=data["nome"],
                    perfil=data["perfil"],
                    login=data["login"],
                )
                QMessageBox.information(
                    self,
                    "Dados Atualizados",
                    f"Os dados de '{data['nome']}' foram atualizados com sucesso!",
                )
                self.refresh_users()
            except Exception as e:
                QMessageBox.critical(self, "Erro ao Atualizar", str(e))

    def open_change_password_dialog(self) -> None:
        user = self._get_selected_user()
        if not user:
            QMessageBox.warning(self, "Atenção", "Selecione um colaborador na tabela para alterar a senha.")
            return

        dialog = PasswordDialog(user_name=user["nome"], parent=self)
        if dialog.exec():
            new_pwd = dialog.get_password()
            try:
                self.repository.change_password(user["id"], new_pwd)
                QMessageBox.information(
                    self,
                    "Senha Atualizada",
                    f"A senha de acesso de '{user['nome']}' foi redefinida com sucesso!",
                )
            except Exception as e:
                QMessageBox.critical(self, "Erro ao Alterar Senha", str(e))

    def toggle_user_status_action(self) -> None:
        user = self._get_selected_user()
        if not user:
            QMessageBox.warning(self, "Atenção", "Selecione um colaborador na tabela para alterar o status.")
            return

        is_active = bool(user.get("ativo", 1))
        novo_status = not is_active
        acao = "reativar" if novo_status else "desativar"

        reply = QMessageBox.question(
            self,
            "Confirmar Alteração de Acesso",
            f"Deseja realmente {acao} o acesso de '{user['nome']}' ({user['login']}) ao sistema?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return

        try:
            self.repository.toggle_user_status(user["id"], novo_status)
            QMessageBox.information(
                self,
                "Status Alterado",
                f"O colaborador '{user['nome']}' foi {acao}do com sucesso!",
            )
            self.refresh_users()
        except Exception as e:
            QMessageBox.critical(self, "Ação Não Permitida", str(e))

    def do_manual_backup(self) -> None:
        manager = BackupManager(db_path=self.repository.database.path)
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        default_name = f"orby_backup_{timestamp}.zip"
        default_target = os.path.join(str(manager.get_backup_dir()), default_name)

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Salvar Cópia de Segurança do Orby",
            default_target,
            "Arquivo Compactado (*.zip);;Banco de Dados SQLite (*.db)",
        )
        if not path:
            return

        try:
            compress = path.lower().endswith(".zip")
            saved_path = manager.create_backup(destination_path=path, compress=compress)
            QMessageBox.information(
                self,
                "Backup Realizado com Sucesso",
                f"A cópia de segurança foi gerada com sucesso!\n\nArquivo: {os.path.basename(saved_path)}\nLocal: {saved_path}",
            )
            self.refresh_settings_backup()
        except Exception as e:
            QMessageBox.critical(self, "Erro no Backup", f"Não foi possível gerar a cópia de segurança:\n{e}")

    def do_quick_backup(self) -> None:
        try:
            manager = BackupManager(db_path=self.repository.database.path)
            saved_path = manager.create_backup(compress=True)
            QMessageBox.information(
                self,
                "Backup Rápido Concluído",
                f"Cópia de segurança compactada criada com sucesso na pasta padrão!\n\nArquivo: {os.path.basename(saved_path)}",
            )
            self.refresh_settings_backup()
        except Exception as e:
            QMessageBox.critical(self, "Erro no Backup", f"Falha no backup rápido:\n{e}")

    def do_restore_backup(self, file_path: str | None = None) -> None:
        manager = BackupManager(db_path=self.repository.database.path)
        if not file_path:
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Selecionar Arquivo de Backup para Restauração",
                str(manager.get_backup_dir()),
                "Backups do Orby (*.zip *.db);;Todos os Arquivos (*.*)",
            )
        if not file_path:
            return

        try:
            val = manager.validate_backup(file_path)
            counts = val.get("counts", {})
            msg = (
                f"Tem certeza que deseja restaurar este backup?\n\n"
                f"Arquivo: {os.path.basename(file_path)}\n"
                f"Tamanho: {val['size_formatted']}\n"
                f"Registros encontrados:\n"
                f"  • Clientes: {counts.get('clientes', 0)}\n"
                f"  • Equipamentos: {counts.get('equipamentos', 0)}\n"
                f"  • Ordens de Serviço: {counts.get('ordens_servico', 0)}\n\n"
                f"⚠️ ATENÇÃO: Os dados atuais serão substituídos pelos do backup. "
                f"Um snapshot de emergência do banco atual será gerado automaticamente antes de prosseguir."
            )
            reply = QMessageBox.warning(
                self,
                "Confirmar Restauração de Dados",
                msg,
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if reply != QMessageBox.Yes:
                return

            manager.restore_backup(file_path)
            QMessageBox.information(
                self,
                "Restauração Concluída",
                "O sistema foi restaurado com sucesso! Todos os dados e migrações foram atualizados.",
            )
            self.refresh_all()
        except InvalidBackupFileError as e:
            QMessageBox.critical(self, "Backup Inválido", f"O arquivo selecionado não é um backup válido:\n{e}")
        except Exception as e:
            QMessageBox.critical(self, "Erro na Restauração", f"Falha ao restaurar backup:\n{e}")

    def open_backup_folder(self) -> None:
        manager = BackupManager(db_path=self.repository.database.path)
        folder = manager.get_backup_dir()
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(folder)))

    def on_auto_backup_toggled(self, state: int) -> None:
        enabled = (state == Qt.CheckState.Checked.value or state == 2)
        self.repository.database.set_setting("auto_backup_on_exit", "true" if enabled else "false")

    def on_modo_producao_toggled(self, state: int) -> None:
        enabled = (state == Qt.CheckState.Checked.value or state == 2)
        self.repository.database.set_setting("modo_producao", "true" if enabled else "false")

    def save_company_settings(self) -> None:
        db = self.repository.database
        db.set_setting("empresa_nome", self.input_emp_nome.text().strip())
        db.set_setting("empresa_cnpj", self.input_emp_cnpj.text().strip())
        db.set_setting("empresa_telefone", self.input_emp_tel.text().strip())
        db.set_setting("empresa_endereco", self.input_emp_end.text().strip())
        db.set_setting("empresa_termos", self.input_emp_termos.toPlainText().strip())
        QMessageBox.information(
            self,
            "Dados da Empresa Salvos",
            "As informações cadastrais foram salvas com sucesso!\nElas já serão utilizadas nos próximos comprovantes e relatórios em PDF.",
        )

    def load_company_settings(self) -> None:
        db = self.repository.database
        if hasattr(self, "input_emp_nome"):
            self.input_emp_nome.setText(db.get_setting("empresa_nome", "Orby Assistência Técnica & Gestão"))
            self.input_emp_cnpj.setText(db.get_setting("empresa_cnpj", "00.000.000/0001-00"))
            self.input_emp_tel.setText(db.get_setting("empresa_telefone", "(11) 98765-4321"))
            self.input_emp_end.setText(db.get_setting("empresa_endereco", "Av. Principal, 100 — Centro"))
            default_termos = (
                "1. Garantia legal de 90 dias referente aos serviços e peças aplicadas, conforme art. 26 do CDC.\n"
                "2. A garantia não cobre danos por mau uso, umidade, quedas ou intervenção de terceiros.\n"
                "3. Equipamentos não retirados em até 90 dias após aviso de conclusão poderão sofrer taxa de guarda."
            )
            self.input_emp_termos.setPlainText(db.get_setting("empresa_termos", default_termos))

    def get_company_info(self) -> dict:
        db = self.repository.database
        return {
            "empresa_nome": db.get_setting("empresa_nome", "Orby Assistência Técnica & Gestão"),
            "empresa_cnpj": db.get_setting("empresa_cnpj", "00.000.000/0001-00"),
            "empresa_telefone": db.get_setting("empresa_telefone", "(11) 98765-4321"),
            "empresa_endereco": db.get_setting("empresa_endereco", "Av. Principal, 100 — Centro"),
            "empresa_termos": db.get_setting("empresa_termos", ""),
        }

    def print_entry_receipt_by_id(self, item_id: int) -> None:
        order = self.repository.order(item_id)
        if not order:
            return

        customer = self.repository.customer(order["cliente_id"]) or {"nome": order.get("cliente_nome", "Cliente")}
        equipment = self.repository.single_equipment(order["equipamento_id"]) if order.get("equipamento_id") else None
        company = self.get_company_info()

        from .core.pdf_generator import generate_entry_receipt, get_default_docs_dir

        default_name = f"Comprovante_Entrada_OS_{item_id:04d}.pdf"
        default_path = os.path.join(str(get_default_docs_dir("comprovantes")), default_name)

        path, _ = QFileDialog.getSaveFileName(
            self,
            f"Salvar Comprovante de Entrada — OS-{item_id:04d}",
            default_path,
            "Documento PDF (*.pdf)",
        )
        if not path:
            return

        try:
            saved_path = generate_entry_receipt(order, customer, equipment, company, output_path=path)
            reply = QMessageBox.information(
                self,
                "Comprovante Gerado",
                f"Comprovante de Entrada da OS-{item_id:04d} gerado com sucesso!\n\nArquivo: {os.path.basename(saved_path)}\n\nDeseja abrir o documento agora?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes,
            )
            if reply == QMessageBox.Yes:
                QDesktopServices.openUrl(QUrl.fromLocalFile(str(saved_path)))
        except Exception as e:
            QMessageBox.critical(self, "Erro na Emissão", f"Falha ao gerar comprovante em PDF:\n{e}")

    def print_entry_receipt(self) -> None:
        item_id = self.selected_id(self.order_table)
        if item_id is None:
            return
        self.print_entry_receipt_by_id(item_id)

    def print_exit_receipt_by_id(self, item_id: int) -> None:
        order = self.repository.order(item_id)
        if not order:
            return

        customer = self.repository.customer(order["cliente_id"]) or {"nome": order.get("cliente_nome", "Cliente")}
        equipment = self.repository.single_equipment(order["equipamento_id"]) if order.get("equipamento_id") else None
        company = self.get_company_info()

        from .core.pdf_generator import generate_exit_receipt, get_default_docs_dir

        default_name = f"Recibo_Saida_Laudo_OS_{item_id:04d}.pdf"
        default_path = os.path.join(str(get_default_docs_dir("comprovantes")), default_name)

        path, _ = QFileDialog.getSaveFileName(
            self,
            f"Salvar Recibo de Saída e Laudo — OS-{item_id:04d}",
            default_path,
            "Documento PDF (*.pdf)",
        )
        if not path:
            return

        try:
            saved_path = generate_exit_receipt(order, customer, equipment, company, output_path=path)
            reply = QMessageBox.information(
                self,
                "Recibo e Laudo Gerado",
                f"Recibo de Saída da OS-{item_id:04d} gerado com sucesso!\n\nArquivo: {os.path.basename(saved_path)}\n\nDeseja abrir o documento agora?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes,
            )
            if reply == QMessageBox.Yes:
                QDesktopServices.openUrl(QUrl.fromLocalFile(str(saved_path)))
        except Exception as e:
            QMessageBox.critical(self, "Erro na Emissão", f"Falha ao gerar recibo de saída em PDF:\n{e}")

    def print_exit_receipt(self) -> None:
        item_id = self.selected_id(self.order_table)
        if item_id is None:
            return
        self.print_exit_receipt_by_id(item_id)

    def export_finance_pdf(self) -> None:
        period = self.finance_period.currentData() or "all"
        period_text = self.finance_period.currentText()
        data = self.repository.finance(period)
        company = self.get_company_info()

        from .core.pdf_generator import generate_financial_report, get_default_docs_dir
        from datetime import datetime

        ts = datetime.now().strftime("%Y-%m-%d")
        default_name = f"Relatorio_Financeiro_{period}_{ts}.pdf"
        default_path = os.path.join(str(get_default_docs_dir("relatorios")), default_name)

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Exportar Relatório Financeiro (PDF)",
            default_path,
            "Documento PDF (*.pdf)",
        )
        if not path:
            return

        try:
            saved = generate_financial_report(data, period_label=period_text, company=company, output_path=path)
            reply = QMessageBox.information(
                self,
                "Relatório Financeiro Exportado",
                f"Relatório financeiro ({period_text}) exportado com sucesso!\n\nArquivo: {os.path.basename(saved)}\n\nDeseja visualizar agora?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes,
            )
            if reply == QMessageBox.Yes:
                QDesktopServices.openUrl(QUrl.fromLocalFile(str(saved)))
        except Exception as e:
            QMessageBox.critical(self, "Erro na Exportação", f"Falha ao gerar relatório financeiro:\n{e}")

    def export_finance_csv(self) -> None:
        period = self.finance_period.currentData() or "all"
        period_text = self.finance_period.currentText()
        data = self.repository.finance(period)
        extrato = data.get("extrato", [])

        if not extrato:
            QMessageBox.information(self, "Extrato Vazio", f"Não há lançamentos de ordens finalizadas para o período '{period_text}'.")
            return

        from .core.pdf_generator import export_financial_csv, get_default_docs_dir
        from datetime import datetime

        ts = datetime.now().strftime("%Y-%m-%d")
        default_name = f"Extrato_Financeiro_{period}_{ts}.csv"
        default_path = os.path.join(str(get_default_docs_dir("relatorios")), default_name)

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Exportar Extrato Analítico (Excel / CSV)",
            default_path,
            "Planilha CSV (*.csv)",
        )
        if not path:
            return

        try:
            saved = export_financial_csv(extrato, output_path=path)
            reply = QMessageBox.information(
                self,
                "Extrato Exportado com Sucesso",
                f"Extrato financeiro com {len(extrato)} registros exportado com sucesso!\n\nArquivo compatível com Microsoft Excel: {os.path.basename(saved)}\n\nDeseja abrir a pasta agora?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes,
            )
            if reply == QMessageBox.Yes:
                QDesktopServices.openUrl(QUrl.fromLocalFile(str(os.path.dirname(saved))))
        except Exception as e:
            QMessageBox.critical(self, "Erro na Exportação", f"Falha ao exportar CSV:\n{e}")

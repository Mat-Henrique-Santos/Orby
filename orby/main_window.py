from __future__ import annotations

from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from .core.models import FORMA_PAGAMENTO_OPCOES, StatusOS
from .importer import read_table, validate_customers
from .repository import Repository
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
        if not self.name.text().strip() or not self.phone.text().strip():
            QMessageBox.warning(self, "Campos Obrigatórios", "Informe ao menos o nome e o telefone do cliente.")
            return
        super().accept()


class OrderDialog(QDialog):
    def __init__(self, parent, customers: list[dict], order: dict | None = None):
        super().__init__(parent)
        self.parent_window = parent
        self.setWindowTitle(f"Editar OS #{order['id']:04d}" if order else "Nova Ordem de Serviço")
        self.resize(640, 600)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING.XXL, SPACING.XXL, SPACING.XXL, SPACING.XXL)
        layout.setSpacing(SPACING.MD)

        form = QFormLayout()
        form.setSpacing(SPACING.SM + 2)

        self.customer = QComboBox()
        self.equipment = QComboBox()
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

        # Discriminação de Valores Financeiros
        self.valor_servico = QDoubleSpinBox()
        self.valor_servico.setMaximum(9_999_999.99)
        self.valor_servico.setPrefix("R$ ")
        self.valor_servico.setDecimals(2)
        self.valor_servico.setValue(float(order.get("valor_servico") or 0.0) if order else 0.0)
        self.valor_servico.valueChanged.connect(self.recalc_total)

        self.valor_pecas = QDoubleSpinBox()
        self.valor_pecas.setMaximum(9_999_999.99)
        self.valor_pecas.setPrefix("R$ ")
        self.valor_pecas.setDecimals(2)
        self.valor_pecas.setValue(float(order.get("valor_pecas") or 0.0) if order else 0.0)
        self.valor_pecas.valueChanged.connect(self.recalc_total)

        self.value = QDoubleSpinBox()
        self.value.setMaximum(9_999_999.99)
        self.value.setPrefix("R$ ")
        self.value.setDecimals(2)
        self.value.setValue(float(order["valor"]) if order else 0.0)

        self.forma_pagamento = QComboBox()
        self.forma_pagamento.addItems(FORMA_PAGAMENTO_OPCOES)
        if order and order.get("forma_pagamento"):
            self.forma_pagamento.setCurrentText(order["forma_pagamento"])

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
        self.equipment.clear()
        cust_id = self.customer.currentData()
        if cust_id:
            items = self.parent_window.repository.equipment(cust_id)
            for item in items:
                label = " ".join(part for part in [item["tipo"], item.get("marca"), item.get("modelo")] if part)
                if item.get("numero_serie"):
                    label += f" (S/N: {item['numero_serie']})"
                self.equipment.addItem(label, item["id"])

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
    def __init__(self, parent, customers: list[dict]):
        super().__init__(parent)
        self.setWindowTitle("Novo Equipamento")
        self.resize(520, 440)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING.XXL, SPACING.XXL, SPACING.XXL, SPACING.XXL)
        layout.setSpacing(SPACING.MD)

        form = QFormLayout()
        form.setSpacing(SPACING.SM + 2)

        self.customer = QComboBox()
        for item in customers:
            self.customer.addItem(item["nome"], item["id"])

        self.type = QLineEdit()
        self.type.setPlaceholderText("Ex: Notebook, Máquina de Solda, Ar-Condicionado, Motor, Celular")
        self.brand = QLineEdit()
        self.brand.setPlaceholderText("Ex: Dell, Makita, Consul, WEG, Samsung")
        self.model = QLineEdit()
        self.model.setPlaceholderText("Ex: Inspiron 15, Inverter 12k, Trifásico, LaserJet")
        self.serial = QLineEdit()
        self.serial.setPlaceholderText("Número de Série ou IMEI")
        self.accessories = QLineEdit()
        self.accessories.setPlaceholderText("Ex: Carregador, Cabo, Capa")
        self.condition = QLineEdit()
        self.condition.setPlaceholderText("Ex: Riscos na tampa, tela trincada")
        self.notes = QTextEdit()
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
        save_btn.setText("Cadastrar Equipamento")
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
        self.resize(820, 580)

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
        layout.addWidget(self.table)

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
        self.repository = Repository(database)
        self.current_user = current_user or {"id": 1, "nome": "Administrador", "perfil": "Gestor"}
        self.perfil = self.current_user.get("perfil", "Gestor")
        self.requested_logout = False

        self.setWindowTitle("Orby — Gestão Operacional para Pequenas Empresas e Serviços")
        self.resize(1300, 840)

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
        user_lbl.setStyleSheet(f"font-size: {TYPOGRAPHY.SIZE_CAPTION + 1}px; color: {get_current_palette().TEXT_PRIMARY};")
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

        # Barra lateral Frutiger Aero (Estilo Dock)
        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(DIMENSIONS.SIDEBAR_WIDTH)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(SPACING.LG + 2, SPACING.XL, SPACING.LG + 2, SPACING.LG + 2)
        sidebar_layout.setSpacing(SPACING.SM + 2)

        # Topo da Sidebar com Ícone Esférico 3D
        logo_box = QHBoxLayout()
        logo_box.setSpacing(SPACING.SM + 2)
        self.orb_logo = OrbLogoWidget()
        logo_text_box = QVBoxLayout()
        logo_text_box.setSpacing(SPACING.XXS)
        logo_title = QLabel("ORBY")
        logo_title.setObjectName("LogoTitle")
        logo_sub = QLabel("Serviços & Manutenção")
        logo_sub.setObjectName("LogoSubtitle")
        logo_text_box.addWidget(logo_title)
        logo_text_box.addWidget(logo_sub)
        logo_box.addWidget(self.orb_logo)
        logo_box.addLayout(logo_text_box)
        logo_box.addStretch()

        sidebar_layout.addLayout(logo_box)
        sidebar_layout.addSpacing(SPACING.MD)

        # Botões de Navegação em Pílula com Ícones Lucide SVG
        self.nav_buttons: list[QPushButton] = []
        nav_items = [
            ("Dashboard", "layout-dashboard", 0),
            ("Financeiro", "chart", 1),
            ("Clientes", "users", 2),
            ("Equipamentos", "laptop", 3),
            ("Ordens de Serviço", "clipboard", 4),
        ]

        for text, icon_name, index in nav_items:
            btn = QPushButton(f"  {text}")
            btn.setObjectName("NavButton")
            btn.setIcon(get_icon(icon_name, size=ICON_SIZES.MD))
            btn.setIconSize(QSize(ICON_SIZES.MD, ICON_SIZES.MD))
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked=False, i=index: self.open_page(i))
            sidebar_layout.addWidget(btn)
            self.nav_buttons.append(btn)

        sidebar_layout.addStretch()

        # Grade Mini Dock de 4 Ícones SVG
        dock_label = QLabel("AÇÕES RÁPIDAS")
        dock_label.setObjectName("DockSectionLabel")
        sidebar_layout.addWidget(dock_label)

        dock_grid = QHBoxLayout()
        dock_grid.setSpacing(SPACING.SM)

        btn_refresh = QPushButton()
        btn_refresh.setObjectName("DockTile")
        btn_refresh.setIcon(get_icon("refresh-cw", size=ICON_SIZES.MD))
        btn_refresh.setIconSize(QSize(ICON_SIZES.MD, ICON_SIZES.MD))
        btn_refresh.setToolTip("Atualizar todos os dados")
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

        dock_grid.addWidget(btn_refresh)
        dock_grid.addWidget(self.btn_import)
        dock_grid.addWidget(self.btn_theme)
        dock_grid.addWidget(btn_about)
        dock_grid.addWidget(self.btn_logout)
        sidebar_layout.addLayout(dock_grid)

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
        self.pages.addWidget(self.make_dashboard())
        self.pages.addWidget(self.make_finance())
        self.pages.addWidget(self.make_customers())
        self.pages.addWidget(self.make_equipment())
        self.pages.addWidget(self.make_orders())

        content_layout.addWidget(self.pages)
        body_layout.addWidget(content_area, 1)

        root_layout.addLayout(body_layout, 1)

        self._apply_permissions()
        self.open_page(0)

    def update_theme_button_icon(self) -> None:
        icon_name = "sun" if is_dark_mode() else "moon"
        self.btn_theme.setIcon(get_icon(icon_name, size=ICON_SIZES.MD))
        self.btn_theme.setIconSize(QSize(ICON_SIZES.MD, ICON_SIZES.MD))

    def on_global_search(self, text: str) -> None:
        term = text.strip()
        idx = self.pages.currentIndex()
        if idx == 2:
            self.customer_search.setText(term)
        elif idx == 4:
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
            if hasattr(self, "delete_equipment_btn"):
                self.delete_equipment_btn.setVisible(False)
            if hasattr(self, "delete_order_btn"):
                self.delete_order_btn.setVisible(False)
        elif self.perfil == "Atendente":
            self.nav_buttons[1].setVisible(False)  # Financeiro
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
        self.card_finalizadas = MetricCard("Finalizadas", "0", "circle-check")
        self.card_faturamento = MetricCard("Faturamento (OS)", "R$ 0,00", "dollar-sign")

        cards_layout.addWidget(self.card_abertas)
        cards_layout.addWidget(self.card_reparo)
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
        pay_card.setFixedWidth(320)
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
        self.pay_table.setHorizontalHeaderLabels(["Forma", "Qtd", "Total (R$)"])
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

        self.equipment_table = ModernTableWidget(0, 5)
        self.equipment_table.setHorizontalHeaderLabels(["ID", "Cliente", "Tipo", "Marca / Modelo", "Nº de Série"])
        card_layout.addWidget(self.equipment_table)

        actions = QHBoxLayout()
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

        actions.addWidget(edit_btn)
        actions.addWidget(timeline_btn)
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
        if self.perfil != "Gestor":
            self.card_faturamento.set_value("Restrito")
        else:
            fat = data.get("faturamento") or 0.0
            self.card_faturamento.set_value(f"R$ {fat:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

        orders = self.repository.orders()[:10]
        self.dash_table.setRowCount(0)
        for item in orders:
            row = self.dash_table.rowCount()
            self.dash_table.insertRow(row)
            self.dash_table.setItem(row, 0, QTableWidgetItem(f"OS-{item['id']:04d}"))
            self.dash_table.setItem(row, 1, QTableWidgetItem(item["cliente_nome"]))
            self.dash_table.setItem(row, 2, QTableWidgetItem(item["equipamento_nome"]))
            badge = StatusBadge(item["status"])
            self.dash_table.setCellWidget(row, 3, badge)
            self.dash_table.setItem(row, 4, QTableWidgetItem(f"R$ {item['valor']:.2f}"))
            self.dash_table.setItem(row, 5, QTableWidgetItem(item["data_abertura"][:10]))

    def refresh_finance(self) -> None:
        period = self.finance_period.currentData() if hasattr(self, "finance_period") else "all"
        fin = self.repository.financial_dashboard(period)

        def fmt(v: float) -> str:
            return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

        self.card_fat_realizado.set_value(fmt(fin["faturamento_realizado"]))
        self.card_rec_prevista.set_value(fmt(fin["receita_prevista"]))
        self.card_ticket_medio.set_value(fmt(fin["ticket_medio"]))
        self.card_lucro_servicos.set_value(fmt(fin["total_servicos"]))

        # Formas de pagamento
        self.pay_table.setRowCount(0)
        for item in fin["formas_pagamento"]:
            row = self.pay_table.rowCount()
            self.pay_table.insertRow(row)
            self.pay_table.setItem(row, 0, QTableWidgetItem(item["forma"]))
            self.pay_table.setItem(row, 1, QTableWidgetItem(str(item["qtd"])))
            self.pay_table.setItem(row, 2, QTableWidgetItem(fmt(item["total"])))

        # Extrato
        self.extrato_table.setRowCount(0)
        for item in fin["extrato"]:
            row = self.extrato_table.rowCount()
            self.extrato_table.insertRow(row)
            self.extrato_table.setItem(row, 0, QTableWidgetItem(f"OS-{item['id']:04d}"))
            self.extrato_table.setItem(row, 1, QTableWidgetItem(item["cliente_nome"]))
            self.extrato_table.setItem(row, 2, QTableWidgetItem(item["equipamento_nome"]))
            self.extrato_table.setItem(row, 3, QTableWidgetItem(fmt(item.get("valor_servico") or 0.0)))
            self.extrato_table.setItem(row, 4, QTableWidgetItem(fmt(item.get("valor_pecas") or 0.0)))
            self.extrato_table.setItem(row, 5, QTableWidgetItem(fmt(item["valor"])))
            self.extrato_table.setItem(row, 6, QTableWidgetItem(item.get("forma_pagamento") or "—"))

    def refresh_customers(self) -> None:
        term = self.customer_search.text() if hasattr(self, "customer_search") else ""
        rows = self.repository.customers(term)
        self.customer_table.setRowCount(0)
        for item in rows:
            row = self.customer_table.rowCount()
            self.customer_table.insertRow(row)
            self.customer_table.setItem(row, 0, QTableWidgetItem(str(item["id"])))
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
            self.order_table.setItem(row, 0, QTableWidgetItem(f"OS-{item['id']:04d}"))
            self.order_table.setItem(row, 1, QTableWidgetItem(item["cliente_nome"]))
            self.order_table.setItem(row, 2, QTableWidgetItem(item["equipamento_nome"]))
            self.order_table.setItem(row, 3, QTableWidgetItem(item["descricao"]))
            badge = StatusBadge(item["status"])
            self.order_table.setCellWidget(row, 4, badge)
            self.order_table.setItem(row, 5, QTableWidgetItem(f"R$ {item.get('valor_servico') or 0.0:.2f}"))
            self.order_table.setItem(row, 6, QTableWidgetItem(f"R$ {item.get('valor_pecas') or 0.0:.2f}"))
            self.order_table.setItem(row, 7, QTableWidgetItem(f"R$ {item['valor']:.2f}"))

    def refresh_equipment(self) -> None:
        rows = self.repository.equipment()
        self.equipment_table.setRowCount(0)
        for item in rows:
            row = self.equipment_table.rowCount()
            self.equipment_table.insertRow(row)
            marca_modelo = " ".join(p for p in [item.get("marca"), item.get("modelo")] if p)
            self.equipment_table.setItem(row, 0, QTableWidgetItem(str(item["id"])))
            self.equipment_table.setItem(row, 1, QTableWidgetItem(item["cliente_nome"]))
            self.equipment_table.setItem(row, 2, QTableWidgetItem(item["tipo"]))
            self.equipment_table.setItem(row, 3, QTableWidgetItem(marca_modelo or "—"))
            self.equipment_table.setItem(row, 4, QTableWidgetItem(item.get("numero_serie") or "—"))

    def selected_id(self, table: QTableWidget) -> int | None:
        row = table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Seleção necessária", "Por favor, selecione um registro na tabela.")
            return None
        text = table.item(row, 0).text().replace("OS-", "")
        return int(text)

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
        ok, message = self.repository.delete_customer(item_id)
        (QMessageBox.information if ok else QMessageBox.warning)(self, "Clientes", message)
        self.refresh_all()

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
        ok, message = self.repository.delete_equipment(item_id)
        (QMessageBox.information if ok else QMessageBox.warning)(self, "Equipamentos", message)
        self.refresh_all()

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
        self.repository.delete_order(item_id)
        self.refresh_all()

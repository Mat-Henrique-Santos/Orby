from __future__ import annotations

from PySide6.QtCore import Qt, QSize
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .icons import get_icon
from .theme import get_current_palette
from .tokens import DIMENSIONS, ICON_SIZES, SPACING, TYPOGRAPHY


class UserDialog(QDialog):
    """Diálogo Frutiger Aero para cadastro e edição de colaboradores/usuários."""

    def __init__(
        self,
        parent: QWidget | None = None,
        user_data: dict | None = None,
    ) -> None:
        super().__init__(parent)
        self.user_data = user_data
        self.is_editing = user_data is not None

        title_text = "Editar Colaborador" if self.is_editing else "Novo Colaborador / Usuário"
        self.setWindowTitle(f"Orby — {title_text}")
        self.setFixedSize(460, 480 if not self.is_editing else 360)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        pal = get_current_palette()

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(SPACING.XL, SPACING.XL, SPACING.XL, SPACING.XL)
        main_layout.setSpacing(SPACING.MD)

        card = QFrame()
        card.setObjectName("ContentCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(SPACING.LG, SPACING.LG, SPACING.LG, SPACING.LG)
        card_layout.setSpacing(SPACING.SM + 2)

        header_lbl = QLabel(title_text)
        header_lbl.setStyleSheet(f"font-size: 16px; font-weight: {TYPOGRAPHY.WEIGHT_BOLD}; color: {pal.TEXT_PRIMARY};")
        card_layout.addWidget(header_lbl)

        # 1. Nome Completo
        lbl_nome = QLabel("Nome Completo *")
        lbl_nome.setStyleSheet(f"font-size: {TYPOGRAPHY.SIZE_CAPTION}px; font-weight: {TYPOGRAPHY.WEIGHT_BOLD}; color: {pal.TEXT_SECONDARY};")
        self.input_nome = QLineEdit()
        self.input_nome.setObjectName("PillSearch")
        self.input_nome.setPlaceholderText("Ex: João da Silva")
        if self.is_editing:
            self.input_nome.setText(self.user_data.get("nome", ""))
        card_layout.addWidget(lbl_nome)
        card_layout.addWidget(self.input_nome)

        # 2. Login de Acesso
        lbl_login = QLabel("Login de Acesso * (Único)")
        lbl_login.setStyleSheet(f"font-size: {TYPOGRAPHY.SIZE_CAPTION}px; font-weight: {TYPOGRAPHY.WEIGHT_BOLD}; color: {pal.TEXT_SECONDARY};")
        self.input_login = QLineEdit()
        self.input_login.setObjectName("PillSearch")
        self.input_login.setPlaceholderText("Ex: joao.silva")
        if self.is_editing:
            self.input_login.setText(self.user_data.get("login", ""))
        card_layout.addWidget(lbl_login)
        card_layout.addWidget(self.input_login)

        # 3. Perfil de Acesso
        lbl_perfil = QLabel("Perfil de Permissão (RBAC) *")
        lbl_perfil.setStyleSheet(f"font-size: {TYPOGRAPHY.SIZE_CAPTION}px; font-weight: {TYPOGRAPHY.WEIGHT_BOLD}; color: {pal.TEXT_SECONDARY};")
        self.combo_perfil = QComboBox()
        self.combo_perfil.addItem("Gestor — Acesso Total ao Sistema e Configurações", "Gestor")
        self.combo_perfil.addItem("Técnico — Bancada, Diagnóstico e Ordens de Serviço", "Técnico")
        self.combo_perfil.addItem("Atendente — Balcão, Cadastro e Abertura de OS", "Atendente")

        if self.is_editing:
            idx = {"Gestor": 0, "Técnico": 1, "Atendente": 2}.get(self.user_data.get("perfil", ""), 1)
            self.combo_perfil.setCurrentIndex(idx)
        else:
            self.combo_perfil.setCurrentIndex(1)  # Padrão: Técnico

        card_layout.addWidget(lbl_perfil)
        card_layout.addWidget(self.combo_perfil)

        # Se for criação de novo usuário, solicitar senha inicial
        if not self.is_editing:
            lbl_pwd = QLabel("Senha de Acesso * (Mínimo 4 caracteres)")
            lbl_pwd.setStyleSheet(f"font-size: {TYPOGRAPHY.SIZE_CAPTION}px; font-weight: {TYPOGRAPHY.WEIGHT_BOLD}; color: {pal.TEXT_SECONDARY};")
            self.input_pwd = QLineEdit()
            self.input_pwd.setObjectName("PillSearch")
            self.input_pwd.setEchoMode(QLineEdit.Password)
            self.input_pwd.setPlaceholderText("Digite uma senha segura...")
            card_layout.addWidget(lbl_pwd)
            card_layout.addWidget(self.input_pwd)

            lbl_pwd2 = QLabel("Confirmação da Senha *")
            lbl_pwd2.setStyleSheet(f"font-size: {TYPOGRAPHY.SIZE_CAPTION}px; font-weight: {TYPOGRAPHY.WEIGHT_BOLD}; color: {pal.TEXT_SECONDARY};")
            self.input_pwd2 = QLineEdit()
            self.input_pwd2.setObjectName("PillSearch")
            self.input_pwd2.setEchoMode(QLineEdit.Password)
            self.input_pwd2.setPlaceholderText("Repita a senha digitada...")
            card_layout.addWidget(lbl_pwd2)
            card_layout.addWidget(self.input_pwd2)

        main_layout.addWidget(card)

        # Botões de Ação
        btn_box = QHBoxLayout()
        btn_box.setSpacing(SPACING.SM)
        btn_box.addStretch()

        btn_cancel = QPushButton("Cancelar")
        btn_cancel.clicked.connect(self.reject)
        btn_box.addWidget(btn_cancel)

        btn_save = QPushButton("Salvar" if self.is_editing else "Cadastrar Usuário")
        btn_save.setObjectName("PrimaryButton")
        btn_save.setIcon(get_icon("circle-check", color="#ffffff", size=ICON_SIZES.SM))
        btn_save.setIconSize(QSize(ICON_SIZES.SM, ICON_SIZES.SM))
        btn_save.clicked.connect(self.validate_and_save)
        btn_box.addWidget(btn_save)

        main_layout.addLayout(btn_box)

    def validate_and_save(self) -> None:
        nome = self.input_nome.text().strip()
        login = self.input_login.text().strip()
        perfil = self.combo_perfil.currentData()

        if not nome:
            QMessageBox.warning(self, "Atenção", "Por favor, preencha o nome completo do colaborador.")
            self.input_nome.setFocus()
            return

        if not login:
            QMessageBox.warning(self, "Atenção", "Por favor, preencha o login de acesso.")
            self.input_login.setFocus()
            return

        if not self.is_editing:
            pwd = self.input_pwd.text()
            pwd2 = self.input_pwd2.text()

            if not pwd or len(pwd) < 4:
                QMessageBox.warning(self, "Senha Fraca", "A senha de acesso deve ter pelo menos 4 caracteres.")
                self.input_pwd.setFocus()
                return

            if pwd != pwd2:
                QMessageBox.warning(self, "Senhas Divergentes", "As senhas digitadas não coincidem. Digite novamente.")
                self.input_pwd2.setFocus()
                return

        self.accept()

    def get_data(self) -> dict:
        data = {
            "nome": self.input_nome.text().strip(),
            "login": self.input_login.text().strip(),
            "perfil": self.combo_perfil.currentData(),
        }
        if not self.is_editing:
            data["password"] = self.input_pwd.text()
        return data


class PasswordDialog(QDialog):
    """Diálogo para redefinição segura de senha."""

    def __init__(self, user_name: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Orby — Alterar Senha de Acesso")
        self.setFixedSize(400, 270)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        pal = get_current_palette()

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(SPACING.XL, SPACING.XL, SPACING.XL, SPACING.XL)
        main_layout.setSpacing(SPACING.MD)

        card = QFrame()
        card.setObjectName("ContentCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(SPACING.LG, SPACING.LG, SPACING.LG, SPACING.LG)
        card_layout.setSpacing(SPACING.SM)

        info_lbl = QLabel(f"Alterando senha de:\n<b>{user_name}</b>")
        info_lbl.setStyleSheet(f"font-size: {TYPOGRAPHY.SIZE_SMALL}px; color: {pal.TEXT_PRIMARY};")
        card_layout.addWidget(info_lbl)

        lbl_pwd = QLabel("Nova Senha *")
        lbl_pwd.setStyleSheet(f"font-size: {TYPOGRAPHY.SIZE_CAPTION}px; font-weight: {TYPOGRAPHY.WEIGHT_BOLD}; color: {pal.TEXT_SECONDARY};")
        self.input_pwd = QLineEdit()
        self.input_pwd.setObjectName("PillSearch")
        self.input_pwd.setEchoMode(QLineEdit.Password)
        self.input_pwd.setPlaceholderText("Mínimo 4 caracteres...")
        card_layout.addWidget(lbl_pwd)
        card_layout.addWidget(self.input_pwd)

        lbl_pwd2 = QLabel("Confirmar Nova Senha *")
        lbl_pwd2.setStyleSheet(f"font-size: {TYPOGRAPHY.SIZE_CAPTION}px; font-weight: {TYPOGRAPHY.WEIGHT_BOLD}; color: {pal.TEXT_SECONDARY};")
        self.input_pwd2 = QLineEdit()
        self.input_pwd2.setObjectName("PillSearch")
        self.input_pwd2.setEchoMode(QLineEdit.Password)
        self.input_pwd2.setPlaceholderText("Repita a nova senha...")
        card_layout.addWidget(lbl_pwd2)
        card_layout.addWidget(self.input_pwd2)

        main_layout.addWidget(card)

        # Botões
        btn_box = QHBoxLayout()
        btn_box.setSpacing(SPACING.SM)
        btn_box.addStretch()

        btn_cancel = QPushButton("Cancelar")
        btn_cancel.clicked.connect(self.reject)
        btn_box.addWidget(btn_cancel)

        btn_save = QPushButton("Redefinir Senha")
        btn_save.setObjectName("PrimaryButton")
        btn_save.setIcon(get_icon("lock", color="#ffffff", size=ICON_SIZES.SM))
        btn_save.setIconSize(QSize(ICON_SIZES.SM, ICON_SIZES.SM))
        btn_save.clicked.connect(self.validate_and_save)
        btn_box.addWidget(btn_save)

        main_layout.addLayout(btn_box)

    def validate_and_save(self) -> None:
        pwd = self.input_pwd.text()
        pwd2 = self.input_pwd2.text()

        if not pwd or len(pwd) < 4:
            QMessageBox.warning(self, "Senha Curta", "A nova senha deve ter no mínimo 4 caracteres.")
            self.input_pwd.setFocus()
            return

        if pwd != pwd2:
            QMessageBox.warning(self, "Senhas Divergentes", "As senhas digitadas não coincidem. Verifique e tente novamente.")
            self.input_pwd2.setFocus()
            return

        self.accept()

    def get_password(self) -> str:
        return self.input_pwd.text()

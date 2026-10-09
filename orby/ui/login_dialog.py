from __future__ import annotations

from PySide6.QtCore import Qt, QSize
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ..repository import Repository
from .components import OrbLogoWidget
from .icons import IconWidget, get_icon
from .theme import get_current_palette
from .tokens import DIMENSIONS, ICON_SIZES, RADIUS, SPACING, TYPOGRAPHY


class LoginDialog(QDialog):
    """Tela de Autenticação Frutiger Aero com suporte a perfis de acesso (RBAC)."""

    def __init__(self, repository: Repository, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.repository = repository
        self.user: dict | None = None

        self.setWindowTitle("Orby — Acesso ao Sistema")
        self.setFixedSize(460, 560)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        pal = get_current_palette()

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(SPACING.XXL, SPACING.XXL, SPACING.XXL, SPACING.XXL)
        main_layout.setSpacing(SPACING.MD)

        # Container Central Glass
        card = QFrame()
        card.setObjectName("ContentCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(SPACING.XL, SPACING.XL, SPACING.XL, SPACING.XL)
        card_layout.setSpacing(SPACING.MD)

        # 1. Topo: Esfera 3D e Marca
        logo_box = QVBoxLayout()
        logo_box.setAlignment(Qt.AlignCenter)
        logo_box.setSpacing(SPACING.XS)

        self.logo = OrbLogoWidget()
        logo_box.addWidget(self.logo, 0, Qt.AlignCenter)

        title = QLabel("ORBY")
        title.setObjectName("LogoTitle")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(f"font-size: 26px; font-weight: {TYPOGRAPHY.WEIGHT_BLACK}; letter-spacing: 2px;")
        logo_box.addWidget(title)

        subtitle = QLabel("Gestão de Serviços e Assistência Técnica\npara Pequenas Empresas")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet(
            f"font-size: {TYPOGRAPHY.SIZE_CAPTION + 1}px; color: {pal.TEXT_SECONDARY}; font-weight: {TYPOGRAPHY.WEIGHT_MEDIUM};"
        )
        logo_box.addWidget(subtitle)

        card_layout.addLayout(logo_box)
        card_layout.addSpacing(SPACING.SM)

        # 2. Formulário de Credenciais
        form_layout = QVBoxLayout()
        form_layout.setSpacing(SPACING.SM + 2)

        lbl_login = QLabel("Usuário / Login")
        lbl_login.setStyleSheet(f"font-size: {TYPOGRAPHY.SIZE_SMALL}px; font-weight: {TYPOGRAPHY.WEIGHT_BOLD}; color: {pal.TEXT_PRIMARY};")
        self.login_input = QLineEdit()
        self.login_input.setObjectName("PillSearch")
        self.login_input.setPlaceholderText("Digite seu usuário...")
        self.login_input.addAction(get_icon("user", color=pal.TEXT_SECONDARY, size=15), QLineEdit.LeadingPosition)
        self.login_input.returnPressed.connect(self.focus_password)
        form_layout.addWidget(lbl_login)
        form_layout.addWidget(self.login_input)

        lbl_senha = QLabel("Senha de Acesso")
        lbl_senha.setStyleSheet(f"font-size: {TYPOGRAPHY.SIZE_SMALL}px; font-weight: {TYPOGRAPHY.WEIGHT_BOLD}; color: {pal.TEXT_PRIMARY};")
        self.password_input = QLineEdit()
        self.password_input.setObjectName("PillSearch")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText("Digite sua senha...")
        self.password_input.addAction(get_icon("lock", color=pal.TEXT_SECONDARY, size=15), QLineEdit.LeadingPosition)
        self.password_input.returnPressed.connect(self.attempt_login)
        form_layout.addWidget(lbl_senha)
        form_layout.addWidget(self.password_input)

        self.error_label = QLabel("")
        self.error_label.setAlignment(Qt.AlignCenter)
        self.error_label.setStyleSheet(
            f"color: {pal.ERROR_TEXT}; font-size: {TYPOGRAPHY.SIZE_SMALL}px; font-weight: {TYPOGRAPHY.WEIGHT_BOLD};"
        )
        self.error_label.setVisible(False)
        form_layout.addWidget(self.error_label)

        card_layout.addLayout(form_layout)
        card_layout.addSpacing(SPACING.XS)

        # 3. Botão Entrar
        self.btn_entrar = QPushButton("Entrar no Orby")
        self.btn_entrar.setObjectName("PrimaryButton")
        self.btn_entrar.setIcon(get_icon("circle-check", color="#ffffff", size=ICON_SIZES.MD))
        self.btn_entrar.setIconSize(QSize(ICON_SIZES.MD, ICON_SIZES.MD))
        self.btn_entrar.setCursor(Qt.PointingHandCursor)
        self.btn_entrar.setFixedHeight(DIMENSIONS.BUTTON_HEIGHT + 4)
        self.btn_entrar.clicked.connect(self.attempt_login)
        card_layout.addWidget(self.btn_entrar)

        # 4. Atalhos rápidos para troca de perfil de teste
        shortcuts_box = QVBoxLayout()
        shortcuts_box.setSpacing(SPACING.XS)
        shortcuts_title = QLabel("Atalhos de Acesso Rápido:")
        shortcuts_title.setAlignment(Qt.AlignCenter)
        shortcuts_title.setStyleSheet(f"font-size: {TYPOGRAPHY.SIZE_CAPTION}px; color: {pal.TEXT_SECONDARY};")
        shortcuts_box.addWidget(shortcuts_title)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(SPACING.SM)

        btn_admin = QPushButton("Gestor")
        btn_admin.setToolTip("admin / admin123")
        btn_admin.clicked.connect(lambda: self.fill_credentials("admin", "admin123"))

        btn_tec = QPushButton("Técnico")
        btn_tec.setToolTip("tecnico / tec123")
        btn_tec.clicked.connect(lambda: self.fill_credentials("tecnico", "tec123"))

        btn_atend = QPushButton("Atendente")
        btn_atend.setToolTip("atendente / atende123")
        btn_atend.clicked.connect(lambda: self.fill_credentials("atendente", "atende123"))

        btn_row.addWidget(btn_admin)
        btn_row.addWidget(btn_tec)
        btn_row.addWidget(btn_atend)
        shortcuts_box.addLayout(btn_row)

        card_layout.addLayout(shortcuts_box)
        main_layout.addWidget(card)

        # Foco inicial
        self.login_input.setFocus()

    def focus_password(self) -> None:
        self.password_input.setFocus()

    def fill_credentials(self, user: str, pwd: str) -> None:
        self.login_input.setText(user)
        self.password_input.setText(pwd)
        self.error_label.setVisible(False)
        self.password_input.setFocus()

    def attempt_login(self) -> None:
        user_text = self.login_input.text().strip()
        pwd_text = self.password_input.text()

        if not user_text or not pwd_text:
            self.error_label.setText("Informe o usuário e a senha.")
            self.error_label.setVisible(True)
            return

        user_data = self.repository.authenticate(user_text, pwd_text)
        if user_data:
            self.user = user_data
            self.accept()
        else:
            self.error_label.setText("Credenciais inválidas. Verifique usuário e senha.")
            self.error_label.setVisible(True)

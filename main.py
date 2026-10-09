import sys

from PySide6.QtWidgets import QApplication

from orby.database import Database
from orby.main_window import MainWindow
from orby.repository import Repository
from orby.ui.login_dialog import LoginDialog
from orby.ui.theme import apply_frutiger_aero_theme


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Orby")
    app.setStyle("Fusion")
    apply_frutiger_aero_theme(app)

    database = Database()
    database.initialize()
    repository = Repository(database)

    # Ciclo de Autenticação e Sessão (com suporte a Logout)
    while True:
        login_dialog = LoginDialog(repository)
        if not login_dialog.exec():
            # Usuário fechou ou cancelou a tela de login
            return 0

        current_user = login_dialog.user
        window = MainWindow(database, current_user=current_user)
        window.show()
        app.exec()

        if not getattr(window, "requested_logout", False):
            # Fechamento normal da janela pelo usuário
            break

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

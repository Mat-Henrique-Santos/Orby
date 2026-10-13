import unittest
import tempfile
import os

from orby.database import Database
from orby.repository import Repository
from orby.core.models import PerfilUsuario


class TestAuthAndRBAC(unittest.TestCase):
    def setUp(self):
        self.temp_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.temp_file.close()
        self.db = Database(self.temp_file.name)
        self.db.initialize()
        self.repo = Repository(self.db)

    def tearDown(self):
        try:
            os.remove(self.temp_file.name)
        except OSError:
            pass

    def test_default_users_seeded(self):
        users = self.repo.users()
        logins = [u["login"] for u in users]
        self.assertIn("admin", logins)
        self.assertIn("tecnico", logins)
        self.assertIn("atendente", logins)

    def test_authenticate_success(self):
        admin = self.repo.authenticate("admin", "admin123")
        self.assertIsNotNone(admin)
        self.assertEqual(admin["perfil"], PerfilUsuario.GESTOR.value)

        tec = self.repo.authenticate("tecnico", "tec123")
        self.assertIsNotNone(tec)
        self.assertEqual(tec["perfil"], PerfilUsuario.TECNICO.value)

        atend = self.repo.authenticate("atendente", "atende123")
        self.assertIsNotNone(atend)
        self.assertEqual(atend["perfil"], PerfilUsuario.ATENDENTE.value)

    def test_authenticate_case_insensitive_login(self):
        admin = self.repo.authenticate("ADMIN", "admin123")
        self.assertIsNotNone(admin)
        self.assertEqual(admin["login"], "admin")

    def test_authenticate_wrong_password(self):
        result = self.repo.authenticate("admin", "senha_errada")
        self.assertIsNone(result)

    def test_authenticate_nonexistent_user(self):
        result = self.repo.authenticate("fantasma", "123")
        self.assertIsNone(result)

    def test_add_new_user(self):
        uid = self.repo.add_user("Lucas Suporte", "lucas", "lucas123", "Técnico")
        self.assertGreater(uid, 0)

        user = self.repo.authenticate("lucas", "lucas123")
        self.assertIsNotNone(user)
        self.assertEqual(user["nome"], "Lucas Suporte")
        self.assertEqual(user["perfil"], "Técnico")

    def test_add_user_invalid_profile(self):
        with self.assertRaises(ValueError):
            self.repo.add_user("Hacker", "hacker", "123", "SuperAdmin")

    def test_rbac_repository_delete_protection(self):
        from orby.repository import PermissionDeniedError
        # Cria um cliente como Gestor
        cust_id = self.repo.add_customer("Cliente Teste", "11999998888")

        # Tenta excluir como Técnico
        self.repo.set_current_user({"id": 2, "nome": "Técnico", "perfil": "Técnico"})
        with self.assertRaises(PermissionDeniedError):
            self.repo.delete_customer(cust_id)

        # Tenta excluir como Atendente
        self.repo.set_current_user({"id": 3, "nome": "Atendente", "perfil": "Atendente"})
        with self.assertRaises(PermissionDeniedError):
            self.repo.delete_customer(cust_id)

        # Gestor consegue excluir
        self.repo.set_current_user({"id": 1, "nome": "Admin", "perfil": "Gestor"})
        ok, msg = self.repo.delete_customer(cust_id)
        self.assertTrue(ok)

    def test_rbac_repository_atendente_cannot_finalize_or_change_values(self):
        from orby.repository import PermissionDeniedError
        cust_id = self.repo.add_customer("Cliente OS", "11999997777")
        eq_id = self.repo.add_equipment(cust_id, "Celular", "Apple", "iPhone 13")
        os_id = self.repo.add_order(
            cliente_id=cust_id,
            equipamento_id=eq_id,
            descricao="Troca de tela",
            status="Aberta",
            valor=200.0,
            valor_servico=150.0,
            valor_pecas=50.0,
        )

        # Como Atendente, tentar finalizar a OS
        self.repo.set_current_user({"id": 3, "nome": "Atendente", "perfil": "Atendente"})
        with self.assertRaises(PermissionDeniedError):
            self.repo.update_order(
                order_id=os_id,
                cliente_id=cust_id,
                equipamento_id=eq_id,
                descricao="Troca de tela",
                status="Finalizada",
                valor=200.0,
                valor_servico=150.0,
                valor_pecas=50.0,
                forma_pagamento="PIX",
            )

        # Como Atendente, tentar mudar o valor financeiro
        with self.assertRaises(PermissionDeniedError):
            self.repo.update_order(
                order_id=os_id,
                cliente_id=cust_id,
                equipamento_id=eq_id,
                descricao="Troca de tela",
                status="Aberta",
                valor=300.0,
                valor_servico=250.0,
                valor_pecas=50.0,
            )


if __name__ == "__main__":
    unittest.main()

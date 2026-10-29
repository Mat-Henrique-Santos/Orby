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



    def test_scrypt_hashing_and_verification(self):
        from orby.database import hash_password, verify_password, is_legacy_hash

        hashed = hash_password("minhasenha_segura")
        self.assertTrue(hashed.startswith("scrypt$"))
        self.assertFalse(is_legacy_hash(hashed))

        # Senha correta
        self.assertTrue(verify_password("minhasenha_segura", hashed))
        # Senha incorreta
        self.assertFalse(verify_password("senha_errada", hashed))

    def test_legacy_sha256_migration_on_login(self):
        from orby.database import hash_password_legacy, is_legacy_hash

        # Insere usuário diretamente com hash legado SHA-256
        legacy_hash = hash_password_legacy("legado123")
        with self.db.connect() as conn:
            conn.execute(
                "INSERT INTO usuarios (nome, login, senha_hash, perfil, ativo) VALUES (?, ?, ?, ?, 1)",
                ("Usuário Legado", "legado", legacy_hash, "Técnico"),
            )

        # Verifica que o hash no banco é legado
        with self.db.connect() as conn:
            stored = conn.execute("SELECT senha_hash FROM usuarios WHERE login = 'legado'").fetchone()["senha_hash"]
        self.assertTrue(is_legacy_hash(stored))

        # Realiza autenticação -> deve migrar automaticamente para scrypt
        user = self.repo.authenticate("legado", "legado123")
        self.assertIsNotNone(user)
        self.assertEqual(user["login"], "legado")

        # Verifica se o banco agora possui o hash moderno scrypt
        with self.db.connect() as conn:
            updated_hash = conn.execute("SELECT senha_hash FROM usuarios WHERE login = 'legado'").fetchone()["senha_hash"]
        self.assertFalse(is_legacy_hash(updated_hash))
        self.assertTrue(updated_hash.startswith("scrypt$"))

        # Próxima autenticação com scrypt continua funcionando perfeitamente
        user2 = self.repo.authenticate("legado", "legado123")
        self.assertIsNotNone(user2)

    def test_update_user_info(self):
        uid = self.repo.add_user("Renato Suporte", "renato", "renato123", "Técnico")
        self.repo.update_user(uid, nome="Renato Silva", perfil="Gestor", login="renato.silva")

        users = self.repo.users()
        renato = next((u for u in users if u["id"] == uid), None)
        self.assertIsNotNone(renato)
        self.assertEqual(renato["nome"], "Renato Silva")
        self.assertEqual(renato["login"], "renato.silva")
        self.assertEqual(renato["perfil"], "Gestor")

    def test_change_user_password(self):
        uid = self.repo.add_user("Bruna Atendimento", "bruna", "bruna123", "Atendente")
        
        # Altera senha
        self.repo.change_password(uid, "nova_senha456")

        # Senha antiga não deve mais autenticar
        self.assertIsNone(self.repo.authenticate("bruna", "bruna123"))

        # Nova senha deve autenticar
        user = self.repo.authenticate("bruna", "nova_senha456")
        self.assertIsNotNone(user)
        self.assertEqual(user["login"], "bruna")

    def test_deactivate_user_blocks_login(self):
        uid = self.repo.add_user("Marcos Teste", "marcos", "marcos123", "Técnico")
        self.assertIsNotNone(self.repo.authenticate("marcos", "marcos123"))

        # Desativa o usuário
        self.repo.toggle_user_status(uid, False)

        # Autenticação bloqueada
        self.assertIsNone(self.repo.authenticate("marcos", "marcos123"))

        # Reativa o usuário
        self.repo.toggle_user_status(uid, True)
        self.assertIsNotNone(self.repo.authenticate("marcos", "marcos123"))

    def test_cannot_deactivate_self(self):
        # Admin logado tenta desativar a própria conta
        admin_user = self.repo.authenticate("admin", "admin123")
        self.repo.set_current_user(admin_user)

        with self.assertRaises(ValueError):
            self.repo.toggle_user_status(admin_user["id"], False)

    def test_cannot_deactivate_or_demote_last_gestor(self):
        users = self.repo.users()
        gestores = [u for u in users if u["perfil"] == "Gestor" and u["ativo"] == 1]
        self.assertEqual(len(gestores), 1)
        gestor_id = gestores[0]["id"]

        # Tentar desativar o único gestor
        self.repo.set_current_user({"id": 999, "nome": "Outro", "perfil": "Gestor"})
        with self.assertRaises(ValueError):
            self.repo.toggle_user_status(gestor_id, False)

        # Tentar rebaixar perfil do único gestor
        with self.assertRaises(ValueError):
            self.repo.update_user(gestor_id, nome="Admin", perfil="Técnico")

    def test_production_mode_setting(self):
        # Modo produção padrão é false
        self.assertEqual(self.db.get_setting("modo_producao", "false"), "false")

        # Ativa modo produção
        self.db.set_setting("modo_producao", "true")
        self.assertEqual(self.db.get_setting("modo_producao"), "true")

        # Desativa
        self.db.set_setting("modo_producao", "false")
        self.assertEqual(self.db.get_setting("modo_producao"), "false")


if __name__ == "__main__":
    unittest.main()

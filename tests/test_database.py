import gc
import os
import tempfile
import unittest

from orby.database import Database


class TestDatabase(unittest.TestCase):
    def setUp(self):
        self.temp_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.db_path = self.temp_file.name
        self.temp_file.close()
        self.db = Database(self.db_path)

    def tearDown(self):
        del self.db
        gc.collect()
        try:
            if os.path.exists(self.db_path):
                os.remove(self.db_path)
        except OSError:
            pass

    def test_database_initialization_and_tables(self):
        self.db.initialize()
        with self.db.connect() as conn:
            tables = {
                row["name"]
                for row in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()
            }
            self.assertIn("clientes", tables)
            self.assertIn("equipamentos", tables)
            self.assertIn("ordens_servico", tables)
            self.assertIn("historico_os", tables)
            self.assertIn("usuarios", tables)
            self.assertIn("configuracoes", tables)

            cliente_cols = {
                row["name"]
                for row in conn.execute("PRAGMA table_info(clientes)").fetchall()
            }
            self.assertIn("documento", cliente_cols)
            self.assertIn("endereco", cliente_cols)

    def test_settings_and_company_info(self):
        self.db.initialize()

        # Configurações inexistentes retornam default
        self.assertEqual(self.db.get_setting("empresa_nome", "Orby Default"), "Orby Default")

        # Salva dados da empresa
        self.db.set_setting("empresa_nome", "Tech Solutions Ltda")
        self.db.set_setting("empresa_cnpj", "12.345.678/0001-99")
        self.db.set_setting("empresa_telefone", "(11) 97777-6666")
        self.db.set_setting("empresa_endereco", "Av. Paulista, 1000")
        self.db.set_setting("empresa_termos", "Termos personalizados da empresa.")

        # Recupera dados
        self.assertEqual(self.db.get_setting("empresa_nome"), "Tech Solutions Ltda")
        self.assertEqual(self.db.get_setting("empresa_cnpj"), "12.345.678/0001-99")
        self.assertEqual(self.db.get_setting("empresa_telefone"), "(11) 97777-6666")
        self.assertEqual(self.db.get_setting("empresa_endereco"), "Av. Paulista, 1000")
        self.assertEqual(self.db.get_setting("empresa_termos"), "Termos personalizados da empresa.")

        # Atualiza com ON CONFLICT
        self.db.set_setting("empresa_nome", "Tech Solutions Atualizada")
        self.assertEqual(self.db.get_setting("empresa_nome"), "Tech Solutions Atualizada")


if __name__ == "__main__":
    unittest.main()

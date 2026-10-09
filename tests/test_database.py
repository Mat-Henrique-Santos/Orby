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

            cliente_cols = {
                row["name"]
                for row in conn.execute("PRAGMA table_info(clientes)").fetchall()
            }
            self.assertIn("documento", cliente_cols)
            self.assertIn("endereco", cliente_cols)


if __name__ == "__main__":
    unittest.main()

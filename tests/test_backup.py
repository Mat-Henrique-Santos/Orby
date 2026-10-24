from __future__ import annotations

import gc
import os
import shutil
import tempfile
import unittest
import zipfile
from pathlib import Path

from orby.core.backup import BackupManager, InvalidBackupFileError
from orby.database import Database, create_database


class TestBackupManager(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="orby_test_bck_")
        self.db_path = os.path.join(self.temp_dir, "orby.db")
        self.backup_dir = os.path.join(self.temp_dir, "backups")
        os.makedirs(self.backup_dir, exist_ok=True)

        self.db = Database(self.db_path)
        self.db.initialize()

        # Insere dados de teste
        with self.db.connect() as conn:
            conn.execute(
                "INSERT INTO clientes (nome, telefone, email) VALUES (?, ?, ?)",
                ("Cliente Teste Backup", "11988887777", "cliente@teste.com"),
            )
            cid = conn.execute("SELECT id FROM clientes WHERE telefone = '11988887777'").fetchone()["id"]
            conn.execute(
                "INSERT INTO ordens_servico (cliente_id, descricao, valor) VALUES (?, ?, ?)",
                (cid, "OS de Teste Backup", 250.0),
            )

        self.manager = BackupManager(db_path=self.db_path, backup_dir=self.backup_dir)

    def tearDown(self):
        del self.db
        del self.manager
        gc.collect()
        try:
            shutil.rmtree(self.temp_dir, ignore_errors=True)
        except OSError:
            pass

    def test_database_info(self):
        info = self.manager.get_database_info()
        self.assertTrue(info["exists"])
        self.assertGreater(info["size_bytes"], 0)
        self.assertEqual(info["counts"].get("clientes"), 1)
        self.assertEqual(info["counts"].get("ordens_servico"), 1)

    def test_create_backup_zip_and_validate(self):
        bck_path = self.manager.create_backup(compress=True)
        self.assertTrue(os.path.exists(bck_path))
        self.assertTrue(str(bck_path).endswith(".zip"))

        # Inspeciona conteúdo do zip
        with zipfile.ZipFile(bck_path, "r") as zf:
            self.assertIn("orby.db", zf.namelist())
            self.assertIn("backup_info.json", zf.namelist())

        # Validação
        val = self.manager.validate_backup(bck_path)
        self.assertTrue(val["valid"])
        self.assertEqual(val["counts"]["clientes"], 1)
        self.assertEqual(val["counts"]["ordens_servico"], 1)

    def test_create_backup_db(self):
        target = os.path.join(self.backup_dir, "manual_backup.db")
        bck_path = self.manager.create_backup(destination_path=target, compress=False)
        self.assertTrue(os.path.exists(bck_path))
        self.assertTrue(str(bck_path).endswith(".db"))

        val = self.manager.validate_backup(bck_path)
        self.assertTrue(val["valid"])

    def test_validate_invalid_file(self):
        # Arquivo de texto comum que não é SQLite nem ZIP válido
        invalid_file = os.path.join(self.backup_dir, "fake_backup.zip")
        with open(invalid_file, "w") as f:
            f.write("I am not a zip or sqlite database")

        with self.assertRaises(InvalidBackupFileError):
            self.manager.validate_backup(invalid_file)

    def test_restore_backup_recovers_data(self):
        # 1. Faz o backup com o estado inicial
        bck_path = self.manager.create_backup(compress=True)

        # 2. Modifica a base (deleta tudo ou adiciona lixo)
        with self.db.connect() as conn:
            conn.execute("DELETE FROM ordens_servico")
            conn.execute("DELETE FROM clientes")
            self.assertEqual(conn.execute("SELECT COUNT(*) AS c FROM clientes").fetchone()["c"], 0)

        # 3. Restaura o backup
        res = self.manager.restore_backup(bck_path)
        self.assertTrue(res["valid"])

        # 4. Verifica se os dados voltaram
        with self.db.connect() as conn:
            clientes_qtd = conn.execute("SELECT COUNT(*) AS c FROM clientes").fetchone()["c"]
            os_qtd = conn.execute("SELECT COUNT(*) AS c FROM ordens_servico").fetchone()["c"]
            self.assertEqual(clientes_qtd, 1)
            self.assertEqual(os_qtd, 1)

    def test_list_and_cleanup_backups(self):
        for i in range(5):
            self.manager.create_backup(
                destination_path=os.path.join(self.backup_dir, f"bck_{i}.zip"),
                compress=True,
            )

        backups = self.manager.list_backups()
        self.assertEqual(len(backups), 5)

        # Remove os mais antigos mantendo 2
        deleted = self.manager.cleanup_old_backups(keep_count=2)
        self.assertEqual(deleted, 3)
        self.assertEqual(len(self.manager.list_backups()), 2)

    def test_database_settings(self):
        self.db.set_setting("empresa_nome", "Assistência Técnica Alpha")
        val = self.db.get_setting("empresa_nome")
        self.assertEqual(val, "Assistência Técnica Alpha")

        default_val = self.db.get_setting("chave_inexistente", default="valor_padrao")
        self.assertEqual(default_val, "valor_padrao")

    def test_perform_auto_backup_on_exit(self):
        bck = self.manager.perform_auto_backup_on_exit()
        self.assertIsNotNone(bck)
        self.assertTrue(os.path.exists(bck))
        self.assertEqual(len(self.manager.list_backups()), 1)

    def test_create_database_factory(self):
        db = create_database("sqlite", path=self.db_path)
        self.assertIsInstance(db, Database)

        with self.assertRaises(NotImplementedError):
            create_database("postgresql")


if __name__ == "__main__":
    unittest.main()

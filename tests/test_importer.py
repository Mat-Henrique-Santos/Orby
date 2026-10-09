import os
import tempfile
import unittest

from orby.importer import read_table, validate_customers


class TestImporter(unittest.TestCase):
    def setUp(self):
        self.csv_file = tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w", encoding="utf-8")
        self.csv_file.write("nome,telefone,email,documento\n")
        self.csv_file.write("Ana Silva,11999991111,ana@teste.com,11122233344\n")
        self.csv_file.write("Bruno Costa,11988882222,bruno@teste.com,22233344455\n")
        self.csv_file.write(",11977773333,semnome@teste.com,\n")  # Sem nome
        self.csv_file.close()

    def tearDown(self):
        if os.path.exists(self.csv_file.name):
            os.remove(self.csv_file.name)

    def test_read_and_validate_csv(self):
        headers, rows = read_table(self.csv_file.name)
        self.assertIn("nome", headers)
        self.assertIn("telefone", headers)
        self.assertEqual(len(rows), 3)

        mapping = {"nome": "nome", "telefone": "telefone", "email": "email", "documento": "documento"}
        approved, rejected = validate_customers(rows, mapping, lambda n, t: False)

        self.assertEqual(len(approved), 2)
        self.assertEqual(len(rejected), 1)
        self.assertIn("Nome obrigatório", rejected[0]["motivo"])


if __name__ == "__main__":
    unittest.main()

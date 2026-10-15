import os
import tempfile
import unittest

from orby.importer import read_table, validate_customers


class TestImporter(unittest.TestCase):
    def setUp(self):
        self.csv_file = tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w", encoding="utf-8")
        self.csv_file.write("nome,telefone,email,documento\n")
        self.csv_file.write("Ana Silva,11999991111,ana@teste.com,52998224725\n")
        self.csv_file.write("Bruno Costa,11988882222,bruno@teste.com,71428793860\n")
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

    def test_read_semicolon_csv(self):
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w", encoding="utf-8") as f:
            f.write("Nome;Telefone;E-mail\n")
            f.write("Marcos Paulo;11912345678;marcos@teste.com\n")
            f.write("Luciana Lima;21987654321;luciana@teste.com\n")
            temp_name = f.name
        try:
            headers, rows = read_table(temp_name)
            self.assertEqual(headers, ["Nome", "Telefone", "E-mail"])
            self.assertEqual(len(rows), 2)
            self.assertEqual(rows[0]["Nome"], "Marcos Paulo")
            self.assertEqual(rows[0]["Telefone"], "11912345678")
        finally:
            if os.path.exists(temp_name):
                os.remove(temp_name)


if __name__ == "__main__":
    unittest.main()

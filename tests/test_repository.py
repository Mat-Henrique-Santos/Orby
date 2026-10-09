import gc
import os
import tempfile
import unittest

from orby.database import Database
from orby.repository import Repository
from orby.core.models import StatusOS


class TestRepository(unittest.TestCase):
    def setUp(self):
        self.temp_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.db_path = self.temp_file.name
        self.temp_file.close()
        self.db = Database(self.db_path)
        self.db.initialize()
        self.repo = Repository(self.db)

    def tearDown(self):
        del self.repo
        del self.db
        gc.collect()
        try:
            if os.path.exists(self.db_path):
                os.remove(self.db_path)
        except OSError:
            pass

    def test_customer_crud(self):
        cust_id = self.repo.add_customer("Carlos Silva", "11988887777", "carlos@teste.com", "12345678900", "Rua A, 100")
        self.assertIsNotNone(cust_id)

        cust = self.repo.customer(cust_id)
        self.assertEqual(cust["nome"], "Carlos Silva")
        self.assertEqual(cust["documento"], "12345678900")

        self.repo.update_customer(cust_id, "Carlos Silva Jr", "11988887777", "carlosjr@teste.com", "12345678900", "Rua B, 200")
        cust_updated = self.repo.customer(cust_id)
        self.assertEqual(cust_updated["nome"], "Carlos Silva Jr")
        self.assertEqual(cust_updated["endereco"], "Rua B, 200")

        # Test duplicate check
        is_dup = self.repo.customer_duplicate("Carlos Silva Jr", "11988887777")
        self.assertTrue(is_dup)

        # Delete customer without relations
        ok, msg = self.repo.delete_customer(cust_id)
        self.assertTrue(ok)
        self.assertIsNone(self.repo.customer(cust_id))

    def test_equipment_and_order_flow(self):
        cust_id = self.repo.add_customer("Mariana Santos", "11977776666")
        eq_id = self.repo.add_equipment(cust_id, "Notebook", "Lenovo", "ThinkPad T14", "SN123456", "Fonte", "Bom estado", "Sem marcas")
        self.assertIsNotNone(eq_id)

        order_id = self.repo.add_order(
            cliente_id=cust_id,
            equipamento_id=eq_id,
            descricao="Formatação e limpeza",
            status=StatusOS.ABERTA.value,
            valor=180.0,
            valor_servico=150.0,
            valor_pecas=30.0,
            observacoes="Urgente",
            diagnostico="HD lento, sugerido SSD",
            tecnico="Lucas",
        )
        self.assertIsNotNone(order_id)

        order = self.repo.order(order_id)
        self.assertEqual(order["cliente_nome"], "Mariana Santos")
        self.assertEqual(order["status"], StatusOS.ABERTA.value)
        self.assertEqual(order["valor_servico"], 150.0)

        # Atualizar status e finalizar com forma de pagamento
        self.repo.update_order(
            order_id=order_id,
            cliente_id=cust_id,
            equipamento_id=eq_id,
            descricao="Formatação e limpeza",
            status=StatusOS.FINALIZADA.value,
            valor=180.0,
            valor_servico=150.0,
            valor_pecas=30.0,
            forma_pagamento="PIX",
        )

        history = self.repo.order_history(order_id)
        self.assertEqual(len(history), 2)  # Criação + Alteração
        self.assertEqual(history[1]["status_anterior"], StatusOS.ABERTA.value)
        self.assertEqual(history[1]["status_novo"], StatusOS.FINALIZADA.value)

        # Verificar Dashboard Financeiro
        fin = self.repo.financial_dashboard("all")
        self.assertEqual(fin["faturamento_realizado"], 180.0)
        self.assertEqual(fin["total_servicos"], 150.0)
        self.assertEqual(fin["total_pecas"], 30.0)
        self.assertEqual(fin["os_finalizadas"], 1)
        self.assertEqual(len(fin["formas_pagamento"]), 1)
        self.assertEqual(fin["formas_pagamento"][0]["forma"], "PIX")

        # Customer with order cannot be deleted
        ok, msg = self.repo.delete_customer(cust_id)
        self.assertFalse(ok)

        # Equipment with order cannot be deleted
        ok_eq, msg_eq = self.repo.delete_equipment(eq_id)
        self.assertFalse(ok_eq)

        # Delete order first, then equipment can be deleted
        self.repo.delete_order(order_id)
        ok_eq2, msg_eq2 = self.repo.delete_equipment(eq_id)
        self.assertTrue(ok_eq2)


if __name__ == "__main__":
    unittest.main()

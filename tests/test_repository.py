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
        cust_id = self.repo.add_customer("Carlos Silva", "11988887777", "carlos@teste.com", "52998224725", "Rua A, 100")
        self.assertIsNotNone(cust_id)

        cust = self.repo.customer(cust_id)
        self.assertEqual(cust["nome"], "Carlos Silva")
        self.assertEqual(cust["documento"], "52998224725")

        self.repo.update_customer(cust_id, "Carlos Silva Jr", "11988887777", "carlosjr@teste.com", "52998224725", "Rua B, 200")
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

    def test_equipment_update_and_search(self):
        cust_id = self.repo.add_customer("Fernanda Teste", "11988889999")
        eq_id = self.repo.add_equipment(cust_id, "Impressora", "HP", "LaserJet Pro", "SN9988")

        # Busca por termo
        res = self.repo.equipment(term="LaserJet")
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]["id"], eq_id)

        # Edição de equipamento
        self.repo.update_equipment(
            equipment_id=eq_id,
            cliente_id=cust_id,
            tipo="Impressora Multifuncional",
            marca="HP",
            modelo="LaserJet Pro M404",
            numero_serie="SN9988-REV2",
            acessorios="Cabo de força",
            condicao="Excelente",
            observacoes="Toner novo instalado",
        )

        eq_updated = self.repo.single_equipment(eq_id)
        self.assertIsNotNone(eq_updated)
        self.assertEqual(eq_updated["tipo"], "Impressora Multifuncional")
        self.assertEqual(eq_updated["modelo"], "LaserJet Pro M404")
        self.assertEqual(eq_updated["numero_serie"], "SN9988-REV2")


    def test_equipment_history(self):
        cust_id = self.repo.add_customer("Carlos Aparelho", "11988887777")
        eq_id = self.repo.add_equipment(cust_id, "Celular", "Apple", "iPhone 12", "IPHONE-SN-12")

        # Abre primeira OS
        os1 = self.repo.add_order(
            cliente_id=cust_id,
            equipamento_id=eq_id,
            descricao="Troca de bateria",
            status="Finalizada",
            valor=250.0,
            forma_pagamento="PIX",
        )

        # Abre segunda OS para o mesmo equipamento
        os2 = self.repo.add_order(
            cliente_id=cust_id,
            equipamento_id=eq_id,
            descricao="Troca de conector de carga",
            status="Em Reparo",
            valor=180.0,
        )

        history = self.repo.orders_by_equipment(eq_id)
        self.assertEqual(len(history), 2)
        # Mais recente primeiro
        self.assertEqual(history[0]["id"], os2)
        self.assertEqual(history[1]["id"], os1)

    def test_delayed_orders_and_alerts(self):
        cust_id = self.repo.add_customer("Juliana Teste", "11977778888")
        eq_id = self.repo.add_equipment(cust_id, "Notebook", "Dell", "Vostro")

        # OS recente (criada agora) -> não deve estar em atraso
        os_recente = self.repo.add_order(
            cliente_id=cust_id,
            equipamento_id=eq_id,
            descricao="Formatação",
            status="Aberta",
            valor=120.0,
        )
        ordem_rec = self.repo.order(os_recente)
        self.assertFalse(ordem_rec["em_atraso"])

        # OS antiga (criada há 10 dias) diretamente no banco para simular atraso
        with self.db.connect() as conn:
            cursor = conn.execute(
                """INSERT INTO ordens_servico(cliente_id, equipamento_id, descricao, status, valor, data_abertura)
                   VALUES (?, ?, 'Placa mãe em curto', 'Em Diagnóstico', 400.0, datetime('now', '-10 days'))""",
                (cust_id, eq_id),
            )
            os_antiga_id = cursor.lastrowid

        ordem_antiga = self.repo.order(os_antiga_id)
        self.assertTrue(ordem_antiga["em_atraso"])
        self.assertGreaterEqual(ordem_antiga["dias_parada"], 9)

        # Filtro de ordens paradas
        delayed_only = self.repo.orders(status="delayed")
        delayed_ids = [o["id"] for o in delayed_only]
        self.assertIn(os_antiga_id, delayed_ids)
        self.assertNotIn(os_recente, delayed_ids)

        # Métrica do Dashboard
        dash = self.repo.dashboard()
        self.assertGreaterEqual(dash.get("atrasadas", 0), 1)


if __name__ == "__main__":
    unittest.main()

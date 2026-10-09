import unittest

from orby.core.models import Cliente, Equipamento, OrdemServico, StatusOS


class TestModels(unittest.TestCase):
    def test_cliente_valid(self):
        c = Cliente(id=1, nome="João Silva", telefone="11999998888", email="joao@teste.com")
        c.validate()
        self.assertEqual(c.nome, "João Silva")

    def test_cliente_invalid_name(self):
        c = Cliente(id=1, nome="", telefone="11999998888")
        with self.assertRaises(ValueError):
            c.validate()

    def test_cliente_invalid_phone(self):
        c = Cliente(id=1, nome="João", telefone="  ")
        with self.assertRaises(ValueError):
            c.validate()

    def test_equipamento_descricao_completa(self):
        eq = Equipamento(id=1, cliente_id=1, tipo="Notebook", marca="Dell", modelo="Inspiron 15")
        self.assertEqual(eq.descricao_completa, "Notebook Dell Inspiron 15")

    def test_equipamento_validation(self):
        eq_no_tipo = Equipamento(id=1, cliente_id=1, tipo="")
        with self.assertRaises(ValueError):
            eq_no_tipo.validate()

        eq_no_client = Equipamento(id=1, cliente_id=0, tipo="Smartphone")
        with self.assertRaises(ValueError):
            eq_no_client.validate()

    def test_ordem_servico_validation(self):
        os_valid = OrdemServico(
            id=1,
            cliente_id=1,
            equipamento_id=1,
            descricao="Troca de conector",
            status=StatusOS.ABERTA.value,
            valor=150.0,
            valor_servico=100.0,
            valor_pecas=50.0,
        )
        os_valid.validate()
        self.assertEqual(os_valid.valor, 150.0)

        os_finalizada_sem_pagamento = OrdemServico(
            id=1,
            cliente_id=1,
            equipamento_id=1,
            descricao="Troca de tela",
            status=StatusOS.FINALIZADA.value,
            valor=350.0,
            forma_pagamento="Não Definido",
        )
        with self.assertRaises(ValueError):
            os_finalizada_sem_pagamento.validate()

        os_finalizada_sem_valor = OrdemServico(
            id=1,
            cliente_id=1,
            equipamento_id=1,
            descricao="Troca de tela",
            status=StatusOS.FINALIZADA.value,
            valor=0.0,
            forma_pagamento="PIX",
        )
        with self.assertRaises(ValueError):
            os_finalizada_sem_valor.validate()


if __name__ == "__main__":
    unittest.main()

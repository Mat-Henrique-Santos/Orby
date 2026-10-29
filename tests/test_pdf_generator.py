from __future__ import annotations

import csv
import os
import shutil
import tempfile
import unittest
from pathlib import Path

from orby.core.pdf_generator import (
    export_financial_csv,
    generate_entry_receipt,
    generate_exit_receipt,
    generate_financial_report,
)


class TestPdfGenerator(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="orby_test_pdf_")

        self.mock_customer = {
            "id": 1,
            "nome": "João da Silva",
            "telefone": "(11) 98765-4321",
            "email": "joao@email.com",
            "documento": "123.456.789-00",
            "endereco": "Rua das Flores, 123 - Centro",
        }

        self.mock_equipment = {
            "id": 1,
            "tipo": "Notebook",
            "marca": "Dell",
            "modelo": "Inspiron 15",
            "numero_serie": "SN12345678",
            "acessorios": "Fonte de alimentação original e capa",
            "condicao_entrada": "Pequeno risco na tampa superior",
        }

        self.mock_order = {
            "id": 42,
            "cliente_id": 1,
            "equipamento_id": 1,
            "descricao": "Aparelho não liga após queda de energia",
            "diagnostico": "Troca de circuito regulador de tensão e regravação de BIOS",
            "tecnico": "Carlos Técnico",
            "status": "Finalizada",
            "valor": 350.0,
            "valor_servico": 250.0,
            "valor_pecas": 100.0,
            "forma_pagamento": "PIX",
            "data_abertura": "2026-10-25 10:00:00",
            "data_finalizacao": "2026-10-26 15:30:00",
            "observacoes": "Urgência solicitada pelo cliente",
        }

        self.mock_company = {
            "empresa_nome": "Orby Oficina Teste",
            "empresa_cnpj": "12.345.678/0001-99",
            "empresa_telefone": "(11) 4002-8922",
            "empresa_endereco": "Av. Tecnologia, 500",
        }

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_generate_entry_receipt(self):
        out_path = Path(self.temp_dir) / "comprovante_entrada.pdf"
        res_path = generate_entry_receipt(
            order=self.mock_order,
            customer=self.mock_customer,
            equipment=self.mock_equipment,
            company=self.mock_company,
            output_path=out_path,
        )

        self.assertTrue(os.path.exists(res_path))
        self.assertGreater(os.path.getsize(res_path), 1000)

        # Verifica cabeçalho mágico de PDF
        with open(res_path, "rb") as f:
            header = f.read(5)
            self.assertEqual(header, b"%PDF-")

    def test_generate_exit_receipt(self):
        out_path = Path(self.temp_dir) / "recibo_saida.pdf"
        res_path = generate_exit_receipt(
            order=self.mock_order,
            customer=self.mock_customer,
            equipment=self.mock_equipment,
            company=self.mock_company,
            output_path=out_path,
        )

        self.assertTrue(os.path.exists(res_path))
        self.assertGreater(os.path.getsize(res_path), 1000)

        with open(res_path, "rb") as f:
            header = f.read(5)
            self.assertEqual(header, b"%PDF-")

    def test_generate_financial_report(self):
        out_path = Path(self.temp_dir) / "relatorio_financeiro.pdf"
        fin_data = {
            "faturamento_realizado": 1500.0,
            "receita_prevista": 600.0,
            "ticket_medio": 375.0,
            "total_servicos": 1000.0,
            "total_pecas": 500.0,
            "os_finalizadas": 4,
            "formas_pagamento": [
                {"forma": "PIX", "total": 1000.0, "qtd": 2},
                {"forma": "Cartão de Crédito", "total": 500.0, "qtd": 2},
            ],
            "extrato": [
                {
                    "id": 1,
                    "cliente_nome": "João da Silva",
                    "equipamento_nome": "Notebook Dell",
                    "valor_servico": 250.0,
                    "valor_pecas": 100.0,
                    "valor": 350.0,
                    "forma_pagamento": "PIX",
                }
            ],
        }

        res_path = generate_financial_report(
            financial_data=fin_data,
            period_label="Mês Atual",
            company=self.mock_company,
            output_path=out_path,
        )

        self.assertTrue(os.path.exists(res_path))
        self.assertGreater(os.path.getsize(res_path), 1000)

        with open(res_path, "rb") as f:
            header = f.read(5)
            self.assertEqual(header, b"%PDF-")

    def test_export_financial_csv(self):
        out_path = Path(self.temp_dir) / "extrato.csv"
        rows = [
            {
                "id": 101,
                "data_abertura": "2026-10-01 09:00:00",
                "data_finalizacao": "2026-10-02 18:00:00",
                "cliente_nome": "Empresa ABC",
                "equipamento_nome": "Servidor HP",
                "valor_servico": 800.0,
                "valor_pecas": 450.0,
                "valor": 1250.0,
                "forma_pagamento": "Boleto Bancário",
                "status": "Finalizada",
            }
        ]

        res_path = export_financial_csv(rows, out_path)
        self.assertTrue(os.path.exists(res_path))

        with open(res_path, "r", encoding="utf-8-sig") as f:
            reader = csv.reader(f, delimiter=";")
            data = list(reader)
            self.assertEqual(len(data), 2)  # Header + 1 linha
            self.assertEqual(data[0][0], "Número OS")
            self.assertEqual(data[1][0], "OS-0101")
            self.assertEqual(data[1][3], "Empresa ABC")
            self.assertEqual(data[1][7], "1250,00")
            self.assertEqual(data[1][8], "Boleto Bancário")


if __name__ == "__main__":
    unittest.main()

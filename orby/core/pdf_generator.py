from __future__ import annotations

import csv
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


def get_default_docs_dir(subfolder: str = "comprovantes") -> Path:
    """Retorna o diretório padrão para armazenamento de comprovantes ou relatórios."""
    appdata = os.getenv("APPDATA")
    if appdata:
        base_dir = Path(appdata) / "Orby"
    else:
        base_dir = Path.home() / ".orby"

    target_dir = base_dir / subfolder
    target_dir.mkdir(parents=True, exist_ok=True)
    return target_dir


def formatar_moeda_pdf(valor: float | int | None) -> str:
    """Formata valor em padrão monetário brasileiro R$ 0.000,00."""
    v = float(valor or 0.0)
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def formatar_data_pdf(data_str: str | None) -> str:
    """Converte ISO timestamp ou string de data para formato DD/MM/AAAA HH:MM."""
    if not data_str:
        return "—"
    try:
        # Se for string com data e hora ISO
        cleaned = data_str.replace("T", " ")
        if len(cleaned) >= 19:
            dt = datetime.strptime(cleaned[:19], "%Y-%m-%d %H:%M:%S")
            return dt.strftime("%d/%m/%Y às %H:%M")
        elif len(cleaned) >= 10:
            dt = datetime.strptime(cleaned[:10], "%Y-%m-%d")
            return dt.strftime("%d/%m/%Y")
    except Exception:
        pass
    return str(data_str)


def _get_styles():
    styles = getSampleStyleSheet()

    # Customizações elegantes alinhadas à identidade visual do Orby
    primary_color = HexColor("#0284c7")
    dark_text = HexColor("#0f172a")
    muted_text = HexColor("#64748b")

    styles.add(
        ParagraphStyle(
            "DocTitle",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=16,
            leading=20,
            textColor=primary_color,
            alignment=1,  # Centralizado
            spaceAfter=4,
        )
    )

    styles.add(
        ParagraphStyle(
            "DocSubtitle",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=9.5,
            leading=13,
            textColor=muted_text,
            alignment=1,
            spaceAfter=12,
        )
    )

    styles.add(
        ParagraphStyle(
            "SectionHeader",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=15,
            textColor=HexColor("#0369a1"),
            spaceBefore=8,
            spaceAfter=4,
        )
    )

    styles.add(
        ParagraphStyle(
            "FieldLabel",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8.5,
            leading=11,
            textColor=dark_text,
        )
    )

    styles.add(
        ParagraphStyle(
            "FieldValue",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=11,
            textColor=dark_text,
        )
    )

    styles.add(
        ParagraphStyle(
            "TermsText",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=7.5,
            leading=10,
            textColor=HexColor("#475569"),
            alignment=4,  # Justificado
        )
    )

    styles.add(
        ParagraphStyle(
            "SignatureLabel",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8,
            leading=11,
            textColor=muted_text,
            alignment=1,
        )
    )

    return styles


def generate_entry_receipt(
    order: dict[str, Any],
    customer: dict[str, Any],
    equipment: dict[str, Any] | None,
    company: dict[str, Any] | None = None,
    output_path: str | Path | None = None,
) -> Path:
    """
    Gera o Comprovante de Entrada de Equipamento em PDF para assinatura na recepção do balcão.
    """
    company = company or {}
    empresa_nome = company.get("empresa_nome", "Orby Assistência Técnica & Gestão")
    empresa_cnpj = company.get("empresa_cnpj", "00.000.000/0001-00")
    empresa_tel = company.get("empresa_telefone", "(11) 98765-4321")
    empresa_end = company.get("empresa_endereco", "Rua Principal, 100 — Centro")

    order_id = order.get("id", 1)
    if not output_path:
        filename = f"comprovante_entrada_OS_{order_id:04d}.pdf"
        output_path = get_default_docs_dir("comprovantes") / filename
    else:
        output_path = Path(output_path)

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        leftMargin=1.5 * cm,
        rightMargin=1.5 * cm,
        topMargin=1.2 * cm,
        bottomMargin=1.2 * cm,
    )

    styles = _get_styles()
    story = []

    # Cabeçalho da Empresa
    header_data = [
        [
            Paragraph(f"<b>{empresa_nome}</b><br/><font color='#64748b' size='8'>CNPJ: {empresa_cnpj} • Tel: {empresa_tel}<br/>{empresa_end}</font>", styles["FieldValue"]),
            Paragraph(f"<font color='#0284c7' size='14'><b>ORDEM DE SERVIÇO</b></font><br/><font color='#e11d48' size='13'><b>Nº OS-{order_id:04d}</b></font><br/><font size='8' color='#64748b'>Entrada: {formatar_data_pdf(order.get('data_abertura'))}</font>", styles["FieldValue"]),
        ]
    ]
    t_header = Table(header_data, colWidths=[11.5 * cm, 6.5 * cm])
    t_header.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN", (1, 0), (1, 0), "RIGHT"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(t_header)

    story.append(HRFlowable(width="100%", thickness=1.5, color=HexColor("#0284c7"), spaceBefore=4, spaceAfter=8))
    story.append(Paragraph("COMPROVANTE DE ENTRADA E GUARDA DE EQUIPAMENTO", styles["DocTitle"]))
    story.append(Paragraph("Via destinada ao cliente para comprovação de entrega e acompanhamento da OS", styles["DocSubtitle"]))

    # Bloco 1: Dados do Cliente
    story.append(Paragraph("1. DADOS DO CLIENTE", styles["SectionHeader"]))
    doc_cliente = customer.get("documento") or "Não informado"
    tel_cliente = customer.get("telefone") or "Não informado"
    email_cliente = customer.get("email") or "Não informado"
    end_cliente = customer.get("endereco") or "Não informado"

    cli_data = [
        [
            Paragraph(f"<b>Nome:</b> {customer.get('nome', '—')}", styles["FieldValue"]),
            Paragraph(f"<b>CPF/CNPJ:</b> {doc_cliente}", styles["FieldValue"]),
        ],
        [
            Paragraph(f"<b>Telefone / WhatsApp:</b> {tel_cliente}", styles["FieldValue"]),
            Paragraph(f"<b>E-mail:</b> {email_cliente}", styles["FieldValue"]),
        ],
        [
            Paragraph(f"<b>Endereço:</b> {end_cliente}", styles["FieldValue"]),
            Paragraph(f"<b>Status Inicial:</b> <font color='#0284c7'><b>{order.get('status', 'Aberta')}</b></font>", styles["FieldValue"]),
        ]
    ]
    t_cli = Table(cli_data, colWidths=[9.0 * cm, 9.0 * cm])
    t_cli.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), HexColor("#f8fafc")),
        ("BOX", (0, 0), (-1, -1), 0.5, HexColor("#cbd5e1")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, HexColor("#e2e8f0")),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(t_cli)
    story.append(Spacer(1, 6))

    # Bloco 2: Dados do Equipamento
    story.append(Paragraph("2. DADOS DO APARELHO / EQUIPAMENTO", styles["SectionHeader"]))
    if equipment:
        eq_tipo = equipment.get("tipo", "Equipamento")
        eq_marca = equipment.get("marca") or "Não informada"
        eq_modelo = equipment.get("modelo") or "Não informado"
        eq_serie = equipment.get("numero_serie") or "Não informado"
        eq_acessorios = equipment.get("acessorios") or "Nenhum acessório retido"
        eq_condicao = equipment.get("condicao_entrada") or "Sem avarias visíveis aparentes"
    else:
        eq_tipo = "Não especificado"
        eq_marca = "—"
        eq_modelo = "—"
        eq_serie = "—"
        eq_acessorios = "Nenhum"
        eq_condicao = "Não registrada"

    eq_data = [
        [
            Paragraph(f"<b>Tipo:</b> {eq_tipo}", styles["FieldValue"]),
            Paragraph(f"<b>Marca:</b> {eq_marca}", styles["FieldValue"]),
            Paragraph(f"<b>Modelo:</b> {eq_modelo}", styles["FieldValue"]),
        ],
        [
            Paragraph(f"<b>Nº de Série / IMEI:</b> {eq_serie}", styles["FieldValue"]),
            Paragraph(f"<b>Acessórios Deixados:</b> {eq_acessorios}", styles["FieldValue"]),
            Paragraph(f"<b>Estado Físico na Entrada:</b> {eq_condicao}", styles["FieldValue"]),
        ],
    ]
    t_eq = Table(eq_data, colWidths=[6.0 * cm, 6.0 * cm, 6.0 * cm])
    t_eq.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), HexColor("#f8fafc")),
        ("BOX", (0, 0), (-1, -1), 0.5, HexColor("#cbd5e1")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, HexColor("#e2e8f0")),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(t_eq)
    story.append(Spacer(1, 6))

    # Bloco 3: Defeito e Sintomas Relatados
    story.append(Paragraph("3. DEFEITO RELATADO PELO CLIENTE", styles["SectionHeader"]))
    desc_problema = order.get("descricao") or "Não informado."
    obs_entrada = order.get("observacoes") or "Nenhuma observação adicional."

    def_data = [
        [Paragraph(f"<b>Problema / Reclamação:</b><br/>{desc_problema}", styles["FieldValue"])],
        [Paragraph(f"<b>Observações Gerais:</b><br/>{obs_entrada}", styles["FieldValue"])],
    ]
    t_def = Table(def_data, colWidths=[18.0 * cm])
    t_def.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), HexColor("#f8fafc")),
        ("BOX", (0, 0), (-1, -1), 0.5, HexColor("#cbd5e1")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, HexColor("#e2e8f0")),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(t_def)
    story.append(Spacer(1, 10))

    # Bloco 4: Termos de Ciência e Garantia
    story.append(Paragraph("4. TERMOS DE CIÊNCIA E CONDIÇÕES DE ATENDIMENTO", styles["SectionHeader"]))
    termos = (
        "1. O cliente declara que as informações prestadas são verídicas e autoriza expressamente a realização de desmontagem, "
        "diagnósticos e testes técnicos necessários para a localização do defeito.<br/>"
        "2. A empresa não se responsabiliza por dados, softwares, fotos ou mídias armazenadas no aparelho. O cliente declara estar ciente "
        "da necessidade de manter cópias prévias de segurança (backup).<br/>"
        "3. Os orçamentos emitidos possuem validade de 10 (dez) dias corridos a partir da data de comunicação ao cliente.<br/>"
        "4. Conforme a legislação vigente, equipamentos prontos ou com orçamento recusado não retirados em até 90 (noventa) dias poderão "
        "ser descartados ou alienados para ressarcimento de custos operacionais e de armazenagem."
    )
    story.append(Paragraph(termos, styles["TermsText"]))
    story.append(Spacer(1, 18))

    # Bloco 5: Assinaturas
    sig_data = [
        [
            Paragraph("____________________________________________<br/><b>Assinatura do Cliente</b><br/>Concordo com os termos e estado do aparelho", styles["SignatureLabel"]),
            Paragraph("____________________________________________<br/><b>Responsável pelo Atendimento</b><br/>Orby Gestão & Serviços", styles["SignatureLabel"]),
        ]
    ]
    t_sig = Table(sig_data, colWidths=[9.0 * cm, 9.0 * cm])
    t_sig.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(KeepTogether(t_sig))

    doc.build(story)
    return output_path


def generate_exit_receipt(
    order: dict[str, Any],
    customer: dict[str, Any],
    equipment: dict[str, Any] | None,
    company: dict[str, Any] | None = None,
    output_path: str | Path | None = None,
) -> Path:
    """
    Gera o Recibo de Saída, Laudo Técnico e Termo de Garantia em PDF após a conclusão da OS.
    """
    company = company or {}
    empresa_nome = company.get("empresa_nome", "Orby Assistência Técnica & Gestão")
    empresa_cnpj = company.get("empresa_cnpj", "00.000.000/0001-00")
    empresa_tel = company.get("empresa_telefone", "(11) 98765-4321")
    empresa_end = company.get("empresa_endereco", "Rua Principal, 100 — Centro")

    order_id = order.get("id", 1)
    if not output_path:
        filename = f"recibo_saida_laudo_OS_{order_id:04d}.pdf"
        output_path = get_default_docs_dir("comprovantes") / filename
    else:
        output_path = Path(output_path)

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        leftMargin=1.5 * cm,
        rightMargin=1.5 * cm,
        topMargin=1.2 * cm,
        bottomMargin=1.2 * cm,
    )

    styles = _get_styles()
    story = []

    # Cabeçalho da Empresa
    header_data = [
        [
            Paragraph(f"<b>{empresa_nome}</b><br/><font color='#64748b' size='8'>CNPJ: {empresa_cnpj} • Tel: {empresa_tel}<br/>{empresa_end}</font>", styles["FieldValue"]),
            Paragraph(f"<font color='#0284c7' size='14'><b>LAUDO & RECIBO DE RETIRADA</b></font><br/><font color='#059669' size='13'><b>Nº OS-{order_id:04d}</b></font><br/><font size='8' color='#64748b'>Encerramento: {formatar_data_pdf(order.get('data_finalizacao') or order.get('data_abertura'))}</font>", styles["FieldValue"]),
        ]
    ]
    t_header = Table(header_data, colWidths=[11.5 * cm, 6.5 * cm])
    t_header.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN", (1, 0), (1, 0), "RIGHT"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(t_header)

    story.append(HRFlowable(width="100%", thickness=1.5, color=HexColor("#059669"), spaceBefore=4, spaceAfter=8))
    story.append(Paragraph("LAUDO TÉCNICO PERICIAL E RECIBO DE QUITAÇÃO", styles["DocTitle"]))
    story.append(Paragraph("Comprovante definitivo de conclusão de serviços, quitação financeira e termo de garantia legal", styles["DocSubtitle"]))

    # Bloco 1: Identificação do Cliente e Equipamento
    story.append(Paragraph("1. IDENTIFICAÇÃO DO ATENDIMENTO", styles["SectionHeader"]))
    eq_nome = equipment.get("descricao_completa") if equipment and hasattr(equipment, "descricao_completa") else (
        f"{equipment.get('tipo', '')} {equipment.get('marca', '')} {equipment.get('modelo', '')}".strip() if equipment else "Aparelho"
    )
    eq_serie = equipment.get("numero_serie") if equipment else "—"

    ident_data = [
        [
            Paragraph(f"<b>Cliente:</b> {customer.get('nome', '—')}", styles["FieldValue"]),
            Paragraph(f"<b>CPF/CNPJ:</b> {customer.get('documento') or 'Não informado'}", styles["FieldValue"]),
        ],
        [
            Paragraph(f"<b>Equipamento:</b> {eq_nome}", styles["FieldValue"]),
            Paragraph(f"<b>Nº de Série / IMEI:</b> {eq_serie}", styles["FieldValue"]),
        ],
        [
            Paragraph(f"<b>Técnico Responsável:</b> {order.get('tecnico') or 'Equipe Técnica Orby'}", styles["FieldValue"]),
            Paragraph(f"<b>Status Final:</b> <font color='#059669'><b>{order.get('status', 'Finalizada')}</b></font>", styles["FieldValue"]),
        ]
    ]
    t_ident = Table(ident_data, colWidths=[9.0 * cm, 9.0 * cm])
    t_ident.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), HexColor("#f8fafc")),
        ("BOX", (0, 0), (-1, -1), 0.5, HexColor("#cbd5e1")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, HexColor("#e2e8f0")),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(t_ident)
    story.append(Spacer(1, 6))

    # Bloco 2: Laudo Técnico e Solução Realizada
    story.append(Paragraph("2. LAUDO PERICIAL E SERVIÇOS EXECUTADOS", styles["SectionHeader"]))
    laudo_texto = order.get("diagnostico") or "Manutenção, testes e reparos operacionais realizados com sucesso."
    serv_desc = order.get("descricao") or "Serviço executado conforme solicitação do cliente."

    laudo_data = [
        [Paragraph(f"<b>Problema Relatado na Entrada:</b><br/>{serv_desc}", styles["FieldValue"])],
        [Paragraph(f"<b>Diagnóstico e Serviços Executados pelo Técnico:</b><br/>{laudo_texto}", styles["FieldValue"])],
    ]
    t_laudo = Table(laudo_data, colWidths=[18.0 * cm])
    t_laudo.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), HexColor("#f8fafc")),
        ("BOX", (0, 0), (-1, -1), 0.5, HexColor("#cbd5e1")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, HexColor("#e2e8f0")),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(t_laudo)
    story.append(Spacer(1, 6))

    # Bloco 3: Discriminação Financeira e Quitação
    story.append(Paragraph("3. DISCRIMINAÇÃO FINANCEIRA E FORMA DE PAGAMENTO", styles["SectionHeader"]))
    v_serv = order.get("valor_servico", 0.0)
    v_pecas = order.get("valor_pecas", 0.0)
    v_total = order.get("valor", 0.0)
    forma_pag = order.get("forma_pagamento") or "Dinheiro / PIX"

    fin_data = [
        [
            Paragraph("<b>Item / Descrição</b>", styles["FieldLabel"]),
            Paragraph("<b>Valor (R$)</b>", styles["FieldLabel"]),
        ],
        [
            Paragraph("Mão de Obra e Serviços Especializados", styles["FieldValue"]),
            Paragraph(formatar_moeda_pdf(v_serv), styles["FieldValue"]),
        ],
        [
            Paragraph("Peças de Reposição e Componentes Aplicados", styles["FieldValue"]),
            Paragraph(formatar_moeda_pdf(v_pecas), styles["FieldValue"]),
        ],
        [
            Paragraph(f"<b>TOTAL LÍQUIDO QUITADO ({forma_pag})</b>", styles["FieldLabel"]),
            Paragraph(f"<font color='#059669' size='11'><b>{formatar_moeda_pdf(v_total)}</b></font>", styles["FieldValue"]),
        ],
    ]
    t_fin = Table(fin_data, colWidths=[13.0 * cm, 5.0 * cm])
    t_fin.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), HexColor("#e2e8f0")),
        ("BACKGROUND", (0, 1), (-1, -2), HexColor("#f8fafc")),
        ("BACKGROUND", (0, -1), (-1, -1), HexColor("#ecfdf5")),
        ("BOX", (0, 0), (-1, -1), 0.5, HexColor("#cbd5e1")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, HexColor("#e2e8f0")),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(t_fin)
    story.append(Spacer(1, 8))

    # Bloco 4: Termo de Garantia Legal (90 Dias)
    story.append(Paragraph("4. TERMO DE GARANTIA E CONDIÇÕES DE RETIRADA", styles["SectionHeader"]))
    garantia_texto = (
        "1. Conforme estabelece o Artigo 26, Inciso II do Código de Defesa do Consumidor (Lei nº 8.078/1990), "
        "os serviços executados e peças trocadas possuem garantia legal de <b>90 (noventa) dias</b> a contar da data de retirada.<br/>"
        "2. A presente garantia perde a validade em caso de violação de lacres de segurança, quedas, contato com umidade/líquidos, "
        "abertura por técnicos não autorizados ou uso em desacordo com as instruções do fabricante.<br/>"
        "3. O cliente declara que testou o equipamento no balcão e o recebeu em perfeito estado de funcionamento e conservação física."
    )
    story.append(Paragraph(garantia_texto, styles["TermsText"]))
    story.append(Spacer(1, 18))

    # Bloco 5: Assinaturas de Recebimento
    sig_data = [
        [
            Paragraph("____________________________________________<br/><b>Assinatura do Cliente / Retirante</b><br/>Recebi o aparelho testado e em perfeito estado", styles["SignatureLabel"]),
            Paragraph("____________________________________________<br/><b>Orby Assistência Técnica</b><br/>Quitação e Responsabilidade Técnica", styles["SignatureLabel"]),
        ]
    ]
    t_sig = Table(sig_data, colWidths=[9.0 * cm, 9.0 * cm])
    t_sig.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(KeepTogether(t_sig))

    doc.build(story)
    return output_path


def generate_financial_report(
    financial_data: dict[str, Any],
    period_label: str = "Todo o Período",
    company: dict[str, Any] | None = None,
    output_path: str | Path | None = None,
) -> Path:
    """
    Gera o Relatório Financeiro e Extrato de Fechamento de Caixa em PDF.
    """
    company = company or {}
    empresa_nome = company.get("empresa_nome", "Orby Assistência Técnica & Gestão")
    empresa_cnpj = company.get("empresa_cnpj", "00.000.000/0001-00")

    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    if not output_path:
        filename = f"relatorio_financeiro_{timestamp}.pdf"
        output_path = get_default_docs_dir("relatorios") / filename
    else:
        output_path = Path(output_path)

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        leftMargin=1.5 * cm,
        rightMargin=1.5 * cm,
        topMargin=1.2 * cm,
        bottomMargin=1.2 * cm,
    )

    styles = _get_styles()
    story = []

    # Cabeçalho
    header_data = [
        [
            Paragraph(f"<b>{empresa_nome}</b><br/><font color='#64748b' size='8'>CNPJ: {empresa_cnpj}</font>", styles["FieldValue"]),
            Paragraph(f"<font color='#0284c7' size='13'><b>PAINEL FINANCEIRO CONSOLIDADO</b></font><br/><font size='8' color='#64748b'>Período: {period_label}<br/>Emitido em: {datetime.now().strftime('%d/%m/%Y às %H:%M')}</font>", styles["FieldValue"]),
        ]
    ]
    t_header = Table(header_data, colWidths=[10.0 * cm, 8.0 * cm])
    t_header.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN", (1, 0), (1, 0), "RIGHT"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(t_header)
    story.append(HRFlowable(width="100%", thickness=1.5, color=HexColor("#0284c7"), spaceBefore=4, spaceAfter=8))

    story.append(Paragraph("DEMONSTRATIVO DE FATURAMENTO E FECHAMENTO", styles["DocTitle"]))
    story.append(Paragraph(f"Relatório gerencial de faturamento realizado, previsão a receber e extrato do período: {period_label}", styles["DocSubtitle"]))

    # Quadro de KPIs
    fat = financial_data.get("faturamento_realizado", 0.0)
    prev = financial_data.get("receita_prevista", 0.0)
    ticket = financial_data.get("ticket_medio", 0.0)
    servicos = financial_data.get("total_servicos", 0.0)
    pecas = financial_data.get("total_pecas", 0.0)
    finalizadas_qtd = financial_data.get("os_finalizadas", 0)

    kpi_data = [
        [
            Paragraph("<b>Faturamento Realizado</b>", styles["FieldLabel"]),
            Paragraph("<b>Receita Prevista (Aberto)</b>", styles["FieldLabel"]),
            Paragraph("<b>Ticket Médio / OS</b>", styles["FieldLabel"]),
            Paragraph("<b>OS Finalizadas</b>", styles["FieldLabel"]),
        ],
        [
            Paragraph(f"<font color='#059669' size='12'><b>{formatar_moeda_pdf(fat)}</b></font>", styles["FieldValue"]),
            Paragraph(f"<font color='#0284c7' size='12'><b>{formatar_moeda_pdf(prev)}</b></font>", styles["FieldValue"]),
            Paragraph(f"<font color='#d97706' size='12'><b>{formatar_moeda_pdf(ticket)}</b></font>", styles["FieldValue"]),
            Paragraph(f"<font color='#0f172a' size='12'><b>{finalizadas_qtd} ordens</b></font>", styles["FieldValue"]),
        ],
        [
            Paragraph(f"Total Mão de Obra: {formatar_moeda_pdf(servicos)}", styles["FieldValue"]),
            Paragraph(f"Total Peças: {formatar_moeda_pdf(pecas)}", styles["FieldValue"]),
            Paragraph("", styles["FieldValue"]),
            Paragraph("", styles["FieldValue"]),
        ]
    ]
    t_kpi = Table(kpi_data, colWidths=[4.5 * cm, 4.5 * cm, 4.5 * cm, 4.5 * cm])
    t_kpi.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), HexColor("#f8fafc")),
        ("BOX", (0, 0), (-1, -1), 0.5, HexColor("#cbd5e1")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, HexColor("#e2e8f0")),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(t_kpi)
    story.append(Spacer(1, 8))

    # Formas de Pagamento
    story.append(Paragraph("DISTRIBUIÇÃO POR FORMA DE PAGAMENTO", styles["SectionHeader"]))
    formas = financial_data.get("formas_pagamento", [])
    pay_rows = [
        [
            Paragraph("<b>Forma de Pagamento</b>", styles["FieldLabel"]),
            Paragraph("<b>Qtd. Ordens</b>", styles["FieldLabel"]),
            Paragraph("<b>Total Realizado (R$)</b>", styles["FieldLabel"]),
        ]
    ]
    if formas:
        for f in formas:
            pay_rows.append([
                Paragraph(str(f.get("forma", "Outros")), styles["FieldValue"]),
                Paragraph(str(f.get("qtd", 0)), styles["FieldValue"]),
                Paragraph(formatar_moeda_pdf(f.get("total", 0.0)), styles["FieldValue"]),
            ])
    else:
        pay_rows.append([Paragraph("Nenhum pagamento registrado no período.", styles["FieldValue"]), Paragraph("0", styles["FieldValue"]), Paragraph("R$ 0,00", styles["FieldValue"])])

    t_pay = Table(pay_rows, colWidths=[9.0 * cm, 4.0 * cm, 5.0 * cm])
    t_pay.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), HexColor("#e2e8f0")),
        ("BACKGROUND", (0, 1), (-1, -1), HexColor("#f8fafc")),
        ("BOX", (0, 0), (-1, -1), 0.5, HexColor("#cbd5e1")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, HexColor("#e2e8f0")),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("TOPPADDING", (0, 0), (-1, -1), 3.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
    ]))
    story.append(t_pay)
    story.append(Spacer(1, 8))

    # Extrato de Ordens do Período
    story.append(Paragraph("EXTRATO ANALÍTICO DE ORDENS FINALIZADAS", styles["SectionHeader"]))
    extrato = financial_data.get("extrato", [])
    ext_rows = [
        [
            Paragraph("<b>OS</b>", styles["FieldLabel"]),
            Paragraph("<b>Cliente</b>", styles["FieldLabel"]),
            Paragraph("<b>Equipamento</b>", styles["FieldLabel"]),
            Paragraph("<b>Serviço</b>", styles["FieldLabel"]),
            Paragraph("<b>Peças</b>", styles["FieldLabel"]),
            Paragraph("<b>Total</b>", styles["FieldLabel"]),
            Paragraph("<b>Pagamento</b>", styles["FieldLabel"]),
        ]
    ]

    if extrato:
        for row in extrato[:50]:  # Limite de segurança por página
            ext_rows.append([
                Paragraph(f"OS-{row.get('id', 0):04d}", styles["FieldValue"]),
                Paragraph(str(row.get("cliente_nome", ""))[:22], styles["FieldValue"]),
                Paragraph(str(row.get("equipamento_nome", ""))[:20], styles["FieldValue"]),
                Paragraph(formatar_moeda_pdf(row.get("valor_servico", 0)), styles["FieldValue"]),
                Paragraph(formatar_moeda_pdf(row.get("valor_pecas", 0)), styles["FieldValue"]),
                Paragraph(f"<b>{formatar_moeda_pdf(row.get('valor', 0))}</b>", styles["FieldValue"]),
                Paragraph(str(row.get("forma_pagamento", "—")), styles["FieldValue"]),
            ])
    else:
        ext_rows.append([Paragraph("Nenhum lançamento no extrato para o período selecionado.", styles["FieldValue"])] + [Paragraph("", styles["FieldValue"])] * 6)

    t_ext = Table(ext_rows, colWidths=[2.2 * cm, 4.0 * cm, 4.0 * cm, 2.2 * cm, 2.0 * cm, 2.3 * cm, 2.3 * cm])
    t_ext.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), HexColor("#e2e8f0")),
        ("BACKGROUND", (0, 1), (-1, -1), HexColor("#ffffff")),
        ("BOX", (0, 0), (-1, -1), 0.5, HexColor("#cbd5e1")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, HexColor("#f1f5f9")),
        ("ALIGN", (3, 0), (5, -1), "RIGHT"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    story.append(t_ext)

    doc.build(story)
    return output_path


def export_financial_csv(
    extrato_rows: list[dict[str, Any]],
    output_path: str | Path,
) -> Path:
    """
    Exporta extrato financeiro para formato CSV compatível com o Microsoft Excel em português.
    Utiliza delimitador ';' e encoding 'utf-8-sig'.
    """
    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    headers = [
        "Número OS",
        "Data Abertura",
        "Data Finalização",
        "Cliente",
        "Equipamento",
        "Valor Serviço (R$)",
        "Valor Peças (R$)",
        "Valor Total (R$)",
        "Forma de Pagamento",
        "Status",
    ]

    with open(out_path, mode="w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(headers)

        for item in extrato_rows:
            os_num = f"OS-{item.get('id', 0):04d}"
            dt_abertura = item.get("data_abertura", "")[:10]
            dt_fim = (item.get("data_finalizacao") or "")[:10]
            cliente = item.get("cliente_nome", "")
            equipamento = item.get("equipamento_nome", "")
            v_serv = f"{float(item.get('valor_servico') or 0.0):.2f}".replace(".", ",")
            v_pecas = f"{float(item.get('valor_pecas') or 0.0):.2f}".replace(".", ",")
            v_total = f"{float(item.get('valor') or 0.0):.2f}".replace(".", ",")
            pagamento = item.get("forma_pagamento") or "Não informado"
            status = item.get("status", "Finalizada")

            writer.writerow([
                os_num,
                dt_abertura,
                dt_fim,
                cliente,
                equipamento,
                v_serv,
                v_pecas,
                v_total,
                pagamento,
                status,
            ])

    return out_path

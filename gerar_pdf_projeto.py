# coding: utf-8
import os
import sys
import io
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Flowable
)
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        if self._pageNumber == 1:
            return  # Capa limpa sem cabeçalho/rodapé
        
        self.saveState()
        # Cabeçalho
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(colors.HexColor("#0284c7"))
        self.drawString(54, 752, "FACULDADE ANHANGUERA • CURSO DE ADS • PROJETO INTEGRADO")
        
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748b"))
        self.drawRightString(612 - 54, 752, "ORBY — GESTÃO OPERACIONAL DE ASSISTÊNCIA TÉCNICA")
        
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.6)
        self.line(54, 744, 612 - 54, 744)
        
        # Rodapé
        self.line(54, 45, 612 - 54, 45)
        self.setFont("Helvetica", 8.5)
        self.setFillColor(colors.HexColor("#64748b"))
        self.drawString(54, 32, "Documentação Essencial do Projeto de Software")
        self.drawRightString(612 - 54, 32, f"Página {self._pageNumber} de {page_count}")
        self.restoreState()


class Bookmark(Flowable):
    def __init__(self, key, registry):
        super().__init__()
        self.key = key
        self.registry = registry

    def draw(self):
        self.registry[self.key] = self.canv._pageNumber


def build_story(page_registry=None, is_dummy=False):
    if page_registry is None:
        page_registry = {}

    styles = getSampleStyleSheet()

    title_inst = ParagraphStyle(
        'InstTitle', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=12, leading=16, alignment=1,
        textColor=colors.HexColor("#0f172a")
    )
    title_doc = ParagraphStyle(
        'DocTitle', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=15, leading=20, alignment=1,
        textColor=colors.HexColor("#0284c7")
    )
    title_subdoc = ParagraphStyle(
        'SubDocTitle', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=12, leading=16, alignment=1,
        textColor=colors.HexColor("#0f172a")
    )
    integ_style = ParagraphStyle(
        'IntegStyle', parent=styles['Normal'],
        fontName='Helvetica', fontSize=10.5, leading=15, alignment=1,
        textColor=colors.HexColor("#334155")
    )
    h1_style = ParagraphStyle(
        'H1Style', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=12.5, leading=16.5,
        textColor=colors.HexColor("#0284c7"), spaceBefore=12, spaceAfter=5
    )
    h2_style = ParagraphStyle(
        'H2Style', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=10.5, leading=14.5,
        textColor=colors.HexColor("#0f172a"), spaceBefore=9, spaceAfter=4
    )
    body_style = ParagraphStyle(
        'BodyCustom', parent=styles['Normal'],
        fontName='Helvetica', fontSize=9.2, leading=13.2, alignment=4,
        textColor=colors.HexColor("#1e293b"), spaceAfter=5
    )
    bullet_style = ParagraphStyle(
        'BulletCustom', parent=styles['Normal'],
        fontName='Helvetica', fontSize=9, leading=13, leftIndent=12,
        alignment=4, textColor=colors.HexColor("#1e293b"), spaceAfter=3.5
    )
    tbl_header = ParagraphStyle(
        'TblH', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=8.5, leading=11,
        textColor=colors.white
    )
    tbl_cell = ParagraphStyle(
        'TblC', parent=styles['Normal'],
        fontName='Helvetica', fontSize=8.2, leading=11.2,
        textColor=colors.HexColor("#1e293b")
    )
    tbl_cell_bold = ParagraphStyle(
        'TblCBold', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=8.2, leading=11.2,
        textColor=colors.HexColor("#0f172a")
    )

    story = []

    # --- CAPA ---
    story.append(Spacer(1, 20))
    story.append(Paragraph("FACULDADE ANHANGUERA<br/>CURSO DE ANÁLISE E DESENVOLVIMENTO DE SISTEMAS<br/>DISCIPLINA: PROJETO INTEGRADO", title_inst))
    story.append(Spacer(1, 90))
    story.append(Paragraph("DOCUMENTAÇÃO ESSENCIAL DO PROJETO DE SOFTWARE", title_doc))
    story.append(Spacer(1, 8))
    story.append(Paragraph("NOME DO PROJETO: Orby", title_subdoc))
    story.append(Spacer(1, 100))
    story.append(Paragraph("<b>INTEGRANTES DO GRUPO</b><br/>Matheus Henrique dos Santos<br/>Luisa Silva Moura<br/>Luan Alexandre Matheus Corujas Saroka", integ_style))
    story.append(Spacer(1, 110))
    story.append(Paragraph("<b>Jacareí<br/>2026</b>", title_inst))
    story.append(PageBreak())

    # --- IDENTIFICAÇÃO DO PROJETO ---
    story.append(Bookmark("sec_id", page_registry))
    story.append(Paragraph("IDENTIFICAÇÃO DO PROJETO", h1_style))
    story.append(Spacer(1, 3))

    id_data = [
        [Paragraph("<b>CAMPO</b>", tbl_header), Paragraph("<b>PREENCHIMENTO</b>", tbl_header)],
        [Paragraph("Nome do projeto", tbl_cell_bold), Paragraph("Orby — Gestão Operacional de Assistência Técnica", tbl_cell)],
        [Paragraph("Turma", tbl_cell_bold), Paragraph("Análise e Desenvolvimento de Sistemas - ADS", tbl_cell)],
        [Paragraph("Semestre", tbl_cell_bold), Paragraph("2º Semestre", tbl_cell)],
        [Paragraph("Professor", tbl_cell_bold), Paragraph("Alex", tbl_cell)],
        [Paragraph("Líder ou responsável pelo contato", tbl_cell_bold), Paragraph("Matheus Henrique dos Santos", tbl_cell)],
        [
            Paragraph("Integrantes e funções", tbl_cell_bold),
            Paragraph("Luisa Silva Moura — Backend e Modelagem de Dados<br/>"
                      "Matheus Henrique dos Santos — Líder de Projeto e Backend<br/>"
                      "Luan Alexandre Matheus Corujas Saroka — Frontend e Usabilidade", tbl_cell)
        ],
        [Paragraph("Link do repositório", tbl_cell_bold), Paragraph("https://github.com/mathe/orby", tbl_cell)],
        [Paragraph("Link do protótipo", tbl_cell_bold), Paragraph("Executável Desktop Orby v2.0 (PySide6 / Windows x64)", tbl_cell)],
        [Paragraph("Data da versão final", tbl_cell_bold), Paragraph("18 de Setembro de 2026", tbl_cell)],
    ]

    t_id = Table(id_data, colWidths=[140, 364])
    t_id.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0284c7')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#f8fafc'), colors.white]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
    ]))
    story.append(t_id)
    story.append(PageBreak())

    # --- SUMÁRIO ---
    story.append(Bookmark("sec_sum", page_registry))
    story.append(Paragraph("SUMÁRIO", h1_style))

    def get_pg(key, default="1"):
        return str(page_registry.get(key, default))

    sumario_lines = [
        f"<b>IDENTIFICAÇÃO DO PROJETO</b> {'.' * 78} {get_pg('sec_id', '2')}",
        f"<b>SUMÁRIO</b> {'.' * 105} {get_pg('sec_sum', '2')}",
        f"<b>1 DEFINIÇÃO DO PROJETO</b> {'.' * 85} {get_pg('sec_1', '3')}",
        f"&nbsp;&nbsp;&nbsp;&nbsp;1.1 TEMA E CONTEXTO {'.' * 84} {get_pg('sec_1_1', '3')}",
        f"&nbsp;&nbsp;&nbsp;&nbsp;1.2 PROBLEMA {'.' * 100} {get_pg('sec_1_2', '3')}",
        f"&nbsp;&nbsp;&nbsp;&nbsp;1.3 SOLUÇÃO PROPOSTA {'.' * 86} {get_pg('sec_1_3', '3')}",
        f"&nbsp;&nbsp;&nbsp;&nbsp;1.4 OBJETIVO {'.' * 104} {get_pg('sec_1_4', '3')}",
        f"<b>2 USUÁRIOS E STAKEHOLDERS</b> {'.' * 77} {get_pg('sec_2', '4')}",
        f"&nbsp;&nbsp;&nbsp;&nbsp;2.1 USUÁRIOS FINAIS {'.' * 89} {get_pg('sec_2_1', '4')}",
        f"&nbsp;&nbsp;&nbsp;&nbsp;2.2 STAKEHOLDERS {'.' * 93} {get_pg('sec_2_2', '4')}",
        f"<b>3 ESCOPO E MVP</b> {'.' * 97} {get_pg('sec_3', '5')}",
        f"&nbsp;&nbsp;&nbsp;&nbsp;3.1 ESCOPO INCLUÍDO {'.' * 88} {get_pg('sec_3_1', '5')}",
        f"&nbsp;&nbsp;&nbsp;&nbsp;3.2 FORA DO ESCOPO {'.' * 91} {get_pg('sec_3_2', '5')}",
        f"&nbsp;&nbsp;&nbsp;&nbsp;3.3 PRODUTO MÍNIMO VIÁVEL {'.' * 77} {get_pg('sec_3_3', '5')}",
        f"&nbsp;&nbsp;&nbsp;&nbsp;3.4 RESTRIÇÕES {'.' * 100} {get_pg('sec_3_4', '5')}",
        f"<b>4 REQUISITOS DO SISTEMA</b> {'.' * 83} {get_pg('sec_4', '6')}",
        f"&nbsp;&nbsp;&nbsp;&nbsp;4.1 REQUISITOS FUNCIONAIS {'.' * 80} {get_pg('sec_4_1', '6')}",
        f"&nbsp;&nbsp;&nbsp;&nbsp;4.2 REQUISITOS NÃO FUNCIONAIS {'.' * 72} {get_pg('sec_4_2', '7')}",
        f"&nbsp;&nbsp;&nbsp;&nbsp;4.3 REGRAS DE NEGÓCIO {'.' * 87} {get_pg('sec_4_3', '7')}",
        f"<b>5 FLUXO PRINCIPAL E CASOS DE USO</b> {'.' * 66} {get_pg('sec_5', '8')}",
        f"&nbsp;&nbsp;&nbsp;&nbsp;5.1 ATORES E AÇÕES {'.' * 92} {get_pg('sec_5_1', '8')}",
        f"&nbsp;&nbsp;&nbsp;&nbsp;5.2 DIAGRAMA DE CASOS DE USO {'.' * 73} {get_pg('sec_5_2', '8')}",
        f"&nbsp;&nbsp;&nbsp;&nbsp;5.3 DESCRIÇÃO DO FLUXO PRINCIPAL {'.' * 67} {get_pg('sec_5_3', '8')}",
        f"<b>6 TELAS E PROTÓTIPO</b> {'.' * 89} {get_pg('sec_6', '9')}",
        f"&nbsp;&nbsp;&nbsp;&nbsp;6.1 MAPA DE TELAS {'.' * 96} {get_pg('sec_6_1', '9')}",
        f"&nbsp;&nbsp;&nbsp;&nbsp;6.2 WIREFRAMES OU PROTÓTIPO {'.' * 74} {get_pg('sec_6_2', '9')}",
        f"<b>7 MODELAGEM DE DADOS</b> {'.' * 80} {get_pg('sec_7', '10')}",
        f"&nbsp;&nbsp;&nbsp;&nbsp;7.1 ENTIDADES PRINCIPAIS {'.' * 83} {get_pg('sec_7_1', '10')}",
        f"&nbsp;&nbsp;&nbsp;&nbsp;7.2 DIAGRAMA ENTIDADE-RELACIONAMENTO {'.' * 56} {get_pg('sec_7_2', '10')}",
        f"<b>8 PLANEJAMENTO DO DESENVOLVIMENTO</b> {'.' * 57} {get_pg('sec_8', '11')}",
        f"&nbsp;&nbsp;&nbsp;&nbsp;8.1 TECNOLOGIAS {'.' * 97} {get_pg('sec_8_1', '11')}",
        f"&nbsp;&nbsp;&nbsp;&nbsp;8.2 RESPONSABILIDADES {'.' * 85} {get_pg('sec_8_2', '11')}",
        f"&nbsp;&nbsp;&nbsp;&nbsp;8.3 CRONOGRAMA RESUMIDO {'.' * 79} {get_pg('sec_8_3', '11')}",
        f"<b>9 VALIDAÇÃO E TESTES</b> {'.' * 84} {get_pg('sec_9', '12')}",
        f"&nbsp;&nbsp;&nbsp;&nbsp;9.1 CASOS DE TESTE {'.' * 94} {get_pg('sec_9_1', '12')}",
        f"&nbsp;&nbsp;&nbsp;&nbsp;9.2 AVALIAÇÃO DO USUÁRIO {'.' * 81} {get_pg('sec_9_2', '12')}",
        f"<b>10 ENTREGA FINAL</b> {'.' * 93} {get_pg('sec_10', '13')}",
        f"&nbsp;&nbsp;&nbsp;&nbsp;10.1 RESULTADOS ALCANÇADOS {'.' * 76} {get_pg('sec_10_1', '13')}",
        f"&nbsp;&nbsp;&nbsp;&nbsp;10.2 LIMITAÇÕES E MELHORIAS FUTURAS {'.' * 61} {get_pg('sec_10_2', '13')}",
        f"&nbsp;&nbsp;&nbsp;&nbsp;10.3 CONSIDERAÇÕES FINAIS {'.' * 80} {get_pg('sec_10_3', '13')}",
        f"&nbsp;&nbsp;&nbsp;&nbsp;10.4 LINKS DA ENTREGA {'.' * 87} {get_pg('sec_10_4', '13')}",
        f"<b>REFERÊNCIAS CONSULTADAS</b> {'.' * 75} {get_pg('sec_ref', '13')}",
    ]
    sumario_text = "<br/>".join(sumario_lines)
    p_sum = Paragraph(sumario_text, ParagraphStyle(
        'SumStyle', parent=styles['Normal'],
        fontName='Helvetica', fontSize=8.2, leading=11.6,
        textColor=colors.HexColor('#1e293b')
    ))
    story.append(p_sum)
    story.append(PageBreak())

    # --- 1 DEFINIÇÃO DO PROJETO ---
    story.append(Bookmark("sec_1", page_registry))
    story.append(Paragraph("1 DEFINIÇÃO DO PROJETO", h1_style))
    
    story.append(Bookmark("sec_1_1", page_registry))
    story.append(Paragraph("1.1 TEMA E CONTEXTO", h2_style))
    story.append(Paragraph(
        "O presente projeto insere-se no setor de prestação de serviços de assistência técnica especializada em informática, "
        "dispositivos móveis e equipamentos eletroeletrônicos. Nesses estabelecimentos, o atendimento de balcão compreende a recepção "
        "do cliente, o registro das condições do aparelho, a abertura da ordem de serviço, a execução do diagnóstico e do reparo "
        "pela bancada técnica, e a entrega do equipamento com garantia e cobrança dos serviços.",
        body_style
    ))
    story.append(Paragraph(
        "Em oficinas de pequeno e médio porte, é comum observar a ausência de sistemas dedicados, sendo frequente o uso de anotações "
        "em papel ou planilhas descentralizadas. Essa prática acarreta falhas de comunicação, perda de prazos e dificuldade em acompanhar "
        "o histórico de manutenções realizadas em cada equipamento.",
        body_style
    ))

    story.append(Bookmark("sec_1_2", page_registry))
    story.append(Paragraph("1.2 PROBLEMA", h2_style))
    story.append(Paragraph(
        "O problema central identificado é a vulnerabilidade operacional e a ausência de rastreabilidade no ciclo de vida das "
        "Ordens de Serviço (OS). Os atendentes de balcão lidam com retrabalho e inconsistências cadastrais; os técnicos perdem "
        "tempo buscando informações sobre o defeito reclamado; e a gerência não tem visibilidade em tempo real sobre a situação "
        "dos atendimentos e os valores a receber.",
        body_style
    ))
    story.append(Paragraph(
        "Essa desorganização provoca atrasos na liberação dos aparelhos, cobranças divergentes e insatisfação nos clientes.",
        body_style
    ))

    story.append(Bookmark("sec_1_3", page_registry))
    story.append(Paragraph("1.3 SOLUÇÃO PROPOSTA", h2_style))
    story.append(Paragraph(
        "A solução desenvolvida é o <b>Orby</b>, uma aplicação desktop para gerenciamento de ordens de serviço, construída com "
        "a linguagem Python, interface gráfica em PySide6 e banco de dados relacional SQLite local. O sistema centraliza o cadastro "
        "de clientes e equipamentos, organiza o ciclo de vida da OS por etapas padronizadas (Aberta, Em Diagnóstico, Em Reparo, "
        "Finalizada e Cancelada), viabiliza o apontamento de laudos técnicos e registra automaticamente o histórico das alterações.",
        body_style
    ))
    story.append(Paragraph(
        "O software foi planejado para operação em rede local ou máquina única, funcionando de maneira rápida no balcão e na bancada, "
        "sem custos recorrentes de servidores em nuvem ou dependência contínua de internet.",
        body_style
    ))

    story.append(Bookmark("sec_1_4", page_registry))
    story.append(Paragraph("1.4 OBJETIVO", h2_style))
    story.append(Paragraph(
        "Desenvolver uma aplicação desktop para gerenciar ordens de serviço em assistências técnicas, centralizando clientes, "
        "equipamentos, diagnósticos e etapas do atendimento, a fim de melhorar a rastreabilidade e a organização operacional.",
        body_style
    ))

    # --- 2 USUÁRIOS E STAKEHOLDERS ---
    story.append(Spacer(1, 4))
    story.append(Bookmark("sec_2", page_registry))
    story.append(Paragraph("2 USUÁRIOS E STAKEHOLDERS", h1_style))
    
    story.append(Bookmark("sec_2_1", page_registry))
    story.append(Paragraph("2.1 USUÁRIOS FINAIS", h2_style))
    story.append(Paragraph(
        "Os usuários finais são os colaboradores que operam o sistema no cotidiano da assistência técnica, interagindo diretamente "
        "com as interfaces para cumprir suas rotinas de trabalho:",
        body_style
    ))

    u_rows = [
        [Paragraph("<b>PERFIL DE USUÁRIO</b>", tbl_header), Paragraph("<b>NECESSIDADE PRINCIPAL</b>", tbl_header), Paragraph("<b>AÇÕES NO SISTEMA</b>", tbl_header)],
        [
            Paragraph("<b>Atendente / Recepcionista</b>", tbl_cell_bold),
            Paragraph("Agilidade no atendimento de balcão e cadastro consistente sem duplicidades.", tbl_cell),
            Paragraph("Cadastrar clientes e equipamentos, abrir Ordens de Serviço, consultar status por nome ou telefone e registrar pagamentos na entrega.", tbl_cell)
        ],
        [
            Paragraph("<b>Técnico de Bancada</b>", tbl_cell_bold),
            Paragraph("Acesso claro ao defeito relatado e registro das intervenções técnicas e peças.", tbl_cell),
            Paragraph("Consultar fila de ordens atribuídas, registrar laudo de diagnóstico técnico, atualizar o status da OS (Em Diagnóstico, Em Reparo) e apontar valores de serviço e peças.", tbl_cell)
        ],
        [
            Paragraph("<b>Gerente / Proprietário</b>", tbl_cell_bold),
            Paragraph("Acompanhamento das ordens em andamento e controle operacional do estabelecimento.", tbl_cell),
            Paragraph("Consultar todas as ordens de serviço, verificar o histórico de status de cada atendimento e autorizar cancelamentos.", tbl_cell)
        ],
    ]

    t_u = Table(u_rows, colWidths=[120, 164, 220])
    t_u.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0284c7')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#f8fafc'), colors.white]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
    ]))
    story.append(t_u)

    story.append(Bookmark("sec_2_2", page_registry))
    story.append(Paragraph("2.2 STAKEHOLDERS", h2_style))
    story.append(Paragraph(
        "Os stakeholders representam as partes interessadas ou impactadas pelo projeto, que não necessariamente operam o software "
        "como atendentes, mas possuem expectativas claras quanto aos seus resultados operacionais e de negócio:",
        body_style
    ))

    s_rows = [
        [Paragraph("<b>STAKEHOLDER</b>", tbl_header), Paragraph("<b>RELAÇÃO COM O PROJETO</b>", tbl_header), Paragraph("<b>EXPECTATIVA OU INTERESSE</b>", tbl_header)],
        [
            Paragraph("<b>Proprietário da Assistência</b>", tbl_cell_bold),
            Paragraph("Patrocinador e gestor do negócio.", tbl_cell),
            Paragraph("Aumentar a organização da oficina, evitar perdas de prazos e aparelhos, e obter transparência nos serviços cobrados sem custos recorrentes de sistemas em nuvem.", tbl_cell)
        ],
        [
            Paragraph("<b>Técnicos de Bancada</b>", tbl_cell_bold),
            Paragraph("Interessados na organização da fila de trabalho técnico.", tbl_cell),
            Paragraph("Esperam receber Ordens de Serviço com o defeito relatado claro e padronizado, reduzindo retrabalho e facilitando o apontamento do diagnóstico e do conserto.", tbl_cell)
        ],
        [
            Paragraph("<b>Clientes da Assistência</b>", tbl_cell_bold),
            Paragraph("Consumidores finais dos serviços de reparo.", tbl_cell),
            Paragraph("Obter orçamentos transparentes, prazos cumpridos, histórico confiável de manutenções anteriores e devolução segura de seus aparelhos reparados.", tbl_cell)
        ],
        [
            Paragraph("<b>Equipe de Desenvolvimento (ADS)</b>", tbl_cell_bold),
            Paragraph("Responsáveis pela entrega do software no Projeto Integrado.", tbl_cell),
            Paragraph("Entregar uma aplicação funcional, estável, com código limpo, cobertura de testes e em conformidade com as diretrizes acadêmicas.", tbl_cell)
        ],
    ]

    t_s = Table(s_rows, colWidths=[120, 154, 230])
    t_s.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0284c7')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#f8fafc'), colors.white]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
    ]))
    story.append(t_s)
    story.append(PageBreak())

    # --- 3 ESCOPO E MVP ---
    story.append(Bookmark("sec_3", page_registry))
    story.append(Paragraph("3 ESCOPO E MVP", h1_style))
    
    story.append(Bookmark("sec_3_1", page_registry))
    story.append(Paragraph("3.1 ESCOPO INCLUÍDO", h2_style))
    story.append(Paragraph(
        "O escopo planejado para a entrega concentra-se no núcleo essencial de atendimento e gestão de bancada da assistência técnica:",
        body_style
    ))

    escopo_list = [
        ("• <b>Gestão de Clientes:</b> ", "Cadastro, consulta, edição e exclusão de clientes, com validação de dados e prevenção de duplicidades por CPF/CNPJ ou telefone e nome."),
        ("• <b>Gestão de Equipamentos:</b> ", "Registro de equipamentos vinculados ao cliente proprietário, contendo tipo, marca, modelo, número de série/IMEI e avarias de entrada."),
        ("• <b>Abertura e Controle de Ordens de Serviço:</b> ", "Abertura estruturada com vínculo obrigatório cliente-equipamento, descrição do problema reclamado, consulta e esteira de status padronizada (Aberta, Em Diagnóstico, Em Reparo, Finalizada, Cancelada)."),
        ("• <b>Registro de Diagnóstico e Histórico de Status:</b> ", "Apontamento do laudo técnico emitido pelo técnico e registro automático e imutável de cada alteração de status com data e hora."),
        ("• <b>Finalização e Apontamento de Valores:</b> ", "Lançamento dos valores de serviço (mão de obra) e peças aplicadas, valor total e seleção da forma de pagamento no encerramento da OS."),
    ]
    for tit, desc in escopo_list:
        story.append(Paragraph(tit + desc, bullet_style))

    story.append(Bookmark("sec_3_2", page_registry))
    story.append(Paragraph("3.2 FORA DO ESCOPO", h2_style))
    story.append(Paragraph(
        "A fim de assegurar o foco na conclusão e a qualidade técnica do fluxo principal de atendimento, os seguintes itens foram mantidos fora do escopo desta versão:",
        body_style
    ))

    fora_list = [
        ("• <b>Dashboard Analítico Avançado e Gráficos:</b> ", "Painéis com gráficos consolidados e métricas analíticas avançadas (postergados para versões futuras, priorizando o fluxo operacional da OS)."),
        ("• <b>Importação em Lote de Planilhas:</b> ", "Assistente de importação externa via arquivos CSV/XLSX (postergado para versão posterior, mantendo o cadastro assistido no balcão)."),
        ("• <b>Emissão Fiscal Automática:</b> ", "Geração de notas fiscais eletrônicas de serviço (NFS-e / NF-e) e integração com órgãos fazendários."),
        ("• <b>Gateway de Pagamento Online:</b> ", "Integração direta com adquirentes de cartão ou liquidação automática de PIX via webhook."),
        ("• <b>Sincronização Multi-Filiais em Nuvem:</b> ", "Comunicação distribuída via internet entre diferentes estabelecimentos físicos."),
        ("• <b>Notificação Automática por Mensageria:</b> ", "Envio automático de alertas por WhatsApp ou SMS."),
    ]
    for tit, desc in fora_list:
        story.append(Paragraph(tit + desc, bullet_style))

    story.append(Bookmark("sec_3_3", page_registry))
    story.append(Paragraph("3.3 PRODUTO MÍNIMO VIÁVEL (MVP)", h2_style))
    story.append(Paragraph(
        "O Produto Mínimo Viável (MVP) do Orby concentra-se no fluxo essencial da ordem de serviço: "
        "<b>cadastrar cliente; cadastrar e vincular equipamento; abrir ordem de serviço; consultar ordens; "
        "registrar diagnóstico; atualizar status; e finalizar ou cancelar a OS.</b>",
        body_style
    ))
    story.append(Paragraph(
        "Com esse conjunto delimitado, o sistema viabiliza uma operação segura e estruturada no atendimento, "
        "eliminando o uso de anotações avulsas e garantindo a rastreabilidade completa de cada intervenção técnica, "
        "sem dispersar esforços em funcionalidades secundárias.",
        body_style
    ))

    story.append(Bookmark("sec_3_4", page_registry))
    story.append(Paragraph("3.4 RESTRIÇÕES", h2_style))
    story.append(Paragraph(
        "O desenvolvimento da solução está sujeito às seguintes restrições:",
        body_style
    ))

    res_list = [
        ("• <b>Plataforma de Execução:</b> ", "A aplicação deve funcionar como software desktop local em sistemas operacionais Microsoft Windows (10 e 11 x64) e compatível com distribuições Linux."),
        ("• <b>Stack Tecnológica:</b> ", "Utilização de Python 3.11+, PySide6 (Qt) para a interface gráfica e SQLite 3 como banco de dados relacional embarcado em arquivo local ('orby.db')."),
        ("• <b>Prazo Acadêmico:</b> ", "Conclusão e validação do projeto ao longo do semestre letivo do curso de Análise e Desenvolvimento de Sistemas na disciplina de Projeto Integrado."),
        ("• <b>Desempenho em Balcão:</b> ", "Operação ágil com tempo de resposta inferior a 1 segundo nas consultas em computadores convencionais de atendimento."),
    ]
    for tit, desc in res_list:
        story.append(Paragraph(tit + desc, bullet_style))

    # --- 4 REQUISITOS DO SISTEMA ---
    story.append(Spacer(1, 4))
    story.append(Bookmark("sec_4", page_registry))
    story.append(Paragraph("4 REQUISITOS DO SISTEMA", h1_style))
    
    story.append(Bookmark("sec_4_1", page_registry))
    story.append(Paragraph("4.1 REQUISITOS FUNCIONAIS", h2_style))
    story.append(Paragraph(
        "A tabela a seguir apresenta os requisitos funcionais que regem as operações do sistema Orby, cobrindo todo o ciclo central de atendimento:",
        body_style
    ))

    rf_rows = [
        [Paragraph("<b>CÓDIGO</b>", tbl_header), Paragraph("<b>REQUISITO FUNCIONAL</b>", tbl_header), Paragraph("<b>PRIORIDADE</b>", tbl_header)],
        [
            Paragraph("<b>RF01</b>", tbl_cell_bold),
            Paragraph("O sistema deverá permitir o cadastro, a consulta, a edição e a exclusão de clientes, armazenando nome completo, telefone, e-mail, CPF/CNPJ e endereço completo.", tbl_cell),
            Paragraph("<b>Essencial</b>", ParagraphStyle('Ess1', parent=tbl_cell, textColor=colors.HexColor('#10b981'), fontName='Helvetica-Bold'))
        ],
        [
            Paragraph("<b>RF02</b>", tbl_cell_bold),
            Paragraph("O sistema deverá validar a duplicidade de clientes no momento do cadastro, impedindo a inserção de registros com mesmo CPF/CNPJ ou mesma combinação de nome e telefone.", tbl_cell),
            Paragraph("<b>Essencial</b>", ParagraphStyle('Ess2', parent=tbl_cell, textColor=colors.HexColor('#10b981'), fontName='Helvetica-Bold'))
        ],
        [
            Paragraph("<b>RF03</b>", tbl_cell_bold),
            Paragraph("O sistema deverá permitir o cadastro e a vinculação de equipamentos ao cliente, registrando tipo, marca, modelo, número de série/IMEI, avarias de entrada e acessórios deixados.", tbl_cell),
            Paragraph("<b>Essencial</b>", ParagraphStyle('Ess3', parent=tbl_cell, textColor=colors.HexColor('#10b981'), fontName='Helvetica-Bold'))
        ],
        [
            Paragraph("<b>RF04</b>", tbl_cell_bold),
            Paragraph("O sistema deverá permitir a abertura de uma Ordem de Serviço (OS), vinculando obrigatoriamente um cliente ativo, um equipamento cadastrado e a descrição do problema relatado.", tbl_cell),
            Paragraph("<b>Essencial</b>", ParagraphStyle('Ess4', parent=tbl_cell, textColor=colors.HexColor('#10b981'), fontName='Helvetica-Bold'))
        ],
        [
            Paragraph("<b>RF05</b>", tbl_cell_bold),
            Paragraph("O sistema deverá permitir a consulta e a filtragem de Ordens de Serviço por status, cliente ou número identificador da OS.", tbl_cell),
            Paragraph("<b>Essencial</b>", ParagraphStyle('Ess5', parent=tbl_cell, textColor=colors.HexColor('#10b981'), fontName='Helvetica-Bold'))
        ],
        [
            Paragraph("<b>RF06</b>", tbl_cell_bold),
            Paragraph("O sistema deverá permitir o registro de diagnóstico técnico e laudo na Ordem de Serviço pelo responsável pela bancada.", tbl_cell),
            Paragraph("<b>Essencial</b>", ParagraphStyle('Ess6', parent=tbl_cell, textColor=colors.HexColor('#10b981'), fontName='Helvetica-Bold'))
        ],
        [
            Paragraph("<b>RF07</b>", tbl_cell_bold),
            Paragraph("O sistema deverá permitir a atualização do status da OS pelas etapas padronizadas (Aberta, Em Diagnóstico, Em Reparo, Finalizada e Cancelada) e armazenar automaticamente o histórico de cada alteração com data e hora.", tbl_cell),
            Paragraph("<b>Essencial</b>", ParagraphStyle('Ess7', parent=tbl_cell, textColor=colors.HexColor('#10b981'), fontName='Helvetica-Bold'))
        ],
        [
            Paragraph("<b>RF08</b>", tbl_cell_bold),
            Paragraph("O sistema deverá permitir a finalização ou o cancelamento da OS, exigindo o preenchimento do valor do serviço/peças (maior que zero) e forma de pagamento para o status 'Finalizada'.", tbl_cell),
            Paragraph("<b>Essencial</b>", ParagraphStyle('Ess8', parent=tbl_cell, textColor=colors.HexColor('#10b981'), fontName='Helvetica-Bold'))
        ],
    ]

    t_rf = Table(rf_rows, colWidths=[52, 368, 84])
    t_rf.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0284c7')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 3.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3.5),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#f8fafc'), colors.white]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
    ]))
    story.append(t_rf)
    story.append(PageBreak())

    # --- 4.2 REQUISITOS NÃO FUNCIONAIS ---
    story.append(Bookmark("sec_4_2", page_registry))
    story.append(Paragraph("4.2 REQUISITOS NÃO FUNCIONAIS", h2_style))
    story.append(Paragraph(
        "Registre somente requisitos de qualidade relevantes e verificáveis, como segurança, usabilidade, desempenho, compatibilidade ou acessibilidade.",
        body_style
    ))

    rnf_rows = [
        [Paragraph("<b>CÓDIGO</b>", tbl_header), Paragraph("<b>CATEGORIA</b>", tbl_header), Paragraph("<b>REQUISITO VERIFICÁVEL</b>", tbl_header), Paragraph("<b>PRIORIDADE</b>", tbl_header)],
        [
            Paragraph("<b>RNF01</b>", tbl_cell_bold),
            Paragraph("Usabilidade", tbl_cell),
            Paragraph("O sistema deverá apresentar interface gráfica intuitiva e padronizada, permitindo que um operador treinado realize a abertura de uma OS em menos de 3 minutos.", tbl_cell),
            Paragraph("<b>Essencial</b>", ParagraphStyle('REss1', parent=tbl_cell, textColor=colors.HexColor('#10b981'), fontName='Helvetica-Bold'))
        ],
        [
            Paragraph("<b>RNF02</b>", tbl_cell_bold),
            Paragraph("Desempenho", tbl_cell),
            Paragraph("O sistema deverá responder a consultas e filtros de busca em tempo inferior a 1 segundo em computadores de configuração básica de atendimento.", tbl_cell),
            Paragraph("<b>Essencial</b>", ParagraphStyle('REss2', parent=tbl_cell, textColor=colors.HexColor('#10b981'), fontName='Helvetica-Bold'))
        ],
        [
            Paragraph("<b>RNF03</b>", tbl_cell_bold),
            Paragraph("Confiabilidade", tbl_cell),
            Paragraph("O sistema deverá assegurar a persistência atômica das transações no banco SQLite local, impedindo perda de dados ou inconsistências em caso de desligamento inesperado.", tbl_cell),
            Paragraph("<b>Essencial</b>", ParagraphStyle('REss3', parent=tbl_cell, textColor=colors.HexColor('#10b981'), fontName='Helvetica-Bold'))
        ],
        [
            Paragraph("<b>RNF04</b>", tbl_cell_bold),
            Paragraph("Portabilidade", tbl_cell),
            Paragraph("O sistema deverá operar como aplicação desktop autônoma em sistemas operacionais Microsoft Windows (10 e 11 x64) e distribuições Linux compatíveis.", tbl_cell),
            Paragraph("<b>Essencial</b>", ParagraphStyle('REss4', parent=tbl_cell, textColor=colors.HexColor('#10b981'), fontName='Helvetica-Bold'))
        ],
        [
            Paragraph("<b>RNF05</b>", tbl_cell_bold),
            Paragraph("Segurança", tbl_cell),
            Paragraph("O sistema deverá validar todos os dados de entrada na interface para prevenir inconsistências cadastrais e garantir a integridade referencial do banco de dados.", tbl_cell),
            Paragraph("<b>Importante</b>", ParagraphStyle('RImp1', parent=tbl_cell, textColor=colors.HexColor('#0284c7'), fontName='Helvetica-Bold'))
        ],
    ]

    t_rnf = Table(rnf_rows, colWidths=[52, 78, 298, 76])
    t_rnf.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0284c7')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 3.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3.5),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#f8fafc'), colors.white]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
    ]))
    story.append(t_rnf)
    story.append(Spacer(1, 6))

    # --- 4.3 REGRAS DE NEGÓCIO ---
    story.append(Bookmark("sec_4_3", page_registry))
    story.append(Paragraph("4.3 REGRAS DE NEGÓCIO", h2_style))
    story.append(Paragraph(
        "Inclua apenas regras que controlam o funcionamento do negócio, como limites, prazos, permissões, cálculos ou condições obrigatórias.",
        body_style
    ))

    rn_rows = [
        [Paragraph("<b>CÓDIGO</b>", tbl_header), Paragraph("<b>REGRA DE NEGÓCIO</b>", tbl_header), Paragraph("<b>REQUISITO RELACIONADO</b>", tbl_header)],
        [
            Paragraph("<b>RN01</b>", tbl_cell_bold),
            Paragraph("Todo equipamento cadastrado deve pertencer obrigatoriamente a um cliente ativo previamente cadastrado no sistema.", tbl_cell),
            Paragraph("RF03", tbl_cell_bold)
        ],
        [
            Paragraph("<b>RN02</b>", tbl_cell_bold),
            Paragraph("Uma Ordem de Serviço não pode ser aberta sem a indicação de um cliente, um equipamento vinculado e a descrição do problema relatado.", tbl_cell),
            Paragraph("RF04", tbl_cell_bold)
        ],
        [
            Paragraph("<b>RN03</b>", tbl_cell_bold),
            Paragraph("O sistema deve impedir o cadastro de clientes em duplicidade, considerando mesmo CPF/CNPJ ou combinação idêntica de nome completo e telefone.", tbl_cell),
            Paragraph("RF02", tbl_cell_bold)
        ],
        [
            Paragraph("<b>RN04</b>", tbl_cell_bold),
            Paragraph("O registro do diagnóstico técnico na OS deve ser efetuado antes que o status do atendimento possa avançar para 'Em Reparo'.", tbl_cell),
            Paragraph("RF06, RF07", tbl_cell_bold)
        ],
        [
            Paragraph("<b>RN05</b>", tbl_cell_bold),
            Paragraph("Toda alteração de status da OS deve gerar um registro automático e imutável no histórico, contendo data, horário e o novo status.", tbl_cell),
            Paragraph("RF07", tbl_cell_bold)
        ],
        [
            Paragraph("<b>RN06</b>", tbl_cell_bold),
            Paragraph("A transição para o status 'Finalizada' exige obrigatoriamente valor total maior que zero e a seleção de uma forma de pagamento válida.", tbl_cell),
            Paragraph("RF08", tbl_cell_bold)
        ],
        [
            Paragraph("<b>RN07</b>", tbl_cell_bold),
            Paragraph("É proibida a exclusão de clientes ou equipamentos que possuam vínculos com Ordens de Serviço cadastradas no sistema.", tbl_cell),
            Paragraph("RF01, RF03, RF04", tbl_cell_bold)
        ],
    ]

    t_rn = Table(rn_rows, colWidths=[52, 368, 84])
    t_rn.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0284c7')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 3.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3.5),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#f8fafc'), colors.white]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
    ]))
    story.append(t_rn)
    story.append(PageBreak())

    # --- 5 FLUXO PRINCIPAL E CASOS DE USO ---
    story.append(Bookmark("sec_5", page_registry))
    story.append(Paragraph("5 FLUXO PRINCIPAL E CASOS DE USO", h1_style))
    
    story.append(Bookmark("sec_5_1", page_registry))
    story.append(Paragraph("5.1 ATORES E AÇÕES", h2_style))
    story.append(Paragraph(
        "A tabela a seguir descreve os atores do sistema e suas responsabilidades operacionais principais:",
        body_style
    ))

    at_rows = [
        [Paragraph("<b>ATOR</b>", tbl_header), Paragraph("<b>DESCRIÇÃO</b>", tbl_header), Paragraph("<b>PRINCIPAIS AÇÕES</b>", tbl_header)],
        [
            Paragraph("<b>Atendente</b>", tbl_cell_bold),
            Paragraph("Profissional de recepção e primeiro contato com o cliente.", tbl_cell),
            Paragraph("Cadastrar cliente e equipamento, abrir Ordem de Serviço, consultar OS e registrar a finalização com cobrança.", tbl_cell)
        ],
        [
            Paragraph("<b>Técnico</b>", tbl_cell_bold),
            Paragraph("Profissional responsável pelos diagnósticos e reparos em bancada.", tbl_cell),
            Paragraph("Consultar fila de ordens, inserir laudo técnico, atualizar status (Em Diagnóstico/Reparo) e discriminar peças e serviços.", tbl_cell)
        ],
        [
            Paragraph("<b>Gerente</b>", tbl_cell_bold),
            Paragraph("Responsável pela supervisão geral da oficina.", tbl_cell),
            Paragraph("Consultar todas as ordens, auditar histórico de alterações e autorizar o cancelamento de OS quando justificado.", tbl_cell)
        ],
    ]

    t_at = Table(at_rows, colWidths=[100, 184, 220])
    t_at.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0284c7')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 3.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3.5),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#f8fafc'), colors.white]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
    ]))
    story.append(t_at)
    story.append(Spacer(1, 4))

    story.append(Bookmark("sec_5_2", page_registry))
    story.append(Paragraph("5.2 DIAGRAMA DE CASOS DE USO", h2_style))
    story.append(Paragraph(
        "O diagrama de casos de uso do Orby estrutura as interações dos atores com as funcionalidades centrais do sistema:",
        body_style
    ))

    uc_data = [
        [Paragraph("<b>ATOR</b>", tbl_header), Paragraph("<b>CASOS DE USO ESSENCIAIS</b>", tbl_header), Paragraph("<b>DESCRIÇÃO OPERACIONAL</b>", tbl_header)],
        [
            Paragraph("<b>Atendente</b>", tbl_cell_bold),
            Paragraph("UC01 — Manter Clientes<br/>UC02 — Manter Equipamentos<br/>UC03 — Abrir Ordem de Serviço<br/>UC04 — Finalizar OS", tbl_cell),
            Paragraph("Realiza o cadastro inicial, vincula o aparelho recebido, abre a OS com o defeito relatado e finaliza a OS registrando o pagamento.", tbl_cell)
        ],
        [
            Paragraph("<b>Técnico</b>", tbl_cell_bold),
            Paragraph("UC05 — Consultar Ordens<br/>UC06 — Registrar Diagnóstico<br/>UC07 — Atualizar Status da OS", tbl_cell),
            Paragraph("Acessa a fila de bancada, emite o laudo diagnóstico e altera o status da OS registrando peças e serviços executados.", tbl_cell)
        ],
        [
            Paragraph("<b>Gerente</b>", tbl_cell_bold),
            Paragraph("UC08 — Cancelar Ordem de Serviço<br/>UC09 — Auditar Histórico", tbl_cell),
            Paragraph("Avalia ordens inviáveis ou descontinuadas, realiza o cancelamento e consulta a trilha de auditoria completa.", tbl_cell)
        ],
    ]
    t_uc = Table(uc_data, colWidths=[100, 184, 220])
    t_uc.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0284c7')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 3.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3.5),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#f8fafc'), colors.white]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
    ]))
    story.append(t_uc)
    story.append(Spacer(1, 4))

    story.append(Bookmark("sec_5_3", page_registry))
    story.append(Paragraph("5.3 DESCRIÇÃO DO FLUXO PRINCIPAL", h2_style))
    story.append(Paragraph(
        "<b>Fluxo Principal: Atendimento e Conclusão de Ordem de Serviço</b>", body_style
    ))
    passos_fluxo = [
        ("1. ", "O cliente comparece ao balcão e o atendente consulta o cadastro pelo CPF/CNPJ ou telefone. Se não existir, realiza o cadastro (RF01, RF02)."),
        ("2. ", "O atendente registra o equipamento a ser reparado, vinculando-o ao cliente com marca, modelo, número de série e avarias de entrada (RF03, RN01)."),
        ("3. ", "O atendente abre a Ordem de Serviço informando o problema relatado. O sistema gera a OS com status inicial 'Aberta' (RF04, RN02)."),
        ("4. ", "O técnico de bancada consulta as ordens abertas, inicia a análise e atualiza o status para 'Em Diagnóstico' (RF05, RF07)."),
        ("5. ", "O técnico registra o laudo técnico do diagnóstico e aponta os valores previstos de serviços e peças (RF06, RN04)."),
        ("6. ", "Após o reparo concluído, o técnico move o status da OS para 'Aguardando Retirada' (RF07, RN05)."),
        ("7. ", "O cliente retorna ao balcão, o atendente confere o serviço, insere a forma de pagamento e altera o status para 'Finalizada' (RF08, RN06)."),
    ]
    for n, p in passos_fluxo:
        story.append(Paragraph(f"<b>{n}</b>{p}", bullet_style))

    story.append(Paragraph(
        "<b>Fluxo Alternativo / Situação de Exceção:</b> Caso o cliente decida não realizar o reparo após o laudo técnico, "
        "o gerente registra o motivo da recusa e atualiza a Ordem de Serviço para o status 'Cancelada', arquivando o histórico e liberando o aparelho para devolução sem cobrança.",
        body_style
    ))
    story.append(PageBreak())

    # --- 6 TELAS E PROTÓTIPO ---
    story.append(Bookmark("sec_6", page_registry))
    story.append(Paragraph("6 TELAS E PROTÓTIPO", h1_style))
    
    story.append(Bookmark("sec_6_1", page_registry))
    story.append(Paragraph("6.1 MAPA DE TELAS", h2_style))
    story.append(Paragraph(
        "O mapa de telas reflete a navegação centralizada da aplicação desktop Orby, estruturada em abas laterais intuitivas:",
        body_style
    ))

    telas_rows = [
        [Paragraph("<b>CÓDIGO</b>", tbl_header), Paragraph("<b>TELA</b>", tbl_header), Paragraph("<b>OBJETIVO</b>", tbl_header), Paragraph("<b>USUÁRIO</b>", tbl_header)],
        [
            Paragraph("<b>TL01</b>", tbl_cell_bold),
            Paragraph("Gestão de Clientes", tbl_cell_bold),
            Paragraph("Cadastrar, consultar, editar e excluir dados cadastrais dos clientes, com checagem de duplicidades.", tbl_cell),
            Paragraph("Atendente / Gerente", tbl_cell)
        ],
        [
            Paragraph("<b>TL02</b>", tbl_cell_bold),
            Paragraph("Gestão de Equipamentos", tbl_cell_bold),
            Paragraph("Vincular aparelhos aos clientes, registrando marca, modelo, número de série e avarias de entrada.", tbl_cell),
            Paragraph("Atendente / Técnico", tbl_cell)
        ],
        [
            Paragraph("<b>TL03</b>", tbl_cell_bold),
            Paragraph("Ordens de Serviço", tbl_cell_bold),
            Paragraph("Visualizar a lista de OS, filtrar por status ou cliente, e abrir novas ordens de atendimento.", tbl_cell),
            Paragraph("Atendente / Técnico / Gerente", tbl_cell)
        ],
        [
            Paragraph("<b>TL04</b>", tbl_cell_bold),
            Paragraph("Detalhes e Diagnóstico da OS", tbl_cell_bold),
            Paragraph("Inserir laudo técnico, avançar a esteira de status, lançar valores e finalizar ou cancelar a OS.", tbl_cell),
            Paragraph("Técnico / Atendente", tbl_cell)
        ],
    ]

    t_tel = Table(telas_rows, colWidths=[48, 110, 266, 80])
    t_tel.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0284c7')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 3.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3.5),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#f8fafc'), colors.white]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
    ]))
    story.append(t_tel)
    story.append(Spacer(1, 4))

    story.append(Bookmark("sec_6_2", page_registry))
    story.append(Paragraph("6.2 WIREFRAMES OU PROTÓTIPO", h2_style))
    story.append(Paragraph(
        "O protótipo funcional foi desenvolvido nativamente com a biblioteca gráfica PySide6 (Qt for Python), apresentando uma "
        "interface padronizada com paleta de cores corporativa, ícones vetoriais SVG Lucide e formulários com validações ativas em tempo real.",
        body_style
    ))
    story.append(Paragraph(
        "A aplicação conta com navegação fluida por abas laterais fixas (Clientes, Equipamentos, Ordens de Serviço), busca dinâmica "
        "com filtragem instantânea e caixas de diálogo modais para cadastro e atualização de status, assegurando que o operador "
        "não perca o foco durante o atendimento de balcão.",
        body_style
    ))
    story.append(Paragraph(
        "<b>Link do protótipo executável:</b> Executável Desktop Orby v2.0 (compilado para Windows x64 e disponível no repositório do projeto).",
        body_style
    ))

    # --- 7 MODELAGEM DE DADOS ---
    story.append(Spacer(1, 4))
    story.append(Bookmark("sec_7", page_registry))
    story.append(Paragraph("7 MODELAGEM DE DADOS", h1_style))
    
    story.append(Bookmark("sec_7_1", page_registry))
    story.append(Paragraph("7.1 ENTIDADES PRINCIPAIS", h2_style))
    story.append(Paragraph(
        "O banco de dados relacional SQLite ('orby.db') é composto pelas seguintes entidades essenciais:",
        body_style
    ))

    ent_rows = [
        [Paragraph("<b>ENTIDADE</b>", tbl_header), Paragraph("<b>FINALIDADE</b>", tbl_header), Paragraph("<b>ATRIBUTOS PRINCIPAIS</b>", tbl_header)],
        [
            Paragraph("<b>clientes</b>", tbl_cell_bold),
            Paragraph("Armazenar dados de identificação e contato dos clientes atendidos.", tbl_cell),
            Paragraph("id (PK), nome, telefone, email, cpf_cnpj, endereco, criado_em", tbl_cell)
        ],
        [
            Paragraph("<b>equipamentos</b>", tbl_cell_bold),
            Paragraph("Registrar os dispositivos físicos deixados para manutenção.", tbl_cell),
            Paragraph("id (PK), cliente_id (FK), tipo, marca, modelo, numero_serie, avarias_entrada, acessorios, criado_em", tbl_cell)
        ],
        [
            Paragraph("<b>ordens_servico</b>", tbl_cell_bold),
            Paragraph("Controlar o atendimento, laudo técnico, valores e status da OS.", tbl_cell),
            Paragraph("id (PK), cliente_id (FK), equipamento_id (FK), defeito_reclamado, laudo_tecnico, status, valor_servico, valor_pecas, valor_total, forma_pagamento, aberto_em, finalizado_em", tbl_cell)
        ],
        [
            Paragraph("<b>historico_os</b>", tbl_cell_bold),
            Paragraph("Auditar cronologicamente todas as transições de status da OS.", tbl_cell),
            Paragraph("id (PK), os_id (FK), status_anterior, status_novo, descricao, data_hora", tbl_cell)
        ],
    ]

    t_ent = Table(ent_rows, colWidths=[90, 174, 240])
    t_ent.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0284c7')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 3.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3.5),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#f8fafc'), colors.white]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
    ]))
    story.append(t_ent)
    story.append(Spacer(1, 4))

    story.append(Bookmark("sec_7_2", page_registry))
    story.append(Paragraph("7.2 DIAGRAMA ENTIDADE-RELACIONAMENTO (DER)", h2_style))
    story.append(Paragraph(
        "O modelo relacional do Orby assegura integridade referencial por meio de chaves estrangeiras ativas (Foreign Keys):<br/>"
        "• <b>clientes (1) ——— (0..N) equipamentos:</b> Um cliente pode possuir vários equipamentos cadastrados; cada equipamento pertence a um único cliente.<br/>"
        "• <b>clientes (1) ——— (0..N) ordens_servico:</b> Um cliente pode ter múltiplas ordens de serviço vinculadas ao seu cadastro.<br/>"
        "• <b>equipamentos (1) ——— (0..N) ordens_servico:</b> Um equipamento pode acumular histórico de várias ordens ao longo de sua vida útil.<br/>"
        "• <b>ordens_servico (1) ——— (1..N) historico_os:</b> Cada OS possui um histórico de eventos e alterações de status (relação com deleção em cascata).",
        body_style
    ))
    story.append(PageBreak())

    # --- 8 PLANEJAMENTO DO DESENVOLVIMENTO ---
    story.append(Bookmark("sec_8", page_registry))
    story.append(Paragraph("8 PLANEJAMENTO DO DESENVOLVIMENTO", h1_style))
    
    story.append(Bookmark("sec_8_1", page_registry))
    story.append(Paragraph("8.1 TECNOLOGIAS", h2_style))
    story.append(Paragraph(
        "A tabela a seguir apresenta as tecnologias selecionadas para o desenvolvimento do Orby e suas justificativas:",
        body_style
    ))

    tec_rows = [
        [Paragraph("<b>PARTE DO PROJETO</b>", tbl_header), Paragraph("<b>TECNOLOGIA OU FERRAMENTA</b>", tbl_header), Paragraph("<b>JUSTIFICATIVA BREVE</b>", tbl_header)],
        [
            Paragraph("<b>Interface Gráfica</b>", tbl_cell_bold),
            Paragraph("PySide6 (Qt for Python)", tbl_cell),
            Paragraph("Framework desktop maduro, ergonômico, multiplataforma e com suporte a renderização nativa rápida.", tbl_cell)
        ],
        [
            Paragraph("<b>Aplicação</b>", tbl_cell_bold),
            Paragraph("Python 3.11+", tbl_cell),
            Paragraph("Linguagem com excelente legibilidade, suporte a tipagem estática e rica biblioteca padrão.", tbl_cell)
        ],
        [
            Paragraph("<b>Banco de Dados</b>", tbl_cell_bold),
            Paragraph("SQLite 3", tbl_cell),
            Paragraph("Motor relacional em arquivo local único, atômico, transacional (ACID) e sem necessidade de servidor externo.", tbl_cell)
        ],
        [
            Paragraph("<b>Prototipação</b>", tbl_cell_bold),
            Paragraph("Design System em PySide6", tbl_cell),
            Paragraph("Padronização de tokens de cores, espaçamentos e ícones vetoriais para consistência visual.", tbl_cell)
        ],
        [
            Paragraph("<b>Versionamento</b>", tbl_cell_bold),
            Paragraph("Git e GitHub", tbl_cell),
            Paragraph("Controle de versão distribuído, colaboração em equipe e rastreabilidade dos commits de desenvolvimento.", tbl_cell)
        ],
    ]

    t_tec = Table(tec_rows, colWidths=[110, 150, 244])
    t_tec.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0284c7')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 3.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3.5),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#f8fafc'), colors.white]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
    ]))
    story.append(t_tec)
    story.append(Spacer(1, 4))

    story.append(Bookmark("sec_8_2", page_registry))
    story.append(Paragraph("8.2 RESPONSABILIDADES", h2_style))
    story.append(Paragraph(
        "A distribuição de atribuições entre os três integrantes da equipe foi organizada por competências técnicas:",
        body_style
    ))

    resp_rows = [
        [Paragraph("<b>INTEGRANTE</b>", tbl_header), Paragraph("<b>RESPONSABILIDADE</b>", tbl_header), Paragraph("<b>ENTREGAS PREVISTAS</b>", tbl_header)],
        [
            Paragraph("<b>Matheus Henrique dos Santos</b>", tbl_cell_bold),
            Paragraph("Líder do Projeto e Desenvolvedor Backend", tbl_cell),
            Paragraph("Arquitetura geral da aplicação, esteira de status da OS, repositório de dados, testes automatizados e compilação do executável.", tbl_cell)
        ],
        [
            Paragraph("<b>Luisa Silva Moura</b>", tbl_cell_bold),
            Paragraph("Desenvolvedora Backend e Banco de Dados", tbl_cell),
            Paragraph("Estruturação do banco SQLite, regras de negócio de integridade referencial, validação de duplicidades e cálculos de serviços.", tbl_cell)
        ],
        [
            Paragraph("<b>Luan Alexandre M. C. Saroka</b>", tbl_cell_bold),
            Paragraph("Desenvolvedor Frontend e Usabilidade", tbl_cell),
            Paragraph("Construção das telas com PySide6, formulários modais, mapa de telas, estilização visual e integração de ícones Lucide.", tbl_cell)
        ],
    ]

    t_resp = Table(resp_rows, colWidths=[120, 150, 234])
    t_resp.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0284c7')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 3.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3.5),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#f8fafc'), colors.white]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
    ]))
    story.append(t_resp)
    story.append(Spacer(1, 4))

    story.append(Bookmark("sec_8_3", page_registry))
    story.append(Paragraph("8.3 CRONOGRAMA RESUMIDO", h2_style))
    story.append(Paragraph(
        "O cronograma do projeto foi executado conforme as etapas planejadas para a disciplina de Projeto Integrado:",
        body_style
    ))

    crono_rows = [
        [Paragraph("<b>ETAPA</b>", tbl_header), Paragraph("<b>RESPONSÁVEL</b>", tbl_header), Paragraph("<b>PRAZO</b>", tbl_header), Paragraph("<b>STATUS</b>", tbl_header)],
        [Paragraph("Requisitos e escopo", tbl_cell_bold), Paragraph("Toda a equipe", tbl_cell), Paragraph("Semanas 1 a 2", tbl_cell), Paragraph("<b>Concluído</b>", tbl_cell_bold)],
        [Paragraph("Modelagem e banco de dados", tbl_cell_bold), Paragraph("Luisa e Matheus", tbl_cell), Paragraph("Semanas 3 a 4", tbl_cell), Paragraph("<b>Concluído</b>", tbl_cell_bold)],
        [Paragraph("Protótipo e telas", tbl_cell_bold), Paragraph("Luan e Matheus", tbl_cell), Paragraph("Semanas 5 a 6", tbl_cell), Paragraph("<b>Concluído</b>", tbl_cell_bold)],
        [Paragraph("Desenvolvimento da OS e regras", tbl_cell_bold), Paragraph("Matheus e Luisa", tbl_cell), Paragraph("Semanas 7 a 8", tbl_cell), Paragraph("<b>Concluído</b>", tbl_cell_bold)],
        [Paragraph("Testes e ajustes", tbl_cell_bold), Paragraph("Toda a equipe", tbl_cell), Paragraph("Semanas 9 a 10", tbl_cell), Paragraph("<b>Concluído</b>", tbl_cell_bold)],
        [Paragraph("Apresentação final", tbl_cell_bold), Paragraph("Toda a equipe", tbl_cell), Paragraph("Semana 12", tbl_cell), Paragraph("Em andamento", tbl_cell)],
    ]

    t_cro = Table(crono_rows, colWidths=[160, 130, 114, 100])
    t_cro.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0284c7')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 3.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3.5),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#f8fafc'), colors.white]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
    ]))
    story.append(t_cro)
    story.append(PageBreak())

    # --- 9 VALIDAÇÃO E TESTES ---
    story.append(Bookmark("sec_9", page_registry))
    story.append(Paragraph("9 VALIDAÇÃO E TESTES", h1_style))
    
    story.append(Bookmark("sec_9_1", page_registry))
    story.append(Paragraph("9.1 CASOS DE TESTE", h2_style))
    story.append(Paragraph(
        "Registre pelo menos cinco testes das funcionalidades essenciais. Inclua situações válidas e inválidas e compare o resultado esperado com o obtido:",
        body_style
    ))

    test_rows = [
        [Paragraph("<b>CÓDIGO</b>", tbl_header), Paragraph("<b>FUNCIONALIDADE E PROCEDIMENTO</b>", tbl_header), Paragraph("<b>RESULTADO ESPERADO</b>", tbl_header), Paragraph("<b>RESULTADO OBTIDO</b>", tbl_header), Paragraph("<b>STATUS</b>", tbl_header)],
        [
            Paragraph("<b>CT01</b>", tbl_cell_bold),
            Paragraph("Cadastro de cliente com CPF já registrado no sistema (situação inválida).", tbl_cell),
            Paragraph("Bloquear cadastro e alertar duplicidade.", tbl_cell),
            Paragraph("Cadastro bloqueado com mensagem de erro clara.", tbl_cell),
            Paragraph("<b>Aprovado</b>", ParagraphStyle('Aprov1', parent=tbl_cell, textColor=colors.HexColor('#10b981'), fontName='Helvetica-Bold'))
        ],
        [
            Paragraph("<b>CT02</b>", tbl_cell_bold),
            Paragraph("Abertura de OS com cliente, aparelho e defeito relatado preenchidos (situação válida).", tbl_cell),
            Paragraph("Criar OS com status inicial 'Aberta'.", tbl_cell),
            Paragraph("OS gerada com sucesso e visível na listagem.", tbl_cell),
            Paragraph("<b>Aprovado</b>", ParagraphStyle('Aprov2', parent=tbl_cell, textColor=colors.HexColor('#10b981'), fontName='Helvetica-Bold'))
        ],
        [
            Paragraph("<b>CT03</b>", tbl_cell_bold),
            Paragraph("Atualização de status da OS de 'Aberta' para 'Em Diagnóstico' pelo técnico.", tbl_cell),
            Paragraph("Status alterado e evento gravado no histórico.", tbl_cell),
            Paragraph("Status atualizado e registrado no historico_os.", tbl_cell),
            Paragraph("<b>Aprovado</b>", ParagraphStyle('Aprov3', parent=tbl_cell, textColor=colors.HexColor('#10b981'), fontName='Helvetica-Bold'))
        ],
        [
            Paragraph("<b>CT04</b>", tbl_cell_bold),
            Paragraph("Tentativa de finalizar OS sem valor informado ou igual a zero (situação inválida).", tbl_cell),
            Paragraph("Impedir finalização e exigir valor maior que zero.", tbl_cell),
            Paragraph("Finalização bloqueada exigindo valor válido.", tbl_cell),
            Paragraph("<b>Aprovado</b>", ParagraphStyle('Aprov4', parent=tbl_cell, textColor=colors.HexColor('#10b981'), fontName='Helvetica-Bold'))
        ],
        [
            Paragraph("<b>CT05</b>", tbl_cell_bold),
            Paragraph("Tentativa de excluir cliente que possui Ordens de Serviço associadas (situação inválida).", tbl_cell),
            Paragraph("Bloquear exclusão informando integridade referencial.", tbl_cell),
            Paragraph("Exclusão impedida pelo banco com aviso na tela.", tbl_cell),
            Paragraph("<b>Aprovado</b>", ParagraphStyle('Aprov5', parent=tbl_cell, textColor=colors.HexColor('#10b981'), fontName='Helvetica-Bold'))
        ],
    ]

    t_test = Table(test_rows, colWidths=[42, 138, 114, 140, 70])
    t_test.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0284c7')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 3.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3.5),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#f8fafc'), colors.white]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
    ]))
    story.append(t_test)
    story.append(Spacer(1, 4))

    story.append(Bookmark("sec_9_2", page_registry))
    story.append(Paragraph("9.2 AVALIAÇÃO DO USUÁRIO", h2_style))
    story.append(Paragraph(
        "A validação do sistema foi realizada pela equipe através de uma simulação estruturada de atendimento de oficina, "
        "reproduzindo o ciclo de 10 atendimentos completos: recepção, cadastro de novos clientes, apontamento de defeitos de bancada, "
        "execução técnica, fechamento de valores e entrega ao cliente.",
        body_style
    ))
    story.append(Paragraph(
        "Os avaliadores destacaram como ponto forte a agilidade na busca de clientes e a clareza da esteira de status, "
        "que torna visível o estado de cada aparelho sem necessidade de consultar papéis ou planilhas externas.",
        body_style
    ))

    # --- 10 ENTREGA FINAL ---
    story.append(Spacer(1, 4))
    story.append(Bookmark("sec_10", page_registry))
    story.append(Paragraph("10 ENTREGA FINAL", h1_style))
    
    story.append(Bookmark("sec_10_1", page_registry))
    story.append(Paragraph("10.1 RESULTADOS ALCANÇADOS", h2_style))
    story.append(Paragraph(
        "O projeto entregou com sucesso o MVP planejado do Orby, contendo o fluxo operacional completo de gerenciamento de ordens de serviço: "
        "cadastro seguro de clientes com prevenção de duplicidades, cadastro e vinculação de equipamentos, abertura de OS com defeito relatado, "
        "esteira controlada de status com laudo de diagnóstico, histórico cronológico de transições e encerramento financeiro com registro de pagamentos.",
        body_style
    ))

    story.append(Bookmark("sec_10_2", page_registry))
    story.append(Paragraph("10.2 LIMITAÇÕES E MELHORIAS FUTURAS", h2_style))
    story.append(Paragraph(
        "Como limitações da versão atual, o sistema não contempla emissão fiscal automatizada nem sincronização multi-lojas via nuvem. "
        "Para versões posteriores, planeja-se a inclusão de um módulo analítico com gráficos gerenciais de faturamento, "
        "assistente de importação em lote de planilhas e integração com serviços de notificação por mensagens (WhatsApp/SMS).",
        body_style
    ))

    story.append(Bookmark("sec_10_3", page_registry))
    story.append(Paragraph("10.3 CONSIDERAÇÕES FINAIS", h2_style))
    story.append(Paragraph(
        "O desenvolvimento do Orby permitiu consolidar na prática os fundamentos de Engenharia de Software, modelagem de dados "
        "relacional e desenvolvimento de interfaces gráficas em Python com PySide6. A experiência evidenciou a importância de manter "
        "o foco no fluxo operacional central antes de introduzir recursos secundários, garantindo uma aplicação estável, robusta e aderente às necessidades reais de assistências técnicas.",
        body_style
    ))

    story.append(Bookmark("sec_10_4", page_registry))
    story.append(Paragraph("10.4 LINKS DA ENTREGA", h2_style))
    
    link_rows = [
        [Paragraph("<b>ITEM</b>", tbl_header), Paragraph("<b>LINK OU LOCALIZAÇÃO</b>", tbl_header)],
        [Paragraph("Repositório do código", tbl_cell_bold), Paragraph("https://github.com/mathe/orby", tbl_cell)],
        [Paragraph("Protótipo", tbl_cell_bold), Paragraph("Executável Desktop Orby v2.0 (PySide6 / Windows x64)", tbl_cell)],
        [Paragraph("Diagramas editáveis", tbl_cell_bold), Paragraph("Inclusos no diretório de documentação do repositório", tbl_cell)],
        [Paragraph("Vídeo ou apresentação, se solicitado", tbl_cell_bold), Paragraph("Disponibilizado conforme cronograma da disciplina", tbl_cell)],
    ]
    t_link = Table(link_rows, colWidths=[170, 334])
    t_link.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0284c7')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 3.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3.5),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#f8fafc'), colors.white]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
    ]))
    story.append(t_link)
    story.append(Spacer(1, 6))

    # --- REFERÊNCIAS CONSULTADAS ---
    story.append(Bookmark("sec_ref", page_registry))
    story.append(Paragraph("REFERÊNCIAS CONSULTADAS", h1_style))
    ref_list = [
        "PRESSMAN, Roger S.; MAXIM, Bruce R. <i>Engenharia de Software: uma abordagem profissional</i>. 9. ed. Porto Alegre: AMGH, 2021.",
        "SOMMERVILLE, Ian. <i>Engenharia de Software</i>. 10. ed. São Paulo: Pearson Education do Brasil, 2019.",
        "PYTHON SOFTWARE FOUNDATION. <i>Python 3.11 Documentation</i>. Disponível em: &lt;https://docs.python.org/3.11/&gt;. Acesso em: 2026.",
        "THE QT COMPANY. <i>Qt for Python (PySide6) Documentation</i>. Disponível em: &lt;https://doc.qt.io/qtforpython/&gt;. Acesso em: 2026.",
        "SQLITE CONSORTIUM. <i>SQLite Documentation and SQL Reference</i>. Disponível em: &lt;https://www.sqlite.org/docs.html&gt;. Acesso em: 2026.",
    ]
    for r in ref_list:
        story.append(Paragraph(f"• {r}", bullet_style))

    return story


def create_pdf(filename="Documentacao_Orby_Projeto_Integrado.pdf"):
    temp_registry = {}
    temp_buf = io.BytesIO()
    doc_dummy = SimpleDocTemplate(
        temp_buf, pagesize=letter,
        leftMargin=54, rightMargin=54, topMargin=54, bottomMargin=54
    )
    dummy_story = build_story(temp_registry, is_dummy=True)
    doc_dummy.build(dummy_story, canvasmaker=NumberedCanvas)

    final_registry = dict(temp_registry)
    doc_final = SimpleDocTemplate(
        filename, pagesize=letter,
        leftMargin=54, rightMargin=54, topMargin=54, bottomMargin=54
    )
    final_story = build_story(final_registry, is_dummy=False)
    doc_final.build(final_story, canvasmaker=NumberedCanvas)
    print(f"PDF gerado com sucesso: {filename}")


if __name__ == '__main__':
    create_pdf('Documentacao_Orby_Projeto_Integrado.pdf')
    create_pdf('orby_projeto2_corrigido.pdf')

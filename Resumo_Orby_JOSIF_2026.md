# REVISÃO DE CÓDIGO COM LLMS EM UMA PLATAFORMA DE GERENCIAMENTO DE ORDENS DE SERVIÇO

---

## RESUMO

A manutenção de sistemas desktop de pequeno porte exige revisões periódicas para preservar legibilidade, correção e evolução segura do código. Este estudo analisou o emprego de um modelo de linguagem de larga escala como apoio à revisão supervisionada do Orby, aplicação Python para controle de ordens de serviço em assistências técnicas. Foram selecionados quatro módulos centrais — persistência, repositório, importação e interface — e submetidos a prompts estruturados que solicitaram análise de clareza, possíveis defeitos e oportunidades de refatoração. Das quatorze recomendações obtidas, cinco foram aceitas e implementadas, três adaptadas pela equipe e seis rejeitadas após verificação manual ou testes funcionais. A ferramenta acelerou a identificação de acoplamentos, inconsistências de validação e trechos de baixa legibilidade, mas também produziu sugestões incorretas sobre o ciclo de vida de conexões SQLite e sobre a lógica de duplicidade de clientes. Conclui-se que a LLM contribui como segunda fonte de análise quando combinada a testes manuais e decisão humana, sem substituir a compreensão do domínio da aplicação.

**Palavras-chave:** Revisão de código; Refatoração; Manutenibilidade; Avaliação humana.

---

## 1. INTRODUÇÃO

Os modelos de linguagem de larga escala vêm sendo incorporados a diferentes atividades da engenharia de software, incluindo análise, programação, testes, documentação e manutenção. Seu emprego pode apoiar a produção de artefatos, mas as respostas precisam ser examinadas pela equipe responsável pelo projeto (HOU et al., 2024). A revisão de código permanece central para garantir legibilidade, manutenibilidade e correção: revisores humanos avaliam não apenas a sintaxe, mas também aderência a regras de negócio, clareza de nomes, tratamento de erros e riscos de regressão. Nesse contexto, a IA generativa pode funcionar como segunda fonte de análise, ampliando a cobertura de leitura e sugerindo refatorações, desde que nenhuma recomendação seja aplicada sem compreensão, validação e teste pela equipe.

O Orby é uma aplicação desktop desenvolvida em Python com PySide6 e SQLite, voltada ao cadastro de clientes, equipamentos e ordens de serviço (OS), além de dashboard operacional e importação de clientes a partir de planilhas CSV ou XLSX. A arquitetura separa a camada de interface (`main_window.py`), acesso a dados (`repository.py`), esquema e migração do banco (`database.py`) e rotinas de importação (`importer.py`). Por tratar de fluxos críticos — exclusão condicional de clientes vinculados a OS, validação de status e valores, detecção de duplicidade na importação —, o código exige revisões cuidadosas antes de alterações estruturais.

O objetivo geral deste estudo foi analisar a contribuição de uma LLM para a revisão e o refinamento supervisionado do código da plataforma Orby.

---

## 2. FUNDAMENTAÇÃO TEÓRICA

A revisão de código consiste na inspeção sistemática de trechos produzidos por outros desenvolvedores, com foco em qualidade, conformidade e redução de defeitos antes da integração. Comentários de revisão eficazes apontam problemas concretos, justificam a preocupação e, quando possível, indicam caminhos de correção. A refatoração, por sua vez, busca melhorar a estrutura interna do software sem alterar o comportamento observável externamente, o que exige validação de comportamento após cada mudança aceita.

Estudos recentes investigam o uso de LLMs para gerar comentários automatizados e propostas de refinamento. LU et al. (2023) demonstram avanços na automação de revisão por meio de modelos ajustados com técnicas eficientes em parâmetros, enquanto GUO et al. (2024) avaliam empiricamente o potencial de modelos conversacionais na melhoria iterativa de código, destacando ganhos dependentes do contexto fornecido e da qualidade da avaliação posterior. HAIDER et al. (2024) reforçam que a utilidade das sugestões varia conforme o prompt, o domínio e a capacidade do revisor humano de filtrar respostas imprecisas.

A literatura sistemática de HOU et al. (2024) sintetiza aplicações de LLMs em engenharia de software e alerta para limitações recorrentes: alucinações, recomendações genéricas desconectadas do projeto e risco de introduzir regressões quando sugestões são aplicadas sem testes. Assim, a fundamentação deste trabalho assume a LLM como ferramenta auxiliar de leitura ampliada, e não como autoridade final sobre correção ou manutenibilidade.

---

## 3. MATERIAL E MÉTODOS

Trata-se de um estudo aplicado e descritivo, conduzido sobre trechos reais do código-fonte do Orby. A equipe selecionou quatro artefatos representativos do fluxo principal da aplicação: `database.py` (inicialização e migração do SQLite), `repository.py` (consultas, validações e regras de negócio), `importer.py` (leitura e validação de planilhas) e `main_window.py` (formulários, tabelas e ações da interface). As linguagens e tecnologias envolvidas foram Python 3.12, PySide6, SQLite, CSV e XLSX via openpyxl.

A revisão foi realizada no ambiente Cursor IDE, utilizando o assistente Composer (modelo de linguagem integrado à ferramenta, baseado na família GPT). Para cada módulo, aplicou-se um prompt padronizado:

> *"Analise o código Python abaixo do projeto Orby, plataforma desktop de ordens de serviço. Avalie legibilidade, organização, possíveis defeitos, acoplamento e oportunidades de refatoração. Indique riscos de regressão e proponha melhorias concretas, justificando cada ponto. Não assuma frameworks não presentes no trecho."*

Os critérios de qualidade adotados foram: (i) clareza e legibilidade; (ii) aderência às regras de negócio do Orby; (iii) consistência entre camadas (interface, repositório e banco); (iv) tratamento de erros e validações; (v) risco de regressão funcional. Cada recomendação recebeu classificação final em *aceita*, *modificada* ou *rejeitada*, conforme deliberação da equipe.

Antes e depois das alterações aceitas, executaram-se testes manuais funcionais: inicialização da aplicação; cadastro, edição e exclusão de clientes; tentativa de exclusão de cliente com OS vinculada; cadastro de equipamentos e abertura de OS; alteração de status até "Finalizada" com valor positivo; importação do arquivo `clientes_teste_importacao.csv` (dez linhas, incluindo duplicatas e campos vazios); verificação dos indicadores do dashboard. Não havia suíte automatizada de testes no repositório; essa ausência também foi registrada como achado da revisão. Os registros completos de prompt e resposta foram organizados em anexo digital interno à equipe para permitir reprodução do procedimento.

---

## 4. RESULTADOS E DISCUSSÕES

### 4.1 Síntese das recomendações

Foram registradas **14 recomendações** distribuídas pelos quatro módulos analisados. Ao final da avaliação humana: **5 aceitas**, **3 modificadas** e **6 rejeitadas**. A Tabela 1 resume a classificação por tema.

| Tema identificado | Aceitas | Modificadas | Rejeitadas |
|---|---:|---:|---:|
| Legibilidade e formatação (`main_window.py`) | 2 | 1 | 0 |
| Validação e regras de negócio | 1 | 1 | 2 |
| Arquitetura e acoplamento | 1 | 0 | 2 |
| Persistência e ciclo de vida de conexões | 0 | 0 | 1 |
| Testes automatizados | 1 | 1 | 1 |

### 4.2 Evidência: prompt e resposta (trecho representativo)

**Prompt enviado para `repository.py` (método `_validate_order` e `customer_duplicate`):**

> Analise o código Python abaixo do projeto Orby [...] Avalie legibilidade, organização, possíveis defeitos [...]

**Resposta resumida da LLM:**

> 1. `_validate_order` concentra regras importantes e está bem localizado; sugere-se mensagem específica quando `equipment_id` for nulo.  
> 2. Em `customer_duplicate`, o uso de `OR` entre nome e telefone pode sinalizar duplicidade quando apenas um dos campos coincide, gerando falsos positivos na importação.  
> 3. Recomenda-se extrair constantes de status finalizados para evitar comparações literais espalhadas.  
> 4. Sugere-se fechar explicitamente conexões SQLite após cada operação.

A equipe **aceitou** a melhoria de mensagem de validação, **modificou** a proposta sobre duplicidade (mantendo o `OR`, mas documentando a regra de negócio aceita pelo domínio) e **rejeitou** o fechamento agressivo de conexões após verificar que o padrão `with self.database.connect()` já delimita transações adequadamente para o escopo atual da aplicação.

### 4.3 Evidência: código antes e depois

**Antes** — validação genérica em `repository.py`:

```python
@staticmethod
def _validate_order(descricao: str, status: str, valor: float, equipment_id: int | None) -> None:
    if not descricao.strip():
        raise ValueError("A descrição do serviço é obrigatória.")
    if not equipment_id:
        raise ValueError("Selecione o equipamento da OS.")
    if status == "Finalizada" and valor <= 0:
        raise ValueError("Informe um valor maior que zero antes de finalizar a OS.")
```

**Depois** — versão validada pela equipe, com mensagens mais explícitas e verificação antecipada de equipamento ausente:

```python
@staticmethod
def _validate_order(descricao: str, status: str, valor: float, equipment_id: int | None) -> None:
    if not descricao.strip():
        raise ValueError("A descrição do serviço é obrigatória.")
    if equipment_id is None:
        raise ValueError("Selecione um equipamento cadastrado para a OS.")
    if status == "Finalizada" and valor <= 0:
        raise ValueError("Informe um valor maior que zero antes de finalizar a OS.")
```

**Antes** — trecho compactado em `main_window.py` (linha 255, parcial):

```python
filters = QHBoxLayout(); self.order_search = QLineEdit(...); self.order_search.textChanged.connect(...)
```

**Depois** — refatoração aceita para legibilidade:

```python
filters = QHBoxLayout()
self.order_search = QLineEdit(placeholderText="Buscar por OS, cliente ou descrição")
self.order_search.textChanged.connect(self.refresh_orders)
```

Testes manuais repetidos após essas alterações confirmaram preservação do comportamento: OS inválida sem equipamento continua bloqueada; filtros e listagens respondem como antes.

### 4.4 Defeitos apontados, testes e sugestões incorretas

Entre os problemas **corretamente identificados** pela LLM estavam: (a) excesso de instruções por linha na interface, dificultando revisão humana; (b) acoplamento de `OrderDialog.load_equipment` ao `parent().repository`, reduzindo reutilização; (c) ausência de testes automatizados; (d) validação tardia em formulários que dependem exclusivamente do repositório; (e) regra de duplicidade na importação que exige atenção do operador.

Entre as sugestões **incorretas ou inadequadas** estavam: (i) reescrever o padrão de acesso a dados com ORM externo, fora do escopo do projeto; (ii) unificar `selected_id` em métodos distintos sem ganho real, aumentando verbosidade; (iii) alterar a detecção de duplicidade para `AND` entre nome e telefone, o que permitiria registros redundantes no banco; (iv) fechar conexões SQLite manualmente em cada método, sem ganho perceptível no volume atual de operações.

Os testes com `clientes_teste_importacao.csv` confirmaram o comportamento esperado: quatro registros válidos, rejeição de duplicata "Ana Souza", linhas sem nome ou telefone marcadas como inválidas. Após refatorações de legibilidade, nenhuma regressão foi observada nos fluxos de cadastro e dashboard.

### 4.5 Discussão

A ferramenta facilitou a varredura inicial de aproximadamente 430 linhas úteis de código Python, produzindo lista estruturada de achados em poucos minutos. Por outro lado, parte das respostas assumiu práticas genéricas de projetos maiores, exigindo filtragem criteriosa. Decisões sensíveis — como a semântica de duplicidade na importação e o limite de refatoração arquitetural — permaneceram com a equipe. A principal limitação para generalização dos resultados é o tamanho reduzido da base analisada e a dependência de testes manuais, o que restringe a confiança estatística das conclusões.

---

## 5. CONCLUSÕES

Conclui-se que a revisão de código apoiada por LLM **auxiliou na identificação de problemas de legibilidade, validação e acoplamento** no Orby, acelerando a etapa inicial de inspeção quando combinada à avaliação humana. A limitação mais relevante observada foi a **proposição pontual de refatorações desalinhadas ao contexto** — especialmente em persistência e regras de negócio —, que poderiam introduzir regressões se aplicadas automaticamente. Os testes funcionais manuais e a decisão da equipe sobre cada recomendação impediram alterações inadequadas e confirmaram a preservação do comportamento do sistema nas mudanças aceitas.

---

## REFERÊNCIAS

GUO, Qi et al. Exploring the potential of ChatGPT in automated code refinement: an empirical study. In: IEEE/ACM INTERNATIONAL CONFERENCE ON SOFTWARE ENGINEERING, 46., 2024. p. 390-402. DOI: 10.1145/3597503.3623306. Disponível em: <https://doi.org/10.1145/3597503.3623306>. Acesso em: 19 ago. 2026.

HAIDER, Md. Asif et al. Prompting and fine-tuning large language models for automated code review comment generation. arXiv, 2024. DOI: 10.48550/arXiv.2411.10129. Disponível em: <https://arxiv.org/abs/2411.10129>. Acesso em: 19 ago. 2026.

HOU, Xinyi et al. Large language models for software engineering: a systematic literature review. ACM Transactions on Software Engineering and Methodology, 2024. DOI: 10.1145/3695988. Disponível em: <https://doi.org/10.1145/3695988>. Acesso em: 19 ago. 2026.

LU, Junyi; YU, Lei; LI, Xiaojia; YANG, Li; ZUO, Chun. LLaMA-Reviewer: advancing code review automation with large language models through parameter-efficient fine-tuning. In: IEEE INTERNATIONAL SYMPOSIUM ON SOFTWARE RELIABILITY ENGINEERING, 34., 2023. p. 647-658. DOI: 10.1109/ISSRE59848.2023.00026. Disponível em: <https://doi.org/10.1109/ISSRE59848.2023.00026>. Acesso em: 19 ago. 2026.

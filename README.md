# Orby — Gestão Operacional para Pequenas Empresas e Serviços

Sistema desktop intuitivo e de alta performance voltado para pequenas empresas, prestadores de serviços e assistências técnicas. O sistema conta com controle completo de clientes, equipamentos e ordens de serviço (OS), painel financeiro, emissão de comprovantes e relatórios em PDF/CSV, rotinas de backup/restauração, autenticação segura (`scrypt`) com controle de acesso baseado em perfis (RBAC), importação em lote e interface gráfica moderna no estilo Frutiger Aero.

---

## Funcionalidades

- **Autenticação Segura & Controle de Acesso (RBAC):**
  - Criptografia de senhas com `hashlib.scrypt` e salt criptográfico individual de 128 bits.
  - **Gestor:** Acesso irrestrito (dashboard, painel financeiro, clientes, equipamentos, OS, importação, backup e gestão de colaboradores/empresa).
  - **Técnico:** Acesso operacional focado em ordens de serviço, diagnósticos, laudos técnicos e equipamentos (com sigilo financeiro).
  - **Atendente:** Recepção, cadastro de clientes, entrada de equipamentos e abertura de OS (com diagnóstico técnico e valores financeiros protegidos).
- **Gestão de Ordens de Serviço (OS):**
  - Abertura, consulta, filtros combinados, alertas automáticos para OS paradas (> 5 dias), atualização de status com linha do tempo imutável de auditoria e histórico de manutenções anteriores por equipamento.
  - Discriminação de valores (Mão de Obra e Peças), forma de pagamento e emissão de **Comprovante de Entrada** e **Recibo / Laudo Técnico de Saída** em PDF.
- **Painel Financeiro e Fechamento de Caixa:**
  - Indicadores em tempo real (Faturamento Realizado, Receita Prevista, Ticket Médio e Mão de Obra), distribuição por forma de pagamento e exportação de relatórios gerenciais em **PDF** e **CSV (Excel)**.
- **Gestão de Clientes e Equipamentos:**
  - Cadastro detalhado com validação de CPF/CNPJ, telefone e e-mail, vínculo direto entre clientes e equipamentos e exclusão com integridade referencial protegida (`ON DELETE RESTRICT`).
- **Importação de Dados em Lote:**
  - Suporte a arquivos `.csv` (detecção automática de delimitador `;` ou `,`) e `.xlsx`.
  - Mapeamento dinâmico de colunas, detecção de duplicidades e pré-visualização antes da gravação.
- **Segurança de Dados e Backup:**
  - Backup manual compactado (`.zip` com manifesto SHA-256) ou `.db`, backup rápido em 1 clique, restauração validada com snapshot preventivo e backup automático ao fechar o sistema.
- **Design & Usabilidade:**
  - Interface responsiva com tema Claro e Escuro (Frutiger Aero Design System), ícones vetoriais SVG e inicialização rápida em até 3 segundos.

---

## Credenciais de Acesso (Ambiente de Demonstração)

Na primeira execução, o sistema inicializa automaticamente o banco de dados `orby.db` com três perfis pré-configurados:

| Perfil | Usuário | Senha | Permissões |
|---|---|---|---|
| **Gestor** | `admin` | `admin123` | Acesso completo a todas as funções, financeiro e configurações |
| **Técnico** | `tecnico` | `tec123` | Edição de OS, diagnósticos técnicos e equipamentos |
| **Atendente** | `atendente` | `atende123` | Cadastro de clientes, equipamentos e abertura de OS |

> **Modo Produção:** Por padrão, o Modo Produção Comercial vem **ativado**, ocultando botões de preenchimento rápido na tela de login. O Gestor pode alternar essa opção a qualquer momento em **Configurações → Usuários & Acessos**.

---

## Como Executar o Projeto

### Pré-requisitos
- **Python 3.11** ou superior
- Gerenciador de pacotes `pip`

### 1. Clonar o repositório
```bash
git clone https://github.com/Mat-Henrique-Santos/Orby.git
cd Orby
```

### 2. Criar e ativar o ambiente virtual (recomendado)

No Windows (PowerShell):
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

No Linux/macOS:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Instalar as dependências
```bash
pip install -r requirements.txt
```

### 4. Executar a aplicação
```bash
python main.py
```

> **Nota:** O banco de dados SQLite (`orby.db`) é criado e populado automaticamente na primeira execução dentro do diretório de dados do usuário (`%APPDATA%/Orby/orby.db` no Windows ou `~/.orby/orby.db` no Linux/macOS), sem poluir a pasta do projeto.
>
> **Usuários Windows:** O executável portátil compilado (`Orby.exe`, que dispensa instalação do Python) está disponível diretamente na raiz do repositório [Mat-Henrique-Santos/Orby](https://github.com/Mat-Henrique-Santos/Orby) e na seção de [Releases](https://github.com/Mat-Henrique-Santos/Orby/releases).

---

## Executando os Testes Automatizados

A suíte possui **48 testes unitários e de integração** cobrindo autenticação (`scrypt` e migração legada), controle RBAC, persistência SQLite, regras de negócio, geração de PDFs/CSVs, rotinas de backup/restauração e importação de planilhas. Você pode executá-los com o `unittest` padrão ou com o `pytest`:

**Via unittest nativo:**
```bash
python -m unittest discover -s tests -p "test_*.py" -v
```

**Via pytest:**
```bash
pip install pytest
python -m pytest
```

---

## Estrutura do Projeto

```text
├── orby/                         # Pacote principal da aplicação
│   ├── core/                     # Modelos de domínio, gerador PDF/CSV e motor de backup
│   ├── ui/                       # Design System Frutiger Aero, diálogos, temas e ícones SVG
│   ├── database.py               # Conexão SQLite, migrações e criptografia scrypt
│   ├── importer.py               # Mecanismo de importação e validação CSV/XLSX
│   ├── repository.py             # Camada de persistência, consultas analíticas e RBAC
│   └── main_window.py            # Janela principal e fluxos operacionais do sistema
├── tests/                        # Suíte com 48 testes automatizados
├── clientes_teste_importacao.csv # Planilha de exemplo para teste de importação
├── main.py                       # Ponto de entrada da aplicação
├── Orby.exe                      # Executável portátil compilado para Windows
├── Orby.spec                     # Especificação para empacotamento com PyInstaller
├── requirements.txt              # Dependências do projeto (PySide6, openpyxl, reportlab)
└── README.md                     # Documentação técnica do repositório
```

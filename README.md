# Orby — Gestão Operacional para Pequenas Empresas e Serviços

Sistema desktop intuitivo e de alta performance voltado para pequenas empresas, prestadores de serviços e assistências técnicas. O sistema conta com controle completo de clientes, equipamentos e ordens de serviço (OS), além de autenticação com controle de acesso baseado em perfis (RBAC), importação em lote e interface gráfica moderna no estilo Frutiger Aero.

---

## 🚀 Funcionalidades

- **Autenticação & Controle de Acesso (RBAC):**
  - **Gestor:** Acesso irrestrito (dashboard financeiro, clientes, equipamentos, OS e importação).
  - **Técnico:** Acesso operacional focado em ordens de serviço, andamentos, laudos e equipamentos.
  - **Atendente:** Recepção e cadastro de clientes e entrada de equipamentos e OS (com diagnóstico técnico protegido).
- **Gestão de Ordens de Serviço (OS):**
  - Abertura, consulta, atualização de status com linha do tempo de histórico e encerramento.
  - Registro de diagnóstico técnico e valor final.
- **Gestão de Clientes e Equipamentos:**
  - Cadastro detalhado e vínculo direto entre clientes e equipamentos/máquinas.
  - Exclusão com integridade referencial protegida.
- **Importação de Dados em Lote:**
  - Suporte a arquivos `.csv` e `.xlsx`.
  - Mapeamento dinâmico de colunas, detecção de duplicidades e relatório de importação.
- **Dashboard e Métricas:**
  - Indicadores operacionais e controle de faturamento em tempo real.
- **Design & Usabilidade:**
  - Interface com tema Claro e Escuro (Frutiger Aero).
  - Ícones vetoriais modernos e inicialização em menos de 3 segundos.

---

## 👥 Credenciais de Acesso (Ambiente de Testes)

O sistema inicializa automaticamente o banco de dados `orby.db` com três perfis pré-configurados para validação:

| Perfil | Usuário | Senha | Permissões |
|---|---|---|---|
| **Gestor** | `admin` | `admin123` | Acesso completo a todas as funções e métricas |
| **Técnico** | `tecnico` | `tec123` | Edição de OS, diagnósticos e equipamentos |
| **Atendente** | `atendente` | `atende123` | Cadastro de clientes, equipamentos e abertura de OS |

---

## 💻 Como Executar o Projeto

### Pré-requisitos
- **Python 3.11** ou superior
- Gerenciador de pacotes `pip`

### 1. Clonar o repositório
```bash
git clone https://github.com/SEU_USUARIO/orby.git
cd orby
```

### 2. Criar e ativar o ambiente virtual (recomendado)

No Windows (PowerShell):
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

No Linux/macOS:
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar as dependências
```bash
pip install -r requirements.txt
```

### 4. Executar a aplicação
```bash
python main.py
```

> **Nota:** O banco de dados SQLite (`orby.db`) é criado e populado automaticamente na primeira execução com os usuários e estrutura inicial.

---

## 🧪 Executando os Testes Unitários

Para rodar a suíte completa de testes automatizados:

```bash
python -m unittest discover tests
```

---

## 📦 Estrutura do Projeto

```text
├── orby/                    # Módulo principal da aplicação
│   ├── core/                # Modelos de domínio e regras de negócio
│   ├── ui/                  # Componentes de interface gráfica, telas e ícones
│   ├── database.py          # Conexão e migrações SQLite
│   ├── importer.py          # Mecanismo de importação CSV/XLSX
│   ├── repository.py        # Camada de persistência e consultas
│   └── main_window.py       # Janela principal do sistema
├── tests/                   # Testes unitários automatizados
├── clientes_teste_importacao.csv # Dados para teste de importação
├── main.py                  # Ponto de entrada do sistema
├── Orby.spec                # Especificação para empacotamento com PyInstaller
├── requirements.txt         # Dependências do projeto
└── README.md                # Documentação técnica do projeto
```

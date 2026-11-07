# Credenciais e Perfis de Acesso Padrão — Orby 2.0

Na primeira inicialização do sistema (quando o banco de dados local `orby.db` é criado), o **Orby** cadastra automaticamente três contas padrão para avaliação e operação inicial, cada uma vinculada a um perfil de controle de acesso baseado em papéis (**RBAC — Role-Based Access Control**).

---

## 1. Contas Padrão para Login

| Perfil (Papel) | Nome do Usuário | Login (Usuário) | Senha |
| :--- | :--- | :--- | :--- |
| **Gestor** | Administrador | `admin` | `admin123` |
| **Técnico** | Carlos Técnico | `tecnico` | `tec123` |
| **Atendente** | Mariana Atendente | `atendente` | `atende123` |

> **Observação sobre Segurança:** Todas as senhas são armazenadas no banco SQLite (`orby.db`) utilizando derivação criptográfica `scrypt` com *salt* aleatório de 16 bytes por usuário e verificação em tempo constante (`hmac.compare_digest`).

---

## 2. Matriz de Permissões por Perfil (RBAC)

| Funcionalidade / Módulo | Gestor (`admin`) | Técnico (`tecnico`) | Atendente (`atendente`) |
| :--- | :---: | :---: | :---: |
| **Dashboard Operacional (Contadores de OS)** | Completo | Completo | Completo |
| **Visualização de Faturamento e Valores (R$)** | Liberado | Oculto (`Restrito`) | Oculto (`Restrito`) |
| **Painel Financeiro e Fechamento de Caixa** | Liberado (PDF / CSV) | Bloqueado | Bloqueado |
| **Cadastro e Edição de Clientes** | Liberado | Somente Consulta | Liberado |
| **Exclusão de Clientes** | Liberado | Bloqueado | Bloqueado |
| **Cadastro e Edição de Equipamentos** | Liberado | Liberado | Liberado |
| **Exclusão de Equipamentos** | Liberado | Bloqueado | Bloqueado |
| **Abertura e Edição de Ordens de Serviço (OS)** | Liberado | Liberado (Laudo e Status) | Liberado (Triagem e Recepção) |
| **Exclusão de Ordens de Serviço (OS)** | Liberado | Bloqueado | Bloqueado |
| **Emissão de Comprovante de Entrada e Recibo/Laudo (PDF)** | Liberado | Liberado | Liberado |
| **Configurações, Backup/Restauração e Gestão de Usuários** | Liberado | Bloqueado | Bloqueado |

---

## 3. Gerenciamento de Contas e Modo Demonstração

- **Criação, Edição e Desativação de Contas:** Ao entrar como **Gestor** (`admin` / `admin123`), acesse **Configurações -> Usuários & Acessos** para cadastrar novos operadores, redefinir senhas, alterar perfis ou ativar/desativar contas existentes.
- **Modo Produção vs. Modo Demonstração:** Por padrão, o sistema inicia com o **Modo Produção ativo** (sem exibir botões de preenchimento rápido na tela de login). Caso deseje habilitar os botões de login rápido de demonstração na tela inicial, acesse **Configurações -> Usuários & Acessos** com o perfil **Gestor** e desmarque a opção de Modo Produção.

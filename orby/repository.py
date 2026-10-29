from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
from .core.models import Cliente, Equipamento, OrdemServico, StatusOS
from .database import Database


class PermissionDeniedError(Exception):
    """Exceção levantada quando uma operação viola as regras de RBAC."""
    pass


class Repository:
    def __init__(self, database: Database, current_user: dict | None = None) -> None:
        self.database = database
        self.current_user = current_user

    def set_current_user(self, current_user: dict | None) -> None:
        self.current_user = current_user

    @property
    def current_role(self) -> str:
        if not self.current_user:
            return "Gestor"  # Default permissivo para testes sem usuário explícito
        return self.current_user.get("perfil", "Gestor")

    def _require_role(self, *allowed_roles: str, action: str = "esta operação") -> None:
        if self.current_role not in allowed_roles:
            raise PermissionDeniedError(
                f"Acesso negado: Perfil '{self.current_role}' não tem permissão para {action}."
            )

    # --- CLIENTES ---

    def customers(self, term: str = "") -> list[dict]:
        with self.database.connect() as db:
            rows = db.execute(
                """SELECT * FROM clientes
                   WHERE nome LIKE ? OR telefone LIKE ? OR (email IS NOT NULL AND email LIKE ?) OR (documento IS NOT NULL AND documento LIKE ?)
                   ORDER BY nome COLLATE NOCASE ASC""",
                (f"%{term}%", f"%{term}%", f"%{term}%", f"%{term}%"),
            ).fetchall()
        return [dict(row) for row in rows]

    def customer(self, customer_id: int) -> dict | None:
        with self.database.connect() as db:
            row = db.execute("SELECT * FROM clientes WHERE id = ?", (customer_id,)).fetchone()
        return dict(row) if row else None

    def add_customer(
        self,
        nome: str,
        telefone: str,
        email: str = "",
        documento: str = "",
        endereco: str = "",
    ) -> int:
        cliente = Cliente(
            id=None,
            nome=nome.strip(),
            telefone=telefone.strip(),
            email=email.strip() or None,
            documento=documento.strip() or None,
            endereco=endereco.strip() or None,
        )
        cliente.validate()
        with self.database.connect() as db:
            cursor = db.execute(
                "INSERT INTO clientes(nome, telefone, email, documento, endereco) VALUES (?, ?, ?, ?, ?)",
                (cliente.nome, cliente.telefone, cliente.email, cliente.documento, cliente.endereco),
            )
        return cursor.lastrowid

    def update_customer(
        self,
        customer_id: int,
        nome: str,
        telefone: str,
        email: str = "",
        documento: str = "",
        endereco: str = "",
    ) -> None:
        cliente = Cliente(
            id=customer_id,
            nome=nome.strip(),
            telefone=telefone.strip(),
            email=email.strip() or None,
            documento=documento.strip() or None,
            endereco=endereco.strip() or None,
        )
        cliente.validate()
        with self.database.connect() as db:
            cursor = db.execute(
                "UPDATE clientes SET nome=?, telefone=?, email=?, documento=?, endereco=? WHERE id=?",
                (cliente.nome, cliente.telefone, cliente.email, cliente.documento, cliente.endereco, customer_id),
            )
            if cursor.rowcount == 0:
                raise ValueError(f"Cliente #{customer_id} não encontrado para atualização.")

    def delete_customer(self, customer_id: int) -> tuple[bool, str]:
        self._require_role("Gestor", action="excluir clientes")
        with self.database.connect() as db:
            count_orders = db.execute("SELECT COUNT(*) FROM ordens_servico WHERE cliente_id=?", (customer_id,)).fetchone()[0]
            if count_orders:
                return False, "Este cliente possui Ordens de Serviço vinculadas e não pode ser excluído."
            count_eq = db.execute("SELECT COUNT(*) FROM equipamentos WHERE cliente_id=?", (customer_id,)).fetchone()[0]
            if count_eq:
                return False, "Este cliente possui Equipamentos vinculados e não pode ser excluído."
            db.execute("DELETE FROM clientes WHERE id=?", (customer_id,))
        return True, "Cliente excluído com sucesso."

    def customer_duplicate(self, nome: str, telefone: str, documento: str = "") -> bool:
        with self.database.connect() as db:
            if documento and documento.strip():
                row = db.execute(
                    "SELECT 1 FROM clientes WHERE documento=? OR (lower(nome)=lower(?) AND telefone=?) LIMIT 1",
                    (documento.strip(), nome.strip(), telefone.strip()),
                ).fetchone()
            else:
                row = db.execute(
                    "SELECT 1 FROM clientes WHERE lower(nome)=lower(?) AND telefone=? LIMIT 1",
                    (nome.strip(), telefone.strip()),
                ).fetchone()
            return bool(row)

    def import_customers(self, rows: Iterable[dict]) -> int:
        values = [
            (
                r["nome"].strip(),
                r["telefone"].strip(),
                r.get("email", "").strip() or None,
                r.get("documento", "").strip() or None,
                r.get("endereco", "").strip() or None,
            )
            for r in rows
        ]
        with self.database.connect() as db:
            db.executemany(
                "INSERT INTO clientes(nome, telefone, email, documento, endereco) VALUES (?, ?, ?, ?, ?)",
                values,
            )
        return len(values)

    # --- EQUIPAMENTOS ---

    def equipment(self, customer_id: int | None = None, term: str = "") -> list[dict]:
        sql = """SELECT e.*, c.nome AS cliente_nome FROM equipamentos e
                 JOIN clientes c ON c.id=e.cliente_id"""
        conditions = []
        params = []
        if customer_id:
            conditions.append("e.cliente_id = ?")
            params.append(customer_id)
        if term:
            t = f"%{term}%"
            conditions.append("(c.nome LIKE ? OR e.tipo LIKE ? OR (e.marca IS NOT NULL AND e.marca LIKE ?) OR (e.modelo IS NOT NULL AND e.modelo LIKE ?) OR (e.numero_serie IS NOT NULL AND e.numero_serie LIKE ?))")
            params.extend([t, t, t, t, t])
        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
        sql += " ORDER BY c.nome COLLATE NOCASE, e.tipo, e.marca, e.modelo"
        with self.database.connect() as db:
            rows = db.execute(sql, params).fetchall()
        return [dict(row) for row in rows]

    def single_equipment(self, equipment_id: int) -> dict | None:
        with self.database.connect() as db:
            row = db.execute(
                """SELECT e.*, c.nome AS cliente_nome FROM equipamentos e
                   JOIN clientes c ON c.id=e.cliente_id
                   WHERE e.id = ?""",
                (equipment_id,),
            ).fetchone()
        return dict(row) if row else None

    def update_equipment(
        self,
        equipment_id: int,
        cliente_id: int,
        tipo: str,
        marca: str = "",
        modelo: str = "",
        numero_serie: str = "",
        acessorios: str = "",
        condicao: str = "",
        observacoes: str = "",
    ) -> None:
        eq = Equipamento(
            id=equipment_id,
            cliente_id=cliente_id,
            tipo=tipo.strip(),
            marca=marca.strip() or None,
            modelo=modelo.strip() or None,
            numero_serie=numero_serie.strip() or None,
            acessorios=acessorios.strip() or None,
            condicao_entrada=condicao.strip() or None,
            observacoes=observacoes.strip() or None,
        )
        eq.validate()
        with self.database.connect() as db:
            cursor = db.execute(
                """UPDATE equipamentos
                   SET cliente_id=?, tipo=?, marca=?, modelo=?, numero_serie=?, acessorios=?, condicao_entrada=?, observacoes=?
                   WHERE id=?""",
                (eq.cliente_id, eq.tipo, eq.marca, eq.modelo, eq.numero_serie, eq.acessorios, eq.condicao_entrada, eq.observacoes, equipment_id),
            )
            if cursor.rowcount == 0:
                raise ValueError(f"Equipamento #{equipment_id} não encontrado para atualização.")

    def add_equipment(
        self,
        cliente_id: int,
        tipo: str,
        marca: str = "",
        modelo: str = "",
        numero_serie: str = "",
        acessorios: str = "",
        condicao: str = "",
        observacoes: str = "",
    ) -> int:
        eq = Equipamento(
            id=None,
            cliente_id=cliente_id,
            tipo=tipo.strip(),
            marca=marca.strip() or None,
            modelo=modelo.strip() or None,
            numero_serie=numero_serie.strip() or None,
            acessorios=acessorios.strip() or None,
            condicao_entrada=condicao.strip() or None,
            observacoes=observacoes.strip() or None,
        )
        eq.validate()
        with self.database.connect() as db:
            cursor = db.execute(
                """INSERT INTO equipamentos(cliente_id, tipo, marca, modelo, numero_serie, acessorios, condicao_entrada, observacoes)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (eq.cliente_id, eq.tipo, eq.marca, eq.modelo, eq.numero_serie, eq.acessorios, eq.condicao_entrada, eq.observacoes),
            )
        return cursor.lastrowid

    def delete_equipment(self, equipment_id: int) -> tuple[bool, str]:
        self._require_role("Gestor", action="excluir equipamentos")
        with self.database.connect() as db:
            count = db.execute(
                "SELECT COUNT(*) FROM ordens_servico WHERE equipamento_id=?",
                (equipment_id,),
            ).fetchone()[0]
            if count > 0:
                return False, "Este equipamento possui Ordens de Serviço vinculadas e não pode ser excluído."
            db.execute("DELETE FROM equipamentos WHERE id=?", (equipment_id,))
        return True, "Equipamento excluído com sucesso."

    # --- ORDENS DE SERVIÇO ---

    def orders(self, term: str = "", status: str = "") -> list[dict]:
        sql = """SELECT o.*, c.nome AS cliente_nome,
                        COALESCE(e.tipo || ' ' || COALESCE(e.marca, '') || ' ' || COALESCE(e.modelo, ''), 'Não informado') AS equipamento_nome
                 FROM ordens_servico o
                 JOIN clientes c ON c.id=o.cliente_id
                 LEFT JOIN equipamentos e ON e.id=o.equipamento_id
                 WHERE (c.nome LIKE ? OR o.descricao LIKE ? OR CAST(o.id AS TEXT) LIKE ? OR (e.modelo IS NOT NULL AND e.modelo LIKE ?))"""
        params: list[str] = [f"%{term}%", f"%{term}%", f"%{term}%", f"%{term}%"]
        if status:
            sql += " AND o.status=?"
            params.append(status)
        sql += " ORDER BY o.id DESC"
        with self.database.connect() as db:
            rows = db.execute(sql, params).fetchall()
        return [dict(row) for row in rows]

    def order(self, order_id: int) -> dict | None:
        sql = """SELECT o.*, c.nome AS cliente_nome,
                        COALESCE(e.tipo || ' ' || COALESCE(e.marca, '') || ' ' || COALESCE(e.modelo, ''), 'Não informado') AS equipamento_nome
                 FROM ordens_servico o
                 JOIN clientes c ON c.id=o.cliente_id
                 LEFT JOIN equipamentos e ON e.id=o.equipamento_id
                 WHERE o.id = ?"""
        with self.database.connect() as db:
            row = db.execute(sql, (order_id,)).fetchone()
        return dict(row) if row else None

    def order_history(self, order_id: int) -> list[dict]:
        with self.database.connect() as db:
            rows = db.execute(
                "SELECT * FROM historico_os WHERE ordem_id=? ORDER BY id ASC",
                (order_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def add_order(
        self,
        cliente_id: int,
        equipamento_id: int,
        descricao: str,
        status: str,
        valor: float = 0.0,
        valor_servico: float = 0.0,
        valor_pecas: float = 0.0,
        forma_pagamento: str | None = None,
        observacoes: str = "",
        diagnostico: str = "",
        tecnico: str = "",
    ) -> int:
        os_obj = OrdemServico(
            id=None,
            cliente_id=cliente_id,
            equipamento_id=equipamento_id,
            descricao=descricao.strip(),
            status=status,
            valor=valor,
            valor_servico=valor_servico,
            valor_pecas=valor_pecas,
            forma_pagamento=forma_pagamento.strip() if forma_pagamento else None,
            diagnostico=diagnostico.strip() or None,
            tecnico=tecnico.strip() or None,
            observacoes=observacoes.strip() or None,
        )
        os_obj.validate()

        now_iso = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        finalizacao = now_iso if os_obj.status == StatusOS.FINALIZADA.value else None

        with self.database.connect() as db:
            cursor = db.execute(
                """INSERT INTO ordens_servico(
                       cliente_id, equipamento_id, descricao, diagnostico, tecnico,
                       status, valor, valor_servico, valor_pecas, forma_pagamento,
                       data_finalizacao, observacoes
                   ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    os_obj.cliente_id,
                    os_obj.equipamento_id,
                    os_obj.descricao,
                    os_obj.diagnostico,
                    os_obj.tecnico,
                    os_obj.status,
                    os_obj.valor,
                    os_obj.valor_servico,
                    os_obj.valor_pecas,
                    os_obj.forma_pagamento,
                    finalizacao,
                    os_obj.observacoes,
                ),
            )
            order_id = cursor.lastrowid
            db.execute(
                "INSERT INTO historico_os(ordem_id, status_novo, observacao) VALUES (?, ?, ?)",
                (order_id, os_obj.status, "Ordem de Serviço criada no balcão"),
            )
        return order_id

    def update_order(
        self,
        order_id: int,
        cliente_id: int,
        equipamento_id: int,
        descricao: str,
        status: str,
        valor: float = 0.0,
        valor_servico: float = 0.0,
        valor_pecas: float = 0.0,
        forma_pagamento: str | None = None,
        observacoes: str = "",
        diagnostico: str = "",
        tecnico: str = "",
    ) -> None:
        os_obj = OrdemServico(
            id=order_id,
            cliente_id=cliente_id,
            equipamento_id=equipamento_id,
            descricao=descricao.strip(),
            status=status,
            valor=valor,
            valor_servico=valor_servico,
            valor_pecas=valor_pecas,
            forma_pagamento=forma_pagamento.strip() if forma_pagamento else None,
            diagnostico=diagnostico.strip() or None,
            tecnico=tecnico.strip() or None,
            observacoes=observacoes.strip() or None,
        )
        os_obj.validate()

        with self.database.connect() as db:
            prev_row = db.execute("SELECT * FROM ordens_servico WHERE id=?", (order_id,)).fetchone()
            if not prev_row:
                raise ValueError(f"Ordem de Serviço #{order_id} não encontrada.")
            previous_status = prev_row["status"]

            # Regras RBAC para Atendente: não pode finalizar OS nem alterar valores financeiros
            if self.current_role == "Atendente":
                if status == StatusOS.FINALIZADA.value and previous_status != StatusOS.FINALIZADA.value:
                    raise PermissionDeniedError("Acesso negado: Perfil 'Atendente' não tem permissão para finalizar Ordens de Serviço.")
                if abs(float(prev_row["valor"] or 0.0) - float(valor)) > 0.001 or \
                   abs(float(prev_row["valor_servico"] or 0.0) - float(valor_servico)) > 0.001 or \
                   abs(float(prev_row["valor_pecas"] or 0.0) - float(valor_pecas)) > 0.001:
                    raise PermissionDeniedError("Acesso negado: Perfil 'Atendente' não tem permissão para alterar valores de Ordens de Serviço.")

            now_iso = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            data_fim = prev_row["data_finalizacao"]
            if status == StatusOS.FINALIZADA.value and not data_fim:
                data_fim = now_iso
            elif status != StatusOS.FINALIZADA.value:
                data_fim = None

            db.execute(
                """UPDATE ordens_servico
                   SET cliente_id=?, equipamento_id=?, descricao=?, diagnostico=?, tecnico=?,
                       status=?, valor=?, valor_servico=?, valor_pecas=?, forma_pagamento=?,
                       data_finalizacao=?, observacoes=?
                   WHERE id=?""",
                (
                    os_obj.cliente_id,
                    os_obj.equipamento_id,
                    os_obj.descricao,
                    os_obj.diagnostico,
                    os_obj.tecnico,
                    os_obj.status,
                    os_obj.valor,
                    os_obj.valor_servico,
                    os_obj.valor_pecas,
                    os_obj.forma_pagamento,
                    data_fim,
                    os_obj.observacoes,
                    order_id,
                ),
            )

            if previous_status != status:
                db.execute(
                    "INSERT INTO historico_os(ordem_id, status_anterior, status_novo, observacao) VALUES (?, ?, ?, ?)",
                    (order_id, previous_status, status, f"Status alterado de '{previous_status}' para '{status}'"),
                )

    def delete_order(self, order_id: int) -> None:
        self._require_role("Gestor", action="excluir ordens de serviço")
        with self.database.connect() as db:
            db.execute("DELETE FROM ordens_servico WHERE id=?", (order_id,))

    # --- DASHBOARD & FINANÇAS ---

    def dashboard(self) -> dict:
        with self.database.connect() as db:
            row = db.execute(
                """SELECT
                    COUNT(*) as total_os,
                    SUM(CASE WHEN status NOT IN ('Finalizada', 'Cancelada') THEN 1 ELSE 0 END) as abertas,
                    SUM(CASE WHEN status='Em Reparo' THEN 1 ELSE 0 END) as em_reparo,
                    SUM(CASE WHEN status='Aguardando Aprovação' THEN 1 ELSE 0 END) as aguardando_aprovacao,
                    SUM(CASE WHEN status='Aguardando Retirada' THEN 1 ELSE 0 END) as aguardando_retirada,
                    SUM(CASE WHEN status='Finalizada' THEN 1 ELSE 0 END) as finalizadas,
                    COALESCE(SUM(CASE WHEN status='Finalizada' THEN valor ELSE 0 END), 0) as faturamento
                   FROM ordens_servico"""
            ).fetchone()
        return dict(row) if row else {}

    def financial_dashboard(self, period: str = "all") -> dict:
        where_clause = "WHERE status = 'Finalizada'"
        if period == "today":
            where_clause += " AND date(COALESCE(data_finalizacao, data_abertura)) = date('now', 'localtime')"
        elif period == "7days":
            where_clause += " AND date(COALESCE(data_finalizacao, data_abertura)) >= date('now', '-7 days', 'localtime')"
        elif period == "month":
            where_clause += " AND strftime('%Y-%m', COALESCE(data_finalizacao, data_abertura)) = strftime('%Y-%m', 'now', 'localtime')"

        with self.database.connect() as db:
            # Resumo de Faturamento Realizado
            resumo = db.execute(
                f"""SELECT
                        COUNT(*) as os_finalizadas,
                        COALESCE(SUM(valor), 0) as faturamento_realizado,
                        COALESCE(SUM(valor_servico), 0) as total_servicos,
                        COALESCE(SUM(valor_pecas), 0) as total_pecas
                    FROM ordens_servico {where_clause}"""
            ).fetchone()

            # Previsão a receber (todas as OS abertas/em andamento não finalizadas nem canceladas)
            prev_row = db.execute(
                """SELECT COALESCE(SUM(valor), 0) as receita_prevista
                   FROM ordens_servico
                   WHERE status NOT IN ('Finalizada', 'Cancelada')"""
            ).fetchone()

            # Distribuição por Forma de Pagamento
            formas = db.execute(
                f"""SELECT COALESCE(forma_pagamento, 'Não Definido') as forma, COALESCE(SUM(valor), 0) as total, COUNT(*) as qtd
                    FROM ordens_servico {where_clause}
                    GROUP BY forma_pagamento
                    ORDER BY total DESC"""
            ).fetchall()

            # Extrato das últimas transações finalizadas
            extrato_rows = db.execute(
                f"""SELECT o.id, c.nome as cliente_nome,
                           COALESCE(e.tipo || ' ' || COALESCE(e.marca, '') || ' ' || COALESCE(e.modelo, ''), 'Não informado') AS equipamento_nome,
                           o.valor, o.valor_servico, o.valor_pecas, o.forma_pagamento,
                           COALESCE(o.data_finalizacao, o.data_abertura) as data_conclusao
                    FROM ordens_servico o
                    JOIN clientes c ON c.id=o.cliente_id
                    LEFT JOIN equipamentos e ON e.id=o.equipamento_id
                    {where_clause}
                    ORDER BY data_conclusao DESC LIMIT 50"""
            ).fetchall()

            fat = resumo["faturamento_realizado"] if resumo else 0.0
            qtd = resumo["os_finalizadas"] if resumo else 0
            ticket = (fat / qtd) if qtd > 0 else 0.0

            return {
                "faturamento_realizado": fat,
                "receita_prevista": prev_row["receita_prevista"] if prev_row else 0.0,
                "total_servicos": resumo["total_servicos"] if resumo else 0.0,
                "total_pecas": resumo["total_pecas"] if resumo else 0.0,
                "os_finalizadas": qtd,
                "ticket_medio": ticket,
                "formas_pagamento": [dict(f) for f in formas],
                "extrato": [dict(e) for e in extrato_rows],
            }

    # ==========================================
    # GESTÃO DE USUÁRIOS E AUTENTICAÇÃO
    # ==========================================
    def authenticate(self, login: str, password: str) -> dict | None:
        from .database import verify_password, hash_password, is_legacy_hash
        user_login = login.strip()
        if not user_login or not password:
            return None

        with self.database.connect() as db:
            row = db.execute(
                """SELECT id, nome, login, senha_hash, perfil, ativo, criado_em 
                   FROM usuarios 
                   WHERE login = ? COLLATE NOCASE""",
                (user_login,),
            ).fetchone()

            if not row:
                return None

            if not row["ativo"]:
                return None  # Usuário inativo/desativado não pode acessar

            if not verify_password(password, row["senha_hash"]):
                return None

            # Migração automática e transparente de SHA-256 legado para scrypt moderno
            if is_legacy_hash(row["senha_hash"]):
                new_hash = hash_password(password)
                db.execute("UPDATE usuarios SET senha_hash = ? WHERE id = ?", (new_hash, row["id"]))

            return {
                "id": row["id"],
                "nome": row["nome"],
                "login": row["login"],
                "perfil": row["perfil"],
                "ativo": row["ativo"],
                "criado_em": row["criado_em"],
            }

    def users(self) -> list[dict]:
        with self.database.connect() as db:
            rows = db.execute(
                """SELECT id, nome, login, perfil, ativo, criado_em 
                   FROM usuarios 
                   ORDER BY ativo DESC, nome COLLATE NOCASE ASC"""
            ).fetchall()
        return [dict(r) for r in rows]

    def add_user(self, nome: str, login: str, password: str, perfil: str) -> int:
        from .database import hash_password
        self._require_role("Gestor", action="cadastrar novos usuários")
        clean_nome = nome.strip()
        clean_login = login.strip()

        if not clean_nome:
            raise ValueError("O nome completo do usuário é obrigatório.")
        if not clean_login:
            raise ValueError("O login de acesso é obrigatório.")
        if not password or len(password) < 4:
            raise ValueError("A senha deve conter no mínimo 4 caracteres.")
        if perfil not in ("Gestor", "Técnico", "Atendente"):
            raise ValueError(f"Perfil '{perfil}' inválido.")

        senha_hash = hash_password(password)
        with self.database.connect() as db:
            existing = db.execute(
                "SELECT id FROM usuarios WHERE login = ? COLLATE NOCASE", (clean_login,)
            ).fetchone()
            if existing:
                raise ValueError(f"Já existe um usuário cadastrado com o login '{clean_login}'.")

            cursor = db.execute(
                "INSERT INTO usuarios (nome, login, senha_hash, perfil, ativo) VALUES (?, ?, ?, ?, 1)",
                (clean_nome, clean_login, senha_hash, perfil),
            )
            return int(cursor.lastrowid)

    def update_user(self, user_id: int, nome: str, perfil: str, login: str | None = None) -> None:
        self._require_role("Gestor", action="editar dados de usuários")
        clean_nome = nome.strip()
        if not clean_nome:
            raise ValueError("O nome completo é obrigatório.")
        if perfil not in ("Gestor", "Técnico", "Atendente"):
            raise ValueError(f"Perfil '{perfil}' inválido.")

        with self.database.connect() as db:
            user = db.execute("SELECT id, login, perfil, ativo FROM usuarios WHERE id = ?", (user_id,)).fetchone()
            if not user:
                raise ValueError(f"Usuário #{user_id} não encontrado.")

            # Proteção: Não permitir rebaixar perfil do último Gestor ativo
            if user["perfil"] == "Gestor" and perfil != "Gestor":
                other_gestores = db.execute(
                    "SELECT COUNT(*) AS total FROM usuarios WHERE perfil = 'Gestor' AND ativo = 1 AND id != ?",
                    (user_id,),
                ).fetchone()["total"]
                if other_gestores == 0:
                    raise ValueError("Não é permitido alterar o perfil do único Gestor ativo no sistema.")

            clean_login = login.strip() if login else user["login"]
            if not clean_login:
                raise ValueError("O login de acesso não pode ser vazio.")

            dup = db.execute(
                "SELECT id FROM usuarios WHERE login = ? COLLATE NOCASE AND id != ?",
                (clean_login, user_id),
            ).fetchone()
            if dup:
                raise ValueError(f"O login '{clean_login}' já está em uso por outro usuário.")

            db.execute(
                "UPDATE usuarios SET nome = ?, login = ?, perfil = ? WHERE id = ?",
                (clean_nome, clean_login, perfil, user_id),
            )

    def change_password(self, user_id: int, new_password: str) -> None:
        if self.current_role != "Gestor" and (not self.current_user or self.current_user.get("id") != user_id):
            self._require_role("Gestor", action="alterar a senha deste usuário")

        if not new_password or len(new_password) < 4:
            raise ValueError("A nova senha deve ter no mínimo 4 caracteres.")

        from .database import hash_password
        senha_hash = hash_password(new_password)
        with self.database.connect() as db:
            cursor = db.execute(
                "UPDATE usuarios SET senha_hash = ? WHERE id = ?",
                (senha_hash, user_id),
            )
            if cursor.rowcount == 0:
                raise ValueError(f"Usuário #{user_id} não encontrado.")

    def toggle_user_status(self, user_id: int, ativo: bool) -> None:
        self._require_role("Gestor", action="alterar status de usuário")
        with self.database.connect() as db:
            user = db.execute("SELECT id, login, perfil, ativo FROM usuarios WHERE id = ?", (user_id,)).fetchone()
            if not user:
                raise ValueError(f"Usuário #{user_id} não encontrado.")

            # Proteção: Impedir desativar o usuário atualmente conectado
            if not ativo and self.current_user and self.current_user.get("id") == user_id:
                raise ValueError("Você não pode desativar o seu próprio usuário logado.")

            # Proteção: Impedir desativar o último Gestor ativo
            if not ativo and user["perfil"] == "Gestor":
                other_gestores = db.execute(
                    "SELECT COUNT(*) AS total FROM usuarios WHERE perfil = 'Gestor' AND ativo = 1 AND id != ?",
                    (user_id,),
                ).fetchone()["total"]
                if other_gestores == 0:
                    raise ValueError("Não é permitido desativar o único Gestor ativo no sistema.")

            db.execute("UPDATE usuarios SET ativo = ? WHERE id = ?", (1 if ativo else 0, user_id))

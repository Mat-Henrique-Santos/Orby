from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
from .core.models import Cliente, Equipamento, OrdemServico, StatusOS
from .database import Database


class Repository:
    def __init__(self, database: Database) -> None:
        self.database = database

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
                    "SELECT 1 FROM clientes WHERE lower(nome)=lower(?) OR telefone=? LIMIT 1",
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

    def equipment(self, customer_id: int | None = None) -> list[dict]:
        sql = """SELECT e.*, c.nome AS cliente_nome FROM equipamentos e
                 JOIN clientes c ON c.id=e.cliente_id"""
        params = []
        if customer_id:
            sql += " WHERE e.cliente_id=?"
            params.append(customer_id)
        sql += " ORDER BY c.nome COLLATE NOCASE, e.tipo, e.marca, e.modelo"
        with self.database.connect() as db:
            rows = db.execute(sql, params).fetchall()
        return [dict(row) for row in rows]

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
            prev_row = db.execute("SELECT status, data_finalizacao FROM ordens_servico WHERE id=?", (order_id,)).fetchone()
            if not prev_row:
                raise ValueError(f"Ordem de Serviço #{order_id} não encontrada.")
            previous_status = prev_row["status"]

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

            # Previsão a receber (OS ativas e aprovadas)
            prev_row = db.execute(
                """SELECT COALESCE(SUM(valor), 0) as receita_prevista
                   FROM ordens_servico
                   WHERE status IN ('Aguardando Aprovação', 'Em Reparo', 'Aguardando Retirada')"""
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
        from .database import hash_password
        senha_hash = hash_password(password)
        with self.database.connect() as db:
            row = db.execute(
                "SELECT id, nome, login, perfil, ativo, criado_em FROM usuarios WHERE login = ? AND senha_hash = ? AND ativo = 1",
                (login.strip(), senha_hash),
            ).fetchone()
        return dict(row) if row else None

    def users(self) -> list[dict]:
        with self.database.connect() as db:
            rows = db.execute(
                "SELECT id, nome, login, perfil, ativo, criado_em FROM usuarios ORDER BY nome ASC"
            ).fetchall()
        return [dict(r) for r in rows]

    def add_user(self, nome: str, login: str, password: str, perfil: str) -> int:
        from .database import hash_password
        if not nome.strip() or not login.strip() or not password.strip():
            raise ValueError("Nome, login e senha são obrigatórios.")
        if perfil not in ("Gestor", "Técnico", "Atendente"):
            raise ValueError(f"Perfil '{perfil}' inválido.")
        senha_hash = hash_password(password)
        with self.database.connect() as db:
            cursor = db.execute(
                "INSERT INTO usuarios (nome, login, senha_hash, perfil) VALUES (?, ?, ?, ?)",
                (nome.strip(), login.strip(), senha_hash, perfil),
            )
            return int(cursor.lastrowid)


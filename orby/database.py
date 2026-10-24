from __future__ import annotations

from abc import ABC, abstractmethod
import hashlib
import os
import sqlite3
from pathlib import Path
from typing import Any


def get_default_db_path() -> str:
    """Retorna o caminho padrão do banco de dados na pasta AppData/Application Support/Home do usuário."""
    appdata = os.getenv("APPDATA")
    if appdata:
        data_dir = Path(appdata) / "Orby"
    else:
        # Fallback cross-platform (Linux/macOS)
        data_dir = Path.home() / ".orby"

    data_dir.mkdir(parents=True, exist_ok=True)
    return str(data_dir / "orby.db")


def hash_password(password: str) -> str:
    salt = "orby_aero_salt_2026"
    return hashlib.sha256((salt + password).encode("utf-8")).hexdigest()


def verify_password(password: str, hashed: str) -> bool:
    return hash_password(password) == hashed


class DatabaseBackend(ABC):
    """
    Interface abstrata para desacoplar a camada de persistência.
    Permite alternar entre SQLite local e bancos relacionais em rede/nuvem (PostgreSQL, MySQL).
    """

    @abstractmethod
    def connect(self) -> Any:
        """Retorna uma conexão ativa compatível com o padrão DB-API 2.0 (PEP 249)."""
        pass

    @abstractmethod
    def initialize(self) -> None:
        """Cria tabelas, índices e executa migrações necessárias."""
        pass

    @abstractmethod
    def backup(self, destination: str | None = None, compress: bool = True) -> str:
        """Executa rotina de backup da base de dados."""
        pass

    @abstractmethod
    def restore(self, source: str) -> dict:
        """Restaura a base de dados a partir de uma cópia de segurança."""
        pass


class Database(DatabaseBackend):
    def __init__(self, path: str | None = None) -> None:
        self.path = path or get_default_db_path()

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def backup(self, destination: str | None = None, compress: bool = True) -> str:
        from .core.backup import BackupManager
        manager = BackupManager(db_path=self.path)
        return str(manager.create_backup(destination_path=destination, compress=compress))

    def restore(self, source: str) -> dict:
        from .core.backup import BackupManager
        manager = BackupManager(db_path=self.path)
        res = manager.restore_backup(source)
        self.initialize()
        return res

    def get_setting(self, key: str, default: str = "") -> str:
        with self.connect() as db:
            row = db.execute("SELECT valor FROM configuracoes WHERE chave = ?", (key,)).fetchone()
            return str(row["valor"]) if row else default

    def set_setting(self, key: str, value: str) -> None:
        with self.connect() as db:
            db.execute(
                """INSERT INTO configuracoes (chave, valor, atualizado_em)
                   VALUES (?, ?, CURRENT_TIMESTAMP)
                   ON CONFLICT(chave) DO UPDATE SET valor = excluded.valor, atualizado_em = CURRENT_TIMESTAMP""",
                (key, str(value)),
            )

    def initialize(self) -> None:
        with self.connect() as db:
            db.executescript(
                """
                CREATE TABLE IF NOT EXISTS clientes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL COLLATE NOCASE,
                    telefone TEXT NOT NULL,
                    email TEXT,
                    documento TEXT,
                    endereco TEXT,
                    criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS equipamentos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cliente_id INTEGER NOT NULL,
                    tipo TEXT NOT NULL,
                    marca TEXT,
                    modelo TEXT,
                    numero_serie TEXT,
                    acessorios TEXT,
                    condicao_entrada TEXT,
                    observacoes TEXT,
                    criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(cliente_id) REFERENCES clientes(id) ON DELETE RESTRICT
                );

                CREATE TABLE IF NOT EXISTS ordens_servico (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cliente_id INTEGER NOT NULL,
                    equipamento_id INTEGER,
                    descricao TEXT NOT NULL,
                    diagnostico TEXT,
                    tecnico TEXT,
                    status TEXT NOT NULL DEFAULT 'Aberta'
                        CHECK(status IN ('Aberta', 'Em Diagnóstico', 'Aguardando Aprovação', 'Em Reparo', 'Aguardando Retirada', 'Finalizada', 'Cancelada')),
                    valor REAL NOT NULL DEFAULT 0,
                    valor_servico REAL NOT NULL DEFAULT 0,
                    valor_pecas REAL NOT NULL DEFAULT 0,
                    forma_pagamento TEXT,
                    data_abertura TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    data_finalizacao TEXT,
                    observacoes TEXT,
                    FOREIGN KEY(cliente_id) REFERENCES clientes(id) ON DELETE RESTRICT,
                    FOREIGN KEY(equipamento_id) REFERENCES equipamentos(id) ON DELETE RESTRICT
                );

                CREATE TABLE IF NOT EXISTS historico_os (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ordem_id INTEGER NOT NULL,
                    status_anterior TEXT,
                    status_novo TEXT NOT NULL,
                    observacao TEXT,
                    criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(ordem_id) REFERENCES ordens_servico(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS usuarios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL,
                    login TEXT NOT NULL UNIQUE COLLATE NOCASE,
                    senha_hash TEXT NOT NULL,
                    perfil TEXT NOT NULL CHECK(perfil IN ('Gestor', 'Técnico', 'Atendente')),
                    ativo INTEGER NOT NULL DEFAULT 1,
                    criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS configuracoes (
                    chave TEXT PRIMARY KEY,
                    valor TEXT NOT NULL,
                    atualizado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                """
            )
            self._apply_migrations(db)
            self._seed_default_users(db)

    def _seed_default_users(self, db: sqlite3.Connection) -> None:
        count = db.execute("SELECT COUNT(*) AS total FROM usuarios").fetchone()["total"]
        if count == 0:
            default_users = [
                ("Administrador", "admin", hash_password("admin123"), "Gestor"),
                ("Carlos Técnico", "tecnico", hash_password("tec123"), "Técnico"),
                ("Mariana Atendente", "atendente", hash_password("atende123"), "Atendente"),
            ]
            db.executemany(
                "INSERT INTO usuarios (nome, login, senha_hash, perfil) VALUES (?, ?, ?, ?)",
                default_users,
            )

    def _apply_migrations(self, db: sqlite3.Connection) -> None:
        # Migração de colunas adicionais para clientes (documento, endereco)
        cliente_cols = {row["name"] for row in db.execute("PRAGMA table_info(clientes)")}
        if "documento" not in cliente_cols:
            db.execute("ALTER TABLE clientes ADD COLUMN documento TEXT")
        if "endereco" not in cliente_cols:
            db.execute("ALTER TABLE clientes ADD COLUMN endereco TEXT")

        # Migração da tabela de ordens de serviço caso seja esquema legado
        os_cols = {row["name"] for row in db.execute("PRAGMA table_info(ordens_servico)")}
        if "equipamento_id" not in os_cols:
            self._migrate_orders(db)
            os_cols = {row["name"] for row in db.execute("PRAGMA table_info(ordens_servico)")}

        # Migrações financeiras adicionais
        if "valor_servico" not in os_cols:
            db.execute("ALTER TABLE ordens_servico ADD COLUMN valor_servico REAL NOT NULL DEFAULT 0")
        if "valor_pecas" not in os_cols:
            db.execute("ALTER TABLE ordens_servico ADD COLUMN valor_pecas REAL NOT NULL DEFAULT 0")
        if "forma_pagamento" not in os_cols:
            db.execute("ALTER TABLE ordens_servico ADD COLUMN forma_pagamento TEXT")
        if "data_finalizacao" not in os_cols:
            db.execute("ALTER TABLE ordens_servico ADD COLUMN data_finalizacao TEXT")

    @staticmethod
    def _migrate_orders(db: sqlite3.Connection) -> None:
        db.executescript(
            """
            ALTER TABLE ordens_servico RENAME TO ordens_servico_anterior;
            CREATE TABLE ordens_servico (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cliente_id INTEGER NOT NULL,
                equipamento_id INTEGER,
                descricao TEXT NOT NULL,
                diagnostico TEXT,
                tecnico TEXT,
                status TEXT NOT NULL DEFAULT 'Aberta'
                    CHECK(status IN ('Aberta', 'Em Diagnóstico', 'Aguardando Aprovação', 'Em Reparo', 'Aguardando Retirada', 'Finalizada', 'Cancelada')),
                valor REAL NOT NULL DEFAULT 0,
                valor_servico REAL NOT NULL DEFAULT 0,
                valor_pecas REAL NOT NULL DEFAULT 0,
                forma_pagamento TEXT,
                data_abertura TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                data_finalizacao TEXT,
                observacoes TEXT,
                FOREIGN KEY(cliente_id) REFERENCES clientes(id) ON DELETE RESTRICT,
                FOREIGN KEY(equipamento_id) REFERENCES equipamentos(id) ON DELETE RESTRICT
            );
            INSERT INTO ordens_servico (id, cliente_id, descricao, status, valor, data_abertura, observacoes)
            SELECT id, cliente_id, descricao,
                CASE status
                    WHEN 'Aberto' THEN 'Aberta'
                    WHEN 'Em Análise' THEN 'Em Diagnóstico'
                    WHEN 'Em Andamento' THEN 'Em Reparo'
                    WHEN 'Cancelado' THEN 'Cancelada'
                    ELSE status
                END,
                valor, data_abertura, observacoes
            FROM ordens_servico_anterior;
            DROP TABLE ordens_servico_anterior;
            """
        )


def create_database(engine: str = "sqlite", **kwargs: Any) -> DatabaseBackend:
    """
    Fábrica para instanciar backends de banco de dados.
    Pronto para conectar ao SQLite local ou a instâncias remotas (PostgreSQL / MySQL)
    sem que o restante da aplicação ou repositório precise ser reescrito.
    """
    engine_normalized = engine.lower().strip()
    if engine_normalized in ("sqlite", "sqlite3", "local"):
        return Database(path=kwargs.get("path"))
    elif engine_normalized in ("postgres", "postgresql", "pg"):
        raise NotImplementedError(
            "O backend PostgreSQL está preparado na arquitetura DatabaseBackend e requer o driver 'psycopg2' ou 'asyncpg'. "
            "Para utilizá-lo em modo cloud, instale as dependências e implemente a subclasse PostgresDatabase(DatabaseBackend)."
        )
    elif engine_normalized in ("mysql", "mariadb"):
        raise NotImplementedError(
            "O backend MySQL está preparado na arquitetura DatabaseBackend e requer 'mysql-connector-python'. "
            "Implemente a subclasse MySQLDatabase(DatabaseBackend)."
        )
    else:
        raise ValueError(f"Motor de banco de dados não suportado: {engine}")

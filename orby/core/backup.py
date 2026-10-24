from __future__ import annotations

import json
import os
import shutil
import sqlite3
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path


class BackupError(Exception):
    """Exceção base para erros de rotinas de backup e restauração."""
    pass


class InvalidBackupFileError(BackupError):
    """Exceção levantada quando um arquivo de backup é inválido ou corrompido."""
    pass


def get_default_backup_dir() -> Path:
    """Retorna o diretório padrão onde backups automáticos e manuais são arquivados."""
    appdata = os.getenv("APPDATA")
    if appdata:
        base_dir = Path(appdata) / "Orby"
    else:
        base_dir = Path.home() / ".orby"

    backup_dir = base_dir / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    return backup_dir


def format_file_size(size_bytes: int) -> str:
    """Formata bytes em string legível (B, KB, MB)."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.2f} MB"


class BackupManager:
    """Gerenciador de backup e restauração de alta confiabilidade para o banco SQLite do Orby."""

    def __init__(self, db_path: str | None = None, backup_dir: str | Path | None = None) -> None:
        if db_path:
            self.db_path = Path(db_path)
        else:
            from ..database import get_default_db_path
            self.db_path = Path(get_default_db_path())

        self.backup_dir = Path(backup_dir) if backup_dir else get_default_backup_dir()

    def get_backup_dir(self) -> Path:
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        return self.backup_dir

    def get_database_info(self) -> dict:
        """Coleta informações operacionais sobre o banco de dados atual."""
        if not self.db_path.exists():
            return {
                "exists": False,
                "path": str(self.db_path),
                "size_formatted": "0 B",
                "size_bytes": 0,
                "last_modified": "Nunca",
                "counts": {},
            }

        size_bytes = self.db_path.stat().st_size
        mtime = datetime.fromtimestamp(self.db_path.stat().st_mtime)

        counts = {}
        try:
            conn = sqlite3.connect(f"file:{self.db_path}?mode=ro", uri=True)
            conn.row_factory = sqlite3.Row
            tables = ["clientes", "equipamentos", "ordens_servico", "usuarios", "historico_os"]
            for table in tables:
                try:
                    row = conn.execute(f"SELECT COUNT(*) as qtd FROM {table}").fetchone()
                    counts[table] = row["qtd"] if row else 0
                except sqlite3.OperationalError:
                    counts[table] = 0
            conn.close()
        except Exception:
            pass

        return {
            "exists": True,
            "path": str(self.db_path),
            "size_formatted": format_file_size(size_bytes),
            "size_bytes": size_bytes,
            "last_modified": mtime.strftime("%d/%m/%Y às %H:%M:%S"),
            "counts": counts,
        }

    def create_backup(
        self,
        destination_path: str | Path | None = None,
        compress: bool = True,
    ) -> Path:
        """
        Gera uma cópia de segurança confiável utilizando a API de backup online do SQLite.
        Se destination_path for omitido, salva na pasta padrão com carimbo de data/hora.
        """
        if not self.db_path.exists():
            raise BackupError(f"Arquivo de banco de dados não localizado: {self.db_path}")

        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")

        if destination_path:
            target_path = Path(destination_path)
            # Se a extensão for .zip, força compressão
            if target_path.suffix.lower() == ".zip":
                compress = True
        else:
            ext = ".zip" if compress else ".db"
            filename = f"orby_backup_{timestamp}{ext}"
            target_path = self.get_backup_dir() / filename

        target_path.parent.mkdir(parents=True, exist_ok=True)

        # 1. Faz o backup seguro via sqlite3.Connection.backup para arquivo temporário
        temp_db_fd, temp_db_path = tempfile.mkstemp(suffix=".db", prefix="orby_bck_")
        os.close(temp_db_fd)

        try:
            src_conn = sqlite3.connect(str(self.db_path))
            dst_conn = sqlite3.connect(temp_db_path)
            with dst_conn:
                src_conn.backup(dst_conn, pages=250)
            dst_conn.close()
            src_conn.close()

            # 2. Se for compactado, gera o arquivo .zip com metadata
            if compress:
                # Coleta metadata simples
                meta = {
                    "system": "Orby Desktop",
                    "backup_time": datetime.now().isoformat(),
                    "source_size_bytes": self.db_path.stat().st_size,
                    "version": "2.0",
                }
                with zipfile.ZipFile(target_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
                    zf.write(temp_db_path, arcname="orby.db")
                    zf.writestr("backup_info.json", json.dumps(meta, indent=2))
            else:
                shutil.copy2(temp_db_path, str(target_path))

        finally:
            if os.path.exists(temp_db_path):
                try:
                    os.remove(temp_db_path)
                except OSError:
                    pass

        return target_path

    def validate_backup(self, backup_file: str | Path) -> dict:
        """
        Inspeciona o arquivo de backup e valida se é um banco SQLite legítimo e íntegro do Orby.
        Retorna metadados das tabelas e registros encontrados.
        """
        file_path = Path(backup_file)
        if not file_path.exists():
            raise InvalidBackupFileError(f"Arquivo de backup não encontrado: {file_path}")

        temp_db_fd, temp_db_path = tempfile.mkstemp(suffix=".db", prefix="orby_val_")
        os.close(temp_db_fd)

        try:
            if file_path.suffix.lower() == ".zip":
                try:
                    with zipfile.ZipFile(file_path, "r") as zf:
                        namelist = zf.namelist()
                        db_name = None
                        if "orby.db" in namelist:
                            db_name = "orby.db"
                        else:
                            # Busca qualquer .db dentro do zip
                            for n in namelist:
                                if n.lower().endswith(".db"):
                                    db_name = n
                                    break

                        if not db_name:
                            raise InvalidBackupFileError("O arquivo .zip não contém um banco 'orby.db' válido.")

                        with open(temp_db_path, "wb") as out_f:
                            out_f.write(zf.read(db_name))
                except zipfile.BadZipFile:
                    raise InvalidBackupFileError("O arquivo ZIP está corrompido ou é inválido.")
            else:
                # Arquivo .db direto
                shutil.copy2(str(file_path), temp_db_path)

            # Validação SQLite
            try:
                conn = sqlite3.connect(temp_db_path)
                conn.row_factory = sqlite3.Row
                # Verifica integridade do arquivo SQLite
                integrity = conn.execute("PRAGMA integrity_check").fetchone()
                if not integrity or integrity[0] != "ok":
                    raise InvalidBackupFileError("O arquivo de banco de dados falhou na checagem de integridade do SQLite.")

                # Verifica tabelas obrigatórias do Orby
                tables = {
                    row["name"]
                    for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
                }
                required = {"clientes", "ordens_servico", "usuarios"}
                if not required.issubset(tables):
                    raise InvalidBackupFileError(
                        f"O banco de backup não possui as tabelas mínimas do Orby. Encontradas: {tables}"
                    )

                counts = {}
                for t in ["clientes", "equipamentos", "ordens_servico", "usuarios"]:
                    if t in tables:
                        counts[t] = conn.execute(f"SELECT COUNT(*) AS c FROM {t}").fetchone()["c"]

                conn.close()
            except sqlite3.DatabaseError as e:
                raise InvalidBackupFileError(f"Arquivo não é um banco SQLite válido: {e}")

            return {
                "valid": True,
                "file_path": str(file_path),
                "size_formatted": format_file_size(file_path.stat().st_size),
                "counts": counts,
            }

        finally:
            if os.path.exists(temp_db_path):
                try:
                    os.remove(temp_db_path)
                except OSError:
                    pass

    def restore_backup(self, backup_file: str | Path) -> dict:
        """
        Restaura o sistema a partir de um backup validado.
        Cria automaticamente um snapshot de emergência pré-restauração antes de sobrescrever.
        """
        validation = self.validate_backup(backup_file)
        file_path = Path(backup_file)

        # 1. Cria snapshot de segurança do estado atual (se existir)
        if self.db_path.exists():
            timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
            emergency_dir = self.get_backup_dir() / "emergency"
            emergency_dir.mkdir(parents=True, exist_ok=True)
            emergency_file = emergency_dir / f"orby_pre_restore_snapshot_{timestamp}.db"
            try:
                src_conn = sqlite3.connect(str(self.db_path))
                dst_conn = sqlite3.connect(str(emergency_file))
                with dst_conn:
                    src_conn.backup(dst_conn)
                dst_conn.close()
                src_conn.close()
            except Exception:
                shutil.copy2(str(self.db_path), str(emergency_file))

        # 2. Extrai ou copia o arquivo restaurado para um temporário
        temp_db_fd, temp_db_path = tempfile.mkstemp(suffix=".db", prefix="orby_rst_")
        os.close(temp_db_fd)

        try:
            if file_path.suffix.lower() == ".zip":
                with zipfile.ZipFile(file_path, "r") as zf:
                    db_name = "orby.db" if "orby.db" in zf.namelist() else [n for n in zf.namelist() if n.endswith(".db")][0]
                    with open(temp_db_path, "wb") as out_f:
                        out_f.write(zf.read(db_name))
            else:
                shutil.copy2(str(file_path), temp_db_path)

            # 3. Substitui o banco ativo com segurança
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

            # Usa conexão SQLite backup para atualizar o arquivo de destino com segurança
            dst_conn = sqlite3.connect(str(self.db_path))
            src_conn = sqlite3.connect(temp_db_path)
            with dst_conn:
                src_conn.backup(dst_conn)
            src_conn.close()
            dst_conn.close()

            # 4. Aplica migrações para garantir que qualquer versão antiga seja compatível
            from ..database import Database
            Database(str(self.db_path)).initialize()

        finally:
            if os.path.exists(temp_db_path):
                try:
                    os.remove(temp_db_path)
                except OSError:
                    pass

        return validation

    def list_backups(self) -> list[dict]:
        """Lista os arquivos de backup arquivados na pasta padrão, ordenados do mais recente ao mais antigo."""
        if not self.backup_dir.exists():
            return []

        backups = []
        for item in self.backup_dir.iterdir():
            if item.is_file() and item.suffix.lower() in (".zip", ".db"):
                stat = item.stat()
                mtime = datetime.fromtimestamp(stat.st_mtime)
                backups.append({
                    "filename": item.name,
                    "path": str(item),
                    "size_bytes": stat.st_size,
                    "size_formatted": format_file_size(stat.st_size),
                    "modified_time": mtime,
                    "date_formatted": mtime.strftime("%d/%m/%Y às %H:%M:%S"),
                    "is_compressed": item.suffix.lower() == ".zip",
                })

        backups.sort(key=lambda x: x["modified_time"], reverse=True)
        return backups

    def cleanup_old_backups(self, keep_count: int = 15) -> int:
        """Remove backups automáticos excedentes para preservar o espaço em disco."""
        backups = self.list_backups()
        if len(backups) <= keep_count:
            return 0

        to_remove = backups[keep_count:]
        deleted = 0
        for b in to_remove:
            try:
                os.remove(b["path"])
                deleted += 1
            except OSError:
                pass
        return deleted

    def perform_auto_backup_on_exit(self) -> Path | None:
        """Executa um backup automático com carimbo de tempo na pasta de backups do usuário."""
        try:
            path = self.create_backup(compress=True)
            self.cleanup_old_backups(keep_count=15)
            return path
        except Exception:
            return None

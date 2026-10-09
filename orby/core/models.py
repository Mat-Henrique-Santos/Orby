from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class StatusOS(str, Enum):
    ABERTA = "Aberta"
    EM_DIAGNOSTICO = "Em Diagnóstico"
    AGUARDANDO_APROVACAO = "Aguardando Aprovação"
    EM_REPARO = "Em Reparo"
    AGUARDANDO_RETIRADA = "Aguardando Retirada"
    FINALIZADA = "Finalizada"
    CANCELADA = "Cancelada"

    @classmethod
    def all_values(cls) -> list[str]:
        return [status.value for status in cls]

    @classmethod
    def active_statuses(cls) -> list[str]:
        return [
            cls.ABERTA.value,
            cls.EM_DIAGNOSTICO.value,
            cls.AGUARDANDO_APROVACAO.value,
            cls.EM_REPARO.value,
            cls.AGUARDANDO_RETIRADA.value,
        ]


class PerfilUsuario(str, Enum):
    GESTOR = "Gestor"
    TECNICO = "Técnico"
    ATENDENTE = "Atendente"

    @classmethod
    def all_values(cls) -> list[str]:
        return [p.value for p in cls]


@dataclass
class Usuario:
    id: int | None
    nome: str
    login: str
    perfil: str
    ativo: bool = True
    criado_em: str | None = None


FORMA_PAGAMENTO_OPCOES = [
    "Não Definido",
    "PIX",
    "Dinheiro",
    "Cartão de Débito",
    "Cartão de Crédito",
    "Boleto Bancário",
    "Transferência / TED",
]


@dataclass
class Cliente:
    id: int | None
    nome: str
    telefone: str
    email: str | None = None
    documento: str | None = None
    endereco: str | None = None
    criado_em: str | None = None

    def validate(self) -> None:
        if not self.nome or not self.nome.strip():
            raise ValueError("O nome do cliente é obrigatório.")
        if not self.telefone or not self.telefone.strip():
            raise ValueError("O telefone do cliente é obrigatório.")


@dataclass
class Equipamento:
    id: int | None
    cliente_id: int
    tipo: str
    marca: str | None = None
    modelo: str | None = None
    numero_serie: str | None = None
    acessorios: str | None = None
    condicao_entrada: str | None = None
    observacoes: str | None = None
    cliente_nome: str | None = None
    criado_em: str | None = None

    @property
    def descricao_completa(self) -> str:
        partes = [self.tipo, self.marca, self.modelo]
        texto = " ".join(p.strip() for p in partes if p and p.strip())
        return texto or "Equipamento"

    def validate(self) -> None:
        if not self.cliente_id:
            raise ValueError("O equipamento deve estar vinculado a um cliente.")
        if not self.tipo or not self.tipo.strip():
            raise ValueError("O tipo do equipamento é obrigatório.")


@dataclass
class OrdemServico:
    id: int | None
    cliente_id: int
    equipamento_id: int
    descricao: str
    status: str = StatusOS.ABERTA.value
    valor: float = 0.0
    valor_servico: float = 0.0
    valor_pecas: float = 0.0
    forma_pagamento: str | None = None
    data_finalizacao: str | None = None
    diagnostico: str | None = None
    tecnico: str | None = None
    observacoes: str | None = None
    cliente_nome: str | None = None
    equipamento_nome: str | None = None
    data_abertura: str | None = None

    def validate(self) -> None:
        if not self.cliente_id:
            raise ValueError("A OS deve estar vinculada a um cliente.")
        if not self.equipamento_id:
            raise ValueError("Selecione o equipamento vinculado à OS.")
        if not self.descricao or not self.descricao.strip():
            raise ValueError("A descrição do serviço/problema é obrigatória.")
        if self.status not in StatusOS.all_values():
            raise ValueError(f"Status '{self.status}' inválido.")

        # Atualiza valor total com base nos componentes se fornecidos
        if self.valor_servico > 0 or self.valor_pecas > 0:
            calculado = round(self.valor_servico + self.valor_pecas, 2)
            if self.valor <= 0 or abs(self.valor - calculado) > 0.01:
                self.valor = calculado

        if self.status == StatusOS.FINALIZADA.value:
            if self.valor <= 0:
                raise ValueError("Informe um valor maior que zero antes de finalizar a OS.")
            if not self.forma_pagamento or self.forma_pagamento == "Não Definido":
                raise ValueError("Selecione a forma de pagamento antes de finalizar a OS.")

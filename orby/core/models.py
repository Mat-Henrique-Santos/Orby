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


import re


def validar_telefone(telefone: str) -> bool:
    """Valida se o telefone possui 10 ou 11 dígitos numéricos após limpeza."""
    digitos = re.sub(r"\D", "", telefone or "")
    return len(digitos) in (10, 11)


def validar_email(email: str) -> bool:
    """Valida o formato básico do endereço de e-mail."""
    if not email or not email.strip():
        return True
    padrao = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    return bool(re.match(padrao, email.strip()))


def validar_cpf(cpf: str) -> bool:
    """Valida CPF com cálculo dos dígitos verificadores."""
    d = [int(c) for c in cpf if c.isdigit()]
    if len(d) != 11 or len(set(d)) == 1:
        return False
    # Primeiro dígito verificador
    soma1 = sum(d[i] * (10 - i) for i in range(9))
    resto1 = (soma1 * 10) % 11
    dig1 = 0 if resto1 in (10, 11) else resto1
    if dig1 != d[9]:
        return False
    # Segundo dígito verificador
    soma2 = sum(d[i] * (11 - i) for i in range(10))
    resto2 = (soma2 * 10) % 11
    dig2 = 0 if resto2 in (10, 11) else resto2
    return dig2 == d[10]


def validar_cnpj(cnpj: str) -> bool:
    """Valida CNPJ com cálculo dos dígitos verificadores."""
    d = [int(c) for c in cnpj if c.isdigit()]
    if len(d) != 14 or len(set(d)) == 1:
        return False
    # Primeiro dígito
    pesos1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    soma1 = sum(d[i] * pesos1[i] for i in range(12))
    resto1 = soma1 % 11
    dig1 = 0 if resto1 < 2 else 11 - resto1
    if dig1 != d[12]:
        return False
    # Segundo dígito
    pesos2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    soma2 = sum(d[i] * pesos2[i] for i in range(13))
    resto2 = soma2 % 11
    dig2 = 0 if resto2 < 2 else 11 - resto2
    return dig2 == d[13]


def validar_documento(doc: str) -> bool:
    """Valida se o documento é um CPF (11 dígitos) ou CNPJ (14 dígitos) válido."""
    if not doc or not doc.strip():
        return True
    digitos = re.sub(r"\D", "", doc)
    if len(digitos) == 11:
        return validar_cpf(digitos)
    if len(digitos) == 14:
        return validar_cnpj(digitos)
    return False


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
        if not validar_telefone(self.telefone):
            raise ValueError("Telefone inválido. O telefone deve conter DDD + 8 ou 9 dígitos (10 ou 11 números).")
        if self.email and not validar_email(self.email):
            raise ValueError(f"E-mail '{self.email}' possui formato inválido.")
        if self.documento and not validar_documento(self.documento):
            raise ValueError(f"Documento '{self.documento}' inválido (CPF ou CNPJ incorreto).")


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

from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class UsuarioCreate(BaseModel):
    nome: str = Field(..., min_length=2, max_length=100, examples=["João Silva"])
    cpf: str = Field(..., min_length=11, max_length=11, pattern=r"^\d{11}$", examples=["12345678901"])
    senha: str = Field(..., min_length=6, examples=["senha123"])


class UsuarioOut(BaseModel):
    id: int
    nome: str
    cpf: str
    criado_em: datetime

    model_config = {"from_attributes": True}


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ContaCreate(BaseModel):
    limite: Decimal = Field(
        default=Decimal("500.00"),
        ge=0,
        description="Limite por saque (padrão R$ 500,00)",
    )
    limite_saques: int = Field(
        default=3,
        ge=1,
        description="Máximo de saques permitidos (padrão 3)",
    )


class ContaOut(BaseModel):
    id: int
    numero: int
    agencia: str
    saldo: Decimal
    limite: Decimal
    limite_saques: int
    criado_em: datetime
    usuario_id: int

    model_config = {"from_attributes": True}


class TransacaoCreate(BaseModel):
    conta_id: int = Field(..., description="ID da conta alvo da transação")
    valor: Decimal = Field(..., gt=0, description="Valor da transação (deve ser positivo)")

    @field_validator("valor")
    @classmethod
    def valor_positivo(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("O valor da transação deve ser maior que zero.")
        return v


class TransacaoOut(BaseModel):
    id: int
    tipo: Literal["deposito", "saque"]
    valor: Decimal
    data: datetime
    conta_id: int

    model_config = {"from_attributes": True}


class ExtratoOut(BaseModel):
    conta: ContaOut
    transacoes: list[TransacaoOut]

from datetime import datetime
from decimal import Decimal

from sqlalchemy import ForeignKey, Numeric, String, DateTime, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Usuario(Base):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    nome: Mapped[str] = mapped_column(String(100), nullable=False)
    cpf: Mapped[str] = mapped_column(String(11), unique=True, index=True, nullable=False)
    senha_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    contas: Mapped[list["Conta"]] = relationship(
        "Conta", back_populates="usuario", cascade="all, delete-orphan"
    )


class Conta(Base):
    __tablename__ = "contas"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    numero: Mapped[int] = mapped_column(unique=True, index=True, nullable=False)
    agencia: Mapped[str] = mapped_column(String(4), default="0001", nullable=False)
    saldo: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    limite: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("500.00"), nullable=False)
    limite_saques: Mapped[int] = mapped_column(default=3, nullable=False)
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), nullable=False)
    usuario: Mapped["Usuario"] = relationship("Usuario", back_populates="contas")

    transacoes: Mapped[list["Transacao"]] = relationship(
        "Transacao", back_populates="conta", cascade="all, delete-orphan"
    )


class Transacao(Base):
    __tablename__ = "transacoes"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    tipo: Mapped[str] = mapped_column(
        Enum("deposito", "saque", name="tipo_transacao"), nullable=False
    )
    valor: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    data: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    conta_id: Mapped[int] = mapped_column(ForeignKey("contas.id"), nullable=False)
    conta: Mapped["Conta"] = relationship("Conta", back_populates="transacoes")

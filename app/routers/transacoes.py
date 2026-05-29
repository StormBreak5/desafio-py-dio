from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.database import get_db
from app.models import Conta, Transacao, Usuario
from app.schemas import TransacaoCreate, TransacaoOut

router = APIRouter(prefix="/transacoes", tags=["Transações"])


async def _get_conta_do_usuario(
    conta_id: int, usuario: Usuario, db: AsyncSession
) -> Conta:
    """Helper: busca a conta e valida que pertence ao usuário autenticado."""
    result = await db.execute(select(Conta).where(Conta.id == conta_id))
    conta = result.scalar_one_or_none()

    if not conta:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conta não encontrada.")

    if conta.usuario_id != usuario.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado: esta conta não pertence ao usuário autenticado.",
        )
    return conta


@router.post(
    "/deposito",
    response_model=TransacaoOut,
    status_code=status.HTTP_201_CREATED,
    summary="Realizar depósito",
    description="Adiciona um valor ao saldo da conta. O valor deve ser positivo.",
)
async def depositar(
    payload: TransacaoCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    usuario: Annotated[Usuario, Depends(get_current_user)],
) -> TransacaoOut:
    conta = await _get_conta_do_usuario(payload.conta_id, usuario, db)

    conta.saldo = Decimal(str(conta.saldo)) + payload.valor

    transacao = Transacao(tipo="deposito", valor=payload.valor, conta_id=conta.id)
    db.add(transacao)
    await db.flush()
    await db.refresh(transacao)
    return transacao


@router.post(
    "/saque",
    response_model=TransacaoOut,
    status_code=status.HTTP_201_CREATED,
    summary="Realizar saque",
    description=(
        "Deduz um valor do saldo da conta. Validações: "
        "valor positivo, saldo suficiente, valor dentro do limite por saque "
        "e número máximo de saques não excedido."
    ),
)
async def sacar(
    payload: TransacaoCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    usuario: Annotated[Usuario, Depends(get_current_user)],
) -> TransacaoOut:
    conta = await _get_conta_do_usuario(payload.conta_id, usuario, db)

    saldo_atual = Decimal(str(conta.saldo))
    limite = Decimal(str(conta.limite))

    if payload.valor > limite:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"O valor do saque (R$ {payload.valor:.2f}) excede o limite por operação (R$ {limite:.2f}).",
        )

    if payload.valor > saldo_atual:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Saldo insuficiente. Saldo disponível: R$ {saldo_atual:.2f}.",
        )

    result = await db.execute(
        select(func.count(Transacao.id)).where(
            Transacao.conta_id == conta.id,
            Transacao.tipo == "saque",
        )
    )
    total_saques = result.scalar() or 0

    if total_saques >= conta.limite_saques:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Número máximo de saques ({conta.limite_saques}) atingido para esta conta.",
        )

    conta.saldo = saldo_atual - payload.valor

    transacao = Transacao(tipo="saque", valor=payload.valor, conta_id=conta.id)
    db.add(transacao)
    await db.flush()
    await db.refresh(transacao)
    return transacao

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth import get_current_user
from app.database import get_db
from app.models import Conta, Transacao, Usuario
from app.schemas import ContaCreate, ContaOut, ExtratoOut

router = APIRouter(prefix="/contas", tags=["Contas"])


@router.post(
    "",
    response_model=ContaOut,
    status_code=status.HTTP_201_CREATED,
    summary="Criar conta corrente",
    description="Cria uma nova conta corrente para o usuário autenticado.",
)
async def criar_conta(
    payload: ContaCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    usuario: Annotated[Usuario, Depends(get_current_user)],
) -> ContaOut:
    # Gerar número de conta único (maior número existente + 1)
    result = await db.execute(select(func.max(Conta.numero)))
    max_numero = result.scalar() or 0

    conta = Conta(
        numero=max_numero + 1,
        usuario_id=usuario.id,
        limite=payload.limite,
        limite_saques=payload.limite_saques,
    )
    db.add(conta)
    await db.flush()
    await db.refresh(conta)
    return conta


@router.get(
    "/{conta_id}/extrato",
    response_model=ExtratoOut,
    summary="Exibir extrato da conta",
    description=(
        "Retorna todas as transações realizadas na conta, além do saldo atual. "
        "Somente o dono da conta pode visualizar o extrato."
    ),
)
async def exibir_extrato(
    conta_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    usuario: Annotated[Usuario, Depends(get_current_user)],
) -> ExtratoOut:
    result = await db.execute(
        select(Conta)
        .options(selectinload(Conta.transacoes))
        .where(Conta.id == conta_id)
    )
    conta = result.scalar_one_or_none()

    if not conta:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conta não encontrada.")

    if conta.usuario_id != usuario.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado: esta conta não pertence ao usuário autenticado.",
        )

    return ExtratoOut(conta=conta, transacoes=conta.transacoes)

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import criar_access_token, hash_senha, verificar_senha
from app.database import get_db
from app.models import Usuario
from app.schemas import Token, UsuarioCreate, UsuarioOut

router = APIRouter(prefix="/auth", tags=["Autenticação"])


@router.post(
    "/register",
    response_model=UsuarioOut,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastrar novo usuário",
    description="Cria um novo usuário/cliente. O CPF deve conter exatamente 11 dígitos e ser único.",
)
async def registrar_usuario(
    payload: UsuarioCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UsuarioOut:
    result = await db.execute(select(Usuario).where(Usuario.cpf == payload.cpf))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Já existe um usuário cadastrado com este CPF.",
        )

    usuario = Usuario(
        nome=payload.nome,
        cpf=payload.cpf,
        senha_hash=hash_senha(payload.senha),
    )
    db.add(usuario)
    await db.flush()
    await db.refresh(usuario)
    return usuario


@router.post(
    "/token",
    response_model=Token,
    summary="Autenticar e obter token JWT",
    description=(
        "Realiza login com CPF e senha. Retorna um token Bearer JWT "
        "que deve ser enviado no header `Authorization` das rotas protegidas."
    ),
)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Token:
    result = await db.execute(select(Usuario).where(Usuario.cpf == form_data.username))
    usuario = result.scalar_one_or_none()

    if not usuario or not verificar_senha(form_data.password, usuario.senha_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="CPF ou senha incorretos.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = criar_access_token(data={"sub": usuario.cpf})
    return Token(access_token=token)

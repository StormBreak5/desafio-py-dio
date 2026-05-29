from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import engine, Base
from app.routers import auth, contas, transacoes


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(
    title="API Bancária Assíncrona",
    description=(
        "API RESTful assíncrona para gerenciamento de operações bancárias. "
        "Permite cadastro de usuários, criação de contas correntes, depósitos, "
        "saques e consulta de extrato. Autenticação via JWT (Bearer Token)."
    ),
    version="1.0.0",
    contact={"name": "Desafio DIO — FastAPI"},
    lifespan=lifespan,
)

app.include_router(auth.router)
app.include_router(contas.router)
app.include_router(transacoes.router)


@app.get("/", tags=["Health"], summary="Health check")
async def root():
    return {"status": "ok", "message": "API Bancária rodando. Acesse /docs para a documentação."}

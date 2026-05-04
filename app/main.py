from fastapi import FastAPI, Request
from contextlib import asynccontextmanager

from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import engine, SessionLocal

# MODELS
from app.models.tipo_host import TipoHost
from app.models.host import Host
from app.models.tipo_servico import TipoServico
from app.models.host_servico import HostServico
from app.models.configuracao_snmp import ConfiguracaoSNMP
from app.models.metrica_snmp import MetricaSNMP
from app.models.verificacao import Verificacao
from app.models.alerta import Alerta

# ROUTES
from app.routes.hosts import router as hosts_router

# SCHEDULER
from app.scheduler.scheduler import iniciar_scheduler


# -------------------------
# LIFESPAN (startup/shutdown)
# -------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 A iniciar aplicação...")
    iniciar_scheduler()
    yield
    print("🛑 A encerrar aplicação...")


# -------------------------
# APP
# -------------------------
app = FastAPI(lifespan=lifespan)

app.include_router(hosts_router)

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")


# -------------------------
# HOME
# -------------------------
@app.get("/")
def home(request: Request):
    db: Session = SessionLocal()
    try:
        hosts = db.query(Host).all()
        tipos_host = db.query(TipoHost).all()
        tipos_servico = db.query(TipoServico).all()

        total_hosts_ativos = (
            db.query(Host)
            .filter(Host.ativo == True)
            .count()
        )

        return templates.TemplateResponse(
            request,
            "index.html",
            {
                "hosts": hosts,
                "tipos_host": tipos_host,
                "tipos_servico": tipos_servico,
                "total_hosts": total_hosts_ativos
            }
        )
    finally:
        db.close()


# -------------------------
# DB TEST
# -------------------------
@app.get("/db-test")
def db_test():
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))
        value = result.scalar()
    return {"db_ok": value == 1}
from typing import List, Optional
import platform
import subprocess

from fastapi import APIRouter, Depends, HTTPException, Form
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.host import Host
from app.models.configuracao_snmp import ConfiguracaoSNMP
from app.models.host_servico import HostServico
from app.models.tipo_servico import TipoServico
from app.schemas.host import HostCreate, HostUpdate, HostResponse
from fastapi import Request
from fastapi.templating import Jinja2Templates


templates = Jinja2Templates(directory="app/templates")
router = APIRouter(prefix="/hosts", tags=["Hosts"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

#ping ao host
def ping_host(host: str) -> bool:
    sistema = platform.system().lower()

    if sistema == "windows":
        comando = ["ping", "-n", "1", "-w", "1000", host]
    else:
        comando = ["ping", "-c", "1", "-W", "1", host]

    try:
        resultado = subprocess.run(
            comando,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        return resultado.returncode == 0
    except Exception:
        return False

#ligar host a serviço
def criar_associacoes_servicos(db: Session, host_id: int, servicos_ids: Optional[List[int]]):
    if not servicos_ids:
        return

    tipos_servico = (
        db.query(TipoServico)
        .filter(TipoServico.id.in_(servicos_ids))
        .all()
    )
     #criar associações HostServico para cada serviço selecionado
    for tipo in tipos_servico:
        novo_host_servico = HostServico(
            host_id=host_id,
            tipo_servico_id=tipo.id,
            nome=tipo.nome,
            porta=tipo.porta_padrao,
            url=None,
            intervalo_verificacao_segundos=60,
            tempo_limite=5,
            ativo=False
        )
        db.add(novo_host_servico)

#criar host
@router.post("/", response_model=HostResponse)
def criar_host(host: HostCreate, db: Session = Depends(get_db)):
    estado_ativo = ping_host(str(host.endereco_ip))

    novo_host = Host(
        nome=host.nome,
        endereco_ip=host.endereco_ip,
        descricao=host.descricao,
        tipo_host_id=host.tipo_host_id,
        ativo=estado_ativo
    )

    db.add(novo_host)
    db.commit()
    db.refresh(novo_host)

    return novo_host

# recebe dadosdo formulario para criar host, incluindo configuração SNMP e serviços associados
@router.post("/form")
def criar_host_form(
    nome: str = Form(...),
    endereco_ip: str = Form(...),
    descricao: str = Form(None),
    tipo_host_id: int = Form(...),
    usar_snmp: str = Form(None),
    versao_snmp: str = Form(None),
    comunidade: str = Form(None),
    porta_snmp: int = Form(161),
    servicos_ids: Optional[List[int]] = Form(None),
    db: Session = Depends(get_db)
):
    estado_ativo = ping_host(endereco_ip)

    novo_host = Host(
        nome=nome,
        endereco_ip=endereco_ip,
        descricao=descricao,
        tipo_host_id=tipo_host_id,
        ativo=estado_ativo
    )

    db.add(novo_host)
    db.commit()
    db.refresh(novo_host)

    if usar_snmp == "on":
        if not versao_snmp or not comunidade:
            db.delete(novo_host)
            db.commit()
            raise HTTPException(
                status_code=400,
                detail="SNMP marcado, mas faltam campos obrigatórios."
            )

        configuracao_snmp = ConfiguracaoSNMP(
            host_id=novo_host.id,
            versao_snmp=versao_snmp,
            comunidade=comunidade,
            porta_snmp=porta_snmp,
            ativo=True
        )
        db.add(configuracao_snmp)

    criar_associacoes_servicos(db, novo_host.id, servicos_ids)
    db.commit()

    return RedirectResponse(url="/", status_code=303)

# editar host, incluindo configuração SNMP e serviços associados
@router.post("/form/{host_id}/editar")
def editar_host_form(
    host_id: int,
    nome: str = Form(...),
    endereco_ip: str = Form(...),
    descricao: str = Form(None),
    tipo_host_id: int = Form(...),
    usar_snmp: str = Form(None),
    versao_snmp: str = Form(None),
    comunidade: str = Form(None),
    porta_snmp: int = Form(161),
    servicos_ids: Optional[List[int]] = Form(None),
    db: Session = Depends(get_db)
):
    host = db.query(Host).filter(Host.id == host_id).first()

    if not host:
        raise HTTPException(status_code=404, detail="Host não encontrado")

    estado_ativo = ping_host(endereco_ip)

    host.nome = nome
    host.endereco_ip = endereco_ip
    host.descricao = descricao
    host.tipo_host_id = tipo_host_id
    host.ativo = estado_ativo

    configuracao_snmp = (
        db.query(ConfiguracaoSNMP)
        .filter(ConfiguracaoSNMP.host_id == host.id)
        .first()
    )

    if usar_snmp == "on":
        if not versao_snmp or not comunidade:
            raise HTTPException(
                status_code=400,
                detail="SNMP marcado, mas faltam campos obrigatórios."
            )

        if configuracao_snmp:
            configuracao_snmp.versao_snmp = versao_snmp
            configuracao_snmp.comunidade = comunidade
            configuracao_snmp.porta_snmp = porta_snmp
            configuracao_snmp.ativo = True
        else:
            configuracao_snmp = ConfiguracaoSNMP(
                host_id=host.id,
                versao_snmp=versao_snmp,
                comunidade=comunidade,
                porta_snmp=porta_snmp,
                ativo=True
            )
            db.add(configuracao_snmp)
    else:
        if configuracao_snmp:
            db.delete(configuracao_snmp)

    db.query(HostServico).filter(HostServico.host_id == host.id).delete()
    criar_associacoes_servicos(db, host.id, servicos_ids)

    db.commit()

    return RedirectResponse(url="/", status_code=303)

# eliminar host 
@router.post("/form/{host_id}/eliminar")
def eliminar_host_form(host_id: int, db: Session = Depends(get_db)):
    host = db.query(Host).filter(Host.id == host_id).first()

    if not host:
        raise HTTPException(status_code=404, detail="Host não encontrado")

    db.delete(host)
    db.commit()

    return RedirectResponse(url="/", status_code=303)


@router.get("/", response_model=list[HostResponse])
def listar_hosts(db: Session = Depends(get_db)):
    return db.query(Host).all()

#rota para mostrar detalhes do host
@router.get("/{host_id}/detalhe")
def detalhe_host(host_id: int, request: Request, db: Session = Depends(get_db)):
    host = db.query(Host).filter(Host.id == host_id).first()

    if not host:
        raise HTTPException(status_code=404, detail="Host não encontrado")

    return templates.TemplateResponse(
        request,
        "host_detalhe.html",
        {
            "host": host
        }
    )
    
#buscar host por id
@router.get("/{host_id}", response_model=HostResponse)
def buscar_host(host_id: int, db: Session = Depends(get_db)):
    host = db.query(Host).filter(Host.id == host_id).first()

    if not host:
        raise HTTPException(status_code=404, detail="Host não encontrado")

    return host

#atualizar um host
@router.put("/{host_id}", response_model=HostResponse)
def atualizar_host(host_id: int, dados: HostUpdate, db: Session = Depends(get_db)):
    host = db.query(Host).filter(Host.id == host_id).first()

    if not host:
        raise HTTPException(status_code=404, detail="Host não encontrado")

    host.nome = dados.nome
    host.endereco_ip = dados.endereco_ip
    host.descricao = dados.descricao
    host.tipo_host_id = dados.tipo_host_id
    host.ativo = dados.ativo

    db.commit()
    db.refresh(host)

    return host

#eliminar host
@router.delete("/{host_id}")
def eliminar_host(host_id: int, db: Session = Depends(get_db)):
    host = db.query(Host).filter(Host.id == host_id).first()

    if not host:
        raise HTTPException(status_code=404, detail="Host não encontrado")

    db.delete(host)
    db.commit()

    return {"mensagem": "Host eliminado com sucesso"}

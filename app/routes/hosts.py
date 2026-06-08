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
from app.checks.ssh_check import verificar_ssh
from sqlalchemy import func
from app.models.metrica_snmp import MetricaSNMP
from app.checks.oids import OIDS_DISPONIVEIS
from app.models.oid_snmp import OidSNMP
from app.models.verificacao import Verificacao
from app.scheduler.scheduler import verificar_servico_job, verificar_host_job, verificar_snmp_job, scheduler
from app.models.alerta import Alerta
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


# ping ao host
def ping_host(host: str) -> bool:
    sistema = platform.system().lower()

    if sistema == "windows":
        comando = ["ping", "-n", "1", "-w", "1000", host]
    else:
        comando = ["ping", "-c", "1", "-W", "1", host]

    try:
        resultado = subprocess.run(
            comando, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        return resultado.returncode == 0
    except Exception:
        return False


# ligar host a serviço
def criar_associacoes_servicos(
    db: Session, host_id: int, servicos_ids: Optional[List[int]]
):
    if not servicos_ids:
        return

    tipos_servico = db.query(TipoServico).filter(TipoServico.id.in_(servicos_ids)).all()
    # criar associações HostServico para cada serviço selecionado
    for tipo in tipos_servico:
        novo_host_servico = HostServico(
            host_id=host_id,
            tipo_servico_id=tipo.id,
            nome=tipo.nome,
            porta=tipo.porta_padrao,
            url=None,
            intervalo_verificacao_segundos=60,
            tempo_limite=5,
            ativo=True,
        )
        db.add(novo_host_servico)


# criar host
@router.post("/", response_model=HostResponse)
def criar_host(host: HostCreate, db: Session = Depends(get_db)):
    estado_ativo = ping_host(str(host.endereco_ip))

    novo_host = Host(
        nome=host.nome,
        endereco_ip=host.endereco_ip,
        descricao=host.descricao,
        tipo_host_id=host.tipo_host_id,
        ativo=estado_ativo,
    )

    db.add(novo_host)
    db.commit()
    db.refresh(novo_host)

    # Gerar alerta se host não responder ao ping
    if not estado_ativo:
        alerta = Alerta(
            host_id=novo_host.id,
            tipo_alerta="host_down",
            mensagem=f"Host {novo_host.nome} ({novo_host.endereco_ip}) não respondeu ao ping durante o registo",
        )
    db.add(alerta)

    return novo_host

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
    oids_selecionados: Optional[List[str]] = Form(None),
    db: Session = Depends(get_db),
):
    estado_ativo = ping_host(endereco_ip)

    novo_host = Host(
        nome=nome,
        endereco_ip=endereco_ip,
        descricao=descricao,
        tipo_host_id=tipo_host_id,
        ativo=estado_ativo,
    )

    db.add(novo_host)
    db.commit()
    db.refresh(novo_host)

    if not estado_ativo:
        alerta = Alerta(
            host_id=novo_host.id,
            tipo_alerta="host_down",
            mensagem=f"Host {novo_host.nome} ({novo_host.endereco_ip}) não respondeu ao ping durante o registo"
        )
        db.add(alerta)

    if usar_snmp == "on":
        if not versao_snmp or not comunidade:
            db.delete(novo_host)
            db.commit()
            raise HTTPException(
                status_code=400, detail="SNMP marcado, mas faltam campos obrigatórios."
            )

        configuracao_snmp = ConfiguracaoSNMP(
            host_id=novo_host.id,
            versao_snmp=versao_snmp,
            comunidade=comunidade,
            porta_snmp=porta_snmp,
            ativo=True,
        )
        db.add(configuracao_snmp)

        if oids_selecionados:
            for oid_valor in oids_selecionados:
                oid_info = next(
                    (o for o in OIDS_DISPONIVEIS if o["oid"] == oid_valor), None
                )
                if oid_info:
                    db.add(
                        OidSNMP(host_id=novo_host.id, nome=oid_info["nome"], oid=oid_valor)
                    )

    criar_associacoes_servicos(db, novo_host.id, servicos_ids)
    db.commit()

    try:
        scheduler.add_job(
            verificar_host_job,
            "interval",
            minutes=5,
            args=[novo_host.id],
            id=f"host_{novo_host.id}"
        )
    except:
        pass

    if usar_snmp == "on":
        try:
            scheduler.add_job(
                verificar_snmp_job,
                "interval",
                minutes=1,
                args=[novo_host.id],
                id=f"snmp_{novo_host.id}"
            )
        except:
            pass

    return RedirectResponse(url="/", status_code=303)

# EDITAR HOST
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
    oids_selecionados: Optional[List[str]] = Form(None),
    db: Session = Depends(get_db),
):
    # verificar se o host existe
    host = db.query(Host).filter(Host.id == host_id).first()

    if not host:
        raise HTTPException(status_code=404, detail="Host não encontrado")

    # atualizar estado com ping
    estado_ativo = ping_host(endereco_ip)

    host.nome = nome
    host.endereco_ip = endereco_ip
    host.descricao = descricao
    host.tipo_host_id = tipo_host_id
    host.ativo = estado_ativo

    # verificar configuração SNMP existente
    configuracao_snmp = (
        db.query(ConfiguracaoSNMP).filter(ConfiguracaoSNMP.host_id == host.id).first()
    )

    if usar_snmp == "on":
        if not versao_snmp or not comunidade:
            raise HTTPException(
                status_code=400, detail="SNMP marcado, mas faltam campos obrigatórios."
            )

        # atualizar ou criar configuração SNMP
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
                ativo=True,
            )
            db.add(configuracao_snmp)

        # substituir OIDs — apaga os antigos e insere os novos
        db.query(OidSNMP).filter(OidSNMP.host_id == host.id).delete()
        if oids_selecionados:
            for oid_valor in oids_selecionados:
                oid_info = next(
                    (o for o in OIDS_DISPONIVEIS if o["oid"] == oid_valor), None
                )
                if oid_info:
                    db.add(OidSNMP(host_id=host.id, nome=oid_info["nome"], oid=oid_valor))
    else:
        # remover configuração SNMP e OIDs se desativado
        if configuracao_snmp:
            db.delete(configuracao_snmp)
        db.query(OidSNMP).filter(OidSNMP.host_id == host.id).delete()

        # resolver alertas snmp_down existentes
        db.query(Alerta).filter(
            Alerta.host_id == host.id,
            Alerta.tipo_alerta == "snmp_down",
            Alerta.resolvido == False
        ).update({"resolvido": True})

    # atualizar serviços — mantém os existentes, apaga os desmarcados, adiciona os novos
    servicos_atuais = {
        hs.tipo_servico_id: hs
        for hs in db.query(HostServico).filter(HostServico.host_id == host.id).all()
    }
    novos_ids = set(servicos_ids) if servicos_ids else set()
    atuais_ids = set(servicos_atuais.keys())

    # apaga os serviços que foram desmarcados
    for tipo_id in atuais_ids - novos_ids:
        db.delete(servicos_atuais[tipo_id])

    # adiciona os serviços novos que foram marcados
    for tipo_id in novos_ids - atuais_ids:
        tipo = db.query(TipoServico).filter(TipoServico.id == tipo_id).first()
        if tipo:
            db.add(HostServico(
                host_id=host.id,
                tipo_servico_id=tipo.id,
                nome=tipo.nome,
                porta=tipo.porta_padrao,
                url=None,
                intervalo_verificacao_segundos=60,
                tempo_limite=5,
                ativo=True
            ))

    db.commit()
    
    # verificação imediata após editar
    verificar_host_job(host_id)
    for servico in db.query(HostServico).filter(HostServico.host_id == host_id).all():
        verificar_servico_job(servico.id)

    if usar_snmp == "on":
        verificar_snmp_job(host_id)

    # atualizar jobs do scheduler — remove os antigos e recria
    for job_id in [f"host_{host_id}", f"snmp_{host_id}"]:
        try:
            scheduler.remove_job(job_id)
        except:
            pass

    try:
        scheduler.add_job(
            verificar_host_job,
            "interval",
            minutes=5,
            args=[host_id],
            id=f"host_{host_id}"
        )
    except:
        pass

    if usar_snmp == "on":
        try:
            scheduler.add_job(
                verificar_snmp_job,
                "interval",
                minutes=1,
                args=[host_id],
                id=f"snmp_{host_id}"
            )
        except:
            pass

    return RedirectResponse(url="/", status_code=303)


#####################################
## ROTA PARA ELIMINAR HOST
######################################
@router.post("/form/{host_id}/eliminar")
def eliminar_host_form(host_id: int, db: Session = Depends(get_db)):
    host = db.query(Host).filter(Host.id == host_id).first()

    if not host:
        raise HTTPException(status_code=404, detail="Host não encontrado")

    db.delete(host)
    db.commit()

    return RedirectResponse(url="/", status_code=303)

#LISTAR HOSTS
@router.get("/", response_model=list[HostResponse])
def listar_hosts(db: Session = Depends(get_db)):
    return db.query(Host).all()


#####################################
## ROTA PARA MOSTRAR DETALHES DO HOST
######################################
@router.get("/{host_id}/detalhe")
def detalhe_host(host_id: int, request: Request, db: Session = Depends(get_db)):
    host = db.query(Host).filter(Host.id == host_id).first()

    if not host:
        raise HTTPException(status_code=404, detail="Host não encontrado")

    # ALERTAS ATIVOS
    alertas = (
        db.query(Alerta)
        .filter(Alerta.resolvido == False)
        .filter(
            (Alerta.host_id == host.id)
            | (Alerta.host_servico_id.in_([s.id for s in host.host_servicos]))
        )
        .all()
    )

    # HISTÓRICO (últimas 10 verificações)
    verificacoes = (
        db.query(Verificacao)
        .filter(
            (Verificacao.host_id == host.id)
            | (Verificacao.host_servico_id.in_([s.id for s in host.host_servicos]))
        )
        .order_by(Verificacao.data_verificacao.desc())
        .limit(10)
        .all()
    )

    # Última métrica de cada OID
    subquery = (
        db.query(
            MetricaSNMP.nome_metrica,
            func.max(MetricaSNMP.data_recolha).label("ultima")
        )
        .filter(MetricaSNMP.host_id == host_id)
        .group_by(MetricaSNMP.nome_metrica)
        .subquery()
    )

    metricas_snmp = (
        db.query(MetricaSNMP)
        .join(
            subquery,
            (MetricaSNMP.nome_metrica == subquery.c.nome_metrica)
            & (MetricaSNMP.data_recolha == subquery.c.ultima),
        )
        .filter(MetricaSNMP.host_id == host_id)
        .all()
    )

    return templates.TemplateResponse(
        request,
        "host_detalhe.html",
        {
            "host": host,
            "alertas": alertas,
            "verificacoes": verificacoes,
            "metricas_snmp": metricas_snmp,
        },
    )

# buscar host por id
@router.get("/{host_id}", response_model=HostResponse)
def buscar_host(host_id: int, db: Session = Depends(get_db)):
    host = db.query(Host).filter(Host.id == host_id).first()

    if not host:
        raise HTTPException(status_code=404, detail="Host não encontrado")

    return host


#####################################
## ROTA PARA ATUALIZAR HOST
######################################
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


# eliminar host
@router.delete("/{host_id}")
def eliminar_host(host_id: int, db: Session = Depends(get_db)):
    host = db.query(Host).filter(Host.id == host_id).first()

    if not host:
        raise HTTPException(status_code=404, detail="Host não encontrado")

    db.delete(host)
    db.commit()

    return {"mensagem": "Host eliminado com sucesso"}


#####################################
## ROTA PARA VERIFICAR HOST MANUALMENTE, BOTÃO
######################################
@router.post("/{host_id}/verificar")
def verificar_host_manual(
    host_id: int, request: Request, db: Session = Depends(get_db)
):
    host = db.query(Host).filter(Host.id == host_id).first()

    if not host:
        raise HTTPException(status_code=404, detail="Host não encontrado")

    verificar_host_job(host_id)

    referer = request.headers.get("referer", "/")
    return RedirectResponse(url=referer, status_code=303)


@router.post("/servico/{servico_id}/verificar")
def verificar_servico_manual(servico_id: int, db: Session = Depends(get_db)):

    servico = db.query(HostServico).filter(HostServico.id == servico_id).first()

    if not servico:
        raise HTTPException(status_code=404, detail="Serviço não encontrado")

    # usa a mesma lógica do scheduler
    verificar_servico_job(servico_id)

    return RedirectResponse(url=f"/hosts/{servico.host_id}/detalhe", status_code=303)



#####################################
## ROTA PARA EDITAR SERVIÇO DE UM HOST
######################################

@router.post("/servico/{servico_id}/editar")
def editar_servico(
    servico_id: int,
    porta: int = Form(None),
    url: str = Form(None),
    intervalo_verificacao_segundos: int = Form(60),
    tempo_limite: int = Form(5),
    db: Session = Depends(get_db)
):
    servico = db.query(HostServico).filter(HostServico.id == servico_id).first()

    if not servico:
        raise HTTPException(status_code=404, detail="Serviço não encontrado")

    servico.porta = porta
    servico.url = url
    servico.intervalo_verificacao_segundos = intervalo_verificacao_segundos
    servico.tempo_limite = tempo_limite

    db.commit()

    # atualiza o job do scheduler com o novo intervalo
    try:
        scheduler.remove_job(f"servico_{servico_id}")
    except:
        pass

    try:
        scheduler.add_job(
            verificar_servico_job,
            "interval",
            seconds=intervalo_verificacao_segundos,
            args=[servico_id],
            id=f"servico_{servico_id}"
        )
    except:
        pass

    return RedirectResponse(url=f"/hosts/{servico.host_id}/detalhe", status_code=303)


#####################################
## ROTA PARA ELIMINAR SERVIÇO DE UM HOST, BOTÃO
######################################
@router.post("/servico/{servico_id}/remover")
def remover_servico(servico_id: int, db: Session = Depends(get_db)):
    servico = db.query(HostServico).filter(HostServico.id == servico_id).first()

    if not servico:
        raise HTTPException(status_code=404, detail="Serviço não encontrado")

    host_id = servico.host_id

    # remove job do scheduler
    try:
        scheduler.remove_job(f"servico_{servico_id}")
    except:
        pass

    db.delete(servico)
    db.commit()

    return RedirectResponse(url=f"/hosts/{host_id}/detalhe", status_code=303)

#####################################
## ROTA PARA Obter metrica SNMP chamar scheduler, BOTÃO
@router.post("/{host_id}/snmp/verificar")
def verificar_snmp_manual(host_id: int, request: Request, db: Session = Depends(get_db)):
    host = db.query(Host).filter(Host.id == host_id).first()

    if not host:
        raise HTTPException(status_code=404, detail="Host não encontrado")

    verificar_snmp_job(host_id)

    referer = request.headers.get("referer", "/")
    return RedirectResponse(url=referer, status_code=303)

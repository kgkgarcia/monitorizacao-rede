from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.host import Host
from app.models.host_servico import HostServico
from app.models.verificacao import Verificacao
from app.models.alerta import Alerta

from app.checks.ssh_check import verificar_ssh
from app.checks.http_check import verificar_http

import platform
import subprocess


scheduler = BackgroundScheduler()


# -------------------------
# PING HOST
# -------------------------
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


# -------------------------
# JOB HOST
# -------------------------
def verificar_host_job(host_id: int):
    db: Session = SessionLocal()

    try:
        host = db.query(Host).get(host_id)

        if not host:
            return

        estado = ping_host(str(host.endereco_ip))
        host.ativo = estado

        db.commit()

    except Exception as e:
        print("Erro host:", e)
    finally:
        db.close()


# -------------------------
# JOB SERVIÇO
# -------------------------
def verificar_servico_job(servico_id: int):
    db: Session = SessionLocal()

    try:
        servico = db.query(HostServico).get(servico_id)

        if not servico or not servico.ativo:
            return

        host_ip = str(servico.host.endereco_ip)
        tipo = servico.tipo_servico.nome.strip().lower()

        # -------------------------
        # ESCOLHER CHECK
        # -------------------------
        if tipo == "ssh":
            resultado = verificar_ssh(
                host_ip,
                servico.porta or 22,
                servico.tempo_limite
            )

        elif tipo == "http":
            url = servico.url or f"http://{host_ip}:{servico.porta or 80}"

            resultado = verificar_http(
                url,
                servico.tempo_limite
            )

        else:
            return

        # -------------------------
        # ATUALIZAR ESTADO
        # -------------------------
        servico.estado_atual = resultado["sucesso"]

        # -------------------------
        # GUARDAR VERIFICAÇÃO
        # -------------------------
        verificacao = Verificacao(
            host_servico_id=servico.id,
            metodo_verificacao="automatico",
            estado="sucesso" if resultado["sucesso"] else "falha",
            tempo_resposta_ms=resultado["tempo_resposta"],
            mensagem_erro=resultado["mensagem"]
        )

        db.add(verificacao)

        # -------------------------
        # ALERTAS
        # -------------------------
        if not resultado["sucesso"]:

            alerta_existente = db.query(Alerta).filter(
                Alerta.host_servico_id == servico.id,
                Alerta.resolvido == False
            ).first()

            if not alerta_existente:
                alerta = Alerta(
                    host_servico_id=servico.id,
                    tipo_alerta="servico_down",
                    mensagem=f"Serviço {servico.nome} está DOWN"
                )
                db.add(alerta)

        else:
            alerta_existente = db.query(Alerta).filter(
                Alerta.host_servico_id == servico.id,
                Alerta.resolvido == False
            ).first()

            if alerta_existente:
                alerta_existente.resolvido = True

        db.commit()

    except Exception as e:
        print("Erro serviço:", e)

    finally:
        db.close()


# -------------------------
# INICIAR SCHEDULER
# -------------------------
def iniciar_scheduler():

    if scheduler.running:
        return

    db: Session = SessionLocal()

    try:
        # -------------------------
        # JOBS HOST
        # -------------------------
        hosts = db.query(Host).all()

        for host in hosts:
            scheduler.add_job(
                verificar_host_job,
                "interval",
                minutes=5,
                args=[host.id],
                id=f"host_{host.id}"
            )

        # -------------------------
        # JOBS SERVIÇOS
        # -------------------------
        servicos = db.query(HostServico).all()

        for servico in servicos:
            scheduler.add_job(
                verificar_servico_job,
                "interval",
                seconds=servico.intervalo_verificacao_segundos,
                args=[servico.id],
                id=f"servico_{servico.id}"
            )

    finally:
        db.close()

    scheduler.start()
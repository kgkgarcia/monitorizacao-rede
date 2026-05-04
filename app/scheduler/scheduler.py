from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.host import Host

import platform
import subprocess


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


def verificar_hosts():
    print("🔄 A verificar estado dos hosts...")

    db: Session = SessionLocal()

    try:
        hosts = db.query(Host).all()

        for host in hosts:
            estado = ping_host(str(host.endereco_ip))
            host.ativo = estado

        db.commit()

    except Exception as e:
        print("Erro no scheduler:", e)
    finally:
        db.close()


scheduler = BackgroundScheduler()

def iniciar_scheduler():
    scheduler.add_job(
        verificar_hosts,
        "interval",
        minutes=5  # intervalo de 5 minutos
    )

    scheduler.start()
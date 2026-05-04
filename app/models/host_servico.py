from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy import text

from app.database import Base


class HostServico(Base):
    __tablename__ = "host_servicos"

    id = Column(Integer, primary_key=True, index=True)
    host_id = Column(Integer, ForeignKey("hosts.id", ondelete="CASCADE"), nullable=False)
    tipo_servico_id = Column(Integer, ForeignKey("tipos_servico.id", ondelete="RESTRICT"), nullable=False)
    nome = Column(String(100), nullable=True)
    porta = Column(Integer, nullable=True)
    url = Column(Text, nullable=True)
    intervalo_verificacao_segundos = Column(Integer, nullable=False)
    tempo_limite = Column(Integer, nullable=False)
    ativo = Column(Boolean, nullable=False, server_default=text("true"))
    estado_atual = Column(Boolean, nullable=True)
    data_criacao = Column(DateTime, nullable=False, server_default=func.now())

    host = relationship("Host", back_populates="host_servicos")
    tipo_servico = relationship("TipoServico", back_populates="host_servicos")
    verificacoes = relationship("Verificacao", back_populates="host_servico", cascade="all, delete-orphan")
    alertas = relationship("Alerta", back_populates="host_servico", cascade="all, delete-orphan")
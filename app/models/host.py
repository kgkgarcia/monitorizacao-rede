from sqlalchemy import Column, Integer, String, Boolean, Text, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import INET
from sqlalchemy.orm import relationship

from app.database import Base


class Host(Base):
    __tablename__ = "hosts"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable=False)
    endereco_ip = Column(INET, nullable=False)
    descricao = Column(Text, nullable=True)
    tipo_host_id = Column(Integer, ForeignKey("tipos_host.id", ondelete="RESTRICT"), nullable=False)
    ativo = Column(Boolean, nullable=False, default=False)
    data_criacao = Column(DateTime, nullable=False, server_default=func.now())

    tipo_host = relationship("TipoHost", back_populates="hosts")
    host_servicos = relationship("HostServico", back_populates="host", cascade="all, delete-orphan")
    configuracao_snmp = relationship("ConfiguracaoSNMP", back_populates="host", uselist=False, cascade="all, delete-orphan")
    metricas_snmp = relationship("MetricaSNMP", back_populates="host", cascade="all, delete-orphan")
    verificacoes = relationship("Verificacao", back_populates="host", cascade="all, delete-orphan")
    alertas = relationship("Alerta", back_populates="host", cascade="all, delete-orphan")
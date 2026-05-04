from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database import Base


class MetricaSNMP(Base):
    __tablename__ = "metricas_snmp"

    id = Column(Integer, primary_key=True, index=True)
    host_id = Column(Integer, ForeignKey("hosts.id", ondelete="CASCADE"), nullable=False)
    nome_metrica = Column(String(100), nullable=False)
    oid = Column(String(100), nullable=False)
    valor = Column(Text, nullable=False)
    data_recolha = Column(DateTime, nullable=False, server_default=func.now())

    host = relationship("Host", back_populates="metricas_snmp")
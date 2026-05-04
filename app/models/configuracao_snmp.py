from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


class ConfiguracaoSNMP(Base):
    __tablename__ = "configuracoes_snmp"

    id = Column(Integer, primary_key=True, index=True)
    host_id = Column(Integer, ForeignKey("hosts.id", ondelete="CASCADE"), nullable=False, unique=True)
    versao_snmp = Column(String(10), nullable=False)
    comunidade = Column(String(100), nullable=False)
    porta_snmp = Column(Integer, nullable=False, default=161)
    ativo = Column(Boolean, nullable=False, default=True)

    host = relationship("Host", back_populates="configuracao_snmp")
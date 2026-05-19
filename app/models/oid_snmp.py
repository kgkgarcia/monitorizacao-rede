from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


class OidSNMP(Base):
    __tablename__ = "oids_snmp"

    id = Column(Integer, primary_key=True, index=True)
    host_id = Column(Integer, ForeignKey("hosts.id", ondelete="CASCADE"), nullable=False)
    nome = Column(String(100), nullable=False)
    oid = Column(String(100), nullable=False)
    ativo = Column(Boolean, nullable=False, default=True)

    host = relationship("Host", back_populates="oids_snmp")
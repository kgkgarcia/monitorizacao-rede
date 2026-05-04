from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, DateTime, CheckConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database import Base


class Alerta(Base):
    __tablename__ = "alertas"

    id = Column(Integer, primary_key=True, index=True)
    host_id = Column(Integer, ForeignKey("hosts.id", ondelete="CASCADE"), nullable=True)
    host_servico_id = Column(Integer, ForeignKey("host_servicos.id", ondelete="CASCADE"), nullable=True)
    tipo_alerta = Column(String(50), nullable=False)
    mensagem = Column(Text, nullable=False)
    resolvido = Column(Boolean, nullable=False, default=False)
    data_criacao = Column(DateTime, nullable=False, server_default=func.now())

    __table_args__ = (
        CheckConstraint(
            "(host_id IS NOT NULL AND host_servico_id IS NULL) OR "
            "(host_id IS NULL AND host_servico_id IS NOT NULL)",
            name="chk_alertas_alvo"
        ),
    )

    host = relationship("Host", back_populates="alertas")
    host_servico = relationship("HostServico", back_populates="alertas")
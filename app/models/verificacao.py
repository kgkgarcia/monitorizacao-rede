from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, CheckConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database import Base


class Verificacao(Base):
    __tablename__ = "verificacoes"

    id = Column(Integer, primary_key=True, index=True)
    host_id = Column(Integer, ForeignKey("hosts.id", ondelete="CASCADE"), nullable=True)
    host_servico_id = Column(Integer, ForeignKey("host_servicos.id", ondelete="CASCADE"), nullable=True)
    metodo_verificacao = Column(String(30), nullable=False)
    estado = Column(String(20), nullable=False)
    tempo_resposta_ms = Column(Integer, nullable=True)
    mensagem_erro = Column(Text, nullable=True)
    data_verificacao = Column(DateTime, nullable=False, server_default=func.now())

    __table_args__ = (
        CheckConstraint(
            "(host_id IS NOT NULL AND host_servico_id IS NULL) OR "
            "(host_id IS NULL AND host_servico_id IS NOT NULL)",
            name="chk_verificacoes_alvo"
        ),
        CheckConstraint(
            "estado IN ('sucesso', 'falha')",
            name="chk_verificacoes_estado"
        ),
    )

    host = relationship("Host", back_populates="verificacoes")
    host_servico = relationship("HostServico", back_populates="verificacoes")
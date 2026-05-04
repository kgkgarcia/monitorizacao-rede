from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class TipoServico(Base):
    __tablename__ = "tipos_servico"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(50), nullable=False, unique=True)
    protocolo = Column(String(20), nullable=False)
    porta_padrao = Column(Integer, nullable=True)
    descricao = Column(Text, nullable=True)

    host_servicos = relationship("HostServico", back_populates="tipo_servico")
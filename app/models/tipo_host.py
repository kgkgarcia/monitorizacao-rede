from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


class TipoHost(Base):
    __tablename__ = "tipos_host"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(50), nullable=False, unique=True)

    hosts = relationship("Host", back_populates="tipo_host")
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from app.schemas.configuracao_snmp import ConfiguracaoSNMPResponse


class HostBase(BaseModel):
    nome: str
    endereco_ip: str
    descricao: Optional[str] = None
    tipo_host_id: int


class HostCreate(HostBase):
    pass


class HostUpdate(BaseModel):
    nome: str
    endereco_ip: str
    descricao: Optional[str] = None
    tipo_host_id: int
    ativo: bool


class HostResponse(HostBase):
    id: int
    ativo: bool
    data_criacao: datetime
    configuracao_snmp: Optional[ConfiguracaoSNMPResponse] = None

    class Config:
        from_attributes = True
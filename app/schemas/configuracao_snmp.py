from pydantic import BaseModel


class ConfiguracaoSNMPBase(BaseModel):
    versao_snmp: str
    comunidade: str
    porta_snmp: int = 161
    ativo: bool = True


class ConfiguracaoSNMPCreate(ConfiguracaoSNMPBase):
    host_id: int


class ConfiguracaoSNMPUpdate(BaseModel):
    versao_snmp: str
    comunidade: str
    porta_snmp: int
    ativo: bool


class ConfiguracaoSNMPResponse(ConfiguracaoSNMPBase):
    id: int
    host_id: int

    class Config:
        from_attributes = True
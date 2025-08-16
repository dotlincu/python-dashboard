from sqlmodel import SQLModel, Field
# from pydantic import PositiveInt


class Categoria(SQLModel, table=True):
    cod_categoria: str = Field(primary_key=True)
    categoria: str
    cod_dre: int

class Lancamentos(SQLModel, table=True):
    id: int = Field(primary_key=True)
    cod_categoria: str
    grupo: str
    natureza: str
    status: str
    data_pagamento: str
    cod_conta: int
    cod_cliente: float
    valor: str

class DRE(SQLModel, table=True):
    cod_dre: int = Field(primary_key=True)
    descricao: str
    operacao: str
    tipo: str

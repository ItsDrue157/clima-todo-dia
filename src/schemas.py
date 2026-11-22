from typing import Literal
from pydantic import BaseModel, Field

class AlarmeClimaSchema(BaseModel):
    cidades: list[str] = Field(
        description="Lista de cidades ou municipios mencionados na mensagem."
    )
    duracao: int = Field(
        default=1, 
        description="Duracao do alarme em dias. Se nao especificado, o padrao e 1."
    )
    recorrente: bool = Field(
        default=False,
        description="True se o usuario indicar que quer receber o aviso sempre ou todos os dias."
    )
    tipo_gatilho: Literal["chuva", "temperatura_maxima", "temperatura_minima", "vento"] = Field(
        description="Metrica climatica do alarme."
    )
    operador: Literal[">", "<"] = Field(
        description="Operador logico. '>' para maior que, '<' para menor que."
    )
    valor_limiar: float = Field(
        description="O valor numerico do limite estabelecido pelo usuario."
    )
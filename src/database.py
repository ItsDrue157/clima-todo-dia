from sqlalchemy.orm import Session
from models import Lembrete
from schemas import LembreteExtraidoSchema

def salvar_lembrete_usuario(session: Session, chat_id: int, dados_ia: LembreteExtraidoSchema):
    # Juntamos os três campos da IA em uma única string estruturada para a sua coluna condicao
    # Exemplo resultante: "temperatura_maxima > 35.0" ou "chuva > 0.0"
    string_condicao = f"{dados_ia.tipo_gatilho} {dados_ia.operador} {dados_ia.valor_limiar}"
    
    # Instanciamos o seu modelo usando a sintaxe moderna do SQLAlchemy 2.0
    novo_lembrete = Lembrete(
        chat_id_database=chat_id,
        cidades=dados_ia.cidades,
        duracao=dados_ia.duracao,
        recorrente=dados_ia.recorrente,
        condicao=string_condicao
    )
    
    # Salva no banco de dados public
    session.add(novo_lembrete)
    session.commit()
    session.refresh(novo_lembrete)
    
    return novo_lembrete
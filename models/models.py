import os
from sqlalchemy import create_engine, Table, Column, MetaData, Integer, Computed, Boolean, String, ARRAY, BigInteger
from sqlalchemy.orm import declarative_base, sessionmaker, Mapped, mapped_column
from typing import Literal
from pydantic import BaseModel, Field
from chat_id import pegar_chat_id

# Configuração do banco
engine = create_engine(os.getenv('DATABASE_URL'))
Base = declarative_base()
Sessao = sessionmaker(bind=engine)

def init_db():
    """Inicializa o banco de dados, criando tabelas se não existirem."""
    Base.metadata.create_all(engine)
    return True

class Usuario(Base):
    __tablename__ = 'usuarios'
    __table_args__ = {'schema': 'public'}

    id: Mapped[int] = mapped_column(primary_key=True)
    chat_id_database: Mapped[int] = mapped_column(BigInteger)
    lista_cidades: Mapped[list[str]] = mapped_column(ARRAY(String))

class Lembrete(Base):
    __tablename__ = 'lembretes'
    __table_args__ = {'schema': 'public'}
    id: Mapped[int] = mapped_column(primary_key=True)
    chat_id_database: Mapped[int] = mapped_column(BigInteger)
    cidades: Mapped[str] = mapped_column(ARRAY(String))
    duracao: Mapped[int] = mapped_column(Integer)
    recorrente: Mapped[bool] = mapped_column(Boolean)
    condicao: Mapped[str] = mapped_column(String)
    
def salvar_usuario(chat_id, lista_cidades):
    
    """Salva ou atualiza um usuário com chat_id e lista de cidades."""
    if lista_cidades is None:
        lista_cidades = []
    with Sessao() as sessao:
        try:
            # Verifica se o usuário já existe
            usuario = sessao.query(Usuario).filter_by(chat_id_database=chat_id).first()
            if usuario:
                usuario.lista_cidades = lista_cidades
            else:
                novo_usuario = Usuario(chat_id_database=chat_id, lista_cidades=lista_cidades)
                sessao.add(novo_usuario)
            sessao.commit()
        except Exception as e:
            sessao.rollback()
            raise e




#CRUD simples
def pegar_cidades(chat_id):
    """Retorna a lista de cidades de um usuário pelo chat_id, ou lista vazia se não encontrado."""
    with Sessao() as sessao:
        usuario = sessao.query(Usuario).filter_by(chat_id_database=chat_id).first()
        if usuario:
            return usuario.lista_cidades
        return []
def adicionar_cidade(chat_id,cidade_adicionada):
    with Sessao() as sessao:
        usuario = sessao.query(Usuario).filter_by(chat_id_database = chat_id).first()
        if usuario:
            if cidade_adicionada not in usuario.lista_cidades:
                lista_antiga = usuario.lista_cidades
                lista_nova = lista_antiga + [cidade_adicionada] 
                usuario.lista_cidades = lista_nova
                sessao.commit()
                return True
            elif cidade_adicionada in usuario.lista_cidades:
                return False
def remover_cidade(chat_id, cidade_removida):
    with Sessao() as sessao:
        usuario = sessao.query(Usuario).filter_by(chat_id_database=chat_id).first()
        if usuario:
            if cidade_removida in usuario.lista_cidades:
                # Criamos uma lista NOVA filtrando a cidade que queremos remover
                usuario.lista_cidades = [cidade for cidade in usuario.lista_cidades if cidade != cidade_removida]
                
                sessao.commit()
                return True
            elif cidade_removida not in usuario.lista_cidades:
                return False
def salvar_lembrete(chat_id, cidades, condicao, duracao, recorrente):
    if cidades is None:
        cidades = []
        
    with Sessao() as sessao:
        # Buscamos se já existe um alarme exatamente igual para este chat_id
        # (Mesmas cidades, mesma condição e mesma duração)
        alarme_duplicado = sessao.query(Lembrete).filter_by(
            chat_id_database=chat_id,
            condicao=condicao,
            duracao=duracao,
            cidades=cidades
        ).first()
        
        # Se o alarme for idêntico, evitamos a duplicidade e retornamos False
        if alarme_duplicado:
            return False
            
        # Se não for duplicado, criamos um novo registro no banco.
        # Note que passamos 'cidades' direto, sem os colchetes [], pois a IA já entrega uma lista.
        novo_lembrete = Lembrete(
            chat_id_database=chat_id,
            cidades=cidades,
            condicao=condicao,
            duracao=duracao,
            recorrente=recorrente
        )
        
        sessao.add(novo_lembrete)
        sessao.commit()
        return True


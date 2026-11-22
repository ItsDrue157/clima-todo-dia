import logging
from pathlib import Path
import sys
from telegram import Update
from telegram.ext import ContextTypes

base_path = Path(__file__).resolve().parent
root_path = base_path.parent
if str(root_path) not in sys.path:
    sys.path.insert(0, str(root_path))

# Mantemos a sua função original de salvar no banco
from models.models import salvar_lembrete
# Importamos o serviço da IA que criamos nos passos anteriores
from ai_service import analisar_mensagem_lembrete

async def criar_alarme_com_ia(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handler único que substitui toda a cascata antiga.
    Captura a frase completa do usuário após o comando /alarme.
    """
    # Junta todos os argumentos enviados após o comando /alarme em uma única string
    # Exemplo: /alarme avisar se fizer mais de 35 graus em Itaguaí e no Rio amanhã
    texto_usuario = " ".join(context.args)
    
    if not texto_usuario:
        await update.message.reply_text(
            "Por favor, digite a configuração do alarme após o comando.\n\n"
            "Exemplos:\n"
            "  /alarme Avisar se chover em Itaguaí nos próximos 2 dias\n"
            "  /alarme Alerta se a temperatura passar de 38 graus no Rio de Janeiro"
        )
        return

    # Envia um feedback visual rápido para o usuário saber que o bot está processando
    mensagem_aguarde = await update.message.reply_text("Processando seu pedido com Inteligência Artificial...")

    try:
        # 1. Envia o texto puro para o Gemini e recebe o objeto Pydantic validado
        dados_ia = analisar_mensagem_lembrete(texto_usuario)
        
        # 2. Monta a string de condição unificada que a sua tabela espera receber
        # Exemplo resultante: "temperatura_maxima > 35.0" ou "chuva > 0.0"
        string_condicao = f"{dados_ia.tipo_gatilho} {dados_ia.operador} {dados_ia.valor_limiar}"
        
        # 3. Salva no banco de dados usando a sua função atual
        # Note que passamos dados_ia.cidades, que já é a lista/ARRAY tratada pela IA
        salvar_lembrete(
            chat_id=update.effective_chat.id,
            cidades=dados_ia.cidades,
            condicao=string_condicao,
            duracao=int(dados_ia.duracao),
            recorrente=dados_ia.recorrente
        )
        
        # 4. Formata uma resposta limpa confirmando o que a IA interpretou
        cidades_formatadas = ", ".join(dados_ia.cidades)
        resposta_sucesso = (
            f"Alarme configurado com sucesso!\n\n"
            f"Locais: {cidades_formatadas}\n"
            f"Condição: {string_condicao}\n"
            f"Duração: {dados_ia.duracao} dia(s)\n"
            f"Recorrente: {'Sim' if dados_ia.recorrente else 'Não'}"
        )
        
        # Atualiza a mensagem de espera com o resultado final
        await mensagem_aguarde.edit_text(resposta_sucesso)

    except Exception as e:
        logging.error(f"Erro ao processar alarme com IA: {e}")
        await mensagem_aguarde.edit_text(
            "Não consegui extrair os dados necessários. "
            "Tente ser mais claro informando a cidade e a condição climática desejada."
        )
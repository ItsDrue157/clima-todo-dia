import datetime
import logging
from main import get_loc_city
from uv_index import uv_index
from wind_direction import calcularDirecaoDoVento
from pydantic import BaseModel, Field
from google import genai
from google.genai import types
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import httpx


logging.basicConfig(level=logging.INFO)



class AlarmeClimaSchema(BaseModel):
    cidade: str = Field(description="Nome da cidade identificada na mensagem")
    condicao: str = Field(description="Condicao climatica a ser monitorada (ex: chuva, calor, vento)")
    data_hora: datetime.datetime = Field(description="Data e hora exata calculada para o disparo do alarme")




scheduler = AsyncIOScheduler()
scheduler.start()








async def get_clima(cidade):
    latitude, longitude = await get_loc_city(cidade)

    if latitude is None or longitude is None:
        return None
    
    async with httpx.AsyncClient(http2=False) as client:
        url = f'https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&hourly=&current=temperature_2m,relative_humidity_2m,wind_speed_10m,wind_direction_10m&timezone=auto&forecast_days=1&daily=temperature_2m_max,temperature_2m_min,uv_index_max,precipitation_probability_max'
        data = await client.get(url)
        conteudo = data.json()
        
        weather = conteudo['current']['temperature_2m']
        humidity = conteudo['current']['relative_humidity_2m']
        chance_chuva = conteudo['daily']['precipitation_probability_max'][0]
        raios_uv_max = conteudo['daily']['uv_index_max'][0]
        direcaoDoVento = conteudo['current']['wind_direction_10m']
        temperatura_maxima = conteudo['daily']['temperature_2m_max'][0]
        temperatura_minima = conteudo['daily']['temperature_2m_min'][0]

        return {
            "temperatura": weather, 
            "humidade": humidity, 
            "direcao_vento": calcularDirecaoDoVento(direcaoDoVento),
            "chuva": chance_chuva,
            "temperatura_maxima": temperatura_maxima,
            "temperatura_minima": temperatura_minima,
            "uv_index": uv_index(raios_uv_max)
        }

async def disparar_alarme_job(id_telegram: int, cidade: str, condicao_alvo: str, estilo_mensagem: str, bot_context):
    """
    Funcao executada pelo APScheduler no momento exato do alarme.
    """
    dados_clima = await get_clima(cidade)
    
    if dados_clima is None:
        logging.error(f"Falha ao buscar clima para {cidade}. Alarme do usuario {id_telegram} nao disparado.")
        await bot_context.bot.send_message(
            chat_id=id_telegram,
            text="Nao consegui checar o clima agora por uma falha de conexao com o serviço meteorológico."
        )
        return

    client = genai.Client()
    
    prompt = f"""
    Voce eh um assistente meteorologico encarregado de enviar um alerta personalizado.
    O usuario configurou este alarme para a cidade: {cidade}.
    Ele queria monitorar especificamente a condicao: {condicao_alvo}.
    
    Dados reais obtidos agora da API Open-Meteo:
    {dados_clima}
    
    Gere um texto de alerta focado em dizer se a condicao esperada foi atingida e trazendo os dados relevantes.
    Estilo da mensagem: {estilo_mensagem}
    """
    
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    
    # Envia a mensagem gerada pela IA direto para o chat do Telegram do usuário
    await bot_context.bot.send_message(chat_id=id_telegram, text=response.text)



def analisar_mensagem_lembrete(texto_usuario: str) -> AlarmeClimaSchema:
    """
    Usa o Gemini para extrair as entidades e transformar em dados estruturados.
    """
    client = genai.Client()
    
    # Passamos a hora exata de agora para a IA saber calcular termos como "amanha"
    data_atual_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    prompt = f"""
    Você é um assistente meteorológico encarregado de configurar alarmes climáticos.
    Extraia as informações necessárias da seguinte mensagem do usuário.
    
    Data e hora atual de referência: {data_atual_str}
    Mensagem do usuário: "{texto_usuario}"
    """
    
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=AlarmeClimaSchema,
            temperature=0.1,
        ),
    )
    
    return response.parsed


async def comando_definir_alarme(update, context):
    """
    Handler principal do comando do Telegram do seu Bot.
    """
    id_telegram = update.effective_user.id
    texto_usuario = update.message.text
    
    try:
        # Extrai os dados estruturados via IA
        dados_alarme = analisar_mensagem_lembrete(texto_usuario)
        
        # Agendamento na fila de tarefas (Job Queue)
        scheduler.add_job(
            disparar_alarme_job,
            'date',
            run_date=dados_alarme.data_hora,
            args=[id_telegram, dados_alarme.cidade, dados_alarme.condicao, "informativo_com_emojis", context]
        )
        
        data_formatada = dados_alarme.data_hora.strftime("%d/%m/%Y as %H:%M")
        await update.message.reply_text(
            f"Alarme agendado! Vou checar o clima em {dados_alarme.cidade} no dia {data_formatada}."
        )
        
    except Exception as e:
        logging.info(f"Alarme agendado com sucesso para {dados_alarme.cidade} em {data_formatada}. Chat ID: {id_telegram}")
        data_formatada = dados_alarme.data_hora.strftime("%d/%m/%Y as %H:%M")
        await update.message.reply_text(
            f"Alarme agendado! Vou checar o clima em {dados_alarme.cidade} no dia {data_formatada}."
        )
        
    except Exception as e:
        logging.error(f"Erro ao processar ou agendar o alarme para o chat ID {id_telegram}: {e}", exc_info=True)
        await update.message.reply_text(
            "Não consegui extrair as informações de data ou local. Tente enviar de forma clara, ex: 'Me avise se vai chover no Rio amanhã as 14h'."
        )

if __name__ == '__main__':
    # Garante que o scheduler está rodando se o arquivo for executado diretamente
    if not scheduler.running:
        scheduler.start()
        logging.info("APScheduler iniciado no bloco principal.")
    try:
        # Aqui você pode adicionar lógica para manter o script rodando
        # Por exemplo, usar asyncio.Event().wait() em um loop principal do bot
        logging.info("Scheduler está pronto para agendar tarefas.")
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        logging.info("APScheduler desligado.")
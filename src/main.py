import logging
import httpx
import os
import sys
from telegram.ext import ApplicationBuilder
from telegram.request import HTTPXRequest
from pathlib import Path
from dotenv import load_dotenv
from telegram.ext import filters, MessageHandler, ApplicationBuilder, ContextTypes, CommandHandler,ConversationHandler
from telegram import Update
from wind_direction import calcularDirecaoDoVento
from uv_index import uv_index
#from chat_id import pegar_chat_id
from handler import *


base_path = Path(__file__).resolve().parent
root_path = base_path.parent
if str(root_path) not in sys.path:
    sys.path.insert(0, str(root_path))
from models.models import salvar_usuario, pegar_cidades, init_db, adicionar_cidade, remover_cidade

print("TESTE 123")

 
env_path = base_path.parent / 'config' / '.env'

load_dotenv(dotenv_path=env_path)
telegram_api_token = os.getenv("token_telegram")
api_gemini = os.getenv("GEMINI_API_KEY")

#processamento 1
async def get_loc_city(cidade):
    async with httpx.AsyncClient(http2=False) as client:
        url = f'https://geocoding-api.open-meteo.com/v1/search?name={cidade}&count=1&language=pt&format=json'
        data = await client.get(url)
        conteudo = data.json()
        if 'results' in conteudo:
            latitude = conteudo['results'][0]['latitude']
            longitude = conteudo['results'][0]['longitude']
            return latitude, longitude
        else:
            
            return (None, None)


        

#processamento 2
async def get_clima(cidade):
    latitude, longitude = await get_loc_city(cidade)

    if latitude is None or longitude is None:
        return None
    
    async with httpx.AsyncClient(http2=False) as client:
        
        url = f'https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&hourly=&current=temperature_2m,relative_humidity_2m,wind_speed_10m,wind_direction_10m&timezone=auto&forecast_days=1&daily=temperature_2m_max,temperature_2m_min,uv_index_max,precipitation_probability_max'
        data = await client.get(url)
        conteudo = data.json()
        weather =            conteudo['current']['temperature_2m']
        humidity =           conteudo['current']['relative_humidity_2m']
        chance_chuva =       conteudo['daily']['precipitation_probability_max'][0]
        raios_uv_max =       conteudo['daily']['uv_index_max'][0]
        direcaoDoVento =     conteudo['current']['wind_direction_10m']
        temperatura_maxima = conteudo['daily']['temperature_2m_max'][0]
        temperatura_minima = conteudo['daily']['temperature_2m_min'][0]

        return {"temperatura":weather, 
                "humidade": humidity, 
                "direcao_vento": calcularDirecaoDoVento(direcaoDoVento),
                "chuva": chance_chuva,
                "temperatura_maxima": temperatura_maxima,
                "temperatura_minima": temperatura_minima,
                "uv_index": uv_index(raios_uv_max),
                "cidade": cidade
                }

#LOGGING CONFIG
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.FileHandler("/app/config/records/logs.log"),
        #descommentar a frase acima sempre antes de mandar para a vps
        logging.StreamHandler() # Isso faz aparecer no docker logs -f
    ]
)

#                               FUNÇOES

#                               funcao para mostar comandos
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id,text=f'''Olá, seja bem-vindo ao ClimApp, seu app que faz consultas em tempo real do clima. Para começar, digite /clima + "nome da cidade" obs: sem aspas.\n Por favor, faça seu cadastro para isso, digite: /cadastro + uma cidade de preferencia. Ex: /cadastro Rio de Janeiro''')

#                               funcao para mostrar as info da cidade 
async def getting_info_from_city(update: Update, context:ContextTypes.DEFAULT_TYPE):
    args = context.args
    cidade = ' '.join(args)
    
    latitude= await get_loc_city(cidade)
    
    if latitude [0] is None:
        logging.warning(f"Falha na busca: A cidade: {cidade} não foi encontrada")
        await update.message.reply_text(f'A cidade: {cidade}, não foi achada. Por Favor tente novamente')
        return
    else: 
        await update.message.reply_text(f'buscando clima da cidade: {cidade}.')
        clima_pego = await get_clima(cidade)
        await context.bot.send_message(chat_id=update.effective_chat.id, 
        text=f'''
        O clima atual na cidade {cidade} é de {clima_pego["temperatura"]}°C,
        a máxima: {clima_pego["temperatura_maxima"]}°C e a mínima {clima_pego["temperatura_minima"]}°C estão previstas para hoje
        a humidade está em: {clima_pego["humidade"]}%,
        a direção do vento está para: {clima_pego["direcao_vento"]}
        a chance de chuva está em: {clima_pego["chuva"]}%
        e o indíce de raio uv: {clima_pego["uv_index"]}
        ''')
#                               funcao para cadastrar o id e a cidade prefererida
async def cadastro(update:Update, context:ContextTypes.DEFAULT_TYPE):
    escolha_de_cidades = context.args
    lista_cidades = ' '.join(escolha_de_cidades)
    chat_id = update.effective_chat.id
    if chat_id == False:
        logging.warning('Não foi possivel estabelecer conexão. ')
        await update.message.reply_text('Por favor tente novamente, pois nosso sistema encontrou uma falha inesperada. ')
    elif chat_id:
        if lista_cidades:
            await update.message.reply_text(f'Voce ja possue uma lista com cidades')
            return

        salvar_usuario(chat_id, [lista_cidades])
        logging.info(f'o chat id: {chat_id} e a cidade {lista_cidades} foram adicionadas no banco de dados com sucesso.')
        await update.message.reply_text(f'Sua cidade: {lista_cidades}, foi adicionada com sucesso. ')
    
    else:
        return

#                               funcoa para mostrar as cidades cadastradas
async def mostrar_lista_cidades(update: Update, context:ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    lista_cidades = pegar_cidades(chat_id) 
    if lista_cidades == []:
        logging.error(f'O usuario {chat_id}, não fez ainda uma lista de cidade.')
        return await update.message.reply_text(f'Nenhuma cidade adicionada, por favor use o /start.')
    elif lista_cidades:
        texto_cidades = ",\n".join(lista_cidades)
        await update.message.reply_text(f'Suas cidades: {texto_cidades}\n')
        logging.info(f'Mostrando a cidade do chat_id {chat_id}.')
    else:
        logging.error(f'erro na hora de mostrar as cidades do usuaario {chat_id}')

#                               funcao para adicionar cidades no banco de dados
async def adicionar_no_banco_cidade(update: Update, context:ContextTypes.DEFAULT_TYPE):
    cidade_adicionada_no_banco = context.args
    cidade_adicionada = ' '.join(cidade_adicionada_no_banco)
    chat_id = update.effective_chat.id
    try:
        if adicionar_cidade(chat_id, cidade_adicionada):
            await update.message.reply_text(f'A cidade: {cidade_adicionada} foi adicionada nas suas cidades salvas.')
            logging.info(f'A cidade {cidade_adicionada_no_banco}, foi adicionada no banco de dados do usuário: {chat_id}')
        else:
            logging.warning(f'o usuario {chat_id}, já possue a cidade: {cidade_adicionada}, no banco de dados.')
            await update.message.reply_text(f'Vocë já possue essa cidade adicionada no seu banco de dados, por favor tente novamente com outra cidade.')

    except ValueError:
        logging.fatal(f'O codigo encontrou um erro inesperado, {ValueError}. ')
        
#                               funcao para remover a cidade no banco de dados
async def remover_cidade_do_banco(update:Update, context:ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    cidade_para_remover = context.args
    cidade_removida = ' '.join(cidade_para_remover)


    if remover_cidade(chat_id, cidade_removida):
        await update.message.reply_text(f'A cidade: {cidade_removida}, foi removida com sucesso da sua lista de cidades. ')
        logging.info(f'o usuario {chat_id}, teve a cidade: {cidade_removida} removida com sucesso.')
    else:
        await update.message.reply_text(f'A cidade digitada não esta na sua lista de cidades, por favor verifique a ortografia e tente novamente')
        logging.info(f'A cidade: {cidade_removida}, não foi removida com sucesso do usuario {chat_id}')

#                               funcao para mostrar os comandos obs: precisa atualizar aqui e la no menu do telegram
async def comandos(update:Update,context:ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('''
    Os comando disponiveis são: 
/start: Para Mostrar Tela Inicial.
/clima: Para consultas de clima. ex: /clima Rio de Janeiro.
/cadastro: Para fazer seu cadastro em nosso aplicativo.
/cidades: Para mostrar suas cidades cadastradas.
/adicionar: Para adicionar uma cidade a sua lista.
/remover: Para remover uma cidade da sua lista.
 ''')





if __name__ == '__main__':
    # Aumentamos o timeout para evitar ConnectTimeout em redes lentas da VPS
    comando_tester = HTTPXRequest(
        http_version="1.1",
        connect_timeout=30, # Aumentado para 30s
        read_timeout=30
    )
    
    application = ApplicationBuilder().token(telegram_api_token).request(comando_tester).build()

    # Função para capturar e logar erros globais
    async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
        logging.error(f"Erro no bot: {context.error}")

    application.add_error_handler(error_handler)

    #               COMANDOS 
    welcome_handler = CommandHandler('start', start)
    application.add_handler(welcome_handler)
    
    clima_handler = CommandHandler('clima', getting_info_from_city)
    application.add_handler(clima_handler)

    cadastro_handler = CommandHandler('cadastro', cadastro)
    application.add_handler(cadastro_handler)

    mostrar_cidades_handler = CommandHandler('cidades', mostrar_lista_cidades)
    application.add_handler(mostrar_cidades_handler)

    adicionar_handler = CommandHandler('adicionar', adicionar_no_banco_cidade)
    application.add_handler(adicionar_handler)

    remover_handler = CommandHandler('remover', remover_cidade_do_banco)
    application.add_handler(remover_handler)

    comandos_handler = CommandHandler('comandos', comandos)
    application.add_handler(comandos_handler)

    application.add_handler(CommandHandler("alarme", criar_alarme_com_ia))



    # verifica se o  banco de dados inicializou com sucesso se não informa no log
    if init_db():
        logging.info('O banco de dados foi inicializado com sucesso')
    else:
        logging.fatal('O banco de dados teve um erro de inicialização')

        
    
    application.run_polling()
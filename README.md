# Clima todo Dia

Bot do Telegram escrito em Python que entrega dados meteorológicos em tempo real e lembretes de clima com ajuda de IA.

Experimente: [t.me/ClimaAppBot](https://t.me/ClimaAppBot)

## Funcionalidades

- Clima atual por cidade (dados da [Open-Meteo](https://open-meteo.com/))
- Índice UV e direção do vento
- Cidades favoritas salvas por usuário
- Alarmes/lembretes agendados, interpretados via Gemini

## Tecnologias

- Python, [python-telegram-bot](https://python-telegram-bot.org/), APScheduler
- PostgreSQL + SQLAlchemy
- Google Gemini (`google-genai`)
- Docker

## Como rodar

1. Copie `config/.env.example` para `config/.env` e preencha:
   - `token_telegram`: token do bot (via [@BotFather](https://t.me/BotFather))
   - `GEMINI_API_KEY`: chave do [Google AI Studio](https://aistudio.google.com/apikey)
   - `DATABASE_URL`: ex. `postgresql+psycopg2://usuario:senha@host:5432/banco`
2. Suba com Docker:

```bash
docker compose up -d --build
```

## Autor

[@ItsDrue157](https://github.com/ItsDrue157)

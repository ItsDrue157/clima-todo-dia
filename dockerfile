FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 1. Copia os arquivos primeiro
COPY . .

# 2. Cria o usuário
RUN useradd -m carlos

# 3. Cria as pastas necessárias e já define o dono como 'carlos'
# O -p garante que toda a árvore (src/config/records) seja criada
RUN mkdir -p /app/config/records/ && \
    chown -R carlos:carlos /app

USER carlos

CMD ["python", "src/main.py"]
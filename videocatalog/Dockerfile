FROM python:3.11-slim

# Instalar ffmpeg (incluye ffprobe) y limpiar cache apt
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Instalar dependencias Python antes de montar el código
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# El UID/GID se controla desde docker-compose (PUID/PGID) en runtime
CMD ["bash"]

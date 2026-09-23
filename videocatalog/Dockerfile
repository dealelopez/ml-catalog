FROM python:3.11-slim

# Instalar ffmpeg (incluye ffprobe) y limpiar cache apt
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg && \
    rm -rf /var/lib/apt/lists/*

# Usuario no-root
RUN useradd --create-home --shell /bin/bash appuser

WORKDIR /app

# Instalar dependencias Python antes de montar el código
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# El código fuente se monta como volumen — no se copia aquí
USER appuser

CMD ["bash"]

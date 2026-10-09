# =============================================================================
# Dockerfile — ml-catalog
# =============================================================================
# Imagen de Python para el catálogo local de vídeos.
# Incluye ffmpeg/ffprobe para extraer metadatos técnicos.
# No incluye los vídeos ni la BD — se montan como volúmenes en compose.
# =============================================================================

FROM python:3.12-slim

# Instalar ffmpeg (incluye ffprobe) y limpiar cache apt
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg && \
    rm -rf /var/lib/apt/lists/*

# Evitar .pyc y buffer en logs (importante para ver logs en Docker).
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Copiar e instalar dependencias primero (aprovecha la caché de capas).
# Si requirements.txt no cambia, Docker reutiliza esta capa sin reinstalar.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código fuente de la aplicación.
COPY src/ ./src/

# Crear usuario sin privilegios para no ejecutar como root.
# El UID/GID efectivo se controla desde docker-compose (PUID/PGID) en runtime.
RUN adduser --disabled-password --no-create-home --gecos "" appuser
USER appuser

# Punto de entrada por defecto: CLI del catálogo.
# Se puede sobreescribir con: docker compose run ml-catalog scan --help
ENTRYPOINT ["python", "-m", "src.cli"]

# Comando por defecto si no se pasa ningún argumento: mostrar ayuda.
CMD ["--help"]

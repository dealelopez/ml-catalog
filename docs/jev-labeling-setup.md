# Prerequisitos para usar label_with_jev.py

Script: `scripts/label_with_jev.py`  
Propósito: etiquetar masivamente los vídeos del catálogo usando Jev (TypeSafe AI)
a través del Vercel AI Gateway, antes de entrenar el clasificador ML.

## Prerequisito cubierto por Task 08

El pipeline ya corrió y `data/catalog.db` contiene vídeos con `label_source = 'rule'`.
El script filtra exactamente esos registros:

```sql
WHERE status = 'active'
  AND (label_source = 'rule' OR label_source IS NULL)
  AND clean_title IS NOT NULL
```

## Bloqueadores pendientes

### 1. `requests` no está en `requirements.txt`

El script importa `requests` directamente pero no está declarado como dependencia.

Añadir a `videocatalog/requirements.txt`:
```
requests==2.32.3
```

Reconstruir la imagen tras el cambio:
```bash
docker compose build
```

### 2. Falta `AI_GATEWAY_API_KEY` en el entorno

El script lanza `EnvironmentError` si no encuentra la variable:

```python
API_KEY = os.environ.get("AI_GATEWAY_API_KEY")
if not API_KEY:
    raise EnvironmentError(...)
```

Pasos:
1. Obtener una API key en https://vercel.com/dashboard → AI Gateway
2. Añadir a `videocatalog/.env`:
   ```
   AI_GATEWAY_API_KEY=tu_clave_aqui
   ```
3. Declarar la variable en `docker-compose.yml` bajo `environment:`:
   ```yaml
   environment:
     - PUID=${PUID:-1000}
     - PGID=${PGID:-1000}
     - AI_GATEWAY_API_KEY=${AI_GATEWAY_API_KEY}   # ← añadir
   ```

### 3. Ruta de la base de datos

El script usa `DB_PATH = os.environ.get("DB_PATH", "data/catalog.db")`.  
El directorio `data/` está montado como volumen en Docker, así que la ruta por defecto
es correcta siempre que se ejecute desde `/app` dentro del contenedor.

Forma recomendada de ejecución:
```bash
docker compose exec videocatalog python scripts/label_with_jev.py
```

Si se ejecuta en el host (fuera del contenedor), hay que estar en `videocatalog/`
y tener `requests` instalado localmente también.

### 4. `src/label.py` está sin implementar (Task 09)

`label_with_jev.py` no depende de `label.py` — accede directamente a SQLite y funciona
independientemente. Pero los pasos que el script sugiere al terminar sí lo requieren:

```
python -m src.label --review    # ← necesita Task 09
python -m src.label --export    # ← necesita Task 09
```

Para ejecutar el etiquetado con Jev solo son necesarios los puntos 1, 2 y 3.
El punto 4 es el flujo posterior de revisión, que es exactamente Task 09.

## Secuencia completa de acciones

```bash
# 1. Añadir requests
echo "requests==2.32.3" >> videocatalog/requirements.txt

# 2. Añadir la clave al .env (sustituir con la clave real)
echo "AI_GATEWAY_API_KEY=tu_clave" >> videocatalog/.env

# 3. Editar docker-compose.yml — añadir la variable en environment:
#    - AI_GATEWAY_API_KEY=${AI_GATEWAY_API_KEY}

# 4. Reconstruir la imagen
docker compose build

# 5. Etiquetar con Jev
docker compose exec videocatalog python scripts/label_with_jev.py

# 6. Revisar los inciertos (requiere Task 09 completada)
docker compose exec videocatalog python -m src.label --review

# 7. Exportar labels.csv para entrenar el modelo (requiere Task 09 completada)
docker compose exec videocatalog python -m src.label --export
```

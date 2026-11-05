# Task 04 — Extracción de metadatos con ffprobe

## Contexto

Proyecto: `videocatalog` — catálogo local de vídeos en servidor Linux.
Tareas previas completadas:
- Task 01: entorno Docker con ffmpeg/ffprobe instalados
- Task 02: esqueleto de `src/metadata.py`
- Task 03: escáner funcional que produce rutas de ficheros

En esta task se implementa `src/metadata.py` completo.

## Objetivo

Implementar la extracción de metadatos en dos capas:
1. **Metadatos del sistema de ficheros** — siempre disponibles: tamaño, fecha de modificación
2. **Metadatos técnicos vía ffprobe** — opcionales: duración, resolución, códec

## Qué entender aquí

Los metadatos técnicos (duración, resolución, códec) son features *opcionales* para el
clasificador. La información más valiosa para clasificar un vídeo está en su nombre y
su ruta, no en sus propiedades técnicas. Dicho esto, la duración puede ser una señal útil:
un vídeo de 8 horas probablemente es un curso completo; uno de 10 minutos es un tutorial corto.

El diseño "fail soft" es una decisión explícita de arquitectura: si ffprobe falla (fichero
corrupto, timeout, formato desconocido), el módulo devuelve `None` en esos campos en lugar
de lanzar una excepción. Un catálogo con algunos campos vacíos es más útil que un pipeline
que se detiene al primer error. Este patrón se repite en todos los módulos del proyecto.

ffprobe devuelve la información en JSON cuando se le pasa `-print_format json`. El módulo
la parsea para extraer solo los campos que necesita: el primer stream de vídeo y su duración,
resolución y códec.

## Ficheros a implementar

```
src/metadata.py
tests/test_metadata.py
```

## Especificación

### src/metadata.py

#### `extract(path: str | Path) -> dict`

Combina metadatos del sistema de ficheros y ffprobe. Nunca lanza excepción.

Devuelve siempre:

```python
{
    "size_bytes":  int | None,
    "modified_at": str | None,   # ISO 8601: "2025-03-12T14:23:01"
    "duration_s":  float | None,
    "width":       int | None,
    "height":      int | None,
    "codec":       str | None,   # "h264", "vp9", "av1"
}
```

Flujo:
1. Obtiene `size_bytes` y `modified_at` de `pathlib.Path.stat()`
2. Llama a `extract_ffprobe(path)` y fusiona el resultado
3. Si `Path.stat()` falla, devuelve dict con todos los campos a `None`

#### `extract_ffprobe(path: str | Path, timeout: int = 30) -> dict`

Ejecuta:
```bash
ffprobe -v quiet -print_format json -show_streams -show_format "<path>"
```

Extracción:
- Busca en `streams` el primer stream con `"codec_type": "video"`
- `duration_s`: intenta `stream["duration"]`, si no `format["duration"]`; convierte a `float`
- `width`, `height`, `codec`: de los campos del stream de vídeo

Devuelve `{"duration_s": None, "width": None, "height": None, "codec": None}` si:
- `ffprobe` no está en el PATH
- El proceso supera el timeout
- La salida no es JSON válido
- Cualquier error de parseo

**No usar `ffmpeg-python`** — llamar a `ffprobe` directamente con `subprocess.run`.

#### Módulo ejecutable como script

```bash
python -m src.metadata <ruta_al_fichero>
```

Imprime el dict como JSON formateado.

### tests/test_metadata.py

```python
def test_extract_sistema_ficheros(tmp_path):
    """Siempre devuelve size_bytes y modified_at."""
    f = tmp_path / "fake.mp4"
    f.write_bytes(b"fake video content" * 100)
    result = extract(f)
    assert result["size_bytes"] == f.stat().st_size
    assert result["modified_at"] is not None
    assert "T" in result["modified_at"]  # formato ISO 8601

def test_extract_todas_las_claves_presentes(tmp_path):
    """El dict siempre tiene todas las claves, aunque sean None."""
    f = tmp_path / "fake.mp4"
    f.write_bytes(b"not a real video")
    result = extract(f)
    for key in ["size_bytes", "modified_at", "duration_s", "width", "height", "codec"]:
        assert key in result

def test_extract_fichero_inexistente():
    """Devuelve dict con Nones si el fichero no existe, sin lanzar excepción."""
    result = extract("/ruta/que/no/existe.mp4")
    assert result["size_bytes"] is None
    assert result["modified_at"] is None

def test_extract_ffprobe_timeout(monkeypatch):
    """Timeout de ffprobe devuelve Nones sin lanzar excepción."""
    import subprocess
    def mock_run(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd="ffprobe", timeout=1)
    monkeypatch.setattr(subprocess, "run", mock_run)
    result = extract_ffprobe("/cualquier/ruta.mp4", timeout=1)
    assert result["duration_s"] is None
    assert result["codec"] is None
```

## Criterios de aceptación

```bash
# Con un fichero webm real de /videos
docker compose exec videocatalog python -m src.metadata \
  "/videos/midudev - Curso Python [abc].webm"
# → JSON con size_bytes, modified_at, y opcionalmente duration_s, width, height, codec

# Con fichero inexistente: no lanza excepción
docker compose exec videocatalog python -c "
from src.metadata import extract
result = extract('/no/existe.mp4')
assert result['size_bytes'] is None
print('OK')
"

# Tests pasan
docker compose exec videocatalog pytest tests/test_metadata.py -v
```

## Notas de implementación

- `modified_at`: `datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds")`
- El comando ffprobe incluye `-v quiet` para suprimir logs en stderr.
- En ficheros `.webm` de yt-dlp el stream puede ser VP9 o AV1. En `.mp4` suele ser H.264.
  El campo `codec` devuelve el `codec_name` de ffprobe tal cual, en minúsculas.

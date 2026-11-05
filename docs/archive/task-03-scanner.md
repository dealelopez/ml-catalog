# Task 03 — Escáner básico con detección de cambios

## Contexto

Proyecto: `videocatalog` — catálogo local de vídeos en servidor Linux.
Tareas previas completadas:
- Task 01: entorno Docker operativo
- Task 02: esqueleto de módulos y `src/config.py` implementado

En esta task se implementa `src/scanner.py` completo. La BD aún no existe (Task 06),
por lo que el escáner en modo `--dry-run` lista ficheros en terminal. La integración
completa con la BD se hará en la Task 08 (pipeline completo).

## Objetivo

Implementar `src/scanner.py` con capacidad de recorrer carpetas eficientemente,
filtrar por extensiones, mostrar progreso, y preparar la base del pipeline
que se completará en Task 08.

## Qué entender aquí

El escáner es incremental: no reprocesa lo que ya está en la BD si no ha cambiado.
A escala (500 GB de vídeos), recorrer los metadatos del sistema de ficheros es barato;
llamar a ffprobe sobre cada vídeo no lo es. Por eso la detección de cambios se basa
en `modified_at` y `size_bytes` — dos valores que el sistema de ficheros proporciona
sin coste, antes de llamar a ninguna herramienta externa.

El escáner usa un generador (`yield`) en lugar de construir una lista completa de paths.
Esto significa que empieza a procesar el primer fichero antes de haber terminado de
recorrer el disco. Con 500 GB de vídeos, la diferencia entre lista y generador
es la diferencia entre esperar 30 segundos a que cargue y ver resultados inmediatamente.

Los ficheros que desaparecen entre dos escaneos no se borran de la BD — se marcan como
`status='missing'`. Esto preserva el historial y permite detectar si un fichero vuelve
a aparecer (movido, restaurado desde backup, etc.).

## Fichero a implementar

```
src/scanner.py
tests/test_scanner.py
```

## Especificación

### src/scanner.py

#### Función principal: `scan(config, dry_run=False) -> dict`

Devuelve dict de resumen:

```python
{
    "found": int,       # ficheros de vídeo encontrados
    "errors": int,      # ficheros con error de acceso
    "skipped": int,     # ficheros ignorados (extensión, carpeta excluida)
    "elapsed_s": float
}
```

Flujo:
1. Lee `config['scan']['folders']`, `extensions`, `ignore_folders`
2. Para cada carpeta, llama a `find_video_files()` (generador)
3. Muestra progreso con `rich.progress`
4. En `dry_run=True`: imprime ruta, tamaño y fecha (no escribe en BD)
5. Captura `PermissionError` y `OSError` por fichero, los registra y continúa
6. Imprime resumen al final

#### Generador: `find_video_files(folders, extensions, ignore_folders) -> Iterator[Path]`

- Recorre recursivamente con `pathlib.Path.rglob("*")`
- `extensions` es un `set` de strings en minúsculas sin punto
- Salta cualquier fichero dentro de una carpeta ignorada
- Filtra solo ficheros (no directorios, no symlinks rotos)
- Normaliza la extensión del fichero a minúsculas antes de comparar

#### Función auxiliar: `format_size(size_bytes: int) -> str`

Convierte bytes a formato legible: `1.2 GB`, `345.6 MB`, `12.3 KB`.

#### Módulo ejecutable como script

```bash
python -m src.scanner [--dry-run] [--config ruta/config.yaml]
```

### Salida esperada en `--dry-run`

```
Escaneando 1 carpeta(s)...

  /videos/midudev - Curso Python [abc].webm     245.3 MB   2025-03-12
  /videos/midudev - Docker desde cero [xyz].webm 1.2 GB    2025-01-08
  ...

Resumen:
  Encontrados : 47
  Errores     : 0
  Tiempo      : 1.3s
```

### tests/test_scanner.py

```python
def test_find_video_files_filtra_extensiones(tmp_path):
    (tmp_path / "video.mp4").touch()
    (tmp_path / "documento.pdf").touch()
    results = list(find_video_files([tmp_path], {"mp4"}, []))
    assert len(results) == 1
    assert results[0].name == "video.mp4"

def test_find_video_files_ignora_carpetas(tmp_path):
    trash = tmp_path / ".trash"
    trash.mkdir()
    (trash / "video.mp4").touch()
    (tmp_path / "otro.mp4").touch()
    results = list(find_video_files([tmp_path], {"mp4"}, [".trash"]))
    assert len(results) == 1
    assert results[0].name == "otro.mp4"

def test_find_video_files_extension_case_insensitive(tmp_path):
    (tmp_path / "VIDEO.MP4").touch()
    results = list(find_video_files([tmp_path], {"mp4"}, []))
    assert len(results) == 1

def test_find_video_files_recursivo(tmp_path):
    sub = tmp_path / "subcarpeta" / "subsub"
    sub.mkdir(parents=True)
    (sub / "video.mkv").touch()
    results = list(find_video_files([tmp_path], {"mkv"}, []))
    assert len(results) == 1

def test_scan_dry_run_no_escribe(tmp_path):
    config = {
        "scan": {"folders": [str(tmp_path)], "extensions": ["mp4"], "ignore_folders": []}
    }
    result = scan(config, dry_run=True)
    assert result["found"] == 0
    assert result["errors"] == 0

def test_format_size():
    assert format_size(1_000) == "1.0 KB"
    assert format_size(1_500_000) == "1.4 MB"
    assert "GB" in format_size(2_000_000_000)
```

## Criterios de aceptación

```bash
# 1. Dry-run sobre /videos muestra los ficheros encontrados
docker compose exec videocatalog python -m src.scanner --dry-run
# → lista de vídeos con tamaño y fecha, resumen al final

# 2. Tests pasan
docker compose exec videocatalog pytest tests/test_scanner.py -v
```

## Notas de implementación

- Usar `rich.progress.Progress` para el contador en tiempo real.
- El generador captura `PermissionError` internamente y hace `yield` solo de ficheros accesibles.
- No llamar a `metadata.py`, `normalizer.py` ni `db.py` en esta task. El escáner ahora solo recorre y lista. La integración completa es la Task 08.
- `os.walk` con `topdown=True` permite modificar `dirnames` in-place para podar carpetas ignoradas eficientemente sin recorrerlas.

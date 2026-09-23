"""
check_db.py — Diagnóstico rápido de la base de datos.

Uso:
    docker compose exec videocatalog python scripts/check_db.py
"""

import os
import sqlite3

DB_PATH = os.environ.get("DB_PATH", "data/catalog.db")

print("=== Entorno ===")
print(f"  cwd          : {os.getcwd()}")
print(f"  DB_PATH (env): {os.environ.get('DB_PATH', '(no definida, usando default)')}")
print(f"  db_path usado: {DB_PATH}")
print(f"  abs path     : {os.path.abspath(DB_PATH)}")

print("\n=== Directorio data/ ===")
data_dir = os.path.dirname(DB_PATH) or "."
if os.path.isdir(data_dir):
    stat = os.stat(data_dir)
    print(f"  existe       : sí")
    print(f"  permisos     : {oct(stat.st_mode)}")
    print(f"  propietario  : uid={stat.st_uid}  gid={stat.st_gid}")
    print(f"  proceso uid  : {os.getuid()}")
    print(f"  contenido    : {os.listdir(data_dir)}")
else:
    print(f"  existe       : NO — el directorio '{data_dir}' no existe")

print("\n=== Fichero catalog.db ===")
if os.path.isfile(DB_PATH):
    stat = os.stat(DB_PATH)
    print(f"  existe       : sí")
    print(f"  tamaño       : {stat.st_size} bytes")
    print(f"  permisos     : {oct(stat.st_mode)}")

    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        total = conn.execute("SELECT COUNT(*) FROM videos").fetchone()[0]
        print(f"  conexión     : OK")
        print(f"  vídeos en BD : {total}")
        conn.close()
    except sqlite3.OperationalError as e:
        print(f"  conexión     : ERROR — {e}")
else:
    print(f"  existe       : NO")
    print(f"  (se creará al primer uso de init_db)")

    # Intentar crear un fichero de prueba para verificar permisos de escritura
    test_path = os.path.join(data_dir, ".write_test")
    try:
        os.makedirs(data_dir, exist_ok=True)
        with open(test_path, "w") as f:
            f.write("ok")
        os.remove(test_path)
        print(f"  escritura    : OK — el proceso puede escribir en '{data_dir}'")
    except OSError as e:
        print(f"  escritura    : ERROR — {e}")

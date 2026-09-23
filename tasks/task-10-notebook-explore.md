# Task 10 — Notebook: Exploración del dataset

## Fichero

`notebooks/01_explore_data.ipynb`

## Contexto

Primera task de ML. El pipeline está completo, la BD tiene vídeos escaneados
y clasificados por reglas, y `labels.csv` fue generado con `src/label.py --export`.

**Antes de tocar cualquier algoritmo de ML, hay que entender los datos.**

## Objetivo

Explorar el dataset e identificar los problemas que afectarán al clasificador
antes de entrenar nada.

## Qué aprenderás

La exploración de datos no es un trámite previo al ML real — es parte del trabajo.
Los problemas que encuentres aquí (desbalance de clases, títulos vacíos, categorías
con pocos ejemplos, canales que dominan una categoría) son exactamente los mismos
que aparecen en proyectos profesionales. Un modelo entrenado sin explorar los datos
suele fallar por razones que se habrían visto en 15 minutos de análisis.

**Desbalance de clases:** si "Python" tiene 200 ejemplos y "Electronica" tiene 8,
el modelo tenderá a ignorar "Electronica" porque equivocarse en ella apenas afecta
a su métrica global. Necesitas saber esto antes de entrenar para aplicar
`class_weight='balanced'` en Task 12.

**Atajos por canal:** si todos los vídeos de "midudev" son de categoría "Web" en
tu dataset, el modelo puede aprender a predecir "Web" siempre que detecta "midudev"
en el título — sin aprender nada sobre el contenido. Ese atajo no generaliza a
canales nuevos. Detectarlo aquí te permite limpiar el dataset antes de entrenar.

**Factor de desbalance:** anota el ratio entre la categoría más grande y la más pequeña.
Lo necesitarás en Task 12 cuando decidas si usar `class_weight='balanced'`.

## Contenido del notebook

### Celda 1 — Imports y carga

```python
import pandas as pd
import matplotlib.pyplot as plt
from collections import Counter

df = pd.read_csv("../data/labels.csv")
print(f"Total de vídeos: {len(df)}")
df.head()
```

### Celda 2 — Distribución de categorías

```python
counts = df["label"].value_counts()
print(counts)

counts.plot(kind="bar", figsize=(12, 4), title="Vídeos por categoría")
plt.xticks(rotation=45, ha="right")
plt.tight_layout()
plt.show()
```

**Preguntas a responder en Markdown:**
- ¿Hay categorías con menos de 20 ejemplos?
- ¿Cuántas veces más grande es la categoría más grande que la más pequeña? (factor de desbalance)
- ¿Qué harás con las categorías con muy pocos ejemplos — fusionarlas, descartarlas, o etiquetar más?

### Celda 3 — Calidad de los títulos

```python
df["title_len"] = df["clean_title"].str.split().str.len()

print("Longitud media de título por categoría:")
print(df.groupby("label")["title_len"].mean().sort_values())

short = df[df["title_len"] <= 2]
print(f"\nTítulos con 2 palabras o menos: {len(short)}")
print(short[["clean_title", "label"]].head(10))
```

**Preguntas:** ¿Hay títulos que son tan cortos que no tienen información suficiente
para clasificar? ¿Qué porcentaje son?

### Celda 4 — Palabras más frecuentes por categoría

```python
def top_words(df, category, n=15):
    titles = df[df["label"] == category]["clean_title"].str.cat(sep=" ")
    return Counter(titles.split()).most_common(n)

for cat in df["label"].unique():
    print(f"\n{cat}:")
    for word, count in top_words(df, cat):
        print(f"  {word}: {count}")
```

**Preguntas:** ¿Hay palabras que aparecen en varias categorías (ej: "curso")?
Estas palabras son malas features — TF-IDF las penalizará en Task 11, pero
vale la pena identificarlas ahora. ¿Hay palabras que son claramente específicas
de una categoría?

### Celda 5 — Canales por categoría

```python
channel_cat = df.groupby(["channel", "label"]).size().unstack(fill_value=0)
print(channel_cat)
```

**Pregunta crítica:** ¿Hay canales que solo tienen vídeos de una categoría en el dataset?
Si "midudev" solo aparece en "Web" y "Python", el modelo puede aprender a predecir
por canal en lugar de por contenido del título. Eso es un atajo que no generaliza.

### Celda 6 — Distribución de rule_score

```python
df["rule_score"].hist(bins=20, figsize=(10, 4))
plt.axvline(0.2, color="red", linestyle="--", label="threshold (0.2)")
plt.title("Distribución de rule_score")
plt.xlabel("Score")
plt.ylabel("Vídeos")
plt.legend()
plt.show()

low_conf = (df["rule_score"] < 0.2).sum()
print(f"Vídeos con score < 0.2: {low_conf} ({100*low_conf/len(df):.1f}%)")
```

**Preguntas:** ¿Qué porcentaje de vídeos cae en "Otros"? Si es alto (>30%), significa
que las reglas no están cubriendo bien la colección. ¿Necesitas añadir keywords al
`config.yaml` antes de seguir?

### Celda 7 — Conclusiones (celda Markdown a rellenar)

Responder explícitamente antes de pasar a Task 11:

1. ¿Cuántos ejemplos tiene la categoría más pequeña? ¿Es suficiente para entrenar?
   (Regla práctica: menos de 20 ejemplos → el modelo no aprenderá esa categoría)
2. ¿Cuál es el factor de desbalance?
3. ¿Hay categorías que deberían fusionarse o eliminarse?
4. ¿Qué % de vídeos están en "Otros"? ¿Necesitas mejorar las reglas o etiquetar más?
5. ¿Necesitas etiquetar más vídeos manualmente antes de entrenar?

## Criterio de aceptación

El notebook se ejecuta de principio a fin sin errores, produce al menos dos gráficos,
y las celdas de conclusiones tienen texto escrito respondiendo las preguntas planteadas.

**Las preguntas no son retóricas.** El notebook es un documento de decisiones, no solo
código. Las respuestas escritas en las celdas Markdown son el output más valioso de esta task.

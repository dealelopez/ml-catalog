# Modelos para opencode vía OpenRouter

Referencia de modelos disponibles en OpenRouter para usar con opencode, con precios actuales y orientación sobre para qué tipo de tarea sirve cada uno.

> Precios en USD por millón de tokens (input / output). Datos obtenidos de la API de OpenRouter en septiembre 2026.

---

## Configuración base

```json
{
  "$schema": "https://opencode.ai/config.json",
  "model": "openrouter/<provider>/<model>"
}
```

Para añadir modelos no precargados:

```json
{
  "$schema": "https://opencode.ai/config.json",
  "provider": {
    "openrouter": {
      "models": {
        "deepseek/deepseek-v4-flash": {}
      }
    }
  }
}
```

---

## Serie OpenAI GPT-5.6 (los más recientes de OpenAI)

OpenAI nombra sus modelos con tres niveles: **Luna** (barato/rápido), **Terra** (equilibrado) y **Sol** (flagship). Todos con razonamiento y 1M tokens de contexto.

| Modelo | ID openrouter | Precio input/output | Para qué sirve |
|---|---|---|---|
| **GPT-5.6 Luna** | `openai/gpt-5.6-luna` | $0.10 / $0.60 | Alto volumen, baja latencia, razonamiento ligero. Chat, clasificación, workflows simples. Equivalente moderno al GPT-4o Mini pero con razonamiento básico. |
| **GPT-5.6 Terra** | `openai/gpt-5.6-terra` | $1.00 / $6.00 | Coding cotidiano, razonamiento y workflows agénticos. Punto medio entre Luna y la gama alta. |
| **GPT-5.6 Sol** | `openai/gpt-5.6-sol` | — | Flagship de la serie. Para tareas muy complejas. |

---

## Serie OpenAI GPT-4.x (consolidados, bien probados)

| Modelo | ID openrouter | Precio input/output | Para qué sirve |
|---|---|---|---|
| **GPT-4.1 Nano** | `openai/gpt-4.1-nano` | $0.10 / $0.40 | Código rutinario con spec muy cerrado. Sin razonamiento, máxima velocidad y mínimo coste. |
| **GPT-4o Mini** | `openai/gpt-4o-mini` | $0.15 / $0.60 | Coding simple, alto volumen. Más veterano que Nano, más proveedores disponibles. |
| **GPT-4.1 Mini** | `openai/gpt-4.1-mini` | $0.40 / $1.60 | Coding con spec detallado. Buen equilibrio coste/calidad para tool calling. |
| **GPT-4.1** | `openai/gpt-4.1` | $2.00 / $8.00 | Spec largo, contexto complejo, texto pedagógico de calidad. 1M tokens contexto. |
| **GPT-4o** | `openai/gpt-4o` | $2.50 / $10.00 | Versátil, multimodal. Superado en coste/calidad por GPT-4.1, menos recomendable. |
| **GPT-5.5** | `openai/gpt-5.5` | $2.50 / $15.00 | Flagship para cargas profesionales muy complejas. |

---

## Serie OpenAI o-series (razonamiento explícito)

Modelos pensados para problemas que requieren razonamiento paso a paso: matemáticas, STEM, arquitectura de software compleja.

| Modelo | ID openrouter | Precio input/output | Para qué sirve |
|---|---|---|---|
| **o3 Mini** | `openai/o3-mini` | $1.10 / $4.40 | Razonamiento STEM eficiente. Bueno cuando hay decisiones de diseño con múltiples restricciones. |
| **o4 Mini** | `openai/o4-mini` | $1.10 / $4.40 | Igual que o3-mini pero más reciente y con soporte multimodal. Mejor opción de los dos. |
| **o3** | `openai/o3` | $2.00 / $8.00 | Razonamiento profundo, mismo precio que GPT-4.1. Mejor para problemas ambiguos o abiertos donde GPT-4.1 se queda corto. |

---

## DeepSeek (mejor ratio precio/calidad para código)

Modelos MoE (Mixture of Experts): muchos parámetros totales, pocos activos por inferencia → baratos y potentes.

| Modelo | ID openrouter | Precio input/output | Para qué sirve |
|---|---|---|---|
| **DeepSeek V4 Flash 0731** `:free` | `deepseek/deepseek-v4-flash-0731:free` | $0 / $0 | Experimentar sin coste. MoE 284B/13B activos, razonamiento incluido. Tiene rate limits. |
| **DeepSeek V4 Flash** ⭐ | `deepseek/deepseek-v4-flash` | $0.09 / $0.18 | Coding rutinario con spec cerrado. El mejor coste/calidad del mercado para código. 1M contexto, razonamiento. |
| **DeepSeek V4 Pro** | `deepseek/deepseek-v4-pro` | $0.94 / $1.88 | Razonamiento más profundo. 1.6T total / 49B activos. Para decisiones de diseño y tareas complejas. |

> **Nota**: el precio de DeepSeek varía según proveedor (DeepInfra, StreamLake, etc.). OpenRouter enruta al más barato por defecto.

---

## Google Gemini

| Modelo | ID openrouter | Precio input/output | Para qué sirve |
|---|---|---|---|
| **Gemini 2.5 Flash** | `google/gemini-2.5-flash` | $0.15 / $0.25¹ | Coding + contexto muy largo. Razonamiento built-in, 1M tokens. Muy bueno para specs extensos. Multimodal. |

¹ El razonamiento interno (`internal_reasoning`) cobra $2.50/M tokens adicionales. Con razonamiento desactivado el coste es $0.30 / $2.50.

---

## MoonshotAI Kimi

| Modelo | ID openrouter | Precio input/output | Para qué sirve |
|---|---|---|---|
| **Kimi K2** | `moonshotai/kimi-k2` | $0.57 / $2.30 | Coding agéntico con múltiples pasos de tool calling. 1T parámetros / 32B activos. Fiable en workflows complejos. |

---

## Qwen (Alibaba)

| Modelo | ID openrouter | Precio input/output | Para qué sirve |
|---|---|---|---|
| **Qwen 2.5 Coder 32B** | `qwen/qwen-2.5-coder-32b-instruct` | $0.07 / $0.10 | El más barato con tool calling. Código puro y rutinario. Sin razonamiento. Contexto corto (32K). |

---

## Modelos propios de OpenRouter

OpenRouter tiene sus propios modelos, principalmente experimentales y sin precio publicado.

| Modelo | ID | Precio | Notas |
|---|---|---|---|
| **Auto Router** | `openrouter/auto` | Precio del modelo seleccionado | Selecciona automáticamente el mejor modelo para cada prompt según el gasto agregado de la comunidad. Soporta `cost_tier`: `low`, `medium`, `high`, `xhigh`, `max`. |
| **Optimus Alpha** | `openrouter/optimus-alpha` | Experimental | Modelo cloaked orientado a casos de uso reales y programación. Sin precio fijo (periodo de feedback). |
| **Quasar Alpha** | `openrouter/quasar-alpha` | Experimental | Modelo cloaked para tareas de uso general y contexto largo. Sin precio fijo. |
| **Horizon Beta** | `openrouter/horizon-beta` | Experimental | Versión mejorada de Horizon Alpha. Sin precio fijo. |

### Auto Router con cost_tier

```json
{
  "$schema": "https://opencode.ai/config.json",
  "model": "openrouter/auto"
}
```

Útil cuando no quieres gestionar la elección de modelo manualmente. El router clasifica el prompt en ~30 tipos de tarea y elige el modelo que la comunidad más usa para ese tipo. Con `cost_tier: low` prioriza baratos; con `max`, los más capaces.

---

## Resumen comparativo por tipo de tarea

Para este proyecto (ml-catalog), la orientación concreta es:

| Tipo de tarea | Modelo recomendado | Precio aprox. |
|---|---|---|
| Código rutinario, spec muy cerrado (tasks 1–5) | `deepseek/deepseek-v4-flash` | $0.09 / $0.18 |
| Pipeline e integración, tool calling intensivo (tasks 6–8) | `deepseek/deepseek-v4-flash` o `openai/gpt-4.1-mini` | $0.09–$0.40 / $0.18–$1.60 |
| Decisiones de diseño, etiquetado, ciclo ML (tasks 9–14) | `deepseek/deepseek-v4-pro` o `openai/o4-mini` | $0.94–$1.10 / $1.88–$4.40 |
| Notebooks pedagógicos, texto explicativo (tasks 10–16) | `openai/gpt-4.1` o `google/gemini-2.5-flash` | $0.15–$2.00 / $0.25–$8.00 |
| Sin presupuesto / experimentar | `deepseek/deepseek-v4-flash-0731:free` | $0 |

---

## Advertencias

- Los modelos `:free` tienen **rate limits** y pueden tener tiempos de espera.
- Los modelos experimentales de OpenRouter (`optimus-alpha`, `quasar-alpha`, etc.) **registran prompts y completions** para recopilar feedback — no usarlos con código o datos sensibles.
- El precio de DeepSeek en OpenRouter varía según el proveedor subyacente (DeepInfra, StreamLake, DigitalOcean…). OpenRouter enruta al más barato por defecto.
- Los precios de la serie GPT-5.6 tienen **pricing por tramos**: a partir de 272K tokens de prompt el precio se duplica.

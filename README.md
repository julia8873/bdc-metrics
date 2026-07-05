# bdc-metrics

Herramienta de métricas cuantitativas y estructurales para bundles OKF
(bases de conocimiento tipo BdC-main). Se ejecuta contra cualquier
carpeta `okf/`, independiente del repo de contenido.

## Uso local

```bash
pip install -r requirements.txt

python src/graph_analysis.py --vault ../BdC-main/okf --out reports/graph.json
python src/structure_check.py --repo ../BdC-main --vault ../BdC-main/okf --out reports/structure.json

# o los dos combinados:
python src/report.py --repo ../BdC-main --vault ../BdC-main/okf --out reports/report.json
```

## Uso desde otro repo (GitHub Actions)

En el repo de contenido (ej. `BdC-main`), crea `.github/workflows/run-metrics.yml`:

```yaml
name: Run BdC Metrics
on:
  push:
    paths: ["okf/**"]
  schedule:
    - cron: "0 3 * * 1"  # todos los lunes

jobs:
  metrics:
    uses: ceprud/bdc-metrics/.github/workflows/metrics.yml@main
    with:
      vault_path: okf
    permissions:
      contents: write
```

El resultado se guarda en `reports/report.json` del propio repo de contenido
y también queda disponible como artefacto de la Action.

## Métricas incluidas

- Nodos, enlaces medios, tasa de huérfanos, densidad de enlaces, profundidad
  del árbol, distancia hamming entre etiquetas (`graph_analysis.py`)
- Existencia de AGENTS.md/log.md/index.md, frontmatter obligatorio, tasa de
  markdown válido (`structure_check.py`)

## Pendiente (fase 2)

- `rag_eval/`: fidelidad (NLI / HHEM) y LLM-as-a-judge sobre pares
  pregunta-contexto-respuesta (requiere modelos locales, no cabe en
  Actions gratis → ejecutar en el servidor del bot y subir el resultado
  agregado a `reports/`).

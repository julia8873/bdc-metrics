"""
pretty_report.py

Convierte el report.json (salida de report.py) en un informe Markdown
legible, con tablas. Pensado para leer en terminal (bat/less) o para
que GitHub lo renderice directamente si se commitea como reports/report.md.

Uso:
    python pretty_report.py --in reports/report.json --out reports/report.md
"""
import argparse
import json
from pathlib import Path


def bar(value: float, max_value: float, width: int = 20) -> str:
    if max_value <= 0:
        return ""
    filled = round((value / max_value) * width)
    return "█" * filled + "░" * (width - filled)


def render(report: dict) -> str:
    g = report.get("grafo", {})
    e = report.get("estructura", {})
    lines = []

    lines.append(f"# Informe de métricas BdC\n")
    lines.append(f"_Generado: {report.get('timestamp', '—')}_")
    lines.append(f"_Repo: `{report.get('repo', '—')}`_\n")

    if "error" in g:
        lines.append(f"⚠️ **Grafo:** {g['error']}\n")
    else:
        lines.append("## 📊 Grafo de conocimiento\n")
        lines.append("| Métrica | Valor |")
        lines.append("|---|---|")
        lines.append(f"| Ficheros totales | {g['n_files']} |")
        lines.append(f"| Nodos válidos | {g['n_nodes_validos']} |")
        lines.append(f"| Con error de frontmatter | {g['n_ficheros_con_error_frontmatter']} |")
        lines.append(f"| Grado medio (nodos conectados) | {g['avg_nodos_conectados']} |")
        lines.append(f"| Huérfanos | {g['n_huerfanos']} ({g['tasa_huerfanos']*100:.1f}%) |")
        lines.append(f"| Densidad de enlaces (media) | {g['densidad_enlaces_promedio']} |")
        lines.append(f"| Profundidad árbol desde index | {g['profundidad_arbol_desde_index']} |")
        lines.append(f"| Etiquetas únicas | {g['n_etiquetas_unicas']} |")
        lines.append(f"| Hamming medio entre tags | {g['distancia_hamming_promedio_tags']} |")
        lines.append(f"| Tamaño medio (palabras/fichero) | {g['tamano_medio_palabras']} |")
        lines.append("")

        if g.get("huerfanos"):
            lines.append(f"**Huérfanos:** {', '.join(g['huerfanos'])}\n")

        densidades = g.get("densidad_por_nodo", {})
        if densidades:
            lines.append("### Densidad de enlaces por nodo (menor → mayor)\n")
            lines.append("| Nodo | Densidad | |")
            lines.append("|---|---|---|")
            max_d = max(densidades.values()) or 1
            for nodo, d in sorted(densidades.items(), key=lambda kv: kv[1]):
                lines.append(f"| `{nodo}` | {d:.4f} | `{bar(d, max_d, 15)}` |")
            lines.append("")

    if "error" in e:
        lines.append(f"⚠️ **Estructura:** {e['error']}\n")
    else:
        lines.append("## 🗂️ Estructura y ficheros base\n")
        base = e.get("ficheros_base", {})
        lines.append("| Fichero | Existe |")
        lines.append("|---|---|")
        for k, v in base.items():
            lines.append(f"| `{k}` | {'✅' if v else '❌'} |")
        lines.append("")
        lines.append(f"**Tasa de markdown válido:** {e['tasa_markdown_valido']*100:.1f}% "
                     f"({e['n_ficheros_analizados']} ficheros analizados)\n")

        problemáticos = [d for d in e.get("detalle_frontmatter", [])
                         if not d.get("frontmatter_ok") or not d.get("tipo_valido")]
        if problemáticos:
            lines.append("### ⚠️ Ficheros con frontmatter incompleto/inválido\n")
            lines.append("| Fichero | Campos faltantes | Tipo válido |")
            lines.append("|---|---|---|")
            for d in problemáticos:
                lines.append(f"| `{d['file']}` | {', '.join(d['missing_fields']) or '—'} | "
                             f"{'✅' if d['tipo_valido'] else '❌'} |")
            lines.append("")
        else:
            lines.append("✅ Todos los ficheros tienen frontmatter completo y tipo válido.\n")

    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", required=True)
    ap.add_argument("--out", default=None, help="Si se omite, imprime a stdout")
    args = ap.parse_args()

    report = json.loads(Path(args.inp).read_text(encoding="utf-8"))
    md = render(report)

    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(md, encoding="utf-8")
        print(f"Informe legible escrito en {args.out}")
    else:
        print(md)


if __name__ == "__main__":
    main()

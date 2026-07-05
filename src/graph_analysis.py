"""
graph_analysis.py

Analiza un vault OKF (carpeta okf/) y calcula métricas cuantitativas
del grafo de conocimiento: nodos, enlaces, huérfanos, densidad,
profundidad del árbol y distancia hamming entre etiquetas.

Uso:
    python graph_analysis.py --vault okf/ --out reports/graph.json
"""
import argparse
import itertools
import json
import re
import sys
from pathlib import Path

import frontmatter
import networkx as nx

WIKILINK_RE = re.compile(r"\[\[([^\]|#]+)(?:\|[^\]]+)?\]\]")


def find_markdown_files(vault: Path):
    return sorted(p for p in vault.rglob("*.md") if p.is_file())


def slug(path: Path, vault: Path) -> str:
    """Identificador estable de un nodo: ruta relativa sin extensión."""
    return str(path.relative_to(vault).with_suffix("")).replace("\\", "/")


def resolve_link(target: str, slugs: dict) -> str | None:
    """Resuelve un [[wikilink]] a un slug real del vault (case-insensitive, por nombre base)."""
    target_norm = target.strip().split("/")[-1].lower()
    for s in slugs:
        if s.lower() == target.strip().lower() or s.lower().split("/")[-1] == target_norm:
            return s
    return None


def hamming(a: list[str], b: list[str]) -> int:
    """Distancia hamming entre dos listas de tags, alineadas por posición
    tras rellenar la más corta. Sirve como proxy de disimilitud de etiquetado."""
    la, lb = sorted(a), sorted(b)
    n = max(len(la), len(lb))
    la += [""] * (n - len(la))
    lb += [""] * (n - len(lb))
    return sum(1 for x, y in zip(la, lb) if x != y)


def build_graph(vault: Path):
    files = find_markdown_files(vault)
    docs = {}
    for f in files:
        try:
            post = frontmatter.load(f)
        except Exception as e:
            docs_slug = slug(f, vault)
            docs[docs_slug] = {"error": f"frontmatter inválido: {e}", "raw_path": str(f)}
            continue
        s = slug(f, vault)
        docs[s] = {
            "path": str(f.relative_to(vault)),
            "content": post.content,
            "meta": post.metadata,
            "word_count": len(post.content.split()),
        }

    slugs = {s: d for s, d in docs.items() if "error" not in d}
    G = nx.DiGraph()
    G.add_nodes_from(slugs.keys())

    for s, d in slugs.items():
        for m in WIKILINK_RE.finditer(d["content"]):
            target = resolve_link(m.group(1), slugs)
            if target and target != s:
                G.add_edge(s, target)

    return G, docs, slugs


def compute_metrics(G: nx.DiGraph, docs: dict, slugs: dict, vault: Path):
    n_nodes = G.number_of_nodes()
    degrees = dict(G.degree())  # in+out
    avg_connected_nodes = (sum(degrees.values()) / n_nodes) if n_nodes else 0.0

    orphans = [s for s, deg in degrees.items() if deg == 0]
    orphan_rate = (len(orphans) / n_nodes) if n_nodes else 0.0

    densities = {}
    for s, d in slugs.items():
        wc = max(d["word_count"], 1)
        n_links = G.out_degree(s)
        densities[s] = n_links / wc
    avg_density = (sum(densities.values()) / len(densities)) if densities else 0.0

    # Profundidad del árbol: BFS desde index (si existe) sobre el grafo no dirigido
    depth_from_index = None
    index_candidates = [s for s in slugs if s.split("/")[-1] == "index"]
    if index_candidates:
        UG = G.to_undirected()
        root = index_candidates[0]
        if root in UG:
            lengths = nx.single_source_shortest_path_length(UG, root)
            depth_from_index = max(lengths.values()) if lengths else 0

    all_tags = {s: d["meta"].get("tags", []) or [] for s, d in slugs.items()}
    pairs = list(itertools.combinations(all_tags.keys(), 2))
    hamming_distances = [hamming(all_tags[a], all_tags[b]) for a, b in pairs]
    avg_hamming = (sum(hamming_distances) / len(hamming_distances)) if hamming_distances else 0.0

    n_tags_unique = len({t for tags in all_tags.values() for t in tags})

    return {
        "n_files": len(docs),
        "n_nodes_validos": n_nodes,
        "n_ficheros_con_error_frontmatter": len(docs) - len(slugs),
        "avg_nodos_conectados": round(avg_connected_nodes, 3),
        "n_huerfanos": len(orphans),
        "tasa_huerfanos": round(orphan_rate, 3),
        "huerfanos": orphans,
        "densidad_enlaces_promedio": round(avg_density, 5),
        "densidad_por_nodo": {k: round(v, 5) for k, v in densities.items()},
        "profundidad_arbol_desde_index": depth_from_index,
        "n_etiquetas_unicas": n_tags_unique,
        "distancia_hamming_promedio_tags": round(avg_hamming, 3),
        "tamano_medio_palabras": round(
            (sum(d["word_count"] for d in slugs.values()) / len(slugs)) if slugs else 0, 1
        ),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--vault", required=True, help="Ruta a la carpeta okf/")
    ap.add_argument("--out", default=None, help="Ruta de salida JSON (opcional; si no, imprime a stdout)")
    args = ap.parse_args()

    vault = Path(args.vault)
    if not vault.exists():
        print(f"ERROR: no existe la ruta {vault}", file=sys.stderr)
        sys.exit(1)

    G, docs, slugs = build_graph(vault)
    metrics = compute_metrics(G, docs, slugs, vault)

    output = json.dumps(metrics, ensure_ascii=False, indent=2)
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(output, encoding="utf-8")
        print(f"Métricas escritas en {args.out}")
    else:
        print(output)


if __name__ == "__main__":
    main()

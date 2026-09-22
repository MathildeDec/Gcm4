#!/usr/bin/python3
# -*- coding: UTF-8 -*-
"""Détecte les imports circulaires *à charge de module* dans le dépôt GCM.

Hook pre-commit local (voir ``.pre-commit-config.yaml``) — appelé sans
argument, il analyse tout le dépôt (pas seulement les fichiers modifiés,
un cycle pouvant apparaître entre deux fichiers dont un seul a changé).

Ce que ce script détecte : les imports exécutés au chargement du module
(``import x`` / ``from x import y`` en tête de fichier, dans un corps de
classe, ou dans un ``if``/``try`` au niveau module) qui, mis bout à bout,
forment un cycle — c'est le seul cas qui casse réellement à l'exécution
(``ImportError: cannot import name ... from partially initialized
module``).

Ce que ce script ignore délibérément (faux positifs qu'un outil générique
remonterait à tort) :

- Les imports à l'intérieur d'un corps de fonction/méthode — le dépôt
  s'appuie intentionnellement sur ce pattern pour casser des cycles
  logiques (ex. ``models.py`` importe ``gcm4_core`` à l'intérieur de ses
  méthodes plutôt qu'en tête de fichier). Un import différé n'est jamais un
  risque de chargement circulaire par construction : au moment où la
  fonction s'exécute, les deux modules sont déjà entièrement chargés.
- Les imports sous ``if TYPE_CHECKING:`` — jamais exécutés à l'exécution
  réelle (uniquement pour les vérificateurs de types statiques), donc sans
  risque de cycle de chargement.

Usage :
    python3 tools/check_circular_imports.py [--root PATH]

Sortie : liste chaque cycle trouvé (ex. ``a -> b -> c -> a``) et sort avec
un code de retour non nul si au moins un cycle est trouvé ; sort 0 sinon.
"""

from __future__ import annotations

import argparse
import ast
import os
import sys


class _TopLevelImportCollector(ast.NodeVisitor):
    """Collecte les imports exécutés au chargement du module (voir docstring de module)."""

    def __init__(self) -> None:
        """Initialise l'ensemble des modules importés au chargement."""
        self.imported_modules: set[str] = set()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:  # noqa: N802 (nom impose par ast.NodeVisitor)
        """Ne descend pas dans le corps : imports différés, hors périmètre."""
        return

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:  # noqa: N802
        """Ne descend pas dans le corps : imports différés, hors périmètre."""
        return

    def visit_If(self, node: ast.If) -> None:
        """Ignore le bloc ``if TYPE_CHECKING:``, sinon descend normalement."""
        test = node.test
        is_type_checking = (isinstance(test, ast.Name) and test.id == "TYPE_CHECKING") or (
            isinstance(test, ast.Attribute) and test.attr == "TYPE_CHECKING"
        )
        if is_type_checking:
            for stmt in node.orelse:
                self.visit(stmt)
            return
        self.generic_visit(node)

    def visit_Import(self, node: ast.Import) -> None:
        """Enregistre chaque module de ``import x[, y...]``."""
        for alias in node.names:
            self.imported_modules.add(alias.name.split(".")[0])

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Enregistre le module de ``from x import y`` (ignore les imports relatifs purs)."""
        if node.module and node.level == 0:
            self.imported_modules.add(node.module.split(".")[0])


def discover_local_modules(root: str) -> dict[str, str]:
    """Recense les modules Python locaux importables du dépôt.

    Args:
        root (str): Racine du dépôt à analyser.

    Returns:
        dict[str, str]: Nom de module -> chemin du fichier .py, pour la
        racine du dépôt et le dossier ``plugins/`` (les deux sont ajoutés à
        ``sys.path`` par l'application, voir ``gnome_connection_manager.py``).
    """
    modules: dict[str, str] = {}
    search_dirs = [root, os.path.join(root, "plugins")]
    for directory in search_dirs:
        if not os.path.isdir(directory):
            continue
        for entry in os.listdir(directory):
            if entry.endswith(".py") and not entry.startswith("."):
                name = entry[:-3]
                path = os.path.join(directory, entry)
                # En cas de doublon de nom entre racine et plugins/, le
                # fichier racine gagne (résolu en premier par sys.path[0]).
                modules.setdefault(name, path)
    return modules


def build_import_graph(modules: dict[str, str]) -> dict[str, set[str]]:
    """Construit le graphe des dépendances locales à charge de module.

    Args:
        modules (dict[str, str]): Sortie de ``discover_local_modules``.

    Returns:
        dict[str, set[str]]: Nom de module -> ensemble des modules locaux
        qu'il importe au chargement.
    """
    graph: dict[str, set[str]] = {}
    for name, path in modules.items():
        try:
            with open(path, encoding="utf-8") as f:
                tree = ast.parse(f.read(), filename=path)
        except (OSError, SyntaxError) as exc:
            print(f"⚠️  {path} ignoré (illisible ou syntaxe invalide) : {exc}", file=sys.stderr)
            graph[name] = set()
            continue
        collector = _TopLevelImportCollector()
        collector.visit(tree)
        graph[name] = {m for m in collector.imported_modules if m in modules and m != name}
    return graph


def find_cycles(graph: dict[str, set[str]]) -> list[list[str]]:
    """Détecte les cycles dans le graphe de dépendances (DFS, 3 couleurs).

    Args:
        graph (dict[str, set[str]]): Sortie de ``build_import_graph``.

    Returns:
        list[list[str]]: Liste des cycles trouvés, chacun étant la liste
        ordonnée des modules du cycle (le premier élément est répété en
        dernier pour lisibilité : ``["a", "b", "c", "a"]``).
    """
    WHITE, GRAY, BLACK = 0, 1, 2
    color = dict.fromkeys(graph, WHITE)
    cycles: list[list[str]] = []
    path: list[str] = []

    def dfs(node: str) -> None:
        """Parcours en profondeur avec détection de cycle par couleurs."""
        color[node] = GRAY
        path.append(node)
        for neighbor in sorted(graph.get(node, ())):
            if color.get(neighbor) == GRAY:
                cycle_start = path.index(neighbor)
                cycles.append([*path[cycle_start:], neighbor])
            elif color.get(neighbor) == WHITE:
                dfs(neighbor)
        path.pop()
        color[node] = BLACK

    for name in sorted(graph):
        if color[name] == WHITE:
            dfs(name)
    return cycles


def main() -> int:
    """Point d'entrée CLI.

    Returns:
        int: 0 si aucun cycle trouvé, 1 sinon (pour le hook pre-commit).
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root", default=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    args = parser.parse_args()

    modules = discover_local_modules(args.root)
    graph = build_import_graph(modules)
    cycles = find_cycles(graph)

    if not cycles:
        print(f"✅ Aucun import circulaire à charge de module ({len(modules)} modules analysés).")
        return 0

    print(f"❌ {len(cycles)} import(s) circulaire(s) trouvé(s) :\n")
    for cycle in cycles:
        print("   " + " -> ".join(cycle))
    print(
        "\nCasse le cycle en différant l'import côté appelant le moins "
        "central (import à l'intérieur d'une fonction/méthode plutôt qu'en "
        "tête de fichier), ou en le limitant à `if TYPE_CHECKING:` s'il ne "
        "sert qu'à l'annotation de type."
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())

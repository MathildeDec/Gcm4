# Session 19 — 2026-09-07 — Scripting avant connexion (#116) — volet « avant »

**Il y a une session (2026-09-07)** : scripting avant connexion (#116),
backlog `features.md` §4.2 (urgence moyenne) → fait pour le volet "avant"
seulement (le volet "après" reste ouvert, voir §4.2), première
implémentation — rien de tel n'existait dans le code (recherche textuelle
confirmée : aucune trace de `pre_connect`/`post_connect`/hook avant cette
session). Nouvelle fonction pure `gcm4_core.resolve_connection_hook_command(
template, host_name, host_address, host_group, protocol)` : résout les
marqueurs `{name}`/`{address}`/`{group}`/`{protocol}` dans un modèle de
commande shell arbitraire, `None` si le modèle est vide/blanc, modèle
inchangé (pas d'exception) si un marqueur est inconnu. 7 tests dans
`tests/test_gcm4_core.py::TestResolveConnectionHookCommand` — 78 tests
verts au total dans ce fichier (71 + 7 nouveaux), exécutés réellement par
`pytest`. Nouveau champ `Host.pre_connect_command` (`models.py`,
`_CORE_FIELDS`, défaut `""`, INI `pre-connect-command`), exposé dans
« Éditer hôte » via un champ texte « Before connecting », **sans** la
restriction habituelle "visible seulement pour VTE" (a du sens pour tous
les protocoles). Nouvelle fonction `gnome_connection_manager.
run_pre_connect_hook(host)` : lance la commande résolue en tâche de fond
(`subprocess.Popen(shell=True)`, non bloquant, échec journalisé en warning
seulement) — câblée en tête de `Wmain._open_connection_tab()`, le point
d'entrée générique unique du projet, donc valable pour **tous les
protocoles** (contrairement à `send_desktop_notification()`, limitée à
VTE via `child-exited`). `python3 -m py_compile` propre sur les 4 fichiers
modifiés (`gcm4_core.py`, `models.py`, `gnome_connection_manager.py`,
`tests/test_gcm4_core.py`), `ruff check gnome_connection_manager.py` sans
nouvelle erreur ; `ruff check models.py` remonte 3 erreurs `D417`
préexistantes sur des fonctions non touchées (`get_val`/
`load_host_from_ini`/`save_host_to_ini`), non corrigées (règle "ne
corriger que ce qu'on modifie"). Câblage GTK non exécuté en conditions
réelles (pas de GTK/VTE dans cet environnement de travail). ⚠️ Volet
"après" (`Host.post_connect_command`) non fait : nécessiterait de
propager une commande à travers les 5 sites de création de
`NotebookTabLabel` (même chantier que `host_auto_close_tab`, voir "il y a
dix sessions" ci-dessous) — hors périmètre de cette session. Détail dans
`features.md` §4.1 (nouvelle entrée) et §4.2 (ligne reformulée, ne porte
plus que sur le volet "après").

---
*Note de journal d'origine (claude.md) : « Il y a une session (2026-09-07) : scripting avant connexion (#116), backlog §4.2 (urgence moyenne) → fait pour le volet « avant » seulement. »*

# Session 21 — 2026-09-08 — Scripting après connexion (#116) — volet « après »

**Il y a une session (2026-09-08)** : scripting après connexion (#116) —
volet "après", symétrique de `Host.pre_connect_command` (volet "avant" fait
le 2026-09-07). Nouveau champ `Host.post_connect_command` (`models.py`,
`_CORE_FIELDS`, INI `post-connect-command`), exposé dans "Éditer hôte" via
un nouveau champ texte "After disconnecting" — pas de nouvelle fonction pure
dans `gcm4_core.py` : `resolve_connection_hook_command()` (déjà écrite le
2026-09-07 pour le volet "avant") était déjà générique aux deux sens, elle
est simplement réutilisée telle quelle. La difficulté propre au volet
"après" est ailleurs : contrairement au hook "avant" (résolu ET lancé
immédiatement dans `_open_connection_tab()`, l'objet `Host` étant sous la
main), le hook "après" doit être lancé plus tard, au moment où la connexion
se termine — moment où `widgets.NotebookTabLabel` ne connaît plus l'objet
`Host` d'origine. Solution : résoudre la commande (marqueurs substitués) dès
l'ouverture de l'onglet, dans `gnome_connection_manager.py` (nouvelle
fonction `resolve_post_connect_command(host, proto)`), puis propager la
chaîne déjà résolue à travers les **5 sites de création de
`NotebookTabLabel`** — exactement le même chantier de propagation que pour
`host_auto_close_tab` (§4.1 2026-09-02) : les 3 sites qui connaissent un
`Host` (`_open_connection_tab()` ×2, `addTab()` legacy pour les sessions
"local") la calculent ; les 2 sites de (dés)division de vue
(`split_notebook()`/`on_btnUnsplit_clicked()`, qui déplacent un onglet
existant sans connaître son `Host`) reportent la valeur déjà résolue de
l'onglet d'origine. Nouveau paramètre `host_post_connect_command` sur
`NotebookTabLabel.__init__()` (`widgets.py`), lancé par
`mark_tab_as_closed()` via un nouvel helper partagé `_launch_hook_command()`
(extrait de l'ancien corps de `run_pre_connect_hook()`, qui délègue
maintenant à ce même helper) — donc, comme pour les notifications de
déconnexion (#109, 2026-09-04), **seulement pour les protocoles VTE**
(SSH/telnet/local/serial/ipmi, via le signal `child-exited`) : RDP/VNC/SPICE
n'ont aujourd'hui aucun point d'accroche commun pour "connexion terminée" —
limitation documentée dans `features.md` §4.2/§2.6 plutôt que masquée.
Aucune option pour désactiver les hooks globalement ni validation/sandboxing
de la commande (même niveau de confiance que `pre_connect_command` et que
`commands` du cluster). `python3 -m py_compile` propre sur les 4 fichiers
modifiés (`models.py`, `gcm4_core.py` — docstring seulement,
`gnome_connection_manager.py`, `widgets.py`), `ruff check` sans nouvelle
erreur (15 préexistantes sur ces fichiers, inchangées, aucune sur le code
ajouté), `ruff format --diff` sans écart sur les lignes ajoutées, aucun
import circulaire nouveau (`tools/check_circular_imports.py`, 38 modules).
85 tests toujours verts dans `tests/test_gcm4_core.py` (inchangé : aucun
test nouveau, `resolve_connection_hook_command()` était déjà testée pour les
deux sens). Câblage GTK non exécuté en conditions réelles (pas de GTK/VTE
dans cet environnement de travail, comme pour le reste du projet).

---
*Note de journal d'origine (claude.md) : « Il y a une session (2026-09-08) : scripting après connexion (#116) — volet « après », symétrique du volet « avant ». »*

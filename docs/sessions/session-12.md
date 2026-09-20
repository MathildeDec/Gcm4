# Session 12 — 2026-09-04 — Cluster — historique de commandes (audit, déjà fait)

**Il y a huit sessions (2026-09-04)** : cluster — historique de commandes,
backlog §4.2 (urgence faible, ligne « liste déroulante, masquage de saisie,
historique commandes ») → déjà fait. Trouvé en reprenant l'audit textuel du
backlog (même réflexe que pour #114 et le 2026-09-01) : `Wcluster.
txtCommands1.history` (simple liste Python, initialisée dans `__init__()`)
est alimenté a chaque envoi par `send_cluster_commands()`
(`widget.history.append(gcm4_core.mask_cluster_command(text))` — déjà la
valeur masquée, cf. le marqueur `#P=` de la session du 2026-09-01) ;
CTRL+UP/CTRL+DOWN dans `on_txtCommands_key_press_event()` fait défiler
`widget.history_index` de façon circulaire. Mécanisme antérieur à toutes
les sessions de ce journal — la session du 2026-09-01 modifiait déjà ce qui
est *poussé* dans `widget.history` sans jamais relever que le rappel
lui-même répondait déjà à ce point du backlog. ⚠️ Limite non résolue :
purement en mémoire, perdu à la fermeture du dialogue/redémarrage — pas de
persistance sur disque. Le reliquat « liste déroulante » de la même ligne
backlog n'a **pas** été implémenté cette session : intitulé ambigu, au moins
deux lectures raisonnables sans indice dans le code pour trancher (liste de
commandes prédéfinies/favorites vs. présentation alternative de l'historique
déjà existant) — reformulé en item à confirmer avec l'auteure plutôt que
deviné. Aucun changement de code cette session — uniquement `features.md`
(nouvelle entrée §4.1, ligne §4.2 rétrécie à « liste déroulante » seule) et
ce fichier.

---
*Note de journal d'origine (claude.md) : « Il y a huit sessions (2026-09-04) : cluster — historique de commandes, backlog §4.2 (urgence faible) → déjà fait. »*

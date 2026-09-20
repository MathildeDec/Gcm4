# Session 15 — 2026-09-06 — Comparaison PATTERNS-COMPARISON.md

**Il y a cinq sessions (2026-09-06)** : pas une tâche de `features.md` —
demande explicite de comparer `PATTERNS.md` (catalogue de conventions
d'un projet tiers, « project-skeleton », sans lien de filiation avec GCM)
au code et à la doc réels de ce dépôt, section par section, avec
vérification par grep/lecture plutôt que par supposition. Nouveau fichier
`PATTERNS-COMPARISON.md` à la racine (12 sections passées en revue,
chacune classée implémenté+documenté / implémenté non documenté / non
implémenté documenté comme choix délibéré / non implémenté et non
documenté / non applicable, avec citation précise de fichier/ligne à
chaque fois). Trouvailles les plus notables, vérifiées en conditions
réelles : `.pre-commit-config.yaml` ne contient **aucun hook pytest**
(seulement ruff, hygiène de base, et le détecteur de cycles d'imports) —
la suite de tests ne tourne jamais automatiquement au commit, contrairement
à ce qu'on pourrait supposer vu la rigueur du reste du dépôt ; le menu
« Quitter » (`on_salir1_activate`) duplique la logique de fermeture de
`on_wMain_destroy`/`on_wMain_delete_event` **sans** la confirmation
« consoles ouvertes, quitter quand même ? » — divergence de comportement
concrète, jamais signalée ; `utils.py::GCMBase.run()` gère Ctrl+C par un
`try/except KeyboardInterrupt: pass` nu autour de `Gtk.main()`, jamais
rattaché à un chemin de fermeture propre ; reproduit à nouveau (déjà
documenté dans `features.md`, mais pas sous cet angle précis) que
`pytest tests/` sans exclusion de `test_gcm.py` bloque la collecte
**entière**, y compris les 65 tests des autres fichiers, sans aucun
garde-fou type `conftest.py` pour l'isoler. Aucune ligne de code changée
cette session — uniquement le nouveau fichier d'analyse et ce journal.

---
*Note de journal d'origine (claude.md) : « Il y a cinq sessions (2026-09-06) : pas une tâche de features.md — demande explicite de comparer PATTERNS.md au code et à la doc réels de ce dépôt. »*

# Session 03 — option CLI --config (#80)

Date non précisée dans le journal d'origine (entre la session 02 et la
session 04 du 2026-08-30) — reprise telle quelle, sans date inventée.

## Fonctionnalité livrée

| Config CLI `--config` (#80) | ✅ Fait (2026-08-30) — nouvelle fonction pure `_resolve_config_dir(argv, default_home)` (via `argparse`, `parse_known_args`) reconnaît `--config PATH` / `--config=PATH` / `-c PATH` et redéfinit `CONFIG_DIR`/`CONFIG_FILE`/`KEY_FILE` en conséquence ; les arguments non reconnus (spécificateurs d'hôte `groupe/nom` de la boucle historique dans `Wmain.__init__`) sont préservés tels quels dans `sys.argv` — comportement CLI existant inchangé. 7 tests ajoutés dans `tests/test_gcm.py::TestResolveConfigDir`, testable sans stub GTK/VTE (même principe que `_compute_zoom_size`, §4.1 ligne précédente) |

---
*Note de journal d'origine (claude.md) : « Il y a dix-sept sessions : option CLI --config PATH (#80). »*

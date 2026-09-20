# Session 09 — 2026-09-02 — Fermeture automatique d'onglet (#77) par hôte

Le réglage global (Jamais/Toujours/Seulement en sortie propre) avait été
retrouvé déjà en place lors de l'audit de la session précédente
(`session-07.md`). Cette session ajoute la surcharge par hôte.

## Travail livré

| Fermeture automatique d'onglet (#77) | ✅ Fait, y compris le volet par host (2026-09-02) — préférence globale `conf.AUTO_CLOSE_TAB` (Jamais/Toujours/Seulement en sortie propre, menu Préférences, trouvée lors de l'audit du 2026-09-01) **et** surcharge par hôte : nouveau champ `Host.auto_close_tab` (`""` hérite du réglage global, `"0"`/`"1"`/`"2"` le surchargent — persisté en INI sous la clé `auto-close-tab`, `HostUtils.load_host_from_ini`/`save_host_to_ini` dans `models.py`), exposé dans « Éditer hôte » via le combo `cmbAutoCloseTab` (visible seulement pour les protocoles VTE, même condition que le champ `TERM` existant). Résolution centralisée dans une fonction pure `gcm4_core.resolve_auto_close_tab(host_override, global_default)` — testable sans stub GTK, même pattern que `resolve_cluster_command()` — appelée depuis `NotebookTabLabel.effective_auto_close_tab()` (`widgets.py`), lui-même utilisé par `mark_tab_as_closed()` à la place de l'ancienne lecture directe de `conf.AUTO_CLOSE_TAB`. La surcharge est propagée aux 5 sites de création de `NotebookTabLabel` dans `gnome_connection_manager.py` : les 3 qui connaissent un `Host` lui passent `host.auto_close_tab`, les 2 sites de (dés)division de vue (`split_notebook()`/`on_btnUnsplit_clicked()`, qui déplacent un onglet existant sans connaître son `Host`) reportent la surcharge de l'onglet d'origine plutôt que de la perdre silencieusement. 4 tests dans `tests/test_gcm4_core.py::TestResolveAutoCloseTab` (repli sur le global, surcharge valide prioritaire, valeur invalide/`None` → repli silencieux, type de retour toujours `int`) |

---
*Note de journal d'origine (claude.md) : « Il y a onze sessions (2026-09-02) : fermeture automatique d'onglet (#77) par host (Host.auto_close_tab, gcm4_core.resolve_auto_close_tab(), 4 tests), détail §4.1. »*

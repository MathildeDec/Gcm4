# Session 45 (2026-09-18) — Audit de `plugins/ssh/gtk4.py`

## Contexte

À l'issue de la session-44 (portage de `button-press-event`, deuxième des
quatre signaux de l'éditeur inline `CellTextView`), trois chantiers
restent ouverts pour la migration GTK4, sans ordre tranché avec
l'auteure :

1. le couple `focus-out-event`/`populate-popup` (dernier des quatre
   signaux de l'éditeur inline, le plus risqué — bloqué sur une question
   de comportement d'exécution GTK4 invérifiable dans cet environnement) ;
2. `plugins/ssh/gtk4.py` (portage effectif des widgets du plugin pilote
   SSH — sa partie logique, `plugins/ssh/core.py`, a été extraite dès la
   session-26) ;
3. RDP (le point de rupture le plus incertain du cœur, `Gtk.Socket`/XEmbed
   supprimé en GTK4 sans équivalent direct).

Conformément à `CONSIGNES-AGENTS-IA.md` (« ne pas trancher seul une
ambiguïté ») et à la discipline déjà appliquée aux audits précédents
(sessions-28/29/38/42 : auditer avant de coder quand le périmètre réel
d'un chantier n'a jamais été détaillé), cette session porte sur l'un des
deux chantiers audit-able sans décision de produit préalable :
`plugins/ssh/gtk4.py`. Le couple `focus-out-event`/`populate-popup` a déjà
été audité (session-42) et RDP appartient à un chantier séparé et plus
incertain (§3.4) ; l'audit de `plugins/ssh/gtk4.py`, jamais fait, était la
case manquante la plus naturelle avant de proposer un ordre entre les
trois.

## Ce qui a été fait

### 1. Inventaire des fichiers concernés

`plugins/ssh/gtk4.py` doit, selon la décision actée en §3.0-bis, regrouper
les dialogues/widgets GTK3 aujourd'hui à la racine du dépôt :

- `ssh_config_editor.py` (1379 lignes) — éditeur `~/.ssh/config`
- `ssh_key_manager_dialog.py` (2678 lignes) — gestionnaire de clés SSH
- `key_picker_dialog.py` (378 lignes) — sélecteur de clé privée

Soit 4435 lignes au total, aucune encore auditée ni portée.
`plugins/ssh/core.py` (extrait en session-26, zéro import GTK) n'est pas
concerné.

### 2. Vérification du point de rupture `Gtk.Dialog.run()`

Bonne surprise : recherche textuelle des trois fichiers, aucun appel
direct `.run()` sur un `Gtk.Dialog` — tous passent déjà par
`utils.run_dialog_sync()`, comme partout ailleurs dans le dépôt depuis
l'audit de la session-28. `KeyPickerDialog` documente même ce choix dans
sa propre docstring d'exemple (`run_dialog_sync(dlg)  # cf.
utils.run_dialog_sync — remplace .run(), supprimé en GTK4`). Le point de
rupture le plus structurant du cœur (§3.2) est donc déjà résolu pour ce
plugin aussi, sans travail supplémentaire à prévoir sur cet axe précis.

### 3. Recherche des ruptures d'API distinctes

Grep ciblé des motifs GTK3-only connus pour être supprimés ou changés de
signature en GTK4, puis vérification de chacun auprès de sources
officielles (guide de migration GNOME, documentation de classe GTK4,
bindings générés depuis les headers C) avant de les consigner :

- `show_all()` — 15 occurrences (6 + 8 + 1) — supprimé en GTK4, confirmé
  par le commit du guide de migration officiel GNOME référencé dans
  `docs/gtk4-migration.md` §3.7.
- `set_border_width()` — 4 occurrences, dans `ssh_key_manager_dialog.py`
  uniquement — `Gtk.Container`/`border-width` supprimé en GTK4, confirmé
  par un correctif upstream `avahi-ui` cité en §3.7.
- `Gtk.Clipboard.get(...)` — 2 occurrences (1 par fichier concerné) —
  classe retirée, section dédiée du guide de migration officiel
  (« Replace GtkClipboard with GdkClipboard »).
- `dlg.get_filename()` — 3 occurrences, `ssh_key_manager_dialog.py` — la
  méthode n'apparaît plus dans la liste des méthodes de l'interface
  `Gtk.FileChooser` en GTK4 (vérifié sur la documentation PyGObject de
  l'interface).
- `set_current_folder(str(...))` — 2 occurrences, même fichier —
  signature changée pour prendre un `Gio.File`, vérifié sur les bindings
  Rust/Vala générés depuis les headers GTK4.
- `Gtk.FileChooserDialog(...)` — 3 occurrences, même fichier — classe
  encore présente en GTK4 mais dépréciée depuis 4.10 au profit de
  `Gtk.FileDialog` (API asynchrone).

Chacun de ces points est distinct des « décorations » de layout
(`pack_start()`/`pack_end()`/`.add()`, ~90 occurrences cumulées) : ceux-ci
seront de toute façon réécrits en bloc par la Stratégie B (réécriture
complète, déjà actée en §3.0/§3.3), sans valeur ajoutée à les verrouiller
un par un — contrairement aux six points ci-dessus, chacun remplaçable
par un mécanisme GTK4 précis et distinct.

### 4. Question d'architecture identifiée, non tranchée

Pour le trio `Gtk.FileChooserDialog`/`get_filename()`/
`set_current_folder()`, deux lectures coexistent sans indice dans le code
pour trancher entre elles : adapter a minima l'existant (rester sur
`Gtk.FileChooserDialog`, encore utilisable malgré sa dépréciation) ou
réécrire directement vers `Gtk.FileDialog` (l'API recommandée, mais
asynchrone — changerait la forme des deux appelants,
`_on_designate_ca()`/`_on_import_ca()`, qui enchaînent aujourd'hui
synchroniquement `run_dialog_sync()` puis le traitement du résultat).
Consigné dans `docs/gtk4-migration.md` §3.7 comme point à confirmer avec
l'auteure, au même titre que l'ordre des trois chantiers restants.

### 5. Nouveau verrou de non-régression

`tests/test_ssh_gtk4_baseline.py` (3 tests / 18 sous-tests) :

- `test_rupture_marker_counts_match_baseline` — compte exact de chacun
  des six marqueurs de rupture ci-dessus, par fichier.
- `test_gtk3_lock_still_present_on_all_three_files` — confirme que les
  trois fichiers verrouillent toujours GTK3
  (`gi.require_version("Gtk", "3.0")`), documentant l'état « portage non
  commencé » plutôt qu'une régression.
- `test_dialog_run_rupture_already_resolved_here_too` — confirme
  l'absence de tout appel direct `.run()` sur un `Gtk.Dialog`, sur le même
  principe que `tests/test_gtk4_core_rupture_points.py` pour le cœur.

Ce fichier ne peut pas importer les trois fichiers concernés (verrou GTK3
actif, GTK3 absent de cet environnement) : mêmes limites et même
principe de scan textuel que
`tests/test_gtk4_context_menus_baseline.py`/
`tests/test_gtk4_inline_editor_baseline.py`.

## Pas fait cette session

- Aucun portage de code : conformément à `CONSIGNES-AGENTS-IA.md`, un
  chantier de cette taille (4435 lignes, trois fichiers jamais touchés,
  une question d'architecture ouverte) n'est pas entamé à l'aveugle sans
  confirmation de l'auteure sur son tour de priorité face aux deux autres
  chantiers restants (`focus-out-event`/`populate-popup`, RDP) et sur le
  choix `FileChooserDialog` vs `FileDialog`.
- Les décomptes `pack_start()`/`pack_end()`/`.add()` ne sont pas
  verrouillés ligne à ligne (voir §3.7 pour la justification) — seuls
  leurs totaux sont mentionnés, à titre de mesure d'ampleur.

## Vérifications

- `ruff check tests/test_ssh_gtk4_baseline.py` / `ruff format --check` :
  propres.
- Suite de tests hors `test_gcm.py` (GTK3 absent de cet environnement) :
  **274 tests / 77 sous-tests**, tous passants (271/59 avant cette
  session + 3 tests/18 sous-tests nouveaux).
- `tools/check_circular_imports.py` : 42 modules, aucune régression
  (fichier de test sans import de module applicatif au niveau module).

## Reste

Ordre entre les trois chantiers restants (`focus-out-event`/
`populate-popup`, `plugins/ssh/gtk4.py` — désormais audité, RDP) toujours
à confirmer avec l'auteure. Pour `plugins/ssh/gtk4.py` spécifiquement, en
plus de l'ordre : le choix `Gtk.FileChooserDialog` adapté vs. réécriture
vers `Gtk.FileDialog` (§3.7).

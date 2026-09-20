# Session 42 — 2026-09-18 — Audit du point 4 : éditeur inline `CellTextView`, correction de terminologie

Consigne : « Continuer les features à faire. Fait évoluer les fichiers de
suivi, de tests et de documentation. Livraison du zip horodaté sans passer
à la suite » — même discipline récurrente que les sessions précédentes.

## Choix de la feature

Le reste du backlog « urgence haute » (SFTP, master password, arbitrage
`snmp_push_core.py`, six choix de noms pour le renommage gcm4) reste
bloqué sur des décisions produit non tranchables seul, inchangé depuis les
sessions 39/40/41.

Pour la migration GTK4, les trois sites du point 3 (déclenchement
`Gtk.GestureClick`) sont désormais tous portés (sessions 39/40/41). Le
backlog documentait comme seul point restant, hors `plugins/ssh/gtk4.py`
et RDP, « le cas `Gtk.Entry`/`populate-popup` » (point 4, issu de l'audit
session-29, §3.6-ter, item 5 du tableau) — jamais détaillé au-delà d'une
ligne de tableau. C'est le candidat naturel de cette session : dernier
élément isolé de l'audit historique des menus contextuels, non encore
traité.

## Réalisé

### Vérification du code réel avant de coder — même discipline que les audits sessions 28/38

Avant tout portage, recherche textuelle du site réel
(`widgets.py::MultilineCellRenderer._on_editor_populate_popup`). Deux
découvertes, aucune ne permettant de coder sereinement cette session :

1. **Terminologie inexacte depuis la session-29** : le widget concerné
   n'est pas un `Gtk.Entry` mais `CellTextView`, une sous-classe de
   `Gtk.TextView` + `Gtk.CellEditable` (éditeur inline utilisé pour
   renommer un hôte/dossier par double-clic dans `treeServers`).
   `Gtk.Entry`/`GtkText` n'apparaît nulle part dans ce chemin de code —
   vérifié par recherche exhaustive.
2. **Périmètre réel plus large que documenté** : `CellTextView.
   do_start_editing()` (`widgets.py:1819-1822`) connecte non pas un seul
   signal GTK3-only mais quatre, consécutifs :
   - `focus-out-event` → `_on_editor_focus_out_event` (annule l'édition à
     la perte de focus, sauf si `_in_editor_menu`)
   - `key-press-event` → `_on_editor_key_press_event` (Entrée valide,
     Échap annule)
   - `populate-popup` → `_on_editor_populate_popup` (positionne
     `_in_editor_menu` pendant que le menu contextuel natif de l'éditeur
     est ouvert — n'ajoute aucun item, contrairement à l'usage habituel
     de ce signal)
   - `button-press-event` → `_on_editor_pressed` (retourne toujours
     `True`, contournement d'un bug connu de VTE/GTK — déjà catalogué
     comme site « décoy » du point 3 dans
     `tests/test_gtk4_context_menus_baseline.py`, vis-à-vis du
     *déclenchement de menu applicatif* seulement, pas de sa propre
     migration GTK4)

### Recherche des équivalents GTK4

Trois des quatre signaux ont un remplacement direct et documenté :
`Gtk.EventControllerFocus` (signal `leave`), `Gtk.EventControllerKey`
(signal `key-pressed`), `Gtk.GestureClick`. Le quatrième,
`populate-popup`, est **supprimé en GTK4** pour `Gtk.TextView`/`Gtk.Text`
et remplacé par un mécanisme différent, `set_extra_menu(Gio.MenuModel)`
(confirmé sur `docs.gtk.org`/`valadoc.org`) — mais ce mécanisme sert à
*ajouter* des items au menu contextuel, pas à *observer* son ouverture/
fermeture, qui est le seul usage fait ici (`_in_editor_menu` ne peuple
jamais le menu, il l'observe uniquement pour ne pas annuler l'édition en
cours).

La question dont dépend une solution correcte — est-ce que le
`Gtk.Popover` interne du menu contextuel natif GTK4 déclenche, à son
ouverture, un `leave` sur `Gtk.EventControllerFocus` du widget porteur,
comme le faisait l'ancien `Gtk.Menu` top-level avec `focus-out-event` ? —
n'a pas de réponse certaine trouvée par la recherche de cette session ;
plusieurs sources suggèrent qu'un `Gtk.Popover` attaché (`set_parent()`)
ne vole pas nécessairement le focus clavier de son widget porteur de la
même façon qu'un ancien menu top-level, ce qui simplifierait le portage
(le contournement `_in_editor_menu` pourrait devenir inutile), mais ceci
n'est pas vérifiable empiriquement dans cet environnement de travail
(GTK4 absent).

### Décision : pas de portage de code cette session

Deux raisons cumulées, dans la continuité directe de la décision prise en
session-29 pour les menus applicatifs :

1. Le périmètre réel (4 signaux, 3 mécanismes de remplacement distincts)
   dépasse largement ce que documentait §3.6-ter (une seule ligne de
   tableau, présentée comme un simple renommage de signal).
2. Le point le plus délicat (`populate-popup`) dépend d'un comportement
   d'exécution GTK4 invérifiable ici, sur une fonctionnalité de base très
   utilisée (renommage inline d'un hôte/dossier) — coder à l'aveugle
   risquerait une régression silencieuse en production, contraire à
   `CONSIGNES-AGENTS-IA.md`.

Livré à la place, même principe que l'audit session-29 :
l'inventaire corrigé (`docs/gtk4-migration.md` §3.6-undecies) et un
nouveau verrou textuel de non-régression.

## Tests

- Nouveau fichier `tests/test_gtk4_inline_editor_baseline.py`
  (`TestInlineEditorSignalBaseline`, 2 tests / 4 sous-tests) :
  - `test_signal_connections_match_baseline` — verrouille les 4
    occurrences exactes des `connect()` GTK3-only de `CellTextView.
    do_start_editing()`, même principe que
    `EXPECTED_GESTURECLICK_TRIGGER_SITES` (check-list vivante pour un
    futur portage : chaque ligne devra être ajustée au fur et à mesure).
  - `test_editor_widget_is_not_a_gtk_entry` — verrouille la correction de
    terminologie (présence de `class CellTextView(Gtk.TextView,
    Gtk.CellEditable):`, absence de `Gtk.Entry(` dans le corps de la
    classe).
- `tests/test_gtk4_context_menus_baseline.py` : note « Mise à jour
  session-42 » ajoutée au docstring du module, référençant la correction
  et le nouveau fichier — aucun compteur existant modifié (ce fichier
  couvre les menus applicatifs et leur déclenchement, périmètre distinct
  de l'éditeur inline d'une cellule).
- `ruff check`/`ruff format --check` : 0 erreur sur le fichier nouveau et
  le fichier modifié. `flake8` (limite 99 caractères, `.flake8`) : 0
  nouvelle erreur sur le fichier nouveau ; le fichier modifié
  (`test_gtk4_context_menus_baseline.py`) conserve ses 2 erreurs `E501`
  préexistantes (lignes de commentaire dans
  `EXPECTED_GTK_MENU_INSTANTIATIONS`/`EXPECTED_LEGACY_POPUP_CALLS`,
  antérieures à cette session, hors des lignes effectivement touchées —
  non corrigées, conformément à `CONSIGNES-AGENTS-IA.md` §6, qui limite
  la correction aux lignes du diff sur un fichier existant modifié).
  `gnome_connection_manager.py` : toujours 182 erreurs `flake8`, chiffre
  inchangé (aucun fichier concerné par cette session).
- `tools/check_circular_imports.py` : aucun import circulaire introduit
  (41 modules analysés, inchangé).
- Suite complète hors `tests/test_gcm.py` (GTK3 requis, non disponible
  ici) : **254 tests / 46 sous-tests**, tous passants (252/42 avant cette
  session).

## Documentation mise à jour

- `docs/gtk4-migration.md` — nouvelle section §3.6-undecies (inventaire
  détaillé des 4 signaux, table des équivalents GTK4, question ouverte
  sur le focus du `Gtk.Popover` interne, décision de ne pas coder cette
  session) ; correction ajoutée en fin de §3.6-decies pointant vers cette
  nouvelle section.
- `CLAUDE.md` — nouveau point « 1-undecies » dans « Prochaine étape ».
- `docs/features-backlog.md` — nouvelle ligne dans « Déjà fait » (l'audit
  lui-même) et mise à jour de la ligne « Migration GTK4 » dans « Pas
  encore fait » (correction de terminologie, périmètre réel du point 4
  précisé à 4 signaux).
- `CHANGELOG.md` — entrée « 2026-09-18 » dans « Non publié » ; plage de
  dates de l'en-tête de section étendue au 2026-09-18.

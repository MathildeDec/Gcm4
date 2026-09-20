# Session 28 — 2026-09-10 — Audit des points de rupture GTK4 du cœur

Consigne : « Continue les features à faire. Fait évoluer les fichiers de
suivi, de tests et de documentation. Livraison du zip horodaté sans passer
à la suite » — même discipline récurrente que les sessions précédentes.

## Choix de la feature

La session-27 laissait le master password bloqué sur une décision produit,
et la quasi-totalité du reste de l'urgence haute du backlog
(`docs/features-backlog.md`) est marquée « à confirmer avec l'auteure avant
d'implémenter ». Le chantier prioritaire du projet, la migration GTK4
(`docs/gtk4-migration.md`), a un point d'entrée clair et non bloqué : §3.6
liste trois points de rupture restants dans `gnome_connection_manager.py`
(`Gtk.Dialog.run()`, `GtkMenuBar`/`GtkMenu`, `Gtk.Widget.reparent()`),
chacun explicitement qualifié de « vraisemblablement une session à lui
seul ». Avant de choisir lequel coder, vérification systématique de leur
état réel dans le code — même discipline que les audits des
sessions-07/20/23/24, qui avaient déjà trouvé plusieurs items du backlog
« déjà faits » à l'audit.

## Constat avant codage

Un `grep` ciblé sur chacun des trois points a immédiatement changé la
donne :

- **`Gtk.Dialog.run()`** : `utils.run_dialog_sync()` existe déjà (palliatif
  `GLib.MainLoop` documenté) et **tous** les appelants du fichier
  l'utilisent déjà — un `grep -n "\.run("` exhaustif sur
  `gnome_connection_manager.py`/`utils.py` ne remonte que ce mécanisme,
  `subprocess.run` (détection du thème desktop, 3 occurrences) et
  `w_main.run()` (boucle GTK principale). Rien à coder : déjà résolu.
- **`GtkMenuBar`/`GtkMenu`** : la docstring de
  `Wmain._build_primary_menu()` (ligne 2189) affirme sans détour construire
  « le menu hamburger qui remplace l'ancien GtkMenuBar (palier 2) », avec
  `Gio.Menu`/`Gio.SimpleAction` et un `Gtk.MenuButton` câblé
  (`self._build_primary_menu()` appelé à l'init, `btnPrimaryMenu.
  set_menu_model(menu)`). Aucun `Gtk.MenuBar(` nulle part dans le fichier.
  **Aucune trace de ce travail** dans `gtk4-migration.md`,
  `features-backlog.md`, `CLAUDE.md`, `CHANGELOG.md` ou un quelconque
  fichier de session — le mot « palier » (qui suppose une numérotation
  d'étapes) n'apparaît nulle part ailleurs que dans ce commentaire de code.
  Conclusion : du travail réel a été fait sur ce point (par une session non
  journalisée, ou hérité d'avant le journal de suivi) sans jamais être
  répercuté dans la documentation de suivi — l'écart inverse de celui
  habituellement trouvé par les audits précédents (documentation en avance
  sur un travail non fait, plutôt que backlog qui ignore un travail fait).
- **`Gtk.Widget.reparent()`** : une seule occurrence
  (`grid.reparent(vbox)`), dans `_inject_spice_frame_LEGACY`. Un
  `grep -n "_inject_spice_frame_LEGACY"` confirme qu'elle n'est **jamais
  appelée** ailleurs dans le dépôt ; le chemin réellement actif est
  `_inject_spice_frame` (méthode juste au-dessus, `pass  # gardé pour ne
  pas casser d'éventuels appels hérités`, documentée « widgets SPICE
  maintenant dans le glade »). Le commentaire immédiatement au-dessus de la
  méthode morte affirmait par ailleurs qu'« il est conservé sous forme de
  commentaire pour référence » — inexact : c'était du code Python actif
  (non commenté), pas un commentaire, malgré ce que le texte prétendait.

Un `grep` complémentaire sur les autres lignes du tableau §3.2 (par
prudence, pour ne pas s'arrêter aux trois points annoncés) a aussi trouvé
un écart inverse : la ligne « Icônes `Gtk.STOCK_*` restantes » affirmait le
nettoyage déjà fait (étape 2 GTK3 du fork), mais
`plugins/plugin_spice.py::_ask_password_dialog` utilisait encore
`Gtk.STOCK_CANCEL`/`Gtk.STOCK_OK` — jamais corrigé alors que le même
nettoyage était déjà appliqué ailleurs (`plugins/plugin_ssh.py`,
`add_buttons()` avec des libellés traduits littéraux).

## Décision

Une session bornée à un vrai chantier de portage (par ex. les menus
contextuels restants, voir « Non traité ») aurait été possible, mais le
plus grand service à rendre au projet cette session était de **corriger
l'inventaire avant de coder dessus** — coder une réécriture de
`Gtk.Dialog.run()` ou du menu principal aurait été strictement inutile
(déjà fait), et l'écart de documentation risquait de faire perdre une
session future à la même chose. Périmètre retenu :

1. Corriger les deux vrais bugs trouvés en cours d'audit (méthode morte
   contenant un appel API supprimé en GTK4 ; constantes stock oubliées) —
   petits, sûrs, sans ambiguïté produit.
2. Verrouiller les quatre constats par des tests de non-régression.
3. Mettre à jour toute la documentation de suivi pour qu'elle reflète l'état
   réel, avec le même luxe de détail que si le code avait été écrit cette
   session (c'est bien le cas pour les points 1-2 ci-dessus).

## Ce qui a été livré

- **`gnome_connection_manager.py`** : suppression de
  `_inject_spice_frame_LEGACY` (~108 lignes de code mort, jamais appelée,
  contenant l'unique `.reparent()` du fichier) et du commentaire inexact
  qui prétendait qu'elle n'était qu'un commentaire. Remplacé par une note
  courte dans le bloc « Méthodes supprimées » déjà présent juste
  au-dessus, avec renvoi à l'historique git. `_inject_spice_frame`
  (chemin réellement actif, no-op documenté) est **inchangé**.
- **`plugins/plugin_spice.py`** : `_ask_password_dialog()` — remplacement
  de `Gtk.STOCK_CANCEL`/`Gtk.STOCK_OK` par `_("Cancel")`/`_("OK")`
  (libellés traduits littéraux), sur le modèle déjà en place dans
  `plugins/plugin_ssh.py`. Docstring complétée d'une note expliquant le
  changement.
- **`tests/test_gtk4_core_rupture_points.py`** (nouveau, 7 tests) : scan
  textuel du code source (aucun import de `gi`/`Gtk` requis, même principe
  que `test_plugin_base.py::test_no_require_version_call_in_source`) :
  - `TestReparentRuptureResolved` (2 tests) — aucun `.reparent(` ni
    définition de `_inject_spice_frame_LEGACY` dans le fichier.
  - `TestMenuBarRuptureResolved` (2 tests) — aucun `Gtk.MenuBar(` ;
    `_build_primary_menu` présent et câblé (appelé à l'init, `set_menu_
    model` utilisé).
  - `TestDialogRunRuptureResolved` (1 test) — chaque occurrence de
    `.run(` dans le fichier correspond à un usage connu et sûr
    (`run_dialog_sync`, `subprocess.run`/alias, `w_main.run()`,
    mentions documentaires) ; toute autre occurrence fait échouer le test.
  - `TestNoStockConstantsRemain` (2 tests) — aucune constante
    `Gtk.STOCK_*` ni dans le cœur ni dans `plugins/*.py`.

## Validation

- `pytest` réel sur la suite GTK-free complète + le nouveau fichier :
  **154/154 passés** (147 hérités de la session-27 + 7 nouveaux).
- `python3 -m py_compile` sur les deux fichiers modifiés : syntaxe valide.
- `ruff check`/`ruff format --check` sur le nouveau fichier de test :
  propre. `ruff check` sur `gnome_connection_manager.py` et
  `plugins/plugin_spice.py` : aucune erreur nouvelle introduite par cette
  session (les 3 erreurs pré-existantes de `plugin_spice.py` — tri
  d'imports, `Callable` via `typing` plutôt que
  `collections.abc`, docstring manquante sur un `__init__` non touché —
  sont antérieures et hors du périmètre de cette modification, cf.
  `CONSIGNES-AGENTS-IA.md` §6).
- `tools/check_circular_imports.py` : aucun import circulaire, 37 modules
  analysés (inchangé).

## Non traité dans cette passe

- **Menus contextuels** (`Gtk.Menu` classique — `popupMenu`,
  `popupMenuFolder`, `popupMenuTab`, et le sous-menu « Custom commands »
  exposé par une action-pont depuis le menu hamburger) : point de rupture
  réel et non résolu, nouvellement isolé par cet audit (il était
  auparavant confondu avec le point « menu principal », maintenant résolu).
  GTK4 supprime `Gtk.Menu` tout autant que `GtkMenuBar` ; le remplacement
  attendu (`GtkPopoverMenu` contextuel) reste à faire, une session à part.
- **RDP embarqué** (§3.4) : inchangé, toujours le point le plus incertain
  du chantier GTK4, dépendant d'une vérification externe
  (`GtkFrdp`/repli fenêtre externe).
- **`plugins/ssh/gtk4.py`** (portage effectif des widgets SSH) : inchangé
  depuis la session-26, toujours tributaire de l'avancement du cœur.
- **Renommage GCM → gcm4 dans le code**, **master password (câblage +
  prompt GTK)**, **SFTP**, **arbitrage `ssh_config_editor.py`/
  `snmp_push_core.py`** : inchangés, toujours en attente d'une décision
  produit à confirmer avec l'autrice (voir `docs/features-backlog.md`).

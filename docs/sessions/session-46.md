# Session 46 (2026-09-19) — Audit RDP, correction du diagnostic de §3.4

## Contexte

Dernier des trois chantiers dont l'ordre reste à confirmer avec l'auteure
(couple `focus-out-event`/`populate-popup` — §3.6-undecies —,
`plugins/ssh/gtk4.py` — audité en session-45, §3.7 —, RDP) à ne pas
encore avoir été audité en détail. Cette session applique au chantier RDP
la même discipline que la session-45 pour `plugins/ssh/gtk4.py` :
inventaire du code réel avant tout portage, conformément à
`CONSIGNES-AGENTS-IA.md` (ne pas trancher seul une ambiguïté, ne pas
coder à l'aveugle un point signalé « à confirmer »).

## Ce qui a été fait

1. **Vérification de la prémisse de §3.4.** §3.4 (rédigé le 2026-08-29)
   décrit `GtkFrdp.Display` et un repli `Gtk.Socket`/XEmbed comme deux
   mécanismes coexistants pour l'embarquement RDP, tous deux dépendants de
   X11. Inspection directe du code réellement chargé
   (`plugins/plugin_rdp.py`) : sa propre docstring de classe dit
   explicitement « Seule solution RDP de GCM (pas de fallback) ». Recherche
   textuelle exhaustive sur le dépôt : zéro occurrence de
   `Gtk.Socket`/`GtkSocket`/`/parent-window:` en dehors de
   `tests/test_gcm.py`.

2. **Origine expliquée d'un orphelin déjà connu.** `tests/test_gcm.py`
   contient toujours `TestRdpEmbeddedTabBuildCmd` (teste
   `RdpEmbeddedTab._build_cmd()` et son argument `/parent-window:<XID>`),
   preuve que l'ancien mécanisme XEmbed a bien existé. Mais ni la classe
   `RdpEmbeddedTab` ni `_rdp_socket_available` n'existent plus dans
   `gnome_connection_manager.py`. `_rdp_socket_available` avait déjà été
   repéré comme orphelin en session-36 (`docs/architecture.md` §5 point 5)
   sans qu'on sache à quoi il servait — cette session établit que
   c'était précisément le détecteur X11 de ce repli XEmbed, disparu très
   probablement lors du passage à l'architecture à plugins
   (`plugin_rdp.py` se décrit lui-même comme le « quatrième plugin
   implémenté »). Le sort des tests orphelins (suppression vs
   réintroduction des fonctions) reste à confirmer avec l'auteure, comme
   déjà documenté — cette session en précise l'origine sans le trancher.

3. **Inspection de la bibliothèque vendorisée `gtk-frdp/`.**
   `plugins/plugin_rdp.py` consomme `GtkFrdp.Display` par introspection
   GObject (`gi.require_version("GtkFrdp", "0.2")`). Lecture de la source
   C vendorisée (projet GNOME, Felipe Borges/Marek Kašík, à l'origine pour
   GNOME Boxes) : `FrdpDisplay` est une sous-classe directe de
   `GtkDrawingArea` (peint via Cairo), et une recherche exhaustive dans
   tout `gtk-frdp/src/` ne trouve **aucune** API X11/Xlib. Seule
   `GdkWindow` (type supprimé en GTK4, remplacé par `GdkSurface`) apparaît,
   dans `frdp-session.c` — rupture réelle mais mineure, d'une classe déjà
   bien connue de ce dépôt. En revanche `gtk-frdp/src/meson.build` épingle
   explicitement `dependency('gtk+-3.0')` : la bibliothèque vendorisée ne
   se construit pas contre GTK4 telle quelle aujourd'hui.

4. **Recherche web (2026-09-19).** `gtk-frdp` est un petit projet GNOME
   sans branche ni ticket « GTK4 » identifiable. Signal le plus
   significatif trouvé : GNOME Boxes — dont Felipe Borges (co-auteur de
   `gtk-frdp`) est le mainteneur — vient de terminer sa propre migration
   GTK4/libadwaita (bêta annoncée le 2026-08-03 par F. Borges lui-même).
   L'annonce et sa couverture presse (Phoronix, UbuntuHandbook, itsfoss)
   décrivent en détail le remplacement du widget SPICE (GTK3 → **Libmks**,
   nouvelle bibliothèque dédiée), mais aucune ne mentionne RDP ni
   `gtk-frdp`. Signal réel mais non concluant : le statut GTK4 de
   `gtk-frdp` reste non confirmé, et apparemment non résolu même côté
   mainteneur sept semaines après une migration qui aurait été
   l'occasion naturelle de le clarifier.

5. **Découverte annexe : un quatrième menu contextuel jamais porté.** En
   vérifiant `plugin_rdp.py`, `widgets.build_remote_desktop_context_menu()`
   (le « constructeur générique RDP/VNC/SPICE » de l'audit session-29,
   partagé par les plugins RDP, VNC et SPICE) se révèle toujours construit
   avec deux `Gtk.Menu()` classiques.
   `tests/test_gtk4_context_menus_baseline.py` le documentait déjà
   correctement en creux depuis la session-33 (« Restent hors périmètre
   de ce fichier »), mais le résumé de `CLAUDE.md` pour cette même session
   affirme que « les quatre menus contextuels applicatifs... sont
   désormais tous portés » — inexact pour celui-ci : seuls trois des
   quatre l'ont été. `CLAUDE.md` (nouvelle entrée 1-quindecies) et
   `gtk4-migration.md` §3.8.4 le signalent ; le paragraphe d'origine de
   la session-33 n'a volontairement pas été réécrit.

## Pas fait cette session

Audit et inventaire seulement, conformément à `CONSIGNES-AGENTS-IA.md`.
Aucun code de portage GTK4 écrit pour RDP : la question de fond (statut
GTK4 amont de `gtk-frdp`) n'est pas tranchable depuis ce dépôt, et
décider entre les trois lectures possibles pour `plugins/rdp/gtk4.py`
(forker `gtk-frdp` localement, attendre un portage amont, explorer une
alternative) serait trancher seul un choix d'architecture. Les tests
orphelins de `tests/test_gcm.py` (`RdpEmbeddedTab`,
`_rdp_socket_available`) n'ont pas été touchés — leur sort reste à
confirmer avec l'auteure comme documenté depuis la session-36.

## Vérifications

- Nouveau fichier `tests/test_gtk4_rdp_baseline.py` (3 classes, 6 tests /
  23 sous-tests, tous passants) : disparition confirmée des marqueurs
  XEmbed du code réellement chargé, dépendance actuelle à `GtkFrdp`/GTK3,
  état non porté de `build_remote_desktop_context_menu()`.
- Suite complète hors `tests/test_gcm.py` (GTK3/VTE indisponibles dans cet
  environnement de travail, comme documenté depuis la session-24) :
  **280 tests / 100 sous-tests**, tous passants (274/77 avant cette
  session).
- `ruff check` et `ruff format --check` propres sur le nouveau fichier.
- `tools/check_circular_imports.py` : aucun import circulaire (42 modules
  analysés, inchangé).
- `docs/architecture.md` §2.1 (tableau des protocoles, ligne RDP) et §5
  (écarts doc/code, nouveau point 8) mis à jour pour refléter la
  disparition du repli XEmbed.

## Reste

Les trois chantiers restants du portage GTK4 (couple
`focus-out-event`/`populate-popup`, `plugins/ssh/gtk4.py`, RDP) sont
désormais **tous audités**. Aucun portage de code n'a encore été entamé
sur aucun des trois. ⚠️ Leur ordre de traitement reste entièrement à
confirmer avec l'auteure — de même que, pour RDP spécifiquement, le choix
d'architecture entre forker `gtk-frdp` localement, attendre un portage
amont, ou explorer une alternative (`gtk4-migration.md` §3.8.5). Reste
également ouvert, sans lien direct avec le portage GTK4 lui-même : le
sort des tests orphelins de `tests/test_gcm.py`
(`RdpEmbeddedTab`/`_rdp_socket_available`, `_vm_name_split`), à confirmer
avec l'auteure comme documenté depuis la session-36.

# Session 38 — 2026-09-16 — Audit du déclenchement `Gtk.GestureClick`

Consigne : « Continuer les features à faire. Fait évoluer les fichiers de
suivi, de tests et de documentation. Livraison du zip horodaté sans passer
à la suite » — même discipline récurrente que les sessions précédentes.

## Choix de la feature

Le reste du backlog « urgence haute » (SFTP, master password, arbitrage
`snmp_push_core.py`, six choix de noms pour le renommage gcm4) reste
bloqué sur des décisions produit non tranchables seul. Pour la migration
GTK4, la session-33 avait laissé quatre chantiers ouverts — le
déclenchement `Gtk.GestureClick` (point 3, commun aux quatre menus
contextuels désormais tous portés), le cas `Gtk.Entry`/`populate-popup`
(point 4), `plugins/ssh/gtk4.py`, et RDP — en signalant explicitement que
« l'ordre entre ces chantiers restants [était] toujours à confirmer avec
l'auteure », sans qu'aucune proposition d'ordre n'ait encore été posée
pour ces quatre-là (contrairement aux quatre menus eux-mêmes, où la
session-29 avait déjà proposé `popupMenuTab` en premier).

Faute de proposition existante à suivre, et conformément à
`CONSIGNES-AGENTS-IA.md` (« proposer un plan avant de coder un gros
morceau », « ne pas trancher seul une ambiguïté ») : plutôt que de choisir
arbitrairement l'un des quatre chantiers et d'y coder à l'aveugle, cette
session reproduit la démarche de la session-29 pour le point qui semblait
le plus proche d'être une continuation technique directe du travail déjà
fait (les trois menus contextuels applicatifs venant d'être portés) plutôt
qu'un nouveau sous-système entier (`plugins/ssh/gtk4.py`, RDP) : un audit
exhaustif du point 3, pour poser une proposition d'ordre sur la table
avant qu'une future session ne code quoi que ce soit.

## Réalisé

### Inventaire exhaustif

Recherche textuelle de `button.press.event` dans `gnome_connection_manager.py`
et `widgets.py` (hors `SSH-Studio`/`gtk-frdp`) : 7 occurrences au total,
dont seulement 3 réellement liées au déclenchement d'un menu contextuel
applicatif :

| Site | Fichier:ligne(s) | Menu déclenché |
|---|---|---|
| `v.connect("button_press_event", self.on_terminal_click)` | `gnome_connection_manager.py:2281` et `:3201` | `popupMenu` |
| `treeServers.connect("button-press-event", self.on_tvServers_button_press_event)` | `gnome_connection_manager.py:1159` | `popupMenuFolder` |
| `self.eb.connect("button-press-event", self.popupmenu, label)` | `widgets.py:1172` | `popupMenuTab` **ou** le menu RDP/VNC/SPICE non porté, selon le type d'onglet |

Les 4 sites restants sont des faux positifs textuels sans rapport avec un
menu : bascule du panneau au double-clic sur le séparateur
(`on_hpMain_button_press_event`), ouverture d'un onglet local au
double/triple-clic dans la zone vide du notebook (`on_double_click`, 2
sites), et un contournement de bug GTK dans l'éditeur inline de noms
d'hôtes/groupes (`_on_editor_pressed`, qui ne fait que retourner `True`).

Détail complet des trois sites réels, y compris leurs particularités
respectives (branche Ctrl+clic pour `on_terminal_click`, absence de
branche modificateur pour `on_tvServers_button_press_event`, double menu
possible pour `NotebookTabLabel.popupmenu`) : `docs/gtk4-migration.md`
§3.6-septies.

### Vérification `GtkGestureMultiPress` (GTK3) / `GtkGestureClick` (GTK4)

Recherche auprès de la documentation GTK officielle (`docs.gtk.org`,
`blog.gtk.org`, guide de migration 3→4) : les deux classes ne diffèrent
que par leur nom et par la suppression, en GTK4, de la propriété `area`
(restriction de zone de clic, non utilisée dans ce dépôt) — même signal
`pressed(gesture, n_press, x, y)` dans les deux générations. Une migration
vers `Gtk.GestureMultiPress` est donc possible dès aujourd'hui, en GTK3,
sans attendre le portage du cœur — contrairement à d'autres points de
rupture de ce chantier qui nécessitent le basculement réel de
`gnome_connection_manager.py`.

### Difficulté réelle identifiée

Le signal `pressed` ne transmet que `(gesture, n_press, x, y)` — ni objet
`Gdk.EventButton`, ni numéro de bouton, ni état des modificateurs clavier.
Les trois gestionnaires actuels lisent pourtant `event.button` (clic
droit/gauche), `on_terminal_click` lit en plus `event.get_state()` (test
Ctrl+clic) et passe l'événement tel quel à deux méthodes VTE
(`match_check_event`/`hyperlink_check_event`). La migration devra donc,
pour chaque site, utiliser `Gtk.GestureSingle.set_button()` (fixer le
bouton écouté sur le geste), `gesture.get_current_event_state()` (état
des modificateurs) et `gesture.get_current_event()` (objet `Gdk.Event`
d'origine, nécessaire pour les appels VTE et pour
`remote_menu.popup(...)` côté `widgets.py`) — trois API disponibles sur
`Gtk.EventController` depuis GTK3, mais qui rendent la migration bien
plus qu'un simple renommage de classe malgré la quasi-identité de nom
entre `GtkGestureMultiPress` et `GtkGestureClick`.

### Proposition d'ordre (non tranchée)

`treeServers`/`popupMenuFolder` en premier (seul des trois sites sans
branche dépendant d'un modificateur clavier), puis `on_terminal_click`
(branche Ctrl+clic à porter, mais menu déjà entièrement porté), et
l'étiquette d'onglet en dernier (seule à devoir continuer à alimenter le
menu `Gtk.Menu` legacy des bureaux distants tant que celui-ci n'est pas
lui-même porté).

### Pas codé cette session

Aucun portage de code — ce point touche le déclenchement d'entrée central
de trois widgets différents, sans environnement GTK3/VTE réel disponible
ici pour vérifier empiriquement le résultat, et son ordre par rapport aux
trois autres chantiers GTK4 restants (`plugins/ssh/gtk4.py`, le cas
`Gtk.Entry`/`populate-popup`, RDP) reste à confirmer avec l'auteure.

## Tests

Nouvelle classe `TestGestureClickTriggerBaseline` dans
`tests/test_gtk4_context_menus_baseline.py` : verrouille le nombre exact
des 3 familles de sites réels et des 4 sites voisins hors périmètre,
même principe que les classes de verrouillage déjà présentes dans ce
fichier (`TestContextMenuInstantiationBaseline`,
`TestLegacyPopupSignatureBaseline`). 5 tests / 11 sous-tests dans ce
fichier, tous passants dans cet environnement de travail (aucun import
`gi`/`Gtk`).

## Documentation mise à jour

- `docs/gtk4-migration.md` — nouvelle section §3.6-septies (inventaire
  complet, vérification GTK officielle, difficulté identifiée,
  proposition d'ordre).
- `CLAUDE.md` — nouveau point « 1-septies » dans « Prochaine étape ».
- `docs/features-backlog.md` — nouvelle ligne dans « Déjà fait » et mise à
  jour de la ligne « Migration GTK4 » dans « Pas encore fait ».
- `CHANGELOG.md` — entrée « 2026-09-16 (ter) » dans « Non publié ».

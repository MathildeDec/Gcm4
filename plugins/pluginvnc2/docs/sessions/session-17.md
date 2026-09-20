# Session 17 — 2026-09-11

Suite à session 16 (capture d'écran). Point de départ différent cette
fois : demande explicite de l'utilisateur (« vérifie ce projet [avec
Context7] et ajoute toutes les fonctions manquantes »), plutôt qu'un choix
autonome. « Toutes les fonctions manquantes » n'étant pas une liste
définie — et le projet documentant déjà (`CLAUDE.md`, session 15) qu'il ne
faut pas inventer de fonctionnalité sans besoin réel — la démarche
retenue a été : (1) utiliser le connecteur MCP Context7, désormais
connecté, pour vérifier contre la doc PyGObject/GTK4 à jour quelles API
sont réellement disponibles ; (2) en tirer une liste bornée de candidats
plausibles, strictement côté GTK4 (rien qui dépende d'une extension
protocolaire `asyncvnc2_patched` non livrée dans ce paquet) ; (3)
soumettre ces candidats à l'utilisateur pour confirmation avant
d'implémenter quoi que ce soit — plutôt que produire un diff massif non
revu sur la base d'une liste auto-décidée. L'utilisateur a retenu les deux
candidats proposés : raccourcis clavier globaux, et reconnexion
automatique après coupure.

## Recherche Context7

Requêtes faites contre `/websites/api_pygobject_gnome` avant de proposer
quoi que ce soit :
- `Gtk.EventControllerKey` / raccourcis globaux → a confirmé l'existence
  de `Gtk.ShortcutController`, `Gtk.ShortcutTrigger.parse_string()`
  (syntaxe accélérateur `<Control><Alt>End`), `Gtk.CallbackAction.new()`
  (signature exacte `(widget, variant, data) -> bool`), `Gtk.Shortcut.new()`.
- `Gdk.Clipboard` image (`read_texture_async`) → confirmé disponible côté
  GTK4, mais écarté : `asyncvnc2` (le fork livré dans ce paquet) n'expose
  que `client.clipboard.text`/`.write(text)`, texte uniquement — l'API
  GTK4 existe mais le protocole ne suit pas, donc hors périmètre ici (cf.
  `docs/features-backlog.md` § « Dépendance »).

## Feature 1 — Raccourcis clavier globaux

`<Shift>F12` (capture d'écran), `F11` (plein écran),
`<Control><Alt>End` (Ctrl+Alt+Suppr — convention déjà répandue chez les
clients VNC : la vraie combinaison locale est interceptée par le système
D'HÔTE avant d'atteindre l'application, ce repli est la seule façon
réaliste de la déclencher à distance).

Piège identifié et documenté avant même d'écrire le code (pas un bug
trouvé après coup, contrairement à la plupart des entrées de
`docs/pieges.md`) : `VncDisplay._on_key_pressed()` retourne TOUJOURS
`True`. Un `Gtk.ShortcutController` posé sans précaution sur `VncTab` (ou
pire, sur `VncDisplay` lui-même) en phase par défaut ne se déclencherait
JAMAIS quand `VncDisplay` a le focus, puisque la phase TARGET du widget
ciblé avalerait l'événement en premier. Solution :
`self.shortcuts.set_propagation_phase(Gtk.PropagationPhase.CAPTURE)` sur
le contrôleur posé sur `VncTab` (ancêtre) — la phase CAPTURE (racine →
cible) s'exécute avant la phase TARGET du widget effectivement visé, donc
avant que `_on_key_pressed` n'ait l'occasion d'avaler l'événement. Détail
complet dans `docs/pieges.md`.

Table `VncTab._GLOBAL_SHORTCUTS` (accélérateur, nom de méthode) extraite
en donnée de classe pure, résolue par `getattr` dans
`_setup_global_shortcuts()` — vérifiable par test sans instancier de vrai
`Gtk.ShortcutController`. Trois méthodes `_shortcut_action_*` en pure
délégation vers des méthodes déjà existantes et déjà testées
(`_on_screenshot_clicked`, `_toggle_fullscreen`,
`display.send_ctrl_alt_del()`) — pas de nouvelle logique métier propre.

## Feature 2 — Reconnexion automatique après coupure

Ne se déclenche que si `VncStatus.ERROR` ET la session avait déjà été
pleinement établie au moins une fois (`_had_connected_before`, mis à jour
dans `_set_status` dès CONNECTED). Volontairement PAS sur un échec de
connexion initiale (auth refusée, hôte injoignable dès le départ) : ça ne
se réparerait pas tout seul, et une boucle de reconnexion automatique
avec le même mot de passe risquerait un verrouillage de compte côté auth
Apple ARD. Jamais sur `VncStatus.DISCONNECTED` non plus — c'est
précisément ce que pose un `stop()`/`close()` volontaire, y compris
DANS un `reconnect()` (manuel ou automatique) en cours, qui ne doit
jamais se reprogrammer lui-même.

Backoff exponentiel plafonné : `_resolve_reconnect_delay_seconds(attempt)`
= `min(2 * 2**attempt, 30)` → 2, 4, 8, 16, 30, 30… Pas de nombre maximal
de tentatives — une coupure prolongée continue de retenter indéfiniment à
ce rythme plafonné ; fermer l'onglet ou cliquer « Reconnecter » reste le
moyen d'interrompre la boucle (`stop()` appelle désormais
`_cancel_pending_auto_reconnect()` en tout premier, qui annule le minuteur
GLib en attente via `GLib.source_remove()`).

`_reconnect_timeout_id` stocké en attribut d'instance (pas de risque
d'callback fantôme après un `stop()` : le minuteur est explicitement
annulé). `_reconnect_attempt` remis à 0 dès qu'un CONNECTED est de
nouveau atteint — une coupure ultérieure repart du délai le plus court,
pas de celui atteint lors d'une série de tentatives précédente.

## Tests

Deux nouveaux fichiers, 21 tests au total :

- `tests/test_global_shortcuts.py` (7 tests) : table `_GLOBAL_SHORTCUTS`
  (non vide, accélérateurs uniques, noms de handlers résolubles et
  appelables, couverture des trois actions attendues) + délégation pure
  des trois méthodes `_shortcut_action_*` (instance construite via
  `VncTab.__new__(VncTab)`, même technique que
  `VncDisplay.__new__(VncDisplay)` dans
  `tests/test_key_and_mouse_mapping.py`, pour éviter de construire de
  vrais widgets GTK).
- `tests/test_auto_reconnect.py` (14 tests) : `_should_schedule_auto_reconnect`
  (matrice statut × `had_connected_before`), `_resolve_reconnect_delay_seconds`
  (séquence complète + plafond), câblage bout en bout dans `_set_status`
  (CONNECTED remet `_had_connected_before`/`_reconnect_attempt` à zéro,
  ERROR planifie seulement après une connexion préalable, DISCONNECTED ne
  planifie jamais), `_schedule_auto_reconnect`/`_on_auto_reconnect_timeout`
  (délai et callback transmis à `GLib.timeout_add_seconds`, via
  `monkeypatch` sur `vnc_tab.GLib` — pas testable en observant un vrai
  minuteur sous le stub), `_cancel_pending_auto_reconnect`/`stop()`
  (annulation du minuteur en attente, no-op si aucun minuteur).

Contre-épreuves : `_should_schedule_auto_reconnect` réduit à
`status_value == VncStatus.ERROR.value` (en ignorant
`had_connected_before`) → 2 tests échouent comme attendu (connexion
initiale + câblage `_set_status`). Renommage d'une entrée de
`_GLOBAL_SHORTCUTS` vers un nom de méthode inexistant → le test de
couverture des trois actions échoue comme attendu. Correctifs restaurés,
suite complète repassée au vert dans les deux cas.

124 tests au total (103 + 7 + 14), tous verts. `ruff check` et
`ruff format --check` propres sur tout le dépôt.

## Backlog

Rien d'identifié comme suite immédiate. Presse-papiers image écarté (hors
périmètre, cf. § « Recherche Context7 » ci-dessus). Comme en sessions 15
et 16 : pas de nouveau point de l'audit « accès à `self.client` » à
chercher, continuer à repartir d'un besoin utilisateur réel ou d'une
extension protocolaire côté `asyncvnc2_patched`.

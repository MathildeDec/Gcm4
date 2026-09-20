# Pièges déjà rencontrés — ne pas les réintroduire

Importé depuis `CLAUDE.md`. Liste organisée par piège (pas par date) : à
consulter avant de toucher une zone qui y ressemble. L'historique complet
de chaque correctif (contexte, découverte, contre-épreuve) est dans
`docs/sessions/`, référencé entrée par entrée ci-dessous.

- **`client.video.refresh()` doit être rappelé après CHAQUE update**, pas
  juste une fois via `screenshot()`. Sans ça, l'affichage se fige
  silencieusement après la première image — bug réel trouvé et corrigé en
  cours de route, cf. le commentaire en tête de `_read_loop`.
- **`VncDisplay` doit avoir `hexpand`/`vexpand` à `True`.** `Gtk.Picture`
  ne les a pas par défaut ; sans ça il ne remplit pas le
  `Gtk.ScrolledWindow`, et `get_display_transform()` calcule une échelle
  fausse à partir d'une taille allouée erronée.
- **Coordonnées souris et overlay curseur doivent tenir compte de
  l'échelle ET du crop multi-écran.** `widget_to_remote()` convertit
  d'abord via `get_display_transform()` (qui elle-même utilise la taille
  de l'écran actif s'il y en a un), PUIS rajoute le décalage `screen.x`/
  `screen.y` pour retomber en coordonnées absolues — `mouse.move()`
  attend toujours de l'absolu, jamais du relatif à ce qui est affiché.
- **`get_display_transform()` et `_apply_active_screen_crop()` doivent
  retomber sur le MÊME bureau (complet) en cas d'écran actif disparu.**
  `_apply_active_screen_crop()` bascule déjà sur le framebuffer complet
  si l'écran sélectionné n'est plus dans `_last_screens` (moniteur
  déconnecté côté serveur). `get_display_transform()` doit faire le même
  repli — PAS renvoyer `None` — sinon l'image affichée (bureau complet)
  et le calcul de coordonnées souris (identité brute, faute de transform)
  divergent silencieusement : clics mal positionnés côté serveur, sans
  erreur visible. Bug réel trouvé et corrigé le 2026-09-04, cf.
  `docs/sessions/session-04.md` et `tests/test_display_transform.py`.
- **Boutons souris et touches maintenus doivent être relâchés à la
  déconnexion** (`_release_all_mouse_holds`/`_release_all_key_holds`
  dans `stop()`), sinon un drag/une touche en cours au moment d'un
  `reconnect()` tente d'écrire sur un socket fermé.
- **`_on_button_pressed` a besoin du même garde anti-collision que
  `_on_key_pressed`, pour une raison différente.** Côté clavier, le
  garde (`if keycode in self._active_key_holds: return`) sert surtout à
  ignorer l'auto-repeat. Côté souris, `_gdk_button_to_vnc` traduit EN
  PLUS délibérément tout bouton GDK non reconnu vers 0 (clic gauche) —
  deux boutons physiques différents (ex. bouton latéral + vrai clic
  gauche) peuvent donc collisionner sur la même clé de
  `_active_mouse_holds`, pas juste le même bouton pressé deux fois. Sans
  garde, le second appui écrase la référence au premier hold, qui n'est
  alors plus jamais relâché explicitement — bouton "collé" côté serveur.
  Bug réel trouvé et corrigé le 2026-09-06, cf.
  `docs/sessions/session-06.md` et `tests/test_mouse_button_holds.py`.
- **Le bouton « ajuster la fenêtre » doit viser l'écran actif, pas le
  bureau complet.** `_last_remote_size` (mis à jour par le signal
  `vnc-size-changed`) suit toujours la taille du framebuffer COMPLET,
  même quand `set_active_screen()` restreint l'affichage à un seul
  écran. `VncTab._resize_window_to_remote()` doit donc passer par
  `_resolve_resize_target_size()`, qui privilégie la taille de l'écran
  sélectionné (`self._screens` + `self.display._active_screen_id`) —
  bug réel trouvé et corrigé le 2026-09-02, cf.
  `docs/sessions/session-02.md` et `tests/test_resize_target.py`.
- **`vnc-screens-changed` ne veut pas dire "reviens au bureau
  complet".** Le serveur peut ré-annoncer ExtendedDesktopSize pour bien
  d'autres raisons qu'un vrai changement de moniteur. Reconstruire le
  modèle du dropdown (`Gtk.StringList` neuve à chaque fois) ne doit PAS
  silencieusement réinitialiser la sélection si l'écran actif est
  toujours dans la nouvelle liste — sinon l'UI affiche "Bureau complet"
  pendant que le crop réel reste sur l'ancien écran, `_updating_screen_dropdown`
  empêchant justement `_on_screen_selected` de corriger l'incohérence.
  `_on_screens_changed()` doit donc chercher la nouvelle position de
  l'écran actif via `_resolve_screen_dropdown_index()` avant de
  reconstruire le modèle, et n'appeler `set_active_screen(None)` que si
  cet écran a vraiment disparu — bug réel trouvé et corrigé le
  2026-09-03, cf. `docs/sessions/session-03.md` et
  `tests/test_screen_dropdown.py`.
- **Cet alignement `_active_screen_id` doit se faire dans TOUTES les
  branches de `_on_screens_changed()`, pas juste celle où le dropdown
  reste visible.** Piège dans le piège précédent : repasser sous 2
  écrans (retour à un seul écran, reconnexion vers un serveur sans info
  multi-écran) empruntait un chemin de sortie séparé (`return` anticipé)
  qui ne passait PAS par `_resolve_screen_dropdown_index()` — donc
  `_active_screen_id` restait périmé, cette fois sans même que
  l'utilisateur ait un dropdown visible pour s'en rendre compte. Calculer
  `selected_index` (et faire l'alignement qui en découle) AVANT de
  décider si le dropdown est visible, pas après — bug réel trouvé et
  corrigé le 2026-09-05, cf. `docs/sessions/session-05.md` et
  `tests/test_screen_dropdown.py`.
- **Touches indexées par `keycode` (scancode physique), pas par
  `keyval`.** Un keyval peut changer entre l'appui et le relâchement de la
  même touche physique (Maj relâchée en cours de route) — indexer par
  keyval casserait le suivi appui/relâchement.
- **`GDK_TO_VNC_KEY` doit rester une table de dérogations minimale.**
  `Gdk.keyval_name()` renvoie déjà les noms keysym X11 standard, que le
  paquet `keysymdef` (utilisé par `asyncvnc2`) reconnaît nativement — y
  compris tout l'AZERTY (accents, symboles, touches mortes). Résister à
  la tentation d'y remettre une grosse table à la main.
- **Ne pas supposer une action GTK côté hôte sans la vérifier contre le
  vrai dépôt.** Le bouton plein écran appelait
  `self.activate_action("win.toggle-fullscreen", None)` sur la seule foi
  d'une hypothèse jamais confirmée. Vérifié le 2026-09-05 contre le
  dépôt gcm4 fourni : cette action n'existe nulle part — le plein écran
  y est géré par un raccourci clavier (F11) câblé uniquement sur les
  widgets VTE (`on_terminal_keypress`), qui bascule directement
  `Gtk.Window.fullscreen()`/`unfullscreen()` sur la fenêtre principale.
  Rien d'exploitable depuis un onglet non-terminal, et rien de garanti
  stable tant que gcm4 est en cours d'écriture. `VncTab._toggle_fullscreen()`
  bascule maintenant lui-même le plein écran sur sa PROPRE fenêtre
  racine (`get_root()`), état local, indépendant de gcm4 — cf.
  `docs/sessions/session-05.md` et `tests/test_fullscreen_toggle.py`.
- **`HostKeyStore.get()` doit être protégée contre une entrée
  INDIVIDUELLE corrompue, pas seulement `_load()` contre un fichier
  entier illisible.** `_connect_and_run()` appelle
  `self.host_key_store.get(...)` AVANT son bloc try/except (celui-ci ne
  protège que `asyncvnc2.connect()` et la suite) — si cette entrée
  précise n'est ni du base64 valide ni une clé DER valide (édition
  manuelle, écriture tronquée en plein `_save()`...),
  `base64.b64decode()`/`load_der_public_key()` lèvent une exception qui
  remontait alors NON INTERCEPTÉE hors de la coroutine : la tâche
  asyncio plantait silencieusement, sans jamais atteindre
  `_set_status(VncStatus.ERROR, ...)` — l'onglet restait bloqué
  indéfiniment sur le spinner "Connexion à ...", sans bouton
  "Réessayer" ni "Oublier la clé enregistrée" (masqués tant que le
  statut reste CONNECTING). `get()` traite maintenant une entrée
  illisible comme absente (retour `None` + avertissement loggé), sans
  toucher aux autres entrées du store. Bug réel trouvé et corrigé le
  2026-09-07, cf. `docs/sessions/session-07.md` et
  `tests/test_host_key_store.py`.
- **`HostKeyStore._save()` doit écrire de façon atomique (fichier
  temporaire + `os.replace()`), pas via `Path.write_text()` direct sur la
  cible.** `write_text()` tronque le fichier avant d'écrire dedans — un
  crash pile à ce moment (coupure de courant, `kill -9`, disque plein en
  cours d'écriture) laisse `~/.gcm/vnc_host_keys.json` dans un état
  partiellement écrit : exactement le scénario que `get()` sait déjà
  encaisser par entrée (piège précédent) et que `_load()` sait déjà
  encaisser pour le fichier entier — mais mieux vaut ne jamais produire
  ce fichier corrompu que de compter uniquement sur la récupération
  après coup. `_save()` écrit maintenant dans un fichier temporaire
  (`tempfile.mkstemp`, même dossier que la cible pour que
  `os.replace()` reste un simple renommage), `flush()`+`fsync()` avant
  de renommer, et nettoie le temporaire si l'écriture échoue en cours de
  route. Corrigé le 2026-09-08, cf. `docs/sessions/session-08.md` et
  `tests/test_host_key_store.py`.
- **`_on_button_released` a besoin du même garde que `_on_key_released`
  autour de `hold_cm.__exit__()`, pour une raison différente du garde
  anti-collision listé plus haut.** `_on_key_released` avale déjà toute
  exception de `__exit__()` ; `_on_button_released` ne le faisait pas.
  Rien ne relâche les holds actifs sur une erreur de lecture —
  `_read_loop` se contente de `_set_status(ERROR, ...)` sans jamais
  toucher à `_active_mouse_holds` (seul `stop()` les relâche tous), et
  `self.client` n'est JAMAIS remis à `None` après une erreur de lecture
  (seule une nouvelle connexion réussie le réaffecte) — donc le garde
  `if not self.client:` en tête de la méthode ne protège pas non plus ce
  chemin. Bug réel trouvé et corrigé le 2026-09-09, cf.
  `docs/sessions/session-09.md` et `tests/test_mouse_button_holds.py`.
- **`_on_button_pressed` avait besoin du même garde, mais côté
  `__enter__()`/écriture initiale plutôt que `__exit__()`.** Même cause
  racine que le piège précédent. Corrigé le 2026-09-10, cf.
  `docs/sessions/session-10.md` et `tests/test_mouse_button_holds.py`.
  Même famille, même cause racine, chacun traité dans sa propre
  session : `_on_motion` (`docs/sessions/session-11.md`) et `_on_scroll`
  (`docs/sessions/session-12.md`).
- **`_on_key_pressed` avait besoin du même garde, en PLUS du
  `except KeyError` existant (pas à sa place).** Le `KeyError` couvre le
  cas normal d'un keysym non reconnu par `asyncvnc2` — il doit rester
  spécifique. Un `except Exception` séparé, ajouté APRÈS, couvre la même
  cause racine que les quatre chemins précédents (`self.client` jamais
  remis à `None` après une erreur de lecture) : `keyboard.hold()` et
  surtout `hold_cm.__enter__()` (qui écrit réellement sur le socket)
  peuvent lever autre chose qu'un `KeyError` sur une connexion déjà
  morte. Dernier des cinq chemins d'entrée haute fréquence à recevoir ce
  garde. Corrigé le 2026-09-13, cf. `docs/sessions/session-13.md` et
  `tests/test_key_dead_connection.py`.
- **`_on_local_clipboard_read` avait besoin du même garde, autour de
  `client.clipboard.write()` — sixième point de cette famille, pas un
  chemin d'entrée mais la même cause racine.** Trouvé en auditant
  systématiquement TOUS les accès à `self.client` du fichier (pas
  seulement les cinq chemins d'entrée déjà listés ci-dessus) : ce
  callback, invoqué directement par GLib via `clipboard.read_text_async()`
  quand le presse-papiers LOCAL change, relaie le texte vers le serveur —
  `client.clipboard.write(text)` écrit réellement sur le socket, sans
  aucun garde jusqu'ici. Le `if not self.client:` déjà présent en tête de
  la méthode ne protège pas ce cas, pour la même raison que les cinq
  précédents : `self.client` n'est jamais remis à `None` après une erreur
  de lecture. Corrigé le 2026-09-14, cf. `docs/sessions/session-14.md` et
  `tests/test_clipboard_dead_connection.py`.
- **`_send_cad` et `set_continuous_updates` avaient besoin du même garde,
  mais sur des actions FIRE-AND-FORGET (`asyncio.ensure_future(...)`), pas
  des callbacks GTK/GLib synchrones.** Septième et huitième (dernier)
  points de la même famille, identifiés dès l'audit de la session 14 mais
  traités en session 15. Sans garde, une exception y devenait un « Task
  exception was never retrieved » silencieux (avalé par le handler par
  défaut d'asyncio), pas une remontée hors d'un callback GTK -- un trou
  réel mais moins visible que les six précédents. Pour `set_continuous_updates`,
  impossible d'envelopper un `try/except` directement autour de la
  coroutine déjà créée avant de la passer à `ensure_future()` : il a fallu
  introduire un wrapper `async def` séparé
  (`_send_enable_continuous_updates`) pour avoir un point d'ancrage où
  faire l'`await` sous garde. Corrigé le 2026-09-15, cf.
  `docs/sessions/session-15.md`, `tests/test_send_cad_dead_connection.py`
  et `tests/test_continuous_updates_dead_connection.py`.

- **Ne jamais s'appuyer sur `self.get_paintable()` (ou tout autre
  accesseur GTK non explicitement stubé) pour détecter un état "pas
  encore arrivé" dans un test.** `VncDisplay.save_screenshot()` a besoin
  de savoir si une image a déjà été reçue. Une première version aurait pu
  lire `self.get_paintable()` directement (`Gtk.Picture` la stocke déjà) —
  mais dans `tests/gtk_stub/`, tout attribut/méthode non défini renvoie un
  `_NoOp()` dont `__bool__` renvoie toujours `True`, y compris
  `get_paintable()` AVANT le tout premier appel à `set_paintable()` : le
  test « pas encore d'image » serait devenu indétectable sous stub (il ne
  passerait que sous vrai GTK4). `_push_frame()` stocke donc la texture
  dans un attribut d'instance normal dédié (`self._last_frame_texture`,
  initialisé à `None` dans `__init__`), qui reste un vrai `None` Python
  tant qu'aucun rendu n'a eu lieu, stub ou pas. Corrigé/anticipé le
  2026-09-10, cf. `docs/sessions/session-16.md` et
  `tests/test_screenshot.py`. Piège à généraliser : pour tout futur état
  qu'un test doit pouvoir observer sous le stub, préférer un attribut
  d'instance explicite à un accesseur GTK dont le stub ne simule pas la
  vraie sémantique.
- **Un raccourci clavier local à l'onglet doit être posé en phase
  CAPTURE sur un ANCÊTRE de `VncDisplay`, jamais en phase TARGET/BUBBLE
  sur `VncDisplay` lui-même (ni sans préciser de phase — le défaut GTK4
  n'est pas CAPTURE).** `VncDisplay._on_key_pressed()` retourne TOUJOURS
  `True`, y compris pour une touche sans équivalent VNC connu (garde
  anti-répétition, résolution du keysym, etc. — voir son corps). En GTK4,
  la phase CAPTURE (racine → cible) s'exécute AVANT la phase TARGET du
  widget effectivement visé par l'événement ; sans ça, un raccourci
  ajouté ailleurs sur l'onglet ne se déclencherait JAMAIS quand
  `VncDisplay` a le focus (le cas normal en usage, puisque c'est lui qui
  relaie les frappes au serveur distant) — la touche serait
  systématiquement avalée d'abord par `_on_key_pressed` et transmise
  telle quelle au serveur distant, sans qu'aucune erreur ne le signale.
  `VncTab._setup_global_shortcuts()` pose son `Gtk.ShortcutController` sur
  `VncTab` (ancêtre) avec
  `set_propagation_phase(Gtk.PropagationPhase.CAPTURE)` explicitement pour
  cette raison. Anticipé/documenté le 2026-09-11, cf.
  `docs/sessions/session-17.md`.
- **`Gdk.unicode_to_keyval()` ne renvoie PAS 0 pour un caractère sans
  keysym X11 nommé — contrairement à l'intuition par symétrie avec
  `Gdk.keyval_to_unicode()` (qui, elle, renvoie bien 0 quand il n'y a pas
  de caractère correspondant).** Elle renvoie un keysym Unicode
  synthétique, `point_de_code | 0x01000000` (convention X11/GDK,
  documentée sur `docs.gtk.org/gdk4/func.unicode_to_keyval.html`). Pour
  `_resolve_vnc_key_name_for_char()` (`send_text()`, session 20) ça ne
  change rien au résultat final : `Gdk.keyval_name()` ne nomme pas ce
  keysym synthétique, et `_resolve_vnc_key_name()` retombe alors sur
  `Gdk.keyval_to_unicode()`, qui sait retrouver le point de code d'origine
  dans cette même plage — le caractère est transmis tel quel, comme prévu.
  Mais un futur test qui monkeypatcherait `Gdk.unicode_to_keyval()` pour
  simuler « pas de keysym nommé » doit renvoyer cette valeur codée
  (`point_de_code | 0x01000000`), pas `0` — sinon le test ne couvre pas le
  vrai comportement de GDK, cf. `tests/test_send_text.py`.
- **Avant de changer la signature d'une méthode déjà appelée depuis
  ailleurs dans la classe, vérifier si des tests existants la
  monkeypatchent directement en tant qu'attribut d'instance** — un test
  qui fait `display._une_methode = lambda: ...` (0 argument) casse
  silencieusement (`TypeError`) si le code appelant se met à l'appeler
  avec un argument. Rencontré en session 23 en complétant le message de
  reconnexion automatique dans `_set_status()` : le délai aurait pu
  remonter en paramètre de `_schedule_auto_reconnect()` plutôt que d'être
  recalculé une deuxième fois, mais `tests/test_auto_reconnect.py`
  monkeypatche déjà cette méthode en 0 argument à plusieurs endroits —
  changer sa signature les aurait tous cassés. Choisi de recalculer le
  délai (calcul pur, sans effet de bord, donc sans risque d'incohérence)
  plutôt que de toucher une signature déjà couverte par des tests.
- **Le ruleset ruff de ce projet (`select = ["E", "F", "W", "C90"]` +
  long `ignore` dans `pyproject.toml`) est volontairement étroit — ne PAS
  l'élargir ni lancer `ruff check --isolated`/règles par défaut en
  pensant "nettoyer" sans comprendre pourquoi chaque catégorie écartée
  l'est.** Vérifié en détail en session 24 (`ruff check --isolated`,
  jeu de règles par défaut, sans le `pyproject.toml` du projet) : 57
  signalements, dont la quasi-totalité rentre dans l'une de ces
  catégories, **délibérément non sélectionnées** :
  - `BLE001`/`S110`/`S112` (except générique, try/except/pass,
    try/except/continue) : c'est très exactement le patron de garde
    "self.client jamais remis à None après une erreur de lecture" qui
    est LE sujet central de ce fichier et de son historique de tests
    depuis la session 09 — near la moitié des signalements. Un linter
    générique ne peut pas savoir que c'est intentionnel et testé.
  - `UP045` (`Optional[X]` → `X | None`) : préférence de style, pas un
    bug — changer les ~14 occurrences irait à l'encontre du style déjà
    utilisé de façon cohérente dans tout le fichier (y compris par les
    ajouts de sessions 20 et 22).
  - `DTZ001`/`DTZ005` (datetime sans tzinfo) : **faux positif** pour
    `_default_screenshot_filename()`/son test — l'horodatage d'un nom de
    fichier de capture d'écran doit refléter l'heure locale du poste de
    l'utilisateur, pas une heure "timezone-aware" qui déplacerait
    l'affichage par rapport à l'heure murale réelle.
  - `RUF012` (défaut mutable de classe) sur les deux `__gsignals__` :
    **faux positif** — c'est le patron PyGObject *requis* pour déclarer
    des signaux personnalisés (lu par la métaclasse GObject à la
    définition de la classe) ; PAS un bug à corriger.
  - `I001` (tri des imports) : **dangereux à corriger aveuglément dans ce
    fichier précis** — `ruff --fix` propose de réordonner le bloc
    d'imports en tête de `vnc_tab.py`, ce qui déplacerait
    `from gi.repository import Gtk, ...` par rapport à
    `gi.require_version("Gtk", "4.0")`. Ces deux lignes ont un ordre
    obligatoire (`require_version` doit s'exécuter avant tout import
    depuis `gi.repository`, sous peine de charger la mauvaise version de
    GTK ou d'échouer) qu'un trieur d'imports générique ignore
    complètement. C'est très probablement LA raison pour laquelle "I"
    n'est pas sélectionné dans ce projet — ne pas l'activer, et ne pas
    lancer `ruff check --fix`/`--unsafe-fixes` sans relire chaque diff un
    par un sur ce fichier en particulier.
  Seuls des signalements SANS rapport avec ces patrons volontaires ont
  été corrigés en session 24 (imports de test réellement morts, une
  variable de tuple réellement inutilisée, un `dict()` réécrit en
  littéral, un shebang rendu exécutable) — cf.
  `docs/sessions/session-24.md` pour le détail complet.

## État des tests — à comprendre avant d'en ajouter

`pytest tests/` sans GTK4 installé : les tests se **collectent sans
erreur mais se SKIP tous** (`requires_gtk4` dans `conftest.py`). Ce n'est
pas un échec caché — c'est la détection qui fonctionne.

Deux façons d'obtenir un vrai pass/fail :

1. **Environnement de dev réel** (poste avec GTK4/PyGObject installé) :
   `pytest tests/` tourne pour de vrai.
2. **Stub léger pour CI sans GTK4** : `tests/gtk_stub/` fournit un faux
   `gi.repository` (classes dynamiques acceptant n'importe quel appel de
   méthode, sans vraie sémantique GTK) plus un faux `asyncvnc2`. Suffisant
   pour importer `vnc_tab.py` et exécuter les tests de logique pure
   (`HostKeyStore`, `VncConnectionInfo`, `GDK_TO_VNC_KEY`,
   `_gdk_button_to_vnc`) et, depuis le 2026-09-01, les tests qui
   instancient un vrai `VncDisplay` (cf. `docs/sessions/session-01.md`)
   — pas pour tester du vrai rendu GTK, qui a besoin d'un display réel
   (Xvfb) et du vrai PyGObject.

   ```bash
   PYTHONPATH=tests/gtk_stub pytest tests/ --ignore=tests/gtk_stub
   ```

Si un futur test instancie `VncTab` (pas juste `VncDisplay`) ou déclenche
un chemin de code touchant à autre chose que taille/contenu/client
(rendu réel du framebuffer, `Gdk.MemoryTexture`, vrais événements
souris/clavier...), attends-toi à devoir enrichir le stub à nouveau — il
reste volontairement minimal, pas une réimplémentation de GTK4.

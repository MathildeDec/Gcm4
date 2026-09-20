# Session 03 — 2026-09-03

**`tests/test_screen_dropdown.py` — le dropdown multi-écran revenait
silencieusement sur « Bureau complet ».**

Autre bug dans la même zone multi-écran que la session précédente :
`VncTab._on_screens_changed()` reconstruit le modèle du dropdown à
chaque ré-annonce `ExtendedDesktopSize` (le serveur peut la renvoyer
pour bien d'autres raisons qu'un vrai changement de moniteur), et
remettait systématiquement l'index sélectionné à 0 — sans jamais
toucher `VncDisplay._active_screen_id`, bloqué par le garde-fou
`_updating_screen_dropdown` (qui sert justement à éviter de
redéclencher `_on_screen_selected` pendant `set_model()`/
`set_selected()`). Résultat : l'UI affichait « Bureau complet » pendant
que le crop réellement appliqué restait sur l'ancien écran — divergence
silencieuse entre ce qui est montré et ce qui est réellement affiché.

Même approche que `test_resize_target.py` : logique extraite en méthode
statique testable (`VncTab._resolve_screen_dropdown_index`), testée sans
instancier `VncTab`. Si l'écran actif a vraiment disparu de la nouvelle
liste, `_active_screen_id` est désormais explicitement réaligné sur
« Bureau complet » plutôt que de rester périmé — ce qui évite aussi de
reprendre un crop sans action de l'utilisateur si cet écran réapparaît
plus tard avec le même id.

Voir `docs/pieges.md` (piège « vnc-screens-changed ») et
`tests/test_screen_dropdown.py`.

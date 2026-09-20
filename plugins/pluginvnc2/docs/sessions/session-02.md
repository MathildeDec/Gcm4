# Session 02 — 2026-09-02

**`tests/test_resize_target.py` — le bouton « ajuster la fenêtre »
ignorait l'écran actif.**

Bug réel corrigé : `VncTab._resize_window_to_remote()` ignorait
`set_active_screen()` et redimensionnait toujours vers
`_last_remote_size` (framebuffer complet, mis à jour par le signal
`vnc-size-changed`), même quand un seul écran recadré était affiché —
la fenêtre grossissait plus que ce qui était réellement montré.

Logique extraite en méthode statique testable
(`VncTab._resolve_resize_target_size`, même style que
`_gdk_button_to_vnc`) : privilégie la taille de l'écran sélectionné
(`self._screens` + `self.display._active_screen_id`), avec repli sur le
bureau complet si l'écran sélectionné a disparu de la liste (même
comportement que `_find_active_screen` ailleurs dans le fichier).

Contrairement à `test_display_transform.py` (session précédente), ce
test n'instancie même pas `VncTab` — la logique est une méthode
statique pure, testée directement comme `_gdk_button_to_vnc`. Pas de
dépendance au stub GTK au-delà de l'import du module.

Voir `docs/pieges.md` (piège « bouton ajuster la fenêtre ») et
`tests/test_resize_target.py`.

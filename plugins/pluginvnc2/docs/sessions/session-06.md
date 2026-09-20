# Session 06 — 2026-09-06

**`tests/test_mouse_button_holds.py` (nouveau fichier) — garde
anti-collision manquant côté souris.**

Après quatre correctifs consécutifs dans la zone multi-écran (sessions
01 à 04), recherche volontairement ailleurs : clavier/souris, cycle de
connexion.

Bug trouvé : `_gdk_button_to_vnc` traduit délibérément tout bouton GDK
non reconnu (boutons latéraux 8/9, etc.) vers 0 (clic gauche) — donc
deux boutons PHYSIQUES différents peuvent se traduire vers le MÊME
bouton VNC. Sans garde, presser le second avant de relâcher le premier
écrasait silencieusement `_active_mouse_holds[0]`, perdant la référence
au premier hold : celui-ci n'était alors jamais relâché côté serveur
(bouton « collé » au premier relâchement physique reçu, quel qu'il
soit). Trouvé en comparant `_on_button_pressed` à `_on_key_pressed`,
qui a ce garde depuis le début.

Contrairement aux tests `_resolve_*` des sessions précédentes (méthodes
statiques pures), ceux-ci appellent les VRAIES méthodes d'instance
`_on_button_pressed`/`_on_button_released` sur un `VncDisplay` réel (via
`make_test_display`, cf. session 01), avec juste `client.mouse`
remplacé par un faux mouse qui trace les holds créés — pas besoin
d'instancier `VncTab` pour ça, ces deux méthodes vivent sur
`VncDisplay`.

Voir `docs/pieges.md` (piège « garde anti-collision souris ») et
`tests/test_mouse_button_holds.py`.

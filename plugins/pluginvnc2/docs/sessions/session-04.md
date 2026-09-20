# Session 04 — 2026-09-04

**`tests/test_display_transform.py` mis à jour, pas juste enrichi.**

En revérifiant `get_display_transform()` face à
`_apply_active_screen_crop()`, un vrai bug de fond est apparu : les
deux fonctions ne retombaient PAS sur le même bureau quand l'écran
actif disparaissait — l'une affichait le framebuffer complet, l'autre
refusait de calculer une transform pour lui (`None`). Conséquence :
l'image affichée (bureau complet) et le calcul de coordonnées souris
(identité brute, faute de transform) divergeaient silencieusement —
clics mal positionnés côté serveur, sans erreur visible.

Le test `test_widget_to_remote_ignores_vanished_active_screen` (ajouté
le 2026-09-01, session 01) avait encodé l'ancien comportement bugué
comme « attendu » (`assert ... is None`) ; il a été remplacé par deux
tests qui vérifient le nouveau comportement corrigé.

À retenir : réutiliser un test existant sans le rejouer mentalement
contre le code qu'il couvre peut simplement figer un bug plutôt que le
documenter — c'est exactement ce qui s'était passé ici.

Voir `docs/pieges.md` (piège « get_display_transform / crop ») et
`tests/test_display_transform.py`.

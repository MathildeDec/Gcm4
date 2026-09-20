# Session 11 — 2026-09-11

**`tests/test_motion_dead_connection.py`** (nouveau fichier) — garde
manquant côté DÉPLACEMENT souris.

Reprise de la liste des chemins encore exposés notée aux sessions 09/10
(`_on_motion`, `_on_scroll`, le `except KeyError` de `_on_key_pressed`)
— `_on_motion` traité en premier car c'est le plus facilement
atteignable des trois : il est appelé à haute fréquence (chaque
déplacement de souris), contrairement aux appuis/relâchements ponctuels
déjà gardés aux sessions précédentes.

Même cause racine que ces deux corrections : `self.client` n'est jamais
remis à `None` après une erreur de lecture (`_read_loop` se contente de
`_set_status(ERROR, ...)`), donc le garde `if not self.client:` en tête
de `_on_motion` ne protège pas le cas où la connexion tombe pendant un
déplacement — `mouse.move()` sur un socket déjà mort pouvait lever hors
du gestionnaire de signal GTK. Correctif : `mouse.move()` déplacé dans
un `try/except Exception: pass`, même style que les gardes voisins.

Quatre tests, sur le même modèle `_make_display_with_fake_mouse()` que
`test_mouse_button_holds.py` (mais avec un faux `FakeMotionController`
sans état, puisque `_on_motion` ne lit que `x`/`y`) : déplacement
normal ; `mouse.move` monkeypatché pour lever et vérification que
`_on_motion()` ne la laisse pas remonter ; contre-épreuve fonctionnelle
qu'un déplacement ultérieur normal, après un premier échec avalé,
fonctionne comme si de rien n'était ; et qu'un appel sans client ne
lève pas.

Total de tests : 64 → 68.

Restent exposés, volontairement pas traités ici pour rester sur une
seule correction par session : `_on_scroll` et le `except KeyError` de
`_on_key_pressed` (qui ne couvre que le nom de touche non reconnu, pas
une erreur d'écriture sur un socket déjà mort).

Voir `docs/pieges.md` (même famille de piège) et
`tests/test_motion_dead_connection.py`.

# Session 12 — 2026-09-12

**`tests/test_scroll_dead_connection.py`** (nouveau fichier) — dernier
garde manquant côté SOURIS haute fréquence.

Reprise de la liste des chemins encore exposés notée à la session 11
(`_on_scroll`, le `except KeyError` de `_on_key_pressed`) — `_on_scroll`
traité en priorité car c'est, comme `_on_motion`, un chemin à haute
fréquence potentielle (molette maintenue pendant un défilement),
contrairement au `except KeyError` de `_on_key_pressed` qui ne couvre
qu'un cas ponctuel (touche non reconnue) et relève d'une famille de bug
différente (pas un socket mort).

Même cause racine que tous les gardes souris précédents : `self.client`
n'est jamais remis à `None` après une erreur de lecture, donc le garde
`if not self.client:` en tête de `_on_scroll` ne protège pas le cas où
la connexion tombe pendant un scroll. Correctif : `mouse.scroll_down()`/
`scroll_up()` sont désormais dans un `try/except Exception: pass`, même
style que `_on_motion` (session 11).

Six tests, sur le même modèle `_make_display_with_fake_mouse()` que les
fichiers précédents (mais avec un `FakeMouse` qui trace
`scroll_down_calls`/`scroll_up_calls` plutôt qu'une position) : scroll
bas normal ; scroll haut normal ; `scroll_down`/`scroll_up`
monkeypatchés séparément pour lever et vérification que `_on_scroll()`
ne laisse rien remonter dans les deux cas ; contre-épreuve
fonctionnelle qu'un scroll ultérieur normal, après un premier échec
avalé, fonctionne comme si de rien n'était ; et qu'un appel sans client
ne lève pas. Contre-épreuve faite comme les sessions précédentes :
rejoué sur une version temporaire de `vnc_tab.py` sans le correctif,
les trois tests attendus échouent bien avec l'`OSError` simulée qui
remonte telle quelle ; les 3 autres tests du fichier restent verts,
comme attendu puisqu'ils ne dépendent pas du `try/except`.

Tous les chemins souris à haute fréquence (`_on_motion`,
`_on_button_pressed`, `_on_button_released`, `_on_scroll`) ont
maintenant ce garde. Seul reste le `except KeyError` de
`_on_key_pressed` — chemin ponctuel et de nature différente,
volontairement pas traité ici (voir `docs/features-backlog.md`).

Total de tests : 68 → 74.

Voir `docs/pieges.md` (dernière entrée de la famille) et
`tests/test_scroll_dead_connection.py`.

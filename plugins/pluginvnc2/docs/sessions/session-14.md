# Session 14 — 2026-09-14

**`_on_local_clipboard_read`** (garde d'exception) + **`tests/test_clipboard_dead_connection.py`**
(nouveau fichier) — sixième point de la famille « écriture sur socket déjà
mort », après les cinq chemins d'entrée haute fréquence des sessions 09 à
13 (`_on_button_pressed`/`_on_button_released`, `_on_motion`, `_on_scroll`,
`_on_key_pressed`).

Point de départ : `docs/features-backlog.md` § « Backlog ouvert » ne
listait plus rien depuis la session 13. Plutôt que d'inventer une
fonctionnalité hors périmètre, relecture complète de `vnc_tab.py` en
cherchant tout `self.client.<x>` qui écrit réellement sur le socket
(`mouse.*`, `keyboard.*`, `clipboard.write`,
`send_enable_continuous_updates`) et vérification, pour chacun, qu'il est
bien enveloppé -- directement ou via la fonction appelante -- dans un
`try/except` couvrant une connexion déjà morte. Trois points sans aucun
garde ressortent de cet audit :

- `client.clipboard.write(text)` dans `_on_local_clipboard_read` --
  callback GTK/GLib SYNCHRONE (invoqué par `clipboard.read_text_async`),
  donc une exception y remonte directement hors du callback, exactement
  comme les cinq chemins déjà corrigés. Choisi pour cette session.
- `client.keyboard.hold(...)`/`.press(...)` dans `_send_cad`
  (Ctrl+Alt+Suppr) -- fire-and-forget (`asyncio.ensure_future`), donc une
  exception y devient un « Task exception was never retrieved » silencieux
  plutôt qu'une remontée directe hors d'un callback GTK. Documenté dans
  `docs/features-backlog.md` pour une prochaine session (priorité
  suggérée : le bouton correspondant reste cliquable dans tous les états).
- `client.send_enable_continuous_updates(...)` dans
  `set_continuous_updates` -- même famille fire-and-forget, mais fenêtre
  plus étroite (`btn_continuous` déjà désactivé hors de l'état CONNECTED).
  Documenté également.

Correctif : un bloc `try/except Exception: pass` ajouté autour du seul
appel `self.client.clipboard.write(text)`, après la mise à jour de
`_last_clipboard_text` (ordre inchangé -- ce correctif ne touche que la
robustesse de l'écriture, pas la logique de déduplication déjà en place).
Même style que les cinq gardes précédents : avale l'exception, pas de log
applicatif (la déconnexion elle-même est déjà loggée par `_read_loop` au
moment où elle survient réellement).

Nouveau fichier de test (`tests/test_clipboard_dead_connection.py`, même
approche que les cinq précédents) : un `FakeServerClipboard` substitué à
`client.clipboard` (trace les écritures, ou lève sur demande) et un
`FakeSystemClipboard` minimal pour le premier argument du callback
(expose juste `read_text_finish`). Cinq tests : (1) écriture normale, (2)
texte inchangé -> aucune écriture tentée (contre-épreuve de la
déduplication déjà en place, jusqu'ici non testée), (3) l'exception sur
écriture est bien avalée, (4) contre-épreuve fonctionnelle -- un second
changement de presse-papiers, différent, réussit normalement après un
premier échec, (5) absence de client. Vérifié que (3) échoue bel et bien
sans le correctif (retrait temporaire du `try/except`, relance ciblée,
restauration) avant de considérer le test valide. 85 tests au total, tous
verts.

Backlog ouvert : les deux points fire-and-forget ci-dessus (Ctrl+Alt+Suppr
en priorité suggérée), détaillés dans `docs/features-backlog.md`.

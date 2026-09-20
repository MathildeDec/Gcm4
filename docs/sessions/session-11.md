# Session 11 — 2026-09-04 (plus tôt) — Notifications desktop (#109) — volet déconnexion

**Il y a neuf sessions (2026-09-04, plus tôt)** : notifications desktop (#109), volet
« déconnexion » (backlog §4.2, urgence faible → fait ; le volet « erreurs de
connexion » reste ouvert, reformulé en §4.2 — portée plus large, pas
seulement les protocoles VTE). Nouvelle fonction
`send_desktop_notification(summary, body="")` (`gnome_connection_manager.py`) :
appel **D-Bus direct** à `org.freedesktop.Notifications.Notify` via `Gio`
(déjà une dépendance dure du projet) plutôt que `gi.repository.Notify`/
libnotify — décision prise en cours de route en constatant que `Gio` est
déjà importé, pour ne rien ajouter aux dépendances système (pas de nouveau
typelib `gir1.2-notify-0.7`). Câblée dans
`NotebookTabLabel.mark_tab_as_closed()` (`widgets.py`), seul point d'appel du
projet, lui-même déclenché sur `child-exited` (VTE) — donc SSH/telnet/local/
serial seulement, pas RDP/VNC/SPICE. Nouvelle préférence
`conf.DISABLE_NOTIFICATIONS` (défaut `False`, opt-out, même schéma que
`DISABLE_SHORTCUTS`) exposée dans Préférences. Échec silencieux si aucun bus
de session/démon de notifications n'est disponible (`GLib.Error` journalisée
en debug). Bug évité avant livraison : j'avais d'abord inventé un paramètre
`invert=True` pour `addParam()` afin de formuler la case à cocher
positivement (« Show... » plutôt que « Disable... ») — `addParam()` ne
prend que `(name, field, ptype, *args)`, sans support d'inversion ; vérifié
dans le code réel avant de livrer, corrigé pour rester sur le schéma
« Disable... » de `DISABLE_SHORTCUTS`. Pas de fonction pure ajoutée à
`gcm4_core.py` cette fois, pour une raison nouvelle (pas juste « trivial »
comme pour `DISABLE_SHORTCUTS`) : `_()` (gettext) n'y est pas garanti
disponible — `builtins.__dict__["_"]` n'est injecté qu'au chargement de
`gnome_connection_manager.py`, donc un appel `_()` dans une fonction de
`gcm4_core.py` casserait `tests/test_gcm4_core.py`
(`NameError: name '_' is not defined` si le module est importé seul, comme
le font les tests — vérifié en conditions réelles dans ce bac à sable).
Nuance à garder en tête pour toute notification future ajoutée à
`gcm4_core.py` : composer les chaînes traduites reste du ressort du code
GTK. `python3 -m py_compile` propre sur les 3 fichiers modifiés
(`utils.py`, `gnome_connection_manager.py`, `widgets.py`), `ruff check` sans
nouvelle erreur (13 préexistantes sur ces 3 fichiers, inchangées),
formatage vérifié par comparaison miroir (3 lignes réenroulées à la main
pour correspondre à `ruff format`). Câblage GTK/D-Bus non exécuté en
conditions réelles (pas de GTK/VTE/bus de session dans cet environnement).
Détail dans `features.md` §4.1 (nouvelle entrée) et §4.2 (entrée reformulée
et rétrécie au volet « erreurs »).

---
*Note de journal d'origine (claude.md) : « Il y a neuf sessions (2026-09-04, plus tôt) : notifications desktop (#109), volet « déconnexion » (backlog §4.2, urgence faible → fait ; le volet « erreurs de connexion » reste ouvert). »*

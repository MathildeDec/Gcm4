# Session 25 — 2026-09-10 — Premier pas concret du portage GTK4 : lever le verrou GTK3 de `plugin_base.py`

Contexte de la demande : urgence exprimée sur l'état d'avancement du cœur
GTK4 (« à combien de sessions sera-t-il prêt »). Réponse détaillée versée
dans `docs/gtk4-migration.md` §3.6 plutôt que répétée ici : en résumé,
aucun codage de portage réel n'avait encore été fait avant cette session, et
un chiffrage fiable en nombre de sessions reste bloqué tant que les
questions ouvertes du §9 de `proposition-architecture-plugins-gtk4.md`
(mécanisme de sélection GTK3/GTK4, découpage fichiers SSH, confirmation du
plugin pilote) ne sont pas tranchées avec l'autrice — donner un chiffre
précis maintenant serait une fausse précision, documenté comme tel plutôt
que deviné silencieusement.

En attendant cette validation, la présente session traite le seul point de
l'ordre de mise en œuvre proposé (§8) qui est explicitement décrit comme
**indépendant** de toute décision encore ouverte : lever le verrou GTK3 de
`plugins/plugin_base.py` (§4 de la proposition).

## Travail livré

| Lever le verrou `gi.require_version("Gtk", "3.0")` dans `plugin_base.py` | ✅ Fait (2026-09-10) — remplacé l'import réel de `Gtk` par un bloc `if TYPE_CHECKING: from gi.repository import Gtk`, conformément à la proposition §4 : le seul usage de `Gtk` dans ce fichier est en annotation de type (`-> Gtk.Widget`), déjà paresseuse grâce à `from __future__ import annotations` présent en tête de fichier — aucune exécution réelle ne dépendait de l'import. Vérifié par exécution réelle, pas seulement par lecture du code : import de `plugin_base` réussi dans un environnement où `gi`/PyGObject **n'est pas installé du tout** (confirmé : `ModuleNotFoundError` sur `gi` si on tente de l'importer directement dans cet environnement), et `'gi' not in sys.modules` après l'import de `plugin_base` — preuve que le module est désormais réellement chargeable sans aucune version de GTK présente, condition nécessaire pour qu'un futur plugin 100 % GTK4 puisse un jour cohabiter avec des plugins encore GTK3 dans le même process (ou plus exactement, pour que le *cœur de découverte de plugins* cesse d'imposer GTK3 à tout le monde). Contrat public (`__all__`, `ConnectionPlugin`, `PluginRegistry`, `BatchPlugin`, `BatchPluginRegistry`) inchangé. Aucun appelant du dépôt n'importait `Gtk` depuis `plugin_base` (vérifié par recherche exhaustive) — changement sans impact sur le reste du code. |

## Tests

- **Nouveau** : `tests/test_plugin_base.py` (4 tests) — verrouille précisément
  la régression visée : import de `plugin_base` sans `gi` préalablement
  présent dans `sys.modules`, absence de `gi` dans `sys.modules` après
  l'import (donc pas d'import caché), absence du texte
  `require_version("Gtk"` dans le fichier source, et non-régression du
  contrat public (`__all__` et classes exportées inchangés).
- Suite complète exécutée réellement (pas seulement écrite) :
  `tests/test_gcm4_core.py` (85 tests) + reste de `tests/` hors
  `test_gcm.py` (110 tests au total, `test_plugin_base.py` inclus) — tous
  verts.
- `tests/test_gcm.py` : échec de **collecte** confirmé pré-existant et sans
  rapport avec ce changement — vérifié en restaurant temporairement l'ancien
  `plugin_base.py` (avec le verrou GTK3) puis en relançant ce même fichier de
  test dans cet environnement : échec identique
  (`AttributeError: module 'GObject' has no attribute 'SignalFlags'`,
  provenant du stub GTK/GObject minimal de `tests/test_gcm.py` lui-même via
  `key_picker_dialog.py`, pas de `plugin_base.py`). Limite de cet
  environnement de développement (PyGObject réel absent), pas une régression
  introduite ici — non corrigée dans cette session, hors périmètre d'un
  changement isolé sur `plugin_base.py`.
- `ruff check`/`ruff format` exécutés sur les deux fichiers touchés
  (`plugins/plugin_base.py`, `tests/test_plugin_base.py`). Le nouveau
  fichier de test est propre sur les deux plans. `plugin_base.py` remonte un
  avertissement `I001` (bloc d'imports mal trié) — **pré-existant avant
  cette session** (vérifié en relançant `ruff check --select I001` sur
  l'ancienne version du fichier : même avertissement, ordre `functools`
  avant `abc` déjà présent) ; non corrigé ici conformément à la règle du
  projet (`CONSIGNES-AGENTS-IA.md` §6 : ne pas profiter d'une petite
  modification pour reformater un fichier hérité au-delà de ce qui a
  effectivement changé). Idem pour les avertissements `B010`/`D107`/`D105`/
  `B007` du fichier, tous sur des lignes non touchées par ce diff.
- `tools/check_circular_imports.py` exécuté : aucun cycle détecté
  (38 modules analysés).

## Choix pris

- Portée délibérément restreinte au seul point §4 de la proposition, en
  laissant de côté le découpage en dossiers `plugins/<nom>/` et le portage
  du plugin pilote SSH : ces derniers dépendent de décisions encore
  ouvertes (§9 de la proposition) qui n'ont pas été validées avec l'autrice
  dans cette session — les traiter maintenant aurait été trancher seul des
  points explicitement marqués comme « à valider avec toi avant tout
  codage ».
- Réponse à la question d'urgence sur le nombre de sessions restantes
  rédigée comme une fourchette grossière et explicitement qualifiée
  d'incertaine plutôt qu'un chiffre unique présenté comme fiable — voir
  `docs/gtk4-migration.md` §3.6 pour le détail et le raisonnement complet.

## Non fait / limites

- Aucun découpage `plugins/<nom>/{core,gtk3,gtk4}.py` commencé.
- Aucun des points de rupture du cœur proprement dit (`Gtk.Dialog.run()`,
  `GtkMenuBar`, `Gtk.Widget.reparent()`, `Gtk.Socket`/RDP) traité.
- Points §9 de la proposition toujours à valider avec l'autrice avant de
  poursuivre ce chantier au-delà de ce point isolé.
- Reste de l'urgence haute du backlog (SFTP, master password, arbitrage
  `ssh_config_editor.py`/`snmp_push_core.py`) non traité — hors périmètre de
  cette session, qui répond spécifiquement à la question posée sur le cœur
  GTK4.

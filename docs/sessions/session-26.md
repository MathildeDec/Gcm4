# Session 26 — 2026-09-10 — Plugin pilote SSH : extraction de `plugins/ssh/core.py`

Consigne : « Continue les features à faire. Fait évoluer les fichiers de
suivi, de tests et de documentation. Livraison du zip horodaté sans passer
à la suite » — même discipline récurrente que les sessions précédentes
(une feature bornée par session, livraison sans enchaîner).

## Choix de la feature

La session-25 levait le seul point préalable indépendant (§4 de la
proposition d'architecture) et actait, le 2026-09-10, les réponses aux
questions ouvertes du §9 (voir `docs/gtk4-migration.md` §3.0-bis) :
dossier par plugin `core.py`+`gtk4.py` uniquement, pas de mécanisme de
sélection GTK3/GTK4, fusion des fichiers SSH en 2, SSH confirmé comme
plugin pilote. La conséquence documentée à la fin de cette même section
est explicite : « le prochain travail de codage sur ce chantier peut
commencer par l'extraction de `plugins/ssh/core.py` (partie testable sans
GTK dès maintenant) ». C'est donc la feature naturelle de cette session —
aucune autre décision de conception n'était nécessaire avant de commencer.

## Constat avant codage

- `ssh_config_parser.py` (598 lignes) et `ssh_migrate_gcm.py` (1069
  lignes) sont tous deux déjà 100 % GTK-free (vérifié : aucun `import gi`
  ni `from gi...`) — la fusion ne change donc aucune contrainte
  d'exécution, uniquement l'organisation des fichiers.
- Le seul couplage entre les deux était un import différé à l'intérieur
  de trois méthodes de `SSHConfigParser`
  (`_is_shared_target`/`_backup_file`/`_atomic_write`), documenté à
  l'époque comme nécessaire « pour que ce module reste utilisable seul
  même si `ssh_migrate_gcm` n'est pas disponible ». Une fois les deux
  fusionnés dans le même fichier, cette justification n'a plus lieu
  d'être : les trois méthodes appellent désormais directement
  `is_shared_target()`/`_write_text_via_pkexec()`, sans import ni
  `try/except ImportError`.
- `ssh_config_parser.py` n'avait **aucun fichier de test dédié** avant
  cette session (seul `ssh_config_editor.py`, qui a besoin de GTK3 et
  n'est donc pas exécutable dans cet environnement, l'exerçait
  indirectement) — confirmé en listant `tests/` et en cherchant
  `SSHConfigParser`/`SSHHost`/`SSHOption` dans le dépôt. Seul
  `ssh_migrate_gcm.py` avait une couverture (`test_ssh_migrate_gcm.py`,
  4 tests, tous concentrés sur `_render_ssh_stanza`/ProxyCommand — une
  fraction du module réel).

## Ce qui a été livré

- **`plugins/ssh/core.py`** (nouveau, ~1650 lignes) : fusion intégrale de
  `ssh_config_parser.py` + `ssh_migrate_gcm.py`. Docstring de module
  réécrite expliquant la fusion, ce qui a changé (imports différés
  devenus directs) et ce qui reste hors périmètre (`gtk4.py`). `__all__`
  fusionné (classes du parser + fonctions publiques de la migration).
- **`plugins/ssh/__init__.py`** (nouveau) : marqueur de package,
  volontairement sans `get_plugin()`/`get_batch_plugin()` — le mécanisme
  de découverte du cœur reste le glob plat existant sur
  `plugins/plugin_*.py` (`plugin_base._discover_plugin_modules()`),
  inchangé par cette session. Ce sous-dossier n'est pas encore un point
  d'entrée de plugin, juste l'emplacement du nouveau `core.py`.
- **`plugins/plugin_ssh.py`** : les 7 imports différés
  `from ssh_migrate_gcm import ...` (dispersés dans 5 méthodes)
  remplacés par `from plugins.ssh.core import ...` — comportement
  identique, seul le chemin d'import change. Commentaires/docstrings
  mentionnant l'ancien module mis à jour (sauf deux références
  historiques à `ssh_migrate_gcm.patch_edit_host_dialog`, qui décrivent
  d'où cette méthode a été rapatriée en session-23 — volontairement
  laissées telles quelles, ce sont des faits historiques, pas un chemin
  d'import actuel).
- **`ssh_config_editor.py`** : import `from ssh_config_parser import
  (...)` + fallback `try/except ImportError` sur `SHARED_SSH_CONFIG_PATH`
  remplacés par un unique `from plugins.ssh.core import (...)`. Le
  fichier reste lui-même à la racine du dépôt (GTK3, pas encore déplacé
  vers `plugins/ssh/gtk4.py` — hors périmètre de cette session).
- **Suppression** de `ssh_config_parser.py` et `ssh_migrate_gcm.py` à la
  racine du dépôt (entièrement absorbés par `plugins/ssh/core.py`).
- **Tests** : `tests/test_ssh_migrate_gcm.py` renommé
  `tests/test_ssh_core.py`. Les 4 tests existants
  (`TestRenderSshStanzaProxyCommand`) conservés tels quels (import
  adapté). **22 tests nouveaux** ajoutés pour la partie jusqu'ici non
  testée : `TestSSHOption` (rendu avec indentation), `TestSSHHost`
  (parsing depuis lignes brutes, get/set/remove/multi-valeurs),
  `TestSSHConfig` (génération de contenu, `is_dirty()`, gestion de la
  liste des hôtes), `TestSSHConfigParser` (parse sur fichier réel,
  round-trip write/parse, backup horodaté créé au premier write,
  absence de backup si contenu inchangé, `validate()` — alias dupliqué,
  port invalide, `IdentityFile` manquant, cas propre —, détection de
  cible partagée). Utilisation de `tempfile.TemporaryDirectory()` pour
  isoler chaque test du `~/.ssh/config` réel.

## Validation

- `pytest` réel sur la suite GTK-free (`test_gcm4_core.py`,
  `test_ssh_core.py`, `test_plugin_base.py`, `test_snmp_bulk_core.py`,
  `test_putty_import_core.py`) : **132/132 passés** (110 hérités − 4
  déplacés + 26 dans le fichier fusionné = 132, vérifié par calcul et par
  exécution avant/après).
- `ruff check` sur tous les fichiers touchés par cette session
  (`plugins/ssh/core.py`, `plugins/ssh/__init__.py`, `tests/test_ssh_core.py`,
  `ssh_config_editor.py`) : propre. `ruff format --diff` : propre sur ces
  mêmes fichiers ; les différences de formatage détectées dans
  `plugins/plugin_ssh.py` sont pré-existantes (lignes GTK non touchées par
  cette session), cohérentes avec la dette déjà documentée dans
  `CLAUDE.md` (423 erreurs `ruff` pré-existantes).
- `tools/check_circular_imports.py` (hook pre-commit local, équivalent
  `import-linter` de ce projet) : **aucun import circulaire**, 36 modules
  analysés.
- `mypy --ignore-missing-imports` sur `plugins/ssh/core.py` : 6 erreurs
  `method-assign`/`assignment`, toutes sur les 3 occurrences de
  `cp.optionxform = str` (idiome `configparser` standard pour préserver
  la casse des clés, hérité tel quel de l'ancien `ssh_migrate_gcm.py`,
  pas introduit par cette fusion). `mypy` n'est pas une commande de
  qualité de ce projet (absent de la liste `make lint`/`make check` de
  `CLAUDE.md`, contrairement à `ruff`) — signalé ici pour mémoire, non
  traité.
- Import réel vérifié à l'exécution : `import plugins.ssh.core` fonctionne
  comme package à espace de noms implicite (PEP 420, sans
  `plugins/__init__.py`), exactement comme `from plugins.plugin_base
  import ...` dans `gnome_connection_manager.py` — confirme que le
  mécanisme d'import choisi est cohérent avec l'existant, pas une
  nouveauté risquée.

## Non traité dans cette passe

- `plugins/ssh/gtk4.py` (portage effectif des widgets — éditeur visuel de
  `~/.ssh/config`, gestion des clés) : session séparée, tributaire de
  l'avancement des points de rupture du cœur GTK4 (`Gtk.Dialog.run()`,
  menus, `Gtk.Widget.reparent()`) pour être réellement exécutable dans
  l'app — voir `docs/gtk4-migration.md` §3.6 points 3-4.
  `ssh_config_editor.py`/`ssh_key_manager_dialog.py`/
  `key_picker_dialog.py` restent donc à la racine du dépôt, en GTK3,
  inchangés fonctionnellement.
- Généralisation du découpage `core.py`/`gtk4.py` aux autres plugins
  (RDP, VNC, SPICE, etc., §8.4 de la proposition) — un plugin pilote
  d'abord, comme prévu, pas de généralisation dans cette session.
- Les points de rupture du cœur GTK4 eux-mêmes (§3.2) : aucun n'a été
  traité ici, hors périmètre d'une extraction de plugin.
- `mypy` sur le reste du dépôt, `ssh_config_editor.py`/
  `ssh_key_manager_dialog.py` (nécessitent GTK3, non importables dans cet
  environnement).

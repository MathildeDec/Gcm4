# Session 05 — 2026-08-30 — Séparation gcm4_core.py / gnome_connection_manager.py

Préalable exécuté avant de commencer le découpage en plugins par dossier :
séparer le cœur en fichier métier (`gcm4_core.py`, zéro GTK) et fichier GTK4
(le reste de `gnome_connection_manager.py`, portage GTK4 lui-même pas encore
commencé). Cette session a aussi produit `CONSIGNES-AGENTS-IA.md` et
`.pre-commit-config.yaml`, et mis au jour plusieurs écarts d'architecture
encore ouverts aujourd'hui (vestiges de protocole dans le cœur, duplication
`CONFIG_DIR` dans `widgets.py`) — détaillés dans `docs/architecture.md`
plutôt que répétés ici.

## Décisions actées cette session

- **Architecture plugins/GTK4** (voir `proposition-architecture-plugins-gtk4.md`) :
  un sous-dossier par plugin (`plugins/<nom>/`), **SSH en plugin pilote**
  (premier réorganisé), **GTK3 100 % abandonné** (pas de coexistence
  GTK3/GTK4 — chaque plugin n'aura qu'un `core.py` + `gtk4.py`, pas de
  `gtk3.py`). Préalable exécuté avant de commencer les plugins : séparer le
  cœur en fichier métier (`gcm4_core.py`, zéro GTK) + fichier GTK4 (reste
  de `gnome_connection_manager.py`, portage GTK4 pas encore commencé). Voir
  `CONSIGNES-AGENTS-IA.md` pour les règles imposées à tout agent travaillant
  sur ce chantier (logging, docstrings, tests, ruff, imports circulaires —
  strictes).
- **Neutralité de protocole du cœur** : aucune donnée/logique spécifique à
  un protocole ne doit rester dans `gcm4_core.py`/`gnome_connection_manager.py`
  à terme. Plusieurs vestiges déjà repérés et documentés pour plus tard
  (templates série, `TEL_BIN`, `vte_protocols`/`is_vte`) — voir
  `features.md` §2.8-bis.

## Travail livré

| Séparation cœur métier / cœur GTK4 (préalable au découpage des plugins) | ✅ Fait (2026-08-30) — nouveau fichier `gcm4_core.py` (639 lignes, zéro import `gi`/`Gtk`/`Vte`, vérifié en l'important sans stub dans cet environnement de travail), extrait de `gnome_connection_manager.py` : résolution `--config`, logger applicatif, chiffrement (xor/AES), identité utilisateur, ports par défaut génériques (`proto_default_port`/`all_default_ports`, paramétrés par `plugin_registry` au lieu de lire le singleton global `wMain`), zoom terminal, couleurs. `gnome_connection_manager.py` garde des alias minces (mêmes noms historiques) qui délèguent à `gcm4_core.py`, pour ne rien casser côté tests existants (`tests/test_gcm.py`). Décisions actées pour ce chantier : SSH sera le premier plugin réorganisé en dossier (`plugins/ssh/`), GTK3 est **100 % abandonné** (pas de coexistence GTK3/GTK4, contrairement à l'hypothèse initiale de la proposition d'architecture). `load_encryption_key()`/`initialise_encyption_key()` lèvent désormais une exception (`RuntimeError`) au lieu d'appeler `msgbox()` directement (impossible depuis un module sans GTK) — attrapée côté `gnome_connection_manager.py` pour reproduire le comportement d'origine (message affiché, exécution qui continue). **Trois erreurs de transcription trouvées et corrigées avant livraison** en revérifiant chaque fonction déplacée contre l'original ligne à ligne : `color_to_hex()` avait perdu son paramètre `diff` (aurait cassé 2 des 4 appels réels), `dep_install_hint()` avait une logique de détection de distribution complètement différente de l'original, et `_gcm_app_name` avait disparu silencieusement — toutes verrouillées par un test dédié dans `tests/test_gcm4_core.py` pour ne pas revenir. Une divergence délibérée et documentée : `get_password()` a gagné une garde défensive contre un `TypeError` latent de l'original (crash si aucune variable d'environnement `USER`/`LOGNAME`/`USERNAME`). **Erreur d'architecture commise puis corrigée en cours de session** : les templates série avaient été déplacés dans `gcm4_core.py` puis remis dans `gnome_connection_manager.py` après relecture — le protocole série étant déjà un plugin, ces données n'ont leur place dans aucun des deux fichiers du cœur à terme (voir §2.8-bis). 26 tests dans `tests/test_gcm4_core.py`, tous exécutés réellement et verts, sans aucun stub GTK. `models.py` mis à jour pour importer `decrypt`/`encrypt`/`get_password` depuis `gcm4_core` au lieu de `gnome_connection_manager` (sens de dépendance correct). Voir `proposition-architecture-plugins-gtk4.md` pour le plan complet du découpage en dossiers par plugin (pas encore commencé), et `CONSIGNES-AGENTS-IA.md` pour les règles imposées à ce chantier |

## Nouveaux outils de qualité

- ✅ **Nouveaux outils de qualité (2026-08-30)** : `CONSIGNES-AGENTS-IA.md`
  (règles strictes pour tout agent IA travaillant sur les plugins — logging
  Loguru, docstrings Google, tests, ruff, imports circulaires) +
  `.pre-commit-config.yaml` (ruff lint/format, hygiène de base, détecteur
  d'imports circulaires local) + `tools/check_circular_imports.py` (analyse
  uniquement les imports exécutés au chargement du module — ignore
  délibérément les imports différés en corps de fonction et les blocs
  `if TYPE_CHECKING:`, pour ne pas remonter de faux positifs sur des
  patterns déjà utilisés intentionnellement dans ce dépôt). Les trois
  validés réellement (dépôt git temporaire, `pre-commit run --all-files`,
  détection positive et négative de cycle testée) — pas seulement rédigés.
  Répertoires vendorisés (`SSH-Studio/`, `gtk-frdp/`) et environnements de
  test (`rdp/`, `vnc/`) exclus de tous les hooks.

---
*Note de journal d'origine (claude.md) : « Il y a quinze sessions (2026-08-30) : préalable au découpage des plugins — séparation gcm4_core.py/gnome_connection_manager.py, détail §4.1. »*

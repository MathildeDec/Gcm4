# Session 27 — 2026-09-10 — Master password : logique de protection du trousseau local

Consigne : « Continue les features à faire. Fait évoluer les fichiers de
suivi, de tests et de documentation. Livraison du zip horodaté sans passer
à la suite » — même discipline récurrente que les sessions précédentes.

## Choix de la feature

La session-26 laissait la migration GTK4 bloquée sur des points nécessitant
soit un environnement GTK4 réel (indisponible ici), soit une validation de
l'autrice avant de généraliser le découpage `core.py`/`gtk4.py`. Le reste de
l'urgence haute du backlog (`docs/features-backlog.md`) est presque
entièrement marqué « à confirmer avec l'auteure avant d'implémenter » —
sauf **« Master password au démarrage »**, seul item sans réserve de ce
type, listé comme fonctionnalité de sécurité à part entière.

## Constat avant codage

- `gcm4_core.initialise_encyption_key()`/`load_encryption_key()` écrivent/
  lisent `KEY_FILE` (`~/.gcm/.gcm.key`) en clair sur disque, permissions
  `0o600`. Cette clé locale sert ensuite (`pyAES`/`gcm4_core.encrypt`/
  `decrypt`) à chiffrer les mots de passe dans `gcm.conf`. Aucune protection
  par mot de passe maître n'existe aujourd'hui : un accès en lecture au
  compte utilisateur (sauvegarde non chiffrée, accès physique machine
  déverrouillée) suffit à récupérer `KEY_FILE` puis à déchiffrer tous les
  mots de passe stockés.
- Une fonctionnalité complète (protection + prompt GTK au démarrage + choix
  produit en cas de mot de passe oublié) est trop large pour une session
  bornée, et touche à des décisions produit non tranchables seul (voir
  « Non traité » ci-dessous). Décision : traiter dans cette session
  uniquement la **logique de chiffrement/déchiffrement elle-même**,
  entièrement testable sans GTK — même discipline que les sessions
  40/44 côté netcross (traiter la partie calculable/sans décision de
  conception incertaine, documenter explicitement le reste).

## Décisions de conception

- **Réutilisation de `pyAES`** (déjà utilisé par le reste du projet pour les
  mots de passe) plutôt qu'un deuxième algorithme de chiffrement — cohérence
  délibérée, pas une nouvelle dépendance à auditer/packager.
- **PBKDF2-HMAC-SHA256** (stdlib `hashlib.pbkdf2_hmac`, aucune nouvelle
  dépendance) pour dériver une clé AES-256 depuis le mot de passe maître.
  200 000 itérations choisies par défaut (recommandation OWASP 2023 pour
  PBKDF2-HMAC-SHA256, en tenant compte que la menace ici — dérivation locale
  à chaque démarrage de l'app — diffère d'un stockage de mot de passe côté
  serveur) — **non mesuré sur une machine réelle** dans cet environnement de
  travail (pas de GTK/matériel cible disponible ici) : documenté comme
  hypothèse à valider empiriquement (temps de démarrage perçu) avant de
  considérer ce chiffre définitif, plutôt que présenté comme acquis.
- **Vérificateur d'intégrité indépendant du contenu chiffré** : plutôt que
  de déchiffrer puis constater un échec silencieux (dépend du contenu —
  `pyAES.decrypt()` ne lève pas nécessairement sur une mauvaise clé), un
  vérificateur SHA-256 de la clé dérivée (plus un contexte fixe) est stocké
  à côté du texte chiffré et vérifié **avant** tout déchiffrement — un mot
  de passe maître incorrect lève `InvalidMasterPasswordError` de façon
  fiable, jamais une clé locale corrompue silencieusement.
- **Rétrocompatibilité totale, sans migration forcée** : `is_protected()`
  détecte un `KEY_FILE` legacy (hex brut, jamais préfixé
  `GCM4MPW1:`) et le laisse intact — contrainte explicite de `CLAUDE.md`
  (« `~/.gcm/gcm.conf` qui casserait la config des utilisateurs existants
  sans migration »), appliquée par anticipation à `KEY_FILE` aussi.
- **Mot de passe maître vide refusé** (`ValueError` à la protection) : une
  protection avec un mot de passe vide donnerait une fausse impression de
  sécurité sans en apporter aucune.

## Ce qui a été livré

- **`master_password_core.py`** (nouveau, racine du dépôt, même famille que
  `gcm4_core.py`/`netmiko_bulk_core.py` — zéro GTK) :
  - `is_protected(key_file_content)` — détection legacy vs protégé.
  - `protect_key_file_content(raw_key, master_password)` — enveloppe la clé
    locale (nouveau sel aléatoire à chaque appel, vérificateur, `pyAES`).
  - `unlock_key_file_content(protected_content, master_password)` — déchiffre,
    lève `InvalidMasterPasswordError` ou `CorruptedProtectedContentError`
    selon le cas.
  - `rewrap_key_file_content(protected_content, old_pw, new_pw)` — change le
    mot de passe maître sans changer la clé locale sous-jacente.
  - `remove_master_password_protection(protected_content, master_password)`
    — revient au contenu legacy en clair (désactivation de la protection).
  - Logging Loguru (2 `debug()` minimum par fonction, jamais de mot de passe
    ni de clé en clair dans les logs — uniquement longueurs/préfixes de
    vérificateur), docstrings Google complètes (`CONSIGNES-AGENTS-IA.md`).
- **`tests/test_master_password_core.py`** (nouveau, 15 tests) :
  détection protégé/legacy/vide, round-trip protection/déverrouillage,
  mot de passe incorrect, mot de passe vide refusé, deux protections de la
  même clé produisent des sorties différentes (sel aléatoire), mot de passe
  maître avec caractères non-ASCII, contenu corrompu (préfixe absent, nombre
  de champs incorrect, sel en base64 invalide), changement de mot de passe
  maître (`rewrap`, avec ancien mot de passe correct/incorrect), retrait de
  la protection (avec mot de passe correct/incorrect).

## Validation

- `pytest` réel sur la suite GTK-free complète (`test_gcm4_core.py`,
  `test_ssh_core.py`, `test_plugin_base.py`, `test_snmp_bulk_core.py`,
  `test_putty_import_core.py`, `test_master_password_core.py`) :
  **147/147 passés** (132 hérités de la session-26 + 15 nouveaux).
- `ruff check`/`ruff format` sur les deux fichiers nouveaux : propres après
  un passage `ruff format` (quelques lignes de log/docstring trop longues
  une fois wrappées automatiquement).
- `tools/check_circular_imports.py` : aucun import circulaire, 37 modules
  analysés (36 + `master_password_core.py`).
- Vérification manuelle à l'exécution (hors suite pytest) : round-trip
  protection → déverrouillage réussi, mot de passe incorrect détecté,
  format du contenu protégé conforme à la docstring de module.

## Non traité dans cette passe

- **Câblage réel** dans `gcm4_core.load_encryption_key()`/
  `initialise_encyption_key()` : décider comment ces deux fonctions
  détectent et gèrent un `KEY_FILE` protégé (ex. lever une exception dédiée
  demandant le mot de passe maître à l'appelant GTK4, plutôt que de
  réutiliser `RuntimeError`) — changement de contrat public, à concevoir
  avec le flux de démarrage réel en tête, pas en aveugle.
- **Prompt GTK au démarrage** (boîte de dialogue demandant le mot de passe
  maître avant de charger `KEY_FILE`) : nécessite GTK3 (indisponible dans
  cet environnement) et une décision d'UX (nombre de tentatives, message
  d'erreur, bouton d'annulation → quel comportement de repli).
- **Politique en cas de mot de passe maître oublié** : aucun mécanisme de
  recouvrement n'existe ni n'est proposé ici — un mot de passe oublié rend
  les mots de passe stockés définitivement inaccessibles avec le schéma
  actuel. Décision produit à confirmer avec l'autrice avant tout câblage
  (ex. accepter ce compromis tel quel, ou prévoir un mode « réinitialiser
  et perdre les mots de passe stockés » explicite dans l'UI).
- **Activation/désactivation dans les préférences** (`Wconfig`) : UI GTK
  pour appeler `protect_key_file_content()`/`rewrap_key_file_content()`/
  `remove_master_password_protection()` depuis l'application — hors
  périmètre, la logique existe et est testée, l'UI reste à faire.
- Migration GTK4 (`plugins/ssh/gtk4.py`, généralisation du découpage aux
  autres plugins) : inchangé depuis la session-26, toujours bloqué sur
  l'environnement GTK4/validation de l'autrice.

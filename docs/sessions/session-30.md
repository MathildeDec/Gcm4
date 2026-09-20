# Session 30 — 2026-09-10 — Renommage GCM → gcm4 : audit exhaustif + mécanisme de migration

Consigne : « Continue les features à faire. Fait évoluer les fichiers de
suivi, de tests et de documentation. Livraison du zip horodaté sans passer
à la suite » — même discipline récurrente que les sessions précédentes. En
cours de session, précision reçue de l'auteure : « rdp sera dans un
plugin ! » — intégrée ci-dessous et dans `docs/gtk4-migration.md` §3.4.

## Choix de la feature

Après la session-29, le chantier GTK4 lui-même reste bloqué sur un ordre à
confirmer entre trois sous-chantiers (`plugins/ssh/gtk4.py`, menus
contextuels, RDP) et le reste de l'urgence haute du backlog (master
password, `snmp_push_core.py`, `ssh_config_editor.py`, SFTP) est marqué
« à confirmer avec l'auteure avant d'implémenter ». Un seul chantier de
premier plan restait non bloqué par une décision produit non tranchée :
le renommage effectif GCM → gcm4 dans le code (`CLAUDE.md`, « Prochaine
étape » point 2, « mérite sa propre session dédiée, pas un à-côté d'une
autre tâche — non commencé à ce jour »). La direction du renommage a été
actée le 2026-08-29 ; seuls des détails d'implémentation (noms définitifs)
restaient ouverts — un chantier à auditer et outiller, pas à trancher.

## Constat

Inventaire exhaustif (détail complet dans `docs/gcm4-rename.md`) :

- **12 fichiers** importent réellement `gnome_connection_manager` (tous en
  import différé, `# noqa: PLC0415`, mécanisme documenté dans
  `CONSIGNES-AGENTS-IA.md` §7) — plus le module lui-même, qui contient une
  astuce d'auto-alias (`sys.modules["gnome_connection_manager"] = ...`) à
  adapter, pas seulement les 12 imports, lors d'un renommage réel.
- **29 occurrences** du domaine i18n `gcm-lang` (1 dans le module principal
  + 28 lignes `msgfmt` dans le `Makefile`, une par langue — mécanique).
- **5 lignes** du fichier `.desktop` (`Name=`, `Exec=`, `Icon=`,
  `StartupWMClass=`, `Name[en]=`).
- **Packaging** : une seule variable `PKG_NAME` (`Makefile`) pilote les
  noms de paquets `.deb`/`.rpm`/openSUSE et les chemins d'installation —
  changer cette variable propage à l'essentiel.
- **Configuration utilisateur** (`~/.gcm/gcm.conf`, `.gcm.key`) : point le
  plus sensible, un renommage du dossier par défaut sans migration
  détruirait les connexions et le mot de passe maître de tout utilisateur
  existant. `widgets.py` duplique indépendamment
  `CONFIG_DIR`/`CONFIG_FILE`/`KEY_FILE` (déjà consigné,
  `docs/architecture.md` §2.8, non corrigé) — à traiter au même moment que
  le renommage réel pour ne pas laisser les deux définitions diverger.

**Trouvaille annexe, en auditant le packaging** : la cible `install` du
`Makefile` copiait `gnome-connection-manager.glade`, et la cible
`validate` appelait `tools/validate_xml_json.py` dessus — fichier absent
du dépôt depuis la suppression de tout `.glade`/`.ui` (session-08).
`make validate` (et donc `make check`) échouait donc silencieusement à
chaque exécution, sans rapport avec les 423 erreurs `ruff` déjà
documentées pour `make lint`, et sans avoir été détecté par aucune session
précédente. Corrigé (référence retirée des deux cibles) et vérifié en
conditions réelles (`gettext` installé dans le bac à sable) : `make
validate` passe désormais proprement.

## Décision de cette session

Le renommage mécanique touche ~12 sites d'import réel, 29 occurrences
i18n, le `.desktop`, le packaging, et surtout un chemin de configuration
utilisateur réel — un rayon d'action largement supérieur aux fixes
ponctuels des sessions précédentes, avec **six choix de noms non
tranchés** (module, dossier de config, fichier de conf/clé, domaine i18n,
id `.desktop`, `PKG_NAME`) que je ne peux pas inventer seul sans risquer
de devoir tout refaire si l'auteure préfère d'autres noms. Conformément à
`CONSIGNES-AGENTS-IA.md` §8 (« proposer un plan avant de coder un gros
morceau », « ne pas trancher seul une ambiguïté ») : **audit et mécanisme
générique seulement cette session, pas d'exécution du renommage** — à
l'image des sessions 28/29 pour la migration GTK4. Le mécanisme de
migration de configuration, en revanche, ne dépend d'aucun de ces six
choix de noms (il reçoit `old_dir`/`new_dir` en paramètres explicites) :
construit et testé dès maintenant, prêt à être câblé une fois les noms
actés — même logique que `master_password_core.py` en session-27
(mécanisme isolé livré, câblage différé à une décision produit).

## Livré cette session

- `Makefile` : référence à `gnome-connection-manager.glade` retirée des
  cibles `install`/`validate` (fichier absent depuis la session-08) —
  `make validate` vérifié de nouveau fonctionnel.
- `gcm4_core.migrate_legacy_config_dir(old_dir, new_dir)` (nouveau) :
  copie générique d'un dossier de config (jamais destructrice — ne
  supprime jamais `old_dir`, pour permettre un retour à une version
  antérieure —, idempotente, permissions préservées, sans aucun nom de
  dossier en dur) ; 8 tests dans `tests/test_gcm4_core.py`
  (`TestMigrateLegacyConfigDir`), couvrant migration réussie, non-écrasement
  d'un `new_dir` existant, absence d'`old_dir`, `old_dir` qui est un
  fichier et non un dossier, idempotence face à une édition utilisateur
  postérieure, et nettoyage propre en cas d'échec partiel (testé par
  mock de `shutil.copytree`).
- `docs/gcm4-rename.md` (nouveau) : inventaire complet ci-dessus, tableau
  des six choix de noms ouverts, et justification de l'absence
  d'exécution cette session.
- `docs/gtk4-migration.md` §3.4 : précision de l'auteure consignée — RDP
  restera dans un plugin, portage GTK4 futur en
  `plugins/rdp/{core.py,gtk4.py}` comme le pilote SSH, pas un traitement
  spécial du cœur (ne tranche pas l'incertitude technique sur le
  remplacement de `Gtk.Socket`/XEmbed lui-même, seulement l'organisation
  du code).
- `tests/test_gcm4_rename_inventory.py` (nouveau, 7 tests) : verrou
  textuel sur l'état actuel avant renommage (12 sites d'import, occurrences
  i18n, contenu du `.desktop`, nom du dossier de config par défaut,
  non-régression sur le fix `.glade` du `Makefile`) — check-list vivante
  pour la future session d'exécution du renommage.
- `docs/features-backlog.md`, `CLAUDE.md`, `docs/architecture.md`,
  `CHANGELOG.md` : mis à jour (voir diffs respectifs).

`ruff check`/`ruff format --check` passent sans erreur sur tout le code
ajouté cette session (seules les lignes neuves de `migrate_legacy_config_dir()`
ont été reformatées dans `gcm4_core.py`, pas le reste du fichier — dérive
de formatage préexistante et sans lien laissée intacte, conformément à
`CONSIGNES-AGENTS-IA.md` §6). Suite complète : **172 tests + 4 subtests**,
tous verts (`test_gcm.py` exclu, non importable dans cet environnement
comme déjà documenté) — 157+4 avant cette session, +15 nouveaux tests
(8 + 7). `make lint` reste en échec pour les raisons pré-existantes déjà
documentées (423 erreurs historiques) — non concerné par cette session.

## Questions posées à l'auteure (à confirmer avant d'implémenter)

1. **Ordre des trois chantiers GTK4 restants** : `plugins/ssh/gtk4.py`
   (widgets réels), menus contextuels, ou RDP — lequel traiter en premier ?
   Précision reçue cette session : RDP sera organisé comme un plugin
   (`plugins/rdp/{core.py,gtk4.py}`), ce qui ne tranche pas l'ordre mais
   clarifie que son portage suivra le même schéma que le pilote SSH plutôt
   qu'un traitement à part au niveau du cœur. Proposition toujours en
   attente de confirmation : `popupMenuTab` seul en premier (le plus
   simple des quatre menus, cf. session-29).
2. **Renommage GCM → gcm4 — six choix de noms** (nouveau cette session,
   voir `docs/gcm4-rename.md` §6) : nom du module principal (`gcm4.py` ?
   `gcm4_app.py` ?), nom du dossier de config (`~/.gcm4/` cousin de
   l'actuel, ou `~/.config/gcm4/` façon XDG — ce dernier élargirait le
   renommage à une vraie migration de layout), nom du fichier de
   conf/clé, domaine i18n, identifiant `.desktop`, `PKG_NAME`. Question
   déjà connue et toujours ouverte, indépendante de ce tableau :
   numérotation de version après renommage (reprise en 1.x ou redémarrage
   en 4.0.0).
3. **Master password (session-27)** : que faire en cas de mot de passe
   maître oublié, sachant qu'aucun mécanisme de recouvrement n'est
   identifié (les mots de passe stockés deviendraient définitivement
   inaccessibles) ? Proposer la protection à l'activation seulement (choix
   explicite de l'utilisatrice), ou la forcer au premier lancement ?
4. **`snmp_push_core.py` vs `snmp_bulk_core.py`** : deux implémentations
   parallèles de la même fonctionnalité coexistent (le premier complet —
   SFTP+FTP/TFTP, asyncio — mais non importé nulle part ; le second utilisé
   par `plugin_snmp_push.py`). Faut-il basculer vers `snmp_push_core.py`,
   le supprimer, ou les garder tous les deux pour des cas d'usage
   différents ?
5. **`ssh_config_editor.py`** : module complet mais son point d'intégration
   dans l'interface n'a pas été retrouvé — reste-t-il un module à câbler,
   ou un vestige à retirer ?

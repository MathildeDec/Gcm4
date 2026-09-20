# Session 29 — 2026-09-10 — Audit approfondi des menus contextuels GTK4

Consigne : « Continue les features à faire. Fait évoluer les fichiers de
suivi, de tests et de documentation. Livraison du zip horodaté sans passer
à la suite » — même discipline récurrente que les sessions précédentes.
Cette fois avec une demande explicite préalable : « pose-moi tes
questions » — questions posées en fin de session (voir plus bas), le
travail de cette session portant sur ce qui restait actionnable sans
attendre les réponses.

## Choix de la feature

Après la session-28, il ne reste plus, côté chantier prioritaire (migration
GTK4, §3.6 de `docs/gtk4-migration.md`), que trois chantiers non commencés :
`plugins/ssh/gtk4.py` (widgets réels, tributaire de l'avancement des points
de rupture du cœur), les menus contextuels (isolés par la session-28 mais
jamais détaillés), et RDP (le plus incertain, §3.4). Le reste de l'urgence
haute du backlog (master password, `snmp_push_core.py`,
`ssh_config_editor.py`) est marqué « à confirmer avec l'auteure avant
d'implémenter ». Plutôt que de choisir arbitrairement lequel des trois
chantiers GTK4 restants coder en premier — un choix qui, vu leur nature,
relève autant d'un arbitrage produit (quel risque de régression accepter
en premier) que d'une décision technique — audit du plus petit des trois en
apparence (menus contextuels) pour objectiver sa taille réelle avant de
proposer un ordre.

## Constat

L'inventaire exhaustif (voir `docs/gtk4-migration.md` §3.6-ter pour le
détail complet) a trouvé un chantier plus large que ce que laissait
supposer la note de clôture de la session-28 : 4 menus applicatifs
distincts (`popupMenu`, `popupMenuFolder`, `popupMenuTab`, et le
constructeur générique partagé par RDP/VNC/SPICE dans `widgets.py`) plus un
cinquième cas à part (menu natif `Gtk.Entry` via `populate-popup`), pour un
total de 6 instanciations `Gtk.Menu()`, 48 items de menu, et 6 sites de
déclenchement utilisant tous la signature `.popup()` à 6 arguments
positionnels — supprimée sans équivalent direct en GTK4 (modèle
`Gtk.EventController`/`Gtk.GestureClick`).

Deux difficultés structurelles, au-delà d'un simple remplacement d'API,
justifient de ne pas coder ce portage à l'aveugle cette session :

- Les items à état coché (`mnuLog`, dans deux des quatre menus) n'ont pas
  d'équivalent direct en `Gio.Menu` — il faut passer par une
  `Gio.SimpleAction` à état (`new_stateful()`), donc repenser le câblage,
  pas juste traduire l'appel.
- Le contenu dynamique (sous-menu « Custom commands » repeuplé au runtime,
  items injectés par chaque plugin dans `popupMenuFolder`, visibilité
  conditionnelle dans `popupMenuTab` selon l'état de l'onglet) reste
  possible avec `Gio.Menu` (mutable via `insert()`/`remove()`), mais chaque
  site d'appel qui fait aujourd'hui `.append()`/`.show()`/`.hide()` doit
  être repensé individuellement.

Conformément à `CONSIGNES-AGENTS-IA.md` (proposer un plan avant un gros
morceau, ne pas trancher seul), cette session s'arrête à l'audit et au plan
proposé (`popupMenuTab` comme premier candidat de portage, le plus simple
des quatre car sans injection dynamique par plugin) — pas de code de
portage réel livré.

## Livré cette session

- `docs/gtk4-migration.md` §3.6-ter : inventaire complet (tableau des 5
  menus/mécanismes, chiffres exacts, 4 difficultés identifiées, plan
  proposé).
- `tests/test_gtk4_context_menus_baseline.py` (nouveau, 3 tests) : verrouille
  les comptages de l'audit (6 `Gtk.Menu()`, 5+1 sites `.popup()` legacy) par
  scan textuel — même principe que `test_gtk4_core_rupture_points.py`,
  mais pour un point de rupture non résolu plutôt que résolu, afin de
  détecter toute dérive avant le portage réel et de servir de check-list
  pour la session qui le traitera.
- `docs/features-backlog.md`, `CLAUDE.md`, `CHANGELOG.md` : mis à jour (voir
  diffs respectifs).

`ruff check`/`ruff format --check` passent sans erreur sur le nouveau
fichier de test. `make lint` reste en échec pour les raisons pré-existantes
déjà documentées (423 erreurs historiques dans `tests/test_gcm.py`,
`CLAUDE.md`) — non concerné par cette session.

## Questions posées à l'auteure (à confirmer avant d'implémenter)

1. **Ordre des trois chantiers GTK4 restants** : `plugins/ssh/gtk4.py`
   (widgets réels), menus contextuels (détaillés ci-dessus), ou RDP (§3.4,
   le plus incertain) — lequel traiter en premier ? Proposition de cette
   session : menus contextuels, en commençant par `popupMenuTab` seul (le
   plus simple des quatre, cf. ci-dessus), mais l'arbitrage relève d'un
   choix de risque/priorité qui n'est pas qu'à moi de trancher.
2. **Master password (session-27)** : que faire en cas de mot de passe
   maître oublié, sachant qu'aucun mécanisme de recouvrement n'est
   identifié (les mots de passe stockés deviendraient définitivement
   inaccessibles) ? Proposer la protection à l'activation seulement (choix
   explicite de l'utilisatrice), ou la forcer au premier lancement ?
3. **`snmp_push_core.py` vs `snmp_bulk_core.py`** : deux implémentations
   parallèles de la même fonctionnalité coexistent (le premier complet —
   SFTP+FTP/TFTP, asyncio — mais non importé nulle part ; le second utilisé
   par `plugin_snmp_push.py`). Faut-il basculer vers `snmp_push_core.py`,
   le supprimer, ou les garder tous les deux pour des cas d'usage
   différents ?
4. **`ssh_config_editor.py`** : module complet mais son point d'intégration
   dans l'interface n'a pas été retrouvé — reste-t-il un module à câbler,
   ou un vestige à retirer ?

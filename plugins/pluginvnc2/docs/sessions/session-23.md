# Session 23 — 2026-09-14

Suite à session 22 (icône « Coller »). Continuation générale de
l'utilisateur (« continuer »), même mode que sessions 16, 18, 19, 20, 21
et 22 : pas de phase de proposition/confirmation, une feature unique et
bornée, choisie en repartant d'un besoin utilisateur réel plutôt que d'un
nouveau point de l'audit « accès à `self.client` » (clos depuis la
session 15) ou de l'une des pistes différées (aucun besoin exprimé pour
le raccourci clavier du dialogue d'envoi de texte, ni pour le garder
ouvert).

## Feature — Délai affiché pendant l'attente d'une reconnexion automatique

Besoin retenu : en relisant le mécanisme de reconnexion automatique
(session 17) pour chercher une piste, remarqué que `_schedule_auto_reconnect()`
journalise le délai avant la prochaine tentative (`logger.info`) mais que
ce délai n'est JAMAIS montré à l'utilisateur — l'interface affiche
seulement le message d'erreur brut (`_set_status(VncStatus.ERROR, f"Connexion
interrompue : {exc}")`) dans le placeholder. Pendant les secondes
d'attente, rien à l'écran n'indique qu'une reconnexion EST prévue ni
dans combien de temps -- l'utilisateur pourrait croire l'onglet
définitivement planté et fermer la fenêtre par réflexe pendant l'attente,
alors qu'une reconnexion automatique est en cours.

### Conception

- `VncDisplay._append_reconnect_delay_to_message(message, delay_seconds)` :
  méthode statique pure (même style que
  `_resolve_reconnect_delay_seconds` juste au-dessus), complète le
  message par « — nouvelle tentative automatique dans Ns ».
- Câblée dans `_set_status()` : le message est complété AVANT
  `self.emit("vnc-status-changed", ...)`, pas après -- sinon l'interface
  afficherait un instant le message brut sans l'info de délai. Seulement
  quand `_should_schedule_auto_reconnect()` renvoie vrai (donc uniquement
  après une coupure en cours de session, jamais sur un échec de connexion
  initiale -- même condition que la planification elle-même, cf.
  `_should_schedule_auto_reconnect`).
- Décision de conception délibérée : **pas de changement de signature de
  `_schedule_auto_reconnect()`**. Le délai aurait pu lui être passé en
  paramètre depuis `_set_status()` pour éviter un calcul redondant, mais
  `tests/test_auto_reconnect.py` la monkeypatche déjà à plusieurs endroits
  comme `lambda: calls.append(1)` (0 argument) -- changer sa signature
  aurait cassé ces tests pour un gain minime. À la place, le délai est
  recalculé une deuxième fois dans `_set_status()`
  (`_resolve_reconnect_delay_seconds(self._reconnect_attempt)`, un calcul
  pur sans effet de bord) : `self._reconnect_attempt` n'a pas encore
  changé entre les deux appels (il n'est incrémenté que DANS
  `_schedule_auto_reconnect`, appelée juste après), donc les deux calculs
  sont garantis identiques -- aucun risque d'incohérence entre le message
  affiché et le délai réellement programmé. Nouvelle entrée dans
  `docs/pieges.md` sur cette classe de piège (signature déjà couverte par
  des tests qui monkeypatchent en tant qu'attribut d'instance).
- Pas de décompte en temps réel (secondes qui défilent à l'écran) :
  message STATIQUE fixé une fois au moment de la planification. Un
  décompte live aurait exigé un second système de minuteur
  (`GLib.timeout_add` toutes les secondes, à annuler proprement en plus
  du minuteur de reconnexion existant) pour un gain d'information limité
  par rapport au message statique -- gardé pour une future session si un
  besoin réel s'exprime (noté dans le backlog).

## Tests

`tests/test_auto_reconnect.py` étendu (fichier existant, pas de nouveau
fichier -- cette feature complète un mécanisme existant plutôt que d'en
introduire un nouveau) :

- 2 tests purs pour `_append_reconnect_delay_to_message` (message non
  vide ; message vide -- cas qui n'arrive pas en pratique mais qu'une
  fonction pure doit gérer correctement).
- 2 tests de câblage bout en bout dans la section déjà existante pour
  `_set_status()` : le message ÉMIS inclut bien le délai quand une
  reconnexion est planifiée (`_had_connected_before=True`) ; le message
  émis reste inchangé quand aucune reconnexion n'est planifiée (échec de
  connexion initiale). Capturés via `display.emit = lambda ...`, même
  principe de monkeypatch direct que le reste du fichier (aucun test de
  ce dépôt ne s'appuie sur une vraie émission/connexion de signal
  GObject, cf. `docs/pieges.md` § stub).

Contre-épreuve : le `if will_auto_reconnect:` entourant l'augmentation du
message dans `_set_status()` changé temporairement en `if False:` — seul
le test attendant le message augmenté échoue, les 17 autres tests du
fichier restent verts (y compris celui qui vérifie l'ABSENCE
d'augmentation, qui n'était de toute façon pas concerné). Correctif
restauré, suite complète repassée au vert.

151 tests au total, tous verts (147 + 4 nouveaux) via
`PYTHONPATH=tests/gtk_stub pytest tests/ --ignore=tests/gtk_stub`.
`ruff check`/`ruff format --check` propres sur tout le dépôt. Les 14
tests déjà existants dans `tests/test_auto_reconnect.py` (avant cette
session) repassés au vert sans aucune modification -- vérifié explicitement
que le changement de conception ci-dessus (pas de nouvelle signature) les
laissait tous valides avant même d'ajouter les 4 nouveaux.

## Backlog après cette session

Toujours aucun point ouvert de la famille `self.client`. Trois pistes
différées à ce jour : raccourci clavier pour le dialogue d'envoi de texte
et dialogue restant ouvert pour un envoi répété (depuis la session 20) ;
décompte en temps réel pour la reconnexion automatique plutôt qu'un
message statique (cette session). Prochaine session : repartir d'un
nouveau besoin utilisateur réel, ou d'une extension protocolaire côté
`asyncvnc2_patched` si ce fork devient disponible dans un futur paquet.

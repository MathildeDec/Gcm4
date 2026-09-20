# Session 06 — 2026-09-01 (plus tôt) — Masquage des mots de passe cluster (`#P=`)

## Fonctionnalité livrée

| Masquer les mots de passe dans les commandes cluster (`#P=password`) | ✅ Fait (2026-09-01) — voir §2.6 pour le détail. Marqueur `#P=<valeur>` : résolu en clair pour l'envoi (`gcm4_core.resolve_cluster_command()`), masqué par des astérisques dans l'historique cluster rappelable (`gcm4_core.mask_cluster_command()`) pour qu'un mot de passe tapé une fois ne persiste jamais en clair en mémoire au-delà de l'envoi. Fonctions pures dans `gcm4_core.py`, 10 tests dans `tests/test_gcm4_core.py`, câblage mince dans `Wcluster.send_cluster_commands()` |

---
*Note de journal d'origine (claude.md) : « Il y a quatorze sessions (2026-09-01, plus tôt) : masquage des mots de passe cluster (marqueur #P=, gcm4_core.resolve_cluster_command()/mask_cluster_command(), 10 tests), détail §2.6/§4.1. »*

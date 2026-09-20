# pluginvnc2

Onglet VNC (GTK4) pour gnome-connection-manager, basé sur un fork maison
d'`asyncvnc2`. Fichier unique (`vnc_tab.py`) pour une installation simple.

- **Notes techniques (point d'entrée)** → [`CLAUDE.md`](CLAUDE.md)
- **Fonctionnalités détaillées et backlog** → [`docs/features-backlog.md`](docs/features-backlog.md)
- **Pièges connus, à ne pas réintroduire** → [`docs/pieges.md`](docs/pieges.md)
- **Historique détaillé par session** → [`docs/sessions/`](docs/sessions/)

## Installation

```bash
./install.sh
```

Installe les dépendances, vérifie `ruff` et lance les tests. Voir
`CLAUDE.md` pour le détail du fonctionnement des tests sans GTK4
disponible (mode stub CI).

## Dépendances

- `PyGObject>=3.50` — **via le gestionnaire de paquets système**, pas
  pip (voir `install.sh`). Sur Debian/Ubuntu :
  `sudo apt install python3-gi gir1.2-gtk-4.0`
- `numpy`, `cryptography`, `loguru` — via `requirements.txt`
- Un `asyncvnc2` modifié sur le `PYTHONPATH` (fork séparé, non inclus
  dans ce paquet)

## Intégration dans gnome-connection-manager

Copier `vnc_tab.py` dans le dépôt principal. Les deux hypothèses
d'intégration (conteneur d'onglets, action plein écran) ont été
tranchées contre le dépôt `gcm4` réel — voir `docs/features-backlog.md`
§ "Hypothèses vérifiées lors de l'intégration".

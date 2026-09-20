# Session 01 — 2026-09-01

**Le stub GTK couvre maintenant l'instanciation réelle de `VncDisplay`.**

Point de départ : `features.md` listait comme non couvert par le stub
initial le fait de tester `get_display_transform()`/`widget_to_remote()`
(letterboxing CONTAIN, FILL, multi-écran) via un VRAI `VncDisplay(...)`,
plutôt que seulement ses méthodes statiques. `tests/test_display_transform.py`
comble ce trou.

Deux choses ont dû changer pour que ça marche :

- `conftest.make_test_display(...)` : construit un `VncDisplay` réel puis
  écrase `get_width`/`get_height`/`get_content_fit` (attributs
  d'instance — priment sur la méthode de classe stub) et remplace
  `client` par un `types.SimpleNamespace` minimal. À utiliser plutôt que
  de réinventer le monkeypatching à chaque nouveau test qui a besoin d'un
  `VncDisplay` réel.
- Le stub `tests/gtk_stub/gi/repository/__init__.py` avait un vrai trou :
  les classes GTK fabriquées dynamiquement ne géraient l'accès attribut
  QUE côté instance (`__getattr__` sur les objets), pas côté classe —
  donc `Gtk.ContentFit.CONTAIN` et `Gtk.EventControllerScroll.new(...)`
  (accès direct sur la classe, jamais sur une instance) levaient
  `AttributeError`/`TypeError`. Invisible tant qu'aucun test n'instanciait
  `VncDisplay` pour de vrai. Corrigé avec une métaclasse (`_WidgetMeta`)
  qui renvoie une `_ClassConstant` (sous-classe de `str`, à la fois
  comparable comme une constante ET appelable comme un "constructeur"
  GI) pour tout attribut de classe inconnu.

À retenir pour la suite : si un futur test instancie `VncTab` (pas juste
`VncDisplay`) ou déclenche un chemin de code touchant à autre chose que
taille/contenu/client (rendu réel du framebuffer, `Gdk.MemoryTexture`,
vrais événements souris/clavier...), il faudra probablement enrichir le
stub à nouveau — il reste volontairement minimal, pas une
réimplémentation de GTK4. Voir `docs/pieges.md` § « État des tests ».

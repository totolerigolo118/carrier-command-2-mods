# Plugin v3 + onglet SPEED v2 : le lien entre l'onglet et le plugin, les risques, comment poser

Préparé le 29/10/2026, **hors du jeu**. **Posé le 30/10/2026 à 07:38, avec l'accord du moddeur, jeu fermé** (étape M3 ci-dessous) : le mod `cc2_modes` contient maintenant la mesure,
l'onglet **v2** (`0A402A3E…`) et le plugin **v3** (`331581C6…`, 222 720 octets), `modes.ini` toujours en observation (`eco_enabled=0`). Premier essai en jeu le 30/10 (ÉCO sur l'avion 10 : 80 m/s, −21 % de carburant ; garde-fou « HELD » vu ; voir `ETUDE.md` §16).
Les corrections tirées des revues du 29/10 (lecture stricte de `modes.ini`, garde-fou pilotage de l'onglet, lignes de journal réservées…) sont **préparées, pas posées** :
voir `RISQUES_v3_1.md` (onglet v2.1 + plugin v3.1). À lire avec `RISQUES_v2.md` (FLANK, ÉCO par type : tout ce qui y est dit reste valable) et `RISQUES_pose.md` (périmé pour les chiffres de la v1).

> **Attention (29/10)** : Steam a mis le jeu à jour le 28/10 ; le SDK CC2X reste **inactif** sur le nouvel exécutable, donc aucun plugin ne s'y charge (ETUDE.md §15). Tout ce qui suit suppose le jeu **ancien build** (copie séparée de l'ancien exe, voie A de l'étude « mise à jour ») ou un chargeur qui accepte le nouveau. Le plugin reconnaît les deux builds, mais **ne rend pas le SDK compatible**.

## Ce qui est nouveau

| Pièce | Ce qu'elle fait |
|---|---|
| **Plugin v3** (`cc2x_modes.dll`, 222 720 octets, sha256 `331581C6…8729`) | la v2 (ÉCO par type, FLANK en plancher) **plus un pont Lua** : `cc2x.modes.set(id, mode)`, `get(id)`, `hold(id)`, `status()`. Le mode de chaque avion se règle depuis l'écran, il est **partagé entre les 3 écrans** et vit pendant la partie (vidé quand une partie commence ou finit : les numéros d'avion ne valent que dans une partie) |
| **Garde-fou pilotage** | l'écran qui contrôle un avion (`g_viewing_vehicle_id > 0`) appelle `hold(id)` à chaque image ; pendant ce temps et 3 s après, le plugin **ne touche plus** aux gaz de cet avion. La limite de la v2 (« un avion piloté n'est pas détecté ») n'est levée **que si** le jeu fait bien ce qu'on lit dans son code : **jamais vu en jeu** tant que la ligne `id N: HELD` n'est pas apparue dans `cc2x.log`. La revue du 29/10 a de plus montré que l'onglet v2 peut ne jamais poser ce crochet (corrigé dans l'onglet v2.1, `RISQUES_v3_1.md`) |
| **Onglet v2** (`lua/v2/library_custom_5.lua`) | les 3 boutons ECO / NORMAL / FLANK règlent le plugin ; une ligne dit l'état réel : « OBSERVATION : SANS EFFET » (plugin sans `enabled=1`), « ACTIF », « EN ATTENTE » (près du bateau, au sol, en retour), « PILOTE : EN PAUSE » ; en dessous une **autonomie estimée** d'après nos mesures (Albatros 0,22 / 0,282 / 0,304 de carburant par seconde ; Manta 0,36 / 0,77 ; ÉCO du Manta « ? » car non mesuré). **Sans plugin il redevient la maquette actuelle** |
| **Garde de sécurité inchangée** | le plugin n'écrit **rien** tant que `modes.ini` n'a pas `enabled=1`, quoi que l'onglet demande. L'onglet ne peut donc pas activer le plafond / le plancher tout seul |

## Ce qui est vérifié, hors jeu

- **130 contrôles automatiques réussis** sur un faux jeu (les 72 de la v2 + 52 pour le pont Lua + 6 pour la reconnaissance de **deux builds** du jeu : l'ancien et celui de la mise à jour Steam du 28/10) : arguments invalides refusés (nil, texte, 0, négatif, trop grand, mode 3, mode −1, argument manquant), réglage et lecture,
  la table Lua l'emporte sur `modes.ini`, rien d'écrit si `enabled=0`, garde-fou pilotage (pause, reprise après 3 s, appels continus), 64 avions maximum et refus enregistré dans le journal, remise à zéro entre les parties, `status()`.
- Plugin : DLL compilée deux fois avec le même résultat ; imports = ceux de la v2 plus les verrous (`EnterCriticalSection`…) ; aucun accès réseau ni processus ; aucune chaîne suspecte.
- **Scripts Lua** : le vérificateur de syntaxe maison `tour/outils/lua_syntaxe.py` (51 tests ; il accepte les 49 scripts du jeu, les 11 des mods et les nôtres, sans erreur) valide l'onglet v2 ;
  `tour/outils/lua_inconnus.py` ne signale que `cc2x` et nos propres variables (aucune faute de frappe sur les fonctions du jeu). **Pas d'interpréteur Lua** sur ce PC : le **comportement** du script n'a été
  relu qu'à la main (même technique que l'onglet v1, qui marche en jeu).
- Installateur : essayé sur une fausse copie (mise à jour de l'onglet v1 → v2, du plugin v1 → v3, idempotence, retrait ; `mods.xml` identique après retrait ; le vrai plugin posé n'a pas bougé).

## Ce qui n'est PAS prouvé

1. **Que `g_viewing_vehicle_id > 0` veuille bien dire « je pilote cet avion »** (lu dans `screen_vehicle_control.lua` : CAMERA le met, l'écran envoie ce numéro au moteur de contrôle ; jamais vu en jeu). Premier essai : en observation, les lignes `[modes]` du journal diront `id N: HELD (the player is flying it by hand)` quand tu prends un avion en main. Tant que ce n'est pas vu, **ne mets jamais en mode l'avion que tu pilotes**.
2. **Le comportement de l'onglet v2 à l'écran** (placement, texte qui se coupe, clics, pas de barre de défilement) : jamais affiché. S'il plante, il se coupe seul (`pcall`) et le jeu continue ; l'onglet v1 est restaurable.
3. Les points de la v2 : effet de FLANK, IA à grande vitesse, ÉCO du Manta, avion très chargé (voir `RISQUES_v2.md`).

## Les risques, par étape (🟡 global)

| Étape | Ce que ça fait | Risque | Comment on s'en protège |
|---|---|---|---|
| **M3 : mise à jour des fichiers** (`mettre-a-jour --etape interface2` puis `mettre-a-jour-plugin`) — **FAIT le 30/10/2026 à 07:38** | remplace l'onglet v1 par la v2 et le plugin par la v3 dans le mod `cc2_modes` ; dossier du jeu, `mods.xml` inchangés. Réécrit aussi `mod.xml` du mod (texte de description seulement : `396765E7…` → `BEDD15C1…`, constaté le 30/10) | 🟢 | jeu fermé exigé ; ne remplace que des versions connues ; retrait possible |
| **A3 : lancer avec v3 + onglet v2, `enabled=0`** | l'onglet lit et règle les modes dans le plugin ; **le plugin n'écrit rien dans le jeu** ; les appels `hold` partent du script | 🟡 faible | partie neuve jetable ; si l'onglet plante : coupé seul ; si le plugin plante : retrait par un fichier |
| **B3 : activer** (`enabled=1`), un avion | ÉCO ou FLANK **depuis les boutons**, sur un avion qui vole seul loin du bateau | 🟡 moyen (ÉCO) à moyen-élevé (FLANK) | comme dans `RISQUES_v2.md` ; un seul avion ; ne pas piloter cet avion ; coupure `enabled=0` en 3 s |

Pas de risque pour tes sauvegardes (essais en partie neuve jetable). Pas de fuite de données (aucun accès réseau). Dépendance : le chargeur du SDK (`dinput8.dll`).

## Alternatives plus sûres

- Rester à la v3 posée (observation, `enabled=0`) : rien à faire. Faire seulement **A3** (lancer, lire l'onglet, voir « OBSERVATION : SANS EFFET », vérifier le garde-fou HELD dans le journal) sans jamais mettre `enabled=1`.
- Commandes à la main par `modes.ini` (v1 / v2), sans l'onglet.

## Poser, essayer, retirer (M3 fait le 30/10 ; il reste A3 puis B3, chacun avec l'accord du moddeur, jeu fermé pour toute pose)

```bash
python tour/etudes_modes_carburant/mod_modes.py mettre-a-jour --etape interface2   # (fait) onglet v2 (mods.xml intact)
python tour/etudes_modes_carburant/mod_modes.py mettre-a-jour-plugin --version 3   # (fait avec la v3 ; depuis la préparation de la v3.1, SANS --version l'outil vise la v3.1)
python tour/etudes_modes_carburant/mod_modes.py etat                               # doit dire : onglet v2, plugin v3 conforme
python tour/etudes_modes_carburant/mod_modes.py mettre-a-jour --etape interface    # retour à l'onglet v1 (maquette)
python tour/etudes_modes_carburant/mod_modes.py retirer-plugin                     # retire le plugin
```

> Depuis le 30/10, `mod_modes.py` refuse **toute** commande qui écrit si un `carrier_command*` tourne (l'ancien exe de la voie A compris, revue I2) et n'accepte plus `--jeu-ouvert-ok`.
> `etat` dit maintenant « v3 … mettre-a-jour-plugin le remplacera par la v3.1 » : c'est une information, pas une action faite.

Réglages : `%APPDATA%\Carrier Command 2\cc2x\modes.ini` (modèle : `plugin/modes.ini.example`, inchangé). Sans fichier, ou avec `enabled=0` : observation seulement.

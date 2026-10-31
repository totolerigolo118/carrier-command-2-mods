> **PARTIELLEMENT OBSOLÈTE (25/10/2026) — lis d'abord ../PASSATION_windows.md.**
> Restent valables : section 3 (énergie, plateforme, grue, roulage : formules et valeurs) et section 4 (empreintes des valeurs).
> Remplacés : section 1 (« tous les joueurs profitent du patch » est une déduction à confirmer, jamais testée avec un 2e joueur) ; sections 5 et 8 (patcher le .exe sur le disque, fichiers .bat, « pip install pefile capstone » et Ghidra : plus la méthode retenue, et **rien ne s'installe sans l'accord du moddeur**) ; section 6 (la référence Windows est à mesurer à l'étape 0 bis de la nouvelle feuille).
> Les fichiers cités dans cette feuille (`ascenseur_x2.py`, `generer_table.py`, `library_custom_1.lua`, `test_horloge.py`) sont à côté, dans ce dossier ; leurs chemins sont ceux du Mac.

# Passation : « Ascenseur ×2 » de Carrier Command 2, de la version Mac à la version Windows

Fiche écrite le 23/10/2026 par Claude Code sur le Mac du moddeur, pour Claude Code sur sa tour Windows.
Fichiers de référence joints : `ascenseur_x2.py` (l'outil Mac, qui marche), `generer_table.py` (comment la
table des retouches a été produite), `library_custom_1.lua` + `test_horloge.py` (l'horloge de jeu).
Ce sont des références : leurs chemins de fichiers sont ceux du Mac, à adapter sous Windows.

---

## 0. À lire en premier : avec qui tu travailles

- **Le moddeur ne code pas.** Il juge le résultat, pas le code. Réponds-lui en français, sans jargon, et définis
  au passage les mots techniques que tu emploies.
- **Une seule question à la fois**, et termine chaque réponse par la prochaine action concrète.
- **Vérifie toi-même et montre la preuve** (sortie réelle des programmes, chiffres). Ne présente jamais
  « ça devrait marcher » comme un fait. Si tu n'as pas pu vérifier, dis-le franchement.
- **Ne lance jamais le jeu et ne le ferme jamais sans le lui demander** dans le message en cours. Il teste
  lui-même en jeu.
- Pas de cosignature Claude dans git (s'il y a un dépôt).

## 1. Le but

Rendre les **sorties et retours d'avions environ 2 fois plus rapides** sur le porte-avions, en échange d'une
**consommation d'énergie doublée** pour le système ASCENSEUR/GRUE (c'est l'idée du moddeur : un compromis).
Sur Mac c'est fait et **validé en jeu : sortie de 4 avions 3:50 → 2:15 en temps de jeu (×1,70)**.
Il faut faire la même chose sur le **programme Windows** du jeu, sur sa tour (c'est là qu'il joue vraiment
et qu'il héberge ses parties en multijoueur).

Bon à savoir : la simulation tourne chez l'hôte. Si le moddeur héberge depuis sa tour patchée, **tous les joueurs
qui le rejoignent profitent du patch** sans rien installer. Le Workshop ne peut PAS distribuer ce patch (il ne
remplace que des fichiers de données, jamais le programme).

## 2. Pourquoi il faut patcher le programme (et pas un fichier de réglages)

Les vitesses sont **écrites en dur dans le programme**. Les attributs `drive_*` de `lift_constraint` dans
`rom_0/game_objects/vehicle_chassis_carrier.xml` n'y changent RIEN : le code avance lui-même la consigne de
l'ascenseur à chaque tick puis pose la pièce physique. C'est pour ça que les mods Workshop « ascenseur
rapide » (ex. « Lubricant ») n'ont jamais marché. `constants.txt` ne contient aucune de ces valeurs.

## 3. Ce que fait le jeu (à reconnaître dans le désassemblage Windows)

Le jeu tourne à **30 ticks par seconde de jeu**. Sur Mac le programme `build_mac` garde les noms des
fonctions C++ (non strippé) ; sur Windows il est probable que non : il faudra reconnaître les fonctions
**par leurs valeurs** (section 4).

### 3.1 Partage d'énergie — `c_vehicle_carrier_server_power_manager::build` et `::tick`

5 systèmes, chacun avec une « part maximale » et des sous-systèmes `{demande, poids, alloué}` (3 floats) :

| système | part max | sous-systèmes (poids) |
|---|---|---|
| réparation | 0,8 | 8 (4, puis 1 ×7) |
| propulsion | 0,8 | 1 |
| armes | 0,6 | 10 (1 chacun) |
| **ascenseur/grue** | **0,4** | **2 (1 et 1) : n°0 = plateforme, n°1 = grue du hangar** |
| radar | 0,2 | 1 |

Désir d'un système = Σ(demande × poids) / Σ(poids) × part. Si la somme des désirs dépasse 1, tout le monde
est réduit au prorata. Alloué d'un sous-système = demande × (alloué/désir). Plateforme et grue avancent de
« pas × alloué » ; **le roulage sur le pont ne dépend pas de l'énergie**.

Sur Mac, `build` contient des stores immédiats : `movl $0x3f4ccccd` (0,8), `$0x3e4ccccd` (0,2),
`$0x3f4ccccd`, `$0x3f19999a` (0,6), puis **`movl $0x3ecccccd, 0x118(%r15)` (0,4)** = la part de
l'ascenseur/grue. **Retouche : 0x3ECCCCCD → 0x3F4CCCCD (0,4 → 0,8).** C'est le « ×2 énergie ».

### 3.2 Plateforme de l'ascenseur — `c_vehicle_server_carrier::tick_server_type`

```
cible = niveaux[indice_cible]            (0 = en haut, -9 = en bas)
delta = clamp(cible - position, -0.025, 0.025)      ← pas max par tick (0,75 m/s)
si |delta| > 0.001 : demande = clamp(|delta| / 0.025, 0, 1) sinon 0
sous_systeme_energie[0].demande = demande
alloue = clamp(sous_systeme_energie[0].alloue, 0, 1)
si alloue > 0 : position += delta × alloue
```
Sur Mac : `maxss [-0.025]`, `minss [0.025]`, `ucomiss [0.001]`, `divss [0.025]` à la suite.
**Retouche : les 3 lectures de ±0,025 → ±0,05** (le `0.001` ne bouge pas). 9 m : 12 s → 6 s.

### 3.3 Grue du hangar — dans `c_vehicle_server_carrier::docking_manager_air::update`

Machine à états (file `mm_vector<e_crane_state>`), position x/y/z + rotation. Par tick et par axe :
`d = clamp(cible - pos, -max, +max)` puis `pos += d × alloué(sous-système 1)` ; demande = max(|dxz|/(1/6),
|dy|/(1/30)) via un `divps` par le vecteur (1/6, 1/30, 0, 0). Cibles de hauteur 11,0 et 12,0 ; rotation
bornée à ±0,04 rad/tick ; arrivée quand |d| < 0,01 (ou < 0,04 pour la rotation).
**Retouches (16 sur Mac)** : ±1/6 → ±1/3 (5 → 10 m/s), ±1/30 → ±1/15 (1 → 2 m/s), ±0,04 → ±0,08.
Le `divps` a été laissé tel quel (la demande plafonne à 1, sans effet notable).

### 3.4 Roulage des avions sur le pont — même fonction `docking_manager_air::update`

7 blocs du même modèle (3 listes de chemins : sortie, retour, etc.) :
```
reste = (1 - t) × L               (L = longueur du tronçon)
v = min(v + 0.05, 2.5)            ← accélération 1,5 m/s² et plafond 2,5 m/s
(sur le dernier tronçon seulement : v = min(v, reste)  → freinage)
si reste < 0.1 (ou 0.01) : tronçon suivant
sinon t += v / (L × 30)
```
**Retouches (14 sur Mac)** : les 7 `addss [0.05]` → 0,1 et les 7 lectures de 2,5 → 5,0.
**Ne PAS toucher** : la course de décollage (un `addss [0.5]` sans plafond), les seuils d'arrivée 0,1/0,01
(les agrandir ferait « sauter » les avions). Le freinage final non touché explique le ×1,7 au lieu de ×2.

## 4. Les empreintes (valeurs float 32 bits, petit-boutiste dans le fichier)

| valeur | hex | rôle | | valeur doublée | hex |
|---|---|---|---|---|---|
| 0,4 | 0x3ECCCCCD | part énergie ascenseur/grue | → | 0,8 | 0x3F4CCCCD |
| 0,025 | 0x3CCCCCCD | pas plateforme | → | 0,05 | 0x3D4CCCCD |
| -0,025 | 0xBCCCCCCD | pas plateforme | → | -0,05 | 0xBD4CCCCD |
| 0,001 | 0x3A83126F | zone morte plateforme (ne pas toucher, sert à reconnaître) | | | |
| 1/6 | 0x3E2AAAAB | grue horizontal | → | 1/3 | 0x3EAAAAAB |
| -1/6 | 0xBE2AAAAB | grue horizontal | → | -1/3 | 0xBEAAAAAB |
| 1/30 | 0x3D088889 | grue vertical | → | 1/15 | 0x3D888889 |
| -1/30 | 0xBD088889 | grue vertical | → | -1/15 | 0xBD888889 |
| 0,04 | 0x3D23D70A | grue rotation | → | 0,08 | 0x3DA3D70A |
| -0,04 | 0xBD23D70A | grue rotation | → | -0,08 | 0xBDA3D70A |
| 0,05 | 0x3D4CCCCD | accélération roulage | → | 0,1 | 0x3DCCCCCD |
| 2,5 | 0x40200000 | plafond roulage | → | 5,0 | 0x40A00000 |

Autres repères : 11,0 = 0x41300000 et 12,0 = 0x41400000 (hauteurs de la grue), 30,0 = 0x41F00000 (ticks/s
dans `t += v/(L×30)`), 0,01 = 0x3C23D70A, 0,1 = 0x3DCCCCCD (seuils d'arrivée), 0,5 = 0x3F000000 (décollage).

## 5. Méthode qui a marché sur Mac (à adapter)

1. **Ne jamais modifier une constante partagée.** Les floats sont dans une zone de constantes partagée par
   des milliers d'instructions. On redirige **uniquement les instructions voulues** vers une autre adresse
   où la valeur doublée existe déjà, dans une section **en lecture seule** (`__TEXT,__const` sur Mac ;
   sous Windows, `.rdata`). Sur Mac, toutes les valeurs doublées existaient déjà. Rien n'est décalé.
2. Instructions SSE avec opérande mémoire RIP-relatif (`f3 0f 10/58/5d/5e/5f modrm disp32`) : le disp32 est
   les 4 derniers octets ; `nouveau_disp = adresse_nouvelle_constante - (adresse_instruction + longueur)`.
3. Une table `(adresse, octets d'origine, ancienne constante, nouvelle constante)` générée depuis le
   désassemblage (voir `generer_table.py`), puis un outil qui : refuse si le jeu tourne ; refuse si le
   programme n'est pas exactement celui analysé (empreinte md5/sha) ; vérifie que chaque site a ses octets
   d'origine OU tous ses octets modifiés (sinon : mise à jour Steam → ne rien toucher) ; garde une copie de
   secours du programme d'origine ; écrit via un fichier temporaire puis remplacement ; relit et contrôle.
4. Vérifications faites sur Mac : chaque site relu lit **exactement le double** (comparaison float exacte,
   pas d'arrondi d'affichage) ; aller-retour (appliquer puis `--origine`) = fichier identique à l'octet ;
   seul le nombre d'octets attendu change.

### Spécificités Windows à prévoir (non vérifiées, à constater)

- **Compilateur Microsoft** : les floats sont souvent des littéraux partagés `__real@3ccccccd` dans
  `.rdata`. Les **négatifs** peuvent ne pas exister comme constantes : le compilateur peut charger le positif
  puis inverser le signe (`xorps` avec un masque `__xmm@80000000…`). Dans ce cas, rediriger la lecture du
  positif suffit pour les deux bornes. Les clamps peuvent être compilés en `minss/maxss` ou en comparaisons.
- Fonctions **inlinées différemment** : `tick_server_type` peut être absorbée ailleurs. Cherche les
  **groupes de constantes** (ex. 0,025 + 0,001 dans quelques dizaines d'octets ; 2,5 + 0,05 par paires, ×7 ;
  1/6 + 1/30 + 11,0/12,0 ensemble ; les 5 parts d'énergie 0,8/0,2/0,8/0,6/0,4 dans une même fonction).
- Si une valeur doublée n'existe pas dans `.rdata` : chercher n'importe quel emplacement 4 octets alignés
  en lecture seule qui la contient ; sinon, en dernier recours, une petite zone libre en fin de section
  (avec ajustement des tailles) — à éviter si possible.
- Vérifier que l'exe n'est **pas signé** ou que la signature n'est pas contrôlée (Steam ne vérifie pas les
  fichiers au lancement, seulement sur « Vérifier l'intégrité »). Le checksum PE n'est pas contrôlé pour un
  programme ordinaire.
- Outils conseillés : Python + `pip install pefile capstone` (scanner les instructions qui lisent une
  adresse donnée, comme `generer_table.py` le faisait avec objdump). Ghidra si besoin de vue d'ensemble.
- Programme : chercher le `.exe` principal dans
  `C:\Program Files (x86)\Steam\steamapps\common\Carrier Command 2\` (ou la bibliothèque Steam du moddeur).

## 6. Le test du moddeur (protocole validé le 23/10)

Le Mac rame (le jeu tombait à 50-72 % de sa vitesse), donc **on mesure en temps de jeu**, pas au chronomètre :
même sauvegarde, même endroit, sortie des avions **A1, A2, A5, A6** ; noter l'heure de jeu au premier ordre
de lancement et quand le dernier a décollé. Résultats Mac : **vanilla 3:50, patché 2:15**. On attend à peu
près la même chose sur Windows (la tour devrait tourner à pleine vitesse, mais la mesure en temps de jeu
reste la bonne).

## 7. L'horloge de jeu (facultatif mais utile pour le test)

`library_custom_1.lua` affiche « TEMPS DE JEU h:mm:ss.s » (= `update_get_logic_tick()/30`) en bas à gauche des
écrans de contrôle des véhicules (`screen_veh_l/m/r`). Installation : copier le fichier dans
`rom_0\scripts\library_custom_1.lua` **seulement s'il est vide** (fichier vide prévu par le jeu pour les
ajouts). Elle s'accroche par `begin_load` + `begin_get_screen_name` ; vérifier que le
`screen_vehicle_control.lua` actif (sur la tour, le mod Workshop **Revolution 1.5, 3098073689**, le remplace)
a toujours `begin()` qui appelle `begin_load()`, et qu'aucun mod actif ne fournit son propre
`library_custom_1.lua`. `test_horloge.py` la teste hors jeu (`pip install lupa`, option `--lua53`).
Attention : `update_get_time_ms` n'existe PAS dans les écrans du porte-avions (seulement dans le frontend).

## 8. Ce que le moddeur attend à la fin

- Un dossier rangé (comme sur Mac) avec : l'outil Windows (`--origine`, `--etat`), **deux fichiers à
  double-cliquer** (`.bat`) « Activer ascenseur x2 » et « Remettre ascenseur d origine », une copie de secours
  du programme d'origine, un LISEZ-MOI en français.
- La preuve des vérifications (sites relus = double exact, aller-retour identique).
- Puis son test en jeu (section 6). À refaire après chaque mise à jour Steam.

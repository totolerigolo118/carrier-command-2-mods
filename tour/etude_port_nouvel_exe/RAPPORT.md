# Portage vers le NOUVEL exe de Steam (461E1262…) : étape 1 sur 3, tout hors du jeu

Étiquettes : **MESURÉ** (calculé ou relu par un script, résultat vu), **LU** (dans un fichier ou une page), **INFÉRÉ** (déduit, à vérifier en jeu), **RAPPORTÉ** (dit par un tiers, non vérifié). Aucun pourcentage de réussite n'est donné : les estimations passées se sont toutes révélées fausses.

**Ce que j'ai fait / pas fait** : rien lancé (ni le jeu ni Steam), rien écrit dans le dossier du jeu, `%APPDATA%`, `mods.xml`, `dinput8.dll`, `cc2x_*.dll`, `frein.ini`, `modes.ini`, aucun téléchargement, aucune installation. Le `carrier_command.exe` de Steam a été **seulement lu** (sha256 relu à la fin : `461E1262…`, inchangé). Tout est écrit dans ce dossier (`tour/etude_port_nouvel_exe/`), dans `tour/outils/` (l'outil de patch et ses tests) et dans le dossier de travail `C:\Users\UTILISATEUR\Documents\cc2-port-travail\` (copies d'exe, hors dépôt). Rien n'est commité.

## Résumé

1. **Patchs d'exe (partie 1)** : les 6 modules de `patch_exe.py` (pas 4) sont portés ; **41 champs sur 41 retrouvés** dans le nouvel exe, par deux méthodes indépendantes qui s'accordent ; **les 6 modules sont portés et prouvés sur les octets, aucun n'est bloqué** (dans l'ordre demandé par le moddeur : `ascenseur_x2`, `temps_x2`, `pont_retour_x2`, puis `helicos_approche_x2`, `atterrissage_cercle`, `atterrissage_creneau`) ; copie patchée « comme avant » = `ascenseur_x2 + temps_x2 + pont_retour_x2` prête hors du jeu (`5AF41B4D…`, même composition que l'exe du 28/10 10:25, `0C5DFE52…`) et la variante à deux modules (`6072A2FD…`, comme `8E7FCBB6…`) ; `retirer` redonne `461E1262…` exactement ; l'outil a deux profils et refuse tout autre fichier (autotests : 182 vérifications ancien exe, 207 nouvel exe, 0 échec). **Jamais essayé en jeu.**
2. **SDK (partie 2)** : le SDK qu'on compile est la **0.5.0** (clone au commit `7ab05c7`), pas la 0.4.0 de `passation_windows`. Un 2e profil (7 valeurs du `Profile` + 17 adresses de `world.c`) est ajouté dans une copie, la DLL compile avec la même chaîne (prouvé : sources inchangées = DLL du jeu hors horodatage), le profil ancien est intact. **Rien posé.**
3. **Plugins (partie 3)** : les 11 sites (crochets du frein v10 et v11, adresse lue de modes) sont **tous SÛRS** ; les décalages de champs d'objets sont **identiques sur tous les accès du code** (311 accès à `dock_state`, tous identiques). **Trouvaille** : `cc2x_modes` connaît déjà le nouvel exe (et la DLL posée aussi) ; le frein, lui, refuse encore le nouveau nom de build et doit être porté (table par build).
4. **Rien lancé, rien posé** : ni jeu ni Steam ; le dossier du jeu, `%APPDATA%`, `mods.xml`, les DLL, les `.ini` et l'exe de Steam n'ont pas été touchés (sha256 de l'exe et de `dinput8.dll` relus à la fin).
5. **Limite principale** : 597 blocs de code diffèrent ailleurs dans l'exe entre les deux builds ; je ne les ai pas lus. Aucun de nos sites n'est dedans, mais ils peuvent changer le comportement du jeu. Seul un essai en jeu le dira.

La liste de ce que la partie suivante devra faire est à la fin.

---

## PARTIE 1 — Patchs d'exe (terminée, état au 30/10)

### 1.1 L'essentiel

- **MESURÉ** : les **41 champs** de nos 6 modules d'exe (40 dans le code + 1 valeur dans l'en-tête) sont **tous retrouvés dans le nouvel exe, sans aucun site ambigu ou introuvable**. Chaque site a été retrouvé de deux façons indépendantes (recherche par contexte + alignement de tout le code), qui donnent **la même adresse pour les 40** (`analyse/croisement_alignement_sites.txt`).
- **MESURÉ** : décalage du code **+0x110** pour 39 sites, **+0x130** pour `temps_x2` (le serveur) ; les constantes lues sont décalées de **+0x38** dans la zone `0xdb71xx–0xdb7exx`, de **0** dans la zone `0xce0b58–0xcee4a4` (même adresse) ; la valeur ajoutée dans l'en-tête reste en `0x400310` (bourrage nul identique).
- **MESURÉ** : deux **copies patchées** du nouvel exe existent, hors du jeu, dans `C:\Users\UTILISATEUR\Documents\cc2-port-travail\` :
  - **`carrier_command_nouveau_patche_ascenseur_temps_pont.exe`**, sha256 **`5AF41B4D78CF18EB25C2F227397EAAA2F0E6443E65D2E9A142CC5043F45CC345`** = nouvel exe + `ascenseur_x2` + `temps_x2` + `pont_retour_x2`. C'est « comme avant » au sens de la précision du moddeur : j'ai **vérifié** que l'ANCIEN original + ces trois modules donne exactement `0C5DFE52DFDF1AE002B0CF8B25C6B32CC1EEC953A80E856D37E4016CF2FE120B`, l'exe du jeu du 28/10 10:25 ;
  - `carrier_command_nouveau_patche_ascenseur_temps.exe`, sha256 `6072A2FDE0013074686B2472B599D026B07FC614CC16CF62AB1F43281FB922C0` = nouvel exe + `ascenseur_x2` + `temps_x2` (même composition que l'ancien `8E7FCBB6…`).
  Pour les deux, `patch_exe.py retirer` (module par module) ramène à **exactement `461E1262…`** (vérifié pour la copie à trois modules après la précision). Au désassembleur, le site de `pont_retour_x2` (`0x6fdeb9`) passe de `movss xmm7,[0xdb79c4]` = 30,0 à `movss xmm7,[0xdb7968]` = 15,0.
- **Jamais essayé en jeu.** Tout ce qui est dit ici porte sur les octets et le désassemblage. Il reste à voir en jeu que l'ascenseur, la grue, le roulage et le temps ×2 se comportent comme sur l'ancien exe (INFÉRÉ : oui, parce que les instructions autour sont identiques ; non prouvé).

### 1.2 Les modules de `patch_exe.py` (il y en a **6**, pas 4 comme le disait l'en-tête de l'outil) : état de chacun

Ordre demandé par le moddeur : d'abord `ascenseur_x2`, `temps_x2`, `pont_retour_x2`, ensuite les trois autres. **Aucun module n'est bloqué sur un site** : les 41 champs sont retrouvés, relus au désassembleur et comparés à l'ancien exe patché (1.3 à 1.6). « Porté et prouvé sur les octets » veut dire cela, pas plus : **aucun n'a été essayé en jeu sur le nouvel exe**.

| # | Module | Champs | État | Somme (nouvel exe + ce module seul) | Vu en jeu avant (ancien exe) |
|---|---|---|---|---|---|
| 1 | `ascenseur_x2` | 32 (31 dans le code + 1 valeur dans l'en-tête) | **PORTÉ, prouvé sur les octets** | `1D004BEF…` | oui |
| 2 | `temps_x2` (MODE TEST, jamais en multijoueur) | 1 (facteur de vitesse du serveur 1,0 → 2,0, en `0x835dfb`) | **PORTÉ, prouvé sur les octets** | `A2353B6A…` | oui |
| 3 | `pont_retour_x2` | 1 (`0x6fdebd` : la constante 30,0 lue par la file de roulage de retour devient 15,0) | **PORTÉ, prouvé sur les octets** | `41A00F2C…` | dans l'exe du jeu du 28/10 10:25 (`0C5DFE52…`, LU dans l'étude de mise à jour) et dans la copie « pont » de l'essai 2 du 29/10, toujours mélangé aux autres ; la fiche d'étude du roulage retour dit « jamais vu en jeu » (effet seul jamais mesuré) |
| 4 | `helicos_approche_x2` | 1 | **PORTÉ, prouvé sur les octets** | `0DF816F7…` | non (validé sur le Mac seulement) |
| 5 | `atterrissage_cercle` | 3 | **PORTÉ, prouvé sur les octets** | `A8B4F449…` | oui (essais 1 et 2) |
| 6 | `atterrissage_creneau` | 3 | **PORTÉ, prouvé sur les octets** | `DD55A1A5…` | oui, une seule partie, mélangé au cercle et à `pont_retour_x2` (essai 2 du 29/10) |

Chaque JSON du nouvel exe porte un champ `statut_portage` qui le dit.

### 1.3 Comment les sites ont été retrouvés (sans rien deviner)

Outils (tous en lecture seule sur les exe, lancés avec `python -I -B`) : `outils/pe_lecture.py`, `outils/localiser_sites.py`, `outils/fabriquer_modules_nouvel_exe.py`, `outils/prouver_equivalence.py`, `outils/alignement.py`, `outils/croiser_sites_alignement.py`.

1. **MESURÉ** — pour chaque champ, on désassemble (capstone) l'ancien exe d'origine, on prend 64 instructions avant et 64 après (20 pour un site à cause d'un bloc voisin différent), on remplace par des jokers **ce qui change forcément** (adresses absolues avec entrée de relocation, déplacements des `call`/`jmp`/`jcc`), et on cherche ce motif dans **tout le code** du nouvel exe. Une seule occurrence = site retrouvé ; zéro ou plusieurs = on s'arrête. (L'ancienne recherche de la passation précédente n'en retrouvait que 23 sur 41 parce que ses « voisins » contenaient justement des adresses décalées.)
2. **MESURÉ** — ce que cachaient les jokers est contrôlé : même section, mêmes octets pour chaque constante lue (en lecture seule), correspondance cohérente (58 adresses absolues et 114 cibles de saut vues : **aucune** ancienne adresse n'a deux équivalents), ordre des sites conservé, aucun doublon.
3. **MESURÉ** — **croisement** avec un alignement du code entier (`analyse/diff_code_ancien_nouveau.txt`) : sur les 2 569 512 instructions de l'ancien exe, 2 560 297 sont dans des suites identiques (comptage, pas une prédiction) ; **597 blocs** diffèrent (9 215 instructions de l'ancien, 9 540 du nouveau ; 468 remplacements, 76 insertions, 53 suppressions). **Aucun de nos 40 sites n'est dans un bloc qui diffère** : le plus proche est à 0x56 octets (le site `0x701f52` du cercle, juste avant la fin de la grande fonction du circuit), les autres à plus de 0x240 octets, la plupart à plusieurs milliers. Autour des sites de l'ascenseur, du roulage et de la grue, le code est identique sur des milliers d'instructions de chaque côté, jusqu'à plus de 14 000 (`analyse/sites_localises.txt`, colonne « identique »).
4. **MESURÉ** — constantes cibles (la valeur doublée, ex. 5,0 pour le plafond de roulage) : on prend la première copie en lecture seule de la même valeur, comme le faisait le générateur d'origine, et on vérifie que c'est **le même bloc de données** que dans l'ancien exe (36 octets voisins identiques). Résultat : 13 constantes, toutes retrouvées (`analyse/modules_nouvel_exe_octets.md`, tableau final).
5. **MESURÉ** — chaque opérande modifié a bien une entrée de relocation dans le nouvel exe (le patch reste juste si Windows déplace le programme) ; les 3 immédiats (énergie, facteur de vitesse, centre du cercle) n'en ont pas.
6. Les 3 sauts du créneau d'atterrissage doivent aller au bloc « test de la piste » : retrouvé par son contexte à `0x701b3a` (ancien `0x701a2a`), c'est bien `cmp dword ptr [edi], 1`, et la sortie commune d'origine est `0x701c14` (ancien `0x701b04`).

### 1.4 `patch_exe.py` : deux profils, aucun refus affaibli

Fichiers : `tour/outils/patch_exe.py` (modifié), `tour/outils/modules_exe_461E1262/*.json` (6 nouveaux modules, tout est en octets lisibles), `tour/outils/test_patch_exe.py` (2 assertions adaptées, voir plus bas), `tour/outils/test_patch_exe_nouveau.py` (nouveau).

- **Deux profils**, choisis par l'horodatage de compilation de l'en-tête PE du fichier donné : ancien build 1.5.18 (`0x6a36c177`, original `1C9A01C3…`) et build de Steam du 28/10 (`0x6ae228f3`, original `461E1262…`). Les **sommes d'origine sont épinglées dans l'outil** (avant, elles n'étaient lues que dans les JSON). Tout autre horodatage, un PE illisible, un octet modifié hors des modules, un site abîmé, un mélange de nos modules d'un autre profil : **refus**, rien d'écrit.
- **Plus strict qu'avant sur un point** : sur le build de Steam, l'outil **n'écrit jamais dans un chemin contenant `steamapps`, même avec `--cest-le-vrai-jeu`** (Steam réécrit ce fichier ; le moddeur ne veut pas qu'on le patche). On patche une copie ailleurs. `etat` (lecture seule) reste permis.
- Un exe qui porte l'horodatage d'un profil mais les octets de l'autre (ancien déguisé en nouveau, ou l'inverse) : INCONNU, refus, même avec `--sauvegarde` et `--restaurer-tout-l-exe`.
- `activer` exige toujours la copie de sauvegarde au sha256 de l'original **du bon profil** (la sauvegarde de l'autre build est refusée).

### 1.5 Autotests (tous passent)

Sorties complètes, relancées avec les outils finaux : `analyse/autotests_ancien_exe.txt` et `analyse/autotests_nouvel_exe.txt`.

- **Ancien exe** : `test_patch_exe.py` → **182 vérifications, 0 échec**. Seules 2 assertions ont dû changer : « le sha du build Steam est dans la liste des builds refusés » et « un exe dont la somme est dans la liste est refusé ». Elles décrivaient l'ancien état (le build Steam était « étranger ») ; elles sont remplacées par « le build Steam a son profil, épinglé, sans écriture sous `steamapps` » et par le même test de liste noire avec le nouveau message. Les 180 autres sont intactes.
- **Nouvel exe** : `test_patch_exe_nouveau.py` → **207 vérifications, 0 échec** : cycle complet de chacun des 6 modules (état, à blanc, activer, déjà actif, retirer = `461E1262…` exact) ; relecture au désassembleur des 41 champs avec les valeurs voulues écrites à la main dans le test ; **les 63 combinaisons** de modules (en mémoire) + 8 combinaisons par la ligne de commande, retrait dans les deux ordres ; octets abîmés, mélange, mauvaises sauvegardes (dont celle de l'AUTRE build), chemin `steamapps`, options inconnues ; ancien exe déguisé / nouvel exe déguisé / horodatage inconnu / pas un PE ; lecture seule du dossier du jeu (le vrai exe est reconnu, `carrier_command_vr.exe` et `dedicated_server.exe` sont refusés, le vrai exe est refusé à l'écriture, sa somme est relue inchangée).

### 1.6 Preuve « mêmes instructions qu'à l'ancien exe patché »

`analyse/preuve_memes_instructions.txt` (script `outils/prouver_equivalence.py`) : on construit en mémoire « ancien original + 6 modules » et « nouvel original + 6 modules », et pour **chacun des 41 champs** on compare l'instruction des deux fichiers patchés : même mnémonique, mêmes registres, même taille, **même valeur finale lue** (celle voulue, écrite à la main : 5,0 ; 0,1 ; 1/3 ; −1/15 ; 15,0 ; 100,0 ; −1800,0…), constante en lecture seule, relocation présente ; pour les 3 sauts du créneau, même cible `cmp dword ptr [edi], 1` suivie des mêmes instructions. **41 sur 41 concordent.** Autres contrôles du même script : seuls les champs listés diffèrent de l'original (89 octets dans l'ancien patché, 96 dans le nouveau), la table de relocation est identique avant/après patch, et les frontières des 2,57 millions d'instructions du code sont inchangées par le patch.

### 1.7 Ce qui est prouvé sur les octets, ce qui reste à voir en jeu

- **Prouvé sur les octets** : sites retrouvés, valeurs finales lues, retrait exact, refus de tout autre fichier.
- **À voir en jeu (INFÉRÉ, rien d'essayé)** : que le nouvel exe patché démarre et se comporte comme l'ancien patché (ascenseur/grue/roulage ×2, temps ×2) ; que Windows accepte l'exe modifié (aucune signature n'est vérifiée d'après la table des imports identique, MESURÉ par l'étude du 29/10, mais jamais essayé) ; le comportement en multijoueur du nouvel exe (inconnu).
- **Limite honnête** : 597 blocs de code diffèrent ailleurs dans l'exe entre les deux builds. Je ne sais pas ce qu'ils changent (je ne les ai pas lus un par un). Ils sont hors de nos sites, mais ils peuvent contenir de vrais changements de comportement du jeu.

### 1.8 « Ascenseur ×2, piste ×2, tout comme avant » : que veut dire « piste ×2 » ?

Précision reçue de la conversation de coordination : le moddeur veut retrouver « ascenseur ×2, piste ×2, tout comme avant ». La lecture retenue par la coordination (**INFÉRÉ**) est « piste ×2 » = `pont_retour_x2`. Ce que j'ai pu **mesurer** à l'appui : l'ancien original + `ascenseur_x2` + `temps_x2` + `pont_retour_x2` donne exactement `0C5DFE52…`, c'est-à-dire l'exe qui était dans le jeu le 28/10 à 10:25. Donc « comme avant » = ces trois modules, et **la copie à trois modules est prête**.

Je n'ai pas de preuve que le moddeur appelle « piste » ce module. Autres lectures plausibles, que je ne tranche pas :
- **`pont_retour_x2`** : les avions et hélicos qui reviennent roulent deux fois plus vite sur le pont après le toucher (de la piste vers l'ascenseur). C'est la lecture retenue.
- **le roulage de départ**, déjà dans `ascenseur_x2` : sa description est « ascenseur, grue et roulage sur le pont ×2 » (7 blocs d'accélération et de plafond de roulage). Si le moddeur parle du roulage vers le bout de piste au décollage, il l'a déjà avec le module 1 (et l'avertissement de `pont_retour_x2` note que le départ « peut aussi » aller plus vite avec lui, déduit, non vu).
- **`atterrissage_creneau`** : « créneau de piste élargi » (la piste peut être donnée à l'avion pendant tout le virage arrière). Porte le mot « piste » mais pas de « ×2 ».
- **`atterrissage_cercle`** : le circuit d'attente devient un cercle (pas un « ×2 » non plus).

Les modules 4 à 6 sont portés quand même ; l'ordre des copies est une affaire d'accord du moddeur, pas de portage. Question à lui poser, **une seule** : « Par "piste ×2", tu veux dire que les avions qui reviennent roulent plus vite sur le pont après l'atterrissage (`pont_retour_x2`) ? »

---

## PARTIE 2 — Profil du SDK pour le nouvel exe (terminée, état au 30/10)

### 2.1 L'essentiel

- **MESURÉ** : le SDK **compilé par nous** n'est **pas** celui de `passation_windows/sdk_public_cc2x/src/`. Ce dossier est la copie **0.4.0** du 25/10 (`cc2x.c` sha256 `52B40540…`, 1 078 lignes, `Profile` avec `off_vehicles` et `off_tiles`). La DLL du jeu (`dinput8.dll` `184B144D…`) a été compilée par `construire.py` depuis le clone `cc2-sdk-tiers\Carrier-Command-2-extender` au commit `7ab05c7` = **CC2X 0.5.0** (`cc2x.c` sha256 `4C93AE43…`, 911 lignes, **sans** `off_vehicles` / `off_tiles` : les instantanés sont passés dans `lua_world.c`). Les empreintes des 6 fichiers compilés sont épinglées dans `tour/atterrissage_manuel/SDK_empreintes_7ab05c7.txt` et ont été vérifiées. J'ai travaillé sur **la version 0.5.0 (celle qu'on compile et qui est dans le jeu)**. `world.c` est identique dans les deux.
- **MESURÉ** : les **7 valeurs du `Profile`** + les **6 signatures Lua** + le **site Lua** sont retrouvés dans le nouvel exe, contrôlés par désassemblage **et** par les octets du source. Taille d'image lue dans l'en-tête du nouvel exe : `0x00af7000` (identique à l'ancien ; **c'est l'horodatage `0x6ae228f3` qui distingue les deux**).
- **MESURÉ** : `world.c` a **sa propre table d'adresses du jeu** (`LAYOUTS`, 17 adresses : fonctions et sites de crochets de l'API du monde), choisie par la même chaîne de build. Sans elle, l'API du monde resterait vide sur le nouvel exe. **Je l'ai portée aussi** (pas demandé dans l'énoncé, nécessaire pour un SDK cohérent).
- **MESURÉ** : une **copie du SDK avec les deux profils compile** (Zig 0.15.2, mêmes options que `construire.py` / `build.py`) : `C:\Users\UTILISATEUR\Documents\cc2-port-travail\sdk\dist\dinput8.dll`, 268 288 octets, sha256 `E1DE25D53A5588BDA62269D6D93335ACB9F32EA555AC9274FE7973C19D6225D7` (cette somme change à chaque compilation à cause de l'horodatage et de l'identifiant de build ; la 2e compilation est identique hors ces deux champs, MESURÉ). **Aucune DLL n'est posée, chargée ni lancée.**
- **Le profil ancien est intact** : relu dans la DLL compilée, ses champs et les 17 adresses de son layout sont identiques à la source d'origine.

### 2.2 Les valeurs (ancien → nouveau)

Détail complet et octets contrôlés : `analyse/profil_sdk_valeurs.txt` (et `.json`). Méthode : recherche par contexte + alignement du code entier (voir 1.3), puis, pour chaque fonction, nombre d'instructions du corps identiques à l'ancien exe.

| Champ du `Profile` | Ancien | Nouveau | Contrôle |
|---|---|---|---|
| horodatage PE / taille d'image | `0x6a36c177` / `0x00af7000` | `0x6ae228f3` / `0x00af7000` | lus dans l'en-tête (MESURÉ) |
| `server_vtable` (3 pointeurs init, tick, end) | `0x00d34bc4` | **`0x00d34bfc`** | seul triplet (init, tick, end) du `.rdata`, 3 relocations ; le pointeur juste avant (type) existe aussi (`0xdc3194`) |
| `server_init` | `0x00772fd0` | **`0x007730c0`** | corps identique sur 1 974 instr. (1er `ret` à la 477e) ; seul l'opérande `push offset` du gestionnaire d'erreurs diffère (adresse relocalisée) |
| `server_tick` | `0x0077ee10` | **`0x0077ef00`** | identique sur 3 991 instr. (1er `ret` à la 43e) |
| `server_end` | `0x0077eea0` | **`0x0077ef90`** | identique sur 3 939 instr. (1er `ret` à la 148e) |
| `lua_site` + 8 octets | `0x004465ec` `6a 20 89 85 64 ff ff ff` | **`0x004465ec`** (même adresse) | 8 octets = `lua_site_bytes` du source ; code non décalé à cet endroit |
| `f_index2addr` | `0x008cda70` | **`0x008cdbc0`** | `LUA_SIGS[0]` OK ; identique sur 475 instr. |
| `f_auxsetstr` | `0x008ce200` | **`0x008ce350`** | `LUA_SIGS[1]` OK ; 806 instr. |
| `f_finishset` | `0x008ff6b0` | **`0x008ff820`** | `LUA_SIGS[2]` OK ; 952 instr. |
| `f_luaS_new` | `0x00908220` | **`0x009083a0`** | `LUA_SIGS[3]` OK ; 642 instr. |
| `f_luaH_new` | `0x00904a50` | **`0x00904bc0`** | `LUA_SIGS[4]` OK ; 451 instr. |
| `f_luaC_step` | `0x00904050` | **`0x009041c0`** | `LUA_SIGS[5]` OK ; 284 instr. **Cas à part** : l'entrée suit une table de sauts rangée dans le `.text`, l'alignement ne la voit pas ; retrouvée par ses 8 octets (une seule occurrence à ±0x400 de la suite égale voisine, décalage `+0x170`) puis corps comparé instruction par instruction |
| `nilobject` | `0x00d03518` | **`0x00d03530`** (+0x18) | les **178** références du code ancien donnent toutes `0xd03530` dans le nouvel exe, 16 octets identiques |

**Si on utilisait la copie 0.4.0** (`passation_windows/sdk_public_cc2x`), son `Profile` aurait en plus `off_vehicles` = `0x37c` et `off_tiles` = `0x440` : ce sont des décalages de champs du serveur, **inchangés** (47 et 37 accès dans l'ancien exe, tous dans du code identique, mêmes nombres dans le nouvel exe, voir 3.5).

`world.c` (`LAYOUTS`) : 6 fonctions du jeu, 8 sites de crochets, 2 fonctions d'événements, `vt_rigid_dynamic` (`0xcdd478`, **inchangé**, 2 références) : tous retrouvés, tous au décalage `+0x110` dans le code, octets attendus (`h_waypoints_bytes`, `h_hangar_bytes`, `h_controller_bytes`) identiques dans le nouvel exe. Les décalages d'objets (`dock_state` `0x174`, `v_flight_state` `0x170`, etc.) sont **recopiés tels quels** (INFÉRÉ inchangés ; contrôle sur les accès du code en partie 3).

### 2.3 Compilation : même chaîne que les nôtres (sommes de contrôle épinglées)

- **MESURÉ** : j'ai d'abord recompilé les sources **inchangées** (commit `7ab05c7`, 6 fichiers aux empreintes épinglées) dans mon dossier : le résultat est **identique à `dinput8.dll` du jeu (`184B144D…`) hors horodatage PE et identifiant de build**. C'est donc la même chaîne (Zig 0.15.2 déjà installé par `pip` chez le moddeur ; aucune installation ni téléchargement de ma part).
- **MESURÉ** : avec le 2e profil : compile, 2e compilation identique (hors horodatage/identifiant), PE32 i386, TLS = celui d'une DLL vide (code du compilateur), mêmes 5 exports, **mêmes imports que la DLL du jeu** (KERNEL32 + api-ms-win-crt, aucune DLL réseau, aucune chaîne suspecte). Rapport : `sdk/RAPPORT_compilation_sdk.md`.
- La modification du source = **52 lignes de diff** (`sdk/profil_nouvel_exe.diff`) : un enregistrement ajouté dans `PROFILES[]` (cc2x.c) et un dans `LAYOUTS[]` (world.c) ; **aucune ligne de code modifiée**. La copie modifiée complète est dans `C:\Users\UTILISATEUR\Documents\cc2-port-travail\sdk\sources_nouveau\` (hors dépôt). Le dossier posé dans le jeu et le clone du SDK n'ont pas été touchés (clone relu : propre, au commit `7ab05c7`).
- **Le nom de build du 2e profil est volontairement différent** : `1.5.18-win32-6ae228f3`. `cc2x_frein.c:599` (`strcmp(game_build, "1.5.18-win32")`) et l'ancien plugin `extension_windows` (`cp_build_gate`) refusent tout autre nom : **ils refuseront de se charger sur le nouvel exe tant qu'on ne les porte pas** (c'est voulu). L'inconvénient : il faut les modifier pour qu'ils acceptent le nouveau nom (liste en fin de rapport). **Exception importante : `cc2x_modes` ne regarde pas le nom de build** (il lit l'horodatage PE et 8 octets de code) et connaît déjà le nouvel exe : voir 3.1.

### 2.4 Vérification dans la DLL compilée (sans la charger)

`sdk/verification_profils_dans_la_dll.txt` (script `outils/verifier_profil_dll.py`) : on relit les enregistrements **dans la DLL** et on rejoue, sur les octets des exe, ce que `startup()` fait au chargement (détection par horodatage + taille d'image, 6 signatures Lua, 8 octets du site Lua, 3 cellules de la table du serveur, octets attendus des crochets du monde) :

- l'**ancien exe** (original `1C9A01C3…` et `8E7FCBB6…`) n'accepte **que** le profil ancien ;
- le **nouvel exe** (original et copie patchée) n'accepte **que** le nouveau profil ;
- `carrier_command_vr.exe` et `dedicated_server.exe` (autres horodatages et autres tailles) : **aucun** profil, le SDK resterait inactif ;
- les valeurs lues dans la DLL = celles trouvées dans le nouvel exe (champs du profil, 6 fonctions Lua, 17 adresses du layout).

### 2.5 Ce qui est prouvé, ce qui reste à voir en jeu

- **Prouvé sur les octets** : valeurs, signatures, chaîne de compilation, profil ancien intact, refus des autres exe.
- **À voir en jeu (INFÉRÉ)** : que le SDK s'installe sur le nouvel exe sans erreur (les 3 écritures de pointeurs + le crochet Lua), que la table Lua `cc2x` apparaît, que les événements du monde se déclenchent. Ce que le SDK suppose des structures du jeu (`lua_State` +0xc/+0x10/+0x14, registre +0x28 de l'état global…) vient de fonctions Lua dont le corps est identique (475 à 952 instructions), donc INFÉRÉ inchangé ; jamais exécuté.
- **Rien posé.** La pose de `dinput8.dll` (qui remplacerait celle de `184B144D…`) viendra avec un « oui » séparé du moddeur et une relecture du diff de 52 lignes par une autre conversation (🟡 : une DLL de plus dans le jeu ; 🟢 pour le code ajouté, qui n'est que deux tables de nombres).
- Les corrections de DYOR / Sample_Fox (RAPPORTÉ) n'ont pas été téléchargées ni lues.

---

## PARTIE 3 — Inventaire des plugins (lecture seule, terminée, état au 30/10)

Rien n'a été modifié dans les plugins. La v11 a été lue **sans y toucher** (simple lecture des fichiers du worktree `musing-nobel-a0872c` ; je n'y ai écrit ni commité ; je me suis limité à comparer `cc2x_frein.c` de la v11 à celui de la v10 avec `diff`). Outils : `outils/inventaire_plugins.py`, `outils/acces_champs.py` ; sorties : `analyse/inventaire_plugins.txt` (+ `.json`), `analyse/acces_champs.txt`.

### 3.1 L'essentiel

- **Chemins** (Glob) : `tour/atterrissage_manuel/frein/cc2x_frein.c` (v10, commité) ; `tour/etudes_modes_carburant/plugin/v3_1/cc2x_modes.c` (v3.1, la plus récente) et `…/plugin/cc2x_modes.c` (v3, même table de builds) ; v11 : `…\worktrees\[dossier-de-travail]\tour\atterrissage_manuel\frein\cc2x_frein.c` (non commité).
- **MESURÉ** : les **11 sites** (7 crochets + 1 cible de saut pour la v10 ; H4 + sa cible pour la v11 ; 1 adresse lue pour modes) sont tous classés **SÛR** par une règle fixe écrite dans l'outil : les deux méthodes indépendantes (alignement du code entier / recherche par contexte) donnent la même adresse, les octets attendus par le plugin sont identiques, les instructions déplacées par le crochet tombent sur les mêmes frontières, **aucun saut du jeu ne vise l'intérieur des octets déplacés** (dans l'ancien comme dans le nouvel exe), au moins 30 instructions identiques de chaque côté (en fait au moins 261 pour le site le plus proche d'une différence). Aucun « incertain », aucun « introuvable ».
- **MESURÉ** : le décalage est **+0x110** pour tous les crochets du frein et **+0x100** pour le site de modes (le décalage change le long de l'exe : on ne peut pas le supposer constant).
- **MESURÉ** : la grande fonction de piste (ancien `0x6fc730..0x701fa8`, 4 846 instructions, où sont **tous** les crochets du frein) est **entièrement identique** à la nouvelle (`0x6fc840`), aux adresses absolues et déplacements relatifs près. Donc toutes les cases de pile `[ebp-0x1fc]`, `[ebp-0x205]`, etc. que lisent les crochets sont les mêmes (voir 3.5).
- **TROUVAILLE à signaler** : `cc2x_modes.c` (v3 **et** v3.1) **connaît déjà le nouvel exe** : sa table `BUILDS` contient `{0x6ae228f3, 0x71dcbf}` (« code décalé de +0x100 »). Je l'ai vérifié : `0x71dbbf → 0x71dcbf`, 8 octets `movss [edi+0x314], xmm0`, 3 477 instructions identiques avant et 7 254 après. **Et la DLL déjà posée** dans le mod (`%APPDATA%\Carrier Command 2\mods\cc2_modes\content\cc2x\cc2x_modes.dll`, sha256 `4B2EBC04…`, 30/10 08:21, relue en lecture seule) **contient les deux horodatages et les deux adresses**. D'après sa source (v3/v3.1) elle ne regarde ni le nom de build du SDK ni autre chose que l'horodatage PE et ces 8 octets, et sa DLL ne contient en effet ni la chaîne `1.5.18` ni le mot `game_build` (MESURÉ, recherche d'octets) : **elle se chargerait donc sur le nouvel exe dès que le SDK y sera actif** (mode « observation » tant que `modes.ini` n'a pas `enabled=1`). Ce que dit l'ETUDE du 29/10 (« modes refuse le nouvel exe, l'instruction est en `0x71dbc2` ») venait d'une **autre occurrence** des mêmes 8 octets (5 occurrences dans chaque exe : `0x71dac2, 0x71db5b, 0x71dbbf, 0x71e1c0, 0x71e248` dans l'ancien ; `0x71dbc2, 0x71dc5b, 0x71dcbf, 0x71e2c0, 0x71e348` dans le nouveau ; la bonne est la 3e).

### 3.2 `cc2x_frein.c` v10 (commité) : chaque crochet et chaque adresse fixe

Le plugin n'installe ses crochets **que si `recall_force=1`** au démarrage (`install_hooks`) ; sinon il ne patche rien du jeu (il ne fait que lire/écrire via l'API du SDK). Il ne lit **aucune autre adresse fixe** (aucune donnée à adresse fixe ; seules les 7 adresses de crochets et `SITE_H2_GOTO`, passée à `A->va()`). Contrôle de build : `strcmp(a->game_build, "1.5.18-win32")` (ligne 599) → **refus** sur le nouveau nom de build (`1.5.18-win32-6ae228f3`), voulu.

| Crochet / adresse | Ancien | Nouveau | Octets attendus (identiques) | Rôle | Verdict |
|---|---|---|---|---|---|
| H1 | `0x7018ce` (6 o) | **`0x7019de`** | `8b 40 04 83 f8 05` | élément de file (montre l'état 1) | **SÛR** |
| H2 | `0x701a3d` (6 o) | **`0x701b4d`** | `8d 85 28 fd ff ff` | saute le test des 1000 m | **SÛR** |
| H3 | `0x6ff0fb` (6 o) | **`0x6ff20b`** | `8b 8d 04 fe ff ff` | lecture seule, chemin « approche abandonnée » | **SÛR** |
| sonde A/B | `0x6febda` (8 o) | **`0x6fecea`** | `f3 0f 10 8d a4 fd ff ff` | lecture seule | **SÛR** |
| sonde C/D | `0x6febe7` (8 o) | **`0x6fecf7`** | idem | lecture seule | **SÛR** |
| sonde E | `0x6febc0` (8 o) | **`0x6fecd0`** | idem | lecture seule | **SÛR** |
| sonde C passée | `0x6fe788` (6 o) | **`0x6fe898`** | `8b 8d b4 fd ff ff` | lecture seule | **SÛR** |
| cible de saut de H2 (`SITE_H2_GOTO`, adresse lue) | `0x701a8a` | **`0x701b9a`** | (instruction après le test des 1000 m) | `cpu->jump_to = A->va(...)` | **SÛR** |

Les trois sondes « A/B », « C/D » et « E » sont elles-mêmes des cibles de sauts du jeu (`0x6fe669 / 0x6fe6b6 → sonde A/B` etc.) : dans le nouvel exe ces sauts (`0x6fe779 / 0x6fe7c6`) visent bien `0x6fecea`, comme prévu. **Ce que les crochets supposent d'autre** (cases de pile, champs du gestionnaire de piste) : voir 3.5.

### 3.3 `cc2x_frein.c` v11 (NON commité) : ses crochets, à part

La v11 = la v10 + **un crochet de plus (H4)**, rien d'autre de neuf côté adresses (lu par `diff` v10/v11). Les 7 crochets et la cible de la v10 sont inchangés dans la v11 (mêmes adresses anciennes, donc mêmes équivalents ci-dessus).

| Crochet / adresse | Ancien | Nouveau | Octets attendus | Verdict |
|---|---|---|---|---|
| **H4** (le magasin `mov byte [ebp-0x205],1`, 7 octets) | **`0x6fe470`** | **`0x6fe580`** | `c6 85 fb fd ff ff 01` | **SÛR** (12 324 instr. identiques avant, 3 206 après ; aucun saut du jeu ne vise l'intérieur des 7 octets, ancien comme nouveau) |
| cible de saut de H4 (`SITE_H4_GOTO`, adresse lue : l'évaluation du commit, portes A-E) | **`0x6fe55b`** | **`0x6fe66b`** | — | **SÛR** (12 367 avant, 3 163 après) |

Autres choses supposées par H4 (toutes vérifiées dans la grande fonction identique) : `[ebp-0x205]` (octet de zone finale), `[ebp-0x204]` (gestionnaire), `[ebp-0x25c]` (distance), `[ebp-0x1fc]` (avion), gestionnaire `+0x1c` (état de piste), `+0xd4` (compteur). Build : même `strcmp` que la v10.

### 3.4 `cc2x_modes.c` v3.1 (et v3)

- **Aucun crochet `patch_mid` / `patch_call` / `patch_ptr`.** Le plugin n'écrit jamais dans le code du jeu.
- **Une adresse fixe lue** : le site du gaz (`memcmp` de 8 octets, porte de sécurité) : `0x71dbbf` → **`0x71dcbf`** (+0x100), **SÛR**, déjà dans sa table.
- **Un décalage d'objet écrit** : `THR_OFFSET 0x314` (le gaz, un float dans l'objet avion, écrit directement chaque tick si `enabled=1`). Voir 3.5 : 77 accès dans l'ancien exe, 77 dans le nouveau, tous dans du code identique.
- Il dépend de l'API du SDK pour `geti/getf/ref/body_get`, `lua_add` : tous passent par le `Layout` de `world.c` (déjà porté en partie 2) et le pont Lua (profil, partie 2).

### 3.5 Décalages de champs d'objets : contrôlés sur les accès du code

Méthode (`outils/acces_champs.py`, `analyse/acces_champs.txt`) : si un champ avait bougé, tous les accès à ce champ auraient un autre déplacement et seraient dans des blocs de code qui diffèrent. On compte, pour chaque décalage de la table `Layout` de `world.c` (et ceux des plugins), les instructions qui ont un accès mémoire avec ce déplacement, dans l'ancien exe, combien sont dans du code identique au nouvel exe, et combien d'accès dans le nouvel exe.

- **MESURÉ** : `dock_state` `0x174` : **311 accès dans l'ancien exe, tous les 311 dans du code identique, 311 dans le nouvel exe**. `v_flight_state` `0x170` : 342 / 342 / 342. Même résultat (nombre égal et tous dans du code identique) pour **tous** les champs propres aux véhicules : `v_id` 0x80 (1 906), `v_definition` 0x84, `v_bodies`, `v_wheels`, `v_team`, `v_attached`, `v_dock_*`, `v_fuel` 0x120, `v_waypoints`, `v_sync_*`, `v_hp`, `v_control_mode/target/speed/power/taxi` (`0x1d0..0x200`), pour ceux du serveur (`s_vehicle_map 0x344`, `s_vehicles 0x37c`, `s_tile_map`, `s_tiles 0x440`, `s_broadcast`), pour ceux des îles/aérodromes (`i_airfields 0x154`, `a_*`), `t_island`, `t_saved_*`, `env_nodes`, `attachment_flying`, `body_actor`, et pour le gaz `0x308..0x314` (119, 91, 92, 77). Pour les décalages « génériques » (`0x48`, `0x40`, `0x20`…, utilisés par des milliers d'instructions de toutes sortes) les nombres sont presque égaux (écarts de quelques unités, qui tombent dans les 597 blocs qui diffèrent).
- **MESURÉ** : les cases de pile et les champs du gestionnaire que lisent les crochets du frein sont compris dans la fonction identique : `[ebp-0x1fc]` (62 accès), `[ebp-0x204]` (41), `[ebp-0x205]` (8), `[ebp-0x224]`, `[ebp-0x278]`, `[ebp-0x2cc]`, `[ebp-0x270]`, `[ebp-0x25c]`, les trois vecteurs, `[ebp-0x24c]`, `[ebp-0x2d8]` : mêmes nombres dans les deux exe, tous dans du code identique ; gestionnaire `+0x1c` (8 574 accès), `+0x5c`, `+0xd4`.
- **INFÉRÉ** (et fortement appuyé) : les décalages d'objets n'ont pas bougé. Ce que cette mesure ne prouve pas : qu'aucun champ n'a changé de **sens** à un décalage donné (il faudrait le voir en jeu) ; ni les décalages inférieurs à 10 (`0x0`, `0x4`, `0x8` : capstone les écrit sans `0x`, mon comptage ne les voit pas : `t_id`, `a_env`, `a_xform`, `wp_type`).

### 3.6 Autres adresses d'un autre chantier (pour mémoire, non demandées)

Étude du bouton Hold (`/side-session-notes/…/bouton_hold_resultat_30-10.md`, **LU**) : recherche par nom `0x63F360 → 0x63f460`, lecture `0x63F570 → 0x63f670`, appels `0x6FCD74 → 0x6fce84` et `0x6FD942 → 0x6fda52`, **crochets prévus** après les deux appels `0x6FCD79 → 0x6fce89` et `0x6FD947 → 0x6fda57` (octets `84 c0 74 …` identiques), fonction du circuit `0x6FC730 → 0x6fc840` : tous dans du code identique (marges de 1 949 à 4 845 instructions). Aucun plugin n'existe encore pour cela.

### 3.7 Ce qui est prouvé, ce qui reste à voir en jeu

- **Prouvé sur les octets** : les adresses et les octets de chaque crochet, l'absence de saut vers l'intérieur des octets déplacés, l'identité de la fonction qui contient les crochets du frein, l'identité des accès aux champs.
- **À voir en jeu (INFÉRÉ, rien d'essayé)** : que les crochets, une fois reportés, se comportent comme sur l'ancien exe (leur logique repose sur des registres et des cases de pile, qui sont les mêmes) ; que `cc2x_modes.dll` se charge et observe correctement sur le nouvel exe ; que les noms de champs du SDK donnent les mêmes valeurs.

---

## Fichiers produits

**Premier essai en jeu (préparé, non fait)** : `premier_essai/lancer_nouveau.py` (copie / lancement direct / retrait de la copie patchée à trois modules, mêmes garde-fous que `lancer_ancien.py`), `premier_essai/tester_lancer_nouveau.py` (45 contrôles sur faux dossiers, 0 échec, aucun jeu lancé), `premier_essai/PROCEDURE_premier_essai_nouvel_exe.md` (ce que le moddeur accepte, avec les niveaux 🟢/🟡/🔴, ce qu'il fait, ce qu'on lit, comment arrêter et revenir en arrière).

Dans le dépôt (`tour/etude_port_nouvel_exe/`, non commités) : `RAPPORT.md` ; `analyse/` (`sites_localises.txt/.json`, `croisement_alignement_sites.txt`, `modules_nouvel_exe_octets.md`, `preuve_memes_instructions.txt`, `diff_code_ancien_nouveau.txt`, `profil_sdk_valeurs.txt/.json`, `inventaire_plugins.txt/.json`, `acces_champs.txt`) ; `sdk/` (`profil_nouvel_exe.diff`, `RAPPORT_compilation_sdk.md`, `verification_profils_dans_la_dll.txt`) ; `outils/` (11 scripts). Dans `tour/outils/` : `patch_exe.py` (modifié), `modules_exe_461E1262/` (6 JSON), `test_patch_exe.py` (2 assertions adaptées), `test_patch_exe_nouveau.py` (nouveau).

Hors dépôt, dans `C:\Users\UTILISATEUR\Documents\cc2-port-travail\` : copies de travail des deux exe (`…ancien_original_1C9A01C3.exe`, `…nouveau_steam_461E1262.exe`), **les copies patchées** `carrier_command_nouveau_patche_ascenseur_temps_pont.exe` (`5AF41B4D…`, « comme avant ») et `carrier_command_nouveau_patche_ascenseur_temps.exe` (`6072A2FD…`), et `sdk\` (sources copiées et modifiées, DLL compilées, caches du compilateur : 70 Mo, supprimable). Retrait : supprimer ce dossier ; sans effet sur le jeu.

---

## CE QUE LA PARTIE SUIVANTE (PORTER LE CODE DES PLUGINS) AURA À FAIRE

Dans l'ordre, chaque pose et chaque lancement avec un « oui » séparé du moddeur.

1. **Relire le diff du SDK (52 lignes, `sdk/profil_nouvel_exe.diff`) dans une conversation différente**, comme on l'a fait pour le SDK d'origine (`tour/atterrissage_manuel/VERDICT_relecture_SDK.md`) ; décider si on pose la DLL telle quelle (`E1DE25D5…`) ou après une recompilation. La DLL à deux profils sert aussi à l'ancien exe (profil ancien intact, MESURÉ).
2. **`cc2x_frein.c` v10 (commité)** :
   - remplacer les `#define SITE_*` par une **table par build** (comme `BUILDS` de modes), choisie par l'horodatage PE ; valeurs du nouvel exe : H1 `0x7019de`, H2 `0x701b4d`, H3 `0x6ff20b`, sondes A/B `0x6fecea`, C/D `0x6fecf7`, E `0x6fecd0`, C passée `0x6fe898`, cible H2 `0x701b9a` (octets attendus : inchangés) ;
   - `cc2x_plugin_load` : accepter **les deux** noms de build (`1.5.18-win32`, `1.5.18-win32-6ae228f3`) **et** vérifier l'horodatage ; garder `api_version >= 3` ;
   - `hook_h2_body` (`A->va(SITE_H2_GOTO)`), `install_hooks` et les messages de journal (`SITE_H1`, `SITE_H2`, `SITE_H3` imprimés) doivent lire la table ;
   - mettre à jour `tests/test_frein.c` (build inconnu refusé, les deux builds acceptés, mauvais octets refusés) ; recompiler avec `construire.py` (sources épinglées + sommes) vers un dossier neuf, mêmes contrôles d'imports ;
   - mettre à jour les commentaires et `RISQUES_*.md` (build, adresses).
3. **`cc2x_frein.c` v11** : après son commit par la conversation `atterrissage-v11` (ne pas la modifier avant), faire pareil et ajouter dans la table **H4 `0x6fe580`** (octets `c6 85 fb fd ff ff 01`) et **la cible `0x6fe66b`**.
4. **`cc2x_modes.c` v3.1** : rien à reporter pour les adresses (déjà dans la table, vérifié). À faire : ajouter au test un cas « nouvel exe » avec les vraies adresses (le test a déjà les cas d'horodatage croisés), confirmer que la DLL posée dans le mod (`4B2EBC04…`) est bien la v3.1 compilée, et **décider** si on veut qu'elle se charge sur le nouvel exe dès que le SDK y sera actif (elle le fera toute seule : mode observation).
5. **Outils de pose et d'essai** à adapter au moment d'adopter le nouvel exe : `lancer_ancien.py` → un `lancer_nouveau.py` (copie `carrier_command_nouveau_patche_ascenseur_temps.exe` dans le dossier du jeu sous un autre nom, jamais l'exe de Steam ; retrait = supprimer la copie) ; `essai_auto.py` (garde sur `8E7FCBB6…`) ; `poser.py` (affiche « AUTRE VERSION : SDK inactif » pour le nouvel exe) ; `test_demarrage_auto.py` (horodatage et adresses de plantage en dur) ; `PROCEDURE_partie_*.md`.
6. **Journal de contrôle après le premier lancement** (avec « oui » du moddeur) : `cc2x.log` doit montrer `CC2X 0.5.0 ready for Carrier Command 2 1.5.18-win32-6ae228f3` et **aucune** ligne « unexpected original bytes » ni « core hooks failed » ; puis `plugin cc2x_modes.dll loaded` ; puis, seulement si `frein` est porté, `frein` chargé.
7. **À mesurer en jeu, dans cet ordre** : (a) le jeu démarre avec la copie patchée seule (sans SDK) ; (b) ascenseur/grue/roulage ×2 et temps ×2 se comportent comme sur l'ancien patché ; (c) avec le SDK : table Lua `cc2x`, événements ; (d) modes en observation ; (e) frein v10 puis v11. Multijoueur : **inconnu**, à tester à deux seulement après tout le reste.
8. **Ne pas oublier** : les 597 blocs de code qui diffèrent ailleurs dans l'exe ne sont pas lus ; le mod décoratif `cc2_hold_copies` remplace un fichier du jeu (à retirer avant une mise à jour Steam si on n'en fait rien) ; l'ancien plugin `extension_windows` (`cc2_patchs`) a sa propre porte de build (`CP_KNOWN_BUILD`) et n'est pas porté (non utilisé aujourd'hui).

---

# Étape 1 — Tableau Mac → Windows (carrier_command.exe 1.5.18, 32 bits)

Fait le 26/10/2026 sur la tour. **Lecture seule** : le script `tour/outils/etape1_empreintes.py` a lu la **copie de sauvegarde** de l'exécutable (sha256 `1C9A01C3007CB2BEC2A04D716812CF9F24C87EFA11056395C89DDD7D2C341026`). Résultat brut complet : `tour/etape1/resultats_etape1.md`.
Toutes les adresses sont des **adresses d'image, base `0x400000`** (celles de Ghidra / IDA). Les décodages (movss, mulss…) viennent de l'octet d'opération qui précède l'adresse de la constante : **c'est un indice fort, pas une relecture au désassembleur** (elle se fait à chaque étape de port, avant d'écrire).

## Verdict

**Les groupes existent dans le code Windows, avec les mêmes valeurs et dans le même ordre : la logique n'a pas changé depuis janvier. On peut porter.** Pas d'arrêt.
Deux écarts à connaître : (1) les vecteurs de 4 nombres de l'atterrissage n'existent pas sous cette forme (Windows lit les nombres un par un) ; (2) 6 paires de roulage trouvées sur 7 (la 7e est ailleurs ou arrangée autrement).

## Groupe par groupe

| Groupe (module Mac) | Ce que dit le Mac | Ce qu'on trouve sur Windows | Verdict |
|---|---|---|---|
| **Énergie** (`ascenseur_x2`, 1 immédiat) | 5 parts 0,8 / 0,2 / 0,8 / 0,6 / 0,4 écrites dans une même fonction ; la 4e (0,4, ascenseur/grue) devient 0,8 | Même fonction, mêmes 5 écritures dans cet ordre : `mov [esi+0x70], 0,8` en `0x006e9ef5` ; `mov [edi+8], 0,2` en `0x006e9f33` ; `mov [esi+0x50], 0,8` en `0x006e9f6f` ; `mov [edi+8], 0,6` en `0x006ea001` ; **`mov [edi+8], 0,4` en `0x006ea0a1`** (octets `c7 47 08 cd cc cc 3e`). À patcher : les 4 octets immédiats en `0x006ea0a1`, `cd cc cc 3e` → `cd cc 4c 3f` (0,8) | **Confirmé** (à relire au désassembleur à l'étape 3) |
| **Plateforme** (`ascenseur_x2`) | pas 0,025 et son négatif, tout près de la zone morte 0,001 | `0,025` lu par `movss` en `0x00705c14` ; `−0,025` lu directement par `maxss` en `0x00705c3e` ; `0,001` lu par `comiss` en `0x00705c53` : trois lectures à moins de 0x40 octets. La fonction qui les contient est voisine des chaînes `lift_constraint` (`0x00705543`, `0x00713038`) et `docking_manager_air` (`0x007049c3`) | **Confirmé**. Attention : 0,025 est lu 55 fois dans tout le jeu, seul ce groupe est la plateforme |
| **Roulage** 2,5 et 0,05 (`ascenseur_x2`) | 7 paires (accélération 0,05, plafond 2,5) | **6 paires** : `0x006f9811`/`0x006f9845`, `0x006fb2e9`/`0x006fb2ce`, `0x006fcbb2`/`0x006fcbaa`, `0x006fce56`/`0x006fce4e`, `0x006fd8f0`/`0x006fd8d5`, `0x006fddbd`/`0x006fddb5` (2,5 par `movss`, 0,05 par `addss`, sauf la dernière en `movss`). Elles sont entre `0x006f8ab5` (`docking_queue`) et `0x006fc1a3` (`lift_lower`) : c'est bien la grande fonction d'accostage du porte-avions (~18 Ko) | **Confirmé pour 6 sur 7** ; la 7e est à chercher à l'étape 3 |
| **Grue** (`ascenseur_x2`) | 1/6 et 1/30 (+ leurs négatifs), 11,0 et 12,0, rotation 0,04 | Bloc entre `0x00700f26` et `0x00701219` : `1/6` en `0x00700f26` et `0x00701035` ; `−1/6` en `0x00700f31` et `0x00701040` ; `1/30` en `0x00700f9a` et `0x007010a6` ; `−1/30` en `0x00700f82` et `0x00701083` ; `12,0` en `0x00701136` ; `11,0` en `0x0070117c` ; `0,04` en `0x00701219`. Les négatifs sont des constantes lues directement (pas un `xorps`) | **Confirmé** (moins de lectures que le Mac : le compilateur a regroupé) |
| **Vitesse de l'IA** (`vitesse_escadrille`) | 144 puis planchers 48 et 72, autour d'un test « type 10 » | `144` lu par `movss` en `0x0071a0cb` ; `48` par `maxss` en `0x0071a0d6` ; `72` par `maxss` en `0x0071a0ec`. La chaîne `vehicle_ai_wing_cruise_speed` n'est lue qu'en `0x00869401` (chargement des réglages) | **Confirmé** (même ordre que le Mac) |
| **Circuit d'atterrissage** (`atterrissage`, 10 retouches) | rayon 1200, centres de virage (−1000, −1800), (1000, 600), fin de ligne droite 600, vitesse 80 ; **vecteurs de 4 nombres** lus par `addps` | Région `0x007013e0`–`0x00701f52` : `1200` en `0x007013e0` et `0x0070147d` ; `−1800` en `0x007018e5` et `0x00701d2f` ; `600` en `0x007018fc`, `0x00701d5e`, `0x00701d69`, `0x00701f52` ; `1000` en `0x00701a7d` ; `−1000` en `0x007019f6` et `0x00701e5c`. **Aucun vecteur de 4 nombres** (`1000, −600, 0, 0` introuvable) : Windows lit les nombres un par un | **La logique est là, la forme est différente** : il faudra lire le code au désassembleur (étape 5). Pas d'`addps` ni d'alignement sur 16 octets à prévoir ici |
| **Hélicos** (2 modules, 5 retouches) | 50 → 100, 120 → 48, 20 → 70, 23,5, plancher −2,0 | Constantes trop courantes pour un repérage isolé (`50`, `100`, `120`, `20` : de 20 à 100 lectures). `70` existe en 2 copies, `23,5` n'existe nulle part (la valeur devra venir de notre propre table) | **À faire à l'étape 4**, en partant de la région du circuit (voisine) |
| **Roulage de retour** (`pont_retour_x2`) | 3 lectures de 30,0 aux états 5, 6, 7 | `30,0` : 3 copies en données, 72 lectures dans tout le jeu | **À faire à l'étape 5** (il faut le désassembleur pour choisir les 3) |

## Chaînes (existent dans tous les builds) : 13 sur 13 présentes

`lift_constraint` `0x00d22e90` · `load_lift_lower` `0x00d22598` · `runway_start` `0x00d70f60` · `runway_end` `0x00d70f70` · `lift_lower` `0x00d22550` · `lift_upper` `0x00d22564` · `hanger_center` `0x00d220a4` · `vehicle_ai_wing_cruise_speed` `0x00d2e8dc` · `docking_queue` `0x00d70e1c` · `runway_state` `0x00d70d1c` · `vehicle_id_crane` `0x00d223a8` · `crane_instructions` `0x00d2237c` · `docking_join_time` `0x00d22520`.
Utilisées surtout entre `0x006f59e9` et `0x00713038` : c'est la zone du porte-avions. (`c_vehicle_server_carrier` : absente de l'exécutable Windows ; c'est un nom de classe C++ qu'on ne connaissait que par les symboles du programme Mac, qui n'est pas « strippé ». Ce n'est pas un problème : les chaînes ci-dessus suffisent à repérer la zone.)

## Ce qui n'est PAS prouvé

- Rien n'a été désassemblé : les « movss / addss / maxss » sont lus à l'octet d'opération. Avant d'écrire un octet (étape 3), on relit chaque site avec un vrai désassembleur.
- « Même logique » veut dire : mêmes valeurs aux mêmes endroits relatifs. La preuve en jeu (sortie de 4 avions 3:50 d'origine, référence Windows) vient à l'étape 0 bis.

## Prochaine étape

Il faut un **désassembleur** pour relire chaque site avant d'écrire. Aucun n'est installé (ni Ghidra, ni objdump). Il faut l'accord du moddeur pour en installer un (liste dans le journal).

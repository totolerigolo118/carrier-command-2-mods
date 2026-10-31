# Diagnostic : le verrouillage « T » et la cible des missiles (27/10/2026)

Étude en **lecture seule** (rien n'a été modifié : ni le jeu, ni `carrier_command.exe`, ni `mods.xml`, ni les DLL).
Sources lues : `rom_0\scripts\vehicle_hud.lua`, `library_enum.lua`, `constants.txt`, `rom_0\game_objects\missile_*.xml`,
le mod Workshop `2937532682`, le mod Revolution `3460002110` (copie Workshop), et la **copie de sauvegarde** du
programme (`tour\sauvegardes\carrier_command_1.5.18_original.exe`, désassemblée avec `tour\outils\desasm.py`).

## 1. Résumé pour le moddeur (français simple)

> **MISE À JOUR (même jour, après le récit du moddeur : « je verrouille un bateau, le cadre rouge est bien dessus, mais le missile
> part sur l'unité la plus proche, près de l'île »).** Cela écarte H1 à H3 (le verrou est bien posé). La **section 11** donne la cause
> probable, lue dans le code du missile : le **détecteur du missile ne voit que 4 000 m** et prend **le premier ennemi qui entre dans son champ**.
> Ce n'est **pas** corrigeable par Lua ; c'est corrigeable par un **petit patch du programme** (🟡). Les sections 1 à 10 ci-dessous
> restent l'historique de l'enquête (leurs « verdict provisoire » sont dépassés).

- **Qui choisit la cible quand on appuie sur T ?** Un **script Lua du jeu** (`vehicle_hud.lua`, l'affichage de pilotage),
  pas le programme. T pose une « cible verrouillée » (cadre rouge). Ce choix est ensuite **relu par le programme** et
  envoyé à l'arme (côté « serveur » de la partie), qui s'en sert pour orienter le missile au départ.
- **Ce qui est certain** : T ne verrouille **que des ennemis « observés »** (repérés/marqués, par exemple par une caméra
  d'observation). Sur un ennemi non observé, T **ne fait rien** : il n'y a alors **aucun verrou**, et un missile tiré sans
  verrou part **tout droit devant l'avion** et se débrouille avec son propre détecteur. C'est **la première explication à
  vérifier** : elle correspondrait exactement à « le missile va vers le plus proche ».
- **Ce qui n'est pas encore prouvé** : comment le missile choisit sa cible **une fois en vol** (le code du missile en vol
  n'a pas été retrouvé dans le programme Windows, qui n'a pas de noms de fonctions). Si c'est le missile lui-même qui
  préfère la cible la plus proche, aucun script Lua ne peut le changer : il faudrait modifier le programme.
- **Verdict provisoire** : on ne peut pas encore dire « corrigeable par Lua » ou « seulement par le programme » sans une
  **observation en jeu** (section 6). Dans le meilleur cas (cause = pas d'observation, ou verrou effacé par le script),
  c'est Lua, sans risque pour le jeu (🟢). Dans le pire cas (le missile choisit seul), c'est un patch du programme
  (🔴, plusieurs séances, et le code à modifier n'est pas encore repéré).
- **Le mod « Gentle Missile Speed Buff »** ne touche **pas** le missile IR ni les roquettes : il change seulement
  l'anti-aérien, le laser, le TV et le missile de croisière (section 5).

## 2. De quels missiles parle-t-on ? (à confirmer avec le moddeur)

Le script active le verrou T pour : **missile IR**, **missile laser**, **missile anti-aérien**, **les 3 bombes**,
**les roquettes (nacelle)** et la **mitrailleuse d'avion** (`get_is_vision_target_lock_behaviour`, `vehicle_hud.lua:2783`).
« Parfois entière » dans la dictée = très probablement **« anti-aérienne »** (le missile AA est lui aussi à guidage
infrarouge : texte russe du jeu « ракета с ИК наведением против воздушных целей »). Les noms internes :
`attachment_hardpoint_missile_ir` (Missile 1, type interne 0x2c), `_laser` (Missile 2, 0x2d), `_aa` (Missile 4, 0x2f).
Le missile **TV** (Missile 3) n'est **pas** dans la liste du verrou T (il se pilote à la caméra).

## 3. La chaîne complète, de la touche T au missile

| Étape | Où | Preuve |
|---|---|---|
| 1. T = action « basculer la stabilisation » (`e_game_input.toggle_stabilisation_mode` = 24) | programme → Lua | `vehicle_hud.lua:2723, 2730` (l'indication « verrouiller cible » est liée à cette action) |
| 2. Le programme met à vrai `g_is_input_cycle_target_next/prev` quand on appuie | programme → Lua | ces deux variables ne sont **jamais écrites** dans les scripts (seulement `= false` aux lignes 7-8) ; leurs noms sont dans l'exécutable (0xd2b7ac, 0xd2b7cc), utilisés une seule fois chacun, en 0x82bf13 / 0x82c07a, dans le même motif que l'écriture de l'identifiant (0x82bd99 : fabriquer le nom, pousser la valeur, appeler la fonction de 0x8ce2c0). Lecture du code, pas essai en jeu |
| 3. Le script choisit la cible et la range dans `g_selected_target_id` / `g_selected_target_type` (type 1 = véhicule) | Lua | `toggle_vision_target` (`vehicle_hud.lua:2716`), appelé ligne 2659 ; `cycle_vision_targets` (2735) pour les autres armes |
| 4. Le programme **relit** ces deux variables à chaque image et les range dans l'état du joueur (+0x2e64 = identifiant, +0x2e60 = type) | programme | lecture d'une variable globale Lua par son nom (fonction 0x8ce0a0, puis conversion en entier 0x445f10 : motif de `lua_getglobal` + `lua_tointeger`, déduit du code, pas de symbole) aux adresses 0x82c2f6 (id) et 0x82c3c4 (type), rangement 0x82c491 / 0x82c4a3 |
| 5. Cet état est recopié dans une structure de sortie (lecture 0x75a91e / 0x75a939) | programme | **très probable** = message vers le serveur (chaîne « client → serveur » non suivie jusqu'à l'envoi réseau) |
| 6. L'arme côté serveur (même code pour IR, laser, AA : `c_attachment_server_hardpoint`, table de méthodes à 0xd28400 / 0xd25bbc / 0xcfaba0) range type et identifiant (+0x12c / +0x130), **seulement si son état interne (+0xc8) vaut 1** | serveur (hôte) | méthode 0x6b0aa0 |
| 7. À chaque pas de simulation, si une cible est verrouillée : l'arme retrouve le véhicule par son identifiant (0x5ee6a0), calcule la **direction vers lui**, la range comme `track_vector` (+0x110) avec `track_timer` = 1800 pas (60 s). **Sans verrou : direction = tout droit devant l'arme** | serveur | tick 0x6af8a0 → 0x6b0aa0, appels 0x6b0125 / 0x6b02c4 ; noms `track_vector`, `track_timer`, `payload_id` lus dans la sauvegarde d'état (0x6af7c0) |
| 8. Au tir, le missile est créé (0x5dfae0) avec ce vecteur (rangé dans le missile à +0x190…0x198) | serveur | 0x6b08db |
| 9. **En vol, le missile suit… ?** | **non trouvé** | voir section 4 |

Point important : dans le code de l'arme (étapes 6-8), **il n'y a aucune recherche de « cible la plus proche »**.
Le « plus proche » ne vient donc **ni du script de verrouillage ni de l'arme au départ** ; il vient soit de l'absence de
verrou (étapes 3 et 6), soit du missile en vol (étape 9).

## 4. Ce qui n'est PAS établi

1. **Le guidage du missile en vol** (étape 9). Pistes déjà écartées :
   - `missile_vision_range` (1000 m) n'est **pas** un détecteur du missile : il est lu **une seule fois** (0x6c4997), dans la
     boucle du véhicule, toutes les 30 pas : pour chaque missile d'une autre équipe à moins de 1000 m, le véhicule l'enregistre
     (probablement l'alerte « MSL INCOMING » ; déduit de la lecture du code). Il ne choisit aucune cible de missile.
   - `target_cooldown_time`, `missile_target_id`, `vehicle_target_id`, `retarget_timer` (noms vus dans le programme) sont les
     champs des **tourelles** automatiques (tourelle missile IR du porte-avions), pas des missiles d'avion.
   - Les réglages `constants.txt` `missile_1_steering` (IR) = 1,0, `missile_4_steering` (AA) = 1,0, `missile_2_steering` (laser) = 1,5 et
     les freinages `missile_angular_damping` 0,95 / `missile_linear_damping` 0,9 montrent que les missiles sont de vrais objets
     physiques dirigés par une « efficacité de virage », mais pas comment ils choisissent leur but.
   - Les deux fonctions qui lisent le tableau des virages (0x748af4, 0x74ba4c) ne sont **pas** la boucle de guidage (chargement/
     définition des missiles) : non approfondi.
2. **Ce que fait exactement l'état interne +0xc8** (la condition « =1 » de l'étape 6) : probablement « arme sélectionnée et armée ».
3. **Le comportement réel en jeu** : aucun essai n'a été fait (le jeu n'a ni été lancé ni touché).
4. La **version 1.5.17 (Mac)** est celle des noms de fonctions du Mac ; sur la tour (1.5.18) tout vient du désassemblage brut.

## 5. Le mod « Gentle Missile Speed Buff » (Workshop 2937532682, actif)

- Mod **uniquement en XML** (aucun script Lua, aucun programme). Il remplace 4 fichiers de `game_objects` :
  `missile_2.xml` (laser), `missile_4.xml` (anti-aérien), `missile_cruise.xml` (croisière), `missile_tv.xml` (TV).
- Dans le jeu d'origine ces 4 fichiers ont `<bodies/>` (**aucun corps physique** déclaré). Le mod y ajoute **un corps** (masse 1,
  une boîte de 0,33 × 3,3 × 0,33 pour le laser, 0,34 × 3,4 × 0,34 pour l'AA, 0,385 × 3,85 × 0,385 pour la croisière, 0,22 × 2,7 × 0,62
  pour le TV). C'est ainsi qu'il change les vitesses annoncées (croisière 78 → 102 m/s, AA 225 → 396, TV 85 → 150, laser 78 → 157).
- **Il ne touche ni `missile_1.xml` (IR), ni les roquettes.** Si le problème du moddeur concerne le **missile IR**, ce mod n'est pas en cause
  directement. Pour le **missile AA ou laser**, c'est possible : leur comportement physique est modifié (un AA à 396 m/s avec le même
  rayon de virage, `missile_4_steering` = 1,0, ne peut plus corriger sa route : il rate, puis…). **Non prouvé.**
- Test simple et sûr : désactiver ce mod le temps d'un essai (une ligne de `mods.xml`, avec accord et sauvegarde) et comparer.

## 6. Hypothèses, de la plus probable à la moins probable, et comment les départager

| # | Hypothèse | Correctable par | Comment la vérifier (sans rien modifier) |
|---|---|---|---|
| H1 | La cible n'est **pas « observée »** : T ne fait rien, pas de verrou, le missile part tout droit et son propre détecteur prend le plus proche. (`is_hoverable = is_observed` ; sans verrou le serveur vise devant l'arme) | **Rien à corriger** (c'est voulu) ; au plus un confort en Lua (🟢/🟡) | En jeu : viser un ennemi, appuyer sur T. **Cadre rouge + texte « verrouiller/libérer cible » = verrou posé ; rien = pas de verrou.** Refaire après avoir « observé » l'ennemi avec une caméra d'observation. |
| H2 | Le verrou est posé sur **une autre cible que celle voulue** : T prend l'ennemi observé **le plus près du centre de l'écran** (rayon de survol 1000 m, donc très large) ; un ennemi plus proche peut gagner | Lua (🟢) | Regarder **quelle cible est en rouge** avant de tirer. |
| H3 | Le script **efface le verrou** tout seul (`vehicle_hud.lua:2536`) dès que la cible sort de la liste (hors de portée 5 km / 10 km pour les navires, plus observée, filtre air/terre : le missile AA ne voit pas les cibles terrestres) | Lua (🟡 : il faut remplacer tout `vehicle_hud.lua`, 3 160 lignes) | Observer si le cadre rouge disparaît avant le tir. |
| H4 | Le verrou est bien envoyé, mais l'arme ne l'accepte pas (condition +0xc8 = 1) ou le serveur ne trouve pas la cible | programme (🔴) | Journal à ajouter en Lua : comparer `g_selected_target_id` et la direction réelle du missile. |
| H5 | Le verrou est bien reçu et l'arme oriente le missile vers lui **au départ**, mais le missile en vol **re-choisit le plus proche** | **programme seulement** (🔴) | Même sonde Lua : si la **direction au départ** vise la cible verrouillée mais la **trajectoire** dérive vers l'autre, c'est H5. |
| H6 | (AA / laser / TV seulement) Le mod de vitesse change le comportement des missiles | retirer / ajuster le mod (🟢) | Essai avec et sans le mod. |

À noter : `Revolution` n'est **plus dans `mods.xml`** (liste actuelle : `2937532682`, `cc2_mesures`, `cc2_carte` ; le fichier a été
modifié à 14:22 aujourd'hui, sauvegarde `mods.xml.bak_2026-10-27_carte`). Si Revolution est remis, son propre `vehicle_hud.lua`
(5 445 lignes au lieu de 3 160) s'applique : il ajoute notamment un radar « modifié » qui rend plus d'ennemis « observés »
(`get_is_visible_by_modded_radar`, ligne 4020) et un verrouillage automatique **pour la tourelle CIWS uniquement** (ligne 2401). Je
l'ai lu en diagonale seulement : à ne pas conclure sans essai avec le même jeu de mods que celui où le problème a été vu.

## 7. Options de correction et risques (aucune n'est appliquée)

| Option | Ce que ça fait | Risque | Retrait |
|---|---|---|---|
| **A. Sonde Lua en lecture seule** (nouveau petit mod local dans `%APPDATA%\Carrier Command 2\mods\`, dans la liste de `mods.xml`) | Affiche à l'écran, pendant un tir : numéro de la cible verrouillée, distance de chaque missile à cette cible et à l'ennemi le plus proche, état « observé » des cibles. Ne modifie rien dans le jeu | 🟢 Faible : Lua pur, retirable en une ligne ; une ligne ajoutée à `mods.xml` (sauvegarde datée d'abord) | supprimer la ligne ou le dossier |
| **B. Corriger le script de verrouillage en Lua** (mod local qui remplace `vehicle_hud.lua` : verrou plus tenace, choix de la cible la plus proche du **curseur** ou de la plus proche **en distance**, etc.) | Change **ce que T envoie** au serveur (le programme relit `g_selected_target_id`, donc Lua peut même le forcer) | 🟡 Moyen : le fichier est long (3 160 lignes), une mise à jour du jeu ou un autre mod (Revolution) qui remplace le même fichier = conflit ; une erreur de script casse l'affichage de pilotage (mais pas la partie) | retirer le mod |
| **C. Mod XML** (ajuster / retirer « Gentle Missile Speed Buff » pour AA et laser) | Ne concerne que les missiles que le mod change | 🟢 Faible | retirer le mod |
| **D. Patch du programme** (changer la façon dont le missile en vol choisit sa cible) | Seule voie si H5 est vraie | 🔴 Élevé : code de guidage **pas encore repéré** sur 1.5.18 (programme sans noms), effet sur tous les missiles, y compris ceux de l'IA et des tourelles ; une erreur peut planter la partie ou décaler la simulation (parties multijoueur) ; à faire **après** que le Mac ait lu sa version commentée | `patch_exe.py retirer` ou la sauvegarde |

## 8. Plan proposé (à valider étape par étape ; rien n'est lancé)

1. **Essai à la main, sans aucune modification (🟢)** : le moddeur tire un missile IR (puis AA) sur un ennemi isolé, en notant :
   (a) l'ennemi est-il « observé » ? (b) après T, y a-t-il un cadre **rouge** et sur **quel** ennemi ? (c) le cadre reste-t-il
   jusqu'au tir ? (d) où va le missile ? Aucun accord technique nécessaire.
2. **Selon la réponse** :
   - pas de cadre rouge → H1 : on explique comment « observer » l'ennemi, fin (ou option B pour assouplir) ;
   - cadre rouge sur la mauvaise cible → H2 → option B (petit correctif) ;
   - cadre rouge sur la bonne cible, le missile va ailleurs → étape 3.
3. **Sonde Lua (option A)**, avec accord du moddeur : jeu **fermé**, une ligne dans `mods.xml` avec sauvegarde, puis il rejoue
   la même scène ; on lit les chiffres. Cela départage H3, H4, H5.
4. **Seulement si H5** : poser la question au Mac (section 9), puis étudier un patch du programme avec la même méthode que
   `patch_exe.py` (sur copie, désassemblage relu), **un accord séparé** pour chaque étape.

## 9. Questions pour le Mac (versions avec noms de fonctions, programme 1.5.17)

Pour approfondir **sans toucher à rien**, le Mac peut lire dans son `build_mac` (avec `nm`) :
1. Quelle fonction lit `c_attachment_server_hardpoint::track_vector` (champ à +0x110 de l'arme, copié dans le missile à la création
   par `c_missile_container_server::create_missile_internal`) : dans quelle fonction du missile (`c_missile_server`… ?) est-il
   consommé, et est-ce là qu'un « plus proche » est calculé ?
2. Que vaut l'état interne de l'arme (champ à +0xc8 sur Windows : « `== 1` » avant d'accepter la cible) ?
3. Y a-t-il, côté missile, une fonction du type `get_closest_…target` (il en existe une pour les tourelles :
   `c_attachment_server_turret::get_closest_missile_target`) utilisée par le missile IR/AA en vol ?

## 10. Ce qui a été fait pendant cette étude (pour mémoire)

- Lecture seule des scripts, XML, constantes, mods Workshop et du programme (copie de sauvegarde, jamais l'original en place).
- Scripts d'aide uniquement dans le dossier temporaire de la session (recherche d'octets, désassemblage avec `capstone`, déjà installé) ;
  rien n'a été exécuté dans le dossier du jeu, le jeu n'a pas été lancé ni fermé, `mods.xml`, les DLL (`dinput8.dll`, `cc2x_frein.dll`,
  `frein.ini`) et les fichiers de `rom_0` n'ont pas été touchés.
- Seul fichier ajouté au dépôt : ce diagnostic (non commité).

## 11. Cause probable : le détecteur du missile (lu dans le code, pas encore vu en jeu)

**Récit du moddeur (27/10, après la première version de ce diagnostic)** : il verrouille un bateau visible sur son radar, le cadre rouge est
bien sur le bateau, mais au tir le missile va sur la cible **la plus proche**, en général près de l'île (une unité de l'île est détruite).

### Ce que fait le missile en vol (boucle de traitement des missiles, 0x746a70 → 0x74ccb0 ; branche du détecteur 0x74706b → 0x7475e2)

Lecture du désassemblage de la copie de sauvegarde (aucun essai en jeu) :

1. Le missile reçoit au départ **une direction** (`track_vector`, la direction vers la cible verrouillée à cet instant), **pas** l'identifiant
   de la cible verrouillée. Dans la boucle du missile, rien ne lit un identifiant de cible verrouillée.
2. Tant que le missile **n'a pas de cible** (indicateur de « guidage » `[missile+0x175]` à 0), il cherche seul, à chaque pas, parmi les
   **véhicules d'une autre équipe** (et non détruits) :
   - à **moins de 4 000 m du missile** (distance² < 16 000 000, constante en 0xdb7b88) ;
   - dans un **cône d'environ 45°** devant lui (produit scalaire > 0,7, constante 0xdb7374) ;
   - il note chaque candidat : **0,9 × (alignement avec la direction de départ)⁵ + 0,1 × (1 − distance / 4 000)** ; il retient le meilleur
     (seuil de départ 0 ; 0,05 pour le missile anti-aérien, qui ne regarde que les cibles aériennes).
3. Dès qu'un candidat est retenu, le missile **s'y accroche** : indicateur `+0x175` et identifiant de cible `+0x1d0`, mise à jour de sa
   position chaque pas ; il ne cherche plus. Un second groupe de candidats est examiné aussi (leurres/« flares », même rayon de 4 000 m).

### Pourquoi ça colle au récit du moddeur

- L'affichage de pilotage permet de verrouiller un bateau jusqu'à **10 000 m** (ennemis terrestres et aériens : 5 000 m ; `vehicle_hud.lua:2428-2429`).
- Le missile, lui, ne **voit** que jusqu'à **4 000 m**. Un bateau verrouillé à 6 ou 8 km n'est donc **pas encore un candidat** au départ.
- Le missile vole vers la direction de départ ; **le premier ennemi qui entre dans sa fenêtre de 4 km et de 45° est pris** — typiquement une défense
  de l'île placée devant le bateau. Quand le bateau entre enfin dans les 4 km, le missile est déjà accroché ailleurs.
- Le verrou ne sert donc, en pratique, qu'à **orienter** le missile et à **choisir parmi les cibles déjà dans les 4 km**.

(Ce raisonnement vient de la lecture du code et du récit du moddeur ; **il reste à confirmer en jeu**.)

### Peut-on le corriger ?

| Voie | Faisable ? | Risque |
|---|---|---|
| **Script Lua** | **Non.** Lua peut écrire quelle cible le HUD envoie (déjà correcte ici) mais n'a aucune commande pour guider un missile déjà lancé. | — |
| **Mod XML** | Non (pas de réglage de portée du détecteur dans `constants.txt` : la limite est écrite en dur) | — |
| **Contournement sans patch** | Oui : tirer quand le bateau est à **moins de ~4 km**, dans le cône de ~45° devant l'avion, et sans autre ennemi près de la ligne de tir | 🟢 (conseil, à vérifier en jeu) |
| **Patch « portée du détecteur »** : faire lire au point 0x747168 (candidats véhicules) une constante **déjà présente** valant 100 000 000 (10 000 m²) au lieu de 16 000 000. Même méthode que `ascenseur_x2` (une instruction redirigée, valeur partagée jamais modifiée). Effet : au départ, le bateau verrouillé (alignement parfait → note ≈ 0,9) devient candidat et **bat** les autres | **Oui, très probablement** (1 seul octet-groupe de 4 à changer ; la constante 100 000 000 existe une fois dans `.rdata`) | 🟡 Moyen : **tous** les missiles qui utilisent ce détecteur sont concernés, y compris ceux de l'IA ennemie (ils verront à 10 km) ; effet d'équilibre, pas de risque de plantage attendu ; réversible par `patch_exe.py retirer` ou la copie de sauvegarde |
| **Patch « verrou transmis »** : au tir, copier l'identifiant verrouillé dans le missile (`+0x1d0`) et le mettre directement en guidage | Possible mais plus lourd (code ajouté, branchements, à écrire en assembleur 32 bits) | 🔴 Élevé |

À savoir : les 4 lectures de la constante 16 000 000 sont en 0x747168 (candidats véhicules), 0x74772c (leurres), 0x749b98 et 0x74a234
(autres groupes, non étudiés : la seconde liste des objets de type 0x43 / 0x44, probablement des contre-mesures) ; **seule la première
serait modifiée**. Il faut encore **vérifier** que le missile vole bien vers la direction de départ avant l'accrochage (sinon la
fenêtre de 45° compte davantage) et décider de la valeur (10 km = portée de verrouillage des bateaux).

### Suite proposée (rien n'est appliqué)

1. Le moddeur confirme le scénario : distance au bateau au moment du tir (> 4 km ?) et type de missile (IR ? anti-aérien ?).
2. Écrire le module `ir_portee` pour `patch_exe.py` (1 site, générateur relu au désassembleur), le tester **sur copie** (le script de test
   existant), sans toucher au jeu.
3. **Accord séparé** du moddeur, jeu fermé : application, puis essai en jeu au même endroit (bateau à 6-8 km, unités de l'île devant).
4. Retour arrière à tout moment : `patch_exe.py retirer`, ou la copie `tour\sauvegardes`.

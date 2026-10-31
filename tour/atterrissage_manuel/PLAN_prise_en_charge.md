# Plan : faire reprendre l'avion posé à la main par le jeu (29/10/2026)

> **Statut au 30/10/2026 (passation)** : §1-§9 historiques (le §10 est **corrigé par le §11**, le §11 est **complété par le §12**) ; l'état à jour est dans le **§12** (résultat du grand essai v10), le **§13** (décision à prendre) et le **§14** (la v11, écrite hors jeu, non posée). Voir aussi « ÉTAT À LA PASSATION » en tête de `JOURNAL_atterrissage.md`.

**Lecture seule.** Rien n'a été lancé, posé, compilé ni modifié dans le jeu. Seul ce fichier est écrit (plus une entrée de journal). Demandé par le moddeur : « j'atterris l'avion, je le freine totalement et l'ordinateur reprend la main pour qu'il se pose et qu'il aille dans le hangar pour se ravitailler ».

Étiquettes : **MESURÉ** = vu dans un journal de partie · **LU** = lu dans un fichier / un désassemblage · **INFÉRÉ** = déduit, pas prouvé.

## 1. Le but, en deux phrases

Quand j'ai posé l'avion à la main et que le frein l'a arrêté, le jeu doit le **prendre en charge comme un avion de l'IA qui vient de toucher le pont** : le faire reculer sur ses rails jusqu'à l'ascenseur, le descendre au hangar et le ravitailler. Sans qu'il recule tout droit, sorte du pont ou tombe à l'eau, comme le 29/10.

## 2. Ce qu'on sait (les faits)

**MESURÉ (essai v6 du 29/10, journal `cc2x_2026-10-29_142607_frein_v6_ancien_exe.log`)**
- Frein, maintien et moteur coupé : ça marche (avion immobile plus d'une minute, `power=0.00`).
- À l'ordre de retour (14:32:48.998) : `dock 0 → 5`, `mode 0 → 3`, `wp 1 → 0` (le jeu efface le waypoint). **Mais `attached` reste 0, `flight` reste 2 (« en vol »), `dock` ne passe jamais à 1 ni à 6.**
- Notre plugin lâche alors le frein ; l'avion recule en ligne droite (vitesse relative 0,3 → 11 m/s en 12 s, 28 → 100 m du centre, roues 0/3 à 89-94 m = bout du pont) et tombe à l'eau.

**LU (SDK public, `cc2x.h`)** : états d'accostage `0 libre, 1 accostage, 2 départ en attente, 3 départ, 4 rangé, 5 EN FILE, 6 ROULAGE (taxi), 7 départ en pause`. On peut **écrire** `DOCK_STATE`, `DOCK_VEHICLE`, `FLIGHT_STATE`, `CONTROL_MODE/TARGET/SPEED/POWER`, `WAYPOINTS`. **`ATTACHED_TO` est en lecture seule** (« id du porte-avions sur lequel il se tient »). Le SDK offre aussi un crochet au milieu du code du jeu, `patch_mid` (avec contrôle des octets attendus). `request_landing` ne marche que pour les pistes des îles, pas pour le porte-avions.

**LU (étude du Mac §7.3 + relecture Windows faite aujourd'hui sur la copie d'origine = l'ancien exe)** : le jeu a un bloc qui s'exécute **juste après un toucher réussi** et qui fait toute la prise en charge. Sur Windows (adresses de l'image, ancien exe `0x6a36c177`) :

| Adresse | Ce que c'est (sens **INFÉRÉ** par correspondance avec le Mac : mêmes valeurs aux mêmes endroits) |
|---|---|
| `0x6ff263` | test « vitesse relative ≤ 10 m/s » (constante 10,0 en `0xdb78ec`) |
| `0x6ff320`-`0x6ff344` | test « toutes les roues touchent » (seuils 0,01 et 0,1, une case de `0x70` octets par roue) |
| `0x6ff362` | **la porte** : `test dl,dl ; je 0x6ffa5c` (si le toucher n'est pas validé, on saute tout le bloc) |
| `0x6ff368` | début du bloc : réservation d'une baie de hangar (`call 0x5ec1e0`, rangée dans le gestionnaire `+0x6c`) |
| `0x6ff3a8` | `frein(0, 1,0)` (appel virtuel `+0x94`) |
| `0x6ff3b4` | `puissance = 0` (`[avion+0x1fc]`, c'est notre `CONTROL_POWER`) |
| `0x6ff42e`-`0x6ff442` | trois champs remis à 0, 0, −1 (`+0x114`, `+0x118`, `+0x11c`) |
| `0x6ff66c`, `0x6ff676` | **`DOCK_STATE = 6` (taxi) et `FLIGHT_STATE = 1` (au sol)** (`+0x174`, `+0x170`) |
| `0x6ff70d` | **état de piste du gestionnaire = 5** (recul) (`[gestionnaire+0x1c]`) |
| `0x6ff757`… | remise à zéro de tampons, puis (appels à identifier : `0x854870`, `0x5eb340`, `0x4e4a90`, `0x5e7760`, `0x860c90`…) l'accrochage au porte-avions, le **joint physique** et les messages aux clients |

**LU (Windows)** : en `0x6ff2e5`, **avant** le test de toucher, le gestionnaire règle lui-même le frein des roues de l'avion à chaque tick (frein 0 au début de l'approche, montant jusqu'à 1 ; adhérence de 1 à 3). **INFÉRÉ** : à `dock=5` le gestionnaire « regarde » notre avion, mais ne le fait pas entrer dans le bloc de prise en charge (condition inconnue : créneau de piste ? progression ? état de la file ?).

## 3. Les options

| | Ce que ça fait | Ce que ça touche | Risque | Étiquette | Ma recommandation |
|---|---|---|---|---|---|
| **A. Écrire les champs depuis `cc2x_frein`** (`DOCK_STATE=6`, `FLIGHT_STATE=1`, `DOCK_VEHICLE`, effacer `WAYPOINTS`) | Dire au jeu « l'avion est au sol et en roulage » | Seulement des champs de l'avion | 🔴 | **INFÉRÉ** : sans la baie, sans le joint qui l'accroche au navire (`ATTACHED_TO` ne peut pas s'écrire), sans l'état de piste 5, l'avion « roule » sans rails et sans gestionnaire ; risque de créneau de piste bloqué, d'avion détruit ou d'état incohérent | **Non** |
| **B. Faire passer le test de toucher du jeu lui-même** (crochet `patch_mid` à la porte `0x6ff362`, uniquement pour l'avion que notre plugin tient et après l'ordre de retour : forcer `dl = 1`) | Le jeu exécute **lui-même tout le bloc** : baie, joint, état 6, piste 5, recul sur rails, ascenseur, hangar | 1 crochet de quelques octets dans le code d'atterrissage (octets attendus vérifiés ; sinon rien n'est posé) ; plugin `cc2x_frein` seul | 🟡 | **INFÉRÉ** : ne marche que si le gestionnaire traite déjà cet avion dans ce code (question 1). Reste à lire : ce que le bloc attend d'autre (créneau de piste, repère d'atterrissage, progression du recul, Mac §7.4) | **Option principale**, après l'étape 0 |
| **C. Rejouer les ~10 opérations du bloc depuis le plugin** (le « bloc du Mac » porté sur Windows) | Faire nous-mêmes baie, frein, puissance, accrochage, joint, états, chemin | Beaucoup de fonctions internes, tous les décalages 32 bits, repère d'atterrissage et progression à calculer | 🔴 | **LU** (Mac) pour la liste, **INFÉRÉ** pour tout le reste ; le SDK avertit qu'on ne déplace pas un avion sur ses roues | **Non** (trop long, trop fragile ; seulement si B échoue) |
| **D. Plan B sans code : toucher et repartir** | Le moddeur fait l'approche à la main, touche, **redécolle**, puis donne l'ordre de retour **en vol** : l'IA l'atterrit et le rentre comme d'habitude. La v6 ne freine jamais l'IA | Rien | 🟢 | **MESURÉ** (l'IA fait déjà ce chemin, le frein ne s'en mêle pas) | Repli si B échoue : ça ne donne pas « j'atterris et je freine », mais le ravitaillement marche |
| **E. Autre piste : commander l'avion nous-mêmes jusqu'à l'ascenseur** (`body_set` + frein) | Conduire l'avion en roulant sur le pont | Position et vitesse de l'avion | 🔴 | **INFÉRÉ** | **Non** |

## 4. Le plan d'essai, pas à pas

**Étape 0 : observation, sans rien lâcher (la plus utile, la moins risquée).** Nouveau plugin « v7 diagnostic » (à écrire et tester hors jeu d'abord, avec ton accord, 🟡 pour la pose comme les autres versions) :
- (a) au rappel (`dock` passe à 5), **on ne relâche pas** : frein 1,0 et moteur 0 pendant `recall_hold_s` (40 s), puis on relâche **seulement** si `recall_release=1` dans `frein.ini` (par défaut 0) ;
- (b) chaque seconde on écrit dans `cc2x.log` une ligne `RECALL id N` avec : `CONTROL_MODE`, `CONTROL_SPEED`, `CONTROL_TARGET` (x, y, z), `CONTROL_TAXI`, `DOCK_STATE`, `DOCK_VEHICLE`, `ATTACHED_TO`, `FLIGHT_STATE`, nombre de waypoints, vitesse relative, distance au centre, roues ;
- (c) seulement si (b) ne suffit pas : un crochet **en lecture seule** à `0x6ff362` qui note dans le journal le résultat du test de toucher (vitesse relative lue, roues, résultat).

Ce que fait le moddeur (il pilote) : partie **neuve** jetable, ancien exe via `lancer_ancien.py` ; navire ralenti ; atterrir en dessous de 30 m/s relatifs ; laisser le frein arrêter l'avion ; quitter l'avion ; attendre 30 s ; donner l'ordre de retour ; **ne plus rien toucher** pendant 40 s ; dire ce qu'il voit.

Ce que je lis dans `cc2x.log` (pas de « concluant » sans ces lignes) :
- `HOLD`, `IDLE` (comme aujourd'hui) puis, à l'ordre : **ligne `RECALL`** avec `mode=3`, `dock=5`, `wp=0` ;
- **la consigne du jeu** : `CONTROL_SPEED` et `CONTROL_TARGET` (vers où il veut aller, à quelle vitesse) ;
- **si l'avion bouge malgré le frein** : la vitesse relative sur 40 s (`rel` < 1 m/s = le jeu ne le tire pas ; `rel` qui monte = il le pilote) ;
- **si le jeu change son état** : `dock` 5 → 1 ou 6, `attached` ≠ 0, `flight` 2 → 1 (= il l'a pris en charge tout seul).

**Étape 1 : option B** (seulement si l'étape 0 dit que le gestionnaire traite l'avion et refuse le toucher). Crochet à `0x6ff362` actif pour un seul id et un seul tick, après `recall_hold_s`. Lignes qui prouvent le succès : `TOUCH id N forced` ; dans les 2 s `dock=6`, `attached=<id du porte-avions>`, `flight=1` ; puis `dist` qui change **le long de la piste** à vitesse régulière (rails), `dock` qui passe à 7 ou 4, l'avion qui disparaît de la liste (monté par l'ascenseur) ; et **à la fin `dock=4` (rangé) avec `fuel` qui monte** : c'est le ravitaillement, le vrai but. À l'écran, le moddeur doit voir l'avion reculer, tourner vers l'ascenseur, monter, entrer au hangar.

**Étape 2 : cas tordus** (une fois que B marche) : avion arrêté n'importe où sur la piste, 2 avions de suite, toucher puis repartir, waypoint remis par le joueur, avion qui change d'id.

## 5. Les sécurités

- **Ne pas relâcher le frein au rappel** tant que l'avion n'est pas pris en charge (étape 0 : `recall_release=0` par défaut).
- Partie **neuve et jetable** ; jamais une sauvegarde importante.
- Arrêter l'avion avec **au moins 60 m de pont derrière lui** (le bord arrière est à ~90 m du centre ; le 29/10 il s'est arrêté à 28 m, il lui restait ~60 m et il les a parcourus en 12 s).
- Tout couper en quelques secondes : (1) `brake_enabled=0` dans `frein.ini` (relu en 3 s, le plugin lâche tout ; **seulement si l'avion est loin du bord** : lâcher le frein, c'est ce qui a fait reculer l'avion) ; (2) remonter dans l'avion (le plugin lâche) ; (3) fermer le jeu ; (4) `poser.py retirer` (jeu fermé) enlève le plugin ; (5) `lancer_ancien.py retirer` enlève la copie de l'exe.
- Rien n'est posé ni lancé sans ton accord, une chose à la fois. Rien ne touche à `carrier_command.exe` de Steam.

## 6. Ce qui reste inconnu, et la première petite question

**Inconnus** : (1) pourquoi le gestionnaire ne valide pas le toucher d'un avion déjà arrêté sur le pont (créneau de piste ? l'avion n'a jamais franchi la « porte » d'entrée ? `flight` reste à 2 ?) ; (2) pourquoi l'avion a reculé moteur à 0 et frein lâché (le jeu le pousse-t-il avec une consigne de vitesse négative ? ou une consigne de point derrière lui ?) ; (3) ce que le bloc attend d'autre : repère d'atterrissage, progression du recul (l'avion arrêté au milieu de la piste : par où repart-il sur les rails ?) ; (4) ce qui se passe si le joueur reste « pilote » de l'avion pendant la prise en charge.

**Première petite question à trancher en jeu (étape 0)** : *à l'ordre de retour, avec le frein tenu, quelle consigne le jeu donne-t-il à l'avion, et fait-il avancer son état (`dock` 5 → 1 ou 6, `attached`) tout seul ?* La réponse choisit entre B (si le gestionnaire traite l'avion) et un travail de plus pour l'y faire entrer.

**La question UNIQUE pour le moddeur** : *« Je prépare le plugin v7 d'observation (il garde le frein au rappel et note ce que le jeu demande à l'avion) et je le teste hors jeu, sans rien poser ; tu fais ensuite un essai sur partie jetable avec l'ancien exe ? »*

## 7. Quel exe

L'**ancien** (`carrier_command_ancien_8E7FCBB6.exe`, voie A, lancé par `lancer_ancien.py`) : les adresses ci-dessus sont celles de ce build (horodatage `0x6a36c177`) ; sur le nouveau build elles sont décalées (étude de mise à jour). **Pas** les copies `carrier_command_test_cercle*.exe` : le circuit d'attente change l'approche et le retour des avions (autre conversation). Cet exe ne double pas le roulage du pont (`pont_retour_x2`), ce qui aide à comparer avec l'essai du 29/10.

## 8. Addendum du 29/10 (soir) : résultat de l'essai v7 et nouvelle piste « B2 : donner la piste nous-mêmes »

**Décision du moddeur (29/10, 16 h)** : « le but, c'est de le faire atterrir soi-même et qu'il reparte dans le hangar tout de suite, pour gagner du temps comparé à l'IA ». Donc **pas** de « il redécolle et se pose tout seul » : la voie 1 (v8 qui rend le moteur) est abandonnée. Reste la prise en charge au sol.

**MESURÉ (essai v7, journal `cc2x_2026-10-29_154658_frein_v7_diag.log`, lignes `RECALL` de 15:53:44 à 15:56:16)** : au rappel, `dock=5`, `mode=3`, `speed_ctl=80`, `target=(1952,120,3577)` (point d'attente à 120 m), `dock_vehicle=2`, `attached_to=0`, `flight=2`, pendant ~2,5 min : le jeu traite l'avion comme un avion **en vol dans la file d'atterrissage**. Il ne le prend pas en charge au sol.

**LU (relecture Windows, ancien exe, aujourd'hui)** — le bon morceau de code, plus petit que prévu :
- **Le jeu a un chemin « approche ratée »** (`0x6ff0f1`-`0x6ff205`) qui remet l'avion dans la file : `frein(0,1,0)`, **`puissance = 1,0`**, **`DOCK_STATE = 5`**, **`FLIGHT_STATE = 2`**, libère la piste (`[gestionnaire+0x5c] = −1`). C'est exactement l'état que notre avion rappelé a. Il est pris si « pas de baie libre » ou « approche trop longue (`[gestionnaire+0xd4] > 3600` ticks) ou angle > 0,45 » et que l'état de piste n'est pas 4.
- **Le bloc qui donne la piste** à un avion de la file (`0x701a2a`-`0x701afe`) est court : si `[gestionnaire] == 1` (navire en mode accostage) **et** `[gestionnaire+0x5c] == −1` (piste libre) **et** l'avion est à moins de 1000 m du « portillon » (point (0 ; −1200) dans le repère du bateau), alors : `[gestionnaire+0x5c] = id de l'avion` ; `[gestionnaire+0x1c] = 3` (état de piste 3 = approche finale + test de toucher) ; `[gestionnaire+0xd4] = 0` ; l'avion est retiré de la file (`call 0x844260`) ; **`DOCK_STATE = 1`** (accostage) ; un champ remis à 0 pour les autres avions de la file.
- **Le test de toucher** (état 3, `0x6ff263`…) et **le bloc de prise en charge** (`0x6ff368`…, `DOCK_STATE=6`, `FLIGHT_STATE=1`, état de piste 5, baie, joint) sont ensuite exécutés **par le jeu** si la vitesse relative ≤ 10 m/s, toutes les roues touchent et une baie est libre.
- Notre avion posé à la main est à ~1130-1280 m du portillon : il échoue au test des 1000 m, **et** son état dans la file est celui du début du circuit, pas celui du portillon.

**Piste B2 (INFÉRÉ, à lire plus avant avant de coder)** : un plugin qui, via un crochet (`patch_mid`) dans cette grande fonction, **fait lui-même les 4 écritures du bloc `0x701a2a`** pour NOTRE avion tenu au frein (piste libre + navire en accostage + avion rappelé `dock=5`) : `[gestionnaire+0x5c] = id`, `[gestionnaire+0x1c] = 3`, `[gestionnaire+0xd4] = 0`, retirer l'avion de la file, `DOCK_STATE = 1`. Au tick suivant, c'est le **code du jeu** qui exécute l'état 3 : avion immobile, roues au sol, vitesse relative ~0 → toucher validé → prise en charge native (baie, joint, recul sur rails, ascenseur, hangar). On n'écrit que ce que le jeu écrirait lui-même au portillon.
- **À lire d'abord** (lecture seule, sans jeu) : le début de l'état 3 (`0x6fdde5`-`0x6ff0da`) pour les conditions d'échec (angle, « bout de piste dépassé », hauteur), la structure de la file (`[gestionnaire+0x34]` : éléments de 12 octets id/état/…), l'appel de retrait `0x844260`, et un endroit du code où `edi` = gestionnaire pour poser le crochet.
- **Risque : 🟡-🔴** (code ajouté dans le programme, structure interne du jeu) ; limité par : une partie jetable, le crochet n'agit que pour un id que le plugin tient et rappelé, retrait = enlever la DLL. **Chance de réussite : moyenne** ; l'échec probable est « approche ratée » (angle, bout de piste) qui remet l'avion en file (dock 5, puissance 1,0, FLIGHT 2) : il faudrait alors tenir le frein.

## 9. Lecture de l'état 3, de la file et du crochet (29/10, soir) — résultat de la lecture seule

Source : désassemblage de la copie d'origine (ancien exe, `desasm.py`), plages `0x6fdde5`-`0x6ff0da` (état 3), `0x6ff0da`-`0x6ff368` (échec / toucher), `0x701a2a`-`0x701b10` (don de la piste). Rien lancé, rien écrit hors ce fichier.

**LU : la file des avions en attente** — dans le gestionnaire, une file circulaire en `[gestionnaire+0x34]` : `+0x34` pointeur des éléments, `+0x38` capacité, `+0x3c` tête, `+0x40` nombre d'éléments (indices relus en `0x6ff12e`-`0x6ff19a`). **Un élément = 12 octets : `{id de l'avion, état de circuit 0-5, un 3e champ}`**. Accès à l'élément n : `call 0x844310` (n en argument, `ecx = file`) ; retrait de l'élément n : `call 0x844260`. L'abandon d'approche (`0x6ff1a0`) remet l'avion en queue avec l'état de circuit **3**, un autre champ à 0.
**LU : le don de la piste** (`0x701a2a`-`0x701afe`) — atteint depuis l'état de circuit 1 quand l'avion passe le portillon (test `x > −1000` en `0x7019f3`, tick par tick). Conditions : `[gestionnaire] == 1`, `[gestionnaire+0x5c] == −1`, **distance de l'avion au point (0 ; −1200) < 1000 m** (`comiss` en `0x701a81`, `jbe` en `0x701a84`). Écritures : `[g+0x5c] = id` ; `[g+0x1c] = 3` ; `[g+0xd4] = 0` ; retrait de la file (`0x844260`) ; `DOCK_STATE = 1` de l'avion ; 3e champ des autres éléments remis à 0.
**LU : l'état 3 pour un avion** (`0x6fdde5`…) — chaque tick : compteur `[g+0xd4]++`, consigne de vitesse `18 × (1 − progression)` écrite dans l'avion (`+0x1f8`, en `0x6feeaf`), cible et mode de contrôle ; **si une roue touche le sol, `puissance = 0`** (`0x6feeee`) ; l'avion est ramené dans le repère du bateau et on calcule `z` = écart au point visé. **Conditions d'échec** (calculées en `0x6fef01`-`0x6ff0a8`) : (a) `z > 0` = point visé dépassé (en `0x6fef4e`), (b) angle entre le cap de l'avion et l'axe > 0,45 rad **seulement si −400 < z < −50** (`0x6fef51`-`0x6ff08e`, jamais pour un hélico), (c) compteur `[g+0xd4] > 3600` (`0x6ff0c5`), (d) pas de baie libre (`call 0x5ec1e0` = −1, `0x6ff0da`). Échec → chemin d'abandon `0x6ff0f1` (sauf si état de piste 4) : `frein(0,1)`, `puissance = 1,0`, `DOCK_STATE = 5`, `FLIGHT_STATE = 2`, piste libérée, avion remis en file. Sinon → test de toucher (`0x6ff263` : vitesse relative ≤ 10 ; roues `0x6ff320`) puis bloc de prise en charge (`0x6ff368`).
**LU : l'API des crochets du SDK** (`cc2x.h`) — `patch_mid(site, longueur ≥ 5, octets attendus, fn, user)` : `fn(cc2x_cpu*)` reçoit **tous les registres** (`edi, esi, ebp, ebx, edx, ecx, eax`), **`eflags`**, la pile (`CC2X_STACK`), et peut **modifier les registres et les drapeaux** ou **rediriger l'exécution (`jump_to`)** ; les octets déplacés doivent être indépendants de la position.
**Attention (LU)** : le compilateur réutilise des cases de pile et le registre `edi` : `edi` = **gestionnaire** autour de `0x6fddcf` et de `0x701a2a`, mais = **avion** dans la partie `0x6feec7`-`0x6fef00`. Le crochet doit se poser là où `edi` est le gestionnaire (vérifié ligne par ligne avant de poser).

**Conception B2 (INFÉRÉ)** : l'avion tenu, rappelé (`dock=5`), est dans la file avec un état de circuit de début de tour (0 ? à confirmer). Deux petits crochets, actifs **seulement pour l'id que notre plugin tient et rappelé**, le reste du jeu étant inchangé :
- **H1** au moment où le code choisit l'état de circuit (table de saut `0x701fd0`, à lire : quel registre porte l'état) : forcer l'état **1**. L'avion est déjà « après le portillon » (x ≈ 0 > −1000 dans le repère du bateau) : le test de `0x7019f3` passe tout de suite.
- **H2** en `0x701a84` (le `jbe` de la distance) : effacer les drapeaux (`CF`/`ZF`) pour que le test des 1000 m passe (l'avion posé est à ~1130-1280 m du point (0 ; −1200)).
Alors le jeu exécute **lui-même** le don de la piste (4 écritures + retrait de la file + `DOCK_STATE=1`), puis l'état 3, le test de toucher et le bloc de prise en charge. Notre plugin garde frein 1,0 et moteur 0 (comme la v7) jusqu'à ce que `dock` passe à 6 / `attached` ≠ 0 ; il ne fait **aucune** écriture dans la mémoire du gestionnaire.
**Réglages à prévoir** : un seul avion flaggé à la fois ; le drapeau s'éteint dès que `dock` ≠ 5 ou `attached`, ou après N secondes sans résultat (retour au comportement v7 = tenu) ; un compteur de tentatives (3 au plus).

**Ce qui reste INCONNU (à lire avant de coder)** : (1) l'instruction exacte et le registre de l'état de circuit au moment de la table de saut `0x701fd0` ; (2) l'état de circuit réel de l'élément à l'entrée dans la file (le rappel) ; (3) si `[gestionnaire] == 1` (navire en accostage) tient quand le moddeur appelle le rappel de l'avion posé à la main (probable : les autres avions rappelés atterrissent) ; (4) si une baie de hangar est libre (sinon échec d) ; (5) ce que fait l'état 3 d'un avion déjà immobile avant le test de toucher (partie `0x6fdf4f`-`0x6fe470` non lue en détail : calcul de la progression et de la cible) ; (6) le comportement au tick d'abandon : le jeu met `puissance = 1,0` et `frein 0` d'un coup (un tick) — notre plugin les remet à 0 / 1,0 au tick suivant, mais **un avion rappelé pourrait avoir un instant de poussée** (mitigation : tenir le frein, partie jetable).

**Estimation honnête** : *faisable en principe* (les 4 écritures du don de la piste sont lues et simples, le reste est natif), mais *jamais vu en jeu*. **Chance que le premier essai en jeu donne la prise en charge : ~35 %** ; **après 2 ou 3 itérations de lecture + essai : ~60 %**. Échecs probables : abandon d'approche (angle / baie) → l'avion repart en file avec `dock=5` (visible dans le journal, sans danger si le frein est tenu), ou plantage du jeu sur un mauvais site de crochet (partie jetable, retrait = enlever la DLL). **Risque** : 🟡 pour le code (crochets dans la fonction d'atterrissage du navire, limités à un id, retirables), 🔴 si l'on écrivait nous-mêmes dans la mémoire du gestionnaire (on ne le fait pas). **Coût** : lire l'état 3 et la table de saut (une séance), écrire + tester hors jeu la v8 (le crochet se teste avec un faux `cc2x_cpu` et une fausse mémoire), puis un à trois essais d'une dizaine de minutes avec le moddeur.

**La question suivante pour le moddeur** : « J'écris et je teste la v8 hors jeu (deux petits crochets, rien posé) pour essayer la prise en charge au sol ? »


## 10. Résultat de l'essai v9 (30/10, 08:48) : la CAUSE de l'abandon est le test d'angle (cône d'approche)

**MESURÉ** (journal `logs_parties\cc2x_2026-10-30_082200_frein_v9.log`, avion 9, ancien exe, v9 posée, `recall_force=1` mis par la coordination) :
- 08:37:37 `hooks H1 (0x7018ce), H2 (0x701a3d) and H3 (0x6ff0fb, read only) installed` ; 08:46:48 `BRAKE start` 27,9 m/s à 58 m ; 08:46:51 `HOLD`, `STOPPED after 5.6 s, 72 m` ; 08:46:59.8 `IDLE` ; avion tenu à 20 m du centre.
- **08:48:27.843 `RECALL start`** ; 08:48:28.307 `FORCE start` ; 08:48:28.323 `HOOK H1 … (real element state 0, manager mode 1, runway slot -1)` et `HOOK H2 … (try 1 of 3)` (`dock=1`) ; **08:48:28.355 `HOOK H3 the game ABORTS the approach (1 so far): bay=8 fail=1 z=-104.2 counter=1 runway_state=3 causes: angle>0.45rad`** ; `power=1.00` lu **une seule fois** (08:48:28.355, l'abandon du jeu), puis `power=0.00` ; `rel` < 0,8 m/s pendant tout l'essai ; 08:48:38.042 `FORCE timeout after 20 s (dock 5)` ; **`FORCE balance (timeout): GRANTS 1, ABANDONS 1`**. L'avion est resté tenu jusqu'à 08:55:31 (1065 s) : `IDLE ended (session ended)`.
- Donc : **la v9 est sûre** (une donation, un abandon, aucune boucle, aucun décollage) **et le diagnostic a marché**.

**Ce que dit H3** : `bay=8` = **il y a une baie libre** (cause « pas de baie » exclue) ; `counter=1` (cause « temps » exclue) ; `z=-104,2` → pas « point dépassé » (z < 0) ; l'indicateur d'échec est 1 et z est entre −400 et −50 : **c'est le test d'angle** (`0x6fef51`-`0x6ff08e`).

**LU (relecture du test d'angle, aujourd'hui)** : le test ne regarde **pas le cap de l'avion**, il regarde sa **position**. Le jeu prend le vecteur (avion − point visé), le normalise (O) et le compare à une direction de référence fixe R = (0 ; 1/15,03 ; −15/15,03) = (0 ; 0,0665 ; −0,9978), soit une **pente de 1 pour 15 (3,8°) vers l'arrière** : le « cône » de la trajectoire d'approche. Si l'angle entre O et R dépasse 0,45 rad (26°), c'est un échec. Pour un avion à 104 m du point visé, cela signifie un écart **latéral ou vertical de plus de ~50 m** par rapport à la pente d'approche (poids de 0 pour le latéral dans le produit scalaire, mais il augmente la longueur de O ; poids 0,0665 pour le vertical). Le test **ne s'applique que si −400 < z < −50** : à moins de 50 m du point visé, ou à plus de 400 m, il est sauté.
**INFÉRÉ** : notre avion est posé sur le pont à ~104 m du point visé (le point visé est ~100-120 m devant le milieu du pont, vers la proue) ; l'écart vertical/latéral entre sa position et le point (dans le repère du navire) dépasse ~50 m, probablement parce que la hauteur de ce point (ou son décalage latéral) n'est pas celle du pont. **Le chiffre exact n'est pas dans le journal** : H3 ne note que `z`, pas les deux autres composantes (`[ebp-0x270]` vertical, `[ebp-0x2cc]` latéral).

**Ce qu'on peut faire (ni l'un ni l'autre n'est posé)**
- **A. Sans code : s'arrêter à moins de 50 m du point visé** (le test d'angle est alors sauté). Le point visé est ~104 m devant l'avion arrêté à 20 m du centre : il faudrait s'arrêter vers 70-120 m du centre, donc tout au bout du pont, au risque de sortir du pont : **déconseillé**.
- **B. v10 : enrichir H3 (lecture seule) avec les deux composantes manquantes** (`[ebp-0x270]`, `[ebp-0x2cc]`) pour voir exactement l'écart ; coût : un test hôte, une pose, un essai.
- **C. v10 : crochet H4 pour sauter le test d'angle, pour l'avion signalé seulement.** Site `0x6fef58` (`89 8d a4 fd ff ff` = `mov [ebp-0x25c], ecx`, 6 octets, aucune opérande absolue, aucun saut n'y entre, aucune relocation, relu aujourd'hui) : entre le `comiss` sur z et le `jbe`. Le crochet ferait `jump_to = 0x6ff0b5` — la destination que le jeu emprunte **déjà** quand z est hors de l'intervalle −400..−50 — avec `ecx` = l'indicateur d'échec déjà calculé (pas de dépassement). Le jeu continue alors par son chemin normal (`0x6ff20a` : calcul de l'approche), puis **le test de toucher** (avion lent ✓ roues au sol ✓ baie 8 ✓) et la prise en charge (`0x6ff368`). Risque 🟡 (un 4e crochet dans la même fonction ; le jeu n'a jamais exécuté l'état 3 pour un avion arrêté, d'autres surprises possibles) ; **chance de prise en charge ~50 %** (le seul obstacle mesuré est l'angle ; restent le repère d'atterrissage et la suite de l'approche, jamais vus).
**Recommandation** : B + C ensemble en v10 (H3 enrichi pour confirmer, H4 pour essayer), tout éteint par défaut, mêmes sécurités (un avion, budget de donations, coupe-boucle, `recall_force=0`, pilote de retour). L'essai se ferait avec la même procédure et la même surveillance (PROCEDURE_partie_v9.md).


## 11. CORRECTION du §10 (30/10, relecture de l'engagement « état 4 ») : ce n'est pas (seulement) l'angle ; le saut de l'angle ne suffirait pas

En relisant `0x6fe436`-`0x6fe7e1` et `0x6ff0b5`-`0x6ff0f5` pour le crochet « sauter le test d'angle », j'ai trouvé que mon étiquette `angle>0.45rad` (écrite dans H3 par déduction) est **trompeuse** et que le crochet prévu ne résoudrait rien.

**LU — la vraie logique de l'état 3 pour un avion (ancien exe)** :
1. `[ebp-0x25c]` = distance restante de l'avion au **milieu de la piste** (écart en z au milieu des deux nœuds `[gestionnaire+0x84]` / `+0x88`). Si < 800 m : train sorti. Si < 400 m : le code évalue **l'engagement** (`0x6fe55b`…). Si < 200 m : l'octet `[ebp-0x205]` = 1 (« zone finale », `0x6fe470`).
2. **L'engagement** (`0x6fe55b`-`0x6fe7e1`) fait passer l'état de piste de 3 à **4** (`mov [edi+0x1c], 4` en `0x6fe7e1`), après avoir réservé la baie (`[gestionnaire+0x6c]`), remis le frein à (0 ; 1), et calculé le **repère d'atterrissage** (matrice copiée en `[gestionnaire+0xd8…0x128]`, en `0x6feb61`-`0x6febb5`). Il faut que tout ceci soit vrai : (A) longueur du vecteur avion → nœud de chemin > 0 (`0x6fe666`) ; (B) sa composante latérale normalisée > −0,08 (`0x6fe6ab`) ; (C) le produit scalaire de deux directions normalisées > 0,95, soit 18° (`0x6fe77b`) ; (D) un appel virtuel renvoie vrai (`0x6fe7a2`) ; (E) l'indice de baie est valide (`0x6fe7cc`). Les échecs A/B retombent en `0x6febda`, C/D en `0x6febe7`, E en `0x6febc0`.
3. **L'octet `[ebp-0x205]` est repris comme base de l'indicateur d'échec** (`0x6feec7` → `0x6fef2d`). Dans la zone finale (< 200 m) l'indicateur vaut donc **1**, et le jeu **abandonne l'approche (`0x6ff0f1`) sauf si l'état de piste est déjà 4** (`cmp [edi+0x1c], 4 ; je 0x6ff20a`). Le test d'angle (> 0,45 rad, `0x6ff08e`) n'est qu'une raison **parmi d'autres** d'avoir l'indicateur à 1.
4. Conséquence : **un avion garé à moins de 200 m du milieu de la piste n'a plus de chance de s'engager ; il est abandonné au premier tick dès qu'il est dans la zone finale sans état 4.** Un avion de l'IA s'engage entre 400 m et 200 m (alignement, cap, baie), puis l'abandon ne compte plus.

**Ce que ça change**
- Le `causes: angle>0.45rad` de H3 ne prouvait **que** « indicateur d'échec = 1, z entre −400 et −50 ». La cause vraie la plus probable est **« jamais engagé (état 3) dans la zone finale »**, indépendamment de l'angle. Mes tests T25 vérifiaient la déduction, pas le jeu : à corriger dans la v10 (libellé neutre : `not-committed-in-final-zone`).
- Le crochet H4 « sauter le test d'angle » (`0x6fef58`) **ne suffirait pas** : l'indicateur resterait à 1 à cause de `[ebp-0x205]`. Il faudrait **forcer l'engagement** (états 3 → 4 avec calcul du repère d'atterrissage, baie), c'est-à-dire neutraliser les portes A à E ou rejouer le bloc `0x6fe788`-`0x6febb5` : beaucoup plus intrusif, avec un calcul du repère d'atterrissage à partir de nœuds de chemin qui supposent un avion en approche.

**Options (honnêtes)**
- **I. v10 « diagnostic seulement » (recommandée)** : H3 corrigé (zone finale + `[ebp-0x205]` + composantes verticale/latérale), plus trois sondes en **lecture seule** sur les points de chute des portes : `0x6febda` (A/B), `0x6febe7` (C/D), `0x6febc0` (E), chacune `8 octets` sans opérande absolue. Résultat : on saura **quelle porte** bloque. Coût : un test hôte, une pose, un essai. Risque 🟡 (4 crochets en lecture seule en plus des 2 de forçage).
- **II. Forcer l'engagement** (après I) : un à quatre crochets qui font passer la porte bloquante pour l'avion signalé. **Chance de prise en charge complète : ~25-30 %** (le repère d'atterrissage et la suite n'ont jamais été vus pour un avion arrêté), risque 🟡-🔴.
- **III. S'arrêter là** pour la prise en charge au sol (garder le frein v7 : l'avion est arrêté, tenu, et le moddeur le repose ou le redécolle à la main ; l'IA ne reprend pas) ; c'est déjà utile si le moddeur veut juste un freinage à l'atterrissage.


## 12. Résultat du grand essai de la v10 (30/10, 09:41) : le jeu n'évalue même pas l'engagement pour un avion posé

**MESURÉ** (journal `logs_parties\cc2x_2026-10-30_092608_frein_v10.log`, avion 9, v10 posée, `recall_force=1`, `max_speed=50`) :
- 09:39:25 `BRAKE start` à 33,4 m/s, 75 m du centre ; 09:39:28 `STOPPED after 6.9 s, 104 m` ; tenu à 12 m du centre ; 09:41:22.465 `RECALL start` ; 09:41:22.929 `FORCE start` ; H1 (real element state 0, manager mode 1, slot -1) ; H2 `try 1 of 3` (`dock=1`) ; **09:41:22.993 `HOOK H3 … bay=8 fail=1 zone=1 x=-0.6 y=1.7 z=-95.2 counter=1 runway_state=3 causes: not-committed-in-final-zone`** ; `power=1.00` lu une fois ; `rel` ≈ 0,1-0,4 m/s ; un second `FORCE start` à 09:41:32 (voir « défaut » ci-dessous) avec un second octroi/abandon ; 09:41:42 `FORCE timeout` ; **`FORCE balance (timeout): GRANTS 1, ABANDONS 1, GATES AB 0 CD 0 (C passed 0) E 0`** ; avion tenu jusqu'à 09:51:10 (1420 s). Aucun décollage.
- **Écarts de l'avion à la trajectoire : latéral −0,6 m, vertical +1,7 m** : l'avion est **parfaitement dans l'axe**. L'hypothèse « angle / alignement » est définitivement écartée, et le conseil « se poser plus droit » n'a aucun sens.
- **Les quatre sondes n'ont JAMAIS tiré** (AB 0, CD 0, « C passed » 0, E 0) : **le code d'engagement n'a pas été exécuté du tout** pour cet avion.

**LU (relecture des seuils, `0x6fe436`-`0x6fe55b`)** : l'engagement (portes A à E, `0x6fe55b`…) n'est évalué que si la distance au milieu de la piste est **entre 200 et 400 m** (`comiss 200` en `0x6fe467` puis `comiss 400` en `0x6fe552`). En dessous de 200 m (cas d'un avion posé sur le pont, ~100 m du milieu) le jeu fait seulement `[ebp-0x205] = 1` (`0x6fe470`, zone finale) et **saute l'évaluation** ; puis le drapeau de zone sans état 4 provoque l'abandon (`0x6ff0f1`). Un avion de l'IA s'engage donc **avant** d'entrer dans les 200 m ; un avion posé à la main n'y a jamais accès.

**Défaut de ma v10 trouvé dans ce journal** : la fenêtre de forçage s'est fermée silencieusement après le premier abandon (le plugin repasse `t->force = 0` quand l'avion ne remplit plus « rel < 1 m/s, roues » pendant un tick), puis une **seconde fenêtre** s'est ouverte 10 s plus tard, avec **un budget de donations remis à zéro** et un coupe-boucle remis à zéro : **deux octrois au total** (au lieu d'un), donc deux ticks de poussée du jeu. Sans conséquence ici (`rel` max 0,95), mais à corriger : une seule fenêtre par rappel, fermeture définitive (`force_done`) et journalisée.

**Options**
- **III. S'arrêter** : garder le frein et le maintien de la v7/v10 ; la prise en charge au sol est refusée par le jeu pour une raison de conception (l'engagement doit avoir lieu à 200-400 m).
- **IV. v11 « entrer dans l'évaluation d'engagement »** (1 crochet de forçage, le seul de la v11) : au site `0x6fe470` (`c6 85 fb fd ff ff 01` = `mov byte [ebp-0x205], 1`, 7 octets, sans opérande absolue), pour l'avion signalé seulement : faire nous-mêmes l'écriture `[ebp-0x205] = 1` (ce que le jeu y fait) puis `jump_to = 0x6fe55b`, c'est-à-dire **rejouer le chemin que le jeu prend à 200-400 m**. Le jeu évalue alors ses portes A à E pour notre avion ; vu les écarts (−0,6 m, +1,7 m, baie 8 libre) elles devraient passer ; il fixe l'état 4, réserve la baie, calcule le repère d'atterrissage, puis dans le même passage le **test de toucher** (vitesse relative ≤ 10, roues au sol) déclenche la prise en charge (baie, joint, `DOCK_STATE=6`, état de piste 5, recul sur les rails). Les sondes de la v10 (inchangées) diront quelle porte échoue si ça rate. **Vérifié aujourd'hui** : à l'entrée de `0x6fe55b` le code ne lit pas xmm0/xmm1 avant de les écrire (la seule « lecture » de xmm0 est `xorps xmm0,xmm0`) ; xmm4/xmm5 restent préservés par l'enveloppeur. **Chance de prise en charge : ~50 %** (les portes devraient passer ; reste à voir si le calcul du repère d'atterrissage et la suite de l'état 4 acceptent un avion arrêté) ; **risque 🟡-🔴** (un crochet qui redirige le flux dans la grande fonction ; essai sur partie jetable avec la surveillance « REMONTE »).
- **Recommandation** : v11 (IV) avec la correction de la fenêtre unique, **uniquement si le moddeur accepte le risque** ; sinon III. Dans les deux cas : atterrir à ≤ 30 m/s (`max_speed=30`).


## 13. Décision à prendre (30/10/2026) et statut des documents

**Question posée au moddeur (sans réponse à la passation)** : « J'écris la **v11** hors jeu (un seul crochet de forçage en `0x6fe470` qui fait évaluer l'engagement à l'avion posé + une seule fenêtre de forçage par rappel), **ou on s'arrête** là pour la prise en charge au sol ? »
- **Si v11** : chance de prise en charge ~50 % (estimation non vérifiée, mes chiffres précédents — 35 %, 60 %, 25-30 % — ne se sont pas confirmés), risque 🟡-🔴 ; à écrire hors jeu avec l'enveloppeur xmm, à tester sur faux jeu, pose éteinte, puis essai groupé avec son oui et les alertes « REMONTE » (`LECTURE_SONDES_v10.md`) ; atterrissage à ≤ 30 m/s.
- **Si on s'arrête** : on garde le freinage + maintien (v10 éteinte posée). Repli pour le ravitaillement : toucher et repartir (les roues touchent, l'avion redécolle), puis ordre de retour **en vol** : l'IA atterrit et rentre comme d'habitude (déjà observé sans problème ; ne donne pas le freinage à l'atterrissage).

| Document | Statut au 30/10 |
|---|---|
| `PROCEDURE_partie_v9.md` | **utilisable** (gestes du moddeur ; valable pour la v10/v11) |
| `LECTURE_SONDES_v10.md` | **utilisable** pour la lecture ; **point 4 périmé** (le cas « aucune sonde + abandon » s'est produit : il mène à l'option v11 du §12, pas à l'arrêt) |
| `frein/RISQUES_v8.md`, `frein/RISQUES_v9.md` | **périmés** (v8/v9 remplacées), historique |
| `frein/RISQUES_v10.md` | **à jour** pour la v10 posée |
| `PLAN_prise_en_charge.md` §10 | **corrigé** par §11 et §12 (la cause « angle » est fausse) |
| `PROCEDURE_partie_v11.md`, `frein/RISQUES_v11.md` | **à jour** pour la v11 (écrite hors jeu, non posée, §14) ; `PROCEDURE_partie_v9.md` renvoie vers la v11 |


## 14. La v11 est écrite et testée hors jeu (30/10/2026) — rien posé, rien lancé

**Ce qui existe** : `frein/cc2x_frein.c` v11 (DLL `cc2x_frein.dll` sha256 `3CD7225D1BCE332B4DBDFFCC292C4834E2CB30D2552E9799194DD8A70C0F210F`, 234 496 octets, dans `cc2-sdk-travail\dist\` ; la v10 posée dans le jeu est sauvegardée dans `cc2-sdk-travail\dist_v10\`, `66731A35…`). **Un crochet nouveau, H4** (`0x6fe470`, 7 octets `c6 85 fb fd ff ff 01`) + la **fenêtre de forçage unique** par rappel + une ligne `VERDICT:` et une lecture de l'état de piste (lecture seule). **H1/H2 (donner la piste) restent** : sans eux le jeu ne fait jamais tourner l'état 3 pour l'avion et H4 ne serait jamais atteint ; H3 et les 4 sondes de la v10 restent inchangés (lecture seule). Total : 8 crochets, tous derrière l'enveloppeur xmm, posés seulement si `recall_force=1` au démarrage. Preuves et risques : `frein/RISQUES_v11.md` ; déroulé de l'essai : `PROCEDURE_partie_v11.md`.

**Relu aujourd'hui dans l'exe sauvegardé `8E7FCBB6` (LU)** — à ajouter au §11 :
- À `0x6fe470`, `edi` = l'avion, `[ebp-0x1fc]` = l'avion, `[ebp-0x204]` = le gestionnaire du porte-avions (`+0x1c` état de piste, `+0x6c` baie, `+0x5c` propriétaire, `+0xd4` compteur), `[ebp-0x25c]` = la distance au milieu de la piste (float). L'octet de zone `[ebp-0x205]` est mis à 0 en `0x6fe07a` (`xor al,al`) ; il n'est écrit à 1 qu'en `0x6fe470`, `0x6febce` (échec de la **porte E**, qui le met elle-même à 1) et `0x6ff23a` (suite de l'approche, avant le test de vitesse ≤ 10).
- Aucun saut relatif (tous alignements) ni adresse absolue du fichier ne vise `0x6fe471`-`0x6fe476` : H4 est posable. `0x6fe477` (juste après le site) est la cible commune du chemin « ≥ 400 m » et de l'échec des portes A/B.
- Le bloc `0x6fe55b`… ne teste **pas lui-même l'état de piste** (il empile un point dans une file, réserve une baie, etc.). Je n'ai pas établi s'il est sans effet pour un avion déjà engagé (état 4) ; **par prudence H4 n'agit que si l'état de piste vaut 3** (pas encore engagé), ce qui est exactement le cas où le jeu l'exécute pour un avion de l'IA qui s'engage. À l'entrée, `xmm0-3` sont écrits avant d'être lus ; la pile est la même que sur le chemin 200-400 m.
- Suites : portes A, B → `0x6fe477` sans toucher à l'octet de zone ; C, D, E → `0x6fe47d` (E met l'octet à 1) ; succès → état 4, `frein(0,1,0)` appelé par le jeu en `0x6fe7f9`, `DOCK_STATE=1` en `0x6feab5`, repère d'atterrissage copié, retour en `0x6fe47d`. Puis `0x6ff0e4`…`0x6ff0f5` : pas d'abandon si l'état vaut 4 ; `0x6ff20a` calcule la vitesse relative (≤ 10) et le test des roues (`0x6ff320` : pour chaque roue, 1er champ ≥ 0,01 **et** 2e champ ≤ 0,1, le sens du 2e champ n'est pas identifié), puis le bloc de prise en charge `0x6ff368`.

**Choix de conception** : H4 écrit lui-même `[ebp-0x205]=1` avant de rediriger (c'est ce que le jeu fait à ce point, et l'instruction déplacée n'est pas exécutée quand on redirige). Conséquence voulue : si une porte A à D échoue, le jeu **abandonne tout de suite** comme à la v10 (comportement mesuré, sûr) au lieu de rejouer le bloc à chaque tick. Sans cette écriture (**INFÉRÉ** d'après `0x6feec7`-`0x6ff0f5`), un échec des portes A à D laisserait l'avion en état 3 sans abandon et l'évaluation serait rejouée à chaque tick jusqu'au compteur 3600 (≈ 2 min), avec un empilement de points à chaque passage : un comportement que le jeu n'a jamais eu à tenir pour un avion arrêté.

**Non établi (INFÉRÉ, jamais vu)** : que les portes passent pour un avion arrêté ; que le repère d'atterrissage accepte un avion arrêté ; que le test de toucher (2e champ des roues) passe ; que le recul sur les rails fonctionne ; ce que le jeu fait de la piste et de la baie 8 si l'avion reste engagé sans être pris en charge. Aucun pourcentage n'est annoncé.

## 15. v12 (31/10/2026) : sauter dans le test de toucher, comme un hélicoptère

La v11 (§14) est **abandonnée sans avoir été posée** : les portes B (pente de descente) et C (vitesse vers le nœud A) ne peuvent pas passer pour un avion arrêté, et un engagement sans prise en charge bloquerait la piste (`tour/etude_atterrissage_apres_engagement/RAPPORT.md`). La v12 suit la conception (b) de `CONCEPTION_v12.md` : un crochet **H5** au site de H4 qui saute dans le **test de toucher** (`0x6ff20a`). **LU le 31/10** : c'est exactement le point où arrivent les **hélicoptères** par leur propre branche de l'état 3 (sans engagement) ; le bloc de prise en charge `0x6ff368` tourne donc à chaque hélico qui se pose. Détail, nœuds de la piste et contrôle des registres : `PISTE_v12_comme_un_helico.md` ; plugin, preuves et procédure : entrée du 31/10 de `JOURNAL_atterrissage.md`, `frein/RISQUES_v12.md`, `PROCEDURE_partie_v12.md`.

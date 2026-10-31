# Piste v12 : faire reprendre l'avion posé « comme un hélicoptère » (31/10/2026)

> **Suite (31/10)** : la v12 décrite au §4 est **écrite et testée hors jeu** (pas posée) : voir l'entrée du 31/10 de `JOURNAL_atterrissage.md`, `frein/RISQUES_v12.md`, `PROCEDURE_partie_v12.md`.

**Lecture seule.** Rien n'a été lancé, posé, compilé ni modifié dans le jeu. Exe lu : `tour/sauvegardes/carrier_command_1.5.18_original.exe` (sha256 `1c9a01c3…`, ancien build, PE `0x6a36c177`). Données lues : `rom_0/game_objects/vehicle_chassis_*.xml` (dossier du jeu, lecture seule). Outils : capstone + deux petits scripts dans le dossier temporaire de la session (pas dans le dépôt).

Étiquettes : **MESURÉ** (journal de partie) · **LU** (désassemblage ou fichier) · **INFÉRÉ** (déduit, pas prouvé).

S'appuie sur : `JOURNAL_atterrissage.md`, `PLAN_prise_en_charge.md` §8-13 (ce dépôt) ; v11 non commitée (worktree `musing-nobel-a0872c`) ; `tour/etude_atterrissage_apres_engagement/RAPPORT.md` et `CONCEPTION_v12.md` (worktree `atterrissage-apres-engagement-521262`, non commités) ; `tour/etude_port_nouvel_exe/RAPPORT.md` (worktree `port-nouvel-exe-27119f`).

## 1. En bref

1. La v11 (forcer l'engagement, portes A à E) **ne doit pas être essayée** : les portes B (pente de descente) et C (vitesse vers le nœud A) ne peuvent pas passer pour un avion arrêté (LU par l'étude « après engagement », revérifié par la coordination).
2. La conception (b) de `CONCEPTION_v12.md` (un crochet **H5** au site de H4, `0x6fe470`, qui saute dans le test de toucher du jeu `0x6ff20a`) est la bonne piste. **Ce que j'ajoute (LU) : ce chemin est celui que le jeu emploie pour CHAQUE atterrissage d'hélicoptère.** Les hélicos ne passent jamais par l'engagement ni par l'état 4 : état 3 → test de toucher → bloc de prise en charge `0x6ff368`. H5 ne fait donc qu'envoyer l'avion arrêté sur le chemin d'un hélico posé.
3. Les hélicos ont **3 roues**, comme les avions (LU, `vehicle_chassis_rotor_*.xml`) : le test des roues du toucher (contact ≥ 0,01 et 2e champ ≤ 0,1) est passé par un véhicule posé sur le pont à chaque atterrissage d'hélico. L'inconnue « M6 » (2e champ des roues) devient très probablement favorable.
4. Les nœuds de la piste sont dans les données du porte-avions (LU, `vehicle_chassis_carrier.xml`) : l'avion arrêté (≈ z −13) sera tiré **en ligne droite sur une trentaine de mètres vers l'ascenseur**, sur la partie du pont où se posent les hélicos. L'inconnue « M2-b » est fermée sans lancer le jeu.
5. Contrôle des cases de pile pour le saut de H5 (LU, script) : la seule case lue par le toucher et la prise en charge et réécrite dans la partie sautée est `[ebp-0x234]`, et elle n'y est réécrite que dans le chemin d'abandon, qui ne mène pas au toucher. Le saut donne donc au jeu les mêmes valeurs qu'au chemin normal.

## 2. Le chemin des hélicoptères (LU, ancien exe)

| Adresse | Ce que c'est |
|---|---|
| `0x6fe187`-`0x6fe192` | `call [vtable+0x4c]` sur le véhicule ; faux → `0x6fe436` (code des avions : 800 / 200 / 400 m, engagement) ; vrai → `0x6fe198` (**branche hélico**, confirmée par le module `helicos_approche_x2`, dont le site `0x6fe1b7` est dans cette branche) |
| `0x6fe3ef`-`0x6fe431` | hélico assez près : train sorti (`+0x98`, 1), **`DOCK_STATE = 1`** (`0x6fe413`), indicateur d'échec = écart latéral trop grand, sinon l'octet de zone `[ebp-0x205]` (resté à 0 : le code des 200 m n'est pas parcouru) |
| `0x6feec7`-`0x6fef51` | tronc commun : puissance 0 si une roue touche, écart au nœud B, « point visé dépassé » |
| `0x6fef79`-`0x6fef80` | 2e `call [vtable+0x4c]` : un hélico **saute le test du cône** (`jne 0x6ff0aa`) |
| `0x6ff0c5`-`0x6ff0eb` | compteur > 3600, baie libre, pas d'échec → **`0x6ff20a`** |
| `0x6ff20a`-`0x6ff362` | test de toucher : vitesse relative ≤ 10 (`0xdb78ec` = 10,0) ; 3e `call [vtable+0x4c]` : frein fixe 0,6 / adhérence 1,0 pour un hélico (`0xdb731c`, `0xdb7418`), frein progressif pour un avion ; chaque roue : `roue[+0] ≥ 0,01` (`0xdb71a0`) et `roue[+4] ≤ 0,1` (`0xdb71f8`) |
| `0x6ff368`… | bloc de prise en charge (baie, joint, `DOCK_STATE = 6`, `FLIGHT_STATE = 1`, état de piste 5, chemin `runway_reverse_a`) |

Conséquence : le bloc `0x6ff368` n'est pas « du code jamais vu » (inconnue n° 6 de `CONCEPTION_v12.md`) ; il tourne à chaque hélico qui se pose, véhicule arrêté sur ses roues, sans engagement.

Différences entre un hélico qui arrive en `0x6ff20a` et notre avion envoyé par H5 (LU) :
- `DOCK_STATE = 1` : l'hélico le reçoit en `0x6fe413`, notre avion l'a déjà reçu au don de la piste (H1/H2, MESURÉ v8-v10 : `dock=1`).
- Train sorti : l'avion le reçoit en `0x6fe436`-`0x6fe44f` (< 800 m), avant le site de H5.
- Frein avant le test des roues : progressif pour l'avion (`0x6ff296`), sans effet sur la suite (la prise en charge remet frein 0 / adhérence 1,0 en `0x6ff3a8`).
- Puissance 0 au contact (`0x6feeee`) : sautée par H5, mais le plugin la tient déjà à 0 (MESURÉ) et la prise en charge l'écrit (`0x6ff3b4`).

## 3. Les nœuds de la piste (LU, `vehicle_chassis_carrier.xml`, repère du navire, mètres)

| Nœud | x | y | z |
|---|---|---|---|
| `runway_start` (4) = nœud A | 0 | 20 | −68 |
| `runway_end` (5) = nœud B | 0 | 20 | +82 |
| `taxi_a` (8) | 0 | 20 | −44 |
| `lift_upper_wait` (7) | 12 | 20 | −32 |
| `lift_upper` (6) | 27,5 | 20 | −32 |

Liens : `runway` 4→5 ; `runway_reverse_a` 7→8 ; `runway_reverse_b` 8→4 ; `runway_reverse` 5→8 ; `lift_top_reverse` 6→7 ; `load_lift_lower` 10→9.

- MESURÉ (v10) : `z = −95,2` par rapport au nœud B, `dist = 12` m du centre ⇒ avion arrêté vers **z ≈ −13** (82 − 95), cohérent. Milieu de piste à z = +7 : l'avion est à ~20 m du milieu, donc dans la « zone finale » (< 200 m), comme lu.
- INFÉRÉ : un avion de l'IA est saisi au nœud B (z = +82) puis tiré vers l'ascenseur (≈ 126 m à ≤ 2,5 m/s, ce qui colle avec « pont → hangar 0:55 » mesuré avant `pont_retour_x2`). Notre avion, saisi vers z ≈ −13, ne fait qu'une **portion** de ce trajet : ≈ 31 m jusqu'à `taxi_a` ou ≈ 26 m jusqu'à `lift_upper_wait` (le « premier nœud » exact de `runway_reverse_a` reste à confirmer dans le journal), en ligne droite, dans l'axe, à côté de l'endroit où les hélicos se posent (z ≈ −40, `MESURES_helicos.md`).

## 4. Ce que serait la v12

Base : la v11 (fenêtre unique par rappel, lecture de l'état de piste, ligne `VERDICT`, enveloppeur xmm), **sans H4**, plus :
1. **H5** au site `0x6fe470` (7 octets `c6 85 fb fd ff ff 01`) : pour l'avion signalé seulement, si `[g+0x1c] == 3` et `[g+0x5c] == id` : `edi = [ebp-0x204]`, `esi = [ebp-0x200]`, `jump_to = 0x6ff20a`. Sinon : rien (le jeu fait son abandon propre, mesuré 3 fois).
2. **Précontrôles en lecture seule** avant chaque saut (repris de `CONCEPTION_v12.md` §2.1) : ascenseur libre `[g+0x58] == −1`, baie préférée libre (ou au moins une baie libre), vitesse relative < 0,5 m/s, 3 roues sur 3.
3. **Critère de succès corrigé** : `dock = 6` **et** `flight = 1` **et** état de piste 5 (pas `attached ≠ 0`, qui apparaît dès l'engagement ou la prise en charge).
4. **Suivi** des états de piste 5, 6, 7, puis `dock = 4` (rangé) et carburant qui monte = **le vrai but**.
5. **Sonde en lecture seule** en `0x6ff379` (baie rendue par le rappel de la prise en charge).
6. **Table par build** dès le départ (ancien exe `0x6a36c177` et nouvel exe `0x6ae228f3`) : sites de la v10 + H5. Nouvel exe : `0x6fe470 → 0x6fe580` (SÛR, étude de portage), cible `0x6ff20a → 0x6ff31a` (+0x110 ; LU le 31/10 dans la copie `461E1262` : mêmes instructions en `0x6fe580`, `0x6ff31a` et au début du bloc de prise en charge `0x6ff478`), nom de build `1.5.18-win32-6ae228f3` accepté en plus de `1.5.18-win32`.
7. Tests hôte (faux `cc2x_cpu`), 2 compilations, imports comparés à la v10, comme d'habitude. Rien posé sans « oui ».

## 5. Ancien ou nouvel exe ?

- **Premier essai sur l'ancien exe** (`lancer_ancien.py`) : SDK, frein, journal et procédure y marchent déjà ; une seule nouveauté à la fois.
- **Sur le nouvel exe directement**, on empilerait trois premières fois (copie patchée du nouvel exe jamais lancée, SDK à deux profils jamais chargé, v12) : en cas d'échec on ne saurait pas laquelle est en cause.
- La v12 aura les deux tables d'adresses ; le passage au nouvel exe se fera quand le SDK à deux profils y sera posé (étape « portage » de la coordination).

## 6. Chances (estimation, avec la raison)

Les estimations précédentes (35 %, 60 %, 50 %, 25-30 %, 50 %) ne se sont **pas** vérifiées : chaque essai a découvert un nouvel obstacle de conception (avion « en vol » dans la file, zone finale, portes d'approche). Ce qui change ici : on ne demande plus au code d'**approche** d'accepter un avion arrêté, on l'envoie sur le chemin qu'emprunte déjà un **hélico posé**.

| Maillon | État |
|---|---|
| Se poser, freiner, tenir | MESURÉ (4 essais) |
| Rappel + don de la piste (H1/H2) | MESURÉ (v8, v9, v10) |
| Le saut H5 ne fait pas planter | LU (site vérifié dans les deux exe, cases de pile cohérentes) ; jamais exécuté |
| Le test de toucher passe | INFÉRÉ fort (les hélicos posés sur 3 roues le passent) ; 2e champ des roues jamais lu |
| La prise en charge et le joint | LU, chemin des hélicos ; jamais vu avec un avion |
| Le recul sur ~30 m, l'ascenseur, le hangar | INFÉRÉ (portion du trajet de l'IA) |

**Environ 1 chance sur 2 que le premier essai aille jusqu'au hangar ; environ 2 sur 3 après un ou deux essais de correction.** Les échecs les plus probables sont sans danger : « le toucher n'a jamais passé » (la fenêtre se ferme, le jeu abandonne proprement, l'avion reste tenu) ; le pire réaliste est un plantage ou une piste bloquée dans une **partie jetable**.

## 7. Ce qui reste inconnu

1. Le sens du 2e champ des roues (`roue[+4] ≤ 0,1`) et sa valeur pour l'avion tenu au frein (le journal de la v12 le lira).
2. Le premier nœud exact de `runway_reverse_a` (7 ou 8) : la v12 l'écrira au journal à la prise en charge.
3. Le comportement du joint sur un avion qui vient d'être tenu au frein (le plugin lâche tout dès `attached ≠ 0`).
4. Si l'ascenseur est occupé, l'avion attend en bout de chemin (comme l'IA).
5. La capture est un pas sans retour (comme pour l'IA), mais les états 5, 6, 7 se terminent seuls.

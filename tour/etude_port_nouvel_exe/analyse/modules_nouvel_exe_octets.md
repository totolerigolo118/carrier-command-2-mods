# Modules d'exe du NOUVEL exe de Steam (461E1262...) : octets site par site

Genere par `tour/etude_port_nouvel_exe/outils/fabriquer_modules_nouvel_exe.py` a partir des 6 modules de l'ancien build et des sites retrouves par `localiser_sites.py`. Etiquette : **MESURE** (octets et desassemblage), jamais vu en jeu.

- nouvel exe : sha256 `461E12623BACB7DE29CA27B4614425C87E8DF2C8327A5E958A957C850EFFE42A`, 11354112 octets, horodatage PE `0x6ae228f3`

## `ascenseur_x2` (32 changements)

*PRIORITAIRE (celui que le moddeur utilise) : utilise en jeu sur l'ancien exe ; sur le nouvel exe, controle sur les octets et au desassemblage seulement, jamais essaye en jeu.*

- sha256 avec ce module seul : `1D004BEF0B90C469FE3251FE8C67F871348DECC1E91F5D8113CFBBA41210C8A2`

| nouvelle adresse | decalage fichier | avant | apres | ancienne adresse | type | reglage | preuve |
|---|---|---|---|---|---|---|---|
| `0x00400310` | `0x310` | `00000000` | `898888bd` | `0x00400310` | cave_entete | `CP_T_CRANE_V_NEG` | meme adresse, bourrage nul dans les deux exe |
| `0x006ea1b1` | `0x2e95b1` | `cdcccc3e` | `cdcc4c3f` | `0x006ea0a1` | imm | `CP_T_ENERGY_SHARE` | immediat identique avant/apres qu'a l'ancien exe |
| `0x006f9921` | `0x2f8d21` | `0077db00` | `6878db00` | `0x006f9811` | abs | `CP_T_TAXI_CAP` | premiere copie en lecture seule de 5.0 (.rdata), voisins identiques a l'ancien 0x00db7830 |
| `0x006f9955` | `0x2f8d55` | `0872db00` | `0c56ce00` | `0x006f9845` | abs | `CP_T_TAXI_ACCEL` | premiere copie en lecture seule de 0.10000000149011612 (.rdata), voisins identiques a l'ancien 0x00ce560c |
| `0x006fb3de` | `0x2fa7de` | `0872db00` | `0c56ce00` | `0x006fb2ce` | abs | `CP_T_TAXI_ACCEL` | premiere copie en lecture seule de 0.10000000149011612 (.rdata), voisins identiques a l'ancien 0x00ce560c |
| `0x006fb3f9` | `0x2fa7f9` | `0077db00` | `6878db00` | `0x006fb2e9` | abs | `CP_T_TAXI_CAP` | premiere copie en lecture seule de 5.0 (.rdata), voisins identiques a l'ancien 0x00db7830 |
| `0x006fccba` | `0x2fc0ba` | `0872db00` | `0c56ce00` | `0x006fcbaa` | abs | `CP_T_TAXI_ACCEL` | premiere copie en lecture seule de 0.10000000149011612 (.rdata), voisins identiques a l'ancien 0x00ce560c |
| `0x006fccc2` | `0x2fc0c2` | `0077db00` | `6878db00` | `0x006fcbb2` | abs | `CP_T_TAXI_CAP` | premiere copie en lecture seule de 5.0 (.rdata), voisins identiques a l'ancien 0x00db7830 |
| `0x006fcf5e` | `0x2fc35e` | `0872db00` | `0c56ce00` | `0x006fce4e` | abs | `CP_T_TAXI_ACCEL` | premiere copie en lecture seule de 0.10000000149011612 (.rdata), voisins identiques a l'ancien 0x00ce560c |
| `0x006fcf66` | `0x2fc366` | `0077db00` | `6878db00` | `0x006fce56` | abs | `CP_T_TAXI_CAP` | premiere copie en lecture seule de 5.0 (.rdata), voisins identiques a l'ancien 0x00db7830 |
| `0x006fd9e5` | `0x2fcde5` | `0872db00` | `0c56ce00` | `0x006fd8d5` | abs | `CP_T_TAXI_ACCEL` | premiere copie en lecture seule de 0.10000000149011612 (.rdata), voisins identiques a l'ancien 0x00ce560c |
| `0x006fda00` | `0x2fce00` | `0077db00` | `6878db00` | `0x006fd8f0` | abs | `CP_T_TAXI_CAP` | premiere copie en lecture seule de 5.0 (.rdata), voisins identiques a l'ancien 0x00db7830 |
| `0x006fdec5` | `0x2fd2c5` | `0872db00` | `0c56ce00` | `0x006fddb5` | abs | `CP_T_TAXI_ACCEL` | premiere copie en lecture seule de 0.10000000149011612 (.rdata), voisins identiques a l'ancien 0x00ce560c |
| `0x006fdecd` | `0x2fd2cd` | `0077db00` | `6878db00` | `0x006fddbd` | abs | `CP_T_TAXI_CAP` | premiere copie en lecture seule de 5.0 (.rdata), voisins identiques a l'ancien 0x00db7830 |
| `0x006ffb78` | `0x2fef78` | `0077db00` | `6878db00` | `0x006ffa68` | abs | `CP_T_TAXI_CAP` | premiere copie en lecture seule de 5.0 (.rdata), voisins identiques a l'ancien 0x00db7830 |
| `0x006ffbff` | `0x2fefff` | `0872db00` | `0c56ce00` | `0x006ffaef` | abs | `CP_T_TAXI_ACCEL` | premiere copie en lecture seule de 0.10000000149011612 (.rdata), voisins identiques a l'ancien 0x00ce560c |
| `0x00701036` | `0x300436` | `5c72db00` | `580bce00` | `0x00700f26` | abs | `CP_T_CRANE_H` | premiere copie en lecture seule de 0.3333333432674408 (.rdata), voisins identiques a l'ancien 0x00ce0b58 |
| `0x00701041` | `0x300441` | `4c7cdb00` | `a4e4ce00` | `0x00700f31` | abs | `CP_T_CRANE_H_NEG` | premiere copie en lecture seule de -0.3333333432674408 (.rdata), voisins identiques a l'ancien 0x00cee4a4 |
| `0x00701092` | `0x300492` | `1c7cdb00` | `10034000` | `0x00700f82` | abs | `CP_T_CRANE_V_NEG` | en-tete : meme adresse |
| `0x007010aa` | `0x3004aa` | `f471db00` | `1c72db00` | `0x00700f9a` | abs | `CP_T_CRANE_V` | premiere copie en lecture seule de 0.06666667014360428 (.rdata), voisins identiques a l'ancien 0x00db71e4 |
| `0x00701145` | `0x300545` | `5c72db00` | `580bce00` | `0x00701035` | abs | `CP_T_CRANE_H` | premiere copie en lecture seule de 0.3333333432674408 (.rdata), voisins identiques a l'ancien 0x00ce0b58 |
| `0x00701150` | `0x300550` | `4c7cdb00` | `a4e4ce00` | `0x00701040` | abs | `CP_T_CRANE_H_NEG` | premiere copie en lecture seule de -0.3333333432674408 (.rdata), voisins identiques a l'ancien 0x00cee4a4 |
| `0x00701193` | `0x300593` | `1c7cdb00` | `10034000` | `0x00701083` | abs | `CP_T_CRANE_V_NEG` | en-tete : meme adresse |
| `0x007011b6` | `0x3005b6` | `f471db00` | `1c72db00` | `0x007010a6` | abs | `CP_T_CRANE_V` | premiere copie en lecture seule de 0.06666667014360428 (.rdata), voisins identiques a l'ancien 0x00db71e4 |
| `0x00701234` | `0x300634` | `f471db00` | `1c72db00` | `0x00701124` | abs | `CP_T_CRANE_V` | premiere copie en lecture seule de 0.06666667014360428 (.rdata), voisins identiques a l'ancien 0x00db71e4 |
| `0x0070123c` | `0x30063c` | `1c7cdb00` | `10034000` | `0x0070112c` | abs | `CP_T_CRANE_V_NEG` | en-tete : meme adresse |
| `0x007012c6` | `0x3006c6` | `f471db00` | `1c72db00` | `0x007011b6` | abs | `CP_T_CRANE_V` | premiere copie en lecture seule de 0.06666667014360428 (.rdata), voisins identiques a l'ancien 0x00db71e4 |
| `0x007012ce` | `0x3006ce` | `1c7cdb00` | `10034000` | `0x007011be` | abs | `CP_T_CRANE_V_NEG` | en-tete : meme adresse |
| `0x00701329` | `0x300729` | `fc71db00` | `2472db00` | `0x00701219` | abs | `CP_T_CRANE_ROT` | premiere copie en lecture seule de 0.07999999821186066 (.rdata), voisins identiques a l'ancien 0x00db71ec |
| `0x00701335` | `0x300735` | `247cdb00` | `347cdb00` | `0x00701225` | abs | `CP_T_CRANE_ROT_NEG` | premiere copie en lecture seule de -0.07999999821186066 (.rdata), voisins identiques a l'ancien 0x00db7bfc |
| `0x00705d24` | `0x305124` | `e871db00` | `0872db00` | `0x00705c14` | abs | `CP_T_PLATFORM_STEP` | premiere copie en lecture seule de 0.05000000074505806 (.rdata), voisins identiques a l'ancien 0x00db71d0 |
| `0x00705d4e` | `0x30514e` | `187cdb00` | `287cdb00` | `0x00705c3e` | abs | `CP_T_PLATFORM_STEP_NEG` | premiere copie en lecture seule de -0.05000000074505806 (.rdata), voisins identiques a l'ancien 0x00db7bf0 |

## `atterrissage_cercle` (3 changements)

*SECONDAIRE : essaye en jeu sur l'ancien exe (essai 1 du 27/10 et essai 2 du 29/10) ; sur le nouvel exe, octets et desassemblage seulement.*

- sha256 avec ce module seul : `A8B4F4490DAC1F7551914C944A046C35C0CC1AA6CCC03BA461A9C43546FEB402`

| nouvelle adresse | decalage fichier | avant | apres | ancienne adresse | type | reglage | preuve |
|---|---|---|---|---|---|---|---|
| `0x0070148f` | `0x30088f` | `00001644` | `0000e1c4` | `0x0070137f` | imm | `LANDING_CIRCLE_FRONT_CENTER_Z` | immediat identique avant/apres qu'a l'ancien exe |
| `0x00701e6e` | `0x30126e` | `a87adb00` | `8c7edb00` | `0x00701d5e` | abs | `LANDING_CIRCLE_STATE3_END` | premiere copie en lecture seule de -1800.0 (.rdata), voisins identiques a l'ancien 0x00db7e54 |
| `0x00702062` | `0x301462` | `a87adb00` | `8c7edb00` | `0x00701f52` | abs | `LANDING_CIRCLE_STATE5_END` | premiere copie en lecture seule de -1800.0 (.rdata), voisins identiques a l'ancien 0x00db7e54 |

## `atterrissage_creneau` (3 changements)

*SECONDAIRE : essaye en jeu sur l'ancien exe (essai 2 du 29/10, une seule partie, melange avec le cercle et pont_retour_x2) ; sur le nouvel exe, octets et desassemblage seulement.*

- sha256 avec ce module seul : `DD55A1A54844250ACAF712D01C93AAB1F3DB27AB4B4B424BE890699A65A5FBC7`

| nouvelle adresse | decalage fichier | avant | apres | ancienne adresse | type | reglage | preuve |
|---|---|---|---|---|---|---|---|
| `0x00701b0c` | `0x300f0c` | `04010000` | `2a000000` | `0x007019fc` | rel32 | `LANDING_GATE_STATE1` | saute au bloc « test de la piste » equivalent 0x00701b3a (contexte 64+64) au lieu de la sortie 0x00701c14 |
| `0x00701e45` | `0x301245` | `cbfdffff` | `f1fcffff` | `0x00701d35` | rel32 | `LANDING_GATE_STATE2` | saute au bloc « test de la piste » equivalent 0x00701b3a (contexte 64+64) au lieu de la sortie 0x00701c14 |
| `0x00701e5f` | `0x30125f` | `b1fdffff` | `d7fcffff` | `0x00701d4f` | rel32 | `LANDING_GATE_STATE2_TO_3` | saute au bloc « test de la piste » equivalent 0x00701b3a (contexte 64+64) au lieu de la sortie 0x00701c14 |

## `helicos_approche_x2` (1 changements)

*SECONDAIRE, JAMAIS VU EN JEU (valide sur le Mac seulement). Sur le nouvel exe : octets et desassemblage seulement.*

- sha256 avec ce module seul : `0DF816F7D5E73B964A4150E907AD5A863999C83ED2131D1AD28899EADEAFD727`

| nouvelle adresse | decalage fichier | avant | apres | ancienne adresse | type | reglage | preuve |
|---|---|---|---|---|---|---|---|
| `0x006fe2c7` | `0x2fd6c7` | `f079db00` | `187adb00` | `0x006fe1b7` | abs | `HELI_APPROACH_AIM_AHEAD_M` | premiere copie en lecture seule de 100.0 (.rdata), voisins identiques a l'ancien 0x00db79e0 |

## `pont_retour_x2` (1 changements)

*SECONDAIRE, PEU VU EN JEU : la fiche d'etude dit « jamais vu en jeu » ; il n'a tourne qu'une fois, melange aux autres (essai 2 du 29/10, copie « pont »). Sur le nouvel exe : octets et desassemblage seulement.*

- sha256 avec ce module seul : `41A00F2CCA385B11B61E99C85B4A26B32E8D9A90F0BF55458DE0F4EB09FA3B0E`

| nouvelle adresse | decalage fichier | avant | apres | ancienne adresse | type | reglage | preuve |
|---|---|---|---|---|---|---|---|
| `0x006fdebd` | `0x2fd2bd` | `c479db00` | `6879db00` | `0x006fddad` | abs | `RETURN_TAXI_TICKS_PER_SECOND` | premiere copie en lecture seule de 15.0 (.rdata), voisins identiques a l'ancien 0x00db7930 |

## `temps_x2` (1 changements)

*PRIORITAIRE (celui que le moddeur utilise, MODE TEST) : utilise en jeu sur l'ancien exe ; sur le nouvel exe, controle sur les octets et au desassemblage seulement, jamais essaye en jeu.*

- sha256 avec ce module seul : `A2353B6A68A34C2B2CD0E42C0C42DB1DC2E3B73C5A09769C0CCD15B5A85C3EFB`

| nouvelle adresse | decalage fichier | avant | apres | ancienne adresse | type | reglage | preuve |
|---|---|---|---|---|---|---|---|
| `0x00835dfb` | `0x4351fb` | `0000803f` | `00000040` | `0x00835ccb` | imm | `SERVER_SPEED_FACTOR` | immediat identique avant/apres qu'a l'ancien exe |

## Constantes cibles (adresse ancienne -> nouvelle)

| ancienne | nouvelle | valeur | choix |
|---|---|---|---|
| `0x00400310` | `0x00400310` | 0.0 | en-tete : meme adresse (1 copie(s) en lecture seule) |
| `0x00ce0b58` | `0x00ce0b58` | 0.3333333432674408 | premiere copie en lecture seule de 0.3333333432674408 (.rdata), voisins identiques a l'ancien 0x00ce0b58 (5 copie(s) en lecture seule) |
| `0x00ce560c` | `0x00ce560c` | 0.10000000149011612 | premiere copie en lecture seule de 0.10000000149011612 (.rdata), voisins identiques a l'ancien 0x00ce560c (5 copie(s) en lecture seule) |
| `0x00cee4a4` | `0x00cee4a4` | -0.3333333432674408 | premiere copie en lecture seule de -0.3333333432674408 (.rdata), voisins identiques a l'ancien 0x00cee4a4 (2 copie(s) en lecture seule) |
| `0x00db71d0` | `0x00db7208` | 0.05000000074505806 | premiere copie en lecture seule de 0.05000000074505806 (.rdata), voisins identiques a l'ancien 0x00db71d0 (4 copie(s) en lecture seule) |
| `0x00db71e4` | `0x00db721c` | 0.06666667014360428 | premiere copie en lecture seule de 0.06666667014360428 (.rdata), voisins identiques a l'ancien 0x00db71e4 (1 copie(s) en lecture seule) |
| `0x00db71ec` | `0x00db7224` | 0.07999999821186066 | premiere copie en lecture seule de 0.07999999821186066 (.rdata), voisins identiques a l'ancien 0x00db71ec (4 copie(s) en lecture seule) |
| `0x00db7830` | `0x00db7868` | 5.0 | premiere copie en lecture seule de 5.0 (.rdata), voisins identiques a l'ancien 0x00db7830 (1 copie(s) en lecture seule) |
| `0x00db7930` | `0x00db7968` | 15.0 | premiere copie en lecture seule de 15.0 (.rdata), voisins identiques a l'ancien 0x00db7930 (1 copie(s) en lecture seule) |
| `0x00db79e0` | `0x00db7a18` | 100.0 | premiere copie en lecture seule de 100.0 (.rdata), voisins identiques a l'ancien 0x00db79e0 (1 copie(s) en lecture seule) |
| `0x00db7bf0` | `0x00db7c28` | -0.05000000074505806 | premiere copie en lecture seule de -0.05000000074505806 (.rdata), voisins identiques a l'ancien 0x00db7bf0 (1 copie(s) en lecture seule) |
| `0x00db7bfc` | `0x00db7c34` | -0.07999999821186066 | premiere copie en lecture seule de -0.07999999821186066 (.rdata), voisins identiques a l'ancien 0x00db7bfc (1 copie(s) en lecture seule) |
| `0x00db7e54` | `0x00db7e8c` | -1800.0 | premiere copie en lecture seule de -1800.0 (.rdata), voisins identiques a l'ancien 0x00db7e54 (1 copie(s) en lecture seule) |

# Module exe `ascenseur_x2` : octets a changer dans carrier_command.exe (1.5.18)

Genere par `tour/outils/generer_module_exe.py` a partir de `SITES_ENERGY` (cp_groups.c) et de la copie de sauvegarde.

- sha256 origine : `1C9A01C3007CB2BEC2A04D716812CF9F24C87EFA11056395C89DDD7D2C341026`
- sha256 apres patch : `DAC8B1E66B03ACEA7DC64B02EB24F6A9F19C61FA242D7E8E68F0C5D8B7888B48`
- 32 changements de 4 octets chacun (30 operandes de constantes + 1 immediat d'energie + 1 valeur(s) ajoutee(s) dans l'en-tete).
- Toutes les adresses modifiees ont une entree de relocation : le patch reste correct si Windows deplace le programme.

## Constantes choisies (valeur doublee)

| reglage | nouvelle valeur | adresse | section | origine |
|---|---|---|---|---|
| `CP_T_CRANE_H` | 0.333333333 | `0x00ce0b58` | .rdata | copie existante (5 en lecture seule) |
| `CP_T_CRANE_H_NEG` | -0.333333333 | `0x00cee4a4` | .rdata | copie existante (2 en lecture seule) |
| `CP_T_CRANE_ROT` | 0.08 | `0x00db71ec` | .rdata | copie existante (4 en lecture seule) |
| `CP_T_CRANE_ROT_NEG` | -0.08 | `0x00db7bfc` | .rdata | copie existante (1 en lecture seule) |
| `CP_T_CRANE_V` | 0.0666666667 | `0x00db71e4` | .rdata | copie existante (1 en lecture seule) |
| `CP_T_CRANE_V_NEG` | -0.0666666667 | `0x00400310` | (en-tete) | bourrage inutilise de l'en-tete du fichier |
| `CP_T_PLATFORM_STEP` | 0.05 | `0x00db71d0` | .rdata | copie existante (4 en lecture seule) |
| `CP_T_PLATFORM_STEP_NEG` | -0.05 | `0x00db7bf0` | .rdata | copie existante (1 en lecture seule) |
| `CP_T_TAXI_ACCEL` | 0.1 | `0x00ce560c` | .rdata | copie existante (5 en lecture seule) |
| `CP_T_TAXI_CAP` | 5 | `0x00db7830` | .rdata | copie existante (1 en lecture seule) |

## Changements

| adresse | decalage fichier | avant | apres | role |
|---|---|---|---|---|
| `0x00400310` | `0x310` | `00000000` | `898888bd` | valeur ajoutee dans le bourrage de l'en-tete (CP_T_CRANE_V_NEG) |
| `0x006ea0a1` | `0x2e94a1` | `cdcccc3e` | `cdcc4c3f` | energie : 5e ecriture de la fonction, part ascenseur / grue presumee (a confirmer par le Mac, Q3), mov [edi+8], 0,4: mov dword ptr [edi + 8], 0x3ecccccd |
| `0x006f9811` | `0x2f8c11` | `c876db00` | `3078db00` | roulage : plafond 2,5, bloc 1: movss xmm2, dword ptr [0xdb76c8], constante 0x00db76c8 = 2.5 |
| `0x006f9845` | `0x2f8c45` | `d071db00` | `0c56ce00` | roulage : acceleration 0,05, bloc 1: addss xmm0, dword ptr [0xdb71d0], constante 0x00db71d0 = 0.0500000007 |
| `0x006fb2ce` | `0x2fa6ce` | `d071db00` | `0c56ce00` | roulage : acceleration 0,05, bloc 2: addss xmm0, dword ptr [0xdb71d0], constante 0x00db71d0 = 0.0500000007 |
| `0x006fb2e9` | `0x2fa6e9` | `c876db00` | `3078db00` | roulage : plafond 2,5, bloc 2: movss xmm1, dword ptr [0xdb76c8], constante 0x00db76c8 = 2.5 |
| `0x006fcbaa` | `0x2fbfaa` | `d071db00` | `0c56ce00` | roulage : acceleration 0,05, bloc 3: addss xmm0, dword ptr [0xdb71d0], constante 0x00db71d0 = 0.0500000007 |
| `0x006fcbb2` | `0x2fbfb2` | `c876db00` | `3078db00` | roulage : plafond 2,5, bloc 3: movss xmm1, dword ptr [0xdb76c8], constante 0x00db76c8 = 2.5 |
| `0x006fce4e` | `0x2fc24e` | `d071db00` | `0c56ce00` | roulage : acceleration 0,05, bloc 4: addss xmm0, dword ptr [0xdb71d0], constante 0x00db71d0 = 0.0500000007 |
| `0x006fce56` | `0x2fc256` | `c876db00` | `3078db00` | roulage : plafond 2,5, bloc 4: movss xmm3, dword ptr [0xdb76c8], constante 0x00db76c8 = 2.5 |
| `0x006fd8d5` | `0x2fccd5` | `d071db00` | `0c56ce00` | roulage : acceleration 0,05, bloc 5: addss xmm0, dword ptr [0xdb71d0], constante 0x00db71d0 = 0.0500000007 |
| `0x006fd8f0` | `0x2fccf0` | `c876db00` | `3078db00` | roulage : plafond 2,5, bloc 5: movss xmm3, dword ptr [0xdb76c8], constante 0x00db76c8 = 2.5 |
| `0x006fddb5` | `0x2fd1b5` | `d071db00` | `0c56ce00` | roulage : acceleration 0,05 chargee dans xmm2 avant l'aiguillage (bloc 6): movss xmm2, dword ptr [0xdb71d0], constante 0x00db71d0 = 0.0500000007 |
| `0x006fddbd` | `0x2fd1bd` | `c876db00` | `3078db00` | roulage : plafond 2,5 chargee dans xmm5 avant l'aiguillage (bloc 6, sert au bloc 7): movss xmm5, dword ptr [0xdb76c8], constante 0x00db76c8 = 2.5 |
| `0x006ffa68` | `0x2fee68` | `c876db00` | `3078db00` | roulage : plafond 2,5, bloc 7: movss xmm5, dword ptr [0xdb76c8], constante 0x00db76c8 = 2.5 |
| `0x006ffaef` | `0x2feeef` | `d071db00` | `0c56ce00` | roulage : acceleration 0,05, bloc 7: addss xmm0, dword ptr [0xdb71d0], constante 0x00db71d0 = 0.0500000007 |
| `0x00700f26` | `0x300326` | `2472db00` | `580bce00` | grue horizontale +1/6, bloc A: movss xmm2, dword ptr [0xdb7224], constante 0x00db7224 = 0.166666672 |
| `0x00700f31` | `0x300331` | `147cdb00` | `a4e4ce00` | grue horizontale -1/6, bloc A: movss xmm1, dword ptr [0xdb7c14], constante 0x00db7c14 = -0.166666672 |
| `0x00700f82` | `0x300382` | `e47bdb00` | `10034000` | grue verticale -1/30, bloc A: movss xmm1, dword ptr [0xdb7be4], constante 0x00db7be4 = -0.0333333351 |
| `0x00700f9a` | `0x30039a` | `bc71db00` | `e471db00` | grue verticale +1/30, bloc A: movss xmm2, dword ptr [0xdb71bc], constante 0x00db71bc = 0.0333333351 |
| `0x00701035` | `0x300435` | `2472db00` | `580bce00` | grue horizontale +1/6, bloc B: movss xmm2, dword ptr [0xdb7224], constante 0x00db7224 = 0.166666672 |
| `0x00701040` | `0x300440` | `147cdb00` | `a4e4ce00` | grue horizontale -1/6, bloc B: movss xmm1, dword ptr [0xdb7c14], constante 0x00db7c14 = -0.166666672 |
| `0x00701083` | `0x300483` | `e47bdb00` | `10034000` | grue verticale -1/30, bloc B: movss xmm1, dword ptr [0xdb7be4], constante 0x00db7be4 = -0.0333333351 |
| `0x007010a6` | `0x3004a6` | `bc71db00` | `e471db00` | grue verticale +1/30, bloc B: movss xmm2, dword ptr [0xdb71bc], constante 0x00db71bc = 0.0333333351 |
| `0x00701124` | `0x300524` | `bc71db00` | `e471db00` | grue verticale +1/30, bloc C (hauteur 12): movss xmm2, dword ptr [0xdb71bc], constante 0x00db71bc = 0.0333333351 |
| `0x0070112c` | `0x30052c` | `e47bdb00` | `10034000` | grue verticale -1/30, bloc C (hauteur 12): movss xmm1, dword ptr [0xdb7be4], constante 0x00db7be4 = -0.0333333351 |
| `0x007011b6` | `0x3005b6` | `bc71db00` | `e471db00` | grue verticale +1/30, bloc D (hauteur 11): movss xmm2, dword ptr [0xdb71bc], constante 0x00db71bc = 0.0333333351 |
| `0x007011be` | `0x3005be` | `e47bdb00` | `10034000` | grue verticale -1/30, bloc D (hauteur 11): movss xmm1, dword ptr [0xdb7be4], constante 0x00db7be4 = -0.0333333351 |
| `0x00701219` | `0x300619` | `c471db00` | `ec71db00` | grue rotation +0,04: movss xmm2, dword ptr [0xdb71c4], constante 0x00db71c4 = 0.0399999991 |
| `0x00701225` | `0x300625` | `ec7bdb00` | `fc7bdb00` | grue rotation -0,04: movss xmm1, dword ptr [0xdb7bec], constante 0x00db7bec = -0.0399999991 |
| `0x00705c14` | `0x305014` | `b071db00` | `d071db00` | plateforme : pas +0,025 (charge xmm3, sert au minss et au divss): movss xmm3, dword ptr [0xdb71b0], constante 0x00db71b0 = 0.0250000004 |
| `0x00705c3e` | `0x30503e` | `e07bdb00` | `f07bdb00` | plateforme : pas -0,025 (borne basse): maxss xmm1, dword ptr [0xdb7be0], constante 0x00db7be0 = -0.0250000004 |

# Etape 3 : verification des 31 sites du groupe energy_lift_crane_taxi

Relus avec capstone dans `carrier_command.exe` (copie de sauvegarde). Aucune erreur. Adresses d'image, base 0x400000.

| adresse | long. | disp | reglage | instruction | constante lue | role |
|---|---|---|---|---|---|---|
| `0x006ea09e` | 7 | +3 | `CP_T_ENERGY_SHARE` | `mov dword ptr [edi + 8], 0x3ecccccd` | immediat 0,4 | energie : 5e ecriture de la fonction, part ascenseur / grue presumee (a confirmer par le Mac, Q3), mov [edi+8], 0,4 |
| `0x00705c10` | 8 | +4 | `CP_T_PLATFORM_STEP` | `movss xmm3, dword ptr [0xdb71b0]` | 0x00db71b0 = 0.0250000004 | plateforme : pas +0,025 (charge xmm3, sert au minss et au divss) |
| `0x00705c3a` | 8 | +4 | `CP_T_PLATFORM_STEP_NEG` | `maxss xmm1, dword ptr [0xdb7be0]` | 0x00db7be0 = -0.0250000004 | plateforme : pas -0,025 (borne basse) |
| `0x00700f22` | 8 | +4 | `CP_T_CRANE_H` | `movss xmm2, dword ptr [0xdb7224]` | 0x00db7224 = 0.166666672 | grue horizontale +1/6, bloc A |
| `0x00700f2d` | 8 | +4 | `CP_T_CRANE_H_NEG` | `movss xmm1, dword ptr [0xdb7c14]` | 0x00db7c14 = -0.166666672 | grue horizontale -1/6, bloc A |
| `0x00700f7e` | 8 | +4 | `CP_T_CRANE_V_NEG` | `movss xmm1, dword ptr [0xdb7be4]` | 0x00db7be4 = -0.0333333351 | grue verticale -1/30, bloc A |
| `0x00700f96` | 8 | +4 | `CP_T_CRANE_V` | `movss xmm2, dword ptr [0xdb71bc]` | 0x00db71bc = 0.0333333351 | grue verticale +1/30, bloc A |
| `0x00701031` | 8 | +4 | `CP_T_CRANE_H` | `movss xmm2, dword ptr [0xdb7224]` | 0x00db7224 = 0.166666672 | grue horizontale +1/6, bloc B |
| `0x0070103c` | 8 | +4 | `CP_T_CRANE_H_NEG` | `movss xmm1, dword ptr [0xdb7c14]` | 0x00db7c14 = -0.166666672 | grue horizontale -1/6, bloc B |
| `0x0070107f` | 8 | +4 | `CP_T_CRANE_V_NEG` | `movss xmm1, dword ptr [0xdb7be4]` | 0x00db7be4 = -0.0333333351 | grue verticale -1/30, bloc B |
| `0x007010a2` | 8 | +4 | `CP_T_CRANE_V` | `movss xmm2, dword ptr [0xdb71bc]` | 0x00db71bc = 0.0333333351 | grue verticale +1/30, bloc B |
| `0x00701120` | 8 | +4 | `CP_T_CRANE_V` | `movss xmm2, dword ptr [0xdb71bc]` | 0x00db71bc = 0.0333333351 | grue verticale +1/30, bloc C (hauteur 12) |
| `0x00701128` | 8 | +4 | `CP_T_CRANE_V_NEG` | `movss xmm1, dword ptr [0xdb7be4]` | 0x00db7be4 = -0.0333333351 | grue verticale -1/30, bloc C (hauteur 12) |
| `0x007011b2` | 8 | +4 | `CP_T_CRANE_V` | `movss xmm2, dword ptr [0xdb71bc]` | 0x00db71bc = 0.0333333351 | grue verticale +1/30, bloc D (hauteur 11) |
| `0x007011ba` | 8 | +4 | `CP_T_CRANE_V_NEG` | `movss xmm1, dword ptr [0xdb7be4]` | 0x00db7be4 = -0.0333333351 | grue verticale -1/30, bloc D (hauteur 11) |
| `0x00701215` | 8 | +4 | `CP_T_CRANE_ROT` | `movss xmm2, dword ptr [0xdb71c4]` | 0x00db71c4 = 0.0399999991 | grue rotation +0,04 |
| `0x00701221` | 8 | +4 | `CP_T_CRANE_ROT_NEG` | `movss xmm1, dword ptr [0xdb7bec]` | 0x00db7bec = -0.0399999991 | grue rotation -0,04 |
| `0x006f9841` | 8 | +4 | `CP_T_TAXI_ACCEL` | `addss xmm0, dword ptr [0xdb71d0]` | 0x00db71d0 = 0.0500000007 | roulage : acceleration 0,05, bloc 1 |
| `0x006fb2ca` | 8 | +4 | `CP_T_TAXI_ACCEL` | `addss xmm0, dword ptr [0xdb71d0]` | 0x00db71d0 = 0.0500000007 | roulage : acceleration 0,05, bloc 2 |
| `0x006fcba6` | 8 | +4 | `CP_T_TAXI_ACCEL` | `addss xmm0, dword ptr [0xdb71d0]` | 0x00db71d0 = 0.0500000007 | roulage : acceleration 0,05, bloc 3 |
| `0x006fce4a` | 8 | +4 | `CP_T_TAXI_ACCEL` | `addss xmm0, dword ptr [0xdb71d0]` | 0x00db71d0 = 0.0500000007 | roulage : acceleration 0,05, bloc 4 |
| `0x006fd8d1` | 8 | +4 | `CP_T_TAXI_ACCEL` | `addss xmm0, dword ptr [0xdb71d0]` | 0x00db71d0 = 0.0500000007 | roulage : acceleration 0,05, bloc 5 |
| `0x006fddb1` | 8 | +4 | `CP_T_TAXI_ACCEL` | `movss xmm2, dword ptr [0xdb71d0]` | 0x00db71d0 = 0.0500000007 | roulage : acceleration 0,05 chargee dans xmm2 avant l'aiguillage (bloc 6) |
| `0x006ffaeb` | 8 | +4 | `CP_T_TAXI_ACCEL` | `addss xmm0, dword ptr [0xdb71d0]` | 0x00db71d0 = 0.0500000007 | roulage : acceleration 0,05, bloc 7 |
| `0x006f980d` | 8 | +4 | `CP_T_TAXI_CAP` | `movss xmm2, dword ptr [0xdb76c8]` | 0x00db76c8 = 2.5 | roulage : plafond 2,5, bloc 1 |
| `0x006fb2e5` | 8 | +4 | `CP_T_TAXI_CAP` | `movss xmm1, dword ptr [0xdb76c8]` | 0x00db76c8 = 2.5 | roulage : plafond 2,5, bloc 2 |
| `0x006fcbae` | 8 | +4 | `CP_T_TAXI_CAP` | `movss xmm1, dword ptr [0xdb76c8]` | 0x00db76c8 = 2.5 | roulage : plafond 2,5, bloc 3 |
| `0x006fce52` | 8 | +4 | `CP_T_TAXI_CAP` | `movss xmm3, dword ptr [0xdb76c8]` | 0x00db76c8 = 2.5 | roulage : plafond 2,5, bloc 4 |
| `0x006fd8ec` | 8 | +4 | `CP_T_TAXI_CAP` | `movss xmm3, dword ptr [0xdb76c8]` | 0x00db76c8 = 2.5 | roulage : plafond 2,5, bloc 5 |
| `0x006fddb9` | 8 | +4 | `CP_T_TAXI_CAP` | `movss xmm5, dword ptr [0xdb76c8]` | 0x00db76c8 = 2.5 | roulage : plafond 2,5 chargee dans xmm5 avant l'aiguillage (bloc 6, sert au bloc 7) |
| `0x006ffa64` | 8 | +4 | `CP_T_TAXI_CAP` | `movss xmm5, dword ptr [0xdb76c8]` | 0x00db76c8 = 2.5 | roulage : plafond 2,5, bloc 7 |

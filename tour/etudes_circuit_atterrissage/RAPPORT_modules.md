# Modules exe `atterrissage_creneau` et `atterrissage_cercle`

Genere par `tour/outils/generer_modules_atterrissage.py` (sites definis dans `tour/etudes_circuit_atterrissage/verifier_sites.py`). Etude complete : `tour/etudes_circuit_atterrissage/ETUDE.md`.

## `atterrissage_creneau`

creneau de piste elargi : la piste peut etre donnee a l'avion pendant tout le virage arriere (3 sauts).

| adresse du champ | decalage fichier | avant | apres | role |
|---|---|---|---|---|
| `0x007019fc` | `0x300dfc` | `04010000` | `2a000000` | etat 1 du circuit (1re moitie du virage arriere) : `jbe 0x701b04` (sortie) -> `jbe 0x701a2a` (test de la piste) [jbe 0x701b04 a 0x007019fa] |
| `0x00701d35` | `0x301135` | `cbfdffff` | `f1fcffff` | etat 2 (2e moitie du virage arriere) : `jbe 0x701b04` (sortie) -> `jbe 0x701a2a` (test de la piste) [jbe 0x701b04 a 0x00701d33] |
| `0x00701d4f` | `0x30114f` | `b1fdffff` | `d7fcffff` | passage etat 2 -> 3 : `jmp 0x701b04` (sortie) -> `jmp 0x701a2a` (test de la piste) [jmp 0x701b04 a 0x00701d4e] |

- sha256 avec ce module seul (a partir de l'original) : `63D8D2800D73BD3DE48C643E24DC6C0B847ACB87D83B716B2541ED4EED67E7A8`
- Retour arriere : `patch_exe.py retirer --module atterrissage_creneau`.

## `atterrissage_cercle`

circuit d'attente des avions en CERCLE au lieu d'un ovale (1 valeur ecrite dans le code, 2 lectures de constante).

| adresse du champ | decalage fichier | avant | apres | role |
|---|---|---|---|---|
| `0x0070137f` | `0x30077f` | `00001644` | `0000e1c4` | centre du virage AVANT, z : `mov dword ptr [ebp-0x2a4], 600.0` -> `-1800.0` (meme cercle que le virage arriere) [mov dword ptr [ebp - 0x2a4], 0x44160000 a 0x00701379] |
| `0x00701d5e` | `0x30115e` | `707adb00` | `547edb00` | etat 3 : seuil de fin de la ligne droite `comiss xmm0,[600.0]` -> `[-1800.0]` [comiss xmm0, dword ptr [0xdb7a70] a 0x00701d5b] |
| `0x00701f52` | `0x301352` | `707adb00` | `547edb00` | etat 5 : seuil de fin du virage avant `movss xmm0,[600.0]` -> `[-1800.0]` [movss xmm0, dword ptr [0xdb7a70] a 0x00701f4e] |

- sha256 avec ce module seul (a partir de l'original) : `25C72357946296ED448852806A3AFB514128AEA4A2C36CD36BCDBB5FBC955DD7`
- Retour arriere : `patch_exe.py retirer --module atterrissage_cercle`.

## Les deux ensemble (reglage « B » du Mac)

- sha256 de l'original + les deux modules : `F408475232AE923EEE1234ECEBD941F4C806D56194DFCFF301B30C74AE0AEA3F`.
- Aucun octet commun entre les deux modules ni avec `ascenseur_x2` / `temps_x2` (controle fait a la generation et par `test_patch_exe.py`).

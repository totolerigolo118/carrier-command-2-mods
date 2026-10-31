# P0 — Liste des faits sur le jeu à revérifier nous-mêmes (phase P2)

Établie le 28/10/2026, **par lecture seule** du SDK figé `7ab05c7` (`C:\Users\UTILISATEUR\Documents\cc2-sdk-tiers\Carrier-Command-2-extender`) et de nos deux plugins. **Aucun de ces faits n'a été revérifié dans cette phase** : tous sont **LU dans le SDK** (donc « affirmé par un tiers »), certains sont en plus **MESURÉ en jeu** (colonne « Vu en jeu »). La phase P2 les confirme ou les contredit au désassembleur (capstone, 32 bits) sur le vrai `carrier_command.exe` (`8E7FCBB6…E8BE`), **en lecture seule**. Tant qu'un fait n'est pas « CONFIRMÉ », il n'est pas utilisé par notre code.

Colonne « Pour » : **C** = nécessaire aux deux plugins C (frein, modes) ; **L** = seulement si on refait la table Lua `cc2x` (option A du plan) ; **les deux** = C et L.
Sources : `cc2x.c` / `world.c` / `lua_world.c` = dépôt du SDK, `src/` ; `frein.c` = `tour/atterrissage_manuel/frein/cc2x_frein.c` ; `modes.c` = `tour/etudes_modes_carburant/plugin/cc2x_modes.c`.

## H — Accroches (comment on se fait appeler à chaque pas du serveur)

| Id | Fait à vérifier | Source | Ce qu'il faut voir au désassembleur | Pour | Vu en jeu |
|---|---|---|---|---|---|
| H1 | Version du jeu : horodatage PE `0x6a36c177`, taille d'image `0x00af7000` | `cc2x.c:29, 828-829` | Lire l'en-tête du vrai exe | C, L | oui (le SDK s'active) |
| H2 | Case `0x00d34bc4` du fichier contient `0x00772fd0` (+ base) = serveur « init » | `cc2x.c:30-31, 851` | Lire la case ; vérifier que c'est bien la table virtuelle du serveur (constructeur qui l'installe, appelants) | C, L | oui |
| H3 | Case `0x00d34bc8` contient `0x0077ee10` = serveur « pas » (tick) | `cc2x.c:31, 852` | idem | C, L | oui |
| H4 | Case `0x00d34bcc` contient `0x0077eea0` = serveur « fin » | `cc2x.c:31, 853` | idem | C, L | oui |
| H5 | Les 3 fonctions sont `thiscall(this)` sans autre argument, retour vide, `ret` nu | `cc2x.c:380, 391, 404, 433` | Prologue/épilogue des 3 fonctions | C, L | oui |
| H6 | Aucun registre `xmm` n'est vivant à travers l'appel virtuel de la case +4 (le tick) | INFÉRÉ (ABI x86 : `xmm` à la charge de l'appelant) | Désassembler les sites qui font `call [reg+4]` sur cette table | C, L | non |
| H7 | Les 3 cases sont dans une section qu'on peut rendre écrivable (`VirtualProtect`) | `cc2x.c:284-291` | Section contenant `0x00d34bc4` (en-tête de sections) | C, L | oui |

## S — Le monde

| Id | Fait à vérifier | Source | Ce qu'il faut voir | Pour | Vu en jeu |
|---|---|---|---|---|---|
| S1 | `this` du tick est l'objet serveur ; la liste des véhicules est une file circulaire à `serveur+0x37c` : `data@+0, cap@+4, head@+8, count@+12`, éléments = pointeurs, élément i = `data[(head+i) mod cap]` | `world.c:57, 76-90` | Le code du jeu qui parcourt cette liste (ex. la fonction `0x005ee6a0` et ses appelants) | C, L | oui (les plugins voient les avions) |

## V — L'objet véhicule

| Id | Fait à vérifier | Décalage / type | Source | Pour | Vu en jeu |
|---|---|---|---|---|---|
| V01 | identifiant | `+0x80` u32, lecture | `world.c:58` | C, L | oui |
| V02 | type de châssis (définition) | `+0x84` u32 | `world.c:58` | C, L | oui (8 = avion, 0 = porte-avions…) |
| V03 | corps physiques : file circulaire, corps principal = élément 0 | `+0x8c` | `world.c:58, 117` | C, L | oui |
| V04 | roues : pointeur `+0xac`, nombre `+0xb0` (u32), taille d'une roue `0x70`, contact = float au début de chaque roue | `+0xac / +0xb0` | `world.c:58, 64, 141-142, 199-203` | C | oui (journal : 2/3, 3/3) |
| V05 | équipe | `+0x108` u32 | `world.c:58` | C, L | oui |
| V06 | rattaché à (id du porte-avions, 0 = aucun) | `+0x10c` u32 | `world.c:58` | C | oui |
| V07 | carburant | `+0x120` float | `world.c:59` | C (modes), L | oui |
| V08 | points de passage : file circulaire, nombre à `+0x140+12 = +0x14c` | `+0x140` | `world.c:59, 79-80, 143` | C (frein, lecture du nombre) | oui |
| V09 | état de vol (0 parqué, 1 sol, 2 vol) | `+0x170` u32 | `world.c:60` | C, L | oui (reste 2 pour un avion posé à la main) |
| V10 | état d'accostage (0 à 7) | `+0x174` u32 | `world.c:60` | C | oui |
| V11 | objet « équipe » : pointeur `+0x1a8` ; octet « est une équipe IA » à `équipe+0x19` | `+0x1a8` puis `+0x19` | `world.c:61, 64, 235-238` | C, L | oui |
| V12 | mode de contrôle (0 = ses points de passage, 3 = va vers une cible) | `+0x1d0` u32 | `world.c:61` | C | oui |
| V13 | puissance moteur commandée, **lecture et écriture** | `+0x1fc` float | `world.c:62, 191` | C (frein v5, `hold_idle`) | oui (le jeu ne la remet pas : 28/10) |
| V14 | roulage au sol (octet) | `+0x200` u8 | `world.c:62` | C (journal seulement) | oui |
| V15 | fonction virtuelle « est une voilure fixe » à `vtable+0x48` (`thiscall`, retour octet) | `vtable+0x48` | `world.c:63, 93-94, 241` | C, L | oui |
| V16 | fonction virtuelle « frein de roues » à `vtable+0x94`, `thiscall(this, float frein, float adhérence)` (**écrit dans le jeu**) | `vtable+0x94` | `world.c:63, 484-489` | C | oui (freinage mesuré 27/10) |
| V17 | vitesse commandée par le pilote automatique | `+0x1f8` float | `world.c:61` | L | oui (lu par `cc2_modes`) |

## B — Le corps physique (PhysX)

| Id | Fait à vérifier | Source | Pour | Vu en jeu |
|---|---|---|---|---|
| B1 | position du corps : 3 doubles à `corps+0x48` | `world.c:64, 246, 365` | C, L | oui |
| B2 | pointeur vers l'acteur PhysX à `corps+0xf0` ; son premier mot doit valoir l'adresse (rebasée) `0x00cdd478` | `world.c:64, 352-356` | C, L | oui |
| B3 | `0x00cdd478` est bien la table virtuelle d'un `NpRigidDynamic` (acteur dynamique) | `world.c:25, 49` | C, L | oui |
| B4 | acteur, `vtable+0x98` (indice 38) = « vitesse linéaire » : `thiscall(this, float sortie[3])` | `world.c:347-348, 366` | C (frein : vitesse relative ; modes : vitesse dans les journaux), L | oui |
| B5 | acteur, `vtable+0x48` (indice 18) = « pose » : `thiscall(this, PxTransform *sortie)`, `PxTransform = {float q[4]; float p[3]}` (sert à calculer le cap `yaw`) | `world.c:339, 347-348, 363` | L | oui (lu par `cc2_carte`) |

On **n'a pas besoin** de : la vitesse angulaire (indice 40), `body_set`, le lancer de rayon, `vehicle_gear`, `request_landing`, les 5 événements à crochet (waypoints, hangar, contrôleurs d'îles, apparitions, tick d'aérodrome). Moins de faits à vérifier et moins de code que dans le SDK.

## M — Plafond de gaz (`cc2x_modes.dll`)

| Id | Fait à vérifier | Source | Pour | Vu en jeu |
|---|---|---|---|---|
| M1 | `véhicule+0x314` (float) = commande de gaz bornée 0..1 (voisins `+0x308/0x30c/0x310` = tangage/roulis/lacet) | `modes.c:12-16, 38` | C | **oui** (28/10 : carburant = 0,304 × gaz ; plafond obéi) |
| M2 | VA `0x0071dbbf` = `F3 0F 11 87 14 03 00 00` (`movss [edi+0x314], xmm0`) : le plugin refuse de se charger sinon | `modes.c:39, 49, 245-249` | C | oui (le plugin s'est chargé) |

Correction de lecture par rapport à la demande : ce contrôle de 8 octets protège **le décalage `+0x314`** (« est-ce la bonne instruction ? »), il n'a rien à voir avec les registres `xmm`.

## G — Valeurs du jeu (pas des adresses)

| Id | Fait | Source | Vu en jeu |
|---|---|---|---|
| G1 | types de châssis : 0 porte-avions, 8 Albatros, 10 Manta | `frein.c:47`, `modes.c:44-46` ; énumération Lua `e_game_object_type` | oui |
| G2 | états de vol 0 / 1 / 2 | `cc2x.h:174` | oui |
| G3 | états d'accostage 0 à 7 | `cc2x.h:170-172` ; `library_enum.lua` (noté dans `JOURNAL_atterrissage.md`) | oui |
| G4 | seuil de contact de roue 0,01 (celui du jeu pour l'IA) | `frein.c:42` | à confirmer au désassembleur (optionnel) |

## L — Seulement si on refait la table Lua `cc2x` (option A du plan)

Îles (« tiles ») — pour `cc2x.tiles()` :

| Id | Fait | Source |
|---|---|---|
| L01 | liste des îles : file circulaire à `serveur+0x440` | `world.c:57` |
| L02 | île : identifiant `+0x00` (u32) | `world.c:66` |
| L03 | île : centre, 3 doubles à `+0x48` | `world.c:66` |
| L04 | île : équipe `+0x60` (u32) | `world.c:66` |
| L05 | île : pointeur de contrôleur `+0x100` (non nul = île chargée) | `world.c:66` |

Entrailles du Lua du jeu (Lua 5.3 compilé par le jeu, 32 bits) :

| Id | Fait | Source |
|---|---|---|
| LI01 | site de 8 octets à `0x004465ec` : `6A 20 89 85 64 FF FF FF` (`push 0x20 ; mov [ebp-0x9c], eax`), et `edi` y contient le `lua_State*` | `cc2x.c:31, 667-669` |
| LI02 | `index2addr` à `0x008cda70` (8 premiers octets `8B 41 14 85 D2 7E 0D C1`) | `cc2x.c:32, 36` |
| LI03 | `auxsetstr` à `0x008ce200` (`55 8B EC 83 EC 08 53 56`) | `cc2x.c:32, 37` |
| LI04 | `finishset` à `0x008ff6b0` (`55 8B EC 83 E4 F8 83 EC`) | `cc2x.c:32, 38` |
| LI05 | `luaS_new` à `0x00908220` (`55 8B EC 83 EC 08 53 8B`) | `cc2x.c:32, 39` |
| LI06 | `luaH_new` à `0x00904a50` (`56 8B 71 10 33 D2 6A 20`) | `cc2x.c:32, 40` |
| LI07 | `luaC_step` à `0x00904050` (`53 8B D9 56 57 8B 7B 10`) | `cc2x.c:32, 41` |
| LI08 | l'objet « nil » du jeu à `0x00d03518` | `cc2x.c:32` |
| LI09 | convention d'appel de ces 6 fonctions (registres `ecx`/`edx`, paramètres sur la pile, qui nettoie) | `cc2x.c:456-487` |
| LI10 | `lua_State` : sommet de pile `+0x0c`, état global `+0x10`, appel en cours `+0x14` ; le premier mot de l'appel en cours = pointeur vers la fonction appelée | `cc2x.c:446-448, 496, 502` |
| LI11 | valeur Lua = 16 octets (valeur 8, étiquette 4, remplissage 4) ; étiquettes : 0 nil, 1 booléen, 0x03 flottant, 0x13 entier, 0x16 fonction C légère, 0x44 chaîne courte, 0x54 chaîne longue, 0x45 table | `cc2x.c:445, 505-547` |
| LI12 | chaîne : étiquette `+4`, longueur courte `+7` (octet), longue `+12`, texte `+16` | `cc2x.c:529-531, 554` |
| LI13 | si `*(int*)(global+0x0c) > 0`, appeler `luaC_step` (sinon le ramasse-miettes ne passe pas) | `cc2x.c:489-491` |
| LI14 | registre à `global+0x28` ; sa table : taille `+8`, tableau `+0x0c` ; table des globales = élément d'indice 1 du tableau | `cc2x.c:656-660` |
| LI15 | une fonction C Lua est `int f(lua_State*)` en `cdecl`, rend le nombre de résultats | `cc2x.h:63`, `cc2x.c:542-547` |
| LI16 | le rappel doit rendre la pile Lua comme il l'a trouvée (le SDK la remet de force) | `cc2x.c:674-677` |

## Décompte

| Groupe | Faits | Nécessaires pour |
|---|---|---|
| H (accroches) | 7 | plugins C |
| S (monde) | 1 | plugins C |
| V (véhicule) | 17 (dont 1 seulement Lua) | plugins C : 16 |
| B (PhysX) | 5 (dont 1 seulement Lua) | plugins C : 4 |
| M (gaz) | 2 | plugin modes |
| **Total plugins C** | **30** | |
| G (valeurs du jeu, hors adresses) | 4 | plugins C |
| L (îles) | 5 | option A |
| LI (entrailles Lua) | 16 | option A |
| **Total supplémentaire option A** | **23** (V17 + B5 + L01-L05 + LI01-LI16) | |

Ordre de vérification proposé en P2 : H1 → H2-H7 → S1 → V (par décalage croissant) → B → M → G ; puis, **seulement si l'option A est retenue**, L et LI. Un fait « DIFFÉRENT » ou « NON TRANCHÉ » arrête le portage de ce qui en dépend et est remonté au moddeur.

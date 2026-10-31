# Conception d'une v12 de la reprise automatique : étude en lecture seule (30/10/2026)

Demandée par la session de coordination (phase 2, après `RAPPORT.md`). **Rien n'a été lancé, posé, compilé, écrit dans le jeu ni commité ; aucun code de plugin écrit ; le worktree de la v11 n'a pas été rouvert.** Exe lu : l'ancien exe d'origine (`1C9A01C3…`). Adresses = ancien exe ; dans la grande fonction `0x6fc7e0`-`0x701fa5` la session de portage donne un décalage de `+0x110` (déjà prouvé pour H4 : `0x6fe470` → `0x6fe580`), à revérifier pour chaque adresse hors de cette fonction.

Étiquettes : **MESURÉ** (journal de partie) · **LU** (désassemblage) · **INFÉRÉ** (déduit) · **INCONNU**. Aucun pourcentage de réussite.

## 0. En bref

1. **Question :** existe-t-il un moyen sûr de faire reprendre un avion arrêté par la prise en charge du jeu ? **Réponse :** il existe un moyen *plus sûr* que la v11, mais pas un moyen *sûr* au sens « on peut défaire ». Le plus simple est de **ne pas passer par l'engagement du tout** : sauter du site de H4 (`0x6fe470`) directement dans le test de toucher du jeu (`0x6ff20a`), qui exécute lui-même le bloc de prise en charge. C'est la conception (b), **un seul crochet**.
2. **LU, point central :** le bloc de prise en charge (`0x6ff368`-`0x6ffa4b`) refait **tout** ce que l'engagement fait côté avion, baie, ancre et messages (attache, occupant de baie, ancre physique, événements, `DOCK_STATE`). L'engagement n'apporte en plus que l'état de piste 4, la vitesse d'engagement `[g+0xd0]` et la copie du repère `[g+0xd8…]`, qui ne servent **qu'à l'état 4**. Les états 5, 6, 7 ne les lisent pas.
3. **Conception (a)** (forcer les portes B et C) : **trois crochets de plus que H4**, plus une soupape avant ; elle fait passer le jeu par l'état 4, jamais vu pour un avion arrêté, et le rappel de baie du même tick ferait **deux** ancres physiques (la première détruite alors qu'elle est inscrite dans une liste du monde). 🔴.
4. **Conception (b)** : 🟡. Pas d'état 4, pas de rappel de baie fautif (l'occupant n'est pas encore posé), pas de double ancre. **Soupape avant la capture : naturelle** (on arrête de forcer ; le jeu abandonne proprement, comme mesuré 3 fois). **Soupape arrière après la capture : il n'y en a pas de sûre** ; mais après la capture l'état suit le chemin normal de l'IA (5 → 6 → 7 → 0), qui se termine tout seul.
5. **Mesures :** trois lectures en suffisent pour décider si (b) vaut la peine (baies, champs des roues, premier nœud du chemin). Les mesures sur les portes (M1, M4, M7) ne servent que pour (a).
6. **Recommandation :** voir §6. En deux mots : **ne pas tester la v11 ; ne pas faire (a) ; (b) seulement après les trois lectures, sur partie jetable, en acceptant que la capture est un pas sans retour.**

---

## 1. L'état minimal : ce que fait l'engagement, ce que lit la suite

Notation : `g` = gestionnaire (`[ebp-0x204]`), `plane` = avion (`[ebp-0x1fc]`), `ship` = navire (`[ebp-0x200]`), `BAY` = `ship+0x154 + [g+0x6c]×0x70` (case de baie de 0x70 octets : +0x00-0x5f matrice de l'ancre, +0x60 objet ancre/joint, +0x64 occupant, +0x68 type), `ctx` = `[ebp-0x21c]` (objet d'événements), `cont` = `[ebp-0x268]` (conteneur monde, liste en `+0x48`), `obs` = `[ebp-0x22c]` (liste d'observateurs).

### 1.1 Les écritures de l'engagement, dans l'ordre (de `0x6fe55b` à `0x6febbb`)

Toutes **LU**. Une fois les portes A à E passées :

| # | Adresse | Écriture / appel | Remarque |
|---|---|---|---|
| E0 | `0x6fe55b`-`0x6fe638` | **avant** les portes : un point (position monde du premier corps de l'avion, 3 doubles) ajouté à la liste `[g+0x24]` (grossit par `0x8629d0` si pleine) | transitoire : la liste est vidée à chaque début de tick (`0x6fc880`-`0x6fc8ac`) |
| E1 | `0x6fe7a2` | porte D : appel virtuel `(id navire, id avion)` | côtés INCONNUS ; supposé sans écriture |
| E2 | `0x6fe7b8`, `0x6fe7c3` | `0x5ec1e0(navire ; classe 1 ; avion+0x188)` puis **`[g+0x6c] = baie`** | porte E = `baie < [navire.modèle+0xec]` |
| E3 | `0x6fe7e1` | **`[g+0x1c] = 4`** | |
| E4 | `0x6fe7f9` | `avion.frein(0 ; 1,0)` (appel virtuel `+0x94`) | |
| E5 | `0x6fe823`-`0x6fe869` | **`avion+0x10c = id navire`** (ATTACHED_TO) ; `0x854870(avion+0x140)` (vide l'instantané de réplication) ; `0x5eb340(avion)` (vide des tampons `+0x25c…0x278`, octet `+0x224 = 0`, `+0x227 = 1`) ; `ctx.vtable[0](id avion, avion+0x230, avion+0x140, avion+0x150)` | c'est l'**inline** de `0x5ec9f0(avion ; ctx ; id)` ; la fonction `0x5ec9f0` appelée avec 0 fait le **détachement** (voir §3) |
| E6 | `0x6fe86b`-`0x6fe87f` | `avion+0x114 = 0`, `+0x118 = 0`, `+0x11c = −1` | |
| E7 | `0x6fe889` | **`avion.octet[+0x188] = baie`** | |
| E8 | `0x6fe8b4`-`0x6fe8cc` | locaux seulement : matrice d'un élément du **modèle de l'avion** (`0x40fb60`), composée avec la pose de l'avion dans le repère du navire `[ebp-0x78]` (`0x40ffa0`) → `[ebp-0xd8]` = repère de l'ancre | |
| E9 | `0x6fe8e6`-`0x6fe8eb` | **`BAY+0x64 = id avion`** (occupant) | |
| E10 | `0x6fe8ee`-`0x6fe96e` | **`BAY+0x00…0x5f` = repère de l'ancre** | |
| E11 | `0x6fe973`-`0x6fe9d9` | si `BAY+0x60` existe et `[ancre+8] ≠ 0` : matrice copiée dans `[ancre+0x18…0x77]` ; appel virtuel `[ancre+8]→vtable[+0x1c](0, 0x4e4a90())` | pose le corps physique de l'ancre |
| E12 | `0x6fe9f6` | **`0x5e7760(BAY ; navire ; avion)`** : détruit l'ancien objet `BAY+0x60` (`vtable[0](1)`), **crée** un joint (`new 0xf0`, constructeur `0x5d52d0`, paramètres dont `+0xe4 = 14,0`), `BAY+0x60 = nouveau` | **l'ancien objet n'est pas retiré de la liste du monde** par cette fonction (voir E13 et §3) |
| E13 | `0x6fea0a`-`0x6fea7c` | **`cont.liste(+0x48).push_back(BAY+0x60)`** puis `ancre.vtable[+4]()` | inscription du joint dans le monde |
| E14 | `0x6fea9e` | `ctx.vtable[+0x20](id navire ; baie ; id avion)` | événement « avion dans la baie » |
| E15 | `0x6feab5` | **`avion+0x174 = 1`** (DOCK_STATE) | |
| E16 | `0x6feac4`-`0x6feb0a` | pour chaque élément de `obs` : `0x566390(élément→[+0x64] ; id avion ; id navire)` | avertit les observateurs (interface) |
| E17 | `0x6feb12`-`0x6feb59` | si `[g+0xc0] ≠ 0` : libère `[g+0xbc]` et le remet à 0 ; `[g+0xc4] = 0`, `[g+0xc8] = 0` ; **`[g+0xd0] = |Q−P|`** (vitesse relative d'engagement) | |
| E18 | `0x6feb65`-`0x6febae` | `[g+0xcc] = 0` ; **`[g+0xd8…0x137]` = pose de l'avion dans le repère du navire** (`[ebp-0x78…-0x19]`) | repère d'atterrissage |
| E19 | `0x6febbb` | retour en `0x6fe47d` | suite normale ; l'état vaut 4 : pas d'abandon |

Sorties : `g` reçoit `+0x1c`, `+0x6c`, `+0xbc…0xc8`, `+0xcc`, `+0xd0`, `+0xd8…0x137` ; l'avion reçoit `+0x10c`, `+0x114…0x11c`, `+0x174`, `+0x188` et le frein ; la baie reçoit `+0x00…0x5f`, `+0x60`, `+0x64` ; le monde reçoit le joint (liste `cont+0x48`) ; trois événements (E5, E14, E16).

### 1.2 Ce que le bloc de prise en charge fait (`0x6ff368`-`0x6ffa4b`)

Le même ensemble (E2 sans la porte D, E4, E5, E6, E7, E8, E9, E10, E11, E12, E13, E14, E16 : `0x6ff374`…`0x6ff6ff`, **LU**) avec ces différences :

| Écriture propre à la prise en charge | Adresse |
|---|---|
| `avion+0x1fc = 0` (puissance) | `0x6ff3b4` |
| `avion+0x174 = 6` (DOCK_STATE taxi), `avion+0x170 = 1` (FLIGHT_STATE sol) au lieu de `DOCK_STATE = 1` | `0x6ff66c`, `0x6ff676` |
| drapeau `+0xc0 = 0` sur chaque équipement de l'avion (`+0x15c`) | `0x6ff69d` |
| `[g+0x1c] = 5` au lieu de 4 | `0x6ff70d` |
| `[g+0xbc…]` vidé, `[g+0xcc] = [g+0xd0] = 0` | `0x6ff714`-`0x6ff761` |
| **chemin sur rails** : recherche de `runway_reverse_a` (`0x5a2770`), un **segment** de 0x7c octets poussé dans `[g+0xbc]` (`0x8444a0`) : matrice de départ = pose de l'avion, position d'arrivée = premier nœud du chemin (64 octets copiés), longueur en `+0x78` | `0x6ff7bd`-`0x6ffa4b` |

**Conséquence (LU)** : le bloc de prise en charge est un **sur-ensemble** de l'engagement pour tout ce qui touche l'avion, la baie, l'ancre et les événements. Il n'y a **rien à « préparer comme le fait l'engagement »** : ni `[g+0x1c] = 4`, ni `[g+0xd0]`, ni le repère `[g+0xd8…]`. Un seul point d'attention : le bloc suppose **la baie encore libre** (occupant 0) quand il appelle `0x5ec1e0` (voir §2.2).
**Corollaire (INFÉRÉ)** : engagement **et** prise en charge dans le même tick ⇒ `0x5e7760` appelé deux fois pour la même baie ⇒ le premier joint est détruit alors qu'il a été inscrit dans `cont+0x48` (E13) et que rien ne le retire (le départ du jeu retire explicitement avant de détruire, §3) ⇒ pointeur pendant dans une liste du monde. Je ne sais pas si cette liste est consommée au tick suivant (INCONNU).

### 1.3 Ce que l'état 5 (puis 6, 7) lit

LU (`0x70066c`, `0x7007de`-`0x7008f1`, `0x7008f6`, `0x700a26`) :
- **Gestionnaire** : `[g+0xbc]`, `[g+0xc0]`, `[g+0xc4]` (le vecteur de segments), `[g+0xcc]` (fraction), `[g+0xd0]` (vitesse), **`[g+0x6c]`** (indice de baie), `[g+0x58]` (propriétaire de l'ascenseur, état 6 → 7).
- **Navire** : `[navire+0x154]` (tableau de baies), `[navire+0x88]` (modèle), `[navire+0xc68]` (état de l'ascenseur, INFÉRÉ ; état 6 → 7 exige `> −0,5`).
- **Baie** : `BAY+0x60` (l'objet ancre, il faut `[ancre+8] ≠ 0`, `0x700895`). L'état 5 **écrit** la pose de l'ancre chaque tick (`0x700826`-`0x7008f1`) : c'est elle qui tire l'avion par le joint.
- **L'avion n'est lu nulle part.** Si le joint n'est pas bien accroché au corps de l'avion, l'état 5-7 se déroule quand même (la pose de l'ancre avance), et l'avion suit ou non.
- **Pas lus** dans la fonction : `[g+0xd8…0x137]`, `[g+0x130]` (lus seulement à l'état 4, `0x70000c`, `0x7000fc`), `[g+0xd0]` comme vitesse d'engagement (l'état 5 le réutilise comme vitesse de rampe, remis à 0 à la capture).

### 1.4 Ce que le jeu fait à l'avion « normal » (rappel, utile pour (a))

Pour l'IA, la prise en charge n'a pas lieu en `0x6ff368` mais en fin d'état 4 : `0x7003a8`-`0x700667` (progression > 0,99 de la pose d'engagement vers le nœud B) : frein (0 ; 1,0), puissance 0, `[g+0x1c] = 5`, `DOCK_STATE = 6`, `FLIGHT_STATE = 1`, drapeaux équipements 0, `[g+0xbc]` vidé, chemin `runway_reverse_a`, premier segment (puis `jmp 0x6ff97c`, le même code que `0x6ff97c` du bloc de prise en charge). **Sans** rappel de baie, **sans** nouvel appel de `0x5e7760` (le joint de l'engagement est gardé).

---

## 2. Les deux conceptions

Notes communes :
- **Garde-fous des crochets existants (v11)** à garder : un seul avion signalé (`mine == [ebp-0x1fc]`), état de piste 3 (`[g+0x1c] == 3`), budget, fenêtre unique, enveloppeur xmm, octets attendus vérifiés ; H1/H2 (le don de la piste par le jeu) restent **nécessaires** : sans état 3 pour l'avion, aucun de ces sites n'est atteint.
- Aucun site proposé n'a d'opérande absolue ni relative dans les octets déplacés (vérifié ligne à ligne ci-dessous), à une exception signalée pour (a).
- Les crochets ne modifient **que** des registres et `eflags` (comme H1, H2, H4) ; aucun n'écrit dans la mémoire du gestionnaire.

### 2.1 Conception (b) : sauter dans le test de toucher du jeu (recommandée)

**Idée.** Remplacer H4 par **H5** : même site `0x6fe470` (7 octets `c6 85 fb fd ff ff 01`, vérifiés par la v11 : rien ne saute dans les octets 2 à 7, ni opérande absolue), mais au lieu de rejouer le chemin 200-400 m, **sauter en `0x6ff20a`**. Ce point est la cible du `je` du contrôle d'abandon (`0x6ff0eb` et `0x6ff0f5`) : le jeu y va déjà quand « pas d'échec, ou état 4 ». Il fait alors lui-même : vitesse relative ≤ 10 (`0x6ff263`), frein progressif de l'IA (`0x6ff2e5`), test des roues (`0x6ff320`), et **si le test passe** le bloc de prise en charge. Si le test échoue : `je 0x6ffa5c`, rien ne se passe ce tick, nouvel essai au tick suivant.

**Registres et cases lus / écrits par H5 (LU).**

| Élément | Lu | Écrit | Pourquoi |
|---|---|---|---|
| `[ebp-0x1fc]` | oui | non | identifier l'avion signalé (comme H4) |
| `[ebp-0x204]` | oui | non | gestionnaire : vérifier `[g+0x1c] == 3`, propriétaire `[g+0x5c] == id` |
| `[ebp-0x200]` | oui | non | navire |
| `cpu->edi` | oui | **oui** (`= [ebp-0x204]`) | au site, `edi` = l'avion ; le bloc `0x6ff368` suppose `edi` = gestionnaire |
| `cpu->esi` | non | **oui** (`= [ebp-0x200]`) | le bloc suppose `esi` = navire (chemin « avion sans roue » `0x6ff35a` : jamais rechargé) |
| `cpu->jump_to` | non | **oui** (`= 0x6ff20a`) | |
| `[ebp-0x205]` | non | non | `0x6ff23a` l'écrit lui-même |
| `[ebp-0x2e4,-0x234,-0x23c]` (P), `[ebp-0x2dc,-0x2d4,-0x2a4]` (Q), `[ebp-0x254]` (progression), `[ebp-0x78…]` (pose) | lus par le jeu | non | **LU** : ils sont posés au début de l'état 3 (`0x6fde15`-`0x6fe0c0`) et je n'ai trouvé aucune écriture de ces cases entre `0x6fe477` et `0x6ff20a` sur le chemin normal (balayage fait) ; l'abandon seul écrit `[ebp-0x234]`, mais il ne mène pas à `0x6ff20a` |
| pile | | | même profondeur qu'en `0x6fe470` : les seuls `push` du chemin normal vers `0x6ff20a` (`push 0xff ; push 1 ; call 0x5ec1e0`, `0x6ff0be`-`0x6ff0da`) sont équilibrés par `ret 8` (**LU**) |

**Ce que le jeu fait ensuite (LU).** Si le test passe : bloc `0x6ff368` (§1.2). Si la baie préférée (`avion+0x188`) est libre, `0x5ec1e0` la renvoie ; sinon une autre libre ; sinon −1 (alors `[g+0x6c] = −1`, bloc sauté, **état 3 conservé** : pas de corruption comme en (a), car je n'ai trouvé aucune lecture de `[g+0x6c]` dans le code de l'état 3 avant qu'il soit réécrit (LU, balayage des lignes `0x6fdde5`-`0x6ff368`), et l'abandon le remet de toute façon à −1).

**Ce qui est sauté** (et pourquoi ce n'est pas gênant, LU) : les portes A à E, l'état 4, `[g+0xd0]`, le repère `[g+0xd8…]`, le contrôle d'abandon (y compris la limite de 3600), l'écriture de la puissance 0 par contact (`0x6feeee`) et les cibles de pilotage automatique (`0x6fed86`…). Conséquences : (i) l'avion ne reçoit plus la « puissance 0 si une roue touche » du jeu : **le plugin continue à la mettre à 0** comme en v10 (MESURÉ : `power_read=0.00` pendant 1420 s) ; (ii) la limite de 3600 ticks n'existe plus : c'est **le délai de la fenêtre du plugin** (`force_timeout_s`, 20 s) qui la remplace.

**Précontrôles en lecture seule à ajouter dans le crochet (propositions).** `[g+0x1c] == 3`, `[g+0x5c] == id`, `[g+0x58] == −1` (ascenseur libre), `[navire+0xc68] > −0,5` (ascenseur prêt, INFÉRÉ), la baie préférée `[navire+0x154 + avion.octet[+0x188]×0x70 + 0x64] == 0` (libre), vitesse relative < 0,5 m/s et 3/3 roues en contact (déjà dans le plugin). Si l'un échoue : ne pas sauter (le jeu abandonne comme avant).

**Ce qui peut mal tourner.**

| Risque | Niveau | Détail |
|---|---|---|
| **Joint jamais vu avec un avion arrêté, frein tenu** | 🟡 | Le jeu met frein (0 ; 1,0) une fois à la capture ; le plugin lâche tout dès que `ATTACHED_TO ≠ 0` (v11, `release()`), donc plus de frein tenu. Comportement de l'ancre sur un avion immobile : INCONNU. La capture d'un avion de l'IA se fait aussi à vitesse relative très faible (MESURÉ v5 : `rel` 0,2 à 0,3 en `dock=1`/`dock=6`) ; c'est un indice, pas une preuve. |
| **Premier segment : ligne droite jusqu'au premier nœud de `runway_reverse_a`** | 🟡 | Position du nœud INCONNUE (mesure M2-b). Si l'avion est à plusieurs dizaines de mètres, il est tiré en ligne droite sur le pont à ≤ 2,5 m/s : obstacles (autres avions, tour) INCONNUS. |
| **Frein progressif de l'IA pendant la fenêtre** | 🟡 | `0x6ff2e5` réécrit chaque tick `frein = clamp(2p(p−0,5), 0, 1)` et adhérence `2p+1` (p = progression 0-1) **tant que le test de toucher échoue** : pour p ≈ 0,5 le frein tombe presque à 0 à chaque tick, puis le plugin remet 1,0 au sien (ordre des deux inconnu). Un avion à vitesse relative 0,1 m/s peut ramper. À journaliser (`rel`). |
| **Fenêtre qui s'éternise** | 🟢 | Le plugin arrête de sauter après `force_timeout_s` ou si l'avion bouge (v11) : le tick suivant le jeu abandonne **proprement** (zone finale, état ≠ 4, `0x6ff0f1` : puissance 1,0 un tick, `DOCK_STATE = 5`, piste et baie libérées, MESURÉ ×3). |
| **Pas de baie libre** | 🟢 | Précontrôle ; sinon le bloc est sauté (voir ci-dessus). |
| **Ascenseur indisponible** | 🟡 | L'état 6 attend en bout de chemin (immobile, `dock=6`) : c'est la règle de l'IA. Pas de soupape arrière (§3). |
| **Code jamais exécuté dans ce contexte** | 🟡 | Le bloc `0x6ff368` n'est atteint par le jeu que si le toucher passe dans le tick même d'un engagement (hélicoptères ?) : on ne sait pas s'il a déjà tourné en vraie partie (INCONNU). |

**Niveau global : 🟡.**

**Ce qu'on journaliserait (lecture seule).** À chaque saut de H5 : tick, id, distance au milieu (`[ebp-0x25c]`, non encore recalculée au site : celle de `0x6fe0a5`), `[g+0x1c]`, `[g+0xd4]`, `avion+0x188`, occupant de cette baie, `[g+0x58]`, `[navire+0xc68]`. Une sonde lecture seule en `0x6ff379` (9 octets `89 47 6c 8b 8e 88 00 00 00`, sans opérande absolue) : `eax` = baie renvoyée par le rappel (LU, oui/non −1). Puis le suivi de piste existant (`RUNWAY state`) étendu à **5, 6, 7**, `[g+0x6c]`, `BAY+0x64`, `BAY+0x60 ≠ 0`. Critère de succès à écrire : **`dock = 6` et `flight = 1` et `RUNWAY state 5`** (pas `attached ≠ 0`). Verdicts possibles : « le test de toucher n'a jamais passé en N ticks » ; « capturé à t = … » ; « abandon du jeu ».

### 2.2 Conception (a) : forcer le passage des portes B et C (déconseillée)

**Idée.** Garder H4 (entrée en `0x6fe55b`), et faire passer l'engagement par des crochets qui rendent « vrai » ce que l'avion arrêté ne remplit pas.

**Crochets nécessaires (tous sans opérande absolue ni relative dans les octets déplacés, vérifiés sur le désassemblage).**

| Rôle | Site (ancien exe) | Octets | Action |
|---|---|---|---|
| **HB** porte B | `0x6fe6ae` : `movss [ebp-0x294], xmm1` | `f3 0f 11 8d 6c fd ff ff` | effacer `CF` et `ZF` dans `eflags` pour que le `jbe` de `0x6fe6b6` ne soit pas pris (l'instruction déplacée ne change pas les drapeaux ; même technique que H2). |
| **HC** porte C | `0x6fe76f` : `mulss xmm2, [ebp-0x244]` | `f3 0f 59 95 bc fd ff ff` | `jump_to = 0x6fe788` (après le `jbe` de `0x6fe782`) : saute le produit scalaire, le `comiss` et le `jbe`. Le seul résultat utile déjà écrit est `[ebp-0x224] = |Q−P|` (`0x6fe767`). Pas de site sûr à placer **sur** le `comiss` (opérande absolue `0xdb73f8` dans ses 7 octets). |
| **HT** (indispensable) | `0x6ff20a` : `movss xmm2, [ebp-0x2e4]` | `f3 0f 10 95 1c fd ff ff` | pendant le tick d'engagement : `jump_to = 0x6ffa5c`, pour **empêcher la prise en charge du même tick** (rappel de baie fautif + double joint, §1.2). |
| **HV** soupape avant | `0x700393` : `movss xmm0, [ebp-0x24c]` | `f3 0f 10 85 b4 fd ff ff` | en état 4, quand le plugin le décide : `jump_to = 0x7003a8` (début de la fin de l'état 4, saute `comiss 0,99` et le `jbe`). |
| H4 inchangé | `0x6fe470` | | |

**Ce qui peut mal tourner.**

| Risque | Niveau |
|---|---|
| Les portes B et C sont des tests de **physique d'approche** ; les forcer fait entrer le jeu dans un code (engagement, puis état 4) qu'il n'a jamais exécuté pour un avion immobile : vitesse d'engagement `[g+0xd0] = |Q−P|` ≈ 0,1 à 0,2 ; l'état 4 fait avancer l'ancre à `[g+0xd0] × (1 − progression)` ; INFÉRÉ : l'avance est quasi nulle, la progression 0,99 n'est jamais atteinte sans HV. | 🔴 |
| **Même tick** : si HT manque ou échoue, le test de toucher passe et le bloc de prise en charge **rappelle `0x5ec1e0`** avec la baie que l'avion vient d'occuper : autre baie ou −1 ; −1 ⇒ `[g+0x6c] = −1` écrit (`0x6ff379`) ⇒ l'état 4 écrit à `navire+0x154 − 0x70`. Avec une deuxième baie : **deux** appels à `0x5e7760`, premier joint détruit alors qu'il est dans `cont+0x48`. | 🔴 |
| Cinq crochets dans la même fonction, dont deux qui court-circuitent des comparaisons flottantes ; pile et xmm identiques d'un site à l'autre à vérifier un par un. | 🟡 |
| ATTACHED_TO est écrit dès l'engagement (E5) ; le plugin lâche alors frein et maintien (v11). Entre l'engagement et HV l'avion n'est tenu que par l'ancre. | 🟡 |
| HV est la seule sortie ; il faut que `[g+0x6c]` soit valide et que la prise en charge de fin d'état 4 (`0x7003a8`) se déroule : elle utilise les cases locales de l'état 4 du **même tick** (`[ebp-0x2b0]`, `[ebp-0x2a0]`, `[ebp-0x290]`, etc., calculées à chaque tick par `0x6ffdbc`-`0x700393`) ⇒ HV ne peut agir **que dans un tick où l'état 4 vient de tourner** (il le fait). | 🟡 |

**Niveau global : 🔴.** Journalisation : les sondes A/B/C/D/E existantes ; `RUNWAY state 4` ; `[g+0xd0]` ; `ATTACHED_TO`, `DOCK_STATE`, `BAY+0x64`, `[g+0x6c]` à chaque tick ; la ligne de HV.

### 2.3 Comparaison

| | (a) forcer B et C | (b) sauter dans le test de toucher |
|---|---|---|
| Crochets nouveaux (en plus de H1, H2, H3, sondes) | 4 (HB, HC, HT, HV) + H4 | 1 (H5, qui remplace H4) |
| Code du jeu parcouru qui n'a jamais vu un avion arrêté | engagement, état 4 pour vitesse ≈ 0, fin d'état 4 | test de toucher + bloc de prise en charge |
| Passages par une baie occupée / double joint | possible (§1.2) si HT échoue | non |
| Soupape avant | HV (en état 4, après coup) | **aucune écriture nécessaire** : on cesse de sauter |
| Où l'avion est « attaché » avant la fin | oui (dès l'engagement) | non (attaché à la capture) |
| Niveau | 🔴 | 🟡 |

---

## 3. La soupape : peut-on débloquer ou défaire ?

### 3.1 Avant tout engagement (état 3)

**Sûre, sans aucune écriture : arrêter de forcer.** Le tick suivant le jeu applique son abandon normal (`0x6ff0f1`-`0x6ff205`) parce que l'octet de zone vaut 1 et que l'état n'est pas 4 : `DOCK_STATE = 5`, `FLIGHT_STATE = 2`, `[g+0x5c] = −1`, `[g+0x6c] = −1`, avion remis dans la file, puissance 1,0 **un tick**, train « rentré ». Aucun occupant de baie n'a été posé en (b) avant la capture. MESURÉ : 1 abandon (v9), 2 abandons (v10), aucun mouvement.

### 3.2 Un état 4 coincé (conception (a) seulement)

**Soupape avant (HV)** : voir §2.2. Elle ne défait pas, elle **achève** : l'avion passe à l'état 5 par le code du jeu. Elle suppose l'état 4 sain (`[g+0x6c]` valide).

### 3.3 Défaire une avion déjà engagé ou capturé (soupape arrière)

**LU : le jeu possède sa propre séquence d'annulation**, dans le code de départ (`0x6fd6c0`-`0x6fd7ac`, répétée en `0x6fd49f` et `0x6fd1cf`) :

1. `0x5e8660(BAY ; cont)` : retire l'objet ancre de la liste du monde (`0x4e95e0`) ;
2. `0x5e8630(BAY)` : désactive le joint (`0x4e7430`), le détruit (`vtable[0](1)`), `BAY+0x60 = 0` ;
3. `BAY+0x64 = 0` (baie libre) ;
4. `0x5ec9f0(avion ; ctx ; 0)` : `ATTACHED_TO = 0` (sans événement de réplication quand l'id est 0) ;
5. `avion+0x114 = 0`, `+0x118 = 0`, `+0x11c = −1` ;
6. `ctx.vtable[+0x20](id navire ; baie ; 0)` : événement « baie libérée » ;
7. pour chaque observateur : `0x566390(…→[+0x64] ; id avion ; 0)`.

Puis le gestionnaire doit être remis : `[g+0x1c] = 0`, `[g+0x5c] = −1`, `[g+0x6c] = −1`, `[g+0xbc…]` vidé, `[g+0xcc] = [g+0xd0] = 0` ; l'avion : `DOCK_STATE`, `FLIGHT_STATE` (à 5/2 comme l'abandon, ou 0/2), `avion+0x188` restauré à sa valeur d'avant. (Le jeu enchaîne, après l'étape 7, le **lancement** de l'avion par `0x6fd7b8`…, qu'on ne veut pas : on ne peut donc pas simplement « sauter dans le départ ».)

**Peut-on le faire sans le jeu ?**
- **Par écritures brutes depuis le plugin (champs seulement)** : on remet bien `g`, la baie, `avion+0x10c`, `+0x174`, `+0x170`, `+0x188`, mais on **laisse** : le joint vivant et inscrit dans `cont+0x48` (le prochain `0x5e7760` sur cette baie le détruirait sans le retirer : pointeur pendant), les événements de réplication non défaits, les observateurs non avertis, un avion encore physiquement lié à l'ancre. **🔴 : non sûr. Je le déconseille.** Et l'API du SDK déclare `ATTACHED_TO` en lecture seule.
- **En appelant les fonctions du jeu** (`0x5e8660`, `0x5e8630`, `0x5ec9f0`…) : elles sont petites et d'appel simple (`ecx` = objet, 0 à 2 arguments sur la pile, `ret n`), mais il faut `cont` et `ctx`, qu'on ne possède que **dans le cadre de la grande fonction** (arguments 1 et 5 de `0x6fc7e0`, copiés en `[ebp-0x268]` et `[ebp-0x21c]` aux adresses `0x6fc833` et `0x6fc84e`). Les appeler depuis un crochet de cette fonction est possible en principe, mais c'est du code de plugin qui appelle l'intérieur du jeu avec des pointeurs lus dans une pile : **🔴, à ne pas faire pour un premier essai.**
- **En laissant le jeu s'en charger** : en état 5, 6, 7 l'annulation n'existe pas (`0x6fc4e0` refuse). La fin normale (état 7 → 0, échange `[g+0x5c] ↔ [g+0x58]`, descente de l'ascenseur, `DOCK_STATE = 4`) est **bornée** : chaque état finit quand son chemin finit ; seule attente possible : l'ascenseur (état 6, §1.3), qui est la même pour l'IA.

**Verdict sur la soupape.**
- (b) : soupape avant **naturelle et sûre** (on cesse de sauter) ; après la capture **pas de retour en arrière**, mais **pas d'état permanent** non plus (états 5-7 bornés, ascenseur excepté). Je considère que le critère « on peut débloquer » est **rempli pour (b)**, au sens où il n'y a pas de situation où la piste reste réservée indéfiniment sans qu'une action du plugin ou du jeu y mette fin, **sauf** si l'ascenseur ne devient jamais disponible (INCONNU, même risque que pour l'IA).
- (a) : soupape avant HV existe, soupape arrière non. **« Sans soupape, on ne teste pas » s'applique à (a)** : HV n'est pas une vraie soupape (elle dépend de l'état 4 sain).
- **Dans les deux cas** : l'essai doit se faire sur partie jetable, car la capture ne se défait pas proprement.

---

## 4. Mesures en lecture seule : lesquelles tranchent, dans quel ordre

Rappel des 7 mesures du `RAPPORT.md` (M1 valeurs des portes, M2 nœuds et chemin, M3 déroulé d'un atterrissage de l'IA, M4 vitesse relative et direction, M5 baies, M6 champs des roues, M7 porte D) et **trois nouvelles** (M8 à M10).

| Ordre | Mesure | Pour (a) | Pour (b) | Ce qu'elle tranche |
|---|---|---|---|---|
| **1** | **M5 baies** : nombre (`[navire+0x158]`), occupant (`+0x64`) de chaque baie, `avion+0x188` de l'avion posé, occupant de cette baie | utile | **décisive** | si la baie préférée de l'avion est libre : le bloc de prise en charge ne tombe pas sur −1. Si elle est occupée et qu'aucune autre n'est libre, (b) est inutile. |
| **2** | **M6 champs des roues** : valeur de `roue[+0]` et `roue[+4]` (`avion+0xac`, pas 0x70) pour l'avion posé | utile | **décisive** | si le test de toucher du jeu passera (`+4 ≤ 0,1`). Sinon (b) ne peut rien faire sans court-circuiter le test (variante `0x6ff346` avec `dl = 1`, qu'on évite). |
| **3** | **M2-b : premier nœud de `runway_reverse_a`** (résultat de `0x5a2770` : tableau de 64 octets par élément, flottants en `+0x34` +0x38 +0x3c de l'élément) et distance de l'avion à ce point | non | **décisive** | par où l'avion sera tiré (ligne droite) et sur quelle longueur ; peut dire « non » si la ligne coupe le pont de façon dangereuse. |
| 4 | **M3 (version complète)** : déroulé tick par tick d'un atterrissage de l'IA, y compris `[g+0x1c]`, `[g+0x6c]`, `BAY+0x64`, `BAY+0x60`, `[g+0x58]`, `[navire+0xc68]`, `[g+0xd0]` | utile | utile | durée de 5 → 7, ascenseur, à quoi ressemble la réussite ; ne décide pas entre (a) et (b). |
| 5 | **M8 (nouvelle) : le frein écrit par le jeu en `0x6ff2e5`** : lire, pour l'avion posé, la valeur de la progression (`[ebp-0x254]`) | non | utile | pour savoir si le frein progressif de l'IA désserre l'avion pendant la fenêtre. |
| 6 | **M9 (nouvelle) : l'avion tenu pendant H1/H2 : `[g+0xd4]`, `[g+0x1c]`, `[g+0x5c]`** | utile | utile | déjà dans le suivi de piste de la v11 (lecture). |
| (a) seulement | M1, M4, M7 | **décisives pour (a)** | inutiles | M1 dit de combien B et C échouent ; M7 dit si D passe. Inutile d'y passer si on renonce à (a). |
| — | **M10 (nouvelle) : le joint** : valeurs de `[BAY+0x60]+0xe4` et voisins après une capture d'un avion de l'IA | non | informatif | donne l'ordre de grandeur de la raideur du joint (14,0 en `+0xe4`, LU `0x5e7c72`) ; ne se mesure que sur un atterrissage normal. |

**Ce qui dit si ça vaut la peine** : M5 + M6 + M2-b. Si l'un des trois est négatif, **ne pas faire (b)**. Les autres mesures améliorent la surveillance mais ne changent pas la décision.

---

## 5. Les points que je n'ai pas pu fermer (INCONNU)

1. La porte D (objet `contexte+4`, méthode `vtable[+4]`).
2. Si la liste `cont+0x48` est consommée et vidée au tick suivant (donc si un pointeur pendant y est dangereux).
3. Le comportement physique du joint avec un avion immobile aux roues libres.
4. La position du premier nœud de `runway_reverse_a` et les obstacles sur la ligne droite du premier segment.
5. Le sens exact de `[navire+0xc68]` (ascenseur) et le délai de l'état 6.
6. Si le bloc de prise en charge `0x6ff368` a déjà tourné dans une vraie partie.
7. Le sens du 2e champ des roues.
8. L'ordre d'exécution du tick du plugin et du tick du gestionnaire (qui écrit le frein en dernier).

---

## 6. Recommandation franche

1. **Ne pas tester la v11 telle quelle** (déjà l'avis de la coordination) : ses portes B et C ne peuvent pas passer pour un avion arrêté (LU), et si elles passaient, le même tick écraserait `[g+0x6c]` ou doublerait le joint, sans soupape.
2. **Abandonner (a).** Quatre crochets de plus, un code jamais vu (état 4 à vitesse nulle), deux scénarios 🔴, et une « soupape » qui n'en est pas une.
3. **(b) est le seul candidat raisonnable : un crochet H5 qui remplace H4** (même site, même garde-fous, mêmes 7 octets), plus un suivi de piste étendu aux états 5-7 et un critère de succès `dock = 6 / flight = 1`. Niveau 🟡. **À condition** que les trois lectures M5, M6, M2-b soient favorables, qu'on teste sur **partie jetable**, et que le moddeur accepte que **la capture est un pas sans retour** (comme chaque atterrissage de l'IA).
4. **« Ne pas faire » reste une réponse valable** : si le moddeur veut seulement ravitailler, le repli « toucher et repartir, puis ordre de retour en vol » (PLAN §13) est déjà observé sans problème ; il ne demande aucun crochet.
5. **Ce que je ne recommande pas** : une soupape par écritures brutes dans le gestionnaire ou la baie (🔴), ou un appel des fonctions de départ du jeu depuis le plugin (🔴).

---

## 7. Adresses nouvelles de cette étude (ancien exe ; la session de portage ajoute `+0x110` dans `0x6fc7e0`-`0x701fa5`, à vérifier ailleurs)

| Adresse | Ce que c'est (étiquette) |
|---|---|
| `0x6fe470` (7 o) | site de H4 / H5 (LU) |
| `0x6ff20a` | début du test de toucher : cible du `je` d'abandon ; **cible de H5** (LU) |
| `0x6ff346`-`0x6ff360` | rechargement de `edi`, `esi`, `eax` avant la porte du toucher (LU) |
| `0x6ff36f` (5 o `8b ce 50 6a 01`), `0x6ff374`, `0x6ff379` (9 o `89 47 6c 8b 8e 88 00 00 00`) | rappel de baie de la prise en charge ; sonde lecture seule possible en `0x6ff379` (LU) |
| `0x6fe6ae` (8 o), `0x6fe76f` (8 o), `0x6fe788` | sites HB / HC et cible de HC (conception (a)) (LU) |
| `0x700393` (8 o), `0x7003a2`, `0x7003a8` | site HV et cible (fin de l'état 4) (LU) |
| `0x6ffa5c` | cible de HT, queue commune (LU) |
| `0x5ec9f0` | `SetAttachedTo(avion ; ctx ; id)` ; inline en `0x6fe823` et `0x6ff3d4` (LU) |
| `0x5e7760` | création du joint de baie (LU) ; détruit l'ancien objet `BAY+0x60` |
| `0x5e8660`, `0x5e8630` | retrait de l'ancre de la liste du monde ; désactivation + destruction du joint (LU) |
| `0x4e95e0`, `0x4e7430` | retrait d'un élément de la liste `cont+0x48` ; désactivation du joint (LU ; sens INFÉRÉ) |
| `0x854870`, `0x5eb340` | remise à zéro de l'instantané de réplication de l'avion (LU) |
| `0x566390` | avertissement d'un observateur (LU ; sens INFÉRÉ) |
| `0x6fd49f`-`0x6fd4d0`, `0x6fd6c0`-`0x6fd7ac`, `0x6fd1cf`-`0x6fd200` | séquence d'annulation du jeu au départ (LU) |
| `0x6f82c0`, `0x6f86c0`, `0x8444a0`, `0x5a2770` | interpolation sur un segment ; construction d'un chemin nommé ; ajout d'un segment ; recherche de chemin nommé (LU ; sens INFÉRÉ) |
| `0xd22570`, `0xd22584`, `0xd22598` | chaînes `runway_reverse_a`, `lift_top_reverse`, `load_lift_lower` (LU) |
| `0x70000c`, `0x7000fc` | seules lectures de `[g+0x130]`/`[g+0xd8]` dans la fonction (état 4) (LU) |

*Rien n'a été commité. Fichiers de travail : dossier temporaire de la session.*

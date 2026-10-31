# Étude (lecture seule) : que se passe-t-il après l'engagement, pour un avion déjà posé et arrêté ?

Date : 30/10/2026. Auteur : session « atterrissage-apres-engagement » (lancée par la session de coordination).
**Rien n'a été lancé, posé, compilé ni modifié.** Seul ce fichier est écrit. Exe lu : `tour/sauvegardes/carrier_command_1.5.18_original.exe` (sha256 `1c9a01c3007cb2be…c341026`, vérifié : c'est bien `1C9A01C3…`). Outils : `capstone` avec `python -I -B` ; un petit désassembleur maison dans le dossier temporaire de la session (pas dans le dépôt). Adresses = image de l'**ancien** exe (PE `0x6a36c177`).

Étiquettes : **MESURÉ** = vu dans un journal de partie (relu ici) · **LU** = lu dans le désassemblage · **INFÉRÉ** = déduit, pas prouvé · **INCONNU** = je ne sais pas, je ne l'ai pas trouvé. **Aucun pourcentage de réussite** dans ce rapport (les anciens se sont tous trompés).

> Ordre de travail respecté : les parties 1 à 3 ont été écrites **avant** d'ouvrir `RISQUES_v11.md`, `PROCEDURE_partie_v11.md`, `PLAN §14` et `cc2x_frein.c` de la v11. La comparaison est dans la partie 4.

---

## 0. Carte du code (pour se repérer)

Tout est dans **une seule grande fonction** : le « tick du gestionnaire de piste » du porte-avions, `0x6fc7e0` (8 arguments, appelée une fois par tick depuis `0x705f75`, le gestionnaire est le composant en `navire+0xd08`). Variables de la pile que j'utilise (**LU**, relues par les écritures et lectures) :

| Pile / registre | Sens (LU) |
|---|---|
| `[ebp-0x204]` (`edi` en général) | le **gestionnaire** `g` : `[g+0]` mode (0 repos, 1 accostage, 2 départ), `[g+0x1c]` **état de piste** (3 approche, 4 engagé, 5/6/7 recul sur rails, 0 libre), `[g+0x5c]` **avion qui possède la piste**, `[g+0x58]` avion qui possède l'ascenseur, `[g+0x6c]` baie choisie, `[g+0x84]`/`[g+0x88]` indices des deux **nœuds de piste A et B**, `[g+0xd4]` compteur d'approche, `[g+0xbc…]` liste des segments du chemin sur rails |
| `[ebp-0x200]` | le **navire** (`+0x88` = son modèle, `+0x154` = tableau des baies de 0x70 octets, `+0x158` = nombre de baies) |
| `[ebp-0x1fc]` | l'**avion** (`+0x80` id, `+0x174` DOCK_STATE, `+0x170` FLIGHT_STATE, `+0x1fc` puissance, `+0x10c` ATTACHED_TO, `+0x188` octet « numéro de baie », `+0xac/+0xb0` roues : 0x70 octets chacune, `+0x1d0` mode de contrôle) |
| `R` = `[ebp-0x2cc]`, `[ebp-0x270]`, `[ebp-0x278]` (x, y, z) | **position de l'avion dans le repère du navire** (calculée en `0x6fdf03`-`0x6fdf3b`) ; **après `0x6fef46`** ces trois cases deviennent **l'écart de l'avion au nœud B** (c'est ce que la sonde H3 de la v10 lisait) |
| `[ebp-0x214…0x20c]` | position du **nœud A** (indice `[g+0x84]`) ; `[ebp-0x2bc…0x2b4]` = position du **nœud B** (indice `[g+0x88]`) (LU `0x6fe00e`-`0x6fe054`) |
| `[ebp-0x25c]` | distance restante **au milieu de la piste** = `(zA+zB)/2 − R.z` (LU `0x6fe0a5`) |
| `[ebp-0x254]` | progression `clamp((R.z−zA)/(zB−zA), 0, 1)` (LU `0x6fe02a`-`0x6fe0c0`) |
| `P`=`[ebp-0x2e4,-0x234,-0x23c]`, `Q`=`[ebp-0x2dc,-0x2d4,-0x2a4]` | vitesses (navire, avion) rapportées au repère du navire ; `Q−P` = **vitesse relative** (INFÉRÉ par usage : la norme est comparée à 10 en `0x6ff263`) |
| `[ebp-0x205]` | octet « **zone finale** » (devient la base de l'indicateur d'échec) |

Table de saut des états de piste : `0x701fa8` (état 3 → `0x6fdde5`, **état 4 → `0x6ffdbc`**, 5 → `0x70066c`, 6 → `0x7008f6`, 7 → `0x700a26`). **LU** (octets lus dans l'exe). L'état 4 a donc **son propre code**, distinct de l'état 3.

---

## 1. Réponses aux quatre questions (avion posé et arrêté sur le pont)

Rappel de ce qui est déjà établi (LU, v10) : le jeu n'évalue l'engagement que si `200 ≤ [ebp-0x25c] < 400` (`0x6fe45f`/`0x6fe54a`) ; sous 200 m il met l'octet de zone à 1 (`0x6fe470`) et saute l'évaluation ; l'indicateur d'échec reprend cet octet, donc l'avion est abandonné (`0x6ff0f1`) sauf si l'état de piste est déjà 4. Le crochet H4 (v11) saute en `0x6fe55b` pour que le jeu évalue quand même l'engagement.

### (a) Les portes A à E : qui teste quoi, passent-elles pour un avion immobile au sol ?

Elles sont dans `0x6fe55b`-`0x6fe7cc`. Elles regardent toutes la **géométrie de l'avion par rapport au nœud A** ; aucune ne regarde la vitesse sol, aucune ne regarde le cap de l'avion. (**LU**)

| Porte | Adresse du test | Ce qu'elle exige (LU) | Pour l'avion arrêté sur le pont |
|---|---|---|---|
| **A** | `0x6fe666` (`jbe 0x6febda`) | longueur du vecteur `V = nœud A − avion` **> 0** | passe (l'avion n'est pas posé pile sur le nœud A) |
| **B** | `0x6fe6ab` (`jbe 0x6febda`) | `V.y / |V| < −0,08` (constante `0xdb7bfc`) : l'avion doit être **au-dessus** du nœud A d'au moins 8 % de la distance (pente de descente d'au moins ~4,6°) | **échoue très probablement** (voir ci-dessous) |
| **C** | `0x6fe77b` (`jbe 0x6febe7`) | produit scalaire de `V` normalisé et de la **vitesse relative** normalisée **> 0,95** (cône de 18°) : l'avion doit **se déplacer vers le nœud A** | **échoue** : vitesse relative ≈ 0 |
| **D** | `0x6fe7a2` (`test al,al ; je 0x6febe7`) | un appel virtuel `contexte→[+4]→vtable[+4](id navire, id avion)` doit renvoyer vrai | **INCONNU** (je n'ai pas identifié l'objet ; vu le nom des arguments, plutôt un contrôle « cet avion peut-il se poser sur ce navire ») |
| **E** | `0x6fe7cc` (`jae 0x6febc0`) | l'indice de baie renvoyé par `0x5ec1e0` est `< [navire.modèle+0xec]` (une baie libre existe) | passe (MESURÉ v10 : `bay=8` libre) |

**Pourquoi B échoue (INFÉRÉ à partir de LU + MESURÉ)** :
- LU : la porte B est un test de **pente de descente**, pas un test latéral. (Le PLAN §11 l'avait décrite comme « composante latérale normalisée > −0,08 » : c'est faux, c'est la composante **verticale** `y`, et le sens est « < −0,08 ».) Ce qui confirme que c'est la pente : l'IA vise, en `0x6fecfa`, une hauteur de `(distance−40) × 0,14` au-dessus de la piste (pente 0,14), donc un avion de l'IA en approche donne `V.y/|V|` ≈ −0,14, bien en dessous de −0,08.
- MESURÉ (journal v10 `cc2x_2026-10-30_092608_frein_v10.log`, ligne 9962, 09:41:22.993, relue ici ; même chose en ligne 10530 : −0,5 / 1,7 / −94,3) : `bay=8 fail=1 zone=1 x=-0.6 y=1.7 z=-95.2 counter=1`, avec `wheels=3/3 (min 0.05)`, `rel` 0,0-0,2 m/s, `dist=12`, `dy=22.1` juste avant. Ces `x,y,z` sont l'écart de l'avion au **nœud B** (la sonde H3 lit `[ebp-0x2cc]`, `[ebp-0x270]`, `[ebp-0x278]` **après** la soustraction de `0x6fef0d`-`0x6fef46`), pas les quantités que les portes A à C comparent : l'avion est ~0,6 m à côté, **~1,7 m au-dessus** du niveau du nœud B (niveau des roues sur le pont) et 95 m avant lui. `counter=1` : l'abandon a lieu au **premier** tick de l'état 3.
- INFÉRÉ : si le nœud A est au même niveau que B (probable : ce sont deux nœuds de piste sur le pont), `V.y ≈ −1,7 m`. Pour passer la porte B il faudrait `1,7 / |V| > 0,08`, soit `|V| < ~21 m` : **l'avion devrait être arrêté à moins de ~21 m du nœud A**. La position du nœud A (et la longueur A→B) est **INCONNUE** : elle vient des données du navire, pas de l'exe. Si l'avion est arrêté plus loin (cas des essais : 95 m avant B), la porte B échoue.

**Pourquoi C échoue (LU + INFÉRÉ)** : `V` est normalisé après un test de longueur (`0x6fe666`), mais la **vitesse relative n'est pas testée avant d'être divisée par sa propre longueur** (`0x6fe721`-`0x6fe77b`, pas de test). Vitesse relative exactement 0 ⇒ 0/0 ⇒ NaN ⇒ `comiss` « non ordonné » ⇒ le saut `jbe` est pris ⇒ **échec**. Avec le petit bruit mesuré (MESURÉ : `rel` = 0,0 à 0,2 m/s pendant le maintien), la direction de cette vitesse est quelconque ; elle ne passe que si elle tombe par hasard dans les 18° autour de la direction du nœud A. Même si B passait, C ne serait donc pas fiable pour un avion immobile.

**Que se passe-t-il quand une porte échoue (LU)** :
- A ou B : retombée en `0x6febda` → `jmp 0x6fe477` (suite normale du code, **sans** repasser par `0x6fe470`).
- C ou D : retombée en `0x6febe7` → `jmp 0x6fe47d`.
- E : retombée en `0x6febc0` → met l'octet de zone à 1 → `jmp 0x6fe47d` (abandon **immédiat** quelle que soit la distance).
- Dans les cas A à D, l'engagement est **réessayé à chaque tick** tant que l'avion est entre 200 et 400 m du milieu ; le compteur `[g+0xd4]` monte d'un par tick (`0x6fdde5`) et, au-delà de **3600** (`0x6ff0c5`), l'indicateur d'échec passe à 1. **Avec le crochet H4**, l'octet de zone est déjà à 1 (le crochet l'écrit lui-même, comme le jeu), donc **une porte qui échoue ⇒ abandon au même tick**, exactement comme sans crochet : le crochet ne change rien si une porte échoue. **LU.**
- L'abandon (`0x6ff0f1`-`0x6ff205`) : frein (0 ; 1,0), puissance = **1,0**, train rentré (appel virtuel `+0x98` avec l'argument 0 ; « train » = sens INFÉRÉ par symétrie avec l'appel `+0x98` avec 1 sous 800 m, `0x6fe44f`), `DOCK_STATE = 5`, `FLIGHT_STATE = 2`, drapeau `+0xc0 = 1` sur les équipements, avion remis en queue de file avec l'état de circuit 3, `[g+0x5c] = −1` et `[g+0x6c] = −1` (piste et baie libérées). **LU.** (C'est ce que la v9 et la v10 ont mesuré : une seule lecture de puissance 1,00.)

### (b) Le calcul du repère d'atterrissage accepte-t-il cette position ?

**LU : il n'y a pas de test de position à cet endroit.** Ce que le jeu appelle « repère d'atterrissage » est juste une **copie de la pose de l'avion dans le repère du navire** (la matrice 3×4 en `[ebp-0x78…-0x18]`, recopiée dans `[g+0xd8…0x128]` en `0x6feb61`-`0x6febae`), plus une **ancre de baie** placée sur cette même pose :
- `0x6fe8b4`-`0x6fe96e` : la matrice de l'avion composée avec celle d'un élément de 0xb4 octets du modèle du navire est écrite dans la case de baie (`navire+0x154 + indice×0x70`, 0x60 octets de matrice) et dans l'objet physique `bay+0x60` (appel virtuel `+0x1c`) ;
- `0x6fe8e6`-`0x6fe8eb` : `baie.occupant (+0x64) = id de l'avion` ; `0x6fe889` : `avion.[+0x188] = indice de baie` ;
- `0x6fe823` : `avion.[+0x10c] = id du navire` (c'est l'**ATTACHED_TO** du SDK) puis appels `0x854870`, `0x5eb340` et un message aux clients (`ctx.vtable[0]`) ; `0x6feab5` : `DOCK_STATE = 1` ; `0x6fe7e1` : `[g+0x1c] = 4` ; frein (0 ; 1,0) en `0x6fe7f9`.
- `0x6feb59` : `[g+0xd0]` = la **longueur de la vitesse relative** (`[ebp-0x224]`) au moment de l'engagement.

Donc, si les portes A à E sont passées, la pose de l'avion est acceptée telle quelle (INFÉRÉ : aucune autre condition lue dans ce bloc). Les seules conditions de position sont les portes (a).

### (c) Le test de toucher des roues se déclenche-t-il pour un avion déjà au sol ?

**Oui, il passerait ; mais il n'est atteint que dans un cas.** (LU `0x6ff20a`-`0x6ff362`)
- Test : `|Q−P| ≤ 10 m/s` (`0x6ff263`) **et**, pour **chaque** roue, `roue[+0] ≥ 0,01` et `roue[+4] ≤ 0,1` (`0x6ff320`-`0x6ff344`, constantes `0xdb71a0` et `0xdb71f8`) ; s'il n'y a aucune roue, seule la vitesse compte. Avion arrêté : MESURÉ (v10) `wheels=3/3 (min 0.05)`, `rel` 0,0-0,2 ⇒ le test **passerait**.
- Mais ce code (`0x6ff20a`) n'est exécuté que si on a franchi le contrôle d'abandon (`0x6ff0e4` : pas d'échec, **ou** `[g+0x1c] == 4` en `0x6ff0f1`). Pour l'avion posé sans engagement, l'indicateur de zone est à 1 ⇒ abandon avant d'arriver au test. **Le test de toucher n'a jamais été atteint dans les essais v9/v10** (cohérent avec : 4 sondes silencieuses).
- Si le test **échoue** : `je 0x6ffa5c` (`0x6ff362`) : rien ne se passe ce tick, nouvel essai au tick suivant tant que l'état reste celui-ci. Le test n'a **pas** de notion « vient de toucher » (pas de détection de transition vol→sol) : un avion déjà au sol le passe comme un autre. (LU)
- Si le test **passe** (même tick que l'engagement, état 4) : bloc de prise en charge `0x6ff368` (voir (d)) **avec un problème de baie, décrit en (d)**.
- Après l'engagement, aux ticks **suivants**, l'état est 4 et c'est le code `0x6ffdbc` qui tourne : **il ne refait pas le test de toucher** (LU : aucune lecture des roues ni de la vitesse relative dans `0x6ffdbc`-`0x70066b`). Il fait glisser l'ancre vers le nœud 0x88 à une vitesse proportionnelle à `[g+0xd0] × (1 − progression)` (`0x700102`-`0x70013d`) ; la prise en charge (`0x7003a8`) n'a lieu que quand une seconde progression (de la pose d'engagement vers le nœud B) dépasse **0,99**.
  - **INFÉRÉ** : pour un avion arrêté, `[g+0xd0]` ≈ 0 (c'est la vitesse relative au moment de l'engagement) ⇒ l'ancre n'avance pas ⇒ la progression reste ≈ 0 ⇒ **l'état 4 ne se termine jamais** sans le passage par le bloc `0x6ff368` du même tick.

### (d) Le « recul sur les rails » : qui le commande, avec quelles conditions, qu'est-ce qui s'y oppose ?

**Qui le commande (LU)** : le **gestionnaire de piste lui-même**, pas l'avion. Après la prise en charge (`0x6ff368`-`0x6ffa4b` ou `0x7003a8`-`0x700667`) le gestionnaire passe en état 5, puis 6, puis 7 :
- Prise en charge : `puissance = 0` (`0x6ff3b4`), frein (0 ; 1,0) (`0x6ff3a8`), `DOCK_STATE = 6` (`0x6ff66c`), `FLIGHT_STATE = 1` (`0x6ff676`), flag équipements `+0xc0 = 0` (`0x6ff69d`), message aux clients (`ctx.vtable[+0x20]`), `[g+0x1c] = 5` (`0x6ff70d`), `[g+0xcc] = [g+0xd0] = 0`.
- Le chemin : le jeu cherche dans le modèle du navire le chemin nommé **`runway_reverse_a`** (chaîne en `0xd22570`, recherche `0x5a2770` en `0x6ff7bd`) et crée **un premier segment** de la pose actuelle de l'avion jusqu'au premier nœud de ce chemin (`0x6ff7f6`-`0x6ffa4b`, longueur rangée en `segment+0x78`).
- **État 5** (`0x70066c`) : chaque tick la vitesse vaut `min(2,5 ; vitesse+0,05 ; distance restante du segment)` (constantes `0xdb76c8`, `0xdb71d0`), la fraction avancée est `vitesse / (longueur × 30)` ; **c'est le jeu qui écrit la pose de l'ancre de baie** (`0x700809`-`0x7008f1`) : l'avion est **tiré par l'ancre**, pas conduit par ses roues. Quand il reste moins de 0,1 m : état 6.
- **État 6** (`0x7008f6`) : suit le chemin `runway_reverse_a` (le vrai recul). Fin de chemin : il faut `[navire+0xc68] > −0,5` **et** `[g+0x58] == −1` (ascenseur libre) pour passer à l'état 7 ; sinon l'avion **attend au bout du chemin** (retombée `0x7007de`). Sens de `[navire+0xc68]` : INFÉRÉ = position de l'ascenseur (comparé à −8,99 ailleurs).
- **État 7** (`0x700a26`) : chemin `lift_top_reverse` (chaîne `0xd22584`) ; à la fin : `[g+0x1c] = 0`, **échange** `[g+0x5c] ↔ [g+0x58]` (la piste est libérée, l'ascenseur est possédé : `0x700adf`-`0x700af1`), chemin suivant `load_lif…` (chaîne `0xd22598`), puis le code commun `0x6ffa5c`-`0x6ffdb7` descend l'avion et finit par `FLIGHT_STATE = 0`, `DOCK_STATE = 4` (rangé) en `0x6ffd7c`/`0x6ffdad`.

**Conditions (LU)** : prise en charge faite ; pour que l'état 6 finisse : ascenseur prêt et libre. **Rien dans l'état 5/6/7 ne regarde le frein, la puissance ni le mode de contrôle de l'avion** : le jeu n'agit que sur l'ancre.

**Ce qui s'oppose (INFÉRÉ, à partir de LU)** :
1. **Le frein et le moteur tenus par notre plugin.** Le jeu met frein = 0 / adhérence = 1 **une seule fois**, à la prise en charge (`0x6ff3a8`) ; il ne le réécrit pas ensuite. Si le plugin continue d'écrire frein 1,0 à chaque tick, les roues restent bloquées pendant que l'ancre tire. Je ne sais pas si l'ancre est assez raide pour entraîner un avion aux roues bloquées sans le faire bondir ou lâcher : **INCONNU**.
2. **Le premier segment est une ligne droite** de la pose actuelle au premier nœud de `runway_reverse_a` (position du nœud : **INCONNU**). Un avion arrêté loin de ce point sera tiré en ligne droite sur le pont (à ≤ 2,5 m/s) ; obstacles éventuels : **INCONNU**.
3. **L'ascenseur** (état 6 → 7) : s'il est occupé ou en bas, l'avion attend en bout de chemin.
4. **Un avion qui n'est plus « le propriétaire de la piste »** n'est pas suivi : tout le code d'état est exécuté pour l'avion `[g+0x5c]` seulement (`0x6fdd9b`).

**Problème de baie dans le même tick (LU, conséquence INFÉRÉE)** : au tick de l'engagement, le jeu a déjà écrit `baie.occupant = avion` et `avion.[+0x188] = baie` (partie (b)). Puis, si le test de toucher passe dans ce même tick, le bloc `0x6ff368` rappelle `0x5ec1e0(navire, 1, avion.[+0x188])`. Or `0x5ec1e0` renvoie l'indice préféré **seulement si cette baie est libre** (`[baie+0x64] == 0`, `0x5ec204`) ; sinon il scanne et renvoie la **première autre baie libre**, ou **−1**. La baie vient d'être prise par cet avion lui-même ⇒ le rappel renvoie une **autre** baie, ou −1 s'il n'y en a pas d'autre. Conséquences :
- −1 (ou toute valeur `≥` nombre de baies) : `[g+0x6c]` est **déjà écrasé par −1** (`0x6ff379`) avant le test `jae 0x6ffa5c` ; le bloc est sauté ; au tick suivant l'état 4 calcule `baie = navire+0x154 + [g+0x6c]×0x70` (`0x700226`, `0x70024d`) avec `[g+0x6c] = −1` ⇒ écritures de ~0x60 octets **juste avant le tableau des baies** ⇒ **corruption mémoire possible** (INFÉRÉ, jamais vu ; plantage ou comportement erratique).
- une autre baie libre : l'avion aurait deux baies (l'ancienne reste « occupée » par lui) : fuite de réservation.
Le jeu ne fait jamais ça pour un avion de l'IA (il y arrive par l'état 4 et `0x7003a8`, qui ne rappelle pas `0x5ec1e0`). **Je n'ai pas trouvé** de code qui libère `baie.occupant` en dehors du cycle complet.

---

## 2. Ce qui se passe, tick par tick, avec le crochet H4 (synthèse)

Avion arrêté à ~95 m avant le nœud B, rappelé (`dock=5`), piste donnée par H1/H2 (état 3), crochet H4 qui entre en `0x6fe55b` :

1. Porte A passe. **Porte B échoue** (si le nœud A est à plus de ~21 m, INFÉRÉ) ⇒ `0x6febda`. L'octet de zone est à 1 ⇒ `0x6ff0f1` : état ≠ 4 ⇒ **abandon** (mêmes effets que la v10 : une lecture de puissance 1,00, `DOCK_STATE=5`, `FLIGHT_STATE=2`, piste et baie libérées, avion remis en file).
2. Si, par chance de géométrie, B passait : **porte C échoue** (vitesse relative ≈ 0 ou bruit) ⇒ `0x6febe7` ⇒ même abandon.
3. Si A, B, C, D, E passaient tous dans un même tick (cas qui n'a **aucune raison** de se produire pour un avion arrêté) : engagement validé (état 4, ATTACHED_TO, DOCK_STATE=1, baie occupée), puis test de toucher **dans le même tick** ⇒ bloc `0x6ff368` ⇒ **rappel de `0x5ec1e0` : problème de baie ci-dessus** ⇒ au mieux une deuxième baie réservée puis prise en charge, au pire `[g+0x6c] = −1` et corruption.
4. Aucun autre chemin vers la prise en charge n'a été trouvé.

---

## 3. Question de sécurité : qu'est-ce qui libère la piste et la baie si l'engagement passe mais la prise en charge ne suit pas ?

Étudié sur l'état 4 (engagé, pas de prise en charge). **LU** sauf mention. Inventaire des écritures `[reg+0x5c] = −1` (piste libre) dans tout l'exe : `0x6fc54f`, `0x6fd5bf`, `0x6fd866`, `0x6ff1f7`, `0x700bff`, `0x700e1c` (+2 hors de cette zone). Celles qui concernent notre cas :

| Libération | Où | Condition | Vaut pour l'état 4 ? |
|---|---|---|---|
| Abandon d'approche | `0x6ff1f7` (+ `[g+0x6c] = −1`) | état 3 seulement : `cmp [g+0x1c],4 ; je 0x6ff20a` (`0x6ff0f1`) **l'ignore en état 4** | **Non** |
| Annulation externe `0x6fc4e0` (appelée par le virtuel `0x7078e0`, qui se range dans une table à ~`0xd59750`) | `0x6fc54f` + `[g+0x1c] = 0` | l'avion est le propriétaire et l'état vaut **0 ou 3** ; refuse (`jne 0x6fc6f9`) en état 4 à 7, et si l'avion possède l'ascenseur (`[g+0x54]`/`[g+0x58]`) ; remet l'avion à `DOCK_STATE=0`, `FLIGHT_STATE=2`, mais **ne libère pas** `baie.occupant` | **Non** |
| L'avion n'existe plus | `0x6fdd9b` → `0x700bff` : `[g+0x5c] = −1` (sans toucher à `[g+0x1c]`) | `0x5ee6a0([g+0x5c])` renvoie 0 (avion détruit / retiré) | **Oui, mais seulement si l'avion disparaît** |
| Fin de cycle normale | `0x700adf`-`0x700af1` (échange avec `[g+0x58]`) | l'avion a fini l'état 7 | Oui, mais c'est la prise en charge complète |
| Mode repos `0x700e0a` | remet `[g+0x54]`, `[g+0x58]`, `[g+0x5c]`, `[g+0x60]` à −1 à chaque tick | `[g] == 0`, qui n'arrive (`0x700e02`) que si **tout est déjà libre** et la file vide | **Non** |

Compteurs / délais : le seul compteur est `[g+0xd4]` (incrémenté en `0x6fdde5`, testé contre 3600 en `0x6ff0c5`), et il n'existe **que dans le code de l'état 3**. **Dans le code de l'état 4 (`0x6ffdbc`-`0x70066b`) je n'ai trouvé ni délai, ni compteur, ni annulation.** (LU : j'ai relu toute la plage.)

**Réponse** : *INFÉRÉ à partir de LU* — si l'engagement passe (état 4) et que la prise en charge ne suit pas (avion immobile : `[g+0xd0] ≈ 0`, l'ancre n'avance pas), **rien ne libère la piste ni la baie** : ni délai, ni annulation (l'annulation externe refuse en état 4), ni abandon. L'état 4 reste. Seules sorties : l'avion est détruit / retiré (alors `[g+0x5c] = −1`, mais `[g+0x1c]` reste 4 et la baie reste marquée occupée par un id mort), ou on quitte la partie. La baie 8 resterait « occupée » (`[baie+0x64]` = id de l'avion). **Aucun mécanisme de secours trouvé.**
Autres effets d'un avion coincé en état 4 (LU) : l'avion est **attaché** (`ATTACHED_TO` = navire), `DOCK_STATE = 1`, frein posé en (0 ; 1,0), et le jeu continue de réécrire sa pose sur l'ancre chaque tick.

**Contraste utile** : tant que l'engagement échoue (état 3), le seul coût est l'abandon propre du jeu (piste et baie libérées au même tick). Le danger n'existe que si **l'engagement réussit sans prise en charge** ; c'est précisément ce que la v11 cherche à obtenir.

---

## 4. Comparaison avec la v11 (fichiers non commités de `musing-nobel-a0872c`, lus APRÈS les parties 1 à 3)

Fichiers lus (lecture seule, rien modifié) : `frein/RISQUES_v11.md`, `PROCEDURE_partie_v11.md`, `PLAN_prise_en_charge.md` §14 (diff), `frein/cc2x_frein.c` (v11 : H4 lignes 408-437, `release()`, `idle_end()`, logique d'éligibilité et de fenêtre lignes ~496-681). Je n'ai **pas** relu les tests ni compilé.

### Accords (ma lecture du code confirme la leur)
1. Le site `0x6fe470` (7 octets `c6 85 fb fd ff ff 01`), `edi` = avion, `[ebp-0x1fc]` = avion, `[ebp-0x204]` = gestionnaire, `[ebp-0x25c]` = distance au milieu : identiques à ma lecture.
2. Les points de chute des portes : A/B → `0x6febda` → `0x6fe477` ; C/D → `0x6febe7` → `0x6fe47d` ; E → `0x6febc0` qui met l'octet de zone à 1. Identiques.
3. Le succès pose l'état 4 (`0x6fe7e1`), `frein(0,1)` (`0x6fe7f9`), `DOCK_STATE=1` (`0x6feab5`), copie le repère (`0x6feb61`-`0x6febae`) et retourne en `0x6fe47d` ; ensuite pas d'abandon si l'état vaut 4 (`0x6ff0f1`). Identique.
4. Le test de toucher : vitesse relative ≤ 10 ; par roue, 1er champ ≥ 0,01 et 2e champ ≤ 0,1 (`0x6ff320`). Identique (le sens du 2e champ reste non identifié chez moi aussi).
5. Choix de faire écrire `[ebp-0x205] = 1` par H4 : correct. Sans cette écriture une porte A à D qui échoue aurait été rejouée à chaque tick jusqu'à 3600 (confirmé par ma lecture de `0x6ff0c5`). Et le garde « état de piste = 3 » est sans danger (l'état 4 a son propre code, ce site n'y est pas atteignable).
6. Leur tableau de risques reconnaît « la piste et la baie 8 restent réservées » si l'engagement passe sans prise en charge : même conclusion que ma partie 3.
7. Un abandon coûte « un tick de poussée 1,0 et de frein 0 » : confirmé (`0x6ff11b`-`0x6ff124`).

### Désaccords (ce que ma lecture contredit ou précise)

**D1. Les portes « devraient passer ».** v11 (RISQUES « INFÉRÉ, jamais vu », PLAN §12 et §14) : les portes A à E devraient passer pour un avion arrêté, vu les écarts −0,6 m latéral et +1,7 m vertical.
Ma lecture : ces écarts (sonde H3) sont ceux au **nœud B** après soustraction ; les portes comparent autre chose. La porte **B** est un test de **pente de descente** (`V.y/|V| < −0,08` : l'avion doit être au-dessus du nœud A d'au moins 8 % de la distance). La porte **C** exige que la **vitesse relative** pointe vers le nœud A à 18° près (impossible à vitesse nulle : 0/0 = NaN = échec). Un avion posé sur le pont, ~95 m avant B, **échoue très probablement en B**, et en C si sa vitesse relative est nulle. Le PLAN §11 décrivait B comme « composante latérale > −0,08 » : c'est la composante **verticale**, avec le sens « < −0,08 ». Étiquette : LU (`0x6fe5af`-`0x6fe6b6`, `0x6fe721`-`0x6fe782`) + INFÉRÉ (position du nœud A inconnue).

**D2. `attached_to` n'est pas un marqueur de prise en charge.** v11 : après `COMMIT:` sans prise en charge, « l'avion reste tenu, `dock=1` **sans `attached_to`** » ; alerte (e) « `dock=1` sans `attached_to` pendant plus de 3 s » ; règle « **ne pas alerter si `attached_to` ≠ 0** (prise en charge réussie) ».
Ma lecture : le jeu écrit `ATTACHED_TO` (`avion+0x10c`, offset confirmé par `world.c` du SDK : `v_attached = 0x10c`) **dès l'engagement** (`0x6fe823`), dans le même tick que `[g+0x1c]=4` et `DOCK_STATE=1`. Après un engagement on a donc `dock=1` **et** `attached ≠ 0` ensemble. **MESURÉ** sur un atterrissage de l'IA, journal v5 `cc2x_2026-10-28_084728_frein_v5_partie2.log` lignes 5207, 5277, 5278 : `dock=1 attached=1` avec `wheels=0/3` puis `1/3` (avion encore en l'air ou qui touche à peine) ; ligne 5357 : `flight=1 dock=6 attached=1 power=0.00` (prise en charge). Conséquences : (i) l'alerte (e) « sans attached_to » **ne se déclenchera jamais** ; (ii) la règle « ne pas alerter si attached ≠ 0 » **masquerait** un avion coincé en état 4 ; (iii) le critère de succès doit être **`dock=6` et `flight=1`** (et `RUNWAY state 5`), pas `attached ≠ 0`. Étiquette : LU + MESURÉ.

**D3. Le plugin lâche l'avion à l'engagement.** v11 : l'avion « reste tenu (frein + moteur 0) » si l'engagement passe sans prise en charge.
Ma lecture du code v11 (`cc2x_frein.c` lignes ~511, 520, 538, 676-679) : `base` et `recall` exigent `!attached` ; dès que le jeu écrit `ATTACHED_TO`, `eligible || hold` devient faux et le plugin appelle `release()` : `vehicle_brakes(0, 1)` puis `idle_end` (« le jeu prend la main : on ne remet pas la puissance »). Le plugin **lâche donc le frein et le maintien au moment de l'engagement**, pas à la prise en charge. L'avion n'est alors tenu que par l'ancre du jeu (qui n'avance pas si `[g+0xd0] ≈ 0`) et par le frein (0 ; 1,0) que le jeu écrit lui-même. Étiquette : LU (v11 et exe) ; effet réel INCONNU.

**D4. Libération de la piste.** v11 : « INFÉRÉ : le jeu libère la piste et la baie à l'abandon ou à la fin ; non vu ».
Ma lecture : vrai pour l'abandon (état 3) et pour la fin du cycle. **Faux pour un engagement sans prise en charge** : l'abandon est désactivé en état 4, l'annulation externe `0x6fc4e0` refuse en état 4, et l'état 4 n'a ni délai ni compteur. Seule la disparition de l'avion libère `[g+0x5c]`. Voir partie 3. Étiquette : LU.

**D5. « Repère d'atterrissage calculé à partir de points de chemin »** (RISQUES, ligne « prise en charge qui démarre mais se passe mal »). Ma lecture : le « repère » est une **copie de la pose actuelle de l'avion** (plus l'ancre de baie posée sur cette pose), non validée. Ce qui dépend de nœuds de chemin, c'est le **premier segment du recul** (de la pose actuelle au premier nœud de `runway_reverse_a`). Étiquette : LU.

**D6. « La prise en charge démarre si le test de toucher passe ».** Pas assez : après l'engagement, le bloc `0x6ff368` rappelle `0x5ec1e0` avec la baie que l'avion occupe déjà (partie 1 (d)) ; il renvoie une **autre** baie libre ou −1. Voir N1. Étiquette : LU + INFÉRÉ.

### Ce que la v11 ne couvre pas
- **N1. Le rappel de la baie dans le même tick** (`0x6ff374`-`0x6ff388`) : peut écrire `[g+0x6c] = −1` puis sauter la prise en charge ; au tick suivant l'état 4 écrit à `navire+0x154 − 0x70` (corruption mémoire possible, INFÉRÉ, jamais vu). Ni les docs ni les alertes de la v11 n'en parlent.
- **N2. L'état 4 permanent.** Pour un avion arrêté `[g+0xd0] ≈ 0`, l'ancre n'avance pas, la progression `> 0,99` (`0x7003a8`) n'est jamais atteinte. La v11 n'écrit rien dans le gestionnaire, donc **elle ne peut pas annuler un engagement** ; `recall_force=0` ne le défait pas (la v11 le dit elle-même : « sauf si le jeu l'a déjà engagé »). Remonter dans l'avion ne libère rien non plus (INCONNU : je n'ai pas lu ce qui se passe quand le joueur reprend un avion attaché). Reste : fermer le jeu.
- **N3. Les critères de succès/échec** (D2) : une fois engagé, une vitesse relative qui « monte » est **normale** (recul jusqu'à 2,5 m/s ; alertes (a) et (f) à lire avec `dock=6`).
- **N4. Après la prise en charge.** Le premier segment est une ligne droite de la pose actuelle au premier nœud de `runway_reverse_a` (position INCONNUE) ; puis le recul ; puis l'état 6 attend que l'ascenseur soit prêt (`[navire+0xc68] > −0,5` et `[g+0x58] == −1`). Si l'ascenseur est occupé ou en bas, l'avion attend en bout de chemin (immobile, `dock=6`).
- **N5. La porte D** (appel virtuel `contexte→[+4]→vtable[+4]`) reste non identifiée chez eux comme chez moi.
- **N6. Le train.** L'abandon du jeu commande « train rentré » (`0x6ff1ed`, appel virtuel `+0x98`, argument 0). MESURÉ v10 : `wheels=3/3` reste affiché juste après l'abandon, donc sans effet visible sur le contact, mais jamais vérifié à l'écran. La v11 autorise jusqu'à `force_tries` = 3 abandons dans une fenêtre.

---

## 5. Conclusions demandées

### (i) Ce que la v11 a de plus risqué, d'après ma lecture
1. **Le cas rare où l'engagement passe** : engagement validé (ATTACHED_TO écrit, baie occupée), puis le même tick appelle le rappel de baie (N1). Au mieux une deuxième baie réservée ; au pire `[g+0x6c] = −1` et écritures hors du tableau des baies. Ensuite l'état 4 est permanent (N2) : piste et baie 8 bloquées jusqu'à la fermeture du jeu, sans que le journal le dise clairement (D2).
2. **Le plugin lâche le frein à l'engagement** (D3) : si l'engagement a lieu sans prise en charge, l'avion est sur un pont qui avance à ~31 m/s (MESURÉ : `speed=31.6` pour un avion à l'arrêt), retenu seulement par l'ancre du jeu.
3. **La surveillance qui prend l'engagement pour un succès** (D2) : « ne pas alerter si `attached ≠ 0` » masque précisément le cas dangereux.
4. Le cas le plus **probable** (porte B qui échoue) ne présente pas de danger nouveau par rapport à la v10 : un abandon au premier tick, comme les abandons déjà mesurés (v9 ×1, v10 ×2), avec jusqu'à 3 abandons permis par la v11.

### (ii) Ce qu'il faudrait observer en jeu pour trancher (sans rien poser soi-même)
Chaque mesure est une **lecture** (aucune écriture dans le jeu). Les deux premières peuvent se faire **avec un atterrissage normal de l'IA**, sans avion posé à la main :
1. **Les valeurs réelles des portes** : lire `V.y/|V|` (le `xmm1` de `0x6fe6ab`) et le produit scalaire (`xmm0` de `0x6fe77b`) pour un avion de l'IA à 200-400 m (attendu d'après ma lecture : environ −0,14 et environ 1), puis pour l'avion posé au tick où H4 entre en `0x6fe55b` (ce que la v10 ne voyait pas : les sondes ne tiraient pas). Cela dit directement si B et C échouent, et de combien.
2. **Les coordonnées des nœuds A et B** (tableau de 64 octets par élément, `[navire+0x88]+0x180`, flottants en `+0x34`, `+0x38`, `+0x3c`, indices `[g+0x84]` et `[g+0x88]`) et la position de l'avion dans le repère du navire (`R`) : donne la distance de l'avion au nœud A (le seuil de ~21 m de la porte B) et la longueur A→B. Aussi la position du **premier nœud de `runway_reverse_a`** (résultat de `0x5a2770`), pour savoir par où l'avion serait tiré.
3. **Le déroulé d'un atterrissage normal de l'IA**, tick par tick, avec `dock`, `attached`, `flight`, l'état de piste (`[g+0x1c]`), `[g+0x6c]`, `[g+0xd0]` et `baie.occupant`, de l'engagement à `dock=6`. Le journal v5 donne déjà `dock=1 attached=1` puis `dock=6 flight=1` (D2) ; il manque l'état de piste et la baie.
4. **La vitesse relative de l'avion posé pendant le maintien et sa direction** dans le repère du navire : MESURÉ `rel` 0,0 à 0,2 m/s, mais la direction n'est pas journalisée (utile pour juger la porte C).
5. **Le nombre total de baies** du porte-avions et leur occupation (`[navire+0x158]`, `[baie+0x64]`) : si une autre baie libre existe, N1 donne « deux baies » plutôt que « −1 ».
6. **Le sens du 2e champ des roues** (`roue+4` ≤ 0,1) et sa valeur pour l'avion posé (MESURÉ seulement le 1er champ : `min 0.05`).
7. **L'identité de la porte D** (classe de l'objet `contexte+4`) et son résultat pour le couple (navire, avion posé).

### (iii) Adresses de l'ancien exe trouvées par cette étude (pour la session de portage)
Un moyen simple de retrouver tout le bloc dans le nouvel exe : chercher les trois **chaînes** `runway_reverse_a`, `lift_top_reverse`, `load_lift_lower` (ancien exe : `0xd22570`, `0xd22584`, `0xd22598`) et leurs références croisées : elles mènent aux blocs de prise en charge et aux états 5/6/7. Constantes flottantes distinctives : 800, 200, 400, −0,08, 0,95, 10, 0,14, 2,5, 0,05 et l'entier 3600 (`0xe10`).

| Adresse (ancien exe) | Ce que c'est (étiquette) |
|---|---|
| `0x6fc7e0` | tick du gestionnaire de piste (fonction géante), appelé en `0x705f75` depuis `0x705ac0` ; aiguillage de mode `0x6fc8b3`-`0x6fc8ca` (LU) |
| `0x6fdba7`, `0x6fdd9b`, `0x6fddcf`, `0x701fa8` | don de la piste ; recherche de l'avion propriétaire ; aiguillage sur `[g+0x1c]-3` ; **table de saut** : état 3 → `0x6fdde5`, 4 → `0x6ffdbc`, 5 → `0x70066c`, 6 → `0x7008f6`, 7 → `0x700a26` (LU) |
| `0x6fdde5` | début de l'état 3 : compteur `[g+0xd4]++` (LU) |
| `0x6fdf03`-`0x6fdf3b`, `0x6fe00e`-`0x6fe054`, `0x6fe0a5` | position `R` de l'avion dans le repère du navire ; positions des nœuds A et B ; distance au milieu `[ebp-0x25c]` (LU) |
| `0x6fe43e`, `0x6fe45f`, `0x6fe54a` | seuils 800 (train sorti), 200 (zone finale), 400 (début de l'évaluation) (LU) |
| `0x6fe470` | **site de H4** : `mov byte [ebp-0x205],1` (LU) |
| `0x6fe55b` | début de l'évaluation d'engagement (LU) |
| `0x6fe666`, `0x6fe6ab`, `0x6fe77b`, `0x6fe7a2`, `0x6fe7cc` | portes **A, B, C, D, E** (LU) ; chutes : `0x6febda` (A/B), `0x6febe7` (C/D), `0x6febc0` (E) |
| `0x6fe7b8` | rappel de `0x5ec1e0` pour la baie à l'engagement (LU) |
| `0x6fe7e1` | **`[g+0x1c] = 4`** (engagement) ; `0x6fe7f9` frein (0 ; 1,0) (LU) |
| `0x6fe823` | **`avion+0x10c = id du navire` (ATTACHED_TO)** (LU + MESURÉ v5) |
| `0x6fe889`, `0x6fe8e6`-`0x6fe8eb` | `avion+0x188 = baie` ; **`baie+0x64 = id de l'avion`** (occupant) (LU) |
| `0x6fe8b4`-`0x6fe96e`, `0x6feb61`-`0x6febae` | pose de l'ancre de baie ; copie du « repère d'atterrissage » dans `[g+0xd8…0x138]` (LU) |
| `0x6feab5` | `DOCK_STATE = 1` à l'engagement (LU) |
| `0x6feb59` | `[g+0xd0]` = norme de la vitesse relative à l'engagement (LU ; sens INFÉRÉ) |
| `0x6fecfa` | pente visée par l'IA, constante 0,14 (`0xdb7218`) (LU) |
| `0x6feeee` | puissance = 0 si une roue touche (état 3) (LU) |
| `0x6fef0d`-`0x6fef46` | passage de `R` à « écart au nœud B » (ce que lit la sonde H3) (LU) |
| `0x6fef3b`-`0x6fef4e`, `0x6fef51`-`0x6ff08e` | test « point visé dépassé » (z > 0) ; test du cône (−400 < z < −50, > 0,45 rad) (LU) |
| `0x6ff0c5` | compteur d'approche > 3600 (LU) |
| `0x6ff0da`, `0x6ff0f1`, `0x6ff0fb`-`0x6ff205` | « une baie libre ? » ; contrôle `cmp [g+0x1c],4` ; **abandon** (puissance 1,0, train rentré, DOCK 5, FLIGHT 2, libère `[g+0x5c]` et `[g+0x6c]`) (LU) |
| `0x6ff20a`-`0x6ff362` | vitesse relative ≤ 10 (`0x6ff263`) ; frein progressif de l'IA (`0x6ff2e5`) ; test des roues (`0x6ff320`) ; **porte du toucher** (`0x6ff362`) (LU) |
| `0x6ff368`-`0x6ff388` | **bloc de prise en charge** ; **rappel de baie** `0x6ff374`/`0x6ff379` (LU) |
| `0x6ff3a8`, `0x6ff3b4` | frein (0 ; 1,0) ; puissance = 0 (LU) |
| `0x6ff66c`, `0x6ff676`, `0x6ff70d` | **DOCK_STATE = 6**, **FLIGHT_STATE = 1**, **`[g+0x1c] = 5`** (LU) |
| `0x6ff7bd`, `0x6ff7f6`-`0x6ffa4b` | recherche du chemin `runway_reverse_a` ; création du premier segment (LU) |
| `0x6ffa5c`, `0x6ffa6c`-`0x6ffdb7` | queue commune (ascenseur, `[g+0x58]`) ; fin : `FLIGHT_STATE = 0`, `DOCK_STATE = 4` en `0x6ffd7c` et `0x6ffdad` (LU) |
| `0x6ffdbc`-`0x70066b` | **état 4** (roulage engagé : ancre tirée vers le nœud B ; prise en charge à progression > 0,99 en `0x7003a8`-`0x700667`) (LU) |
| `0x70066c`, `0x7008f6`, `0x700a26` | états **5, 6, 7** (suivi de chemin ; attente ascenseur en `0x70095a`-`0x700973`) (LU) |
| `0x700a8a`-`0x700af1` | fin de l'état 7 : `[g+0x1c] = 0`, **échange `[g+0x5c]` et `[g+0x58]`** (libération de la piste) (LU) |
| `0x700bff` | avion propriétaire introuvable → `[g+0x5c] = −1` (LU) |
| `0x700e0a` | mode 0 : remet `[g+0x54]`, `[g+0x58]`, `[g+0x5c]`, `[g+0x60]` à −1 (LU) |
| `0x6fc4e0` (appelée par le virtuel `0x7078e0`, table ≈ `0xd59750`) | annulation externe : refuse en état 4 à 7 (LU) |
| `0x5ec1e0` | recherche de baie (navire ; classe ; indice préféré) : rend l'indice préféré **seulement si libre**, sinon la première autre libre, sinon −1 (LU) |
| `0x5ee6a0` | recherche d'un véhicule par id (LU ; sens INFÉRÉ) |
| `0x5a2770` | recherche d'un chemin nommé dans le modèle du navire (LU ; sens INFÉRÉ) |
| `0x6f86c0` | construction des segments d'un chemin nommé (LU ; sens INFÉRÉ) |
| `0x40ff10`, `0x40ffa0`, `0x40fcc0`, `0x40f430`, `0x40ae90` | transformation d'un point par une matrice 3×4 en doubles ; composition de matrices ; matrice d'un corps ; rotation d'un vecteur ; racine carrée (LU ; sens INFÉRÉ) |
| `0x844260` | retrait d'un élément de la file circulaire (LU) |

Offsets d'objet utilisés (confirmés par `world.c` du SDK pour l'avion) : avion `+0x80` id, `+0x10c` ATTACHED_TO, `+0x170` FLIGHT_STATE, `+0x174` DOCK_STATE, `+0x1fc` puissance, `+0xac` et `+0xb0` roues. Gestionnaire (LU seulement) : `+0x1c` état de piste, `+0x34` à `+0x40` file, `+0x54`, `+0x58`, `+0x5c`, `+0x60` propriétaires, `+0x6c` baie, `+0x84` et `+0x88` nœuds A et B, `+0xbc` segments, `+0xcc` et `+0xd0` fraction et vitesse, `+0xd4` compteur, `+0xd8` à `+0x138` repère.

---

*Rien n'a été commité. Les fichiers temporaires de l'étude (désassemblages, petit outil `dis.py`) sont dans le dossier temporaire de la session, pas dans le dépôt.*

# Réponses du Mac aux 3 questions de la tour (27/10/2026)

Réponses à `tour/questions_pour_le_mac.md`. **Lecture seule** : programme d'origine du Mac `sauvegarde/build_mac_origine`
(md5 `b0107170ddaf0245cbfee8a2d876aeb6`, relu en début de session : identique). Le jeu n'a pas été lancé, aucun patch n'a été
activé ni retiré. Désassemblage fait avec `objdump -d` d'Apple (syntaxe AT&T : le **dernier opérande est la destination**).
Adresses = adresses du fichier Mac (64 bits) ; elles ne servent à la tour que comme **repères de logique**.

## Tableau récapitulatif

| Q | Question | Verdict | Ce que la tour fait |
|---|---|---|---|
| Q3 | La 5e écriture (0,4) de Windows est-elle bien l'ascenseur/grue ? | **Oui, confirmé côté Mac** : la 5e écriture du code Mac (0,4) est le système « ascenseur/grue » (`breaker_lift`), et l'ordre des valeurs est le même que sur Windows. | Garder `0x006ea09e`. Contrôle de preuve côté Windows : juste après, un appel qui crée **2** sous-systèmes + deux `1.0`. |
| Q1 | Le Mac a-t-il une « vitesse de départ » qui lit aussi 2,5 ? | **Non.** Sur le Mac, les 7 lectures de 2,5 sont **toutes** accouplées à un `+ 0,05` ; il n'existe aucune lecture isolée de 2,5. Le 8e site de Windows (`0x006fb3d8`) n'a **pas d'équivalent** Mac. | **Ne pas le doubler** (choix déjà fait). Le Mac validé (×1,70) n'en avait pas. |
| Q2 | Où va le rapport de la grue (÷ 1/6, ÷ 1/30) ? | Dans la **demande d'énergie de la grue**, bornée à 1,0, rien d'autre (ni animation, ni son, ni test d'arrivée). Mais cette demande sert aussi de **freinage de fin de course**, donc le diviseur compte un peu. | Garder le patch tel quel pour le premier essai ; ne séparer borne et diviseur **que si** la mesure des 4 avions est nettement plus lente que 2:15. |

Détail et preuves ci-dessous. **Calculé** = déduit du code, pas mesuré en jeu.

---

## Q3 — Énergie : les 5 écritures, dans l'ordre du code

**Verdict : confirmé.** Les 5 parts écrites dans `c_vehicle_carrier_server_power_manager::build` (`0x10019eeb8`), dans l'ordre du code :

| # | Adresse Mac | Instruction | Valeur | Système (index i) | Sous-systèmes créés juste après |
|---|---|---|---|---|---|
| 1 | `0x10019eed7` | `movl $0x3f4ccccd, 0xc8(%rdi)` | 0,8 | propulsion (i = 1) | `reset(1)` |
| 2 | `0x10019ef34` | `movl $0x3e4ccccd, 0x140(%r15)` | 0,2 | radar (i = 4) | `reset(1)` |
| 3 | `0x10019ef92` | `movl $0x3f4ccccd, 0xa0(%r15)` | 0,8 | réparation (i = 0) | `reset(8)`, poids 4,0 puis 7 × 1,0 |
| 4 | `0x10019f021` | `movl $0x3f19999a, 0xf0(%r15)` | 0,6 | armes (i = 2) | `reset(10)`, 10 × 1,0 |
| 5 | `0x10019f0ad` | `movl $0x3ecccccd, 0x118(%r15)` | **0,4** | **ascenseur/grue (i = 3)** | `reset(2)`, 2 × 1,0 |

**Preuve 1 — chaque système porte un disjoncteur (« breaker ») de même numéro.** Dans `build`, les 5 boutons sont construits aux
décalages `+0x18, +0x30, +0x48, +0x60, +0x78` avec ces noms (chaînes lues dans le fichier) :

```
10019f11f  leaq 0x18(%r15),%rbx   ## chaîne 0x102918991 = "breaker_repair"
10019f161  leaq 0x30(%r15),%rbx   ## chaîne 0x102918965 = "breaker_propulsion"
10019f19c  leaq 0x48(%r15),%rbx   ## chaîne 0x102918978 = "breaker_wep"
10019f1d7  leaq 0x60(%r15),%rbx   ## chaîne 0x102918984 = "breaker_lift"
10019f212  leaq 0x78(%r15),%rbx   ## chaîne 0x1029189a0 = "breaker_radar"
```

Dans `::tick` (`0x1001b3fdc`), la boucle `i = 0..4` prend **le même `i`** pour le bouton et le système :

```
1001b4037  leaq (%rcx,%rcx,4),%r9          ## système i : base 0x90 + 40·i  (stride 0x28)
1001b413d  leaq (%rcx,%rcx,2),%rax
1001b4141  movq 0x20(%r14,%rax,8),%rax     ## bouton i : 0x18 + 24·i, champ +8  (stride 0x18)
1001b41c8  mulss 0xa0(%r14,%r9,8),%xmm1    ## part (« share ») du système i
```

Donc i = 3 ↔ `breaker_lift` ↔ système à `0x90 + 120 = 0x108` (tableau) / part à `0x118` = **l'écriture n° 5 (0,4)**.

**Preuve 2 — le code du pont lit bien ce système.** `docking_manager_air::update` (`0x1001accd8`) reçoit le gestionnaire d'énergie en 8e argument :

```
1001ae7e9  movq 0x18(%rbp),%r14           ## 8e argument = c_vehicle_carrier_server_power_manager&
1001ae82c  movq 0x108(%r14),%rdi          ## tableau de sous-systèmes du système 3 (ascenseur/grue)
1001ae833  movss 0x14(%rdi),%xmm0         ## sous-système 1 (12 octets chacun), champ +8 = puissance allouée
1001ae838  maxss %xmm4,%xmm0              ## borne à 0
1001ae83c  minss 0x26baeec(%rip),%xmm0    ## borne à 1,0  (0x102869730)
1001aebfb  movq 0x108(%r14),%rax
1001aec02  movss %xmm4,0xc(%rax)          ## écrit sa demande dans le sous-système 1, champ +0
```

C'est la grue du hangar (sous-système n° 1 de nos notes : « #0 = plateforme, #1 = grue »).

**Preuve 3 — cohérence avec la liste de la tour.** Windows écrit **0,8 / 0,2 / 0,8 / 0,6 / 0,4** dans cet ordre ; le Mac aussi
(propulsion 0,8 / radar 0,2 / réparation 0,8 / armes 0,6 / ascenseur-grue 0,4). Les deux 0,8 de Windows sont en `[esi+0x70]` puis
`[esi+0x50]` : le premier est **plus loin** en mémoire que le troisième, exactement comme au Mac (propulsion `+0xc8`, réparation
`+0xa0`, écart = un pas de système). Seul 0,4 est unique : c'est le seul candidat pour « ascenseur/grue ».

**Contrôle à faire côté Windows (preuve décisive, sans jeu).** Autour de `0x006ea09e`, on doit voir **un appel qui crée 2 sous-systèmes** puis
**deux écritures de `1.0`** (Mac : `movl $0x2,%esi` en `0x10019f0b8`, puis `0x3f800000` écrit en `0x4(%rax)` et `0x10(%rax)`). Les autres
0,8 : l'un est suivi de `reset(1)` (propulsion), l'autre de `reset(8)` + un poids de 4,0 (réparation).

**Ce que ça change.** Rien pour le patch : on garde `0x006ea09e`. Le point est levé (« présumé » → « confirmé côté Mac »). La
confirmation Windows reste la mesure (ou le contrôle ci-dessus).

---

## Q1 — Roulage : « vitesse de départ » qui lit aussi 2,5 ?

**Verdict : non, pas d'équivalent sur le Mac.** Dans `docking_manager_air::update` (`0x1001accd8` → `0x1001b2618`), toutes les lectures
des deux constantes :

```
2,5 (0x1028697bc) : 1001ad701  1001adf41  1001ae036  1001ae110  1001ae2cd  1001ae6e8  1001b0117     = 7
0,05 (0x1028697a4): 1001ad6f9  1001adf35  1001ae02a  1001ae104  1001ae2c1  1001ae6e0  1001b010f     = 7
```

Chaque lecture de 2,5 est à ≤ 12 octets d'un `addss 0,05`, dans le même bloc `v = min(2,5 ; v + 0,05)` (stocké en `0xec`, `0x10c` ou `0xcc` du
véhicule). Exemple (bloc `0x1001ad6f0`) :

```
1001ad6f0  movss 0xec(%r14),%xmm4
1001ad6f9  addss 0x1028697a4(%rip),%xmm4     ## + 0,05
1001ad701  movss 0x1028697bc(%rip),%xmm2     ## 2,5
1001ad709  minss %xmm4,%xmm2                 ## min(2,5 ; v + 0,05)
1001ad70d  movss %xmm2,0xec(%r14)
```

Trois blocs (`0x1001adf2c`, `0x1001ae021`, `0x1001ae0fb`) ajoutent ensuite `minss %xmm3,%xmm2` (« reste à faire × longueur ») **sur le résultat
déjà plafonné** ; le bloc `0x1001ae6d7` le fait sous condition (`cmpl $1,0x100(%r14)`). Aucun bloc ne charge 2,5 **sans** ajouter 0,05.

Autres recherches (négatives) : l'immédiat `0x40200000` (2,5 en entier) n'apparaît pas dans `update` ; l'unique autre copie de 2,5 dans le
pool (`0x10286b878`) n'y est lue **nulle part**.

**Réponses aux 3 sous-questions.**
1. 7 lectures de 2,5 et 7 de 0,05 : liste ci-dessus ; les 14 sont rip-relatives, chargées **juste avant** d'être utilisées.
2. **Pas de bloc « début de tronçon »** sans le `+ 0,05`. Au Mac, une nouvelle séquence démarre avec la vitesse remise à zéro
   (`movl $0x0,0x10c(%r14)` en `0x1001b01d0`), puis accélère de 0,05 par pas : pas de saut direct à `min(2,5 ; reste)`. Les 7 `movss` 2,5 sont
   tous doublés par le module : **rien ne reste à 2,5**.
3. **Aucun registre hissé** avant une table de sauts : chaque bloc recharge ses constantes. (Le seul réemploi est à l'intérieur d'un même
   bloc : `xmm2` du bloc `0x1001ae6d7`, réutilisé pour le second `minss`.)

**Ce que ça change.** Le Mac validé (×1,70) **n'a jamais touché** une lecture isolée de 2,5, parce qu'il n'y en a pas. Le 8e site de
Windows n'a donc pas de modèle Mac : **non tranché** (peut-être une vraie différence de code entre les deux versions, ou une façon de
compiler différente). Rester prudent comme la tour : **ne pas le doubler**. Si c'est bien un départ de tronçon, le laisser à 2,5 ne
borne que la vitesse initiale ; le plafond d'accélération (patché à 5,0) reste atteint ensuite.

---

## Q2 — Grue : où va le « rapport » calculé avec le diviseur (1/6, 1/30) ?

**Verdict : dans la demande d'énergie de la grue, bornée à 1,0.** Rien d'autre ne le consomme.

```
1001ae90f  divps 0x10286b8a0(%rip),%xmm4     ## [max(|dx|,|dz|) , |dy|] ÷ [1/6 , 1/30]
1001ae916  movshdup %xmm4,%xmm2
1001ae91a  maxss %xmm2,%xmm4                 ## rapport = le plus grand des deux
   ...  (les 5 mouvements de grue se rejoignent ici)
1001aebee  maxss %xmm10,%xmm4                ## ≥ 0   (xmm10 = 0)
1001aebf3  minss 0x102869730(%rip),%xmm4     ## ≤ 1,0
1001aebfb  movq 0x108(%r14),%rax             ## tableau de sous-systèmes ascenseur/grue
1001aec02  movss %xmm4,0xc(%rax)             ## demande du sous-système 1 (la grue)
```

Le même rapport ne sort **pas** vers une animation, un son ni un test d'arrivée (l'arrivée se teste avec `ucomiss` sur l'écart, avant,
en `0x1001ae91e`–`0x1001ae928`).

**Mais la demande sert à ralentir en fin de course.** Pas d'un axe : `d = borne(écart, ±pas)`, `pas_réel = d × puissance allouée`
(`0x1001ae932`, `mulss %xmm3,%xmm0` puis `addss` dans la position `0x153c`), et la puissance allouée = demande × facteur d'énergie (≤ 1) ; la demande
est elle-même le rapport `|d| ÷ diviseur` (plafonné à 1). Donc loin de la cible la grue va à fond ; **près de la cible elle freine**, et plus le diviseur
est grand, plus la zone de freinage est large.

| | borne (pas) | diviseur | la grue freine à partir de |
|---|---|---|---|
| jeu d'origine | 1/6 | 1/6 | 1/6 m |
| **Mac patché** | 1/3 | **1/6 (laissé)** | 1/6 m (comme l'origine) ; le rapport est plafonné à 1 |
| **Windows (patch actuel de la tour)** | 1/3 | **1/3 (doublé avec la borne)** | 1/3 m (freinage plus tôt) |

**Calculé, pas mesuré** : en fin de course la position converge comme `d' = d − d²/diviseur`. De 1/6 (ou 1/3) m jusqu'à 1 cm, ça prend
environ 16 pas (0,5 s) avec le diviseur 1/6, environ 32 pas (1,1 s) avec 1/3 ; en vertical et en rotation l'écart est de l'ordre de
0,1 s. Au total à peu près **2 s de plus par avion lancé** (donc de l'ordre de 7 s sur les 2:15 de 4 avions), si la grue est le
facteur limitant. Pas de risque de blocage : l'arrivée reste testée sur l'écart, pas sur la puissance.

**Ce que ça change.** Rien d'obligatoire. Pour le premier essai : **garder le patch tel quel**, mesurer les 4 avions. Si le résultat est
nettement plus lent que 2:15 (par exemple au-dessus de 2:25), séparer borne et diviseur : avec un crochet qui sauvegarde les
registres flottants, ou en dupliquant l'instruction. Le Mac, lui, garde le diviseur d'origine.

---

## Pour le moddeur (une phrase par question)

- **Q3** : oui, la valeur 0,4 qu'a retenue la tour est bien celle de l'ascenseur et de la grue.
- **Q1** : la vitesse de départ du roulage n'existe pas sur le Mac ; on ne double pas ce site sur Windows.
- **Q2** : le rapport de la grue règle son freinage de fin de course ; sur Windows elle freinera un peu plus tôt (de l'ordre de 2 s de plus par avion, calcul non mesuré), à vérifier seulement si la mesure sort nettement au-dessus de 2:15.

**Prochaine action unique (côté tour)** : étape 0 bis, la mesure du jeu d'origine (sortie des 4 avions, environ 3:50 attendus).

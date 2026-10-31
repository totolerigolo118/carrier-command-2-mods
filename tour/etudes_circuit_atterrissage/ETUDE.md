# Étude — circuit d'attente des avions au retour : cercle + créneau de piste élargi (port du Mac vers la tour)

> **Fiche de passation à jour (29/10/2026) : voir `PASSATION.md` dans ce dossier** (état, copies d'essai posées, décisions à demander au moddeur, effet de la mise à jour Steam du 28/10).

Écrite le 27/10/2026 sur la tour. **Étude en lecture seule** (la suite, étape 1, est en section 11) : le vrai `carrier_command.exe` n'a pas été modifié (somme de contrôle lue : `8E7FCBB6…E8BE`, = `ascenseur_x2` + `temps_x2`), le jeu n'a pas été lancé ni fermé, `mods.xml` et les DLL (`dinput8.dll`, `cc2x_frein.dll`, `frein.ini`) n'ont pas été touchés. Tout le travail s'est fait sur des **copies** de l'exécutable, dans un dossier temporaire. Seuls fichiers créés dans le dépôt : ce document et deux petits scripts de contrôle (dans ce dossier).

## En bref (français simple)

- **Ce que tu veux** : que les avions qui reviennent attendent en **cercle** (comme sur le Mac) et non en **ovale**, et qu'on puisse leur donner la piste sur un **créneau plus large** (plus de poses réussies, 0 raté).
- **Pourquoi ça accélère** : aujourd'hui la piste n'est donnée à un avion qu'à **un seul instant par tour** (un « portillon » au bas du virage arrière : 1 tick de simulation, soit 2,7 m de vol). Si la piste est encore occupée à cet instant, l'avion refait **un tour entier : 154 s** (l'ovale mesure 12,3 km). Avec le cercle, un tour ne dure plus que **94 s** ; avec le créneau élargi, la piste peut être donnée pendant **≈ 26 s de vol** au lieu d'un instant.
- **Résultat de l'étude** : **les 10 retouches du Mac se retrouvent toutes sur Windows** (aucune « non trouvée »). La forme est plus simple que sur le Mac : **6 changements de 4 octets** (+ 1 facultatif que je déconseille). Les 4 « vecteurs » du Mac se résument ici à **une seule valeur** (le centre du virage avant, écrit directement dans le code). Aucune constante partagée n'est modifiée, aucune nouvelle valeur n'est à ajouter.
- **Preuves** : chaque site relu au désassembleur sur une copie (octets d'origine, instruction, cible, relocation) ; un script refait tous les contrôles (**35 contrôles, 0 échec**) ; un petit modèle de la machine à états retrouve exactement les **154 s / 12,3 km** (ovale d'origine) et **94 s / 7,5 km** (cercle) annoncés par le Mac, ce qui confirme que j'ai bien lu le bon morceau de code.
- **Gain attendu** (estimation, jamais mesurée sur la tour) : environ **1 à 2 minutes sur 4 avions** (aujourd'hui 8:47 à 10:10 ; prévision 7:30 à 8:30, centre ≈ 7:45), pistes données toutes les **≈ 1:30 à 1:50** au lieu de 1:59 à 2:15. Le Mac avait mesuré 7:28 et une piste toutes les 1:31 avec le même réglage. **(Corrigé après l'essai 1 du cercle, section 12 : l'occupation de la piste, ≈ 1:40 par avion sur la tour, borne le gain ; plancher réaliste ≈ 8:00-8:30, résultat du 1er essai 8:58.)**
- **Risque** : 🟢 faible pour l'étude et la préparation (rien ne touche ton jeu). 🟡 moyen pour la pose (on change le programme du jeu, mais de très peu : 12 à 24 octets, retour arrière en une commande).
- **Ma proposition** (détail section 6) : deux petits modules posés l'un après l'autre, le plus sûr d'abord (**le cercle**, qui donne l'essentiel du gain, ne change aucun saut dans le code) puis **le créneau élargi** (3 sauts dans le code, un peu plus délicat). Une mesure de 3 essais après chaque module.
- **Mise à jour (étape 1 faite, accord du moddeur du 27/10)** : les deux modules existent (`atterrissage_cercle`, `atterrissage_creneau`), testés **sur copies** (157 contrôles, 0 échec) ; une **copie d'essai** de l'exécutable avec le cercle, `carrier_command_test_cercle.exe`, a été posée **à côté** du jeu (le vrai `carrier_command.exe` n'est **pas** modifié) et lancée une fois : elle démarre, reste vivante, aucun plantage. Voir la section 11. Reste à faire : l'essai de 4 avions (par le moddeur), et seulement ensuite la pose sur le vrai exécutable (accord séparé).

---

## 1. Comment ça marche aujourd'hui (repère du bateau : x vers tribord, z vers la proue)

Les avions qui reviennent font la queue sur un circuit d'attente à 80 m/s. Le code (une très grande fonction, `0x006fc730` → `0x00701fa5`, ≈ 22 Ko, 4 846 instructions, l'équivalent de `docking_manager_air::update` du Mac) a **6 états**, choisis par une table de saut en `0x00701fd0` :

| État | Ce que fait l'avion | Passe à l'état suivant quand… (adresse du début du test) |
|---|---|---|
| 0 | ligne droite x = −2200 vers l'arrière | z < −1800 (`0x007018e1`) |
| 1 | 1re moitié du virage arrière, centre (−1000, −1800), rayon 1200 | x > −1000 : c'est le **portillon**, au point (−1000, −3000) (`0x007019f3`) |
| 2 | 2e moitié du virage arrière | z > −1800 (`0x00701d2c`) |
| 3 | ligne droite x = 200 vers l'avant | z > 600 (`0x00701d5b`) |
| 4 | 1er quart du virage avant, centre (−1000, **600**) | x < −1000 (`0x00701e58`) |
| 5 | 2e quart du virage avant | z < 600 (`0x00701f4e`) → retour à l'état 0 |

**Le goulot** : la piste n'est donnée **qu'au tick où l'avion passe de l'état 1 à l'état 2**, et seulement si le bateau est en mode « accostage », la piste libre (case `[gestionnaire+0x5c]` = −1) et l'avion à moins de 1000 m du portillon. Ce test est le bloc qui commence en **`0x00701a2a`** (`cmp dword ptr [edi], 1`). Sinon : un tour de plus.
La partie « hélicos » du code (autre branche, vers `0x007016e9`) **n'utilise aucune des valeurs ci-dessus** : ils ne sont pas concernés.

## 2. Les 10 retouches du Mac et leur équivalent Windows

Mac : `outil/modules/atterrissage.py` (réglage B, 10 retouches). Windows : adresses d'image (base `0x400000`).

| n° | Mac | Ce que ça fait | Windows | Statut |
|---|---|---|---|---|
| 1 | `0x1001af900` (saut) | état 1 : tester la piste à chaque tick | **`0x007019fa`** `jbe 0x701b04` → `jbe 0x701a2a` | **trouvé** (site **S1**) |
| 2 | `0x1001af85b` (saut) | état 2 : tester la piste pendant la 2e moitié du virage | **`0x00701d33`** `jbe 0x701b04` → `0x701a2a` | **trouvé** (**S2**) |
| 3 | `0x1001af867` (saut) | passage 2 → 3 : tester aussi à ce moment | **`0x00701d4e`** `jmp 0x701b04` → `0x701a2a` | **trouvé** (**S3**) |
| 4 | `0x1001af785` (`addps`) | état 4 : centre du virage avant (−1000, 600) → (−1000, −1800) | **`0x00701379`** : `mov [ebp-0x2a4], 600` → `−1800` | **trouvé, forme différente** (**C1**, voir 3) |
| 5 | `0x1001af7d4` (`addps`) | idem, « retour au repère » | (même changement C1) | **trouvé = C1** |
| 6 | `0x1001afa98` (`addps`) | état 5 : idem | (même changement C1) | **trouvé = C1** |
| 7 | `0x1001afae7` (`addps`) | état 5 : idem, retour au repère | (même changement C1) | **trouvé = C1** |
| 8 | `0x1001af870` (`movss`) | état 3 : fin de la ligne droite 600 → −1800 | **`0x00701d5b`** `comiss xmm0,[600]` → `[−1800]` | **trouvé** (**C2**) |
| 9 | `0x1001afaf2` (`movss`) | état 5 : fin du virage avant 600 → −1800 | **`0x00701f4e`** `movss xmm0,[600]` → `[−1800]` | **trouvé** (**C3**) |
| 10 | `0x1001af87b` (`addss` → `subss`) | état 3 : la visée reste 1800 m devant l'avion | **`0x00701d65`** `addss xmm1,[600]` | **trouvé, mais facultatif** (**C4**, voir 4) |

**Pourquoi 10 → 6 changements.** Sur le Mac le centre du virage avant était un vecteur de 4 nombres lu en mémoire (`addps`) à 4 endroits : il fallait 4 redirections et des constantes alignées sur 16 octets. Sur Windows (compilateur Microsoft) ce centre est **écrit dans la pile par 2 instructions au début de la fonction** (`0x0070136f` : x = −1000 ; `0x00701379` : z = 600), puis relu par les états 4 et 5. Changer **une seule valeur** (600 → −1800) fait ce que 4 redirections faisaient sur le Mac. Je l'ai vérifié : à part ces 2 écritures, cet emplacement n'est lu que par les états 4 et 5, et rien ne peut sauter par-dessus l'initialisation (la zone `0x00701321`–`0x00701610` n'est entrée que par son début, `0x00701321` ; aucun saut ne tombe au milieu).

## 3. Les changements à écrire (chaque octet d'origine lu dans le fichier)

Les valeurs sont les 4 octets du champ changé (petit-boutiste). « Relocation » : un champ qui est une **adresse** a une entrée dans la table de relocation (ASLR) : on garde la même entrée en changeant seulement l'adresse visée ; les autres champs n'en ont pas (vérifié).

| Site | Instruction (adresse) | Champ | Avant | Après | Effet |
|---|---|---|---|---|---|
| **S1** | `jbe 0x701b04` (`0x007019fa`) | `0x007019fc` | `04 01 00 00` | `2a 00 00 00` | cible → `0x00701a2a` |
| **S2** | `jbe 0x701b04` (`0x00701d33`) | `0x00701d35` | `cb fd ff ff` | `f1 fc ff ff` | cible → `0x00701a2a` |
| **S3** | `jmp 0x701b04` (`0x00701d4e`) | `0x00701d4f` | `b1 fd ff ff` | `d7 fc ff ff` | cible → `0x00701a2a` |
| **C1** | `mov dword [ebp-0x2a4], 0x44160000` (`0x00701379`) | `0x0070137f` | `00 00 16 44` (600,0) | `00 00 e1 c4` (−1800,0) | centre du virage avant : z = −1800 |
| **C2** | `comiss xmm0,[0xdb7a70]` (`0x00701d5b`) | `0x00701d5e` | `70 7a db 00` (→ 600) | `54 7e db 00` (→ −1800) | état 3 : seuil −1800 |
| **C3** | `movss xmm0,[0xdb7a70]` (`0x00701f4e`) | `0x00701f52` | `70 7a db 00` (→ 600) | `54 7e db 00` (→ −1800) | état 5 : seuil −1800 |
| *C4 (facultatif)* | `addss xmm1,[0xdb7a70]` (`0x00701d65`) | 8 octets | `f3 0f 58 0d 70 7a db 00` | `f3 0f 5c 0d 54 7e db 00` | `subss xmm1,[−1800]` (2 changements de 4 octets pour l'outil) |

- **Grouping** : *créneau élargi* = S1 + S2 + S3 (3 sauts). *Cercle* = C1 + C2 + C3 (3 valeurs). Réglage B du Mac = les deux.
- La constante −1800,0 existe déjà en lecture seule (`0x00db7e54`, section `.rdata`, sans droit d'écriture) : **rien à ajouter**. La constante 600 (`0x00db7a70`) n'est **jamais** modifiée, seules les lectures du cercle sont redirigées (règle du projet).
- Les 6 champs tiennent dans le format de 4 octets de `patch_exe.py`. Aucun ne chevauche les 33 endroits déjà retouchés par `ascenseur_x2` et `temps_x2` (vérifié).
- **Pourquoi les 3 sauts sont sûrs en théorie** : la cible `0x00701a2a` est le début d'une instruction (`cmp dword ptr [edi], 1`) ; c'est exactement l'endroit où le code d'origine arrive **après** avoir changé l'état d'attente 1 → 2, donc le bloc n'attend aucun registre (il relit tout dans la pile) ; en cas de refus il retombe sur `0x00701b04`, la sortie commune d'origine. Le Mac fait la même chose (bloc `0x1001af914`).
- **Sommes de contrôle attendues** (SHA-256 calculés en mémoire, à refaire de façon indépendante à l'étape 1), à partir de l'exécutable actuel `8E7FCBB6…` :
  - créneau seul : `C7851BBF06C2BBD681B675E4E8C187D15A7566494058EEA86244761202FE72EB`
  - cercle seul : `80E9D871A342FA7D244453BE4062A93653C30838B99ED84471026C2FAC7098DA`
  - les deux (réglage B) : `563994278CB0B3ED1504C99B43087B3CEFABA98627AA68C84FBB3B797860202C`

## 4. Différences avec le Mac, et points d'attention

1. **Le 10e site (C4) est inutile sur Windows.** Sur le Mac, le seuil et la « visée » partageaient un même registre, donc changer le seuil obligeait à inverser le signe de la visée. Sur Windows ce sont deux lectures séparées : la visée garde ses 600 m, ce qui ne compte que **pendant 1 tick** (avec le cercle, l'état 3 ne dure plus que 1 tick, vérifié par le modèle). **Recommandation : ne pas le faire** (moins de changements). C'est un choix à ta main : le faire reproduirait exactement le comportement validé sur le Mac.
2. **La fenêtre du créneau élargi vaut ≈ 26 s de vol (2,06 km), pas 2,7 km / 35 s** comme écrit dans les notes du Mac. Calcul : le test exige « distance au portillon < 1000 m » (fonction `0x0040d3e0` relue : c'est bien une distance euclidienne), soit 1032 m avant le portillon et 1029 m après. L'écart avec les 2,7 km des notes (surtout la partie « après » : 1684 m) **est expliqué par le Mac le 28/10** (`passation_windows/REPONSES_mac_pour_la_tour_28-10.md`, Q3 : sur le Mac le terme en x du test de distance est le contenu d'un registre laissé par le code précédent, ce qui donne 1 031 + 1 684 m = 2,7 km ; **c'est un artefact du Mac, 2,06 km est le bon calcul pour Windows**, fenêtre environ un quart plus courte que celle du Mac, sans effet sur le cercle) ; il **ne change pas la décision** (mêmes nombres des deux côtés, le cercle fait l'essentiel du gain) mais je préfère le signaler.
3. **Avion dont l'approche rate** : il est remis dans la file à l'état 3. Avec le cercle, l'état 3 passe tout de suite à l'état 4 : l'avion rejoint le cercle depuis l'endroit où il est. **Jamais vu en jeu** (0 approche ratée sur le Mac avec ce réglage). À surveiller dans le journal (« ratées »).
4. **Durée d'occupation de la piste sur la tour ≈ 95 s** (estimation : approche 0:52 + ≈ 43 s de roulage jusqu'à l'ascenseur, par analogie avec le Mac où la piste se libère 38-41 s après le toucher ; Mac : 88 s en tout). La simulation du Mac dit que le réglage B est **plus lent seulement si un atterrissage dure 140–160 s** : on en est loin.
5. **Le porte-avions adverse utilise le même code** : ses avions aussi passeront au cercle (comme sur le Mac).
6. Seul `carrier_command.exe` est concerné (comme les deux modules déjà posés). `dedicated_server.exe` ne change pas. La logique tourne chez l'hôte : si le moddeur héberge avec le jeu normal, les joueurs qui rejoignent en profitent probablement (déduction, non testée).
7. Le circuit sert aussi de « gabarit » à l'étude d'atterrissage à la main (retour de l'avion 10 par l'IA) : voir section 9.

## 5. Ce qui a été vérifié, comment, et ce qui ne l'est pas

**Vérifié (sur copies, lecture seule)**
- Outils : `desasm.py` (capstone), puis `verifier_sites.py` (nouveau, dans ce dossier) : `python -I tour/etudes_circuit_atterrissage/verifier_sites.py <copie> --sans-recouvrement tour/outils/modules_exe`. Résultat sur la copie de l'original (`1C9A01C3…`) **et** sur la copie de l'exécutable actuel (`8E7FCBB6…`) : **35 contrôles, 0 échec, sorties identiques**.
- Contrôlé pour chaque site : instruction décodée (mnémonique, longueur, cible ou constante), octets d'origine, nouveaux octets, relocation attendue ou absente, pas de chevauchement. Sur une copie **en mémoire** patchée : les frontières de **toutes** les instructions de la fonction (4 846) sont inchangées, les 3 sauts atterrissent exactement en `0x00701a2a`, les 3 valeurs lisent bien −1800.
- `modele_circuit.py` (nouveau, calcul pur) : machine à états idéalisée, seuils d'origine puis modifiés : l'ordre **0 → 1 → 2 → 3 → 4 → 5 → 0** est respecté ; tour **154,3 s** (12 340 m) d'origine, **94,3 s** (7 540 m) modifié ; fenêtre de piste 2 061 m = 25,8 s.
- Simulateur de file du Mac (`outil/generateurs/simuler_file_atterrissage.py`, relancé avec une occupation de piste de 90 à 100 s) : 4 avions rangés en ≈ 9:50–10:10 (origine), 8:30–9:40 (créneau seul), **6:50–7:40 (cercle seul)**, **6:40–7:10 (les deux)**. Sur le Mac la simulation (piste occupée 88 s) donnait 98–104 s entre deux pistes pour B et la mesure 91 s (7:28 au total) : elle est un peu pessimiste sur l'écart mais ne compte ni le temps avant la 1re piste (≈ 1:12 sur la tour) ni la fin de l'atterrissage du dernier avion (0:52 + 0:55) ; en les ajoutant on obtient **7:30 à 8:30 (centre ≈ 7:45)** pour B sur la tour. **Le cercle fait l'essentiel du gain** ; le créneau élargi réduit surtout les pires attentes (écart maximal ≈ 160 s au lieu de ≈ 190 s).

**Pas prouvé** (à ne jamais présenter comme un fait)
- Rien n'a tourné en jeu. Les relectures sont faites à l'octet et au désassemblage, pas observées en exécution. Seule une partie le dira. **[PÉRIMÉ depuis le 27/10 (cercle, §12) et le 29/10 (créneau, §14) : le cercle a tourné à l'essai 1 (8:58), le créneau à l'essai 2 avec la copie « pont » (7:09, 0 raté, aucun plantage) ; voir ces sections pour ce qui est mesuré, déduit ou non prouvé.]**
- Les chiffres de gain sont des **estimations** par simulation (avion idéal, durée de piste ≈ 95 s supposée) ; la tour n'a jamais mesuré le jeu d'origine sans `ascenseur_x2` autrement que par la référence 9:58.
- Le comportement après approche ratée (point 3 ci-dessus) n'est pas éclairci. (L'écart de fenêtre du point 2 est expliqué depuis le 28/10 : artefact du Mac ; le Mac confirme aussi que les 10 retouches correspondent et que le 10e site est inutile sur Windows.)
- Un contrôle d'intégrité caché du jeu n'est pas à craindre (l'exécutable patché démarre depuis 07:46), mais c'est le premier lancement qui le confirmera pour ces changements-ci.

## 6. Plan en étapes (une étape = un accord du moddeur + une preuve dans le journal)

| Étape | Ce que ça fait, en clair | Risque | Alternative plus sûre / garde-fou |
|---|---|---|---|
| **0. Étude** (faite) | lire, retrouver les sites, vérifier | 🟢 | — |
| **1. Préparer 2 modules et les tester sur des copies** (**FAIT** le 27/10, voir 11) | j'écris `atterrissage_cercle` et `atterrissage_creneau` (un fichier JSON chacun dans `tour/outils/modules_exe/`, comme `ascenseur_x2`), le générateur qui relit chaque site, et j'étends les tests de `patch_exe.py` : cycle activer / retirer sur copies, les sommes de contrôle de la section 3 recalculées autrement, retirer dans n'importe quel ordre redonne exactement l'original ou l'état actuel. **Aucun fichier du jeu n'est touché.** | 🟢 | c'est déjà la variante sûre |
| **2. Poser le module « cercle »** sur le vrai exécutable | `patch_exe.py activer --module atterrissage_cercle --cest-le-vrai-jeu`, jeu fermé : 3 champs de 4 octets changés (une valeur écrite dans le code, 2 adresses de constantes), sommes vérifiées avant / après, **nouvelle copie de l'état dans `tour/sauvegardes/`**. Puis un premier lancement pour voir que le jeu démarre. **Accord séparé du moddeur**, et message préalable à la conversation « atterrissage à la main » (voir 9). | 🟡 | choisir d'abord le module qui ne change **aucun saut** dans le code (c'est le cercle) ; garder la copie `…_patche_8E7FCBB6.exe` ; essai sur une partie neuve jetable |
| **3. Mesurer le cercle** | Le moddeur joue 3 essais de 4 avions (section 7) ; je lis le journal | 🟢 (rien n'est modifié) | si 1 plantage ou 1 approche ratée : retour arrière, on regarde avant de continuer |
| **4. Poser le module « créneau élargi »** | mêmes gestes que l'étape 2 : 3 sauts changés (le bloc `0x00701a2a` est atteint plus souvent). **Accord séparé.** | 🟡 (un cran au-dessus du cercle : on touche l'enchaînement du code ; en cas d'erreur le jeu planterait au premier avion en vol d'attente, donc visible tout de suite) | **voie rapide** possible : poser les deux modules en une fois, comme sur le Mac (1 pose, 1 série de mesures, mais si ça se passe mal on ne saura pas lequel des deux est en cause) |
| **5. Mesurer, conclure, ranger** | 3 essais ; tableau avant / après ; mise à jour de `JOURNAL_tour.md` ; commit et push | 🟢 | — |

Remarque : comme **le chargement d'une sauvegarde plante déjà** (cause sans rapport, connue), un plantage pendant un essai fait perdre la partie en cours : ne tester que sur une partie neuve, jamais au milieu d'une partie qui compte.

## 7. Mesurer avant / après avec le mod `cc2_mesures` (journal des retours)

- **Conditions identiques** à celles des deux mesures de référence de la même configuration : mods actifs = missiles + `cc2_mesures` (Revolution désactivé), exécutable `ascenseur_x2` + `temps_x2` (« SIM ×1,33 » en pratique, sans importance : tout est en **temps de jeu**), partie neuve, navire à l'arrêt, mêmes 4 avions lancés puis rappelés tout de suite.
- **Ce que le journal affiche** (« FINI en … ») : total pour les 4 avions, **piste toutes les**, ratées, **approche**, **pont > hangar**, et pour chaque avion l'heure de piste / pont / hangar. Prendre une capture à chaque essai.
- **Avant** (même configuration, exécutable actuel) : essai 1 = **FINI en 10:10**, pistes à 1:33, 3:36, 6:04, 8:18 (écarts 2:03, 2:28, 2:14 ; « toutes les 2:15 ») ; essai 2 = **8:47**, pistes à 0:58, 2:53, 4:53, 6:55 (écarts 1:55, 2:00, 2:02 ; « toutes les 1:59 »). Approche 0:52 et pont > hangar 0:55 dans les deux. Référence d'origine (autre configuration) : 9:58.
- **Comment lire** : pour *ce* patch, **« approche » et « pont > hangar » ne doivent PAS bouger** (0:52 et 0:55 ; le patch n'y touche pas) : ce sont des **témoins** qui prouvent que les conditions sont les mêmes (s'ils changent, quelque chose d'autre a changé). Le **total** varie beaucoup d'un essai à l'autre (1:23 d'écart à conditions identiques) : il faut donc **3 essais par étape** et regarder surtout **chaque écart entre deux pistes** (un « tour perdu » se voit : ≈ 2:30 de plus à l'ovale, ≈ 1:35 de plus au cercle).
- **Critères de réussite proposés** (à valider par le moddeur) : 0 plantage ; **0 approche ratée** ; les 4 avions rangés ; approche et pont > hangar inchangés ; écarts entre pistes en moyenne **≤ 1:50** (contre 1:59 à 2:15) ; « FINI en » moyen **< 8:30** (contre ≈ 9:30). À l'œil : sur la carte, les avions en attente tournent en **cercle** d'environ 2,4 km de large, à 859 m du bateau au plus près (centre à 1,8 km derrière), au lieu d'un ovale.

## 8. Retour arrière

- Normal (jeu fermé) : `python tour/outils/patch_exe.py retirer --exe "<vrai exe>" --module <atterrissage_creneau | atterrissage_cercle> --cest-le-vrai-jeu` : l'outil remet les octets d'origine, vérifie la somme et refuse tout état inattendu. Contrôler ensuite `Get-FileHash` = `8E7FCBB6…E8BE` (état actuel) ou la somme attendue. **[PÉRIMÉ depuis le 28/10 : le vrai `carrier_command.exe` est le build de Steam `461E1262…` (§13, mise à jour du 28/10), sans nos patchs ; cette commande ne vaut que pour l'ancien build, NE PAS UTILISER sur l'exe de Steam (l'outil le refuse : état INCONNU). Pour les copies d'essai : supprimer le fichier. Voir `PASSATION.md` et §14.]**
- Copies : `tour/sauvegardes/carrier_command_1.5.18_patche_8E7FCBB6.exe` (état actuel) et `…_original.exe` (sommes dans le journal) ; après chaque pose je crée la copie de l'état suivant (sinon une conversation qui « restaure » depuis une ancienne copie effacerait nos changements sans le dire).
- En dernier recours seulement : « Vérifier l'intégrité des fichiers » dans Steam (remet l'exécutable d'origine : **efface aussi** `ascenseur_x2` et `temps_x2`).
- Rien d'autre n'est à défaire : pas de fichier, pas de réglage, pas de DLL.

## 9. Coordination avec les autres conversations

- **Atterrissage à la main** : elle utilise le jeu avec `dinput8.dll`, `cc2x_frein.dll`, `frein.ini` posés dans le dossier du jeu (**je n'y touche pas**) et a observé le retour d'un avion par l'IA. Le circuit d'attente changerait le déroulé de ces retours. **Avant toute pose** : la prévenir par message, ne rien poser pendant qu'un essai est en cours. Un seul jeu à la fois sur le PC : **ne jamais lancer le jeu sans l'accord du moddeur.**
- **Missiles, modes carburant** : aucun lien (autres fichiers, autres adresses ; `mods.xml` non touché, `cc2_carte` inchangé).
- Le roulage de retour ×2 (`pont_retour_x2` : 3 lectures de `30,0` aux états 5-7 de piste, même fonction) est un **autre port**, non fait : à ne pas mélanger avec celui-ci (« une seule modification testée à la fois » ; aucun chevauchement avec les sites ci-dessus).

## 10. Fichiers de cette étude

- `ETUDE.md` : ce document.
- `verifier_sites.py` : retrouve et contrôle les 7 sites sur une copie ; imprime le tableau et le verdict (`python -I`, lecture seule, aucun paquet à installer en dehors de capstone déjà présent).
- `modele_circuit.py` : modèle idéalisé de la machine à états (calcul pur).
- `RAPPORT_modules.md` : tableau des changements des deux modules (généré).
- Hors de ce dossier : `tour/outils/generer_modules_atterrissage.py` (génère les deux JSON en relisant chaque site), `tour/outils/modules_exe/atterrissage_cercle.json` et `atterrissage_creneau.json`, `tour/outils/test_patch_exe.py` (section 5 ajoutée), `tour/outils/patch_exe.py` (seule la liste des modules du commentaire d'en-tête a changé).
- Les copies de travail de l'exécutable et les sorties brutes sont dans le dossier temporaire de la session (hors dépôt).

## 11. Étape 1 : ce qui a été fait (27/10/2026, après l'accord du moddeur : « tu peux ouvrir le jeu si besoin, et faire tes tests dessus »)

**Fait**
- **Deux modules** générés par `tour/outils/generer_modules_atterrissage.py` (qui relit chaque site avec `verifier_sites.py` et refuse d'écrire au moindre écart) : `atterrissage_cercle.json` et `atterrissage_creneau.json` dans `tour/outils/modules_exe/`. Chacun = 3 changements de 4 octets, tout ou rien ; aucun octet commun avec l'autre ni avec `ascenseur_x2` / `temps_x2`. Tableau : `RAPPORT_modules.md`.
- **Tests sur copies** : `tour/outils/test_patch_exe.py`, section 5 ajoutée. **157 contrôles au total, 0 échec** (les anciens passent toujours ; **182 depuis la sécurisation de `patch_exe.py` du 30/10/2026**, section 6 du test : exe inconnu ou d'un autre build refusé, restauration complète seulement avec `--restaurer-tout-l-exe`). Ils recalculent les octets voulus **sans lire les JSON** (cible des sauts, −1800 en virgule flottante, adresse de la constante) ; recalculent les sommes de contrôle de la section 3 (**identiques** à celles calculées en mémoire pendant l'étude : `8E7FCBB6…` pour l'exécutable actuel, `C7851BBF…` +créneau, `80E9D871…` +cercle, `56399427…` +les deux) ; relisent le fichier patché au désassemblage (les 4 846 instructions gardent leurs frontières, les 3 sauts tombent en `0x00701a2a`, les 2 lectures visent `−1800.0`, la constante `600.0` n'est pas touchée) ; essaient les **15 combinaisons** des 4 modules (poser un à un, retirer dans l'ordre inverse ou direct : chaque étape a la somme attendue, et on retombe sur l'original exact) ; vérifient aussi l'état mélangé (module à moitié posé), l'octet inconnu, le chemin « steamapps ».
- **Aucun fichier du jeu modifié.** **[PÉRIMÉ : le vrai exe a changé depuis (28/10 10:25 `0C5DFE52…`, puis 28/10 21:30 build Steam `461E1262…` ; voir §13 et §14).]** Le vrai `carrier_command.exe` est toujours `8E7FCBB6…` (date 10:21, `patch_exe.py etat` : `ascenseur_x2` et `temps_x2` posés, les deux nouveaux modules « ORIGINAL »). `mods.xml`, `dinput8.dll`, `cc2x_frein.dll`, `frein.ini` : non touchés.
- **Copie d'essai posée À CÔTÉ du jeu** (nouveau fichier, rien d'existant remplacé) : `C:\Program Files (x86)\Steam\steamapps\common\Carrier Command 2\carrier_command_test_cercle.exe` = exécutable actuel + module `atterrissage_cercle`, somme `80E9D871A342FA7D244453BE4062A93653C30838B99ED84471026C2FAC7098DA` (relue après la copie). Pourquoi une copie plutôt que la pose : le jeu normal ne change pas, et pour tout défaire il suffit de **supprimer ce fichier**.
- **Premier lancement de cette copie** (directement, Steam ouvert, `steam_appid.txt` présent) : lancée à 17:41:32, restée vivante, réactive (253 Mo) à l'écran-titre pendant ≈ 100 s, **fermée poliment en 1 s**, **aucun rapport de plantage** Windows. L'extension du frein (`cc2x_frein.dll`) s'est chargée comme d'habitude (`cc2x.log`).

**Ce que ça prouve, et ce que ça ne prouve pas**
- Prouvé : le fichier patché est un exécutable valide qui démarre, avec l'extension en place. Rien n'est cassé au chargement.
- **Pas prouvé** : le circuit lui-même. La grande fonction ne travaille réellement que quand des avions **reviennent**, et sur la tour **personne ne sait encore faire décoller les avions sans le moddeur** (l'automatisation a été abandonnée à 14 h 25). Aucune capture d'écran n'a été prise : l'outil de capture demande à PowerShell de contourner la protection des scripts, ce que le système a refusé, et je ne contourne pas.

**Point d'attention (un seul jeu à la fois)** : les outils de la tour qui contrôlent « le jeu tourne-t-il ? » cherchent le nom exact `carrier_command.exe` et **ne voient pas** la copie d'essai. Avant de lancer le vrai jeu, ou un outil d'essai, vérifier qu'aucune copie ne tourne : `Get-Process carrier_command*` doit ne rien renvoyer.

**Prochaine étape (celle du moddeur)** : lancer `carrier_command_test_cercle.exe` (double-clic dans le dossier du jeu ; pas par Steam, qui lance l'exécutable normal), faire une **partie neuve**, lancer les 4 avions et les rappeler tout de suite, comme pour les mesures de référence (section 7), puis lire le « FINI en » du mod `cc2_mesures` ; 3 essais. Les mods actifs et les sauvegardes sont les mêmes que pour le jeu normal (dossier de données commun). La pose sur le vrai exécutable (commande de la section 8, à l'envers) ne se fait qu'après, avec un **accord séparé**. Pour tester le créneau en plus : une 2e copie (« les deux ») se prépare en une minute, sans toucher au vrai exécutable.

## 12. Essai 1 avec le cercle (copie d'essai `carrier_command_test_cercle.exe`, 27/10/2026, partie de 17:50 à 18:00)

**Lecture du journal affiché** (capture du moddeur : `essais/essai1_cercle_capture_journal.png`, horloge 11:50.8, SIM ×1,33) :

| avion | piste | pont | hangar |
|---|---|---|---|
| 2 | 1:33 | 2:30 | 3:25 |
| 4 | 3:24 | 4:08 | 5:03 |
| 1 | 5:07 | 6:02 | 6:56 |
| 3 | 7:19 | 8:04 | 8:58 |

« FINI en **8:58** : 4 avions » ; piste toutes les **1:55** (écarts 1:51, 1:43, 2:12) ; ratées **0** ; approche **0:50** ; pont > hangar **0:55**. Fermeture normale du jeu (journal du SDK : `session ended` 18:00:54), **aucun rapport de plantage Windows**.

**Comparaison avec l'ovale (même exécutable de base, mêmes mods de mesure ; deux mods en plus aujourd'hui, `cc2_carte` et `cc2_modes`)**

| | ovale, essai 1 | ovale, essai 2 | **cercle, essai 1** |
|---|---|---|---|
| FINI en | 10:10 | 8:47 | **8:58** |
| piste toutes les | 2:15 | 1:59 | **1:55** |
| écarts entre pistes | 2:03, 2:28, 2:14 | 1:55, 2:00, 2:02 | **1:51, 1:43, 2:12** |
| approche / pont > hangar (témoins) | 0:52 / 0:55 | 0:52 / 0:55 | **0:50 / 0:55** (inchangés) |
| attente perdue après l'arrivée du précédent au hangar | +11, +47, +34 s | non relevé | **−1, +4, +23 s** |

- **Lecture honnête : un essai ne conclut pas.** Le total (8:58) est dans la fourchette des deux essais à l'ovale (8:47 à 10:10) ; l'écart moyen entre pistes baisse un peu (1:55 contre 1:59 et 2:15) ; l'attente perdue après la libération de la piste est nettement plus courte (23 s au pire contre 47 s), ce qui va dans le sens attendu. Les deux témoins n'ont pas bougé : les conditions sont comparables.
- **Ce qui borne le gain** : les écarts mesurés ne descendent pas sous **1:43** ; l'écart entre deux pistes est du même ordre que « piste → hangar » de l'avion précédent (1:39 à 1:52 : l'avion 2 arrive au hangar à 3:25 et le suivant reçoit la piste à 3:24). La piste semble donc libérée vers l'arrivée de l'avion au hangar : **c'est cette occupation de la piste (≈ 1:40) qui limite**, bien plus que le circuit. Mon estimation de 7:30 à 8:30 (occupation ≈ 95 s supposée) était **trop optimiste** ; avec cette occupation et le premier toucher à 1:33, le plancher réaliste est plutôt **≈ 8:00 à 8:30**. (Inférence tirée de 1 essai : à confirmer par les deux suivants.)
- **Reste à gagner avec le créneau élargi** : au plus l'attente perdue restante (ici 23 s sur le dernier écart, 27 s en tout). Sa pose ne se justifie que si les essais 2 et 3 montrent des attentes perdues plus grandes.

**Preuve en jeu que le cercle est bien actif** (données du journal du SDK, `cc2x.log`, enregistrées par le mod `cc2_carte`, positions toutes les 10 s de jeu ; script `trajets_circuit.py`, résultat dans `essais/essai1_trajets.txt`) : les avions en attente tournent sur un **cercle ajusté de centre (−977 à −987 ; −1781 à −1817) m dans le repère du bateau, soit celui du code (−1000 ; −1800) à 20-30 m près**, rayon **808 m** (avion 17) et **840 m** (avion 18), **958 m** (avion 9, autre type d'appareil), avec un écart moyen au cercle de 34 à 63 m ; l'avion 17 a fait **9,5 tours** (60 s par tour) en attendant son tour. Un ovale d'origine monterait vers z = +1800 (centre du virage avant à +600) : on ne voit rien de tel (hors décollage et approche finale).
- **Point à noter** : le rayon réellement volé (≈ 800-950 m) est **plus petit que le rayon de 1200 m du code** : l'avion coupe les virages en visant un point devant lui. Mon modèle (`modele_circuit.py`, tour théorique de 94 s) surestime donc la durée d'un tour (réel ≈ 60 s pour les avions du type 10). Cela ne change aucune décision, mais les durées de tour de la section 1 sont des durées théoriques.
- **Non résolu** : les secondes du journal affiché par le mod de mesures et celles du journal du SDK ne sont pas dans la même unité (rapport mesuré ≈ 1,56 sur les écarts entre touchers : 150, 180, 190 s contre 98, 114, 122 s). À ne pas mélanger sans conversion ; sans effet sur la comparaison ovale / cercle, qui n'utilise que le journal affiché.
- Correspondance des avions (journal affiché ↔ journal du SDK) : avion 2 = id 10, avion 4 = id 18, avion 1 = id 9, avion 3 = id 17.

**Suite** : essais 2 et 3 avec la même copie (le moddeur) ; puis décision sur le créneau et sur la pose du cercle dans le vrai exécutable (accord séparé).

## 13. Créneau élargi : 2e copie d'essai « les deux » (27/10/2026, 18 h 20)

- **Demande du moddeur** après l'essai 1 : il est content tant que **l'intervalle de créneau est plus grand** (la piste peut être donnée pendant ≈ 26 s de vol au lieu d'un seul tick). Il n'a pas demandé d'essais supplémentaires du cercle seul.
- **Copie posée à côté du jeu** : `…\Carrier Command 2\carrier_command_test_cercle_creneau.exe` = exécutable actuel + `atterrissage_cercle` + `atterrissage_creneau`, somme **`563994278CB0B3ED1504C99B43087B3CEFABA98627AA68C84FBB3B797860202C`** (celle annoncée par l'étude, section 3, calculée avant : **identique**). Posée avec `patch_exe.py` sur une copie hors du jeu (modules `atterrissage_cercle` puis `atterrissage_creneau`), puis copiée et relue. Le vrai `carrier_command.exe` est inchangé (`8E7FCBB6…`) ; `carrier_command_test_cercle.exe` (cercle seul) est toujours là. **Pas lancée** : seul son démarrage a été vérifié sur la copie « cercle » ; le créneau change 3 sauts du circuit, donc la première vraie preuve sera un essai avec des avions en attente (un plantage se verrait tout de suite).
- **Comment on verra que le créneau agit** : (1) journal affiché : « ratées » doit rester 0, écarts entre pistes ≤ 1:50, attente perdue après l'arrivée du précédent au hangar proche de 0 ; (2) journal du SDK (`trajets_circuit.py`) : l'avion quitte le cercle pour l'approche **n'importe où** sur la partie arrière du cercle (plus seulement au passage du portillon).

**Prochain essai (préparé le 28/10/2026, à faire par le moddeur)** : avec `carrier_command_test_cercle_creneau.exe` (jeu normal fermé : un seul jeu à la fois ; le 28/10 à 08:08 un `carrier_command.exe` normal tournait depuis 07:53, lancé par un autre chantier ou par le moddeur). Même protocole que l'essai 1 (section 12) : partie neuve, navire à l'arrêt, 4 avions sortis (A1, A2, A5, A6) puis rappelés tout de suite, capture du journal à « FINI en … », capture de la carte pendant l'attente. Dès la fermeture, **le journal du SDK est recopié automatiquement** (surveillance en arrière-plan de la session d'étude) dans `essais/cc2x_essai_cercle_creneau_AAAAMMJJ_HHMMSS.log` ; sinon le copier à la main **avant** de relancer un autre jeu (le journal est recréé à chaque lancement). Lecture : `python -I trajets_circuit.py <copie du journal>` (hors du dossier du jeu).

**Mise à jour du 28/10/2026 (vers 10 h 30) : le vrai exécutable a changé, par une autre conversation.** `carrier_command.exe` est maintenant `0C5DFE52DFDF1AE002B0CF8B25C6B32CC1EEC953A80E856D37E4016CF2FE120B` (modifié à 10:25:36) = `ascenseur_x2` + `temps_x2` + **`pont_retour_x2`** (le roulage de retour sur le pont, piste → ascenseur, va 2 fois plus vite ; module de l'étude « roulage de retour », 1 changement). Je n'y ai pas touché ; ce n'est pas moi. Conséquences pour cette étude :
- **Mes deux copies d'essai (`…_cercle.exe` 80E9D871…, `…_cercle_creneau.exe` 56399427…) ont été faites AVANT et n'ont PAS `pont_retour_x2`** : elles sont toujours identiques à l'ancien exe (8E7FCBB6…) + mes modules. Elles restent valables pour comparer avec l'essai 1 (8:58, mêmes conditions), mais elles ne montrent plus ce que donnerait le vrai jeu actuel.
- **Le roulage ×2 touche justement ce qui bornait le gain** : la piste reste occupée ≈ de la touche au hangar (≈ 1:40 mesuré) ; si ce trajet raccourcit, le plancher baisse et le créneau élargi pèse davantage. Le témoin « pont > hangar » (0:55) doit baisser avec `pont_retour_x2` (à lire, pas à supposer).
- **Compatibilité vérifiée hors jeu** (sur une copie dans le dossier temporaire de la session, `patch_exe.py activer` avec `--sauvegarde` = l'original) : l'exécutable actuel + `atterrissage_cercle` + `atterrissage_creneau` donne la somme **`67E6028DE50F96074106A0103745DDD6F6402991EBD5E897D7A6C8AE617BC229`**, état « PATCHE (ascenseur_x2, atterrissage_cercle, atterrissage_creneau, pont_retour_x2, temps_x2 ; cohérent avec l'original) » : aucun recouvrement. Le vrai exécutable reste `0C5DFE52…`. Une 3e copie d'essai « jeu actuel + cercle + créneau » (= ce somme) n'est **pas** posée : choix à faire par le moddeur.

**Mise à jour du 29/10/2026 (09 h) : Steam a mis le jeu à jour le 28/10 à 21:30, et la 3e copie est posée.**
- **Le `carrier_command.exe` de Steam est maintenant un autre build** (`461E12623BACB7DE29CA27B4614425C87E8DF2C8327A5E958A957C850EFFE42A`, 11 354 112 octets, build Steam 26277078, recompilé le 28/10 ; l'horodatage PE n'est plus `0x6a36c177`). Il n'a **aucun** de nos patchs (ni `0C5DFE52…`, qui a été écrasé). `patch_exe.py etat` répond « INCONNU » (40 endroits ne sont ni l'original ni le patch). **Mes modules `atterrissage_cercle` et `_creneau` ne s'appliquent donc plus au jeu normal** : ils sont à porter (adresses décalées, voir `tour/etude_mise_a_jour/ETUDE.md`, conversation « mise à jour »). Je n'ai rien patché ni lancé sur l'exe de Steam.
- **Les copies d'essai sont de l'ancien build et restent valables** : elles gardent l'horodatage `0x6a36c177`, donc le SDK s'y active comme avant (les données `rom_0` n'ont pas changé d'après l'étude de mise à jour ; **compatibilité de l'ancien exe avec les nouveaux fichiers de Steam : inférée, jamais essayée en jeu** **[PÉRIMÉ depuis le 29/10 : essayée sur une partie complète à l'essai 2 (§14), sans plantage ; une seule partie]**).
- **3e copie posée à la demande du moddeur** (« prépare la 3e copie d'essai : exe actuel + cercle + créneau, à côté du jeu, sans la lancer ») : `…\Carrier Command 2\carrier_command_test_cercle_creneau_pont.exe`, somme **`67E6028DE50F96074106A0103745DDD6F6402991EBD5E897D7A6C8AE617BC229`**. Fabriquée **deux fois, par deux chemins** (a : ancien exe patché `0C5DFE52…` + cercle + créneau ; b : original sauvegardé `1C9A01C3…` + `ascenseur_x2`, `temps_x2`, `pont_retour_x2`, `atterrissage_cercle`, `atterrissage_creneau`), même somme que celle annoncée avant ; état relu : « cohérent avec l'original », aucun recouvrement. Contenu = l'ancien jeu tel qu'il était à 10:30 le 28/10 (avec le roulage ×2) + mon circuit. **Non lancée.** Pour la retirer : supprimer le fichier.
- **Avant de la lancer** : le jeu normal doit être fermé (`Get-Process carrier_command*`), et il vaut mieux attendre la décision du moddeur sur la voie A/B de la mise à jour (ce fichier est la voie A). Un lancement par Steam démarrerait le **nouvel** exe, pas celui-ci : double-clic direct sur la copie.
- **Ce que cet essai dira** : l'effet du circuit + créneau + roulage ×2 ensemble, sur l'ancien build. Les anciennes copies (`…_cercle.exe`, `…_cercle_creneau.exe`) servent à comparer avec l'essai 1 (sans roulage ×2).

## 14. Essai 2 : copie « pont » (cercle + créneau + roulage ×2), 29/10/2026, 16:47-16:54

**Conditions.** Copie `carrier_command_test_cercle_creneau_pont.exe` (`67E6028D…`, ancien build 1.5.18). Jeu normal fermé, Steam ouvert. **Lancée par moi à 16:47:02 (PID 1904) sur la demande écrite du moddeur dans le chat (« Lance-le pour moi »)**, double-clic direct (`Start-Process`, pas par Steam) ; fermée par le moddeur à 16:54:38 (« session ended » dans le journal). Partie neuve, 4 avions (ids 9, 10, 17, 18 ; vus en vol près du bateau à t = 177, 222, 264, 307 s du journal du SDK). Le SDK 0.5.0 s'est activé (« ready for 1.5.18-win32 »), `cc2x_modes.dll` (observation seule, `eco_enabled=0`) et `cc2x_frein.dll` (`brake_enabled=1`) ont chargé. Journal du SDK copié automatiquement dans `essais/cc2x_essai_cercle_creneau_pont_20261029_165455.log` (1 291 498 octets) ; capture du moddeur : `essais/essai_pont_capture_journal.png` ; analyses : `essais/essai_pont_trajets.txt`, script `depart_cercle.py`.

**MESURÉ (capture du moddeur, journal « temps de jeu » affiché)** : piste 4:03 / 1:24 / 2:52 / 5:49 (avions 1 à 4), pont 5:01 / 2:30 / 3:41 / 6:37, hangar 5:33 / 3:05 / 4:15 / 7:09. **« FINI en 7:09 : 4 avions », piste toutes les 1:28, ratées 0, approche 0:55, pont>hangar 0:33.** Écarts réels entre pistes (triés) : 1:28, **1:11**, 1:46.

| | FINI en | piste toutes les | écart mini | ratées | approche | pont>hangar |
|---|---|---|---|---|---|---|
| ovale d'origine (essais d'avant) | 10:10 ; 8:47 | 1:59 à 2:15 | — | — | — | — |
| essai 1 : cercle seul (27/10) | 8:58 | 1:55 | 1:43 | 0 | 0:50 | 0:55 |
| **essai 2 : cercle + créneau + roulage ×2** | **7:09** | **1:28** | **1:11** | **0** | **0:55** | **0:33** |

**Lecture honnête.**
- **Aucun plantage, 0 raté** : c'est la **première fois que les 3 sauts du créneau tournent en jeu**, sans incident (MESURÉ : 4 poses réussies, journal sans erreur).
- **Les témoins bougent comme prévu** : « approche » inchangé (0:50 → 0:55, bruit) ; « pont>hangar » baisse (0:55 → 0:33), ce qui est l'effet attendu du roulage ×2 (`pont_retour_x2`) ; le roulage est donc bien actif dans cette copie.
- **Écart mini entre pistes : 1:11 contre 1:43** : la piste est redonnée plus tôt. Piste→pont (≈ 0:48 à 1:06 d'après la capture) est plus court que l'écart de 1:11 : INFÉRÉ que la piste est libre dès que l'avion passe sur le pont, pas seulement au hangar ; l'ancienne lecture « occupation ≈ piste→hangar ≈ 1:40 » est donc à corriger (1 essai : à reconfirmer).
- **Le créneau agit, INFÉRÉ (signature, pas preuve directe)** : sur les positions du journal du SDK (≈ 1 point toutes les 10 s, soit ≈ 800 m), **2 avions sur 4 (17 et 18) coupent à l'intérieur du cercle juste avant le portillon** : distance au centre 595 m (avion 17, angle 290°) et 551 m (avion 18, angle 303°) contre 780-800 m sur un tour normal. Dans l'essai 1 (cercle seul, mêmes avions, même script) **aucun** avion ne coupe (distances 782-800 m à 274°-331°). Les avions 9 et 10 suivent le cercle jusqu'au portillon (270°) sans couper. Lecture : 17 et 18 ont reçu la piste **avant** le portillon (créneau), puis ont pris la 2e moitié du virage en ligne droite. Pour le prouver il faudrait lire l'état du circuit de chaque avion (non fait) ou un journal à pas plus fin.
- **Frein de l'extension** : actif dans cette copie (`brake_enabled=1`) mais **n'a rien freiné** : 117 lignes `eligible=0`, 0 ligne `eligible=1`, `brk=0` partout (MESURÉ) ; il n'a donc pas faussé la mesure.
- **Ce qu'on ne peut PAS dire** : (1) **un seul essai** ; (2) **trois changements à la fois par rapport à l'essai 1** (créneau + roulage ×2 ; le cercle est commun) : on ne sait pas répartir les 1:49 gagnés (8:58 → 7:09) entre le créneau et le roulage ×2 ; (3) l'essai 1 date de l'ancien exe `8E7FCBB6` sans roulage ×2 : le bon témoin « sans créneau, avec roulage ×2 » n'existe pas ; (4) je n'ai **pas vérifié que le moddeur n'a piloté aucun avion** pendant l'essai (le journal du frein ne montre aucun avion éligible, ce qui va dans ce sens) ; (5) l'unité de temps journal affiché / journal du SDK reste ≈ 1,56-1,6 (550 s de journal affiché pour 890 s de journal du SDK) : non résolu, sans effet sur la comparaison de journaux affichés entre eux ; (6) l'ancien exe tourne avec les fichiers du jeu mis à jour par Steam : il a fonctionné ici (INFÉRÉ « compatible » devient **MESURÉ sur cette partie**, une seule).
- **Pour séparer les effets** (non fait, accord du moddeur à demander) : une copie « cercle + roulage ×2 » sans créneau (à fabriquer hors jeu comme les autres), puis un essai identique ; sinon rester sur « les trois ensemble marchent et donnent 7:09 sur 1 essai ».

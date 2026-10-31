# Étude : libérer la piste plus tôt (A) et préparer les avions sur le pont (B)

25/10/2026, lecture seule (programme d'origine `sauvegarde/build_mac_origine`, fichier du navire
`vehicle_chassis_carrier.xml`). Rien n'a été modifié dans le jeu ni dans l'atelier.

## En bref

| Idée | Verdict | Difficulté | Sessions | Gain estimé | Risque |
|---|---|---|---|---|---|
| A telle quelle : rendre la piste quand l'avion a dégagé | **non** : le jeu la rend déjà au premier moment sûr | 5/10 | 2 | ~7 s par avion | collision avec l'avion qui attend à 12 m de l'axe |
| **A' : rouler 3× plus vite sur le pont au retour** (recommandé) | **oui** | **1-2/10** | **1 courte** | piste occupée 88 s → ~62 s par avion ; 4 avions : −0:30 à −1:30 sur 7:28 | aucun nouveau risque de collision |
| B : avions garés sur le pont, prêts à partir (demande n° 2023) | possible, gros chantier, **déconseillé maintenant** | 8/10 | 4-6 (+ Windows) | seulement pour une vague préparée à l'avance : 4 départs ~2:15 → ~1:00-1:15 | collisions sur le pont, avions bloqués après une sauvegarde, pont encombré pendant les retours |
| B' : rouler plus vite de l'ascenseur au bout de piste au départ | oui, à mesurer d'abord | 2/10 | 1 | incertain (~15-30 s sur 4 départs) | faible |

## Ce qui se passe vraiment sur le pont après un atterrissage

Plan du pont (repère du bateau, x vers tribord, z vers la proue, mètres) : piste sur l'axe x = 0, de
`runway_start` (z −68, à l'arrière) à `runway_end` (z 82, à l'avant) ; `taxi_a` (0, −44) **sur la piste** ;
`lift_upper_wait` (12, −32) ; plateforme de l'ascenseur `lift_upper` (27,5, −32), pavé x 21…33.

Un avion qui se pose (états de piste, table de saut 0x1001b25d8, index = état − 3) :

| État | Ce que fait l'avion | Où | Durée (ascenseur ×2) |
|---|---|---|---|
| 3 | approche | en l'air, derrière le bateau | } « approche » du journal : 0:49 |
| 4 « rails » | roule sur la piste **jusqu'au bout avant** (99 % du chemin vers z 82) | sur l'axe | } |
| 5 | **recule sur toute la piste** de l'avant (z ≈ 81) jusqu'à `taxi_a` (z −44) : ~125 m | **sur l'axe, en plein dans la zone de toucher** | **28,5 s** |
| 6 | `taxi_a` → `lift_upper_wait` (~17 m en biais) | quitte l'axe | 7,1 s |
| 7 | `lift_upper_wait` → plateforme (15,5 m) ; attend l'ascenseur en haut et libre | à côté de la piste, puis dessus l'ascenseur | 6,8 s |

Total calculé 42 s ; mesuré par le journal le 23/10 : la piste se libère 38-41 s après le « toucher » (le
journal note le toucher quand l'avion passe en état 5, dock_state 6). Le modèle colle.

**Où la piste est prise** : case « piste » 0x80 du gestionnaire. Avions : bloc de la porte 0x1001af914,
`mov %eax, 0x80(%r14)` à 0x1001af95c puis état 3 à 0x1001af963. Hélicos : 0x1001adb23.
**Où elle est rendue** : fin de l'état 7, échange 0x80 ↔ 0x7c à 0x1001ae183 (l'avion passe dans la case
« ascenseur »). Aussi : approche ratée (0x1001b254a) et véhicule disparu / changement de mode (0x1001ad624,
0x1001ae753).

## A — Rendre la piste plus tôt : pourquoi non, et quoi faire à la place

L'avion posé **reste sur l'axe de la piste pendant ~29 des 42 s**, puis ne s'en écarte que peu à peu : il
recule de l'avant vers l'arrière, droit vers l'avion suivant qui arrive. Rendre la piste pendant l'état 5 = le suivant se pose sur lui (choc de face).

Le premier endroit hors de l'axe est `lift_upper_wait` (fin de l'état 6). Mais là, l'avion est tourné de 90°
(nez vers le travers) à 12 m de l'axe : son nez arrive vers x ≈ 6 m, et les ailes de l'avion qui se pose
débordent de plusieurs mètres de l'axe (plus l'écart de l'approche). Le jeu d'origine n'a jamais eu besoin de
cette marge, il n'y en a pas. Le seul endroit vraiment dégagé est la plateforme de l'ascenseur… c'est
exactement là que le jeu rend la piste aujourd'hui.

Le faire quand même à `lift_upper_wait` demanderait une greffe (la case 0x80 est aussi celle qui fait rouler
l'avion : il faut le passer d'avance dans la case ascenseur, l'avion « sauterait » de 15 m sur la plateforme)
pour ~7 s gagnées par avion et un vrai risque de collision. **Pas rentable.**

**À la place (A')** : garder la règle du jeu (piste réservée jusqu'à l'ascenseur), mais **raccourcir le temps
passé sur le pont**. Chaque tronçon de roulage avance de `v / (L × 30)` par tick ; les trois multiplications
par 30 des états 5, 6 et 7 sont des instructions distinctes, **non touchées par l'ascenseur ×2** (lui change
l'accélération et le plafond, d'autres octets) ni par aucun autre module :

| Adresse | Instruction (octets) | État |
|---|---|---|
| 0x1001b0824 | `mulss [30.0], %xmm1` (f30f590d6c906b02), atteinte seulement par le `jbe` de 0x1001adf65 | 5 (recul sur la piste) |
| 0x1001ae07c | `mulss [30.0], %xmm1` (f30f590d14b86b02), seulement depuis l'état 6 | 6 |
| 0x1001b0831 | `mulss [30.0], %xmm1` (f30f590d5f906b02), seulement par le `jbe` de 0x1001ae134 | 7 |

Rediriger ces trois lectures de 30.0 (0x102869898) vers **10.0** (0x1028697b4, existe déjà) = roulage ×3, ou
vers **15.0** (0x1028699cc) = ×2. Trois retouches « rip » de l'atelier, générées depuis le désassemblage.

| Temps sur le pont | aujourd'hui (asc. ×2) | A' ×2 | A' ×3 |
|---|---|---|---|
| état 5 (recul 125 m) | 28,5 s | 14,6 s | 10,0 s |
| états 6 + 7 | 13,9 s | 7,7 s | 5,7 s |
| **total** | **42 s** | **22 s** | **16 s** |
| vitesse maxi du recul | 18 km/h | 36 km/h | 54 km/h |

Gain sur la file (simulateur `outil/generateurs/simuler_file_atterrissage.py`, circuit en cercle + créneau
élargi, 4 avions) : occupation de la piste 88 s → ~62 s.
- 4 avions **groupés** (300 m d'écart) : 394 → 366 s, seulement −28 s. Le circuit fait 94 s : quand la piste se
  libère, l'avion suivant vient de passer la fenêtre et doit finir son tour. Le gain se limite au dernier avion.
- 4 avions **dispersés** (moyenne de 400 tirages) : 401 → 279 s (**−30 %**), écart moyen entre deux pistes
  104 → 72 s.
- Ton essai du 23/10 était entre les deux (écarts 98, 80, 96 s). Estimation honnête : **−0:30 à −1:30 sur les
  7:28**. Le journal le mesurera tout seul.

Risques de A' :
- collision : **aucun nouveau** (rien ne change dans l'attribution de la piste) ;
- visuel : l'avion recule vite (54 km/h en ×3, 36 km/h en ×2) et démarre sec ; il est porté par le bateau
  (accroche déplacée à chaque tick, comme aujourd'hui), donc pas de risque qu'il se renverse ;
- les hélicos passent aussi par les états 5-7 : leur court roulage vers l'ascenseur sera lui aussi plus rapide
  (petit bonus pour les 4:22) ;
- le porte-avions adverse utilise le même code : ses retours aussi seront plus rapides (déjà vrai pour
  l'ascenseur ×2).

Pour aller plus loin un jour : le vrai frein des avions groupés est le **tour du circuit** (94 s), pas la piste.
Piste à étudier séparément : espacer les avions dans le circuit ou rétrécir le cercle pour qu'il colle à la
nouvelle occupation (~62 s). Autre piste non étudiée : arrêter l'avion plus tôt sur la piste (comme un brin
d'arrêt), ce qui supprimerait la moitié du recul, au prix d'un arrêt brutal à l'écran.

## B — Avions garés sur le pont, prêts à partir

**Ce que le jeu fait déjà** (lu dans le code des sorties) : il enchaîne déjà trois avions — un sur la grue
(case 0x78), un sur l'ascenseur (0x7c), un sur la piste (0x80). Avec le bouton rouge « attendre au
lancement », l'avion de tête attend au bout arrière de la piste (dock_state 7, test 0x1001b0185 : seul l'avion
autorisé, 0x28 du gestionnaire, part), le suivant attend en haut de l'ascenseur, le troisième sur la grue.
Il n'existe **aucune place de stationnement** ailleurs : les 8 places `air1..air8` sont toutes dans le hangar
(y 13,5).

Ce qu'il faudrait pour en garer davantage sur le pont :
1. **Places sur le pont** : des nœuds et des chemins nouveaux dans `vehicle_chassis_carrier.xml` (ascenseur →
   place n, place n → `runway_start`). Le fichier est facile à remplacer (module « fichier »). Mais il faut des
   places **loin de l'axe** (ailes des avions qui se posent ou décollent) et hors des trajets existants :
   probablement le côté tribord devant l'ascenseur (x ≈ 18-33, z −18…80), soit 2 à 4 places au mieux.
   À vérifier dans le modèle 3D du pont (bord du pont, îlot, plateforme).
2. **Logique** (greffe de code, plusieurs Ko, en C comme pour les hélicos) : en mode sortie, si on prépare,
   l'avion monté va sur une place libre au lieu du bout de piste, l'ascenseur redescend chercher le suivant ;
   au lancement, les avions garés partent d'abord, chacun par son chemin jusqu'au bout de piste. On peut
   réutiliser l'état 7 « attente au lancement » et déduire la place du numéro de baie du hangar : pas besoin
   de mémoire nouvelle par bateau (important : le porte-avions adverse passe par le même code).
3. **Commande** : réutiliser le bouton rouge (rouge = on prépare et on gare ; on relâche = tout part à la
   suite), pour ne rien ajouter aux écrans.
4. **Piste gardée libre pour les retours** : le bateau est soit en mode retours, soit en mode sorties, jamais
   les deux. Pendant un retour, le code des atterrissages ignore les avions garés ; ils gardent leur baie du
   hangar. Les places doivent donc être sûres même quand un avion se pose à côté.
5. **Sauvegardes** : un avion garé est sauvegardé avec son état, mais probablement pas sa position sur le pont
   → au chargement, il faut le traiter comme « au hangar ». Retirer le module avec des avions garés pourrait
   les laisser bloqués : il faudrait tout ranger avant.

Gain : seulement quand une vague a été préparée à l'avance, pendant un moment calme (la préparation prend le
même temps qu'un départ aujourd'hui). Alors 4 départs passeraient d'environ 2:15 à ~1:00-1:15 (estimation :
~15 s de roulage + ~5 s de course par avion). Aucun gain pour un départ improvisé.

Risques : collisions sur le pont (le jeu détruit bien les appareils qui se touchent, vu le 24/10 avec les
hélicos), place réelle sur le pont incertaine, avions garés exposés aux tirs, sauvegardes, affichage chez les
joueurs qui rejoignent (probablement bon : la position passe par l'accroche, comme pendant le roulage).
Difficulté 8/10, 4 à 6 sessions, à refaire sur Windows.

**Plus simple (B')** : au départ, l'avion roule ~56 m de l'ascenseur au bout de piste (~22 s avec
l'ascenseur ×2) avant sa course. Le rendre 2 à 3× plus rapide, comme A', coûte 2/10 et 1 session. Mais on ne
sait pas encore si c'est ce roulage ou la grue + l'ascenseur qui freine les départs : le journal ne chronomètre
que les retours. À mesurer avant (le journal peut apprendre les départs : états 2/3 du dock_state).

## Annexe pour la phase 2 (A')

- Module `pont_retour` (nom provisoire), type « programme », 3 retouches « rip » : (0x1001b0824,
  "f30f590d6c906b02", 0x102869898 → 0x1028697b4), (0x1001ae07c, "f30f590d14b86b02", …),
  (0x1001b0831, "f30f590d5f906b02", …). Facteur 1/3 pas exact en float : passer `None` et vérifier la valeur
  10.0 à la main dans le test (ou ×2 avec 15.0 à 0x1028699cc, facteur 0,5 exact).
- Aucune adresse commune avec ascenseur_x2 (0x1001adf35/41, 0x1001ae02a/36, 0x1001ae104/10), atterrissage
  (0x1001af785…0x1001afaf2), helicos_* (0x1001ad3ef, 0x1001ad3fc, 0x1001ad57a, 0x1001b1066).
- Tronçon : v = min(v + 0,1, 5, reste) (avec asc. ×2), avance v / (L × div) ; arrivée quand reste < 0,1 m ; pas de
  dépassement possible (v ≤ reste).
- Mesure : même protocole que le 23/10 (asc. ×2 + atterrissage actifs, même sauvegarde, navire à l'arrêt, 4
  avions lancés puis rappelés), lire le journal : total, écart entre pistes, pont → hangar (51 s le 23/10).

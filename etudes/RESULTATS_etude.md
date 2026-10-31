# Résultats de l'étude : deux hélicos à la fois, un 2e ascenseur, autres pistes

Étude du 23/10/2026, **lecture seule** : rien n'a été modifié dans le jeu ni dans l'atelier. Tout a été lu dans
la copie d'origine du programme (`sauvegarde/build_mac_origine`, md5 b0107170…) et dans
`rom_0/game_objects/vehicle_chassis_carrier.xml`. Les adresses sont celles du programme Mac du 05/01/2026.

## En bref

| Piste | Verdict | Difficulté | Sessions | Gain attendu |
|---|---|---|---|---|
| **A1 — hélicos posés directement sur l'ascenseur** (recommandé) | faisable, petite greffe de code | 5/10 | 2 | hélicos ~2× plus rapides à rentrer (estimation à mesurer) |
| A2 — deux places de pose sur le pont (vraie double pose) | faisable, grosse greffe | 8/10 | 3-4 | pas mieux que A1, beaucoup plus cher |
| **B — deuxième ascenseur** | possible en théorie, déconseillé | 9/10 | 8-12 (+3-5 pour Windows) | faible pour les avions (la piste reste unique) |

Le vrai goulot n'est **pas l'ascenseur** : c'est **la piste**, qui est une case unique partagée par les avions et
les hélicos, et qui reste prise jusqu'à ce que l'appareil soit **monté sur l'ascenseur**. Un hélico occupe donc la
piste pendant son approche **et** pendant ~100 m de roulage sur le pont. A1 supprime ce roulage pour les hélicos.

---

## A. Poser deux hélicos à la fois

### Comment le jeu pose un hélico aujourd'hui

Tout se passe dans `c_vehicle_server_carrier::docking_manager_air::update` (0x1001accd8 → 0x1001b2618).
Le gestionnaire a **une seule case par étape** (une case = le numéro d'un seul appareil) :

| Case (dans le gestionnaire) | Rôle | Une seule ? |
|---|---|---|
| 0x48 `docking_queue` | file d'attente commune avions + hélicos | oui, une file |
| 0x80 « piste » | l'appareil qui se pose et roule sur le pont | **oui** |
| 0x7c « ascenseur » | l'appareil sur la plateforme | oui |
| 0x78 « grue » | l'appareil porté par la grue du hangar | oui |
| 0x84 « décollage hélico » | hélico qui décolle depuis l'ascenseur (sorties seulement) | oui |

Le trajet d'un hélico, étape par étape (repère du bateau : x vers tribord, z vers la proue, pont à y = 20) :

1. **Attente** : les hélicos tiennent un point fixe derrière le bateau, x = −100, z = −240 − 60 × rang, altitude 80
   (0x1001af4af…0x1001af551). Le premier reçoit la piste quand il est à moins de 100 m de la première place
   (0x1001adadc, constantes (−100, −240) à 0x10286b880 et 100² à 0x10286998c) **et** que la piste est libre.
2. **Approche** (état de piste 3, partie hélico 0x1001ad3ef…0x1001ad61f puis 0x1001b102e) : l'hélico vise un point
   sur l'axe de piste 50 m devant lui (au plus z = 52) et descend selon la distance au **milieu de la piste**
   (z = 7) : hauteur visée = ½ × (7 − z), bornée −2…80 m. À moins de 20 m du milieu : train sorti, état « atterrissage ».
3. **Toucher** (0x1001b1f5c…0x1001b2058, commun avions/hélicos) : vitesse relative au bateau < 10 m/s **et** toutes les
   roues au contact. L'hélico est alors accroché au bateau (sa future place du hangar, 0x90) et l'état passe à 5.
   Pas de « rails » pour les hélicos (l'état 4 est celui des avions).
4. **Roulage en 3 tronçons**, la vitesse repartant de 0 à chaque tronçon (donc 3 freinages) :
   état 5 du point de toucher (z ≈ 7 à 30) jusqu'à `taxi_a` (0, −44) ; état 6 `taxi_a` → `lift_upper_wait` (12, −32) ;
   attente que l'ascenseur soit en haut et libre ; état 7 → `lift_upper` (27,5, −32). Soit ~90 à 110 m.
5. **Fin de l'état 7** (0x1001ae13a…0x1001ae231) : l'appareil passe dans la case « ascenseur » et **la piste est
   enfin libérée** (échange 0x80 ↔ 0x7c à 0x1001ae183). L'hélico suivant ne peut commencer son approche qu'à ce moment.
6. Ascenseur en bas → roulage du bas de l'ascenseur au centre du hangar (27,5 m) → la grue le prend → l'ascenseur
   remonte aussitôt (0x1001ad6a4…, 0x1001b1164).

En plus, **le porte-avions ne fait jamais les deux à la fois** : il est soit en mode « retours » (1), soit en mode
« sorties » (2) (0x1001acd2b ; retour au repos 0x1001ae780 quand toutes les cases sont vides). Les retours ont la priorité.

### Où est exactement la limite « un seul à la fois »

C'est la **case piste unique (0x80)**, avec tout ce qui va avec : un seul état de piste (0x24), un seul chemin en cours
(0xf0, avancement 0x108, vitesse 0x10c), une seule place réservée (0x90), un seul chronomètre d'approche (0x110).
Le gestionnaire s'arrête vers 0x178 et l'objet suivant commence juste après : **il n'y a pas de place pour une 2e case**.

### Ce qu'il faudrait changer

**A0 — réglages seuls (2/10, gain faible)** : rapprocher le point d'attente (−240 → −120, constante existante
0x102869cfc, + seuil 100 m → 122 m avec 15000 à 0x102869a0c). Gagne quelques secondes de vol par hélico. On ne peut
**pas** déplacer le point de toucher par simple réglage : la distance au milieu de piste sert aussi tout l'atterrissage
des avions (pente de descente à 0x1001b1be6, seuils 800/200/400 m), y toucher casserait les avions.

**A1 — hélicos posés sur l'ascenseur (recommandé, 5/10, 2 sessions)** : les hélicos décollent déjà directement de la
plateforme (case 0x84, 0x1001ae3c1) ; on fait la même chose à l'atterrissage.
- Greffe 1, au début de la partie hélico de l'approche (0x1001ad3ef) : viser le point `lift_upper` (27,5, 20, −32) au lieu
  de l'axe de piste, tourné comme la plateforme (les appareils y sont tournés de 90°) ; descendre selon la distance à
  la plateforme ; **rester en vol stationnaire ~15 m au-dessus** tant qu'elle n'est pas en haut et libre (0x7c = −1,
  position 0x1518 du bateau ≈ 0). Remplir la case −0x90 de la pile pour que le train sorte (test à 0x1001b106e).
- Greffe 2, juste après le toucher (0x1001b22b8, avant le passage à l'état 5) : si c'est un hélico, posé à moins de
  ~6 m de la plateforme, et la plateforme prête → sauter dans la fin de l'état 7 existante (0x1001ae13a), qui fait déjà
  tout : piste libérée, case ascenseur, chemin vers le hangar. Sinon, comportement d'origine (roulage).
- Taille : ~200 à 400 octets de code neuf. Il y a **11 Ko libres** dans l'en-tête du programme (entre la fin des
  commandes de chargement, 0xF40, et le début du code, 0x3BD0), dans la partie exécutable. Plan de secours si Rosetta
  refusait d'y exécuter du code : réutiliser le code de démonstration ImGui jamais appelé (`ExampleAppConsole`,
  `ExampleAppLog`, vers 0x1000a4c78).
- Les avions ne passent jamais par ces greffes. Le module de l'autre conversation (circuit des avions,
  0x1001af85b…0x1001afaf2) ne touche pas les mêmes octets.

**A2 — deux places de pose (8/10, 3-4 sessions)** : garder le 2e hélico dans la file d'attente avec deux états
nouveaux (« se pose sur la place 2 », « garé sur la place 2 »), une place à l'avant de la piste (z ≈ 60), le toucher et
l'accrochage recopiés, les messages aux joueurs recopiés (0x1001b2233…0x1001b22b6), la passation quand la piste se
libère, et l'interdiction de donner la piste à un avion tant qu'un hélico y est garé. Beaucoup de code neuf, pour un gain
qui ne dépasse pas celui de A1.

### Verdict A

**A1** : patch de comportement par petite greffe de code. Difficulté **5/10**, **2 sessions** (1 : écrire et tester sur
copies, relecture objdump ; 2 : réglage après ton test : hauteur d'attente, vitesse de descente). Windows : à refaire
ensuite (logique courte, mais sans noms de fonctions).

Estimation, **à vérifier par une mesure** : aujourd'hui, avec l'ascenseur ×2, un hélico occupe la piste ~50-60 s
(≈ 25 s d'approche, chiffre deviné, + ≈ 30 s de roulage en 3 tronçons) ; avec A1, ~25-35 s, l'ascenseur (≈ 20 s par
aller-retour avec ×2) n'étant pas le nouveau goulot. Soit **environ deux fois plus vite pour une vague d'hélicos**.

**Ce que tu verrais en jeu** : les hélicos ne roulent plus sur le pont. Ils se posent sur la plateforme de l'ascenseur
(à tribord, au milieu du bateau), déjà tournés comme il faut, et descendent aussitôt. Le suivant arrive pendant ce temps
et attend en vol stationnaire au-dessus de la plateforme si elle n'est pas encore remontée : deux hélicos à l'ascenseur
en même temps, l'un qui descend, l'autre qui attend.

**Ce qui pourrait mal tourner** :
- pose imprécise : un petit saut (1-3 m) quand l'hélico est recalé sur la plateforme ;
- hélico qui rebondit ou ne « touche » pas (contact des roues sur la plateforme, qui est une pièce physique à part) ;
- attente au-dessus trop longue → au bout de 2 min (3600 ticks, 0xe10) le jeu le renvoie dans la file (comme un raté) ;
- code exécuté dans l'en-tête : si Rosetta refuse, plantage au premier hélico → l'atelier retire le patch, on passe au
  plan de secours ;
- les porte-avions de l'IA en profitent aussi (même programme) ; en multijoueur, seulement si c'est toi qui héberges.

**Première étape concrète** : une mesure de référence en jeu (5 min, avec les patchs actuels) : rappeler 2 à 4 hélicos
et noter l'heure de jeu à l'ordre de retour, à chaque toucher du pont, et quand le dernier est rangé. Puis la session
d'écriture du module `helicos_ascenseur` (après la mesure du module `atterrissage`, une modification à la fois).

---

## B. Un deuxième ascenseur

### Inventaire (vérifié et complété)

**Fichier du navire** `vehicle_chassis_carrier.xml` :
- Corps physiques : `hull` (collisions `meshes/aircraft_carrier/aircraft_carrier_hangar_physics.cphys`, 234 Ko),
  `lift` (collisions `meshes/chassis_carrier_lift_phys.cphys` = **une seule boîte** x 21…33, y 19…20, z −45,5…−18,2 :
  plateforme de 12 × 27 m), `lift_personnel`.
- Contraintes `lift_constraint` (type 0, course −9…0) et `lift_personnel` (type 4). Les réglages `drive_*` ne servent à
  rien : le programme impose la position.
- Modèles 3D réellement utilisés : `aircraft_carrier_shell/aircraft_carrier_lift.mesh` (plateforme),
  `aircraft_carrier_hangar.mesh` (pont + hangar), `gantry_crane*.mesh` (grue). **Correction de la fiche** :
  `chassis_carrier.mesh`, `chassis_carrier_phys.cphys`, `chassis_carrier_lift.mesh` et `chassis_carrier_crane*` ne sont
  référencés par aucun fichier : ce sont des restes.
- Chemins : 47 nœuds, 48 liens. Le programme n'en utilise que 6 par leur nom : `runway`, `runway_lift`,
  `runway_reverse_a`, `runway_reverse_b`, `lift_top_reverse`, `load_lift_lower` (`runway_reverse` n'est jamais lu).
  Nœuds lus par leur nom (`docking_manager_air::build` 0x1001a02ca) : `hanger_center`, `lift_lower`, `lift_upper`,
  `runway_start`, `runway_end`.
- Maillages de navigation : `lift_aircraft` attaché au corps n° 1 (la plateforme).

**Collisions (.cphys)** : enfin identifié. En-tête « cphy », version 1, nombre de morceaux, puis des **maillages convexes
PhysX « cuisinés »** (signatures `NXS\x01CVXM`, `ICE CLHL`). La coque en compte **477**. La plateforme est un simple pavé
de 432 octets, qu'on pourrait recopier en changeant les coordonnées. Mais percer le pont veut dire retrouver et
redécouper les morceaux de la coque sous le trou : sans l'outil de « cuisson » de PhysX, c'est du travail à la main.

**Programme** :
- Un seul ascenseur codé en dur dans le bateau : position 0x1518, niveaux 0x1520, consigne 0x1538 (0 bas, 1 haut),
  décalage 0x152c, énergie 0x1218, et le lien physique 0x14e0, **retrouvé par le nom `lift_constraint`** dans
  `c_vehicle_server_carrier::build` (0x100193022). Avancé et posé dans `tick_server_type` (0x100194523…0x100194641,
  `set_attachment_transform_b`). Une 2e contrainte dans le XML serait donc ignorée.
- Une seule grue (0x153c…0x1548), un seul gestionnaire avec une seule case ascenseur (0x7c).
- **Côté affichage** (`c_vehicle_client_carrier`) : le client ne reçoit pas la hauteur de la plateforme en clair. Il lit
  l'état de la grue et de l'ascenseur (`e_crane_state`, `e_elevator_state`, pour les écrans) dans `parse_state`
  (0x10011b954), et la position des pièces par le mécanisme général des corps (`get_body_transform`). Une 2e plateforme
  serait donc **probablement** montrée aux joueurs sans rien changer côté client (à confirmer). Les écrans du navire ne
  montreraient que l'ascenseur 1.

### Brique par brique

| Brique | Difficulté | Remarque |
|---|---|---|
| 1. Trou dans le pont, plateforme, puits dans le hangar (3D) | 7/10 | format .mesh connu mais il faut écrire un « écrivain » ; vrai travail de modélisation dans Blender ; choisir un endroit où le hangar a la place (l'îlot est à bâbord au même niveau que l'ascenseur actuel) |
| 1 bis. Collisions | 8/10 | 477 morceaux PhysX cuisinés à redécouper ; sinon les avions tombent à travers ou butent sur un trou invisible |
| 2. Corps et contrainte dans le XML | 3/10 | facile, mais inutile sans code |
| 3. Chemins des avions | 2/10 | facile en XML, mais le code ne connaît que 6 noms |
| 4. Logique (2 ascenseurs, choix de l'ascenseur, grue partagée, énergie, sorties) | 9/10 | greffe importante, sans doute une bibliothèque écrite en C injectée dans le jeu (clang est installé) ; l'état du 2e ascenseur ne serait pas sauvegardé par le jeu → appareil perdu si on sauvegarde en plein cycle |
| 5. Multijoueur | 5/10 | patch côté hôte seulement ; XML à faire passer par le système de mods ; plateforme probablement synchronisée |

### Verdict B

Possible en théorie, **9/10**, **8 à 12 sessions** sur Mac, puis **3 à 5** pour refaire la logique sur Windows. Et le gain
est **faible** : la piste reste unique, donc les avions continuent de se poser et de décoller un par un ; l'ascenseur
n'est pas ce qui les freine. Le seul vrai bénéfice d'un 2e ascenseur serait de donner aux hélicos un chemin à eux… ce
que **A1 fait déjà avec l'ascenseur existant**. Je le déconseille pour l'instant.

Alternatives plus modestes :
- **A1** (voir plus haut) : les hélicos ne passent plus par la piste.
- Ascenseur ×3 : 2/10, 1 session, gain faible (l'ascenseur n'est pas le goulot).
- Deux avions sur la plateforme (12 × 27 m) : 6/10, 2-3 sessions, gain faible pour la même raison.
- « Préparer l'avion suivant pendant que l'ascenseur monte » : **le jeu le fait déjà** en sortie (la grue va chercher
  l'avion suivant pendant que l'ascenseur est occupé, cases 0x78 et 0x7c séparées). Rien à faire.

Risques si on le fait quand même : collisions fausses (trou invisible ou pont qui ne se ferme pas), puits qui traverse
quelque chose dans le hangar, appareil coincé entre deux ascenseurs, sauvegarde en plein cycle, travail entier à refaire
sur Windows.

**Première étape concrète, si tu le veux malgré tout** : une session de maquette, sans toucher au jeu : vue de dessus du
vrai pont avec 4 à 6 emplacements possibles, et vérification dans Blender de la place dans le hangar sous chacun.

---

## C. Survol des autres pistes

| Piste | Difficulté | Sessions | Intérêt pour toi | Ce qu'on sait |
|---|---|---|---|---|
| « Vrai ×2 » des sorties (freinage final) | 2/10 | 1 | faible | chaque tronçon finit par un freinage d'environ 4 s ; gain de quelques secondes par avion |
| Roulage des véhicules terrestres et navires ×2 | 2-3/10 | 1 | moyen | `docking_manager_surface::update` **n'est pas inliné** : 0x1001aa404 → 0x1001accd8 ; même modèle que les avions (0,05 / 2,5 / 0,1), environ 5 retouches ; pas de grue vue dans cette fonction |
| Courbe « vitesse du jeu » | 2/10 | 1 | moyen (outil de mesure) | `overlay.lua` a l'heure réelle et l'heure de jeu ; module fichier, marche tel quel sur Windows |
| Écran de contrôle aérien enrichi | 3-4/10 | 1-2 | élevé, et sert à mesurer A1 | `screen_landing.lua` dessine déjà la file (`get_docking_vehicles`, hélicos et avions à part) ; ajouter état, rang, temps d'attente par `library_custom` |
| Journal de partie enrichi | 6/10 | 2 | moyen | le journal note déjà `destroy_vehicle` avec l'équipe du tireur ; ajouter l'unité et l'arme = greffe dans le programme (à refaire sur Windows) |
| Boutons « rappeler tous les avions » | 3/10 | 1 | élevé | en Lua : pour chaque appareil, `clear_waypoints` + `add_waypoint` sur le bateau + `set_target_vehicle` (ce que fait le glisser-déposer) ; accroche par `library_custom` à cause du mod Revolution |
| Bouton « relancer une vague » | 5/10 | 2 | moyen | la sortie d'un appareil passe par l'écran des baies ; il faut retrouver l'ordre exact |
| Sorties pendant les retours | 8/10 | 3+ | moyen | trouvé en passant : le bateau est soit en mode retours, soit en mode sorties ; jamais les deux |

---

## Annexe technique (pour la session qui écrira A1)

- Gestionnaire (`this` = docking_manager_air, r14 ou −0x30(%rbp)) : 0x00 mode ; 0x24 état de piste (3 approche, 4 rails,
  5/6/7 roulages, table 0x1001b25d8) ; 0x78/0x7c/0x80/0x84 cases grue/ascenseur/piste/décollage hélico (−1 = vide) ;
  0x88/0x8c/0x90/0x94 places du hangar de ces cases (échangées par `rolq $0x20`) ; 0x98/0xa0/0xa4/0xa8/0xac nœuds
  hanger_center/lift_lower/lift_upper/runway_start/runway_end ; 0xb0/0xd0/0xf0 chemins grue/ascenseur/piste (+0x18
  avancement, +0x1c vitesse) ; 0x110 temps d'approche ; 0x118 repère de pose (mat34_f64).
- Nœud du XML : tableau `def+0x220` (pas 0x48, index anneau `0x22c`/`0x228`), position à +0x38/+0x3c/+0x40 (float).
  `lift_upper` est tourné de 90° (m02 = −1, m20 = 1).
- Véhicule (r13 dans l'approche) : 0x220 dock_state, 0x2a0 mode de pilotage (3 = consigne), 0x2a8/0x2b0/0x2b8 cible
  (double, monde), 0x2c0/0x2c4 direction, 0x2c8 vitesse, 0x2cc puissance ; vcall 0xa0 = hélico ? ; vcall 0x138(1) =
  train / état atterrissage ; 0xd0 roues (pas 0x70 ; +0 ≥ 0,01 et +4 ≤ 0,1 pour « au contact »).
- Pile dans l'approche : −0x60 z local de l'appareil, −0x1c0 (x, y) local, −0x1d0/−0x1e0 vitesse du bateau en local,
  −0x260/−0xf4 vitesse de l'appareil en local, −0x120 z de runway_start, −0x1a8 z de runway_end, −0x90 = 7 − z
  (milieu de piste), −0x110 avancement le long de la piste.
- Fin de l'état 7 réutilisable : 0x1001ae13a (attend r14 = gestionnaire, ecx = nombre d'éléments de 0xf0, rsi = 0xf0) ;
  elle finit par `jmp 0x1001b24af` → `0x1001ad62f` (logique de l'ascenseur).
- Ascenseur prêt : 0x7c = −1 et `0x1518(bateau)` > −0,01 (le roulage d'origine teste > −0,5 à 0x1001ae068).
- Zone libre : en-tête du programme, octets 0xF40…0x3BD0 du fichier (= adresses 0x100000f40…0x100003bd0), dans
  __TEXT (lecture + exécution). Commandes de chargement : 27, 3872 octets.

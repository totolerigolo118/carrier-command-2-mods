# Vitesse maximale des avions selon l'altitude — étape 1 (lecture seule), 02/11/2026

Demande du moddeur : « la vitesse maximale de l'avion : un avion plus haut irait légèrement plus rapidement qu'un avion qui serait bas ».
Rien n'a été posé ni lancé. Lu : les données du jeu (lecture seule), le nouvel exe Steam `461E1262…` (copie de travail
`C:\Users\UTILISATEUR\Documents\cc2-port-travail\carrier_command_nouveau_steam_461E1262.exe`), l'ancien exe d'origine
`tour/sauvegardes/carrier_command_1.5.18_original.exe` (`1C9A01C3…`), le SDK CC2X 0.5.0 (clone 7ab05c7) et l'étude
`tour/etudes_modes_carburant/`. Outils : `tour/outils/desasm.py` (capstone) et trois petits scripts maison en lecture seule
dans `outils/` (`chaines.py` = chaînes du programme, `references.py` = qui lit une adresse, `comparer_exe.py` = mêmes octets
dans l'ancien exe). Adresses d'image (base 0x400000) ; « ancien » = 1.5.18.

## 1. Résumé

- **Un mod de données ne peut pas le faire** : les fichiers `vehicle_chassis_wing_*.xml` ne contiennent que des nombres fixes
  (poussée du moteur 50 Albatros / 100 Manta, gouvernes, roues). Les monter rend l'avion plus rapide partout, pas seulement en haut.
  Le freinage de l'air et la croisière 120 m/s de l'IA sont écrits dans l'exe.
- **Ce qui limite la vitesse** (LU, identique dans les deux exe) : poussée fixe du moteur contre un **freinage de l'air
  proportionnel à la vitesse** (réglage interne `vehicle_linear_damping_air` = 0,1, posé à chaque tick sur le corps PhysX de
  chaque véhicule). Calcul : vitesse max ≈ 150 m/s Albatros, 300 m/s Manta ; mesuré en jeu (étude modes) 131-135 et 290 :
  le freinage de l'air fait presque tout, la traînée des ailes fait le reste.
- **Le jeu a déjà un plafond** : la poussée des moteurs est pleine jusqu'à 2 000 m et tombe à 0 à 2 100 m.
- **Proposition** : un petit plugin, désactivé par défaut, qui fait « l'air plus fin en altitude » : partie A (SDK seul, aucun
  octet du jeu changé) pour les avions pilotés à la main et ceux de l'IA ; partie B en option (un crochet) pour que l'IA, qui
  vise toujours 120 m/s, croise aussi un peu plus vite en haut. Ordre de grandeur : **+4 à +5 % à 1 000 m, +8 à +9 % à 2 000 m**,
  rien près de la mer (décollage, appontage, atterrissage inchangés).

## 2. Ce qui fixe la vitesse d'un avion

### 2.1 Poussée du moteur (fonction du jeu « tick des force_emitter »)
Nouvel exe `0x5d35e2`–`0x5d383b` (ancien : même code `-0x130`, plafond lu en `0x5d364a`).
- Le niveau réel du moteur suit la commande à `vehicle_control_force_emitter_speed` = 0,05 par tick (valeur en `0xe47c60`).
- Poussée = direction × 10 × puissance (XML `force_emitter magnitude` : Albatros 50, Manta 100) × niveau × **facteur plafond**.
- Facteur plafond (`0x5d377a`) : `clamp((y − 2 100) / (2 000 − 2 100), 0, 1)` avec y la hauteur du moteur et 2 000 une variable
  globale de `.data` (`0xe1eacc`, même adresse dans les deux exe) : 1 jusqu'à 2 000 m, 0 à 2 100 m.
- Appliquée par `0xc12750` (PxRigidBodyExt::addForceAtPos), 4e argument = 1 = **impulsion**, une fois par tick (30 par seconde) :
  15 m/s² pour l'Albatros, 30 m/s² pour le Manta (masse 1 000 dans le XML, la même pour les deux).

### 2.2 Freinage de l'air
- Réglages internes (« dev values », écrits par le constructeur `0x868400…`, enregistrements de 24 octets {type, catégorie, nom,
  valeur, min/max}) ; table : valeur = `0xe47954 + enregistrement + 0xc`, mêmes adresses dans les deux exe :

  | Réglage | Valeur | Adresse de la valeur |
  |---|---|---|
  | `vehicle_linear_damping_air` | **0,1** | `0xe47b40` |
  | `vehicle_linear_damping_water` | 0,7 | `0xe47b58` |
  | `vehicle_angular_damping_air` | 0,5 | `0xe47b70` |
  | `vehicle_angular_damping_water` | 0,75 | `0xe47b88` |
  | `vehicle_control_surface_scalar` | 0,16 | `0xe47ba0` |
  | `vehicle_control_surface_max_velocity` | 10 000 | `0xe47bb8` |
  | `vehicle_ai_wing_throttle_stiffness` | 0,2 | `0xe48110` |
  | `vehicle_ai_wing_dogfight_target_speed` | 160 | `0xe48128` |

- À chaque tick, pour chaque véhicule (nouvel exe `0x5d0bb1`–`0x5d0ea2`, ancien `0x5d0a81`…) : amortissement linéaire =
  air + (eau − air) × part immergée (`[ebx+0x7c]`), puis pour chaque corps `call [eax+0x88]` = `PxRigidBody::setLinearDamping`
  en **`0x5d0e64`** (ancien **`0x5d0d34`**), et `setAngularDamping` (`+0x90`). `ebx` = véhicule + 0x88 (les corps sont à
  véhicule + 0x8c, comme dans le SDK : `v_bodies = 0x8c`, `body_actor = 0xf0`).
- PhysX retire à chaque pas `c × dt × v` de la vitesse : à l'équilibre, poussée = c × v. Avec c = 0,1 : 150 m/s (Albatros) et
  300 m/s (Manta) sans autre traînée. Mesuré : 131-135 et 290. La différence vient des gouvernes (aile de 5 pour l'Albatros, 4
  pour le Manta), d'où un Albatros un peu moins sensible au freinage de l'air.

### 2.3 Consigne de vitesse de l'IA (déjà connue par l'étude modes, relue ici)
Nouvel exe `0x71deb5`–`0x71df6a` (ancien `0x71ddb5`…, `-0x100`) :
- S = `CONTROL_SPEED` (`+0x1f8`) + correction bornée −10 / +40 ; a = clamp((distance au point − 20) / 780, 0, 1)
  (`0x71ccfd`–`0x71cd37`) ; **T = S + a × (120 − S)** ; gaz (`+0x314`) += 0,2 × ((T − v) / 120 − dv), v = `[edi+0x320]`.
  Loin du point, T = 120 quel que soit `CONTROL_SPEED` : **le SDK ne peut pas changer la croisière**.
- Le 120 de T est chargé par `movss xmm5, [0xdb7a24]` en `0x71decc` (ancien `[0xdb79ec]` en `0x71ddcc`). C'est une constante
  partagée (aussi diviseur en `0x71df3d` et dans la branche combat `0x71cfb1`) : **ne pas l'écrire**.
- Site possible pour l'option B : l'instruction suivante, `0x71ded4` (ancien `0x71ddd4`), `f3 0f 10 bf 20 03 00 00`
  (`movss xmm7, [edi+0x320]`, 8 octets, sans adresse relative) : `edi` = l'avion, `xmm5` = 120 vivant. Le relais `patch_mid`
  du SDK ne sauve pas les registres SSE : il faut l'enveloppe assembleur de `cc2x_frein.c` (`XMM_WRAP`), et c'est la copie
  sauvegardée de `xmm5` que le crochet remplacerait (seulement si elle vaut exactement 120).
- Combat : T = 160 (`0x71cf5b`), non touché.

### 2.4 Ce que le SDK CC2X 0.5.0 permet
`on_server_tick` ; liste des véhicules ; champs `IS_WING`, `DOCK_STATE`, `FLIGHT_STATE`, `WHEEL_CONTACT`, `POS`, `TEAM_IS_AI` ;
`body_get` / `body_set` (position, vitesse : `PxRigidDynamic::setLinearVelocity`, slot 39) ; `patch_mid`. Rien pour le freinage
de l'air ni pour la croisière 120.

## 3. Proposition

### A. « Air plus fin » — avions à la main ET de l'IA, SDK seul
À chaque tick serveur, pour chaque avion à ailes **en vol** (`FLIGHT_STATE` = vol, `DOCK_STATE` = 0 : pas en file
d'atterrissage, pas au parking, aucune roue au contact) et **au-dessus d'une hauteur minimale** (ex. 100 m) : le plugin rend
une petite partie du freinage de l'air, en multipliant la vitesse par `1 + (1 − s) × 0,1 × (1/30)`, avec
`s(h) = 1 / (1 + g × h / 1 000)` et h borné à 2 000 m (plafond des moteurs). Cela revient exactement (au premier ordre) à
un freinage de l'air `s × 0,1`. À 120 m/s et 1 000 m : +0,02 m/s par tick, imperceptible au toucher, mais la vitesse
d'équilibre monte.
- Aucun octet du jeu modifié, aucune adresse du jeu dans le plugin (le SDK connaît les deux exe).
- Couper (`enabled=0`) = jeu d'origine au tick suivant.
- Effet sur l'IA seule : elle garde 120 m/s (son régulateur réduit les gaz) et consomme un peu moins en altitude.

### B. Option « croisière de l'IA » — un crochet
`patch_mid` en `0x71ded4` / `0x71ddd4` (enveloppe xmm) : pour un avion en vol au-dessus de la hauteur minimale, la croisière
120 devient `120 × (1 + g × h / 1 000)`. Combinée à A, l'IA garde à peu près les mêmes gaz et va plus vite en haut.

### Ordre de grandeur (g = 0,05, réglable)
Modèle : poussée = 0,1 × s × v + k × v², k ajusté sur les vitesses max mesurées (Albatros 133, Manta 290).

| Hauteur | Albatros à fond | Manta à fond | Croisière IA (option B) |
|---|---|---|---|
| < 100 m | inchangé | inchangé | 120 |
| 400 m (croisière habituelle de l'IA) | 135 m/s (+1,6 %) | 295 m/s (+1,9 %) | 122 |
| 1 000 m | 138 m/s (+3,9 %) | 304 m/s (+4,7 %) | 126 |
| 2 000 m (plafond) | 143 m/s (+7,7 %) | 317 m/s (+9,3 %) | 132 |

Valable pour tous les avions à ailes, ceux du moddeur et ceux de l'ennemi (c'est l'air qui change). Les hélicoptères ne sont pas
touchés.

## 4. Coexistence
- `cc2x_modes` v3.1 (posé, observation) : écrit le gaz `+0x314` après le tick, sans crochet. A écrit la vitesse, B un registre :
  aucun champ commun. Les modes se combinent (ÉCO = plafond de gaz, reste plafonné). Attention : en FLANK, le Manta irait un peu
  plus vite en altitude, donc plus près de l'oscillation vue vers 222 m/s : à essayer séparément.
- `cc2x_frein` v13 : ses crochets sont dans le code des pistes et du porte-avions (`0x6fd…`–`0x701…`), loin de `0x71ded4`.
  A ne touche jamais un avion en file d'atterrissage, roulant ou posé (et le SDK refuse deux crochets qui se chevauchent).
- `cc2x_hold` v2 : crochet `0x7061f0`, sans rapport.
- Crochets du SDK lui-même (`0x62…`, `0x63…`, `0x778…`) : sans rapport.

## 5. À vérifier à l'étape 2 (si le moddeur est d'accord)
- Le pas de temps de la physique (1/30 s fixe ?) : lire l'appel à `PxScene::simulate`. Le moddeur teste toujours au temps x1,33
  (copie patchée `carrier_command_nouveau_5AF41B4D.exe`, module `temps_x2` : seul l'intervalle réel entre deux ticks du
  serveur raccourcit, `0x77ee10`). La formule de A est par tick : elle reste juste si le pas passé à `simulate` est fixe, et
  non le temps réel écoulé. À confirmer avant d'écrire le plugin.
- Qu'aucun saut du jeu n'arrive dans `0x71ded4`–`0x71dedb` (et `0x71ddd4`… ancien), comme `VERIF_sites_v13.txt`.
- Tests hôte (formule, bornes, pannes injectées : SDK absent, champ inconnu, vitesse absurde, NaN), deux compilations comparées,
  imports comparés (comme `tour/atterrissage_manuel/frein/construire.py`), notice de risques, procédure d'essai en partie neuve
  au temps x1,33 (copie `5AF41B4D` lancée par `tour/essai_nouvel_exe/outils/lancer_nouveau.py`, Steam ouvert avant, jamais
  l'exe Steam brut) : Manta ou Albatros à la main, pleins gaz en palier à 300 m puis à 1 500 m, vitesse lue dans `cc2x.log`.
- Le plugin est en C : il n'utilise pas `library_custom_2` (réservé au mod Lua « aide_approche »).

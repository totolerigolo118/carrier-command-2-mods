# Étude du Mac — atterrissage « approche et toucher à la main, puis le jeu fait le pushback » (27/10/2026)

Souhait du moddeur : **il pilote l'approche et le toucher des roues sur le porte-avions ; dès qu'il est arrêté, le jeu reprend et fait le pushback habituel** (retour au hangar par la piste puis l'ascenseur).
**Lecture seule** du programme d'origine du Mac (`sauvegarde/build_mac_origine`, md5 `b0107170…`, v1.5.17) + nos notes (`partage/cc2_notes.txt`, partie 03). Rien lancé, rien modifié. Adresses = adresses du fichier Mac (64 bits) : ce sont des repères de logique, pas des adresses Windows.
Étiquettes : **CONFIRMÉ** (lu dans le désassemblage), **NOTES** (déjà établi dans nos notes), **INFÉRÉ** (déduit, à vérifier).

## 1. Ce que le jeu fait déjà (et qu'on peut réutiliser)

1. **Le toucher des roues est un vrai test physique.** CONFIRMÉ, `docking_manager_air::update`, `0x1001b1f5c` → `0x1001b2058` : le toucher est validé si la **vitesse relative au navire ≤ 10 m/s** (constante `0x1028697b4` = 10,0) **et** si **toutes les roues sont en contact** (tableau de roues du véhicule en `+0xd0`, nombre en `+0xd8`, pas de `0x70` ; par roue : un champ `+0x00 ≥ 0,01` et un champ `+0x04 ≤ 0,1`). Donc la piste a une surface sur laquelle les roues se posent (collision de la coque : `chassis_carrier_phys.cphys`). Quand le test réussit, un emplacement de hangar est réservé (`manager+0x90`), l'avion est rattaché au navire et le retour commence (NOTES : états de retour 5, 6, 7).
2. **Le pushback existe tel quel.** NOTES : après le toucher, l'avion roule « sur rails » le long de la piste jusqu'au bout, **recule** sur ~125 m jusqu'au point `taxi_a` (≈ 28,5 s), rejoint l'ascenseur (≈ 14 s), attend l'ascenseur libre ; total ≈ 42 s. **La piste n'est libérée qu'à la fin** (ses échanges de créneaux `0x80` ↔ `0x7c`), donc aucun autre atterrissage ni décollage pendant ce temps. C'est le « pushback comme d'habitude ».
3. **La piste est dans l'axe du navire** (NOTES) : de `runway_start` (z −68, côté poupe) à `runway_end` (z +82, côté proue), environ 150 m ; les avions de l'IA arrivent par l'arrière. L'approche finale vise un point à 240 m devant l'avion, vitesse imposée `18 × (1 − progression)`.
4. **Le navire freine l'avion lui-même** pendant l'atterrissage (INFÉRÉ) : dans le bloc du toucher, le code appelle une fonction virtuelle du véhicule (`+0x130`) avec deux valeurs calculées sur la vitesse ; le SDK public de la tour expose « freins et train » : c'est très probablement le frein et le train.

## 2. Ce qui empêcherait un pilotage à la main

- **Le navire pilote l'avion pendant l'approche.** CONFIRMÉ : le bloc de pilotage écrit `control_mode = 3` (`movl $0x3, 0x2a0(%r13)` en `0x1001ad26f`) et la cible (`0x2a8`, `0x2b0`, `0x2b8`) à chaque pas : la consigne du navire écraserait la manette. Pour un avion de joueur, ces écritures devraient être sautées (INFÉRÉ : le bloc exact lié à l'état d'approche n'est pas tracé).
- **Conditions d'échec** (NOTES) : l'approche est ratée et l'avion repart dans la file si `docking_join_time > 3600` pas (2 min), ou si l'angle dépasse 0,45 rad entre 50 et 400 m du bout de piste, ou si le bout de piste est dépassé, ou s'il n'y a pas de baie libre. Un avion de joueur devrait y échapper ou avoir des seuils plus larges.
- **Comment un avion entre dans le processus** : l'entrée dans la file (`dock_state = 5`) est faite par `c_vehicle_server_carrier::dock(container, id)` (`0x100193e0e`, appelle `docking_manager_air::dock`, `0x1001a89f2`), qui n'a **aucun appelant direct** dans le code lu : l'appel passe par un appel indirect (table de fonctions). Le jeu a un type de waypoint `dock` (`e_waypoint_type.dock = 1`) et un waypoint dont la cible est le porte-avions rappelle l'avion (testé en jeu sur le Mac le 25/10, par script). **On ne sait pas comment un avion piloté à la main demanderait à se poser** (aucun bouton « dock » trouvé dans les commandes du jeu, aucun appel de script du programme nommé « dock » ou « atterrir ») : c'est la question centrale.
- **Le créneau de piste** est unique (`manager+0x80`, pris au franchissement de la « porte » d'entrée, `0x1001af95c`) : l'avion du joueur devrait le réserver, sinon un avion de l'IA peut arriver en même temps.

## 3. Esquisse du mode demandé (à valider par l'essai)

1. **Déclenchement** : quand l'avion du joueur est dans une « fenêtre » (dans l'axe de la piste, derrière le bout de piste, hauteur et vitesse faibles, train sorti), il est mis dans le processus d'atterrissage avec un drapeau « piloté », qui réserve le créneau de piste.
2. **Pendant l'approche** : le navire n'écrit plus la consigne (`control_mode` reste celui du joueur) et les conditions d'échec sont ignorées ou assouplies.
3. **Toucher** : le test existant (roues en contact, vitesse relative ≤ 10 m/s) ; pour « dès que je suis arrêté », on peut resserrer la vitesse (**ne pas modifier la constante 10,0, elle est partagée** : rediriger la lecture vers une valeur à nous).
4. **Pushback** : une fois le test réussi, le jeu fait le reste (rails, recul, ascenseur).
Difficulté estimée : **moyenne à élevée** — le code touché est la fonction de ~5 000 instructions, mais les mécanismes (test de toucher, pushback, créneau de piste) existent et sont déjà cartographiés. Le risque principal : un avion de joueur mal géré qui **bloque le créneau de piste** (plus aucun décollage ni atterrissage).

## 4. Ce que l'étude n'a pas pu établir

- **Comment le jeu reconnaît un avion piloté à la main** (représentation du contrôle du joueur : le mode `1` « autre » de `control_mode` est une piste, non vérifiée).
- **Ce qui se passe aujourd'hui** quand un avion piloté touche le pont sans rien faire : c'est l'objet de l'essai du moddeur (protocole ci-dessous).
- Le bloc exact de l'état d'approche qui écrit la consigne ; le nom et le rôle exacts de la fonction virtuelle `+0x130`.
- Tout ce qui touche **Windows 1.5.18** (rien lu).

## 5. Protocole d'essai court (le moddeur, sur la tour, rien à activer)

À faire avec une sauvegarde jetable (ne **pas** enregistrer par-dessus la sauvegarde de référence), navire à l'arrêt, personne d'autre sur la piste.
1. Lance un avion (Manta ou Albatros) comme d'habitude, laisse-le décoller, puis **prends-le en main**.
2. Fais un tour et présente-toi **en finale dans l'axe du navire**, par l'arrière, train sorti, vitesse basse.
3. **Touche le pont avec les roues**, freine, arrête-toi. Fais 2 ou 3 essais (un doux, un plus dur).
4. Après chaque essai, une ligne : **où** tu as touché (piste / pont / ailleurs), la vitesse à peu près, et **ce qu'a fait le jeu** : les roues roulent-elles normalement ? l'avion explose, rebondit ? le jeu le prend-il en charge tout seul (il roule ou recule sans toi) ? reste-t-il là ?
5. **Rends-lui les commandes** (sors de l'avion) une fois arrêté sur la piste : que fait-il ? se range-t-il au hangar ou reste-t-il ?

## 6. Résultat de l'essai du moddeur sur la tour (27/10, Windows 1.5.18, jeu avec patch ascenseur ×2) et ce que ça change

Ce que le moddeur a vu (OBSERVÉ EN JEU, rapporté par lui, non mesuré) :
1. Posé sur la piste, l'avion **glisse** : pas de friction utile, **rien ne l'arrête**. Pour s'arrêter par rapport au pont il faudrait que le porte-avions avance à la même vitesse (« délicat »).
2. **À vitesse nulle, il ne se passe rien** : l'avion reste là, puis **l'IA essaie de redécoller**.

Lecture avec le code du Mac (CONFIRMÉ / INFÉRÉ comme indiqué) :
- **Pas de frein pour le joueur** : les commandes de pilotage du jeu ne comprennent que gaz, tangage, lacet, roulis (CONFIRMÉ, `e_game_input` : 54 à 57). Mais le moteur a un **frein de roues** : `c_vehicle_server::set_wheel_brake(float, float)` (surchargé pour les ailes légère/lourde et les rotors) et `set_gear_state(bool)` (CONFIRMÉ, symboles). Pendant son propre atterrissage, le navire appelle ce frein sur l'avion (appel virtuel `+0x130` dans le bloc du toucher, `0x1001b1ffe`) : pour un avion à voilure fixe, une valeur qui **monte avec l'avancement** (quelque chose comme `2·s·(s − 0,5)` borné entre 0 et 1, `s` calculé plus haut, non tracé), pour un hélicoptère une valeur fixe 0,6 (constantes `0x1028697e8` = −0,5 et `0x10286980c` = 0,6). INFÉRÉ : c'est bien le frein.
- **Le jeu ne reconnaît pas un avion posé à la main** : le test de toucher et le pushback ne tournent que pour un avion **déjà dans le processus d'atterrissage** (créneau de piste pris, état « atterrissage »). Un avion piloté qui roule sur la piste n'y est pas : rien ne le prend en charge. Et il garde son comportement d'IA/ses waypoints, d'où la **tentative de redécollage** (INFÉRÉ, cohérent avec l'observation).

Donc **deux pièces manquent, toutes deux dans le programme, pas faisables en Lua seul** :
1. **Freinage automatique** de l'avion du joueur dès que ses roues touchent la piste (même appel de frein que celui du jeu).
2. **Prise en charge à l'arrêt (ou à vitesse faible)** : quand l'avion du joueur est sur la zone de piste, roues en contact, vitesse faible → le mettre dans le processus d'atterrissage (créneau de piste, état « atterrissage », waypoints effacés) pour que le test de toucher existant réussisse et que rails + pushback se déroulent.
Option plus simple, moins proche de la demande : une **« prise au toucher »** (le jeu attrape l'avion dès que les roues touchent, sans attendre l'arrêt) : pas de frein à écrire, mais l'avion n'est pas réellement arrêté par le pilote.
Aller plus vite que le navire n'est pas nécessaire si l'on freine (le frottement des roues contre le pont s'oppose au mouvement, quelle que soit la vitesse du navire) : INFÉRÉ.
Le SDK public de la tour expose « freins et train » côté véhicule (à confirmer dans `sdk_public_cc2x/WORLD_API.md`), mais **pas** le porte-avions : la pièce n° 2 demande les décalages 32 bits du gestionnaire d'avions (étape 7 de la feuille de la tour).

## 7. Choix du moddeur (27/10) : « l'avion freine tout seul au toucher, je m'arrête, puis le jeu fait le pushback » — plan technique (lecture seule, Mac)

### 7.1 Le frein : simple, et déjà dans le jeu
- `c_vehicle_server_wing_light::set_wheel_brake(float brake, float grip)` (`0x1001c1f2a`) et la version « heavy » (`0x1001c7094`) ne font qu'écrire deux nombres dans **les trois roues** de l'avion : `roue+0x14 = frein`, `roue+0x10 = adhérence` (tableau de roues `véhicule+0xd0`, pas de `0x70`, indices des trois roues en `véhicule+0x420/0x424/0x428`). CONFIRMÉ. Valeurs « repos » : frein 0, adhérence 1,0 (le jeu les remet à `(0, 1,0)` juste après un toucher réussi, `0x1001b20a6`). Pendant sa propre approche, le navire applique une montée du frein (jusqu'à 1) avec une adhérence qui monte vers 3,0. Le second nombre est bien une **adhérence** : le SDK public de la tour l'appelle `grip` (`vehicle_brakes(v, brake, grip)`, `WORLD_API.md` ligne 76).
- **Côté Windows, le frein n'exige aucune adresse du jeu** : `vehicle_brakes(v, 1,0, 3,0)` existe dans le SDK public (et `vehicle_gear(v, down)` pour le train). À appeler à chaque pas serveur tant que l'avion du joueur est sur la piste, roues en contact ; remettre `(0, 1,0)` dès qu'une roue quitte le sol ou que la prise en charge a lieu. Les valeurs `(1,0 ; 3,0)` sont celles de la fin d'approche de l'IA (sûres) : le bon couple se règle à l'essai.
- Mise en garde du SDK : **ne jamais fixer la position d'un véhicule posé sur ses roues** (le jeu le détruit) : pour le déplacer, il faut le laisser au mécanisme du jeu (rattachement par joint).

### 7.2 Reconnaître l'avion du joueur
CONFIRMÉ (structure) / INFÉRÉ (sens) : un véhicule a une file de « pilotes » (`controlling_peer_container`) en `véhicule+0x270` ; `c_vehicle_server::add_controlling_peer` (`0x100348200`) y ajoute le joueur et le premier élément est le pilote courant ; **nombre d'éléments en `véhicule+0x280`**. « Piloté par un joueur » = ce nombre ≠ 0 (à vérifier en jeu). Les entrées du pilote sont lues par `get_peer_vehicle_control_input` (`0x1001c0246`). Côté Windows : décalages 32 bits à retrouver (comme pour le reste), le SDK n'expose pas ce point à ma connaissance.

### 7.3 La prise en charge à l'arrêt : le bloc à reproduire (CONFIRMÉ, `0x1001b2058` → `0x1001b2330`)
C'est ce qu'exécute le jeu **juste après un toucher réussi**. Pour un avion posé à la main, il faut déclencher la même chose (avec l'avion à sa place actuelle) :
1. `get_available_vehicle_bay_index(type, 1)` → numéro de baie, rangé en `manager+0x90` ; abandon s'il n'y a pas de baie libre.
2. `set_wheel_brake(0, 1,0)` (relâche le frein).
3. `véhicule+0x2cc = 0` (consigne de puissance à zéro).
4. `set_attached_to_vehicle_id(carte, id du porte-avions)` : l'avion est rattaché au navire.
5. `véhicule+0x198 = 0`, `véhicule+0x1a0 = −1` (champs remis à zéro ; sens non établi, probablement liés à la cible de waypoint ou d'accostage).
6. `véhicule+0x234 = baie`.
7. Transformation de rattachement = repère de la baie × repère d'atterrissage ; `set_attachment_transform`, `create_physics` (**un joint physique** relie l'avion au navire), puis les messages aux clients (`event_vehicle_set_attached_to_vehicle`).
8. `véhicule+0x21c = 1` (état de vol : au sol) et `véhicule+0x220 = 6` (état d'accostage : retour au hangar en roulant), écrits d'un coup (`0x600000001`).
9. `manager+0x24 (état de piste) = 5` ; remise à zéro des tampons `manager+0xf0..` et des progressions `manager+0xfc` / `manager+0x108` ; puis le chemin de pushback est choisi par son nom dans le graphe du porte-avions (`runway_reverse_a`, chaîne `0x10291e855`, ou `_b`).
Avant tout cela, le créneau de piste (`manager+0x80`) doit contenir l'identifiant de l'avion.

### 7.4 Ce qui reste à établir (par la lecture, avant d'écrire du code)
- **Le « repère d'atterrissage »** (`manager+0x118`, matrice) est fixé par l'IA quand elle franchit la porte d'entrée : pour l'avion du joueur il faut le **calculer à partir de sa pose actuelle**.
- **La progression du pushback** (`manager+0x108`) démarre à 0 = bout de piste côté proue (z ≈ +81) : si l'avion s'est arrêté au milieu, il faut **initialiser la progression à sa position** sur le chemin, sinon il saute au bout de piste (et le SDK avertit que déplacer un véhicule sur ses roues peut le détruire : à tester d'abord avec un avion de rechange).
- **Qui reste aux commandes** pendant le pushback : le joueur reste-t-il pilote (la file `+0x270` non vide) ? Il faudra sans doute l'éjecter ou ignorer ses entrées pendant le remorquage.
- **L'IA qui veut redécoller** (observé par le moddeur) : à la prise en charge, `véhicule+0x2a0 (control_mode)` et les waypoints doivent être remis comme pour un avion de l'IA qui vient de se poser (effacer waypoints et cible d'attaque).
- **Où brancher le bloc** : une vérification à chaque pas des avions du joueur proches du porte-avions (dans `docking_manager_air::update` ou dans le pas serveur du véhicule). Le code vit dans la fonction de ~5 000 instructions ; côté Windows : étape 7 de la feuille (décalages 32 bits du gestionnaire).
- Multijoueur : traité côté serveur, donc uniquement pour l'hôte.

### 7.5 Verdict de faisabilité
**Faisable, difficulté moyenne.** Le frein est trivial (une fonction du SDK, sans adresse). La prise en charge est la vraie difficulté : un bloc de ~10 opérations déjà écrit dans le jeu, à rejouer proprement pour un avion posé n'importe où sur la piste, avec le risque principal de **bloquer le créneau de piste** (plus aucun décollage ni atterrissage). Ordre conseillé : (1) frein seul (essai immédiat, aucun risque pour la piste) ; (2) prise en charge, d'abord avec l'avion arrêté **sur l'axe près du début du chemin de pushback**, puis à n'importe quel endroit.

# Étude de faisabilité : deux hélicos à la fois, un deuxième ascenseur, et les autres pistes

Fiche préparée le 23/10/2026 pour une conversation **d'étude seulement** : réfléchir, lire le programme et les
fichiers du jeu, rendre des verdicts francs. **Rien n'est modifié ni installé.**

## 0. À lire avant tout

1. `mods/cc2-patchs/DEMARRER_cc2_patchs.md` : qui est le moddeur, ses règles, l'atelier, tout ce qu'on sait déjà du
   programme (sections 4 et 5) et la feuille de route (section 6).
2. Règles propres à cette étude :
   - **Lecture seule** : ne modifier ni le jeu, ni `outil/`, ni `tests/`, ni `fichiers/`, ni la fiche DEMARRER.
     Une autre conversation (« CC2 : atterrissages plus rapides ») travaille en ce moment dans
     `docking_manager_air::update` et dans l'atelier : ne pas la gêner.
   - Écrire seulement dans `mods/cc2-patchs/etudes/` (et le dossier temporaire de la session pour les
     désassemblages).
   - Ne pas lancer le jeu. Son Mac est un Mac Apple Silicon sans ventilateur : désassembler par tranches
     (`objdump --start-address … --stop-address …`), pas tout le programme d'un coup.
   - Le moddeur ne code pas : rendu en français simple, une seule question à la fin.

## 1. Les questions

### A. Poser deux hélicos à la fois (Razorbill = hélico léger, Petrel = hélico lourd)

- Comment le jeu pose un hélico aujourd'hui : file d'attente (`dock_queue`), où il se pose sur le pont, chemin
  jusqu'à l'ascenseur, rôle de la grue du hangar, durée de chaque étape.
- Où est exactement la limite « un seul à la fois » : une file unique ? un seul point de pose ? l'ascenseur
  occupé ? une condition « piste libre » ?
- Ce qu'il faudrait changer (valeurs, conditions, nouvelle logique), et le risque de collision sur le pont.
- Verdict : patch de valeurs, patch de comportement, ou greffe de code ; difficulté sur 10 ; nombre de
  sessions ; ce que le moddeur verrait en jeu ; ce qui pourrait mal tourner.

### B. Un deuxième ascenseur

Inventaire de ce qui existe (à vérifier et compléter) :
- **Fichier du navire** `rom_0/game_objects/vehicle_chassis_carrier.xml` (remplaçable par un mod) : corps
  physique `lift` + contrainte `lift_constraint` (course −9 … 0 m), corps `lift_personnel`, chemins `graph_link`
  (`runway`, `runway_lift`, `runway_reverse`, `runway_reverse_a/b`, `lift_top_reverse`, `load_lift_lower`,
  `surface_*`), places `vehicle_attachment air1..air8` (avions) et `vehicle_attachment1..8` (terrestres),
  lumières `vehicle_bay_air_lift_light`, boutons `lift_tower_floor_*`.
- **Modèles 3D** `rom_0/meshes/` : `chassis_carrier_lift.mesh`, `chassis_carrier_lift_phys.cphys`,
  `chassis_carrier_phys.cphys`, `chassis_carrier_crane*.mesh/.cphys`, et
  `meshes/aircraft_carrier/aircraft_carrier_shell/aircraft_carrier_lift.mesh` + `aircraft_carrier_hangar.mesh`
  (dessus du hangar = pont d'envol). Le format `.mesh` est décodé (mémoire « cc2-format-mesh », code
  `ZClaude/outils/cc2-logs/mesh_stl.py`) ; le format `.cphys` (collisions) est **inconnu**.
- **Programme** : un seul ascenseur codé en dur dans `c_vehicle_server_carrier` (position `this+0x1518`,
  consigne `0x1538`, niveaux `0x1520`, avancé dans `tick_server_type`), une seule grue du hangar
  (`this+0x153c…0x1548`) et une seule machine d'état dans `docking_manager_air::update` ; côté affichage,
  `c_vehicle_client_carrier` (à étudier : comment le client reçoit la position de l'ascenseur).

Ce qu'il faut évaluer, brique par brique : (1) ouvrir un trou dans le pont et fabriquer la plateforme
(modèle 3D + collisions) ; (2) deuxième corps physique et contrainte dans le XML ; (3) chemins des avions ;
(4) la logique : deux ascenseurs et deux files dans le programme (probablement une greffe de code) ;
(5) le multijoueur (ce que voient les joueurs qui rejoignent).
Chercher aussi des **alternatives plus modestes** qui donnent une partie du gain : deux avions sur la même
plateforme, un ascenseur encore plus rapide, préparer l'avion suivant dans le hangar pendant que l'ascenseur
monte, etc.

### C. Survol rapide des autres pistes (une ligne chacune : difficulté sur 10, intérêt pour le moddeur)

- le « vrai ×2 » des sorties (raccourcir le freinage final du roulage) ;
- la grue des véhicules terrestres et des navires ×2 (`docking_manager_surface`, update inliné, à trouver) ;
- la courbe « vitesse du jeu » (temps de jeu / temps réel, dans `overlay.lua`, qui a `update_get_time_ms`) ;
- un écran de contrôle aérien enrichi (scripts Lua) ;
- un journal de partie enrichi (qui a tué qui, avec quelle arme) pour ses rapports de bataille ;
- des boutons d'ordres en un clic (rappeler tous les avions, relancer une vague).

## 2. Ce qu'on attend à la fin

- Un fichier `mods/cc2-patchs/etudes/RESULTATS_etude.md` : pour A et B, ce qui a été trouvé (adresses,
  fonctions, fichiers), le verdict, la difficulté sur 10, le nombre de sessions, les risques, la première
  étape concrète ; pour C, un tableau court.
- Un message au moddeur en français simple, sans jargon, avec une recommandation et **une seule question** :
  lequel lancer en premier.
- Aucune modification du jeu ni de l'atelier.

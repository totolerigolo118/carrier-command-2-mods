# Retour automatique au hangar (`auto_recall`) — étude B1 et conception (31/10/2026)

> **Suite (31/10)** : le moddeur a dit de continuer (« continue de travailler sur le retour automatique, je peux le tester maintenant ») ; la façon **A** ci-dessous est **écrite dans la v14** et testée hors jeu, pas posée : `frein/RISQUES_v14.md`, `PROCEDURE_partie_v14_retour_auto.md`.

Étiquettes : **LU**, **INFÉRÉ**, **INCONNU**.

**Ce que le moddeur veut** : quand l'avion posé à la main est arrêté (tenu par le frein) et que le pilote le quitte, il repart seul vers l'ascenseur et le hangar, sans aller donner l'ordre de retour sur la carte.

## 1. Comment le jeu donne l'ordre de retour (LU)

- **Côté carte (Lua, `rom_0/scripts/screen_vehicle_control.lua`, lignes 2569-2582)** : faire glisser l'appareil sur un véhicule ami (le porte-avions) envoie quatre appels : `clear_waypoints()`, `clear_attack_target()`, `add_waypoint(x, z)` à la position du navire, puis `set_target_vehicle(id_du_waypoint, id_du_navire)` (un « waypoint de soutien »). C'est **le seul** ordre de retour des scripts (aucune autre fonction « dock » côté Lua).
- **Côté serveur (exe)** : tout finit dans **une seule fonction du porte-avions**, sa fonction virtuelle `+0x7c` (`0x707330` ancien exe, `0x707440` nouvel exe, même code, relu instruction par instruction). Pour un appareil volant qui n'est pas déjà en file : elle ajoute `{id, 0, 0}` à la file d'atterrissage (`[navire+0xd3c]`, la file que lisent H1 et H6), met `DOCK_STATE = 5` et `DOCK_VEHICLE` = le navire. Elle vérifie elle-même tout le reste (déjà en file, déjà sur une piste, sinon elle ne fait rien).
- Elle est appelée par deux chemins du jeu : le traitement d'un message du joueur (`0x7784e9` → `0x5ebf80` : « si le demandeur n'est pas un porte-avions et la cible en est un ») avec `monde = serveur + 0x344`, et le code de l'IA qui suit les waypoints (`0x6c2bb7`, le waypoint de soutien).
- Mesuré au rappel (v7, 29/10) : `dock=5`, `dock_vehicle=2`, `wp=0` (plus de waypoint), `flight=2` une seconde après ; puis la chaîne v12 (H1/H2, H5, prise en charge) fait le reste.

## 1 bis. La touche R (« manuel / auto ») (LU, 02/11)

- La touche « changer de mode » (`e_game_input.toggle_control_mode`, `vehicle_hud.lua` 185-190) envoie au serveur un message que le serveur applique ainsi (`0x779fc9`-`0x779ffb`, ancien exe) : il vérifie que l'expéditeur pilote bien ce véhicule (ou que personne ne le pilote), puis appelle la fonction virtuelle `+0x78` du véhicule (`0x6c4ab0` : `[véhicule+0x1d0] = valeur demandée`, c'est le `CONTROL_MODE` du SDK). Côté Lua, `vehicle:get_control_mode()` lit cette valeur : 0 = « auto », 1 = « manuel », 2 = « off », 3 = « override » (`0x8918b4`, table `0x891910`).
- Donc **R fait passer `CONTROL_MODE` de 1 à 0 alors que le pilote reste dans le siège**. La v14 démarre son compte à rebours dès que `CONTROL_MODE` n'est plus 1 : **R est déjà couvert**, sans rien changer (avion tenu et arrêté sur le pont seulement ; en vol, rien ne change). INFÉRÉ : que R envoie bien ce message (le HUD affiche « auto / manuel » à partir de la même valeur). INCONNU : ce que fait le jeu du pilote resté assis quand l'avion arrive au hangar.

## 2. Ce que le SDK CC2X 0.5.0 sait faire (LU, `src/world.c`, `src/lua_world.c`, `include/cc2x.h` du commit 7ab05c7)

- **Côté C** : lire / vider la liste des waypoints, changer le type ou le paramètre d'un waypoint **existant** ; `request_landing` = atterrissage sur un **aérodrome d'île** (fonction `0x62b4a0`), **pas** sur un porte-avions ; aucune fonction pour **ajouter** un waypoint ni pour mettre un appareil dans la file d'un navire.
- **Côté Lua (table `cc2x`)** : `set_waypoint` (type/param d'un waypoint existant), `clear_waypoints`, `request_landing` (île), `queue_push/queue_remove` (files d'un aérodrome d'île). Rien pour un porte-avions.
- Mais le jeu donne au plugin, à chaque tick, le pointeur du **serveur** ; `serveur + 0x344` est exactement le « monde » que le SDK utilise lui-même pour trouver un véhicule (`s_vehicle_map`), et donc celui que le jeu passe à la fonction `+0x7c`.

## 3. Trois façons possibles

| | Comment | Pour | Contre | Risque |
|---|---|---|---|---|
| **A (proposée)** | le plugin appelle **la fonction `+0x7c` du porte-avions** (`appareil`, `monde = serveur + 0x344`), une fois, comme le fait le serveur quand il reçoit l'ordre | même fonction finale que l'ordre du joueur ; dans le tick du serveur (le fil du plugin) ; rien à écrire dans la mémoire du jeu ; pas de nouveau mod | première fois que **notre** plugin appelle directement une fonction du jeu (le SDK le fait déjà pour le frein et le train) ; mauvais argument = plantage d'une partie jetable | 🟡 |
| B | un petit mod Lua (emplacement libre `library_custom_0` ou `_8` ; `_2` est pris depuis le 01/11 par le mod « aide_approche ») qui, sur **un seul** écran, envoie les 4 appels de la carte pour les appareils que le plugin dit « prêts » (fonction Lua ajoutée par le plugin) | c'est **mot pour mot** l'ordre du joueur | un nouveau mod + un pont plugin ↔ Lua entre deux fils ; dépend de l'écran choisi (qui doit tourner) ; un écran de plus = l'ordre envoyé plusieurs fois | 🟡 |
| C | écrire nous-mêmes la file et `DOCK_STATE` | — | refait à la main ce que le jeu fait, sans ses contrôles | 🔴 (écarté) |

## 4. Conception proposée (A) — **à valider, pas écrite**

- Nouveau réglage **`auto_recall=0`** par défaut (et `auto_recall_s=5` : délai après le départ du pilote).
- Conditions, **toutes** : l'avion est **tenu** par le plugin (frein de maintien), **arrêté** (< 0,3 m/s par rapport au navire), roues au contact, `DOCK_STATE = 0`, pas accroché, **pilote parti depuis `auto_recall_s` secondes sans interruption**, dans la zone du navire de son équipe, équipe humaine, `only_id` respecté ; **`recall_force=1` et ses crochets posés** (sinon l'avion serait mis dans la file « comme en vol », sans prise en charge) ; aucun autre appareil signalé.
- **Une seule demande par atterrissage** (verrou), puis on regarde : `DOCK_STATE = 5` au tick suivant ⇒ la chaîne v12 habituelle (fenêtre, H1/H2, H5, prise en charge) ; sinon une ligne « AUTO RECALL refusé par le jeu » et on n'insiste pas.
- Garde-fou : avant d'appeler, le plugin vérifie que l'entrée `+0x7c` de la table du navire **est exactement** la fonction relue pour ce build (`0x707330` / `0x707440`) ; sinon il ne fait rien et l'écrit.
- Si le pilote remonte avant les 5 s : rien n'est demandé. Pour couper en jeu : `auto_recall=0` (relu en 3 s).
- Hélicos (si `heli_recall=1`) : même chose pour un hélico posé, immobile, pilote parti (H6 prend le relais).
- Journal : `AUTO RECALL: asked the carrier's own dock request for aircraft N after X s without a pilot` puis les lignes habituelles.

## 5. Ce qui reste INCONNU

- Ce que le jeu fait d'autre au rappel par la carte (par exemple `flight=2`, vu une seconde après) et qui ne viendrait pas avec l'appel direct (INFÉRÉ : sans effet, la prise en charge remet `flight=1`).
- Comment le joueur verra l'ordre sur la carte (pas de waypoint dessiné : l'appareil passera simplement « en retour »).
- Multijoueur : non prévu (solo uniquement, comme le reste).

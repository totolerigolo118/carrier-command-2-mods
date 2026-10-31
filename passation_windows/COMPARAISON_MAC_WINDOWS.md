# Comparaison Mac (64 bits) ↔ Windows (32 bits) — ce qu'on sait, lu dans le code

Écrit le 25/10/2026. Sources :
- **Mac** : nos notes (`reference_en/cc2_notes.txt`, parties 01 et 02) et nos lectures du programme `build_mac` (md5 b0107170…, build du 2026-01-05). Adresses = adresses virtuelles du fichier Mac.
- **Windows** : le profil de build du SDK public CC2X (`sdk_public_cc2x/`, dont `sdk_public_cc2x/src/cc2x.c` et `src/world.c` ; dépôt GitHub `Dioramawhois/Carrier-Command-2-extender`, que j'ai relu en direct le 25/10/2026). Il décrit **un seul build** : `1.5.18-win32`, horodatage PE `0x6a36c177` (= 2026-06-20 16:36 UTC), taille d'image `0x00af7000`, exécutable `carrier_command.exe`, 32 bits. Toutes les adresses Windows ci-dessous sont des **adresses d'image pour la base 0x00400000** (celles que Ghidra ou IDA affichent).

⚠️ Je n'ai **jamais vu l'exécutable Windows**. Tout ce qui est « Windows » ici vient de ce profil public, pas d'une lecture à moi. Le build Mac (janvier 2026) est plus ancien que ce build Windows (juin 2026) : le code a pu changer entre les deux. C'est la première chose à vérifier sur la tour (étape 1 de la feuille).

## 1. Ce qui est identique (confirmé des deux côtés)

| Point | Mac (nos notes) | Windows (SDK public) |
|---|---|---|
| États d'accostage `e_vehicle_dock_state` | 0 en vol, 1 atterrissage, 2 sortie demandée, 3 sortie, 4 au hangar, 5 file d'atterrissage, 6 roulage retour, 7 attente au lancement (« probablement le bouton rouge », non vérifié) | `UNDOCKED`=0, `DOCKING`=1, `PENDING_UNDOCK`=2, `UNDOCKING`=3, `DOCKED`=4, `QUEUED`=5, `TAXI`=6, **`UNDOCK_HOLDING`=7** → notre 7 est **confirmé** |
| Mode de pilotage d'un véhicule | `control_mode` : 0 = points de passage, 3 = consigne imposée par le bateau ; puis cible (3 doubles), vitesse visée, puissance | `CONTROL_MODE` : 0 = ses waypoints, 3 = « voler vers CONTROL_TARGET » ; puis `CONTROL_TARGET` (3 doubles), `CONTROL_SPEED`, `CONTROL_POWER` |
| Drapeau « équipe pilotée par l'IA » | objet équipe, octet `+0x19` | objet équipe, `team_is_ai = 0x19` |
| Taille d'une roue (`wheel`) | pas de 0x70 | `wheel_size = 0x70` |

## 2. Un véhicule : décalages (octets depuis le début de l'objet véhicule)

Les décalages **diffèrent** (pointeurs de 8 octets contre 4), mais l'ordre et les écarts dans un même bloc se retrouvent.

| Champ | Mac | Windows 1.5.18 | Remarque |
|---|---|---|---|
| identifiant (`id`) | non relevé | `0x80` | |
| définition (`e_game_object_type`) | `0x90` | `0x84` | Mac : `cmpl $0xa, 0x90(...)` teste « Manta » (type 10) |
| équipe (pointeur vers l'objet équipe) | `0x260` | `0x1a8` (`v_team_object`) ; `v_team` (numéro) `0x108` | |
| waypoints (vecteur) | `0x1d0` | `0x140` | Mac : on y appelle `clear` dans `cancel_undocking` |
| **état de vol** | `0x21c` (« phase » : mis à 1 par la grue, 0 à l'annulation) | `0x170` (`v_flight_state` : 0 garé, 1 sol, 2 en vol) | **adjacent à `dock_state` des deux côtés** : très probablement le même champ |
| **`dock_state`** | `0x220` | `0x174` | |
| `control_mode` | `0x2a0` | `0x1d0` | écart 0xd0 |
| cible (3 doubles) | `0x2a8` | `0x1d8` | `+8` après `control_mode` des deux côtés |
| **vitesse visée** | `0x2c8` | `0x1f8` | `+0x20` après la cible des deux côtés |
| **puissance** | `0x2cc` | `0x1fc` | `+4` après la vitesse des deux côtés |
| `control_taxi` | non relevé | `0x200` | |
| attaché à (id du porte-avions) | non relevé | `0x10c` | |
| accosté à (véhicule / île / aérodrome) | non relevé | `0x114` / `0x118` / `0x11c` | |
| carburant, points de vie | non relevés ici | `0x120`, `0x180` | |

Lecture : le bloc « pilotage » (mode, cible, vitesse, puissance) a **exactement la même forme** sur les deux plateformes, décalé de `0xd0`. C'est le bloc qu'utilisent notre circuit d'attente (consigne imposée) et notre plancher de vitesse des avions de l'IA (écriture dans la vitesse visée).

## 3. Le gestionnaire d'aérodrome des îles (Windows) et celui du porte-avions (Mac) : deux classes sœurs

Le SDK public expose le gestionnaire d'**aérodrome d'île** (`c_environment_tile_airfield_manager` côté Mac). Il a la même conception que notre `docking_manager_air` du porte-avions (mode, état de piste, véhicule sur la piste, file d'atterrissage, file de décollage, chemin de roulage, cases de hangar), mais **ce n'est pas la même disposition** :

| Champ | Aérodrome d'île, Windows (`a_*`) | Porte-avions, Mac (`docking_manager_air`) |
|---|---|---|
| mode | `0x74` | `0x00` |
| état de piste | `0x78` | `0x24` |
| véhicule sur la piste | `0x7c` (−1 = aucun) | `0x80` |
| nœud de bout de piste / début | `0xb4` / `0xb8` | `0xac` / `0xa8` (début avant fin) |
| chemin de roulage | `0xbc` | `0xb0` (chemins grue, ascenseur, piste) |
| file d'atterrissage | `0xcc` | `0x48` (éléments de 12 octets) |
| file de décollage | `0xdc` | `0x60` |
| cases de hangar | pointeur `0x68`, nombre `0x6c` (4 cases) | 4 cases 0x78 grue, 0x7c ascenseur, 0x80 piste, 0x84 rotor |
| tuile (île) | `0xf0` | — |

Donc : **les décalages du porte-avions sur Windows restent à découvrir** (voir la recette « analyseurs d'état sauvegardé » dans `reference_en/cc2_notes.txt`, partie 01 section 6 et partie 11 section 3 d). Le SDK public **n'expose pas le porte-avions** (ascenseur, grue, case de piste) : c'est justement ce que nos notes décrivent et ce qu'il lui manque.

## 4. Les points d'ancrage Windows donnés par le SDK public (adresses d'image, base 0x400000)

Ce sont des fonctions et crochets que le SDK a déjà localisés dans `carrier_command.exe` 1.5.18. Utiles comme **repères** pour naviguer dans Ghidra, et pour mettre en face de nos noms Mac. La colonne « à mettre en face (Mac) » est une **hypothèse de rapprochement** (même rôle, même famille de fonctions), à vérifier en lisant le code.

| Rôle | Adresse Windows | À mettre en face (Mac) |
|---|---|---|
| table de fonctions virtuelles du serveur logique (init, tick, fin) | `0x00d34bc4` | classe du serveur logique |
| `server_init` / `server_tick` / `server_end` | `0x00772fd0` / `0x0077ee10` / `0x0077eea0` | |
| création de l'environnement Lua (juste après les bibliothèques standard) | `0x004465ec` | création d'une `lua_State` dans le moteur |
| bibliothèque Lua 5.3 : `index2addr`, `auxsetstr`, `luaV_finishset`, `luaS_new`, `luaH_new`, `luaC_step` | `0x008cda70`, `0x008ce200`, `0x008ff6b0`, `0x00908220`, `0x00904a50`, `0x00904050` | |
| véhicule par id / tuile par id / tuile à une position | `0x005ee6a0` / `0x00631240` / `0x00631040` | conteneurs de véhicules et de tuiles |
| **demande d'atterrissage** (mise en file) | `0x0062b4a0` | `c_environment_tile_airfield_manager::dock` |
| **pas de simulation d'un aérodrome** | `0x00628600` (le SDK s'accroche en `0x0062b8f3`) | `c_environment_tile_airfield_manager::update` |
| choix du hangar pour un avion qui atterrit (crochet) | `0x0062ae8d` (branche « trouvé » `0x0062aefc`, branche « aucun » `0x0062aead`) | `get_available_hangar_node` |
| contrôleur d'île (crochets) / apparition des défenses | `0x0063014f`, `0x00634981` / `0x00634f3d`, fonction `0x0062ca30` | `c_enemy_spawner`, contrôleur d'île |
| effacement des waypoints | `0x00854870` | `mm_vector<c_vehicle_waypoint_data>::clear` |
| croissance d'une file (deque) | `0x00860c90` | `mm_vector<…>::buffer_resize` |
| crochet « nouveaux waypoints d'un joueur » | `0x007781d4` | |

Le serveur : liste des véhicules `+0x37c` (carte `+0x344`), liste des tuiles `+0x440` (carte `+0x42c`), diffusion `+0x514`. Tuile : id `+0x00`, position `+0x48`, équipe `+0x60`, île `+0x100` ; île → aérodromes `+0x154`.

Les fonctions du voisinage `0x0062…` à `0x0063…` sont la famille « aérodrome d'île » ; la fonction équivalente du porte-avions (`docking_manager_air::update`, ~5 000 instructions sur Mac) est ailleurs : on la retrouvera par les empreintes (partie 11 section 3 des notes) et par les chaînes `lift_constraint`, `load_lift_lower`, `runway_start`…

## 5. Ce que fait le SDK public, et ce qu'il ne fait pas

Fait : reconnaissance du build (horodatage + taille), patchs transactionnels (octets d'origine vérifiés, chevauchements refusés, tout-ou-rien), crochets en milieu de fonction avec les registres généraux (pas les registres flottants !), remplacement d'un pointeur de table virtuelle, événements du serveur (init, pas, fin), ajout de fonctions Lua `cc2x.<espace>.<nom>`, journal `cc2x.log`, lecture/écriture de champs de véhicules, tuiles, aérodromes, physique du corps principal (position, vitesse, rotation), lancer de rayon, freins et train, mise en file d'atterrissage, événements (waypoints, pas d'aérodrome, choix de hangar…).

Ne fait pas : **écriture d'octets bruts** (tous nos patchs sont de ce type : un plugin peut le faire lui-même avec `VirtualProtect` + copie, mais sans la protection contre les chevauchements) ; sauvegarde des registres flottants dans ses crochets (nos greffes ont buté sur ce point : on ne sait pas quels registres `xmm` sont vivants) ; le porte-avions ; le multijoueur (aucun transport : solo ou hôte seulement) ; autre chose que la build 1.5.18-win32.

Licence : GPL-3.0-or-later, y compris pour `cc2x.h` : une extension publiée doit l'être avec son code source sous licence compatible. Pour un usage strictement personnel, aucune obligation de publication.

# Scénario PvP : 2 équipes de 5, unités terrestres, capture d'île — étude de faisabilité (28/10/2026)

## ÉTAT À LA PASSATION (29/10/2026)

1. **Objectif** : préparer pour le moddeur et ses amis une partie de Carrier Command 2 centrée sur les unités terrestres (Seals), soit en PvP 5 contre 5 (§1-9), soit en PvE coop contre l'IA rouge des îles, 4 îles, défenseurs « que des Seals » (§10 bis).
2. **Établi** (rien n'est **MESURÉ** en jeu par moi) — **LU** : menu HOST > CUSTOM (16 joueurs, 4 équipes humaines, 0-4 IA, 4-64 îles, **1-4 porte-avions par équipe humaine**) ; le Seal (400 PV, blindage 10, coût 500, 120 s, amphibie) ; 8 baies terrestres + 8 aériennes par porte-avions ; pas de réglage « sans avions » ni de position d'îles ; victoire d'origine = détruire les porte-avions, rien en Lua pour terminer une partie ; défenseurs d'île selon `difficulty_factor` (0,00 = 13-19 Seals à tourelle 15 mm, sans Mule, Bears dès ~0,56) ; **formule des dégâts** (§10 ter, lue dans l'exe d'AVANT la mise à jour) : dégâts de l'arme − blindage, minimum 1 → Seal défenseur 15 mm = 2 par tir sur un Seal, 30 mm = 18, 40 mm = 40, 20 mm (avion) = 1. **INFÉRÉ** : tout effet d'un mod de constantes (sauf la durée de fabrication, validée sur le Manta par le Mac) ; qu'une île proche soit à 0,00 ; la répartition des joueurs avec 2 porte-avions ; les dégâts de zone.
3. **Posé par moi** : **rien** dans le jeu, Steam, `%APPDATA%`, les DLL ou les exe. Seuls fichiers écrits : `tour/scenario_pvp/ETUDE.md` (ce fichier), la note `scenario_pvp_note.md` dans le dossier partagé des sessions, et des scripts jetables dans le dossier temporaire de la session (rien à retirer). Aucune sauvegarde du jeu modifiée (lues seulement : `slot_0` à `slot_19`).
4. **Attend le moddeur** : (a) **quel scénario** : PvP 5 contre 5 terrestre, ou PvE coop « un peu standard mais plus dur » (il hésite : « je suis pas sûr ») ; (b) **quel mod préparer** : « constantes » minimal (Seal moins cher et plus rapide ; option : dégâts du 15 mm 12 → 20 pour des défenseurs plus dangereux), ou mod PvP complet (constantes + Lua qui cache l'aérien + arbitre d'île) ; (c) accord pour un **essai solo sans mod** (jeu lancé par lui). Le multijoueur n'a **jamais été testé avec de vrais joueurs** (ni avec nos mods, ni avec nos patchs).
5. **Prochaine action unique** : l'**essai solo sans mod** (§10 bis, fin) : NEW GAME > CUSTOM, 4 îles, 1 IA, difficulté 1, chargement complet, plans tous ; noter les icônes de difficulté de la holomap, le parc et le stock de Seals, puis chronométrer les tirs d'un Seal défenseur (cadence et dégâts de zone, inconnus). Jeu lancé par le moddeur, jamais par moi. Ordre recommandé ensuite : PvE P1 → P2 → P3 → P4 ; PvP A → B → C, puis E (carte fixée par sauvegarde) ; jamais D (porte-avions XML sans baies aériennes) ni G (patch de fin de partie). Prototype PvP T0-T4 : héberger seul avec mot de passe → avec mod → contre une IA → avec 1 ami → 4-6 puis 10.
6. **Pièges** : ne **jamais** toucher aux capacités de munitions ; un mod local est **envoyé aux invités** (désactiver `cc2_*` pour un PvP) ; héberger ouvre une partie réseau (**mot de passe** obligatoire) ; ne pas éditer une vraie sauvegarde (toujours une copie ; les sauvegardes faites avec Revolution plantent au chargement sans lui) ; ne pas cumuler Revolution avec le mod du scénario ; ne pas présenter l'inféré comme un fait ; ne rien lancer ni fermer côté jeu sans l'accord du moddeur.
7. **Non commité, à moi** : `tour/scenario_pvp/ETUDE.md` seulement (dossier `tour/scenario_pvp/` entier non suivi).
8. **Effet de la mise à jour Steam du 28/10 21:30** (rapportée par la conversation de coordination, **non vérifiée par moi**) : mon étude de `rom_0` date du 28/10 AVANT la mise à jour ; la formule des dégâts vient de la copie de l'**ancien** exe (`tour/sauvegardes/carrier_command_1.5.18_original.exe`), pas du nouvel exe `461E1262…`. À RE-VÉRIFIER avant de s'y fier : `constants.txt` (lignes 45, 63, 106, 169), `screen_menu_main.lua:1062-1144`, les adresses `0x5e8ba0` / `0x7414b0`. Les commandes du §9.1 pour retirer `temps_x2` et `pont_retour_x2` sont **sans objet** tant que l'exe est celui d'origine ; la liste « état de la tour » du §6 est périmée (SDK et plugins inactifs).

---

**Étude en lecture seule.** Le jeu n'a pas été lancé ni fermé. Rien n'a été modifié dans le dossier du jeu, dans `%APPDATA%\Carrier Command 2\` (j'y ai seulement *lu* une sauvegarde, la liste des mods et le dossier `mods\`), dans Steam, les exe ou les DLL. Rien n'a été téléchargé, installé, posté ni commité. Seul fichier écrit : celui-ci. Trois pages web publiques ont été lues (Steam + suivi officiel), sans rien envoyer.

**Étiquettes** : **LU** = lu dans un fichier ou une page (source indiquée) · **INFÉRÉ** = déduit, à vérifier (jamais un fait) · **INCONNU** = je n'ai pas trouvé.
Risque : 🟢 faible · 🟡 moyen · 🔴 élevé. Effort : S (une séance) · M (quelques séances) · L (beaucoup).

---

## 0. En bref

| Question | Réponse courte |
|---|---|
| Le PvP existe-t-il ? | **Oui, dans le menu du jeu.** Jusqu'à 16 joueurs, 4 équipes humaines, 0 à 4 équipes IA. Les joueurs choisissent leur équipe en rejoignant ; une équipe = l'équipage d'un porte-avions (LU). |
| 2 porte-avions par équipe ? | **Oui, c'est un réglage du menu** « Transporteurs par équipe humaine » (1 à 4), seulement en partie hébergée (LU). L'idée « impossible » vient de 2022 ; le réglage existe en 1.5.18. Reste des défauts connus (confusion des équipiers, pas d'échange entre porte-avions) et **jamais testé ici**. |
| Que des unités terrestres ? | **Pas d'interrupteur « sans avions ».** Mais on peut rendre l'aérien **inutilisable** (prix énormes dans un mod) et le **cacher** dans les menus (mod Lua). Les avions de départ ne se retirent pas proprement. |
| Le « Seal » | Châssis `chassis_land_wheel_light` (type 2) : **400 PV, blindage 10, coût 500, 120 s**, 4 emplacements, amphibie (LU). Le moins blindé et le moins cher des 4 véhicules terrestres. Tous ont **les mêmes 400 PV**. |
| 4 îles, porte-avions de part et d'autre | **Pas de choix de disposition dans le menu** : le nombre d'îles est réglable (4 à 64), la position est générée. On peut **fixer une carte** via sa graine (`world_seed`) et une sauvegarde ; **éditer la sauvegarde** pour placer les îles est plausible mais non essayé. Une île dessinée à la main : très lourd. |
| « Premier à capturer l'île » | **Pas dans le jeu** : la victoire d'origine = détruire tous les porte-avions ennemis. Avec des Seals seuls, c'est quasi impossible (blindage 40, 5000 PV). Un mod Lua peut **détecter et annoncer** la capture, **pas terminer la partie**. |
| Nos patchs | `temps_x2` : **à retirer** pour un PvP (il impose la vitesse à tous, la tour sature déjà à ×1,33). Les deux autres ne touchent que l'aérien. Les mods locaux `cc2_*` sont **envoyés aux invités** : à désactiver. |
| Plus petit test | **Seul, en hébergeant avec mot de passe** (équipe 2 vide) : voir la disposition, le parc de départ, les prix. Puis 1 ami. §9. |

**Ma recommandation (§8)** : commencer par **A + B** (menu + petit mod de constantes : Seal bon marché, aérien hors de prix), puis **C** (cacher l'aérien + annonce de victoire par l'île centrale). Ne pas toucher aux porte-avions en XML (D), ni à l'exe (G).

---

## 1. Le PvP existe-t-il, et comment ?

**LU** :
- **Menu « HOST »** (`rom_0/scripts/screen_menu_main.lua:396-460`) : joueurs max **1 à 16** (l. 415-416), mot de passe, puis NEW GAME (campagne ou **personnalisé**) ou LOAD GAME (`host_load_game`). Seul le mode **personnalisé** donne les réglages ci-dessous.
- **Réglages de partie** (`screen_menu_main.lua:1062-1144`, `imgui_game_customisation`) :

| Réglage | Valeurs | Remarque |
|---|---|---|
| Îles (`islands`) | 4 à 64 | total, départs compris (INFÉRÉ, voir §4) |
| Équipes humaines | 1 à 4 | **multijoueur seulement** |
| Équipes IA | 0 à 4 (1 à 4 en solo) | |
| Îles de départ par équipe | 1 à 64 | |
| Porte-avions par équipe humaine | **1 à 4** | **multijoueur seulement** (l. 1129-1132) |
| Difficulté de base | 1 à 4 | |
| Chargement (`loadout`) | défaut / minimal / complet | contenu exact **INCONNU** |
| Plans débloqués | défaut / aucun / tous | |

- **Rejoindre** (`screen_menu_main.lua:266-384`) : on **choisit une équipe humaine** ; plusieurs joueurs peuvent être dans la même équipe (la table liste « les joueurs de l'équipe »). C'est l'équipe, pas le porte-avions, qu'on choisit.
- **Rôles à bord** (`rom_0/game_objects/vehicle_chassis_carrier.xml`, balise `seats`) : **10 sièges** par porte-avions : 3 contrôle de véhicules, 1 barre, 1 navigation, 2 chargement, 1 armement du bateau, 2 logistique. Un joueur peut aussi **piloter une unité** à distance (`screen_vehicle_control.lua:2867-2880`, tout véhicule de son équipe sauf le porte-avions et le chien-robot). Donc 5 joueurs par équipe tiennent sur **un** porte-avions (10 sièges) (INFÉRÉ pour la répartition libre).
- **Preuve que ça a servi** : `logs/game_log_2026-01-24_13-13-53.jsonl` : deux joueurs en **équipes 1 et 2** qui se détruisent des véhicules (victime équipe 1 / tireur équipe 2, et l'inverse), l'équipe 0 (IA neutre) tire aussi. Les 111 journaux locaux ne contiennent **aucun** événement `team_win` / `team_lose` (LU, comptage fait : seulement `chat`, `destroy_vehicle`, `player_joined`, `player_left`) ; un seul journal montre deux équipes humaines : **la règle de fin n'a pas été observée ici**. Le pseudo « Yoloplayer » revient 91 fois ; l'auteur de `cc2_carte` est « Yolo » : c'est probablement toi (INFÉRÉ, à confirmer) — tu as donc déjà hébergé ; la plupart de ces parties semblent en coopération (6 joueurs différents en équipe 1 le 29/10/2025, INFÉRÉ).
- **Règle d'origine** (manuel intégré, `localization.csv:822-826`) : « Détruisez tous les porte-avions ennemis pour gagner » ; capturer des îles sert à étendre la logistique (virus-bots sur un centre de commandement, tourelles converties).

**Verdict** : PvP équipes contre équipes = **fonctionnalité normale** du jeu.

---

## 2. Deux porte-avions par équipe

**Ce qu'on avait écarté** (`IDEES.md`) : « impossible par mod (Steam, mai 2023) ; édition de sauvegarde = bugs de logistique (Steam, sept. 2022) ».

**Ce que je trouve dans le jeu actuel (1.5.18)** :
- Le sélecteur « Transporteurs par équipe humaine » existe, 1 à 4 (LU `screen_menu_main.lua:1129-1131` ; texte `localization.csv:1535`). `server_config.xml` du serveur dédié a aussi `carrier_count_per_team="1"` (LU). Le programme a `get_new_game_team_carrier_count_per_team` (LU, symboles du Mac, `envoi_native_bridge/symbols_lifecycle_candidates.txt:126`).
- Le mod Workshop « Out of Bounds » (installé) écrit : « Quand il y a plusieurs porte-avions dans une équipe… » (LU `workshop/content/1489630/3386389411/mod.xml`).
- **Lecture des pages web** (28/10) : le fil Steam de septembre 2022 (« Multiple Carriers for Co-op? ») dit « officiellement non » et que l'ajout se fait par édition de sauvegarde (un message sur des barges qui livrent le mauvais porte-avions) ; **mais** deux demandes du suivi officiel de **mars 2023** parlent déjà de deux porte-avions dans la même équipe : #18648 « Confusion with Teammates on Two Separate Carriers » (v1.5.1, ouverte, 2 votes) et #18599 « Trading Ammo or Units to Different Friendly Carriers » (v1.4.5, ouverte, 1 vote). Pas de réponse des développeurs sur ces pages.

**Conclusion** : l'idée « impossible » est **périmée** : c'est une option officielle du menu (au moins depuis la v1.4.5, INFÉRÉ d'après les dates). **Défauts ouverts à garder en tête** : équipiers qui se perdent entre deux porte-avions, **pas d'échange** de munitions ou d'unités entre eux. Pour des unités terrestres, l'échange compte peu (chaque porte-avions a ses 8 baies). **Où apparaissent les joueurs qui rejoignent** quand l'équipe a 2 porte-avions : INCONNU (la position de réapparition est par équipe, `get_peer_respawn_position`, LU symboles).

**Faut-il vraiment 2 porte-avions ?** Ce qui limite les Seals, c'est :
1. les **baies de départ** : **8 baies terrestres** par porte-avions (LU : 17 emplacements dont 8 de type 0 « terrestre », 8 de type 1 « aérien », 1 canot ; `screen_vehicle_loadout.lua:25` « terrestre si baie < 8 »). Les Seals déployés **ne comptent plus** dans les baies : il faut seulement des baies libres pour recharger.
2. la **production** : stock de châssis dans l'inventaire du porte-avions, fabriqués dans les usines des îles (file `+1/+10/+100/+1000`, `screen_inventory.lua:1360-1367`) puis amenés par barge.

**Alternatives à un 2e porte-avions** (classées) :
| Alternative | Effet | Faisabilité | Risque | Effort |
|---|---|---|---|---|
| **Seal bon marché et rapide** (constantes, §3) | plus de Seals, sans toucher au bateau | haute (LU les constantes) | 🟢 | S |
| **2 îles de départ avec usine par équipe** (`starting_islands`=2) | double la production | haute (menu) | 🟢 | S |
| **Mod « Rev:Resupply+ »** (installé, 3398249587) : le porte-avions prend le fret **directement à moins de 2 km d'une île**, sans barge | moins de navettes | moyenne (remplace `library_custom_2.lua` et la barge) | 🟡 | S |
| **2 porte-avions par équipe** (menu) | 16 baies, 20 sièges | haute pour lancer ; **inconnue** pour la qualité | 🟡 | S |
| Plus de baies en XML | plus d'unités au départ | INCONNU (aucun mod ne le fait ici) | 🔴 | M |

---

## 3. Unités terrestres seulement ; le « Seal »

### 3.1 Fiche du Seal (LU)
| Donnée | Valeur | Source |
|---|---|---|
| Nom / type | **Seal** (« phoque ») ; `chassis_land_wheel_light` = **2** | `library_enum.lua:15`, `08_constants…:21` |
| Points de vie | **400** | `constants.txt:45` |
| Blindage | **10** (Walrus 20, Bear 40, Mule 60) | `constants.txt:63-66` |
| Coût / durée de fabrication | **500** / **120 s** (Walrus 750/180, Bear 1500/300, Mule 1000/180) | `constants.txt:106-109, 169-172` |
| Carburant | capacité 800, conso 2,0 | `constants.txt:87, 96` |
| Masse | 1000 kg ; 4 roues | `vehicle_chassis_wheel_small.xml` |
| Emplacements | **3 petits (type 0) + 1 grand (type 1)** | idem (Walrus pareil ; Bear 3 petits + 1 « énorme » type 5 ; Mule 1 petit + 6 conteneurs) |
| Amphibie | oui : force de propulsion « water » = **14** ; le mod « Seal 2x Water » (installé, 3385750786) la passe à **23** | diff du XML |
| Vitesse maximale | **INCONNU** dans les fichiers (code du jeu) ; à mesurer en jeu | |

**Armement** (dégâts de base, `constants.txt:11-22`) : 15 mm = 12 · 30 mm = 28 · 40 mm = 50 · canon 100 mm = 80 · canon lourd = 100. Le **15 mm n'a pas d'objet d'inventaire** (il manque dans `e_inventory_item`), donc probablement **sans stock à fournir** (INFÉRÉ : `screen_vehicle_loadout.lua:341` laisse passer un objet sans type d'inventaire) ; les 30 mm (coût 200), 40 mm (250), canon 100 mm / lourd (750) demandent du stock. **Quelles armes vont dans quel emplacement** : INCONNU (la liste vient du programme, `update_get_attachment_option`). **Formule du blindage** : trouvée dans le code, voir §10 ter (dégâts − blindage, minimum 1).

**Pour capturer une île** : un **module virus** (coût 200, 60 s) dans la « capsule de contrôle » ; on déploie les virus-bots sur un centre de commandement ennemi (manuel, `localization.csv:826`).

### 3.2 Comment interdire ou retirer l'aérien — 4 niveaux
| Niveau | Comment | Force | Risque | Effort |
|---|---|---|---|---|
| **N1 Prix** | mod avec `constants.txt` complet : `item_vehicle_wing_light/heavy_production_cost` et `rotor_light/heavy` à 100000 (et durées longues) | **côté serveur** (l'hôte fait foi, INFÉRÉ) ; empêche de **fabriquer** | 🟢 | S |
| **N2 Menus** | mod Lua (`library_custom_N.lua`) qui retire les châssis aériens de `get_selected_chassis_options` (écran de chargement, `screen_vehicle_loadout.lua:23-46`) et de la liste de production (`begin_load_inventory_data`, `library_vehicle.lua:443`) | seulement l'interface ; contournable par un client modifié (amis : sans importance) | 🟡 (un emballage de fonction mal fait casse un écran ; accident connu `07_lua_api…:17`) | M |
| **N3 Départ** | « chargement minimal » : contenu **INCONNU**, à regarder en solo ; sinon accord oral de ne pas sortir les avions de départ. Pas de fonction Lua pour détruire/téléporter une unité (LU `07_lua_api…:49`) ; seule l'**auto-destruction**, réservée à l'admin et à un véhicule déjà sorti (`screen_vehicle_control.lua:419`) | partiel | 🟢 | S |
| **N4 Porte-avions sans baies aériennes** | copie de `vehicle_chassis_carrier.xml` sans les 8 emplacements « air » | fort | 🔴 : le jeu lit des tableaux sans vérifier leur taille (cause du plantage des sauvegardes, `etudes_demarrage_auto/ETUDE.md` §3) ; conflit avec les autres mods de porte-avions (Revolution, Tactical Ops) | M |

**Parc de départ « choisi »** : la liste de départ est **générée par le programme** (`create_carrier_starting_loadout(type)`, LU symboles ; `08_constants…:96` « aucun fichier modifiable »). Exemple LU dans ta sauvegarde n°19 (chargement probablement « complet », INFÉRÉ ; faite avec Revolution, donc pas un départ d'origine) : 4 Seals, 2 Walrus, 2 Bears, 2 de chaque aérien, 1 barge, 1 canot. Donc on **ne choisit pas** le parc : on rend les Seals peu chers et on les fabrique dès la minute 0 (file `+100`).

### 3.3 Équilibrage « beaucoup d'unités légères » — valeurs de **départ** pour un premier essai
(Tout est dans `constants.txt` : **un mod le remplace en entier**, et les invités le reçoivent. Les lignes sont globales : elles touchent aussi les Seals **de l'IA neutre**. Piège LU `08_constants…:25` : **ne pas toucher aux capacités de munitions**.)

| Réglage (`constants.txt`) | Origine | Essai | Pourquoi |
|---|---|---|---|
| `item_vehicle_wheel_light_production_cost` | 500 | 150 | Seals en masse |
| `item_vehicle_wheel_light_production_time` | 120 | 30 | idem (confirmé en jeu sur le Manta : la durée marche) |
| `item_vehicle_wheel_medium_production_cost` | 750 | 1500 | décourager le Walrus |
| `item_vehicle_wheel_heavy_production_cost` | 1500 | 4000 | décourager le Bear |
| `item_vehicle_wing_light/heavy`, `rotor_light/heavy` `_production_cost` | 1000/2500/750/1500 | 100000 | pas d'aérien |
| `item_virus_module_production_cost` / `_time` | 200 / 60 | 100 / 30 | la capture dépend de lui |
| `land_wheel_light_hp` | 400 | 400 (ou 300) | « pas trop tanky » : déjà le moins blindé |

Effet réel des coûts/PV : **INFÉRÉ** (la durée de production est la seule validée en jeu). L'unité du coût (monnaie de l'équipe) est INFÉRÉE.

---

## 4. 4 îles de base et position des porte-avions

**Comment le jeu fait les îles (LU)** :
- Les îles sont **générées** : un fichier de biome (`rom_0/biomes/*.xml`) donne la liste des tuiles autorisées et des bruits (`island_noise_parameters`…). Les « préfabriqués » (`tile_prefabs/`, 17 fichiers : bases de commandement, usines, piste, fonderie) sont des assemblages de tuiles triangulaires. **Aucun fichier du jeu ne cite les préfabriqués par leur nom** : le programme les choisit lui-même (règle INCONNUE).
- Une **sauvegarde** contient pour chaque île : `seed`, `biome_type`, `difficulty_factor`, `world_position` (x, z), propriétaire (`team_control`) ; et pour la partie `world_seed` (LU, `saved_games/slot_19/save.xml`, structure lue sans copie). Les équipes ont `start_tile_id` et `respawn_position` (celle du porte-avions : ~1,3 km de son île de départ dans cet exemple).
- Dans l'exemple (24 îles, 1 équipe humaine + 1 IA) : 2 îles de départ + **22 neutres** (équipe 0) ; les deux départs sont à **~76 km** l'un de l'autre (positions en mètres, INFÉRÉ). C'est la preuve que `islands` = total et que la carte est grande (INFÉRÉ pour les petits nombres : monde plus petit ?).

**Ce qu'on peut obtenir** :
| Besoin | Moyen | Faisabilité | Risque | Effort |
|---|---|---|---|---|
| 4 ou 5 îles, 2 équipes | menu : `islands`=4 ou 5, `starting_islands`=1 ou 2, équipes humaines=2, IA=0 | **haute** (LU) | 🟢 | S |
| **Carte reproductible** | générer, regarder, **sauvegarder**, puis toujours héberger depuis cette sauvegarde (`host_load_game`) ; la graine est dans la sauvegarde | haute (INFÉRÉ qu'elle redonne la même carte) | 🟢 | S |
| Porte-avions « de part et d'autre » | dépend du générateur ; sinon on **édite** les positions dans la sauvegarde (`respawn_position`, `world_position`) | moyenne (aucun essai ; une édition de sauvegarde mal faite plante, voir ci-dessus) | 🟡 | M |
| Rapprocher les îles (traversées en mer longues : l'eau est lente) | édition de sauvegarde, ou mods « Seal 2x Water », « Out of Bounds » (limite la zone jouable par une ligne rouge) | moyenne | 🟡 | M |
| **Île sur mesure** (forme dessinée) | (a) choisir graine/biome d'une île par édition de sauvegarde ; (b) nouveau préfabriqué en XML : le jeu le prendra-t-il ? INCONNU ; (c) nouvelles tuiles/meshes avec `mod_dev_kit/bin/build_content.exe` (156 tuiles source fournies) | (a) moyenne, (b) basse, (c) basse | 🟡 | (a) M, (b)(c) L |

**Disposition possible** (à tenter d'abord) : 5 îles = 2 de départ par équipe + 1 centrale neutre (« l'île à prendre »). Avec 4 îles seulement : 1 départ par équipe + 2 neutres ; « l'île » à prendre est alors à choisir. **Je n'ai trouvé aucun réglage de graine dans le menu** : la carte change à chaque partie neuve.

---

## 5. Condition de victoire « premier à capturer l'île »

**LU** :
- La règle d'origine est dans le programme (journal `island_captured`, `team_win`, `team_lose` : `08_constants…:75` ; `<scene is_triggered_game_end>` dans la sauvegarde). **Aucune règle de victoire en Lua** dans `rom_0/scripts` (recherche faite).
- Les commandes que Lua peut envoyer au programme (`update_ui_event`) : `load_game`, `host_game`, `quit_to_menu`, `save_game`, `chat`, `chat_team`, `host_kick_peer`, `host_ban_peer`, `set_game_setting`… **Aucune « terminer la partie »** (liste vérifiée dans les scripts).
- Lua **lit** l'état des îles : `update_get_tile_count()`, `update_get_tile_by_index(i)`, `get_team_control()`, `get_team_capture()`, `get_team_capture_progress()` (LU `screen_vehicle_control.lua:1194-1245`, `07_lua_api…:33-37`), la position de l'île (`get_position_xz()`), et peut **écrire dans le chat** (`update_ui_event("chat", …)`).

**Conséquence** :
- **Option R1 « arbitre Lua »** : un mod qui, côté hôte, repère l'île centrale (la plus proche du milieu des deux îles de départ, INFÉRÉ faisable) et **annonce** « ÉQUIPE X A GAGNÉ » dans le chat quand `get_team_control()` change. **Ne termine pas** la partie ; l'hôte arrête à la main. Faisabilité moyenne-haute ; risque 🟡 ; effort M. Limite : Lua ne tourne que pendant qu'un écran est affiché (`07_lua_api…:49`) ; l'écran `overlay.lua` / la visée des unités peut servir (INFÉRÉ, à tester).
- **Garder la règle d'origine** (détruire les porte-avions) : presque inatteignable avec des Seals (blindage 40, 5000 PV, `constants.txt:44, 62`), et un porte-avions a des canons contre eux. Donc à compléter par R1.
- **Patch du programme** pour une vraie fin de partie : la fonction n'est pas retrouvée (🔴, L) → **écarté**.

---

## 6. Multijoueur et nos patchs

**LU `partage_detail/08_constants_and_multiplayer.txt` §3 (lu dans le programme, jamais testé avec 2 joueurs)** :
- Les joueurs qui rejoignent reçoivent **tous les fichiers modifiés** (XML, `constants.txt`, Lua, textures, sons). Seules exceptions : `localization.csv` et la police. **Un mod = rien à installer chez l'invité.** Le serveur affiche un drapeau « modifié » (LU `library_ui.lua:1852`).
- Un **patch du programme** n'est **jamais** envoyé : il n'agit que chez l'hôte, qui fait tourner la simulation.
- Un **plugin DLL** (SDK de DYOR) : chez l'hôte seulement ; le SDK dit lui-même « serveur dédié non supporté » (LU `passation_windows/sdk_public_cc2x/README_PLAYERS.txt:31`).

**État actuel de la tour (LU, `tour/etudes_roulage_retour/ETUDE.md` §5 bis)** : exe `0C5DFE52…` = `ascenseur_x2` + `temps_x2` + `pont_retour_x2` (posé aujourd'hui à 10:25, **jamais vu en jeu**). Mods actifs d'après les notes du 28/10 : `2937532682` (missiles), `cc2_mesures`, `cc2_carte`, `cc2_modes` ; plugins : `cc2x_frein.dll` + le plugin des modes.

| Élément | Effet en PvP terrestre | À retirer pour un PvP équitable ? |
|---|---|---|
| `temps_x2` | **le serveur impose la vitesse à tous** (LU `module_exe_temps_x2.md` : « mode test… aussi aux joueurs d'une partie hébergée ») ; la tour sature déjà à ×1,33 sans joueurs (LU `JOURNAL_tour.md`, cité dans `IDEES.md`) ; avec 10 joueurs et des dizaines de Seals, le retard est probable (INFÉRÉ) | **Oui.** |
| `ascenseur_x2` | grue / ascenseur / pont : aérien (INFÉRÉ ; le doc parle de grue et de roulage) | Non nécessaire ; ne gêne pas l'équité (même hôte pour tous) |
| `pont_retour_x2` | roulage des avions au retour : aérien | Retirer pour le 1er essai (patch tout neuf, jamais vu) |
| Mods `cc2_mesures`, `cc2_carte`, `cc2_modes`, `2937532682` | **envoyés aux invités** et exécutés chez eux ; `cc2_modes` dessine un onglet SPEED ; les missiles de `2937532682` changent l'équilibre | **Oui** : n'activer que le mod du scénario |
| Plugins `cc2x_frein.dll` & co | atterrissage / vitesse d'avions : sans objet | Inoffensifs attendus (INFÉRÉ) ; les ôter si plantage |
| Revolution (non actif) | ajoute des emplacements au porte-avions et remplace `vehicle_chassis_wheel_small.xml` | Ne pas l'activer avec le scénario (conflits de fichiers) |

**Serveur dédié** (autre piste) : `dedicated_server.exe` + `server_config.xml` (`island_count`, `island_count_per_team`, `carrier_count_per_team`, `team_count_ai`, `team_count_human`, `base_difficulty`, `loadout_type`, `blueprints`, `active_mod_folders`) est un exe **non patché** et **sans SDK**, donc « propre » par construction, et libère le PC de jeu. Jamais lancé ici ; comment il charge les mods locaux : INCONNU → 🟡, M, **pas pour le 1er essai**.

---

## 7. Mods Workshop déjà installés qui servent (LU, descriptions)
- **Seal 2x Water** (3385750786) : 1 valeur du XML du Seal (propulsion dans l'eau 14 → 23).
- **Out of Bounds** (3386389411) : zone jouable limitée par une ligne rouge (empêche de fuir loin).
- **Rev:Resupply+** (3398249587) : fret pris directement à moins de 2 km d'une île.
- **BetterGameChat** (3429383959) : chat d'équipe séparé (utile à 10 joueurs).
- **AI:Skynet** (3225306468) : IA neutre plus agressive (hors scénario, mais montre qu'on peut changer l'IA).
Tous remplacent des fichiers : vérifier les conflits avant d'en cumuler (règle LU `08_constants…:49`, « le dernier gagne »).

---

## 8. Options classées

| # | Option | Faisabilité | Risque | Effort | Commentaire |
|---|---|---|---|---|---|
| **A** | Menu seul : 2 équipes humaines, 0 IA, 4-5 îles, 2 porte-avions/équipe, chargement minimal ; « pas d'avions » et « l'île centrale gagne » par **accord oral** | haute | 🟢 | S | Aucun code. L'aérien de départ reste. |
| **B** | **A + mod de constantes** (§3.3) : Seals pas chers, aérien hors de prix | haute (LU) | 🟢 | S | Un dossier de mod + 1 ligne dans `mods.xml`. Retrait : décocher. |
| **C** | **B + mod Lua** : cache l'aérien (chargement, production) + **arbitre** qui annonce la capture de l'île centrale | moyenne-haute | 🟡 | M | Nécessite un essai en jeu à chaque écran touché. |
| **E** | Carte fixée par sauvegarde (graine) ; **édition des positions** des îles et porte-avions | moyenne | 🟡 | M | Une sauvegarde éditée peut planter ; toujours sur copie. |
| **H** | Serveur dédié propre | inconnue | 🟡 | M | Plus tard. |
| **F** | Île sur mesure (préfabriqué / tuiles / kit de mod) | basse, incertaine | 🟡 | L | Seulement si la graine ne donne rien de bien. |
| **D** | Porte-avions XML sans baies aériennes | moyenne-basse | 🔴 | M | Risque de plantage (tableaux non bornés). |
| **G** | Patch du programme pour une vraie fin de partie « île » | faible | 🔴 | L | Écarté. |

**Recommandation** : **A → B → C**, puis **E** seulement si la disposition générée ne convient pas. Pas D, pas G. Commencer par **le plus petit prototype** ci-dessous.

---

## 9. Plus petit prototype réaliste, sans le lancer maintenant

### 9.0 Ce qu'on sait déjà sans jouer
Rien de ce scénario n'a été joué à plusieurs avec nos patchs (INCONNU). Ce qui se **vérifie seul** (T0-T2) : démarrage, parc de départ, disposition, prix, file de production, charge de la simulation. Ce qui demande **un ami** (T3) : équipe 2 réelle, envoi du mod, qui apparaît où avec 2 porte-avions. Ce qui demande **10 personnes** : la charge réelle et l'équilibre.

### 9.1 Avant (jeu **fermé**, une conversation à la fois ; les autres utilisent l'exe et `mods.xml`)
1. **Tout noter** : exe `0C5DFE52…` ; `mods.xml` actuel (`mods_actifs.py` en fait une copie datée à chaque fois).
2. **Retirer `temps_x2` et `pont_retour_x2`** (exe d'origine pour ces essais). 🟡 : écrit le vrai exe, réversible ; **demande ton accord** :
   ```
   python tour/outils/patch_exe.py retirer --exe "C:\Program Files (x86)\Steam\steamapps\common\Carrier Command 2\carrier_command.exe" --module temps_x2 --sauvegarde tour/sauvegardes/carrier_command_1.5.18_original.exe --cest-le-vrai-jeu
   ```
   (puis la même commande avec `--module pont_retour_x2`). **Restaurer** : même commande avec `activer` à la place de `retirer`.
3. **Désactiver les mods locaux et celui des missiles** : 🟢
   ```
   python tour/outils/mods_actifs.py desactiver --nom cc2_mesures --nom cc2_carte --nom cc2_modes --nom 2937532682 --suffixe pvp
   ```
   **Restaurer** : `python tour/outils/mods_actifs.py restaurer --depuis mods.xml.bak_<date>pvp` (le nom exact est affiché par la commande ; les dossiers des mods ne sont pas touchés).
4. **Mod du scénario (étape B)** : à écrire (modèle : `tour/etudes_modes_carburant/mod_modes.py`, qui sait déjà `installer` / `retirer`). Contenu : `mod.xml` + `content/scripts/constants.txt` (copie complète de `rom_0/scripts/constants.txt` avec les lignes du §3.3). **Non écrit** : je le prépare à ta demande, avec un test hors jeu comme pour les autres mods.

### 9.2 En jeu (par le moddeur)
**T0 — seul, sans mod (20-30 min)** : Menu → **MULTIPLAYER / HOST** → joueurs max 10, **mot de passe** (n'importe quel mot inventé, pas un vrai) → NEW GAME → **CUSTOM** → Îles **5**, Équipes humaines **2**, Équipes IA **0**, Îles de départ **2**, Porte-avions par équipe **2**, Difficulté **1**, Chargement **minimal**, Plans **tous** → START.
Relever : (1) que le jeu démarre ; (2) combien de porte-avions et d'unités au départ (écran de chargement) ; (3) la carte (holomap) : distances entre îles, côtés des porte-avions ; (4) coûts et durées affichés pour Seal / Walrus / Bear et pour l'aérien ; (5) vitesse du Seal sur terre et en mer ; (6) ce qui se passe quand tu es seul dans l'équipe 1 et que l'équipe 2 est vide. Puis quitter (`quit_to_menu`) et fermer.
⚠ **Sécurité (🟡)** : héberger ouvre une partie réseau. Le mot de passe empêche les inconnus d'entrer ; l'écran « liste des serveurs » peut quand même montrer ta partie (INFÉRÉ). Fermer le jeu juste après.

**T1 — seul, avec le mod B** : mêmes réglages. Relever : prix affichés = ceux du mod ; l'aérien est-il fabriquable (file `+1`) ? combien de Seals en 10 min avec la file `+100` ? la **vitesse de simulation** (affichage « SIM » de `cc2_mesures`, à réactiver seulement pour cette mesure).

**T2 — seul contre une IA** : Équipes humaines 1, Équipes IA 1. Relever : l'IA attaque-t-elle des Seals ? peut-on capturer l'île neutre avec un module virus ? vérifier que l'arbitre (étape C) l'annonce.

**T3 — avec 1 ami** (même réglages que T1, mod envoyé automatiquement) : l'ami rejoint l'**équipe 2**. Relever : téléchargement du mod, choix de l'équipe, où il apparaît, si les prix sont bien ceux du mod, retard (« lag ») et plantages (`logs/game_log_*.jsonl` note les arrivées et destructions).

**T4 — 4 à 6, puis 10** : seulement après T3 propre. Mesurer la simulation avec ~100 Seals.

### 9.3 Tout remettre
Fermer le jeu ; `mod_scenario_pvp.py retirer` (à écrire, comme `mod_modes.py retirer`) ou `mods_actifs.py restaurer` ; `patch_exe.py activer --module temps_x2` (puis `pont_retour_x2`) avec la copie `tour/sauvegardes/carrier_command_1.5.18_original.exe` ; vérifier l'exe `0C5DFE52…`. Les sauvegardes de test : supprimer les emplacements créés pour le test (à regarder avant, jamais à l'aveugle).

---

## 10. Limites et inconnues (honnêteté)
- **Rien n'a été joué.** Tout ce qui est « effet » est INFÉRÉ, sauf la durée de fabrication (validée sur le Manta par le Mac).
- INCONNU : contenu exact des chargements défaut / minimal / complet ; cadence de tir et dégâts de zone (la formule du blindage est trouvée, §10 ter) ; armes compatibles avec les emplacements du Seal ; vitesse du Seal ; taille du monde avec 4-5 îles ; apparition des joueurs avec 2 porte-avions ; règle de fin de partie réellement appliquée en 1.5.18 (aucun `team_win` dans les journaux) ; si le jeu prend un nouveau préfabriqué ; si `team_count_ai`=0 est accepté sans équipe IA cachée ; effet des plans « aucun » sur les châssis.
- Les pages web (Steam, suivi officiel) sont des **données** : aucune instruction trouvée dedans n'a été suivie. Le suivi (#18648, #18599) ne montre que le titre et la date ; le détail des défauts n'est pas lu.
- Le jeu a été patché en 1.5.18 (26/06/2026) « uniquement correctif » (LU `08_constants…:55`) ; les messages Steam de 2022-2023 datent d'avant.
- Jusqu'au 28/10 je n'avais pas lu l'exécutable ; depuis le 29/10 j'ai désassemblé la **copie** du dépôt (`tour/sauvegardes/carrier_command_1.5.18_original.exe`) pour la formule des dégâts (§10 ter), jamais l'exe du dossier du jeu. Les autres noms de fonctions viennent des notes du Mac (symboles).

## 10 bis. Variante PvE (29/10) : coop contre l'IA rouge des îles, uniquement des Seals en face

Demande du moddeur : plutôt que du PvP, un PvE « comme d'habitude » ; 4 îles ; chargement complet, pas d'économie, on sort les Seals et on capture l'île ; en face, **que des Seals** (pas de Mules ni de Bears à gros canons). **Étude toujours en lecture seule** (saves lues en structure seulement : `slot_5, 9, 12, 13, 15, 17, 18, 19, 0`).

**Verdict : c'est faisable, et presque sans rien modifier.** La composition des défenseurs d'une île dépend d'un nombre propre à chaque île, `difficulty_factor` (de 0,00 à 0,75), écrit dans la sauvegarde. Il n'y a **aucun réglage de menu** pour imposer « que des Seals » (le générateur d'ennemis est dans le programme, INFÉRÉ d'après les symboles du Mac `c_enemy_spawner::spawn_land / spawn_plane / spawn_turret / spawn_ship`), mais les îles à 0,00 le font toutes seules.

**Ce que les défenseurs contiennent selon `difficulty_factor`** (LU : `spawn_data` détaillé île par île dans les sauvegardes n°9 et n°17, et comptage global sur 10 sauvegardes ; dans `spawn_data`, type 0 = terrestre, 1 = aérien, 2 = tourelle, 3 = navire) :

| `difficulty_factor` | Défenseurs relevés |
|---|---|
| **0,00** | **13 ou 19 Seals**, rien d'autre (ni tourelle, ni avion, ni bateau) |
| 0,19 | 16 Seals + 2 Walrus |
| 0,35-0,45 | Seals + Walrus (≈ moitié-moitié), **avions et hélicos**, tourelles dès ~0,39, bateaux dès ~0,44 |
| 0,56 et plus | + **Bears** (1 à 5), davantage de tourelles et de bateaux |
| 0,75 | jusqu'à ~22 véhicules terrestres (Seals, 12 Walrus, 4-5 Bears), 6 tourelles, 4 bateaux, plusieurs avions |

- **Aucune Mule** n'apparaît parmi les défenseurs dans les 10 sauvegardes lues (types vus : 2, 4, 6, 8, 10, 12, 14, 59, 77, 79). Les Bears n'arrivent qu'à partir de ~0,56.
- **Les Seals de l'île facile** : 400 PV, **une seule tourelle de 15 mm** (12 de dégâts de base) + une caméra (LU, 32 Seals relevés). Pas de gros canon.
- **Où sont les îles à 0,00** (LU, 5 sauvegardes) : la difficulté **monte avec la distance à l'île de départ la plus proche**, de façon irrégulière jusqu'à 0,75 (corrélation +0,54 à +0,81). Dans les **3 sauvegardes à 2 départs** (n°9, 13, 17), l'île la plus proche de chaque départ (~13 km) est à 0,00-0,11. Dans les **2 sauvegardes à 5 départs** (n°5, 15), les voisines à ~12-13 km vont de 0,00 à 0,75 : **la règle n'est pas sûre**. Avec 4 îles, il est **possible** que les trois autres soient faciles (INFÉRÉ, jamais essayé) ; sinon on le voit sur la holomap.
- **Tu peux le voir avant d'y aller** : la carte holomap et la carte de contrôle des véhicules dessinent des **icônes de difficulté** sous le nom de chaque île (`island:get_difficulty_level()`, LU `screen_holomap.lua:295-311` et `screen_vehicle_control.lua:1299-1305`). Le lien exact niveau d'icônes ↔ `difficulty_factor` : INCONNU.
- **Les défenseurs ne sont créés qu'à l'approche** : dans la sauvegarde n°19, 23 îles sur 24 ont `is_set="false"` et aucun défenseur (LU). Donc changer `difficulty_factor` **avant la première approche** devrait changer la composition (INFÉRÉ, jamais essayé).

**Leviers, du plus simple au plus risqué :**
| # | Levier | Effet | Faisabilité | Risque | Effort |
|---|---|---|---|---|---|
| P1 | **Partie personnalisée, 4 îles, difficulté de base 1, chargement complet, plans tous** — et on **regarde les icônes** ; si une île est trop dure, on régénère ou on évite cette île | rien à installer | haute (LU menu) | 🟢 | S |
| P2 | Partie hébergée en coop : **1 équipe humaine, 0 équipe IA** (0 IA permis seulement en multijoueur, LU `screen_menu_main.lua:1113`) : tous les amis dans la même équipe, un porte-avions (10 sièges) | pas de porte-avions IA ; il ne reste que l'IA rouge des îles | haute | 🟡 (héberger : mot de passe) | S |
| P3 | **Éditer `difficulty_factor` à 0** dans une sauvegarde neuve (avant d'approcher), puis héberger/charger cette sauvegarde | île garantie « que des Seals » | moyenne (jamais essayé ; une sauvegarde éditée peut mal se charger, toujours sur copie) | 🟡 | S-M |
| P4 | « Mieux chargée » : **pas de réglage**. Le nombre de Seals à 0,00 est de 13 à 19. Seul levier : PV / blindage du Seal dans `constants.txt` — **global**, donc aussi pour tes Seals | île plus coriace, pas plus peuplée | haute | 🟢 | S |

**Pas d'économie ? Pas tout à fait.** Dans la sauvegarde n°19 (partie neuve vieille de ~10 min, faite avec Revolution) le départ donne **4 Seals en baie + 2 Seals en stock sur l'île de départ** (+ 2 Walrus, 2 Bears, avions, 20 modules virus, 4 tourelles 30 mm), soit **~6 Seals** et non 8 ou plus (LU, `facility/inventory` de l'île de départ). Le contenu **exact** d'un vrai départ « complet » : INCONNU (à lire en essai). Pour sortir « que des Seals » en nombre, il faut en fabriquer (500 chacun, 120 s : `constants.txt:106, 169`). Deux façons :
- **Mod de constantes minimal** (le « B » du §3.3, réduit à 3 lignes) : Seal à 100-150 de coût et 20-30 s, module virus moins cher. Aucun autre effet sur le jeu (hors Seals de l'IA : le coût ne les touche pas ; les PV oui s'ils sont changés).
- Éditer la quantité de Seals en stock (`facility/inventory/quantities`, `i="1"`) dans la sauvegarde neuve (INFÉRÉ ; 🟡).

**Dégâts Seal contre Seal** : la formule a été **trouvée dans le code** (voir §10 ter) : chaque tir fait « dégâts de l'arme − blindage », avec un **minimum de 1**. Un Seal défenseur (15 mm = 12 de dégâts) fait donc **2 par tir** à ton Seal (blindage 10). Le **30 mm** fait 18, le **40 mm** fait 40. Cadence de tir : INCONNUE (pas dans les fichiers) → à chronométrer en jeu.

**Capture** : modules virus (20 en stock au départ dans la sauvegarde n°19), à déployer sur le centre de commandement ; les tourelles de l'île passent à ton équipe (manuel, `localization.csv:826`). Sans équipe ennemie (P2), la partie n'a probablement **pas de fin automatique** (INFÉRÉ) : la capture de la dernière île est l'objectif, annoncé à la main.

**Le plus petit test (P1, aucun mod, aucun patch à retirer, solo)** — jeu lancé par le moddeur, jamais par moi :
1. Menu → NEW GAME → CUSTOM : Îles **4**, Équipes IA **1** (minimum en solo, c'est le porte-avions rival ; tu peux l'ignorer), Îles de départ **1**, Difficulté **1**, Chargement **complet**, Plans **tous** → START.
2. Ouvrir la **holomap** : noter le nombre d'icônes de difficulté de chacune des îles et leur distance.
3. Relever le parc de départ (écran de chargement : baies terrestres 1-8) et le **stock de Seals** (écran de chargement, chiffre sous l'icône du Seal).
4. Approcher UNE île à 0 icône/1 icône avec 2-3 Seals : compter les défenseurs, leurs armes, et ce que fait un tir de 15 mm sur ton Seal (barre de PV).
5. Quitter sans sauvegarder, ou sauvegarder dans un emplacement de test.
**Risque de sécurité : 🟢** (solo, rien d'écrit ni installé). Pour P2 (coop avec amis), même test mais en **HOST** avec mot de passe : 🟡 (partie réseau).

**Ce qui reste valable de l'étude PvP** : l'avertissement sur `temps_x2` (la simulation imposée à tous), les mods locaux envoyés aux invités (§6), la restauration (§9.3). **Ce qui tombe** : l'arbitre d'île centrale, la carte symétrique, le 2e porte-avions.

---

## 10 ter. Dégâts Seal contre Seal (29/10) : la formule est dans le code

**Méthode** : désassemblage, en lecture seule, de la **copie** de l'exe du dépôt (`tour/sauvegardes/carrier_command_1.5.18_original.exe`, pas celui du jeu ; outils `capstone` déjà installés). Rien d'exécuté.

**LU dans le code (1.5.18, Windows)** :
- Le tableau des **dégâts de base par type de projectile** est lu en `0x746450` (il lit les mêmes valeurs que `constants.txt`).
- Le tableau des **blindages par type de véhicule** est la fonction `0x5e8ba0` (elle renvoie `land_wheel_light_armour`, etc.).
- La fonction `0x7414b0` (appelée par le traitement d'un tir, `0x746651`) **applique les dégâts à un véhicule** : en `0x7418ab-0x741934`, elle fait
  1. `dégâts = dégâts du tir − blindage de la cible`, **ramené à 0 si négatif** ;
  2. seulement si la cible est un **porte-avions** et la source une bombe ou une roquette : ×0,25 (bombe) ou ×0,1 (roquette) (`missile_damage_scale_bomb/rocket`) ;
  3. **minimum 1** (`cmp edx,1 ; cmovbe edx,eax`) ;
  4. soustraction aux PV (`[véhicule+0x180]`).
- **INFÉRÉ** : que cette fonction soit bien celle qui reçoit un tir de canon de Seal (appel lu, arguments non suivis jusqu'au bout) ; qu'il n'y ait pas de coefficient caché : un facteur ×5 existe pour un cas de projectile non identifié (`0x7465e8`) et je n'ai pas lu les dégâts de zone (rayon 10 m des 15/30/40 mm, `constants.txt:26-30`) : un obus pourrait toucher plusieurs Seals serrés.

**Dégâts par tir (base − blindage, mini 1)** — PV de tous les véhicules terrestres : 400 :

| Arme (base) | contre Seal (blind. 10) | Walrus (20) | Bear (40) | Mule (60) | Tourelle d'île (20, 800 PV) |
|---|---|---|---|---|---|
| **Canon 15 mm** (12), celui des défenseurs | **2** | 1 | 1 | 1 | 1 |
| **Auto-canon 20 mm** (10), arme d'**avion**, pas de Seal | **1** | 1 | 1 | 1 | 1 |
| **Canon 30 mm** (28) | **18** | 8 | 1 | 1 | 8 |
| **Canon 40 mm** (50) | **40** | 30 | 10 | 1 | 30 |
| Canon 100 mm (80) | 70 | 60 | 40 | 20 | 60 |
| Canon lourd (100) | 90 | 80 | 60 | 40 | 80 |

**Tirs pour détruire un véhicule de 400 PV** : Seal : 15 mm = **200**, 30 mm = **23**, 40 mm = **10**, 100 mm = 6. Walrus : 30 mm = 50, 40 mm = 14. Bear : 30 mm = **400**, 40 mm = 40, 100 mm = 10. Mule : 40 mm = **400**, 100 mm = 20.

**Ce que ça dit, en clair**
- Ton souvenir est **exact** : le 20 mm est un auto-canon d'avion (10 de dégâts) ; il ne fait que **1** par tir sur un Seal. Le **30 mm** fait peu (18, et **1** contre un Bear), le **40 mm** beaucoup (40 contre un Seal, 10 contre un Bear). Plus la cible est blindée, plus l'écart 30 mm / 40 mm est grand.
- **Seals défenseurs (15 mm) contre tes Seals** : 2 dégâts par tir, soit 200 tirs pour en tuer un seul. Une île « 0,00 » est donc **peu dangereuse** pour des Seals, même nombreuse (13 à 19), tant que la cadence reste normale. À confirmer au chronomètre.
- C'est aussi la raison pour laquelle **les Bears et les Mules** (blindage 40 et 60) sont des murs : un 15 mm ou un 30 mm leur fait **1** par tir. Une île sans Bears ni Mules (difficulté < ~0,5) est ce qui rend un essaim de Seals jouable avec du 30 mm / 40 mm.
- **Leviers pour « un peu standard mais plus dur »** (tous dans `constants.txt`, donc par mod, **globaux**, effet INFÉRÉ jusqu'à l'essai) : `projectile_type_15mm_damage` 12 → 20 ferait **10** par tir aux Seals défenseurs (au lieu de 2) ; ou baisser `land_wheel_light_armour` 10 → 5 (touche aussi tes Seals) ; ou monter `land_wheel_light_hp`. Je ne recommande **rien** avant d'avoir chronométré une vraie scène en jeu.

**Ce qui manque** : la **cadence de tir** de chaque tourelle (pas dans les XML, dans le code) et les dégâts de zone. Un chronométrage de 30 s en jeu suffit : compter les tirs reçus par seconde et la baisse de PV d'un Seal.

---

## 11. Fichiers lus (pour retrouver les preuves)
`rom_0/scripts/screen_menu_main.lua` (menu hôte, réglages, rejoindre), `screen_vehicle_loadout.lua`, `screen_vehicle_control.lua`, `screen_inventory.lua`, `library_vehicle.lua`, `library_enum.lua`, `constants.txt` · `rom_0/game_objects/vehicle_chassis_wheel_{small,medium,heavy,mule}.xml`, `vehicle_chassis_carrier.xml` · `rom_0/biomes/`, `tile_prefabs/`, `tiles/` · `rom_0/locale/localization.csv` · `server_config.xml` · `logs/game_log_*.jsonl` · mods Workshop installés (`mod.xml`) · `%APPDATA%\Carrier Command 2\saved_games\slot_19\save.xml` (structure seulement) · `partage_detail/07, 08, 12`, `tour/idees_et_demandes/IDEES.md`, `tour/etudes_demarrage_auto/ETUDE.md`, `tour/etudes_roulage_retour/ETUDE.md`, `tour/etape3/module_exe_*.md`, `tour/outils/patch_exe.py` et `mods_actifs.py` (syntaxe seulement, rien exécuté), notes des conversations liées.

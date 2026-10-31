# Glossaire du projet

Vocabulaire tel que les notes l'emploient. Chaque entrée cite la note où le mot est défini ou employé de façon claire ; quand deux notes donnent des sens différents, c'est signalé. Classement : lieux et acteurs · builds et fichiers · outils de patch · notions du jeu · mesures et étiquettes.

## Lieux, acteurs, façon de travailler

| Terme | Sens dans les notes | Source |
|---|---|---|
| **CC2** | Carrier Command 2, jeu Steam (appid 1489630) | `DEMARRER_cc2_patchs.md:9` ; `tour/PASSATION_coordination_29-10.md:22` |
| **Mac** | Le Mac du moddeur et la version Mac du jeu (`build_mac`, sous Rosetta). Il sert maintenant de « dictionnaire de noms » : le binaire Mac a ses noms de fonctions, celui de Windows non | `DEMARRER_cc2_patchs.md:125` ; `DEMARRER_cc2_patchs.md:375` |
| **tour** | Le PC Windows du moddeur où tourne le jeu Windows ; aussi le dossier `tour/` du dépôt, où ce travail est écrit | `passation_windows/JOURNAL_tour.md:20` ; `passation_windows/PASSATION_windows.md:202` |
| **Rosetta** | Traduction x86_64 sur le Mac M2 ; exécute aussi les greffes pendant les tests | `DEMARRER_cc2_patchs.md:43` |
| **atelier** | L'outil unique du Mac qui active ou retire les patchs, avec ses sécurités ; deux boutons à double-clic | `LISEZ-MOI.txt:4` ; `DEMARRER_cc2_patchs.md:51` |
| **coordination**, **conversation fille** | La conversation qui tient la carte de toutes les études, et les conversations qu'elle a démarrées, une par chantier | `tour/PASSATION_coordination_29-10.md:3` ; `tour/PASSATION_coordination_29-10.md:42` |
| **fiche de passation**, **ÉTAT À LA PASSATION** | Note d'état écrite pour qu'une autre conversation reprenne le travail (objectif, établi, posé, attend le moddeur, prochaine action, pièges) | `tour/scenario_pvp/ETUDE.md:3` ; `tour/etude_mise_a_jour/PASSATION.md:1` |
| **DYOR**, **Sample_Fox**, **Native Bridge** | Moddeurs de la communauté ; DYOR est l'auteur présumé du SDK public ; Sample_Fox va s'appuyer dessus ; « Native Bridge » est leur futur pont Windows, à l'origine de la demande de symboles | `tour/POINT_POUR_LE_MAC.md:36` ; `tour/POINT_POUR_LE_MAC.md:37` ; `DEMARRER_cc2_patchs.md:373` |
| **Geometa** | Site des bugs et idées du jeu (domaine geometa.co.uk), où les demandes sont numérotées (par exemple la demande n° 1499 dans `etudes/cctv_net.md:3`) ; bloque (erreur 429) au-delà d'environ 60 pages en une minute | `DEMARRER_cc2_patchs.md:227` |
| **Revolution** | Gros mod Workshop (identifiant 3460002110) qui remplace les écrans de contrôle des véhicules ; désactivé sur la tour ; suspecté du bug des waypoints | `DEMARRER_cc2_patchs.md:204` ; `passation_windows/JOURNAL_tour.md:222` |
| **Island Airfields** | Mod Workshop (3826940003) qui laisse avions et hélicos se poser sur les îles ; demande le SDK, solo seulement | `passation_windows/JOURNAL_tour.md:98` |
| **session cloud**, **branche à part** | Sessions Claude hébergées ; elles rendent leur travail sur une branche à part, jamais sur `main` | `passation_windows/PASSATION_windows.md:206` |
| **règle de propriété** | La tour écrit `tour/`, `extension_windows/` et le journal ; le Mac écrit le reste ; `passation_windows/reference_en/` ne se modifie pas | `passation_windows/PASSATION_windows.md:202` ; `passation_windows/PASSATION_windows.md:4` |
| **accord par phase** | Un « oui » ne vaut que pour la chose demandée, pas pour la suivante (incident du chargeur maison) | `tour/PASSATION_coordination_29-10.md:17` |
| **🟢 / 🟡 / 🔴** | Risque faible / moyen / élevé, annoncé avant toute action qui demande une autorisation | `tour/etude_mise_a_jour/ETUDE.md:42` ; `tour/PASSATION_coordination_29-10.md:12` |

## Builds, fichiers et dossiers du jeu

| Terme | Sens dans les notes | Source |
|---|---|---|
| **build_mac** | Programme du jeu sur Mac : x86_64, non strippé (les noms C++ sont lisibles), non signé ; version du 05/01/2026, md5 `b0107170…` | `DEMARRER_cc2_patchs.md:125` ; `outil/patchs_cc2.py:41` |
| **v1.5.17 / v1.5.18** | Version du programme Mac / version affichée du jeu Windows. Le nouvel exe Windows affiche encore « v1.5.18 » | `DEMARRER_cc2_patchs.md:373` ; `tour/etude_mise_a_jour/ETUDE.md:38` |
| **ancien build / nouveau build** | Avant / après la mise à jour Steam du 28/10/2026 21:30 (Steam 23836745 → 26277078 ; horodatage PE `0x6a36c177` → `0x6ae228f3`) | `tour/etude_mise_a_jour/ETUDE.md:8` ; `tour/etude_mise_a_jour/ETUDE.md:33` |
| **`1C9A01C3…`, `8E7FCBB6…`, `0C5DFE52…`, `461E1262…`** | Débuts de sha256 : exe d'origine ; origine + `ascenseur_x2` + `temps_x2` ; + `pont_retour_x2` ; nouvel exe de Steam sans patch | `tour/POINT_POUR_LE_MAC.md:8` ; `tour/etude_mise_a_jour/ETUDE.md:9` ; `tour/PASSATION_coordination_29-10.md:30` |
| **horodatage PE** | Date de compilation écrite dans l'en-tête de l'exe ; le SDK s'en sert pour reconnaître le build | `tour/etude_mise_a_jour/ETUDE.md:58` |
| **voie A / B / C** | A : l'ancien exe patché lancé à part ; B : porter les patchs sur le nouvel exe (ou, ailleurs dans la même étude, remplacer l'exe de Steam) ; C : ramener le jeu à l'ancien build par Steam. Voir `doc/CONTRADICTIONS.md` A6 | `tour/etude_mise_a_jour/ETUDE.md:92` ; `tour/etude_mise_a_jour/ETUDE.md:98` ; `tour/etude_mise_a_jour/ETUDE.md:110` ; `tour/etude_mise_a_jour/ETUDE.md:112` |
| **copie d'essai** | Exe de l'ancien build posé à côté du jeu et lancé par double-clic direct (pas par Steam) | `passation_windows/JOURNAL_tour.md:392` |
| **`rom_0`** | Dossier de données du jeu (scripts Lua 5.3.5, XML, shaders, `constants.txt`) | `DEMARRER_cc2_patchs.md:168` |
| **`library_custom_0…9.lua`** | Dix fichiers Lua vides d'origine chargés après le script de chaque écran : points d'accroche des mods. Attribution sur le Mac : 0 fumée tricolore, 1 horloge, 4 journal, 5 relevé, 6 vitesse | `DEMARRER_cc2_patchs.md:171` ; `DEMARRER_cc2_patchs.md:173` |
| **`constants.txt`** | 308 réglages du jeu (le moteur en connaît 314) ; un mod le remplace en entier | `DEMARRER_cc2_patchs.md:169` ; `partage_detail/08_constants_and_multiplayer.txt:7` |
| **mod local / mod Workshop** | Un mod posé dans le dossier de données de l'utilisateur (`mods/`) par opposition à `rom_0` ou au Workshop ; les fichiers d'un mod sont envoyés aux joueurs qui rejoignent, pas les patchs d'exe ni les DLL | `passation_windows/JOURNAL_tour.md:106` ; `DEMARRER_cc2_patchs.md:225` |
| **`cc2x.log`** | Journal du SDK, recréé à chaque lancement | `tour/PROMPT_conversation_unique_29-10.md:25` |
| **partie neuve (CUSTOM)** | NEW GAME > CUSTOM > START, utilisée parce que le chargement d'une sauvegarde plante | `passation_windows/JOURNAL_tour.md:335` |
| **`partage/`, `partage_detail/`, `passation_windows/reference_en/`, `envoi_native_bridge/`** | Notes en anglais destinées (ou non) à d'autres moddeurs : voir `doc/CARTE_DES_DOSSIERS.md` | `passation_windows/PASSATION_windows.md:4` ; `DEMARRER_cc2_patchs.md:379` |

## Outils de patch et de plugin

| Terme | Sens dans les notes | Source |
|---|---|---|
| **module « programme » / module « fichier »** | « programme » : retouches d'octets dans le binaire ; « fichier » : remplacement d'un fichier de `rom_0` (script Lua, effet) | `DEMARRER_cc2_patchs.md:87` ; `outil/patchs_cc2.py:5` |
| **retouche `imm` / `rip`** | `imm` : octets avant/après à une adresse ; `rip` : une instruction qui lit une constante est redirigée vers une autre constante déjà présente | `DEMARRER_cc2_patchs.md:88` |
| **greffe** | Code ajouté (C ou assembleur), placé dans le code mort d'ImGui (`ShowDemoWindow`, 27 Ko jamais appelés) et relié par des `jmp` | `DEMARRER_cc2_patchs.md:106` |
| **abîmé** | Module dont les octets ne sont ni tous d'origine ni tous modifiés : l'atelier refuse d'agir | `outil/patchs_cc2.py:25` |
| **relu par objdump** | Chaque instruction retouchée est relue au désassembleur après l'activation | `DEMARRER_cc2_patchs.md:27` |
| **patch direct** | Modifier les octets de `carrier_command.exe` sur le disque, comme sur le Mac, sans `dinput8.dll` ni SDK | `passation_windows/JOURNAL_tour.md:83` |
| **module d'exe (JSON)** | Fichier de changements d'octets appliqué par `tour/outils/patch_exe.py` (`etat`, `activer`, `retirer`) ; réponses `ORIGINAL`, `PATCHÉ` ou `INCONNU` | `passation_windows/JOURNAL_tour.md:85` ; `passation_windows/JOURNAL_tour.md:405` |
| **`--cest-le-vrai-jeu`** | Option exigée pour que l'outil écrive dans le vrai dossier du jeu | `passation_windows/JOURNAL_tour.md:86` |
| **site** | Un endroit modifié par un module : l'adresse d'une constante ou d'un immédiat (4 octets) | `tour/etape3/module_exe_ascenseur_x2.md:7` ; `passation_windows/JOURNAL_tour.md:49` |
| **SDK CC2X**, **`dinput8.dll`** | Boîte à outils publique d'un moddeur (DYOR) : une `dinput8.dll` posée à côté de l'exe qui reconnaît le build, pose des crochets et charge les plugins `cc2x_*.dll`. **Code d'un tiers** : le moddeur exige relecture complète et accord | `tour/POINT_POUR_LE_MAC.md:36` ; `tour/etude_mise_a_jour/ETUDE.md:12` ; `passation_windows/NOTE_mac_frein_seul_27-10.md:8` |
| **profil (du SDK)** | Horodatage PE + taille d'image + adresses connues pour un build ; le SDK n'en a qu'un (1.5.18-win32), hors profil il reste inactif | `tour/etude_mise_a_jour/ETUDE.md:57` |
| **plugin** | DLL chargée par le SDK : `cc2x_frein.dll`, `cc2x_modes.dll`, `cc2x_cc2_patchs.dll` ; chacune a sa propre barrière de version | `tour/etude_mise_a_jour/ETUDE.md:48` ; `tour/etude_mise_a_jour/ETUDE.md:60` |
| **extension_windows : groupe, portier, tremplin, ASLR** | Groupe : famille de retouches avec un interrupteur éteint par défaut ; portier : contrôle de version avant toute écriture ; tremplin/crochet : code qui détourne l'exécution vers du C en sauvegardant les registres ; ASLR : déplacement du programme en mémoire par Windows | `extension_windows/README_FR.md:9` ; `extension_windows/README_FR.md:31` ; `extension_windows/README_FR.md:62` ; `extension_windows/README_FR.md:42` |
| **chargeur maison** | Chargeur à nous, destiné à remplacer le SDK de DYOR ; phases P0 (faite) puis P1 (non accordée) ; travail arrêté | `tour/idees_et_demandes/IDEES.md:98` ; `tour/PASSATION_coordination_29-10.md:56` |
| **capstone, Zig** | Désassembleur Python et compilateur C installés par `pip` sur la tour avec l'accord du moddeur | `passation_windows/JOURNAL_tour.md:47` ; `tour/POINT_POUR_LE_MAC.md:60` |
| **`python -I`** | Exécution isolée imposée pour les scripts Python du dépôt | `tour/etude_mise_a_jour/PASSATION.md:17` |

## Les patchs et mods, par nom

| Terme | Sens dans les notes | Source |
|---|---|---|
| **`ascenseur_x2`** | Ascenseur, grue et roulage sur le pont environ ×2 plus rapides contre ×2 d'énergie. Sur Mac 34 retouches, sur Windows 32 changements | `LISEZ-MOI.txt:16` ; `tour/etape3/module_exe_ascenseur_x2.md:7` |
| **`temps_x2`** | Simulation ×2 pour les **tests** (facteur de vitesse du serveur 1,0 → 2,0) ; jamais en partie hébergée | `tour/etape3/module_exe_temps_x2.md:8` |
| **`pont_retour_x2`** | Roulage ×2 sur le pont au retour (30,0 → 15,0) | `outil/modules/pont_retour_x2.py:7` |
| **`atterrissage`, réglage A / B, cercle, créneau** | A : créneau de piste élargi seul ; B : A + circuit d'attente en cercle (choisi par le moddeur). Sur Windows, deux modules séparés `atterrissage_cercle` et `atterrissage_creneau` | `DEMARRER_cc2_patchs.md:241` ; `tour/outils/modules_exe/atterrissage_cercle.json` |
| **`helicos_approche_x2`, `helicos_pres_ascenseur`** | Hélicos : approche ×2 ; toucher près de l'ascenseur | `DEMARRER_cc2_patchs.md:273` |
| **`grue_annulation`** | Un 2e appui sur le bouton de baie ramène à sa baie un avion déjà pris par la grue | `DEMARRER_cc2_patchs.md:310` |
| **`cctv_net`** | Écran des caméras CCTV en 512 × 512 | `DEMARRER_cc2_patchs.md:326` |
| **`vitesse_escadrille`, `vitesse_boutons`** | Modes de vitesse de l'escadrille et la barre de boutons associée (sens Mac de ECO / NORMAL / FLANK) | `DEMARRER_cc2_patchs.md:337` |
| **ECO / NORMAL / FLANK** | Sur le Mac : plancher de vitesse de l'IA (ECO = jeu d'origine, NORMAL ≈ 80 %, FLANK = plein gaz). Sur Windows (étude des modes carburant) : plafond de gaz (ÉCO) ou plancher de gaz (FLANK) posé par le plugin `cc2x_modes` | `DEMARRER_cc2_patchs.md:341` ; `tour/etudes_modes_carburant/PASSATION.md:4` ; `tour/etudes_modes_carburant/plugin/RISQUES_v2.md:11` |
| **gaz** | La commande de gaz de l'avion (nombre de 0 à 1 à +0x314 de l'objet avion) que le plugin lit et écrit ; FLANK = plein gaz | `tour/etudes_modes_carburant/PASSATION.md:4` ; `DEMARRER_cc2_patchs.md:341` |
| **HELD** | État du plugin `cc2x_modes` pour l'avion que le joueur pilote à la main : « HELD, modes paused ». La fiche interdit de mettre en mode un avion piloté tant que HELD n'a pas été vu | `tour/etudes_modes_carburant/plugin/cc2x_modes.c:312` ; `tour/etudes_modes_carburant/PASSATION.md:8` |
| **`effet_tele`**, **`interface_x2`** | Supprime l'effet vieille télé de l'interface de pilotage ; interface plus fine (en réserve, le moddeur n'en veut pas) | `outil/modules/effet_tele.py:2` ; `DEMARRER_cc2_patchs.md:238` |
| **horloge, journal, relevé** | Affichages Lua : temps de jeu ; chronomètre des retours d'avions ; note des mesures dans un fichier (lignes `CC2R1`) | `DEMARRER_cc2_patchs.md:12` ; `LISEZ-MOI.txt:25` ; `DEMARRER_cc2_patchs.md:290` |
| **`cc2_mesures`, `cc2_carte`, `cc2_modes`** | Mods locaux de la tour : horloge/journal/SIM/SORTIES ; enregistreur de positions ; modes carburant | `tour/etude_mise_a_jour/ETUDE.md:67` ; `tour/etude_mise_a_jour/ETUDE.md:72` ; `tour/PROMPT_conversation_unique_29-10.md:21` |
| **SIM**, **SORTIES** | Affichages du mod de mesures : SIM = temps de jeu ÷ temps réel ; SORTIES = heures d'ordre et de décollage de chaque avion | `passation_windows/JOURNAL_tour.md:204` ; `passation_windows/JOURNAL_tour.md:228` |
| **courbes du lag** | Page HTML de courbes faite après la partie à partir du relevé (« fais les courbes de ma dernière partie ») | `LISEZ-MOI.txt:43` ; `DEMARRER_cc2_patchs.md:285` |

## Notions du jeu

| Terme | Sens dans les notes | Source |
|---|---|---|
| **tick** | 1/30 s de simulation ; la simulation tourne chez l'hôte | `DEMARRER_cc2_patchs.md:163` |
| **temps de jeu** | `update_get_logic_tick()` ÷ 30 ; seule mesure valable, car la machine ralentit (le Mac tombe à 50-72 % de vitesse) | `DEMARRER_cc2_patchs.md:42` |
| **porte-avions, baie, hangar, grue, ascenseur, piste** | Le bateau du moddeur ; les emplacements d'avions du hangar ; la grue les amène à l'ascenseur, la piste est un emplacement **unique** partagé par avions et hélicos | `etudes/RESULTATS_etude.md:30` ; `etudes/RESULTATS_etude.md:31` |
| **créneau de piste** | Le seul emplacement de piste, tenu de l'octroi jusqu'à l'avion sur l'ascenseur : le vrai goulot | `partage/README.txt:40` |
| **circuit d'attente, porte** | Ovale de 12,3 km où les avions attendent ; la « porte » est le seul endroit où la piste est donnée dans le jeu d'origine | `DEMARRER_cc2_patchs.md:148` ; `DEMARRER_cc2_patchs.md:152` |
| **états d'accostage (`dock_state`)** | 0 en vol, 1 atterrissage, 2 sortie demandée, 3 sortie, 4 au hangar, 5 file d'atterrissage, 6 roulage retour, 7 attente au lancement | `DEMARRER_cc2_patchs.md:139` |
| **bouton rouge** | « Attendre au lancement » : existe déjà en jeu, à ne pas refaire | `DEMARRER_cc2_patchs.md:355` |
| **`taxi_a`, `lift_upper_wait`** | Nœuds du pont : `taxi_a` sur la piste, puis l'attente avant l'ascenseur | `etudes/piste_et_pont.md:18` |
| **Albatros / Manta / Razorbill / Petrel** | Avion léger / avion lourd / hélico léger / hélico lourd | `partage_detail/00_README.txt:42` ; `etudes/ETUDE_helicos_2e_ascenseur.md:22` |
| **Seal / Walrus / Bear / Mule** | Châssis terrestres (400 PV, blindage 10 / 20 / 40 / 60) ; le Seal est amphibie | `tour/scenario_pvp/ETUDE.md:97` |
| **verrou T, cadre rouge** | Touche qui pose une cible verrouillée choisie par le Lua de l'interface ; ne verrouille que des ennemis observés (repérés ou marqués) | `tour/etudes_missiles/DIAGNOSTIC.md:16` ; `tour/etudes_missiles/DIAGNOSTIC.md:19` |
| **détecteur du missile** | Recherche automatique de cible par le missile en vol : 4 000 m, cône d'environ 45° | `tour/etudes_missiles/DIAGNOSTIC.md:162` |
| **`difficulty_factor`** | Nombre propre à chaque île (0,00 à 0,75) qui fixe la composition des défenseurs | `tour/scenario_pvp/ETUDE.md:269` |
| **holomap** | Carte du jeu ; dessine des icônes de difficulté sous chaque île | `tour/scenario_pvp/ETUDE.md:284` |
| **CCTV** | Écran des caméras du pont (`screen_veh_top_r`) | `etudes/cctv_net.md:3` |
| **plancher de vitesse** | Vitesse minimale que le programme impose quand l'IA vise un point : Albatros 48 m/s, Manta 72 m/s | `etudes/ia_vitesse.md:9` |

## Mesures et étiquettes de preuve

| Terme | Sens dans les notes | Source |
|---|---|---|
| **LU / MESURÉ / INFÉRÉ / RAPPORTÉ** | LU : dans un fichier ou une page ; MESURÉ : calculé ou comparé par un script (ou vu en jeu), résultat vu ; INFÉRÉ : déduit, à vérifier ; RAPPORTÉ : dit par un tiers ou une autre conversation, non revérifié. Le mot MESURÉ n'a pas partout le même sens (voir `doc/CONTRADICTIONS.md` C7) | `tour/etude_mise_a_jour/ETUDE.md:4` ; `tour/PASSATION_coordination_29-10.md:3` |
| **[GAME] / [ASM] / [EST] / [UNV]** | Étiquettes des notes anglaises du Mac : vu en jeu ; lu au désassemblage ; estimation ; non vérifié | `partage_detail/00_README.txt:34` |
| **Établi (mesuré)**, **Hypothèse retenue (non prouvée)**, **estimation à l'œil** | Étiquettes du journal de la tour : mesuré sur la tour ; explication de travail sans preuve ; durée estimée par le moddeur sans chronomètre | `passation_windows/JOURNAL_tour.md:311` ; `passation_windows/JOURNAL_tour.md:303` ; `passation_windows/JOURNAL_tour.md:224` |
| **étape 0 bis** | Mesure de référence du jeu d'origine sur Windows (4 avions lancés depuis A1, A2, A5, A6) | `passation_windows/JOURNAL_tour.md:118` ; `tour/etape1/TABLEAU_mac_windows.md:32` |
| **pont → hangar** | Durée de roulage et d'ascenseur entre le toucher et le rangement, relevée par le journal des retours ; métrique retenue sur la tour | `passation_windows/JOURNAL_tour.md:152` ; `passation_windows/JOURNAL_tour.md:243` |
| **jeu d'origine** | Jeu sans aucun patch ; « n'a toujours pas été mesuré » pour l'atterrissage (Mac) et la sortie des 4 avions (Windows) | `DEMARRER_cc2_patchs.md:366` ; `passation_windows/JOURNAL_tour.md:161` |

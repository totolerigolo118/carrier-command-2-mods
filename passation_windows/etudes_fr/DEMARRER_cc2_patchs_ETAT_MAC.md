# DÉMARRER — Atelier de patchs de Carrier Command 2

À lire en premier dans toute nouvelle conversation sur les modifications de CC2.
Dernière mise à jour : 25/10/2026 (grue ; écran des caméras CCTV en 512 × 512 ; roulage ×2 sur le pont au retour ;
vitesse de l'escadrille ECO / NORMAL / FLANK).

## 1. En trois lignes

- **Le projet** : modifier Carrier Command 2 (Steam, version Mac) au-delà de ce que permettent les mods, en
  retouchant le programme du jeu et ses fichiers.
- **Où on en est** : l'**ascenseur ×2** est fait et validé en jeu (sortie de 4 avions 3:50 → 2:15 en temps de
  jeu). L'**horloge de jeu** est installée, et l'**interface de pilotage sans effet vieille télé** aussi
  (à vérifier en jeu). Un **atelier** commun gère tous les patchs. Module **atterrissage** (réglage B choisi
  par le moddeur) **essayé en jeu le 23/10 : 4 avions rangés en 7:28, un atterrissage toutes les 1:31, aucune
  approche ratée** (jeu d'origine estimé ≈ 3 min de plus, pas encore mesuré), grâce à un **journal** qui
  chronomètre les atterrissages tout seul. **Hélicos (24/10) : approche ×2 + toucher près de l'ascenseur,
  validés en jeu : 4 hélicos 6:52 → 4:22 (−36 %), approche 1:00 → 0:28, 0 ratée.** La pose directe sur la
  plateforme a été essayée puis abandonnée (collision entre deux hélicos), en réserve. **Courbes du lag
  (24/10)** : le jeu note pendant la partie (modules `releve` + `ecriture_releve`) et Claude fait la page de
  courbes après la partie (`outil/courbes/faire_courbes.py`, voir section 6 point 5). Dans le jeu au 24/10 :
  **9 modules actifs** (ascenseur_x2, atterrissage, effet_tele, horloge, journal, helicos_approche_x2,
  helicos_pres_ascenseur, releve, ecriture_releve ; programme md5 afc9e2d8…, relu par objdump).
- **La suite** : la **1re partie avec le relevé** (le moddeur joue ~10 min par Steam, moniteur de température en
  route, puis dit « fini » ; vérifier le fichier, faire les courbes, alléger le relevé selon ce qu'on voit) ;
  puis, s'il le veut, l'essai sans le module atterrissage ; le 2e ascenseur est déconseillé.
  **Grue (25/10)** : module `grue_annulation` **ACTIF dans le jeu depuis le 25/10** (10 modules actifs, programme md5
  6fcfd65e…, relu par objdump), **pas encore essayé en jeu** (section 6 point 7).
  **Écran CCTV (25/10)** : module `cctv_net` (512 × 512) **activé dans le jeu le 25/10, à vérifier en jeu** (point 8) ;
  programme avec 11 modules (les 9 + grue_annulation + cctv_net) : md5 653fb8e6….
  **Roulage ×2 sur le pont au retour (25/10)** : module `pont_retour_x2` **activé dans le jeu le 25/10, à mesurer
  en jeu** (section 6 point 2) ; programme avec **12 modules** : md5 5db48de7…, relu par objdump.
  **Vitesse de l'escadrille (25/10)** : modules `vitesse_escadrille` (programme) + `vitesse_boutons` (barre
  ECO / NORMAL / FLANK en bas à droite des écrans de contrôle des véhicules) **activés dans le jeu le 25/10, pas
  encore essayés en jeu** (section 6 point 9) ; programme avec **14 modules** : md5 ce8dafec…, relu par objdump.
  **Phrase pour les courbes** : « fais les courbes de ma dernière partie » (ou « compare avec celle d'hier »).

## 2. Règles avec le moddeur (en plus de son CLAUDE.md)

- Il ne code pas : français simple, une seule question à la fois, finir par la prochaine action concrète.
- **Ne jamais lancer ni fermer le jeu** sans le lui demander dans le message en cours. Il teste lui-même.
- **Une seule modification testée à la fois**, sinon on ne sait plus ce qui produit quoi.
- **Mesurer en temps de jeu** avec l'horloge. Son Mac Apple Silicon n'a pas de ventilateur et fait tourner le
  jeu via Rosetta : le jeu tombe à 50-72 % de sa vitesse au fil des parties, donc un chronomètre réel ne
  vaut rien. Protocole validé : même sauvegarde, même endroit, heure de jeu au début et à la fin.
- Pendant qu'il joue, ne rien lancer de lourd (l'app Claude prend du processeur au jeu).
- **Jamais de test sur le vrai jeu** : utiliser `tests/test_patchs.py`, ou des chemins de copie passés comme
  **arguments séparés**. ⛔ Le 23/10, des options mises dans une variable zsh (`O="--programme …"` puis
  `$O`) n'ont pas été découpées : l'outil a agi sur le vrai jeu (fermé, état rétabli). L'outil refuse
  désormais tout argument non compris.

## 3. L'atelier

```
mods/cc2-patchs/
  Atelier CC2 (activer ou retirer les patchs).command   → outil --menu
  Tout remettre CC2 d origine.command                   → outil --origine
  outil/patchs_cc2.py        le moteur (états, sécurités, écriture, relecture)
  outil/modules/*.py         un fichier par patch
  outil/modules_en_reserve/  modules écrits mais hors du menu (interface_x2, atterrissage_creneau,
                             helicos_ascenseur, helicos_temoin) + copie des modules générés
  outil/generateurs/         scripts qui écrivent les tables de retouches depuis le désassemblage ;
                             helicos_ascenseur.c + generer_helicos_ascenseur.py = greffes de code (voir 4) ;
                             grue_annulation.c + generer_grue_annulation.py (réutilise son éditeur de liens) ;
                             cctv_net.s + generer_cctv_net.py (TAILLE = 512 en tête du générateur)
  fichiers/<module>/…        fichiers de remplacement des modules « fichier »
  sauvegarde/                programme d'origine reconstruit + fichiers d'origine remplacés
  tests/test_patchs.py       tests sur copies (à relancer après chaque ajout)
  tests/test_horloge.py      test hors jeu du script de l'horloge (lupa, --lua53)
  tests/test_journal.py      test hors jeu du journal des atterrissages (scénario de 4 appareils, --lua53)
  tests/test_helicos.py      modules hélicos sur copies : branchements, chaque appel relu par objdump
  tests/test_releve.py       script du relevé hors jeu (--lua53) ; --fichier X simule une partie de 15 min
  tests/test_ecriture_releve.py  greffe print() -> fichier : relue par objdump PUIS exécutée (Rosetta)
  tests/test_courbes.py      outil des courbes sur la partie simulée (vitesse, unités, activité, pause, bilan)
  tests/test_grue_annulation.py  logique de la greffe sur un faux hangar (essai_grue_annulation.c, Rosetta) +
                             relecture objdump de tout le code ajouté et des 2 branchements
  tests/test_cctv_net.py     écran CCTV : 4 branchements et tout le programme relus par objdump, puis les
                             greffes exécutées (Rosetta) dans un programme d'essai qui imite les 4 endroits
  tests/test_vitesse_escadrille.py  vitesse des avions : relecture objdump + greffe exécutée (Rosetta, 120 cas)
  tests/test_vitesse_boutons.py     barre ECO / NORMAL / FLANK hors jeu (--lua53 ; --apercu FICHIER = dessin)
  outil/courbes/             faire_courbes.py + modele_courbes.html (page des courbes du lag)
  courbes/                   pages produites (courbes_AAAA-MM-JJ_HHhMM.html)
```

Commandes : `patchs_cc2.py` (état), `--activer NOM…`, `--retirer NOM…`, `--origine`, `--menu` ; pour les
tests `--programme`, `--rom`, `--modules`, `--sauvegarde`, `--sauvegarde-rom`.

Deux types de modules :
- **« programme »** : `RETOUCHES = [("imm", adresse, octets_avant, octets_après), ("rip", adresse,
  octets_avant, ancienne_constante, nouvelle_constante, facteur)]`. « rip » = instruction SSE qui lit une
  constante par adresse relative (disp32 = 4 derniers octets) : on la redirige vers une autre constante
  **déjà présente** en lecture seule. Si `facteur` n'est pas None, l'outil vérifie nouvelle = facteur ×
  ancienne (float exact).
- **« fichier »** : `CIBLE` (chemin dans rom_0), `SOURCE` (dans fichiers/), `ORIGINE_SHA256` du fichier
  d'origine. Activer = copie de l'original dans sauvegarde/ puis remplacement ; retirer = remise de l'original.

Sécurités du moteur : jeu ouvert (`pgrep -x build_mac`) → refus ; une fois tous les modules remis d'origine
en mémoire, le md5 doit être `b0107170ddaf0245cbfee8a2d876aeb6` (sinon mise à jour Steam → refus) ;
module ni tout d'origine ni tout modifié → « abîmé », refus ; deux modules sur les mêmes octets ou le même
fichier → refus au chargement ; écriture via fichier temporaire puis relecture.

**Ajouter un patch** : 1) analyser (section 5) ; 2) générer la table depuis le désassemblage (jamais à la
main ; voir `mods/cc2-ascenseur-x2/windows/generer_table.py`) ; 3) écrire `outil/modules/<nom>.py` ; 4)
`python3 tests/test_patchs.py` (ajouter les vérifications du nouveau module) ; 5) activer sur le vrai jeu
avec l'accord du moddeur ; 6) son test en jeu avec l'horloge ; 7) mettre à jour cette fiche.

**Ajouter du code (greffe)**, quand une constante ne suffit pas : le code va dans `ImGui::ShowDemoWindow`
(0x10005af39 → 0x100061c00, 27 Ko de code mort : ni appel ni adresse dans tout le programme), une vraie zone de
code que Rosetta exécute (vérifié en jeu le 24/10). On écrit en C (ou en assembleur), `clang -arch x86_64`
compile, et `generer_helicos_ascenseur.py` relie lui-même l'objet (relocations BRANCH/SIGNED/SIGNED_n, vers
les adresses du jeu listées dans `JEU`) puis écrit un module « imm » + des `jmp` de branchement. Chaque
branchement remplace des instructions entières (aucun saut du jeu ne doit tomber au milieu : vérifié par la
liste des cibles de sauts) et les rejoue. `tests/test_helicos.py` relit tout par objdump. Occupation de la
zone : 0x10005af40…0x10005c4e0 = helicos_ascenseur (réserve), 0x100061a00…0x100061aa5 = ecriture_releve (code +
chemin du fichier), 0x100061b80…0x100061b9c = helicos_pres_ascenseur, 0x100061200…0x1000615a4 = grue_annulation
(réservé jusqu'à 0x100061600), 0x100061800…0x1000619b7 = cctv_net (réservé jusqu'à 0x100061a00),
0x10005d000…0x10005d29f = vitesse_escadrille (réservé jusqu'à 0x10005d400). Mémoire
inscriptible libre (statiques de la démo ImGui, seulement lues par ce code mort) : 0x102a2a828 (8 o) = FILE*
d'ecriture_releve ; 0x102a2a864 (4 o, __bss) = échelle de cctv_net ; 0x1029e5680…0x1029e5692 (fin du tampon
`ShowDemoWindowWidgets()::text`, __data, zéros dans le fichier, 16 Ko lus seulement par la démo) = modes de
vitesse_escadrille ; d'autres voisines dans
`nm -m | grep ShowExample` (vérifier qu'aucune adresse n'est lue hors de 0x10005af39…0x100061c00).

## 4. Ce qu'on sait du programme (Mac)

- `carriercommand.app/Contents/MacOS/build_mac` : x86_64 seul (Rosetta), **non strippé** (`nm | c++filt`
  donne les noms C++), **non signé** (rien à re-signer), offset fichier = adresse − 0x100000000. Version du
  05/01/2026. Désassembler avec `objdump -d --start-address=… --stop-address=…` (bornes : trier la sortie de
  `nm` par adresse). Constantes float partagées dans `__TEXT,__const` (0x102869720…) : **ne jamais modifier
  une valeur partagée**, rediriger l'instruction.
- **Énergie** (`c_vehicle_carrier_server_power_manager::build` 0x10019eeb8, `::tick` 0x1001b3fdc) : 5
  systèmes (réparation 0,8 ; propulsion 0,8 ; armes 0,6 ; ascenseur/grue 0,4 ; radar 0,2). Si la somme des
  demandes dépasse 1, tout est réduit au prorata. Sous-système ascenseur/grue n°0 = plateforme, n°1 = grue.
- **Plateforme de l'ascenseur** : `c_vehicle_server_carrier::tick_server_type`, pas de 0,025 m/tick ×
  énergie ; le XML `lift_constraint` ne sert à rien (le code pose la pièce).
- **Grue du hangar et roulage des avions** : `c_vehicle_server_carrier::docking_manager_air::update`
  (0x1001accd8 → 0x1001b2618, ~5 000 instructions). Roulage : `v = min(v + 0,05, 2,5 [, reste])`, `t += v /
  (L × 30)`, arrivée si reste < 0,1. Course de décollage : `addss 0,5` sans plafond. File d'attente
  abandonnée après 7201 ticks ; circuit d'approche 600-3000 m (non retouché).
- **États d'accostage** (`e_vehicle_dock_state`) : 0 en vol, 1 atterrissage, 2 sortie demandée, 3 sortie,
  4 au hangar, 5 file d'atterrissage, 6 roulage retour, 7 attente au lancement (probablement le bouton
  rouge du jeu, non vérifié).
- **Atterrissage des avions (étudié le 23/10)**, même fonction. Champs du gestionnaire (noms tirés de
  `parse_state_xml` 0x100199dde) : 0x00 mode (0 repos, 1 accostage, 2 lancement), 0x24 `runway_state`, 0x48
  `docking_queue` (éléments de 12 o : id, état d'attente, timer), 0x7c/0x80 véhicule sur l'ascenseur / la piste,
  0x110 `docking_join_time`. Véhicule : 0x220 dock_state, 0x2a0 control_mode (3 = consigne imposée), 0x2a8
  position visée, 0x2c8 vitesse visée. vcall 0xa0 = `get_is_rotor` (hélicos : attente sur place derrière le
  bateau, x −100, z −240 − 60 × rang, alt. 80).
  - **Circuit d'attente des avions** (0x1001af631…0x1001afc63, table de saut 0x1001b2600), repère du bateau
    (x latéral, z vers la proue) : ovale anti-horaire de 12,3 km = ligne x −2200 vers l'arrière (état 0),
    virage arrière centre (−1000, −1800) rayon 1200 (états 1-2), ligne x 200 vers l'avant jusqu'à z 600 (3),
    virage avant centre (−1000, 600) (4-5). Vitesse imposée 80 m/s (tour 154 s), altitude 120 + 20 × rang.
  - **Goulot** : la piste n'est donnée qu'au tick du passage 1 → 2 (bas du virage arrière, « porte »
    (−1000, −3000)), si mode 1, piste libre et à < 1000 m de la porte (bloc 0x1001af914). Sinon un tour de plus.
    La piste n'est libérée que quand l'avion est sur l'ascenseur (échange 0x80 ↔ 0x7c à 0x1001ae183).
  - Délais en dur : file abandonnée après 7201 ticks sans passer la porte ; approche ratée (remis en file à
    l'état 3) si `docking_join_time` > 3600 ticks (2 min), angle > 0,45 rad entre 50 et 400 m du bout de piste,
    bout de piste dépassé, ou plus de baie libre. Approche : cible sur l'axe 240 m devant l'avion, vitesse
    imposée 18 × (1 − avancement) + correction de l'autopilote (bornée −10/+40).
  - Simulation de la file d'attente (porte, fenêtre, tour, durée d'atterrissage O) :
    `outil/generateurs/simuler_file_atterrissage.py`.
- Autres fonctions : `docking_manager_surface` (véhicules terrestres et navires, grue arrière ; update
  inliné, à trouver), `docking_manager_lifeboat`, `c_lift_tower_controller`.
- Le jeu tourne à 30 ticks par seconde ; la simulation tourne chez l'hôte (un patch « serveur » profite aux
  joueurs qui rejoignent ; leur affichage reste d'origine).

## 5. Scripts, fichiers et effets du jeu

- `rom_0/` : `scripts/*.lua` (écrans du navire, Lua 5.3.5), `game_objects/*.xml`, `shaders/*.glsl`,
  `constants.txt` (308 réglages, 314 connus du moteur). Extensions remplaçables : xml, txtr, atlas, glsl,
  ogg, ttf, csv, anim, lua, txt.
- `library_custom_0..9.lua` : fichiers vides chargés dans chaque écran **après** son script (aussi dans
  l'affichage de pilotage, le menu pause, l'overlay et le menu principal : `c_screen_lua_libs::get_scripts`).
  Occupation : **0 = fumée tricolore** (installée dans rom_0), **1 = horloge**, **4 = journal des
  atterrissages**, **5 = relevé des performances**, **6 = vitesse de l'escadrille** (modules de l'atelier).
  **Nouvelle fonction Lua sans toucher à print** : l'entrée `{ "dofile", luaB_dofile }` de `base_funcs`
  (0x1029dd310, pointeurs rebasés : on y écrit des adresses non glissées) devient `{ "cc2_vitesse", greffe }` ;
  dofile n'est utilisé ni par le jeu ni par les mods installés. Recette réutilisable (loadfile aussi est libre).
  Revolution remplace le porte-avions : écrans de contrôle des véhicules `screen_veh_l/m/r/ll`,
  `screen_veh_captchair`, `tacops_left/middle/right_control`, `sidebar_1` ; il dessine l'échelle de la carte en bas
  à droite (y ≈ h − 30…h − 16). Côté serveur, véhicule + 0x260 = son équipe (`c_team_server*`) : + 0x14 numéro,
  + 0x19 `is_ai_controlled` (les équipes IA ne consomment pas de carburant), + 0x1a `is_neutral`. Les mods Workshop inactifs 3398249587 et 3225306468 utilisent 2 et 3. Lua utile (vu dans
  `screen_landing.lua`) : `update_get_map_vehicle_count/_by_index/_by_id`, `vehicle:get_dock_state()`,
  `get_dock_parent_id()`, `get_definition_index()` (`e_game_object_type.chassis_air_wing_light/heavy`,
  `_rotor_light/heavy`), `update_get_screen_vehicle()` = le bateau. Les écrans de contrôle des véhicules ont
  `refresh_interval="1"` dans le XML (fréquence de mise à jour non vérifiée : le journal signale un écran
  figé plus de 5 s). Aucune commande Lua trouvée pour lancer ou rappeler un avion (ça passe par des clics).
- Accroche d'un écran : envelopper `begin_load` puis tester `begin_get_screen_name()` (noms dans
  `vehicle_chassis_carrier.xml` : `screen_veh_l/m/r` = contrôle des véhicules, `screen_veh_top_m` = trafic
  aérien, `screen_veh_top_r` = caméras CCTV, `holomap_screen`…). Enveloppes avec `...` + `table.pack`.
- `update_get_logic_tick()` existe dans les écrans du navire ; `update_get_time_ms()` **non** (seulement le
  frontend, qui a les deux). `update_ui_line` existe. **`update_get_time_since_epoch()`** (secondes, heure
  réelle) existe dans les écrans du navire (`c_screen_lua_callback::bind`), comme `update_get_missile_count`,
  `update_get_projectile_count`, `update_get_screen_state_active`, `update_get_is_focus_local`.
  Les listes de véhicules et de missiles des écrans contiennent aussi ce que le brouillard cache
  (`get_is_visible()` = false). Affichage de pilotage (`vehicle_hud.lua`) : `update(screen_w, screen_h,
  tick_fraction, delta_time, local_peer_id, vehicle, map_data)`, pas de `begin_get_screen_name` (reconnu par
  `debug.getinfo(update).nparams` = 7). Bibliothèques Lua : base (dont `print`), debug, math, string, table,
  utf8 ; ni io ni os. `print` (luaB_print 0x10283ae97) écrit sur stdout, perdu quand Steam lance le jeu (d'où
  le module `ecriture_releve`). Le mod Revolution appelle souvent `print` (erreurs) : le relevé en laisse
  passer 20 par minute et par écran.
- **Sauvegardes** (`~/Library/Application Support/Carrier Command 2/saved_games/slot_N/save.xml`, XML 5 Mo) :
  `<scene logic_tick=…>`, section `<vehicles>` (`<v id definition_index team_id>`), `vehicle_states` (dock_state).
  Équipe 0 = îles, 1 = le moddeur, 2 = porte-avions adverse. 23/10 : 106 véhicules (69 sur les îles) ; 24/10 : 52 (14).
- Mods actifs sur le Mac : 2937532682 (missiles) et Revolution 3460002110 (remplace
  `screen_vehicle_control.lua`, garde `begin()` → `begin_load()`).
- **Vue de pilotage et caméra gimbal (étudié le 23/10)** : le monde 3D est rendu en **pleine résolution**
  de la fenêtre (cibles `gbuffer`, `post`, `depth` à la taille de l'écran, `c_frontend_renderer::update`
  0x1001ecdc2). L'**interface** (viseur, échelles, textes de `vehicle_hud.lua`) est dessinée dans la cible
  `hud_ui_target` de **256 px de haut** (largeur = rapport d'écran × 256) : `movl $0x100, %r9d` à
  0x1001ed3f4 (octets `41 b9 00 01 00 00`) et `mulss [256.0]` à 0x1001ed3b7 (constante 0x102869944),
  filtrage « 0 » (probablement au plus proche). Puis `pass_hud_ui` (0x1002143da) la pose sur l'écran avec
  `c_material_screen_crt_hud` = `shaders/screen_crt_hud.glsl` (luminosité 1, déformation 0, effet 1) ;
  `pass_overlay_ui` utilise le même effet. Pour une interface plus fine : 384.0 existe (0x10286973c), 512.0
  aussi (0x102869b58), **768.0 n'existe pas**. Le Lua place l'interface en pixels fixes : plus de pixels =
  éléments plus petits à l'écran. Coût en performances quasi nul (2D). `shaders/screen_crt.glsl` = écrans
  du pont (non touché).
- **Écrans du pont (étudié le 25/10, `etudes/cctv_net.md`)** : chaque écran a UNE image (fond + interface Lua),
  créée dans `create_lite` (0x1000ad74f) selon son `type` XML : tables u32 0x1028b1470 (hauteurs 128,128,256,256,
  192,32) et 0x1028b1488 (largeurs 128,256,512,256,256,64) ; type 0 = 128 × 128 = 35 écrans. Le Lua reçoit sa
  taille d'autres tables (float, `tick_screens` 0x10011e363). `render_screen` (0x10021cc14) : fond (type 9 =
  caméra : rendu 3D simplifié, textures seulement, `render_command_screen_background`), puis caméra de
  l'interface = taille de l'image, et `c_ui::element_clip::render` = glScissor en unités Lua prises pour des points.
  Filtrage de l'image : MAG au plus proche, MIN mipmaps. `screen_crt.glsl` reçoit la taille de l'image (franges,
  grain). Définition d'un écran (0x78 o) : 0x18 `script_file_name` (mm_string : texte, longueur à +8), 0x60 type.
- Multijoueur : les fichiers passés par le **système de mods** sont envoyés aux joueurs qui rejoignent ; les
  fichiers écrits directement dans rom_0 et les patchs du programme, non.
- Site des bugs et idées : https://geometa.co.uk/support/carriercommand. ⛔ Il bloque (Error 429, plus d'une
  heure) au-delà d'environ 60 pages en une minute. Relevé du 23/10 : `ZClaude/outils/cc2-tracker/`.

## 6. Feuille de route (ordre proposé au moddeur le 23/10)

1. **Vue de pilotage et caméra gimbal plus nettes** — FAIT le 23/10, **à vérifier en jeu par le moddeur**.
   Maquette `maquette_camera_cc2.html` (6 variantes, simulation WebGL avec la police lanapixel et le vrai
   effet) ; il a choisi la **variante 2 « Sans effet »** (mêmes tailles, image propre) → module
   `effet_tele` (ACTIF). Le calcul d'origine reste dans le fichier avec un poids nul (`step(1e30,
   animation_time)`) pour garder les 15 uniforms actifs ; compilation vérifiée par
   `tests/test_effet_tele_web.html` (WebGL 2). Le module « interface 2× plus fine » a été écrit et testé
   (`outil/modules_en_reserve/interface_x2.py`, 3 octets) mais le moddeur **n'en veut pas** (23/10) : hors du
   menu, à ne pas réinstaller sans qu'il le demande.
2. **Atterrissages plus rapides** (demandes 23487, 14728, 1163) — module `atterrissage` ÉCRIT et testé sur
   copies le 23/10, **activé dans le jeu le 23/10 (avec ascenseur ×2), à mesurer en jeu**. Réglage B choisi par le moddeur : A « créneau élargi » (3
   sauts redirigés vers le bloc 0x1001af914 : piste possible sur tout le virage arrière, ~2,7 km) + « circuit
   en cercle » (le virage avant prend le centre du virage arrière : tour 7,5 km / 94 s ; 6 lectures de
   constantes redirigées + `addss` → `subss` à 0x1001af87b). 10 retouches générées par
   `outil/generateurs/generer_atterrissage.py`, md5 avec ce module seul 073338c4…. Le réglage A seul est en
   réserve (`modules_en_reserve/atterrissage_creneau.py`, mêmes octets : jamais les deux dans `modules/`).
   Simulation (4 avions, durée d'un atterrissage O inconnue) : groupés O = 110 s → 609 s d'origine, 510 s avec
   B ; **B est plus lent si O ≈ 140-160 s** (l'avion suivant arrive trop tôt et refait un tour) → alors passer
   au réglage A. Protocole de mesure : ascenseur ×2 actif, même sauvegarde, navire à l'arrêt, 4 avions
   lancés puis rappelés ; le module **journal** (23/10) affiche tout seul pour chaque avion l'heure (depuis
   l'entrée du 1er dans la file) de la piste, du toucher et du hangar, plus le total, l'écart moyen entre
   deux pistes données, l'approche moyenne, pont → hangar et les approches ratées. Un essai avec le module
   donne la durée réelle d'un atterrissage ; la simulation (`simuler_file_atterrissage.py`) en déduit le jeu
   d'origine ; l'essai sans le module (menu : retirer Atterrissages) reste la vraie preuve.
   **Essai du 23/10 (ascenseur ×2 + atterrissage, journal)** : 4 avions rangés en **7:28** (entrée du 1er dans
   la file → 4e au hangar) ; chrono du moddeur **8:15** (1er ordre de retour → fin du clignotement des baies).
   Pistes données à 1:22, 3:00, 4:20, 5:56 = **une toutes les 1:31** ; approche moyenne 0:49 ; pont → hangar
   0:51 ; **0 approche ratée** ; écran jamais figé. La piste se libère ~38-41 s après le toucher (piste
   suivante donnée aussitôt) → occupation de la piste ≈ 88 s par avion. Simulation avec 88 s : jeu d'origine
   154-158 s par avion (un tour d'ovale), réglage B 98-104 s → mesuré 91 s. **Gain estimé ≈ 3 min sur 4
   avions (≈ −30 %), essai sans le module pas encore fait** (le moddeur : « peut-être plus tard »). Le journal
   coupait les heures « hangar » (ligne trop longue) : lignes raccourcies à ≤ 36 signes le 23/10 (vérifié par
   test, pas encore revu en jeu).
   **Piste et pont (25/10, `etudes/piste_et_pont.md`)** : après le toucher, l'avion roule jusqu'au bout avant de
   la piste puis **recule ~125 m sur l'axe** jusqu'à taxi_a avant d'aller à l'ascenseur (~42 s sur le pont) :
   rendre la piste plus tôt = collision, refusé. Choix du moddeur : **module `pont_retour_x2`** (roulage ×2 des
   états de piste 5-7 : `mulss [30.0]` → 15.0 à 0x1001b0824, 0x1001ae07c, 0x1001b0831 ; généré par
   `outil/generateurs/generer_pont_retour.py`) : pont ~42 s → ~22 s, piste occupée 88 → ~68 s. Testé sur copies
   le 25/10 (md5 seul 96d568f1…), **ACTIF dans le jeu depuis le 25/10 (accord du moddeur), pas encore mesuré**.
   À mesurer : même protocole que le 23/10 (référence 7:28, une piste toutes les 1:31, pont → hangar 0:51) ;
   attendu −0:20 (avions groupés) à −1:25 (dispersés). Idée B (avions garés sur le pont, demande 2023) : 8/10,
   4-6 sessions, déconseillée pour l'instant.
3. **Hélicos plus rapides** — FAIT et VALIDÉ le 24/10 (mesures : `etudes/MESURES_helicos.md`). Étude
   (`etudes/RESULTATS_etude.md`) : un hélico occupe la piste (case unique 0x80) pendant toute son approche
   (~1:00, le pilote automatique ne vole qu'à ~5 m/s vers un point 50 m devant) et son roulage jusqu'à
   l'ascenseur. Modules actifs : `helicos_approche_x2` (point visé 100 m devant, 0x1001ad3ef) et
   `helicos_pres_ascenseur` (toucher vers z = −40 à côté de taxi_a au lieu de z ≈ 7-30 : constantes 0x1001ad3fc
   120 → 48 et 0x1001b1066 20 → 70, greffe de 28 o qui décale la hauteur visée de 23,5 m). Résultat : 4 hélicos
   6:52 → 4:22, 0 ratée. Le moddeur trouve le toucher « légèrement à l'arrière » mais ne veut pas qu'on y touche.
   Essayé puis abandonné : `helicos_ascenseur` (voie ascenseur : un hélico se pose sur la plateforme pendant
   qu'un autre utilise la piste, case 0x84 + greffe de 5,5 Ko) → collision entre deux hélicos le 24/10 ;
   Le moddeur : « pas la priorité ». En réserve avec `helicos_temoin` (même greffe, ne fait rien).
4. **2e ascenseur** — étude faite le 23/10 : 9/10, 8-12 sessions, gain faible (la piste reste unique) →
   déconseillé. Détails, briques et alternatives dans `etudes/RESULTATS_etude.md`.
5. **Courbes du lag** (demandées le 24/10) — FAIT, **actif dans le jeu le 24/10, pas encore vu sur une vraie
   partie**. Le moddeur veut les regarder **après** la partie, hors du jeu ; lancement par Steam comme d'habitude ;
   c'est Claude qui fait la page quand il le demande ; bilan court en plus ; comparaison sur demande. Maquette
   `maquette_courbes_cc2.html` (6 présentations) : il a choisi la **n° 1 « colonne de courbes »** (4 chiffres,
   bilan, puis vitesse, images/s, unités par camp, missiles et obus, écrans allumés, activité, Mac).
   - **`releve`** (library_custom_5.lua) : chaque écran écrit avec print() une ligne `CC2R1 E … FIN` toutes les
     10 s (heure réelle `e`, top du jeu `t`, écran `s`, appels à update `n`, allumé `a`, joueur dessus `f`,
     print() de mods jetés `x`) ; holomap_screen, screen_veh_m, screen_nav_m et hud écrivent aussi `CC2R1 D …`
     toutes les 5 s dès que la seconde change (équipe `moi`, `mis`, `pro` = obus, `epa`, `pil` = véhicule
     piloté, `q<équipe>=pa,terre,avion,hélico,navire,tourelle,autre,hangar,cachés`) ; `S` au démarrage.
   - **`ecriture_releve`** (généré par `outil/generateurs/generer_ecriture_releve.py` depuis `ecriture_releve.s`) :
     0x10283aed0 et 0x10283af78 (lecture de la GOT de __stdoutp dans luaB_print) → `call` vers 0x100061a00 /
     0x100061a0d ; au 1er print(), fopen(« a ») de `~/Library/Application Support/Carrier Command 2/releve_cc2.txt`
     (repli : stdout) ; md5 avec ce module seul 8655d717…. ~0,5 Mo par heure de jeu (fichier jamais vidé).
   - **Courbes** : `python3 outil/courbes/faire_courbes.py` (dernière partie), `--liste`, `--partie N`,
     `--comparer N` → `courbes/courbes_<date>.html` (+ bilan affiché) ; à envoyer au moddeur (SendUserFile, render).
     Une partie = pas de trou de plus de 2 min et pas de retour en arrière de l'horloge du jeu. Vitesse = Δtop /
     (30 × Δs) sur 5 s ; pause = vitesse < 2 % ; activité : affichage de pilotage vivant → commandes, holomap
     avec le joueur dessus → carte, sinon pont. Mac : moyenne du processeur et maximum de la température.
   - **À vérifier à la 1re partie** : quels écrans tournent pendant le pilotage, si les « images par seconde »
     (appels à update / 10 s) collent à ce qu'il voit, si les unités adverses cachées sont bien comptées ; puis
     ne garder qu'un seul écran de données (aujourd'hui 3 écrivent la même ligne D).
6. Plus tard : le « vrai ×2 » (raccourcir le freinage final), le roulage des véhicules terrestres ×2
   (`docking_manager_surface::update` 0x1001aa404, non inliné, même modèle 0,05/2,5/0,1).
7. **Annuler la sortie d'un avion déjà pris par la grue** (demande Geometa 20652, 25/10 ; étude
   `etudes/annuler_montee.md`) — module **`grue_annulation` écrit, testé sur copies et ACTIVÉ dans le jeu le
   25/10 avec l'accord du moddeur** (md5 seul 773c3319…, jeu du 25/10 + module 6fcfd65e… = programme du jeu,
   relu par objdump après activation). Déclenchement : **2e appui sur le bouton de
   la baie** pendant que la grue s'occupe de l'avion (aujourd'hui l'annulation ne marche que dans la file, que
   la grue vide presque aussitôt). Pas encore accroché → la grue remonte et revient au repos ; accroché et pas
   encore tourné → elle le rapporte à sa baie, le pose, revient. Trop tard (rien ne change) : en train d'être
   retourné (baies de droite, ~1 s avant le lâcher), lâché au-dessus de l'ascenseur, sur l'ascenseur. Fenêtre ≈
   13-18 s avec l'ascenseur ×2. Greffe de 932 o (C) à 0x100061200 ; branchements 0x1001a8c01 (`undock`, 13 o)
   et 0x1001ad9ad (`update`, fin de grue en mode lancement, 5 o) ; généré par
   `outil/generateurs/generer_grue_annulation.py`. Le retour est repéré par l'état sauvegardé (avion « au
   hangar » dans la grue en mode lancement, ce que le jeu ne fait jamais) : il reprend après un chargement.
   Retirer le module ne bloque rien (un avion en plein retour serait passé à l'ascenseur). **Essai en jeu à
   faire** : annuler pendant que la grue va à la baie / porte l'avion / le pose sur l'ascenseur ; une baie de
   droite au moment où il est retourné (doit refuser) ; 2 avions lancés, annuler le 2e pendant que le 1er
   monte ; sauvegarder pendant un retour puis recharger. Le risque à surveiller : grue bloquée (plus de
   lancement ni d'atterrissage) → retirer le module. Extension à l'ascenseur : 8/10, déconseillée.
8. **Écran des caméras CCTV plus net** (idée Geometa 1499, 25/10 ; étude `etudes/cctv_net.md`) — le moddeur a choisi
   **512 × 512** (4 fois plus fin ; 1024 proposé, refusé). Module **`cctv_net` ÉCRIT et testé sur copies, ACTIVÉ dans le
   jeu le 25/10 à 09:04** (relu ensuite : sans lui, le programme redevient exactement celui d'avant). Seul l'écran dont le script est `scripts/screen_cctv.lua` change (aussi avec Revolution,
   même script) ; cadre, textes et boutons gardent leur taille (interface en 128 unités dessinée 4 fois plus
   grande). Greffes A-D (439 o, assembleur `cctv_net.s`) à 0x100061800 ; branchements 0x1000ad74f (`create_lite`,
   taille de l'image), 0x10021ce70 (`render_screen`, caméra de l'interface 128 × 128 + échelle 4 dans 0x102a2a864),
   0x10015e662 (`element_clip`, glScissor × échelle), 0x10021cf13 (échelle remise à 0 après l'interface, avant le
   pilotage / la pause / l'overlay). md5 avec ce module seul 18e12e18… ; jeu du 25/10 + cctv_net 2791122b….
   **Essai en jeu à faire** : vue des 2 caméras plus fine ; cadre, « 1/2 », boutons < > et texte du bas à leur
   place et entiers ; autres écrans du pont, affichage de pilotage et menu pause inchangés ; si l'interface est
   coupée ou dans un coin → retirer le module. Le lag se vérifie avec les courbes (coût attendu négligeable).
9. **Vitesse de l'escadrille** (demande du moddeur le 25/10 : ses avions sous IA « traînent à 50 % ») — étude
   `etudes/ia_vitesse.md` : en vol vers un point, l'IA vise un **plancher** (Albatros 48 m/s, Manta 72 m/s ;
   `vehicle_ai_wing_cruise_speed` = 120 n'est jamais lu). Le moddeur a choisi des **modes pour toute l'escadrille**,
   barre de la maquette n° 1 (`etudes/maquette_vitesse_ia.html`) **en anglais** : ECO (jeu d'origine) / NORMAL
   (61 / 91 m/s, ≈ 80 % de puissance, **estimation à ajuster**) / FLANK (144 m/s = plein gaz). Avions ennemis (équipes
   IA) inchangés. Modules : `vitesse_escadrille` (greffe C de 671 o à 0x10005d000 : branchement 0x1001c2b4b dans
   `c_vehicle_server_wing::tick_control` + fonction Lua `cc2_vitesse(equipe [, mode])` à la place de dofile ; mode
   gardé dans `~/Library/Application Support/Carrier Command 2/vitesse_escadrille.txt`) et `vitesse_boutons`
   (library_custom_6.lua : barre en bas à droite des écrans de contrôle, 1re fois NORMAL, clics de la barre non
   transmis à la carte ; sans le module programme, rien ne s'affiche). md5 avec vitesse_escadrille seul f03c977f….
   Tests : `tests/test_vitesse_escadrille.py` (relecture + greffe exécutée sous Rosetta : 120 cas de vitesse, fichier
   du mode), `tests/test_vitesse_boutons.py --lua53` (barre et clics), `tests/test_patchs.py` (14 modules ensemble).
   Aperçu des ordres de dessin : `etudes/apercu_vitesse_boutons.html`. **ACTIVÉS dans le jeu le 25/10** avec
   l'accord du moddeur (14 modules, md5 ce8dafec… ; branchement, base_funcs, planchers et library_custom_6.lua relus
   dans le jeu). À vérifier au 1er lancement : la barre s'affiche (sinon le module programme manque ou le nom
   d'écran diffère), un clic change le bouton allumé, la carte réagit encore aux clics ailleurs. **Essai en jeu à
   faire** : même sauvegarde, un Albatros envoyé vers un point lointain en ECO puis en FLANK, temps de jeu avec
   l'horloge et jauge de carburant → vraie vitesse et vraie autonomie, puis régler NORMAL (≈ 80 %).
« Attendre au lancement » existe déjà en jeu (bouton rouge) : à ne pas refaire.

## 7. Windows (sa tour, l'objectif final)

**Mise à jour 25/10 (soir)** : le SDK public CC2X d'un moddeur du Discord (README lu) cible **Windows 1.5.18 en 32 bits** :
les adresses et décalages du Mac (64 bits) ne se transposent pas, seuls la logique, les valeurs, les noms et les
fichiers de données passent (méthode de repérage sans symboles : `partage/11_porting_and_priorities.txt`).
**Passation pour la tour (25/10 soir)** : `passation_windows/` (feuille française `PASSATION_windows.md`, comparaison Mac/Windows, prompt à coller, notes anglaises, études, Lua à installer, copie du SDK public) ; **lire d'abord cette feuille pour tout travail sur la tour**. Décision : passer à Windows maintenant, le Mac ne sert plus que de dictionnaire de noms (plus de nouveaux patchs ni de tests longs dessus).
**Test de lancement du 25/10 à 17:26** (le moddeur absent, il avait autorisé le lancement) : les 14 modules actifs, le jeu démarre, tient 100 s au menu à pleine vitesse, se ferme proprement, aucun rapport de plantage ; `releve_cc2.txt` créé (98 lignes `CC2R1 E`) = l'écriture de `print()` dans un fichier et le crochet Lua `begin_load` marchent en jeu (au menu seulement ; CCTV, vitesse et grue pas exercés). ⚠️ Rappel : une permission « ouvre le jeu » ne vaut que pendant son absence (il est déjà revenu sans prévenir le 18/10).
Un dossier de notes en anglais pour ce moddeur est prêt : `partage/` = **3 fichiers texte à joindre** (`cc2_notes.txt`,
`cc2_reference.txt`, `cc2_sources.txt`, pas de zip : il n'en voulait pas) ; la version détaillée à 39 fichiers + son zip sont
rangés dans `partage_detail/` (source des 3 fichiers, ne pas envoyer). Aucune trace personnelle (recherche finale à 0). Il faut le mettre à jour si les patchs changent (les tableaux de `partage/10_…`
sont générés par un script du scratchpad, pas par l'atelier : à refaire à la main).

Chaque module « programme » est à refaire sur le programme Windows, qui n'a probablement pas les noms des
fonctions. Passation de l'ascenseur ×2 : `mods/cc2-ascenseur-x2/windows/PASSATION_windows.md`, en ligne sur
https://claude.ai/artifact/3vVrGcuCt7VzwzzymnBUB4. Les modules « fichier » marchent tels quels sur Windows.

## 8. Historique

- 26-27/06 : mod XML « Ascenseur rapide » sans effet (on sait aujourd'hui pourquoi).
- 29/08-05/09 : fumée tricolore, canon 160 (constants.txt), modèles 3D extraits.
- 23/10 : énergie et ascenseur décodés, ascenseur ×2 (34 retouches) validé ×1,7 ; horloge de jeu ; site des
  bugs relu (640 idées) ; passation Windows ; création de l'atelier.
- 23/10 (suite) : atterrissage décodé (circuit d'attente, porte unique, délais) ; simulation de la file (4 avions,
  fenêtre et tour) ; réglages A et B proposés, B choisi ; module `atterrissage` écrit, tests sur copies OK
  (chaque instruction retouchée relue par objdump) ; activé dans le jeu avec l'ascenseur ×2 ; module `journal`
  (chronomètre automatique des atterrissages, library_custom_4.lua) écrit, testé hors jeu et activé.
- 23-24/10 : étude hélicos / 2e ascenseur (`etudes/`) ; référence 4 hélicos 6:52 ; greffes de code en C dans
  le code mort d'ImGui ; voie ascenseur essayée (collision) puis abandonnée ; approche ×2 + toucher près de
  l'ascenseur validés : 4:22.
- 24/10 (suite) : courbes du lag : cadrage, maquette de 6 présentations (n° 1 choisie), modules `releve` +
  `ecriture_releve` (greffe : print() → fichier) et outil `faire_courbes.py`, tous testés hors jeu ; activés.
- 25/10 : grue du hangar décodée (5 gestes, l'avion reste rangé dans sa baie pendant le portage) ; module
  `grue_annulation` (2e appui = ramener l'avion) écrit et testé sur copies.
- 25/10 : écrans du pont décodés (image unique par écran, tables de tailles par type, glScissor) ; étude CCTV
  (512 ou 1024), 512 choisi ; module `cctv_net` (4 greffes) écrit, relu par objdump et exécuté sous Rosetta ; activé.
- 25/10 : vitesse des avions sous IA décodée (plancher 48 / 72 m/s, gaz, carburant, équipes) ; maquette de 6
  sélecteurs, n° 1 choisie en anglais ; modules `vitesse_escadrille` + `vitesse_boutons` écrits, testés sur copies
  et activés dans le jeu (14 modules).
- 25/10 (soir) : dossier `partage/` (3 fichiers texte : notes, tableaux + index de symboles, sources) pour un moddeur Windows ; version détaillée dans `partage_detail/` ; sous-agents pour traduire les sources, code vérifié identique.

# Revue indépendante du système « modes carburant » (ÉCO / NORMAL / FLANK par avion)

Revue du 29/10/2026, faite dans une session cloud **sans le jeu, sans Steam, sans Windows, sans Wine**. Périmètre : tout `tour/etudes_modes_carburant/`
(plugin C `cc2x_modes.c` v3 + banc d'essai + `construire_modes.py` + `modes.ini.example`, installateur `mod_modes.py`, scripts Lua `lua/` et `lua/v2/`,
notes `ETUDE.md`, `PASSATION.md`, `plugin/RISQUES_*.md`). Aucun fichier source n'a été modifié : seul ce rapport est ajouté.

Étiquettes utilisées : **[EXÉCUTÉ]** j'ai fait tourner le code et vu le résultat ici ; **[LU]** relu dans le code, non exécuté ;
**[INFÉRÉ]** raisonnement, non vérifié ; **[MESURÉ ailleurs]** donnée des journaux du moddeur (28/10) ou d'une autre étude du dépôt.
**Rien dans ce rapport ne dit qu'une chose marche en jeu** : je n'ai pas le jeu. « Le banc passe » signifie seulement « le banc passe ».

---

## 0. Verdict en dix lignes

- **Sûreté mémoire du plugin C : je n'ai trouvé aucun défaut** (tampons, bornes, écriture à `+0x314`, verrous). 130 contrôles du banc réussis sous ASan + UBSan, 0 avertissement.
- **Un constat bloquant avant l'étape (c) `enabled=1`** : la lecture de `modes.ini` peut supprimer **sans aucun message** la zone libre autour du porte-avions
  (valeur vide, « 1 500 », `nan`) et peut mettre en mode des avions cités dans un commentaire (§B1). C'est la seule protection du décollage.
- **Le garde-fou « HELD » est fail-open** et son crochet Lua peut ne jamais être posé (§I1). Aucune preuve en jeu ; l'autre étude du dépôt a même mesuré qu'un autre champ serveur
  (`CONTROL_MODE`) **ne** distingue **pas** le pilotage à la main. À garder comme condition de l'étape (c), comme le dit déjà la passation.
- **`mod_modes.py` : deux défauts de réversibilité reproduits** (§I2 : le « refus si le jeu tourne » ne voit pas l'ancien exe de la voie A pour `installer` / `mettre-a-jour` ;
  §I3 : `retirer` supprime le dossier du mod mais laisse la ligne dans `mods.xml` si celui-ci est en CRLF ou a un doublon, en disant « rien à retirer »).
- Les chiffres de carburant des notes **recoupent** les journaux (0,298–0,304 × gaz pour l'Albatros, 0,76 × gaz pour le Manta) ; en revanche le plugin compte **62,5 rappels par seconde réelle**
  dans la session du 28/10 (et non 30), ce qui change le sens des « 3 s » (§M1).
- Comptes : **1 bloquant, 6 importants, 12 mineurs**, plus 9 contradictions note/code (§6).

---

## 1. Ce qui a pu ou non être exécuté (précis)

| Élément | Résultat | Remarques |
|---|---|---|
| Tests Python existants liés au sujet : `tour/outils/test_lua_syntaxe.py` | **[EXÉCUTÉ] 51 réussis, 0 échec** | |
| `tour/outils/lua_syntaxe.py` sur `lua/library_custom_3.lua`, `lua/library_custom_5.lua`, `lua/v2/library_custom_5.lua` | **[EXÉCUTÉ] 3 fichiers OK, 0 erreur** | syntaxe seulement |
| `tour/outils/lua_inconnus.py` | **non exécuté** | exige les scripts du jeu (`C:\Program Files (x86)\Steam\…\rom_0\scripts`), absents ici |
| `test_patch_exe.py`, `test_essai_auto.py` (hors sujet) | non exécutables | `capstone` absent ; `powershell` absent |
| `test_modes.c` natif Linux (gcc 13.3, `-fsanitize=address,undefined`, `-Wall -Wextra`) | **[EXÉCUTÉ] 130 réussis, 0 échec**, 0 avertissement | avec **ma fausse `windows.h`** (verrous instrumentés, lecteur INI imitant `GetPrivateProfileStringA`) ; 64 bits ; en-tête `cc2x.h` = **la copie du dépôt** (SDK 0.4.0, sha `ed436737…`), pas celui de la compilation réelle (commit `7ab05c7`, sha `8b4dfc82…`, absent du dépôt) |
| Analyse statique `clang --analyze` de `cc2x_modes.c` | **[EXÉCUTÉ] aucun avertissement** | |
| `cc2x_modes.c` → DLL 32 bits avec **les vrais en-têtes Windows** (mingw-w64 13, `-std=c11 -O2 -fno-strict-aliasing -Wall -Wextra`, mêmes options que le SDK) | **[EXÉCUTÉ] compile, 0 avertissement**, export unique `cc2x_plugin_load` | compilateur ≠ Zig du projet : la DLL obtenue **n'est pas comparable** au sha `331581C6…` de `mod_modes.py` |
| `test_modes.c` → `.exe` Windows 32 bits (`-Werror`) | **[EXÉCUTÉ] compile** | **non lancé** : pas de Wine. Donc `GetPrivateProfileStringA`, `CRITICAL_SECTION` et l'arithmétique 32 bits réels **n'ont pas été exercés** |
| Mes scénarios supplémentaires S1–S10 sur le vrai code du plugin (sanitizers + `float-cast-overflow`) | **[EXÉCUTÉ]** | voir §B1 (S1–S6), §I6 (S8), §M3 (S7, S10), §M4 (S9) ; fichiers dans le scratchpad, **non versés** |
| `mod_modes.py` sur une fausse racine `APPDATA` avec un faux `tasklist` | **[EXÉCUTÉ]** installer / mettre-à-jour / état / retirer ; cas CRLF et doublon | |
| `mod_modes.py` : commandes `poser-plugin` / `mettre-a-jour-plugin` | **non exécutées** | `PLUGIN_SRC` = `C:\Users\UTILISATEUR\…\dist\cc2x_modes.dll`, absent ; lues seulement |
| Scripts Lua exécutés (`lua/v2/library_custom_5.lua`, 30 contrôles) | **[EXÉCUTÉ]** dans un faux environnement de jeu | Lua **5.4** (`liblua5.4.so.0` déjà installée, appelée par `ctypes`) alors que le jeu est en **5.3** ; API du jeu simulée : je vérifie la **logique** (boutons, états, erreurs, crochets), **pas** l'affichage |
| `construire_modes.py` | non exécuté | chemins Windows en dur, Zig absent |
| Vérification que la DLL `331581C6…` correspond bien au source | **impossible ici** | Zig 0.15.2 absent, DLL absente du dépôt (règle : pas de DLL commitée) |
| Le jeu, le SDK, le moindre chargement de plugin | **impossible** | |

**Avertissement de sécurité (demandé par le moddeur pour toute action qui demande une autorisation).** Pour compiler avec les vrais en-têtes Windows j'ai fait, **dans le conteneur cloud jetable de cette session
seulement**, `apt-get update` puis `apt-get install gcc-mingw-w64-i686` (+ dépendances `mingw-w64-*`, `binutils-mingw-w64-i686`), via le proxy de la session, paquets de la distribution Ubuntu
signés et vérifiés par `apt`. Les scripts de ces paquets s'exécutent en root **dans le conteneur** ; rien n'a été installé sur le PC du moddeur, aucune DLL ni exe n'est versé au dépôt
(les binaires sont dans le scratchpad, hors dépôt), aucun secret n'a été envoyé. Aucun paquet Python, aucun téléchargement de binaire hors `apt`. Le reste est fait avec des outils maison (fausse `windows.h`,
faux `tasklist`, banc Lua par `ctypes` sur une bibliothèque déjà présente).

---

## 2. Constat bloquant (à corriger avant l'étape (c) : `enabled=1`)

### B1. `modes.ini` : certaines saisies plausibles suppriment la zone libre ou ajoutent des avions, sans message

- **Où** : `plugin/cc2x_modes.c:131-137` (`ini_num`), `:152-162` (`read_ids`), `:185-195` (`read_cfg`), `:314` (zone libre), `:129` (`clampd`).
- **Preuves [EXÉCUTÉ]** (S1–S6, sur le vrai code ; le lecteur INI est **ma réimplémentation** de `GetPrivateProfileStringA`, voir « À confirmer sous Windows » ci-dessous) :

| Contenu de `modes.ini` | Effet constaté | Pourquoi |
|---|---|---|
| `eco_free_zone_m=` (vide) | l'avion à **800 m** du porte-avions est plafonné | clé présente mais vide → `""` → `atof("")` = 0 → zone de 0 m (le défaut 1500 n'est utilisé que si la clé est **absente**) |
| `eco_free_zone_m=1 500`, `flank_free_zone_m=6 000` (milliers à la française, comme dans toutes les notes) | zone lue = **1 m** et **6 m** ; ÉCO plafonne à 800 m, FLANK force les gaz à **5 000 m** du bateau | `atof` s'arrête à l'espace |
| `eco_free_zone_m=1.500` (ou `1,500`) | zone lue = 1,5 m | la virgule devient un point (ligne 135), donc « 1,500 » se lit comme « 1.500 » |
| `eco_free_zone_m=nan` | plafonné à 800 m | `clampd(NaN,…)` renvoie NaN (`v < lo` et `v > hi` sont faux) ; `dist <= NaN` est faux |
| `eco_cap_light=nan` | plus aucun plafond, et **12 lignes « settings: » en 1000 ticks** | `cfg_same` est toujours faux avec un NaN → relog à chaque lecture (cadence 90 ticks) |
| `observe_s=nan` | **comportement indéfini** (UBSan : `cc2x_modes.c:195:83: nan is outside the range of representable values of type 'int'`) | cast `(int)` d'un NaN |
| `eco_ids=9 ; avion 10 en vol` (commentaire de fin de ligne) | l'avion **10 est aussi plafonné** | Windows ne traite `;` comme commentaire qu'en **début** de ligne ; `read_ids` saute `;` et lit les chiffres du commentaire. Le banc contient ce piège sans l'asserter (`test_modes.c:263` : `eco_ids=9,10 ; 11`) |
| `eco_ids=1,…,18` | les ids **17 et 18 sont ignorés, sans aucun avertissement** (la ligne « settings: » n'affiche que 16 ids) | `MAX_IDS 16` (ligne 64), troncature silencieuse |
| `enabled=true`, `eco_all=yes` | plugin **désactivé** / option ignorée, sans message | `atof("true")` = 0 (sens sûr, mais silencieux) |
| `eco_cap_light=` (vide) | plafond **0,55** (le minimum) au lieu du défaut 0,65 | `atof("")` = 0 puis `clampd` |

- **Scénario concret de défaillance** : le moddeur prépare l'essai (c) ÉCO. Il vide la ligne `eco_free_zone_m=` « pour remettre le défaut » (comme `eco_ids=` l'est dans l'exemple). Il met `enabled=1`.
  L'avion qui **décolle** du pont est, d'après la mesure de l'étude d'atterrissage, déjà en `flight=2 dock=0 attached=0` dès le décollage (`tour/atterrissage_manuel/JOURNAL_atterrissage.md:152`, **[MESURÉ ailleurs]**) :
  le seul garde-fou qui le protège est la zone libre. Avec 0 m, le plafond de gaz (appliqué ≈ 0,72 d'après les notes) s'écrit pendant la montée initiale. Je n'affirme pas que l'avion tombe : je dis que **la protection annoncée n'existe plus** et que le journal ne le signale pas.
- **Correctif proposé** :
  1. Lecture **stricte** : copier la valeur, `strtod` avec contrôle de la fin (`espaces` tolérés, rien d'autre), `isfinite`, sinon **défaut + `WARN` une seule fois** (« clé=valeur illisible, défaut utilisé »). Une valeur **vide** = défaut.
  2. Planchers **inamovibles** pour les zones libres (par exemple ≥ 500 m ÉCO et ≥ 3 000 m FLANK dans `clampd`), comme les plafonds de gaz ont déjà leur minimum. Le test `free_zone_m=100` (`test_modes.c:352`) devrait alors changer : c'est une décision à prendre.
  3. `read_ids` : s'arrêter au premier `;` ou `#` ; n'accepter que chiffres, virgules et espaces ; **avertir** si plus de 16 numéros (ou passer `MAX_IDS` à 64 comme `MAX_SET`).
  4. Booléens : accepter `0/1/true/false/yes/no/on/off`, sinon `WARN` + désactivé.
  5. `clampd` : `if (!(v == v)) return lo;` (ou le défaut) pour éliminer les NaN d'un seul coup ; `observe_s` aussi.
  6. Ajouter au banc les cas du tableau ci-dessus **avec assertions** (aujourd'hui le banc passe 130/130 alors que ces cas ne sont pas couverts).
- **À confirmer sous Windows** : que `GetPrivateProfileStringA` renvoie bien `""` (et pas la valeur par défaut) pour `clé=` vide, et ne traite pas `;` en fin de ligne comme un commentaire. C'est le comportement documenté et connu, mais je ne l'ai
  pas vérifié sur Windows (mon banc l'imite). Une ligne `[modes]`/`eco_free_zone_m=` essayée avec un petit programme maison de 10 lignes sur le PC du moddeur le tranche (sans le jeu).

---

## 3. Constats importants

### I1. Garde-fou « HELD » : fail-open, crochet Lua conditionnel, aucun recoupement côté serveur

- **Où** : `lua/v2/library_custom_5.lua:53-57` (`cm_hold`), `:201-209` (`envelopper_update`, condition ligne 202), `:216-221` ; `plugin/cc2x_modes.c:247-253` (`is_held`), `:452-465` (`lua_hold`).
- **Constat** :
  1. Le crochet sur `update` n'est posé que si `type(g_viewing_vehicle_id) == "number"` **au moment où `begin_load` se termine** (ligne 202). **[EXÉCUTÉ]** (T5b, Lua 5.4 + faux jeu) : si cette variable vaut `nil` à cet instant puis devient un nombre,
    **`update` n'est jamais enveloppé, `hold()` n'est jamais appelé, et l'onglet n'affiche rien d'anormal**. Le script du jeu n'est pas dans le dépôt : je ne sais pas si la variable existe déjà à cet instant (**non vérifiable sans le jeu**). Le script du Mac (`fichiers/vitesse_boutons/library_custom_6.lua:50`) écrit
    `type(g_viewing_vehicle_id) == "number" and …`, ce qui laisse penser que la variable peut ne pas être un nombre sur certains écrans.
  2. La sémantique « `g_viewing_vehicle_id > 0` = je **pilote** cet avion » n'est pas prouvée. Le même test dans `library_custom_6.lua:50` sert à ne **pas** afficher une barre quand l'écran montre « la vue d'un véhicule », ce qui est compatible avec « je regarde la **caméra** de cet avion » (faux positif, sens sûr) mais ne prouve pas « je pilote ».
  3. Le plugin ne peut pas recouper : l'étude d'atterrissage a **mesuré** que `CONTROL_MODE` ne distingue pas le pilotage à la main (`JOURNAL_atterrissage.md:115`, avion 10 à la main avec `mode=0`). **Ne pas utiliser `CONTROL_MODE` comme détecteur** ; `control_speed` / `control_power` ne le reflètent pas non plus (`ETUDE.md` §8).
  4. Le chemin `modes.ini` (`eco_ids`, `flank_ids`, `eco_all`, `flank_all`) **contourne entièrement l'onglet** : si le script Lua v2 n'est pas chargé (onglet v1 posé, mod désactivé, script absent), aucun `hold` n'existe et le plugin écrit sur l'avion piloté.
- **Scénario** : le moddeur met `enabled=1`, ÉCO sur l'avion 10, puis prend l'avion 10 en main ; si la variable est `nil` à `begin_load`, le plugin plafonne **sa** manette (≤ 0,65) ; en FLANK il l'empêche de ralentir à l'appontage. Aucun journal ne le dit.
- **Correctif proposé** :
  - Lua : poser le crochet `update` **sans condition sur le type** (le test est déjà refait à chaque appel dans `cm_hold`, ligne 56) ; supprimer `or type(g_viewing_vehicle_id) ~= "number"` de la ligne 202.
  - Plugin : **battement de cœur**. Le même wrapper `update` appelle `cc2x.modes.hold(0)` (ou une fonction `alive()`) à chaque image ; le plugin n'écrit que si un battement date de moins de `HOLD_TICKS` (**fail-closed** : crochet absent ⇒ aucune écriture). Enregistrer dans le journal les indices d'écran qui battent.
  - Procédure : (b) doit montrer dans `cc2x.log` la ligne `id N: HELD` **et** le battement des 3 écrans avant tout `enabled=1` (déjà dit par la passation §5-6, à conserver comme condition ferme).

### I2. `mod_modes.py` : le « refus si le jeu tourne » ne voit pas l'ancien exe pour `installer` et `mettre-a-jour`

- **Où** : `outils/mod_mesures.py:64-69` (`jeu_ouvert` : `IMAGENAME eq carrier_command.exe`, nom **exact**), appelé en `:139` (mettre-à-jour) et `:166` (installer) ; `mod_modes.py:66-73` (`_jeu_ouvert`, `carrier_command*`) n'est utilisé que pour les commandes de plugin (`:99, :129, :158`) ; `charger_outil` (`mod_modes.py:176-181`) ne remplace pas la fonction du module chargé.
- **Preuve [EXÉCUTÉ]** (faux `tasklist` + faux `APPDATA`, racine « vraie ») : avec `carrier_command_ancien_8E7FCBB6.exe` « en cours », `installer --etape tout2` **écrit** (sauvegarde, dossier, ligne de `mods.xml`) et `mettre-a-jour --etape interface2` **ne refuse pas** ; avec `carrier_command.exe`, les deux refusent ; `retirer` refuse dans les deux cas (il passe d'abord par `plugin_retirer`, qui utilise la vérification large).
- **Scénario** : voie A (la seule qui charge le SDK depuis le 28/10) = le jeu tourne sous `carrier_command_ancien_8E7FCBB6.exe`. La commande (a) de la passation (`mettre-a-jour --etape interface2`) est précisément celle qui n'est **pas** protégée. La note (`PASSATION.md` §6 : « `mod_modes.py` refuse sinon ») est donc inexacte pour 2 commandes sur 3. Conséquence : réécriture de `library_custom_5.lua` / `mods.xml` sous un jeu ouvert (le jeu peut réécrire `mods.xml` à sa fermeture et perdre la ligne).
  Le `poser.py` du frein utilise déjà `carrier_command*` en connaissance de cause (`tour/atterrissage_manuel/frein/poser.py:71`).
- **Correctif** : dans `charger_outil`, après `exec_module(mm)`, ajouter `mm.jeu_ouvert = _jeu_ouvert` (les fonctions de `mod_mesures` cherchent `jeu_ouvert` dans leur module à l'appel). Ajouter un essai avec faux `tasklist` au dépôt.

### I3. `retirer` : dossier supprimé, `mods.xml` laissé avec la ligne, et message « rien à retirer »

- **Où** : `outils/mod_mesures.py:216-239` (`cmd_retirer`), ligne 222 `if txt.count(ligne) == 1` avec `ligne = '\t\t<path value="…"/>\n'` ; ligne 235-236 `if presents <= attendus: shutil.rmtree(…)`.
- **Preuve [EXÉCUTÉ]** : (a) `mods.xml` réécrit en **CRLF** après l'installation → `retirer` affiche « cc2_modes n'y figure pas (rien à retirer) » **puis** « Dossier supprimé » ; `mods.xml` garde la ligne `…\mods\cc2_modes`. (b) ligne **en double** → même résultat. (c) cas nominal LF : `mods.xml` revient **octet pour octet** à la sauvegarde (même sha256).
- **Scénario** : le jeu ou un éditeur Windows réécrit `mods.xml` avec des fins de ligne `\r\n` (l'installateur refuse déjà cette forme, `mod_mesures.py:179`, mais `retirer` ne la vérifie pas). Le moddeur lance `retirer` pour « tout défaire » : le mod disparaît, la ligne reste, la 4ᵉ entrée de `mods.xml` pointe vers un dossier absent. Comportement du jeu et du SDK (`GetFileAttributesW(plugins)` → `continue`, `cc2x.c`) face à un chemin absent : le SDK l'ignore ; le jeu : **inconnu**.
  Par ailleurs `retirer` ne vérifie que les **noms** de fichiers avant `rmtree` (`attendus` ligne 230) : une version modifiée à la main de `library_custom_5.lua` serait supprimée sans comparaison de contenu, contrairement à ce que dit l'en-tête (« retirer ne supprime que ce que l'installation a créé »).
- **Correctif** : normaliser les fins de ligne comme `active_dans` (`replace('\r\n','\n')`), compter avec une expression régulière tolérante (indentation, `/>`), et **refuser de supprimer le dossier** si la ligne n'a pas été retirée exactement une fois (ou si elle n'est pas trouvée alors que le dossier existe) ; réécrire `mods.xml` en conservant ses fins de ligne d'origine ; comparer le sha256 des scripts avant `rmtree`.

### I4. FLANK : la sortie de zone est un interrupteur, sans lien avec la vitesse de l'avion

- **Où** : `plugin/cc2x_modes.c:314-315` (zone libre = seul critère de distance), `:12-13` (en-tête).
- **Constat [LU, chiffres des notes]** : FLANK écrit un plancher de gaz jusqu'à 6 000 m du bateau, puis lâche d'un coup. Le Manta peut y arriver à ≈ 230-290 m/s (`ETUDE.md` §11-12) alors que l'IA vise 72-80 m/s pour le circuit. Le seul secours est la procédure (« rappeler à plus de 10 km »,
  `RISQUES_v2.md`). L'arrêt sur rappel (`dock=5` immédiat) est, lui, **mesuré ailleurs** (`JOURNAL_atterrissage.md:152`) ; mais un point de passage **à l'intérieur** des 6 km (patrouille proche) lâche FLANK à pleine vitesse.
- **Scénario** : ordre de patrouille à 4 km du bateau pendant que l'avion est à 250 m/s en FLANK : à 6 km le plugin cesse d'écrire ; la décélération dépend du régulateur de l'IA, dont **la vitesse de décélération n'a jamais été mesurée** (non vérifiable sans le jeu).
- **Correctif** : relâchement **progressif et lié à la vitesse** (réduire le plancher en fonction de `distance` et de la vitesse `body_get().vel`), ou zone libre élargie dynamiquement (`max(flank_free_m, v² / (2·a_décél_mesurée))`). À défaut, journaliser la vitesse à la sortie de zone (ligne `FLANK off`) pour la mesurer à l'essai (c).

### I5. ÉCO / FLANK n'ont aucune notion de situation (combat, relief, carburant)

- **Où** : `plugin/cc2x_modes.c:314-321` ; `RISQUES_pose.md:25-27` (« à 0,65 de gaz l'Albatros n'a presque pas de réserve de poussée »), `RISQUES_v2.md:29-31` (virages larges à grande vitesse).
- **Constat [LU / INFÉRÉ]** : ÉCO plafonne aussi en attaque (l'IA y demande 160 m/s, `ETUDE.md` §2) et en montée vers un point de passage plus haut ; FLANK ne tient pas compte du relief ni du carburant restant. Rien dans le plugin ne lit le carburant (`CC2X_VEHICLE_FUEL`, déjà lu pour le journal) pour se couper ni les points de passage
  (`CC2X_VEHICLE_WAYPOINTS` / `CC2X_WAYPOINT_TYPE`, qui ne distinguent que MOVE / DOCK / SUPPORT / DEPLOY / BARGE : l'API publique `cc2x.h` n'expose **ni** « en attaque » **ni** altitude visée). Le carburant par kilomètre étant meilleur à haute vitesse (`ETUDE.md` §10-11), c'est surtout ÉCO (+16 % au km) qui peut laisser un avion sans retour.
- **Scénario** : Albatros en ÉCO envoyé attaquer : plafond de gaz pendant l'engagement. Albatros en ÉCO avec carburant bas, loin : consommation au kilomètre plus élevée que NORMAL. Aucun de ces cas n'est observable ici.
- **Correctif** : coupure sous un seuil de carburant (`fuel < eco_fuel_min`, simple à tester ici) ; journaliser à chaque ligne d'observation le type du point courant, la vitesse et l'altitude pour que les essais montrent ce qui se passe réellement. Pour le **combat**, aucun signal fiable n'est disponible dans l'API publique : il faudrait relire le code du jeu (hors de portée ici) ; en attendant, le dire noir sur blanc dans `modes.ini.example` (« ne pas mettre en ÉCO un avion en mission d'attaque »).

### I6. `eco_all` / `flank_all` s'appliquent à toutes les équipes humaines, la doc dit « ton équipe »

- **Où** : `plugin/cc2x_modes.c:373` (filtre : `TEAM_IS_AI == 0`, pas l'équipe du joueur) ; `plugin/modes.ini.example:14` (« tous les avions de ton équipe ») ; `cc2x_modes.c:3` (« human team »).
- **Preuve [EXÉCUTÉ]** (S8) : deux équipes humaines chacune avec son porte-avions, `eco_all=1` → l'avion de l'**autre** équipe humaine est plafonné.
- **Scénario** : essai du scénario PvP (`tour/scenario_pvp`) ou coopération avec `eco_all=1` : les avions adverses humains, côté hôte, sont ralentis.
- **Correctif** : n'accepter que l'équipe qui possède les écrans (le plugin ne la connaît pas ; passer par une clé `team=` ou par la liste Lua uniquement), ou corriger la doc. À défaut, l'écrire en gras dans l'exemple.

---

## 4. Constats mineurs

- **M1. Cadence réelle ≠ 30 ticks/s.** `TICKS_PER_S 30.0` (`cc2x_modes.c:60`), `CFG_PERIOD 90`, `HOLD_TICKS 90` (« 3 s », lignes 61-62 et en-tête). **[EXÉCUTÉ]** sur `mesures/2026-10-28_partie2_plugin_modes.log` : les `t=` du plugin (ticks/30) avancent à **2,083 × l'heure du journal** (médiane sur 3 avions) ;
  pendant l'essai ÉCO il y a **96 écritures par intervalle de 150 rappels** (64 %), soit ≈ 40 écritures/s réelles (1 901 écritures en 47,5 s). Cohérent avec l'ancien exe « temps_x2 » (`PASSATION_coordination_29-10.md:30`) et un moteur qui ne fait pas un tick de contrôle par rappel : **[INFÉRÉ]**, non confirmé.
  Conséquence : « `enabled=0` pris en compte en 3 s » = **3 s de jeu**, ≈ 1,4 s réelles dans cette session ; la durée du garde-fou HELD (90 rappels) vaut ≈ 1,4 s réelles : suffisant si l'écran appelle `hold` à chaque image, **à re-vérifier si l'écran est ralenti**. Les « minutes d'autonomie » de l'onglet sont des minutes **de jeu** (ticks/30), pas des minutes réelles.
  Correctif : documenter l'unité, et/ou mesurer le temps réel (`GetTickCount64`) pour la relecture de l'ini.
- **M2. Relecture de l'ini non atomique et bloquante.** `cc2x_modes.c:180-197` : ≈ 15 appels `GetPrivateProfileStringA` (chacun ouvre et analyse le fichier ; compté dans le code) toutes les 90 ticks, **dans le thread logique du jeu**. Un enregistrement en cours d'écriture peut donner une valeur tronquée (`eco_free_zone_m=15` lu pour `1500`). Correctif : lire le fichier d'un coup dans un tampon, valider l'ensemble, n'adopter la config que si elle est complète.
- **M3. Journal : plafond de 4 000 lignes et rebonds.** `cc2x_modes.c:70, 164-173`. **[EXÉCUTÉ]** (S10) : 5 avions en vol avec `observe_s=5` atteignent `LOG_CAP` après **120 150 rappels** (32 min à 62,5/s, 67 min à 30/s) ; ensuite **la ligne `HELD` (niveau INFO) n'est plus écrite**, or c'est la preuve demandée par la passation (§5). **[EXÉCUTÉ]** (S7) : un avion qui reste à ±2 m de la limite de zone produit **1 ligne de journal par tick** (299 « off after » en 600 ticks) : sans hystérésis, ce cas (extrême : bascule à chaque tick) atteint le plafond en 1 à 2 minutes. Correctif : exempter `HELD` / transitions du plafond (ou niveau WARN), ajouter une hystérésis (par exemple 5 %) aux zones.
- **M4. Table Lua de 64 entrées jamais purgée.** `cc2x_modes.c:65, 414-433` ; **[EXÉCUTÉ]** (S9) : 64 clics NORMAL (même sans effet) la remplissent ; le 65ᵉ avion est refusé jusqu'à la fin de la session, et l'onglet ne dit rien (T7) : le bouton revient à NORMAL au cadre suivant. Correctif : purger les ids qui n'existent plus, ne pas stocker `NORMAL` quand l'ini ne dit pas le contraire, afficher « table pleine ».
- **M5. Avion le plus proche par distance de Manhattan, zone libre en distance euclidienne.** `cc2x_modes.c:377-380` vs `:301-303`. Avec deux porte-avions de la même équipe, le « plus proche » peut ne pas être le plus proche ; effet faible. Correctif : utiliser le carré de la distance euclidienne.
- **M6. `getf` renvoie `0.0` en cas d'échec.** `passation_windows/sdk_public_cc2x/src/world.c:294` : une position illisible (corps absent) donne `(0, 0)`, donc une distance quelconque au porte-avions, au lieu de « inconnue ». Le plugin ne le détecte pas (`cc2x_modes.c:301-303`). Peu probable pour un avion en vol ; **[LU]**. Correctif : vérifier `A->body_get()` avant de calculer la distance, sinon traiter comme « zone libre ».
- **M7. `THR_OFFSET` et `THR_BYTES` sont deux constantes séparées** (`cc2x_modes.c:63, 78`) ; le contrôle des 8 octets valide bien le déplacement `0x314` (octets `14 03 00 00`), mais rien n'empêche de modifier l'un sans l'autre. Correctif : `_Static_assert` ou génération de `THR_BYTES` à partir de `THR_OFFSET`.
- **M8. Pas de `DeleteCriticalSection` ni de désenregistrement** (`cc2x_modes.c:512`) : sans conséquence tant que la DLL n'est jamais déchargée avant la fin du processus. Scénario : le futur chargeur maison (chantier en cours ailleurs) décharge les plugins → rappels vers du code déchargé. Correctif : exporter une fonction `cc2x_plugin_unload` si le futur chargeur la prévoit, sinon documenter « ne jamais décharger ».
- **M9. Journal « loaded … Lua cc2x.modes.* » même si le pont Lua est inactif** (`:518-526, 525`). Le pont est enregistré seulement si `lua_add`/`lua_feature` existent, mais le message est inconditionnel ; avec un SDK sans pont Lua (`g_lua_ok` faux, cf. `cc2x.c`), l'onglet affichera « MAQUETTE » sans que le journal du plugin explique pourquoi. Correctif : n'écrire « Lua cc2x.modes.* » que si `lua_add` a réussi (valeur de retour), sinon un `WARN` « pont Lua indisponible ».
- **M10. `mettre-a-jour` réécrit aussi `mod.xml`.** `mod_mesures.py:136-161` + `mod_modes.py:44-52` : le `mod.xml` posé (sha `396765E7…`, `PASSATION.md` §3) diffère du texte courant de `MOD_XML` (sha `BEDD15C1…`, calculé), donc la commande (a) modifie un 3ᵉ fichier non annoncé (« fichiers seulement »). Effet faible (description du mod). Par ailleurs cette description ne dit pas que le mod embarque une **DLL native** ; c'est utile au moddeur pour sa règle sur les risques.
- **M11. Chemins absolus d'une machine** : `mod_modes.py:55` (`PLUGIN_SRC`), `construire_modes.py:20` (`TRAVAIL`). Outil inutilisable ailleurs ; aucun mécanisme dans le dépôt ne lie le source `cc2x_modes.c` au sha `331581C6…` (la reproductibilité de la compilation est vérifiée par `construire_modes.py` sur le PC du moddeur, pas ici). L'en-tête `cc2x.h` utilisé pour la compilation réelle (`7ab05c7`) n'est pas dans le dépôt, seulement son sha (`tour/atterrissage_manuel/SDK_empreintes_7ab05c7.txt`).
- **M12. Onglet v2 : l'autonomie affichée est celle du mode *demandé***, même en « OBSERVATION : SANS EFFET », « EN ATTENTE » ou « PILOTE : EN PAUSE » (`lua/v2/library_custom_5.lua:155-159`) ; **[EXÉCUTÉ]** (T2) : ÉCO demandé, plugin en observation → « AUTONOMIE ~61 min » alors que rien n'est appliqué. Le texte au-dessus dit « SANS EFFET » mais le chiffre est trompeur. Les débits viennent des mesures de peu d'avions peu chargés (`DEBIT` lignes 41-44).

---

## 5. Ce qui m'a paru solide

(Sous réserve de §1 : jamais exécuté dans le jeu.)

- **Reconnaissance du build** : horodatage PE **et** 8 octets de code à l'adresse du build reconnu, refus sinon (`cc2x_modes.c:78-85, 485-511`). Les 8 octets contiennent le déplacement `0x314` : le contrôle valide donc aussi le décalage écrit. Le banc couvre les 4 croisements (ancien/nouveau horodatage × ancienne/nouvelle adresse), l'absence d'en-tête MZ, `module_base` nul, API < 3.
  J'ai vérifié l'encodage : `F3 0F 11 87 14 03 00 00` = `movss [edi+0x314], xmm0`.
- **Aucun accès hors tampon trouvé** : `read_ids` (`n < MAX_IDS`, avance garantie), `ini_num` (tampon 32 + `GetPrivateProfileStringA` borné), `list_text` (borné), `drain_events` (`g_nev ≤ MAX_EV`), `track_of`, `snprintf`/`vsnprintf` partout, journal par `"%s"` (pas de chaîne de format fournie par l'extérieur). 130 contrôles sous ASan/UBSan, 0 avertissement `-Wall -Wextra`, `clang --analyze` muet.
- **Concurrence** : l'état partagé (tableau Lua, avions tenus, états publiés, config publiée) est entièrement sous `g_lock` ; aucun appel au jeu ou au journal verrou pris (**[EXÉCUTÉ]** : verrou instrumenté, profondeur maximale 1, profondeur finale 0, `log`/pushs Lua jamais appelés verrou pris) ; `on_tick` et `on_session` sont sur le même thread serveur (**[LU]** dans `cc2x.c`, `tick_once`/`session_change`).
- **Écriture minimale et réversible** : une seule écriture, jamais sur `NaN`, négatif ou > 1,0001, seulement pour réduire (ÉCO) ou relever (FLANK) ; rien n'est écrit tant que `enabled` ≠ 0 (le chemin « pas de fichier » → observation seule est testé) ; coupure par `enabled=0` ou par `set(id, 0)`, effective au prochain rappel, sans état résiduel côté plugin.
- **Exclusions** : équipes IA, hélicoptères, avions non en vol, rattachés, en file/atterrissage (`dock != 0`), sans porte-avions de leur équipe, zone libre. Le rappel met `dock=5` immédiatement (**[MESURÉ ailleurs]**, `JOURNAL_atterrissage.md:152`) et le plugin n'écrit pas quand `dock ≠ 0` (**[EXÉCUTÉ]** par le banc, `test_modes.c:325-326`).
- **Chiffres** : le journal du 28/10 recoupe les notes sur la loi carburant (**[EXÉCUTÉ]** régression : Albatros 0,298 et médiane 0,304, Manta 0,764 et médiane 0,760 par unité de gaz), sur le plafond appliqué ≈ 0,72 pour 0,65 écrit (`mx=0,719`) et sur la vitesse ≈ 80 m/s au plafond.
- **Onglet Lua** : syntaxe OK ; 29 contrôles sur 30 (le 30ᵉ est la démonstration voulue de I1) : correspondance des boutons ECO→1, NORMAL→0, FLANK→2 correcte ; états ACTIF / EN ATTENTE / PILOTE : EN PAUSE / OBSERVATION / MAQUETTE ; valeurs de retour du jeu conservées par l'enveloppe ; piles de l'interface remises en ordre et onglet coupé après une erreur de dessin ;
  `pcall` autour de tout appel au plugin (un `get` ou un `status` qui plantent ne cassent pas le cadre) ; double chargement sans double enveloppe ; absence de `hold` sans erreur ; autonomies conformes à la formule (61 / 47 / 44 min pour l'Albatros plein, 56 / 26 pour le Manta).
- **Installateur** : refuse si `tasklist` échoue (fail-closed) ; sauvegarde datée ne l'écrasant jamais ; écriture atomique de `mods.xml` ; ne remplace que des versions connues de la DLL (sha256) ; `installer` puis `retirer` rend **le même `mods.xml` octet pour octet** dans le cas nominal (**[EXÉCUTÉ]**) ; commandes de plugin protégées par la vérification large `carrier_command*`.
- **Empreintes** : `lua/*` correspondent aux sha256 de `mod_modes.py` (3 sur 3) ; `.gitattributes` force LF pour `*.lua` (un checkout Windows ne casse donc pas les sha).

---

## 6. Contradictions entre notes et code / entre notes

| # | Où | Contradiction |
|---|---|---|
| 1 | `ETUDE.md:460` | plugin v3 « sha256 `49AFE401…7A36`, **124** contrôles » ; `RISQUES_v3.md:12,19`, `RAPPORT_compilation.md:5`, `mod_modes.py:56` : `331581C6…`, **130** contrôles |
| 2 | `ETUDE.md:492` | « le plugin n'aurait plus qu'à changer `THR_SITE` (`0x71dcbf`) et accepter la chaîne de build du SDK » alors que, 3 lignes plus haut (`:489`), « côté plugin, déjà fait » ; `THR_SITE` n'existe plus dans le code et le plugin ne lit pas `game_build` |
| 3 | `PASSATION.md` §7 | « Non commité (à moi) : … » ; ces fichiers sont dans `57723e1` (`git log`) |
| 4 | `PASSATION.md` §3 | `mod.xml` posé = `396765E7…` ; le texte courant de `MOD_XML` donne `BEDD15C1…` (la commande (a) le réécrit) |
| 5 | `PASSATION.md` §6 | « `mod_modes.py` refuse sinon (jeu ouvert) » : faux pour `installer` et `mettre-a-jour` (§I2) |
| 6 | `RISQUES_v2.md:32` | « un avion piloté à la main n'est pas détecté » (limite 4) ; `RISQUES_v3.md:13` dit que cette limite est « levée, si le jeu fait bien ce qu'on lit » : formulation à unifier (elle n'est pas levée tant que HELD n'a pas été vu) |
| 7 | `RISQUES_pose.md:7-9, 15, 57-58` | « 216 Ko », « 38 contrôles », « n'a pas encore FLANK ni le lien avec l'onglet » : périmé (v3) ; le fichier est toujours listé comme document à lire d'abord |
| 8 | `modes.ini.example:14` / `cc2x_modes.c:3` | « ton équipe » / « human team » ; le code vise toutes les équipes non-IA (§I6) |
| 9 | `cc2x_modes.c:62` et en-tête, `modes.ini.example:2`, `PASSATION.md` §6 | « 3 s » : 3 s **de jeu** (90 rappels), ≈ 1,4 s réelles dans la session mesurée (§M1) |

---

## 7. Non vérifiable sans le jeu

À ne **pas** considérer comme acquis, même si les tests passent :

1. **`g_viewing_vehicle_id > 0` = « je pilote cet avion »**, et le moment où cette variable devient un nombre (§I1). Aucune lecture du script `screen_vehicle_control.lua` n'est possible ici (absent du dépôt).
2. **Que `hold()` soit appelé depuis l'écran qui porte le pilotage**, et que les 3 écrans le fassent.
3. **L'affichage de l'onglet v2** (placement, coupure du texte, clics, barre de défilement), le comportement sous **Lua 5.3** réel (j'ai exécuté du 5.4).
4. **Que `GetPrivateProfileStringA` se comporte comme mon imitation** (§B1) et que `CRITICAL_SECTION`, l'arithmétique 32 bits et le chargement de la DLL se passent bien : la DLL mingw n'a pas été chargée, l'exe de test Windows n'a pas été lancé.
5. **Que le `cc2x.h` de compilation réelle (`7ab05c7`) ait la même disposition que la copie du dépôt** pour les champs utilisés, et que la DLL `331581C6…` soit bien issue de ce source.
6. **Le comportement de l'IA** sous plafond ou plancher de gaz hors des cas mesurés : FLANK, ÉCO du Manta, avion chargé (plafond de demande moteur 0,8 / 0,75), vols près du relief, combat (§I4, §I5).
7. **Le nouveau build du jeu** (`0x6ae228f3`) : le plugin sait le reconnaître et contrôle le code, mais le SDK reste inactif dessus, donc rien n'a pu être observé ; les décalages « inchangés » viennent du désassemblage des notes, pas d'un essai.
8. **La cause de la cadence 62,5 / 40 par seconde** (§M1) : `temps_x2`, moteur à pas fixe, ou autre.
9. **Le comportement du jeu** devant un chemin de mod absent dans `mods.xml` (§I3) et sa réécriture éventuelle de `mods.xml` à la fermeture.
10. **L'effet réel des mesures de carburant sur la partie suivante** (réservoir 800 / 1200 selon équipement, `DEBIT` du Manta en ÉCO inconnu).

---

## 8. Ordre de correction que je propose

1. B1 (lecture stricte de l'ini + planchers de zone + cas du banc) : petit, local, testable ici.
2. I1 : retirer la condition ligne 202 du Lua ; battement de cœur côté plugin ; garder la condition « HELD vu en jeu » avant (c).
3. I2 (une ligne) puis I3 (normalisation et refus de `rmtree`) : testables ici avec un faux `tasklist` et une fausse racine (j'en ai les scénarios).
4. M3 (HELD hors plafond du journal) avant l'essai (b), car c'est la preuve attendue.
5. Le reste selon l'envie du moddeur ; I4 et I5 demandent des mesures en jeu avant de choisir une solution.

## Annexe — reproduction (rien de tout cela n'est dans le dépôt)

- Fausse `windows.h` : `CRITICAL_SECTION` à compteur de profondeur ; `GetPrivateProfileStringA` : section et clé insensibles à la casse, lignes `;` seulement en début de ligne, valeur vide renvoyée telle quelle, blancs rognés, guillemets retirés, troncature à `size-1`.
- Banc natif : `gcc -std=gnu11 -Wall -Wextra -fsanitize=address,undefined,float-cast-overflow -I shim tests/test_modes.c` ; scénarios S1–S10 ajoutés dans un `main` qui appelle l'ancien `main` renommé.
- DLL 32 bits : `i686-w64-mingw32-gcc -std=c11 -O2 -fno-strict-aliasing -Wall -Wextra -Wno-unused-parameter -Werror=implicit-function-declaration -shared -I passation_windows/sdk_public_cc2x tour/etudes_modes_carburant/plugin/cc2x_modes.c`.
- Lua : `ctypes` sur `liblua5.4.so.0` (`luaL_newstate`, `luaL_loadstring`, `lua_pcallk`), faux jeu en Lua (fenêtres, piles, boutons, `cc2x.modes`), 30 contrôles.
- `mod_modes.py` : `APPDATA` pointant sur un dossier jetable, `tasklist` factice placé en tête du `PATH` (variable `FAKE_RUNNING`), `mods.xml` d'exemple tiré de `tour/etude_mise_a_jour/apres/mods.xml`.

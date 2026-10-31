# P0 — Inventaire et plan : remplacer le SDK de DYOR par un chargeur et une mini-API à nous

Date : 28/10/2026. **Phase P0 = lecture seule.** Branche `[branche]` (découpée de `main` au commit `80f2a8a`). Rien n'a été lancé, fermé, posé ni modifié côté jeu. Étiquettes : **LU** (lu dans un fichier), **MESURÉ** (vu en jeu, d'après les journaux), **INFÉRÉ** (déduit, à vérifier).

## 1. En dix lignes

1. **C'est faisable, et plus petit qu'on pourrait croire pour la partie C.** À elles deux, nos DLL n'utilisent que **12 des 59 fonctions** de l'interface C du SDK et **30 faits sur le jeu** (adresses, décalages) à revérifier (LU, section 4 et `P0_decalages_a_reverifier.md`).
2. **Le morceau difficile n'est ni le chargeur ni les plugins : c'est la table Lua `cc2x`.** La refaire demande **23 faits de plus**, dont 16 sur les entrailles du Lua du jeu, et ne peut pas être prouvée hors du jeu (pas de Lua 5.3 du jeu sur la tour). C'est la décision (d), à prendre avec toi (section 5).
3. **Nos scripts Lua n'appellent que 6 membres de `cc2x`** : `api`, `version`, `log`, `tick`, `vehicles`, `tiles` (14 champs de véhicule, 5 champs d'île). Les 22 autres fonctions de monde du SDK (dont toutes les commandes : freins, position, files d'aérodrome…), `has` et `game_build` sont inutilisées (LU) : la table Lua du SDK compte 30 membres, nous en utilisons 6.
4. **Correction du brief : `cc2_mesures` n'appelle rien du SDK** (recherche sans résultat dans ses 4 scripts). Les appels viennent de `cc2_carte` (script 6) et `cc2_modes` (scripts 3 et 5).
5. **Deux défauts du SDK qu'on ne recopie pas** : (a) `DllMain` charge les plugins avec `LoadLibrary` (`cc2x.c:895-911` → `startup` → `load_plugins` → `cc2x.c:707`) ; (b) son relais en milieu de fonction ne sauve que les registres généraux (`cc2x.c:243-257` : `pushfd ; pushad ; … ; popad ; popfd`), ni `xmm`, ni alignement de pile, ni indicateur de direction. Dans notre configuration (aucun plugin n'abonne d'événement à crochet), il n'est utilisé qu'à **un** endroit au démarrage (le site de 8 octets `0x004465ec`) ; les 3 cases de table sont de simples appels de fonction.
6. **Le chargeur peut démarrer plus tard que `DllMain`** : au premier `DirectInput8Create` du jeu (hors du verrou du chargeur Windows). C'est **INFÉRÉ** : à vérifier en P2 (ordre des appels) puis en jeu en P5.
7. **Notre propre code de tremplin existe déjà et est testé** (`extension_windows/src/cp_hook.c`, sauve `xmm0`-`xmm7`, 138 contrôles exécutés en 32 bits sous Linux) : on le réutilise pour le site Lua.
8. **Le retour arrière sera simple** : si on laisse en place `cc2x_frein.dll` et `cc2x_modes.dll` (inertes sous notre chargeur, qui ne scanne rien), remettre le SDK = **remplacer un seul fichier** (`dinput8.dll`).
9. **Volume estimé (INFÉRÉ)** : ~1 000 lignes de C (chargeur, SHA-256, mini-API, journal) + ~400 lignes pour le pont Lua si option A ; tests hôte ≥ **203** contrôles (≥ 105 + 38 repris un à un + ≥ 60 pour la couche d'API). Détail section 8.
10. **Rien n'est bloquant pour démarrer P1** (le chargeur seul) : la décision (d) n'influence que P3.

## 2. État réel constaté (28/10, lecture seule, jeu fermé)

| Élément | Constat | Étiquette |
|---|---|---|
| Jeu | aucun processus `carrier_command*` ; seul Steam tourne | MESURÉ |
| `carrier_command.exe` | sha256 `8E7FCBB6CE27BD3D8FEB02BF7F3DBBA646CCE6D4944360570F082972E8DFE8BE`, 11 353 600 o (inchangé) | MESURÉ |
| `dinput8.dll` du jeu (SDK 0.5.0) | `184B144D…0982`, 267 264 o | MESURÉ |
| `cc2x_frein.dll` du jeu (v5) | `4B70F031…526F29`, 219 648 o | MESURÉ |
| `cc2x_modes.dll` (dans le mod `cc2_modes\content\cc2x\`, **pas** dans le dossier du jeu) | `AB2D5343…46E4`, 216 576 o (v1) | MESURÉ |
| Mods actifs (`mods.xml`) | Workshop `2937532682` (missiles, pas de dossier `cc2x`), `cc2_mesures`, `cc2_carte`, `cc2_modes` | MESURÉ |
| DLL ou dossier `cc2x` dans les mods locaux et le mod Workshop actif | **un seul** : `cc2_modes\content\cc2x\cc2x_modes.dll` | MESURÉ |
| Autres exécutables dans le dossier du jeu | `carrier_command_test_cercle.exe` et `carrier_command_test_cercle_creneau.exe` (copies d'essai de l'autre chantier, même taille que le vrai), `carrier_command_vr.exe`, `dedicated_server.exe` | MESURÉ |
| `dinput8.dll` du système (32 bits) | `C:\Windows\SysWOW64\dinput8.dll`, 176 640 o | MESURÉ |
| Outils présents | Python 3.12.10, capstone 5.0.7, Zig 0.15.2 (rien à installer) | MESURÉ |
| Identité git de la branche | `[pseudo retire]`, adresse `…@users.noreply.github.com` | MESURÉ |

**Le périmètre bouge pendant que je lis** (à intégrer, pas à ignorer) : (1) le dépôt principal a avancé d'un commit (`596d2b3`, journal seulement) ; (2) l'autre conversation a **un plugin modes v2 non commité** (ÉCO par type + FLANK en plancher de gaz, 72 contrôles, sha `8B3A5A87…`, d'après sa note) : j'ai regardé (lecture seule) ses appels au SDK, **ce sont les mêmes** que la v1 (aucune fonction nouvelle, les mêmes champs) ; (3) le frein a connu un essai v5 le 28/10 qui annonce peut-être une **v6** (« ne rendre la poussée qu'à un signal explicite »). Conséquence : la mini-API doit rester **de la même forme** que l'API actuelle pour que ces versions se portent sans réécriture (section 7).

## 3. Ce que fait le SDK aujourd'hui, et ce qu'on reprend

| Fonction du SDK | Où | On reprend ? |
|---|---|---|
| Proxy `dinput8.dll` : 5 exports, vrai `dinput8.dll` par le dossier système | `cc2x.c:81-124` | **Oui**, à l'identique (chargement à la demande). Noms de sortie **non décorés** (voir section 7) |
| Détection de version (horodatage PE + taille) | `cc2x.c:824-834` | **Oui** (fait H1) |
| Remplacement de 3 cases de table (init / pas / fin) | `cc2x.c:262-278, 391-439, 851-853` | **Oui** (H2-H5) |
| Rappels `on_server_tick` / `on_session` | `cc2x.c:349-357, 385-439` | **Oui** |
| Journal `cc2x.log` (supprimé à chaque lancement, une ligne = heure + auteur + niveau + texte) | `cc2x.c:55-77, 908` | **Oui**, même fichier et même format de ligne : aucun outil des autres conversations à changer (`trajets_circuit.py`, copies de journal) |
| Dossier de réglages `%APPDATA%\Carrier Command 2\cc2x` | `cc2x.c:877-883` | **Oui**, même chemin : `frein.ini` et `modes.ini` continuent de marcher |
| Chargeur de plugins par balayage (`mods.xml`, `content\cc2x\*.dll`, `cc2x_*.dll`, `cc2x\plugins\*.dll`) | `cc2x.c:696-820` | **Non** : liste fixe + sha256 |
| Moteur de patchs `patch_call/mid/ptr/commit`, mémoire exécutable de 64 Ko | `cc2x.c:126-337` | **Non** pour les plugins ; version minuscule pour nos 4 sites seulement |
| `server_post`, `time_scale`, lecture de `cc2x.ini` | `cc2x.c:359-376, 401, 884-889` | **Non** (aucun usage) |
| Monde : lecture des champs, `find`, `body_get`, `vehicle_brakes` | `world.c` | **Oui**, la partie utilisée (section 4) |
| Monde : `body_set`, rayon, `vehicle_gear`, `request_landing`, `waypoints_sync`, 5 événements à crochet, aérodromes | `world.c:373-648` | **Non** (aucun usage ; moins de code et moins de surface) |
| Instantané de tout le monde à **chaque** tick (véhicules, îles, aérodromes) | `lua_world.c:141-176, 433-453` | **Non** en l'état. Option A : seulement 14 + 5 champs, sur demande plutôt qu'à chaque tick (INFÉRÉ : charge nettement plus faible que le SDK) |
| Pont Lua (table `cc2x`, 25 fonctions de monde, `has`, `log`) | `cc2x.c:443-678`, `lua_world.c:466-861` | **Option A seulement**, et **en lecture seule** : 6 membres au lieu de 30. Un mod ne pourrait plus tricher dans la partie par cette voie (le SDK permet 25 commandes) |

## 4. Inventaire exact — nos deux plugins C

### 4.1 Fonctions et champs du SDK utilisés (relevé par recherche sur le code source)

| Élément du SDK | `cc2x_frein.c` | `cc2x_modes.c` |
|---|---|---|
| `api_version`, `size`, `game_build`, `config_dir` | oui | oui |
| `log` | oui | oui |
| `count` (liste des véhicules ; roues ; points de passage) | oui (3 usages) | oui (1 usage : liste) |
| `ref` (élément i de la liste) | oui | oui |
| `find` (véhicule par identifiant) | **oui** | non |
| `geti` / `getf` | oui (11 / 6) | oui (11 / 7) |
| `setf` | **oui** (`CONTROL_POWER`, `hold_idle`) | non |
| `body_get` | oui (position + vitesse) | oui (vitesse, journaux) |
| `vehicle_brakes` | **oui** | non |
| `va` | non | **oui** (contrôle des 8 octets) |
| `on_server_tick`, `on_session` | oui | oui |
| Écriture directe dans le véhicule | non | **oui** : `*(float*)(véhicule+0x314)` |

**Union : 12 fonctions** (`log`, `count`, `ref`, `find`, `geti`, `getf`, `setf`, `body_get`, `vehicle_brakes`, `va`, `on_server_tick`, `on_session`) sur 59 fonctions de `cc2x_api`. Les plugins n'appellent aucune fonction Windows autre que `GetPrivateProfileStringA` (lecture de leur `.ini`) et la bibliothèque C.

Champs lus ou écrits : `WORLD_VEHICLES`, `VEHICLE_ID`, `DEFINITION`, `TEAM`, `TEAM_IS_AI`, `IS_WING`, `ATTACHED_TO`, `DOCK_STATE`, `FLIGHT_STATE`, `CONTROL_MODE`, `CONTROL_TAXI`, `CONTROL_POWER` (**lu et écrit**), `POS`, `WHEELS`, `WHEEL_CONTACT`, `WAYPOINTS` (nombre), `FUEL`. Écritures dans le jeu au total : **frein** (fonction virtuelle), **puissance moteur** (`+0x1fc`), **gaz** (`+0x314`). Tout le reste est de la lecture.

### 4.2 Hors périmètre, mais à savoir
- `extension_windows/` (`cc2x_cc2_patchs.dll`) : squelette **non installé** ; il appelle en plus `lua_feature`, `lua_add` et `module_base` et utilise son propre moteur de patchs (`cp_patch.c`). On ne le porte pas dans ce chantier, mais sa charpente (`cp_hook`, `cp_patch`, `cp_pe`) est réutilisable.
- Plugins futurs annoncés dans les notes (vitesse / FLANK, circuit) : à ce jour ils ne demandent **aucune** fonction nouvelle (modes v2 le confirme). Si un crochet de code est demandé plus tard, on ajoutera la brique « patch » au moment voulu, avec son propre accord.

## 5. Inventaire exact — scripts Lua et décision (d)

### 5.1 Ce que chaque script appelle (relevé par lecture des 3 fichiers installés, `%APPDATA%\Carrier Command 2\mods\…`)

| Script | Mod | Appels à `cc2x` | Champs lus |
|---|---|---|---|
| `library_custom_6.lua` (enregistreur de carte `CC2MAP`, `CC2DIAG`) | `cc2_carte` | `cc2x.api` (test `>= 4`), `cc2x.version`, `cc2x.tick()`, `cc2x.log(...)`, `cc2x.vehicles()`, `cc2x.tiles()` | véhicule : `id`, `definition`, `team`, `x`, `z`, `yaw`, `team_is_ai` ; île : `id`, `team`, `x`, `z`, `island` |
| `library_custom_3.lua` (télémétrie `CC2MODES`) | `cc2_modes` | `cc2x.api`, `cc2x.version`, `cc2x.tick()`, `cc2x.log(...)`, `cc2x.vehicles(équipe)` et `cc2x.vehicles()` | véhicule : `id`, `definition`, `is_wing`, `flight_state`, `x`, `y`, `z`, `speed`, `fuel`, `control_speed`, `control_power` |
| `library_custom_5.lua` (onglet SPEED, maquette) | `cc2_modes` | seulement `cc2x.log` **dans le chemin d'erreur**, protégé par `type(cc2x) == "table"` et `pcall` | aucun |
| `library_custom_1/4/7/9.lua` | `cc2_mesures` | **aucun** | — |

Donc : **6 membres** (`api`, `version`, `log`, `tick`, `vehicles`, `tiles`), **14 champs de véhicule**, **5 champs d'île**. Sans `cc2x`, les scripts 6 et 3 s'arrêtent d'eux-mêmes (`cc2x_ok()` faux : `library_custom_6.lua:188`, `library_custom_3.lua:100`) et le 5 marche (LU). Le journal reçoit les lignes `CC2MAP|…`, `CC2DIAG|…` et `CC2MODES|…` **via `cc2x.log`** : Lua n'a aucun autre moyen d'écrire (aucun `io`/`os`, dit par les scripts eux-mêmes). Des outils lisent ces lignes (`tour/etudes_circuit_atterrissage/trajets_circuit.py`, copies de journal des autres conversations). **Les données de `vehicles()` et `tiles()` (équipes ennemies dans le brouillard comprises) ne sont accessibles que par `cc2x`** ; les missiles (`CC2MAP|M`) et les colonnes `jeu_*` de `CC2MODES` viennent de l'API Lua du jeu, qui n'a besoin de `cc2x` que pour **écrire** dans le journal.

### 5.2 Les options

| | A — Équivalent minimal | B — Changer le canal (enregistrer depuis le C) | C — Plus de télémétrie Lua |
|---|---|---|---|
| Principe | on refait `cc2x.api/version/log/tick/vehicles/tiles`, en **lecture seule** | un petit plugin C écrit lui-même les lignes `CC2MAP\|V`, `CC2MAP\|T`, `CC2MODES\|A` au même format ; plus de table `cc2x` | on ne fournit rien ; `cc2_carte` et `cc2_modes` se taisent |
| Scripts Lua changés | aucun | aucun, mais `cc2_carte` et la mesure de `cc2_modes` deviennent inutiles (à retirer de `mods.xml`, avec ton accord) | aucun |
| Journaux gardés | **tous**, identiques | véhicules, îles, gaz, carburant : oui ; **missiles (`CC2MAP\|M`) et colonnes `jeu_*` : perdus** (pas de moyen de les écrire sans pont Lua) | aucun |
| Faits de plus à vérifier | +23 (dont 16 sur le Lua du jeu) | +2 (V17, B5) | 0 |
| Code de plus | ~400 lignes | ~300 lignes | 0 |
| Preuve possible hors du jeu | partielle : on teste la logique avec un faux Lua, **pas** les structures internes du vrai | complète | complète |
| Risque (🟢/🟡/🔴) | 🟡 : seul endroit où notre code écrit dans l'état Lua du jeu (le SDK le fait déjà aujourd'hui sans incident, MESURÉ ; ici ce serait notre code relu) | 🟢 | 🟢 |
| Ce que tu perds | rien | missiles dans le timelapse, certaines colonnes de télémétrie | timelapse et télémétrie |

**Recommandation (INFÉRÉ)** : viser **A, construit en dernier et séparé** du reste. On fait d'abord P1-P4 pour les deux plugins C (aucun Lua) ; la vérification P2 des 16 faits sur le Lua tranche ensuite : si l'un d'eux est « DIFFÉRENT » ou « NON TRANCHÉ », **repli automatique sur B** (sans nouvelle discussion). A a un avantage de sécurité net sur le SDK : une interface Lua **sans aucune commande** (le SDK en offre 25).

## 6. Les décalages à revérifier

Détail complet (identifiant, valeur, source `fichier:ligne`, ce qu'il faut voir, ce qui en dépend, vu en jeu ou non) : **`P0_decalages_a_reverifier.md`**.

| Groupe | Faits | Pour |
|---|---|---|
| H — accroches (version, 3 cases de table, convention d'appel, `xmm`) | 7 | plugins C |
| S — liste des véhicules | 1 | plugins C |
| V — objet véhicule (16 pour les plugins C + 1 pour Lua) | 17 | plugins C : 16 |
| B — corps physique PhysX (4 + 1 pour Lua) | 5 | plugins C : 4 |
| M — gaz du plugin modes | 2 | plugins C |
| **Total plugins C** | **30** | |
| G — valeurs de jeu (types, états) | 4 | plugins C |
| L + LI — îles et entrailles Lua | 21 | option A seulement |

Presque tous sont déjà **MESURÉS en jeu** par nos plugins (ils lisent les bons avions) ; ce qui manque, c'est la preuve **par le code du jeu**. Deux faits portent un risque d'**écriture** : V16 (le frein) et M1 (le gaz). Ils passent en tête de la vérification.

## 7. Conception proposée (à valider phase par phase)

Choix déjà faits, mais **modifiables sur ta demande** :

1. **Nom des exports** : les 5 noms **non décorés** (`DirectInput8Create`, `DllCanUnloadNow`, `DllGetClassObject`, `DllRegisterServer`, `DllUnregisterServer`), obtenus comme le SDK par un fichier `.def` (en 32 bits le compilateur décore `DirectInput8Create@20`, etc. ; c'est le piège cité dans le brief). **Contrôlé en P1** par la lecture de la table d'exports de la DLL fabriquée (le script `construire.py` actuel le fait déjà pour le SDK).
2. **`DllMain` ne fait presque rien** (mémoriser le module, rien d'autre : ni `LoadLibrary`, ni fichier). Le vrai `dinput8.dll` **et** nos plugins sont chargés au **premier `DirectInput8Create`** (une seule fois, protégé), hors verrou du chargeur. Chemin du vrai : `GetSystemDirectoryW` + `\dinput8.dll` (dans un processus 32 bits sous Windows 64 bits, ça donne `SysWOW64`, INFÉRÉ, documenté par Windows ; **vérifié en P1** sur le faux jeu).
3. **Plugins nommés, jamais balayés** : une liste fixe (nom + sha256), vérifiée **avant** chargement ; un fichier absent ou au mauvais sha256 est refusé et journalisé, le jeu continue sans lui. Noms proposés : `cc2m\cm_frein.dll` et `cc2m\cm_modes.dll` dans le dossier du jeu — **volontairement différents de `cc2x_*.dll`** pour que le SDK (pendant la transition ou au retour arrière) ne les charge jamais par erreur. La liste des sha256 : fichier à côté du chargeur **ou** gravée dans le chargeur — **décision à prendre en P1** (graver = plus sûr mais il faut recompiler le chargeur à chaque nouvelle version de plugin).
4. **SHA-256 écrit par nous** (~80 lignes, testé sur les vecteurs officiels et contre `hashlib` de Python) plutôt que l'API Windows de chiffrement : on garde ainsi **KERNEL32 + bibliothèque C seulement** dans les imports (même contrôle qu'aujourd'hui, `construire.py`).
5. **Mini-API de même forme** que l'actuelle (lire/écrire un champ par identifiant + indice, mêmes noms de fonctions), **en-tête et code écrits par nous** (aucune ligne de `cc2x.h`/`world.c` copiée : on reprend des **faits sur le jeu**, pas du code ; le verdict de relecture l'avait noté). Avantage : modes v2 et frein v6 se portent presque mécaniquement, et les 143 contrôles actuels se rejouent tels quels.
6. **Écritures inchangées** : mêmes champs, mêmes valeurs, mêmes bornes que les versions SDK. Aucune écriture nouvelle.
7. **Garde-fous de lecture conservés** : contrôles de cohérence de la file circulaire (`dq_ok`), indices bornés, pointeurs nuls ignorés.
8. **Tick sûr pour `xmm`** : les 3 cases de table sont des appels virtuels normaux (INFÉRÉ sûr, à vérifier : H6). Le seul relais en milieu de fonction (site Lua, option A) utilise notre tremplin `cp_hook` (sauve `xmm0-7`, drapeaux, aligne la pile).
9. **Même journal** `cc2x.log` (voir section 3). Le chargeur journalise ce qu'il a chargé ou refusé, avec les sha256.
10. **Cibles de test pour que le chargeur soit testable sans le jeu** : un petit programme hôte 32 bits qui charge notre `dinput8.dll` dans un faux dossier de jeu, avec un faux `dinput8.dll` « système » (version de test uniquement, jamais installée), et un faux jeu en mémoire (serveur, véhicules, corps) construit **avec les vrais décalages** pour tester la lecture et l'écriture.

## 8. Plan par phases, chiffré

« Session » = un tour de travail comparable à celui-ci (ordre de grandeur, INFÉRÉ). Le risque est celui de **l'action de la phase** pour toi.

| Phase | Ce qu'on fait | Livrables | Volume (INFÉRÉ) | Critères de réussite | Arrêt si | Risque | Ce que tu fais |
|---|---|---|---|---|---|---|---|
| **P1** chargeur seul, hors jeu | `dinput8.dll` à nous : 5 exports, vrai dinput8 par chemin absolu, SHA-256, liste de plugins nommés, journal ; essayé avec faux jeu / faux dossier | sources, `construire.py`, rapport (imports par fonction, sha256, déterminisme ×2) | ~450 lignes C + ~300 lignes de tests/scripts ; **≥ 40 contrôles** (exports non décorés, chemin absolu, sha refusé / accepté, aucun balayage, `DllMain` sans appel interdit, imports = KERNEL32 + CRT) ; 1 session | 0 échec ; table d'exports exactement les 5 noms ; aucun import réseau, registre, processus, interface | un import interdit, un export décoré, un échec non expliqué | 🟢 (compilation et essai dans un dossier de travail, hors jeu) | rien |
| **P2** vérification statique | les 30 faits (+23 si option A) revérifiés au désassembleur sur le vrai `carrier_command.exe`, **lecture seule** ; décision A/B tranchée par les faits Lua | script de vérification (~350 lignes), rapport « CONFIRMÉ / DIFFÉRENT / NON TRANCHÉ » par fait | 1 à 2 sessions | tous les faits utilisés sont CONFIRMÉS ; sinon ce qui en dépend est exclu | un fait d'écriture (V16, M1, V13) non confirmé | 🟢 (le fichier du jeu n'est que lu) | rien |
| **P3** mini-API et portage | mini-API (~450 lignes) ; frein v5 et modes (v1 ou v2, selon ce qui est posé) portés ; faux jeu en mémoire ; **comparaison de comportement** : mêmes scénarios rejoués contre l'ancienne API et la nouvelle, journaux comparés ligne à ligne | sources, tests, rapport de comparaison | **≥ 203 contrôles** : ≥ 105 (frein) + ≥ 38 (modes) repris un à un, plus ≥ 60 sur la couche d'API (lecture/écriture aux bons décalages, listes vides ou cassées, pointeurs nuls, bornes). Si modes v2 est la cible : ≥ 105 + 72 + 60 ; 2 à 3 sessions | 0 échec ; journaux identiques à ceux des versions SDK sur tous les scénarios | un écart de comportement non expliqué | 🟢 | rien |
| **P3b** (si option A) pont Lua | `cc2x.api/version/log/tick/vehicles/tiles` en lecture seule, relais Lua avec tremplin `xmm`-sûr | sources, tests avec **faux** Lua | ~400 lignes ; 1 à 2 sessions de plus ; la preuve réelle n'existe qu'en jeu (P5) | tests de logique OK ; faits LI01-LI16 CONFIRMÉS | un fait LI non confirmé → repli sur B | 🟡 en P5 (le reste 🟢) | rien |
| **P4** compilation déterministe | deux compilations, même résultat (hors horodatage PE et identifiant de build, comme aujourd'hui) ; relecture des imports ; sha256 | rapport signé de sha256, liste d'imports | ½ session | aucun import réseau / registre / processus ; sha256 stables | tout import nouveau | 🟢 | rien |
| **P5** remplacement dans le vrai jeu | outil `etat / installer / retirer` (adapté de `poser.py`, ses 38 contrôles sur faux dossiers refaits, essayé d'abord sur de FAUX dossiers) ; remplacement de `dinput8.dll` + pose de 2 DLL + vérification des sha256 | outil, rapport de pose | 1 session + un essai avec toi | `cc2x.log` montre le chargeur, le build reconnu, les deux plugins chargés, une partie sans plantage, **SIM ×1,33 comme avant** ; frein et gaz se comportent comme avec le SDK | plantage au démarrage, plugin refusé, écart de SIM, comportement différent du frein | 🟡 (du code natif de notre fabrication remplace du code natif de tiers dans le jeu) | fermer le jeu, dire « oui », jouer l'essai |

**Précaution pour P5** : l'outil `poser.py` du frein et `mod_modes.py poser-plugin` de la conversation modes **supposent le SDK** (ils refusent un autre `dinput8.dll` ou posent la DLL dans le mod). Après P5 ils seraient faux ; il faudra les neutraliser ou les remplacer, et prévenir les autres conversations **avant** (je ne les modifie pas).

## 9. Pièges et écarts relevés (pour que rien ne te surprenne)

1. **`cc2_mesures` n'appelle pas `cc2x`** (brief corrigé, section 5.1).
2. **Le contrôle des 8 octets à `0x71dbbf` n'est pas lié à `xmm`** (section 6) ; le risque `xmm` n'existe qu'au site Lua `0x004465ec` du SDK (LU `cc2x.c:243-257`, `854`).
3. **`cc2x_modes.dll` est dans le mod `cc2_modes`**, pas dans le dossier du jeu : sous notre chargeur il serait ignoré (c'est voulu) ; il suffira de ne pas le supprimer pour garder le retour arrière.
4. **Les copies d'essai `carrier_command_test_cercle*.exe`** ont le même en-tête que le vrai exe : le SDK les accepte (il ne contrôle que horodatage et taille). Notre chargeur fera de même ; si tu veux qu'il refuse tout exécutable qui ne s'appelle pas `carrier_command.exe`, c'est une décision à prendre en P1. `carrier_command_vr.exe` et `dedicated_server.exe` n'ont a priori pas le même en-tête (INFÉRÉ, à vérifier en P2) : le chargeur resterait inerte.
5. **Le journal `cc2x.log` est supprimé à chaque lancement** (`cc2x.c:908`) ; on garde ce comportement (les outils de copie des autres conversations le supposent).
6. **Ma branche** s'appelle `[branche]` (le préfixe est mis par l'application) au lieu de `chargeur-maison` ; jamais `main`.
7. **Plan B du Mac** (`NOTE_mac_frein_seul_27-10.md`, ligne 27 : « plusieurs jours de travail » pour retrouver les fonctions) : ici c'est bien moins lourd, parce qu'on **vérifie** des adresses déjà publiées au lieu de les **chercher** ; la charge est dans la preuve, pas dans la découverte.

## 10. Limites de cette phase

- **Aucun désassemblage** n'a été fait : tous les décalages sont « affirmés par le SDK », pas « confirmés ». Les estimations de volume et de sessions sont des ordres de grandeur (INFÉRÉ).
- J'ai lu les scripts Lua **installés** (copies réelles dans `%APPDATA%`), pas seulement ceux du dépôt, parce que le script de `cc2_carte` n'est pas dans le dépôt (aucun fichier `.lua` du dépôt ne contient `CC2MAP`). Je n'ai **rien** modifié dans ces dossiers.
- Lecture seule de la copie non commitée de `cc2x_modes.c` (v2) dans le dossier principal, **sans toucher** à ce dossier ; ses chiffres (72 contrôles, sha) viennent de la note de l'autre conversation, **non revérifiés**.
- Rien n'a été compilé en P0.

## 11. Prochaine action concrète

Après ta réponse à la question de décision (d) et ton accord écrit pour P1, j'écris le **chargeur seul** dans `tour/chargeur_maison/`, je le fabrique et l'essaie **dans un dossier de travail avec un faux jeu** (rien dans le vrai dossier du jeu, jeu non lancé), puis je te rends un rapport avec la table d'exports, les imports par fonction et les sha256.

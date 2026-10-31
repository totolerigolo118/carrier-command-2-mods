# Note du Mac pour la tour — test du FREIN SEUL pour l'atterrissage à la main (27/10/2026)

Contexte : voir `passation_windows/ETUDE_mac_atterrissage_manuel_27-10.md` (sections 6 et 7). Le moddeur veut, à terme : **il pose l'avion à la main sur le porte-avions, l'avion freine tout seul au toucher, il s'arrête, puis le jeu fait le pushback**. Ici on teste **uniquement le frein** (pas de prise en charge, pas de pushback).
**Décision du moddeur (27/10) : voie « SDK relu et compilé par nous », avec un accord séparé de sa part pour chaque étape.** Rien de ce qui suit ne se fait sans son « oui » à l'étape concernée.

## Règles du moddeur qui priment (rappel)
- Aucun risque inutile. Pour chaque action : ce qu'elle fait, le risque (🟢 faible / 🟡 moyen / 🔴 élevé), une alternative plus sûre.
- **Aucun code de tiers dans le jeu sans relecture complète et sans son accord.** Un accord ne couvre jamais plusieurs actions (téléchargement, installation, fichier du jeu modifié, lancement du jeu).
- Français simple, une seule question à la fois, finir par la prochaine action concrète. Ne jamais lancer ni fermer le jeu sans qu'il le demande.
- Pas de DLL de release d'un tiers : **on compile nous-mêmes, depuis des sources relues.**

## Ce qu'on teste, et pourquoi le SDK
Ton essai (le moddeur, 27/10) : posé à la main sur la piste, l'avion **glisse** ; à vitesse nulle rien ne se passe et l'IA essaie de redécoller. Le jeu a un frein de roues (`set_wheel_brake(frein, adhérence)`, écrit deux nombres dans les 3 roues de l'avion ; lu sur le Mac), mais **le joueur n'a pas d'entrée de frein**. Freiner exige du code qui tourne dans le jeu. Le SDK public offre `vehicle_brakes(v, brake, grip)` (documenté « 0..1 chacun », `WORLD_API.md`), la lecture de l'état des véhicules et de leurs roues, et un rappel à chaque pas serveur : **aucune adresse du jeu à retrouver** pour ce test.
**Réussi si** : posé à vitesse normale sur la piste, l'avion s'arrête avant le bout (~150 m), le frein n'agit ni en vol ni au décollage, et les avions de l'IA se posent et rentrent comme avant.

## Étapes (chacune demande un accord séparé du moddeur)

| # | Étape | Risque | Alternative plus sûre |
|---|---|---|---|
| 1 | `git clone` du dépôt public du SDK (`Dioramawhois/Carrier-Command-2-extender`) **dans un dossier à part**, hors du dépôt du projet et hors du dossier du jeu ; **noter le hash du commit**. Récupérer ainsi les fichiers manquants (`internal.h`, `dinput8.def`, `include/cc2x.h`, `tests/selftest/…`). | 🟢 (texte, rien n'est lancé) | Sans objet : sans ces fichiers on ne peut pas compiler. |
| 2 | **Relire TOUT le SDK** (voir la liste de contrôle ci-dessous) et rendre au moddeur un verdict écrit : sûr / pas sûr, avec les preuves. | 🟢 | — |
| 3 | Écrire le **plugin de test** (≈ 80 lignes, voir spécification) et compiler `dinput8.dll` + `cc2x_frein.dll` avec Zig (déjà installé) **dans un dossier de travail**. Pas de copie dans le jeu. | 🟢 | — |
| 4 | **Poser** `dinput8.dll` et `cc2x_frein.dll` à côté de `carrier_command.exe`, avec un petit outil `etat / installer / retirer` (même esprit que `patch_exe.py` : refuse si le jeu tourne, vérifie les sha256, ne remplace rien d'existant). | 🟡 (du code compilé depuis des sources de tiers, relues, tourne dans le jeu) | Ne pas faire cette étape : le test de frein est alors impossible. Plan B : nos propres crochets (voir plus bas). |
| 5 | **Le moddeur lance le jeu et fait l'essai** (protocole ci-dessous). | 🟡 (avion perdu, plantage possible) | Sauvegarde jetable, jamais celle de référence. |
| 6 | **Retour arrière** : `retirer` (supprime les deux DLL ; l'exécutable patché n'est pas touché). | 🟢 | — |

**Plan B si le moddeur refuse l'étape 4 ou si la relecture est mauvaise** : nos propres crochets sans SDK (code dans une zone vide de l'exécutable, comme sur le Mac) ; il faut alors retrouver côté Windows la fonction `set_wheel_brake` (écriture de 2 nombres dans les roues, `véhicule+0xd0`, pas `0x70`), le test de toucher et la file des pilotes : plusieurs jours de travail ; ce serait la voie « sans tiers » pour la version finale.

## Étape 2 — liste de contrôle de la relecture du SDK
Lire entièrement : `src/cc2x.c`, `src/world.c`, `internal.h`, `dinput8.def`, `include/cc2x.h`, `build.py`, le plugin d'exemple. Vérifier, preuve à l'appui (nom de fichier + ligne) :
1. **Rôle de `dinput8.dll`** : ne charge que la **vraie** `dinput8.dll` du dossier système (chemin système, pas un chemin relatif) et lui renvoie les 5 fonctions exportées (`DirectInputCreate…`).
2. **Rien de réseau** : aucun appel WinSock / WinHTTP / WinINet / `URLDownloadToFile` / `curl` / DNS.
3. **Aucun lancement de programme** (`CreateProcess`, `ShellExecute`, `WinExec`, `system`), **aucune écriture dans le registre**, aucune suppression de fichier, aucun crochet de clavier ou de souris, aucun accès au presse-papiers.
4. **Fichiers écrits** : seulement `cc2x.log` et le dossier de réglages (`api->config_dir` = `%APPDATA%\Carrier Command 2\cc2x`). Lister tout autre chemin écrit.
5. **Aucune mise à jour automatique**, aucune télémétrie.
6. **Ce que le SDK modifie dans le jeu au démarrage** (le texte dit : rien sans abonné ; confirmer dans le code ce que fait l'événement `on_server_tick`, qui remplace une case de table de fonctions du serveur).
7. **Chargeur de plugins** : d'où il charge les DLL. D'après `PLUGINS.md`, il charge aussi `content\cc2x\*.dll` de **chaque mod activé** dans `mods.xml`. Vérifier qu'**aucun mod actif du moddeur** (Revolution, missiles, `cc2_mesures`) n'a de dossier `cc2x`, et dire au moddeur qu'un futur mod Workshop avec un tel dossier serait exécuté.
8. **Comparer le dépôt actuel à notre copie du 25/10** (`SOURCE.txt` donne ses empreintes ; le journal des changements a bougé trois fois le 25/10) et **figer le hash** du commit relu. Ce qu'on compile doit être exactement ce qu'on a relu.
En cas de réseau, de lancement de programme, d'écriture hors de la liste ou de comportement inexpliqué : **arrêt et rapport**, on ne continue pas.

## Spécification du plugin de test `cc2x_frein.dll` (source dans `tour/frein/`)
Réglages dans `%APPDATA%\Carrier Command 2\cc2x\frein.ini` (mêmes règles que `cc2_patchs.ini` : tout éteint par défaut) : `brake_enabled` (0/1, **0 par défaut**), `brake` (0..1, défaut 1,0), `grip` (0..1, défaut 1,0), `zone_m` (défaut 150).
À chaque pas serveur (`on_server_tick`, fil serveur uniquement), pour chaque véhicule de la liste `CC2X_WORLD_VEHICLES` :
- **Éligible** si **toutes** ces conditions sont vraies : voilure fixe (`CC2X_VEHICLE_IS_WING`), équipe humaine (`CC2X_VEHICLE_TEAM_IS_AI == 0`), **pas** rattaché au porte-avions (`CC2X_VEHICLE_ATTACHED_TO == 0`), état d'accostage « en vol » (`CC2X_VEHICLE_DOCK_STATE == 0`), état de vol « au sol » (`CC2X_VEHICLE_FLIGHT_STATE`, valeur de `CC2X_FLIGHT_*` pour le sol), **toutes les roues en contact** (`CC2X_VEHICLE_WHEEL_CONTACT[i] > 0` pour chaque `i`), et **à moins de `zone_m` mètres** du porte-avions de son équipe (position de son corps, `body_get`, hauteur à ±20 m). Le porte-avions de l'équipe se retrouve par son type (`CC2X_VEHICLE_DEFINITION`) dans la même liste.
- **Phase 1 (observation, `brake_enabled = 0`)** : ne rien freiner ; écrire dans `cc2x.log` (via `api->log`), à chaque changement d'état d'un avion éligible ou presque éligible, ses valeurs : `flight_state`, `dock_state`, `attached_to`, contacts des roues, vitesse (`body_get`, norme de la vitesse), distance au porte-avions. **But : confirmer que l'avion posé à la main a bien ces valeurs-là** (c'est une hypothèse tirée de l'observation du moddeur, pas encore vue).
- **Phase 2 (frein, `brake_enabled = 1`)** : sur un avion éligible, appeler `vehicle_brakes(v, brake, grip)` à chaque pas ; mémoriser son identifiant ; journaliser le **début du freinage** (vitesse, distance parcourue sur le pont) et l'**arrêt** (vitesse < 0,3 m/s : temps et distance de freinage). Dès qu'un avion mémorisé n'est plus éligible : `vehicle_brakes(v, 0, 1,0)` (valeurs « repos » du jeu) et le journaliser.
- **Ne jamais** toucher un avion rattaché au navire, en état d'accostage non nul ou de l'équipe IA (sinon on freine le pushback de l'IA et on bloque la piste). Ne jamais écrire la position d'un avion sur ses roues (le SDK avertit que le jeu le détruit).
- Hélicoptères : pas dans ce test.

## Protocole d'essai (étape 5, le moddeur) — deux phases, sauvegarde jetable
Même manœuvre que son premier essai (voir la note d'étude, section 5) : lancer un avion, le prendre en main, finale dans l'axe, toucher le pont, rester sur la piste.
- **Phase 1** (`brake_enabled = 0`) : 2 atterrissages ; la tour lit `cc2x.log` et confirme les valeurs d'état de l'avion posé. **Rien n'est freiné.** Si les valeurs ne correspondent pas à l'éligibilité ci-dessus : on corrige le plugin avant la phase 2.
- **Phase 2** (`brake_enabled = 1`, `brake = 1,0`, `grip = 1,0`) : 3 atterrissages (un doux, un plus dur) ; lire distance et temps d'arrêt dans le journal ; noter ce que le moddeur ressent. Si l'avion ne s'arrête pas : essayer `grip` autre (le jeu utilise jusqu'à 3,0 pour ses propres avions, le SDK documente 0..1 : à vérifier par l'essai) ; ne pas dépasser sans l'accord du moddeur.
- **Vérification IA obligatoire en fin d'essai** : lancer puis rappeler 4 avions de l'IA avec le plugin actif ; le journal du plugin doit montrer **0 freinage** pour eux, et ils doivent rentrer normalement (pas de piste bloquée). Comparer le résumé du journal des retours aux mesures précédentes.

## Conditions d'arrêt
SDK : réseau, lancement de programme, écriture hors liste, hash introuvable. Jeu : plantage au démarrage, `cc2x.log` ne reconnaît pas le build `1.5.18-win32`, avion de l'IA freiné, piste bloquée. Dans tous ces cas : `retirer`, journaliser, rendre la main au moddeur.

## Ce que ce test ne fait pas
Pas de prise en charge à l'arrêt, pas de pushback, pas d'hélicoptères, pas de multijoueur (le SDK n'a aucun transport : solo ou hôte seulement, et la règle du moddeur est de ne l'utiliser qu'en local pour ce test). La prise en charge viendra après, avec les décalages 32 bits du gestionnaire d'avions (étape 7 de la feuille).

## Propriété des fichiers
La tour écrit `tour/frein/` (source du plugin, journaux, outil `etat/installer/retirer`) et `passation_windows/JOURNAL_tour.md`. Le Mac ne les modifie pas. Le SDK cloné reste **hors du dépôt** (seule la liste des fichiers lus et le hash du commit entrent dans le journal).

## Texte à coller dans la session de la tour
```text
Fais d'abord git pull, puis lis passation_windows/NOTE_mac_frein_seul_27-10.md en entier, puis passation_windows/ETUDE_mac_atterrissage_manuel_27-10.md (sections 6 et 7).
On teste le FREIN SEUL pour l'atterrissage à la main, par la voie « SDK relu et compilé par nous ». Règles : aucun risque inutile (pour chaque action : ce qu'elle fait, le risque 🟢/🟡/🔴, une alternative plus sûre), un accord séparé pour chaque téléchargement, installation, fichier du jeu modifié ou lancement du jeu, une seule question à la fois, français simple.
Commence par trois lignes : ce que tu vas faire, ce que tu ne feras pas, la première chose dont tu as besoin. Présente-moi seulement l'étape 1 (cloner le dépôt du SDK dans un dossier à part et noter le hash du commit), avec son risque, et attends mon accord. Ne copie rien dans le dossier du jeu.
```

# Plugin v3.1 + onglet SPEED v2.1 : ce qui change, pourquoi, les risques, comment poser et revenir en arrière

Préparé le 30/10/2026, **hors du jeu**, puis **POSÉ le 30/10 à 08:21 avec le « Oui, pose » du moddeur (jeu fermé)** : le mod `cc2_modes` contient maintenant la mesure, l'onglet **v2.1** (`C91FFDEB…`) et le plugin **v3.1** (`4B2EBC04…`),
`modes.ini` inchangé (`eco_enabled=0`, observation). Ils ont remplacé l'onglet v2 et le plugin v3, posés à 07:38 et essayés en jeu le même jour (ÉCO sur l'avion 10 : 80 m/s, −21 % de carburant ; garde-fou « HELD » vu ; voir `ETUDE.md` §16).
**Elles ont tourné en jeu le 30/10 (08:37 → 09:51) : voir « Résultats en jeu » ci-dessous.** Les commandes de pose plus bas sont **déjà faites** ; elles servent de rappel et pour le retour arrière.

## Résultats en jeu (30/10/2026, v3.1 + v2.1 posées à 08:21 ; détail : `ETUDE.md` §17 et §18)

- **Marche** : `loaded v3.1`, **0** avertissement, **0** ligne `modes.ini:`, **0** erreur d'onglet. ÉCO (avion 10) : 80 m/s, **−22 % de carburant**. Garde-fou pilote **vu** sur les avions 9, 10 et 17 : pause à la même milliseconde que la prise en main, reprise 3 s de jeu après. Les **clics** ECO / NORMAL / FLANK de l'onglet arrivent au plugin et passent avant `modes.ini` ; capture du moddeur (relayée par la coordination) : FLANK en jaune, « ACTIF », « AUTONOMIE ~33 min ».
- **Ne marche pas comme espéré** : **FLANK sur l'Albatros = aucun gain** (119,1 m/s comme NORMAL). **FLANK sur le Manta** : ≈ 225 m/s puis **oscillation d'altitude (±18 m) à partir de ~222 m/s**, qui coûte 35 % de portée ; hypothèse non prouvée : la boucle d'altitude de l'IA. Cela ne vient pas des corrections v2.1 / v3.1 ni du garde-fou (l'oscillation est sans rapport avec un pilotage) ; la cause reste une hypothèse : comportement de l'IA à cette vitesse, éventuellement aggravé par les gaz bloqués à 1,0. Prochain essai proposé : `flank_floor_heavy=0.75`.
- **Toujours pas vu** : « PLUGIN PLEIN » (64 avions), ÉCO du Manta, `retirer` en vrai. Le texte « OBSERVATION : SANS EFFET » n'a pas été confirmé séparément (la capture montre « ACTIF »).

## Pourquoi

Deux relectures indépendantes (faites dans le nuage, sans le jeu) ont trouvé des défauts dans notre code. J'ai **revérifié chaque point en relisant le code** avant de le corriger ;
ceux qui sont réels et sûrs à corriger hors jeu sont corrigés ici. Les autres sont listés plus bas, avec la raison pour laquelle je ne les ai pas touchés.

## Ce qui change

| Où | Le défaut (vérifié dans le code) | Après la correction |
|---|---|---|
| **Plugin** : lecture de `modes.ini` (revue B1, le point bloquant) | une valeur **vide** donnait une zone de 0 m ; `1 500` (espace) était lu **1 m** ; `nan` supprimait la zone ou le plafond ; un commentaire `eco_ids=9 ; avion 10` mettait aussi l'avion 10 en ÉCO ; au-delà de 16 numéros, les suivants étaient perdus **sans rien dire**. La zone libre est la seule protection du décollage | une valeur **absente** garde son défaut sans bruit ; une valeur **illisible** (vide, `nan`, `1 500`, lettres…) est ignorée, le défaut sert, et le plugin écrit **une seule ligne** `modes.ini: clé="valeur" …` dans `cc2x.log` (et la réécrit seulement si le texte change). Un nombre lisible mais hors limites est ramené à la limite la plus proche, avec la même ligne. Les **zones de sécurité ne peuvent plus descendre sous leur valeur par défaut** (ÉCO 1500 m, FLANK 6000 m ; maximum 20 000 / 30 000 m). Un commentaire après `;` ou `#` est ignoré. Interrupteurs : `0 1 true false yes no on off` (autre chose, par exemple `2` ou vide = **éteint** + ligne d'avertissement). Listes d'avions : que des chiffres, virgules, espaces, sinon **toute** la liste est ignorée (+ ligne) ; plus de 16 numéros : les 16 premiers comptent (+ ligne) |
| **Plugin** : journal (revue M3) | après 4000 lignes, la ligne `id N: HELD` (la preuve qu'on attend au premier essai) n'était plus écrite | `HELD` / `no longer held`, la ligne `settings:` et les avertissements `modes.ini` ont leur **propre réserve** de 1000 lignes ; les lignes ordinaires s'arrêtent toujours à 4000. Les avertissements passent toujours |
| **Plugin** : `status()` | — | ajoute `revision = 1` (la version reste 3). Le journal dit `loaded v3.1` |
| **Onglet** (revue ONG-R1) | le crochet « le joueur pilote cet avion » n'était posé que si `g_viewing_vehicle_id` était déjà un nombre au démarrage de l'écran, et **jamais réessayé** : si ce n'était pas le cas, le plugin pouvait écrire les gaz de l'avion que le moddeur pilote | le crochet est posé **sans condition** sur `update()`, réessayé à chaque image où le jeu dessine la sélection, et refait si le jeu (ou un autre mod) remplace `update()`. Il reteste `g_viewing_vehicle_id` à chaque appel : sur un écran sans avion piloté il ne fait rien |
| **Onglet** (revue ONG-R2) | le crochet ne lisait que la valeur de l'image **précédente** : une image de retard à la prise en main | appelé **avant et après** `update()` du jeu |
| **Onglet** (revue ONG-1) | le plugin refuse le 65e avion (sa table est pleine) mais l'onglet ignorait la réponse : le bouton revenait à NORMAL sans un mot | la réponse est lue : refus → le bouton ne s'allume pas et l'onglet écrit **« PLUGIN PLEIN »** (ou « PLUGIN : ERREUR ») pendant quelques secondes (180 images) |
| **Outil** `mod_modes.py` (revue I2) | le « refus si le jeu tourne » ne voyait **pas** l'ancien exe de la voie A pour `installer`, `mettre-a-jour` et `retirer` ; l'option `--jeu-ouvert-ok` permettait de passer outre | **toutes** les commandes qui écrivent refusent si un `carrier_command*` tourne ou si on ne peut pas le savoir ; `--jeu-ouvert-ok` est refusé. Nouveaux : `--etape interface2_1` / `tout2_1` (onglet v2.1), `mettre-a-jour-plugin --version 3` ou `3.1` (aller **et retour**), `etat` décrit toutes les versions connues |
| **Documents** | `RISQUES_v3.md` disait « rien n'est posé » (faux depuis le 30/10 à 07:38) ; `modes.ini.example` disait « ton équipe » pour `eco_all` alors que le code vise **toutes les équipes humaines** | `RISQUES_v3.md` corrigé ; `plugin/v3_1/modes.ini.example` corrigé et complété par les règles ci-dessus |

## Ce qui ne change PAS

- **Le plugin reste passif** : il n'écrit toujours **rien dans le jeu** tant que `modes.ini` n'a pas `enabled=1` (ou `true`, `yes`, `on`). Même code d'écriture (le flottant à +0x314, après le tick), mêmes plafonds, mêmes planchers, mêmes exclusions (équipes IA, hélicoptères, avions au sol, en rappel, près du bateau), mêmes deux builds du jeu reconnus.
- Aucun accès réseau, aucun fichier écrit hors `cc2x.log` ; mêmes appels Windows qu'avant, à une nuance près (voir « Contrôles »).
- Le `modes.ini` **actuel** du moddeur (`eco_enabled=0`, `eco_cap=0.65`, `eco_all=0`, `eco_ids=10`, `free_zone_m=1500`, `observe_s=5`, sha `DC8947E6…`) se lit **sans aucun avertissement** avec les mêmes valeurs ; je l'ai vérifié sur la copie `mesures/2026-10-28_partie2_modes.ini`.

## Ce qui change pour qui écrit un `modes.ini` à la main

1. Zone libre ÉCO **au moins 1500 m**, FLANK **au moins 6000 m** (avant : n'importe quoi, même 0). Pour essayer plus près du bateau il faudra une décision explicite (et une nouvelle version).
2. `enabled=2` ne veut plus dire « oui » (avant, tout nombre non nul). Écrire `1` ou `true`.
3. Pas d'espace dans un nombre (`1500`, pas `1 500`). La virgule décimale reste acceptée (`0,65`).
4. Un `; commentaire` à la fin d'une ligne est maintenant ignoré (Windows, lui, le garde dans la valeur : j'ai vérifié sur ce PC).

## Contrôles faits (tous hors jeu, sur ce PC)

- **Banc de la v3.1 : 289 contrôles réussis, 0 échec** (292 avec la lecture de `modes.ini.example`), programme 32 bits Windows compilé avec UBSan et `-Werror`, qui utilise le **vrai** `GetPrivateProfileStringA` de Windows. Ce sont les 130 de la v3 (dont **2 adaptés**, voir ci-dessous) + 159 nouveaux : zones ÉCO et FLANK avec 18 et 8 valeurs fautives, plafonds, planchers, `observe_s`, interrupteurs (6 « oui », 4 « non », 8 fautifs), listes d'avions (commentaires, 17 numéros, liste trop longue, 8 formes fautives), avertissement écrit une seule fois puis de nouveau si le texte change, `HELD` et avertissements encore écrits **après** la coupure du journal, la réserve elle-même bornée à 1000 lignes.
- **Les 2 contrôles de la v3 que j'ai dû adapter** : « `flank_free_zone_m=2000` » (maintenant 8000) et « `free_zone_m=100` avec un avion à 800 m » (maintenant 2500 / 3000 m), parce que ces valeurs sont **sous les nouveaux planchers**. Le banc de la v3, **non modifié**, lancé contre la source v3.1, donne 128 réussis et ces 2 seuls échecs : rien d'autre n'a bougé.
- **Windows confirmé** (petit programme maison, jetable) : `clé=` vide est rendu **vide** (pas le défaut) ; un espace seul aussi ; `clé=9 ; 10` est rendu `9 ; 10` (le commentaire n'est pas retiré par Windows) ; les guillemets sont retirés ; `1 500` est rendu tel quel ; une ligne qui commence par `;` est un vrai commentaire. C'était le point « à confirmer sous Windows » de la revue.
- **DLL v3.1** : 225 280 octets, sha256 `4B2EBC04D772D7EFB2F21E70AA17CB7FE26CF7A044FDFE3B97F07FDCD1FE1D51`, dossier de travail à part `C:\Users\UTILISATEUR\Documents\cc2-modes-travail-v3_1\` (la DLL v3 posée, `cc2-modes-travail\dist`, n'a pas bougé : `331581C6…`). **Deux compilations identiques** (hors horodatage). Un seul export, `cc2x_plugin_load`. Aucune chaîne suspecte. **Imports comparés à la v3** : disparus `atof` et `strchr` ; ajoutés `strtod` et `strcmp` (fonctions standard de texte et de nombres, même DLL système) ; tout le reste identique (verrous, `GetPrivateProfileStringA`, sorties texte).
- **Onglet v2.1** (`lua/v2_1/library_custom_5.lua`, 259 lignes, sha256 `C91FFDEBE7CBE08DFD27EB83F492BB261686B0C4CEE084F482BE05D578E197A2`) : syntaxe validée par `tour/outils/lua_syntaxe.py` (0 erreur) ; `lua_inconnus.py` ne signale que `cc2x` et nos propres variables (comme la v2 ; `g_cm_update_vu` remplace `g_cm_update_enveloppe`). `lua/v2` n'est pas modifié (sha `0A402A3E…`).
- **Installateur** : `test_mod_modes.py`, **60 contrôles réussis**, sur une fausse racine : refus si le jeu tourne **ou si on ne sait pas**, pour `installer`, `mettre-a-jour` (3 étapes), `retirer`, `poser-plugin`, `mettre-a-jour-plugin`, `retirer-plugin` ; `--jeu-ouvert-ok` refusé ; v2.1 → v2 → v1 → v2.1 avec `mods.xml` identique ; v3 ⇄ v3.1 ; un plugin inconnu n'est jamais remplacé ni retiré ; `retirer` rend `mods.xml` à l'octet près. Les fichiers **réels** (`mods.xml`, `mod.xml`, scripts, DLL, `modes.ini`) avaient les mêmes empreintes avant et après l'essai.

## Ce qui n'est PAS prouvé

1. **L'onglet v2.1 n'a jamais été exécuté ni affiché** : il n'y a pas d'interpréteur Lua sur ce PC (et je n'en installe pas). Syntaxe et noms sont vérifiés par nos outils maison ; la logique a été relue à la main, comme pour la v1 (qui, elle, marche en jeu). S'il plante, il se coupe seul (`pcall`) et le jeu continue.
2. **Que `g_viewing_vehicle_id > 0` veuille dire « je pilote cet avion »**, et **à quel moment** cette variable existe : toujours inconnu. La v2.1 supprime la dépendance au moment (crochet posé tout de suite, réessayé), pas l'incertitude sur le sens.
3. Le crochet enveloppe `update()` dans **tous** les états Lua où le script est chargé (pas seulement l'écran de pilotage) ; il ne fait rien là où il n'y a pas d'avion piloté. Comme la mesure `library_custom_3.lua` le fait déjà, cela change le nombre de paramètres de `update` pour un autre mod qui le lirait (revue MES-R4, non corrigé).
4. Tout ce qui concerne le comportement des avions (FLANK, ÉCO du Manta, IA à grande vitesse, avion chargé) : inchangé, voir `RISQUES_v2.md`.

## Ce que je n'ai PAS corrigé, et pourquoi

| Point de la revue | Raison |
|---|---|
| **I1, volet plugin** : « battement de cœur » (le plugin n'écrit que si l'écran répond, fail-closed) | c'est un **changement de logique de sécurité** (il casserait les listes `eco_ids` de `modes.ini` quand l'onglet n'est pas chargé) : décision de conception à prendre avec le moddeur. En attendant : **ne jamais passer `enabled=1` tant que `HELD` n'a pas été vu dans le journal** |
| I3 : `retirer` et `mods.xml` en CRLF / doublon | dans l'outil de base `tour/outils/mod_mesures.py` partagé avec d'autres études ; je ne le modifie pas. Aucun risque tant que `mods.xml` garde ses fins de ligne actuelles (c'est le cas : `E1267AED…`) |
| I4 : FLANK lâche d'un coup à la sortie de zone / I5 : rien sur le combat, le relief, le carburant | il faut des **mesures en jeu** avant de choisir une solution (décélération de l'IA jamais mesurée) |
| I6 : `eco_all` / `flank_all` visent toutes les équipes humaines | seule la **documentation** est corrigée (`modes.ini.example`) ; filtrer par équipe demande de connaître l'équipe du joueur |
| M1 (cadence ≠ 30 ticks/s), M2 (relecture non atomique), M4 (table de 64 purgée), M5 à M9, M11 | sans risque pour l'observation ; M2 est en pratique couvert par les planchers de zone (une valeur coupée comme `15` pour `1500` est remontée à 1500) ; M4 est en partie traité côté onglet (« PLUGIN PLEIN ») |
| M10 (`mettre-a-jour` réécrit `mod.xml`) | noté dans `RISQUES_v3.md` (description seulement) |
| M12 (autonomie affichée même en « SANS EFFET ») | purement d'affichage, hors du périmètre demandé |
| MES-R1 à R4, ENS-R*, autres scripts | hors de ce chantier |
| Hystérésis sur la limite de zone (M3, 2e partie) | l'effet (beaucoup de lignes ordinaires) est borné par la coupure à 4000 lignes ; le cas extrême est rare |

## Les risques, par étape (🟢 faible / 🟡 moyen)

| Étape | Ce que ça fait | Risque |
|---|---|---|
| **M4 : poser les fichiers** (jeu fermé) | remplace l'onglet v2 par la v2.1 et le plugin v3 par la v3.1 dans `mods\cc2_modes` ; ne touche ni au jeu, ni à `mods.xml`, ni à `modes.ini` ; réécrit `mod.xml` seulement si son texte diffère (il est déjà à jour) | 🟢 pas de risque de sécurité notable. Le plugin ne tourne pas encore |
| **A4 : lancer** (ancien exe, partie neuve jetable, `enabled=0`) | le plugin se charge, **n'écrit rien dans le jeu** ; l'onglet lit et règle la table du plugin ; les appels `hold` partent du script | 🟡 faible (code natif chargé dans le jeu ; retrait par une commande) |
| **B4 : `enabled=1`** sur un seul avion qui vole seul, loin du bateau | comme `RISQUES_v2.md` | 🟡 moyen (ÉCO) à moyen-élevé (FLANK) ; **seulement après avoir vu `HELD`** |

Pas de risque pour les sauvegardes de parties (essais en partie neuve jetable), pas de fuite de données (aucun accès réseau), dépendance inchangée : le chargeur du SDK sur l'ancien exe (voie A).

## Ce que montrera le premier lancement (A4), dans `cc2x.log`

1. `[modes] loaded v3.1; ini …\cc2x\modes.ini; observe only unless enabled=1; strict modes.ini; Lua cc2x.modes.set/get/hold/status` (si on lit encore `loaded v3;` c'est l'ancien plugin).
2. `[modes] session started`, puis `[modes] settings: enabled=0 … (observe only: nothing is written)`. **Aucune** ligne `modes.ini: …` avec le `modes.ini` actuel ; s'il y en a une, c'est une faute de frappe signalée une fois.
3. Des lignes d'observation `id N t=… NORMAL game_thr=… written=…` toutes les 5 s de jeu pour chaque avion en vol (`written` = `game_thr` : rien n'est écrit).
4. **Quand le moddeur prend un avion en main** : `[modes] id N: HELD, modes paused (the player is flying it by hand)`, puis `id N: no longer held …` environ 3 s après l'avoir lâché. **C'est la preuve attendue.** Si elle n'apparaît jamais, on **n'active rien** : on cherche pourquoi.
5. À l'écran, sous LOADOUT quand on clique un avion : l'onglet SPEED avec ECO / NORMAL / FLANK et la ligne **« OBSERVATION : SANS EFFET »** (jaune), puis « AUTONOMIE ~N min ». « PLUGIN PLEIN » n'apparaît qu'au 65e avion différent.

## Poser (quand le moddeur dit oui, jeu fermé), vérifier, revenir en arrière

```bash
python -I tour/etudes_modes_carburant/mod_modes.py mettre-a-jour --etape interface2_1   # onglet v2.1 (mods.xml intact)
python -I tour/etudes_modes_carburant/mod_modes.py mettre-a-jour-plugin                  # plugin v3 -> v3.1 (la v3.1 est la cible par défaut)
python -I tour/etudes_modes_carburant/mod_modes.py etat                                  # doit dire : onglet v2.1, plugin v3.1 conforme
```

**Retour à l'état actuel (onglet v2 + plugin v3), jeu fermé :**

```bash
python -I tour/etudes_modes_carburant/mod_modes.py mettre-a-jour --etape interface2
python -I tour/etudes_modes_carburant/mod_modes.py mettre-a-jour-plugin --version 3
```

Retrait complet : `… mod_modes.py retirer` (plugin + mod + ligne de `mods.xml`). Les DLL de référence v3 et v3.1 restent dans leurs dossiers de travail (hors dépôt, vérifiées par sha256 avant toute copie).

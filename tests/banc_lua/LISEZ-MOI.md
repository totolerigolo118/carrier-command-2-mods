# Banc Lua de Carrier Command 2 : les scripts de mod, hors du jeu, contre une fausse API

Ce dossier fait tourner **sans lancer le jeu** les scripts Lua de mod du dépôt, dans un vrai interpréteur Lua 5.3, contre une **fausse API** du jeu (callbacks `update`/`begin_load`,
véhicules, menu, `update_ui_event`, interface `g_ui`, table `cc2x` du SDK et plugin `cc2x.modes`). Chaque script a des scénarios automatiques (chargement, enchaînement d'images simulées,
assertions). Les bugs trouvés sont dans [`BUGS_TROUVES.md`](BUGS_TROUVES.md). **Aucun script source n'a été modifié.**

> **Ce que ce banc n'est pas** : une preuve que les scripts marchent *dans le jeu*. Il prouve leur logique contre ce que les documents du dépôt disent de l'API, et il dit clairement
> quand il a dû deviner. Voir « Ce que le banc ne peut pas vérifier ».

## Lancer

```bash
python tests/banc_lua/lancer.py
```

Ce qu'il fait, dans l'ordre (≈ 25 s) :
1. **contrôles statiques**, avec les outils maison du dépôt : syntaxe (`tour/outils/lua_syntaxe.py`, **et** le vrai compilateur Lua 5.3, qui doivent être d'accord), aucun
   `io`/`os`/`package`/`require`/`dofile`/`load`/`debug` dans les scripts, aucun nom inconnu de la fausse API (`tour/outils/lua_inconnus.py` adapté), et les 51 tests de `test_lua_syntaxe.py` ;
2. **tous les scénarios** (136 scénarios, 1 387 vérifications à la dernière exécution).

Il se termine par `TOUT EST OK` (code 0) ou `IL Y A DES ECHECS` (code 1). Code 2 : interpréteur Lua 5.3 introuvable.

| Option | Effet |
|---|---|
| `--filtre "BUG DEM-1"` | ne joue que les scénarios dont « groupe nom » contient ce texte |
| `--seulement sim_lib7,sorties_lib9` | ne charge que ces fichiers de `scenarios/` |
| `--lua CHEMIN` | interpréteur à utiliser (sinon variable d'environnement `LUA53`, sinon `lua5.3`, `lua53`, `lua` du PATH — il doit répondre `Lua 5.3`) |
| `--sans-statique` | saute les contrôles statiques |
| `--verbeux` | affiche aussi les notes des scénarios |
| `--mutations` | valide le banc lui-même (voir plus bas) ; plus long (≈ 2 min) |
| `--inventaire` | réécrit [`INVENTAIRE_API.md`](INVENTAIRE_API.md) (la liste des fonctions de la fausse API et leur statut) |

Le banc seul, sans Python : `lua5.3 tests/banc_lua/banc.lua . [--filtre texte]` depuis la racine du dépôt.

Lecture de la sortie : `OK` = scénario passé ; `ECHEC` = une vérification est fausse ; `* BUG …` / `* RISQUE … reproduit` = un défaut **connu et épinglé** (le test *passe* tant que le
défaut est là ; s'il disparaît parce que le script a été corrigé, le test devient `ECHEC … NON REPRODUIT` pour rappeler de mettre à jour `BUGS_TROUVES.md`).

## Dépendances et version de Lua visée

- **Python 3.8+**, bibliothèque standard seulement (pas de `pip`, pas de `lupa`, pas de réseau). Les `.py` du banc n'écrivent rien dans le dépôt, sauf `--inventaire` (un fichier).
- **Un interpréteur Lua 5.3** (programme `lua5.3` / `lua53.exe`). C'est la seule dépendance.
- **Version visée : Lua 5.3.** Déduit de :
  - `partage_detail/07_lua_api_and_hooks.txt` : « The game embeds Lua 5.3.5 » ; bibliothèques ouvertes : base, debug, math, string, table, utf8 (**pas** de io, os, package, coroutine) ;
  - `passation_windows/sdk_public_cc2x/README.md` : le SDK utilise « the game's own Lua 5.3 internals » ; et `src/cc2x.c:620-627` lit des entiers *et* des flottants (étiquettes `0x13`/`0x03`), ce
    qui n'existe qu'à partir de Lua 5.3 ;
  - `outil/tests_en_jeu/sonde_api_lua.lua` relève `_VERSION`, `string.pack` et `utf8` dans chaque écran (les résultats de cette sonde ne sont pas conservés dans le dépôt).
- **Pas sûr** : la version corrective exacte (le jeu : 5.3.5 ; le banc a été exécuté ici avec **Lua 5.3.6**, Ubuntu 24.04 ; les deux n'ont que des corrections de bogues en commun, mais je n'ai pas
  pu comparer) et les options de compilation du jeu (`LUA_COMPAT_*` : présence de `unpack`, `loadstring`… dans le jeu non établie ; les scripts écrivent `table.unpack or unpack`, donc ça ne compte
  pas pour eux).
- **Les autres versions sont refusées** (`_VERSION` ≠ `Lua 5.3`, message clair, code 2) : en 5.1/5.2 `string.format("%d", 3.5)` ne lève pas d'erreur et les entiers n'existent pas ; en 5.4 le
  comportement de certains cas limites change. `BANC_LUA_TOLERER_VERSION=1` force quand même (à vos risques).

### Ce que j'ai fait dans le cloud (et pourquoi c'est sans danger notable)

Le conteneur n'avait ni Lua ni `lupa`. J'ai installé **un seul paquet** : `apt-get install lua5.3` (dépôt Ubuntu 24.04 `archive.ubuntu.com`, paquet signé par Ubuntu, aucune dépendance en plus,
version 5.3.6-2build2). Je l'ai signalé avant. Risques résiduels : les scripts d'installation d'un paquet s'exécutent en root *dans ce conteneur éphémère* ; le trafic part par le proxy de la session
vers ce seul dépôt. **Rien n'a été installé sur le PC du moddeur, aucun paquet PyPI, pas de `lupa`**. Rien dans le banc ne lit ni n'écrit hors du dépôt (les mutations travaillent sur des copies
dans le dossier temporaire du système) ; le banc n'ouvre aucune connexion réseau.

### Côté PC du moddeur (Python avec capstone/numpy, pas de Lua)

Il faut **un `lua.exe` qui répond `Lua 5.3`**. Le `lua51.dll` d'OBS Studio (utilisé par `tour/outils/lua_sonde.py`) est un **Lua 5.1** : il ne convient pas, et c'est une DLL, pas un programme.
Trois voies, du plus au moins « fait maison » — **chacune demande l'accord du moddeur avant d'agir, et voici le risque de chacune** :

1. **Compiler le source officiel de Lua 5.3.x** (archive `lua-5.3.x.tar.gz` de lua.org, ≈ 300 Ko, dont la somme SHA-256 est publiée sur lua.org/ftp : la comparer avant de compiler) avec un compilateur C
   déjà présent (Zig, gcc ou MSVC) : compiler tous les `src/*.c` **sauf `luac.c`** en un `lua.exe`. *Risque* : un téléchargement (réseau) d'un tarball ; le code est petit et lisible, la somme publiée permet de
   vérifier qu'il n'a pas été altéré. *Je n'ai pas essayé cette compilation* (pas de téléchargement de ma part).
2. **Un binaire déjà compilé** (par exemple les « LuaBinaries » de SourceForge, ou `scoop install lua` / `choco install lua`). *Risque* : on exécute un programme tiers, non vérifié par le moddeur ; à décider par le moddeur.
3. **WSL ou un Linux / Mac sous la main** : `apt install lua5.3` / `brew install lua@5.3` (même risque que ci-dessus, paquet signé de la distribution).

Ensuite : `set LUA53=C:\chemin\lua.exe` puis `python tests\banc_lua\lancer.py` (ou `--lua C:\chemin\lua.exe`). Le banc est écrit pour tourner sous Windows aussi (chemins avec `/`, pas de commande
Unix) mais **je n'ai pu l'exécuter que sous Linux** : le premier lancement sous Windows est une vérification en soi.

## Contenu du dossier

| Fichier | Rôle |
|---|---|
| `lancer.py` | lanceur (statique + scénarios + mutations + inventaire), Python standard seulement |
| `banc.lua`, `compiler.lua` | point d'entrée Lua du banc ; compilation sans exécution (contrôle de syntaxe) |
| `fausse_api/api_jeu.lua` | **la fausse API** : environnement global d'un écran, fonctions `update_*` par type d'écran |
| `fausse_api/jeu.lua` | le « jeu » : horloge (30 ticks par seconde), monde, événements reçus, mots de passe, planning |
| `fausse_api/objets.lua` | poignées de véhicule (`v:get()`, `v:get_dock_state()`, `v:add_waypoint()`…) |
| `fausse_api/ui.lua` | fausse `g_ui` (fenêtres, piles, boutons) pour l'onglet SPEED |
| `fausse_api/cc2x.lua` | fausse table `cc2x` (SDK 0.4.0 documenté, 0.5.0 supposé) et plugin `cc2x.modes` (contrat lu dans `cc2x_modes.c`) |
| `fausse_api/contexte.lua` | un écran = un état Lua séparé ; ordre de chargement ; liaison de l'API ; images |
| `fausse_api/ecrans/*.lua` | faux scripts d'écran du jeu (contrôle des véhicules, menu, overlay, indications) — ne contiennent que ce dont les scripts du dépôt dépendent |
| `fausse_api/comportements.lua` | une flotte de test, avions « dociles » (délais mesurés du dépôt) |
| `fausse_api/cadre.lua`, `aides.lua`, `onglet.lua`, `inventaire.lua` | cadre de test, aides, pilotage de l'onglet, registre des statuts |
| `scenarios/*.lua` | les scénarios, un fichier par script (+ `ensemble_ecran_de_bord`, `fausse_api_elle_meme`) |
| `INVENTAIRE_API.md` | généré : chaque fonction de la fausse API avec son statut DOC / SCRIPT / SUPPOSÉ |
| `BUGS_TROUVES.md` | les 8 bugs et 16 risques trouvés (dont 1 non épinglé), avec fichier:ligne et scénario |

## Ce que chaque script a comme scénarios

| Script | Scénarios (extraits) |
|---|---|
| `tour/lua/library_custom_7.lua` (SIM) | chargement dans 4 ordres ; seulement `screen_veh_l/m/r` ; transparence de l'enveloppe (retours avec `nil`) ; mesure x1.00 / x2.00 / x0.50 / x1.33 sur fenêtres de 10 s ; pause ; retour en arrière ; écran trop étroit ; erreurs de dessin/horloge |
| `tour/lua/library_custom_9.lua` (SORTIES) | sortie de 4 avions (étapes dans l'ordre, « FINI en 2:15 », écart moyen) ; affichage 2 min puis disparition ; avions et hélicoptères ; abandon / ordre redonné / appareil détruit ; liens « rattaché » et « accosté » ; appareil d'un autre bateau |
| `tour/auto/library_custom_5.lua` (essai auto) | menu : un seul `load_game` après 28 s, verrou entre contextes, slot absent ; partie : mission complète attente > sortie > retour > fin avec ordres exacts, `quit_game` une fois ; échecs (pas d'avion, ordres refusés, avions qui restent au hangar : 8 renouvellements) ; overlay et surveillance de `update` ; « boîte aux lettres » ≤ 480 caractères sans `< > & "` |
| `tour/etudes_demarrage_auto/demarrage_auto.lua` | étapes dans l'ordre (accroche, interrupteur, compte à rebours 30 s, **une** commande, message) ; mode « charger » ; `g_da_attente`, `g_da_attendre_menu` ; plusieurs contextes ; mod décoché / absent / illisible |
| `.../lua/library_custom_3.lua` (télémétrie) | en-tête une fois, mesure toutes les 150 ticks, format identique au journal réel du 28/10, 14 avions = 3 lignes < 900 caractères, erreurs avalées une fois, retour en arrière du tick, barrière `cc2x.api >= 4` |
| `.../lua/library_custom_5.lua` (onglet v1) | géométrie sous LOADOUT ; seulement les avions de l'équipe ; boutons ; **ne commande rien** ; reprise sur erreur (piles rendues, onglet coupé) |
| `.../lua/v2/library_custom_5.lua` (onglet v2) | **valeurs envoyées bornées** (600 clics au hasard) ; correspondance ECO→1 / NORMAL→0 / FLANK→2 ; états OBSERVATION / ACTIF / EN ATTENTE / PILOTE ; autonomie 0–120 min ; garde-fou `hold` ; plugin qui plante / répond de travers ; partage entre les 3 écrans |
| tous ensemble | 48 combinaisons d'ordre de 4 scripts sur le même écran ; collisions de noms globaux ; un script qui plante ne prive pas les autres |

## Ce qui est simulé et à quel point on peut s'y fier

Chaque fonction de la fausse API a un **statut** (liste complète : [`INVENTAIRE_API.md`](INVENTAIRE_API.md)) :

- **DOC** : écrit dans la documentation du dépôt (`LUA_API.md`, `WORLD_API.md`, `partage_detail/07`, `03`, `08`, notes de passation, source du plugin `cc2x_modes.c`) ;
- **SCRIPT** : pas documenté, mais un script du dépôt l'appelle : on connaît la *forme* de l'appel, le comportement est deviné ;
- **SUPPOSÉ** : rien ne l'établit ; choix du banc pour pouvoir faire tourner le script.

Les suppositions qui comptent le plus (chacune est signalée `SUPPOSE`/`SUPPOSÉ` dans le code) :

1. **Quand l'API est liée** : au premier `begin_load()` (d'après `outil/tests_en_jeu/LISEZ-MOI.txt`), sauf l'overlay, où `begin_load` n'est jamais appelé. Le banc place la liaison *dans* `begin_load`.
2. **Ordre de chargement** : `partage_detail/07` dit que les `library_custom_N` sont chargés *après* le script d'écran, d'autres commentaires du dépôt (sonde, essai auto) disent *avant*. Les deux
   sont essayés partout (`libs APRES / AVANT l'ecran`).
3. **Quelle API chaque type d'écran possède** : établi seulement pour l'overlay et l'écran d'indications (pas d'API du monde, mesure du 27/10). Le reste est une proposition raisonnable.
4. **`update(screen_w, screen_h, tick_fraction, delta_time)`**, `delta_time` en millisecondes ; écrans de bord 256 × 256, menu et overlay 1920 × 1080 ; police de 5 × 9 par caractère (la même doublure que
   `tests/test_horloge.py`).
5. **Les poignées de véhicule** : jamais `nil` ; lire un véhicule disparu lève une erreur (force les scripts à tester `v:get()`) ; « pas de parent / baie vide » vaut `-1`.
6. **`g_ui`** : tout est déduit de l'usage qu'en font les deux onglets (`window_stack`, `region_stack`, `begin_window`, `hoverable`, `text_basic`…).
7. **`cc2x` 0.5.0** : `cc2x.tick()` et les champs `is_wing`, `flight_state`, `speed`, `control_speed`, `control_power` sont *déduits* de `library_custom_3.lua` et de `ETUDE.md` annexe B ; la doc 0.5.0 n'est pas dans le dépôt.
8. **`get_linear_speed` / `get_throttle_factor`** : le journal réel du 28/10 les montre à `-` dans 96 % des lignes et numériques dans 4 % (contexte non identifié). Le banc prend le cas majoritaire (absentes).
9. **Un `update_ui_event` n'a aucun effet de jeu** : la partie ne se charge pas, le menu reste ; on vérifie seulement *quelle* commande part, *quand* et *combien de fois*.
10. **Les avions « dociles »** copient les délais mesurés du dépôt (4 avions en l'air en 4048 ticks ; piste toutes les 1:31, approche 0:49, pont → hangar 0:51). Ce sont des repères, pas une simulation du moteur.
11. **Une erreur levée par `update`** est capturée par le banc (`ctx.erreurs`) ; ce que fait le vrai jeu d'une telle erreur est inconnu.

Contrôles de fidélité : `scenarios/fausse_api_elle_meme.lua` (11 scénarios) vérifie la fausse API elle-même — horloge, liaison au `begin_load`, profils, vérification des types des arguments, contrat de
`cc2x.modes` (bornes, 64 avions, 90 ticks de garde), `cc2x.log` (900 caractères), fenêtres de `g_ui`.

## Ce que le banc NE PEUT PAS vérifier (comportement réel du moteur)

Un test vert veut dire « le script se comporte bien **dans ce modèle** ». Restent hors de portée d'un banc sans le jeu (et d'une session cloud, qui n'a ni Steam ni les fichiers du jeu) :

- **Le moteur lui-même** : fréquence réelle d'appel de `update`, valeurs et unités de `tick_fraction`/`delta_time` (`refresh_interval="1"` non vérifié), ordre réel de chargement des scripts, ce que
  le jeu fait d'une erreur Lua dans `update`, un seul fil ou plusieurs (la doc du SDK dit que les fonctions Lua tournent sur un autre fil que le serveur).
- **Que les fonctions existent et font ce que dit la fausse API** pour tout ce qui est SCRIPT ou SUPPOSÉ (voir l'inventaire) — notamment `g_viewing_vehicle_id`, `window_stack`/`region_stack`, `get_attached_parent_id`, `update_set_host_password`.
- **Que les ordres de vol servent à quelque chose** : le banc ne sait pas qu'un `add_waypoint` fait décoller un avion ou qu'un `set_target_vehicle` le rappelle (établi en jeu le 25/10 d'après les notes, pas ici).
- **Le plugin C `cc2x_modes.dll`** : il n'est pas exécuté. Le banc vérifie ce que l'onglet *envoie* (`set`/`hold`, types et bornes), jamais que ÉCO ou FLANK modifient réellement les gaz, ni que `hold`
  protège l'avion piloté à la main (voir ONG-R1/ONG-R2 dans les bugs : c'est le point de sécurité à tester en jeu).
- **Le SDK CC2X** (`dinput8.dll`) : sa table `cc2x` est celle de la fausse API ; le SDK est de plus **inactif sur le nouvel exécutable** (mise à jour Steam du 28/10, `tour/etude_mise_a_jour/ETUDE.md`).
- **Le nouvel exécutable et les scripts de `rom_0` mis à jour** : toutes les mesures du dépôt sont de l'ancien build ; le banc n'en sait rien.
- **L'affichage** : aucune vérification visuelle (position réelle des textes, chevauchements, lisibilité, couleurs, manette). Il vérifie des coordonnées dans un modèle de police inventé.
- **La charge** : coût CPU en jeu, nombre d'écritures disque réel (voir AUTO-R3).
- **Plusieurs joueurs, sauvegardes/chargements, autres mods** (Revolution remplace des écrans entiers ; les `library_custom_N` des mods s'écrasent entre eux par numéro de slot) : non simulés.
- **Lua 5.3.5 exact et les options de compilation du jeu** (voir plus haut).

## Valider le banc lui-même (mutations)

`python tests/banc_lua/lancer.py --mutations` copie les 7 scripts dans un dossier temporaire, y introduit **un défaut volontaire à la fois** (une constante changée, un `pcall` retiré, un test inversé…,
39 cas listés dans `lancer.py`) et vérifie que le banc devient rouge. Un mutant qui « survit » signale un scénario trop faible ; la première version du banc en laissait survivre 4 sur 39 : trois scénarios ont été ajoutés
(erreur interne de l'essai auto, barrière d'API de la télémétrie, région d'interface laissée ouverte) et une mutation mal ciblée (elle touchait un commentaire) a été corrigée. Un mutant qui boucle à l'infini est arrêté
par un délai de 120 s et compte comme tué. Résultat de la dernière exécution : voir la fin de ce fichier.

**Relecture indépendante.** En plus des scénarios, les sept scripts ont été relus par un autre agent à qui je n'avais donné que le code (pas ma liste). Ses dix points ont chacun été revérifiés : sept ont été reproduits dans le banc
et ajoutés à `BUGS_TROUVES.md`, un l'a été comme risque non épinglable (conflits de slots), deux ont été écartés faute de preuve (section « Points examinés et écartés »).

## Ajouter ou modifier un scénario

1. Écrire dans `scenarios/<script>.lua` : `cadre.groupe("nom", function() cadre.scenario("nom", function(t) … end) end)` ; `t:verifier(cond, msg)`, `t:egal(obtenu, attendu, msg)`.
2. Pour épingler un défaut : `t:bug("ID", "titre", function() return reproduit, detail end)` ou `t:risque(...)`, puis décrire l'entrée dans `BUGS_TROUVES.md`.
3. Monter un écran : `Contexte.nouveau(jeu, { nom = "screen_veh_m", profil = "bord", vehicule_ecran = 1, cc2x = {niveau = "0.5", plugin_modes = true} })` puis `ctx:monter({ ecran = "bord_controle", libs = {"chemin/du/script.lua"}, ordre = "apres" })` ; `jeu:jouer(10)` joue 10 s réelles à 30 images par seconde.
4. Si un script du dépôt change : relancer `python tests/banc_lua/lancer.py` ; les tests de défauts connus diront lesquels ont été corrigés ; `--mutations` signalera les motifs devenus introuvables.

Rien ici ne remplace un essai en jeu : les fiches `PASSATION.md` des dossiers d'étude disent lesquels sont à faire et dans quel ordre.

## Dernière exécution (cloud, 29/10/2026)

- Interpréteur : Lua 5.3.6 (`apt install lua5.3`, Ubuntu 24.04) ; Python 3.13.
- `python tests/banc_lua/lancer.py` : contrôles statiques tous OK ; **136 scénarios OK, 0 en échec, 1 387 vérifications**, 23 défauts connus reproduits (8 bugs + 15 risques épinglés ; un 16ᵉ risque, ENS-R2, n'est pas épinglable ; voir `BUGS_TROUVES.md`) ; ≈ 25 s.
- `python tests/banc_lua/lancer.py --mutations` : **39 mutations sur 39 détectées**, 0 survivante.
- Non exécuté : sous Windows, avec Lua 5.3.5, et en jeu.


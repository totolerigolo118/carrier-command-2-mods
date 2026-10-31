# Bugs et risques trouvés par le banc Lua dans les scripts du dépôt

Aucun script source n'a été modifié (consigne). La liste vient de ma relecture + des scénarios, puis d'une **relecture indépendante** par un autre agent à qui je n'avais donné que le code ; chacun de ses points a été revérifié (reproduit dans le banc, ou écarté, voir « Points examinés et écartés »). Chaque entrée dit **où** (fichier:ligne), **quel scénario** le reproduit, **ce qui se passe**, et — séparément — une
**piste de correction** que personne n'a appliquée.

**Comment lire cette liste.**
- **BUG** : comportement du script lui-même, reproduit par le banc dans le modèle de jeu documenté. Il ne dépend que d'hypothèses faibles sur le moteur.
- **RISQUE** : le script se comporte comme décrit **si** une hypothèse sur le vrai moteur est juste. Le banc montre la conséquence ; seul un essai en jeu dit si l'hypothèse est vraie.
- Chaque entrée est **épinglée** par un test (`t:bug(...)` / `t:risque(...)`) : il passe tant que le défaut est là. Si le script est corrigé, le test devient rouge avec
  « NON REPRODUIT » : il faut alors mettre à jour ce fichier et le test.
- Rejouer une entrée : `python tests/banc_lua/lancer.py --filtre "BUG DEM-1"` (le filtre est le début du nom du scénario).

| Id | Type | Gravité | Où | En une ligne |
|---|---|---|---|---|
| [DEM-1](#dem-1) | BUG | moyenne | `tour/etudes_demarrage_auto/demarrage_auto.lua:60,68` | « Décocher le mod pour annuler » n'annule rien pendant le compte à rebours |
| [DEM-2](#dem-2) | BUG | faible | `tour/etudes_demarrage_auto/demarrage_auto.lua:36-46` | Mode « charger » avec une sauvegarde absente : échec totalement silencieux |
| [AUTO-2](#auto-2) | BUG | faible | `tour/auto/library_custom_5.lua:354-369,450` | Un écran qui se croit « passif » à 1800 ticks le reste pour toujours |
| [AUTO-1](#auto-1) | BUG | faible | `tour/auto/library_custom_5.lua:29,465-469,525` | Bande rouge de calibrage (`AFFICHER_NOMS = true`) dessinée sur tous les écrans |
| [AUTO-3](#auto-3) | BUG | cosmétique | `tour/auto/library_custom_5.lua:322-346,539-545` | Le panneau de l'overlay affiche « attente tick 0 » en permanence, forcé visible |
| [SORT-1](#sort-1) | BUG | cosmétique | `tour/lua/library_custom_9.lua:107-109,130` | Si tous les ordres sont annulés : « 0/N EN L'AIR : FINI » en vert |
| [SIM-1](#sim-1) | BUG | cosmétique | `tour/lua/library_custom_7.lua:23-26` | Après un rechargement, l'ancienne valeur « SIM x… » reste affichée jusqu'à 10 s |
| [ONG-1](#ong-1) | BUG | faible | `tour/etudes_modes_carburant/lua/v2/library_custom_5.lua:132-136` | Le retour de `set()` est ignoré : refus du plugin = bouton qui clignote, sans message |
| [ONG-R1](#ong-r1) | RISQUE | **élevée** si vrai | `tour/etudes_modes_carburant/lua/v2/library_custom_5.lua:202` | Le garde-fou « le joueur pilote » peut ne jamais être installé |
| [ONG-R2](#ong-r2) | RISQUE | moyenne | `tour/etudes_modes_carburant/lua/v2/library_custom_5.lua:53-57,204-208` | Le garde-fou a une image de retard à la prise en main |
| [AUTO-R3](#auto-r3) | RISQUE | moyenne | `tour/auto/library_custom_5.lua:408,414,455-456` | Le mot de passe d'hébergement change 30 fois par seconde |
| [AUTO-R4](#auto-r4) | RISQUE | faible | `tour/auto/library_custom_5.lua:419,456-460` | Si `quit_game` est ignoré, le chat reçoit un paquet de messages toutes les 5 s sans fin |
| [DEM-R1](#dem-r1) | RISQUE | moyenne | `tour/etudes_demarrage_auto/demarrage_auto.lua:34-36` | « Une partie par lancement » repose sur la survie du mot de passe de connexion |
| [DEM-R2](#dem-r2) | RISQUE | moyenne | `tour/etudes_demarrage_auto/demarrage_auto.lua:60-61` | Interrupteur lu « absent » à la 1re image = démarrage abandonné pour toujours, sans message |
| [MES-R1](#mes-r1) | RISQUE | faible | `tour/etudes_modes_carburant/lua/library_custom_3.lua:68` | `cc2x.vehicles(équipe)` n'est pas documenté (argument peut-être ignoré) |
| [MES-R2](#mes-r2) | RISQUE | faible | `tour/etudes_modes_carburant/lua/library_custom_3.lua:64-68,120-135` | Un état Lua sans numéro d'équipe journalise toutes les équipes |
| [MES-R3](#mes-r3) | RISQUE | faible | `tour/etudes_modes_carburant/lua/library_custom_3.lua:68` | L'idiome `a and f(x) or f()` bascule sur toutes les équipes si `f(x)` renvoie nil |
| [MES-R4](#mes-r4) | RISQUE | faible | `tour/etudes_modes_carburant/lua/library_custom_3.lua:128` | `update = function(...)` fait passer `nparams` de 7 à 0 sur l'écran de pilotage |
| [ENS-R1](#ens-r1) | RISQUE | faible | `tour/etudes_demarrage_auto/demarrage_auto.lua:19,35-36` + `tour/auto/library_custom_5.lua:32,517-519` | Deux verrous différents : les deux outils se marchent dessus s'ils sont installés ensemble |
| [ENS-R2](#ens-r2) | RISQUE | moyenne | `tour/outils/essai_auto.py:608-609,633` + `tour/etudes_demarrage_auto/ETUDE.md:44` | Conflits de numéros de `library_custom_N` : un script écrase l'autre (**non épinglé** par le banc) |
| [ENS-R3](#ens-r3) | RISQUE | faible | `tour/lua/library_custom_9.lua:167-168` | Le panneau SORTIES (haut à droite) recouvre LOADOUT, et SPEED au-delà de 4 appareils |
| [SORT-R2](#sort-r2) | RISQUE | faible | `tour/lua/library_custom_9.lua:16-50` | Pas de réinitialisation quand le tick recule (contrairement à `library_custom_7` et `_3`) |
| [AUTO-R2](#auto-r2) | RISQUE | faible | `tour/auto/library_custom_5.lua:224-225` | Après un échec de sortie, les avions déjà en l'air ne sont pas rappelés |
| [AUTO-R1](#auto-r1) | RISQUE | faible | `tour/auto/library_custom_5.lua:476-483` | Branche HUD : `ca_image` reçoit peut-être `tick_fraction` à la place de `delta_time` |

---

## Bugs

### DEM-1
**`tour/etudes_demarrage_auto/demarrage_auto.lua:60` et `:68`** — scénario `BUG DEM-1` (`scenarios/demarrage_auto.lua`).
Le compte à rebours affiche `DEMARRAGE AUTO dans N s (decocher le mod "Demarrage auto" pour annuler)`. Mais l'interrupteur n'est lu qu'**une fois**, à la
première image (`if g_da_arme == nil then g_da_arme = da_arme() end`) ; ensuite `g_da_arme` est mémorisé et la liste des mods n'est plus relue.
**Scénario** : mod coché → compte à rebours à 5 s → le mod est décoché (`update_get_mod_details` rend alors `is_enabled = false`) → 30 s plus tard `new_game_custom` part quand même.
**Conséquence** : la promesse affichée à l'écran est fausse (que le menu des mods mette à jour `is_enabled` en direct ou non : dans le premier cas le script l'ignore, dans le second le texte
ment). Un utilisateur qui change d'avis perd sa partie en cours de menu.
*Piste (non appliquée)* : relire `da_arme()` à chaque image du compte à rebours (c'est un simple appel de lecture), ou retirer la phrase « pour annuler ».

### DEM-2
**`tour/etudes_demarrage_auto/demarrage_auto.lua:36-46`** — scénario `BUG DEM-2`.
En mode `"charger"`, si la sauvegarde demandée n'existe pas dans `update_get_save_slots()` (ou si la liste est illisible), `da_demarrer()` sort **sans rien dire** : le verrou est quand
même posé (ligne 36), `g_da_fini` est vrai, aucun message n'est affiché (le message « commande envoyee » n'apparaît que si `g_da_envoye`) et le compte à rebours a disparu.
**Conséquence** : l'utilisateur voit le compte à rebours s'arrêter et rien d'autre — impossible de distinguer « ça charge » de « ça a échoué ».
*Piste* : afficher « sauvegarde N absente » (comme `g_ca.menu = "slot N absent"` dans `tour/auto/library_custom_5.lua:70`).

### AUTO-2
**`tour/auto/library_custom_5.lua:354-369` et `:450`** — scénario `BUG AUTO-2`.
`ca_logique` fait `if t >= ATTENTE_JEU and not ca_est_chef() then s.etat = "passif"; return end`. Si `update_get_screen_vehicle()` n'est pas valide **à cet instant**,
`ca_est_chef()` renvoie `false` (ligne 358) *sans mémoriser* le résultat, mais l'état est quand même passé à `"passif"`, et plus loin
(`s.etat ~= "passif"`, ligne 451) `ca_pas` ne tourne plus jamais pour cet écran, même quand le vaisseau de l'écran redevient valide.
**Scénario** : vaisseau d'écran invalide jusqu'au tick 1850, valide ensuite → à 4000 ticks, état `passif`, 0 ordre donné.
**Conséquence** : l'essai automatique ne démarre pas, sans message (l'état « passif » est aussi celui des autres porte-avions). Peu probable (30 s de jeu après le chargement), mais le
défaut est dans la logique, pas dans les données.
*Piste* : ne passer à `"passif"` que si `ca_est_chef()` a répondu `false` de façon définitive (mémorisée), pas sur une lecture invalide.

### AUTO-1
**`tour/auto/library_custom_5.lua:29`, `:465-469`, `:525`** — scénario `BUG AUTO-1`.
`AFFICHER_NOMS = true` (réglage de calibrage, commenté « calibrage : bande rouge + repère… ») est resté actif : tant que le script est installé, chaque écran accroché dessine un
rectangle rouge (200, 0, 0) de 14 de haut en bas de l'écran et un texte `ca[...]:nom #n`.
**Conséquence** : bande rouge visible sur tous les écrans du jeu pendant un essai. Voulu pendant le calibrage ; à couper avant tout autre usage.
*Piste* : passer la constante à `false` (ou la lire dans `g_ca_afficher_noms or false` comme les autres réglages).

### SORT-1
**`tour/lua/library_custom_9.lua:107-109` et `:130`** — scénario `BUG SORT-1`.
Une sortie est déclarée terminée dès que plus aucun appareil n'est « à attendre » (`reste == 0`), y compris quand **tous** les ordres ont été annulés (appareils revenus au hangar,
marqués `abandon`). La ligne finale devient verte : `0/2 EN L'AIR : FINI en 0:01`.
**Conséquence** : affichage trompeur (vert, « FINI ») alors que rien n'a décollé. Sans effet sur le jeu.
*Piste* : n'écrire « FINI » que si `en_vol > 0` ; sinon effacer la sortie.

### SIM-1
**`tour/lua/library_custom_7.lua:23-26`** — scénario `BUG SIM-1`.
Quand le tick revient en arrière (chargement d'une autre partie), la branche de réinitialisation remet `tick0`/`reel0` mais **pas** `v.vitesse`. L'ancienne valeur (par exemple `SIM x2.00`)
reste affichée jusqu'à la fin de la première fenêtre de 10 s de la nouvelle partie.
**Conséquence** : valeur périmée pendant ≤ 10 s ; purement cosmétique.
*Piste* : `v.vitesse = nil` dans la branche de réinitialisation.

### AUTO-3
**`tour/auto/library_custom_5.lua:322-346` (`ca_image`) et `:539-545`** — scénario `BUG AUTO-3` (trouvé par la relecture indépendante, reproduit).
L'overlay n'a pas l'API du monde (le commentaire des lignes 349-350 : mesure du 27/10), donc `ca_ticks()` y vaut `nil` et `ca_pas` n'y tourne jamais. Mais le script y dessine quand même son panneau
et le force visible (`update_set_is_visible(true)`, ligne 332) à chaque image après le premier chargement : il affiche `ESSAI AUTO cc2_auto : attente   tick 0 (0:00)` pour toute la session, pendant que
l'essai se déroule sur l'écran de bord.
**Conséquence** : sur une capture d'écran, un panneau « attente » contredit l'essai réel (le script note lui-même que les résultats sortent sur `screen_veh_m` et dans le chat).
*Piste* : ne pas accrocher l'overlay (supprimer `ca_guetter`) ou ne dessiner que si `ca_ticks()` n'est pas `nil`.

### ONG-1
**`tour/etudes_modes_carburant/lua/v2/library_custom_5.lua:132` et `:136`** — scénario `BUG ONG-1` (trouvé par la relecture indépendante, reproduit).
Le script fait `pcall(cc2x.modes.set, id, MODE_PLUGIN[i])` puis `bouton = i` sans lire le résultat. Le plugin refuse (`false`) quand sa table de 64 avions est pleine (`cc2x_modes.c:65,414-431`) ; or
**chaque clic sur un nouvel avion y prend une entrée, même un clic NORMAL**, et la table n'est vidée qu'en fin de session. Au 65e avion distinct, le bouton cliqué s'allume pendant l'image du clic
puis l'onglet repasse à NORMAL, sans message. (La v1 n'a pas ce défaut : elle ne parle pas au plugin.)
**Conséquence** : l'utilisateur croit avoir réglé ECO ou FLANK ; rien n'est appliqué. Rare (64 avions distincts cliqués dans une session).
*Piste* : lire le retour de `set` ; en cas de `false`, afficher « PLUGIN PLEIN ».

---

## Risques (dépendent d'une hypothèse sur le vrai moteur)

### ONG-R1
**`tour/etudes_modes_carburant/lua/v2/library_custom_5.lua:202`** — scénario `RISQUE ONG-R1`.
`envelopper_update()` n'installe le garde-fou « le joueur pilote » (`cc2x.modes.hold(g_viewing_vehicle_id)` à chaque image) que si `type(g_viewing_vehicle_id) == "number"`
**au moment du `begin_load`**. Sinon il revient sans rien faire et ne réessaie qu'au prochain `begin_load`.
**Hypothèse** : le vrai `screen_vehicle_control.lua` définit `g_viewing_vehicle_id` avant la fin de `begin()`. Rien dans le dépôt ne l'établit (le module vitesse du Mac écrit
`type(g_viewing_vehicle_id) == "number" and …`, ce qui suggère qu'il peut être `nil`).
**Si elle est fausse** : `hold()` n'est **jamais** appelé, et le plugin peut écrire les gaz de l'avion que le moddeur pilote (c'est précisément ce que la PASSATION interdit : « ne jamais mettre en
mode l'avion que le moddeur pilote tant que HELD n'a pas été vu »).
**À vérifier en jeu** : `cc2x.log` doit montrer `id N: HELD` dès qu'on prend un avion en main. Le banc ne peut pas le savoir.
*Piste* : tester `g_viewing_vehicle_id` à chaque image dans le wrapper (au lieu d'une fois au `begin_load`), ou installer le wrapper sans condition.

### ONG-R2
**`tour/etudes_modes_carburant/lua/v2/library_custom_5.lua:53-57` et `:204-208`** — scénario `RISQUE ONG-R2`.
Le wrapper appelle `pcall(cm_hold)` **avant** `origine(...)` : il lit donc le `g_viewing_vehicle_id` de l'image précédente. À l'image où le joueur prend l'avion, l'avion n'est pas encore « tenu » ;
il l'est à l'image suivante (garde de 90 ticks ensuite).
**Hypothèse** : c'est `update()` de cet écran qui change `g_viewing_vehicle_id`, et la fréquence d'`update` est celle d'une image (la fiche dit seulement `refresh_interval="1"`, non vérifié).
**Si vrai** : pendant une image (voire davantage si l'écran est rafraîchi lentement), un avion en ECO que le joueur vient de prendre peut encore recevoir un plafond de gaz.
*Piste* : appeler `cm_hold` après `origine(...)` (ou avant **et** après).

### AUTO-R3
**`tour/auto/library_custom_5.lua:408`, `:414`, `:455-456`** — scénario `RISQUE AUTO-R3`.
`ca_chat` appelle `ca_mail` à **chaque image**, qui appelle `update_set_host_password(texte)` avec un texte contenant le tick : **30 valeurs différentes par seconde** (mesuré dans le banc).
**Hypothèse** : le jeu enregistre le mot de passe d'hébergement dans `persistent_data.xml` à **chaque changement** (le commentaire du script, lignes 371-372, dit que l'orchestrateur le lit
« pendant la partie » dans ce fichier). Le dépôt ne dit pas combien d'écritures le jeu fait réellement ni si un essai long a été fait avec ce canal.
**Si vrai** : une écriture disque par image pendant tout l'essai ; au minimum de la charge, au pire un ralentissement du jeu.
*Piste* : n'écrire que si le texte (sans le tick) a changé, ou au plus une fois par seconde.

### DEM-R1
**`tour/etudes_demarrage_auto/demarrage_auto.lua:34-36`** — scénario `RISQUE DEM-R1`.
« Un seul essai par lancement du jeu » repose sur le mot de passe de connexion, qui sert de verrou (`VERROU`). Au retour au menu, l'état Lua est neuf (`g_da_fini` repart de `nil`) :
seul le verrou empêche une 2e partie.
**Hypothèse** : le jeu ne remet pas ce mot de passe à zéro en lançant une partie ni en revenant au menu.
**Si fausse** : chaque retour au menu relance une nouvelle partie 30 s plus tard (le banc montre 2 commandes au total).
**À vérifier en jeu** : lancer une partie, revenir au menu, attendre 40 s.

### MES-R1
**`tour/etudes_modes_carburant/lua/library_custom_3.lua:68`** — scénario `RISQUE MES-R1`.
Le script appelle `cc2x.vehicles(equipe)`. La doc du dépôt (`passation_windows/sdk_public_cc2x/LUA_API.md`, SDK 0.4.0) ne connaît que `cc2x.vehicles()` sans argument ; la doc du SDK 0.5.0
(137 lignes) n'est pas dans le dépôt.
**Si l'argument est ignoré** : les avions de l'IA sont journalisés comme « de ton équipe » (le banc : `9,12`). Le journal du 28/10 contient les avions 9, 10, 17, 18 et 103 ; rien dans
le CSV n'indique l'équipe du 103 (apparu au tick ~21 850), donc il ne tranche pas.
**À vérifier** : lire `LUA_API.md` du commit `7ab05c7` du SDK, ou une mesure avec un avion de l'IA en l'air.

### MES-R2
**`tour/etudes_modes_carburant/lua/library_custom_3.lua:64-68` et `:120-135`** — scénario `RISQUE MES-R2`.
Le script s'accroche à `begin_load` de **tous** les écrans. Dans un état Lua sans `update_get_screen_team_id` (l'écran d'indications, d'après `tour/auto/library_custom_5.lua:349-350`),
`equipe` vaut `nil` et `cc2x.vehicles()` renvoie toutes les équipes, avec le nom d'écran `?`.
**Hypothèse** : l'écran d'indications appelle `begin_load` et possède `update`/`cc2x` (affirmé par un commentaire de `tour/auto`, jamais mesuré).
**Conséquence** : lignes `CC2MODES|A|…|?|…` en plus, avec des avions de toutes les équipes. L'en-tête du script dit « une seule mesure par tick suffit » mais ne prévoit pas ce cas.

### MES-R3
**`tour/etudes_modes_carburant/lua/library_custom_3.lua:68`** — scénario `RISQUE MES-R3`.
`(equipe ~= nil) and cc2x.vehicles(equipe) or cc2x.vehicles()` : si le premier appel renvoie `nil` (la doc : « CC2X functions … return nil when something is not available »), l'idiome
`and/or` bascule sans bruit sur l'appel **sans** équipe. Même conséquence que MES-R1.
*Piste* : écrire un `if` explicite.

### ENS-R1
**`tour/etudes_demarrage_auto/demarrage_auto.lua:19,35-36` et `tour/auto/library_custom_5.lua:32,517-519`** — scénario `RISQUE ENS-R1`.
Les deux outils posent un verrou **différent** (`__cc2_demarrage_auto__` et `__cc2_auto_verrou__`). Installés tous les deux dans le menu (le premier dans `library_custom_0.lua`, le
second dans `rom_0\scripts\library_custom_5.lua` d'après `tour/auto/LISEZ-MOI.md`), chacun envoie sa commande : `load_game 18` à 28 s, `new_game_custom` à 30 s.
**Conséquence** : deux ordres contradictoires. Aucune des deux fiches n'interdit de les combiner.
*Piste* : un verrou commun, ou une phrase dans les deux fiches.

### AUTO-R2
**`tour/auto/library_custom_5.lua:224-225`** — scénario `un seul ordre refuse sur 4` (`scenarios/essai_auto_lib5.lua`).
Quand la sortie échoue au délai (par exemple parce qu'un seul avion n'a pas pu recevoir son ordre), l'état passe à `echec` mais **aucun rappel** n'est donné aux avions déjà en l'air : ils
restent en vol, sans ordre de retour, jusqu'à la fermeture du jeu par `quit_game`.
**Conséquence** : sans importance pour une partie jetable ; gênant si la sauvegarde sert ensuite.

### AUTO-R1
**`tour/auto/library_custom_5.lua:476-483`** — scénario `RISQUE AUTO-R1`.
Dans la branche HUD (`g_ca_hud = true`, désactivée par défaut), `update = function(screen_w, screen_h, delta_time, ...)` transmet le **3e** paramètre à `ca_image` comme `delta_time`.
Si l'écran d'indications a la signature de l'overlay `(screen_w, screen_h, tick_fraction, delta_time)`, le chronomètre `s.ms` n'avance presque pas (le banc : 0.0 après 10 s).
**Hypothèse** : signature de `interactions.lua`, non vérifiée. Sans effet tant que `HUD = false`.

### DEM-R2
**`tour/etudes_demarrage_auto/demarrage_auto.lua:60-61`** — scénario `RISQUE DEM-R2` (relecture indépendante, reproduit).
Même mémorisation que DEM-1, autre déclencheur : `g_da_arme` n'est évalué qu'une fois, et un résultat négatif met `g_da_fini = true` pour toujours. Si `update_get_mod_details()` renvoie une liste
vide ou incomplète **à la première image** (écran-titre), le démarrage est abandonné sans message, même si la liste est complète une seconde plus tard.
**Hypothèse** : la liste des mods peut être incomplète à ce moment. Le dépôt n'en dit rien ; `ETUDE.md` section 2 dit seulement que l'écran MODS du menu l'utilise. (Avec une liste complète dès la 1re image, le banc obtient bien la commande.)
*Piste* : réévaluer `da_arme()` tant que le compte à rebours n'est pas écoulé.

### ENS-R2
**`tour/outils/essai_auto.py:608-609,633-634` et `tour/etudes_demarrage_auto/ETUDE.md:44`** — **non épinglé** (dépend du système de mods du jeu, que le banc ne simule pas).
`essai_auto.py` pose par défaut le script d'essai dans le slot **5** et n'interdit que les slots 1, 4, 7, 9 (« pris par cc2_mesures »). Or `cc2_modes` occupe 3 (télémétrie) et **5** (onglet SPEED), d'après
`ETUDE.md` de `demarrage_auto` (section 2, « Slot libre »). La règle du jeu est « les mods remplacent des fichiers entiers, le dernier chargé gagne » (`partage_detail/07`, section 1).
**Si les deux mods sont cochés ensemble** : l'un des deux scripts disparaît sans erreur. Avec `--rom0 5` (recommandé par `tour/auto/LISEZ-MOI.md`), le menu charge bien la sauvegarde depuis
`rom_0`, mais en partie le fichier du mod `cc2_modes` remplace celui de `rom_0` : la mission sortie/retour ne tourne jamais. Même type de collision, d'après le même inventaire : télémétrie (slot 3) avec
le Workshop 3225306468, SIM (slot 7) avec `camera_libre`.
**À vérifier** : ne cocher qu'un mod à la fois pour un essai, ou choisir un slot libre (`ETUDE.md` : seul le 0).

### ENS-R3
**`tour/lua/library_custom_9.lua:167-168`** — scénario `RISQUE ENS-R3` (relecture indépendante, reproduit dans le modèle).
`sorties_dessiner` dessine son fond en `(screen_w - 4 - w, 4)`, **après** le jeu, sur toute la hauteur de ses lignes. Dans le banc (écran 256 × 256, police 5 × 9 inventée) : fond `(99, 4)` de 153 × 54 pour 2 appareils,
alors que LOADOUT est en `(172, 10)` de 74 × 84 : le panneau le recouvre. Avec plus de 4 appareils la hauteur dépasse 99 et touche aussi la fenêtre SPEED des onglets carburant.
**Hypothèse** : la vraie police est assez large pour que le panneau atteigne x ≥ 172 (le recouvrement de LOADOUT reste vrai tant que le panneau fait plus de 84 de large) ; jamais vu en jeu.
**Conséquence** : pendant une sortie et 2 minutes après, une partie de LOADOUT / SPEED est masquée. Les clics atteignent quand même les boutons cachés.

### AUTO-R4
**`tour/auto/library_custom_5.lua:419` et `:456-460`** — scénario `RISQUE AUTO-R4` (relecture indépendante, reproduit).
Après la fin de l'essai, `s.quit = true` est posé au premier envoi de `quit_game`, mais l'état reste `fin`/`echec`, donc `ca_chat` (appelé à chaque image) continue de poster le détail complet toutes les 150 ticks
(le banc : 20 paquets, 40 messages, dans les 100 s qui suivent).
**Hypothèse** : le jeu ignore `quit_game` envoyé depuis cet écran (point 3 des « Inconnues à lever » de `tour/auto/LISEZ-MOI.md`). Alors le chat est inondé jusqu'à la fermeture forcée par l'orchestrateur (1800 s par défaut).
*Piste* : ne plus appeler `ca_chat` une fois `s.quit` vrai.

### MES-R4
**`tour/etudes_modes_carburant/lua/library_custom_3.lua:120-131` (`update = function(...)` à la ligne 128)** — scénario `RISQUE MES-R4` (relecture indépendante, reproduit).
Le script enveloppe `update` par une fonction `...` dans **tout** état Lua où `begin_load` est appelé. Sur un `update` à 7 paramètres (l'écran de pilotage), `debug.getinfo(update, "u").nparams` passe de 7 à 0.
**Hypothèse** : `partage_detail/07` section 1 dit que l'écran de pilotage « is recognised by debug.getinfo(update).nparams == 7 » (par d'autres mods, chargés après celui-ci) et que cet écran appelle `begin_load`.
**Conséquence** : un autre mod ne reconnaît plus le HUD de pilotage tant que la télémétrie est cochée. (Le risque inverse existe pour tout script qui enveloppe `update` avec `...`.)

### SORT-R2
**`tour/lua/library_custom_9.lua:16-50`** — scénario `RISQUE SORT-R2` (relecture indépendante, reproduit).
Contrairement à `library_custom_7.lua:23` et `library_custom_3.lua:103`, le journal des sorties ne regarde jamais si le tick recule. Après une sortie terminée au tick 2124, un retour du tick à 100 laisse la ligne
`FINI en …` affichée jusqu'à ce que le nouveau tick dépasse `fin + 3600`.
**Hypothèse** : l'état Lua de l'écran survit au chargement d'une autre partie (le commentaire de `library_custom_7.lua:24` le suppose).
**Conséquence** : résultat de l'ancienne partie affiché dans la nouvelle ; cosmétique. Autre limite de même nature, déjà valable pour le journal des atterrissages : chaque écran ne chronomètre que pendant qu'il est affiché, donc les trois écrans peuvent diverger.

---

## Vérifié sans problème (par le banc, dans le modèle de jeu documenté)

- **Les 7 scripts** se chargent sans erreur dans les 4 ordres de chargement (libs avant/après l'écran × API liée au chargement/au `begin_load`), ne créent que leurs propres globales
  et ne portent aucun appel `io`/`os`/`package`/`require`/`dofile`/`load`/`debug` (contrôle par jetons).
- **Aucun nom inconnu** de la fausse API dans aucun script (contrôle `lua_inconnus` adapté) ; la syntaxe est acceptée à la fois par l'outil maison et par le vrai compilateur Lua 5.3.
- **Pas de collision de noms globaux** entre les 7 scripts (sauf l'onglet v1/v2, deux versions du même) ; SIM + SORTIES + télémétrie + onglet v2 fonctionnent ensemble dans les
  48 combinaisons d'ordre testées.
- **Enveloppes transparentes** : `update` et `begin_load` rendent les mêmes valeurs (y compris `nil` au milieu) et reçoivent les mêmes paramètres (7 pour l'écran de pilotage).
- **Onglet SPEED v2** : valeurs envoyées bornées sur 600 clics tirés au hasard (`set(id entier > 0, mode ∈ {0,1,2})` seulement) ; correspondance ECO→1, NORMAL→0, FLANK→2 ; `hold(id)` jamais
  appelé avec un id ≤ 0 ; autonomie toujours entre 0 et 120 min ou « ? » ; reprise sur erreur de dessin (piles remises en ordre, onglet coupé, une ligne dans `cc2x.log`).
- **Démarrage auto** : étapes dans l'ordre (accroche → interrupteur → compte à rebours → **une** commande → message), un seul contexte du menu passe le verrou.
- **Essai auto** : mission complète (attente → sortie → retour → fin) avec les durées mesurées du dépôt, ordres exacts, `quit_game` une seule fois ; texte de la « boîte aux lettres » ≤ 480
  caractères et sans `< > & "` (il est écrit dans un XML) ; messages du chat ≤ 120 caractères.
- **Télémétrie** : format identique au journal réel du 28/10 (12 champs), lignes < 900 caractères (limite du SDK) même avec des coordonnées extrêmes.

## Points examinés et écartés (relecture indépendante)

- **Menu pause qui lancerait une partie par-dessus la partie en cours** (`demarrage_auto.lua:34-36,77-80`) : le scénario suppose que le contexte du menu pause définit `g_is_menu_active`. Rien ne l'étaye :
  `ETUDE.md:41` dit que cette variable n'est posée qu'en tête de `screen_menu_main.lua`, et la ligne de `cc2_sources.txt` citée ne concerne que le test d'un module du Mac. Non retenu ; à surveiller si on ajoute un journal de `rawget(_G, "g_is_menu_active")` dans la pause.
- **SIM avec des secondes entières** (`library_custom_7.lua:27-31`) : si `update_get_time_since_epoch` rendait des secondes entières, la fenêtre « 10 s » durerait de 9 à 11 s réelles (écart jusqu'à ±10 %). Le doc dit « seconds, real time »
  et la valeur ×1,33 relevée par le moddeur sur la tour est cohérente avec des secondes fractionnaires. Non retenu.
- **SIM après une pause solo** : la 1re fenêtre mêlerait pause et jeu (« SIM x0.2 » pendant 10 s). Dépend de la façon dont le jeu appelle `update` pendant la pause, inconnue. Non retenu.
- **Retours jetés** par les enveloppes de l'overlay et du HUD de `tour/auto/library_custom_5.lua` (`ca_envelopper_overlay`, branche HUD) : sans effet connu (ces `update` ne rendent rien).
- **Entiers / flottants Lua 5.3** : aucun `%d`, `floor`, `ceil` ni division ne reçoit un non-entier avec les valeurs de l'API (l'agent l'a fuzzé sans `pcall`, 300 parties aléatoires, 0 exception ; le banc a refait l'essai avec des ticks
  flottants à valeur entière : mêmes résultats).

## Notes (ce n'est pas un bug)

- Onglet SPEED (v1 et v2) : pendant l'image du clic, **aucun** bouton n'est allumé (ECO est dessiné avant le clic, NORMAL après) ; le bon bouton s'allume à l'image suivante.
- Essai auto : `DELAI_SORTIE` (9000 ticks) se compte depuis le **dernier renouvellement d'ordre** (`s.t_cmd`), donc un échec peut survenir jusqu'à ~15 600 ticks après le début (le script le dit).
- Télémétrie : chaque état Lua qui appelle `begin_load` écrit sa propre mesure : l'en-tête du script annonce « 2 ou 3 » lignes identiques par tick, mais le nombre réel est celui des états Lua concernés (une dizaine ou plus, d'après l'agent ; non mesuré).
- Essai auto : un seul ordre sur quatre refusé laisse l'essai continuer avec 3 avions et échouer au délai (voir AUTO-R2) ; c'est cohérent avec le code mais pas très utile.

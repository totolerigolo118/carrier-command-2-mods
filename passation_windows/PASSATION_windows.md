# PASSATION — Carrier Command 2 : du Mac à la tour Windows

Écrite le 25/10/2026 par Claude Code sur le Mac du moddeur, pour Claude Code sur sa tour Windows. Version 2 : corrigée après une **relecture à froid** par une autre instance qui ne connaissait pas le projet.
Feuille **privée** : elle contient des informations personnelles volontairement. Les fichiers de `reference_en/` (anglais) ont été envoyés à d'autres moddeurs : **ne les modifie jamais** et n'y mets aucune information personnelle. Tes comptes rendus vont dans `JOURNAL_tour.md`.
Elle **remplace** la passation du 23/10 (`ancienne_passation_23-10/`, ascenseur ×2 seulement) ; celle-ci porte un bandeau qui dit quelles sections restent valables.

---

## 0. À lire en premier : avec qui tu travailles

- **Le moddeur** **ne code pas** : il juge le résultat, pas le code. Réponds-lui en **français simple** et définis au passage les mots techniques (une adresse, un crochet, une empreinte, une greffe…).
- **Au début d'une session** sur un projet existant : trois lignes de rappel (ce qu'est le projet, où on s'était arrêté, ce qui reste), avant toute autre chose.
- **Une seule question à la fois**, et termine chaque réponse par **la prochaine action concrète** (ce que tu vas faire, ou ce qu'il doit décider). Jamais quatre questions empilées.
- **Pour toute tâche un peu substantielle : montre le plan en français, du point de vue de ce qu'il verra changer, et attends son feu vert** avant de toucher à un fichier. Dis explicitement ce que tu vas casser ou supprimer. Les corrections de bug et les retouches qu'il a décrites précisément se font sans demander.
- **Rien ne se télécharge, s'installe ou s'exécute sans son accord explicite, étape par étape** : DLL, compilateur (Zig…), paquets Python (`pip install`), Ghidra, Java, `git clone`, scripts d'un dépôt. Dis d'où ça vient et ce que ça fait. Un seul accord ne couvre jamais plusieurs actions.
- **Vérifie toi-même et montre la preuve** (sortie réelle des programmes, chiffres relevés). Ne conclus jamais par « dis-moi si ça marche ». Si tu n'as pas pu tester, dis-le franchement et dis ce qu'il doit regarder lui-même. Jamais de « ça devrait marcher » présenté comme un fait.
- **Choix visuels** (couleurs, mise en page, style) : 4 à 6 variantes numérotées dans une page HTML, il répond par un numéro.
- **Quand il te demande de mettre à jour les fichiers Markdown**, termine ta réponse par un **prompt prêt à coller** pour la conversation suivante (dans un bloc de code, 3 à 6 lignes, à la première personne : fichier à lire en premier avec son chemin exact, où on s'est arrêté, prochaine chose à faire).
- **Le jeu** : sur cette tour, **ne lance et ne ferme jamais le jeu sans le lui avoir demandé dans le message en cours** (il revient sans prévenir). C'est **lui qui lance et qui joue** pour les mesures. Sur le Mac, le 25/10 au soir, il m'a autorisé à le lancer pendant qu'il était absent : cette permission ne vaut **que sur le Mac et que pendant ce moment-là**.
- **Une seule modification testée à la fois**, sinon on ne sait plus ce qui produit quoi.
- **Mesure en temps de jeu**, pas au chronomètre : horloge de jeu = `update_get_logic_tick() / 30` (`lua_a_installer/library_custom_1.lua`). Sur le Mac le jeu tombait à 50-72 % de sa vitesse ; la tour devrait tourner à pleine vitesse, mais la mesure en temps de jeu reste la bonne.
- Pas de cosignature « Claude » dans les messages git s'il y a un dépôt. Pas d'emoji à profusion.
- Le site des bugs et idées (geometa.co.uk/support/carriercommand) bloque (erreur 429, plus d'une heure) au-delà d'environ 60 pages par minute : une requête toutes les 10-15 s, et prévenir le moddeur avant d'y retourner.
- Formules de maths : un vrai rendu, pas du texte approximatif.
- **Mémoire du projet** : il n'y en a pas sur la tour. Tu tiens `JOURNAL_tour.md` à jour à chaque étape ; le moddeur le rapportera au Mac.

## 1. Le but

Rendre les **sorties et retours d'avions et d'hélicos du porte-avions plus rapides**, avec quelques conforts (horloge, journal, vitesse de l'escadrille, caméra CCTV nette, annuler un lancement), **sur sa tour Windows**, là où il joue et où il **héberge ses parties en multijoueur**.
La simulation tourne chez l'hôte : s'il héberge depuis une tour patchée, les joueurs qui le rejoignent profitent probablement des patchs « serveur » sans rien installer (**déduction, jamais testée avec un 2e joueur**). Un patch du programme n'est jamais transmis aux autres joueurs ; seuls les fichiers passés par le système de mods le sont.
Vocabulaire du projet : une **greffe** = un bout de code ajouté au programme ; les **baies A1 à A8** = les 8 places d'avions du hangar (une par bouton de baie) ; **réglage A** de l'atterrissage = « créneau de piste élargi » seul, **réglage B** = A + circuit d'attente en cercle ; **piste** = la case unique qui réserve la piste.

## 2. Où on en est (tout a été fait sur le Mac, programme `build_mac` du 2026-01-05)

« 14 modules » = **9 patchs du programme + 5 fichiers de données** (4 scripts Lua + 1 shader). Mesures en temps de jeu, même sauvegarde, navire à l'arrêt.

| Patch (nom du module Mac) | Résultat | Statut |
|---|---|---|
| `ascenseur_x2` : énergie ascenseur/grue 0,4 → 0,8, plateforme, grue et roulage ×2 (34 retouches de constantes) | sortie de 4 avions **3:50 → 2:15** (×1,70), jeu d'origine contre patché | **validé en jeu** |
| `helicos_approche_x2` + `helicos_pres_ascenseur` | 4 hélicos **6:52 → 4:22** (−36 %), 0 raté. ⚠️ Le 6:52 a été mesuré **avec `ascenseur_x2` et `atterrissage` déjà actifs** : ce n'est pas une référence « jeu d'origine » | **validé en jeu** |
| `atterrissage` (créneau de piste élargi + circuit en cercle : 10 retouches, voir étape 5) | 4 avions rangés en **7:28**, une piste donnée toutes les 1:31, 0 raté | validé en jeu ; **jeu d'origine jamais mesuré** (estimé ≈ 3 min de plus) |
| `pont_retour_x2` (roulage ×2 au retour, 3 retouches) | pont → hangar 0:51 → 0:32 par avion ; retours de 4 avions 7:28 → 5:49 (mélange d'avions différent) | **mesuré en jeu le 25/10** (un passage) |
| `grue_annulation` (2e appui sur le bouton de baie ramène l'avion déjà pris par la grue) | fenêtre ≈ 13-18 s | installé, testé hors jeu, **jamais vu en jeu** |
| `vitesse_escadrille` + `vitesse_boutons` (ECO / NORMAL / FLANK) | plancher IA 48/72 m/s → NORMAL 61/91, FLANK 144 | **la fonction Lua `cc2_vitesse` est vérifiée en jeu** (sonde du 25/10 : enregistrée dans tous les contextes, `dofile` disparu, 11 appels corrects, fichier du mode écrit) ; le crochet sur le plancher de vitesse et la barre ne sont **jamais vus en partie** ; NORMAL = estimation à régler |
| `cctv_net` (écran CCTV 512 × 512) | 4× plus net | installé, testé hors jeu, **jamais vu en jeu** |
| `ecriture_releve` + `releve` (relevé du lag dans un fichier) | | **vu en jeu au menu principal** (voir ci-dessous) ; aucune partie enregistrée |
| `horloge`, `journal` (Lua) | chronomètre automatique des atterrissages | **utilisés en jeu**, marchent |
| `effet_tele` (shader sans l'effet « vieille télé ») | | installé, à vérifier. Fichier de données : voir `shader_effet_tele/` (à n'appliquer que si le shader d'origine de la tour a le sha256 `ceadab0a21459350b0e75a3467fafd98ab7efb8eade5aaa1eec1458db83775f8`, celui du Mac ; sinon le refaire : principe dans `reference_en/cc2_notes.txt`, partie 06) |
| Essayés puis abandonnés | hélicos posés sur l'ascenseur (collision de 2 hélicos), 2e ascenseur (9/10, inutile : la piste est le goulot), piste libérée plus tôt (collision), interface de pilotage plus fine (il n'en veut pas) | |

**Test de lancement du 25/10 à 17:26** (le moddeur absent, il m'avait autorisé à lancer le jeu sur le Mac) : programme avec les 14 modules actifs (md5 ce8dafec…) : le jeu démarre, tient **100 s au menu principal à pleine vitesse** (≈148 % de processeur, 713 Mo), se ferme proprement, **aucun rapport de plantage**. Le relevé a produit `releve_cc2.txt` : **98 lignes au bon format** (`CC2R1 E … FIN`, écrans `screen_front`, `screen_pilot_*`), donc **l'écriture de `print()` dans un fichier et le crochet Lua `begin_load` marchent en jeu** — au menu seulement : aucune partie chargée, donc les modules du porte-avions (CCTV, vitesse, grue) n'ont **pas** été exercés. La table de fonctions Lua modifiée (`dofile` → `cc2_vitesse`) n'a pas fait planter le démarrage.
**Sonde Lua du 25/10 à 17:53** (un fichier `library_custom_7.lua` temporaire, retiré ensuite, fichiers du jeu remis identiques, aucun plantage) : au menu, **`cc2_vitesse` est une fonction dans tous les contextes Lua et `dofile` n'existe plus** ; 11 appels : lecture d'une équipe sans mode → 0 ; réglage 3 → 3 ; mode invalide (9, 0) ignoré ; équipe hors limites (99, −1) → 0 ; argument texte ou absent → équipe 0 ; flottant entier accepté ; le fichier du dernier mode est bien écrit (`1`). Une équipe sans mode **adopte le dernier mode réglé** (voulu, jamais un bug). Contextes vus au menu : une interface (`update_get_time_ms` présent, `update_get_logic_tick` absent, `update` à 3 paramètres) et les écrans du « vaisseau » du menu (`screen_front` ×4, `screen_pilot_c/l/l_2/r/r_2`) qui ont `update_get_logic_tick`, `update_get_time_since_epoch`, `update_ui_event`, `update_get_save_slots`, `update_launch_carrier`, mais pas `update_get_time_ms`, ni `io`, `os`, `dofile`, `loadstring`, `require`. Lua 5.3 avec `string.pack` et `utf8`. (Le `README.txt` de `reference_en/` dit encore « tested outside the game only » : périmé depuis ce test.)


**Tests en jeu du 25/10 au soir (Mac, sans cliquer ; le moddeur a arrêté la suite à sa demande)** — scripts et mode d'emploi : `outil/tests_en_jeu/` (sur le Mac ; ce dossier-ci ne les contient pas, l'idée se refait avec le SDK).
- **Une sauvegarde se charge toute seule** par `update_ui_event("load_game", 18)` depuis le menu : 4 min, 123 véhicules, 50 écrans du porte-avions en train de tourner, **aucun plantage** avec les 14 modules ; vitesse moyenne **62 %** (Mac à 82 °C) contre 101 % au menu. Les écrans étaient « éteints » (pas de joueur) : l'affichage CCTV et la barre de vitesse n'ont **pas** été exercés ; la création des écrans (crochet A de `cctv_net`) s'est faite sans erreur.
- **Le Lua peut lancer et rappeler des avions** : `v:clear_waypoints(); v:clear_attack_target(); v:add_waypoint(x, z)` sur un avion rangé le lance ; `add_waypoint` sur le porte-avions + `set_target_vehicle(wp, id_porte_avions)` le rappelle. Même chaîne que les boutons de baie.
- **Mesures automatiques, tous les patchs actifs, 4 avions (2 Albatros + 2 Manta), même sauvegarde n° 18** : sortie des 4 (ordre → tous en l'air) **2:15** (4 048 ticks, identique à la mesure à la main) ; rappel dès que le dernier a décollé : **retours 5:49** (1re entrée en file → dernier rangé), pistes données **toutes les 1:13** en moyenne (0:38, 1:47, 2:52, 4:19 après la 1re file), approche 0:47, **pont → hangar 0:32 pour chacun des 4** (0:51 avant `pont_retour_x2`), 0 approche ratée. Référence du 23/10 sans `pont_retour_x2` : retours 7:28, une piste toutes les 1:31, pont → hangar 0:51 (mélange d'avions différent : indicatif). **Le jeu d'origine n'a toujours pas été mesuré** (la tentative sans patchs n'a pas eu lieu) : à mesurer sur la tour (étape 0 bis) ; si le jeu d'origine de la tour donne 3:50 pour la sortie des 4 avions des baies A1, A2, A5, A6, le code est le même que sur le Mac.
- **Vitesse en vol (mesure)** : en ECO (jeu d'origine), un Albatros et un Manta qui vont vers un point à 20 km croisent à **≈ 120 m/s** (120,1 et 121,7), PAS à 48 / 72 m/s. Le régulateur de gaz vise 120 m/s au-delà d'environ 800 m du point quel que soit le plancher : **les modes ECO / NORMAL / FLANK ne changent donc la vitesse que près du point**, pas la vitesse de transit. Pour de vrais modes de transit il faudrait aussi changer le 120 du régulateur (non fait). Le test près du point (300 m du porte-avions) a été lancé puis arrêté ; **jamais terminé**. Les deux avions du test lointain ont été abattus par l'ennemi (~10 km).
- **Fonction Lua `cc2_vitesse`** : vérifiée en jeu (voir plus haut). **Le relevé** (`releve` + `ecriture_releve`) est vu en jeu : fichier créé, lignes au bon format, y compris en partie chargée (93 lignes de données d'unités).

Détails, adresses, octets avant/après : `reference_en/cc2_reference.txt` (partie 10). Explications : `reference_en/cc2_notes.txt`. Études d'origine : `etudes_fr/` (lire `etudes_fr/LISEZ-MOI.txt` d'abord : certaines recommandations y ont été abandonnées depuis).

## 3. Ce qu'on sait de la tour — et ce qu'on ne sait pas

**Connu** (par le SDK public CC2X, relu le 25/10, voir `COMPARAISON_MAC_WINDOWS.md` et `sdk_public_cc2x/SOURCE.txt`) : le build Windows courant est **1.5.18**, exécutable **`carrier_command.exe` en 32 bits**, horodatage PE `0x6a36c177` (2026-06-20 16:36 UTC), taille d'image `0x00af7000`. Le build Mac est plus ancien (janvier 2026). Application Steam : **1489630**.
**Connu par ses messages précédents** : sur la tour il avait le mod Workshop **Revolution** (remplace les écrans de contrôle des véhicules ; version 1.5 = objet 3098073689 à l'époque : **version peut-être périmée**). Nos modules Lua s'accrochent par `begin_load()` : à vérifier que le script de Revolution l'appelle toujours.
**Inconnu — à relever à l'étape 0** : chemin du jeu (typiquement `C:\Program Files (x86)\Steam\steamapps\common\Carrier Command 2\`, ou une autre bibliothèque Steam : **demande-le au moddeur, ne fouille pas le disque**), version de Windows, outils déjà installés (Python ? compilateur ? Ghidra ?), si Steam met le jeu à jour tout seul, si CC2X est déjà là, quels mods sont actifs (`%APPDATA%\Carrier Command 2\mods.xml`). **Le sha256 de l'exécutable Windows n'est connu de personne** : seuls l'horodatage et la taille sont comparables ; tu relèves le sha256 comme référence.
**Où ranger** (à confirmer avec le moddeur à l'étape 0) : un dossier de travail `Documents\cc2-patchs\` sur la tour ; les sauvegardes de l'exécutable y vont aussi, **jamais dans le dossier Steam** (Steam peut le nettoyer).

## 4. Décision de méthode (à confirmer à l'étape 2)

**Base = le SDK public CC2X** (`sdk_public_cc2x/`, dépôt GitHub `Dioramawhois/Carrier-Command-2-extender`, auteur « DYOR » sur le Discord du jeu). C'est une DLL nommée `dinput8.dll` déposée à côté de `carrier_command.exe` (le jeu la charge avant celle du système). Nos patchs deviennent **une extension** `cc2x_<nom>.dll` (32 bits), **placée à côté de l'exécutable pendant le développement** (l'en-tête le prévoit), qui s'applique **en mémoire** au démarrage ; supprimer les DLL = jeu d'origine, l'exécutable n'est jamais modifié.
Pourquoi plutôt qu'un patch direct de l'exécutable comme sur Mac :
- en 32 bits, une constante flottante se lit par une **adresse absolue** : on la redirige vers **un float placé dans notre propre DLL** ; plus besoin qu'une valeur doublée existe déjà dans le jeu ;
- le SDK reconnaît le build, a un pas de simulation (`on_server_tick`), un journal (`cc2x.log`), ajoute des fonctions Lua (`api->lua_add`) et lit/écrit les véhicules ;
- du C normal, plus de « code mort d'ImGui » ni d'éditeur de liens maison.
Contreparties, à garder en tête :
- **un seul build** géré (1.5.18 win32), **solo ou hôte** (aucun transport multijoueur) ;
- **pas d'écriture d'octets bruts** dans son API : le plugin le fait lui-même avec `VirtualProtect` + copie, ce qui **contourne** la vérification des octets d'origine et le refus des chevauchements. Donc : adresses rebasées avec `api->va()`, **vérifie toi-même les octets d'origine avant d'écrire**, et ne touche pas aux octets que le SDK ou d'autres plugins (ex. Island Airfields) patchent déjà ;
- ses crochets **ne sauvent pas les registres flottants** (voir pièges) et `patch_mid` refuse les instructions déplacées qui contiennent des sauts relatifs ;
- **licence GPL-3.0-or-later** : elle joue si **tu donnes** la DLL ou son code à quelqu'un d'autre (le multijoueur ne donne rien aux joueurs : les patchs restent sur la tour). Garder tout sur la tour = aucune obligation.
**Compilation** : `build.py` (à la racine du dépôt, **3,4 Ko : lis-le avant de l'exécuter**) a besoin de **Zig 0.15.2**, qui **n'est pas dans le dépôt et que `build.py` ne télécharge pas** (voir `sdk_public_cc2x/SOURCE.txt` : adresse et sha256). Deux voies : compiler soi-même (3 accords séparés : télécharger Zig, exécuter `build.py`, déposer la DLL) ou prendre la DLL de la release (un accord pour télécharger, un pour déposer). Préfère compiler depuis les sources lues.
Plan B si le SDK ne convient pas : écrire notre propre petite `dinput8.dll` qui renvoie tout au système et applique nos patchs.

## 5. Plan par étapes (une étape = un feu vert + une preuve dans `JOURNAL_tour.md`)

Pour chaque étape : présente le plan au moddeur, attends son accord, fais, **montre la preuve**, consigne-la, puis propose la suite. **Au début, ne présente que le plan de l'étape 0.**

**Étape 0 — Reconnaissance.** Aucune modification du jeu. Seule écriture permise : la **copie de sauvegarde de `carrier_command.exe`**, dans un dossier que le moddeur a nommé (voir section 3), avec son accord.
Première question à lui poser : « Où est installé Carrier Command 2 ? » (puis, **une question à la fois** : où ranger le dossier de travail et les sauvegardes). Relève : version de Windows, outils présents, horodatage PE et taille d'image de l'exécutable (**doivent valoir `0x6a36c177` et `0x00af7000`**) et son sha256, mods actifs (`mods.xml`), présence d'un `dinput8.dll` dans le dossier du jeu, et le script de Revolution (chemin typique : `steamapps\workshop\content\1489630\<numéro>` ; vérifie qu'il appelle `begin_load()`).
*Preuve :* un tableau « trouvé / manquant » en français. *Stop :* si l'horodatage est différent (autre version que 1.5.18), le SDK public ne marchera pas : dis-le, ne continue pas.

**Étape 0 bis — Mesures de référence sur le jeu d'origine** (aucun patch du programme ; deux fichiers de `rom_0\scripts\` changent, avec son accord explicite).
Avec son accord : vérifie que `rom_0\scripts\library_custom_1.lua` et `library_custom_4.lua` du jeu sont **vides** (sha256 d'un fichier vide : `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`), sauvegarde-les, puis copie-y `lua_a_installer/library_custom_1.lua` (horloge) et `library_custom_4.lua` (journal). Si un mod actif fournit déjà un de ces fichiers, **stop** et demande-lui.
**C'est lui qui lance le jeu et qui joue** (ne le lance pas). Protocole, même sauvegarde à chaque fois, **navire à l'arrêt** :
 1. **Sorties** : lancer les 4 avions des baies A1, A2, A5 et A6 d'un coup ; noter l'heure de jeu au premier ordre et quand le dernier a décollé. (Mac, jeu d'origine : 3:50.)
 2. **Retours des avions** : lancer les 4 avions puis les rappeler tout de suite ; le journal affiche seul les heures de piste, de toucher et de hangar et le total. (Mac, jamais mesuré sur le jeu d'origine.)
 3. **Retours des hélicos** : lancer 4 hélicos (2 Razorbill puis 2 Petrel), les rappeler tout de suite ; même lecture du journal. (Mac : 6:52 mais avec d'autres patchs actifs, voir section 2.)
**La sauvegarde de référence est à créer sur la tour** (une partie neuve ou n'importe quelle sauvegarde de la tour, qu'on ne touche plus ensuite) : celles du Mac restent sur le Mac, et une sauvegarde faite avec le build de janvier n'est pas garantie de se charger en 1.5.18.
*Pourquoi :* sans référence Windows, on ne saura pas ce que valent les patchs. *Preuve :* trois mesures avec la date, la sauvegarde utilisée et, pour les retours, la copie du résumé du journal.

**Étape 1 — Les empreintes : le code Windows est-il le même ?** (lecture seule ; si un outil d'analyse manque, demande avant de l'installer.)
Cherche dans l'image de `carrier_command.exe` les valeurs de la table de la **section 6**, liste les instructions qui les lisent et vérifie les **groupes** (0,025 + 0,001 proches ; 2,5 et 0,05 par paires ×7 ; 1/6 + 1/30 + 11,0/12,0 ; les cinq parts d'énergie ; les empreintes de l'atterrissage). Mets les résultats en face de `reference_en/cc2_reference.txt` (partie 10).
*Preuve :* un tableau « Mac → Windows » par groupe (adresse d'image, instruction). *Stop :* si les groupes n'existent pas, la logique a changé depuis janvier : ne porte rien, dis-le ; on relira la logique avant de continuer.

**Étape 2 — Installer le SDK** (trois accords séparés, voir section 4).
(2a) lire `sdk_public_cc2x/PLUGINS.md`, `cc2x.h`, `build.py` et `SOURCE.txt`, puis obtenir Zig ou la DLL de release ; (2b) déposer `dinput8.dll` dans le dossier du jeu ; (2c) **demander au moddeur de lancer le jeu**, puis lire `cc2x.log` (build reconnu `1.5.18-win32`) ; puis compiler et charger l'exemple `examples_hello_plugin/hello.c`.
*Preuve :* extrait de `cc2x.log`. *Retour arrière :* supprimer `dinput8.dll` et les `cc2x_*.dll`, relancer le jeu.

**Étape 3 — Port n° 1 : énergie, ascenseur, grue, roulage ×2** (le plus rentable : −41 % sur le Mac ; 34 retouches de constantes et 1 immédiat ; tout est dans `reference_en/cc2_reference.txt`, premier module, et `ancienne_passation_23-10/`, sections 3 et 4).
Dans l'extension : vérifie le build ; pour chaque instruction trouvée à l'étape 1, **vérifie les octets d'origine**, puis remplace l'**adresse absolue** de la constante par celle d'un float de ta DLL contenant la valeur doublée ; pour l'énergie, change l'immédiat 0,4 → 0,8. Ne modifie **jamais** la constante partagée elle-même. Relis chaque octet écrit au désassemblage.
*Preuve :* la liste des sites patchés (avant/après), puis la **mesure du moddeur** : sortie de 4 avions, à comparer à la référence Windows de l'étape 0 bis (Mac : 3:50 → 2:15).

**Étape 4 — Port n° 2 : hélicos** (partie 04 des notes). **3 constantes** (point visé 50 → 100 ; point visé au plus 120 → 48 ; seuil de train sorti 20 → 70), **une petite greffe de 21 octets** (soustrait 23,5 avant le plancher −2,0 de la hauteur visée) et **un branchement** (en tout 5 sites dans la partie 10). Mesure : 4 hélicos, à comparer à l'étape 0 bis point 3 **et** à la mesure de l'étape 3 (une modification à la fois : on mesure l'effet de ce port seul).
**Étape 5 — Port n° 3 : roulage de retour ×2, puis circuit d'atterrissage.** Roulage ×2 : 3 constantes (la lecture partagée de 30,0 redirigée vers 15,0 aux trois endroits des états 5, 6 et 7). Circuit : **10 retouches qui ne sont pas toutes des constantes** : 3 sauts redirigés vers le bloc qui donne la piste (écrire les octets soi-même : `patch_mid` refuse les sauts relatifs), 4 lectures de **vecteurs de 4 floats** (`addps` : les nouvelles constantes doivent être **alignées sur 16 octets**), 2 lectures de float scalaire (600 → −1800) et 1 instruction `addss` → `subss`. Mesure avec le journal. La simulation prévoit que le réglage B est plus lent si un atterrissage dure 140-160 s : dans ce cas, le réglage A seul (les 3 premiers sites).
**Étape 6 — Modes de vitesse de l'escadrille** (partie 05). Deux voies : (a) **essai rapide, probablement sans effet** : écrire `CONTROL_SPEED` (`+0x1f8`) des avions de l'équipe du joueur pilotés par l'IA à chaque pas de simulation. Sur le Mac, cette vitesse visée est **réécrite à chaque tick** par le code du jeu et lue dans le même appel, et `on_server_tick` s'exécute **après** le pas d'origine du serveur (vérifié dans `sdk_public_cc2x/src/cc2x.c`, fonction `tick_once` : `o_tick(self)` d'abord, puis les rappels) : l'écriture sera sans doute écrasée au pas suivant ; (b) **voie fiable** : crochet sur le plancher 48/72 (chercher `48.0` puis `144.0` autour d'un test « type 10 »). Côté Lua : `api->lua_add("speed", "mode", …)` crée **`cc2x.speed.mode`, pas une fonction globale** ; adapte `library_custom_6.lua` (qui appelle la globale `cc2_vitesse(equipe [, mode])`) ou fais un petit script Lua qui définit `cc2_vitesse` en appelant `cc2x.speed.mode`.
**Étape 7 — Annuler un lancement déjà pris par la grue** (partie 02 section 5). **Seulement après les étapes 3 à 6 validées.** Retrouve d'abord les **décalages 32 bits du gestionnaire des avions** par les analyseurs d'état sauvegardé (recette : notes partie 01 section 6 et partie 11 section 3 d). Le plus risqué : crochet au milieu d'une fonction d'environ 5 000 instructions où l'on ne sait pas quels registres flottants sont vivants ; une grue bloquée empêche tout lancement et tout atterrissage. Retour arrière : supprimer la DLL et **relancer le jeu** (le SDK ne décharge pas un plugin en cours de partie).
**Étape 8 — Le reste, seulement si le moddeur le demande** : caméra CCTV 512 (4 crochets de rendu, gain cosmétique) ; relevé du lag : sur Windows **`print()` n'est pas redirigé par le SDK** (il n'a que la fonction Lua `cc2x.log(...)`, qui écrit dans `cc2x.log`) : il faudrait adapter `library_custom_5.lua` pour appeler `cc2x.log` quand `cc2x` existe.

## 6. Les empreintes (valeurs flottantes 32 bits ; en mémoire elles sont petit-boutistes)

| valeur | bits | rôle | doublée | bits |
|---|---|---|---|---|
| 0,4 | 0x3ECCCCCD | part d'énergie ascenseur/grue | 0,8 | 0x3F4CCCCD |
| 0,025 / −0,025 | 0x3CCCCCCD / 0xBCCCCCCD | pas de la plateforme | 0,05 / −0,05 | 0x3D4CCCCD / 0xBD4CCCCD |
| 0,001 | 0x3A83126F | zone morte de la plateforme (repère, ne pas toucher) | | |
| 1/6 / −1/6 | 0x3E2AAAAB / 0xBE2AAAAB | grue horizontale | 1/3 / −1/3 | 0x3EAAAAAB / 0xBEAAAAAB |
| 1/30 / −1/30 | 0x3D088889 / 0xBD088889 | grue verticale | 1/15 / −1/15 | 0x3D888889 / 0xBD888889 |
| 0,04 / −0,04 | 0x3D23D70A / 0xBD23D70A | rotation de la grue | 0,08 / −0,08 | 0x3DA3D70A / 0xBDA3D70A |
| 0,05 | 0x3D4CCCCD | accélération de roulage | 0,1 | 0x3DCCCCCD |
| 2,5 | 0x40200000 | plafond de roulage | 5,0 | 0x40A00000 |
| 11,0 / 12,0 | 0x41300000 / 0x41400000 | hauteurs du crochet de la grue | | |
| 30,0 | 0x41F00000 | ticks par seconde dans `t += v/(L×30)` | 15,0 aux 3 lectures des états 5-7 | 0x41700000 |
| 0,01 / 0,1 | 0x3C23D70A / 0x3DCCCCCD | seuils d'arrivée (ne pas toucher) | | |
| 0,5 | 0x3F000000 | course de décollage sans plafond (ne pas toucher) | | |
| 48 / 72 / 144 | 0x42400000 / 0x42900000 / 0x43100000 | planchers de vitesse IA (Albatross / Manta) et plafond | | |
| 50 → 100 ; 120 → 48 ; 20 → 70 ; −2,0 ; 23,5 | | hélicos (partie 04) | | |
| 600 → −1800 | 0x44160000 → 0xC4E10000 | atterrissage : fin de la ligne droite (états 3 et 5) | | |
| vecteur (1000, −600, 0, 0) → (1000, 1800, 0, 0) | 0x447A0000, 0xC4160000 → 0x447A0000, 0x44E10000 | atterrissage : centre du virage avant vers le centre du virage arrière (états 4 et 5) | | |
| vecteur (−1000, 600, 0, 0) → (−1000, −1800, 0, 0) | 0xC47A0000, 0x44160000 → 0xC47A0000, 0xC4E10000 | idem, retour au repère | | |
| 80 ; 1200 ; 154 s / 94 s | 0x42A00000 ; 0x44960000 | vitesse imposée du circuit ; rayon des virages ; durée d'un tour d'ovale / de cercle | | |

Groupes (meilleurs repères que des valeurs isolées) : 0,025 et 0,001 à quelques dizaines d'octets ; 2,5 et 0,05 par paires 7 fois ; 1/6 + 1/30 + 11,0/12,0 ensemble ; les 5 parts d'énergie 0,8 / 0,2 / 0,8 / 0,6 / 0,4 dans une même fonction ; 48,0 → 144,0 → 72,0 → 144,0 autour d'un test « type 10 ».
Chaînes qui existent dans tous les builds : `lift_constraint`, `load_lift_lower`, `runway_start`, `runway_end`, `lift_lower`, `lift_upper`, `hanger_center` (l'orthographe est celle du jeu), `vehicle_ai_wing_cruise_speed`, et les noms de champs d'état sauvegardé (`docking_queue`, `runway_state`, `vehicle_id_crane`, `crane_instructions`, `docking_join_time`…).
Spécificités du compilateur Microsoft (non vérifiées) : constantes partagées sous forme `__real@3ccccccd` ; les négatifs peuvent être obtenus par `xorps` avec un masque `__xmm@80000000…` (alors, rediriger la lecture du positif couvre les deux bornes) ; fonctions inlinées autrement (cherche les groupes, pas une fonction).

## 7. Pièges

1. **Registres flottants dans les crochets.** Le crochet du SDK sauve les registres généraux, pas `xmm0-7`. Du C appelé depuis un crochet au milieu d'une fonction de calcul peut écraser un `xmm` vivant (c'est ce qui nous a obligés à écrire des greffes en assembleur sur le Mac). Écris le crochet en assembleur qui sauve/restaure `xmm0-7` autour de l'appel C.
2. **Convention d'appel et `this`.** Mac : System V. Windows 32 bits : `thiscall` (`this` dans ECX) / `cdecl`. Les greffes C de `reference_en/cc2_sources.txt` sont en System V : à **réécrire**, pas à recompiler.
3. **Les décalages de structures du Mac ne s'appliquent pas** (pointeurs de 8 contre 4 octets) : ce sont des étiquettes. Recette fiable : les analyseurs d'état sauvegardé lisent chaque champ **par son nom** : trouve la chaîne, suis la référence, lis le décalage.
4. **Constantes partagées : ne jamais modifier la valeur**, rediriger l'instruction.
5. **Ne pas changer le seuil d'arrivée du roulage ni la course de décollage** (les avions « sautent »).
6. **Le goulot est la piste** (une seule case, tenue jusqu'à ce que l'avion soit sur l'ascenseur), pas l'ascenseur. Ne pas libérer la piste plus tôt : collision de face (le jeu détruit les véhicules qui se touchent).
7. **Vitesse de la plateforme** : écrite dans le programme (0,025 m par tick × énergie) ; les réglages `drive_*` du XML `lift_constraint` ne servent à rien : les mods XML « ascenseur rapide » n'ont jamais marché pour ça.
8. **Une grue bloquée** bloque lancements et atterrissages : retour arrière = supprimer la DLL **et relancer le jeu**.
9. **Mods locaux** : sur le Mac, un mod local n'est actif que pour la session où on l'active. Les fichiers écrits directement dans `rom_0` ne sont pas envoyés aux joueurs qui rejoignent ; ceux d'un mod le sont.
10. **Mesure** : toujours en temps de jeu, « même sauvegarde, même endroit », une modification à la fois.
11. **Ne jamais monter une capacité de munitions** dans `constants.txt` : un véhicule ne se déploie qu'avec le plein.
12. **Accident à ne pas répéter** : une variable shell contenant plusieurs options n'est pas découpée par zsh et l'outil a agi sur le vrai jeu. Chemins en arguments séparés, sauvegardes avant tout.
13. **Mise à jour Steam** : elle remplace l'exécutable ; l'extension doit refuser de s'appliquer si le build n'est pas reconnu (le SDK le fait) et le jeu tourne alors d'origine. Refaire l'étape 1 après chaque mise à jour.

## 8. Ce que le SDK public ne couvre pas et que nos notes apportent (pour plus tard, à la demande du moddeur)

Le porte-avions n'est pas dans son API. Idées à lui proposer **avec l'accord du moddeur** : écriture d'octets bruts (`patch_bytes`), crochets qui sauvent `xmm`, champs du gestionnaire des avions du porte-avions (file, cases grue/ascenseur/piste, états), « réglages » nommés lisibles et modifiables depuis Lua. Liste classée : `reference_en/cc2_notes.txt`, partie 11 section 7.
Sur le Discord du jeu, **DYOR** est l'auteur du SDK et **Sample_Fox** un autre moddeur Windows. DYOR a suggéré de refaire les patchs en **Lua** par-dessus sa plateforme : elle charge des scripts Lua sous n'importe quel nom de fichier, déclarés dans un fichier json du mod, un peu comme les mods de Payday 2. C'est possible pour tout ce qui est écran et mesure (déjà fait : `lua_a_installer/`), pas pour les valeurs écrites en dur dans le programme.

## 9. Ce que le moddeur attend à la fin

- Pour chaque port : la liste des sites, la **mesure en temps de jeu** et le **retour arrière** en une action (supprimer la DLL et relancer le jeu, ou rétablir le fichier sauvegardé).
- Un petit dossier rangé sur la tour (`Documents\cc2-patchs\`, à confirmer) : l'extension, ses sources, un LISEZ-MOI en français, les sauvegardes, `JOURNAL_tour.md`. Pas de manipulation compliquée.
- `JOURNAL_tour.md` à jour à chaque étape (c'est ce qu'il rapportera au Mac).

## 10. Inventaire de ce dossier (tous les chemins cités dans cette feuille existent)

```
passation_windows/
  PASSATION_windows.md            cette feuille
  COMPARAISON_MAC_WINDOWS.md      états, décalages et points d'ancrage Mac <-> Windows (lu dans le SDK public)
  PROMPT_A_COLLER.txt             le prompt à coller dans la nouvelle conversation sur la tour
  JOURNAL_tour.md                 le journal à tenir sur la tour
  reference_en/                   README.txt, cc2_notes.txt, cc2_reference.txt, cc2_sources.txt (anglais, déjà envoyés à d'autres moddeurs : ne pas modifier)
  etudes_fr/                      les études d'origine (+ LISEZ-MOI.txt, + DEMARRER_cc2_patchs_ETAT_MAC.md : l'état complet du travail sur le Mac)
  lua_a_installer/                library_custom_1/4/5/6.lua (horloge, journal, relevé, barre de vitesse) : marchent tels quels sur Windows (le relevé a besoin que print() soit redirigé, voir étape 8)
  shader_effet_tele/              le shader modifié du Mac (voir section 2 pour savoir quand l'appliquer)
  sdk_public_cc2x/                copie du SDK public (en-tête, documentation, sources, build.py, exemple), SOURCE.txt (origine, version, empreintes) ; GPL-3.0-or-later
  (à la racine du dépôt : extension_windows/   la charpente de l'extension en C, sans adresses du jeu : voir section 13)
  ancienne_passation_23-10/       la passation « ascenseur x2 » du 23/10 + ses fichiers (ascenseur_x2.py, generer_table.py, test_horloge.py, library_custom_1.lua) ; bandeau « partiellement obsolète »
```
Sauvegardes de référence restées sur le Mac (trop lourdes pour être copiées) : programme d'origine reconstruit, md5 b0107170…

## 11. Historique résumé

23/10 : énergie et ascenseur décodés, ascenseur ×2 validé (×1,70), horloge, atelier de patchs. 23-24/10 : atterrissage décodé et mesuré, hélicos validés (−36 %), greffes de code dans le code mort d'ImGui, courbes du lag. 25/10 : grue, écrans du pont (CCTV), vitesse des avions, roulage de retour ; dossier de notes en anglais envoyé à un moddeur Windows ; lecture du SDK public (Windows 32 bits) ; test de lancement au menu ; décision de passer sur la tour.

## 12. Le va-et-vient Mac <-> tour passe par GitHub (mis en place le 26/10/2026)

Dépôt **privé** : `[depot prive]` (compte GitHub **perso** du moddeur, `[pseudo retire]` ; **jamais** son compte ni son adresse professionnelle). Boucle fermée : seuls le Mac et la tour le lisent. Il contient **tout le texte du projet, informations personnelles comprises** ; il ne contient **jamais** le programme du jeu, ni les sauvegardes, ni les DLL, ni les zip (`.gitignore`). Ne jamais le rendre public ni partager son lien.
- **Identité des commits (obligatoire, dans le dépôt cloné sur la tour)** : `git config user.name "[pseudo retire]"` et `git config user.email "[adresse retiree]"`. Jamais l'adresse professionnelle (le git global du Mac l'a, pas celui de ce dépôt). Pas de mention « Claude » dans les messages de commit.
- **Début de session : `git pull`** avant de lire quoi que ce soit. **Fin de chaque étape : `git add`, `git commit`, `git push`**, avec un message en français qui dit quelle étape.
- **Qui écrit quoi** (pour éviter les conflits) : la **tour** écrit `passation_windows/JOURNAL_tour.md` et son propre dossier `tour/` (extension, sources, mesures, sauvegardes de ses réglages). **Depuis le 26/10 elle écrit aussi dans `extension_windows/`** (section 13). Le **Mac** écrit tout le reste (notes, feuille, scripts). La tour ne modifie pas les autres fichiers ; si elle voit une erreur dans la feuille, elle l'écrit dans le journal et le Mac corrige.
- **Rien d'énorme ni de binaire** : si un fichier de plus de 1 Mo ou un exécutable apparaît dans `git status`, ne pas l'ajouter, le dire au moddeur.
- Les fins de ligne sont normalisées en LF (`.gitattributes`).
- **Pas du temps réel** : chaque côté n'agit que pendant sa session ; le moddeur dit « va voir le journal » ou « pousse » quand l'autre côté doit réagir.
- **Cloud** : les sessions cloud de Claude Code (crédit d'environ 130 $, jusqu'au 05/11/2026 à 8 h 59) lisent ce même dépôt et rendent leur travail sur **une branche à part** (jamais sur `main`) ; rien du jeu n'y est lisible.

## 13. La charpente de l'extension existe déjà : `extension_windows/` (faite par une session cloud le 26/10/2026)

Les étapes 3 à 8 n'ont **pas** à repartir de zéro : le dossier **`extension_windows/`** (à la racine du dépôt) contient une extension CC2X en C, prête à recevoir les adresses de la tour. **Aucune adresse du jeu Windows n'y est écrite** : les 8 listes de retouches de `extension_windows/src/cp_groups.c` sont **vides** (14 repères `TODO(tower step N)`). Lis d'abord `extension_windows/README_FR.md` (explication simple) puis `extension_windows/RAPPORT_cloud.md` (le tableau « groupe → ce que la tour doit trouver → étape » est dans sa section 6 ; ses sections 5 et 7 listent ce qui n'est **pas** vérifié et les pièges).
- **Ce qu'elle fait déjà** : portier de version (refuse sauf `1.5.18-win32` + horodatage PE `0x6a36c177` + taille `0x00af7000`) ; couche d'écriture sûre (vérifie les octets d'origine, tout ou rien par groupe, retour arrière, refuse les chevauchements, recale les adresses) ; table de nombres à nous alignée sur 16 octets ; un interrupteur par groupe dans `%APPDATA%\Carrier Command 2\cc2x\cc2_patchs.ini` (modèle : `extension_windows/cc2_patchs.ini.example`, **tout éteint par défaut**) ; crochet qui sauvegarde `xmm0`–`xmm7` ; journal une ligne par groupe ; côté Lua de la vitesse (`extension_windows/lua/cc2_vitesse_shim.lua` à coller en tête de `library_custom_6.lua`).
- **Ce qui est vérifié** : elle compile sur Linux avec Zig 0.15.2 (`pip install ziglang==0.15.2`, commandes exactes dans `extension_windows/BUILD.txt`) ; 48 tests / 732 contrôles réussis sur une fausse mémoire (refaits sur le Mac le 26/10, mêmes résultats) ; le crochet a été exécuté pour de vrai dans un programme 32 bits sous Linux.
- **Ce qui ne l'est PAS** : rien n'a jamais tourné sous Windows ni dans le jeu, ni chargé par le vrai SDK. C'est **à toi, la tour, de le prouver** à l'étape 2 (chargement, journal) puis à l'étape 3 (premiers groupes).
- **Règle de propriété (complète la section 12)** : à partir de l'étape 3, la **tour** écrit dans `extension_windows/` (listes de retouches, corps des crochets) en plus de `tour/` et du journal ; le Mac et le cloud n'y touchent plus sans que le moddeur le dise. Les octets d'origine à écrire dans les listes sont ceux **du fichier `.exe`** (base `0x400000`), pas ceux du jeu en marche.
- **Compilation sur la tour** : `python extension_windows/build.py` (cherche seul `cc2x.h` dans `passation_windows/sdk_public_cc2x/`). Il faut Zig 0.15.2 : voir section 4 pour les accords à demander. La DLL (`dist/`) n'est jamais dans le dépôt.

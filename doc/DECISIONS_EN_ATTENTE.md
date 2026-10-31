# Décisions et essais qui attendent le moddeur

Tiré des fiches de passation du 29/10/2026 (et, pour le Mac, de `DEMARRER_cc2_patchs.md`). **Une décision par ligne.** Le niveau de risque est celui **écrit dans la note** (🟢 faible, 🟡 moyen, 🔴 élevé) ; *non indiqué* veut dire que la note n'en donne pas : ce document n'en invente pas.

**Règles du moddeur à garder en tête avant toute ligne** (`tour/PASSATION_coordination_29-10.md:9` à `:18`) : une seule question à la fois ; dire ce que fait l'action, son risque et une alternative plus sûre avant toute autorisation ; ne jamais lancer ni fermer le jeu sans demande dans le message en cours ; un « oui » ne vaut que pour la phase demandée ; citer ses mots exacts quand on transmet un accord ; préférer les outils faits maison aux programmes tiers téléchargés ; aucun commit ni push sans son accord (l'accord du 29/10 ne vaut que pour ce push, `tour/PASSATION_coordination_29-10.md:92`).

**Rien ici n'a été fait** : cette session ne peut pas lancer le jeu et n'a pas touché aux fichiers du jeu.

## 1. Les décisions de la carte de coordination (dans l'ordre recommandé)

Source commune : `tour/PASSATION_coordination_29-10.md:76` à `:88`. Entre parenthèses, la fiche de détail du chantier.

| # | Décision ou essai | Ce qu'on attend du moddeur | Risque indiqué | Alternative plus sûre (si la note en donne une) |
|---|---|---|---|---|
| 1 | **Modes carburant** : poser l'onglet v2 + le plugin v3 (`tour/etudes_modes_carburant/PASSATION.md`) | Accord : « accord pour poser l'onglet v2 + plugin v3 ? » (`tour/PASSATION_coordination_29-10.md:76`) ; jeu fermé, via l'ancien exe pour que le plugin tourne | Poser les fichiers : 🟢 (`tour/etudes_modes_carburant/PASSATION.md:6`) ; voir lignes 21-22 pour la suite | Rester sur la v1 posée, sans rien faire (`tour/etudes_modes_carburant/plugin/RISQUES_v3.md:45`) |
| 2 | **Atterrissage à la main** : suite = prise en charge de l'avion posé | Un plan à lui montrer d'abord ; l'essai demande que le moddeur pilote (`tour/PASSATION_coordination_29-10.md:77`) | non indiqué ici (chantier **en cours** ailleurs, `tour/atterrissage_manuel/`) | non indiquée ici |
| 3 | **Mise à jour Steam** : porter les patchs d'exe et le SDK sur le nouvel exe, ou rester sur l'ancien exe patché lancé à part (`tour/etude_mise_a_jour/PASSATION.md`) | Choisir ; question exacte : « Porter les patchs d'exe et le SDK sur le nouvel exe de Steam (suit les mises à jour futures, demande du travail et des essais), ou rester sur l'ancien exe patché lancé à part ? » (`tour/PASSATION_coordination_29-10.md:78`) | Porter : 🟡 « nouveau code d'exe, jamais essayé en jeu » ; SDK : 🟢 tel quel / 🔴 si on le « force » (`tour/etude_mise_a_jour/ETUDE.md:46` ; `tour/etude_mise_a_jour/ETUDE.md:47`). Rester (voie A) : 🟢 (`tour/etude_mise_a_jour/ETUDE.md:107`) | Voie A, « recommandée, la plus sûre » (`tour/etude_mise_a_jour/ETUDE.md:98`) |
| 3 bis | **Ranger dans `tour/sauvegardes/`** une copie du nouvel exe `461E1262…` et de l'ancien patché reconstruit `0C5DFE52…` | Accord (« NON fait ») (`tour/etude_mise_a_jour/PASSATION.md:15`) | non indiqué (les exe ne vont pas sur GitHub) | Ne pas ranger ; la reconstruction reste dans un dossier temporaire (`tour/etude_mise_a_jour/PASSATION.md:13`) |
| 4 | **Circuit d'atterrissage** : essais 2 et 3 (4 avions chacun) avec la copie d'essai (c), double-clic direct, pas par Steam (`tour/etudes_circuit_atterrissage/PASSATION.md`) | Lancer les essais ; accord, jeu normal fermé, partie neuve, navire à l'arrêt (`tour/etudes_circuit_atterrissage/PASSATION.md:6`) | Mesurer : 🟢 ; poser le créneau : 🟡 (`tour/etudes_circuit_atterrissage/ETUDE.md:108`) | S'arrêter après 1 plantage ou 1 approche ratée (`tour/etudes_circuit_atterrissage/ETUDE.md:109`) |
| 5a | **Missiles** : « Je prépare ce patch sur une copie seulement ? » (patch `ir_portee`, copie du nouvel exe) (`tour/etudes_missiles/PASSATION.md:18`) | Réponse oui/non | 🟡 pour le patch ; « pas de risque de plantage attendu » (`tour/etudes_missiles/PASSATION.md:22`) | Contournement sans patch : tirer à moins de ~4 km, 🟢 (`tour/etudes_missiles/DIAGNOSTIC.md:183`) |
| 5b | **Missiles** : corriger `tour/etudes_missiles/DIAGNOSTIC.md` avec les 3 corrections du Mac | Accord (`tour/etudes_missiles/PASSATION.md:19`) | non indiqué (documentation) | — |
| 5c | **Missiles** : dire à quelle distance du bateau il tire et quel missile (IR ou anti-aérien) | Une information (`tour/etudes_missiles/PASSATION.md:20`) | — | — |
| 6 | **Démarrage automatique**, premier essai guidé (E3) (`tour/etudes_demarrage_auto/ETUDE.md`) | « OK pour écrire `rom_0\scripts\library_custom_0.lua` (🟡) et créer le mod interrupteur ? » (`tour/PASSATION_coordination_29-10.md:81`) | 🟡 pour le fichier du jeu ; 🟢 pour le mod interrupteur (`tour/etudes_demarrage_auto/ETUDE.md:8`) | Option D, clics simulés, sans rien écrire dans le dossier du jeu (`tour/etudes_demarrage_auto/ETUDE.md:142`) |
| 6 bis | **Démarrage automatique** : faire aussi E2 (sauvegarde de test) pendant ce premier essai ? | « Question restée sans réponse » (`tour/etudes_demarrage_auto/ETUDE.md:8`) | 🟢/🟡 : 🟡 seulement si le slot contient une vraie partie (`tour/etudes_demarrage_auto/ETUDE.md:131`) | Sauvegarder d'abord le dossier des sauvegardes (`tour/etudes_demarrage_auto/ETUDE.md:133`) |
| 7 | **Chargeur maison** : arrêter ou autoriser la phase P1 | « arrêter (ma recommandation, en gardant les 3 habitudes de sa fiche) » ; autoriser P1 demande un « oui, P1 » explicite (`tour/PASSATION_coordination_29-10.md:82`) | non indiqué | Arrêter : depuis la mise à jour le SDK est inactif, l'urgence de le retirer a disparu (`tour/PASSATION_coordination_29-10.md:82`) |
| 8 | **PvP / PvE** : quel scénario, quel mod, et accord pour un essai solo sans mod (jeu lancé par le moddeur) (`tour/scenario_pvp/ETUDE.md`) | « quel scénario (PvP 5 contre 5 terrestre, ou PvE coop contre l'IA : il hésite) » (`tour/PASSATION_coordination_29-10.md:83`) | Essai solo sans mod : 🟢 (`tour/scenario_pvp/ETUDE.md:309`) ; mod de constantes 🟢, mod avec Lua 🟡 | — |
| 8 bis | **Usine à argent** : mesurer d'abord le revenu actuel | « On commence par mesurer le revenu actuel (écran Rapport de devises, toutes les 5 min pendant 30 min), sans aucun fichier ? » (`tour/PASSATION_coordination_29-10.md:84`) | « aucun risque, rien de touché » (`tour/etude_usine_argent/ETUDE.md:29`) | — |
| 8 ter | **Idées** : re-porter `pont_retour_x2` puis `helicos_approche_x2` sur le nouvel exe (sur copie), puis les poser un à un avec une mesure entre les deux | Accord ; l'accord du 28/10 « ne vaut plus pour le nouvel exe » (`tour/idees_et_demandes/PASSATION.md:8`) ; se règle avec la décision 3 (`tour/PASSATION_coordination_29-10.md:85`) | 🟢 sur copie, 🟡 à la pose sur le vrai exe (`tour/idees_et_demandes/IDEES.md:54`) | — |
| 9 | **Idées** : quelle idée prendre en tête | Un choix ; la note recommande la n° 2 pour un gain vite et sûr (`tour/idees_et_demandes/IDEES.md:27`) | non indiqué | — |
| 10 | **GitHub / Mac** : informer le Mac de la mise à jour (son jeu va probablement se mettre à jour aussi, INFÉRÉ) et lui demander de relire | Accord ; la partie commit et push a été réglée par l'accord du 29/10 (`tour/PASSATION_coordination_29-10.md:92`) | non indiqué | — |
| 11 | **Hors liste** : bug des waypoints (apparu avec Revolution) et vrai test multijoueur | « jamais commencés » (`tour/PASSATION_coordination_29-10.md:88`) | Test multijoueur : 🟡 (`tour/idees_et_demandes/IDEES.md:56`) | — |

## 2. Autres décisions et essais tirés des fiches, par chantier

### Modes carburant (`tour/etudes_modes_carburant/`)

| Décision ou essai | Ce qu'on attend du moddeur | Risque indiqué | Alternative | Source |
|---|---|---|---|---|
| (b) Lancer le jeu par l'ancien exe en observation (`enabled=0`) | Accord, jeu fermé, partie neuve jetable | 🟡 faible | Étape A3 seule, ou commandes à la main | `tour/etudes_modes_carburant/PASSATION.md:6` ; `tour/etudes_modes_carburant/plugin/RISQUES_v3.md:38` |
| (c) Activer ÉCO puis FLANK sur UN avion seul à plus de 6 km du bateau | Accord explicite, ÉCO d'abord | ÉCO 🟡 moyen ; FLANK 🟡 moyen à élevé | Faire seulement l'ÉCO du Manta, laisser FLANK de côté ; piloter à la main à pleins gaz | `tour/etudes_modes_carburant/PASSATION.md:6` ; `tour/etudes_modes_carburant/plugin/RISQUES_v2.md:50` |
| Choix de la voie après la mise à jour : SDK porté, ou chargeur maison | « décision du moddeur plus tard » ; P1 du chargeur non accordée | non indiqué ; profil dans le SDK tiers « déconseillé » | Voie A (ancien exe patché lancé à part) | `tour/etudes_modes_carburant/PASSATION.md:10` ; `tour/etudes_modes_carburant/ETUDE.md:488` |
| Persistance des modes dans un fichier (version 2), maquette 3, multijoueur | « si tu le veux » / « seulement si tu le demandes » | non indiqué | Version 1 en mémoire (recommandée) | `tour/etudes_modes_carburant/ETUDE.md:150` ; `tour/etudes_modes_carburant/ETUDE.md:252` |

### Circuit d'atterrissage et roulage de retour (`tour/etudes_circuit_atterrissage/`, `tour/etudes_roulage_retour/`)

| Décision ou essai | Ce qu'on attend du moddeur | Risque indiqué | Alternative | Source |
|---|---|---|---|---|
| Poser cercle / créneau sur le vrai exécutable | Accord séparé, « jamais donné » ; prévenir la conversation d'atterrissage à la main ; nouvelle sauvegarde, jeu fermé | 🟡 | Poser d'abord le cercle (aucun saut) ; l'outil répond « INCONNU » sur l'exe de Steam | `tour/etudes_circuit_atterrissage/PASSATION.md:6` ; `tour/etudes_circuit_atterrissage/PASSATION.md:8` |
| Porter cercle et créneau sur le nouveau build | Décider d'abord de la voie A/B | « calculs sur copies, rien dans le jeu » | Voie A | `tour/etudes_circuit_atterrissage/PASSATION.md:6` ; `tour/etudes_circuit_atterrissage/PASSATION.md:10` |
| Faire ou non le site facultatif C4 | « choix à ta main » | non indiqué | Recommandation de l'étude : ne pas le faire | `tour/etudes_circuit_atterrissage/ETUDE.md:80` |
| Poser les deux modules en une fois ou un par un | Choix | 🟡 | Un à la fois | `tour/etudes_circuit_atterrissage/ETUDE.md:110` |
| Valider les critères de réussite des essais | Validation | non indiqué | — | `tour/etudes_circuit_atterrissage/ETUDE.md:121` |
| Mesurer `pont_retour_x2`, puis poser `helicos_approche_x2` (un module à la fois) | Accord pour le 2e module après la mesure du 1er | 🟡 (4 octets dans le vrai exe) ; `pont_retour_x2` a été effacé par la mise à jour (rapporté) | Copie d'essai | `tour/etudes_roulage_retour/ETUDE.md:62` ; `tour/etudes_roulage_retour/ETUDE.md:54` |

### Démarrage automatique, missiles, PvP, idées, usine à argent

| Décision ou essai | Ce qu'on attend du moddeur | Risque indiqué | Alternative | Source |
|---|---|---|---|---|
| E1 : cocher Revolution et charger le slot 19 (« Attendu : ça charge. ») | Essai de 5 min, sans outil | 🟢 faible, au pire un plantage | Se contenter du vérificateur hors jeu | `tour/etudes_demarrage_auto/ETUDE.md:125` ; `tour/etudes_demarrage_auto/ETUDE.md:129` |
| Choix du slot de sauvegarde (10, 11 ou 14) et du jeu de mods du test | Choix | 🟡 seulement si le slot contient une vraie partie | Sauvegarder d'abord `saved_games\` | `tour/etudes_demarrage_auto/ETUDE.md:155` ; `tour/etudes_demarrage_auto/ETUDE.md:133` |
| Missiles : essai à la main sans modification (verrou T, missile IR puis AA sur un ennemi isolé) | « Aucun accord technique nécessaire » | 🟢 | — | `tour/etudes_missiles/DIAGNOSTIC.md:119` |
| Missiles : sonde Lua en lecture seule (option A) | Accord, jeu fermé, une ligne dans `mods.xml` avec sauvegarde | 🟢 « retirable en une ligne » | Retirer la ligne | `tour/etudes_missiles/DIAGNOSTIC.md:110` |
| Missiles : essai avec/sans le mod de vitesse 2937532682 | Accord pour le désactiver le temps d'un essai | 🟢 (option C) | — | `tour/etudes_missiles/DIAGNOSTIC.md:87` |
| Missiles : patch du guidage (« verrou transmis ») | « un accord séparé » pour chaque étape | 🔴 pour l'hypothèse H5 ; 🟡 pour la seule portée | `patch_exe.py retirer` ou la sauvegarde | `tour/etudes_missiles/DIAGNOSTIC.md:127` ; `tour/etudes_missiles/DIAGNOSTIC.md:185` |
| PvP : quel mod préparer (constantes minimal, ou mod complet avec Lua et arbitre) | Choix | 🟢 (constantes) / 🟡 (Lua) | — | `tour/scenario_pvp/ETUDE.md:8` |
| PvP : héberger la partie de test (T0) avec mot de passe | Lancer lui-même l'hébergement, fermer le jeu après | 🟡 « héberger ouvre une partie réseau » | Essai solo | `tour/scenario_pvp/ETUDE.md:243` |
| PvP : retirer `temps_x2` et `pont_retour_x2` avant un essai | Accord — devenu **sans objet** tant que l'exe est celui de Steam | 🟡 (`tour/scenario_pvp/ETUDE.md:228`) | — | `tour/scenario_pvp/ETUDE.md:12` |
| Idées : remettre les mods perso (drapeau, livrées, ciel violet…) | Accord, « quand les essais seront finis » | 🟢 | — | `tour/idees_et_demandes/IDEES.md:58` |
| Idées : Revolution est-il remis ? (question préalable au bug des waypoints) | Réponse | non indiqué | — | `tour/idees_et_demandes/IDEES.md:21` |
| Idées 20 et 21 (mode fenêtré ; scénario 3 porte-avions / 6 Manta) | Reposer la question / préciser | non indiqué | — | `tour/idees_et_demandes/IDEES.md:72` ; `tour/idees_et_demandes/IDEES.md:73` |

## 3. Côté Windows : jamais mesuré, jamais décidé

| Décision ou essai | Ce qu'on attend du moddeur | Risque indiqué | Alternative | Source |
|---|---|---|---|---|
| Mesure de la **sortie** des 4 avions avec `ascenseur_x2` (jamais chronométrée) | Faire le geste lui-même (~10 minutes) pendant que le mod de mesure note les temps ; ne séparer borne et diviseur de la grue que si la sortie dépasse nettement 2:25 | non indiqué | Garder le patch tel quel | `passation_windows/JOURNAL_tour.md:384` ; `passation_windows/JOURNAL_tour.md:170` |
| Mesure de **référence du jeu d'origine** sur la tour (« étape 0 bis »), dont les hélicos (2 Razorbill puis 2 Petrel) | Lancer le jeu et jouer | non indiqué | — | `passation_windows/REPONSES_mac_pour_la_tour.md:170` ; `passation_windows/JOURNAL_tour.md:118` |
| Suite du bug des waypoints : jouer sans Revolution, mettre le mod à jour, ou faire un mod correctif | Choisir | non indiqué | Jouer sans Revolution | `passation_windows/JOURNAL_tour.md:222` |
| Hébergement : jeu normal ou serveur dédié ? | Répondre | non indiqué | — | `passation_windows/JOURNAL_tour.md:29` |
| Avait-il déjà chargé une sauvegarde depuis les patchs, ou seulement lancé des parties neuves ? | Répondre | sans objet | Tests proposés dans le journal | `passation_windows/JOURNAL_tour.md:318` |
| Mod Island Airfields : regarder le bandeau de retrait sur la page Workshop | Regarder la page à l'œil | non indiqué | Ne rien installer | `passation_windows/JOURNAL_tour.md:98` |
| Journal des atterrissages qui recouvre la moitié basse de la carte | Le demander s'il veut le réduire | non indiqué | — | `passation_windows/JOURNAL_tour.md:154` |
| Étapes du test du **frein seul** (clone du SDK, relecture, compilation, pose des DLL, essai, retrait), proposées par le Mac le 27/10 | Un accord **séparé** par étape | Étapes 1-3 et 6 : 🟢 ; étapes 4 et 5 : 🟡 | Plan B, crochets à nous sans SDK (plusieurs jours) | `passation_windows/NOTE_mac_frein_seul_27-10.md:20` à `:25` ; `passation_windows/NOTE_mac_frein_seul_27-10.md:27` |
| Doubler aussi la 8e lecture de 2,5 du roulage (début de tronçon) | Décision de la tour après la réponse du Mac | non indiqué | Ne pas la doubler « par prudence » (état actuel) | `tour/questions_pour_le_mac.md:26` ; `tour/questions_pour_le_mac.md:18` |
| Installer le SDK (trois accords séparés : outil de compilation, compilation, dépôt de la DLL) | Accords séparés ; méthode mise en réserve depuis le 27/10 (`DEMARRER_cc2_patchs.md:372`) | non indiqué | Patch direct sans SDK | `passation_windows/PASSATION_windows.md:83` |
| Extension C : copier la DLL, allumer **un groupe à la fois**, lancer le jeu et lire le journal | Accord à chaque étape | non indiqué | Retour arrière : supprimer la DLL (`extension_windows/README_FR.md:87`) | `extension_windows/BUILD.txt:66` ; `extension_windows/README_FR.md:75` |
| Extension C : décider du groupe « recorder » et de « cctv » | Décision ; « Seulement si le moddeur le demande. » pour le CCTV | non indiqué | Adapter `passation_windows/lua_a_installer/library_custom_5.lua` pour écrire dans `cc2x.log` (jugé plus simple) | `extension_windows/RAPPORT_cloud.md:243` ; `extension_windows/RAPPORT_cloud.md:244` |
| Essai automatique avec écriture dans le script d'un emplacement vide du dossier du jeu | Accord explicite (`--accord-dossier-jeu`) | non indiqué (le fichier est remis vide) | Script posé comme mod (ne s'exécute pas dans le menu) | `tour/auto/LISEZ-MOI.md:41` ; `tour/auto/LISEZ-MOI.md:40` |
| Vérifications du Mac après la mise à jour (version installée, empreinte du binaire, chaîne `support_sign_in`) | Demander à la session Mac | non indiqué (lecture seule) | Comparer la tour sur l'ancien exe et le Mac sur son build actuel | `tour/etude_mise_a_jour/ETUDE.md:119` ; `tour/etude_mise_a_jour/ETUDE.md:120` |
| Voie C : ramener tout le jeu à l'ancien build par Steam | Accord explicite | 🟡 (≈ 1,3 Go téléchargés ; commande « INFÉRÉ, non testée ») | Voie A (« Inutile tant que la voie A suffit ») | `tour/etude_mise_a_jour/ETUDE.md:112` |

## 4. Côté Mac : essais en jeu jamais faits, d'après `DEMARRER_cc2_patchs.md`

Ces patchs sont déjà **actifs** (à la date des notes) ; l'essai attend le moddeur. Aucune note du Mac ne donne d'échelle 🟢🟡🔴 : seuls les risques écrits sont repris.

| Essai | Ce qu'on attend du moddeur | Risque écrit | Parade | Source |
|---|---|---|---|---|
| `effet_tele` : vérifier l'interface de pilotage sans effet vieille télé | Vérifier en jeu | non indiqué | Retrait par le menu de l'atelier | `DEMARRER_cc2_patchs.md:232` |
| 1re vraie partie avec le relevé, puis les courbes | Jouer ~10 min, dire « fini » ; alléger le relevé (un seul écran de données sur 3) | non indiqué | — | `DEMARRER_cc2_patchs.md:23` ; `DEMARRER_cc2_patchs.md:306` |
| Mesurer le jeu d'origine d'atterrissage (essai sans le module) | « peut-être plus tard » | non indiqué | Simulateur `outil/generateurs/simuler_file_atterrissage.py` | `DEMARRER_cc2_patchs.md:261` |
| Mesurer `pont_retour_x2` avec le protocole du 23/10 | Refaire l'essai (même sauvegarde, 4 avions) | « collision : aucun nouveau » (`etudes/piste_et_pont.md:86`) | La mesure automatique du 25/10 existe, avec un autre mélange d'avions | `DEMARRER_cc2_patchs.md:270` |
| `grue_annulation` : annuler pendant que la grue va à la baie, porte l'avion, le pose ; baie de droite à la rotation (doit refuser) ; 2 avions ; sauvegarder pendant un retour | Essai en jeu | Grue bloquée : plus de lancement ni d'atterrissage | Retirer le module | `DEMARRER_cc2_patchs.md:324` ; `DEMARRER_cc2_patchs.md:325` ; `etudes/annuler_montee.md:114` |
| `cctv_net` : caméras plus fines, cadre et boutons entiers, autres écrans inchangés | Essai en jeu | Interface coupée ou dans un coin | Retirer le module | `DEMARRER_cc2_patchs.md:334` ; `DEMARRER_cc2_patchs.md:336` |
| Barre de vitesse et `vitesse_escadrille` ; régler NORMAL (≈ 80 %) | Essai en jeu (un Albatros vers un point lointain en ECO puis FLANK) | non indiqué | Retirer les deux modules | `DEMARRER_cc2_patchs.md:351` ; `DEMARRER_cc2_patchs.md:354` |
| Modes de **transit** : changer aussi le 120 du régulateur ? terminer le test près du point ? | Décision non attribuée | non indiqué | — | `DEMARRER_cc2_patchs.md:367` |
| 2e ascenseur « si tu le veux malgré tout » | Choix ; 1re étape = une maquette sans toucher au jeu | Collisions fausses, puits qui traverse le hangar, appareil coincé, sauvegarde en plein cycle | A1 (abandonné), ascenseur ×3 | `etudes/RESULTATS_etude.md:184` ; `etudes/RESULTATS_etude.md:188` |
| B' : roulage plus rapide au départ | À mesurer d'abord (le journal ne chronomètre que les retours) | « faible » (tableau) | Apprendre au journal à chronométrer les départs | `etudes/piste_et_pont.md:13` ; `etudes/piste_et_pont.md:139` |
| Envoi à d'autres moddeurs (paquet `envoi_native_bridge/`) | **C'est le moddeur qui envoie**, sans archive ; accord avant tout envoi | « sans info perso, recherche finale = 0 » | — | `DEMARRER_cc2_patchs.md:373` ; `tour/idees_et_demandes/IDEES.md:68` |
| Branche non fusionnée `revue_cloud` + 2 tâches cloud restantes | Lancer / fusionner ; crédit « à dépenser avant le 05/11 à 8 h 59 » | non indiqué | — | `DEMARRER_cc2_patchs.md:371` ; `DEMARRER_cc2_patchs.md:372` |
| Mettre à jour `partage/` si les patchs changent | Session Mac | non indiqué | — | `DEMARRER_cc2_patchs.md:379` |

## 5. À ne pas oublier (pièges que les fiches signalent)

- Un « oui » général n'est pas un accord de phase : `chargeur-maison` s'est trompée ainsi (`tour/PASSATION_coordination_29-10.md:99`) ; `idees-et-demandes` a posé `pont_retour_x2` après un accord ambigu (`tour/PASSATION_coordination_29-10.md:100`).
- Une conversation qui annonce un test concluant n'est pas une preuve : vérifier la sortie (`tour/PASSATION_coordination_29-10.md:18`).
- Ne pas cliquer sur « Vérifier l'intégrité des fichiers » sans y penser : cela remet aussi à zéro les ajouts dans le dossier du jeu (`tour/PASSATION_coordination_29-10.md:102`).
- Multijoueur jamais testé avec de vrais joueurs ; pour des parties avec des amis, le plus sûr est l'exe de Steam non patché et les mods `cc2_*` désactivés (`tour/PASSATION_coordination_29-10.md:104`).

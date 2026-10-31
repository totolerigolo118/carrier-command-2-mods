# Carte des dossiers du dépôt

Ce document dit à quoi sert chaque dossier, ce qui est en double ou périmé, et par où commencer. Il décrit le dépôt tel qu'il est au 29/10/2026 (117 fichiers .md / .txt ; 347 fichiers suivis par git avant l'ajout de `doc/`). Les comparaisons « identique » ont été faites octet à octet pour ce document (outil `cmp`) ; les autres affirmations citent la note qui les porte. Rien n'a été déplacé ni modifié dans les dossiers existants.

## 1. Par où commencer

| Vous voulez… | Lisez dans cet ordre |
|---|---|
| **Reprendre la coordination des études Windows** (la « tour ») | 1. `tour/PASSATION_coordination_29-10.md` (carte de toutes les conversations, exe, décisions ; elle-même dit de commencer par elle, `tour/PASSATION_coordination_29-10.md:109`) ; 2. `tour/etude_mise_a_jour/ETUDE.md` § 0 (la mise à jour Steam du 28/10) ; 3. la section « ÉTAT À LA PASSATION » en tête de la fiche de chaque chantier (liste dans `tour/PASSATION_coordination_29-10.md:60`) |
| **Comprendre ce qui existe côté Mac** (patchs validés) | `DEMARRER_cc2_patchs.md` (« À lire en premier », mais son en-tête est daté du 25/10 et ses statuts sont en partie périmés : voir `doc/CONTRADICTIONS.md`), puis l'étude concernée dans `etudes/` |
| **Voir le point sur Windows en un coup d'œil** | `doc/ETAT_DES_LIEUX.md`, puis `passation_windows/JOURNAL_tour.md` (journal chronologique du 26/10 au 29/10 ; aucune entrée pour le 28/10) |
| **Savoir ce qui attend le moddeur** | `doc/DECISIONS_EN_ATTENTE.md`, qui renvoie aux fiches de passation |
| **Lire en tant que nouvelle session Claude** | Les règles permanentes du moddeur sont dans `tour/PASSATION_coordination_29-10.md` § 1 et dans `DEMARRER_cc2_patchs.md` § 2 (une seule question à la fois ; ne jamais lancer ni fermer le jeu sans demande dans le message en cours ; dire le risque 🟢/🟡/🔴 avant toute action qui demande une autorisation) |

## 2. Dossier par dossier

| Dossier ou fichier | À quoi il sert | Statut |
|---|---|---|
| `DEMARRER_cc2_patchs.md`, `LISEZ-MOI.txt` (racine) | Fiche d'état maître côté Mac ; mode d'emploi utilisateur de l'atelier | `DEMARRER_cc2_patchs.md` : actif, mais l'en-tête dit « Dernière mise à jour : 25/10/2026 » alors que le texte va jusqu'au 27/10 (`DEMARRER_cc2_patchs.md:4`) ; `LISEZ-MOI.txt` : **périmé en partie** (liste 9 modules au 24/10, il y en a 14 : `LISEZ-MOI.txt:14`) |
| `Atelier CC2 (activer ou retirer les patchs).command`, `Tout remettre CC2 d origine.command` | Boutons à double-clic de l'atelier Mac | Actifs **sur le Mac seulement** (chemin du Mac en dur) |
| `outil/` | Cœur de l'atelier Mac : `outil/patchs_cc2.py` (moteur), `outil/modules/` (14 modules actifs), `outil/modules_en_reserve/` (8 fichiers), `outil/generateurs/` (scripts qui écrivent les tables de retouches), `outil/courbes/`, `outil/tests_en_jeu/` | Actif (Mac). Dans `outil/modules_en_reserve/`, 4 fichiers (cctv_net, ecriture_releve, helicos_approche_x2, helicos_pres_ascenseur) sont des **copies identiques** des modules de `outil/modules/` |
| `fichiers/` | Fichiers de remplacement des modules « fichier » (Lua, shader) | Actif (Mac) ; **doublon** de `passation_windows/lua_a_installer/` et `passation_windows/shader_effet_tele/` |
| `tests/` | Tests hors jeu sur copies, à relancer après chaque ajout de module (`tests/test_patchs.py:8`) | Actif ; dépend de `sauvegarde/` et du jeu Mac, absents du dépôt (`.gitignore`) |
| `courbes/` | 2 pages de courbes du lag du 25/10 (générées) | Sorties ; leurs noms diffèrent du motif décrit dans `DEMARRER_cc2_patchs.md:81` |
| `maquette_camera_cc2.html`, `maquette_courbes_cc2.html` (racine) | Maquettes (6 variantes caméra, 6 présentations de courbes) | Historiques : le moddeur a choisi la variante 2 et la n° 1 (`DEMARRER_cc2_patchs.md:234` ; `DEMARRER_cc2_patchs.md:287`) |
| `etudes/` | Études Mac du 23-25/10 (hélicos, 2e ascenseur, piste et pont, grue, CCTV, vitesse IA) + 2 maquettes HTML | **Journal de bord, pas l'état final** (voir § 3) ; les 7 fichiers .md sont des **doublons** de `passation_windows/etudes_fr/` |
| `passation_windows/` | Dossier de passation Mac → tour (feuille `passation_windows/PASSATION_windows.md`, comparaison `passation_windows/COMPARAISON_MAC_WINDOWS.md`, journal de la tour, réponses et notes du Mac, copie du SDK public, Lua à installer) | Actif mais **privé** : « CE DOSSIER CONTIENT DES INFORMATIONS PERSONNELLES » (`passation_windows/NE_PAS_PARTAGER.txt:1`). Sous-dossiers : voir § 3 et § 4 |
| `passation_windows/JOURNAL_tour.md` | Journal de la tour (26/10 → 29/10) | À jour pour l'avancement Windows ; la tour l'écrit, le Mac ne le modifie pas (`tour/POINT_POUR_LE_MAC.md:16`) |
| `passation_windows/sdk_public_cc2x/` | Copie de lecture du SDK public CC2X (0.4.0, du 25/10) | **Incomplète** (le fichier internal.h est absent) et ancienne ; code d'un tiers (`passation_windows/sdk_public_cc2x/SOURCE.txt:5` ; `DEMARRER_cc2_patchs.md:372`) |
| `passation_windows/ancienne_passation_23-10/` | Première passation (ascenseur ×2) | **Partiellement obsolète** : « lis d'abord ../PASSATION_windows.md » (`passation_windows/ancienne_passation_23-10/PASSATION_ascenseur_x2_23-10.md:1`) |
| `partage/`, `passation_windows/reference_en/` | Notes en anglais nettoyées pour d'autres moddeurs (`passation_windows/NE_PAS_PARTAGER.txt:3`) (README + 3 fichiers) | **Doublon exact** l'un de l'autre. « ne les modifie jamais » (`passation_windows/PASSATION_windows.md:4`) |
| `partage_detail/` | Version détaillée en anglais (13 notes numérotées + `partage_detail/workshop/` : copie traduite et anonymisée de `outil/`, `fichiers/`, `tests/`) | Source interne des 3 fichiers de `partage/` : « ne pas envoyer » (`DEMARRER_cc2_patchs.md:379`) alors que son README le destine à un moddeur (`partage_detail/00_README.txt:5`) |
| `envoi_native_bridge/` | Paquet en anglais (symboles du binaire Mac, cycle de vie d'une partie, empreintes Windows) demandé par d'autres moddeurs | Prêt, **rien envoyé** (`DEMARRER_cc2_patchs.md:373`). les fichiers symbols_raw.txt et symbols_demangled.txt, cités par `envoi_native_bridge/README.txt`, ne sont pas suivis par git (`.gitignore`) |
| `extension_windows/` | Charpente C d'une extension du SDK (DLL), rapport d'une session cloud du 26/10 | En réserve : « n'est plus sur le chemin du premier essai » (`passation_windows/JOURNAL_tour.md:83`). `extension_windows/RAPPORT_cloud.md` contient des éléments personnels (identité git locale) |
| `tour/` | Tout le travail Windows (la « tour ») ; la tour écrit ici (`passation_windows/PASSATION_windows.md:202`) | Voir § 2 bis |

### 2 bis. Dans `tour/`

| Sous-dossier ou fichier | À quoi il sert | Statut |
|---|---|---|
| `tour/PASSATION_coordination_29-10.md` | Carte de passation de la coordination (exe, conversations, décisions, pièges) | **À lire en premier** |
| `tour/POINT_POUR_LE_MAC.md`, `tour/questions_pour_le_mac.md` | Point de reprise du 27/10 pour le Mac ; 3 questions de désassemblage | **Partiellement périmés** : écrits avant la pose du patch du 27/10 et avant la mise à jour du 28/10 (`tour/POINT_POUR_LE_MAC.md:8`). Les 3 questions ont reçu réponse (`passation_windows/REPONSES_mac_pour_la_tour.md`) |
| `tour/PROMPT_conversation_unique_29-10.md`, `tour/PROMPT_etude_atterrissage_manuel.md` | Textes de départ de conversations (29/10 ; 27/10) | Le premier couvre 4 chantiers seulement et demande de ne pas toucher aux autres dossiers (`tour/PROMPT_conversation_unique_29-10.md:26`) ; le second est antérieur à la mise à jour |
| `tour/etape1/`, `tour/etape3/` | Empreintes Mac → Windows (étape 1) ; relecture des 31 sites et rapports des modules d'exe (étape 3) | Historique, adresses de l'**ancien** exe seulement. Lire `tour/etape1/TABLEAU_mac_windows.md` avant `tour/etape1/resultats_etape1.md` (sortie brute de 1 240 lignes) |
| `tour/etude_mise_a_jour/` | Étude de la mise à jour Steam du 28/10 : `tour/etude_mise_a_jour/ETUDE.md`, `tour/etude_mise_a_jour/PASSATION.md`, `tour/etude_mise_a_jour/analyse/`, `tour/etude_mise_a_jour/avant/`, `tour/etude_mise_a_jour/apres/`, `tour/etude_mise_a_jour/outils/` | Terminée ; **à lire en premier** pour tout ce qui touche au nouvel exe. Les manifestes Steam (.acf) ne sont pas dans le dépôt (identifiant Steam personnel) |
| `tour/etudes_modes_carburant/` | Modes ÉCO / NORMAL / FLANK : étude, plugin v1-v3, mod, mesures du 28/10 | Actif ; lire `tour/etudes_modes_carburant/PASSATION.md` d'abord. `tour/etudes_modes_carburant/plugin/RISQUES_pose.md` est **périmé en partie** (v1) |
| `tour/etudes_circuit_atterrissage/` | Cercle d'attente + créneau de piste : étude, essai 1, modules | Actif ; lire `tour/etudes_circuit_atterrissage/PASSATION.md` d'abord ; § 5 et § 8 de `tour/etudes_circuit_atterrissage/ETUDE.md` partiellement dépassés |
| `tour/etudes_roulage_retour/` | `pont_retour_x2` et `helicos_approche_x2` pour Windows | Actif (modules à re-porter) ; l'état au 29/10 est dans `tour/idees_et_demandes/PASSATION.md` (`tour/etudes_roulage_retour/ETUDE.md:3`) |
| `tour/etudes_demarrage_auto/` | Démarrer directement sur une partie prête | Actif ; pas de PASSATION.md séparé, l'encadré est en tête de `tour/etudes_demarrage_auto/ETUDE.md` |
| `tour/etudes_missiles/`, `tour/scenario_pvp/`, `tour/idees_et_demandes/`, `tour/etude_usine_argent/` | Études en lecture seule (missiles, PvP/PvE, 21 idées, usine à argent) | Actives ; adresses de l'**ancien** exe seulement. `tour/scenario_pvp/ETUDE.md` contient un pseudo de jeu et des chemins de sauvegarde (à ne pas partager) |
| `tour/atterrissage_manuel/` | Atterrir un avion à la main, plugin de frein | **En cours** ailleurs : non modifié ni détaillé ici |
| `tour/outils/` | Outils Python/PowerShell de la tour : `tour/outils/patch_exe.py`, `tour/outils/modules_exe/` (6 modules JSON), banc d'essais, vérificateurs Lua | Actif ; propres à la tour (empreintes et chemins de la tour) : « Le Mac ne modifie pas ces fichiers » (`tour/POINT_POUR_LE_MAC.md:16`) |
| `tour/lua/`, `tour/auto/`, `tour/waypoints/` | Scripts Lua de mesure (SIM, SORTIES), banc d'essais automatiques (lancement automatique des avions abandonné le 27/10), empreintes de Revolution | Actifs ou historiques selon le cas ; voir `doc/ETAT_DES_LIEUX.md` § 3 |

## 3. Doublons et copies (vérifiés octet à octet pour ce document)

| Original | Copie | Remarque |
|---|---|---|
| `etudes/*.md` (7 fichiers) | `passation_windows/etudes_fr/*.md` | Identiques. Les 2 fichiers HTML de `etudes/` n'ont pas de copie. `passation_windows/etudes_fr/LISEZ-MOI.txt` prévient : « à lire comme un JOURNAL DE BORD, pas comme l'état final » (`passation_windows/etudes_fr/LISEZ-MOI.txt:1`) |
| `DEMARRER_cc2_patchs.md` | `passation_windows/etudes_fr/DEMARRER_cc2_patchs_ETAT_MAC.md` | La copie (395 lignes) n'a pas les lignes 362-374 de la racine (408 lignes) : mesures automatiques du 25/10 au soir, dépôt GitHub, charpente cloud, trois blocs du 27/10. Ailleurs identique |
| `partage/` (4 fichiers) | `passation_windows/reference_en/` (4 fichiers) | Identiques |
| `fichiers/horloge`, `fichiers/journal`, `fichiers/releve`, `fichiers/vitesse_boutons`, `fichiers/effet_tele` | `passation_windows/lua_a_installer/` (4 fichiers Lua), `passation_windows/shader_effet_tele/` | Identiques ; `passation_windows/ancienne_passation_23-10/library_custom_1.lua` est aussi identique à `passation_windows/lua_a_installer/library_custom_1.lua` |
| `outil/modules/` (4 modules) | `outil/modules_en_reserve/` | Copies identiques (`outil/generateurs/generer_cctv_net.py:13` : le générateur écrit les deux) |
| `outil/`, `fichiers/`, `tests/` (partie) | `partage_detail/workshop/` | **Aucun fichier identique** : traduit en anglais, chemins anonymisés. Même logique pour la majorité des fichiers (comparaison du code sans commentaires), pas relu ligne par ligne |
| `DEMARRER_cc2_patchs.md:364` à `:368` | `passation_windows/PASSATION_windows.md:56` à `:60` | Recopiés mot pour mot |
| `tour/outils/modules_exe/pont_retour_x2.json`, `tour/outils/modules_exe/helicos_approche_x2.json` | `tour/etudes_roulage_retour/modules/` | Même contenu cité par les deux études (`tour/etudes_roulage_retour/ETUDE.md:3`) |

## 4. Périmé ou à relire avec précaution

- **Recommandations abandonnées mais encore écrites** : `etudes/RESULTATS_etude.md` recommande « A1 » (hélicos sur l'ascenseur), essayé puis abandonné ; `etudes/piste_et_pont.md` parle d'un roulage ×3, c'est le ×2 qui est installé (`passation_windows/etudes_fr/LISEZ-MOI.txt:4` ; `passation_windows/etudes_fr/LISEZ-MOI.txt:5`). `passation_windows/PASSATION_windows.md:73` pose encore « Base = le SDK public CC2X », alors que le patch direct a été retenu le 27/10 (`DEMARRER_cc2_patchs.md:372`). Détails dans `doc/CONTRADICTIONS.md`.
- **Adresses** : toutes les adresses de `tour/` (étapes 1 et 3, études) valent pour l'**ancien** exe Windows ; le nouvel exe est décalé de +0xf0 à +0x130 dans la zone des sites de patch (`tour/PASSATION_coordination_29-10.md:40`). Les adresses du Mac (`DEMARRER_cc2_patchs.md`, `partage_detail/10_patch_tables.txt`) ne se transposent pas sur Windows (`DEMARRER_cc2_patchs.md:359`).
- **Fichiers .md/.txt qui dépendent d'un dossier absent** : voir § 5.

## 5. Cité par les notes mais absent du dépôt

- *tour/sauvegardes/* (copies d'exe : les `*.exe` sont ignorés par git, `.gitignore`) ; le nouvel exe `461E1262…` n'y est pas, il faut l'accord du moddeur (`tour/PASSATION_coordination_29-10.md:36`).
- *tour/chargeur_maison/*, *tour/JOURNAL_unique.md*, *tour/carte/*, *passation_windows/enregistreur_carte/* : dans des branches ou des worktrees à part (`tour/PASSATION_coordination_29-10.md:69` ; `tour/PASSATION_coordination_29-10.md:72`).
- *revue_cloud/FEUILLE_MAC_desassemblage.md* : branche `[branche]`, « non fusionnée » (`DEMARRER_cc2_patchs.md:372`).
- *passation_windows/REPONSES_mac_pour_la_tour_28-10.md* : cité par `tour/etudes_missiles/PASSATION.md:4`, introuvable ; le fichier existant est `passation_windows/REPONSES_mac_pour_la_tour.md` (voir `doc/CONTRADICTIONS.md`).
- Les manifestes Steam (fichiers .acf, `tour/PASSATION_coordination_29-10.md:92`) et les gros fichiers de symboles (`envoi_native_bridge/README.txt`).

## 6. Confidentialité (à respecter avant tout partage)

- Le dépôt est **privé** et contient des informations personnelles : ne jamais le rendre public ni partager son lien (`tour/POINT_POUR_LE_MAC.md:66`).
- **Destinés à d'autres moddeurs** : `partage/` et `passation_windows/reference_en/` (déjà envoyés d'après `passation_windows/PASSATION_windows.md:4`, « prêts » d'après `DEMARRER_cc2_patchs.md:377`), `envoi_native_bridge/` (rien envoyé).
- **Ne pas partager** : `passation_windows/` (`passation_windows/NE_PAS_PARTAGER.txt:2`), `extension_windows/RAPPORT_cloud.md`, `tour/scenario_pvp/ETUDE.md`, et plus généralement les fiches de `tour/` qui citent le moddeur.

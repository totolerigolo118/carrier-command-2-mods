# Contradictions entre les notes

Chaque entrée donne **les deux citations** (copiées telles quelles) et leurs fichiers. **Aucune n'est tranchée** : quand une remarque aide à comprendre, elle reste neutre. Beaucoup de désaccords viennent de notes écrites à des dates différentes, dont la plus ancienne n'a pas été marquée périmée ; c'est dit chaque fois que la source le permet.

**Repères** : la mise à jour Steam du **28/10/2026 à 21:30** a remplacé l'exe Windows par un exe recompilé (voir `tour/etude_mise_a_jour/ETUDE.md:8`). *Ancien* = avant, *nouveau* = après. *Mac* = `build_mac`, *Windows* = la tour. Aucune note du côté Mac ne parle de cette mise à jour.

Sommaire : **A** avant / après la mise à jour du 28/10 · **B** Mac contre Windows · **C** statuts de preuve qui ne se suivent pas · **D** recommandations abandonnées mais encore écrites · **E** inventaires, chemins, partage.

---

## A. Avant / après la mise à jour Steam du 28/10/2026 21:30

**A1. Le code du nouvel exe est-il décalé de façon « uniforme » ?** (autre : même étude, deux phrases)
- A : `tour/etude_mise_a_jour/ETUDE.md:46` « les 40 se retrouvent avec un décalage uniforme »
- B : `tour/etude_mise_a_jour/ETUDE.md:156` « le code est décalé de façon non uniforme (de +0 à +0x190 octets, par pas de 16 » ; `tour/PASSATION_coordination_29-10.md:40` « le code est décalé de façon non uniforme, +0xf0 à +0x130 dans nos sites »
- Remarque : le maximum du décalage s'écrit `0x190` (`tour/etude_mise_a_jour/ETUDE.md:11`), « jusqu'à ~0x1a0 octets » (`tour/etude_mise_a_jour/ETUDE.md:50`) et « VA 0x620480  decalage +0x1de » (`tour/etude_mise_a_jour/analyse/decalages_du_code.txt:32`). Le script de recherche libre donne « retrouves 23 sur 41 » (`tour/etude_mise_a_jour/analyse/sites_de_patch_dans_nouvel_exe.txt:42`) et le script à décalage fixe « coherents (decalage uniforme): 40 » (`tour/etude_mise_a_jour/analyse/sites_de_patch_dans_nouvel_exe.txt:44`). Autre phrase : « toutes les adresses fixes de nos outils sont fausses » (`tour/etude_mise_a_jour/ETUDE.md:11`) alors que l'adresse VA 0x401d80 est à « decalage +0x0 » (`tour/etude_mise_a_jour/analyse/decalages_du_code.txt:2`).

**A2. Quel est le dernier exe patché avant la mise à jour : `8E7FCBB6…` ou `0C5DFE52…` ?** (avant/après le 28/10 10:25, puis avant/après 21:30)
- A : `tour/etudes_circuit_atterrissage/ETUDE.md:150` « Le vrai `carrier_command.exe` est toujours `8E7FCBB6 » ; `tour/etudes_modes_carburant/ETUDE.md:476` « ni le patché de la tour (`8E7FCBB6 »
- B : `tour/etudes_circuit_atterrissage/ETUDE.md:204` « (modifié à 10:25:36) » (somme `0C5DFE52…`, avec `pont_retour_x2`) ; `tour/etude_mise_a_jour/ETUDE.md:9` « original + `ascenseur_x2` + `temps_x2` + `pont_retour_x2` → sha256 exact `0C5DFE52…` »
- Remarque : `tour/PASSATION_coordination_29-10.md:30` prévient que l'exe de la voie A n'est pas le second : « Piège : il n'a PAS `pont_retour_x2` ». `tour/etude_mise_a_jour/ETUDE.md:107` parle d'une copie `carrier_command_ancien_patche.exe` (la reconstruction), `tour/etude_mise_a_jour/PASSATION.md:14` d'une autre forme déjà posée. La commande de retour arrière du circuit vise toujours le premier (`tour/etudes_circuit_atterrissage/ETUDE.md:125` « (état actuel) ou la somme attendue »).

**A3. A-t-on touché au vrai jeu Windows ?** (états successifs des 27-28/10)
- A : `tour/POINT_POUR_LE_MAC.md:8` « rien n'a été fait sur le vrai jeu » ; `DEMARRER_cc2_patchs.md:372` « Rien n'a été essayé ni mesuré sur le vrai jeu Windows. » ; `tour/POINT_POUR_LE_MAC.md:60` « Rien dans le dossier du jeu. » ; `tour/etudes_roulage_retour/ETUDE.md:5` « Rien n'a été posé dans le jeu »
- B : `passation_windows/JOURNAL_tour.md:167` « Appliqué le 27/10 à 07:46 » ; `tour/etudes_roulage_retour/ETUDE.md:62` « `pont_retour_x2` POSÉ » ; `tour/PASSATION_coordination_29-10.md:37` « `dinput8.dll` (27/10, SDK »
- Remarque : le journal ne consigne pas l'accord du moddeur pour poser `dinput8.dll` (il écrit avant « sans `dinput8.dll`, sans SDK », `passation_windows/JOURNAL_tour.md:83`). Le journal n'a aucune entrée datée du 28/10 : ce jour n'y apparaît qu'à la ligne 405, dans l'entrée du 29/10 (`passation_windows/JOURNAL_tour.md:405`). `cc2x_frein.dll` est citée dès le 27/10 (`passation_windows/JOURNAL_tour.md:391`) mais datée du 28/10 par la fiche de coordination (`tour/PASSATION_coordination_29-10.md:37`). Pour le 28/10, la pose de `pont_retour_x2` est attribuée à « la conversation » « roulage retour » (`passation_windows/JOURNAL_tour.md:405`) ou à `idees-et-demandes` (`tour/PASSATION_coordination_29-10.md:100`).

**A4. Le patch direct et le SDK coexistent-ils ?** (avant/après)
- A : `tour/POINT_POUR_LE_MAC.md:40` « ne se gênent pas » ; `passation_windows/JOURNAL_tour.md:100` « Les deux voies peuvent coexister. »
- B : `tour/PASSATION_coordination_29-10.md:29` « donc aucun plugin ne tourne quand on lance le jeu par Steam »
- Remarque : A vaut pour l'ancien exe (même horodatage PE, donc le SDK s'active) ; B constate que le SDK est inactif sur le nouvel exe (`tour/etude_mise_a_jour/ETUDE.md:12`).

**A5. `cc2x_modes.dll` : posée ou absente ?** (après)
- A : `tour/PROMPT_conversation_unique_29-10.md:17` « Acquis : plugin `cc2x_modes.dll` v1 posé (observation seule) »
- B : `tour/etude_mise_a_jour/PASSATION.md:12` « `cc2x_modes.dll` absent »
- Remarque : la DLL est dans le dossier du mod `cc2_modes`, pas dans le dossier du jeu (`tour/etude_mise_a_jour/ETUDE.md:72`) ; les deux phrases peuvent être vraies, aucune note ne le dit.

**A6. « Voie B » a deux sens** (autre : même étude)
- A : `tour/etude_mise_a_jour/ETUDE.md:92` « Choisir entre **A** garder l'ancien exe patché à côté, **B** porter les patchs sur le nouvel exe (§5). »
- B : `tour/etude_mise_a_jour/ETUDE.md:110` « Voie B : remplacer `carrier_command.exe` de Steam par l'original puis re-patcher »
- Remarque : le § 5 ajoute une voie C (`tour/etude_mise_a_jour/ETUDE.md:112`). La question posée au moddeur est formulée en termes de porter ou rester, sans nommer A/B (`tour/etude_mise_a_jour/PASSATION.md:15`).

**A7. Les textes qui ont changé dans le nouvel exe** (autre)
- A : `tour/etude_mise_a_jour/ETUDE.md:34` « seuls changements lisibles »
- B : `tour/etude_mise_a_jour/analyse/textes_differents.txt:10` « - Gget_repair_factor »
- Remarque : quatre paires de chaînes ressemblent à des artefacts d'extraction (un caractère de tête) et l'étude ne les commente pas ; ce n'est pas établi.

**A8. L'extension C de la tour : jamais compilée, puis compilée** (même journal, deux dates)
- A : `passation_windows/JOURNAL_tour.md:62` « n'a jamais été compilé »
- B : `passation_windows/JOURNAL_tour.md:71` « L'extension compile »
- Remarque : `extension_windows/README_FR.md:20` et `extension_windows/RAPPORT_cloud.md` décrivent encore des « listes d'endroits vides » alors que la table des 31 sites de l'énergie est remplie (`passation_windows/JOURNAL_tour.md:49`). Nombre de contrôles : « 48 tests / 732 contrôles réussis » (`DEMARRER_cc2_patchs.md:371`) contre « 48 tests, 1 288 contrôles, 0 échec » (`passation_windows/JOURNAL_tour.md:72`) ; le journal lui-même ne réconcilie pas les deux.

---

## B. Mac contre Windows

**B1. Combien de retouches pour le groupe « ascenseur » ?**
- A : `DEMARRER_cc2_patchs.md:372` « 31 sites, Mac : 34 » ; `passation_windows/PASSATION_windows.md:111` « 34 retouches de constantes et 1 immédiat »
- B : `tour/etape3/module_exe_ascenseur_x2.md:7` « 32 changements de 4 octets chacun »
- Remarque : 32 = 31 sites + une valeur écrite dans l'en-tête (`tour/etape3/module_exe_ascenseur_x2.md:7`). 34 + 1 ferait 35 : INCERTAIN. Le compilateur explique une partie de l'écart (`tour/questions_pour_le_mac.md:14`).

**B2. Le roulage de retour : 3 lectures ou 1 ?**
- A : `tour/etudes_roulage_retour/ETUDE.md:20` « ont donné 0:51 → 0:32 par avion »
- B : `tour/etudes_roulage_retour/ETUDE.md:23` « Le `30,0` est lu **une seule fois**, au début de la boucle de la file »
- Remarque : sur le Mac, trois lectures sont redirigées ; sur Windows une seule. Conséquence déduite côté Windows : « le roulage des décollages pourrait aussi aller 2× plus vite » (`tour/etudes_roulage_retour/ETUDE.md:29`), ce que le Mac n'avait pas.

**B3. Circuit d'atterrissage : 10 retouches ou 6 ; 2,7 km ou 2,06 km**
- A : `tour/etudes_circuit_atterrissage/ETUDE.md:36` « Les 10 retouches du Mac et leur équivalent Windows » ; `tour/etudes_circuit_atterrissage/ETUDE.md:81` « 1 031 + 1 684 m = 2,7 km »
- B : `tour/etudes_circuit_atterrissage/ETUDE.md:11` « 6 changements de 4 octets » ; `tour/etudes_circuit_atterrissage/ETUDE.md:81` « 2,06 km est le bon calcul pour Windows »
- Remarque : l'étude explique 10 → 6 (`tour/etudes_circuit_atterrissage/ETUDE.md:53`) et le Mac a expliqué le 2,7 km par un artefact ; la fiche dit « ne pas viser 2,7 km » (`tour/etudes_circuit_atterrissage/PASSATION.md:8`).

**B4. Résultat attendu et mesuré du cercle**
- A : `tour/etudes_circuit_atterrissage/ETUDE.md:13` « Le Mac avait mesuré 7:28 et une piste toutes les 1:31 avec le même réglage. » ; `tour/etudes_circuit_atterrissage/ETUDE.md:94` « 7:30 à 8:30 (centre ≈ 7:45) » ; `tour/etudes_circuit_atterrissage/ETUDE.md:10` « Avec le cercle, un tour ne dure plus que 94 s »
- B : `tour/etudes_circuit_atterrissage/ETUDE.md:173` « FINI en 8:58 : 4 avions » ; `tour/etudes_circuit_atterrissage/ETUDE.md:186` « Mon estimation de 7:30 à 8:30 (occupation ≈ 95 s supposée) était trop optimiste » ; `tour/etudes_circuit_atterrissage/essais/essai1_trajets.txt:13` « 9.5 tours en 570 s -> 60 s par tour »
- Remarque : un seul essai, « un essai ne conclut pas » (`tour/etudes_circuit_atterrissage/ETUDE.md:185`). Le même fichier d'essai donne aussi « 4.6 tours en 450 s -> 98 s par tour » (`tour/etudes_circuit_atterrissage/essais/essai1_trajets.txt:5`). Les secondes du journal affiché et celles du journal du SDK « ne sont pas dans la même unité » (`tour/etudes_circuit_atterrissage/ETUDE.md:191`, marqué « Non résolu »).

**B5. Le diviseur de la grue : laissé ou doublé ; plafond 2 ou 1**
- A : `passation_windows/REPONSES_mac_pour_la_tour.md:150` « 1/6 (laissé) » ; `tour/POINT_POUR_LE_MAC.md:32` « le rapport allait jusqu'à 2 »
- B : `passation_windows/REPONSES_mac_pour_la_tour.md:151` « 1/3 (doublé avec la borne) » ; `passation_windows/JOURNAL_tour.md:57` « le rapport reste entre 0 et 1 »
- Remarque : sur Mac le diviseur reste à 1/6, sur Windows le patch de la tour le double ; l'effet (≈ 2 s de plus par avion) est « Calculé, pas mesuré » (`passation_windows/REPONSES_mac_pour_la_tour.md:153`).

**B6. La référence « 3:50 » de la sortie des 4 avions**
- A : `DEMARRER_cc2_patchs.md:11` « l'**ascenseur ×2** est fait et validé en jeu (sortie de 4 avions 3:50 → 2:15 en temps de » (côté Mac, avec l'horloge)
- B : `passation_windows/JOURNAL_tour.md:161` « C'est le **souvenir du moddeur** » ; `tour/POINT_POUR_LE_MAC.md:56` « la mesure d'origine Windows (3:50 ?) n'existe pas »
- Remarque : sur Windows, la sortie avec patch n'a jamais été chronométrée (`passation_windows/JOURNAL_tour.md:185`), seulement estimée « à l'œil » (`passation_windows/JOURNAL_tour.md:224`).

**B7. Vitesse de simulation de `temps_x2`**
- A : `passation_windows/JOURNAL_tour.md:196` « soit ≈ ×2,06 en temps réel »
- B : `passation_windows/JOURNAL_tour.md:223` « il indique ×1,33 »
- Remarque : le journal attribue l'écart à la machine, pas au patch (`passation_windows/JOURNAL_tour.md:226`). L'étude des modes de carburant ne mentionne ni `temps_x2` ni ×1,33 ; on ne sait pas si ses valeurs par seconde sont en temps de jeu (calcul de la relecture, pas une note).

**B8. Formules du Mac contre mesures Windows (modes carburant)**
- A : `tour/etudes_modes_carburant/ETUDE.md:99` « Autonomie à pleins gaz | ≈ 28 min | ≈ 17 min » ; `tour/etudes_modes_carburant/ETUDE.md:34` « (environ −33 % à 80 m/s »
- B : `tour/etudes_modes_carburant/ETUDE.md:323` « réservoir 800 → ~44 min à pleins gaz, et non 28 min comme calculé d'après le Mac » ; `tour/etudes_modes_carburant/ETUDE.md:393` « ≈ 2,75 (+16 %) »
- Remarque : « L'écart de 0,633 reste inexpliqué » (`tour/etudes_modes_carburant/ETUDE.md:452`) ; le résumé de tête et le tableau du § 2 ne sont pas corrigés. Même étude : ÉCO à « ~90 m/s » (`tour/etudes_modes_carburant/ETUDE.md:354`) contre « se stabilise à ≈ 80 m/s » (`tour/etudes_modes_carburant/ETUDE.md:390`).

**B9. Le Lua peut-il lancer ou rappeler un avion ?**
- A : `DEMARRER_cc2_patchs.md:365` « Le Lua peut lancer et rappeler des avions » ; (même fichier, plus haut) `DEMARRER_cc2_patchs.md:186` « Aucune commande Lua trouvée pour lancer ou rappeler un avion »
- B : `passation_windows/JOURNAL_tour.md:354` « `add_waypoint` n'est pas suffisant en partie neuve »
- Remarque : le journal avance une hypothèse (le test du Mac marchait parce que la sauvegarde plaçait le joueur à la console), non vérifiée.

**B10. Chargement d'une sauvegarde**
- A : `DEMARRER_cc2_patchs.md:364` « aucun plantage » (Mac, 14 modules, sauvegarde 18)
- B : `passation_windows/JOURNAL_tour.md:344` « Plantage au chargement d'une sauvegarde : 100 % » ; `tour/PASSATION_coordination_29-10.md:39` « plante (défaut connu, aussi sur le Mac) »
- Remarque : la mention « aussi sur le Mac » (`tour/PASSATION_coordination_29-10.md:39`) n'est étayée par aucune des notes lues. Sur Windows, les parties neuves « n'ont pas ce problème » (`passation_windows/JOURNAL_tour.md:333`) puis « elle tient 1 fois sur 2 environ » (`passation_windows/JOURNAL_tour.md:344`). Cause : « Hypothèse retenue (non prouvée) » (`passation_windows/JOURNAL_tour.md:333`) ; l'étude du démarrage auto la dit « probable, pas démontré en jeu » (`tour/etudes_demarrage_auto/ETUDE.md:74`), alors que d'autres fiches parlent d'une cause « connue » (`tour/etudes_circuit_atterrissage/ETUDE.md:113`).

**B11. Les emplacements `library_custom_N` sont-ils chargés partout ?**
- A : `DEMARRER_cc2_patchs.md:171` « fichiers vides chargés dans chaque écran **après** son script »
- B : `passation_windows/JOURNAL_tour.md:312` « les scripts d'un mod ne le sont qu'en partie »
- Remarque : la distinction fichier du jeu / script de mod n'existe pas côté Mac ; sur Windows elle est « Ce qui est établi (mesuré) » (`passation_windows/JOURNAL_tour.md:311`) après avoir été une hypothèse. Les numéros d'emplacement n'ont pas la même attribution (Mac : 1, 4, 5, 6, `DEMARRER_cc2_patchs.md:173` ; tour : 1, 4, 7, 9 dans le mod `cc2_mesures`, `tour/etude_mise_a_jour/ETUDE.md:70`).

**B12. Le code Windows a-t-il changé depuis janvier ?**
- A : `passation_windows/COMPARAISON_MAC_WINDOWS.md:7` « le code a pu changer entre les deux »
- B : `DEMARRER_cc2_patchs.md:372` « la logique n'a pas changé depuis janvier »
- Remarque : B repose sur des valeurs et un ordre de constantes, pas sur du code relu : « c'est un indice fort, pas une relecture au désassembleur » (`tour/etape1/TABLEAU_mac_windows.md:4`) ; seul le groupe énergie / ascenseur / grue / roulage a été relu (31 sites).

**B13. `effet_tele` : tel quel ou sous condition sur Windows ?**
- A : `LISEZ-MOI.txt:37` « Marche aussi tel quel sur Windows (c'est un fichier d'effet, pas le programme). »
- B : `passation_windows/PASSATION_windows.md:48` « à n'appliquer que si le shader d'origine de la tour a le sha256 »

**B14. Hélicos : taille de la greffe et nombre de sites**
- A : `passation_windows/PASSATION_windows.md:115` « une petite greffe de 21 octets » ; `partage_detail/00_README.txt:62` « 4 sites »
- B : `DEMARRER_cc2_patchs.md:278` « greffe de 28 o qui décale la hauteur visée de 23,5 m » ; `extension_windows/RAPPORT_cloud.md:238` « 5 retouches »
- Remarque : le rapport cloud écrit lui-même « 4 endroits au lieu de 5 » côté Windows (`extension_windows/RAPPORT_cloud.md:238`).

**B15. La copie de Revolution : 43 ou 42 fichiers**
- A : `passation_windows/NOTE_mac_bug_waypoints_27-10.md:4` « 43 fichiers »
- B : `tour/waypoints/sha256_revolution_tour.txt:2` « la tour en a 42 »
- Remarque : écart non expliqué ; piste de cause du bug des waypoints. Les identifiants du mod diffèrent aussi d'une note à l'autre : `3460002110` (`tour/etudes_missiles/DIAGNOSTIC.md:5`) et « objet 3098073689 à l'époque » (`passation_windows/PASSATION_windows.md:67`), qui admet une version « peut-être périmée ».

---

## C. Statuts de preuve qui ne se suivent pas

**C1. Le même fichier dit « à mesurer » puis donne la mesure** (Mac, `DEMARRER_cc2_patchs.md`)
- `pont_retour_x2` : `DEMARRER_cc2_patchs.md:269` « pas encore mesuré » contre `DEMARRER_cc2_patchs.md:366` « pont → hangar 0:32 pour chacun des 4 »
- relevé : `DEMARRER_cc2_patchs.md:285` « pas encore vu sur une vraie » contre `DEMARRER_cc2_patchs.md:368` « est vu en jeu : fichier créé, lignes au bon format »
- atterrissage : `DEMARRER_cc2_patchs.md:241` « à mesurer en jeu » contre `DEMARRER_cc2_patchs.md:14` « essayé en jeu le 23/10 »
- vitesse : `DEMARRER_cc2_patchs.md:34` « encore essayés en jeu » contre `DEMARRER_cc2_patchs.md:368` « vérifiée en jeu »
- Remarque : les mesures du 25/10 au soir portent sur un mélange d'avions différent, « indicatif » (`DEMARRER_cc2_patchs.md:366`), et sur une partie chargée sans joueur (`DEMARRER_cc2_patchs.md:364`). En-tête non mis à jour : « Dernière mise à jour : 25/10/2026 » (`DEMARRER_cc2_patchs.md:4`) contre des entrées du 27/10 (`DEMARRER_cc2_patchs.md:372`).

**C2. Vitesse de croisière des avions sous IA**
- A : `etudes/ia_vitesse.md:11` « Albatros : 48 m/s » ; `outil/modules/vitesse_escadrille.py:6` « En vol vers un point, l'IA des avions vise la vitesse plancher : 48 m/s (Albatros) ou 72 m/s (Manta). » ; `partage_detail/11_porting_and_priorities.txt:111` « +27 % / +41 % speed [EST] »
- B : `DEMARRER_cc2_patchs.md:367` « PAS à 48 / 72 m/s » ; `partage/README.txt:19` « the modes only act NEAR a waypoint »
- Remarque : mesure du 25/10 : ≈ 120 m/s en ECO ; les modes ne changent la vitesse que près du point (`DEMARRER_cc2_patchs.md:367`). L'estimation `[EST]` est restée dans les notes anglaises.

**C3. Gains `[GAME]` ou `[EST]` dans les notes anglaises du Mac**
- A : `partage_detail/00_README.txt:64` « 0:51 -> 0:32 per aircraft [GAME, one run] »
- B : `partage_detail/11_porting_and_priorities.txt:139` « the deck-taxi x2 and the landing-vs-stock gain are not measured » ; `partage_detail/11_porting_and_priorities.txt:109` « -0:20 to -1:25 on 4 aircraft [EST] »
- Remarque : le chiffre 7:28 (essai d'atterrissage du 23/10, `partage/README.txt:12`) sert aussi d'« avant » pour le roulage ×2 : « 4 returns 7:28 -> 5:49 (one run each, not the same aircraft mix) » (`partage/README.txt:13`). La source signale elle-même que les mélanges d'avions diffèrent.

**C4. Hélicos : −36 % ou −45 % ; « validés » avec ou sans réserve**
- A : `etudes/MESURES_helicos.md:46` « −2:30, −36 % » ; `DEMARRER_cc2_patchs.md:17` « validés en jeu : 4 hélicos 6:52 → 4:22 »
- B : `etudes/MESURES_helicos.md:50` « 3:18 contre 6:03 (−45 %) »
- Remarque : deux bases de calcul (total, ou de la 1re piste au dernier rangé). Le 6:52 « a été mesuré avec `ascenseur_x2` et `atterrissage` déjà actifs » (`passation_windows/PASSATION_windows.md:40`), donc n'est pas le jeu d'origine.

**C5. Total des retours : un gain ou du bruit ?** (même journal)
- A : `passation_windows/JOURNAL_tour.md:185` « Le total gagne 1:55 car l'avion libère la piste plus tôt »
- B : `passation_windows/JOURNAL_tour.md:243` « Le TOTAL n'est pas une mesure fiable »
- Remarque : « à configuration identique, le total varie de 1:23 » (`passation_windows/JOURNAL_tour.md:283`) ; la métrique retenue est « pont → hangar » (`passation_windows/JOURNAL_tour.md:243`).

**C6. Missiles : deux verdicts dans le même diagnostic ; trois corrections du Mac non reportées**
- A : `tour/etudes_missiles/DIAGNOSTIC.md:29` « (🔴, plusieurs séances, et le code à modifier n'est pas encore repéré). » ; `tour/etudes_missiles/DIAGNOSTIC.md:163` « (seuil de départ 0 ; 0,05 pour le missile anti-aérien, »
- B : `tour/etudes_missiles/DIAGNOSTIC.md:13` « c'est corrigeable par un **petit patch du programme** (🟡). » ; `tour/etudes_missiles/PASSATION.md:36` « est **faux** : le seuil de départ est 0 pour tous les types »
- Remarque : le bandeau dit que les sections 1 à 10 restent l'historique de l'enquête et que leurs verdicts provisoires « sont dépassés » (`tour/etudes_missiles/DIAGNOSTIC.md:14`), mais elles restent écrites avec leur propre verdict. Le fichier de réponses du Mac est introuvable (E3). Une correction du diagnostic attend l'accord du moddeur (`tour/etudes_missiles/PASSATION.md:19`).

**C7. Que veut dire « MESURÉ » ?**
- A : `tour/etudes_circuit_atterrissage/PASSATION.md:2` « MESURÉ (calculé ou vu en jeu) »
- B : `tour/etudes_modes_carburant/PASSATION.md:4` « [MESURÉ, ancien build, 28/10] » (observé en jeu) ; `tour/etude_mise_a_jour/ETUDE.md:4` « MESURÉ (calculé ou comparé par un script, résultat vu) »
- Remarque : même mot, deux sens (calculé sur copie / observé en jeu). À garder en tête en lisant les tableaux de `doc/ETAT_DES_LIEUX.md`.

**C8. Plugin `cc2x_modes.dll` v3 : deux sommes et deux comptes de contrôles**
- A : `tour/etudes_modes_carburant/ETUDE.md:460` « 124 contrôles réussis »
- B : `tour/etudes_modes_carburant/plugin/RISQUES_v3.md:19` « 130 contrôles automatiques réussis » ; `tour/etudes_modes_carburant/plugin/RAPPORT_compilation.md:5` « 331581C64CB880AB0BC8CBC3258414F55C41723FB8DA7042CFDABE08CABC8729 »
- Remarque : l'étude cite aussi `49AFE401` pour la même v3 (`tour/etudes_modes_carburant/ETUDE.md:460`) ; INCERTAIN : version antérieure à l'ajout des deux builds ?

**C9. Un interpréteur Lua existe-t-il sur la tour ?** (27/10 contre 28-29/10)
- A : `tour/PROMPT_etude_atterrissage_manuel.md:27` « Il n'y a pas d'interpréteur Lua sur la tour » ; `tour/etudes_modes_carburant/PASSATION.md:4` « (pas de Lua sur le PC, pas de `lupa`) »
- B : `tour/etudes_demarrage_auto/ETUDE.md:14` « un interpréteur Lua d'essai (DLL signée d'OBS, déjà utilisée par `lua_sonde.py`, sans réseau) »
- Remarque : deux conversations, deux outils ; la note des modes ne cite pas `tour/outils/lua_sonde.py`.

**C10. Fiches qui disent « non commité » alors que les fichiers sont suivis par git**
- A : `tour/etudes_missiles/DIAGNOSTIC.md:145` « Seul fichier ajouté au dépôt : ce diagnostic (non commité). » ; `tour/idees_et_demandes/IDEES.md:5` « Rien n'est commité. »
- B : `tour/etudes_missiles/PASSATION.md:3` « (déjà commité et poussé par une autre session, »
- Remarque : vérifié pour ce document avec `git log` : ces dossiers sont suivis et un commit les cite.

---

## D. Recommandations abandonnées mais encore écrites

**D1. Hélicos posés sur l'ascenseur**
- Écrit : `etudes/RESULTATS_etude.md:11` « A1 — hélicos posés directement sur l'ascenseur (recommandé) »
- Dit ailleurs : `passation_windows/etudes_fr/LISEZ-MOI.txt:4` « essayé le 24/10, deux hélicos se sont percutés, abandonné. » ; `etudes/MESURES_helicos.md:31` « la pose sur l'ascenseur n'est pas la priorité »

**D2. Roulage ×3 ou ×2**
- Écrit : `etudes/piste_et_pont.md:11` « A' : rouler 3× plus vite sur le pont au retour (recommandé) »
- Dit ailleurs : `DEMARRER_cc2_patchs.md:268` « pont ~42 s → ~22 s, piste occupée 88 → ~68 s » (module à 15,0, donc ×2 : `outil/modules/pont_retour_x2.py:7`) ; `passation_windows/etudes_fr/LISEZ-MOI.txt:5` « c'est le roulage ×2 (constante 15,0) qui a été choisi et installé »

**D3. Méthode pour Windows : SDK ou patch direct**
- Écrit : `passation_windows/PASSATION_windows.md:73` « Base = le SDK public CC2X » ; `passation_windows/PROMPT_A_COLLER.txt:3` « en s'appuyant sur le SDK public CC2X »
- Dit ailleurs : `DEMARRER_cc2_patchs.md:372` « patch DIRECT de `carrier_command.exe`, comme sur le Mac, sans le SDK d'un tiers » ; `passation_windows/NOTE_mac_frein_seul_27-10.md:4` « SDK relu et compilé par nous » (pour le frein seulement)
- Remarque : le SDK est « en réserve » pour les groupes à crochets (`DEMARRER_cc2_patchs.md:372`) ; `passation_windows/PASSATION_windows.md:68` écrit aussi « Le sha256 de l'exécutable Windows n'est connu de personne », devenu faux (`DEMARRER_cc2_patchs.md:372` « jeu Windows = bien la 1.5.18 »).

**D4. PvP : retirer `temps_x2` et `pont_retour_x2`**
- Écrit : `tour/scenario_pvp/ETUDE.md:228` « Retirer `temps_x2` et `pont_retour_x2` »
- Dit ailleurs : `tour/scenario_pvp/ETUDE.md:12` « sont **sans objet** tant que l'exe est celui d'origine » (encadré du 29/10)

**D5. « Plusieurs porte-avions par équipe » : impossible ou option du menu**
- A : `tour/idees_et_demandes/IDEES.md:84` « Impossible par mod »
- B : `tour/scenario_pvp/ETUDE.md:75` « c'est une option officielle du menu »
- Remarque : la 2e étude se présente comme corrigeant la 1re (`tour/scenario_pvp/ETUDE.md:68`) ; l'option n'a jamais été essayée.

**D6. Textes de l'étude de vitesse et des modes restés au présent**
- `etudes/ia_vitesse.md:141` « Plan présenté au moddeur, en attente de son feu vert. » contre `etudes/ia_vitesse.md:144` « activés dans le jeu » ; `tour/etudes_modes_carburant/plugin/RISQUES_pose.md:3` « Rien n'est posé » contre `tour/etudes_modes_carburant/PASSATION.md:5` « POSÉ maintenant (rien dans le dossier du jeu ni dans le SDK) » ; `LISEZ-MOI.txt:14` « Les patchs disponibles (24/10/2026) » (9 modules) contre `DEMARRER_cc2_patchs.md:34` « 14 modules ».

---

## E. Inventaires, chemins, partage

**E1. `partage/` : 3 ou 4 fichiers ? envoyés ou seulement prêts ?**
- A : `DEMARRER_cc2_patchs.md:377` « 3 fichiers texte à joindre » ; `DEMARRER_cc2_patchs.md:377` « Un dossier de notes en anglais pour ce moddeur est prêt »
- B : `passation_windows/NE_PAS_PARTAGER.txt:3` « (4 fichiers texte nettoyés) » ; `passation_windows/PASSATION_windows.md:4` « ont été envoyés à d'autres moddeurs »
- Remarque : `partage/` contient 4 fichiers dont `partage/README.txt`. `DEMARRER_cc2_patchs.md:373` dit « Rien envoyé » mais pour `envoi_native_bridge/`, un autre ensemble.

**E2. `partage_detail/` : à envoyer ou non ?**
- A : `partage_detail/00_README.txt:5` « useful to someone who works on the Windows build with a DLL. »
- B : `DEMARRER_cc2_patchs.md:379` « (source des 3 fichiers, ne pas envoyer) »

**E3. Fichier de réponses du Mac sur les missiles**
- A : `tour/etudes_missiles/PASSATION.md:4` « Réponses du Mac : `passation_windows/REPONSES_mac_pour_la_tour_28-10.md` »
- B : `tour/PASSATION_coordination_29-10.md:94` « fichier `tour/REPONSES_mac_pour_la_tour_28-10.md` » (branche du Mac non fusionnée)
- Remarque : aucun des deux chemins n'existe dans le dépôt ; le fichier présent, `passation_windows/REPONSES_mac_pour_la_tour.md`, répond à d'autres questions (grue, roulage, énergie).

**E4. Renvois cassés**
- `DEMARRER_cc2_patchs.md:361` « `partage/11_porting_and_priorities.txt` » : ce fichier n'existe que sous `partage_detail/`. `tour/etude_mise_a_jour/ETUDE.md:91` renvoie à un « §7 » pour la demande d'accord, qui est en fait dans `tour/etude_mise_a_jour/PASSATION.md:15`. `passation_windows/NOTE_mac_frein_seul_27-10.md:63` « tour/frein/ » : ce dossier n'existe pas (le travail est dans `tour/atterrissage_manuel/`, en cours).

**E5. Le mod Workshop 3826940003 (Island Airfields) : identité vérifiée ou non ; disponible ou retiré**
- A : `tour/POINT_POUR_LE_MAC.md:37` « mais l'identité n'est pas vérifiée »
- B : `passation_windows/JOURNAL_tour.md:98` « = **Island Airfields**, auteur Steam » ; `tour/idees_et_demandes/IDEES.md:164` « retiré de la communauté pour violation des règles de Steam »
- Remarque : le journal précède la fiche du Mac ; la page Workshop n'a été lue que par un outil, jamais ouverte dans un navigateur (`passation_windows/JOURNAL_tour.md:98`).

**E6. Fichiers de symboles cités mais absents**
- `envoi_native_bridge/README.txt` liste symbols_raw.txt et symbols_demangled.txt ; ils ne sont pas dans le dossier (ignorés par git : `.gitignore`, refaisables avec `nm` / `c++filt` : `DEMARRER_cc2_patchs.md:373`).

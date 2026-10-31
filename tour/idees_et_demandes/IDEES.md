# Tes idées non traitées et les demandes de la communauté — repérage du 28/10/2026

> **Reprise : lire d'abord `PASSATION.md` (même dossier) — état au 29/10/2026**, puis le §1 bis ci-dessous. La mise à jour Steam du 28/10 a effacé `pont_retour_x2` (rapporté).

Étude **en lecture seule côté jeu** : rien n'a été lancé, installé, téléchargé, posté ni modifié (ni jeu, ni `%APPDATA%`, ni exe, ni DLL, ni Steam). Seul ce fichier est écrit. Rien n'est commité.

**Étiquettes** : **LU** = lu dans un fichier ou une page (source indiquée) · **INFÉRÉ** = déduit, à vérifier (jamais présenté comme un fait).

**Comment lire les colonnes**
- **Intérêt pour toi** : haut / moyen / bas (selon ce que tu as dit ; si tu n'as rien dit sur le sujet, c'est mon estimation, marquée INFÉRÉ).
- **Moyen** : *mod Lua* (script d'un mod), *patch exe* (retouches du programme par module), *plugin DLL* (via le SDK posé), *aucun code* (juste un essai ou une décision), *impossible* (dans nos moyens actuels).
- **Multijoueur** (rien de tout ça n'a jamais été testé avec de vrais joueurs) : un **mod** (Lua, XML, shader) est envoyé aux joueurs qui rejoignent (LU, lecture du programme dans `partage_detail/08_constants_and_multiplayer.txt`) ; un **patch exe** n'agit que **chez l'hôte** (LU, même fichier) ; un **plugin DLL** : solo ou hôte seulement, pas envoyé aux invités (LU `tour/etudes_modes_carburant/ETUDE.md` §3.5 + `PASSATION_windows.md` §4).
- **Risque** : 🟢 faible · 🟡 moyen · 🔴 élevé. **Effort** : S (une séance) · M (quelques séances) · L (beaucoup).

---

## 1. Les 5 meilleures pistes (celles qui ne sont encore dans aucune conversation)

| # | Piste | Pourquoi | Par quoi commencer |
|---|---|---|---|
| 1 | **Bug des waypoints** (« impossible de tracer pendant que les avions partent ») | Tu as dit : « il faut à tout prix fixer ce bug » (27/10). Gêne à chaque sortie d'avions. | Étude **lecture seule** : comparer les écrans de Revolution avec ceux du jeu de base (là où la cause a été vue) et voir si une copie corrigée en mod Lua suffit. Question préalable : Revolution est-il remis ? (voir ligne 1 du tableau). |
| 2 | **Roulage de retour ×2** (`pont_retour_x2`) | Les retours sont le plus lent : « pont → hangar » = 0:55 par avion, ×4. Sur le Mac ce module a fait 0:51 → 0:32 (LU `DEMARRER_cc2_patchs.md`). Seulement 3 retouches. | Identifier les 3 lectures de `30,0` des états 5, 6 et 7 au désassembleur, faire un module JSON, le tester **sur copie** (comme les modules du circuit). |
| 3 | **Aides visuelles à l'atterrissage** (ton idée : encadrés verts, couleurs de vitesse) | Complète l'atterrissage à la main : tu vois tout de suite « trop haut / trop vite ». La communauté demande l'atterrissage manuel depuis 2021 (voir C1). | Un affichage de **lecture seule** dans l'écran de pilotage (mod Lua) : vitesse par rapport au pont + hauteur, en rouge/bleu/vert. D'abord vérifier quelles données le Lua du pilotage reçoit (INFÉRÉ : il reçoit le véhicule et la carte). |
| 4 | **Un vrai test multijoueur** avec un ami | Tout ce qu'on dit du multijoueur est **déduit** : « si je host, les autres peuvent-ils me rejoindre avec mes modifications ? » (ta question du 27/10). Tant que ce n'est pas testé, un patch peut gêner tes parties publiques sans qu'on le sache. | Un protocole court (15 min) : tu héberges depuis la tour patchée, un ami rejoint, on note ce qu'il voit (horloge, SORTIES, vitesse des avions) et si ça tient. Aucun code à écrire. |
| 5 | **Hélicos plus rapides** (module Mac validé : 4 hélicos 6:52 → 4:22, −36 %) | C'est une partie du but de départ (sorties **et** retours d'avions **et d'hélicos**) et rien n'est porté sur la tour. | Relire les 5 sites sur Windows (constantes 50, 100, 120, 20…) ; le plus délicat est une petite greffe de 21 octets : voir si le SDK ou un module d'exe peut la porter (INFÉRÉ : pas de zone vide évidente). |

**Question de décision** (aussi posée à la fin du résumé) : par laquelle commence-t-on ? Ma recommandation : la **n° 2** si tu veux un gain vite et sûr, la **n° 1** si c'est ton irritant principal.

### 1 bis. État au 29/10/2026 (mis à jour ; rien de nouveau cherché)

« Rapporté » = écrit dans le message de coordination du 29/10, non revérifié par moi. L'ordre des 5 premières pistes est **inchangé** : leur intérêt n'a pas changé ; seul l'effort des n° 2 et 5 augmente (à refaire sur le nouvel exe).

| # | État au 29/10 |
|---|---|
| 1 Waypoints | Inchangé, aucune étude lancée. La mise à jour Steam a peut-être touché les scripts du jeu (INFÉRÉ, non vérifié). |
| 2 Roulage de retour ×2 | Module prêt sur l'**ancien** exe. **Posé le 28/10 à 10:25 puis effacé par la mise à jour Steam** (21:30, nouvel exe `461E1262…` sans patch) — rapporté. Aucune mesure rapportée. **À re-porter** sur le nouvel exe, après accord du moddeur. |
| 3 Aides visuelles | En attente de l'atterrissage à la main : l'essai v6 du frein a montré que le frein, le maintien et le moteur coupé marchent, mais que **la reprise par l'IA a échoué** (l'avion posé à la main est tombé à l'eau après l'ordre de retour) — rapporté. Pas validé, donc pas commencé. |
| 4 Test multijoueur | Inchangé, jamais fait. |
| 5 Hélicos | « Approche ×2 » prête sur l'ancien exe, **jamais posée** ; à re-porter. Le « toucher près de l'ascenseur » (greffe) reste à faire. |
| 6 Mods perso | Inchangé (à remettre quand les essais sont finis). |
| 9 Annuler un décollage (grue) | Dépendait du chargeur maison : **travail arrêté, il ne reste qu'un journal** — rapporté. Donc en attente, sans calendrier. |
| 14 Réglages cachés / 21 Scénario 3 porte-avions, 6 Manta | Un dossier `scenario_pvp` existe (conversation « scenario-pvp ») avec une **variante PvE** et la **formule des dégâts** — rapporté, non relu ; lien avec ces deux lignes INFÉRÉ. |
| Autres lignes | Inchangées. |

---

## 2. Tableau classé (tout ce qui a été trouvé, de la meilleure piste à la moins utile)

Légende « Où » : **T** = ton idée/point (source citée) · **M** = notes du Mac (module déjà validé là-bas, pas porté) · **C** = demande de la communauté (liens en §5).

| # | Idée / demande | Où | Intérêt | Moyen | Multijoueur | Risque | Effort | Remarque / doublon |
|---|---|---|---|---|---|---|---|---|
| 1 | **Waypoints bloqués pendant la sortie des avions** | T | haut | mod Lua (copie corrigée des écrans de contrôle) | mod → envoyé aux invités | 🟢 | M | Cause vue **avec** Revolution (LU résumé de la conversation principale du 27/10 ; tu as confirmé « sans Révolution, ça marche bien »). **Mais** la note missiles du 28/10 dit que Revolution n'est plus dans `mods.xml` (LU) : le bug n'apparaît donc plus aujourd'hui. Aucune conversation dédiée (INFÉRÉ). Liens avec C5 et C6. La liste Workshop (28/10) montre des versions Revolution 1.5-22 et 1.6-19 : la tienne est peut-être périmée (INFÉRÉ, `PASSATION_windows.md` §3 le soupçonnait déjà). |
| 2 | **Roulage de retour ×2** (`pont_retour_x2`) | M | haut | patch exe, 3 retouches de 4 octets | hôte seulement | 🟢 sur copie, 🟡 à la pose sur le vrai exe | S–M | **MIS À JOUR 28/10 : module prêt, 1 seule retouche de 4 octets, testé sur copie de l'exe (pas en jeu)** : voir `tour/etudes_roulage_retour/ETUDE.md`. Gain Mac : 0:51 → 0:32 par avion. Effet de bord déduit : le roulage des départs peut aussi aller ×2. **Pas de doublon**, mais voisin de la conversation « circuit » (même zone du code). |
| 3 | **Aides visuelles à l'atterrissage** | T | haut | mod Lua (écran de pilotage) | affichage local ; envoyé aux invités comme mod | 🟢 | M | Ton idée, JOURNAL_atterrissage 27/10 15:29 : « pour plus tard, non étudiée ». Les données (vitesse relative, hauteur du pont) existent déjà dans le plugin de frein (LU). À lancer **après** la validation de l'atterrissage à la main. |
| 4 | **Test multijoueur réel** | T | haut | aucun code | — | 🟡 | S | Ta question du 27/10 (« Si je host une game… ») et ton projet de donner l'outil de lag à un ami qui héberge des serveurs publics (conversation « Carrier Command 2 performance monitoring », 06/10). À vérifier au passage : un mod Lua est-il bien envoyé et le plugin DLL **pas** envoyé (LU dans le code Mac, jamais vu). |
| 5 | **Hélicos −36 %** (`helicos_approche_x2` + `helicos_pres_ascenseur`) | M | haut | patch exe + greffe de 21 octets | hôte seulement | 🟡 | L | **MIS À JOUR 28/10 : la moitié « approche ×2 » est prête** (1 retouche de 4 octets, testée sur copie, jamais vue en jeu : `tour/etudes_roulage_retour/ETUDE.md`). Le « toucher près de l'ascenseur » demande en plus une greffe de 21 octets : pas fait. Pas de conversation en cours. |
| 6 | **Remettre tes mods perso** (drapeau français sur le pont, lumière rouge, livrées, ciel violet, fumée tricolore, tableau d'escadre…) | T | moyen–haut (INFÉRÉ) | `mods_actifs.py restaurer` | mods → envoyés aux invités | 🟢 | S | Tu les as fait désactiver le 27/10 : « straight to the point » (LU `JOURNAL_tour.md`). Sauvegarde `mods.xml.bak_2026-10-27b` existe (LU). À faire **quand les essais seront finis** (les autres conversations utilisent `mods.xml`). `pack_moddeur` modifie aussi `constants.txt` : vérifier qu'il ne gêne pas `cc2_modes` (INFÉRÉ). |
| 7 | **Accélération du temps réglable en jeu** (×1 / ×2 / pause) | T + C | moyen–haut | plugin DLL (le facteur de vitesse du serveur est en `+0x1b8` côté Mac, LU) | hôte seulement ; tout le monde subit le changement | 🟡 | M | **Doublon partiel** : `temps_x2` est déjà posé, mais la simulation sature à ×1,33 (processeur, un seul cœur, LU `JOURNAL_tour.md`). Demandée par la communauté (C2). Un « bouton » en direct n'existe pas : à étudier. |
| 8 | **Courbes du lag / SIM** (graphique durée de simulation contre temps réel) | T | moyen | outil hors jeu + `cc2x.log` du SDK ou mod | — | 🟢 | M | Tes mots (27/10) : « c'est pas trop grave, c'est un petit plus ». Existe sur le Mac (`releve` + courbes) ; sur la tour : affichage « SIM ×… » dans `cc2_mesures` (LU). À relier au point 4 (ami sur serveur public). |
| 9 | **Annuler un décollage déjà pris par la grue** (`grue_annulation`) | M + C | moyen | patch exe + greffe de 932 octets, ou plugin DLL | hôte seulement | 🔴 si grue bloquée, sinon 🟡 | L | Demande n° 20652 du tracker. Risque cité par le Mac : une grue bloquée empêche tout lancement et tout atterrissage (LU). À faire seulement après le chargeur maison. |
| 10 | **Pilote automatique / équipage IA du porte-avions** | C | moyen (INFÉRÉ) | mod Lua (piste à explorer) | mod → invités | 🟡 | L | Demandé en solo (C3). Le Lua sait lancer/rappeler un avion par waypoint (LU Mac) ; pour le bateau lui-même : **INFÉRÉ, non vérifié**. |
| 11 | **Indicateurs et outils de waypoints** (savoir qu'un avion rangé a déjà un waypoint, tracer de meilleures routes) | C | moyen | mod Lua | mod → invités | 🟢 | M | #14467, #515. À combiner avec le n° 1. |
| 12 | **Raccourcis / commandes rapides** (déployer en cliquant sur le véhicule, groupes, points de ralliement) | C | moyen | mod Lua | mod → invités | 🟢 | M–L | #2344, #18780, #477, #27697. Proche de ton onglet « mode de l'avion » (conversation modes-carburant) : même technique d'interface. UI Enhancer et Captain Controls (Workshop) font déjà une partie. |
| 13 | **Caméra libre / mode observateur / mode photo** | C | moyen (tu fais des vidéos et des timelapses, INFÉRÉ) | inconnu | inconnu | 🟡 | L | #18947, #14918, #2335. Voir ce que fait déjà `cc2_carte` / la conversation timelapse avant de partir de zéro. |
| 14 | **Réglages cachés modifiables** (cadence de tir, poids des conteneurs, vitesse de production, paramètres d'armes) | C | bas–moyen | mod XML / `constants.txt` pour une partie ; plugin DLL pour le reste | mod → invités | 🟢 / 🟡 | M | #27999, #28021, #23918, #2360. Ton `pack_moddeur` modifie déjà `constants.txt` (LU). Selon un moddeur (Steam, mai 2023), dégâts, portée, PV et coûts ne se changent pas par mod (LU, à re-vérifier : le jeu a évolué depuis). |
| 15 | **Petites améliorations des missiles** (plusieurs missiles guidés par un opérateur, alerte de décrochage du missile TV, viseur d'avance pour roquettes) | C | moyen | patch exe ou plugin | hôte seulement | 🟡 | M | #2325, #29644, #14544. Conversation « missiles T » déjà ouverte sur le verrou : à traiter ensemble, pas séparément. |
| 16 | **Partager nos extraits de noms avec d'autres moddeurs** (création d'objets, commandes du porte-avions) | T | moyen | aucun code (envoi) | — | 🟢 | S | Dossier prêt `envoi_native_bridge/`, « rien envoyé », « sans info perso » (LU `PASSATION_windows.md` §7). C'est toi qui décides d'envoyer. |
| 17 | **Shader sans effet « vieille télé »** (`effet_tele`) | M | moyen | fichier de données (mod) | mod → invités | 🟢 | S | Ne s'applique que si le shader d'origine de la tour a la bonne empreinte (LU `PASSATION_windows.md` §2), sinon à refaire. |
| 18 | **Écran des caméras CCTV 512 × 512** (`cctv_net`) | M + C | bas–moyen | patch exe, 4 greffes | hôte seulement | 🟡 | L | Demande n° 1499. Purement visuel. |
| 19 | **Freinage final plus court (« vrai ×2 ») et roulage des véhicules terrestres ×2** | M | bas–moyen | patch exe | hôte seulement | 🟡 | M | « Plus tard » dans `DEMARRER_cc2_patchs.md` §6.6. |
| 20 | **Mode fenêtré** (« ouvrir le jeu en pas plein écran ») | T | bas | réglage du jeu / option de lancement (INFÉRÉ) | — | 🟢 | S | Ta question du 27/10. Je n'ai pas retrouvé la réponse dans les notes : à reposer si elle n'a pas été traitée. |
| 21 | **Scénario de départ : 3 porte-avions, 6 Manta** | T | à préciser | à préciser | à préciser | — | — | Une phrase du 18/09 (session « CC2 ») : « je voudrais faire 6 mantas, je commencerai avec 3 porte avions ». **Contexte non relu**, je ne sais pas ce que tu voulais faire exactement. |

### Écartées ou impossibles (pour mémoire, pour ne pas les redemander)

| Idée | Pourquoi |
|---|---|
| Avions garés sur le pont, prêts à décoller (#2023, 8 votes, la plus votée de ce repérage) | Mac : difficulté 8/10, 4-6 séances, « pas maintenant » (LU `partage_detail/11_porting_and_priorities.txt`). |
| 2e ascenseur | Inutile : la piste est le goulot (Mac, 9/10). |
| Hélicos posés sur l'ascenseur | Essayé : collision de 2 hélicos, abandonné. |
| Interface de pilotage 2× plus fine | Tu n'en veux pas (23/10). |
| Automatiser le lancement des avions pour les essais | Tu as arrêté (27/10) : « est-ce que c'est tant utile que ça ? Je pense pas, non. On peut passer à autre chose. » |
| Plusieurs porte-avions par équipe, Swordfish pilotable, sous-marins, nouvelles unités | **Impossible par mod** d'après des moddeurs (Steam, mai 2023) ; contournement par édition de sauvegarde = bugs de logistique (Steam, sept. 2022). Hors de nos moyens (INFÉRÉ). |
| Musique / sons (#29671, #17333, #2286), VR, Stream Deck, traductions, serveur Linux, matchmaking | Hors sujet de nos patchs ; des mods de son existent déjà (« deep sound », « Muffled Carrier Engine »). |

---

## 3. Ce que tu as demandé et qui est **déjà pris** par une conversation (doublons — ne pas relancer)

| Ta demande | Conversation | État d'après les notes |
|---|---|---|
| Atterrir à la main, l'IA reprend et fait le pushback | atterrissage-main | plugin de frein v6 posé ; mesures en cours (LU `git log`) |
| Circuit en cercle + créneau élargi | circuit-atterrissage | 2 modules JSON prêts, copie d'essai, essais 2 et 3 à faire |
| Modes économique / normal / flank par avion | modes-carburant | plugin v1 posé, v2 prêt non posé |
| Missiles : viser la cible verrouillée avec T | missiles-viser-la-cible | diagnostic fait, patch à décider |
| Démarrer le jeu sur une partie prête (+ plantage au chargement) | demarrage-auto | étude à jour ; cause non prouvée en jeu |
| Remplacer le SDK de DYOR par un chargeur à nous | chargeur-maison | P0 fait, arrêt au malentendu P1 |
| Horloge, journal, affichage SORTIES, ascenseur ×2, temps ×2 | — | faits et posés |

---

## 4. Ce que dit la communauté (résumé avec mes mots)

**Tracker officiel de Geometa** (`geometa.co.uk/support/carriercommand`). LU le 28/10 : 1 défaut ouvert, **640 demandes** de fonctions, 2 354 fermées. J'ai lu 8 pages sur 32 (20 demandes par page) : les plus récentes (2025-2026) et trois pages plus anciennes. Les « votes » sont lus d'après le texte aplati de la page : **approximatifs**.

| Réf. | Demande de la communauté | Votes (approx.) | Lien avec nos travaux |
|---|---|---|---|
| C1 | **Atterrissage / décollage manuel** : #1036 (11 doublons), fil Steam de juillet 2022 (après un atterrissage manuel le jeu ne range pas l'avion, un waypoint vers le bateau reprend la main, pas de direction au sol), #29414 (les véhicules posés ne devraient pas glisser hors du pont), #19758 (pont stabilisé), #29413 (poser un hélico) | 2 + doublons | **Doublon avec atterrissage-main** (frottement du pont, prise en charge) |
| C2 | **Accélération du temps** : #479 (« accélération douce pour voyager entre îles en solo »), plusieurs avis Steam et forums (« pas d'accélération du temps »), forum Quarter to Three (oct. 2025) | peu | **Fait en partie** (`temps_x2`) |
| C3 | **Moins de corvées en solo** : pilote automatique du porte-avions, équipiers IA, priorité de réparation automatique, raccourcis pour changer de poste (Steam mars 2023 ; Quarter to Three oct. 2025) | — | n° 10 et n° 12 |
| C4 | **Optimiser départs / atterrissages / chargements** : #14728 (5 votes), #2307 (5), #28452, #27696, #18565 | 1 à 5 | **Doublon** : ascenseur ×2, circuit |
| C5 | **Circuit d'attente interactif** : #513 (5 votes, 3 doublons) | 5 | **Doublon** : conversation circuit |
| C6 | **Annuler la livraison d'un avion depuis le hangar** : #20652 | 1 | n° 9 (fait sur le Mac seulement) |
| C7 | **Horloge en jeu** : #2329 (4 votes), #512 | 4 | **Fait** (`cc2_mesures`) |
| C8 | **Mettre un indicateur quand un avion rangé a reçu un waypoint** : #14467 ; outils de waypoints : #515 | 1 | n° 1 et n° 11 |
| C9 | **Décollage/atterrissage depuis les îles capturées** : #14135 (4 votes, 2 doublons) | 4 | Déjà fait par le mod communautaire « Island Airfields » (voir §6) |
| C10 | **Plateau d'avions garés sur le pont** : #2023 | 8 | Écartée (Mac) |
| C11 | **Modding plus ouvert** : #26784, #26620, #2292 (6 votes), #2019 (6), #2047 (5, documentation), #21123 (mods côté serveur) | 1 à 6 | Notre SDK / chargeur va dans ce sens |
| C12 | **Missiles et armes** : #2325, #29644, #14544, #26519 (zoom), #21683 (torpilles qui explosent à l'impact) | 2 à 5 | n° 15 |
| C13 | **Plusieurs porte-avions par équipe** (Steam sept. 2022, #18648, #18599) | 1 | Écartée |
| C14 | **Unités nouvelles / pilotables** : #2031, #2030, #17960 (sous-marins) | 1 à 6 | Écartée |

**Autres sources lues** (fils Steam, Workshop, forum) : en bref, les mêmes thèmes — corvées du solo, absence d'accélération du temps, atterrissage à la main, mods limités, multijoueur instable avec une mauvaise connexion. Détails et liens en §5.

**Sur la recherche elle-même** : Reddit n'a rien remonté dans la recherche (non consulté directement) ; Nexus Mods a refusé la lecture (403) ; le dépôt GitHub du SDK (`Dioramawhois/Carrier-Command-2-extender`) a **0 demande ouverte** (LU : « Open 0 », le nombre de demandes fermées n'est pas affiché) ; sa feuille de route « limites / prochaines étapes » parle de plus de versions du jeu, d'un transport multijoueur et de plus de données (équipes, inventaires, capture d'îles). Pour Geometa : une douzaine de lectures sur ~35 minutes, aucun blocage (le site bloque au-delà de ~60 pages par minute).

---

## 5. Sources (liens)

Tracker officiel Geometa
- Page d'accueil du suivi : https://geometa.co.uk/support/carriercommand · liste des demandes : https://geometa.co.uk/support/carriercommand/features (pages 1 à 7, 10, 20, 28 lues) · une demande : `/support/carriercommand/<numéro>`.

Steam (discussions du jeu, appid 1489630)
- Plusieurs porte-avions en coop : https://steamcommunity.com/app/1489630/discussions/0/3369279464993957114
- Jeu jouable ? accélération du temps, IA, équilibrage, mods limités : https://steamcommunity.com/app/1489630/discussions/0/3803901984154854351
- Contrôler un Swordfish : https://steamcommunity.com/app/1489630/discussions/0/3183488858479889041
- Solo ou multijoueur (allers-retours entre consoles) : https://steamcommunity.com/app/1489630/discussions/0/3049485912466319976
- Ressources de modding et limites des mods (mai 2023) : https://steamcommunity.com/app/1489630/discussions/0/3828667551849084745
- Ranger un avion posé à la main (juil. 2022) : https://steamcommunity.com/app/1489630/discussions/0/3468352315394322506
- Le solo est-il trop dur ? (pilote automatique, équipiers IA) : https://steamcommunity.com/app/1489630/discussions/0/3780246883330745499
- UI Enhancer (août 2021) : https://steamcommunity.com/app/1489630/discussions/0/3057367774854084350

Steam Workshop
- Mods les plus populaires (1 semaine) : https://steamcommunity.com/workshop/browse/?appid=1489630&browsesort=trend&section=readytouseitems
- Island Airfields (id 3826940003) : https://steamcommunity.com/sharedfiles/filedetails/?id=3826940003
- Revolution (commentaires) : https://steamcommunity.com/sharedfiles/filedetails/comments/3335926653

Forum
- Quarter to Three, fil Carrier Command 2 (page 8) : https://forum.quartertothree.com/t/carrier-command-2/152487?page=8

GitHub
- SDK tiers : https://github.com/Dioramawhois/Carrier-Command-2-extender (issues : https://github.com/Dioramawhois/Carrier-Command-2-extender/issues)

Notes internes lues : `passation_windows/PASSATION_windows.md`, `passation_windows/JOURNAL_tour.md`, `DEMARRER_cc2_patchs.md`, `partage_detail/08_constants_and_multiplayer.txt`, `partage_detail/11_porting_and_priorities.txt`, `tour/POINT_POUR_LE_MAC.md`, `tour/etape1/TABLEAU_mac_windows.md`, `tour/atterrissage_manuel/JOURNAL_atterrissage.md`, `tour/etudes_modes_carburant/ETUDE.md`, notes des conversations liées (dossier partagé des sessions) et ta conversation principale (messages du 26 au 28/10).

---

## 6. Ce qui existe déjà chez la communauté (pour ne pas refaire)

Liste Workshop « tendance 1 semaine » du 28/10 (descriptions déduites des titres, **non vérifiées une par une**) : Revolution 1.5-22 et 1.6-19 (Bredroll), UI Enhancer (QuantX), logistics+, Naval Gun Stabilizer, Vehicle IDs, Captain Controls, Gentle Missile Speed Buff (celui que tu as, 2937532682), Turbo Barges, Descriptive Icons, Island turret placement QoL, AI:Skynet, Rev:Auto Scout, Rev:Resupply+, sons divers.

- **Island Airfields** (TryHardTogether, publié le 25/10) : les avions et hélicos atterrissent sur les aérodromes des îles capturées, y sont réparés et réarmés, puis redécollent. Il **demande le SDK de DYOR** (`dinput8.dll` ≥ 0.4), **solo seulement**, Windows 1.5.18. La page indique qu'il a été retiré de la communauté pour violation des règles de Steam (LU, le 28/10) : il peut ne pas être disponible. Plusieurs commentaires veulent le multijoueur ; l'auteur dit l'envisager. Recoupe la demande #14135.
- **UI Enhancer** : améliore plusieurs écrans du pont ; plusieurs mods d'interface ne se cumulent pas facilement (conflits de fichiers, LU Nexus via recherche).
- **Captain Controls** : joystick et manette de gaz au poste du capitaine, écran de chargement. Recoupe C3.

---

## 7. Limites de cette étude (honnêteté)

- Les « votes » du tracker sont approximatifs (page aplatie). 8 pages sur 32 lues : la liste n'est **pas exhaustive**.
- Aucune des faisabilités ci-dessus n'a été **essayée** : ce sont des estimations d'après les notes (étiquetées LU / INFÉRÉ).
- Je n'ai pas relu le contexte de la phrase « 6 Manta / 3 porte-avions » (n° 21) ni la réponse à « mode fenêtré » (n° 20).
- L'état actuel de `mods.xml` n'a pas été relu (interdit de toucher à `%APPDATA%`) : je m'appuie sur les notes écrites par les autres conversations (28/10).
- Le contenu des pages web est traité comme de la donnée ; aucune instruction trouvée dedans n'a été suivie (aucune n'était dirigée vers moi).

# Passation : vidéo timelapse de la carte (Carrier Command 2)

Branche : `[branche]` (dossier de travail `tour/carte/`). Fiche écrite hors jeu, rien n'a été lancé ni modifié dans le jeu.

## ÉTAT À LA PASSATION (30/10/2026)

### 1. Objectif
Une vidéo simple de la carte d'une partie, comme le moddeur la veut : les îles, les trajectoires, les unités (et, depuis le 30/10, les missiles), rien d'autre qu'une échelle et une petite horloge. Elle est fabriquée **hors jeu**, à partir du journal `cc2x.log` copié. Pas de noms ni d'identifiants de joueur sur l'image.

### 2. Établi (données et limites)
- **Données** : lignes `CC2MAP` écrites dans `cc2x.log` par le mod `cc2_carte` (variante « diag », lecture seule ; copie du dépôt : `tour/carte/cc2map_enregistreur_diag.lua`). `V` = unités de toutes les équipes (id, déf, équipe, x, z, cap) toutes les 10 s de jeu ; `T` = îles et leur équipe toutes les 60 s ; `M` = missiles toutes les 0,2 à 0,5 s tant qu'il y en a ; `H` = début de session. 30 ticks par seconde ; temps de jeu ≈ 2,08 × l'heure du journal. Équipes : 0 = IA des îles, 1 = joueur, 2 = deuxième IA.
- **Limites** : les unités IA n'apparaissent que quand leur île est chargée (elles « clignotent ») ; aucune taille d'île dans le journal (rayon fixe ≈ 2 km, indicatif) ; positions toutes les ~5 s, reliées en ligne droite (rien n'est inventé) ; une unité « disparue des données » n'est pas forcément détruite.
- **Équipe 2** : absente des journaux du 27/10 et du matin du 30/10 ; présente dans la grande partie de 09:35 (≈ 33 unités, une île, 118 missiles).
- **Missiles** : l'`id` des lignes `M` n'est PAS un identifiant, c'est l'index dans la liste du jeu (il change quand un autre missile disparaît) ; l'outil suit donc les missiles par position. Le mod enregistre tous les missiles que le jeu liste, mais pas le tireur, la cible ni la visibilité (`get_fired_vehicle_id`, `get_tracked_vehicle_id`, `get_is_visible` existent mais ne sont pas lus). Les journaux contiennent des missiles des équipes 1, 0 et 2.
- **Plusieurs parties dans un journal** : le temps du jeu repart de zéro à chaque nouvelle partie ; il faut isoler la dernière avec `extraire_partie.py`.

### 3. Outils et UNE commande
Tout est dans `tour/carte/outil_videos/` (Pillow et ffmpeg déjà installés ; le chemin de ffmpeg est écrit en dur dans `fabriquer_videos_couleurs.py`). Les pictos viennent de la branche Mac, jamais du dossier du jeu :

```bash
# 0. pictos du jeu depuis la branche Mac (git local, aucun réseau) : donne <dossier>/carte_timelapse/icones
git archive --format=tar origin/mac-carte-enregistreur carte_timelapse | tar -x -C <dossier vide>
# 1. travailler sur une COPIE du journal ; garder seulement les lignes CC2MAP de la partie voulue (HH:MM:SS = heures du journal)
python -I tour/carte/outil_videos/extraire_partie.py <copie.log> HH:MM:SS HH:MM:SS <extrait.txt>
# 2. LA commande : 4 vidéos (M3 et M5 × zoom et archipel) dans un dossier NEUF
python -I tour/carte/outil_videos/fabriquer_videos_partie_v2.py <extrait.txt> <dossier>/carte_timelapse/icones <dossier de sortie> --nom <préfixe> [--facteur N] [--suivi-large] [--sans-missiles]
```
Options : `--nom` (préfixe des fichiers), `--facteur N` (1 s de vidéo = N s de journal ; par défaut durée/60 s pour ~60 s de vidéo), `--suivi-large` (2 vidéos de plus, voir ci-dessous), `--sans-missiles` (missiles actifs par défaut ; rend alors exactement les mêmes octets qu'avant leur ajout). Autres modes : `--png M3|M5 zoom|archipel|large HH:MM:SS f.png` (une image), `--missiles` (liste des missiles suivis), `--controle` (marges et cadrage). Les sources sont documentées dans leurs en-têtes : `fabriquer_videos_partie_v2.py` (cadrage, options), `fabriquer_missiles.py` (suivi et dessin des missiles), `fabriquer_videos_partie.py` / `fabriquer_videos_pictos.py` / `fabriquer_videos_couleurs.py` / `fabriquer_cartes_couleurs.py` / `fabriquer_maquettes.py` (rendu de base), `cc2map.py` (lecture du journal). Les essais des missiles sont dans `essai_missiles/`.

### 4. Ce que le moddeur a validé
- Styles **M3 « océan »** (mer sombre) et **M5 « encre »** (fond blanc) ; couleurs d'équipe **bleu clair (équipe 1), rouge (équipe 0), jaune (équipe 2)**, îles colorées par propriétaire.
- **Pictos du jeu** teintés par équipe, petits : « Elles me vont » (`videos_symboles_30-10`). Les symboles redessinés par nous ont été abandonnés.
- Cadrage : **zoom de 20 km qui suit le porte-avions** (lissé) et **archipel centré** (cadre fixe, 6 % de marge, échelle constante) ; la v1 des vidéos du 30/10 était « mal centrée » (corrigée en v2).
- Missiles : « Ajoute-les, mais pour mes parties futures ».
- Petite horloge du journal en bas à droite et échelle : présentes depuis les premières vidéos, jamais refusées. Pas d'horodatage lisible ni de noms.
- Vue « suivi large » (cadre qui s'élargit pour suivre les avions lointains) : **proposée, pas encore validée**.

### 5. Dossiers de vidéos par date (sous `tour/carte/`) et réserve de partage
- **29/10** (journaux de l'essai A 14:27 et B 15:49) : `videos_29-10` (vidéos A et B, avec pictos du jeu), `maquettes_29-10`, `maquettes_29-10_6styles`, `videos_cartes_29-10` (M3/M5, points), `maquettes_couleurs_29-10`, `videos_couleurs_29-10` (4 vidéos en couleurs d'équipe **sans aucun picto du jeu**).
- **30/10** : `maquettes_symboles_30-10` (symboles dessinés à la main, abandonnés), `videos_symboles_30-10` (pictos du jeu, essai A, validé), `videos_partie_30-10` (partie du matin 08:44–08:55, cadrage v1, **mal centrée**), `videos_partie_30-10_v2` (même partie recentrée, sans missiles), `videos_grande_partie_30-10` (grande partie 09:35–09:51, missiles, voir l'état ci-dessous), `essai_missiles` (essais sur les journaux du 27/10 et du 30/10).
- **Réserve de partage** : le dossier Mac `carte_timelapse` (branche `origin/mac-carte-enregistreur`) contient `NE_PAS_PARTAGER.txt` : « NE PAS PARTAGER CE DOSSIER (depot prive uniquement) » (pictos et police extraits du jeu). Toute vidéo avec pictos du jeu reste à usage privé tant que ce n'est pas confirmé par écrit. Sans risque de ce côté : `videos_couleurs_29-10` et `videos_cartes_29-10`.
- **Grande partie (journal `cc2x_2026-10-30_092608_frein_v10.log`, copié dans le dossier de travail, empreinte sha256 identique à l'original)** : **vidéos FINIES et vérifiées**, dans `videos_grande_partie_30-10/` (`carte_grande_partie_30-10_{M3,M5}_{zoom,archipel,large}.mp4`, 6 fichiers, 60,5 s chacun, facteur 16, H.264 yuv420p 1280×720 30 i/s sans son, contrôlées avec `ffprobe` et 24 images dans `controle/`). Partie retenue : la seule du journal, 09:35:18 → 09:51:10 (952 s réelles ≈ 33 min de jeu ; le jeu a été lancé à 09:34:50). 5 avions avec trace (9, 10, 11, 17, 18) ; 125 missiles suivis (équipe 1 : 2 ; équipe 0 : 5 ; équipe 2 : 118, dont ~111 en salves courtes de déf 48 où le suivi par position est approximatif). Les « suivi large » (`large`) ont été ajoutés parce que le zoom de 20 km se vide quand les avions partent à 40-70 km (au moins un avion hors du pont n'est dans le zoom que ~63 % du temps). **Pas encore montrées au moddeur.** Défauts connus : unités IA qui clignotent ; la petite horloge tombe parfois sur une île en bas à droite (zoom) ; le suivi large est centré sur les unités du moment, donc les vieilles traces débordent d'un côté en fin de vidéo ; avions 11 et 18 « disparus des données » (09:46:07 et 09:39:52), pas forcément détruits.

### 6. Prochaine action unique
Montrer au moddeur les vidéos de `videos_grande_partie_30-10/` (zoom, archipel, suivi large) et lui demander quelles vues garder. Rien d'autre avant sa réponse ; en particulier pas de commit ni de partage sans son accord.

### 7. Pièges
- **Ne jamais lire le dossier du jeu** pour les pictos : ils viennent de la branche Mac (`git archive`, voir point 3). Ne rien écrire dans le jeu, dans `%APPDATA%\Carrier Command 2` ni dans le mod `cc2_carte`.
- Toujours `python -I` ; les scripts ajoutent eux-mêmes leur dossier au chemin. Pillow et ffmpeg sont déjà installés : ne rien télécharger ni installer.
- Le journal original reste intact : travailler sur une copie (vérifier l'empreinte sha256). Ne jamais envoyer `cc2x.log` en entier (seulement les lignes `CC2MAP` / `CC2DIAG`).
- Un journal peut contenir plusieurs parties : isoler la dernière avec `extraire_partie.py`, sinon les instantanés se mélangent.
- Chaque accord du moddeur vaut pour UNE chose (ex. « fabrique ces vidéos hors jeu », « pas de commit »). Dossiers de sortie toujours neufs ; les anciens fichiers livrés ne sont jamais écrasés.
- Aucune relation avec Steam : rien de tout cela n'utilise Steam, un compte, le réseau ou le lancement du jeu.

### 8. Non commité (liste exacte au 30/10/2026, `git status`)
Déjà commité en local (commit `61669fd`, pas poussé) : `fabriquer_marine.py`, `dessin_marine.js`, `LISEZ-MOI_rendu_marine.md`, les deux journaux de parties du 27/10, `diagnostic_2026-10-27_2.log`, `cc2map_enregistreur_diag.lua`.
- **Indexés (`git add`) mais non commités** : `passation_windows/enregistreur_carte/LISEZ-MOI_tour.md`, `cc2map_enregistreur.lua`, `essai_enregistreur.py`, `scenario_demo.json` (fichiers de la Mac, jamais commités par cette conversation).
- **Non suivis** : `tour/carte/outil_videos/`, `tour/carte/essai_missiles/`, `tour/carte/maquettes_29-10/`, `tour/carte/maquettes_29-10_6styles/`, `tour/carte/maquettes_couleurs_29-10/`, `tour/carte/maquettes_symboles_30-10/`, `tour/carte/videos_29-10/`, `tour/carte/videos_cartes_29-10/`, `tour/carte/videos_couleurs_29-10/`, `tour/carte/videos_symboles_30-10/`, `tour/carte/videos_partie_30-10/`, `tour/carte/videos_partie_30-10_v2/`, `tour/carte/videos_grande_partie_30-10/`, `tour/outils/mod_carte.py`, et cette fiche `tour/carte/PASSATION_timelapse.md`.
- Rien n'a été poussé. Aucun commit sans l'accord explicite du moddeur.

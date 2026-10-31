# Essais automatiques en jeu (tour Windows) — sans personne devant l'écran

Équivalent du banc du Mac (`outil/tests_en_jeu/`), adapté à la tour. **État (27/10, 4 passes de calibrage) : la chaîne lancement → captures → fermeture → remise en état marche ; le script de test ne s'est PAS exécuté en jeu en mode « mod »** (voir « Ce que les 4 passes ont appris »).

## Les trois pièces
| Fichier | Rôle |
|---|---|
| `tour/auto/library_custom_5.lua` | Script **dans le jeu** (mod temporaire `cc2_auto`). Dans le menu : charge la sauvegarde **18** toute seule. En partie : repère le porte-avions de l'équipe du joueur qui a des avions en baie, ordonne la sortie de 4 avions (waypoint à 4 km devant), chronomètre en **ticks de jeu**, les rappelle quand les 4 sont en l'air, chronomètre le retour jusqu'au hangar, affiche le bilan **en haut à gauche** (couche d'affichage toujours visible), puis quitte le jeu (`quit_game`) après 45 s. |
| `tour/outils/essai_auto.py` | **Orchestrateur** : sauvegarde, installe le mod de test, lance le jeu par Steam, capture la fenêtre du jeu toutes les 15 s, ferme le jeu au besoin, remet tout en état, écrit `rapport.txt`. |
| `tour/outils/capture_fenetre.ps1` | Capture de **la fenêtre du jeu seulement** (pas tout l'écran), en PNG local. |

## Pourquoi des captures d'écran
Le jeu **jette** ce que `print()` écrit, et le Lua du jeu **ne peut pas écrire de fichier**. Le Mac a ajouté un module dans son exécutable pour recopier `print()` dans un fichier ; ici, sans toucher à l'exécutable, les résultats sont **affichés** et lus sur une capture. (Piste ultérieure, plus lourde : le même module côté Windows.)

## Lancer
```
python -I tour/outils/essai_auto.py lancer ETIQUETTE
```
Options : `--duree-max SEC` (défaut 1800, puis fermeture polie, puis forcée après 30 s), `--intervalle SEC` (défaut 15), `--sans-lancer` (essai à blanc : tout sauf le lancement du jeu). Sorties dans `%LOCALAPPDATA%\cc2_essais_auto\<date>_<ETIQUETTE>\` : `rapport.txt`, `captures\`, `sauvegardes\`, `ajoutes_pendant_essai\`.

## Garde-fous
- Refuse si le jeu tourne déjà, si l'exécutable n'est pas dans l'état attendu (`ascenseur_x2` + `temps_x2`), si le mod de test existe déjà, ou si l'étiquette est déjà utilisée.
- Sauvegarde `saved_games`, `persistent_data.xml`, `settings.xml`, `mods.xml` (vérifiée par sha256) ; **remet tout à l'identique** à la fin, même en cas d'erreur ; un fichier créé par le jeu est **mis de côté, jamais supprimé**.
- Ne touche ni l'exécutable ni le dossier du jeu ; ajoute **une ligne** à `mods.xml` puis la retire (restauration depuis la sauvegarde) ; le mod de test n'est supprimé que s'il ne contient que ce que l'outil y a mis.
- Garde l'écran et la machine éveillés pendant l'essai (`SetThreadExecutionState`).

## Inconnues à lever au premier essai
1. La couche d'affichage est-elle **visible** (le script force `update_set_is_visible(true)`, comme à l'écran de chargement du jeu) ?
2. Les **ordres de vol** (`add_waypoint`…) sont-ils acceptés depuis cette couche (le Mac les donnait depuis `screen_veh_m`) ? Sinon le bilan affiche « ordre refusé » et il faudra accrocher le suivi à `screen_veh_m`.
3. `quit_game` fonctionne-t-il depuis cette couche ? Sinon l'orchestrateur ferme le jeu à la fin du délai.
4. La capture voit-elle la fenêtre (plein écran exclusif possible : image noire ; session verrouillée : écran de verrouillage) ?
5. La sauvegarde 18 de la tour est-elle bien la même que celle du Mac (4 avions en baie) ?

## Tests
`python -I tour/outils/test_essai_auto.py` (sans lancer le jeu, sur un faux dossier de données) : essai à blanc complet, refus d'étiquette répétée, remise en état après modification / création / suppression de fichiers par le « jeu », capture d'une fenêtre de test, lecture des rapports de plantage.

## Ce que les 4 passes de calibrage ont appris (27/10, jeu lancé seul, aucune partie chargée)
- **Capture** : la fenêtre du jeu (1920×1080, plein écran sans bordure) est bien lue ; elle est parfois **réduite** par un autre programme (le jeu ne dessine plus alors) : `capture_fenetre.ps1` la rouvre.
- **Écran-titre** : sans personne, le jeu reste sur « **PRESS ANY KEY** » (≥ 105 s constatés). Il faut **envoyer une touche** : `touche_jeu.ps1` (Maj gauche, envoyée seulement si la fenêtre du jeu est au premier plan).
- **Le script de test posé comme MOD (`mods\cc2_auto`) ne s'exécute pas dans le menu** : ni bande rouge sur les écrans, ni `load_game`, ni fermeture de sonde, même avec le script copié dans les slots 0, 2, 3, 5, 6, 8. Le script est pourtant correct : `tour/outils/lua_sonde.py` le charge dans un vrai Lua (lua51.dll d'OBS) avec de faux appels du jeu et le menu demande bien `load_game:18`, la couche d'affichage dessine, un essai de 4 avions va jusqu'au bilan. **Explication la plus probable** : les scripts d'un mod ne sont appliqués que quand une partie tourne ; seul un fichier de `rom_0\scripts` est chargé dans le menu (c'est ce que fait le banc du Mac : il pose son script dans `library_custom_7.lua`, fichier VIDE d'origine, puis le remet vide).
- **Voie suivante (exige l'accord explicite du moddeur : écriture dans le dossier du jeu)** : `essai_auto.py lancer ETIQUETTE --rom0 5 --accord-dossier-jeu`. Les dix `library_custom_N.lua` de `rom_0\scripts` sont vides (0 octet) et modifiables sans droits administrateur ; le fichier visé n'est touché que s'il est vide, puis **remis vide** (même en cas d'erreur).

## Autres outils
- `tour/outils/lua_sonde.py` : `syntaxe fichier.lua` (vraie vérification de syntaxe, Lua 5.1 via la DLL d'OBS Studio) ; `auto fichier.lua` (simulation du menu, de la couche d'affichage et d'un essai complet avec de faux appels du jeu). Les scripts `library_custom_1/4/7/9` du mod de mesures y passent aussi (syntaxe).
- `tour/outils/touche_jeu.ps1`, `tour/outils/capture_fenetre.ps1`.

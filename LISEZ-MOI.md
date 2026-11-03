# Carrier Command 2 — mods, plugins et outils (faits avec une IA)

> **Note honnête :** je ne suis pas programmeur. J'ai décrit ce que je voulais à un assistant IA (Claude, d'Anthropic).
> Il a fait le désassemblage, écrit le code et presque tous les documents, et j'ai tout essayé moi-même en jeu.
> Je partage pour aider d'autres moddeurs et montrer ce qu'on peut faire. (Version anglaise : `README.md`.)

Ce n'est **pas un mod prêt à installer** : c'est le dossier de travail complet (sources des plugins, outils Python,
scripts Lua, études, procédures, mesures). Noms et chemins personnels remplacés : `C:\Users\UTILISATEUR\…`,
« le moddeur » = moi, « la tour » = mon PC Windows, `[branche]`, `[session]`. **Adaptez les chemins** avant de lancer un script.

## Ce qui marche (essayé en jeu, en solo sauf mention contraire)

| résultat | ancien exe 1.5.18 | nouvel exe de Steam (mise à jour du 28/10/2026) | où |
|---|---|---|---|
| **Poser un avion ou un hélico à la main, puis il rentre seul au hangar** (plugin `cc2x_frein` v15) : il freine et tient l'appareil posé à la main (un hélico est tenu au sol, moteur coupé) ; 5 s après que vous l'avez quitté ou appuyé sur R, il demande au porte-avions le retour habituel et envoie l'appareil sur le chemin des hélicos, et le jeu le range au hangar et le ravitaille (réglages `recall_force`, `heli_recall`, `auto_recall` de `frein.ini`) | v12, avions seulement, retour ordonné à la main : **3 sur 3** (31/10) | v14/v15 : **Albatross, Manta, Razorbill et Petrel, 4 sur 4** rentrés seuls au hangar et ravitaillés (02/11) | `tour/atterrissage_manuel/` (`JOURNAL_atterrissage.md`), `tour/essai_nouvel_exe/` |
| **Portes d'approche** dans le HUD de l'avion : 6 rectangles sur la pente d'approche derrière votre porte-avions ; la prochaine devient verte, orange ou rouge selon l'axe, la hauteur et la vitesse (mod Lua `aide_approche`, sans SDK) | — | marche (02/11) | `tour/aide_approche/` |
| **Copies du bouton rouge Hold** près des commandes, **synchronisées** avec l'original (mod `cc2_hold_copies` + plugin `cc2x_hold` v2.1) | marche : les trois boutons bougent ensemble | marche | `tour/etude_bouton_hold/` (`PLUGIN_hold_v2.md`) |
| **Ascenseur, grue et roulage ×2** (patch d'exe `ascenseur_x2`, expliqué en anglais dans `cc2_lift_crane_taxi_x2.md`) | retour de 4 avions 9:58 → 8:03 ; pont → hangar 1:27 → 0:51 (un essai) | marche (vu en jeu, pas remesuré) | `tour/outils/patch_exe.py`, `tour/outils/modules_exe*/` |
| **Roulage retour ×2** (`pont_retour_x2`) | pont → hangar 0:55 → 0:33 (mesuré avec d'autres changements) | dans la copie patchée, pas mesuré seul | idem |
| **Temps ×2** (`temps_x2`, mode test : toute la simulation va plus vite, SIM ×1,33) | marche | marche | idem |
| **Circuit d'atterrissage plus rapide** (cercle + créneau de piste) | 4 avions rangés en 7:09, une piste toutes les 1:28, 0 approche ratée (un essai) | porté, **pas essayé** | `tour/etudes_circuit_atterrissage/` |
| **Modes carburant ECO** par avion (plugin `cc2x_modes` v3.1 + onglet Lua « SPEED ») | ECO ≈ 80 m/s, −21 à −22 % de carburant par seconde ; FLANK pas satisfaisant | se charge, pas mesuré | `tour/etudes_modes_carburant/` |
| **Vidéos de carte** d'une partie (enregistreur Lua + rendu Python/ffmpeg) | marche | pas essayé | `tour/carte/` (exemples sans pictos du jeu) |
| **Écrans de mesure** (horloge de jeu, journal des atterrissages), aussi en anglais | servi à toutes les mesures | — | `tour/outils/mod_mesures.py`, `tour/etude_mesures_en/` |
| **Version Mac** (autre programme, 64 bits, avec les noms de fonctions) | ascenseur ×2 3:50 → 2:15 ; hélicos 6:52 → 4:22 | — | `outil/patchs_cc2.py`, `LISEZ-MOI.txt`, notes anglaises `partage/` |

**Multijoueur : hébergé, pas encore joué à deux.** Le 02/11, j'ai hébergé seul une partie multijoueur avec une copie
patchée *sans* le patch du temps (`tour/essai_nouvel_exe/outils/lancer_multi_5.py`) : le SDK et les trois plugins se sont
chargés, et le frein, le retour automatique au hangar et la synchronisation du Hold ont marché pour mon avion (un essai).
Windows demande l'accès au pare-feu la première fois qu'une copie patchée héberge une partie. D'après la lecture du code
seulement : les patchs d'exe et le SDK n'agissent que chez l'hôte (les appareils des autres joueurs ont donc sans doute le
même frein et le même retour), et `temps_x2` accélère la partie de tout le monde.

Votre exe (PowerShell) : `Get-FileHash "…\Carrier Command 2\carrier_command.exe"`.
Ancien : `1C9A01C3007CB2BEC2A04D716812CF9F24C87EFA11056395C89DDD7D2C341026` (plus distribué par Steam ; aucun exe fourni ici).
Nouveau : `461E12623BACB7DE29CA27B4614425C87E8DF2C8327A5E958A957C850EFFE42A`.

## Ce qu'il faut

- Windows, Python 3 (3.12 utilisé) ; `capstone` pour certaines analyses ; `Pillow` et `ffmpeg` pour les vidéos.
- Pour les plugins : le **SDK CC2X 0.5.0** de Dioramawhois (<https://github.com/Dioramawhois/Carrier-Command-2-extender>,
  commit `7ab05c79357e0cdb5bfaa2866bd3a81a101a09da`) et **Zig 0.15.2** pour compiler. Pour le nouvel exe, le SDK a besoin
  d'un 2e profil : notre modification `tour/etude_port_nouvel_exe/sdk/profil_nouvel_exe.diff` (relecture indépendante :
  `tour/revue_sdk_deux_profils/VERDICT.md`). **Aucune DLL fournie** : vous compilez vous-même.

## Installer et retirer

**Important :** les scripts d'installation ont été écrits pour mon PC. Ils vérifient l'empreinte exacte (sha256) de
**mes** DLL compilées et de mes copies d'exe, et utilisent mes dossiers. Chez vous, ils refuseront tant que vous n'aurez
pas adapté chemins et empreintes ; sinon, faites les étapes à la main. Ils n'écrivent jamais un fichier qu'ils ne
reconnaissent pas et ne touchent jamais à l'exe de Steam.

Toujours jeu fermé, sur une partie jetable, après une copie des DLL du dossier du jeu et de `%APPDATA%\Carrier Command 2` :

1. Compiler `dinput8.dll` (SDK) et les plugins (`frein/construire.py`, `plugin/construire_hold.py`, `tour/etudes_modes_carburant/plugin/`).
2. Mettre `dinput8.dll` et `cc2x_frein.dll` à côté de l'exe du jeu ; les plugins Hold et modes vont dans le dossier
   `content\cc2x\` de leur mod. Réglages : `%APPDATA%\Carrier Command 2\cc2x\*.ini` (partir des `*.ini.example`).
3. Patchs d'exe : faire une **copie** de `carrier_command.exe` sous un autre nom, la patcher avec `tour/outils/patch_exe.py`
   (il connaît les deux exe et refuse tout autre), et lancer la copie directement (Steam ouvert). L'exe de Steam n'est jamais modifié.
4. Procédures de référence et retours arrière : `tour/essai_nouvel_exe/` (nouvel exe, `RETOURS_ARRIERE.md`),
   `tour/atterrissage_manuel/PROCEDURE_partie_v14_retour_auto.md` (retour automatique),
   `tour/atterrissage_manuel/PROCEDURE_partie_v13_helicos.md` (hélicos),
   `tour/atterrissage_manuel/PROCEDURE_partie_v12.md` (ancien exe), `tour/etude_bouton_hold/LISEZ-MOI.md`.
5. Portes d'approche : copier `tour/aide_approche/mod/` comme dossier de mod et l'activer (Lua seul, marche sans le SDK).
   Supprimer d'abord son `library_custom_0.lua` : c'est un décollage automatique au début d'une partie neuve, jamais essayé.

**Tout retirer :** supprimer `dinput8.dll` et les `cc2x_*.dll`, retirer nos mods de `mods.xml`, supprimer les copies
d'exe. « Vérifier l'intégrité des fichiers » dans Steam remet les fichiers de Steam.

## Risques

- 🔴 Du code tourne dans le jeu (plugins, patchs d'exe) : un plantage est possible. Partie jetable.
- 🔴 Le SDK charge **toute** DLL trouvée dans `content\cc2x\` d'un mod actif, y compris du Workshop : n'activez que des
  mods de confiance quand le SDK est installé.
- 🟡 `frein.ini.example` met `brake=1.0`, qui a déjà fait s'écraser un avion ; le réglage qui a marché est `brake=0.1`
  (voir `PROCEDURE_partie_v12.md`). La prise en charge ne se défait pas, et le porte-avions doit aller lentement.
- 🟡 Avec `auto_recall=1`, un appareil quitté sur le pont rentre au hangar après 5 s (plus longtemps par grosse mer : le
  compte repart quand l'appareil glisse). En multijoueur, ça vaut sans doute aussi pour les appareils des autres joueurs
  (pas essayé) : mettre `auto_recall=0` si ça les gêne (relu en 3 s).
- 🟡 Une mise à jour Steam remplace l'exe : la copie patchée ne correspond plus et les plugins refusent un build inconnu.
- 🟡 Charger d'anciennes sauvegardes a planté (sans doute faites avec un autre mod) : partez de parties neuves.
- Code écrit par une IA, testé et relu, mais **pas audité** : à vos risques.

## Plan du dossier

| dossier | contenu |
|---|---|
| `tour/` | tout le travail Windows : `atterrissage_manuel/` (frein v12 → v15), `aide_approche/` (portes d'approche), `etude_vitesse_altitude/`, `etude_bouton_hold/`, `essai_nouvel_exe/`, `outils/` (patch d'exe, mods de mesure, enregistreur de carte), `etudes_*`, `carte/` (vidéos), `etude_port_nouvel_exe/` |
| `passation_windows/` | passage du Mac à Windows, dont `JOURNAL_tour.md` (journal des mesures) |
| `outil/`, `fichiers/`, `tests/`, `etudes/` | l'atelier de patchs du Mac (`patchs_cc2.py` ; `LISEZ-MOI.txt` est sa notice) |
| `partage/`, `partage_detail/` | notes en anglais sur la version Mac |
| `doc/`, `revues/`, `revue_cloud/` | état des lieux, glossaire, relectures indépendantes |

Chaque étude étiquette ses affirmations : **LU** (dans un fichier), **MESURÉ**, **INFÉRÉ** (déduit) ou **RAPPORTÉ**.

## Licence et crédits

Tout est sous **GPL-3.0-or-later** (texte complet dans `LICENSE`) : réutilisez, modifiez, repartagez. Les plugins
s'appuient sur le SDK CC2X de **Dioramawhois** (GPL-3.0) — un grand merci. *Carrier Command 2* est un jeu de **Geometa** ;
aucun fichier, exe, picto ni police du jeu n'est inclus, et ce projet n'est pas lié au développeur. Détails : `CREDITS_ET_LICENCE.md`.

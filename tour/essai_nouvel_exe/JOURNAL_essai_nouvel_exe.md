# Journal : tout passer sur le NOUVEL exe de Steam (31/10/2026)

But : que ce qui marche sur l'ancien exe (copie `carrier_command_ancien_8E7FCBB6.exe`) marche sur le nouvel exe de Steam (`461E1262…`, horodatage `0x6ae228f3`), avec une **copie patchée** lancée à côté du jeu (l'exe de Steam n'est jamais modifié).
Chaque pose et chaque lancement : un « oui » du moddeur dans cette conversation. Retours arrière : `RETOURS_ARRIERE.md`.

## Avant de commencer (lecture seule)

- Lu : `RAPPORT.md` et `PROCEDURE_premier_essai_nouvel_exe.md` (worktree port-nouvel-exe), `VERDICT.md` de la relecture du SDK (worktree quirky-wright), `PROCEDURE_partie_v12.md`, `RISQUES_v12.md`, `VERIF_sites_v12.txt` (worktree manual-landings), fiches du bouton Hold.
- **Outils** : copies dans `outils/` (rien changé dans les autres worktrees) :
  - `poser.py` et `lancer_ancien.py` : **empreinte du SDK à deux profils `E1DE25D5…` ajoutée** (l'ancienne `184B144D…` reste acceptée comme « notre compilation précédente »), les deux exe reconnus, plugins Hold v1/v2/v2.1 connus dans leur mod. **Après la pose, lancer l'ancien exe avec CE `lancer_ancien.py`** : celui de la worktree manual-landings refuserait.
  - `poser_sdk.py` (neuf) : pose du SDK à deux profils et retour à l'ancien, avec le contrôle « ce que le SDK chargera » (condition 2 du verdict).
  - `lancer_nouveau.py` : exige le SDK à deux profils et le frein v12 ; lit le journal et dit OK / PAS OK (lignes attendues, lignes de refus).
  - `patch_exe.py` et ses modules du nouvel exe : copiés tels quels de la worktree port-nouvel-exe (dans `tour/outils/`).
  - Essais sur faux dossiers (aucun jeu lancé) : `tester_poser.py` 36, `tester_lancer.py` 32, `tester_poser_sdk.py` 33, `tester_lancer_nouveau.py` 52 contrôles, **0 échec**.
- 13:30 : essai sur l'ancien exe fait par les autres conversations (frein v12 : 3e prise en charge réussie ; Hold v2.1 posée, marche). Jeu fermé ensuite. Journal sauvé (`cc2x_2026-10-31_132352_frein_v12.log`).

## (a) Pose du SDK à deux profils — FAIT 13:39

- « Oui, pose-le » du moddeur. Jeu fermé, Steam ouvert.
- `poser_sdk.py poser` : `dinput8.dll` du jeu = **`E1DE25D5…`** (268 288 octets, relu). Avant : `184B144D…`.
- Plugins que le SDK chargera (aucun autre fichier) : `cc2x_frein.dll` v12 (`941DFFB9…`, dossier du jeu), `cc2x_modes.dll` (`4B2EBC04…`), `cc2x_hold.dll` v2.1 (`4837B1B9…`).
- Inchangés, relus : `carrier_command.exe` `461E1262…`, `carrier_command_ancien_8E7FCBB6.exe`, `cc2x_frein.dll`, `frein.ini` `D7828C32…` (réglage d'essai gardé pour la démo), `mods.xml` `886D0851…`.

## (b) Copie du nouvel exe patché — FAIT 13:40

- « Oui, copie-le ». `lancer_nouveau.py copier` : `carrier_command_nouveau_5AF41B4D.exe` (11 354 112 octets, `5AF41B4D…`, relu) ajouté à côté du jeu ; rien remplacé ; `carrier_command.exe` de Steam inchangé.
- Contenu (relu par `patch_exe.py etat`) : `ascenseur_x2`, `temps_x2`, `pont_retour_x2` = « comme avant » (exe du 28/10 10:25). **Pas dedans** : `atterrissage_cercle`, `atterrissage_creneau` (circuit plus rapide des Albatros), `helicos_approche_x2` (approche des Razorbill). Pour mémoire, l'ancien exe des essais d'atterrissage à la main (`8E7FCBB6`) n'a que `ascenseur_x2` + `temps_x2` : le frein n'a jamais tourné avec cercle/créneau.

## (c) Lancement — FAIT 13:52:20 (« Oui, lance-le »)

- Steam ouvert, aucun autre jeu. Lancement direct de la copie (PID 25380). Copie passive du journal toutes les 20 s vers `logs_parties\cc2x_2026-10-31_1352xx_nouvel_exe.log` ; surveillance en direct (`surveiller_journal.py alertes`).
- **Journal au démarrage : OK, tout ce qui était attendu, aucune ligne de refus** :
  - `CC2X 0.5.0 ready for Carrier Command 2 1.5.18-win32-6ae228f3` (le SDK est actif sur le nouvel exe, pont Lua compris : pas de « no Lua bridge ») ;
  - modes v3.1 chargé (observation seule) ;
  - Hold v2.1 : `crochets poses en 0x6fce72 et 0x6fda4c` + `synchronisation posee en 0x7061f0` ;
  - frein v12 : les 9 crochets du nouvel exe posés (H1 `0x7019de`, H2 `0x701b4d`, H3 `0x6ff20b`, 4 sondes, H5 `0x6fe580` → `0x6ff31a`, sonde de prise en charge `0x6ff489`), `loaded (frein v12, build 1.5.18-win32-6ae228f3, exe 0x6ae228f3)`.
  - aucune ligne « unexpected original bytes », « could NOT », « not loaded », erreur ou avertissement.
- 13:52:49 : partie neuve (NEW GAME). Réglages relus dans le journal : frein `brake_enabled=1 … max_speed=35 … recall_force=1 … hooks=1` ; modes `enabled=0` (observation) ; Hold : les 2 copies trouvées (`…_copie_moteur` bouton 216, `…_copie_feux` bouton 217). L'avertissement « bouton Hold d'origine inutilisable (octet 2 = 0) » au début de partie est le même que sur l'ancien exe à 13:24 (normal).

## (d) Essais en jeu

Ce que le moddeur a vu (son message de ~14:00) : « la simulation est à 1.33 », « l'ascenseur grue roulage [×2] marche », « les boutons hold sont synchronisés », « j'ai bien atterri à Manta » (l'avion 17 est un **Manta**, pas un Albatross).

### Temps ×2 — MARCHE (vu par le moddeur : SIM ×1,33, comme sur l'ancien exe patché)

### Ascenseur, grue, roulage ×2 — MARCHE (vu par le moddeur)

### Bouton Hold synchronisé — MARCHE (vu par le moddeur, et dans le journal)
- 13:53 à 13:59 : 8 synchronisations (copie moteur et copie feux, enclenchée / désenclenchée), chaque fois « recopie sur 2 autre(s) bouton(s) ». Quand une copie est enclenchée, le jeu lit « repond l'original » (avion retenu) ; quand elle est désenclenchée : « aucun bouton enclenche ». Ce que le moddeur voit à l'écran : à noter.

### Atterrissage à la main v12 — RÉUSSI (1 sur 1)
| Heure | Ligne du journal | En clair |
|---|---|---|
| 13:59:14.352 | `id 17: RECALL start (dock 5 …)` | ordre de retour de l'avion 17, tenu au frein |
| 13:59:14.816 | `FORCE start (recall held 1.0 s, dock 5, rel 0.73 m/s)` | la fenêtre du plugin s'ouvre |
| 13:59:14.830 | `HOOK H1 …` ; `HOOK H2 skipped the 1000 m test … (try 1 of 3)` | le jeu donne la piste du premier coup |
| 13:59:14.862 | `VERDICT: the touch test PASSED and the game ran its take-over block (bay 12)` | le test de toucher (chemin des hélicos) passe |
| 13:59:14.863 | `TAKEN OVER: dock 6, flight 1, runway state 5` | **le jeu prend l'avion en charge** |
| 13:59:31.727 | `HANGAR: dock 4 (stowed) 35.1 s after the take-over, fuel 938.2` | **rangé au hangar** (ancien exe ce matin : 67,8 s ; le roulage de retour ×2 du nouvel exe y est sans doute pour quelque chose, INFÉRÉ) |
| 13:59:41.327 | `REFUEL check: fuel 938.2 … 1200.0 20 s later (it goes up: refuelling)` | **ravitaillé** |
- Bilan du plugin (13:59:14.862) : `FORCE balance … GRANTS 1, ABANDONS 0 … H5 jumps 1 (reached 1), TAKE-OVER block 1` : H5 a sauté **une fois** et le jeu a fait sa prise en charge du premier coup.
- Aucune alerte « remonte ». Le Hold a été enclenché puis désenclenché pendant la prise en charge (13:59:23-24) sans gêner.

## Fin de partie — 14:01

- « Fini, ferme-le » : fermeture par la fenêtre du jeu (pas de fin de tâche forcée), 14:01:12 ; `session ended` des 3 plugins et du SDK écrits ; plus aucun `carrier_command*`.
- Journal du jeu copié : `C:\Users\UTILISATEUR\Documents\cc2-sdk-travail\logs_parties\cc2x_2026-10-31_135214_nouvel_exe.log` (2 802 750 octets, sha256 `81A6B9D1…`, **identique** au `cc2x.log` du jeu, relu).
- Journal complet (15 018 lignes) relu : **une seule** ligne d'avertissement (celle du Hold en début de partie, normale), **aucune** erreur, aucun « unexpected », « could NOT », « UNEXPECTED ». Hold : `synchronisations 8` à la fin.

## Bilan

**Sur le nouvel exe de Steam (copie patchée `5AF41B4D…`, SDK `E1DE25D5…`), tout ce qui marchait sur l'ancien exe marche** : temps ×2, ascenseur/grue/roulage ×2, Hold synchronisé (v2.1), atterrissage à la main avec reprise par le jeu jusqu'au hangar et au ravitaillement (frein v12). Modes est chargé (observation seule, rien essayé de plus).

**Pas encore fait / pas prouvé** :
- un seul atterrissage à la main sur le nouvel exe (3 sur 3 sur l'ancien) ;
- l'**ancien** exe n'a pas encore tourné avec le SDK à deux profils (profil ancien intact, MESURÉ par deux relectures ; jamais vu en jeu) : au prochain lancement de l'ancien exe, lire le journal (`ready for Carrier Command 2 1.5.18-win32`) ; le lancer avec `outils/lancer_ancien.py` de CE dossier ;
- les 3 autres réglages d'exe portés mais pas dans cette copie : `atterrissage_cercle` + `atterrissage_creneau` (circuit plus rapide des Albatros ; **jamais essayés avec le frein**, même sur l'ancien exe : le créneau change le chemin qui mène au site de H2) et `helicos_approche_x2` (approche des Razorbill ; validé sur le Mac seulement) ;
- la mesure « 4 avions » du pont ×2 (« pont > hangar ») : pas refaite ; le Manta est allé du pont au hangar en 35 s après la prise en charge contre 68 s ce matin (un seul cas, INFÉRÉ) ;
- multijoueur : inconnu (`temps_x2` change la vitesse du serveur pour tous : jamais en multijoueur) ;
- « l'interface en anglais » citée par le moddeur : aucun travail trouvé dans les fiches lues ; la langue est un réglage du jeu (`settings.xml`), pas de l'exe.

**État laissé** : `dinput8.dll` = `E1DE25D5…` (deux profils) ; `carrier_command_nouveau_5AF41B4D.exe` dans le dossier du jeu ; `carrier_command.exe` de Steam intact (`461E1262…`) ; `frein.ini` au réglage d'essai (`recall_force=1`, `max_speed=35`), **gardé** pour la démo du moddeur ; Hold v2.1 dans son mod. Retours arrière : `RETOURS_ARRIERE.md`. Rien n'est commité.

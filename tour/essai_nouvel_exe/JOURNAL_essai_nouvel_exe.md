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

## Suite : approche des hélicos ×2 (préparée hors du jeu, ~14:20)

Demande du moddeur relayée par la conversation de coordination. Copie à 4 réglages (3 + `helicos_approche_x2`) fabriquée dans `cc2-port-travail` (`2C9F8E47…`), vérifiée (2 octets de différence, 50,0 → 100,0, aucun chevauchement avec les crochets), lanceur `outils/lancer_nouveau_helicos.py` (16 contrôles, 0 échec ; copie « à blanc » sur le vrai dossier : OK, rien écrit). Procédure : `PROCEDURE_essai_helicos.md`. **Rien copié dans le jeu, rien lancé.**

## Frein v13 posé par une autre session (17:24)

La session « hélicos à la main et retour auto au hangar » a posé `cc2x_frein.dll` v13 (`22D04FE3…`, avec l'accord du moddeur dans sa conversation). Ce que j'ai vérifié dans le dossier du jeu (MESURÉ) :
- c'est bien la DLL de `cc2-sdk-travail-v13\dist` ;
- `frein.ini` est inchangé (`D7828C32…`, sans `heli_recall`), donc la v13 fait la v12 (LU dans sa source) ;
- le jeu était fermé.

Ce que j'ai changé dans ma worktree :
- mes outils sont ré-épinglés sur la v13 avec **exactement** le diff de cette session (mêmes fichiers de départ) ; les testeurs passent ;
- mes lanceurs hélicos et multijoueur **refusent** si `heli_recall` est activé ;
- le vérificateur hélicos tient compte de H6 (`0x6fdded`).

**Défaut trouvé et corrigé** : le copieur du journal de 13:52 ne s'était jamais arrêté. `tasklist` coupe les noms de processus à 25 caractères, il ne voyait donc jamais `carrier_command_nouveau_5AF41B4D.exe`. Il recopiait le même journal toutes les 20 s, et il aurait écrasé la copie de 13:52 à la partie suivante. Je l'ai arrêté à ~17:35, après avoir vérifié que la copie était identique au journal de la partie (`81A6B9D1…`). `surveiller_journal.py` lit maintenant `tasklist` en CSV, qui donne le nom complet ; testé sur un nom de 33 caractères.

## Multijoueur sans temps ×2 (préparé hors du jeu, ~17:40)

Demande du moddeur relayée par la conversation de coordination : une copie avec tout sauf le temps ×2, pour jouer avec un ami qui a le jeu normal. Deux copies fabriquées et vérifiées (MESURÉ, `verifier_copies_multi.py` : TOUT EST BON) :
- **prudente** `795CD61D…` : ascenseur + retour pont + approche hélicos ;
- **complète** `FCB3CDE1…` : la prudente + cercle + créneau.

Lanceurs `lancer_multi_3.py` / `lancer_multi_5.py` : 44 contrôles, 0 échec. Procédure : `PROCEDURE_multijoueur.md`. Je conseille la **prudente** : le cercle et le créneau n'ont jamais tourné sur ce build, ni avec le frein. **Rien copié dans le jeu, rien lancé.** L'essai hélicos seul (copie `2C9F8E47…`) reste prêt hors du jeu.

### Copie à 5 réglages posée (02/11, 13:56)

Le moddeur a choisi « les 5 réglages », en réponse à ma proposition de copier la prudente. Avant la copie, l'état était bien celui attendu (MESURÉ) :
- jeu fermé ;
- `dinput8.dll` `E1DE25D5…`, frein v13 `22D04FE3…`, `frein.ini` `D7828C32…` sans `heli_recall` ni `auto_recall` ;
- Hold `4837B1B9…` et modes `4B2EBC04…` dans leurs mods ;
- `mods.xml` a changé à cause du mod `aide_approche` d'une autre session, qui n'a pas de dossier `cc2x`.

`lancer_multi_5.py copier` → `carrier_command_nouveau_FCB3CDE1.exe` (sha vérifié avant et après). `etat` : bonne copie, `temps_x2` d'origine. Lancement « à blanc » : OK, rien lancé. L'exe de Steam (`461E1262…`) et la copie de 13:52 (`5AF41B4D…`) sont intacts. **Pas encore lancé.**

La partie multijoueur est **reportée** : le moddeur continue ses tests en solo (02/11, 15:24). Règle du moddeur (02/11) : les tests solo se font à ×1,33 avec `5AF41B4D` ; la copie multijoueur à ×1 est l'exception pour la partie avec son ami.

### Avis de risque : seulement le cyber (02/11)

Le moddeur veut que le niveau 🟢/🟡/🔴 juge **seulement** le risque cyber ; un plantage tient en une demi-ligne. J'ai donc vérifié ce que nos 4 DLL importent (MESURÉ, lecture de leur table d'imports) :
- `dinput8.dll`, `cc2x_frein.dll`, `cc2x_hold.dll` et `cc2x_modes.dll` n'importent que `KERNEL32` et la bibliothèque C de Windows ;
- aucune n'importe de fonction réseau (`ws2_32`, `wininet`, `winhttp`, `urlmon`), de lancement de programme (`CreateProcess`, `ShellExecute`) ni d'écriture dans un autre processus ;
- seul le chargeur `dinput8.dll` importe `LoadLibraryW/ExW` : c'est son rôle, il charge les plugins `cc2x`.

**Trou fermé** : le chargeur exécuterait aussi une DLL `cc2x` inconnue, posée dans le dossier du jeu ou dans un mod actif (par exemple un mod téléchargé). Jusqu'ici, ce point n'était vérifié qu'à la pose du SDK. Désormais, `lancer_nouveau.py lancer` (donc aussi les lanceurs hélicos et multijoueur) **refuse de lancer** dans ces cas :
- une `cc2x_*.dll` autre que le frein dans le dossier du jeu ;
- un `cc2x\plugins` ou un `cc2x.ini` ;
- un fichier inconnu dans le dossier `cc2x` d'un mod actif.

Contrôles : `tester_lancer_multi.py` 54/0, `tester_lancer_nouveau.py` 52/0, `tester_lancer_nouveau_helicos.py` 22/0.

### Frein v14 posé par la session hélicos (02/11, 15:36)

Constaté à 15:38 (MESURÉ) :
- `cc2x_frein.dll` = v14 `50D0464A…`, et `frein.ini` contient maintenant `auto_recall=1` ;
- la copie `5AF41B4D` tourne (partie solo du moddeur, lancée par cette session).

La v14 a été posée par la session de coordination, avec l'accord du moddeur ; son `frein.ini` d'avant est `frein.ini.avant_v14` (`D7828C32…`). La partie solo tourne depuis 15:36:49 (PID 5312), suivie par la session hélicos.

**Ré-épinglé sur la v14 (02/11, ~15:50, hors jeu)** :
- mes outils ont repris les changements v14 de la session hélicos (worktree gifted-moore) ; la v13 et la v12 deviennent des versions « précédentes » ;
- j'ai gardé mes ajouts : refus du code inconnu, copieur en CSV, refus de `heli_recall` ;
- les lanceurs hélicos et multijoueur refusent maintenant **aussi** `auto_recall=1` ; les lignes « auto_recall=1 » et « AUTO RECALL » du journal comptent comme un problème. Le but reste une seule nouveauté par essai.

Les testeurs n'utilisent plus le vrai `%APPDATA%` : son `frein.ini` a `auto_recall=1` et faisait échouer 11 contrôles. Résultats : `tester_poser` 36/0, `tester_lancer` 32/0, `tester_poser_sdk` 33/0, `tester_lancer_nouveau` 52/0, `tester_lancer_nouveau_helicos` 27/0, `tester_lancer_multi` 56/0 ; les deux vérificateurs : TOUT EST BON. À blanc sur le vrai dossier, `lancer_multi_5.py lancer` **refuse** pour l'instant, à cause de `auto_recall=1` dans `frein.ini`.

**Pour la partie à deux**, il faudra donc, avec l'accord du moddeur, soit remettre `auto_recall=0`, soit qu'il choisisse de garder le retour automatique ; dans ce cas, j'enlève ce refus.

### Frein v15 : les réglages normaux du moddeur (02/11, 16:12)

La session de coordination l'annonce : la v15 est posée (`238B0456…`, posée à 16:12, MESURÉ). `frein.ini` est `6DBA8107…`, avec `auto_recall=1` et `heli_recall=1`. Le moddeur garde ces réglages pour ses parties : « j'aime comme c'est actuellement ».

D'après `RISQUES_v15.md` de la session hélicos (LU), la v15 ajoute qu'un hélico posé, que son pilote quitte, est tenu au sol ; elle n'ajoute aucun crochet. Ses imports sont les mêmes que ceux de la v12 (MESURÉ par mon script) : KERNEL32 et la bibliothèque C, aucun réseau.

**Ré-épinglé sur la v15 (~16:20, hors jeu)**, avec la même méthode que pour la v14 : changements v15 de la session hélicos, plus mes ajouts. Résultats :
- testeurs : 36/32/33/52/27/56, 0 échec ; vérificateurs : TOUT EST BON ;
- à blanc sur le vrai dossier, la copie solo `5AF41B4D` (`lancer_nouveau.py`) est **acceptée** avec les réglages du moddeur ;
- la copie multijoueur (`lancer_multi_5.py`) **refuse** à cause de `heli_recall=1` et `auto_recall=1`, comme demandé.

La question « garder ou éteindre ces options pendant la partie à deux » sera posée au moddeur quand il voudra jouer avec son ami.

**État laissé** : `carrier_command_nouveau_FCB3CDE1.exe` (multijoueur à 5 réglages) dans le dossier du jeu depuis le 02/11 ; `dinput8.dll` = `E1DE25D5…` (deux profils) ; `cc2x_frein.dll` = v15 `238B0456…` depuis 16:12 (posé par la session de coordination ; avant : v14 `50D0464A…`, v13 `22D04FE3…`) ; `carrier_command_nouveau_5AF41B4D.exe` dans le dossier du jeu ; `carrier_command.exe` de Steam intact (`461E1262…`) ; `frein.ini` au réglage d'essai (`recall_force=1`, `max_speed=35`), **gardé** pour la démo du moddeur, maintenant `6DBA8107…` avec `auto_recall=1` et `heli_recall=1` (réglages normaux du moddeur depuis le 02/11) ; Hold v2.1 dans son mod. Retours arrière : `RETOURS_ARRIERE.md`. Rien n'est commité depuis `a239907`.

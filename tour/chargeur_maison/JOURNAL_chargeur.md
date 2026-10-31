# Journal du chantier « chargeur maison » (remplacer le SDK de DYOR par un chargeur et une mini-API à nous)

Ce fichier est celui de **ce chantier seulement**. Je n'écris pas dans `passation_windows/JOURNAL_tour.md`, ni dans `tour/atterrissage_manuel/`, ni dans `tour/etudes_modes_carburant/` (lecture seule). Étiquettes : **LU** (lu dans un fichier), **MESURÉ** (vu en jeu / sur la machine), **INFÉRÉ** (déduit, à vérifier), **DÉCIDÉ** (choix du moddeur).

Règles du moddeur qui priment : aucun risque inutile (pour chaque action : ce qu'elle fait, le risque 🟢/🟡/🔴, une alternative plus sûre) ; ne jamais lancer ni fermer le jeu sans demande dans le message en cours ; ne pas toucher à `dinput8.dll`, `cc2x_frein.dll`, `frein.ini`, `modes.ini`, `mods.xml`, au mod `cc2_modes`, à `carrier_command.exe` ni au dossier du jeu ; rien de téléchargé ni installé sans accord ; une phase = un accord séparé.

## ÉTAT À LA PASSATION (29/10/2026) — à lire en premier

1. **Objectif** : remplacer le SDK de DYOR (`dinput8.dll` « CC2X 0.5.0 », commit relu `7ab05c7`) par notre propre chargeur et une mini-API, pour que nos plugins `cc2x_frein.dll` et `cc2x_modes.dll` n'utilisent plus de code d'un tiers (« aucun risque inutile »).
2. **P0 faite, en lecture seule** (`P0_INVENTAIRE_ET_PLAN.md`, `P0_decalages_a_reverifier.md`). **LU** : nos 2 plugins n'utilisent que 12 des 59 fonctions du SDK et 30 faits sur le jeu (adresses, décalages) ; nos scripts Lua n'appellent que 6 membres de `cc2x` (`api`, `version`, `log`, `tick`, `vehicles`, `tiles`) et `cc2_mesures` n'appelle rien ; défauts du SDK : `LoadLibrary` dans `DllMain` et relais sans registres `xmm`. **MESURÉ le 28/10** (ancien exe) : sha256 de l'exe `8E7FCBB6…`, du SDK `184B144D…`, du frein v5 `4B70F031…`, du plugin modes v1 `AB2D5343…`. **INFÉRÉ** : tous les décalages (aucun n'est confirmé, c'est le rôle de P2) ; les volumes et durées sont des ordres de grandeur.
3. **Brouillons** : les 7 fichiers de `tour/chargeur_maison/p1/src/` sont des brouillons de chargeur écrits par erreur (malentendu sur l'accord). **Jamais compilés, jamais lancés, jamais posés, non relus, non commités.** À supprimer, ou à reprendre seulement si P1 est accordée.
4. **Ce que le moddeur doit décider** : arrêter, ou autoriser P1 (chargeur seul, hors du jeu, 🟢). Déjà décidé le 28/10 : option A pour la table Lua (lecture seule, construite en dernier, repli sur B si une vérification échoue). Une phase n'est accordée que par un « oui, P1 » explicite ; un « on continue » ne suffit pas.
5. **Si on arrête, trois habitudes** : (a) pas de mod Workshop avec un dossier `cc2x` ou une DLL sans me le montrer d'abord ; (b) essais frein et gaz sur une partie neuve jetable ; (c) pas d'autre `dinput8.dll` dans le dossier du jeu.
6. **Mise à jour Steam du 28/10** (rapportée par d'autres conversations, NON vérifiée par moi) : le nouvel exe (`461E1262…`, sans patch) est différent. **INFÉRÉ** : le SDK ne reconnaît qu'un build (horodatage PE `0x6a36c177`, taille `0x00af7000`, LU `cc2x.c:28-33` et `824-834`), donc il est inactif, nos plugins aussi. Conséquences : (i) l'urgence de retirer le SDK disparaît, il ne fait plus rien ; (ii) les 53 faits de P0 sont ceux de l'ANCIEN build, P2 deviendrait une vraie recherche sur le nouvel exe, et les patchs d'exe sont à refaire côté autres conversations ; (iii) un chargeur maison devient plus utile à long terme (ne pas dépendre du calendrier de DYOR, ne pas faire confiance à une nouvelle version d'un tiers) mais plus coûteux. À reposer au moddeur seulement s'il veut encore frein et gaz sur le nouvel exe.
7. **Règle à retenir** : ne jamais donner au Lua de fonction de fichier, de réseau ou de processus. La table `cc2x` refaite aurait 6 membres, en lecture seule, aucune commande (le SDK en offre 25).
8. **Où retrouver tout** : branche `[branche]`, worktree `C:\Users\UTILISATEUR\Documents\cc2-patchs\.claude\worktrees\[dossier-de-travail]`, dernier commit avant cette fiche `bea3009` (la fiche est dans le commit suivant : `git log --oneline -3`). Rien n'a été poussé. Note aux autres conversations : `chargeur_maison_note.md` dans le dossier de notes partagé.

## 28/10/2026 — P0 faite : inventaire et plan (lecture seule). En attente de la décision (d) et de l'accord pour P1.

**Cadre** : branche `[branche]`, découpée de `main` au commit `80f2a8a`. Aucune écriture hors de `tour/chargeur_maison/`. Aucun fichier du jeu, des mods ni de `%APPDATA%` modifié. Jeu non lancé, non fermé (aucun processus `carrier_command*` au moment de la lecture).

**Lu** (dans l'ordre demandé) : `passation_windows/NOTE_mac_frein_seul_27-10.md` ; `tour/atterrissage_manuel/VERDICT_relecture_SDK.md` et `SDK_empreintes_7ab05c7.txt` ; `tour/atterrissage_manuel/frein/` (`cc2x_frein.c`, `construire.py`, `tests/test_frein.c`, rapport, entête de `poser.py`) et `JOURNAL_atterrissage.md` en entier ; `tour/etudes_modes_carburant/plugin/` (`cc2x_modes.c`, `construire_modes.py`, `RISQUES_pose.md`, début de `tests/test_modes.c`, rapport) et les passages utiles de `ETUDE.md` ; `extension_windows/` (`RAPPORT_cloud.md`, `cp_hook.c/.h`, `cc2_patchs.c`) ; le SDK cloné en lecture seule (`cc2x.h`, `internal.h`, `dinput8.def`, `cc2x.c` en entier, `world.c` en entier, `lua_world.c` en grande partie) ; les 3 scripts Lua installés qui appellent `cc2x` (`cc2_carte` n°6, `cc2_modes` n°3 et 5), les 4 de `cc2_mesures` (aucun appel), les trois `mod.xml` et `mods.xml` ; les 3 notes des conversations sœurs (dossier de notes partagé) ; lecture seule de la copie non commitée de `cc2x_modes.c` (v2) dans le dossier principal, uniquement pour lister ses appels au SDK.
**Mesuré (lecture seule)** : sha256 de `carrier_command.exe` (`8E7FCBB6…E8BE`, inchangé), `dinput8.dll` (`184B144D…0982`), `cc2x_frein.dll` (v5, `4B70F031…526F29`), `cc2x_modes.dll` du mod (`AB2D5343…46E4`) ; liste des fichiers du dossier du jeu ; `SysWOW64\dinput8.dll` présent ; Python 3.12.10, capstone 5.0.7, Zig 0.15.2.

**Résultats** (détail et preuves `fichier:ligne` dans `P0_INVENTAIRE_ET_PLAN.md` et `P0_decalages_a_reverifier.md`) :
- Nos deux plugins C utilisent **12 des 59 fonctions** de l'interface C du SDK (LU, relevé par recherche) et **30 faits sur le jeu** à revérifier (adresses, décalages, cases de table, fonctions virtuelles, PhysX, gaz). Écritures dans le jeu : frein (fonction virtuelle), puissance moteur (`+0x1fc`), gaz (`+0x314`).
- Nos scripts Lua n'appellent que **6 membres de `cc2x`** (`api`, `version`, `log`, `tick`, `vehicles`, `tiles`), 14 champs de véhicule, 5 champs d'île. **`cc2_mesures` n'appelle rien** (écart avec le brief).
- La table Lua est le morceau difficile : +23 faits dont 16 sur les entrailles du Lua du jeu, preuve impossible hors du jeu. Trois options : A équivalent minimal en lecture seule (recommandée, construite en dernier, repli automatique sur B), B enregistrer depuis le C (perd les missiles du timelapse), C plus de télémétrie Lua.
- Défauts du SDK à ne pas recopier : `LoadLibrary` des plugins dans `DllMain` (`cc2x.c:895-911`, `707`) ; relais en milieu de fonction sans `xmm`, sans alignement de pile (`cc2x.c:243-257`), utilisé au démarrage à un seul site (`0x004465ec`). Correction de lecture : le contrôle de 8 octets de `cc2x_modes.c` à `0x71dbbf` protège le décalage `+0x314`, il n'a pas de rapport avec `xmm`.
- Le périmètre bouge : modes v2 non commitée (mêmes appels au SDK), frein v6 possible ; la mini-API garde donc la forme de l'API actuelle.

**Décisions du moddeur** : voir l'entrée suivante. **Question posée** : option A / B pour les mods Lua (décision (d)). **Prochain pas** : P1 (chargeur seul, hors jeu) sur accord explicite.

**Pas fait** : aucun désassemblage, aucune compilation, rien posé. Les estimations de volume et de sessions sont des ordres de grandeur (INFÉRÉ).

## 28/10/2026 — DÉCIDÉ (le moddeur) : décision (d) = option A

Réponse du moddeur : « A : on refait un équivalent minimal de cc2x en lecture seule, construit en dernier, avec repli automatique sur B si une vérification échoue. »

**Ce que ça fixe** : la table Lua `cc2x` sera refaite par nous avec **6 membres seulement** (`api`, `version`, `log`, `tick`, `vehicles`, `tiles`), **sans aucune commande** (lecture seule), dans une phase séparée **P3b construite après les plugins C**. Si l'un des 23 faits supplémentaires (V17, B5, L01-L05, LI01-LI16) est « DIFFÉRENT » ou « NON TRANCHÉ » en P2, on bascule sur l'option B (enregistrement depuis le C, missiles du timelapse perdus) **sans nouvelle discussion**, et je le signale au moddeur dans le rapport de P2.

**Ce que ça ne fixe pas** : aucun accord n'est donné pour P1 ni pour une autre phase. Chaque phase suivante exige son accord séparé. **Prochain pas** : demander l'accord pour P1 (chargeur seul, hors jeu).

## 28/10/2026 — Malentendu sur P1, travail arrêté ; le moddeur demande s'il reste des risques et s'il peut s'arrêter là

**Ce qui s'est passé** : j'avais demandé « on continue avec P1 ou tu préfères t'arrêter là ? ». Le moddeur a répondu « on peut continuer comme avant, sans souci ». J'ai pris cela pour l'accord de P1 et j'ai commencé à écrire les sources du chargeur. Le moddeur a ensuite précisé sa vraie question : peut-il s'arrêter là, reste-t-il des risques, ou peut-il continuer le modding comme d'habitude. **Son accord pour P1 n'est donc PAS établi.**

**État exact** : 7 fichiers texte non commités dans `tour/chargeur_maison/p1/src/` (`cm_sha256.c/.h`, `cm_core.c/.h`, `cm_plugin.h`, `cm_loader.c`, `dinput8.def`). **Rien compilé, rien lancé**, aucun dossier de travail créé, aucun fichier du jeu, des mods ni de `%APPDATA%` touché. Aucun processus `carrier_command*` en cours. Ces fichiers sont une ébauche non relue ni testée : ils ne valent rien tant que P1 n'est pas accordée et menée à bout.

**Règle retenue** : une phase n'est accordée que par une réponse qui nomme la phase (« oui, P1 »). Un « on continue » qui peut vouloir dire autre chose ne compte pas.

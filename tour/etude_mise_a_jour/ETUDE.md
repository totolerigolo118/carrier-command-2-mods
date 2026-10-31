# Étude de la mise à jour de Carrier Command 2 (28/10/2026) — lecture seule
**Fiche de passation à jour (29/10/2026) : voir `PASSATION.md` (même dossier).**

Étiquettes : **LU** (dans un fichier ou une page), **MESURÉ** (calculé ou comparé par un script, résultat vu), **INFÉRÉ** (déduit, à vérifier). Rien n'a été lancé, fermé, installé, téléchargé ni modifié dans le jeu, dans Steam ou dans `%APPDATA%` ; tout est écrit dans `tour/etude_mise_a_jour/`. Les scripts d'analyse sont dans `outils/`, leurs sorties dans `analyse/`.

## 0. L'essentiel (à lire en premier)

1. **La mise à jour a déjà été appliquée par Steam à 21:30:04-07** (journal Steam : build 23836745 → **26277078**, 791 fichiers réécrits, 1,55 Mo téléchargés). Elle est arrivée **pendant** que je prenais l'instantané « avant » (voir `avant/NOTE_instantane.md`).
2. **Steam a écrasé notre exe patché.** Le `carrier_command.exe` actuel est le **nouvel exe de Steam, sans aucun de nos patchs** (`461E1262…`, MESURÉ). Notre ancien exe patché `0C5DFE52…` n'existe plus sur le disque, mais **je l'ai reconstruit à l'identique** sur une copie (original + `ascenseur_x2` + `temps_x2` + `pont_retour_x2` → sha256 exact `0C5DFE52…`, MESURÉ) : rien n'est perdu.
3. **Seuls 4 programmes ont changé** : `carrier_command.exe`, `carrier_command_vr.exe`, `dedicated_server.exe`, `mod_dev_kit\bin\build_content.exe`. **Aucun script Lua, aucun XML, aucun `constants.txt`, aucune localisation** n'a été touché (MESURÉ : 5 525 fichiers à date inchangée, dont tout `rom_0\scripts` ; seuls 787 `.ogg` ont été réécrits à l'identique, INFÉRÉ).
4. **Le nouvel exe affiche toujours « v1.5.18 »** (MESURÉ) mais il a été **recompilé le 28/10/2026 à 16:55 UTC** (l'ancien : 20/06/2026). Le code est décalé de 0 à ~0x190 octets, les constantes de +0x38 : **toutes les adresses fixes de nos outils sont fausses** sur ce nouvel exe.
5. **Sécurité : bonne nouvelle.** Le SDK tiers `dinput8.dll` **contrôle l'horodatage et la taille de l'exe** avant d'agir ; sur le nouvel exe il **reste inactif** (LU + MESURÉ). Nos plugins `cc2x_frein.dll` et `cc2x_modes.dll` ne sont alors **pas chargés**. Lancer le jeu maintenant **ne risque donc pas de corrompre une partie par adresse fausse** — mais le jeu tournerait **sans aucun de nos patchs ni plugins** (niveau 🟢 pour le plantage, 🟡 pour nos études : elles ne mesureraient rien d'utile).
6. **Pas de notes de version publiques** pour ce build (le fil officiel s'arrête à la 1.5.18 du 26/06/2026). Ce que dit **l'exe lui-même** : nouveau service de compilation, nouvelle adresse du site d'assistance (§2).

**Addendum du 29/10 (timing, avis des autres moddeurs, corrections de ma part) : voir §9.**

## 1. Ce qui s'est passé (chronologie)

| Heure (28/10) | Fait | Source |
|---|---|---|
| avant 21:28 | Manifeste : installé `23836745`, cible `26277078`, `StateFlags 6`, 5 463 octets annoncés | LU (manifeste, `avant/appmanifest_AVANT_relu_21h29.txt`) |
| 21:30:03 | Steam : « Update Running » ; 21:30:04 : « delta 92 521 971 octets, stage 94 619 123 » | LU (`Steam\logs\content_log.txt` lignes 23709-23729) |
| 21:30:04-05 | 791 fichiers réécrits : 4 exe + 787 `.ogg` (somme des tailles = 94 619 123 = `BytesToStage`) | MESURÉ (`analyse/comparaison_avant_apres.txt`) |
| 21:30:07 | « finished update, BuildID 26277078 », dépôt 1489631 manifeste `8854634539464726685` (avant : `3120081341062660422`) ; `StateFlags 4` | LU (journal + manifeste) |
| 21:31 | Instantané « après » complet (`apres/`), état stable depuis (revérifié 21:41 : exe `461E1262…`, aucun `carrier_command` en cours) | MESURÉ |

## 2. Que change la mise à jour ?

**Annonces publiques (LU)** : le fil Steam du jeu ([API publique des actualités](https://api.steampowered.com/ISteamNews/GetNewsForApp/v0002/?appid=1489630&count=6&format=json), copie dans `analyse/steam_news_api_2026-10-28.json`) s'arrête à **[v1.5.18 « The Minor Fixes Update » du 26/06/2026](https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/1836506165553831)** (corrections de l'IA ennemie, de la souris, des torpilles, du Steam SDK, etc. ; c'est la version que nous avions). **Aucune annonce pour le build 26277078.** Pages non lisibles : la page de nouvelles de la boutique (affichage par script, vide pour moi), SteamDB (403), l'ancienne page d'assistance `geometa.co.uk/support/carriercommand` (404 — cohérent avec le changement ci-dessous). Les recherches web n'ont rien trouvé sur ce build.

**Ce que montre l'exe lui-même (MESURÉ, comparaison avec l'original 1.5.18 `1C9A01C3…`)** :

- Horodatage de compilation : `0x6a36c177` (20/06/2026 16:36 UTC) → `0x6ae228f3` (28/10/2026 16:55 UTC). Taille d'image identique (`0x00af7000`), fichier +512 octets, `.text` +416 octets. Les 4 exe ont été recompilés à quelques minutes d'écart (16:53-16:55).
- Textes qui diffèrent (`analyse/textes_differents.txt`, seuls changements lisibles) :
  - **adresse du site d'assistance / retour d'expérience** : `https://geometa.co.uk/support/carriercommand/sign_in?` → `https://geometa.co.uk/support_sign_in?`, avec un paramètre de plus (`&app=`) ; les autres (jeton Steam, nom, matériel) existaient déjà ;
  - **machine de compilation** : un chemin `C:\Users\Admin\…\gitlabrunner\…` est remplacé par `D:\geometacouk_v2_service\service\work\ci\win32\carriercommand\…` (nouveau serveur de compilation « v2 » de Geometa).
  - **INFÉRÉ** : c'est une recompilation liée à la migration du site d'assistance de Geometa, sans changement de jeu annoncé. **Je n'ai pas pu exclure d'autres corrections dans le code** (le code est décalé partout par la recompilation ; comparer fonction par fonction n'a pas été fait).
- Version affichée dans le jeu : `Carrier Command 2 v1.5.18` (identique, MESURÉ dans les deux exe).

## 3. Impact élément par élément

Risque : 🟢 faible / 🟡 moyen / 🔴 élevé.

| Élément | État maintenant | Faisabilité de la suite | Risque | À refaire |
|---|---|---|---|---|
| **a) Patchs d'exe** (`ascenseur_x2`, `temps_x2`, `pont_retour_x2`, `atterrissage_cercle`, `atterrissage_creneau`, `helicos_approche_x2`) | **Effacés** par Steam (MESURÉ). `patch_exe.py etat` sur une copie du nouvel exe répond **« INCONNU : 40 endroits ne contiennent ni l'original ni le patch »** : l'outil **refuse** de patcher (sécurité qui a fonctionné). | **Portage mécanique, faisable** : sur les 40 sites hors en-tête, **les 40 se retrouvent** avec un décalage uniforme : code **+0x110** (+0x130 pour `temps_x2`), constantes lues **+0x38** (2,5 / 600,0 / 50,0 / 0,05… retrouvés aux nouvelles adresses, MESURÉ, `analyse/sites_de_patch_dans_nouvel_exe.txt`). Le site d'en-tête (VA `0x400310`, bourrage nul) est toujours à zéro. | 🟡 (nouveau code d'exe, jamais essayé en jeu) | Nouveaux fichiers JSON pour le build `0x6ae228f3` (nouvelle empreinte d'origine `461E1262…`), nouveaux tests sur copie, accord du moddeur pour chaque pose. **INFÉRÉ** : il faut aussi vérifier que les opérandes redirigés figurent bien dans la table de relocation du nouvel exe. |
| **b) SDK `dinput8.dll` « CC2X 0.5.0 »** | **Inactif** sur le nouvel exe (voir ci-dessous). Il charge la vraie `dinput8.dll` et laisse passer. | Pour le réactiver : un **nouveau profil** dans le SDK (≥ 7 adresses à redécouvrir) = modifier le code d'un tiers et le relire à nouveau. Aucune urgence. | 🟢 tel quel / 🔴 si on le « force » | Rien tant qu'on ne décide pas d'un portage. **Ne jamais** modifier le SDK pour qu'il accepte l'ancien profil sur le nouvel exe. |
| **b) Plugins `cc2x_frein.dll`, `cc2x_modes.dll`** | **Non chargés** (le chargeur est dans le SDK, qui s'arrête avant). Même s'ils l'étaient : seconde barrière dans le plugin lui-même. | Réécrire les décalages d'objets et re-tester. | 🟢 / 🔴 si forcés | À refaire seulement après un portage du SDK. |
| **c) Mods** `cc2_mesures`, `cc2_carte`, `cc2_modes`, `2937532682` (missiles) | **Aucun fichier d'origine qu'ils remplacent n'a changé** (MESURÉ : `rom_0\scripts\library_custom_*.lua` et `rom_0\game_objects\missile_*.xml` ont la même date et le même contenu qu'avant). Les scripts `cc2_carte` / `cc2_modes` testent `type(cc2x)=="table"` avant d'agir (LU) : **sans SDK actif ils ne font rien**. | Rien à faire. | 🟢 | Rien. Les autres mods du Workshop (Revolution, Seal 2x Water…) ne sont pas dans `mods.xml` actuel : même conclusion si on les réactive (les originaux n'ont pas bougé). |
| **d) Sauvegardes et parties** | Aucun fichier de `saved_games` n'a été touché (non lu par Steam). Même version affichée **v1.5.18**, mêmes données de jeu (`rom_0` identique) : **INFÉRÉ** que les sauvegardes se chargent comme avant. | Test en jeu nécessaire (non fait). | 🟡 | Le **plantage connu au chargement** (équipements de Revolution, `etudes_demarrage_auto/ETUDE.md`) vient de **données**, pas de l'exe : il n'est **ni corrigé ni aggravé** par cette mise à jour (INFÉRÉ). Mais ses adresses de plantage (`0x5EF518`, `0x5EF525`, décalage `0x1EF518`) valent pour **l'ancien** exe ; sur le nouveau elles seront décalées (jusqu'à ~0x1a0 octets) : à adapter avant de comparer des rapports de plantage. |
| **d) Multijoueur** | **Inconnu.** L'exe porte la même chaîne `v1.5.18` ; si le jeu compare cette chaîne, un joueur sur l'ancien exe et un sur le nouveau **pourraient** se connecter, mais je n'ai pas pu savoir si le protocole réseau a changé dans le code. | Tester à deux (non fait). | 🟡 | Jouer à plusieurs avec **le même exe que les autres** (les invités reçoivent la vitesse du serveur : `temps_x2` ne doit jamais servir en partie hébergée, comme déjà noté). Chacun reçoit la mise à jour Steam automatiquement. |
| **e) Outils d'essai** | `essai_auto.py` **refuse** de lancer si l'exe n'est pas `8E7FCBB6…` (garde-fou, déjà périmé : l'exe courant avant mise à jour était `0C5DFE52…`, il fallait `--exe-quelconque`). `poser.py` signale « AUTRE VERSION : le SDK resterait inactif ». `test_demarrage_auto.py` a l'horodatage `0x6a36c177` et les décalages de plantage écrits en dur. | Mettre à jour les constantes quand un nouveau build sera adopté. | 🟢 | Voir le tableau suivant. |
| **f) Le Mac** | Je n'y ai pas accès. **INFÉRÉ** : le build `26277078` concerne toute l'application ; Steam sur le Mac recevra aussi un nouveau binaire (un dépôt différent) dès qu'il se mettra à jour. | Voir §6. | 🟡 | Voir §6. |

### Détail b) — pourquoi le SDK ne peut pas écrire au mauvais endroit (point de sécurité n° 1)

- **LU** `cc2x.c:824-833` (`detect`) : le SDK ne démarre que si l'**horodatage PE** et la **taille d'image** de l'exe sont ceux de son **seul profil** « 1.5.18-win32 » (`0x6a36c177`, `0x00af7000`). Sinon il écrit « unsupported game build … CC2X stays inactive » dans `cc2x.log` ; `cc2x.c:837-838` : `P = detect(); if (!P) return;` — aucun crochet n'est posé, `load_plugins()` (ligne 892) n'est jamais atteint.
- **MESURÉ** : l'horodatage du nouvel exe est `0x6ae228f3` ≠ `0x6a36c177` → le profil ne correspond plus. (La taille d'image reste `0x00af7000` : **la taille seule ne protégerait pas**, c'est l'horodatage qui protège.)
- **Seconde barrière** (LU `cc2x.c`, relue dans `VERDICT_relecture_SDK.md`) : chaque écriture vérifie d'abord la valeur d'origine. **MESURÉ** sur le nouvel exe aux adresses fixes du SDK (`analyse/adresses_sdk_dans_nouvel_exe.txt`) : les 3 cases de la table du serveur (`0x00d34bc4/8/c`) contiennent maintenant du **texte** (`_tim…`) au lieu des 3 pointeurs attendus (`0x772fd0`, `0x77ee10`, `0x77eea0`) ; les 6 débuts de fonctions Lua ne correspondent plus ; `server_tick` est maintenant à `0x77ef00` (+0xf0) et `server_end` à `0x77ef90`. Seul le site Lua `0x004465ec` a encore les mêmes octets (zone non décalée).
- **Troisième barrière dans `cc2x_modes.dll`** (LU `cc2x_modes.c:303-306`) : refuse si `game_build` n'est pas « 1.5.18-win32 » **et** si les 8 octets de `0x71dbbf` ne sont pas `movss [edi+0x314], xmm0` ; **MESURÉ** : sur le nouvel exe l'instruction est à `0x71dbc2` (+3), donc refus. `cc2x_frein.c:314` : même contrôle de `game_build`.
- **Reste un risque indirect** : `dinput8.dll` s'exécute quand même au lancement (il charge la vraie bibliothèque, supprime et recrée `cc2x.log`) ; rien d'écrit dans le jeu hors ce journal. Les exe de test `carrier_command_test_cercle*.exe` ont **l'ancien** horodatage : lancés, le SDK s'y activerait normalement (comme avant).

### Mods : ce qu'ils remplacent (c)

MESURÉ (`apres/jeu_fichiers.tsv`) : les 10 `rom_0\scripts\library_custom_0…9.lua` sont des fichiers **vides** (0 octet, sha256 du vide), avant comme après : un mod qui y met un script ne peut donc pas « annuler une correction » de la mise à jour. (`library_custom_5.lua` porte une date du 27/10 11:24 : trace d'un de nos essais précédents, contenu bien vide.) Les 4 XML de missiles et `vehicle_attachment_hardpoint_missile_tv.xml` ont le même contenu qu'avant.

| Mod actif (`mods.xml`) | Fichiers qui remplacent un original | Original changé par la mise à jour ? |
|---|---|---|
| `2937532682` (missiles, Workshop) | `game_objects\missile_2.xml`, `missile_4.xml`, `missile_cruise.xml`, `missile_tv.xml` | Non |
| `cc2_mesures` | `scripts\library_custom_1.lua`, `_4`, `_7`, `_9` | Non |
| `cc2_carte` | `scripts\library_custom_6.lua` | Non |
| `cc2_modes` | `scripts\library_custom_3.lua`, `_5` ; DLL `content\cc2x\cc2x_modes.dll` | Non (scripts) ; DLL non chargée (SDK inactif) |

### Études en cours (e)

| Étude | Dépend de | Après la mise à jour |
|---|---|---|
| Circuit d'atterrissage (`etudes_circuit_atterrissage`) | modules `atterrissage_cercle` / `_creneau`, exe de test `carrier_command_test_cercle*.exe` | Les **exe de test existent toujours**, intacts (MESURÉ : même date et même sha256) : les essais restent faisables **sur l'ancien build**. Pour le jeu normal : **à porter** (§3 a). |
| Roulage retour (`etudes_roulage_retour`) | modules `pont_retour_x2`, `helicos_approche_x2` | Idem : **à porter**. |
| Frein à la main (`atterrissage_manuel`) | SDK + `cc2x_frein.dll` | **Inactif** sur le nouvel exe ; valable seulement sur l'ancien build. |
| Modes carburant (`etudes_modes_carburant`) | SDK + `cc2x_modes.dll` + scripts | **Inactif** sur le nouvel exe ; scripts inertes. |
| Missiles (`etudes_missiles`) | mod XML du Workshop | **Inchangé** (XML identiques) : **reste valable**, 🟢. |
| Démarrage automatique (`etudes_demarrage_auto`) | scripts Lua + désassemblage de l'ancien exe | Le Lua reste valable ; les **adresses** du désassemblage sont celles de l'ancien exe (copie d'origine gardée dans `tour/sauvegardes/`, donc relisible). |
| Scénario PvP (`scenario_pvp`) | scénario/scripts (non relus en détail) | **INFÉRÉ** inchangé (données de `rom_0` identiques). |
| Idées / usine d'argent | — | Pas de dépendance à l'exe relevée. |

## 4. Conduite à tenir (dans l'ordre)

1. **Ne rien lancer** tant que le moddeur n'a pas choisi la voie (§5). Ne pas cliquer « Vérifier l'intégrité » ni réinstaller dans Steam sans y penser : cela ré-écrase tout fichier de la liste de Steam. Nos fichiers ajoutés (`dinput8.dll`, `cc2x_frein.dll`, exe de test) ne sont **pas** dans la liste de Steam : ils ne seront pas effacés.
2. Si on lance quand même le jeu tel quel : il est **vanille** (aucun patch, SDK inactif) ; les études qui mesurent quelque chose avec nos DLL/patchs ne produiront rien d'utile. Contrôle à faire après : `cc2x.log` doit contenir « unsupported game build … CC2X stays inactive ».
3. Garder une **copie du nouvel exe** (11 Mo) dans `tour/sauvegardes/` (pas encore fait : demande d'accord, §7).
4. Choisir entre **A** garder l'ancien exe patché à côté, **B** porter les patchs sur le nouvel exe (§5).
5. **Mac** : voir §6, avant de comparer les résultats Mac/tour.
6. Ne pas hâter la remise à jour des outils (`essai_auto.py`, `poser.py`, tests) : attendre la voie choisie.

## 5. Revenir à l'état d'avant (procédure, rien n'a été exécuté)

**Voie A (recommandée, la plus sûre) : l'ancien exe patché comme fichier séparé**, comme on fait déjà pour `carrier_command_test_cercle.exe`. L'exe de Steam n'est pas touché.

1. Jeu fermé. Sur une copie dans le dossier d'étude (rien dans le jeu à ce stade) :
   ```
   copy tour\sauvegardes\carrier_command_1.5.18_original.exe tour\etude_mise_a_jour\ancien_patche.exe
   python -I tour\outils\patch_exe.py activer --exe tour\etude_mise_a_jour\ancien_patche.exe --sauvegarde tour\sauvegardes\carrier_command_1.5.18_original.exe --module ascenseur_x2
   (idem avec --module temps_x2, puis --module pont_retour_x2)
   ```
   Sha256 attendu à la fin : `0C5DFE52DFDF1AE002B0CF8B25C6B32CC1EEC953A80E856D37E4016CF2FE120B` (je l'ai obtenu ainsi, sur une copie du bloc-notes, MESURÉ).
2. **Avec l'accord du moddeur** (écriture dans le dossier du jeu, 🟢 : ajout d'un fichier nouveau que Steam ne connaît pas) : copier ce fichier à côté sous le nom `carrier_command_ancien_patche.exe`, le lancer directement (pas par Steam), `dinput8.dll` s'y active comme avant (horodatage `0x6a36c177`).
3. Limites : données de jeu identiques (`rom_0` inchangé, MESURÉ) donc **INFÉRÉ** compatible ; **multijoueur avec des joueurs au nouvel exe : non testé**.

**Voie B : remplacer `carrier_command.exe` de Steam** par l'original puis re-patcher (`--cest-le-vrai-jeu`). 🟡 : Steam peut le re-écraser à la prochaine vérification ou mise à jour ; **sauvegarder d'abord le nouvel exe** (`461E1262…`).

**Voie C : ramener tout le jeu à l'ancien build via Steam** (manifeste de l'ancien dépôt `3120081341062660422`, LU dans l'ancien manifeste). La commande de la console Steam `download_depot 1489630 1489631 3120081341062660422` existe d'après mes connaissances (**INFÉRÉ, non testée**) ; c'est une action dans Steam (🟡 : télécharge ~1,3 Go dans `steamapps\content`, ne remplace pas le jeu installé) : **à ne faire que sur accord explicite du moddeur**. Inutile tant que la voie A suffit.

**Copies disponibles** : `tour/sauvegardes/carrier_command_1.5.18_original.exe` (`1C9A01C3…`) ; `carrier_command_1.5.18_patche_8E7FCBB6.exe` (ascenseur_x2 + temps_x2) ; l'exe `0C5DFE52…` (reconstruit sur demande, pas encore écrit dans `sauvegardes/` : **vérifié d'abord, absent**, ne sera écrit que si le moddeur accepte) ; le nouvel exe `461E1262…` (copie de travail seulement dans le bloc-notes de la session).

## 6. Le Mac

- **INFÉRÉ** : un numéro de build s'applique à toute l'application sur Steam ; le Mac aura un nouveau binaire macOS (l'ancien fil d'actualités montre que la version Mac peut être mise à jour séparément, ex. « V1.5.17 HOTFIX » corrigeait un build Mac). **Rien de ce qui est dit ici ne dépend de l'adresse d'un fichier du Mac** : ses études en octets de Mach-O sont indépendantes des adresses Windows.
- **À relire/faire côté Mac (sans changer quoi que ce soit)** : (1) lire `appmanifest_1489630.acf` : `buildid` installé (si encore `23836745`, les études restent comparables ; si `26277078`, le binaire a changé) ; (2) calculer le sha256 du binaire Mac et le comparer à celui des études ; (3) chercher dans le binaire la chaîne `support_sign_in` (signe de la recompilation vue ici) ; (4) relire `tour/etude_mise_a_jour/ETUDE.md` §2 et §3a ; (5) ne pas régler ses études « pour égaler la tour » avant de savoir si l'écart vient de la mise à jour.
- Pour que les études restent **comparables**, la solution simple est de comparer **tour sur ancien exe** (voie A) et **Mac sur son build actuel** tant que ni l'un ni l'autre ne passent au nouveau.

## 7. Limites de cette étude (honnêtement)

- Le « avant » des 787 `.ogg` est douteux (lecture simultanée à la mise à jour) ; la conclusion « inchangés » repose sur la taille identique et le journal Steam (« reuse 94 619 123 », seulement 1,55 Mo téléchargés) : **INFÉRÉ**.
- Je n'ai pas désassemblé le nouvel exe : je ne peux pas affirmer qu'aucun comportement du jeu n'a changé dans le code (§2). Seuls la recompilation, la nouvelle adresse d'assistance et le nouveau chemin de compilation sont **MESURÉS**.
- Le portage des patchs (§3 a) est **vérifié sur les octets des 40 sites**, pas sur le comportement en jeu (rien n'a été lancé).
- Pas d'accès au Mac, pas d'essai multijoueur, pas d'essai de chargement de sauvegarde.
- Les pages web ont été traitées comme des données ; aucune instruction n'y a été suivie.

## 8. Fichiers de cette étude

- `avant/` et `apres/` : listes `jeu_fichiers.tsv` (chemin, taille, date, sha256 de 6 316 fichiers), manifestes, `mods.xml` ; `avant/NOTE_instantane.md` explique la fiabilité du « avant ».
- `analyse/` : `comparaison_avant_apres.txt`, `diff_pe_ancien_nouveau.txt`, `horodatages_et_versions.txt`, `textes_differents.txt`, `adresses_sdk_dans_nouvel_exe.txt`, `sites_de_patch_dans_nouvel_exe.txt`, `steam_news_api_2026-10-28.json`.
- `outils/` : scripts utilisés (lecture seule sur les exe ; `snapshot.ps1` écrit un fichier texte).

## 9. Addendum du 29/10/2026 : « c'est trop bien tombé » (le timing) et ce que disent les autres moddeurs

**Source des témoignages** : le moddeur a collé une discussion publique de moddeurs (dont l'auteur du SDK `dinput8.dll`). Ce sont des propos non vérifiés (**RAPPORTÉ**), traités comme des données. Rien n'a été téléchargé ni lu en ligne à ce sujet.

### 9.1 Ce que cette discussion confirme de façon indépendante
- Même jour, mêmes fichiers : « 4 exe + ~788 sons » chez eux ; chez nous **MESURÉ** : 4 exe + 787 `.ogg` (§2). Concorde.
- « Une mise à jour d'environ 1 Mo » : notre journal Steam dit **4 morceaux téléchargés** seulement (**MESURÉ**, `content_log.txt`). Concorde.
- Le « coupe-circuit » de la DLL de DYOR s'est déclenché parce que l'empreinte (sha256) du jeu a changé : c'est exactement ce que j'avais **INFÉRÉ** pour notre SDK (profil `1.5.18-win32` non reconnu → inactif, §3 b). Un tiers l'a constaté en vrai.
- DYOR dit avoir mis en ligne une version corrigée de son SDK, et Sample_Fox dit avoir de « nouvelles adresses ». **Non vérifié, rien lu ni téléchargé.** Toute nouvelle `dinput8.dll` devra passer par la même relecture que la précédente (`tour/atterrissage_manuel/VERDICT_relecture_SDK.md`) avant la moindre pose.
- Dans la discussion, Sample_Fox retire lui-même une accusation (« ils ont mis une défense sur mes adresses ») : c'était en fait les garde-fous de l'outil de DYOR. Ce n'est donc **pas** un indice d'une mesure volontaire des développeurs.

### 9.2 Faits sur le timing (MESURÉ)
- Dernière version publiée avant : **v1.5.18, le 26/06/2026** (actualité Steam), donc il y a **4 mois**, pas 6. (Le vrai long silence est antérieur : 05/01 → 26/06/2026.)
- Le nouvel exe a été compilé le **28/10/2026 à 16:55 UTC**, avec les 3 autres exe en 2 minutes (16:53–16:55). Notre Steam l'a vu à 19:48 et l'a appliqué à 21:30 (heure locale). Donc une reconstruction **faite ce jour-là**, d'un seul coup, puis publiée dans la foulée. Ce n'est pas un build resté en attente depuis des semaines.
- Par ailleurs, la discussion dit que le SDK de DYOR (« le hook ») était sorti « il y a quelques jours » (**RAPPORTÉ**). La coïncidence est réelle : je ne peux ni l'écarter ni la prouver.

### 9.3 Ce que l'analyse de l'exe permet de dire, et ne permet pas de dire
- **Pour une cause banale** : l'ancienne adresse de support du jeu est **morte** aujourd'hui (`geometa.co.uk/support/carriercommand/sign_in` répond **404**, test du 29/10, `analyse/adresses_support_test_2026-10-29.txt`) et la nouvelle (`/support_sign_in`) répond (redirection vers `/feedback_sign_in`). Le compte de compilation a aussi changé : `gitlabrunner` → `geometacouk_v2_service`. Il faut recompiler pour que le lien d'assistance du jeu marche à nouveau : c'est une raison fonctionnelle de publier un exe. (On ne sait pas depuis quand l'ancienne adresse est morte.)
- **Rien de nouveau côté protection** (**MESURÉ**, `analyse/imports_ancien_nouveau.txt`) : la table des imports Windows est **identique** (9 DLL, 322 fonctions). Aucune fonction de hachage, de signature, de protection mémoire ou de détection de débogueur n'a été ajoutée ; aucun texte « intégrité / checksum / tamper » ; `dinput8` n'apparaît qu'une fois, dans les deux exe (le jeu l'utilise lui-même pour la manette/souris).
- **Les sons** : 787 fichiers, **taille identique pour chacun**, seule la date change (`analyse/ogg_tailles_avant_apres.txt`) ; Steam n'a téléchargé que 4 morceaux. Le contenu audio n'a donc probablement pas changé (**INFÉRÉ**) ; pourquoi Steam les réécrit tous, je ne le sais pas.
- **Ce que je ne peux pas exclure** : le code est décalé de façon **non uniforme** (de +0 à +0x190 octets, par pas de 16, 132 changements de décalage le long du code : `analyse/decalages_du_code.txt`). Ça veut dire de **nombreuses petites différences de code**. Je n'ai pas lu ce que c'est (pas de désassemblage). Des modifications de comportement, ou un contrôle d'intégrité écrit sans nouvelle fonction Windows (par exemple un calcul interne), restent possibles. Des adresses fixes cassent à la moindre modification : leur casse n'est donc **pas** une preuve d'intention.
- **Correction de ma formulation du 29/10** : j'avais écrit que « rien dans l'exe ne vise les joueurs qui modifient le jeu ». C'est trop fort. La vérité mesurée : **aucun indice de protection anti-modification au niveau des textes et des fonctions Windows importées ; le code lui-même n'a pas été analysé**.
- **Précision sur les décalages de nos patchs** : le « +0x110 » (et +0x130 pour `temps_x2`) n'est valable que **dans la zone de nos 40 sites** (adresses 0x60xxxx–0x73xxxx, où le décalage varie de 0xf0 à 0x130 selon l'endroit). Chaque site a été retrouvé par son contexte, pas par une constante globale. Un futur module de patch doit retrouver ses emplacements **par le contexte**.

### 9.4 Conclusion honnête
Intention des développeurs : **non déterminable** avec ces mesures. Raison banale plausible (migration du site d'assistance + nouveau serveur de compilation, **INFÉRÉ**), coïncidence de dates réelle (**MESURÉ** / **RAPPORTÉ**). La conduite à tenir (§4) ne dépend pas de la réponse : exe patché séparé à côté du jeu (§5 Voie A), SDK inactif tant que son profil ne correspond pas, patchs à retrouver par le contexte.

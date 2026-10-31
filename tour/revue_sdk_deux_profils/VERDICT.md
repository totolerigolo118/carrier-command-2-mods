# Verdict de la relecture indépendante du SDK CC2X à deux profils (31/10/2026) — lecture seule

**Ce qui a été relu** : la copie du SDK 0.5.0 (commit `7ab05c7`) à laquelle la conversation « port-nouvel-exe » a ajouté un 2e profil pour le nouvel exe de Steam (`461E1262…`, horodatage PE `0x6ae228f3`), et la DLL compilée à partir de cette copie :
`C:\Users\UTILISATEUR\Documents\cc2-port-travail\sdk\dist\dinput8.dll`, 268 288 octets, sha256 **`E1DE25D53A5588BDA62269D6D93335ACB9F32EA555AC9274FE7973C19D6225D7`**.

Relecteur : une autre conversation que l'auteur du portage. Ordre suivi : sources d'abord, puis **mes propres** adresses retrouvées dans le nouvel exe **avant** d'ouvrir les valeurs du porteur (`analyse/profil_sdk_valeurs.txt`), puis la DLL.
**Rien n'a été posé, lancé, compilé ni modifié** : ni dans le dossier du jeu, ni dans `%APPDATA%\Carrier Command 2`, ni dans la worktree `port-nouvel-exe-27119f`, ni dans le clone du SDK. Rien de téléchargé ni d'installé (capstone 5.0.7 était déjà là). Tous les outils sont faits maison, dans `outils/`, lancés en `python -I -B` ; leurs sorties complètes sont dans `sorties/`.

## Verdict : **POSE ACCEPTABLE** pour la DLL `E1DE25D5…` — risque de la pose 🟡 (le même niveau que le SDK déjà accepté le 27/10), avec 3 conditions avant de poser

**Aucun écart trouvé** : pas une valeur fausse, pas une ligne de logique ajoutée, pas un import ni une chaîne nouvelle (hors le nom du 2e build).
Pour la sécurité de ton ordinateur, cette DLL fait **exactement les mêmes choses** que celle déjà posée (`184B144D…`, relue le 27/10) : mêmes fonctions de Windows, mêmes fichiers, aucun réseau. La seule différence est qu'elle **reconnaît aussi le nouvel exe**.

**À bien comprendre** : aujourd'hui, sur le nouvel exe, le SDK posé est **inactif** (« unsupported game build ») : il ne charge aucun plugin et ne donne pas la table Lua `cc2x` aux mods. Avec la nouvelle DLL, il redevient **actif**, comme il l'était sur l'ancien exe. **Poser le SDK revient donc aussi à réactiver 3 plugins** (condition 1 ci-dessous), que cette relecture ne couvre pas.

## 1. Les sources, fichier par fichier, contre le clone d'origine (MESURÉ)

| Contrôle | Résultat | Preuve |
|---|---|---|
| Clone `cc2-sdk-tiers\Carrier-Command-2-extender` propre ? | **Oui** : `git status --porcelain --ignored` vide, `git log -1` = `7ab05c79357e0cdb5bfaa2866bd3a81a101a09da` (fusion « sdk-0.5 », 25/10 23:19), `git fsck` sans erreur, fins de ligne LF | commande `git` en lecture |
| Clone conforme aux empreintes épinglées ? | **25/25** sha256 identiques à `tour/atterrissage_manuel/SDK_empreintes_7ab05c7.txt` | `sorties/1_comparer_sources.txt` |
| `sources_ref` (copie « inchangée ») | 6 fichiers **identiques octet pour octet** au clone | idem |
| `sources_nouveau` : fichiers identiques | `include/cc2x.h`, `src/dinput8.def`, `src/internal.h`, `src/lua_world.c` : **identiques octet pour octet** | idem |
| `sources_nouveau` : fichiers modifiés | **2** : `src/cc2x.c` (+610 octets) et `src/world.c` (+2 155 octets) | idem |
| Nature des modifications | **Deux insertions pures, aucune ligne retirée ni modifiée** : (a) `cc2x.c` lignes 33-40 : un 2e élément du tableau `PROFILES` (le nom `"1.5.18-win32-6ae228f3"`, 3 lignes de commentaire, 16 nombres et 8 octets) ; (b) `world.c` lignes 71-96 : un 2e élément du tableau `LAYOUTS` (le même nom, 17 adresses du jeu, et 65 décalages de champs **recopiés à l'identique** du 1er élément, avec les mêmes octets attendus aux sites) | diff complet dans `sorties/1_comparer_sources.txt` ; ses **34 lignes ajoutées** sont identiques à celles du diff fourni `profil_nouvel_exe.diff`, **0 ligne retirée** dans les deux (contrôle par programme) |
| Logique, réseau, fichiers, processus, chaîne nouvelle ? | **Rien de tout cela.** La seule chaîne ajoutée est le nom du build (deux fois). Aucun caractère hors ASCII, aucun retour chariot caché. Le code qui lit ces tableaux (`detect()` `cc2x.c:832-842`, `world_init()` `world.c:678-682`) est **inchangé** : il parcourt le tableau avec `sizeof`, il accepte donc le 2e élément sans modification | lecture de `cc2x.c` et `world.c` |

Choix du profil (LU) : `detect()` compare l'horodatage PE **et** la taille d'image de l'exe ; le Layout est ensuite choisi par le nom (`strcmp`). Le nouvel exe (`0x6ae228f3`, `0x00af7000`) ne peut tomber que sur le 2e profil ; l'ancien (`0x6a36c177`) que sur le 1er, qui est **resté tel quel**.

## 2. Les valeurs, retrouvées par moi dans le nouvel exe (MESURÉ)

Méthode (`outils/trouver_profil.py`) : pour chaque adresse de l'ancien profil, je désassemble (capstone) 48 à 96 octets de l'ancien exe d'origine (`1C9A01C3…`) à cette adresse ; je masque **seulement** les octets qui portent une adresse de l'image ou un saut ; je cherche ce motif dans **tout** le code du nouvel exe. Une **seule** correspondance est exigée. Les constantes (décalages de champs, tailles) restent dans le motif : elles sont vérifiées au passage. Pour les données (table du serveur, `nilobject`, vtable PhysX), je pars du code de l'ancien exe qui y fait référence et je lis la valeur au même endroit dans le code correspondant du nouvel exe.

**Résultat : 29 valeurs sur 29 trouvées, chacune avec une seule correspondance, et 0 écart avec le diff** (comparaison faite par programme, `outils/comparer_au_diff.py`, pas à l'œil).

| Valeur demandée | Ancien | Trouvé par moi | Dans le diff | Comment |
|---|---|---|---|---|
| `server_vtable` | `0x00d34bc4` | **`0x00d34bfc`** | `0x00d34bfc` ✔ | 2 méthodes : (1) la seule instruction de l'ancien code qui écrit cette table (`0x835bc2`) se retrouve en `0x835cf2` et y écrit `0x00d34bfc` ; (2) le triplet (init, tick, fin) retrouvé (`0x7730c0`, `0x77ef00`, `0x77ef90`) n'apparaît **qu'une fois** dans tout le fichier, à `0x00d34bfc`. Les 3 cases sont dans la table de relocations (comme dans l'ancien) |
| `server_tick` | `0x0077ee10` | **`0x0077ef00`** | `0x0077ef00` ✔ | fenêtre de 49 octets, unique (décalage +0xf0, comme init et fin) |
| `f_luaC_step` | `0x00904050` | **`0x009041c0`** | `0x009041c0` ✔ | fenêtre de 49 octets, unique (+0x170) ; les 8 octets attendus par le SDK (`LUA_SIGS`) y sont |
| `nilobject` | `0x00d03518` | **`0x00d03530`** | `0x00d03530` ✔ | 178 instructions de l'ancien code y font référence ; j'en ai suivi 40 : **toutes** donnent `0x00d03530` dans le nouveau. Contenu : 16 octets à zéro dans les deux (une valeur Lua « nil ») |
| `LAYOUTS.f_vehicle_by_id` | `0x005ee6a0` | **`0x005ee7e0`** | ✔ | unique, +0x140 |
| `LAYOUTS.f_request_landing` | `0x0062b4a0` | **`0x0062b5b0`** | ✔ | unique, +0x110 |
| `LAYOUTS.h_hangar` (+ `found`, `none`) | `0x0062ae8d` | **`0x0062af9d`** (`0x0062b00c`, `0x0062afbd`) | ✔ | les deux cibles de saut sont retrouvées **deux fois** : par leur propre fenêtre et comme cibles des sauts du site `h_hangar` |
| `LAYOUTS.vt_rigid_dynamic` | `0x00cdd478` | **`0x00cdd478`** (inchangée) | ✔ | les 2 références de l'ancien code donnent la même valeur ; les 8 premières cases de cette vtable pointent sur les fonctions correspondantes, décalées de +0x190 à +0x1b0 (une case commune inchangée) |
| … et les 21 autres | | | **tous ✔** | liste complète dans `sorties/3_comparer_au_diff.txt` |

Contrôles en plus (MESURÉ) :
- Les octets que le SDK vérifie lui-même au démarrage sont bons dans le nouvel exe : les 6 signatures Lua (`LUA_SIGS`) et les 8 octets du site Lua (`6a20898564ffffff` à `0x004465ec`).
- **Les 65 décalages de champs** du 2e Layout sont identiques à ceux du 1er (MESURÉ dans la source). Dans le code entier des deux exe, le nombre d'accès `[registre + décalage]` est **le même à l'unité** pour les 36 décalages testés (véhicule, serveur, île, aérodrome ; par exemple `0x174` état d'accostage : 467 / 467) : une structure qui aurait changé ferait bouger ces nombres (`sorties/6_decalages_champs.txt`).
- **Sur la copie patchée que tu lanceras** (`5AF41B4D…`, ascenseur + temps + pont) : même horodatage et même taille d'image ; les 128 octets autour de chacune des 29 adresses sont **identiques** à l'exe de Steam (29/29) ; les 34 petites zones patchées (82 octets) sont toutes à **plus de 125 857 octets** de toute adresse du SDK.
- Après mon propre travail, j'ai ouvert les valeurs du porteur (`profil_sdk_valeurs.txt`) et son contrôle `verification_profils_dans_la_dll.txt` (LU, son outil n'a pas été relancé) : ils disent la même chose, par une autre méthode (longues suites d'instructions identiques, 178/178 références de `nilobject`).

## 3. La DLL compilée `E1DE25D5…`, lue en-tête par en-tête (MESURÉ, lecteur PE fait maison)

| Point | DLL posée `184B144D…` | Nouvelle `E1DE25D5…` | Conclusion |
|---|---|---|---|
| Type | PE32 i386, DLL, ASLR + NX | idem | ✔ |
| Sections (noms et droits) | `.text` R-X, `.rdata` R, `.buildid` R, `.data` RW, `.tls` RW, `.reloc` R, `.debug_frame` R | **identiques** ; aucune section à la fois écrivable et exécutable | ✔ |
| Tailles | — | `.text` +656 o, `.rdata` +464 o, `.reloc` +112 o | expliqué plus bas |
| Exports | les 5 fonctions de `dinput8` (`DirectInput8Create`, `DllCanUnloadNow`, `DllGetClassObject`, `DllRegisterServer`, `DllUnregisterServer`) | **identiques** | ✔ |
| Imports | `KERNEL32` (39 fonctions) + la bibliothèque C `api-ms-win-crt-*` (29) | **identiques, dans le même ordre** ; aucun `ws2_32`, `wininet`, `winhttp`, `advapi32`, `shell32` | ✔ |
| Imports retardés, ressources, signature | absents | absents | ✔ |
| TLS | 2 rappels (ceux de la bibliothèque C) | 2 rappels, **même code**, adresses décalées de +0x290 comme tout le code | ✔ |
| Point d'entrée | `0xb2d0` | `0xb560` : **même fonction**, décalée de +0x290 | ✔ |
| Débogage | `dinput8.pdb` (nom seul, aucun chemin de ton disque) | idem | ✔ |
| Chaînes dans les sections de données | — | **une seule nouvelle : `1.5.18-win32-6ae228f3`** ; aucune chaîne UTF-16 nouvelle ; aucune disparue (les 2 autres « différences » sont les octets aléatoires de l'identifiant de build) | ✔ (`sorties/7_chaines_sections_donnees.txt`) |
| Tables dans la DLL | `PROFILES` : 1 élément ; `LAYOUTS` : 1 | `PROFILES` : **2** (17 champs chacun) ; `LAYOUTS` : **2** (90 champs chacun) ; **chaque champ égal à la source**, et l'ancien profil égal à celui de la DLL posée | ✔ (`sorties/4_analyser_dll.txt`) |

**Pourquoi le code a changé de 656 octets alors que la source n'a reçu que des données** (MESURÉ puis expliqué) : avec **un seul** profil, le compilateur avait remplacé les lectures de la table par des constantes écrites directement dans le code (exemple : `[eax + 0x37c]`). Avec **deux** profils, il doit lire la table (exemple : `mov ecx, [W]` puis `[ecx + 0x6c]`, la case `s_vehicles` du Layout, qui vaut `0x37c`). J'ai vérifié **fonction par fonction** grâce aux bornes de la section `.debug_frame` (`outils/comparer_fonctions_dll.py`) :
- **648 fonctions dans chaque DLL ; 618 identiques ; 30 changées**, toutes parmi celles qui lisent le profil ou le Layout (démarrage, monde du jeu).
- Ces 30 fonctions appellent **exactement les mêmes imports et les mêmes fonctions internes**, et lisent **les mêmes chaînes** qu'avant, à une exception près, attendue : le nom `"1.5.18-win32"` n'est plus écrit en dur à 4 endroits (il est lu dans la table), et `world_init` compare maintenant aux deux noms de build.
- Nombre total d'appels à chaque fonction de Windows : **identique** entre les deux DLL.

**La chaîne de compilation** (MESURÉ sur les fichiers du porteur) : `dist_ref` (sources inchangées, compilées le 30/10) diffère de la DLL posée par **20 octets seulement** : l'horodatage PE, les 2 horodatages du répertoire de débogage et 8 octets de l'identifiant de build. `dist` et `dist_verif` (deux compilations des sources modifiées) diffèrent exactement aux **mêmes 20 octets**, et nulle part ailleurs. Donc même compilateur, mêmes options, résultat stable.

## 4. Les 3 conditions avant la pose

1. **Décider des 3 plugins que la pose réactive.** Une fois le SDK actif sur le nouvel exe, son chargeur exécutera (LU dans `mods.xml` et dans les dossiers, rien modifié) :
   - `cc2x_frein.dll` **dans le dossier du jeu**, sha `941DFFB9F1671CB3…`, **modifiée aujourd'hui 31/10 à 11:15** : c'est la v12, qui **connaît** le nouveau build (chaîne `1.5.18-win32-6ae228f3` présente) ; elle se chargera donc (« brake off unless brake_enabled=1 », réglage dans `%APPDATA%\Carrier Command 2\cc2x\frein.ini`, modifié aussi à 11:15). **Attention** : la note du porteur du 30/10 disait que le frein refuserait ; ce n'est plus vrai avec la v12. Ses sites sur le nouvel exe : **INCONNU** pour moi (le porteur a vérifié v10 et v11, pas la v12).
   - `cc2x_modes.dll` (mod `cc2_modes`), sha `4B2EBC04…` : connaît le nouvel exe, observation seule sans `enabled=1` (LU, note du porteur).
   - `cc2x_hold.dll` (mod `cc2_hold_copies`), sha `EE9043DA…`, modifiée aujourd'hui à 11:36 : sa source a une entrée « nouvel exe Steam 461E1262 (jamais essayé) » et donne les octets attendus au SDK (si les octets ne sont pas ceux prévus, le SDK refuse le crochet). J'ai vérifié ses 6 adresses du nouvel exe avec mon outil : **6/6 conformes** (MESURÉ) ; que la DLL posée soit bien compilée depuis cette source : **INCONNU** (hors de cette relecture).
   → Pour un premier essai « SDK seul », la voie la plus prudente est que ces plugins soient retirés ou désactivés **par la conversation qui les a faits**, sur ta décision. Sinon, accepter en connaissance de cause qu'ils se chargent ensemble.
2. **Refaire le contrôle des dossiers lus par le chargeur juste avant la pose** (condition 2 du verdict du 27/10) : pas d'autre `cc2x_*.dll` dans le jeu, pas de dossier `cc2x\plugins`, pas de `cc2x.ini`, pas de nouveau mod actif avec un dossier `cc2x`. Aujourd'hui : rien d'autre que les 3 plugins ci-dessus (MESURÉ pendant cette relecture, le 31/10 ; à refaire puisque deux de ces fichiers ont changé ce matin).
3. **Vérifier l'empreinte au moment de la pose** : la DLL copiée dans le jeu doit avoir le sha256 `E1DE25D53A5588BDA62269D6D93335ACB9F32EA555AC9274FE7973C19D6225D7` ; un accord séparé pour la pose (fichier dans `Program Files`) et un autre pour le lancement ; sauvegarde jetable ; jeu fermé pendant la copie.

## 5. Ce qui reste INFÉRÉ (jamais vu en jeu) ou INCONNU

- **INFÉRÉ** : que le SDK démarre vraiment sur le nouvel exe. Signe attendu dans `cc2x.log` : `CC2X 0.5.0 ready for Carrier Command 2 1.5.18-win32-6ae228f3` (sans « no Lua bridge »). S'il trouve un octet ou un pointeur inattendu, il **reste inactif tout seul** (contrôles de `cc2x.c:183-200`, `270-286` et `863-867` dans la copie modifiée ; signatures Lua `849-852`, LU) : cas sans danger.
- **INFÉRÉ** : les valeurs que le SDK **ne contrôle pas** au démarrage sont justes : `nilobject`, les 6 fonctions du jeu de `world.c` appelées par l'API (`f_vehicle_by_id`…), les cibles `h_hangar_found` / `h_hangar_none`, les 65 décalages de champs. Elles sont MESURÉES par deux méthodes (la mienne et celle du porteur) mais jamais exécutées. Une erreur ferait **planter le jeu** (pas de fuite de données) ; `vt_rigid_dynamic` sert seulement de garde-fou avant de déplacer un corps.
- **INFÉRÉ** : la charge du fil SIM (condition 3 du 27/10, toujours valable) : la 0.5.0 copie tous les véhicules à chaque tick dès qu'elle est active. À surveiller sur l'affichage SIM.
- **INFÉRÉ** : que `E1DE25D5…` soit compilée depuis `sources_nouveau` : tout concorde (tables champ par champ, chaînes, 618 fonctions identiques, 30 expliquées), mais **je n'ai pas recompilé moi-même** (lecture seule demandée). Une recompilation indépendante dans un dossier temporaire serait le dernier verrou possible (🟢 : compilateur déjà installé, rien hors du dossier temporaire) ; elle n'est pas nécessaire pour ce verdict.
- **INCONNU** : le comportement des 3 plugins sur le nouvel exe (condition 1).
- Les noms de build : un plugin ou un script qui exige exactement `"1.5.18-win32"` refusera le nouvel exe. Recherche de `game_build` dans les 5 mods actifs : **aucun** script ne le lit (MESURÉ).

## 6. Retour arrière

Jeu **fermé**, recopier l'ancienne DLL `184B144D6E2BB868FFEB7D45ECD463F8919E64732E3B5681A16165363EBA0982` par-dessus `C:\Program Files (x86)\Steam\steamapps\common\Carrier Command 2\dinput8.dll`. Copies conformes déjà sur ton disque (MESURÉ) : `C:\Users\UTILISATEUR\Documents\cc2-sdk-travail\dist\dinput8.dll` (et 6 autres dans `dist_v6` à `dist_v11`). Vérifier le sha256 après la copie. Le SDK redevient alors inactif sur le nouvel exe (comme aujourd'hui). Pour tout couper : supprimer `dinput8.dll` du dossier du jeu. Les exe patchés ne sont pas concernés.

## Fichiers de cette relecture

- `outils/comparer_sources.py` → `sorties/1_comparer_sources.txt` (sources contre clone et empreintes)
- `outils/trouver_profil.py` → `sorties/2_trouver_profil.txt` (mes 29 valeurs, méthode capstone)
- `outils/comparer_au_diff.py` → `sorties/3_comparer_au_diff.txt` (mes valeurs contre la source ; copie patchée `5AF41B4D…`)
- `outils/analyser_dll.py` → `sorties/4_analyser_dll.txt` (en-têtes, imports, exports, TLS, chaînes, tables, 4 DLL)
- `outils/comparer_fonctions_dll.py` → `sorties/5_fonctions_posee_contre_nouvelle.txt` (fonction par fonction)
- `outils/compter_decalages.py` → `sorties/6_decalages_champs.txt` (décalages de champs, relocations)
- `sorties/7_chaines_sections_donnees.txt` (chaînes des seules sections de données)

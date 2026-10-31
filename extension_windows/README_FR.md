# Extension Windows pour Carrier Command 2 : le squelette

Ce dossier contient **tout ce qu'on peut écrire sans connaître le jeu Windows** : le « moteur » de l'extension qui portera, plus tard, nos patchs du Mac sur la tour. **Aucune adresse du jeu Windows n'y figure** : elles seront trouvées sur la tour, étape par étape (voir la feuille `passation_windows/PASSATION_windows.md`, section 5). Rien de ce dossier n'a encore tourné dans le vrai jeu.

## En deux mots

- Une **extension** (on dit aussi *plugin*) est un petit programme, ici un fichier `cc2x_cc2_patchs.dll`. Une **DLL** est un morceau de programme que Windows charge au démarrage du jeu. Le **SDK CC2X** (une boîte à outils publique d'un autre moddeur, dans `passation_windows/sdk_public_cc2x/`) la charge pour nous.
- Cette extension ne modifie **jamais le fichier du jeu** : elle change quelques octets **en mémoire** quand le jeu démarre. Supprimer la DLL et relancer le jeu = jeu d'origine.
- Chaque famille de patchs est un **groupe** avec un interrupteur **éteint par défaut** dans un petit fichier de réglages. Tant qu'on n'allume rien, l'extension ne touche à rien.

## Ce qu'il y a dans le dossier

| Fichier | À quoi il sert |
|---|---|
| `src/cc2_patchs.c` | Le point d'entrée : ce que l'extension fait quand le SDK la charge. |
| `src/cp_pe.c` | Le **portier** : lit la « carte d'identité » du jeu et refuse de s'activer si ce n'est pas la bonne version. |
| `src/cp_patch.c` | La **couche d'écriture sûre** : vérifie, écrit, relit, et défait tout si un seul endroit pose problème. |
| `src/cp_tunables.c` | Notre **table de nombres à nous** (les valeurs doublées du Mac, modifiables). |
| `src/cp_hook.c` | Le **crochet sûr** : un petit « tremplin » qui permet d'appeler du code C au milieu d'une fonction du jeu sans casser ses calculs. |
| `src/cp_groups.c` | La **table des 8 groupes**, avec les listes d'endroits **vides** et des notes sur ce qu'il faudra trouver. |
| `src/cp_ini.c`, `src/cp_config.c` | Lecture du fichier de réglages. |
| `src/cp_speed.c`, `lua/cc2_vitesse_shim.lua` | Le côté Lua des modes de vitesse ECO / NORMAL / FLANK. |
| `src/cp_win.c` | **Seul** fichier qui parle à Windows (écrire en mémoire, lire un fichier). |
| `cc2_patchs.ini.example` | Le fichier de réglages à copier (tout y est éteint). |
| `build.py`, `BUILD.txt` | Comment fabriquer la DLL, et ce qui a été utilisé ici. |
| `tests/` | Les tests faits sur Linux, avec `tests/run_tests.sh`. |
| `RAPPORT_cloud.md` | Le compte rendu de cette session : ce qui marche, ce qui n'est pas vérifié, le travail de la tour. |

## Ce que fait l'extension quand le jeu la charge

1. **Le portier.** Elle lit dans le jeu trois informations : le nom de version donné par le SDK (`1.5.18-win32`), la **date de fabrication** du programme et sa **taille en mémoire** (ce sont les deux nombres de la « carte d'identité » du fichier, appelés *horodatage PE* et *SizeOfImage*). Si l'un des trois est différent de ce qu'on attend (`0x6a36c177` et `0x00af7000`), elle écrit la raison dans le journal du SDK (`cc2x.log`), **ne touche à rien** et s'arrête proprement. C'est ce qui nous protège d'une mise à jour Steam : le jeu tourne alors d'origine.
2. **Les réglages.** Elle lit `cc2_patchs.ini` (dans le dossier de réglages que le SDK lui indique, normalement `%APPDATA%\Carrier Command 2\cc2x\`). Pas de fichier = tout éteint.
3. **Les groupes.** Pour chaque groupe, elle écrit **une ligne** dans `cc2x.log` : *appliqué*, *sauté* (éteint) ou *refusé*, avec la raison. Un groupe allumé dont la liste d'endroits est encore vide est *refusé* avec la mention « pas encore porté ».
4. **Le Lua.** Si le groupe de vitesse est vraiment appliqué (ou si on le demande pour un essai), elle ajoute la fonction `cc2x.speed.mode(equipe [, mode])` côté Lua.

## Les protections de la couche d'écriture

Pour **chaque endroit** à modifier (on dit un *site* : une adresse, une longueur, les octets d'origine, le type de retouche) :

- les **octets d'origine sont vérifiés** avant d'écrire : si le jeu contient autre chose, c'est **refusé** ;
- après l'écriture, elle **relit** pour vérifier que ça y est ;
- les adresses sont **recalculées** si Windows a déplacé le jeu en mémoire (le mécanisme *ASLR*) : les tableaux contiennent les adresses « du fichier » (base `0x00400000`, celles que Ghidra montre) ;
- deux endroits qui **se chevauchent** sont refusés, même entre deux groupes différents.

Pour **chaque groupe** : c'est **tout ou rien**. Si un seul endroit pose problème, **rien n'est écrit** ; si une écriture échoue en cours de route, ce qui a déjà été écrit est **remis comme avant**. Appliquer deux fois le même groupe ne fait **rien** la deuxième fois.

Les quatre types de retouche (colonne « type » de la table des groupes) :

| Type | Ce que ça fait |
|---|---|
| `abs_float` | Une instruction lit un nombre à virgule (une **constante flottante**) à une adresse fixe : on change cette adresse pour qu'elle pointe vers **notre** nombre. La constante du jeu n'est **jamais modifiée** (elle sert à d'autres endroits). Avant, on vérifie que cette constante contient bien sa valeur d'origine. |
| `imm` | Des octets remplacés tels quels (une valeur écrite dans l'instruction, un code d'opération…). Pour l'énergie de l'ascenseur, la valeur 0,8 vient de la table de nombres. |
| `jump` | Un saut du jeu est redirigé vers un autre endroit (circuit d'atterrissage). |
| `hook` | Un **crochet** : l'endroit est remplacé par un saut vers un tremplin qui appelle notre code C. |

## Notre table de nombres

Les valeurs sont celles du Mac (les valeurs « doublées » : plateforme 0,05 au lieu de 0,025, plafond de roulage 5 au lieu de 2,5, etc.). Elle est **alignée sur 16 octets** : certaines lectures du jeu prennent **quatre nombres d'un coup** et plantent si l'adresse n'est pas alignée. Chaque valeur peut être changée dans `cc2_patchs.ini` (section `[tunables]`) ; le fichier d'exemple donne toutes les clés avec leur valeur par défaut et la valeur du jeu.

## Le crochet sûr (et ses limites)

Sur le Mac, nos greffes en C cassaient des calculs : le C appelé au milieu d'une fonction écrasait des **registres de calcul à virgule** (`xmm0` à `xmm7`) dont le jeu avait encore besoin. Le crochet du SDK ne les sauvegarde pas. **Le nôtre sauvegarde et restaure `xmm0`–`xmm7`, les drapeaux du processeur et tous les registres généraux** autour de l'appel C, et laisse le code C **lire et modifier** ces valeurs. Contraintes à connaître (écrites aussi dans `src/cp_hook.h`) :

- il faut au moins **5 octets** à l'endroit du crochet, découpés en **instructions entières** ;
- ces instructions sont **recopiées ailleurs** : elles ne doivent pas contenir de **saut relatif** (un saut « de tant d'octets vers l'avant »), sauf si c'est la **première** (elle est alors recalée automatiquement). Le programme **ne peut pas détecter** un saut relatif caché plus loin : c'est à la personne qui remplit le tableau de vérifier ;
- aucune autre partie du jeu ne doit sauter **au milieu** des octets remplacés ;
- les calculs de l'ancien processeur (« x87 ») ne sont pas sauvegardés : ne pas accrocher au milieu de tels calculs.

**Ce qui a été vérifié :** le tremplin a été **exécuté pour de vrai dans un programme 32 bits sous Linux** (voir le rapport). **Ce qui ne l'a pas été :** son fonctionnement **dans le jeu Windows**. Personne ne l'a vu tourner là-bas.

## Comment la tour remplira un groupe

1. Trouver dans `carrier_command.exe` les endroits (empreintes de la section 6 de la feuille, notes sur chaque groupe dans `src/cp_groups.c`).
2. Pour chaque endroit, écrire une entrée dans le tableau du groupe : adresse du **fichier** (base `0x400000`), longueur, **octets d'origine tels qu'ils sont dans le fichier** (adresses absolues comprises, pas relevées en mémoire), type, et la valeur de la table de nombres concernée. Des raccourcis existent (`CP_ABS_FLOAT`, `CP_JUMP`, `CP_HOOK`, voir `src/cp_patch.h`).
3. Mettre `n_sites` à jour, **compiler, tester sur Linux** (`tests/run_tests.sh` vérifie déjà que les tables sont bien formées et sans chevauchement), puis **demander au moddeur de lancer le jeu** et lire `cc2x.log`.
4. Allumer **un seul groupe à la fois** dans l'ini (règle de la feuille : une modification testée à la fois).

## Fabriquer et tester

Voir `BUILD.txt` pour le détail. En bref, depuis ce dossier :

```
python build.py            # fabrique dist/cc2x_cc2_patchs.dll (a besoin de Zig 0.15.2, par exemple pip install ziglang==0.15.2)
tests/run_tests.sh         # tous les tests faits sur Linux
```

**Retour arrière :** supprimer `cc2x_cc2_patchs.dll` du dossier du jeu et **relancer le jeu**. (Le SDK ne sait pas décharger une extension pendant une partie.)

## Petit lexique

- **Octet** : une case de mémoire (deux chiffres comme `8d` ou `0f`). Un programme est une suite d'octets.
- **Adresse** : le numéro d'une case de mémoire. **Adresse du fichier** : celle qu'on voit dans Ghidra (base `0x400000`) ; **adresse réelle** : celle en mémoire une fois le jeu lancé, qui peut être décalée.
- **Constante flottante** : un nombre à virgule écrit une fois dans le jeu et lu par le code.
- **Registre** : une toute petite mémoire du processeur. `xmm0`–`xmm7` servent aux calculs à virgule.
- **Crochet** (*hook*) : détourner l'exécution à un endroit précis pour appeler notre code puis rendre la main.
- **Hôte** : la machine où tournent les tests (ici Linux) ; **fausse mémoire** : un tableau d'octets qui joue le rôle de la mémoire du jeu dans les tests.
- **SPDX** : l'étiquette de licence en tête de chaque fichier (GPL-3.0 ou plus, comme le SDK).
- **tour** : le PC Windows du moddeur.

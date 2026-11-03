> **02/11/2026 : CHOIX DE moddeur, à respecter par toute session** : il **garde** `auto_recall=1` et `heli_recall=1` dans `frein.ini` (« j'aime pouvoir les poser à la main et que ça reprenne la main derrière »). **Ne pas retirer ces lignes après un essai et ne pas remettre `frein.ini.avant_v13` / `frein.ini.avant_v14`** ; les commentaires « à retirer après l'essai » de `frein.ini` sont périmés. Dans le jeu : la v15.

> **Statut (31/10/2026) : prête, PAS encore utilisée.** La v13 est **posée** (31/10, accord du moddeur) ; `heli_recall=1` pas encore ajouté à `frein.ini`. Notice des risques : `frein/RISQUES_v13.md`. Pourquoi : `ETUDE_v13_helicos.md`. Pour les avions, rien ne change : `PROCEDURE_partie_v12.md` reste valable.

# Essai v13 : un hélico posé à la main rentre seul au hangar (2 minutes de lecture)

**Ce qu'on essaie** : tu poses un **Razorbill** (ou un Petrel) sur le pont à la main, tu le quittes, tu donnes l'ordre de retour, et **le jeu le prend tout de suite en charge** (ascenseur, hangar) au lieu de le faire redécoller pour son tour d'attente.

**Avant de jouer** (rien à faire de ta part, sauf dire « oui ») :
1. ~~Je pose la v13~~ : **fait** (31/10). Elle fait exactement comme la v12 tant que le réglage hélico est éteint.
2. J'ajoute **une ligne** `heli_recall=1` dans `frein.ini` (ton « oui », même message possible). Le reste reste comme aujourd'hui (`recall_force=1`, `max_speed=35`). Je garde une copie.
3. Je lance une copie passive du journal (elle ne fait que lire).
4. Le jeu se lance avec la **copie du nouvel exe** (`carrier_command_nouveau_5AF41B4D.exe`, celle qui a marché à 13:52, **sans** l'approche ×2 des hélicos : une seule nouveauté à la fois). Elle contient le **temps ×2 : la simulation tourne à ×1,33 comme d'habitude** (ta règle pour tous les essais ; jamais l'exe de Steam tel quel, qui tourne à ×1). Tu me dis « oui, lance » et je le lance.

**Dans le jeu :**
1. **Partie neuve** (jamais une sauvegarde). Steam ouvert.
2. **Ralentis le navire** au minimum (ou arrête-le).
3. Sors un **Razorbill**, décolle, fais un petit tour.
4. Pose-le **sur la piste, sur la ligne du milieu**, plutôt **vers l'arrière ou au milieu** du pont (pas tout à l'avant, pas sur l'ascenseur, pas près de la tour). Doucement, sur ses trois roues, et attends qu'il soit **immobile**.
5. **Quitte l'hélico.** Regarde-le 5 secondes : **reste-t-il posé** ou décolle-t-il tout seul ? Dis-le-moi (c'est une des choses qu'on ne sait pas).
6. S'il est resté posé : donne l'**ordre de retour** (comme d'habitude, sur la carte), puis **ne touche plus à rien** et regarde-le pendant 1 minute.

**Ce que tu peux voir :**
- ✅ **Succès** : l'hélico est **tiré doucement** vers l'ascenseur, descend et rentre au hangar. Dis-le-moi, attends encore 20 s (je vérifie le carburant).
- ⚪ **Il redécolle et fait son tour comme d'habitude** : la v13 n'a pas pu le prendre (le journal dira pourquoi). **Sans danger** : c'est le retour normal du jeu.
- ⚪ **Il fait un petit saut et se repose plus loin sur le pont**, puis rentre : le jeu lui a donné la piste mais a voulu le reposer lui-même. C'est aussi un succès (un peu moins rapide).
- ⚠️ **Si je te dis « remonte »** : remonte tout de suite dans l'hélico.
- ⚠️ **Il est tiré contre quelque chose** (tour, bord) ou bascule : remonte dedans. La partie est jetable.

Tu peux recommencer avec un **Petrel**, puis avec un **avion** (pour vérifier que les avions marchent toujours pareil).

**À la fin** : dis « **fini** ». Je ferme le jeu moi-même, je copie le journal (et je **laisse** `heli_recall=1` : ton choix du 02/11) et je te dis en français ce qui s'est passé.

---

## Pour moi (ou la coordination) : le moddeur n'a pas à lire ceci

### Avant (chaque point = un « oui » du moddeur dans CETTE conversation)
0. **Coordination** : la session « Passer au nouvel exe » (`[session]`) a un essai « approche ×2 des hélicos » prêt avec ses propres outils, épinglés sur la v12 : **après la pose de la v13, ses lanceurs refuseront** (frein pas à la version qu'ils attendent). Décider l'ordre avec elle (le plus simple : son essai d'abord, puis la v13 ; ou elle reprend les outils de cette worktree). Un seul jeu à la fois, jeu fermé pour poser.
1. **Pose de la v13.** Jeu fermé (`Get-Process carrier_command*` vide). Depuis `tour/essai_nouvel_exe/outils/` de CETTE worktree : `python -I -B poser.py maj --jeu "<jeu>" --cest-le-vrai-jeu --a-blanc`, puis sans `--a-blanc`. Vérifier : `cc2x_frein.dll` = `22D04FE3F28D087403534732217779EE315A36EF33A547CD9F47253D03349113` (247 808 o) ; `dinput8.dll` = `E1DE25D5…` ; `carrier_command.exe` = `461E1262…` ; copies `8E7FCBB6`, `5AF41B4D` inchangées ; `frein.ini` non touché. Retour : copier `C:\Users\UTILISATEUR\Documents\cc2-sdk-travail\dist_v12\cc2x_frein.dll` (`941DFFB9…`) sur la DLL du jeu.
2. **`frein.ini`** : copie `frein.ini.avant_v13` (= `D7828C32…`, relue), puis **une** ligne `heli_recall=1` à la fin (avec un commentaire « à retirer après l'essai »).
3. Copieur passif du journal → `C:\Users\UTILISATEUR\Documents\cc2-sdk-travail\logs_parties\cc2x_<date>_frein_v13.log`.
4. Lancement : `python -I -B lancer_nouveau.py lancer --jeu "<jeu>" --cest-le-vrai-jeu` (même dossier) ; il vérifie les empreintes (SDK à deux profils + v13) et lit le journal de démarrage.

### Au démarrage, `cc2x.log` doit montrer
- `CC2X 0.5.0 ready for Carrier Command 2 1.5.18-win32-6ae228f3`
- `loaded (frein v13, build 1.5.18-win32-6ae228f3, exe 0x6ae228f3)`
- la ligne des 9 crochets de la v12 (H1 `0x7019de` … H5 `0x6fe580` … `0x6ff489`), **plus** `heli_recall=1: hook H6 (0x6fdded, gives the runway to the flagged helicopter: continues at 0x6fde02) installed too`
- `settings: … recall_force=1 … hooks=1 heli_recall=1 heli_hook=1`

`could NOT be installed` ou `not loaded` = **arrêt**.

### Lignes attendues
| Ligne | Sens |
|---|---|
| `heli N t=…: flight=… dock=0 … mode=0 … wheels=3/3 … rel=… deck x=… z=… standing=1 window=0` | posé, pilote parti ; **noter si `wheels` / `rel` changent** (décolle-t-il seul ?) ; `deck z` : −68 arrière, +7 milieu, +82 avant |
| `HELI window open (recalled helicopter standing on the deck: …)` | rappel vu, H6 armé (un seul don) |
| `HOOK H6 skipped the helicopters' 100 m test: the game gives the runway itself (queue place 0, free bays N)` | le jeu donne la piste |
| `PROBE take-over block entered: the touch test PASSED, the game got bay N (limit M)` | toucher passé, prise en charge |
| `HELI balance (take-over): H6 visits 1, GRANTS 1, ABORTS 0, TAKE-OVER block 1` puis `HELI VERDICT: … ran its take-over block (bay N)` | idem |
| **`TAKEN OVER: dock 6, flight 1, runway state 5`**, `FOLLOW …`, **`HANGAR: dock 4 (stowed)`**, **`REFUEL check: … it goes up`** | **le but** |

### Échecs possibles (lus dans `HELI VERDICT:`)
- `SILENT - the game never looked at this helicopter …` : piste occupée ou autre hélico devant dans la file ; l'hélico fait son retour normal.
- `H6 saw the helicopter N time(s) but did not act: …` : la raison est écrite (pas de baie libre de classe 1, mode, piste…).
- `runway given, then the game ABORTED the landing (H3 line)` : lire la ligne `HOOK H3 … fail=… counter=…` (si `deck z` > 82 : trop en avant ; si près du milieu et `deck x` > 30 : trop sur le côté).
- `runway given, no take-over in the window` : le toucher n'est pas passé tout de suite ; l'hélico a la piste et se repose seul (regarder s'il rentre quand même : la prise en charge n'est alors plus suivie par le plugin).

### Alertes « REMONTE »
Avant la prise en charge : l'hélico **glisse** (`rel` > 1,5 m/s qui monte, `wheels` qui tombe) près d'un bord ; après `TAKEN OVER` : il est tiré **vers** la tour ou un bord au lieu de l'ascenseur (regarder l'écran), ou `FOLLOW` montre `attached=0` puis `aircraft is gone`. Dire « remonte » au premier cas.

### Après (« fini »)
Fermer le jeu (accord permanent du moddeur après « fini »), vérifier la copie du journal, **ne pas** toucher à `frein.ini` (choix du moddeur du 02/11), écrire le résultat dans `JOURNAL_atterrissage.md`.

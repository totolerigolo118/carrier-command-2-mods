> **02/11/2026 : CHOIX DE moddeur, à respecter par toute session** : il **garde** `auto_recall=1` et `heli_recall=1` dans `frein.ini` (« j'aime pouvoir les poser à la main et que ça reprenne la main derrière »). **Ne pas retirer ces lignes après un essai et ne pas remettre `frein.ini.avant_v13` / `frein.ini.avant_v14`** ; les commentaires « à retirer après l'essai » de `frein.ini` sont périmés. Dans le jeu : la v15.

> **Statut (31/10/2026) : prête, PAS encore utilisée.** La v14 est écrite et testée hors jeu, **pas posée** (dans le jeu : la v13). Risques : `frein/RISQUES_v14.md`. Conception : `CONCEPTION_retour_auto.md`.

# Essai v14 : l'avion rentre seul au hangar quand tu le quittes (2 minutes de lecture)

**Ce qu'on essaie** : tu poses l'avion à la main, le frein l'arrête, **tu le quittes, et c'est tout**. Cinq secondes après, il part seul vers l'ascenseur et le hangar, **sans que tu donnes l'ordre de retour sur la carte**.

**Avant de jouer** (rien à faire de ta part, sauf dire « oui ») :
0. Je vérifie avec la session « nouvel exe » qu'aucune autre partie n'est prévue (ta partie multijoueur passe d'abord si elle est prête) : un seul jeu à la fois.
1. Je pose la v14 dans le dossier du jeu, jeu fermé (ton « oui »). Sans le nouveau réglage, elle fait exactement comme aujourd'hui.
2. J'ajoute **une ligne** `auto_recall=1` dans `frein.ini` (ton « oui », même message possible). Le reste reste comme aujourd'hui (`recall_force=1`, `max_speed=35`). Je garde une copie.
3. Je lance une copie passive du journal (elle ne fait que lire).
4. Le jeu se lance avec la copie du nouvel exe (`carrier_command_nouveau_5AF41B4D.exe`, par `lancer_nouveau.py`). Elle contient le **temps ×2 : la simulation tourne à ×1,33 comme d'habitude** (ta règle pour tous les essais ; jamais l'exe de Steam tel quel, qui tourne à ×1). Tu me dis « oui, lance » et je le lance.

**Dans le jeu :**
1. **Partie neuve** (jamais une sauvegarde). Steam ouvert.
2. **Ralentis le navire** au minimum.
3. Sors un avion (Albatross ou Manta), décolle, fais un tour, et pose-toi **dans l'axe**, à **30 m/s relatifs au plus**, comme d'habitude.
4. Laisse le **frein** l'arrêter, ne touche plus aux gaz, puis **quitte l'avion**, **ou** reste assis et appuie sur **R** (« auto »).
5. **Ne donne PAS l'ordre de retour.** Attends et regarde : **au bout de 5 secondes**, il doit partir seul (tiré doucement vers l'ascenseur, puis le hangar).
6. Si tu veux le garder (pour redécoller), **remonte dedans (ou réappuie sur R) avant 5 secondes** : c'est annulé. En vol, R fait comme d'habitude (l'IA reprend sa route) : rien de changé.

**Ce que tu peux voir :**
- ✅ **Succès** : 5 s après que tu l'as quitté, il recule vers l'ascenseur et rentre au hangar. Dis-le-moi, attends encore 20 s (je vérifie le carburant).
- ⚪ **Rien ne se passe au bout de 10 s** : le plugin n'a pas pu demander le retour, ou le jeu l'a refusé (le journal dira pourquoi). **Sans danger** : l'avion reste tenu au frein ; donne l'ordre de retour sur la carte comme avant.
- ⚠️ **Si je te dis « remonte »** : remonte tout de suite dans l'avion.
- ⚠️ **Le jeu se ferme tout seul** : dis-le-moi ; la partie était jetable, on revient à la v13.

**À la fin** : dis « **fini** ». Je ferme le jeu, je copie le journal et je te raconte (je **laisse** `auto_recall=1` : ton choix du 02/11).

---

## Pour moi (ou la coordination) : le moddeur n'a pas à lire ceci

### Avant (chaque point = un « oui » du moddeur dans CETTE conversation)
0. **Coordination** avec la session « Passer au nouvel exe » (`[session]`) : elle prépare une copie multijoueur ; un seul jeu à la fois, **rien posé pendant qu'un jeu tourne**. Ses outils sont épinglés sur la v13 : après la pose de la v14, elle doit ajouter `50D0464A…` (ou reprendre les outils de cette worktree), et ses lanceurs refusent `auto_recall=1` si elle les règle comme pour `heli_recall`.
1. **Pose de la v14** : jeu fermé ; depuis `tour/essai_nouvel_exe/outils/` de CETTE worktree : `python -I -B poser.py maj --jeu "<jeu>" --cest-le-vrai-jeu --a-blanc`, puis sans `--a-blanc`. Vérifier : `cc2x_frein.dll` = `50D0464A052792BAA611D4EDE3990F7387046CB9A4EFD69D3DC2427F9A0C9404` (250 880 o), `dinput8.dll` = `E1DE25D5…`, exe et copies inchangés, `frein.ini` non touché. Retour : copier `C:\Users\UTILISATEUR\Documents\cc2-sdk-travail-v13\dist\cc2x_frein.dll` (v13).
2. **`frein.ini`** : copie `frein.ini.avant_v14` (= `D7828C32…`, relue), puis une ligne `auto_recall=1` (commentaire « à retirer après l'essai »). Ne pas mettre `heli_recall=1` en même temps (une nouveauté à la fois).
3. Copieur passif → `C:\Users\UTILISATEUR\Documents\cc2-sdk-travail\logs_parties\cc2x_<date>_frein_v14.log`.
4. `python -I -B lancer_nouveau.py lancer --jeu "<jeu>" --cest-le-vrai-jeu`.

### Au démarrage, `cc2x.log` doit montrer
- `loaded (frein v14, build 1.5.18-win32-6ae228f3, exe 0x6ae228f3)` et la ligne des 9 crochets (comme la v12)
- `settings: … recall_force=1 … hooks=1 heli_recall=0 heli_hook=0 auto_recall=1 auto_recall_s=5`

### Lignes attendues
| Ligne | Sens |
|---|---|
| `BRAKE start`, `HOLD`, `STOPPED`, `IDLE` | comme d'habitude |
| `AUTO RECALL armed (held and stopped, pilot gone): the carrier is asked in 5 s …` | The modder a quitté l'avion |
| **`AUTO RECALL: held and stopped, pilot gone 5 s: asked the carrier's own dock request (as for the map's recall order) -> dock 5 (queued: the usual recall follows)`** | **la nouveauté a marché** |
| `RECALL start (dock 5 …)`, `FORCE start`, `HOOK H2`, `VERDICT: the touch test PASSED …`, `TAKEN OVER`, `HANGAR`, `REFUEL` | la suite de la v12 |

### Échecs possibles
- `AUTO RECALL not asked: the carrier's table … is not the one read for this build` : garde-fou, rien appelé ; l'ordre de la carte marche comme avant.
- `-> dock 0 (the game did not queue it; not asked again)` : le jeu a refusé ; l'ordre de la carte marche comme avant.
- `AUTO RECALL cancelled (…)` : la raison est écrite (pilote revenu, rappel déjà donné, un autre appareil en cours…).
- Plantage juste après la ligne `AUTO RECALL:` : l'appel direct pose problème ; revenir à la v13 et rester sur l'ordre de la carte.

### Après (« fini »)
Fermer le jeu, vérifier la copie du journal, **ne pas** toucher à `frein.ini` (choix du moddeur du 02/11), écrire le résultat dans `JOURNAL_atterrissage.md`.

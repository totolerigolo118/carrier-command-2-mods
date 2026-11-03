# Atterrissage à la main des hélicoptères (Razorbill, Petrel) — étude A1 et plugin v13 (31/10/2026)

**Lecture seule du jeu.** Rien n'a été posé, lancé ni changé dans le dossier du jeu ou un mod. Exe lus : l'ancien `carrier_command_1.5.18_original.exe` (`1C9A01C3…`, `tour/sauvegardes/` du dossier principal) et l'exe de Steam `461E1262…` (dossier du jeu, lecture seule) ; copies patchées relues aux mêmes endroits : `8E7FCBB6`, `5AF41B4D`, `2C9F8E47` (approche ×2 des hélicos). Outils : capstone + petits scripts du dossier temporaire de la session ; contrôles gardés dans le dépôt : `outils/verifier_sites_v13.py` → `frein/VERIF_sites_v13.txt`.

Étiquettes : **LU** (lu dans l'exe ou un fichier) · **INFÉRÉ** (déduit, pas vu en jeu) · **INCONNU**.
Adresses de l'ancien exe ; dans le nouvel exe, toute la grande fonction de la piste est la même, instruction par instruction, décalée de **+0x110** (4775 instructions comparées, 0 différence).

## 1. En bref

1. **H1/H2 ne servent à rien pour un hélico** (LU). La boucle de la file d'atterrissage envoie chaque hélico vers **son point d'attente** et passe à l'élément suivant **sans jamais arriver au code du circuit des avions** où sont H1 et H2 (`0x7016dd` → `0x70186c jmp 0x701c38`).
2. **Le jeu donne la piste aux hélicos ailleurs** (LU, `0x6fdba7`-`0x6fdd90`) : porte-avions en mode « accostage », piste libre, **premier hélico de la file**, et **seulement s'il est à moins de 100 m de son premier point d'attente** (x −100, z −240 dans le repère du navire : environ **260 m derrière**, à droite, à 80 m de haut).
3. **Un hélico posé sur le pont n'y est jamais** (au moins ~190 m de ce point) : rappelé, **le jeu seul le fait redécoller**, aller au point d'attente, puis revenir se poser (l'atterrissage normal de l'IA, ~1 min mesurée sur le Mac). Ce n'est pas dangereux, mais ce n'est pas ce que veut le moddeur.
4. **Une fois la piste donnée, tout le reste existe déjà pour lui** (LU) : dans le même tick, l'état 3 prend la branche hélico (`0x6fe198`), pas d'engagement, pas de cône, puis le **test de toucher** `0x6ff20a` et le **bloc de prise en charge** `0x6ff368` — exactement le chemin que la v12 fait prendre aux avions (3 prises en charge sur 3 + le Manta).
5. **Il faut donc un seul crochet de plus, H6** (v13) : pour l'hélico signalé, il saute le test des 100 m (`0x6fdcdd` → `0x6fdcf2`). Pas besoin de H5 (les hélicos n'y passent pas), ni du frein (le jeu met lui-même le frein des hélicos à 0,6 juste avant le toucher). **INFÉRÉ fort** que le toucher passe pour un hélico posé et immobile (c'est ce que passe chaque hélico de l'IA, et ce qu'ont passé nos avions tenus au frein).

## 2. Ce qui se passe quand on rappelle un hélico posé et arrêté (LU, pas à pas)

| Étape | Adresse (ancien exe) | Ce que fait le jeu |
|---|---|---|
| Rappel (carte) | `0x707330` = fonction virtuelle `+0x7c` du porte-avions | met l'hélico dans la file `{id, 0, 0}`, `DOCK_STATE = 5`, `DOCK_VEHICLE` = le navire |
| Don de la piste (hélicos) | `0x6fdba7` | si mode 1 et piste libre : parcourt la file, saute les avions, prend le **1er hélico** |
| Test des 100 m | `0x6fdc38`-`0x6fdcec` | position de l'hélico dans le repère du navire ; `(−100 − x)² + (−240 − z)² < 10000` ? sinon on s'arrête là |
| Don | `0x6fdcf2`-`0x6fdd90` | propriétaire de la piste = l'hélico, état de piste 3, compteur 0, train sorti, `DOCK_STATE = 1`, retiré de la file |
| Boucle de la file | `0x7016ce`-`0x70186c` | chaque hélico encore en file : vers le point d'attente n° k (x −100, hauteur 80, z −240 − 60·k), mode de pilotage 3 — **il redécolle** |
| État 3, même tick | `0x6fdde5` → `0x6fe187` | `call [vtable+0x4c]` vrai = hélico → branche `0x6fe198` |
| Branche hélico | `0x6fe198`-`0x6fe431` | vise un point **50 m devant lui** (100 m avec le réglage « approche ×2 ») et une hauteur pont + (distance au milieu)/2 ; **si la distance au milieu de la piste est < 20 m** : train, `DOCK_STATE = 1`, et **échec si l'écart latéral dépasse 30 m** |
| Tronc commun | `0x6feec7`-`0x6ff0eb` | puissance 0 si une roue touche ; **échec si l'hélico est au-delà du nœud B** (z > +82, l'avant du pont) ; le cône est sauté pour un hélico (`0x6fef79`) ; échec si compteur > 3600 ; il faut une baie libre de classe 1 |
| Toucher | `0x6ff20a`-`0x6ff362` | vitesse relative au navire ≤ 10 m/s ; frein fixe 0,6 / adhérence 1,0 (hélico) ; chaque roue : contact ≥ 0,01 et 2e champ ≤ 0,1 |
| Prise en charge | `0x6ff368`… | baie, joint, `DOCK_STATE = 6`, `FLIGHT_STATE = 1`, état de piste 5, recul vers l'ascenseur (comme les avions de la v12) |
| Abandon (si échec) | `0x6ff0f1` | frein 0, puissance 1, train rentré, `DOCK_STATE = 5`, remis en file : **l'hélico repart faire son approche normale** |

Les seuils demandés : **écart latéral 30 m** (constante `0xdb798c`, ne compte que si l'hélico est à moins de 20 m du milieu de la piste, ou plus en avant) ; **distance 20 m** (`0x6fe3ef`, distance signée au milieu de la piste, z ≈ +7 : en dessous de z ≈ −13 l'hélico « n'est pas encore proche » mais va quand même au toucher s'il est posé).

## 3. Ce que fait la v13 (écrite et testée hors jeu ; **posée le 31/10**, `heli_recall` pas encore activé)

- **Désactivée par défaut** : sans `heli_recall=1` dans `frein.ini` **au démarrage du jeu**, H6 n'est pas posé et aucun hélico n'est même regardé : la v13 fait **exactement la v12** (mêmes 9 crochets, mêmes octets).
- `heli_recall=1` **et** `recall_force=1` au démarrage : 10 crochets en une seule transaction ; **H6** en `0x6fdcdd` (nouvel exe `0x6fdded`), 8 octets `f3 0f 59 d2 f3 0f 59 db` (`mulss xmm2,xmm2 ; mulss xmm3,xmm3`), cible `0x6fdcf2` (nouvel exe `0x6fde02`).
- Un hélico humain est **signalé** quand il est **rappelé** (`DOCK_STATE = 5`) alors qu'il **tient sur le pont** : toutes ses roues au contact, < 1 m/s par rapport au navire, pilote parti, pas accroché. Pas d'attente d'une seconde (il n'est pas tenu par un frein). **Une fenêtre de 10 s par rappel, un seul don de piste par fenêtre** (compté dans le crochet), un seul appareil à la fois (avion ou hélico).
- H6 ne fait que **sauter la comparaison** : rien n'est écrit dans la mémoire du jeu, aucun registre changé ; il refuse si le cadre n'est pas le bon, si le navire n'est pas en mode accostage, si la piste n'est pas libre, ou s'il n'y a **aucune baie libre de classe 1**.
- **Aucun frein, aucun moteur écrit pour un hélico.** H3, la sonde de prise en charge et le SUIVI jusqu'au hangar (v12) servent aussi aux hélicos.
- Journal : `heli N t=…: … deck x=… z=… standing=…` (position sur le pont, approximative), `HELI window open`, `HOOK H6 …`, `HOOK H3 …` (abandon), `PROBE take-over …`, `HELI balance …`, `HELI VERDICT: …`, puis `TAKEN OVER`, `HANGAR`, `REFUEL` comme pour les avions.

Preuves (hors jeu) : `frein/VERIF_sites_v13.txt` (10 sites sûrs dans les deux exe, entre le site de H6 et sa cible seulement 4 calculs SSE de registres et le saut conditionnel, xmm2/xmm3 pas vivants à la cible, `[ebp-0x270]` = l'hélico écrit par le jeu avant, 14 faits du chemin des hélicos relus dans les deux exe) ; test hôte 397 contrôles / 0 échec ; 18 pannes injectées / 18 attrapées ; voir `frein/RISQUES_v13.md`.

## 4. LU, INFÉRÉ, INCONNU

**LU** : tout le tableau du §2 ; le site H6 et sa cible dans les deux exe et dans les trois copies patchées ; la boucle de la file qui sépare hélicos et avions ; le seuil de 100 m ; les seuils 20 m / 30 m / z > 82 / 3600 / 10 m/s ; le frein fixe 0,6 des hélicos au toucher ; le chemin d'abandon.

**INFÉRÉ** :
- que le toucher passe pour un hélico posé et immobile (comme pour chaque hélico de l'IA) ;
- que le recul vers l'ascenseur part de l'endroit où il est posé, en ligne droite, comme pour les avions de la v12 (à vérifier : un hélico posé loin de l'axe ou près de l'îlot pourrait accrocher quelque chose en étant tiré) ;
- que si le toucher ne passe pas, l'hélico, qui a déjà la piste, fait simplement l'approche courte du jeu (le point visé est à 50 m devant lui) et se repose : c'est la fin normale de l'IA.

**INCONNU (seul un essai le dira)** :
- **ce que fait un hélico quand le pilote le quitte sur le pont, avant le rappel** : reste-t-il posé ou l'IA le fait-elle décoller (comme les avions le 27/10) ? Le journal v13 l'écrit (lignes `heli N …`, roues et vitesse). Si l'IA le soulève avant le rappel, la v13 ne l'attrape pas (pas « tenu sur le pont ») et le jeu fait son retour normal.
- le vent relatif : le 31/10 un **avion** arrêté s'est soulevé avec le navire à ~42 m/s (ses ailes portent) ; un hélico n'a pas d'ailes, mais garder le navire lent reste la règle.
- le 2e champ des roues (`≤ 0,1`) pour un hélico posé à la main (il est passé pour nos avions tenus au frein).
- le comportement si un **autre hélico** est devant lui dans la file (le jeu ne regarde que le premier : la fenêtre se fermera « SILENT » et l'hélico fera son retour normal).

## 5. Et le réglage « approche ×2 des hélicos » de l'autre session ?

Il change une seule constante de la branche hélico (`0x6fe1b3`, 50 m → 100 m : le point visé devant l'hélico), à 693 octets de H5 et loin de H6 (`0x6fdcdd`). Il ne touche ni le don de la piste, ni le toucher, ni la prise en charge. Les deux peuvent coexister (INFÉRÉ), mais **un seul changement à la fois pendant les essais** : d'abord l'essai de l'approche ×2 (prévu, autre session), puis la v13, ou l'inverse — pas les deux dans la même partie la première fois.

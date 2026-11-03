# Essai : approche des hélicos ×2 sur le nouvel exe (31/10/2026)

Demande du moddeur (relayée par la conversation de coordination) : « tester approche x2, la vitesse d'approche x2 pour les hélicoptères ». Étiquettes : **MESURÉ**, **LU**, **INFÉRÉ**.

## Ce qu'on essaie

Une **seule nouveauté** par rapport à la copie qui a marché à 13:52 (`5AF41B4D…`) : le réglage `helicos_approche_x2`. En approche, l'hélico vise un point **100 m devant lui au lieu de 50 m**, donc il avance environ 2 fois plus vite vers le pont (≈ 10 m/s au lieu de ≈ 5, LU dans `etudes/MESURES_helicos.md`). Les avions ne sont pas concernés (cette partie du code est réservée aux hélicos).

- Copie fabriquée **hors du jeu** : `C:\Users\UTILISATEUR\Documents\cc2-port-travail\carrier_command_nouveau_patche_ascenseur_temps_pont_helicos.exe`, sha256 **`2C9F8E47FD494BD3EF04038910C6E2A086742BCDA6AF71CACE2E1B69EA766F06`** = copie à 3 réglages + `helicos_approche_x2` (`patch_exe.py activer`).
- Vérifié (MESURÉ, `outils/verifier_copie_helicos.py`) : elle ne diffère de la copie à 3 réglages que de **2 octets** (un opérande de 4 octets dont 2 changent) ; remettre ces octets redonne exactement `5AF41B4D…` ; au désassembleur, en `0x6fe2c3`, `addss xmm2, [0xdb79f0]` = 50,0 devient `addss xmm2, [0xdb7a18]` = 100,0 (constante en lecture seule) ; **aucun chevauchement** avec les crochets des plugins (le plus proche, H5 du frein, est à 693 octets ; le Hold à plus de 2 000). `patch_exe.py etat` : exactement `ascenseur_x2, helicos_approche_x2, pont_retour_x2, temps_x2`.
- Dans le dossier du jeu, elle aura un **nouveau nom** : `carrier_command_nouveau_2C9F8E47.exe` (la copie à 3 réglages reste à côté, intacte). Outil : `outils/lancer_nouveau_helicos.py` (mêmes garde-fous que `lancer_nouveau.py`) ; 16 contrôles sur faux dossiers, 0 échec.

## Le frein a changé à 17:24 : v13

La session « hélicos à la main et retour auto au hangar » a posé **`cc2x_frein.dll` v13** (`22D04FE3…`, accord du moddeur dans sa conversation, MESURÉ dans le dossier du jeu). Sans `heli_recall` dans `frein.ini` (c'est le cas : `frein.ini` est toujours `D7828C32…`, MESURÉ), la v13 ne regarde aucun hélico et ne pose pas son crochet H6 : elle fait la v12 (LU dans `cc2x_frein.c`, worktree gifted-moore). Conséquences ici :

- mes outils sont épinglés sur la v13, avec exactement les mêmes changements que ceux de la session hélicos ; les 6 testeurs passent (36/32/33/52/22, 0 échec) ;
- `lancer_nouveau_helicos.py lancer` **refuse** si `frein.ini` active `heli_recall` : ce serait une 2e nouveauté dans cet essai ; une ligne « hook H6 » dans `cc2x.log` compte aussi comme un problème ;
- H6 (`0x6fdded`, 8 octets) ne chevauche pas les 2 octets changés : il est à 1 234 octets (MESURÉ, `verifier_copie_helicos.py`) ;
- la v13 n'a encore jamais tourné dans une partie (sauf si la session hélicos l'a lancée entre-temps) : la mesure de référence (copie à 3 réglages) sert donc **aussi** de premier essai de la v13 « comme la v12 ». Les deux parties ont le même frein, donc la seule différence entre elles reste les 2 octets de l'approche.

## Ce que le moddeur accepte (un « oui » à chaque fois)

Depuis le 02/11, le niveau 🟢/🟡/🔴 juge **seulement le risque cyber**, selon la préférence du moddeur. Pour ces trois étapes, il est 🟢 : nos copies et nos plugins, aucun code d'un tiers, aucune connexion ajoutée. Les niveaux 🟡 ci-dessous datent d'avant cette règle et parlaient d'un plantage possible.

| # | Ce que ça fait | Risque |
|---|---|---|
| 1. Copier | ajoute **un fichier** de 11 Mo dans le dossier du jeu ; rien remplacé | 🟢 |
| 2. (conseillé) Lancer la copie à **3** réglages pour une mesure de référence | même copie qu'à 13:52, déjà vue marcher ; nouveau : le frein v13, jamais lancé (si son crochet ne se pose pas, le bilan le dit avant de jouer) | 🟡 |
| 3. Lancer la copie à **4** réglages | première fois que ce fichier tourne ; seule nouveauté : 2 octets dans l'approche des hélicos ; pire cas : un hélico qui arrive mal (collision, partie jetable) ou un plantage | 🟡 |

## Ce que le moddeur fait dans le jeu (à chaque partie, pareil)

1. **NEW GAME** (jamais une sauvegarde). **Navire à l'arrêt**.
2. Sors **3 hélicos** (Razorbill et/ou Petrel ; **les mêmes types** dans les deux parties), fais-les décoller, puis **rappelle-les tout de suite**.
3. Regarde le **journal des retours** du mod `cc2_mesures` à l'écran. Quand il affiche **« FINI en … »**, prends une **capture d'écran** et dis « c'est fini ».
4. Dis-moi aussi ce que tu as vu : approche plus rapide ? un hélico qui arrive mal, qui touche un autre, qui rate le pont ?

## Ce qu'on compare

| | approche (pont − piste) | pont → hangar | piste toutes les |
|---|---|---|---|
| Mac, 23/10, sans réglage hélicos (LU) | **1:00** en moyenne | 0:40 | 1:29 |
| Mac, 24/10, approche ×2 **+** toucher près de l'ascenseur (LU) | **0:28** | 0:30 | 0:47 |
| Windows, nouvel exe, 3 réglages (référence) | à mesurer | à mesurer | à mesurer |
| **Windows, nouvel exe, 4 réglages** | **à mesurer** | à mesurer | à mesurer |

- La colonne **« approche »** est le signal : si le réglage agit, elle doit être **nettement plus courte** qu'à la référence (INFÉRÉ ; sur le Mac, le réglage était essayé **avec** un autre, « toucher près de l'ascenseur », non porté : on ne peut pas attendre 0:28 exactement).
- « pont → hangar » ne devrait pas changer à cause de ce réglage (il dépend du roulage ×2, présent dans les deux copies).
- Un seul essai ne conclut pas finement ; mais un écart de l'ordre de 1:00 à ~0:30 se verrait.

## Pendant la partie, côté Claude

- Copie passive du journal toutes les 20 s vers `logs_parties`, surveillance (`surveiller_journal.py`).
- Au démarrage, mêmes lignes attendues qu'à 13:52 (`lancer_nouveau_helicos.py` fait le même bilan).
- **Fini** = le moddeur dit « fini » ; je ferme le jeu moi-même.

## Revenir en arrière

Jeu fermé : `python -I -B lancer_nouveau_helicos.py retirer --jeu "<jeu>" --cest-le-vrai-jeu` (supprime seulement `carrier_command_nouveau_2C9F8E47.exe`, s'il est exactement notre copie). Rien d'autre n'est changé par cet essai.

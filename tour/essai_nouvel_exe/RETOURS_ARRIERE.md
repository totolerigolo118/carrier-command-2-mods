# Retours arrière de l'essai « nouvel exe » (31/10/2026)

Toujours **jeu fermé** (`Get-Process carrier_command*` vide). Commandes à lancer depuis `tour/essai_nouvel_exe/outils/` de cette worktree, en `python -I -B`. Jeu = `C:\Program Files (x86)\Steam\steamapps\common\Carrier Command 2`.

| Ce qu'on défait | Commande | Ce que ça remet |
|---|---|---|
| Le SDK à deux profils | `python -I -B poser_sdk.py revenir --jeu "<jeu>" --cest-le-vrai-jeu` | `dinput8.dll` = `184B144D…` (copie de `C:\Users\UTILISATEUR\Documents\cc2-sdk-travail\dist\dinput8.dll`, empreinte vérifiée avant et après). Le SDK redevient inactif sur le nouvel exe ; l'ancien exe marche comme avant. |
| La copie du nouvel exe patché | `python -I -B lancer_nouveau.py retirer --jeu "<jeu>" --cest-le-vrai-jeu` | supprime seulement `carrier_command_nouveau_5AF41B4D.exe`, et seulement si c'est exactement notre copie (`5AF41B4D…`). L'exe de Steam n'est jamais touché. |
| La copie à 4 réglages (+ approche des hélicos ×2), si elle a été copiée | `python -I -B lancer_nouveau_helicos.py retirer --jeu "<jeu>" --cest-le-vrai-jeu` | supprime seulement `carrier_command_nouveau_2C9F8E47.exe`, s'il est exactement notre copie (`2C9F8E47…`). |
| Une copie multijoueur (sans temps ×2), si elle a été copiée | `python -I -B lancer_multi_3.py retirer --jeu "<jeu>" --cest-le-vrai-jeu` (ou `lancer_multi_5.py`) | supprime seulement `carrier_command_nouveau_795CD61D.exe` (ou `…_FCB3CDE1.exe`), s'il est exactement notre copie. |
| Le frein v15, réglages normaux du moddeur (posé le 02/11 à 16:12 par la session de coordination, pas par moi ; avant : v14 posée à 15:36, v13 posée le 31/10) | **Le moddeur garde ces réglages** ; s'il voulait revenir en arrière, à décider avec ces sessions, jeu fermé : recopier `C:\Users\UTILISATEUR\Documents\cc2-sdk-travail-v14\dist\cc2x_frein.dll` (`50D0464A…`), `…\cc2-sdk-travail-v13\dist\…` (`22D04FE3…`) ou `…\cc2-sdk-travail\dist_v12\…` (`941DFFB9…`) ; `frein.ini.avant_v14` (`D7828C32…`) est le `frein.ini` d'avant `auto_recall`/`heli_recall` | le frein d'avant. Mes lanceurs, épinglés sur la v15 depuis le 02/11, refuseraient alors cette version : il faudrait les ré-épingler. |
| Tout couper d'urgence | supprimer `dinput8.dll` du dossier du jeu | plus aucun plugin ne se charge (ni frein, ni modes, ni Hold). |

**Ne PAS faire sans l'accord du moddeur** : remettre `frein.ini.avant_v12` (il garde le réglage d'essai `recall_force=1`, `max_speed=35` pour une démo).

Pour lancer l'**ancien** exe tant que le SDK à deux profils est posé : `python -I -B lancer_ancien.py lancer --jeu "<jeu>" --cest-le-vrai-jeu` **de ce dossier** (celui de la worktree manual-landings refuserait `E1DE25D5…`).

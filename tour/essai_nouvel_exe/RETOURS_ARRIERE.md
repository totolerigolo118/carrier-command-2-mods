# Retours arrière de l'essai « nouvel exe » (31/10/2026)

Toujours **jeu fermé** (`Get-Process carrier_command*` vide). Commandes à lancer depuis `tour/essai_nouvel_exe/outils/` de cette worktree, en `python -I -B`. Jeu = `C:\Program Files (x86)\Steam\steamapps\common\Carrier Command 2`.

| Ce qu'on défait | Commande | Ce que ça remet |
|---|---|---|
| Le SDK à deux profils | `python -I -B poser_sdk.py revenir --jeu "<jeu>" --cest-le-vrai-jeu` | `dinput8.dll` = `184B144D…` (copie de `C:\Users\UTILISATEUR\Documents\cc2-sdk-travail\dist\dinput8.dll`, empreinte vérifiée avant et après). Le SDK redevient inactif sur le nouvel exe ; l'ancien exe marche comme avant. |
| La copie du nouvel exe patché | `python -I -B lancer_nouveau.py retirer --jeu "<jeu>" --cest-le-vrai-jeu` | supprime seulement `carrier_command_nouveau_5AF41B4D.exe`, et seulement si c'est exactement notre copie (`5AF41B4D…`). L'exe de Steam n'est jamais touché. |
| Tout couper d'urgence | supprimer `dinput8.dll` du dossier du jeu | plus aucun plugin ne se charge (ni frein, ni modes, ni Hold). |

**Ne PAS faire sans l'accord du moddeur** : remettre `frein.ini.avant_v12` (il garde le réglage d'essai `recall_force=1`, `max_speed=35` pour une démo).

Pour lancer l'**ancien** exe tant que le SDK à deux profils est posé : `python -I -B lancer_ancien.py lancer --jeu "<jeu>" --cest-le-vrai-jeu` **de ce dossier** (celui de la worktree manual-landings refuserait `E1DE25D5…`).

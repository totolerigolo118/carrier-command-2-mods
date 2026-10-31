# Premier essai du NOUVEL exe patché (ascenseur ×2, temps ×2, pont ×2)

**État (30/10/2026) : tout est préparé hors du jeu. Rien n'est copié, rien n'est posé, rien n'est lancé.** Étiquettes : **MESURÉ** (vu par un script), **LU** (dans un de nos fichiers), **INFÉRÉ** (déduit, jamais vu en jeu).

Ce qu'on essaie : le `carrier_command.exe` de Steam d'aujourd'hui (celui de la mise à jour du 28/10), **avec nos trois patchs** `ascenseur_x2`, `temps_x2` et `pont_retour_x2` = « comme avant ». Ce fichier a été fabriqué hors du jeu (`carrier_command_nouveau_patche_ascenseur_temps_pont.exe`, sha256 `5AF41B4D…`) ; **il n'a jamais tourné**. Le but de ce premier essai : voir s'il démarre et si les trois patchs agissent. Rien d'autre (ni frein, ni modes, ni boutons : le SDK reste éteint, c'est voulu).

## Ce que tu auras à accepter (deux « oui » séparés)

| # | Ce que ça fait | Risque | Niveau |
|---|---|---|---|
| **Oui n° 1 : copier** | Ajoute **un seul fichier** de 11 Mo dans le dossier du jeu : `carrier_command_nouveau_5AF41B4D.exe`. Ne remplace rien, ne touche pas à `carrier_command.exe`. Vérifie avant et après que le fichier est exactement le bon. | Un fichier de plus que Steam ne connaît pas (Steam ne l'efface pas, même avec « vérifier l'intégrité », LU dans l'étude de mise à jour). Se retire d'une commande. | 🟢 |
| **Oui n° 2 : lancer** | Lance **cette copie** directement (pas par Steam), comme on le fait pour l'ancien exe. | **Première fois que ce fichier tourne** : il peut ne pas démarrer ou se fermer tout seul (alors rien à réparer : on retire la copie). Il écrit les fichiers que le jeu écrit toujours (réglages, journal, sauvegarde automatique d'une partie neuve). Windows peut afficher un avertissement sur un fichier modifié : **dans ce cas ne rien contourner, me le dire**. | 🟡 |
| Pendant l'essai | Le SDK `dinput8.dll` (celui d'aujourd'hui, qui ne connaît que l'ancien exe) se charge, écrit `cc2x.log` dans le dossier du jeu et **reste éteint** : `unsupported game build … stays inactive` = **attendu**. Aucun plugin n'est chargé. | Aucun, à part ce petit fichier journal. | 🟢 |

**À ne PAS faire pendant cet essai (ce serait 🔴)** : charger une sauvegarde (le chargement plante depuis le 27/10, indépendamment de nos DLL, LU dans le protocole du frein), jouer en multijoueur (`temps_x2` change la vitesse du serveur pour tous), poser la nouvelle DLL du SDK (pas relue : une autre étape, un autre « oui »), lancer par-dessus `carrier_command.exe`.

## Avant, après : ce que je (Claude) fais

1. **Avant la copie** : jeu fermé, Steam ouvert, sommes des fichiers relues (`etat`). Tu dis « oui, copie ».
2. **Copie** (`copier`) puis relecture : un seul fichier ajouté, `carrier_command.exe` inchangé (`461E1262…`).
3. **Avant le lancement** : le programme refuse tout seul si le jeu tourne, si Steam n'est pas ouvert, si `dinput8.dll` / `cc2x_frein.dll` ne sont pas exactement nos versions, si la copie ou `carrier_command.exe` ont changé. Tu dis « oui, lance ».
4. **Lancement** (`lancer`) ; je lis `cc2x.log` et je te dis ce que j'y vois.

## Ce que tu fais dans le jeu (une dizaine de minutes)

**A. Le jeu démarre avec la copie seule.** Le menu s'affiche → **NEW GAME** (partie neuve, navire à l'arrêt). **Ne charge aucune sauvegarde.** Si le menu n'apparaît pas ou si le jeu se ferme : tu me le dis, on arrête (voir « Revenir en arrière »).

**B. Les trois patchs.**
1. **Temps ×2** : après ~20 s, regarde l'affichage **SIM** : il doit montrer **environ ×1,33**, comme sur l'ancien exe patché (LU, protocole du frein). Sans le patch il devrait valoir ×1,00 (INFÉRÉ).
2. **Ascenseur ×2, grue, roulage** : fais monter/descendre un avion sur l'ascenseur et regarde-le : il doit aller **nettement plus vite** que dans le jeu normal (même impression que sur l'ancien exe patché).
3. **Pont ×2 et mesure à 4 avions** (la même que le 27/10) : partie neuve, navire à l'arrêt, sors les **4 avions A1, A2, A5, A6**, **rappelle-les tout de suite**, attends que le journal des retours (mod `cc2_mesures`, à l'écran) affiche **« FINI en … »**, puis **prends une capture d'écran** (comme d'habitude, `Pictures\Screenshots`) et dis-moi « c'est fini ».

**Ce qu'on compare** (journal affiché, en temps de jeu ; LU dans `tour/etudes_circuit_atterrissage/ETUDE.md`) :

| | FINI en | piste toutes les | approche | pont > hangar |
|---|---|---|---|---|
| sans patch (27/10, autre configuration) | 9:58 | — | — | — |
| ancien exe `ascenseur_x2 + temps_x2`, circuit ovale (essais 1 et 2) | 10:10 ; 8:47 | 2:15 ; 1:59 | 0:52 | 0:55 |
| ancien exe cercle + créneau + pont (essai 2 du 29/10) | 7:09 | 1:28 | 0:55 | **0:33** |
| **cet essai : nouvel exe `ascenseur_x2 + temps_x2 + pont_retour_x2`, circuit ovale** | **à mesurer** | **à mesurer** | **~0:52 à 0:55 attendu** | **~0:33 attendu si le pont ×2 agit** |

- « **approche** » est un **témoin** : il ne doit pas bouger (si oui, quelque chose d'autre a changé).
- « **pont > hangar** » est le **signal du pont ×2** : à l'essai 2, avec ce même module, il est passé de 0:55 à 0:33 (MESURÉ ; le cercle et le créneau ne devraient pas l'influencer, INFÉRÉ). **S'il reste à 0:55**, `pont_retour_x2` n'agit pas (ou « piste ×2 » voulait dire autre chose : voir `RAPPORT.md` §1.8).
- Le **total** varie beaucoup d'un essai à l'autre (1:23 d'écart à conditions identiques, LU) : **un seul essai ne conclut pas** ; le comparer à 8:47-10:10, pas à un chiffre exact. Je n'annonce aucun chiffre de réussite.
- Les mods actifs aujourd'hui sont ceux de `mods.xml` (missiles, `cc2_mesures`, `cc2_carte`, `cc2_modes`, et `cc2_hold_copies` posé le 30/10, décoratif) ; seul `cc2_hold_copies` est nouveau par rapport aux essais précédents, et il n'agit pas sur les atterrissages (INFÉRÉ).

**Réussi si** : le jeu démarre ; NEW GAME marche ; SIM ≈ ×1,33 ; l'ascenseur est nettement plus rapide ; les 4 avions rentrent (0 raté) ; « pont > hangar » ≈ 0:33 ; aucun plantage ; `cc2x.log` ne contient que la ligne « unsupported … inactive » attendue.
**On arrête et on retire si** : plantage au démarrage ; menu impossible ; SIM = ×1,00 (le temps ×2 n'agit pas) ; avertissement de Windows ; ligne `ready for` dans `cc2x.log` (inattendu : le SDK ne doit PAS s'activer).

## Ce que je lis dans `cc2x.log`

- **Attendu** : `unsupported game build (PE timestamp 0x6ae228f3, size 0x00af7000): CC2X stays inactive`. C'est le SDK actuel qui dit « je ne connais pas cet exe, je ne fais rien ». Aucune autre ligne ne devrait suivre (INFÉRÉ d'après le source du SDK : il s'arrête là).
- **Inattendu** : `CC2X 0.5.0 ready for …` (le SDK s'est activé : une DLL à deux profils serait posée, ce n'est pas le cas), ou un journal absent alors que `dinput8.dll` est là.
- Après l'essai, je copie `cc2x.log` dans `C:\Users\UTILISATEUR\Documents\cc2-sdk-travail\logs_parties\` (comme pour les autres parties) : il est recréé à chaque lancement.

## Arrêter

- **Normal** : quitte le jeu par son menu, ou dis **« fini »** : tu m'as autorisé à fermer le jeu moi-même quand les tests sont finis (le processus `carrier_command_nouveau_5AF41B4D`). Je ne ferme jamais en plein test.
- **Urgent** (jeu figé, comportement bizarre) : Alt+F4 ; sinon Gestionnaire des tâches → fin de tâche sur `carrier_command_nouveau_5AF41B4D.exe`. Ne touche pas à Steam.

## Revenir en arrière

Jeu fermé, une commande : `lancer_nouveau.py retirer` supprime **uniquement** la copie, et seulement si elle est exactement la bonne. **Rien d'autre n'a été changé** : `carrier_command.exe` n'est jamais touché, aucune DLL n'est posée, `mods.xml` est intact. Le jeu normal lancé par Steam reste l'exe de Steam sans patch (SDK éteint aussi). Les fichiers que le jeu écrit seul pendant l'essai (réglages, sauvegarde automatique de la partie neuve) restent sans effet sur ta campagne ; on peut les supprimer si tu veux.

## Commandes (pour Claude ; `python -I -B`, dans la worktree `port-nouvel-exe-27119f`)

```
python -I -B tour\etude_port_nouvel_exe\premier_essai\lancer_nouveau.py etat    --jeu "C:\Program Files (x86)\Steam\steamapps\common\Carrier Command 2" --cest-le-vrai-jeu
python -I -B tour\etude_port_nouvel_exe\premier_essai\lancer_nouveau.py copier  --jeu "…" --cest-le-vrai-jeu      (après « oui, copie » ; --a-blanc pour répéter sans rien écrire)
python -I -B tour\etude_port_nouvel_exe\premier_essai\lancer_nouveau.py lancer  --jeu "…" --cest-le-vrai-jeu      (après « oui, lance » ; --a-blanc possible)
python -I -B tour\etude_port_nouvel_exe\premier_essai\lancer_nouveau.py retirer --jeu "…" --cest-le-vrai-jeu      (jeu fermé)
```

Essais hors jeu du programme : `python -I -B tour\etude_port_nouvel_exe\premier_essai\tester_lancer_nouveau.py` (faux dossiers dans `cc2-port-travail`, aucun jeu lancé) : **45 contrôles, 0 échec** (30/10). `etat`, `copier --a-blanc` et `lancer --a-blanc` ont aussi été lancés sur le vrai dossier, **sans rien écrire ni lancer** : `etat` voit l'exe de Steam `461E1262…`, nos deux DLL aux sommes attendues, `steam_appid.txt`, Steam ouvert, jeu fermé, copie absente.

## Ce que cet essai ne dit PAS

Frein, modes, boutons Hold : **éteints** (le SDK n'agit pas sur le nouvel exe). Multijoueur : inconnu. Chargement de sauvegarde : non essayé (plante déjà sur l'ancien exe). Les 597 blocs de code qui diffèrent ailleurs dans l'exe (voir `RAPPORT.md`) ne sont pas lus : seul l'essai en jeu dira s'ils changent quelque chose. Et la nouvelle DLL du SDK (deux profils) **n'est pas posée** : sa relecture par une autre conversation reste à faire avant tout « oui » de pose.

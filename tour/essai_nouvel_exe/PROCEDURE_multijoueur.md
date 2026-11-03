# Partie multijoueur avec un ami, sans le temps ×2 (31/10/2026)

Demande du moddeur, relayée par la conversation de coordination : « faire une copie sans l'accélérateur de temps, avec tous les autres features, sauf ça. Et après, jouer avec lui. » le moddeur **héberge** ; son ami rejoint avec son jeu Steam normal, à jour, sans rien d'installé. Étiquettes : **MESURÉ**, **LU**, **INFÉRÉ**.

## Les deux copies (fabriquées hors du jeu, dans `C:\Users\UTILISATEUR\Documents\cc2-port-travail`)

Les deux sont **sans `temps_x2`** : la simulation va à ×1, comme le jeu de l'ami.

| Copie | Réglages | sha256 | Nom dans le jeu | Lanceur |
|---|---|---|---|---|
| **prudente (conseillée)** | ascenseur/grue/roulage ×2, retour sur le pont ×2, approche des hélicos ×2 | `795CD61D…` | `carrier_command_nouveau_795CD61D.exe` | `outils/lancer_multi_3.py` |
| complète | les 3 ci-dessus + circuit en cercle + créneau de piste élargi (Albatros) | `FCB3CDE1…` | `carrier_command_nouveau_FCB3CDE1.exe` | `outils/lancer_multi_5.py` |

**Vérifié** (MESURÉ, `outils/verifier_copies_multi.py`, « TOUT EST BON ») :
- chaque copie ne diffère du build de Steam qu'aux endroits de ses réglages (82 et 94 octets) ; `temps_x2` est d'origine ; remettre ces endroits redonne exactement `461E1262…` ;
- recoupement : la prudente = la copie hélicos déjà vérifiée (`2C9F8E47…`) **sans** le temps ×2 = la copie lancée à 13:52 (`5AF41B4D…`) sans le temps ×2, avec l'approche des hélicos ; la complète = la prudente + cercle + créneau ;
- au désassembleur, à chaque endroit : même instruction avant et après, seul l'opérande change ; les constantes lues sont en lecture seule (approche 50 → 100, retour 30 → 15, cercle 600 → −1800) ;
- aucun chevauchement avec les crochets des plugins (frein v13 avec H6, Hold v2.1, modes). Le plus proche : le créneau, à 61 octets de H2 du frein.
- lanceurs : 44 contrôles sur faux dossiers, 0 échec ; copie « à blanc » sur le vrai dossier : OK, rien écrit.

**Pourquoi la prudente est conseillée** : le cercle et le créneau n'ont **jamais tourné sur le nouvel exe**, et **jamais avec le frein**, même sur l'ancien. Le créneau renvoie les avions du virage arrière vers le bloc « test de la piste » (`jbe 0x701c14` → `jbe 0x701b3a`), 19 octets avant le crochet H2 du frein (LU au désassembleur ; l'effet sur un atterrissage à la main est INCONNU). Une première partie multijoueur avec un ami n'est pas le bon moment pour les essayer.

## Ce qui n'a jamais été essayé

- **Rien n'a jamais tourné en multijoueur** : ni les copies patchées, ni les plugins. Pire cas : désynchronisation ou plantage d'une partie jetable. Rien n'est installé chez l'ami ; ses fichiers ne sont pas touchés. Si le jeu de l'ami plante, c'est cette partie seulement (INFÉRÉ).
- Cette copie n'a jamais tourné, même seule. L'approche des hélicos ×2 n'a été vue que sur le Mac.
- Le frein v13 (posé à 17:24 par la session hélicos, `heli_recall` éteint) n'a peut-être encore jamais tourné. Sans `heli_recall`, il fait la v12 (LU). Le lanceur refuse si `heli_recall` est activé.
- Les **mods actifs** chez le moddeur, l'ami ne les a pas. Ce sont les mods de `mods.xml`, dont `cc2_hold_copies`, `cc2_modes`, `cc2_mesures` et, depuis le 02/11, `aide_approche`, posé par une autre session. Je ne sais pas si le jeu exige les mêmes mods chez l'ami (INCONNU). Si l'ami ne peut pas rejoindre, ou si l'affichage diffère, c'est une piste. `aide_approche` n'a pas de dossier `cc2x` : il ne change rien aux plugins (MESURÉ).
- Le jeu est lancé **directement** (pas par le bouton « Jouer » de Steam), comme à 13:52, avec Steam ouvert. Les invitations Steam devraient marcher (INFÉRÉ, jamais vu). Si l'ami ne trouve pas la partie, dis-le-moi.
- Le frein agit sur l'ordinateur du moddeur, pour **tous** les avions de l'équipe posés à la main, y compris peut-être ceux de l'ami (INFÉRÉ). Après un atterrissage à la main, **l'ordre de retour reste nécessaire** : le retour automatique n'est pas encore fait.

**Règle du moddeur (02/11)** : « pour les futurs tests, il faut que la vitesse soit 1.33 comme d'habitude ». En solo, on lance toujours `carrier_command_nouveau_5AF41B4D.exe` (`lancer_nouveau.py`). Cette copie multijoueur à ×1 est l'**exception** qu'il a demandée pour jouer avec son ami. Un essai solo de cette copie, avant la partie à deux, tournerait donc aussi à ×1.

## Ce que le moddeur accepte (un « oui » à chaque fois)

Depuis le 02/11, le niveau 🟢/🟡/🔴 juge **seulement le risque cyber** (code étranger, réseau, secrets, fuite, droits, suppression de fichiers), selon la préférence du moddeur. Un plantage tient en une demi-ligne.

| # | Ce que ça fait | Risque cyber |
|---|---|---|
| 1. Copier | ajoute **un fichier** de 11 Mo dans le dossier du jeu ; rien remplacé (la copie de 13:52 et l'exe de Steam restent) | 🟢 : notre copie, faite ici, empreinte vérifiée |
| 2. Lancer | premier lancement de cette copie et première partie multijoueur avec nos changements | 🟢 : aucun code d'un tiers ; la seule connexion est celle du jeu avec l'ami par Steam, comme une partie normale ; nos plugins n'ouvrent aucune connexion. Plantage possible d'une partie jetable. |

## Dans le jeu

1. Le moddeur lance (par moi), puis crée une **NOUVELLE partie multijoueur**, jamais une sauvegarde. Il invite son ami.
2. À regarder pendant **10 à 15 minutes** :
   - l'ami **rejoint** sans erreur ;
   - l'ami **voit l'ascenseur plus rapide**, comme le moddeur ;
   - les **boutons Hold bougent ensemble** chez les deux ;
   - la partie reste **fluide**, sans saccades ni retours en arrière des véhicules ;
   - s'il y a un atterrissage à la main, il faut donner l'ordre de retour.
3. Le moddeur dit « fini », et je ferme le jeu moi-même.

## Pendant la partie, côté Claude

- Journal copié toutes les 20 s vers `logs_parties` (`surveiller_journal.py copier --processus carrier_command_nouveau_795CD61D.exe`). Le défaut du copieur, qui ne s'arrêtait jamais avec un nom long, est corrigé : `tasklist` en CSV.
- Au démarrage, le bilan vérifie les mêmes lignes qu'à 13:52 : SDK actif, modes, Hold synchronisé, frein et ses 9 crochets.

## Revenir en arrière

Jeu fermé : `python -I -B lancer_multi_3.py retirer --jeu "<jeu>" --cest-le-vrai-jeu` (ou `lancer_multi_5.py`). Cette commande supprime seulement notre copie exacte. Rien d'autre n'est changé.

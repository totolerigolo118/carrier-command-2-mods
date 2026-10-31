# Pannes injectees dans `cc2x_hold.c` v2 — genere par `injecter_pannes.py`

Chaque ligne : une copie du plugin avec UNE erreur volontaire, compilee avec `tests/test_hold.c` (UBSan, -Werror) et lancee, dans `C:\Users\UTILISATEUR\Documents\cc2-hold-travail\plugin_v2\pannes` (hors depot, hors jeu). Plugin intact : le test passe (tous les controles passent).

**26 / 26 pannes detectees.**

| n. | erreur volontaire | resultat | detail |
|---|---|---|---|
| 1 | synchro : l'original inutilisable (octet 2 = 0) n'arrete plus rien | **detectee** | 5 controle(s) en echec, ex. FAIL line 531: original unusable (byte2 = 0): nothing copied, nothing sent |
| 2 | synchro : ecrit l'octet 2 au lieu de l'octet 0 | **detectee** | 27 controle(s) en echec, ex. FAIL line 481: original on -> both copies on |
| 3 | synchro : deux changements au meme instant recopies quand meme | **detectee** | 5 controle(s) en echec, ex. FAIL line 515: two changes in the same update: nothing copied, nothing sent |
| 4 | synchro : deux changements au meme instant non journalises | **detectee** | 1 controle(s) en echec, ex. FAIL line 517: logged |
| 5 | message 20 avec le drapeau 1 (clic chez les joueurs) au lieu de 0 | **detectee** | 5 controle(s) en echec, ex. FAIL line 483: message 20 for each copy to each player (vehicle id, button, value 1, flag 0) |
| 6 | mauvais numero du porte-avions (+0x84 au lieu de +0x80) | **detectee** | 6 controle(s) en echec, ex. FAIL line 483: message 20 for each copy to each player (vehicle id, button, value 1, flag 0) |
| 7 | mauvaise file du joueur (+0x68 au lieu de +0x64) | **detectee** | 28 controle(s) en echec, ex. FAIL line 481: original on -> both copies on |
| 8 | liste des joueurs : pas de retour au debut de l'anneau | **detectee** | 27 controle(s) en echec, ex. FAIL line 481: original on -> both copies on |
| 9 | liste des joueurs : capacite non bornee | **detectee** | 3 controle(s) en echec, ex. FAIL line 628: liste trop grande: nothing written, nothing sent, stopped (reason 4) |
| 10 | file d'un joueur non verifiee (count > capacite) | **detectee** | 3 controle(s) en echec, ex. FAIL line 628: file : plus de messages que de places: nothing written, nothing sent, stopped (reason 5) |
| 11 | premiere mise a jour vue : recopie au lieu de seulement noter | **detectee** | 7 controle(s) en echec, ex. FAIL line 476: first update seen: nothing written, nothing sent |
| 12 | apres ecriture, l'etat note n'est pas mis a jour | **detectee** | 9 controle(s) en echec, ex. FAIL line 490: logged at the tick: who, what, how many |
| 13 | une copie inutilisable (octet 2 = 0) est ecrite quand meme | **detectee** | 1 controle(s) en echec, ex. FAIL line 545: unusable copy: not written, no message for it |
| 14 | ecriture sans verifier que l'etat est modifiable | **detectee** | arret du test (code 0xc0000005) |
| 15 | arret de la synchro non remis a zero a la partie suivante | **detectee** | 18 controle(s) en echec, ex. FAIL line 628: liste : plus de joueurs que de places: nothing written, nothing sent, stopped (reason 4) |
| 16 | crochet de synchronisation jamais aiguille | **detectee** | 45 controle(s) en echec, ex. FAIL line 481: original on -> both copies on |
| 17 | chargement : bloc du groupe de 6 boutons non controle | **detectee** | 4 controle(s) en echec, ex. FAIL line 684: changed byte at 0070600e: loaded without the synchronisation |
| 18 | chargement : cible de l'appel du groupe non controlee | **detectee** | 1 controle(s) en echec, ex. FAIL line 684: changed byte at 007060b1: loaded without the synchronisation |
| 19 | chargement : type 20 du message non controle | **detectee** | 1 controle(s) en echec, ex. FAIL line 684: changed byte at 006f0101: loaded without the synchronisation |
| 20 | chargement : adresses relogees de 0x565ce0 non controlees | **detectee** | 8 controle(s) en echec, ex. FAIL line 684: changed byte at 00565ce6: loaded without the synchronisation |
| 21 | chargement : adresses de 0x565ce0 comparees au fichier, sans relocalisation (le defaut du 31/10 13 h 14) | **detectee** | 38 controle(s) en echec, ex. FAIL line 311: synchronisation hook refused: abort, inactive |
| 22 | chargement : les jokers ?? ne sont plus acceptes | **detectee** | 38 controle(s) en echec, ex. FAIL line 311: synchronisation hook refused: abort, inactive |
| 23 | chargement : la synchro est posee meme si le code differe | **detectee** | 17 controle(s) en echec, ex. FAIL line 684: changed byte at 0070600e: loaded without the synchronisation |
| 24 | xmm7 non restaure par l'enveloppe des crochets | **detectee** | 32 controle(s) en echec, ex. FAIL line 266: xmm0-xmm7 kept by the synchronisation |
| 25 | v1 : une copie passe outre l'original inutilisable | **detectee** | 2 controle(s) en echec, ex. FAIL line 209: answer 1/1, expected 0 |
| 26 | v1 : saut vers la mauvaise instruction | **detectee** | 30 controle(s) en echec, ex. FAIL line 203: jump to the instruction after the lea (got 03648d8a) |

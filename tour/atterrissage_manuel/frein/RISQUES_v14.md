# Notice des risques : `cc2x_frein.dll` v14 — retour automatique (31/10/2026)

**Empreinte** : `50D0464A052792BAA611D4EDE3990F7387046CB9A4EFD69D3DC2427F9A0C9404` (250 880 octets), dans `C:\Users\UTILISATEUR\Documents\cc2-sdk-travail-v14\dist\`. **Pas posée.** Dans le jeu : la v13 (`22D04FE3…`, posée le 31/10, copie dans `cc2-sdk-travail-v13\dist\`). Conception : `../CONCEPTION_retour_auto.md`. Hélicos : `RISQUES_v13.md` (inchangé).

## En une phrase par cas

| Réglage de `frein.ini` | Ce que fait la v14 | Risque |
|---|---|---|
| tel qu'aujourd'hui (`recall_force=1`, sans `auto_recall` ni `heli_recall`) | **exactement la v12 / v13** : mêmes 9 crochets ; rien n'est appelé | 🟢 |
| `auto_recall=1` (avec `recall_force=1` au démarrage, `recall_hold=1`, `brake_enabled=1`) | quand un avion posé à la main est **tenu, arrêté, roues au contact, pas encore rappelé**, et que **le pilote l'a quitté depuis 5 s**, le plugin demande **une fois** son retour au porte-avions (la même fonction que l'ordre de la carte) ; ensuite c'est la v12 (prise en charge, ascenseur, hangar) | 🟡 |
| `auto_recall=1` et `heli_recall=1` (H6 posé) | pareil pour un hélico posé et immobile, pilote parti depuis 5 s ; ensuite c'est la v13 | 🟡 |

## Ce qui change par rapport à la v13
1. **Aucun nouveau crochet.** Le plugin **appelle** une fonction du jeu : la fonction virtuelle `+0x7c` du porte-avions (« demande d'accostage », `0x707330` ancien exe, `0x707440` nouvel exe), avec les mêmes arguments que le serveur quand il reçoit l'ordre du joueur (`monde = serveur + 0x344`, numéro de l'appareil). Cette fonction ne fait que mettre l'appareil dans la file d'atterrissage et passer `DOCK_STATE` à 5 ; elle vérifie elle-même tout le reste.
2. **Garde-fou** : avant l'appel, le plugin vérifie que la table du porte-avions est **exactement** celle lue pour ce build (`0xd596cc` / `0xd596ec`) **et** que son entrée `+0x7c` est **exactement** cette fonction ; sinon, il n'appelle rien et l'écrit (`AUTO RECALL not asked: …`).
3. **Une seule demande par atterrissage**, après `auto_recall_s` secondes (5 par défaut, de 2 à 60) sans pilote et sans interruption. Si tu remontes avant, c'est annulé (`AUTO RECALL cancelled (pilot back)`). Rien n'est demandé si un autre appareil est déjà en cours, si l'avion bouge, s'il est déjà rappelé, ou si les crochets ne sont pas posés (sans eux, le jeu traiterait l'avion comme s'il volait).
4. Journal : `AUTO RECALL armed …`, `AUTO RECALL: … -> dock 5 (queued: the usual recall follows)`, puis les lignes habituelles (`RECALL start`, `FORCE start`, `TAKEN OVER`, `HANGAR`).
5. Version annoncée : `loaded (frein v14, …)`.

## Ce qui est prouvé (hors jeu)
- **Lu dans les deux exe** (`../outils/verifier_sites_v14.py` → `VERIF_sites_v14.txt`) : entrée `+0x7c` de la table du porte-avions = la fonction de demande d'accostage ; cette fonction trouve l'appareil avec `[ebp+8]` (le monde) et `[ebp+0xc]` (l'id), écrit `DOCK_STATE = 5` et `DOCK_VEHICLE`, et finit par `ret 8` (deux arguments, nettoyés par elle) ; le serveur l'appelle avec `lea eax,[esi+0x344]` (le monde). Les 10 sites de crochets de la v13 sont toujours sûrs.
- **Code compilé relu** : l'appel fait `ecx = porte-avions`, pousse l'id puis le monde, `call` vers l'adresse vérifiée, et ne retouche pas la pile après (comme le jeu l'attend).
- **Test hôte** (`tests/test_frein.c`, UBSan, `-Werror`) : **437 contrôles, 0 échec** (397 de la v13 + T34 : 40 contrôles du retour automatique avec une fausse fonction du jeu).
- **33 pannes injectées** dans une copie du plugin, **33 attrapées** : les 18 de la v13 + 15 du retour automatique (sans contrôle de la table, sans contrôle de l'entrée `+0x7c`, mauvais monde `+0x340`, appel à chaque tick, sans délai, avec le pilote à bord, sans crochets, sans `recall_hold`, en roulant, verrou jamais remis à zéro, id du navire au lieu de l'avion, compte à rebours non remis à zéro au retour du pilote, fonction de l'ancien exe sur le nouveau, sans attendre un autre appareil, hélico appelé pilote à bord).
- **Compilation** : 2 compilations identiques hors horodatage ; imports, exports, sections, TLS **identiques à la v12/v13** ; aucune chaîne suspecte.
- **Outils** (`tour/essai_nouvel_exe/outils/`, épinglés sur la v14 ; v13 et v12 « précédentes ») : `tester_poser` 36/0, `tester_lancer` 32/0, `tester_poser_sdk` 33/0, `tester_lancer_nouveau` 52/0, `tester_lancer_nouveau_helicos` 16/0 ; `poser.py maj --a-blanc` sur le vrai dossier : « remplacer cc2x_frein.dll (notre version précédente) », rien écrit.

## Ce qui n'est PAS prouvé (seul un essai le dira)
| Inconnu | Si ça tourne mal | Gravité |
|---|---|---|
| L'appel direct en vrai (jamais exécuté par notre plugin ; le SDK appelle déjà ainsi le frein et le train) | plantage du jeu (partie jetable) | 🟡 |
| Ce que l'ordre de la carte fait en plus (par exemple `flight=2`) et qui ne vient pas avec l'appel direct | le jeu ne met pas l'avion en file : `-> dock 0 (the game did not queue it)` ; l'avion reste tenu, tu donnes l'ordre à la main comme avant | 🟢 |
| La suite (prise en charge) | identique à un rappel par la carte : v12 (3 sur 3 + Manta) | 🟢 |
| Tu quittes l'avion pour une autre raison (changer de siège, regarder la carte) | au bout de 5 s il part au hangar : allonge `auto_recall_s` ou remonte avant | 🟢 |

## Couper vite
1. **Remonter dans l'avion** avant 5 s : annulé.
2. `auto_recall=0` dans `frein.ini` : plus aucune demande en ≤ 3 s.
3. Fermer le jeu ; la partie est jetable.
4. Retour à la v13 : jeu fermé, copier `C:\Users\UTILISATEUR\Documents\cc2-sdk-travail-v13\dist\cc2x_frein.dll` (`22D04FE3…`) sur la DLL du jeu ; à la v12 : `cc2-sdk-travail\dist_v12\`.

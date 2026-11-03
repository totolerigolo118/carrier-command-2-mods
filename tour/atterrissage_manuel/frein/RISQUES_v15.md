# Notice des risques : `cc2x_frein.dll` v15 — hélico tenu au sol (02/11/2026)

**Empreinte** : `238B0456807AF87FE303F7033899C5CC7DC0F3659054DCDDF44C49FAD0FDE907` (253 952 octets), dans `C:\Users\UTILISATEUR\Documents\cc2-sdk-travail-v15\dist\`. **Pas posée** au moment de l'écriture (dans le jeu : la v14 `50D0464A…`, copie dans `cc2-sdk-travail-v14\dist\`).

## Pourquoi
Essai du 02/11 (15:49-15:58) : Albatross et Manta, quittés par le pilote, sont partis seuls au hangar (v14). Le **Razorbill**, posé sur ses 3 roues et immobile, a été **redécollé par l'IA du jeu 0,5 s après le départ du pilote** (moteur à 1,00, mode 0), deux fois : le retour automatique ne pouvait pas le prendre.

## Ce qui change par rapport à la v14
- Avec `heli_recall=1` (crochet H6 posé au démarrage), `brake_enabled=1` et `hold_idle=1` : un hélico que **son pilote vient de quitter** (mode 1 → autre, **R** compris) alors qu'il est **posé sur le pont** (toutes les roues au contact, < 1 m/s, `dock=0`) est **tenu** comme un avion depuis la v5 : **moteur à 0 et frein de maintien à chaque tick**.
- La tenue finit quand : le jeu le prend en charge (moteur laissé au jeu), le pilote revient (moteur rendu), il quitte la zone, sa fenêtre de rappel finit **sans** prise en charge (moteur rendu : le jeu le fait voler comme sans nous), un réglage est coupé, la partie finit.
- Un hélico **jamais piloté** (ceux du jeu) n'est jamais tenu. **Les avions : exactement la v14.**
- Journal : `HELI HOLD (pilot gone, standing on the deck): engine power … -> 0, brake …`, `HELI HOLD check after 1 s / 10 s: power read …`, `HELI HOLD ended (…)`.

## Risque cybersécurité : 🟢
Imports de la DLL (vérifiés par script, **identiques à la v12, v13 et v14**) : la bibliothèque C (`atof`, `strchr`, `strcmp`, `strlen`, `strncmp`, `calloc`, `free`, écriture du journal) et KERNEL32 : `GetModuleHandleA`, `GetPrivateProfileStringA` (lire `frein.ini`), `VirtualQuery`, `VirtualProtect` (lire / poser les crochets en mémoire), `Sleep`, sections critiques, `GetLastError`, `TlsGetValue`. **Aucun réseau, aucun lancement de programme, aucune ouverture de fichier autre que `frein.ini`, aucun chargement de DLL, aucun registre.** Source écrite par nous (`frein/cc2x_frein.c`), compilée ici avec Zig, aucune chaîne suspecte. Côté plantage : une partie jetable au pire.

## Preuves (hors jeu)
- Test hôte UBSan `-Werror` : **470 contrôles, 0 échec** (437 de la v14 + T35 : 33 contrôles de la tenue des hélicos, dont « un avion à côté reste traité par le code des avions »).
- **45 pannes injectées, 45 attrapées** (18 de la v13, 15 de la v14, 12 de la tenue : hélico jamais piloté tenu, moteur non coupé, pas de frein, moteur rendu à la prise en charge, pas lâché au retour du pilote / à la fin de la fenêtre / quand il n'est plus suivi / à la fin de la partie / en quittant la zone, `hold_idle` ou l'absence de H6 ignorés, souvenir du pilote jamais mis à jour).
- 2 compilations identiques hors horodatage ; imports/exports/sections/TLS identiques à la v12 ; 7 enveloppeurs xmm (aucun nouveau crochet).
- Outils (`tour/essai_nouvel_exe/outils/`, épinglés v15 ; v14, v13, v12 « précédentes ») : testeurs 36/32/33/52/16, 0 échec ; `poser.py maj --a-blanc` sur le vrai dossier : OK, rien écrit.

## Pas prouvé (seul l'essai le dira)
- Que le moteur à 0 suffise : si l'IA réécrit la puissance à chaque tick **avant** la physique, l'hélico pourrait encore se soulever (le journal `HELI HOLD check … power read` le dira). Sans danger : il ferait comme aujourd'hui.

## Couper vite
Remonter dans l'hélico ; `heli_recall=0` ou `hold_idle=0` dans `frein.ini` (≤ 3 s, moteur rendu) ; retour à la v14 : jeu fermé, copier `cc2-sdk-travail-v14\dist\cc2x_frein.dll`.

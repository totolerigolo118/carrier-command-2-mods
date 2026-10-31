# Test A/B « sans patch » / « avec ascenseur ×2 », journal en anglais (30/10/2026)

Étiquettes : **LU**, **MESURÉ** (sortie d'un script), **INFÉRÉ**. Rien de ceci n'est posé dans le jeu.

## But (le moddeur)
Refaire la mesure du 27/10 (retour de 4 avions, journal à l'écran), pour **quantifier** le gain de l'ascenseur ×2, avec un texte en **anglais** pour le partager. Un premier test « sans patch », un deuxième « avec ».

## Rappel du 27/10 (captures dans `C:\Users\UTILISATEUR\Pictures\Screenshots\`)
- sans patch : `Capture d'écran 2026-10-27 073909.png` = « FINI en **9:58** : 4 avions », pont→hangar 1:27 ;
- avec `ascenseur_x2` : `Capture d'écran 2026-10-27 075819.png` = « FINI en **8:03** : 4 avions », pont→hangar 0:51.
Réserves : un essai de chaque côté ; mods actifs différents (le « sans » avait en plus barge, pack_moddeur, boite_noire).

## Ce qui est prêt (hors jeu)
1. **Journal en anglais** : `C:\Users\UTILISATEUR\Documents\cc2-mesures-travail\mesures_en\content\scripts\` (4 scripts), fabriqué par `tour/etude_mesures_en/traduire_mesures.py` à partir du mod installé (`%APPDATA%\Carrier Command 2\mods\cc2_mesures`). **MESURÉ** : 22 lignes changées (1 + 1 + 12 + 8), uniquement des textes affichés, aucune ligne ajoutée ni supprimée, syntaxe Lua vérifiée (`lua_syntaxe.py`, 0 erreur). Les mots français qui restent sont des noms internes (clés `avion` / `helico`, variables). Sommes, source → anglais : `library_custom_1` D0344F94 → 260E9396 ; `_7` E7C30BF6 → 104B4853 ; `_4` B0CEDB8C → 353084D7 ; `_9` 061A3780 → 8E60E12F.
   Exemples : `LANDING LOG (game time)` / `runway deck hangar` / `DONE in 8:03 : 4 planes` / `runway every 1:46  missed 0` / `approach 0:49  deck>hangar 0:51` / `GAME TIME 10:37.3` ; journal des sorties : `LAUNCHES (game time)`, `4/4 AIRBORNE : DONE in 2:15`.
2. **Deux exe de test** (copies, hors du jeu) dans `C:\Users\UTILISATEUR\Documents\cc2-mesures-travail\exe\` : `A_sans_patch.exe` = original exact (`1C9A01C3…`) ; `B_ascenseur_x2.exe` = original + le SEUL module `ascenseur_x2` (`DAC8B1E6…`, **identique à l'exe mesuré le 27/10** : MESURÉ). Même version du jeu (1.5.18 d'avant la mise à jour Steam du 28/10) et même horodatage PE : le SDK s'y active comme sur la copie ancienne.

## Reste à faire (chaque ligne = un « oui » du moddeur dans le message en cours)
- **Poser le journal anglais** (jeu FERMÉ) : sauvegarder les 4 scripts français actuels (dossier de sauvegarde à côté, hors de `mods\`), copier les 4 scripts anglais dans `%APPDATA%\Carrier Command 2\mods\cc2_mesures\content\scripts\`, relire les sommes. **Retour** : recopier les 4 sauvegardes. Les noms de lignes du journal du SDK (`cc2x.log`) ne sont pas touchés. Je n'ai pas encore écrit l'outil de pose (à faire avec le « oui »).
- **Copier A et B dans le dossier du jeu** sous un nouveau nom (`carrier_command_test_A_sans_patch.exe`, `carrier_command_test_B_ascenseur.exe`), jamais par-dessus un fichier ; lancement direct de la copie (jamais par Steam), un seul jeu à la fois, partie NEUVE.
- **Lancer** : jeu fermé, Steam ouvert, `Get-Process carrier_command*` vide ; seulement avec son « oui, lance ».

## Protocole du test (pour un chiffre propre)
Même sauvegarde de départ, même manière de faire : sortir les 4 mêmes avions (A1, A2, A5, A6) puis les rappeler tous ; lire « DONE in … » du journal, avec la capture. Un seul changement entre A et B : le patch. **Idéalement 2 essais de chaque** (la cadence des pistes varie un peu d'un essai à l'autre : 8:47 / 8:03 / 10:10 selon les conditions). Les deux exe tournent à vitesse NORMALE (≈ 10 minutes réelles chacun). **Accélérer la simulation** : possible avec le module `temps_x2` (SIM ×1,33 mesuré), mais il change peut-être un peu les durées lues (pont→hangar 0:55 avec, 0:51 sans, avec d'autres mods différents : INFÉRÉ, non démontré) ; à faire en plus, pas à la place, si le moddeur le veut.

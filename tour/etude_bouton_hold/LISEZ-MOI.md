# Bouton rouge « Hold On Deck » copié près du Helm (30/10/2026)

Étiquettes : **LU** (dans un fichier du jeu), **MESURÉ** (sortie d'un script), **INFÉRÉ** (déduit, jamais vu en jeu).

## Ce qui est fait (hors jeu, rien n'est posé)
- **Demande du moddeur** : le bouton rouge doit être COPIÉ (pas déplacé) près du Helm ; l'original reste sur la console des avions. Le moddeur veut voir les DEUX options dans le même essai, puis garder celle qu'il préfère.
- **LU** (`rom_0\game_objects\vehicle_chassis_carrier.xml`, 422 472 octets, sha256 `FAA0B746…F46F`, 216 boutons) : l'original est `vehicle_control_air_hold`, type 18, panneau 0 (`docking_controls_air`), ligne 1882. Le Helm = panneaux **8** (`nav_left` : démarrer, arrêter, marche arrière, propulseurs latéraux) et **7** (`nav_table_right` : verrou de cap, maintien de cap, feux de navigation, phares).
- **Mod fabriqué** : `C:\Users\UTILISATEUR\Documents\cc2-hold-travail\mod_AB\cc2_hold_copies\` (hors dépôt, hors jeu) = `mod.xml` + `thumbnail.png` + une copie COMPLÈTE du fichier du jeu avec 2 blocs `<button>` ajoutés juste après l'original. Fichier du mod : 423 391 octets, sha256 `BFC52038…3934`.
  - **Copie A** `vehicle_control_air_hold_copie_moteur` : panneau 8, tx=0, ty=0,0015, tz=0,117 (milieu du trou entre « Démarrer » 0,204 et « Arrêter » 0,030 ; juste à côté de « Arrêter le moteur » : risque de confusion).
  - **Copie B** `vehicle_control_air_hold_copie_feux` : panneau 7, tx=−0,117, ty=0,0011, tz=0,036 (milieu du trou entre « Maintien de cap » −0,228 et « Feux de navigation » −0,005).
  - Même `type="18"`, même `display_name_loc="1527"`, même `help_tag` que l'original. Rotation = identité (comme les voisins).
- **MESURÉ** : `diff` indépendant jeu / mod = exactement 6 lignes ajoutées (2 × 3), 0 modifiée, 0 supprimée ; XML bien formé ; 218 boutons, noms uniques. Fichier du jeu et `mods.xml` inchangés (sommes relues après coup). `autotest` : 17 contrôles, 0 échec.
- **Outil** : `fabriquer_mod_hold.py` (Python standard, `python -I`, aucun réseau, aucun sous-processus ; refuse un dossier de sortie dans le jeu ou dans `%APPDATA%\Carrier Command 2`, ou non vide).

## Déplacement de la copie aux feux (02/11/2026, demande du moddeur : « l'encadré rouge »)
- **LU** (`meshes/aircraft_carrier/aircraft_carrier_shell/aircraft_carrier_bridge.mesh`, placé tel quel dans le porte-avions) : sous les leviers des feux de navigation et des phares, le plateau du pupitre est plat à la hauteur du panneau 7 (y = 29,7607), de x −27,458 à −26,939, jusqu'à 27,8 cm devant le panneau (tz −0,278) ; puis un rebord vertical de 8 cm.
- **INFÉRÉ** : la caméra de la capture du moddeur, recalée sur 8 repères (erreur moyenne 2 px), met le centre de l'encadré rouge vers tx −0,03, tz −0,24.
- **Copie C** = la copie aux feux (même nom) à tx = −0,025, ty = 0,0011, tz = −0,220 : sur le plateau, devant le voyant des feux de navigation, à 5,8 cm du rebord. Mod `C:\Users\UTILISATEUR\Documents\cc2-hold-travail\mod_AC\cc2_hold_copies\` (copies A et C), XML `2AC3E98B…` : **une seule ligne** diffère du XML posé `BFC52038…` (la position de la copie aux feux).
- Pose = `poser_mod_hold.py deplacer` (remplace seulement ce fichier dans le mod posé ; le plugin et `mods.xml` restent), jeu fermé, avec le « oui » du moddeur. Retour : la même commande avec `--mod C:\Users\UTILISATEUR\Documents\cc2-hold-travail\mod_AB\cc2_hold_copies`.
- **FAIT le 02/11 à 15 h 34** (« Oui, déplace »), jeu fermé. Mod posé relu : XML `2AC3E98B…`, plugin `4837B1B9…` (v2.1) inchangé, `mod.xml` et vignette inchangés, 4 fichiers. `mods.xml` non touché (dernière modification à 13 h 53, par une autre session). Autotest de `poser_mod_hold.py` : 33 contrôles, 0 échec ; `fabriquer_mod_hold.py autotest` : 0 échec. **Pas encore vu en jeu** : à vérifier que le bouton est bien à plat dans l'encadré, et qu'il bouge toujours avec les deux autres.

## Retrait de la copie près du moteur (02/11/2026, demande du moddeur relayée par la coordination)
- Le moddeur : la copie aux feux (dans l'encadré) « marche tout aussi bien et est mieux placée » ; retirer `vehicle_control_air_hold_copie_moteur`.
- Mod `C:\Users\UTILISATEUR\Documents\cc2-hold-travail\mod_C\cc2_hold_copies\` (`--options C` : la copie aux feux seule, à sa place de l'encadré), XML `84E0558A…` : par rapport au XML posé `2AC3E98B…`, seul le bloc de 3 lignes de `copie_moteur` disparaît.
- `poser_mod_hold.py deplacer` accepte maintenant : position changée, copie retirée ou remise en entier (au moins une copie reste) ; à blanc, il peut tourner pendant le jeu. Autotest : 0 échec. Essai à blanc sur la vraie machine (02/11, ~15 h 55) : accepté, rien écrit.
- **POSÉ le 02/11 par la session coordination** (« cc2 v4 », avec le « oui » du moddeur donné chez elle), jeu fermé : à blanc puis pour de vrai, « DEPLACE : … = 84E0558A (relu) ». Pas encore vu en jeu (relance prévue avec la v15 des hélicos). Plugin v2.1 inchangé (test 636/0 : « une seule copie copie_feux » couvert). Retour : `deplacer --mod …\mod_AC\cc2_hold_copies`.

## Refaire le mod (après une mise à jour du jeu : le mod contient une copie complète du fichier)
```bash
python -I tour/etude_bouton_hold/fabriquer_mod_hold.py autotest
python -I tour/etude_bouton_hold/fabriquer_mod_hold.py fabriquer --jeu "C:\Program Files (x86)\Steam\steamapps\common\Carrier Command 2" --sortie C:\Users\UTILISATEUR\Documents\cc2-hold-travail\mod_AB_2 --options AB
```
Si le fichier du jeu a changé au point que le bouton d'origine n'est plus trouvé exactement une fois, l'outil refuse.

## Poser (PAS fait : demande l'accord du moddeur dans le message en cours ; 🟡 faible, annulable)
Écrit dans `mods.xml` (fichier protégé). Jeu FERMÉ (`Get-Process carrier_command*` vide).
1. Sauvegarde : `mods.xml` → `mods.xml.bak_2026-10-30_hold` (même dossier).
2. Copier `cc2_hold_copies` dans `%APPDATA%\Carrier Command 2\mods\`.
3. Ajouter dans `<active_mod_folders>` : `<path value="C:\Users\UTILISATEUR\AppData\Roaming\Carrier Command 2\mods\cc2_hold_copies"/>`.
**Retrait** : enlever cette ligne (ou restaurer la sauvegarde), supprimer le dossier.
**Conflit** : deux mods Workshop téléchargés ont leur propre copie complète de ce fichier (`3280370621` « Tactical Operations Centre », `3460002110` « Revolution 1.6-19 ») : ils ne sont PAS actifs aujourd'hui (`mods.xml` : 2937532682, `cc2_mesures`, `cc2_carte`, `cc2_modes`). Ne jamais les activer en même temps que ce mod : un seul remplace le fichier.

## À regarder pendant l'essai (partie neuve, ancien exe, `lancer_ancien.py`)
1. Les deux copies s'affichent-elles, bien à plat (ni enfoncées dans le panneau, ni flottantes) ? Sinon corriger `ty` (en mm) et refaire.
2. Quand on appuie sur une copie : l'original bouge-t-il aussi (même interrupteur) ? Et l'inverse ?
3. Un avion encore sur le pont est-il retenu / relâché comme avec l'original ?
4. L'original marche-t-il toujours ?
5. Quelle copie le moddeur préfère (A ou B) ; l'autre sera retirée en refaisant le mod avec `--options A` ou `--options B`.
**INFÉRÉ, jamais essayé** : que le moteur accepte un bouton ajouté, qu'il le relie à la même fonction (par le type 18 ? par le NOM ?). Si une copie s'affiche mais n'agit pas, la fonction est sans doute liée au nom : on le saura seulement en jeu.

## Réserves
- Le contour réel des panneaux est INCONNU : les emplacements sont des milieux de trous entre boutons existants (donc sûrement sur le panneau). Pas d'étiquette « HOLD » sur les copies (le texte est dessiné dans l'image du panneau, qu'on ne change pas) : le bouton se reconnaît à sa couleur.
- Rien n'est commité. Le dossier `cc2-hold-travail` (copie d'un fichier du jeu) ne doit pas entrer dans le dépôt.

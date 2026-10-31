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

# Plugin `cc2x_hold` : les copies du bouton « Hold On Deck » fonctionnent (31/10/2026)

> Suite (31/10) : **v2** où l'original et les copies se suivent, dans `PLUGIN_hold_v2.md` (non posée).

Étiquettes : **LU** (désassemblage de l'exe), **MESURÉ** (sortie d'un script ou d'un test), **INFÉRÉ** (déduit, jamais vu en jeu).
**POSÉ le 31/10** avec l'accord du moddeur (« Oui, pose-le ») : `%APPDATA%\Carrier Command 2\mods\cc2_hold_copies\content\cc2x\cc2x_hold.dll` (`EE9043DA…`, relu identique), jeu fermé, `mods.xml` inchangé (`886D0851`). Pas encore essayé en jeu. Rien n'est commité.

## L'idée en une phrase
Le jeu demande « le Hold est-il enclenché ? » en deux endroits seulement. Juste avant chaque question, le plugin regarde si l'original est enclenché ; sinon, si une copie l'est, il fait lire au jeu l'état de **la copie** à la place de l'original. Il n'écrit rien dans la mémoire du jeu.

## Ce qui est LU dans l'exe (en plus de `RAPPORT_exe_30-10.md`)
- Chaque bouton a un état de 8 octets dans le véhicule (+0x88 : définitions ; +0x4c : états ; +0x50 : nombre). À la création du porte-avions, **tous** les états naissent avec octet 0 = 0 et octet 2 = 1 (fonction 0x84B130).
- Un appui sur un bouton de type 18 (le Hold et ses copies) **inverse l'octet 0** de CE bouton (fonction d'appui 0x5D5530, table des types : 18 = interrupteur). Donc une copie garde son propre « enclenché / pas enclenché ».
- La question « Hold enclenché ? » (0x63F570) répond oui si octet 0 ≠ 0 et octet 2 ≠ 0. Elle est posée en 0x6FCD74 et 0x6FD942, juste après `lea ecx,[esi+0x560]` (esi = le porte-avions). Le plugin pose ses deux crochets sur ces deux `lea` (0x6FCD62 et 0x6FD93C).
- Règle choisie : si l'original est inutilisable (octet 2 = 0, le jeu peut le faire), une copie ne passe pas outre.

## Ancien ou nouvel exe ? (question du moddeur)
- **Fait pour l'ancien exe** (`8E7FCBB6`), le seul où le SDK se charge aujourd'hui.
- **La traduction pour le nouvel exe est déjà dedans.** MESURÉ le 31/10 : les deux endroits et les 5 fonctions dont dépend le plugin sont identiques dans le nouvel exe Steam (`461E1262`), instruction par instruction, seulement décalés de 0x100 à 0x110. Le plugin reconnaît l'exe à sa date de fabrication (horodatage PE) et revérifie octet par octet le code attendu avant de poser quoi que ce soit ; sinon il ne fait rien.
- Ce qui manque pour le nouvel exe : que le SDK lui-même s'y charge (portage en cours dans une autre conversation), puis un essai en jeu. INFÉRÉ : le plugin n'aura pas besoin d'être réécrit.

## Fichiers (dans `tour/etude_bouton_hold/plugin/`, non commités)
- `cc2x_hold.c` : le plugin (C, une page). `tests/test_hold.c` : faux jeu et faux SDK, 273 contrôles.
- `construire_hold.py` : compile dans `C:\Users\UTILISATEUR\Documents\cc2-hold-travail\plugin_v1\` (hors dépôt, hors jeu), contrôle la DLL, compile et lance le test. Rapport : `RAPPORT_compilation.md`.
- `poser_plugin_hold.py` : pose / retrait / état / autotest (20 contrôles sur faux dossiers).

## MESURÉ (31/10, hors jeu)
- DLL `cc2x_hold.dll` : 217 088 octets, sha256 `EE9043DA…3793`. Deux compilations identiques. Exporte seulement `cc2x_plugin_load`. Imports : seulement KERNEL32 (dont `VirtualQuery` pour vérifier qu'une adresse se lit) et le C standard ; aucune bibliothèque réseau, registre ou processus ; aucune chaîne suspecte. Le code C n'appelle ni `VirtualProtect` ni écriture de fichier (contrôle automatique ; `VirtualProtect` figure dans les imports à cause du code de démarrage du compilateur, comme pour le frein).
- Test : 273 contrôles, 0 échec (avec UBSan). 13 pannes injectées volontairement dans des copies du plugin (garde de l'octet 2, saut, contrôle des pointeurs, préfixe des noms, anneau, registres xmm, etc.) : **13 détectées**.
- Pose : `poser_plugin_hold.py autotest` 20 contrôles, 0 échec ; `etat` sur la vraie machine : jeu fermé, mod `cc2_hold_copies` posé et actif avec ses 2 copies, plugin non posé.
- Pas de conflit d'adresses avec les plugins existants (`modes` : 0x71DBBF ; frein : 0x6FE…–0x701… ; Hold : 0x6FCD62, 0x6FD93C) ; le SDK refuserait de toute façon deux patchs qui se chevauchent.

## Poser (FAIT le 31/10 ; 🟡)
Jeu FERMÉ. Une seule écriture : la DLL copiée dans le mod déjà posé, `%APPDATA%\Carrier Command 2\mods\cc2_hold_copies\content\cc2x\cc2x_hold.dll`. `mods.xml` n'est pas touché.
```bash
python -I -B tour/etude_bouton_hold/plugin/poser_plugin_hold.py poser
```
**Retrait** (jeu fermé) : `python -I -B tour/etude_bouton_hold/plugin/poser_plugin_hold.py retirer`. À faire AVANT `poser_mod_hold.py retirer` (qui refuse un dossier de mod qui n'a pas exactement ses 3 fichiers).

Risques : le plugin s'exécute dans le jeu à chaque lancement (code écrit et compilé par nous) et change 2 instructions en mémoire (pas le fichier exe). Si une adresse ne correspond pas, il ne fait rien et l'écrit dans `cc2x.log`. Un défaut non vu par les tests pourrait faire planter le jeu (pas de risque pour l'ordinateur ni pour les fichiers ; la sauvegarde d'une partie jetable). Une copie laissée enclenchée retient les avions comme l'original : la désenclencher.

## À regarder pendant l'essai (partie neuve, ancien exe)
1. `cc2x.log` : « crochets poses en 0x6fcd62 et 0x6fd93c », puis « copie trouvee : …_copie_moteur » et « …_copie_feux ».
2. Enclencher une copie (A au moteur ou B aux feux), lancer un avion : il doit rester retenu sur le pont ; le journal dit « repond vehicle_control_air_hold_copie_… ».
3. Désenclencher la copie : l'avion part.
4. L'original seul marche toujours comme avant.
5. Laquelle des deux copies le moddeur garde (l'autre sera retirée en refaisant le mod avec `--options A` ou `B`).
Limites prévues : appuyer sur une copie ne fait pas bouger l'original, et le voyant rouge de la console des avions peut ne pas s'allumer (INCONNU).

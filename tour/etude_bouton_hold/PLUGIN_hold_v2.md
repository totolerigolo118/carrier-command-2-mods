# Plugin `cc2x_hold` v2 : l'original et ses deux copies toujours dans le même état (31/10/2026)

Étiquettes : **LU** (désassemblage de l'exe, contrôlé par `verifier_synchro_v2.py`), **MESURÉ** (sortie d'un script ou d'un test), **INFÉRÉ** (déduit, jamais vu en jeu), **INCONNU**.

**État au 31/10, après le premier lancement :**
- **v2 (`DDB0AB76…DDA5`) POSÉE** le 31/10 vers 13 h avec l'accord du moddeur (« Oui, remplace »), jeu fermé, à la place de la v1 `EE9043DA…` ; le mod a ses 4 fichiers, `mods.xml` inchangé (`886D0851`). Une copie est gardée dans `C:\Users\UTILISATEUR\Documents\cc2-hold-travail\plugin_v2\posee_31-10_DDB0AB76\`.
- **MESURÉ au lancement (13 h 14, ancien exe 8E7FCBB6)** : `[hold] warn: … synchronisation NON installee (le code du jeu differe en 0x00565ce0) : les copies marchent comme en v1`. Les crochets v1 sont posés : le plugin s'est replié comme prévu, les copies retiennent les avions mais ne se suivent pas.
- **Cause (LU, table de relocalisation de l'exe)** : l'exe est chargé à une adresse variable (ASLR) ; Windows réécrit alors 4 adresses dans la fonction d'envoi 0x565CE0 (offsets +0x6, +0x15, +0x38, +0x45). J'avais mis des jokers sur trois d'entre elles mais pas sur +0x15 (l'adresse du « cookie de sécurité ») : la v2 la comparait à l'octet du fichier. Mon test ne simulait pas ce chargement ailleurs, d'où le trou. Le bloc du groupe et les zones de la v1 n'ont aucune relocalisation.
- **v2.1 (`4837B1B9…DF17`) POSÉE le 31/10 après 13 h 18** avec l'accord du moddeur (« Oui, remplace »), jeu fermé, à la place de la v2 ; empreinte relue, le mod a ses 4 fichiers, `mods.xml` inchangé (`886D0851`). Elle vérifie les 4 adresses **telles que Windows les a réécrites** (valeur exacte attendue, pas un joker). Le test charge maintenant le faux jeu « ailleurs » et reproduit ce défaut. Pas encore essayée en jeu.
- **MESURÉ en jeu avec la v2.1 (ancien exe, lancé à 13 h 23 min 52, journal relu par la session atterrissage)** : « synchronisation posee en 0x7060e0 » ; 12 synchronisations entre 13 h 24 min 30 et 13 h 26 min 19, depuis la copie au moteur ET la copie aux feux, dans les deux sens, chaque fois « recopie sur 2 autre(s) bouton(s), 2 message(s) aux joueurs » (en solo : un seul joueur, le moddeur) ; aucune alerte (ni « arretee », ni « verification ratee », ni « au meme instant »). Après un appui sur une copie, le jeu répond « l'original » : l'original est bien enclenché par la synchronisation. Une seule remarque : au début de la partie (13 h 24 min 13, 0,6 s après « copie trouvee »), « le jeu a rendu le bouton Hold d'origine inutilisable (octet 2 = 0) » : état passager du démarrage, la synchronisation a marché dès 13 h 24 min 30. INFÉRÉ : le jeu met l'octet 2 à 0 pendant un instant au démarrage ; l'avertissement est inutile mais sans effet. **MESURÉ par le moddeur à l'écran (13 h 30)** : « Oui, les trois boutons ont bougé ensemble, je suis très content. » Voyant rouge : pas dit (toujours INCONNU). Jeu fermé à 13 h 30 min 56 (« session finie : synchronisations 12 ») ; journal `cc2x_2026-10-31_1323xx_frein_v12.log` dans `C:\Users\UTILISATEUR\Documents\cc2-sdk-travail\logs_parties\`.
- Séance de 13 h 14 avec la v2 (journal `C:\Users\UTILISATEUR\Documents\cc2-sdk-travail\logs_parties\cc2x_2026-10-31_131446_frein_v12.log`) : deux parties, la copie au moteur a retenu les avions (mode v1), « copie trouvee » une seule fois par partie, aucune synchronisation, aucune erreur.
- Rien n'est commité.

## En une phrase
Quand le moddeur enclenche ou désenclenche l'un des trois boutons « Hold On Deck » (l'original, la copie au moteur, la copie aux feux), le plugin met les deux autres dans le même état **et prévient l'écran de chaque joueur**, exactement comme le jeu le fait pour ses propres boutons. Il ne se demande plus lequel est enclenché : ils bougent ensemble.

## Pourquoi il ne suffisait pas de recopier l'octet (l'idée de départ)
- **LU** : l'état « enclenché » (octet 0) vit sur le **serveur** du jeu (même en solo, le jeu a un serveur et un écran séparés). Ce que le moddeur **voit** est une autre copie, celle de son écran (16 octets par bouton, octet +0xC). Cette copie ne change **que** quand le serveur envoie un message « bouton changé » (le message n° 20 : véhicule, bouton, valeur, drapeau).
- **LU** : le jeu envoie ce message à **chaque** fois qu'il change un bouton : après un appui (0x779C00 et 0x782350, drapeau 1 = petit clic), et quand sa propre logique change un bouton (panneau d'autodestruction 0x6F0950, commandes du porte-avions 0x6EBEC0, groupe de 6 boutons « un seul enfoncé » en 0x705FCD, drapeau 0 = sans clic).
- Donc une simple écriture de l'octet 0 aurait changé la logique (les avions retenus ou non) **sans** bouger les boutons à l'écran. Exemple : le moddeur enfonce l'original, les copies restent sorties à l'écran mais sont « enclenchées » en coulisse ; il appuie sur une copie pour l'enclencher… et la désenclenche, et tout se relâche alors que l'original paraît toujours enfoncé. Pire que la v1. Je ne l'ai pas fait.

## Ce que fait la v2 (et la v2.1)
- **Trois crochets** : les deux de la v1 (inchangés : une copie enclenchée retient les avions) et **un nouveau** dans la mise à jour du porte-avions, en 0x7060E0, **juste après** le groupe de 6 boutons du jeu (LU : ce groupe fait déjà exactement ce qu'il faut : il écrit l'octet 0 puis envoie le message 20 à chaque joueur de la liste, drapeau 0). Le plugin fait la même chose, au même endroit, avec la même liste de joueurs.
- **Règles** (à chaque mise à jour du porte-avions, plusieurs fois par seconde) :
  - **un seul** des trois a changé depuis la fois d'avant → sa valeur est recopiée dans les deux autres, et un message 20 part pour chacun d'eux à chaque joueur ;
  - **deux ou trois** ont changé au même instant → rien n'est recopié, c'est écrit dans `cc2x.log` (il suffit de rappuyer) ;
  - l'original rendu **inutilisable** par le jeu (octet 2 = 0) → rien n'est recopié (même règle qu'en v1 : une copie ne passe pas outre) ;
  - une **copie** inutilisable → ni recopiée, ni source ;
  - la toute première mise à jour après le chargement d'une partie → le plugin note l'état, ne recopie rien. Si, après un chargement, les trois ne sont pas dans le même état, le prochain appui les remet d'accord.
- **Écrit seulement l'octet 0** des autres boutons (jamais l'octet 2, ni les autres). Le message part avec le drapeau 0 : pas de clic sur les boutons qui suivent (le bouton appuyé fait son clic habituel, c'est le jeu).
- **Avant d'écrire**, il vérifie la liste des joueurs et la file de messages de chacun, et que l'état est modifiable. Au moindre doute : **rien n'est écrit**, la synchronisation s'arrête pour la partie (c'est écrit dans le journal) et la v1 continue de marcher.
- **Au chargement**, il revérifie octet par octet les 216 octets du groupe de 6 boutons (où il se pose) et les 186 octets de la fonction d'envoi du jeu (0x565CE0, avec ses 4 adresses telles que Windows les a relogées — c'est la correction de la v2.1 — et le type 20 du message). Si ça diffère : il pose seulement les crochets de la v1.

## Qui lit ou écrit ces octets (LU, `verifier_synchro_v2.py` : 50 contrôles OK, dont 9 sur la table de relocalisation)
| Qui | Quoi | Prévient les écrans ? |
|---|---|---|
| création du porte-avions (0x84B130) | octet 0 = 0, octet 2 = 1 | (état de départ, envoyé à l'arrivée d'un joueur — INFÉRÉ) |
| appui d'un joueur (0x5D5530, appelé seulement depuis 0x779C00 et 0x782350) | octet 0 inversé (interrupteur, type 18) | oui, message 20, drapeau 1 |
| logique du jeu (groupe de 6 boutons, autodestruction, commandes) | octet 0 écrit directement | oui, message 20, drapeau 0 |
| fin de mise à jour du véhicule (0x6C4A60) | octet 1 := octet 0 (« valeur d'avant ») | non (ne change pas l'octet 0) |
| question « Hold enclenché ? » (0x63F570, seulement en 0x6FCD74 et 0x6FD942) | lit octets 0 et 2 de l'original | — |
| **plugin v2 / v2.1** | octet 0 des autres boutons, seulement après un changement | **oui, message 20, drapeau 0** |

Personne d'autre dans le jeu ne connaît les copies (leurs noms ne sont pas dans l'exe) : elles ne changent que par appui ou par le plugin.

## Réseau (LU)
Le serveur envoie le message 20 à chaque joueur de la liste du porte-avions. Le plugin n'agit que là où tourne le serveur (chez l'hôte de la partie) ; il envoie aux mêmes joueurs que le jeu. INFÉRÉ : en partie à plusieurs, les autres joueurs voient aussi les trois boutons bouger ensemble. Jamais essayé.

## L'affichage suit-il ?
- **LU** : chez chaque joueur, le message 20 est appliqué par 0x5CEB10 : l'octet +0xC de son état d'écran prend la valeur (toujours), le clic ne sonne que si le drapeau ≠ 0.
- **LU** : c'est le même mécanisme qui fait ressortir les autres boutons du groupe de 6 quand on en enfonce un.
- **MESURÉ** (le moddeur, 31/10, 13 h 30, v2.1) : les trois boutons bougent ensemble à l'écran.
- **INCONNU** : le voyant rouge de la console des avions. INFÉRÉ : comme l'original est maintenant vraiment enclenché quand on appuie sur une copie, s'il suit l'original, il suivra.

## Ancien ou nouvel exe ?
Les deux tables de la v1 sont gardées. **MESURÉ** : dans le nouvel exe Steam (`461E1262`), le bloc de 216 octets est identique 0x110 plus loin (0x70611E, crochet en 0x7061F0) et la fonction d'envoi 0x120 plus loin (0x565E00), avec ses 4 adresses relogées aux mêmes offsets. L'exe patché que le moddeur lance (`8E7FCBB6`) est identique à l'original à tous ces endroits. Le nouvel exe n'est **pas essayé** (le SDK ne s'y charge pas encore).

## MESURÉ (31/10, hors jeu)
- **v2.1** dans `C:\Users\UTILISATEUR\Documents\cc2-hold-travail\plugin_v2\dist\` : **223 744 octets, sha256 `4837B1B9FC26C3AA236A28564785BF6F74F2BC97D4C3150B54355AD90D89DF17`**. Deuxième compilation identique (hors horodatage PE et identifiant de build, comme la v1). Exporte seulement `cc2x_plugin_load`. **Imports identiques à la v1** (aucune fonction en plus) ; aucune chaîne suspecte ; le code C n'appelle aucune fonction interdite (`VirtualProtect`, fichiers, threads…). Rapport : `plugin/RAPPORT_compilation.md`. (La v2 posée, `DDB0AB76…`, avait passé les mêmes contrôles ; son défaut est celui de 13 h 14.)
- Test hors jeu : **636 contrôles, 0 échec, avec UBSan** (ceux de la v1, adaptés aux 3 crochets, + synchronisation dans les deux sens, deux et trois changements au même instant, original inutilisable, copie inutilisable, copie absente, une seule copie, aucun joueur, trois joueurs, deux porte-avions, 17 porte-avions, listes et files de joueurs abîmées (8 cas), état non modifiable, code du jeu différent (16 octets changés un à un), adresse laissée comme dans le fichier (le défaut de 13 h 14), nouvel exe). Le faux jeu est chargé ailleurs qu'à 0x400000, avec les adresses relogées comme le fait Windows. La fausse fonction d'envoi est écrite en assembleur avec la convention du jeu et abîme xmm0–xmm7, comme pourrait le faire la vraie.
- **26 pannes injectées volontairement** dans des copies du plugin (garde de l'octet 2, drapeau du message, numéro du véhicule, file du joueur, anneau des joueurs, première mise à jour, deux changements, contrôles au chargement, adresses relogées — dont le défaut de 13 h 14 —, jokers, registres xmm, etc.) : **26 détectées**. Rapport : `plugin/RAPPORT_pannes.md`.
- `verifier_synchro_v2.py` sur les trois exe : **50 contrôles, 0 échec** (à 13 h la fiche annonçait 42 : c'était en réalité 41 ; 9 contrôles de relocalisation ajoutés depuis — ce sont eux qui auraient vu le défaut).
- `poser_plugin_hold.py autotest` : **34 contrôles, 0 échec** (dont la commande `remplacer`, sur de faux dossiers).
- Sur la vraie machine : `remplacer` v1 → v2 fait vers 13 h avec le « oui » du moddeur, empreinte relue `DDB0AB76…`. Lancement à 13 h 14 : synchronisation refusée (voir l'état en haut), v1 active.

## Risque : 🟡 (un cran au-dessus de la v1)
- **Nouveau par rapport à la v1** : la v2.1 **écrit** dans la mémoire du jeu (l'octet 0 d'au plus deux autres boutons, seulement après un changement) et **appelle une fonction du jeu** (0x565CE0) qui range un petit message dans la file de chaque joueur (le jeu le fait lui-même en 12 endroits).
- **Pire cas** : un défaut non vu par les tests ferait planter le jeu ou désaccorderait l'affichage des boutons. Aucun risque pour l'ordinateur ni pour les fichiers. Une sauvegarde peut garder l'état des boutons (le même qu'un joueur peut mettre à la main) : faire l'essai sur une partie jetable.
- **Garde-fous** : code du jeu revérifié octet par octet ; tout est vérifié avant d'écrire ; au moindre doute rien n'est écrit et la v1 continue (c'est ce qui s'est passé à 13 h 14) ; une seule écriture de fichier pour poser, réversible.
- **Alternative plus sûre** : revenir à la v1 (🟡 plus bas) : les copies marchent, mais sans se suivre. La v2 posée aujourd'hui se comporte déjà comme la v1.

## Poser
**v1 → v2 : FAIT le 31/10 vers 13 h** avec le « oui » du moddeur (synchronisation refusée au lancement, voir en haut).

**v2 → v2.1 : FAIT le 31/10 après 13 h 18** avec le « oui » du moddeur, jeu fermé (commandes gardées pour mémoire). Une seule écriture : la DLL du mod est remplacée. Le script refuse si la DLL posée n'est pas exactement la v2 `DDB0AB76…` (sa copie gardée sert de référence), si le jeu tourne, si le mod n'a pas exactement ses 4 fichiers. `mods.xml` n'est pas touché. Risque 🟡, le même que la v2.
```bash
python -I -B tour/etude_bouton_hold/plugin/poser_plugin_hold.py remplacer --ancienne "C:\Users\UTILISATEUR\Documents\cc2-hold-travail\plugin_v2\posee_31-10_DDB0AB76\cc2x_hold.dll" --a-blanc
```
```bash
python -I -B tour/etude_bouton_hold/plugin/poser_plugin_hold.py remplacer --ancienne "C:\Users\UTILISATEUR\Documents\cc2-hold-travail\plugin_v2\posee_31-10_DDB0AB76\cc2x_hold.dll"
```
**Retour à la v1** (jeu fermé), depuis la v2.1 :
```bash
python -I -B tour/etude_bouton_hold/plugin/poser_plugin_hold.py remplacer --dll "C:\Users\UTILISATEUR\Documents\cc2-hold-travail\plugin_v1\dist\cc2x_hold.dll" --ancienne "C:\Users\UTILISATEUR\Documents\cc2-hold-travail\plugin_v2\dist\cc2x_hold.dll"
```
Depuis la v2 encore posée : même commande avec `--ancienne` = la copie `posee_31-10_DDB0AB76`. **Retrait complet** : `poser_plugin_hold.py retirer --dll <la DLL posée>`.

## À regarder pendant l'essai (partie jetable, ancien exe)
1. `cc2x.log` : « crochets poses en 0x6fcd62 et 0x6fd93c », puis « **synchronisation posee en 0x7060e0** » (avec la v2.1 ; la v2 disait « NON installee »), puis les deux « copie trouvee ».
2. Appuyer sur la copie au moteur : l'original et la copie aux feux **s'enfoncent aussi** à l'écran. Journal : « vehicle_control_air_hold_copie_moteur enclenche ; recopie sur 2 autre(s) bouton(s), N message(s) aux joueurs ».
3. Lancer un avion : il reste retenu. Appuyer sur l'original : les **trois ressortent**, l'avion part.
4. Le voyant rouge de la console des avions s'allume-t-il ? (INCONNU)
5. Si le journal dit « synchronisation arretee » ou « NON installee » : me le recopier ; les copies marchent alors comme en v1.

## Fichiers (dans `tour/etude_bouton_hold/`, non commités)
- `plugin/cc2x_hold.c` (v2.1), `plugin/tests/test_hold.c` (636 contrôles), `plugin/construire_hold.py` (compile dans `plugin_v2`, compare à la v1), `plugin/injecter_pannes.py` (26 pannes), `plugin/poser_plugin_hold.py` (+ `remplacer`), rapports `plugin/RAPPORT_compilation.md` et `plugin/RAPPORT_pannes.md`.
- `verifier_synchro_v2.py` : relit les trois exe (lecture seule) et refait les 50 contrôles :
```bash
python -I -B tour/etude_bouton_hold/verifier_synchro_v2.py "C:\Users\UTILISATEUR\Documents\cc2-patchs\tour\sauvegardes\carrier_command_1.5.18_original.exe" "C:\Users\UTILISATEUR\Documents\cc2-patchs\tour\sauvegardes\carrier_command_1.5.18_patche_8E7FCBB6.exe" "C:\Users\UTILISATEUR\Documents\cc2-port-travail\carrier_command_nouveau_steam_461E1262.exe"
```

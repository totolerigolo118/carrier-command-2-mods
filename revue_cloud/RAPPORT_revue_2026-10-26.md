# Revue critique des greffes + tests cloud (session cloud du 26/10/2026)

Branche : `[branche]` (jamais `main`). **Aucun fichier existant n'a été modifié** : cette note et le dossier
`essais_differentiels/` sont les seuls ajouts. Aucune correction n'est appliquée : elles touchent des modules du Mac
(propriété du Mac, section 12 de la passation) et doivent être vérifiées avec le programme du jeu ou en jeu.

**Suite pour le Mac** : `FEUILLE_MAC_desassemblage.md` (comment répondre aux questions de la section 5, pas à pas), l'outil de lecture
`outils_mac/desasm.py` (lecture seule ; essayé ici avec l'`objdump` de Linux, à contrôler sur le Mac comme l'indique la feuille) et le texte
à coller dans la session du Mac, `PROMPT_A_COLLER_MAC.txt`.

## 1. En trois lignes

- Les tests de l'extension Windows passent tous, et la DLL 32 bits se compile. Rien n'a tourné sous Windows ni dans le jeu.
- Quatre relectures indépendantes (grue, CCTV, vitesse de l'escadrille, roulage au retour + barre de vitesse) n'ont trouvé
  **aucun défaut certain de plantage**, mais plusieurs points à vérifier sur le désassemblage et **trois écarts avec ce que le
  patch promet** (section 3, points 1 à 3).
- Les relectures n'avaient **pas** le programme du jeu (absent du dépôt) : tout ce qui dépend de lui est une question en section 5.

Légende des constats : **[exécuté]** reproduit par un programme d'essai ici ; **[vérifié]** relu dans le dépôt par moi ;
**[rapporté]** affirmé par un relecteur, non revérifié ; **[binaire]** seul le désassemblage ou le jeu peut trancher.

## 2. Ce qui a tourné

| Essai | Résultat |
|---|---|
| `extension_windows/tests/run_tests.sh`, étapes 1 à 5 (gcc + sanitizers, tremplin exécuté en 32 bits, tests compilés en 32 bits, Lua 5.3 via lupa) | 48 tests, 732 contrôles, 0 échec ; tremplin 138 contrôles, 0 échec ; shim Lua : tout passe |
| `extension_windows/build.py` (Zig 0.15.2) | DLL i386 de 235 008 octets, exports `cc2x_plugin_load`, mêmes imports que dans `BUILD.txt`. sha256 de cette compilation : `d28bbfbee09119960846950baa1fcebec28ef4821f83b721e92a6af21c05e1bd` (aucune empreinte n'avait été notée avant) |
| `extension_windows/tools/mac_table_to_comments.py --check` | À jour |
| `tests/essai_grue_annulation.c` en natif Linux x86_64 (même source que le test « Rosetta » du Mac) | « RESULTAT LOGIQUE : tout est bon » ; refait aussi en -O0, -O2, -O3 par le relecteur : tout passe |
| Banc différentiel vitesse (`essais_differentiels/vitesse/`) | Les octets réels du module (greffe + branchement + octets d'origine) chargés à leurs vraies adresses : **400 000 cas du plancher** et **200 000 appels de `cc2_vitesse`**, comparés au code d'origine et à un modèle : 0 écart (16 registres, 16 xmm, drapeaux, pile, structures) |
| Banc différentiel CCTV (`essais_differentiels/cctv/`) | Les 4 greffes contre les octets d'origine, 2000 essais chacune avec registres/drapeaux/xmm aléatoires : voir section 3, CCTV |

**Impossible ici** : `tests/test_patchs.py`, `test_helicos`, `test_cctv_net`, `test_vitesse_escadrille`, `test_ecriture_releve`
(partie objdump) lisent `sauvegarde/build_mac_origine` ; `test_horloge`, `test_journal`, `test_releve`, `test_vitesse_boutons`
lisent les Lua d'origine du Steam du Mac. À relancer sur le Mac. Les essais en jeu ne se font que sur le Mac / la tour.

## 3. Ce que la relecture a trouvé (par ordre d'importance)

### Écarts avec ce que le moddeur croit obtenir

1. **La barre ECO / NORMAL / FLANK ne change presque pas la vitesse de croisière** [rapporté, cohérent avec la mesure du 25/10
   déjà dans DEMARRER section 7]. Le régulateur vise 120 m/s au-delà d'environ 800 m quel que soit le plancher. Calcul du
   relecteur avec la formule de l'étude : 20 km en ECO 169,9 s, en FLANK 165,9 s, soit environ 2 % (l'étude annonce ~40 %). L'en-tête
   de la barre (`fichiers/vitesse_boutons/library_custom_6.lua` lignes 2-7 : « vitesse de croisière », « 50 % / 80 % / plein gaz ») et
   `etudes/ia_vitesse.md` promettent plus. Seul ECO a été mesuré en jeu ; pour NORMAL et FLANK c'est déduit de la formule.
   Seul un second crochet sur le 120 du régulateur (0x1001c5da0…) donnerait une vraie vitesse de transit.
2. **NORMAL est appliqué sans aucun clic** [vérifié] : `g_vit_mode_defaut = 2` (ligne 26) et `vit_lire` (lignes 35-37) appellent
   `cc2_vitesse(équipe, 2)` dès que le mode vaut 0 (« pas encore choisi » = jeu d'origine côté greffe). Au premier écran de contrôle
   affiché, les avions du moddeur passent à 61/91 m/s (estimation) sans qu'il ait cliqué. Contraire à « une modification testée à la
   fois » et à la base de comparaison. Piste : `g_vit_mode_defaut = 1` (ECO) pour le premier essai.
3. **NORMAL / FLANK agissent aussi hors transit** [rapporté] : le plancher s'applique à tout avion en `control_mode` 0 (attente,
   escorte, vol vers le porte-avions). FLANK = 144 m/s visés en permanence près d'un point : carburant brûlé environ deux fois plus
   vite ; au retour, arrivée vers 144 m/s au lieu de 48 au gestionnaire d'accostage, ce qui peut fausser le module `atterrissage`.
   Le test `outil/tests_en_jeu/vitesse_vol_pres_du_point.lua` n'a jamais été terminé.

### CCTV (`cctv_net`) — jamais vu avec un joueur

4. **La greffe A écrit `rdx`, que le code d'origine ne touche pas** [exécuté + vérifié] : `outil/generateurs/cctv_net.s` ligne 19
   (`leaq (%rax,%rcx), %rdx`) ; l'en-tête du fichier affirme que l'original écrase `rax rcx rdx r8 r9` juste après, ce qui est faux
   pour `rdx` d'après les octets d'origine (banc : `rdx` diffère dans 2000 essais sur 2000 sur le chemin non-CCTV, `rcx` dans 192).
   Si le code entre 0x1000ad77c et l'appel `create` (0x1000ad798) lit `rdx`, la création de **tous** les écrans est corrompue ; le
   chargement sans erreur du 25/10 ne le prouve pas (écrans éteints). **Correction sans coût** : prendre `rcx` comme pointeur
   (`leaq (%rax,%rcx),%rcx`, puis 0x60/0x20/0x18 via `rcx`) ; `r8` et `r9` sont déjà réécrits ensuite. [binaire] pour savoir si c'est nécessaire.
5. **Drapeaux modifiés** [exécuté] : B (0x10021ce70) change les drapeaux dans 1974 essais sur 2000 alors que ses 21 octets d'origine n'y
   touchent pas ; C aussi (1965/2000) et xmm2/xmm3 (sans importance : `glScissor` est appelé juste après). Inoffensif si les
   drapeaux sont morts en 0x10021ce70 et 0x10021ce85 ; sinon `render_screen` bifurque mal pour tous les écrans. [binaire]
6. **L'échelle peut rester à 4,0** [rapporté] si un chemin quitte `render_screen` entre B (0x10021ce85) et D (0x10021cf13) : scissors du
   pilotage / pause / overlay multipliés par 4 pour une image. [binaire]
7. **Hypothèse centrale jamais examinée** [vérifié : ni `etudes/cctv_net.md` ni `partage_detail/06_screens_hud_cctv.txt` ne contiennent le mot
   « viewport »] : que le viewport GL suive la taille de l'**image** (512 × 512) et non celle de la caméra d'interface forcée à 128 × 128
   (l'étude, lignes 82-84, ne traite que de la taille de la caméra). Les cibles `gbuffer`/`post`/`depth` ont la taille de la fenêtre [rapporté] :
   un 512 de haut peut donner un tampon incomplet si la fenêtre fait moins de 512. C'est le point qui peut rendre tout le patch
   inopérant (écran noir, interface minuscule ou coupée). [binaire / jeu]
8. Plus mineurs [rapporté] : un écran portant `screen_cctv.lua` mais de type ≠ 0 (Workshop, Revolution) serait mal mis en page ;
   le CCTV est reconnu seulement par la taille 512 × 512 ; fuites possibles d'état du scissor ; dépassement de `glScissor` pour un
   rectangle > ~5,4e8 ; textes un peu plus flous à l'échelle 4. Lacune de test : `tests/test_cctv_net.py` part de registres propres
   et ne compare ni registres ni drapeaux (le banc `essais_differentiels/cctv/` le fait).

### Grue (`grue_annulation`) — jamais essayée en jeu

Aucun défaut certain (932 octets désassemblés, jmp/call corrects, instructions rejouées exactes, pile 9 push + 0x108 alignée,
callee-saved préservés, zone 0x100061200–0x1000615a4 sans recouvrement). À vérifier sur le binaire avant la **première annulation** :

9. `rcx` = « carte » au crochet A (0x1001a8c01) : si ce n'est pas le bon pointeur, `call *(%rax)` saute n'importe où (plantage à la
   première annulation acceptée). [binaire]
10. Alignement de pile à 0x1001a8c01 et valeur de retour de `undock` (la greffe met 0 ou 1 dans `eax`). [binaire]
11. Gestes 4 et 5 : la remontée à 12 m est-elle hors du `if` de la prise / du lâcher ? Sinon l'avion peut se déplacer avec la grue basse
    (0x1001aea99, 0x1001ae949). Le test de l'essai simule la grue, il ne voit rien là-dessus. [binaire]
12. Le crochet B écrit 0x78 avant que le jeu le relise ; effets de `take` non défaits (largeur de 0x21c, consigne ascenseur 0x1538,
    chemin `load_lift_lower`) ; et « retirer le module ne bloque rien » est
    invérifié si une sauvegarde est faite en plein retour (DEMARRER ligne 321 et `etudes/annuler_montee.md:114` le promettent). [binaire]
- **Conseil du relecteur** : premier essai sur la sauvegarde n° 18 avec un enregistrement juste avant, d'abord un lancement normal,
  puis l'annulation « pas encore attrapé » avant le cas « tenu ».

### Vitesse de l'escadrille — le code est bon

Banc différentiel : 0 écart sur 600 000 cas ; zone 0x10005d000.. (671 octets) sans recouvrement ; personne n'appelle `dofile`.
Restent [binaire] : (a) un saut du jeu tombant dans les 62 `int3` du bloc remplacé (0x1001c2b4c..0x1001c2b8d) ; (b) le stub `fgetc`
(0x102867e60) jamais exercé en jeu (lecture du fichier au 2e lancement) ; (c) `0x260(%r13)` = pointeur d'équipe et son numéro
(`+0x14`) égal à `update_get_screen_team_id()`. Autres points [rapporté] : le mode n'est appliqué qu'au premier dessin de la barre ;
`isnum` jamais vérifié (équipe 0 par défaut) ; **le fichier `vitesse_escadrille.txt` sur le Mac contient sans doute « 1 » laissé par les
scripts d'essai** (le « première fois NORMAL » annoncé n'aura pas lieu) ; **`CHEMIN` est calculé avec `expanduser`**
(`outil/generateurs/generer_vitesse_escadrille.py:24`) [vérifié] : **ne jamais régénérer ce module depuis le cloud** (le chemin
deviendrait `/root/Library/…`) ; en multijoueur seul le mode de l'hôte compte.

### Barre de vitesse (Lua) et `pont_retour_x2`

13. **`color8` est appelée dès le chargement du fichier** [vérifié] (`library_custom_6.lua` lignes 21-25), alors que dans les
    bibliothèques `horloge` et `journal` elle n'est appelée que dans des fonctions. La sonde du 25/10 a noté que l'API des écrans
    n'est liée qu'au `begin_load`. Si `color8` n'existe pas à ce moment, le fichier s'arrête à la ligne 22 : pas de barre, sans message
    clair (mécanisme reproduit avec lupa par le relecteur ; le test du dépôt définit `color8` avant, donc il ne peut pas le voir).
    Correction d'une ligne : construire `g_vit_couleurs` dans `vit_dessiner`, sous le `pcall`. Vérification : chercher `color8(`
    non indenté dans `rom_0/scripts/screen_*.lua` sur le Mac.
14. La chaîne « clic → mode → vitesse de l'avion » n'a jamais été vue de bout en bout [rapporté] : le remplacement de `input_pointer` /
    `input_event` dans `begin_load` n'est pas prouvé en jeu (seul `update` l'est) ; états `appui` / `visible` pouvant rester périmés.
15. `pont_retour_x2` : **le patch est correct** [rapporté, recalculé] : adresses 0x1001b0824, 0x1001ae07c, 0x1001b0831 identiques dans le
    module, le générateur, l'étude et `partage_detail/10_…` ; 30,0 → 15,0 exact ; pas de chevauchement avec les 13 autres modules ;
    tronçons recalculés 42,6 s → 22,4 s, sans dépassement. Effets non mesurés : arrêt sec (~20 m/s²), **hélicos** (avec
    `helicos_pres_ascenseur` le tronçon 5 ne fait que ~4 m ; une mesure de 4 hélicos suffit).
16. **Documentation incohérente** [vérifié pour la dernière ligne, le reste rapporté] : `etudes/piste_et_pont.md` (lignes 11 et 77)
    recommande encore ×3 / « 88 → ~62 s » alors que le module est ×2 (~68 s) ; `partage_detail/02_…:98-104` décrit un autre modèle
    de freinage (faux pour les tronçons de retour) ; DEMARRER section 6 (ligne 269) dit « pas encore mesuré » alors que la section 7
    donne la mesure (pont → hangar 0:51 → 0:32) ; « états 5, 6, 7 » désignent `runway_state` (+0x24) mais aussi des `dock_state`
    ailleurs dans DEMARRER : confusion possible au portage Windows.
17. **Windows** [rapporté] : `extension_windows/lua/cc2_vitesse_shim.lua` ne définit `cc2_vitesse` que si `cc2x.speed.mode` existe à la
    charge du fichier. Plus robuste : toujours définir `cc2_vitesse`, qui renvoie 0 si la fonction manque (la barre se cache seule).
    Avec `lua_speed_stub = 1` la barre bouge sans effet (seul le journal du plugin le dit).

## 4. Ce que je recommande de faire, dans cet ordre (rien n'est appliqué)

1. Décider du **message de la barre** (points 1 à 3) : corriger l'en-tête de la barre, `etudes/ia_vitesse.md` et DEMARRER pour dire
   que le réglage n'agit que près du point ; mettre `g_vit_mode_defaut = 1` pour le premier essai ; finir
   `vitesse_vol_pres_du_point.lua` avant de proposer FLANK.
2. **CCTV** : au désassemblage, répondre aux questions 1 à 4 de la section 5 ; si `rdx` est vivant (ou par prudence), passer à `rcx`
   (gratuit). Ne pas conclure sur le CCTV avant un essai avec un joueur et une fenêtre petite.
3. **Grue** : répondre aux questions 5 à 8 de la section 5 **avant** la première annulation ; ne pas sauvegarder en plein retour.
4. **Barre** : vérifier `color8` (grep ci-dessus) ou déplacer la construction des couleurs sous le `pcall`.
5. Supprimer `vitesse_escadrille.txt` laissé par les essais avant la première vraie partie.
6. Corriger les quatre phrases de documentation du point 16.
7. Sur la tour : définir toujours `cc2_vitesse` dans le shim ; relire les points de ce rapport avant de reporter une greffe en 32 bits.

## 5. Questions à poser au désassemblage du jeu (Mac, `build_mac`)

CCTV
1. 0x1000ad77c → appel `create` (0x1000ad798) : `rdx`, `rcx`, `r8`, `r9` sont-ils écrits avant d'être lus ? un consommateur de drapeaux ?
2. Autour de 0x10021ce70 / 0x10021ce85 : dernier écrivain de drapeaux avant, premier `jcc` / `cmov` / `adc` après ? 0x10021ce70 est-il une entrée de bloc ?
3. Graphe de `render_screen` (0x10021cc14) : un chemin de 0x10021ce85 vers une sortie sans passer par 0x10021cf13 ?
4. Où est appelé `glViewport` dans le passage écran et d'après quels champs (image ou caméra) ? quel tampon de profondeur est attaché aux images d'écran ? `create` garde-t-il largeur/hauteur telles quelles en +0x20/+0x24 ?

Grue
5. D'où vient `rcx` à 0x1001a8c01 ? même pointeur de carte que `cancel_undocking` ? push et `sub rsp` du prologue de `undock` (rsp mod 16) ; l'épilogue 0x1001a8c0e ne fait-il que des pop et `ret` ? `undock` (0x100193eaa) lit-il `eax` ?
6. Aucun saut du jeu entre 0x1001a8c02..0x1001a8c0d ni entre 0x1001ad9ae..0x1001ad9b1 ? `-0x38(%rbp)` écrit au prologue de `update` ? rsp multiple de 16 à 0x1001ad9ad ?
7. Gestes 4 (0x1001aea99) et 5 (0x1001ae949) : comportement avec / sans objet tenu ; la remontée à 12 est-elle hors du `if` ? un état de geste vit-il hors de la liste ?
8. Après 0x1001ad9b2 le jeu relit-il 0x78 avant le roulage (0x1001ae272, 0x1001b10ce) et teste-t-il `dock_state` = 3 ? écritures de `take` (0x1001b0eb1) : largeur de 0x21c, consigne 0x1538, chemin `load_lift_lower` ; `parse_state_xml` : un véhicule `dock_state` 4 dans 0x78 est-il remis à zéro au chargement ?

Vitesse
9. Quelles instructions de `tick_control` sautent vers 0x1001c2b4c..0x1001c2b8d (y compris tables de sauts) ? registres et drapeaux lus après 0x1001c2b8e jusqu'à 0x1001c2ba7 ?
10. Les adresses 0x102867e42 / e60 / e78 / e84 sont-elles `_fclose` / `_fgetc` / `_fopen` / `_fputs` ? 0x1028278dc / 0x102827dc4 / 0x10282801b sont-elles `lua_gettop` / `lua_tointegerx` / `lua_pushinteger` ?
11. `0x260(%r13)` est-il le pointeur d'équipe lu aussi par `c_vehicle_server_base::tick` ? `+0x14` = ce que renvoie `update_get_screen_team_id` (comparer au `team_id` de `save.xml`) ? littéral 120 (0x1028697b8) partagé ? à quelle distance le gestionnaire d'accostage met-il `control_mode` à 3 ?

## 6. À vérifier en jeu (le moddeur, sauvegarde n° 18, jamais dans une partie en cours)

- Barre : visible, entière, en bas à droite des écrans l / m / r ; quel bouton est allumé au tout premier lancement (NORMAL attendu) ;
  clics ECO / FLANK / NORMAL répercutés ; un clic ailleurs sur la carte marche toujours ; après relance, la barre reprend le dernier mode.
- Vitesse : un Albatros et un Manta envoyés à ~300 m du porte-avions, vitesse en ECO puis en FLANK ; rappel de 4 avions en FLANK : journal (0 approche ratée) et jauge de carburant.
- Roulage au retour : 4 avions puis 4 hélicos, à l'œil (recul, virage, arrivée à l'ascenseur, sans saut ni collision) ; journal pont → hangar ≈ 0:32.
- CCTV : écran allumé avec un joueur, fenêtre normale puis petite ; interface lisible, pas d'écran noir, HUD de pilotage intact après.
- Grue : voir le conseil de la section 3.

## 7. Limites de cette revue

- Les quatre relecteurs sont des instances de Claude qui ne connaissaient pas mes conclusions ; leurs rapports sont des **lectures**, pas des
  preuves. Seuls les points marqués [exécuté] ou [vérifié] ont été reproduits ici.
- Pas de programme du jeu : toutes les adresses et tous les décalages viennent des études du dépôt, non revérifiés.
- Rien n'a été essayé sous Windows ni dans le jeu. Les bancs Linux comparent des octets du module à des octets d'origine du module ;
  ils ne disent rien de l'état des registres que le jeu attend réellement.
- Wine n'a pas été essayé (index apt vide dans ce conteneur) : les appels Windows de l'extension (`VirtualProtect`, `VirtualQuery`, …)
  restent compilés mais jamais exécutés.
- Si ce sujet est repris dans le cloud : ne **pas** régénérer les modules (`CHEMIN` dépend du compte), ne rien écrire dans `main`.

## 8. Relancer les essais

```
# extension Windows (Linux, avec  python3 -m venv v && v/bin/pip install ziglang==0.15.2 lupa)
ZIG="v/bin/python -m ziglang" PATH=v/bin:$PATH bash extension_windows/tests/run_tests.sh
v/bin/python extension_windows/build.py
# logique de la grue, en natif Linux
clang -O1 -Wall -Wextra -Werror -o /tmp/essai_grue tests/essai_grue_annulation.c && /tmp/essai_grue
# bancs différentiels (Linux x86_64 seulement)
sh revue_cloud/essais_differentiels/vitesse/lancer.sh
sh revue_cloud/essais_differentiels/cctv/build.sh && revue_cloud/essais_differentiels/cctv/diff
```

Résultat attendu pour le banc CCTV : `rdx` (A), les drapeaux (B, C), `xmm2`/`xmm3` (C) et `g_echelle` (B, D) diffèrent. Pour `g_echelle` et
`xmm2`/`xmm3` c'est voulu par la conception ; pour `rdx` et les drapeaux, c'est le sujet des points 4 et 5.

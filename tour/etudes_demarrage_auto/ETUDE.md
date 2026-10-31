# Démarrer Carrier Command 2 sans cliquer dans les menus : étude (28/10/2026)

## ÉTAT À LA PASSATION (29/10/2026)

1. **Objectif** : arriver directement dans une partie prête (nouvelle partie jetable, ou sauvegarde) en lançant Carrier Command 2, sans cliquer dans les menus, pour tester les mods (modes carburant, frein, circuit d'atterrissage).
2. **Établi** : (LU) un script Lua posé dans un fichier vide de `rom_0\scripts` peut envoyer au menu `new_game_custom` (bouton START) ou `load_game N` ; les réglages de partie neuve sont mémorisés dans `persistent_data.xml`. (LU + MESURÉ hors jeu) les 17 sauvegardes dépassent les emplacements d'équipement du jeu normal et tiennent toutes dans ceux de Revolution (outil `verifier_emplacements_sauvegardes.py`) ; le code qui plante (`0x5EF2D0`, exe 1.5.18 d'origine) relit les équipements sans contrôle de borne ; le Mac confirme le même défaut et Revolution actif chez lui (LU, branche `origin/mac/reponses-tour-28-10`). (INFÉRÉ) la cause Revolution du plantage au chargement : **jamais vue en jeu**. Non expliqué : le plantage « 1 fois sur 2 » d'une partie neuve. Tests hors jeu : 63 + 14 contrôles, 0 échec.
3. **Posé** : **RIEN** dans le dossier du jeu, `%APPDATA%\Carrier Command 2\`, Steam ni ailleurs sur le disque (étude en lecture seule ; j'y ai seulement *lu*). Écrit : ce dossier et mes scripts jetables dans le dossier temporaire de ma session. `installer`, `armer` et `lancer_cc2.py` n'ont **jamais** été exécutés pour de vrai ; `demarrage_auto.py etat` l'a été une fois (lecture seule). Dernier constat réel (28/10, avant la mise à jour Steam) : les 10 `rom_0\scripts\library_custom_N.lua` à 0 octet, mod `cc2_demarrage_auto` absent, pas de dossier `%LOCALAPPDATA%\cc2_demarrage_auto`. Rien à retirer ; si un jour installé : `python -I tour/etudes_demarrage_auto/demarrage_auto.py desinstaller` (jeu fermé).
4. **En attente** : (a) **premier essai guidé (E3)**, le moddeur devant l'écran, jeu libre : il a validé la *préparation* (28/10), pas l'*installation* ; décision à lui demander : « Le jeu est libre ? OK pour écrire `rom_0\scripts\library_custom_0.lua` (🟡 : 0 octet → script, remis à 0 par `desinstaller`) et créer le mod interrupteur (dossier dans `mods\`, ligne dans `mods.xml` via `armer`) ? » (b) Le plantage **au chargement** se tranche par **E1** (cocher Revolution, charger le slot 19 : attendu « ça charge ») et **E2** (partie neuve, SAVE dans `slot_14`, recharger : attendu « ça charge »), un essai chacun ; les **10 lancements** (E4, lanceur, adresse notée à chaque plantage) mesurent, eux, le plantage des parties **neuves**. Question restée sans réponse : faire E2 pendant le premier essai ?
5. **Prochaine action unique** : quand le moddeur annonce le jeu libre, lancer `python -I tour/etudes_demarrage_auto/demarrage_auto.py etat` (lecture seule) pour revérifier après la mise à jour Steam, puis lui poser la question de 4(a).
6. **Pièges** : un seul jeu à la fois (chercher `carrier_command*`, y compris l'ancien exe et les exe d'essai) ; rien sans accord du moddeur et jeu fermé ; `library_custom_0.lua` est le seul numéro libre (1 à 9 pris par des mods) ; ne pas écraser le slot 19 ni se servir de l'autosave comme sauvegarde de test ; ne pas sauvegarder pendant que le plugin de frein tient un avion (le 0 est enregistré) ; Revolution seulement le temps de E1 ; `-dev` non testé ; ne pas accuser « nos patchs » du plantage au chargement (testé avec l'exe d'origine aussi) ; les adresses du texte valent pour l'exe 1.5.18 d'origine.
7. **Non commités (à moi)** : `tour/etudes_demarrage_auto/ETUDE.md` (confirmation du Mac en 3.5 + cette section). Le reste du dossier (`demarrage_auto.lua/.py`, `lancer_cc2.py`, `test_demarrage_auto.py`, `test_lua_demarrage_auto.py`, `verifier_emplacements_sauvegardes.py`) est dans le commit `80f2a8a`, identique à `origin/main` d'après les références locales (pas de `fetch`, non revérifié depuis).
8. **Mise à jour Steam** (signalée par d'autres, je ne l'ai pas vérifiée) : exe remplacé, SDK inactif. **Non évalué** pour mon étude : le nouvel exe a-t-il encore le défaut de borne ? les scripts et définitions de `rom_0` ont-ils changé (mon script s'appuie sur `screen_menu_main.lua`, `update_ui_event`, `update_get_mod_details`, `g_is_menu_active`) ? les fichiers `library_custom_N.lua` sont-ils restés vides ? Le démarrage auto n'a pas besoin de CC2X. INFÉRÉ d'après mon code (non testé) : `lancer_cc2.py --exe` peut lancer l'ancien exe (son nom commence par `carrier_command`).

**Étude en lecture seule.** Le jeu n'a pas été lancé ni fermé ; rien n'a été modifié dans le dossier du jeu, dans `%APPDATA%\Carrier Command 2\` (j'y ai seulement *lu* `persistent_data.xml`, `settings.xml`, `mods.xml`, `saved_games\*\save.xml` et le dossier `mods\`), dans les DLL, les exe ou Steam. Seuls fichiers écrits : ceux de ce dossier `tour/etudes_demarrage_auto/` (cette étude, une proposition de script Lua et son test hors jeu, un outil de vérification des sauvegardes), plus mes scripts jetables dans le dossier temporaire de la session ; rien n'est commité. Aucune commande ni aucun lancement du jeu n'a été fait ; ce que j'ai exécuté : du Python en lecture seule sur les copies d'exe du dépôt et un interpréteur Lua d'essai (DLL signée d'OBS, déjà utilisée par `lua_sonde.py`, sans réseau) — **pas de risque de sécurité** pour tout cela.

## 0. En bref

1. **Oui, c'est faisable, et sans toucher à l'exécutable** : un petit script Lua posé dans un fichier **vide d'origine** de `rom_0\scripts` (par exemple `library_custom_0.lua`) peut, dans le menu, envoyer au jeu **exactement la commande du bouton START** (`update_ui_event("new_game_custom")`). Les réglages de la partie neuve sont **déjà mémorisés** par le jeu (`persistent_data.xml` → `new_game_settings` : 24 îles, 1 équipe IA, équipement complet, tous les plans). Le script, l'installateur et le lanceur sont **écrits et testés hors jeu, mais pas installés** : section 6bis.
2. **Interrupteur sans outil** : le script ne fait rien tant qu'un petit mod « Demarrage auto » n'est pas **coché dans le menu MODS** du jeu (même geste que pour `cc2_modes`). Décocher = menu normal.
3. **Le plantage au chargement d'une sauvegarde a une cause très probable, trouvée** : *toutes* tes 17 sauvegardes contiennent plus d'équipements que le jeu normal n'a d'emplacements, et tiennent exactement dans ceux de **Revolution** (il en ajoute aux avions et au porte-avions) ; Revolution est désactivé depuis le 27/10 matin, et le jeu relit alors ces équipements **sans vérifier** qu'il y a assez d'emplacements. Ce n'est donc très probablement ni nos patchs, ni Windows. Section 3. **Le Mac confirme** (28/10) : même défaut de borne dans son code, et Revolution était actif à chaque chargement chez lui (3.5) ; pas encore de preuve en jeu.
4. **Conséquence** : on peut aussi démarrer **sur une sauvegarde**, à condition qu'elle ait été faite *sans* Revolution (ou avec Revolution recoché). Pour une sauvegarde « jetable » de test : une partie neuve, sauvegarder, c'est fait.
5. **Le plantage « 1 fois sur 2 » en partie neuve n'est PAS expliqué** par cette trouvaille (section 3.4) : prévoir une **relance automatique** si le jeu s'arrête dans les premières minutes.
6. **Ce qui reste à vérifier avec un vrai lancement** (section 5) : que la commande est acceptée **sans appuyer de touche** sur l'écran-titre « PRESS ANY KEY » (sur le Mac oui ; sur Windows jamais testé sans touche), le délai minimal, et le taux réel de plantage.
7. **Recommandation** (section 6) : A (script + interrupteur) + B (relance auto), puis C (sauvegarde sans Revolution). Un seul point 🟡 : écrire un fichier dans le dossier du jeu (réversible en une commande).

## 1. Ce qui existe déjà

| Pièce | Où | Rôle | Statut |
|---|---|---|---|
| Banc Mac | `outil/tests_en_jeu/` (`lancer_test.sh`, `charger_partie_seule.lua`) | Script Lua dans `library_custom_7.lua` de `rom_0` (vide d'origine) : dans le menu, `update_ui_event("load_game", 18)` ; le Mac attend 120 s sans clavier/souris avant de lancer, donc **en principe aucune touche n'était pressée** | a marché (4 min de partie, 123 véhicules) |
| Banc tour | `tour/auto/library_custom_5.lua`, `tour/outils/essai_auto.py`, `essai_auto_reessais.py` | Même idée sur Windows : script dans `rom_0\scripts\library_custom_5.lua`, verrou par le mot de passe de connexion (le menu a ≥ 4 contextes Lua), orchestrateur qui sauvegarde/restaure tout, relance les passes plantées | la partie *menu → commande* marche ; le **chargement plante** à tous les coups |
| Pilotage par clics simulés | `tour/outils/entree_jeu.ps1` (+ `capture_fenetre.ps1`, entrées `viser`/`touche` d'`essai_auto.py`) | Touche pour l'écran-titre, visée de l'écran « GAME » + E, curseur absolu + boucle fermée sur la ligne surlignée : NEW GAME → CUSTOM → START | a marché en partie neuve, **uniquement quand tu n'es pas devant le PC** (la fenêtre du jeu doit être au premier plan ; sinon tout est refusé) |
| Plugin CC2X | `dinput8.dll` + `cc2x_frein.dll` (dossier du jeu, posés par l'étude d'atterrissage) | Code natif chargé au démarrage du jeu | **pas** nécessaire ici (voir option H) |

Constats déjà établis le 27/10 et que je reprends tels quels : les scripts de `rom_0\scripts` sont chargés dans **tous** les états Lua, menu compris ; ceux d'un **mod** ne le sont **qu'en partie** (4 passes en mod : aucun signe de vie au menu) ; les dix `library_custom_N.lua` de `rom_0` sont à 0 octet (revérifié aujourd'hui : tous à 0 octet, le n°5 a été remis vide le 27/10 à 11:24).

## 2. Ce que le jeu sait faire (lu dans `rom_0\scripts` et dans l'exe)

- **Les « commandes » du jeu** passent par `update_ui_event("nom", …)` (`library_ui.lua:2092` → `callback_script_event`). Commandes retrouvées dans l'exe (gestionnaire `0x831750`, liste non garantie complète) : `new_game_campaign`, **`new_game_custom`**, **`load_game N`**, `save_game N nom`, `host_game`, `host_game_campaign`, `host_load_game N`, `join_game_steam_id …`, `join_game_token …`, `quit_game`, plus (dans les scripts) `quit_to_menu`, `character_return_to_bridge`. **Il n'existe aucun « continuer la dernière partie »**.
- **Bouton START** (`screen_menu_main.lua:170-171`) : `update_ui_event("new_game_custom")`. Les réglages sont lus par `update_get_new_game_*` et **mémorisés dans `persistent_data.xml`** (balise `new_game_settings`, valeurs actuelles : `island_count=24 team_count_ai=1 team_count_human=1 island_count_per_team=1 base_difficulty=1 loadout_type=2 blueprints=2 is_tutorial=false`). Le script n'a donc **rien à régler** ; s'il fallait changer un réglage, `update_set_new_game_*` existe (mêmes fonctions que le menu).
- **Écran-titre** « PRESS ANY KEY » : affiché quand la variable `g_is_menu_active` (posée par le programme) est fausse (`screen_menu_main.lua:104` et `:852-872`). Rien dans le script n'attend une touche : le blocage est dans le programme.
- **Détection de l'interrupteur** : `update_get_mod_details()` (utilisée par l'écran MODS du menu) donne pour chaque mod `id`, `is_enabled`, `manifest.name`, `system_folder`. Les scripts de `rom_0` tournent au menu, donc ils peuvent lire cette liste. (`update_set_is_mod_enabled` existe aussi : **le script de la proposition ne l'appelle jamais**.)
- **Verrou entre contextes** : `update_get_join_password` / `update_set_join_password` (valeur partagée par tous les contextes du menu, **non écrite sur disque** : seul `host_password` l'est, on le voit dans `persistent_data.xml`). Il sert aussi à ne lancer qu'**une** partie par lancement du jeu, même si tu reviens au menu.
- **Slot libre** : seul `library_custom_0.lua` n'est utilisé par **aucun** mod présent sur la machine (cc2_mesures : 1, 4, 7, 9 ; cc2_modes : 3 et 5 ; cc2_carte : 6 ; boite_noire : 8 ; camera_libre : 7 ; Workshop 3398249587 « Rev:Resupply+ » : 2 ; Workshop 3225306468 : 3). Je propose le **0**. Les mods ne s'appliquent pas au menu, donc un même numéro ne gênerait de toute façon qu'en partie, où le script est inerte.

## 3. Pourquoi charger une sauvegarde plante (trouvaille)

### 3.1 Ce que fait le code qui plante (lu au désassemblage, copie d'origine `tour/sauvegardes/carrier_command_1.5.18_original.exe`)

- `0x776B29` appelle `0x5EF2D0` depuis la fonction `0x7764e0` (voisine de celle qui écrit « post-loading saved game… », en `0x776f00`). `0x7764e0` est appelée par `load_game` du serveur (`0x775b50`, juste avant son message « proceding with game ») et par une autre branche du gestionnaire de commandes (`0x7754d0` ← `0x831f48`).
- Pour chaque véhicule enregistré, `0x5EF2D0` crée (ou retrouve) le véhicule d'après sa **définition**, puis, pour chaque **équipement enregistré** `i`, appelle `0x5E9D10(slot, …)` ; cette dernière **ignore sans erreur** tout équipement dont le numéro d'emplacement est ≥ au nombre d'emplacements du véhicule (`cmp eax,[ebx+0x160] ; jae` en `0x5E9D48`) ; puis `0x5EF2D0` relit `véhicule.équipements[i]` en `0x5EF512-0x5EF518` **sans comparer `i` à ce nombre** : lecture **au-delà du tableau**.
- Les deux adresses de plantage connues : `0x5EF518` (lecture de l'élément `i`, tableau absent/trop court) et `0x5EF525` (élément non nul mais **poubelle** : on lit `[edi+0x4c]`). Selon ce que contient la mémoire après le tableau, ça plante tout de suite ou plus loin — ce qui explique aussi qu'il y ait **deux** adresses.

### 3.2 La preuve hors jeu : le nombre d'emplacements (outil `verifier_emplacements_sauvegardes.py`)

Emplacements d'équipement par modèle, comptés dans les définitions XML :

| Modèle (indice) | Jeu normal | **Revolution 1.6** | Sauvegarde 19 (autosave du 27/10) | Sauvegarde 18 (ancienne copie, venue du Mac) |
|---|---|---|---|---|
| porte-avions (0) | 14 | **18** | **18** | 14 |
| avion léger `wing_small` (8) | 6 | **9** | **7** | **8** |
| avion lourd `wing_heavy` (10) | 9 | **11** | 4 | 6 |
| hélico léger `rotor_small` (12) | 5 | **7** | 4 | 3 |

(Colonnes des sauvegardes : le plus grand nombre d'équipements enregistrés pour un véhicule de ce modèle. En gras : ce qui dépasse le jeu normal. La sauvegarde 18 que le Mac a **aujourd'hui** est plus récente et donne 18 / 7 / 6 / 4 : voir 3.5.)

**Résultat sur les 17 sauvegardes** : avec les mods actifs actuels (Revolution absent), **17 sur 17 dépassent** le nombre d'emplacements ; avec Revolution ajouté (simulation, aucun fichier modifié), **0 sur 17** ne dépasse. Autrement dit chaque sauvegarde a été faite avec Revolution, et se recharge en dépassant les tableaux dès qu'il n'est plus là. Cela colle avec tout ce qui a été observé :

- plante **à tous les coups** (≥ 14 sur 14) et **aussi avec l'exe d'origine** (le test d'exe retirait nos patchs, pas Revolution) ;
- les deux sauvegardes testées (18 et 19) plantent, la 19 étant pourtant écrite par l'exe Windows ;
- **ça marchait sur le Mac** le 25/10 : les notes du Mac disent que Revolution (3460002110) y était actif (`DEMARRER_cc2_patchs_ETAT_MAC.md`, ligne 204) ;
- tous les essais de plantage datent d'**après** la désactivation de Revolution (08:07 le 27/10, « environnement épuré ») ; le test « mêmes clics avec Revolution actif », proposé dans le journal, **n'apparaît nulle part comme fait**.

**Niveau de certitude : probable, pas démontré en jeu.** L'explication par le code (3.1) et par les données (3.2) est complète et cohérente, mais je n'ai pas vu le jeu charger avec Revolution recoché. Le test E1 de la section 5 tranche. **Le Mac apporte une seconde confirmation indépendante (3.5)**, qui renforce l'explication sans la prouver.

### 3.3 Ce que ça permet

- **Recharger les anciennes sauvegardes** : cocher Revolution (Workshop 3460002110) dans MODS, puis LOAD GAME. (Revolution change le jeu : à ne faire que pour ces sauvegardes.)
- **Avoir une sauvegarde de test chargeable sans Revolution** : une partie neuve avec les mods actuels, puis SAVE depuis le menu pause. L'outil `verifier_emplacements_sauvegardes.py` dira « tient » pour elle. Emplacements sans dossier de sauvegarde (donc rien d'écrasé) : `slot_10`, `slot_11`, `slot_14` (le jeu en garde les lignes dans `persistent_data.xml`, mais les dossiers n'existent pas).
- **Quand sauvegarder** : jamais pendant qu'un avion est tenu par le plugin de frein (voir 3.5, dernier point) ; éviter de compter sur l'autosave (slot 19) pour une sauvegarde de test.
- **Prédire un plantage avant de lancer** : `python -I tour/etudes_demarrage_auto/verifier_emplacements_sauvegardes.py` (lecture seule ; `--ajouter-mod DOSSIER` pour simuler un autre jeu de mods).

### 3.4 Ce qui n'est PAS expliqué

Le journal dit qu'une **partie neuve** plante « 1 fois sur 2 environ, à la même fonction ». Or, d'après les appelants que j'ai trouvés, cette fonction sert à **restaurer un état enregistré** ; la création d'une partie neuve (`generate`, `0x773730`) passe par une autre voie, et une partie neuve n'a aucun véhicule « enregistré » avec trop d'équipements. Deux possibilités : (a) ces plantages de parties neuves étaient à une **autre adresse** que ce que le journal résume ; (b) la restauration est aussi utilisée au démarrage d'une partie neuve (côté « client », avec une vraie course entre serveur et client, ce qui donnerait l'intermittence). **À trancher avec le rapport de plantage Windows** (adresse exacte) *au prochain plantage* (`Get-WinEvent … 'Application Error'`, lecture seule) ; l'outil de relance (option B) peut le noter. En attendant, la prudence demande de **compter sur une relance automatique**.

(Au passage : un vieux fichier `carrier_command_1005012_crash_2025_10_3T14_31_10C0.mdmp` traîne dans le dossier du jeu, daté d'octobre 2025 : autre version de l'exe, autre adresse (`0x46BC7C`), lecture à l'adresse `0xCC` ; **sans lien**.)

### 3.5 Confirmation du Mac (relecture du 28/10, lue sans rien modifier)

Source : `passation_windows/REPONSES_mac_pour_la_tour_28-10.md` sur la branche `origin/mac/reponses-tour-28-10` (pas fusionnée dans `main`), questions Q5 (cette étude) et Q4 (frein). Le Mac a relu **son** programme (désassemblage `objdump`, jeu non lancé) ; ses adresses sont des repères de logique, pas des adresses Windows.

- **Même défaut dans le code Mac** (LU) : `create_from_save_data` appelle `set_attachment`, qui **ignore sans erreur** un emplacement trop grand ; puis une boucle relit `véhicule.équipements[i]` **sans comparer `i` au nombre d'équipements** ; une *autre* boucle de la même fonction **fait** ce contrôle : l'oubli est local à la première. C'est le même schéma que `0x5E9D10` / `0x5EF512-0x5EF518` ici. Deux builds différents (Mac janvier, Windows 1.5.18) : ce n'est pas un accident de notre exe.
- **Revolution était actif à chaque chargement sur le Mac** : son `mods.xml` (inchangé depuis le 3 septembre) cite `2937532682` et `3460002110` ; sa copie de Revolution a les mêmes nombres d'emplacements (porte-avions 18, avion léger 9, avion lourd 11, hélico léger 7). Ses sauvegardes actuelles (slot 18 : 18 / 7 / 6 / 4 ; slot 19 : 18 / 7 / 5 / 4 pour porte-avions / avion léger / avion lourd / hélico léger) **dépassent le jeu normal mais tiennent dans Revolution** : exactement le motif des tiennes.
- **Une précision utile** (DÉDUIT par le Mac) : lire au-delà du tableau **ne plante pas forcément** : si la mémoire qui suit est à zéro, l'élément est sauté en silence ; sinon c'est un plantage. Un chargement « qui passe parfois » n'est donc pas contradictoire avec la cause ; et si la restauration sert aussi au démarrage d'une partie neuve (3.4, hypothèse b), cela irait dans le sens d'un plantage **intermittent** — à confirmer par l'adresse du prochain plantage.
- **Ce que le Mac n'a PAS fait** : charger une sauvegarde **sans** Revolution (aucun plantage chez lui ne prouve donc rien tant que Revolution était présent) ; un test miroir (retirer Revolution, charger le slot 18) est possible côté Mac mais n'a pas été fait. **Le test E1 de la tour reste le bon test.**
- **Mise en garde sur les sauvegardes de test** (Q4 du Mac, à lire avec 3.3) : le jeu **enregistre** la puissance moteur de chaque véhicule (`override_power`, valeur par défaut 1,0) ; il en met lui-même à 0 sur des véhicules rangés ou garés (au moins 17 par sauvegarde du Mac). Si on sauvegarde — l'autosave surtout — **pendant que le plugin de frein tient un avion à 0**, ce 0 est écrit ; au rechargement le plugin a perdu sa mémoire, relit 0 et le moteur reste coupé jusqu'à ce que le jeu réécrive 1,0. **À retenir : ne sauvegarder que lorsqu'aucun avion n'est tenu par le frein** (sauvegarde « départ », avions au hangar, ou « retour », avions en l'air et libres).

## 4. Les options, classées

Risque : 🟢 faible · 🟡 moyen · 🔴 élevé. « Fiabilité » = chance que ça fasse bien ce qu'on veut une fois en place.

| Rang | Option | Fiabilité | Effort | Risque | Verdict |
|---|---|---|---|---|---|
| **1** | **A. Script Lua de menu** (`rom_0\scripts\library_custom_0.lua`) qui envoie `new_game_custom`, avec **mod interrupteur** coché/décoché dans le menu MODS | élevée pour le déclenchement (même commande que START ; mécanisme prouvé pour `load_game` au Mac sans aucune touche, et sur Windows jusqu'au plantage) ; **à vérifier** : écran-titre sans touche | faible (script déjà écrit et testé hors jeu ; reste un installateur sur le modèle de `essai_auto.py --rom0`) | 🟡 écrit 1 fichier dans le dossier du jeu (0 octet → ~4 Ko, remis à 0 octet en une commande ; code Lua exécuté *dans* le jeu, sans accès aux fichiers) | **recommandé** |
| **2** | **B. Lanceur avec relance automatique** : lance par Steam (ou une exe d'essai directement), surveille ; si le jeu s'arrête dans les 3 premières minutes avec un rapport de plantage Windows, il relance (3 fois au plus), note l'adresse de plantage, puis se retire | élevée | faible (reprend `processus_jeu`, `evenements_plantage` d'`essai_auto.py`) | 🟢 ne fait que lancer le jeu et lire le journal d'événements ; n'écrit rien | **recommandé avec A** |
| **3** | **C. Démarrer sur une sauvegarde** (`MODE = "charger"`, `SLOT = n`) | élevée **si** la sauvegarde tient (outil de vérification) ; saute la génération du monde (peut-être plus rapide et plus stable : **non mesuré**) | faible (même script, 1 constante) | 🟢/🟡 (voir E2 : on écrit une sauvegarde de plus) | **2ᵉ étape** |
| 4 | D. Clics simulés (outil existant) | moyenne ; **ne marche que si tu n'es pas devant le PC** (fenêtre au premier plan obligatoire) | déjà fait | 🟡 vrais clics/touches synthétiques (curseur et clic bornés à la fenêtre du jeu depuis le 27/10) | **secours** si A échoue |
| 5 | F. Fichiers de configuration | nulle pour démarrer ; mais utile : `new_game_settings` est déjà mémorisé | — | — | rien à faire |
| 6 | E. Ligne de commande / options Steam | **nulle** : l'exe ne lit que `+connect <adresse>`, `+password <mot de passe>` (rejoindre une partie en ligne) et `-dev` (non documenté ; d'après le désassemblage il enregistre le dossier `rom_0` comme dossier de données ; **ne saute aucun menu**, effet non testé) | — | 🟢 | écarté |
| 7 | G. Serveur dédié (`dedicated_server.exe` + `server_config.xml` + `+connect`) | faible : c'est un **autre exe, non patché** (nos patchs d'ascenseur/temps/atterrissage ne s'y appliquent pas), CC2X ne le gère pas, la partie tournerait chez le serveur | élevé | 🔴 | écarté |
| 8 | H. Plugin natif CC2X (DLL) qui déclenche la commande | élevée en théorie ; il faudrait localiser en plus des adresses internes (exécution d'un script ou du gestionnaire de commandes) | élevé | 🔴 code natif dans le jeu | écarté (réserve si A échoue) |
| — | I. Script de **mod** (dossier `mods\`) | **impossible** pour lancer (les scripts de mod ne tournent pas au menu : mesuré le 27/10) ; sert **seulement d'interrupteur** | — | 🟢 | utilisé comme interrupteur |

Notes sur A :
- **Pourquoi pas un script permanent sans interrupteur** : il lancerait une partie à *chaque* démarrage ; il faudrait vider le fichier pour retrouver le menu. L'interrupteur par mod évite ça et n'exige aucun outil au quotidien.
- **Ce que A touche** : `rom_0\scripts\library_custom_0.lua` (dossier du jeu) ; le mod interrupteur est un dossier `%APPDATA%\Carrier Command 2\mods\cc2_demarrage_auto\` (même forme que `cc2_modes` : `mod.xml` avec `name="Demarrage auto"`, `thumbnail.png`, et un `content\scripts\library_custom_0.lua` ne contenant qu'un commentaire : si, comme je le suppose, un fichier de mod prend la place de celui de `rom_0` *en partie*, le script de menu ne tourne alors pas du tout en jeu — inoffensif de toute façon) et **une ligne** dans `mods.xml` (celle que le menu MODS ajoute quand tu coches).
- **Les exe d'essai** (`carrier_command_test_cercle*.exe`) lisent le même `rom_0` : le script marche aussi avec eux ; le lanceur B doit alors accepter `--exe` (ils ne passent pas par Steam).
- **Risque résiduel de A** : le script enveloppe `begin_load` dans **tous** les contextes Lua (comme l'ancien script d'essai, qui a tourné en jeu) ; un défaut pourrait déranger des écrans. Mitigation : tout est dans des `pcall`, la structure est identique à l'ancien script, et le script passe la syntaxe et 14 contrôles hors jeu (section 7).

## 5. Ce qui exigerait un vrai lancement du jeu

Un seul jeu à la fois : les quatre autres conversations l'utilisent. **Rien de ceci n'est lancé sans ton accord.** Pour chaque essai : ce que ça fait, risque, fichiers touchés, comment tout remettre.

**E1 — Prouver la cause du plantage (🟢 faible ; toi, 5 min, sans outil)**
- *Ce que ça fait* : dans le menu MODS, cocher Revolution (Workshop 3460002110), redémarrer le jeu, LOAD GAME → slot 19. **Attendu : ça charge.** Sinon l'explication de la section 3 est fausse ou incomplète (et on cherche ailleurs).
- *Risque* : au pire un plantage du jeu. Aucune donnée écrasée tant que tu ne sauvegardes pas par-dessus.
- *Fichiers touchés* : `mods.xml` (une ligne, par le menu du jeu). *Retour* : décocher Revolution.
- *Alternative plus sûre* : aucune plus simple ; sinon se contenter de `verifier_emplacements_sauvegardes.py`.

**E2 — Fabriquer une sauvegarde de test chargeable sans Revolution (🟢/🟡)**
- *Ce que ça fait* : partie neuve avec les mods actuels, menu pause → SAVE GAME → **`slot_14`** (ou `slot_10`/`slot_11`, sans dossier existant), quitter, relancer, LOAD GAME → ce slot. **Attendu : ça charge.**
- *Risque* : 🟡 uniquement si on choisit un slot qui contient une vraie partie (elle serait écrasée) : se limiter à 10, 11 ou 14, ou **sauvegarder d'abord** `saved_games\` et `persistent_data.xml` (copie hors du dossier du jeu).
- *Quand sauvegarder* : avions **libres** (aucun tenu par le frein), voir 3.5 ; pas d'autosave comme sauvegarde de test.
- *Fichiers touchés* : `saved_games\slot_14\save.xml` (nouveau), `persistent_data.xml` (la ligne du slot). *Retour* : supprimer le dossier `slot_14` créé, remettre `persistent_data.xml` depuis la copie (jeu fermé).

**E3 — Premier essai du démarrage automatique (🟡)**
- *Ce que ça fait* : pose le script dans `rom_0\scripts\library_custom_0.lua`, crée le mod interrupteur et coche-le, **tu** lances le jeu (ou le lanceur B) : au bout de ~30 s de menu, une partie neuve doit démarrer toute seule. Mesures utiles : (1) la commande est-elle acceptée **sans toucher une touche** (écran-titre) ? (2) délai minimal (`ATTENTE_S` : 30 → 10 → 5) ; (3) plante-t-il 1 fois sur 2 ?
- *Risque* : 🟡 écriture d'un fichier dans le dossier du jeu (il revient à 0 octet en une commande ; Steam « Vérifier l'intégrité des fichiers » le remet aussi à zéro ; une mise à jour du jeu peut l'écraser). Code Lua dans le bac à sable du jeu : pas d'accès disque ni réseau. Aucun exe ni DLL touché.
- *Fichiers touchés* : `library_custom_0.lua` (0 octet → script), `mods\cc2_demarrage_auto\` (nouveau dossier), `mods.xml` (une ligne).
- *Retour* : vider le fichier (sha256 de 0 octet `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`), décocher puis supprimer le dossier du mod, remettre `mods.xml` depuis sa copie.
- *Alternative plus sûre* : option D (clics simulés) — **sans** écrire dans le dossier du jeu, mais seulement quand tu es absent.
- *Si la commande est ignorée à l'écran-titre* : plan B = envoyer **une** touche (`touche_jeu.ps1`, fenêtre au premier plan seulement) ; plan C = D ; plan D = H (réserve).

**E4 — Mesurer le plantage au démarrage (🟢)**
- 10 lancements de partie neuve (A+B), on note à chaque plantage l'adresse du rapport Windows (`0x1EF518` ou `0x1EF525` ou autre). Tranche la section 3.4. Aucun fichier écrit en dehors du journal de l'outil.

## 6. Recommandation

1. **A + B sont prêts (section 6bis), non installés.** Quand le jeu est libre (les quatre conversations s'en servent) et que tu me le dis : premier lancement avec **toi** devant l'écran (E3 : la seule vraie inconnue est l'écran-titre).
2. **Au premier lancement réussi, fais E2** (SAVE dans `slot_14`) : tu auras une sauvegarde de test **chargeable** ; on bascule alors `MODE = "charger"`, si ça se révèle plus rapide/plus stable que la partie neuve (E4 le dira).
3. **E1 si tu veux la preuve** (5 minutes) ou si E2 plante (cela contredirait l'explication).
4. **Ne pas** viser le serveur dédié ni un plugin natif ; **garder** les clics simulés comme secours.

Décisions qui te reviennent au moment du premier essai : (a) OK pour écrire `library_custom_0.lua` (🟡) ; (b) OK pour le mod interrupteur (dossier dans `mods\` ; `armer` ajoute une ligne à `mods.xml`, 🟢) ; (c) slot de sauvegarde pour E2 (10, 11 ou 14) ; (d) quel jeu de mods pour le test (actuel : Gentle Missile Speed Buff, cc2_mesures, cc2_carte, cc2_modes).

## 6bis. Préparation faite (28/10, après ton accord) — **rien n'est installé ni lancé**

Accord reçu : « prépare l'installateur, le mod interrupteur et le lanceur avec relance, sans rien installer ni lancer tant que je n'ai pas validé le premier essai ». Voici ce qui est prêt dans `tour/etudes_demarrage_auto/` :

| Fichier | Rôle |
|---|---|
| `demarrage_auto.lua` | le script de menu (source) |
| `demarrage_auto.py` | installateur : `etat` (lecture seule), `installer`, `armer`, `desarmer`, `desinstaller` |
| `lancer_cc2.py` | lanceur avec relance automatique en cas de plantage |
| `test_demarrage_auto.py`, `test_lua_demarrage_auto.py` | tests hors jeu (63 + 14 contrôles, 0 échec) |
| `verifier_emplacements_sauvegardes.py` | prédit si une sauvegarde plantera au chargement |

**L'installateur** (`python -I demarrage_auto.py …`) :
- `installer` crée le dossier du mod `%APPDATA%\Carrier Command 2\mods\cc2_demarrage_auto\` (zone utilisateur, d'abord) puis écrit le script dans `rom_0\scripts\library_custom_0.lua` **seulement s'il est vide (0 octet)**, relit pour vérifier, et **n'ouvre pas `mods.xml`**. Refuse : jeu en cours (tout `carrier_command*.exe`, exe d'essai compris, ou impossible à vérifier) ; fichier de rom_0 non vide ; dossier du mod déjà là ; numéro de `library_custom` déjà fourni par un autre mod (y compris Workshop). En cas d'erreur en cours de route : fichier de rom_0 remis à 0 octet, dossier retiré.
- Options : `--rom N` (0 par défaut), `--mode nouvelle|charger`, `--partie N`, `--attente S` (30), `--attendre-touche` (le compte à rebours ne démarre qu'après l'écran-titre : plan B si la commande est ignorée sans touche), `--date`.
- `armer` / `desarmer` ajoutent / retirent **une seule ligne** de `mods.xml` (sauvegarde datée jamais écrasée, forme du fichier vérifiée, XML revalidé) : c'est l'équivalent de cocher/décocher dans le menu MODS du jeu.
- `desinstaller` remet **tous** les fichiers de rom_0 qui portent la marque de l'outil à 0 octet (sha256 vérifié), décoche, supprime le mod ; **ne vide jamais** un fichier qui n'est pas le sien ; garde le dossier du mod s'il contient autre chose que ses fichiers ou s'il est encore cité par `mods.xml`.
- Écrit uniquement : le fichier de rom_0, le dossier du mod, et (pour `armer`/`desarmer`) `mods.xml` et sa sauvegarde.

**Le lanceur** (`python -I lancer_cc2.py`) lance par Steam (ou `--exe` pour une exe d'essai, directement), surveille 180 s ; si le jeu s'arrête **et** que Windows a écrit un rapport de plantage, il note le code et l'adresse (en signalant `0x1EF518`/`0x1EF525`) puis relance (3 essais au plus) ; un arrêt sans rapport = pas de relance (tu l'as fermé). Il affiche d'abord si le script est posé et si l'interrupteur est coché (`--a-blanc` : vérifie sans rien lancer). Seul fichier écrit : `%LOCALAPPDATA%\cc2_demarrage_auto\lancements.log`.

**Déroulé du premier essai (E3), à ton signal, jeu fermé et libre** :
1. `python -I tour/etudes_demarrage_auto/demarrage_auto.py etat` (rien à signaler : 10 fichiers vides, mod absent).
2. `… installer` puis `… armer` (ou cocher « Demarrage auto » dans MODS).
3. `python -I tour/etudes_demarrage_auto/lancer_cc2.py` **avec toi devant l'écran** : compte à rebours orange en bas à gauche du menu ; à 0, une partie neuve doit démarrer. Si un message rouge « commande envoyée … ignorée » reste affiché : l'écran-titre bloque ; fais `desinstaller` puis `installer --attendre-touche` et recommence (une touche à l'écran-titre, puis 30 s).
4. Ce qu'on relève : commande acceptée sans touche ? délai minimal (`--attente` 30 → 10 → 5) ? plantage (journal du lanceur) ?
5. Retour arrière à tout moment, jeu fermé : `… desinstaller`.
6. **Suspect en cas de plantage au premier essai** (info de la conversation « modes carburant », 28/10) : le plugin d'observation `cc2x_modes.dll`, posé dans `mods\cc2_modes\content\cc2x\` et chargé à chaque lancement tant que `cc2_modes` est coché ; jamais tourné dans le vrai jeu avant. Retrait : `python tour/etudes_modes_carburant/mod_modes.py retirer-plugin` (jeu fermé). Si le premier essai plante, relever l'adresse (journal du lanceur) avant de l'accuser : `0x1EF518`/`0x1EF525` = le plantage déjà connu, une autre adresse = autre cause (peut-être ce plugin). Un seul jeu à la fois : prévenir « modes carburant » avant de lancer.

**Risques de cette préparation** : 🟢 aucun pour le disque tant que rien n'est installé (les tests n'ont touché qu'un faux dossier, supprimé ensuite). L'installation réelle reste le point 🟡 décrit en section 5 (E3), avec retour arrière vérifié par les tests.

## 7. Annexes

**Vérifications faites** (toutes hors jeu). (1) `demarrage_auto.lua` passe la vérification de syntaxe (`lua_sonde.py syntaxe`) et **14 contrôles** (`test_lua_demarrage_auto.py`) dans un vrai interpréteur Lua avec de faux appels du jeu : rien avant 30 s, une seule commande `new_game_custom` après, compte à rebours affiché, message de diagnostic qui reste si la commande est ignorée, un second contexte est bloqué par le verrou, mod décoché → aucune commande ni affichage, contexte de partie → aucune accroche, `charger` → `load_game:19`, slot absent → rien, attente réglable, option « attendre l'écran-titre ». Ces essais prouvent la **logique d'accrochage**, pas le comportement réel du jeu (même limite que `lua_sonde.py`). (2) `test_demarrage_auto.py` : **63 contrôles** sur un faux dossier du jeu et de données (voir 6bis). Aucun fichier réel n'a été lu ou écrit par ces tests.

**Sources lues** : `tour/auto/LISEZ-MOI.md`, `library_custom_5.lua`, `essai_auto.py`, `essai_auto_reessais.py`, `entree_jeu.ps1`, `passation_windows/JOURNAL_tour.md` (entrées des 27/10), `outil/tests_en_jeu/`, `envoi_native_bridge/session_lifecycle_analysis.md`, SDK CC2X (`passation_windows/sdk_public_cc2x/`) ; `rom_0\scripts\screen_menu_main.lua`, `library_ui.lua`, `library_util.lua`, `library_enum.lua`, `game_objects\vehicle_chassis_*.xml` (jeu et Revolution), notes des autres conversations (dossier de notes partagé) ; réponses du Mac du 28/10 (`REPONSES_mac_pour_la_tour_28-10.md`, branche `origin/mac/reponses-tour-28-10`, Q4 et Q5).

**Désassemblage** : copie d'origine du dépôt (`tour/sauvegardes/carrier_command_1.5.18_original.exe`), avec `tour/outils/desasm.py` ; le vrai exe du dossier du jeu n'a pas été ouvert.

**Limites** : la correspondance indice de définition → fichier est sûre pour le porte-avions, supposée pour les autres modèles ; le rôle exact de `0x7754d0` (autre appelant de `0x7764e0`) n'est pas établi ; tout ce qui concerne l'écran-titre sans touche sur Windows et le plantage des parties neuves est **non vérifié** ; la cause Revolution du plantage au chargement est confirmée par le code des deux plateformes et par les données, mais **jamais vue en jeu** (ni sur Windows, ni sur le Mac).

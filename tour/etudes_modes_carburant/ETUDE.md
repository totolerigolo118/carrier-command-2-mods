# Étude — Modes ÉCO / NORMAL / FLANK par avion (carburant et vitesse)

> **ÉTAT À LA PASSATION (30/10/2026) : lire d'abord `PASSATION.md`** (même dossier) : ce qui est posé (onglet v2.1 + plugin v3.1), les résultats en jeu (ÉCO validé, garde-fou validé, FLANK décevant : aucun gain sur l'Albatros, oscillation du Manta au-dessus de ~222 m/s), ce qui attend l'accord du moddeur, les commandes, les pièges. Ce fichier-ci est l'étude détaillée (sections 0 à 18, la plus récente en bas : §16 à §18 = les essais en jeu du 30/10).

Écrite le 27/10/2026 par une conversation « étude » de la tour. **Lecture seule** : le jeu n'a pas été lancé, `carrier_command.exe`
(`8E7FCBB6…`), `mods.xml`, `dinput8.dll`, `cc2x_frein.dll` et `frein.ini` n'ont pas été touchés. Seules écritures : ce dossier et un
petit script de lecture dans le dossier temporaire de la session.

**Suite (même jour, après ton choix « l'onglet de l'avion » et ton « go pour le plan »)** : j'ai ajouté dans ce dossier, **sans rien
installer ni toucher au jeu**, `variantes_onglet.html` (6 variantes de l'onglet, couleurs et mots au choix), `lua/` (deux scripts
prêts : mesure en lecture seule et onglet « sans effet ») et `mod_modes.py` (installateur à sauvegarde et retrait, essayé sur une
fausse copie). Voir la section 7.

---

## 0. Résumé en français simple (à lire en premier)

**Ton idée** : pour chaque avion, trois modes, ÉCO (il économise le carburant), NORMAL (comme aujourd'hui), FLANK (pleine vitesse),
choisis soit par trois cases, soit par un petit onglet qui s'allume quand on clique sur l'avion.

**Réponse courte : oui, c'est faisable, mais en deux morceaux de nature très différente.**

1. **L'affichage (cases ou onglet)** : c'est un mod Lua. Sûr (🟢), retirable en enlevant une ligne de `mods.xml`. Le jeu a déjà, quand on
   clique sur un avion, un panneau avec son carburant en % et des cases à cocher : on peut y ajouter un onglet « SPEED » dans le même style.
2. **L'ordre de vitesse** : **impossible en Lua pur.** J'ai relu la liste des commandes d'écriture que le jeu donne aux scripts (21 commandes) :
   il n'y a **aucune** commande « vitesse », « gaz » ou « carburant » pour un avion (seulement : ordres de déplacement, altitude d'un point
   de passage, tenir le feu, lumière faible, armement…). Il faut donc un petit morceau de code natif dans le jeu. Le moins risquable ici :
   **un plugin DLL de plus** avec le chargeur (SDK) déjà installé pour le frein d'atterrissage : on le retire en supprimant un fichier,
   l'exécutable n'est pas touché (🟡). L'autre voie, retoucher l'exécutable comme pour l'ascenseur ×2, marche aussi mais elle est plus
   étroite et plus délicate (🟡/🔴).

**Un « éco » économise-t-il vraiment ?** Oui en principe : le carburant brûlé à chaque instant est **proportionnel aux gaz** du moteur
(manette), et les gaz suivent la vitesse demandée. Plus lent = moins de gaz = moins de carburant par seconde, et (si la résistance de
l'air croît comme le carré de la vitesse, ce qui reste à mesurer) aussi moins de carburant **par kilomètre** (environ −33 % à 80 m/s
au lieu de 120).

**Mais une découverte change le plan** : mesuré sur le Mac le 25/10, les avions sous IA ne croisent **pas** à 48 / 72 m/s mais à
**≈ 120 m/s** quand le point est loin. Les « planchers » 48 / 72 ne jouent qu'**à moins de ~800 m du point** (patrouille, escorte,
approche). Donc des modes qui ne changent que les planchers (ce que le Mac avait fait) **ne changent presque rien en vol de transit**.
Pour que ÉCO économise et que FLANK aille plus vite en transit, chaque mode doit aussi fixer la **vitesse de croisière** (le 120).
J'ai retrouvé sur Windows les deux endroits (planchers et 120), voir l'annexe.

**FLANK dépasserait-il la vitesse actuelle ?** Probablement oui : à 120 m/s les avions sont **régulés** (120,1 et 121,7 mesurés), donc leur
moteur n'est pas à fond ; il reste une marge. De combien, **on ne le sait pas** : il faut une mesure (étape 0).

**Mode retenu par avion ?** Possible (mémoire + petit fichier). Comme **NORMAL = jeu d'origine**, si le jeu oublie le mode (rechargement,
avion mort), l'avion reprend simplement le comportement normal : l'oubli est sans danger. Aujourd'hui on ne peut de toute façon pas
tester le rechargement (le plantage au chargement d'une sauvegarde est connu).

**Multijoueur** : le serveur (l'hôte) dicte la simulation. Le mode n'agit que **chez l'hôte** ; un invité n'a ni le plugin ni le droit
de commander. Jamais testé avec un 2e joueur.

**Ma recommandation (par étapes, un seul changement testé à la fois)** : mesurer d'abord (🟢), choisir l'interface sur maquette (🟢),
l'essayer « sans effet » (🟢), puis seulement brancher l'ordre de vitesse par un plugin DLL (🟡), un avion à la fois.

**Ce que je te demande** : (a) quelle interface (maquette 1, 2 ou 3, section 4) ; (b) jusqu'à quel niveau de risque on va (🟢 seulement
mesurer et dessiner ; 🟡 plugin retirable).

---

## 1. Ce qui a été lu (et ce que j'ai vérifié moi-même)

Lu : `DEMARRER_cc2_patchs.md` (sections 3, 5, 6 point 9), `etudes/ia_vitesse.md`, `partage_detail/05_ai_wing_speed_fuel.txt`,
`partage_detail/07_lua_api_and_hooks.txt`, `passation_windows/PASSATION_windows.md` (étape 6, pièges), `passation_windows/JOURNAL_tour.md`
(fin), `passation_windows/lua_a_installer/library_custom_6.lua` (la barre ECO/NORMAL/FLANK du Mac), `tour/etape1/TABLEAU_mac_windows.md`,
`tour/atterrissage_manuel/VERDICT_relecture_SDK.md` et la fin du journal du frein, la doc du SDK (`docs/LUA_API.md`,
`src/lua_world.c`, copie figée hors dépôt), les scripts du jeu `screen_vehicle_control.lua`, `vehicle_hud.lua`, `screen_propulsion.lua`,
`constants.txt`, `vehicle_chassis_wing_small.xml`, et la note de la conversation « missiles » (rien de commun avec ce sujet).

Vérifié par moi **sur la copie d'origine de l'exécutable Windows** (`tour/sauvegardes/carrier_command_1.5.18_original.exe`, lecture seule,
désassemblage capstone) : les planchers 48 / 72 / 144 et la vitesse de croisière 120 (annexe A). Vérifié dans l'exécutable : la liste
complète des commandes `set_*` du Lua (annexe B).

Sur la tour, **Revolution n'est plus actif** (`mods.xml` : missiles, `cc2_mesures`, `cc2_carte`) : l'écran de contrôle des véhicules est
donc celui du jeu d'origine, que j'ai lu.

---

## 2. Comment le jeu règle la vitesse d'un avion sous IA

Pour un avion qui vole vers un point (Albatros = petit, Manta = gros), cinq étapes à chaque tick (30 par seconde) :

1. **Vitesse demandée S** : en vol normal l'IA ne demande rien (0). Le programme remonte ce 0 à un **plancher** : **48 m/s Albatros,
   72 m/s Manta**, plafond 144. (Au combat l'IA demande 160 ; au retour, dans le circuit d'atterrissage, le bateau impose 80 m/s : les
   modes ne doivent rien changer là.)
2. **Vitesse visée T = S + a × (120 − S)**, où *a* monte de 0 (à 20 m du point) à 1 (à ~800 m et plus). Donc **loin du point, T = 120
   quel que soit S** ; près du point, T = S (le plancher).
3. **Régulateur de gaz** (comme un régulateur de vitesse de voiture) : gaz += raideur × ((T − vitesse) / 120 − …), bornés entre 0 et 1.
4. **Poussée** : le niveau réel du moteur suit les gaz à 0,05 par tick ; force = 10 × puissance du moteur × niveau (Albatros 50,
   Manta 100, même masse de 1 t).
5. **Carburant** : à chaque tick, brûlé = gaz × consommation du type (Albatros 2, Manta 5) × 0,008. Réservoirs 800 (Albatros) et 1200 (Manta).
   Les équipes IA adverses ne consomment pas de carburant ; la tienne, si.

**Ce que ça donne en chiffres** (calcul sur la formule, gaz = 100 % de la manette) :

| | Albatros | Manta |
|---|---|---|
| Carburant brûlé à pleins gaz | 0,48 par seconde | 1,2 par seconde |
| Autonomie à pleins gaz | ≈ 28 min | ≈ 17 min |
| Autonomie à *x* % de gaz | 28 min ÷ *x* | 17 min ÷ *x* |

Exemple : à 50 % de gaz, 55 min (Albatros) et 33 min (Manta), ce qui retombe sur les chiffres de `etudes/ia_vitesse.md`.

**À retenir** :
- La consommation dépend de la **vitesse seulement par les gaz**. Ce que l'on ne connaît pas, c'est *combien de gaz il faut pour tenir
  120 m/s* (ou 80, ou 144). C'est le chiffre qui décide de tout et il n'a **jamais été mesuré**.
- Les formules viennent du Mac (désassemblage). Sur Windows j'ai retrouvé les mêmes constantes (`wing_light_fuel_consumption`,
  `fuel_consumption_multiplier` sont dans l'exécutable) et le même régulateur (annexe A), mais **la formule du carburant n'a pas été
  relue sur Windows** : la mesure de l'étape 0 la confirmera.

---

## 3. Réponses aux questions clés

### 3.1 Un « éco » réduirait-il vraiment la consommation ?
Oui, par les gaz. Deux conditions :
- le mode doit agir **en transit**, donc fixer la vitesse de croisière (le 120), pas seulement les planchers ;
- le gain par kilomètre dépend de la loi de résistance de l'air du jeu (inconnue). Si elle croît comme le carré de la vitesse (cas
  habituel) : 80 m/s au lieu de 120 = environ 44 % des gaz, soit **−56 % de carburant par seconde** et **−33 % par kilomètre**, pour
  50 % de temps de vol en plus. Si la loi est différente, le gain peut être plus faible, voire nul : à mesurer.

### 3.2 Un « flank » dépasserait-il la vitesse actuelle ?
Probablement : les avions sont régulés à ≈ 120 m/s en transit, donc pas à fond. Vitesse maximale réelle, inconnue. Si elle est de
144 m/s, le coût est environ +44 % de gaz, +20 % de carburant par km et −17 % de temps. Autres effets à connaître : virages beaucoup
plus larges à grande vitesse (rayon ∝ vitesse²) : l'avion peut dépasser son point et tourner autour ; la vitesse du plafond (144) ne
joue que sur le plancher, pas sur la croisière.

### 3.3 Mod Lua, patch de l'exécutable ou DLL ?

| Voie | Ce que ça permet | Retrait | Risque | Remarques |
|---|---|---|---|---|
| **Mod Lua seul** | l'interface, la lecture (vitesse, carburant), un journal dans `cc2x.log` | enlever la ligne de `mods.xml` | 🟢 | **aucun ordre de vitesse possible** (annexe B). Lua ne tourne que quand un écran est allumé : pas de « tâche de fond » |
| **Mod de données** (`constants.txt` / XML) | changer la consommation ou la puissance moteur, **fixe** | idem | 🟢 | pas de modes. Touche tous les avions du type (puissance moteur : ennemis compris). Plan B « éco permanent » |
| **Plugin DLL** (SDK déjà installé) | ordre de vitesse **par avion** + fonction Lua pour l'interface | supprimer le fichier de la DLL (exécutable intact) | 🟡 | du code natif dans le jeu : un bogue = plantage. Chaîne déjà éprouvée avec `cc2x_frein.dll` (relue, compilée par nous). Les crochets sauvent `xmm0–7` (déjà écrits et testés dans `extension_windows/`) |
| **Patch de l'exécutable** | idem | `patch_exe.py retirer`, jeu fermé | 🟡/🔴 | il faut loger le code : ~290 octets libres sans agrandir la section (1,3 Ko en la modifiant), et l'exécutable est relogé en mémoire (ASLR) : toute adresse écrite doit figurer dans la table de translation. Le Mac avait 671 octets de greffe |

**Écriture directe du champ « vitesse visée »** (`control_speed`, `+0x1f8`, la « voie a » de la passation) : **à écarter**. Je l'ai
confirmé sur Windows : le programme l'écrit à 0x71a0de et le relit à 0x71ddec **dans la même grande fonction** (aucun bourrage entre les
deux adresses), avant que le plugin ne puisse passer. L'écriture du plugin serait donc écrasée au tick suivant. La seule vraie voie est le **crochet** sur les planchers et la croisière.

**Variante à étudier plus tard (non vérifiée)** : un ÉCO « plafond de gaz » : le plugin ramène chaque tick le champ `control_power` à
*x* %. Plus simple (pas de crochet au milieu d'une fonction), mais il se bat avec le régulateur et l'effet sur le carburant est partiel
(le tick suivant le régulateur remonte un peu les gaz avant le calcul du carburant). Utile comme premier essai du plugin, pas comme
solution finale. L'étape 0 dira si `control_power` d'un avion IA suit bien les gaz.

### 3.4 Le mode choisi doit-il persister par avion ?
Oui, c'est raisonnable : un tableau « numéro d'avion → mode » dans le plugin (jusqu'à ~256 avions).
- **Version 1 (recommandée)** : en mémoire seulement ; au démarrage tout est NORMAL = jeu d'origine. Rien à sauvegarder, aucun risque
  de coincer une partie.
- **Version 2 (si tu le veux)** : un petit fichier texte « numéro : mode » à côté des sauvegardes. À prévoir : le même numéro d'avion
  peut désigner un autre avion dans une autre partie (le fichier doit donc se rattacher à une partie, ce qu'on ne sait pas faire
  proprement aujourd'hui). Et on ne peut pas encore tester le chargement d'une sauvegarde (plantage connu).
- Chaque écran de contrôle du pont a son **propre** monde Lua : l'état ne peut pas vivre dans un script. Il vit dans le plugin et les
  trois écrans le lisent (c'est ce que faisait déjà `cc2_vitesse` sur le Mac).

### 3.5 Multijoueur
- La simulation tourne chez l'hôte. Le plugin et le tableau des modes sont donc **chez l'hôte seulement**. Pour un invité,
  la doc du SDK dit que les commandes « ne font rien » : il ne peut pas régler les modes de sa propre escadrille.
- Les invités verraient les avions plus vite / plus lents (positions envoyées par le serveur), **sans** l'interface s'ils n'ont pas
  le mod (par déduction, jamais testé avec un 2e joueur).
- Un plugin DLL n'est pas envoyé aux invités ; un mod Lua de `mods.xml` l'est parfois (système de mods).
- Il faut limiter l'effet à **ton équipe** (les avions ennemis restent d'origine), comme prévu sur le Mac.

---

## 4. Où dessiner dans le jeu, et trois maquettes

### 4.1 Ce que le jeu offre (écrans de contrôle des véhicules `screen_veh_l/m/r`, script `screen_vehicle_control.lua`)

| Endroit | Fonction (ligne) | Ce qui y est déjà |
|---|---|---|
| **Panneau d'un avion cliqué** | `render_selection_vehicle` (346) | fenêtre STATUS (PV, **FUEL %**, AMMO %, actions : tenir le feu, lumière faible, centrer, caméra, autodestruction), fenêtre LOADOUT à droite (74 de large). **Sous le LOADOUT l'espace est libre.** |
| Liste « DEPLOYED » du porte-avions | `ui_render_selection_carrier_vehicle_overview` (228) | grille de 6 colonnes, cases d'environ 24 × 16, trois fines barres (réparation, carburant, munitions) |
| Carte | boucle d'affichage des véhicules (~l. 1780-1880) | icône d'avion + minuscules pastilles (carburant bas, munitions basses, tenir le feu) |
| Pilotage | `vehicle_hud.lua` | jauges carburant, gaz, vitesse, **seulement quand tu pilotes** |

Lire le carburant : `vehicle:get_fuel_factor()` (déjà utilisé). Aucune commande de vitesse (voir 3.3). L'écran logique fait 256 × 256 unités.
`render_selection_vehicle` est une fonction globale : un fichier `library_custom_N.lua` peut l'envelopper (même technique que la barre
du Mac) sans remplacer le script du jeu ; prévoir un repli si Revolution revient.

### 4.2 Maquette 1 — « L'onglet de l'avion » (ta 2e idée), ma préférée

Clic sur un avion de la carte : en plus de ses fenêtres, un onglet **SPEED** apparaît sous LOADOUT, trois gros boutons, celui du mode
actif allumé (vert / cyan / orange). En option, l'autonomie estimée en dessous.

```
+-- STATUS ---------------------+  +-- LOADOUT ---+
| HP            40/40           |  |  armement    |
| FUEL          63 %            |  |              |
| AMMO          100 %           |  +-- SPEED -----+
| -- ACTIONS --                 |  | [ ECO     ]  |  vert
|  [x] Hold fire                |  | [ NORMAL  ]  |  cyan  <- allumé
|  [ ] Low light                |  | [ FLANK   ]  |  orange
|  Center / Camera / Self-dest. |  | autonomie    |
+-------------------------------+  | ~ 21 min     |
                                   +--------------+
```
Plus : une **pastille de couleur** près de l'icône sur la carte pour voir d'un coup d'œil les avions qui ne sont pas en NORMAL.
Points forts : boutons gros (faciles à viser), look du jeu, manette utilisable, un avion à la fois. Défaut : un clic de plus pour
régler tout l'escadron.

### 4.3 Maquette 2 — « Trois cases par avion » (ta 1re idée)

Un petit tableau en bas à droite de l'écran, une ligne par avion en l'air, trois cases E / N / F par ligne :

```
                 +-----------------------------+
                 | SPEED            E    N   F |
                 | Albatros 9      [ ]  [#]  [ ]|
                 | Albatros 10     [#]  [ ]  [ ]|
                 | Manta 11        [ ]  [ ]  [#]|
                 +-----------------------------+
```
Points forts : on voit et on change tous les avions d'un coup. Défauts : les cases sont petites (environ 12 × 9 unités) donc dures à viser
à la mire ; avec 8 avions le tableau cache la carte et l'échelle de la carte (bas droite). Dans la liste « DEPLOYED » les cases du jeu
(24 × 16) sont **trop petites** pour y mettre trois boutons : seule une lettre colorée y tient, pour l'affichage.

### 4.4 Maquette 3 — « Barre de l'escadron + exception par avion »

La barre du Mac (SQUADRON SPEED : ECO / NORMAL / FLANK, en bas à droite) règle **tous** les avions d'un clic ; un clic sur un avion ouvre
l'onglet de la maquette 1 avec un 4e bouton « SUIT L'ESCADRON » pour une exception.

```
 carte ...                    SQUADRON SPEED [ECO] [NORMAL] [FLANK]
 clic sur un avion ->  onglet SPEED: ECO / NORMAL / FLANK / [x] SUIT L'ESCADRON
```
Points forts : rapide pour tous, précis pour un. Défaut : deux niveaux à comprendre, plus de code (la barre existe déjà côté Mac,
`library_custom_6.lua`, à adapter à la fonction du plugin).

**Mon avis** : maquette 1 d'abord (avec la pastille sur la carte), maquette 3 plus tard si tu veux le raccourci « tous ». Quand tu auras
choisi la famille, je te fais la page HTML de 4 à 6 variantes numérotées (couleurs, tailles) comme d'habitude.

---

## 5. Plan par étapes, risques et alternatives plus sûres

Règles : un seul changement testé à la fois ; **jamais** lancer ou fermer le jeu sans ton accord dans le message en cours ; **un seul
jeu à la fois sur le PC** : l'étude d'atterrissage utilise le jeu (`dinput8.dll`, `cc2x_frein.dll`, `frein.ini`) ; je lui demanderai
par message avant tout besoin du jeu, et je ne toucherai pas à ces fichiers.

| # | Étape | Ce que ça fait | Risque | Alternative plus sûre |
|---|---|---|---|---|
| 0a | **Vol de contrôle à la main** (toi) | tu pilotes un Albatros à 30 %, 60 %, 100 % de gaz ; on note vitesse, carburant perdu par minute | 🟢 aucun fichier | — |
| 0b | **Mod « télémétrie »** (lecture seule) | toutes les 5 s, écrit dans `cc2x.log` (journal du SDK, tant que son chargeur est posé comme pour le frein) vitesse, vitesse visée, gaz, carburant de chaque avion de ton équipe ; je lis le fichier après. Ajoute **une ligne à `mods.xml`** (accord requis) et un dossier de mod | 🟢 : rien ne sort du PC ; le seul risque est un bogue Lua qui masquerait un écran (protégé, retrait = enlever la ligne) | 0a seul, sans mod |
| 1 | **Maquette HTML** (4-6 variantes) | page de dessins, rien dans le jeu | 🟢 | — |
| 2 | **Interface « sans effet »** (mod Lua) | l'onglet SPEED s'affiche et s'allume, mais ne commande rien (étiquette « maquette ») : pour juger lisibilité, taille, manette | 🟢 (même risque Lua que 0b) | rester sur la maquette HTML |
| 3a | **Plugin `cc2x_vitesse.dll`** (SDK installé) | relire les sites (identifiés, annexe A), écrire un crochet qui, **pour tes avions seulement**, choisit plancher et croisière selon le mode ; tester hors jeu ; poser avec ton accord | 🟡 : code natif dans le jeu (bogue = plantage ; avion bloqué ? pas de mort possible hors partie) ; retrait = supprimer la DLL | **3c** (plafond de gaz) ou **mod de données** |
| 3b | Patch de l'exécutable | même chose en retouchant `carrier_command.exe` | 🟡/🔴 (modification de l'exécutable, table de translation, peu de place) | 3a |
| 3c | **Premier essai « plafond de gaz »** (plugin minimal) | ÉCO = gaz plafonnés à *x* % par le plugin ; pas de crochet | 🟡 (plugin natif, mais très court) | mod de données (consommation réduite pour tous) |
| 4 | **Essais en jeu par paliers** | (i) un avion loin, ÉCO puis FLANK, mesures de 0b ; (ii) les 3 modes ; (iii) interface reliée au plugin | 🟡 (jeu avec le plugin ; partie neuve jetable) | s'arrêter à (i) |
| 5 | Persistance fichier, pastille carte, autonomie estimée | confort | 🟢/🟡 | rester en mémoire seulement |
| 6 | Multijoueur | seulement si tu le demandes | — | non prévu |

Durées indicatives : étape 0 une session + 20 min de ton temps ; 1 une demi-session ; 2 une session ; 3a deux à trois sessions ;
4 une à deux sessions ; 5 une session.

**Ordre conseillé** : 0 → 1 → 2 → 3c ou 3a → 4 → 5. **L'étape 0 est la plus utile** : sans elle on ne sait pas dire de combien ÉCO
économise ni jusqu'où FLANK va, et on risquerait de régler des modes à l'aveugle.

---

## 6. Ce qui n'est pas prouvé

- La loi gaz ↔ vitesse (donc le gain d'ÉCO et la marge de FLANK) : **jamais mesurée**, ni sur Mac ni sur Windows.
- La formule du carburant : vue sur le Mac, présumée identique sur Windows (constantes présentes).
- L'allure réelle du jeu d'origine sur Windows : **rien de vitesse n'a été mesuré sur la tour**.
- Que `cc2x.vehicle(id).id` du SDK soit le même numéro que `vehicle:get_id()` du Lua d'écran (très probable, à vérifier à l'étape 0b).
- Que `vehicle:get_linear_speed()` et `get_throttle_factor()` marchent sur les véhicules de la carte (on ne les voit utilisés que sur le
  véhicule piloté) ; repli : vitesse déduite de la position, gaz déduits du carburant perdu.
- Que l'enveloppe de `render_selection_vehicle` s'affiche proprement (fenêtres du jeu, manette) : à essayer à l'étape 2.
- Les effets d'un avion trop rapide (virages, décrochage, dégâts) : inconnus.
- Le multijoueur : déduit, jamais testé.
- Le plantage au chargement d'une sauvegarde (connu, sans rapport) empêche de tester le rechargement.

---

## 7. Suite après ton « go » (onglet de l'avion) : ce qui est prêt, ce qui attend ton accord

### 7.1 Prêt, rien d'installé (🟢, aucun fichier du jeu touché)

| Quoi | Fichier | Ce que c'est |
|---|---|---|
| Étape 1 | `variantes_onglet.html` | 6 variantes de l'onglet SPEED (liste de 3 boutons, bouton qui tourne, 3 cases E/N/F, curseur, gros boutons expliqués, flèches ‹ ›), avec 3 jeux de couleurs et 3 jeux de mots à essayer |
| Étape 0b | `lua/library_custom_3.lua` | **mesure en lecture seule** : toutes les 5 s, pour chaque avion de ton équipe en l'air, écrit dans `cc2x.log` l'identifiant, la position, la vitesse, le carburant, `control_speed`, `control_power`, plus ce que l'API des écrans du jeu donne (`get_fuel_factor`, `get_linear_speed`, `get_throttle_factor`, « - » si absent). Rien d'autre |
| Étape 2 | `lua/library_custom_5.lua` | **onglet « sans effet »** : sous LOADOUT, trois boutons ECO / NORMAL / FLANK, le dernier cliqué s'allume, un texte rouge « MAQUETTE : SANS EFFET ». Ne commande rien. Si son dessin plante, il remet les piles de l'interface du jeu en ordre et se coupe seul |
| Installation | `mod_modes.py` | copie les scripts dans `%APPDATA%\Carrier Command 2\mods\cc2_modes\`, sauvegarde `mods.xml` (datée), y ajoute **une** ligne ; `retirer` défait tout. Réutilise `tour/outils/mod_mesures.py` sans le modifier. **Essayé sur une fausse copie** (installation, ajout du 2e script, 2e installation refusée, retrait) : `mods.xml` revenu identique (sha256). Jamais lancé sur le vrai dossier |

Limites connues de l'onglet « sans effet » (à juger, pas à corriger maintenant) : souris seulement (pas encore la manette), le choix
n'est **pas** partagé entre les 3 écrans de contrôle (chacun a son propre Lua) ni gardé d'une partie à l'autre ; ces deux points se
règlent quand le plugin tiendra les modes (étape 3).

**Non testé** : aucun interpréteur Lua sur ce PC, donc les deux scripts n'ont été relus qu'à la main (contre `library_ui.lua` et
`screen_vehicle_control.lua` du jeu, même technique que `cc2_mesures` / `cc2_carte` qui marchent). Un vrai Lua 5.3 existe via
`pip install lupa` (déjà utilisé par les tests de la tour) : à ne faire qu'avec ton accord (voir 7.2).

### 7.2 Ce qui demande ton accord, un par un (rien n'est fait)

| # | Action | Ce que ça fait | Risque | Alternative plus sûre |
|---|---|---|---|---|
| A | `pip install lupa` | télécharge un paquet depuis PyPI (un interpréteur Lua pour Python) pour essayer les 2 scripts hors du jeu | 🟡 code téléchargé d'Internet, mais très répandu ; il ne touche ni au jeu ni à `mods.xml` | ne pas l'installer : relecture à la main + essai en jeu protégé par `pcall` |
| B | Poser la **mesure** (`mod_modes.py installer --etape mesure`) | crée le dossier `mods\cc2_modes` et ajoute **une ligne** à `mods.xml` (sauvegarde datée avant) ; le jeu ne doit pas tourner | 🟢 lecture seule, rien ne sort du PC ; seul risque : un bogue Lua (protégé), retrait = `retirer` | vol de contrôle à la main sans mod (0a seul) |
| C | Ajouter l'**onglet sans effet** (`mettre-a-jour --etape interface`) | copie `library_custom_5.lua` dans le dossier du mod ; `mods.xml` non touché ; effet au prochain lancement du jeu | 🟢 (même risque Lua que B) | rester sur la maquette HTML |
| D | **Lancer le jeu** pour l'étape 0a / 0b / 2 | une seule partie à la fois sur le PC : l'étude d'atterrissage utilise aussi le jeu. Le chargeur du SDK charge aussi `cc2x_frein.dll` (frein actif près du sol, `brake_enabled=1`) : sans effet sur un vol de croisière | 🟢 | — |

**Protocole de l'étape 0a (toi, 20 min)** une fois B posé : partie neuve jetable, sortir un Albatros, le piloter à la main à 30 %,
60 % puis 100 % de gaz (~1 min chacun, en palier, loin du bateau), puis laisser un avion IA voler vers un point lointain (2 min) ;
je lis `cc2x.log` ensuite. On en tire : vitesse selon les gaz, carburant perdu par minute, et si `get_linear_speed` /
`get_throttle_factor` marchent sur les avions de la carte. **C'est cette mesure qui dit de combien ÉCO économise et jusqu'où FLANK va.**

---

## 8. Première mesure en jeu (28/10/2026, partie neuve, ~27 min de jeu) : ce qu'on sait maintenant

Données : `mesures/2026-10-28_partie1_CC2MODES.csv` (24 641 lignes, 5 avions : Albatros 9, 10, 103 ; Manta 17, 18). Mod `cc2_modes` posé le
27/10 (mesure + onglet « sans effet »), **aucune erreur Lua** (0 ligne `CC2MODES|E` ni `CC2MODES|UI`), l'onglet s'affiche bien sous LOADOUT
(capture du moddeur). **L'avion 9 a été piloté à la main de t ≈ 1300 à 1570 s** (gaz lus 1,00 / 0,63 / 0,70 / 0,41 ; deux touchers du pont à 83 puis
69 m/s relatifs, donc jamais freinés : le frein n'agit que sous 30 m/s relatifs). Pas de vrais paliers de gaz propres (30 / 60 / 100 % tenus en palier).

| Mesuré | Valeur | Lecture |
|---|---|---|
| Croisière IA, Albatros | **119,1 m/s**, 0,282 carburant/s, gaz lus 0,92 | cohérent avec le Mac (≈ 120). `control_speed` reste à 48 (le plancher), la vitesse réelle vient de la croisière 120 du code |
| Croisière IA, Manta | **121,7 m/s**, 0,356 carburant/s | idem, `control_speed` 72 |
| Carburant selon les gaz (Albatros 9 à la main) | 1,00 → **0,304 /s** ; 0,92 → 0,28 ; 0,70 → 0,21 ; 0,63 → 0,19 ; 0,41 → 0,10 | **le carburant est proportionnel aux gaz** : ≈ **0,30 × gaz par seconde** (réservoir 800 → ~44 min à pleins gaz, et non 28 min comme calculé d'après le Mac ; le coefficient Windows est ≈ 0,63 fois celui qu'on avait déduit) |
| Vitesse max Albatros à pleins gaz | **130-135 m/s** en vol presque horizontal (avion 9 à la main t = 1370-1410 ; avion 10 en IA t = 1125-1225) | FLANK ne ferait gagner qu'**≈ 10-13 %** de vitesse à l'Albatros (la croisière IA utilise déjà ~93 % de la poussée) pour ≈ +7 % de carburant par seconde |
| Manta | croisière à ~47 % de la poussée (0,356 / 0,76 par seconde à pleins gaz) ; pointes vues : 176-181 m/s en piqué | marge de FLANK **bien plus grande** pour le Manta (de l'ordre de +40 %, à confirmer en palier) ; même poussée nécessaire à 120 m/s pour les deux types (~465 en unités du jeu : Albatros 0,93 × 500, Manta 0,47 × 1000) |
| Vol en rond au plancher (orbite) | Albatros **52,4 m/s : 0,193 /s** (~0,65 de gaz) ; Manta **88,1 m/s : 0,695 /s** | un avion qui attend brûle presque autant qu'en croisière ; **au plancher (52 m/s), le kilomètre coûte plus cher** (Albatros : 3,9 par km contre 2,35 à 119 m/s). Attention : ce n'est **pas** vrai pour toutes les vitesses lentes, voir « Loi gaz ↔ vitesse » plus bas (corrigé le 28/10) |

**Ce que ça change pour les modes**
- ~~ÉCO économise le temps de vol, pas la distance~~ **(corrigé le 28/10, voir « Loi gaz ↔ vitesse »)** : ÉCO économise bien le carburant par seconde (−30 % vers 90 m/s) **et** un peu par kilomètre (≈ −8 %), à condition de rester vers 90 m/s ; en dessous de ~70 m/s (plancher, orbite) le kilomètre coûte plus cher.
- **FLANK** : intéressant surtout pour le **Manta** ; pour l'Albatros le gain de vitesse est faible.
- La lecture des gaz par l'API des écrans (`get_throttle_factor`) **marche sur les avions de la carte** (vue depuis certains écrans seulement) mais **n'est pas fiable pour l'IA** (valeurs figées, ex. 1,00 à 52 m/s pour un avion qui brûle 0,2 /s) ; la vitesse (`get_linear_speed`) et le carburant sont fiables et concordent avec CC2X. `control_speed` / `control_power` de CC2X ne reflètent **pas** le pilotage à la main (restent 48 ou 72 / 1,000).
- **Inexpliqué** : le Manta en orbite à 88 m/s brûle **le double** de sa croisière à 122 m/s (0,695 contre 0,356 /s). Probablement le virage (inclinaison) ; à vérifier.

### Loi gaz ↔ vitesse de l'Albatros, estimée sans nouveau vol (28/10, à confirmer)

Le moddeur : « à 30 % et 50 % de gaz je perds de l'altitude à chaque fois ». **C'est le comportement réel** : il n'existe pas de vol en palier à ces gaz.
Estimation faite sur 661 segments de trajet droit de l'Albatros (bilan d'énergie sur 4 s : `d(v²/2 + g·h)/dt ÷ v = k·gaz − A·v² − B/v²`,
les gaz étant déduits du carburant brûlé, `/0,304`) :

| Gaz | Vitesse d'équilibre en palier (estimation) | Carburant |
|---|---|---|
| ≤ 0,50 | **aucune** : l'avion ne tient pas l'altitude (limite vers 0,57-0,60 à ~65-70 m/s) | — |
| 0,65 | **≈ 92 m/s** (branche stable) ; l'IA tient aussi 52 m/s à ce gaz (côté instable, observé en orbite) | 0,198 /s |
| 0,80 | ≈ 108 m/s | 0,243 /s |
| 0,93 | **≈ 119,5 m/s** (= croisière IA mesurée) | 0,282 /s |
| 1,00 | ≈ 125 m/s estimé (**131-135 observé** : le modèle sous-estime d'environ 6-10 m/s) | 0,304 /s |

**Vitesse de meilleure autonomie en distance** (minimum de carburant par km) : ≈ **90 m/s**, soit **≈ 2,16 par km** contre 2,35 à 119 m/s (**≈ −8 %**)
pour **−24 % de vitesse** ; par seconde : −30 %. **Fiabilité** : l'ajustement est bruité (écart type 0,40 pour un signal moyen de 0,17) ; il
retrouve bien les trois points mesurés (119 m/s ↔ 0,93 ; 52 m/s ↔ 0,65 ; plafond ~125-135 à 1,00), donc l'ordre de grandeur est solide
(**± 10 m/s**), pas le détail. À confirmer à l'étape 4 avec le plugin.

**(Corrigé le jour même par l'essai réel, voir §10 : ce paragraphe sur ~90 m/s et −8 % par km était faux.)**
**Ce que ça suggère pour les modes (Albatros)** : **ÉCO ≈ gaz plafonnés vers 0,65** (→ ~90 m/s, −30 % de carburant par seconde, ≈ −8 % par km) ;
NORMAL = jeu d'origine (119 m/s) ; **FLANK ≈ gaz à fond** (≈ 131 m/s). Donc **la variante « plafond de gaz » (étape 3c) suffit pour ÉCO** et
évite de toucher à la vitesse de croisière ; FLANK demande de relever la vitesse visée (le 120 du code) pour que le régulateur pousse les gaz à fond.
Le Manta n'a pas été calibré (sa croisière n'utilise que ~47 % des gaz ; marge de FLANK bien plus grande).

**Ce qui manque** (pas bloquant) : confirmation par le plugin (plafond de gaz réellement obéi par l'IA ?), vitesse max en palier du Manta, et la loi du Manta.

---

## 9. Plugin « plafond de gaz » (ÉCO) préparé, NON posé (28/10/2026)

Dossier `plugin/` : `cc2x_modes.c` (le plugin), `tests/test_modes.c` (38 contrôles sur un faux jeu, tous réussis), `construire_modes.py`
(compilation Zig, 2 fois identique, imports vérifiés, rapport dans `RAPPORT_compilation.md`), `modes.ini.example`, **`RISQUES_pose.md`**
(les risques par étape, à lire avant toute pose). `mod_modes.py` a deux commandes de plus : `poser-plugin` et `retirer-plugin`
(la DLL va dans `mods\cc2_modes\content\cc2x\`, le dossier du jeu n'est jamais touché ; essayé sur fausse copie).

**Découverte qui a changé le plan** : `CONTROL_POWER` du SDK **n'est pas un plafond de gaz**. Le jeu le multiplie à **toutes** les commandes de vol
(tangage, roulis, lacet **et** gaz, 0x71daf2..0x71dbbf) : l'utiliser affaiblirait aussi la direction. Le plugin écrit donc directement la
commande de gaz de l'avion (flottant à l'octet 0x314 de l'objet, borné 0..1, accumulé à chaque tick), **après le tick du jeu**, sans crochet de
code (le trampoline du SDK ne sauve pas les registres xmm, risqué sur ce code flottant). Il vérifie au chargement que les 8 octets du jeu en
0x71dbbf sont bien `movss [edi+0x314], xmm0`. **Deux étapes** : observation (rien n'est écrit, on compare avec les gaz mesurés), puis plafond sur un
seul avion. Non prouvé : que 0x314 soit le gaz, et que le jeu obéisse (c'est l'objet de l'essai A puis B).

---

## 10. Essais du plugin en jeu (28/10/2026, avec l'accord du moddeur, partie jetable)

Données : `mesures/2026-10-28_partie2_plugin_modes.log` (lignes `[modes]`), `mesures/2026-10-28_partie2_modes.ini`. Plugin posé le 28/10 08:2x (observation seule), **aucune erreur**.

**Étape A (observation) : le champ à +0x314 EST la commande de gaz de l'Albatros.** Lu 0,646-0,651 à 52,4 m/s (carburant 0,197 /s = 0,65 × 0,304), 0,57 (0,173 /s = 0,57 × 0,304),
1,00 (0,307 /s), 0,00 posé (carburant constant). Carburant par seconde = **0,304 × gaz** vérifié sur 4 niveaux. Pas encore vu pour le Manta.

**Étape B (plafond 0,65 sur l'avion 10, seul en vol, IA, à 10,9 km du bateau, 400 m) :**

| | Avant (NORMAL) | Plafond écrit 0,65 | Après coupure |
|---|---|---|---|
| Vitesse | 119 m/s | **se stabilise à ≈ 80 m/s** (en ~35 s, sans oscillation) | 80 → 96 m/s en 5 s (≈ 3 m/s²) |
| Altitude | 400 m | 398-400 m (aucune perte) | 400 → 404 m |
| Carburant | 0,282 /s | **0,22 /s** (−22 %) | 0,29-0,30 /s |
| Par kilomètre | 2,37 | **≈ 2,75 (+16 %)** | — |

- **Le mécanisme marche et se coupe sans reste** (`eco_enabled=0` pris en compte en ~3 s, l'IA remet tous les gaz et reprend sa vitesse).
- **Le plafond réellement appliqué est ≈ 0,72, pas 0,65** : le jeu ajoute son pas d'intégration (+0,07) avant que le moteur ne lise la valeur (la ligne `game_thr` montre 0,69 → 0,72 pendant que `written` = 0,65, et le carburant 0,22 /s = 0,72 × 0,304). Pour viser 0,65 effectif il faudrait écrire ~0,58 (près du plancher de sécurité 0,55) ou crocheter le code ; non nécessaire.
- **Corrections** : (1) mon estimation « 0,65 → ~92 m/s » surestimait d'environ 12 m/s (le modèle ajusté sur l'IA est trop optimiste à basse vitesse) ; mesuré : **0,72 effectif → 80 m/s**. (2) mon affirmation « ÉCO économise aussi par km (−8 % vers 90 m/s) » est **fausse** : par kilomètre, **plus vite = mieux** sur toute la plage mesurée (3,7 /km à 52 m/s, 2,75 à 80, 2,37 à 119, 2,32 à 131 pour l'Albatros). Le carburant par seconde dépend peu de la vitesse (0,20 à 0,30).
- **Conséquence pour les modes** : **ÉCO = rester plus longtemps en l'air** (≈ 60 min d'autonomie contre 47 min en croisière IA et 44 min à pleins gaz), **pas aller plus loin** (portée −14 % environ). **FLANK** (≈ 131 m/s) donne la meilleure portée et la vitesse maximale, au prix du temps de vol (44 min). Intérêt réel d'ÉCO : patrouille, attente, escorte lente. Le Manta reste à mesurer.

---

## 11. Mesure du Manta (28/10/2026, même partie, avion 17 ; vol de croisière IA puis pilotage à la main du moddeur)

Données : `mesures/2026-10-28_partie2_plugin_modes.log` (lignes `id 17`, t = 1611-2151 s). Plugin en observation seule, rien écrit.

| Gaz (lu par le plugin) | Vitesse tenue | Carburant | Par km | Remarque |
|---|---|---|---|---|
| **0,466** (croisière IA) | **121,7 m/s**, altitude 402 | 0,36 /s | 2,96 | stable pendant plus de 60 s, deux fois (t = 1660-1700 et 2080-2150) |
| 0,50 (à la main) | ≈ 132-136 m/s (encore en légère accélération) | 0,38 /s | ≈ 2,85 | |
| 0,77 (à la main) | **≈ 220 m/s** | 0,59 /s | 2,68 | stable, altitude 280-340 |
| **1,00** (à la main) | **≈ 290 m/s** (288-293 pendant 100 s) | 0,77 /s | **2,66** | quasi en palier (altitude 250-310) |

- **Consommation du Manta = 0,76 × gaz par seconde** (2,5 fois l'Albatros, comme les constantes 5 / 2), tous niveaux confirmés ; réservoir 1200 → **≈ 26 min à pleins gaz** contre ≈ 55 min en croisière IA.
- **Le champ de gaz à +0x314 est bien la commande de gaz aussi pour le Manta** (carburant = 0,76 × gaz à chaque palier).
- **La croisière IA du Manta n'utilise que 47 % des gaz** ; à pleins gaz il fait **290 m/s, soit 2,4 fois sa croisière** (l'Albatros : 131 contre 119, soit +10 %). Vitesse à peu près linéaire en gaz au-dessus de la croisière : v ≈ 122 + 310 × (gaz − 0,466) m/s.
- **Par kilomètre, plus vite est mieux, y compris pour le Manta** : 2,96 en croisière contre 2,66 à pleins gaz (−10 %). Portée à pleins réservoirs : ≈ 405 km en croisière, ≈ 450 km à pleins gaz.
- Le moddeur a volé le Manta à 290 m/s sans incident visible dans le journal (altitude tenue, pas de perte brutale), mais « effets d'un avion très rapide sur l'IA (virages, rayon, franchissement de point) » reste non mesuré.

**Idée qui change le plan de FLANK** : puisque le plugin pilote déjà la commande de gaz de l'IA après chaque tick, **FLANK peut être un plancher de gaz** (le plugin écrit « au moins X » au lieu de « au plus X »), avec **le même mécanisme et sans aucun patch de code ni du 120 de la croisière**. La commande est une valeur accumulée par le régulateur de l'IA : le jeu la rabaisserait d'un petit pas à chaque tick (≈ −0,07), le plugin la remonte aussitôt, d'où un gaz appliqué un peu sous la consigne (0,93 pour 1,0). À tester (étape C) : effet sur le suivi de points de passage à très grande vitesse. ÉCO du Manta demande un plafond **par type** : son plancher de sécurité doit être autour de 0,30-0,35 (le plafond minimal actuel de 0,55 est sans effet sur une croisière qui n'utilise que 0,47).

---

## 12. Plugin v2 préparé, NON posé (28/10/2026) : ÉCO par type et FLANK en plancher de gaz

Dossier `plugin/` : `cc2x_modes.c` (v2), `tests/test_modes.c` (**72 contrôles réussis**), `modes.ini.example` (v2), **`RISQUES_v2.md`** (à lire avant toute pose),
`RAPPORT_compilation.md` (DLL 218 624 octets, sha256 `8B3A5A87…DB35`, 2 compilations identiques, aucun import réseau). `mod_modes.py` : nouvelle commande
`mettre-a-jour-plugin` (remplace la v1 `AB2D5343…` posée par la v2 ; essayée sur fausse copie). Le plugin posé dans le vrai mod est **toujours la v1**.

- **FLANK = plancher de gaz** (idée née de la mesure du Manta, §11) : si le jeu laisse un gaz plus bas que le plancher, le plugin le remonte, après chaque tick ;
  aucun patch du code. Gaz appliqué = plancher moins le pas de régulation de l'IA (qui veut ralentir au-delà de ~120 m/s) : attendu ≈ 130 m/s Albatros, **≈ 230 m/s Manta**
  (estimation, à mesurer). Zone libre 6 km autour du bateau ; l'ordre de retour (dock 5) arrête FLANK immédiatement.
- **ÉCO par type** : Albatros 0,65 (min 0,55), Manta 0,35 (min 0,30).
- **Risques** : 🟡 ; FLANK est le plus délicat (comportement de l'IA à très grande vitesse jamais mesuré, virages larges, point dépassé, relief). Essai prévu :
  un seul avion, loin du bateau, plancher à 0,8 d'abord, partie jetable. Détail : `RISQUES_v2.md`.
- **Limite connue** : un avion piloté à la main n'est pas détecté ; ne jamais le mettre dans une liste. Le lien avec l'onglet SPEED (Lua) n'existe pas encore : les modes se
  choisissent par numéro d'avion dans `modes.ini`.

---

## 13. Relecture par le Mac (28/10/2026, branche `origin/mac/reponses-tour-28-10`, fichier `passation_windows/REPONSES_mac_pour_la_tour_28-10.md`, Q1)

Lu sans rien modifier. Le Mac a relu le code de son programme (équivalents : Windows `+0x308…0x314` ↔ Mac `+0x3e8…0x3f4`, écart constant `0xe0`).

| Point | Verdict du Mac | Effet sur le plugin |
|---|---|---|
| `+0x314` = commande de gaz 0..1 | **Oui** (lu : intégrateur `gaz += raideur × ((T − v)/120 − dv)`, borné 0..1 ; raideur `vehicle_ai_wing_throttle_stiffness` = **0,2**) | confirme ce que l'essai A a montré. **Vérifié aussi sur Windows** : la valeur 0,2 (`0x3e4ccccd`) est bien celle de ce réglage dans l'exécutable |
| `+0x1fc` (CONTROL_POWER) multiplie tangage, roulis, lacet **et** gaz | **Oui**, et le produit est **re-stocké** à chaque tick (le gaz « fond ») ; cas particulier : si `[0x18c]` ≠ 0 les 3 axes sont mis à 0 et gaz = puissance | confirme qu'il ne faut pas l'utiliser |
| Un plafond posé après le tick « fuit » d'un pas | **Oui, déduit** : la copie du gaz vers le moteur est dans `tick_ai`, juste après `tick_control` ; le moteur reçoit « plafond + un pas », pas = `0,2 × (T − v)/120` | **c'est exactement ce que l'essai B a mesuré** : écrit 0,65, appliqué 0,72 ; à 80 m/s de vitesse pour une cible de 120, le pas vaut 0,2 × 40/120 = **0,067** (mesuré 0,068). Le même calcul donne FLANK : appliqué = plancher − 0,2 × (v − 120)/120, soit 0,82 pour le Manta à 230 m/s, ce qui retombe sur l'estimation de ≈ 230 m/s du §12 |
| Le gaz envoyé au moteur est borné par `max(1 − S, plancher)`, plancher **0,8 (Albatros) / 0,75 (Manta)**, S = somme d'une valeur par équipement | lu, côté Mac | **nouveau risque pour FLANK** : un avion très équipé ne pourrait pas dépasser 0,8 (Albatros) / 0,75 (Manta) de demande moteur même avec un « gaz » affiché de 1,00 : le gain de FLANK serait plus petit. Nos essais (Albatros 131 m/s, Manta 290 m/s) ont été faits avec des avions peu chargés ; **à mesurer avec un avion équipé** |
| Carburant : 0,008 ou ≈ 0,005 par tick ? | Mac : 0,008 sûr ; Windows « probablement 0,005 » (déduit de 0,304 /s) | **Vérifié sur l'exécutable Windows d'origine** : `fuel_consumption_multiplier` est écrit avec `0x3c03126f` = **0,008** (en `0x868046`), comme sur le Mac ; les consommations `wing_light` 2,0 et `wing_heavy` 5,0 sont aussi les mêmes (`constants.txt`). L'hypothèse « 0,005 » n'est **pas** confirmée. |

**L'écart de 0,633 reste inexpliqué** : formule attendue 2 × 0,008 × 30 = 0,48 /s (Albatros) et 1,2 /s (Manta) à demande moteur 1,0 ; mesuré 0,304 et 0,76 à « gaz lu » 1,0, soit 0,633 pour les deux types et à tous
les niveaux de gaz (le carburant reste proportionnel au gaz lu). Donc soit la demande moteur vaut 0,633 × le gaz lu, soit un autre facteur commun existe (réglage appliqué à l'exécution ?). **Sans conséquence pour le
plugin** (qui agit sur le gaz lu et dont les effets sont mesurés), mais à garder pour les calculs d'autonomie : la loi empirique est **carburant par seconde = 0,304 × gaz (Albatros), 0,76 × gaz (Manta)**.

---

## 14. Lien onglet ↔ plugin préparé, NON posé (29/10/2026) : plugin v3, onglet v2, vérificateurs Lua maison

- **Plugin v3** (`plugin/cc2x_modes.c`, DLL 222 720 octets, sha256 `49AFE401…7A36`, **124 contrôles réussis**) : la v2 plus un pont Lua `cc2x.modes.set / get / hold / status`. Le mode de chaque avion
  se règle depuis l'écran et il est partagé entre les 3 écrans ; il ne s'applique que si `modes.ini` a `enabled=1`. **Garde-fou pilotage** : l'écran qui contrôle un avion appelle `hold(id)` à chaque
  image, et le plugin ne touche plus aux gaz de cet avion (lu dans `screen_vehicle_control.lua` : `g_viewing_vehicle_id > 0`, jamais vu en jeu).
- **Onglet v2** (`lua/v2/library_custom_5.lua`) : mêmes 3 boutons, branchés sur le plugin, état réel affiché (OBSERVATION / ACTIF / EN ATTENTE / PILOTE : EN PAUSE) et autonomie estimée
  d'après les mesures (Albatros 0,22 / 0,282 / 0,304 /s ; Manta 0,36 / 0,77 /s ; ÉCO du Manta « ? »). Sans plugin : redevient la maquette.
- **Outils maison** (préférence du moddeur : pas de programme tiers, donc pas de `lupa`) : `tour/outils/lua_syntaxe.py` (vérificateur de syntaxe Lua 5.3, 51 tests, accepte les 49 scripts du jeu et les nôtres,
  refuse les 28 cas mauvais) et `tour/outils/lua_inconnus.py` (noms inconnus = fautes de frappe possibles ; ne signale que `cc2x` et nos propres variables).
- **Installateur** (`mod_modes.py`) : nouvelles étapes `interface2` / `tout2`, `mettre-a-jour-plugin` remplace v1 ou v2 par la v3 ; essayé sur fausse copie ; `etat` dit la version de l'onglet et du plugin.
- **Risques** : `plugin/RISQUES_v3.md` (🟡). **Limite** : le comportement du script de l'onglet n'a été relu qu'à la main (pas d'interpréteur Lua), seule sa syntaxe et ses noms sont vérifiés.

---

## 15. ALERTE : le jeu a été mis à jour par Steam le 28/10/2026 à 21:30 (constaté le 29/10)

`carrier_command.exe` n'est plus celui que toutes nos études visaient : Steam a installé le build `26277078` (manifeste `LastUpdated` 28/10 21:30:07 ; `carrier_command.exe` et `carrier_command_vr.exe` remplacés à 21:30:04 ;
horodatage de compilation PE `0x6ae228f3` = 28/10 16:55 UTC, au lieu de `0x6a36c177` ; taille de l'image identique `0xaf7000` ; fichier 11 354 112 octets au lieu de 11 353 600).
sha256 `461E1262…`, ni l'exécutable d'origine (`1C9A01C3…`) ni le patché de la tour (`8E7FCBB6…`, qui est donc **écrasé** : ses retouches ne sont plus appliquées).

Conséquences, **vérifiées dans le code du SDK** (`src/cc2x.c` l. 828-832) : le SDK reconnaît un build par son horodatage PE et la taille de son image ; **sur un build inconnu « CC2X stays inactive »** : aucun plugin
chargé (le plugin de frein, notre `cc2x_modes.dll`), pas de table `cc2x` dans le Lua, donc la mesure `library_custom_3` ne fait plus rien (elle se garde avec `cc2x_ok()`), l'onglet v1 (maquette) marche encore (il n'utilise pas `cc2x`).
Le plugin v1 posé **ne se chargerait de toute façon pas** (il refuse si les 8 octets en `0x71dbbf` ne sont pas ceux attendus : ils sont maintenant décalés).

**Ce qui a bougé, mesuré dans les deux exécutables** : le code est le même, décalé : le store du gaz `movss [edi+0x314], xmm0` est en **`0x71dcbf`** (au lieu de `0x71dbbf`, +0x100), `mulss xmm0,[edi+0x1fc]` en `0x71dc53`
(au lieu de `0x71db53`), la constante 0,008 en `0x868182` / `0x8f0900` / `0x8f0adf` ; les **déplacements dans l'objet avion (`0x314`, `0x1fc`) sont inchangés**. Donc : mise à jour légère du jeu, adresses décalées.

**Mise à jour du 29/10 (après lecture de `tour/etude_mise_a_jour/ETUDE.md` et du chantier `chargeur_maison`)** : une étude complète de la mise à jour existe déjà ; elle recommande la **voie A** (garder l'ancien exécutable, patché, comme **fichier séparé** à côté de celui de Steam :
le SDK s'y active comme avant, rien à refaire) et déconseille de modifier le SDK pour qu'il accepte le nouvel exe. L'étude d'atterrissage a écrit l'outil `lancer_ancien.py` pour cette voie (non lancé : il demande l'accord du moddeur, 🟢 : ajout d'un fichier nouveau
que Steam ne connaît pas). Le chantier « chargeur maison » (remplacer le SDK de DYOR par un chargeur et une mini-API à nous) est cadré (P0 : nos deux plugins n'utilisent que 12 des 59 fonctions du SDK et 6 membres Lua ; décision (d) = option A) mais **P1 n'est pas accordée** et rien n'est compilé.
**Trois voies pour les modes carburant** : (A) ancien exe, immédiat ; (B) un jour, notre propre chargeur, qui pourrait viser directement le nouveau build ; (C) un profil « nouveau build » dans le SDK tiers (≥ 7 adresses, modifie le code d'un tiers : déconseillé).
**Côté plugin, déjà fait** : il reconnaît maintenant **les deux builds** par l'horodatage PE (`0x6a36c177` : store du gaz en `0x71dbbf` ; `0x6ae228f3` : en `0x71dcbf`) et contrôle les 8 octets à l'adresse du build reconnu (130 contrôles réussis) ; il ne dépend plus de la chaîne « 1.5.18-win32 » du SDK.

**Pour que le plugin remarche** : (1) le SDK doit connaître le nouveau build (un « profil » : horodatage `0x6ae228f3` + les adresses et déplacements du monde du jeu de `src/world.c`, à retrouver) ; c'est le travail du SDK (ou d'un chargeur maison, une conversation y travaille), pas du plugin ;
(2) le plugin n'aurait plus qu'à changer `THR_SITE` (`0x71dcbf`) et accepter la chaîne de build du SDK. **Rien n'a été modifié pour cela**, ni dans le SDK, ni dans le jeu.

---

## 16. Premier essai en jeu avec le plugin v3 + l'onglet v2 (30/10/2026) ; correctifs préparés d'après les revues du 29/10

**Posé le 30/10 à 07:38** (accord du moddeur, jeu fermé) : onglet v2 (`0A402A3E…`) + plugin v3 (`331581C6…`). Le jeu (ancien exe de la voie A) a ensuite été lancé à 08:01 par l'étude d'atterrissage pour l'essai du frein v8 ;
Le moddeur a enchaîné, dans la même partie, un essai ÉCO : l'accord « Oui, active ÉCO » a été transmis par la session de coordination, qui a changé **une seule ligne** de `modes.ini` (`eco_enabled=0` → `1`, sauvegarde
`modes.ini.avant_eco_0809`), puis remis `eco_enabled=0` à 08:11:32. Je n'ai rien fait pendant la partie ; j'ai relu `cc2x.log` ensuite, en lecture seule (extrait des lignes `[modes]` :
`mesures/2026-10-30_eco_avion10_plugin_v3_lignes_modes.log`, 491 lignes).

**ÉCO sur l'avion 10 (Albatros), 08:08:28 → 08:11:34** [MESURÉ, ancien build] : mis en ÉCO alors qu'il volait seul à 29 km du bateau, gaz du jeu 1,000. Vitesse 119,1 → 111 → 97 → 87 → **79,8–80,0 m/s stable en ~50 s** ; plafond écrit
0,650, gaz appliqué 0,719 ; altitude 400 (minimum 398 pendant la décélération) ; carburant −1,4 → −1,1 par ligne de 5 s de jeu soit 0,28 → 0,22 par seconde (**−21 %**) ; l'avion 9 (NORMAL) n'a pas été touché (gaz écrit = gaz lu).
C'est le résultat du 28/10, cette fois avec le plugin v3 et l'onglet v2. Aucune ligne d'avertissement. Coupure : fichier modifié 08:11:32, « enabled=0 » vu à 08:11:34,3 (≈ 2 s), l'avion repart de 82 à 117 m/s en ~25 s.

**Garde-fou pilote : vu en vrai pour la première fois** [MESURÉ] : `id 9: HELD` 08:04:37 → `no longer held` 08:06:26 ; `id 10: HELD` 08:10:57,859 et, **à la même milliseconde**, `ECO off after 5970 writes (held=1)` ; le pilote garde ses gaz (1,000) ;
relâché 08:11:07 → ÉCO reprend aussitôt ; encore `HELD` 08:11:09,8 → 08:11:13,3 puis reprise. Reste à confirmer avec le moddeur qu'il **pilotait** bien à ces instants (et non pas seulement la caméra) : le sens de « `g_viewing_vehicle_id > 0` = je pilote »
est donc très probable, pas définitivement établi. Pas vu : FLANK, ÉCO du Manta, un clic sur les boutons de l'onglet (le mode de l'avion 10 venait de `modes.ini`), l'affichage de l'onglet (aucun retour du moddeur lu ici).

**Revues cloud du 29/10** (`revues/REVUE_modes_carburant.md` et `tests/banc_lua/BUGS_TROUVES.md` sur les branches `origin/[branche]` et `origin/[branche]`) : points relus un par un dans le code puis corrigés hors jeu
→ **plugin v3.1** (`plugin/v3_1/`, lecture stricte de `modes.ini`, lignes de journal réservées), **onglet v2.1** (`lua/v2_1/`, garde-fou pilote sans condition et avant/après `update`, « PLUGIN PLEIN »), `mod_modes.py` (refus si un `carrier_command*` tourne, `--version`,
étape `interface2_1`) ; tout est décrit dans `plugin/RISQUES_v3_1.md`. **Non posés** ; la pose demande l'accord du moddeur, jeu fermé. Les 2 gros doutes de la revue sur le garde-fou (crochet jamais posé ; une image de retard) ne se sont pas manifestés dans cet essai.

## 17. Deuxième essai en jeu : plugin v3.1 + onglet v2.1, partie combinée avec l'essai v9 d'atterrissage (30/10/2026, 08:37 → 08:55)

Journal analysé en lecture seule : `cc2-sdk-travail\logs_parties\cc2x_2026-10-30_082200_frein_v9.log` (3 parties successives ; extrait des lignes `[modes]` : `mesures/2026-10-30_partie_v9_lignes_modes.log`, 669 lignes). Pose faite à 08:21 avec le « Oui, pose » du moddeur ; `modes.ini` modifié deux fois par la coordination (ÉCO à 08:49:09, remis ensuite), jamais par moi.

**Ce qui a marché** [MESURÉ] : `loaded v3.1` ; **0** ligne d'avertissement, **0** ligne `modes.ini:`, **0** erreur d'onglet (`CC2MODES|UI|erreur`) ; observation seule au départ. **ÉCO sur l'avion 10** : 125 lignes d'observation en ÉCO, 80 m/s (79,8–80,2) en ~40 s, gaz écrit 0,650 / appliqué 0,719, altitude 398–406, carburant **0,2816 → 0,2198 par seconde = −22 %** (deux phases : −22,1 % et −21,8 %), comme les 28/10 et 30/10 matin.
**Garde-fou pilote** : 3 pauses d'ÉCO sur 3 prises en main (`HELD` 08:49:12.589, 08:51:03.911, 08:51:20.183) **à la même milliseconde** que `ECO off … held=1`, gaz du pilote laissés intacts ; reprise de l'ÉCO au `no longer held` (3 s de jeu après la dernière prise). `HELD` aussi pour l'avion 9 (4 fois, v9) : l'avion 9 n'a jamais reçu une écriture (326 lignes, gaz écrit = gaz lu).
**Boutons de l'onglet** [vu pour la première fois] : `Lua: id 10 set to NORMAL` 08:51:16.983 → `ECO off … asked=NORMAL` ; `Lua: id 10 set to ECO` 08:51:19.111 → `ECO cap 0.65 on` : les clics de l'onglet v2.1 arrivent au plugin et le mode de l'onglet passe avant `modes.ini`. Donc la fenêtre SPEED s'affichait et répondait ; le **texte** affiché (« OBSERVATION… », « ACTIF », autonomie) n'a pas été décrit par le moddeur.
**Deux fenêtres à noter** : 110 écritures (2,7 s) entre l'activation à 08:49:09.855 et le `HELD` de 08:49:12.589, et 44 écritures (1,1 s) entre le clic ECO de 08:51:19.111 et le `HELD` de 08:51:20.183 : le journal ne permet pas de savoir si le moddeur pilotait déjà (garde-fou en retard) ou a pris l'avion juste après (cas le plus probable : il active puis saute dans l'avion). **À demander au moddeur**. Le ralentissement à 52 m/s de 08:48:46 à 08:49:09 (gaz du jeu 0, `enabled=0` donc rien d'écrit) est le comportement de l'IA, pas l'ÉCO.
**Pas prouvé** : FLANK (jamais essayé), ÉCO du Manta, « PLUGIN PLEIN » (il faut 64 avions), le texte de l'onglet, l'autonomie affichée.

## 18. FLANK essayé en jeu (30/10/2026, 09:40 → 09:51) : l'Albatros ne gagne rien, le Manta oscille au-dessus de ~220 m/s

Données : `mesures/2026-10-30_flank_albatros_manta_lignes_modes.log` (lignes `[modes]`) et `mesures/2026-10-30_manta17_flank_telemetrie_par_tick.csv` (Manta 17, un point par tick, altitude entière). Réglages d'essai : `enabled=1`, `flank_free_zone_m=15000` (ajouté par la coordination à 09:43:51), FLANK demandé par le bouton de l'onglet. Analyse faite en lecture seule.

**Albatros (id 10)** [MESURÉ] : gaz écrit 1,000, gaz du jeu 1,000, mais la vitesse plafonne à **119,1 m/s, exactement la croisière NORMAL**, altitude 400 plate, carburant **≈ 0,26/s** (NORMAL : 0,2816). FLANK ne sert donc à rien sur un Albatros piloté par l'IA : le « 131 m/s à pleins gaz » du 28/10 était un vol piloté à la main. Cause non établie (plafond de demande moteur de l'IA ? voir la relecture du Mac, §13).
**Manta (id 17)** [MESURÉ] : à partir de 126 m/s il accélère presque en ligne droite (un virage de 115° juste après le clic, cap 24° → −98°, à 09:47:04–11, explique le creux de vitesse à 95 m/s) jusqu'à **224,8 m/s** (plancher 1,0 : le jeu retire son pas, ≈ 0,82 appliqué ; modèle : 232 m/s, mesuré 225) ; altitude plate à ±1 m jusqu'à ~220 m/s. **Puis, à ≈ 222–225 m/s, une oscillation d'altitude apparaît et croît** (amplitude 1 → 4 → 8 → 22 m en ~10 s de jeu), la vitesse tombe à 150–166 m/s et un **cycle limite persistant** s'installe : altitude 387 ↔ 423 m (±18 m), période ≈ 35–40 s de jeu, vitesse en opposition de phase (maximum en bas, minimum en haut = type phugoïde). Dans le 2e vol il dure jusqu'à la fin de l'essai (2 min, sans HELD) ; dans le 1er le cap est resté constant (−91°) pendant toute l'oscillation, donc ce n'est pas un virage. Même scénario aux 2 vols FLANK sans pilote (09:47:30 et 09:49:06). À 122 m/s en NORMAL : 0 m d'oscillation. Carburant dans le cycle : ≈ 0,64/s à 155 m/s = **4,1 par km, contre 2,96 en NORMAL (−35 % de portée)** ; en vol plat à 225 m/s : 2,84 par km (−4 %).
**Hypothèse** : la boucle d'altitude de l'IA, réglée pour ~120 m/s, devient instable vers 220 m/s (gain de gouverne ∝ v²) ; le plugin n'écrit que les gaz (+0x314) et ne touche pas aux sorties de tangage (+0x308..0x310) ; il peut ajouter un effet indirect en supprimant la moitié « augmenter les gaz » de la régulation de vitesse du jeu (gaz bloqués à 1,0). Essai pour trancher : plancher plus bas (`flank_floor_heavy=0.75` → ≈ 176–182 m/s, `0.80` → ≈ 185–192 m/s ; modèle étalonné sur le 232 prévu / 225 mesuré).
**Décélération mesurée** (gaz du jeu à 0, pilote qui lâche, 09:48:13) : 216 → 163 → 140 → 130 → 125 m/s en 20 s de jeu (≈ 10 m/s² au début, ≈ 3 km parcourus) : le relâchement à la limite de zone n'a donc pas besoin de plus de ~3 km pour le Manta.

## Annexe A — Adresses Windows retrouvées (copie d'origine, base `0x400000`)

Fonction du contrôle des ailes (équivalent de `c_vehicle_server_wing::tick_control`), début vers `0x719b80` :

```
0071a0b8  cmp   dword [edi+0x84], 0xa        ; type 10 = Manta
0071a0bf  movss xmm1, [ebp-0x1bc]            ; vitesse renvoyée par le point de passage (0 en vol normal)
0071a0c7  movss xmm2, [0xdb7a00]             ; 144.0   (plafond)
0071a0d2  maxss xmm0, [0xdb79b4]             ; 48.0    (plancher Albatros, opérande en 0x71a0d6)
0071a0da  minss xmm0, xmm2
0071a0de  movss [edi+0x1f8], xmm0            ; vitesse visée stockée (écrasée à chaque tick)
0071a0e8  maxss xmm1, [0xdb79cc]             ; 72.0    (plancher Manta, opérande en 0x71a0ec)
0071a0f4  movss [edi+0x1f8], xmm1
```
Régulateur de gaz (même fonction, plus loin) :
```
0071ddcc  movss xmm5, [0xdb79ec]             ; 120.0   <- vitesse de croisière lointaine
0071dddc  maxss xmm0, [-10.0] / minss [40.0] ; correction bornée
0071ddec  addss xmm0, [edi+0x1f8]            ; + vitesse visée S
0071ddf4  subss xmm5, xmm0 ; mulss xmm5, a ; addss xmm5, xmm0   ; T = S + a (120 - S)
0071de3d  divss xmm5, [0xdb79ec]             ; (T - v) / 120
```
Autres lectures de 120 et de 780 voisines (`0x71ceb1`, `0x71cc1b`) : le 780 est la rampe de *a* ; le rôle exact du 120 de `0x71ceb1` est
à confirmer au désassembleur avant toute écriture. Les octets du fichier et l'adresse du champ « équipe » restent à relever (le champ
`+0x84` est le type, `+0x1f8` la vitesse visée ; l'équipe n'a pas encore été cherchée sur Windows).

Place disponible dans l'exécutable : `.text` finit à `0xCD5ADB`, la section suivante commence à `0xCD6000` (1,3 Ko de pages exécutables
remplies de zéros, dont 293 octets seulement présents dans le fichier). La chaîne `dofile` (point d'entrée possible d'une fonction Lua
nouvelle, comme sur le Mac) existe bien dans l'exécutable.

## Annexe B — Commandes d'écriture du Lua (extraites de l'exécutable)

`set_*` : `set_attached_vehicle_attachment`, `set_attached_vehicle_chassis`, `set_damage_zone_repairing`, `set_facility_*_production_queue_*`
(4), `set_game_setting`, `set_inventory_order`, `set_is_hold_fire`, `set_is_low_light`, `set_sensor_angle`, `set_target_vehicle`,
`set_waypoint_altitude`, `set_waypoint_attack_target_*` (2), `set_waypoint_repeat`, `set_waypoint_type_*` (3), `set_waypoint_wait_group`
— plus `add_waypoint`, `clear_waypoints`, `clear_attack_target`, `trigger_self_destruct` et les `update_set_*` d'interface. **Aucune pour la
vitesse, les gaz ou le carburant.** Lecture : `get_fuel_factor`, `get_fuel_capacity/remaining` (réservoirs), `get_linear_speed`,
`get_linear_velocity`, `get_velocity_magnitude`, `get_throttle_factor`.

SDK déjà installé (`dinput8.dll`, 0.5.0) : `cc2x.vehicle(id)` donne `speed`, `fuel`, `control_speed`, `control_power`, `team_is_ai`,
`is_wing`… ; `cc2x.set_vehicle(id, "control_speed" | "control_power", valeur)` existe mais, vu la section 3.3, ne suffit pas pour la
vitesse ; `cc2x.log(...)` écrit une ligne dans `cc2x.log` (canal de sortie utile pour l'étape 0b) ; un plugin peut ajouter ses propres
fonctions Lua (`api->lua_add`, ex. `cc2x.speed.mode(id [, mode])`).

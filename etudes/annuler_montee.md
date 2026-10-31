# Étude — annuler la sortie d'un avion déjà pris par la grue (demande Geometa n° 20652)

Écrite le 25/10/2026, phase 1 (lecture seule du programme, rien n'a été modifié).
**Phase 2 faite le 25/10 (feu vert du moddeur, option 1)** : module `outil/modules/grue_annulation.py`, généré par
`outil/generateurs/generer_grue_annulation.py` depuis `grue_annulation.c` ; greffe à 0x100061200 (932 o) au lieu de
« après 0x10005c4e0 » ; testé sur copies (`tests/test_grue_annulation.py`, `tests/test_patchs.py`), **activé dans le jeu le 25/10**
(md5 6fcfd65e…), pas encore essayé en jeu. Programme Mac du 05/01/2026,
tel qu'installé (9 modules actifs). Adresses = adresses du programme (offset fichier = adresse − 0x100000000).

## 1. Verdict

**Faisable, par une greffe de code C (technique déjà validée), pour toute la durée où l'avion est sur la grue.**
Le même bouton de baie qu'aujourd'hui sert d'annulation : un 2e appui renvoie la grue en arrière et l'avion
reprend sa place. **Difficulté 5/10, 1 session** (+ son essai en jeu, éventuellement une petite 2e session de
retouche). Étendre à l'ascenseur (avion déjà posé sur la plateforme) : **8/10, 3-4 sessions, risque de blocage
grue/ascenseur → déconseillé pour l'instant.**

Fenêtre d'annulation gagnée (ascenseur ×2 actif, énergie pleine) : de l'appui jusqu'au moment où la grue lâche
l'avion au-dessus de l'ascenseur, soit **≈ 13 s pour les baies proches, ≈ 18 s pour les plus éloignées** (le double
sans l'ascenseur ×2). Aujourd'hui la fenêtre est presque nulle : si la grue est libre, elle prend l'avion dès le
tick suivant l'appui, donc la file d'attente (seul moment annulable) ne dure qu'une fraction de seconde.

## 2. Comment marche le bouton aujourd'hui

- Bouton physique `vehicle_control_air_bay_N` (aide `veh_con_button_deploy_air`). Côté serveur,
  `c_vehicle_carrier_server_vehicle_control::tick` (0x1001b2e18) : à l'appui (front montant) sur une baie occupée,
  appel virtuel 0x108 = `c_vehicle_server_carrier::undock` (0x100193eaa), **sans regarder l'état de l'avion**.
  Il passe la main à `docking_manager_air::undock` (0x1001a8bd4), gestionnaire = porte-avions + 0x15e8.
- `docking_manager_air::undock` est un **interrupteur** :
  - avion dans la grue (0x78), l'ascenseur (0x7c), la piste (0x80) ou le décollage hélico (0x84) : si
    dock_state = 7 (attente au lancement, bouton rouge) → 0x28 = id (= « vas-y ») ; **sinon rien** ;
  - avion dans la file d'atterrissage (0x48) → rien ;
  - avion déjà dans la file de sortie (0x60) → `cancel_undocking` (0x1001a8dfa) ;
  - sinon → ajouté à la file de sortie, dock_state = 2.
- `cancel_undocking` : seulement si l'avion est dans la file de sortie : l'en retire, dock_state = 4, efface ses
  points de passage (`mm_vector<c_vehicle_waypoint_data>::clear` sur +0x1d0, `reset_waypoint_path`) et prévient
  la carte (appel virtuel 0 de la carte avec id, +0x300, +0x1d0, +0x1e8). **Dès que la grue a pris l'avion, il
  n'est plus dans la file : l'annulation ne trouve rien.** Voilà tout le « pourquoi ».
- L'IA du porte-avions ennemi n'appelle `undock` que sur des appareils au hangar (dock_state = 4 vérifié à
  0x100109ef5 et 0x10010dfb0) : jamais concernée par ce patch.

## 3. La machine de la grue (docking_manager_air::update, 0x1001accd8)

Champs du gestionnaire (noms tirés de `parse_state_xml`, sauvegardés) : 0x00 `mode` (0 repos, 1 rangement,
2 lancement) · 0x04 état de l'ascenseur pour les écrans · 0x08 `crane_instructions` (anneau d'entiers : pointeur
0x08, capacité 0x10, début 0x14, nombre 0x18) · 0x20 `is_crane_lifting` (la grue tient l'avion) · 0x60
`undocking_queue` · 0x78/0x7c/0x80/0x84 `vehicle_id_crane/lift/runway/rotor_takeoff` · 0x88…0x94 les baies
correspondantes (`vehicle_attachment_index_*`) · 0xb0 `paths_crane` (+0x18 avancement 0xc8, +0x1c vitesse 0xcc).
Non sauvegardé : 0x28 (id libéré de l'attente au lancement), 0x98 (nœud de repos de la grue).
Porte-avions : 0x153c/0x1544 position de la grue (x/z), 0x1540 hauteur du crochet (12 haut, 11 bas), 0x1548
rotation (0 ou π), 0x1518 hauteur de l'ascenseur (−9 bas → 0 haut), 0x1538 consigne (0 bas, 1 haut).

**Les 5 gestes** (table de saut 0x1001b25ec, le premier de la liste s'exécute, puis il est retiré) :

| n° | adresse | geste |
|---|---|---|
| 1 | 0x1001ae858 | aller au-dessus de la baie 0x88 (z d'abord, puis x) |
| 2 | 0x1001ae9a1 | revenir au repos au-dessus de l'ascenseur (nœud 0x98 ; x d'abord, puis z) |
| 3 | 0x1001aea82 | tourner : vers π si (mode = 2) == « tient l'avion », sinon vers 0 |
| 4 | 0x1001aea99 | si ne tient rien : descendre à 11, attraper (0x20 = 1) ; puis remonter à 12 |
| 5 | 0x1001ae949 | si tient : descendre à 11, lâcher (0x20 = 0) ; puis remonter à 12 |

Vitesses actuelles (×2) : 1/3 m par tick à l'horizontale, 1/15 en vertical, 0,08 rad/tick, × part d'énergie.

- **Lancement** (mode 2, bloc 0x1001acea1 → 0x1001ad84d → 0x1001b0eb1) : si la file de sortie n'est pas vide et
  la grue libre (0x78 = −1), la grue prend le premier : 0x78 = id, retiré de la file, liste = **[1, 4, 2, 5]**,
  ou **[1, 4, 2, 3, 5, 3]** pour les baies où l'avion doit être retourné (baies du côté droit, x = +13 :
  probablement 2, 4, 6, 8) ; chemin `load_lift_lower` créé, frein serré, véhicule +0x21c = 1, **dock_state = 3**.
  Si l'avion n'est pas prêt (`get_is_undock_ready`), il est remis en fin de file.
- **Pendant tout le portage, l'avion reste rangé dans sa baie** (case 0x1f0 + 0x70 × baie du porte-avions) : quand
  la grue le tient (0x20 = 1), le jeu déplace seulement la position de cette case pour suivre le crochet
  (0x1001aec07 → `set_attachment_transform`). Il ne peut donc pas être « perdu ».
- **Fin de grue** (0x1001ad9ad) : liste vide, ascenseur libre et en bas (< −8,5) → l'avion roule sur
  `load_lift_lower` (0x1001ae272 → 0x1001b10ce), puis passe sur l'ascenseur (0x1001b15bb : 0x7c = id, 0x78 = −1),
  qui monte ; en haut : piste, ou attente au lancement (dock_state 7).
- **Rangement** (mode 1, 0x1001b1164) : la grue prend l'avion sur l'ascenseur, liste [4, 1, 5, 2] ou
  [3, 4, 3, 1, 5, 2], dock_state = 4 dès la prise ; quand la liste est vide, 0x78 = −1 (0x1001ad769).
- Le mode ne change que quand les 4 cases (0x78…0x84) sont vides (retour à 0). La grue exécute sa liste dans
  tous les modes (0x1001ae787).

## 4. Ce que ferait le patch (option 1 : grue seulement)

Deux branchements, une greffe de ~250 octets dans la zone morte d'ImGui (après 0x10005c4e0, à revérifier).

**Branchement A — l'appui** : 0x1001a8c01…0x1001a8c0d (13 octets : `cmpl $7,0x220(%r14)` / `jne` / `movl
%ebx,0x28(%rdi)`, aucun saut du jeu au milieu) → `jmp` greffe. La greffe rejoue l'original si dock_state = 7,
sinon appelle `annuler_grue(gestionnaire rdi, avion r14, carte rcx)` puis retourne à 0x1001a8c0e. Pile alignée
(5 empilements) : appel C direct possible. `annuler_grue` n'agit que si **mode = 2, 0x78 = cet avion et
dock_state = 3**, et :
- **pas encore attrapé** (0x20 = 0 et un 4 reste dans la liste) : liste = [5, 2] (5 sans avion = simple
  remontée), 0x78 = 0x88 = −1. L'avion n'a jamais bougé ;
- **tenu** (0x20 = 1) **et pas tourné** (|0x1548| < 0,01) : liste = [4, 1, 5, 2] (4 en tenant = remonter, aller
  à la baie, poser, revenir au repos), 0x78 gardé jusqu'à la fin ;
- **sinon** (déjà en train d'être tourné ou lâché au-dessus de l'ascenseur, roulage, ascenseur) : **rien**,
  comme aujourd'hui.
Dans les deux premiers cas : dock_state = 4, +0x21c = 0, points de passage effacés et carte prévenue (mêmes
appels que `cancel_undocking`). La liste se réécrit avec début = nombre = 0 puis `mm_vector<e_crane_state>::
push_back` (0x10019a450).

**Branchement B — fin du retour** : 0x1001ad9ad (5 octets `cmpl $0,0x18(%r14)`, 4 sauts y arrivent, aucun au
milieu ; seulement en mode 2) → greffe en assembleur pur (pas d'appel C : on ne sait pas quels registres xmm sont
vivants) : si la liste est vide, 0x78 ≠ −1 et l'avion 0x78 a dock_state = 4 → 0x78 = 0x88 = −1. Puis rejoue le
`cmpl` et revient à 0x1001ad9b2. Ce cas n'existe pas dans le jeu d'origine (en mode 2, le seul « dock_state = 4 »
écrit dans la fonction est celui du rangement, en mode 1) : le test repose sur un état **sauvegardé**, donc un
retour interrompu par une sauvegarde reprend au chargement.

Pas besoin de toucher au geste 3 : on refuse l'annulation dès que l'avion a commencé à tourner (≈ 1 s avant le
lâcher, baies de droite seulement).

## 5. Risques

| risque | quand | parade |
|---|---|---|
| **Grue bloquée** (le plus grave) | B ne se déclenche jamais → 0x78 reste pris : plus de lancement, et le hangar reste en mode 2 donc **plus d'atterrissage** | condition simple ; tests sur copies ; si ça arrive, retirer le module suffit (le jeu d'origine passe alors l'avion à l'ascenseur et le lance : tout se débloque) |
| Avion lâché en l'air | 0x78 vidé alors que la grue tient l'avion | B attend la liste vide (avion posé) ; au pire l'avion reste affiché de travers dans sa baie jusqu'au prochain lancement, qui le reprend |
| Avion perdu | — | impossible : il ne quitte jamais sa case de baie pendant la grue |
| Avion à l'envers | annulation après la rotation | refusée (|rotation| > 0,01) |
| Double appui | 3e appui pendant le retour | sans effet (dock_state = 4 et dans la grue : le jeu ne fait rien) ; relançable une fois rangé |
| Sauvegarde pendant le retour | — | état sauvegardé, le retour reprend (à vérifier en jeu) |
| Autres conversations | deux autres travaillent dans la même fonction | points A et B libres le 25/10 ; revérifier les modules et `ATELIER_OCCUPE.txt` en phase 2 |
| Mise à jour Steam | — | refus du moteur comme pour les autres modules |
| Multijoueur | — | agit chez l'hôte seulement (comme les autres patchs) |

## 6. Option 2 (grue + ascenseur) : pourquoi pas maintenant

Une fois l'avion lâché, il roule sur `load_lift_lower` puis monte ; le ramener demande de faire redescendre
l'ascenseur en mode 2, faire rouler l'avion **à l'envers** (n'existe pas dans le jeu), le faire reprendre par la
grue avec une liste de rangement, et refuser si la grue tient déjà l'avion suivant (sinon les deux s'attendent pour
toujours : grue et ascenseur bloqués). Environ 3 branchements de plus et une greffe de 1-2 Ko. Gain : ~6-10 s de
fenêtre en plus. Variante plus simple mais limitée : passer le hangar en mode « rangement » quand l'avion est seul
dans le circuit (pas d'autre avion sur la grue, l'ascenseur ou la piste) — le jeu ferait alors le retour tout seul.

## 7. Phase 2 (si feu vert)

1. Vérifier `ATELIER_OCCUPE.txt`, le créer. 2. `outil/generateurs/annuler_grue.c` + `.s` (branchement B) et un
générateur dérivé de `generer_helicos_ascenseur.py`. 3. Module `outil/modules/annuler_grue.py`. 4. Tests :
relecture objdump de chaque branchement, chaque appel et chaque saut ; **test de la logique C sur un faux
gestionnaire** (liste, cas refusés) exécuté via Rosetta ; `tests/test_patchs.py` complet. 5. Activation avec son
accord. 6. Son essai : sortir un avion d'une baie du fond et ré-appuyer pendant que la grue y va / le porte / le
pose ; une baie de droite au moment de la rotation (doit refuser) ; deux avions lancés, annuler le 2e pendant que
le 1er monte ; sauvegarder pendant un retour puis recharger. 7. Fiche DEMARRER.

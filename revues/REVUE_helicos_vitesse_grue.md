# Revue indépendante — patchs « hélicos », vitesse de l'escadrille, grue (et modules voisins)

Relecteur : Claude, session cloud, le 29/10/2026. Dépôt `cc2-patchs`, branche `[branche]`, base `ea7e2f7`.
Aucun fichier source n'a été modifié : ce rapport est le seul fichier ajouté.

Étiquettes utilisées (comme dans les études du dépôt) : **EXÉCUTÉ** (je l'ai lancé et j'ai vu le résultat), **LU** (lu dans le code
ou les notes), **INFÉRÉ** (déduit, pas vérifié). Je n'ai ni le jeu, ni Steam, ni le programme d'origine : **aucune conclusion de ce
rapport ne dit qu'une chose marche en jeu.**

---

## 0. L'essentiel

**En clair pour le moddeur**

- Les petits programmes ajoutés au jeu (grue, vitesse, écran CCTV, écriture du relevé) se comportent comme leurs tests le disent,
  d'après ce que j'ai pu rejouer hors du jeu. Je n'ai trouvé aucun défaut dans leur code qui ferait planter le jeu à coup sûr,
  sous réserve des hypothèses que je n'ai pas pu vérifier (§5).
- **Deux choses à ne pas faire avant correction** : (1) utiliser le menu de l'Atelier pendant qu'une mise à jour Steam peut tomber
  (il peut remettre l'ancien programme par-dessus le nouveau, je l'ai reproduit sur une copie) ; (2) remettre le module
  « hélicos sur l'ascenseur » (celui qui a provoqué une collision le 24/10) dans `outil/modules/`.
- Le curseur ECO / NORMAL / FLANK ne change **pas** la vitesse de transit des avions (mesure du 25/10 : ~120 m/s dans tous les cas),
  seulement leur vitesse près du point visé. Les textes du module et de la barre promettent plus que ça.
- Après la mise à jour Steam, si le Mac a aussi reçu un nouveau programme, l'Atelier refusera de toucher au jeu (c'est bien), mais
  avec un message trompeur, et le bouton « Tout remettre » ne marchera pas non plus.

**Pour le technique**

- 2 bloquants, 8 importants, 10 mineurs (§3). Solide : §4. Hors de portée sans le jeu : §5. Cas limites demandés : §6.
- **Aucun des 11 scripts de test du dépôt ne s'exécute dans le cloud** (0 contrôle passé : il leur faut le programme d'origine, le jeu
  installé, Rosetta, un `objdump` Apple, `lupa`). J'ai refait à la main ce qui était refaisable (§2) : plus de 300 contrôles
  exécutés, 0 échec sur le code livré, mais sur des maquettes (faux gestionnaire, faux programme), pas sur le vrai programme.

---

## 1. Cadre, limites, sécurité

**Ce que j'avais** : les sources, les modules (octets « avant » / « après »), les générateurs, les tests, les notes, les copies de
partage. **Ce que je n'avais pas** : le jeu, `sauvegarde/build_mac_origine` (ignoré par git, donc absent d'un clone), les fichiers
du jeu. Conséquence : je n'ai jamais pu relire les octets « avant » dans le vrai programme. J'ai désassemblé ceux que les modules
annoncent (cohérence interne), ce qui ne prouve pas que le programme d'origine les contient (c'est le rôle du md5 d'origine).

**Sécurité (le moddeur veut être prévenu avant toute action à autorisation)** :
- Je n'ai **rien installé, rien téléchargé, aucun accès réseau**. Pas de `pip`, pas d'`apt`.
- Pour le Lua, plutôt que d'installer `lupa` (paquet tiers), j'ai écrit un lanceur C de 30 lignes qui relie la bibliothèque
  `liblua5.4` **déjà présente** sur la machine. C'est du Lua 5.4 ; le jeu embarque du 5.3 (différences mineures, non testées ici).
- Mes essais ont mappé du code exécutable (RWX) à des adresses fixes dans mes propres processus de test, dans le bac à sable du
  cloud. Aucun risque pour le Mac du moddeur. Mes scripts sont dans le dossier de travail de la session (annexe), pas dans le dépôt.
- J'ai créé puis supprimé des dossiers `__pycache__` dans le dépôt (ignorés par git) ; `git status` est propre hors ce rapport.
- Risques que je signale pour la suite : (a) `patchs_cc2.py` fait `exec_module` de **tout** `.py` de `outil/modules/`
  (`charger_modules`, L79-93) : ne jamais y déposer un fichier non relu ; (b) tout `print()` Lua de n'importe quel mod part dans
  `releve_cc2.txt` sans limite de taille (M6).

---

## 2. Ce qui a été exécuté et ce qui ne l'a pas été

### 2.1 Les tests du dépôt, lancés tels quels

`python3 -I tests/<test>.py` pour chacun, puis `python3 -I -m unittest discover -s tests` (qui échoue partout : ce sont des scripts qui
s'exécutent à l'import, pas des `unittest`).

| Test | Résultat dans le cloud | Cause (ligne) |
|---|---|---|
| `test_patchs.py` | échec au démarrage, 0 contrôle | copie le **vrai** programme du jeu `P.PROGRAMME` (L72), chemin Mac absolu |
| `test_helicos.py` | échec au démarrage, 0 contrôle | `sauvegarde/build_mac_origine` absent (L60) |
| `test_grue_annulation.py` | 1 ECHEC puis échec | `clang -arch x86_64` refusé sous Linux (L62), puis programme d'origine absent (L73) |
| `test_vitesse_escadrille.py` | échec au démarrage | programme d'origine absent (L148) ; plus loin `clang -arch`, `arch -x86_64` (L203-208) |
| `test_cctv_net.py` | échec au démarrage | programme d'origine absent (L207) ; plus loin `clang -arch`, `nm -m` Apple |
| `test_ecriture_releve.py` | échec au démarrage | programme d'origine absent (L103) |
| `test_vitesse_boutons.py`, `test_releve.py`, `test_horloge.py`, `test_journal.py` | échec à l'import | `lupa` absent ; ils lisent aussi `library_custom_0.lua` dans le jeu installé (chemin Mac `ROM`) |
| `test_courbes.py` | échec | appelle `test_releve.py --lua53` (même cause) |

**Bilan : 11 scripts lancés, 0 terminé, 0 contrôle réussi** (1 ECHEC enregistré, dû à l'option `-arch`).

### 2.2 Ce que j'ai refait à la main (dossier de travail de la session, rien dans le dépôt)

| Contrôle | Résultat |
|---|---|
| Logique de `grue_annulation.c` sur faux gestionnaire : `tests/essai_grue_annulation.c` compilé avec `gcc` (sans `-arch`), + variante ASan/UBSan | **30 / 30 OK**, 0 alerte |
| **Les octets réellement livrés** par `grue_annulation.py` (932 o à 0x100061200) chargés à leur adresse dans un processus de test, mêmes 30 scénarios, avec des « fonctions du jeu » factices posées aux adresses de `push_back`, `clear`, `reset_waypoint_path` | **30 / 30 OK** |
| Crochets A (0x100061200) et B (0x100061230) **sur les octets livrés** : registres `rax rcx rdx rsi rdi r8-r11`, `r12 r13`, `xmm0-xmm15` remplis de sentinelles, indicateur ZF après le `cmpl` rejoué, chemin « dock_state 7 » du crochet A | **8 / 8 OK** |
| `vitesse_escadrille.c` : harnais du test d'origine (adapté aux noms ELF) : fonction Lua + 120 cas de plancher | **12 / 12 Lua, 120 / 120 planchers, 0 écart** |
| Bornes que le test d'origine ne couvre pas (équipe 15, 16, 0xffffffff, table corrompue à 4 ou 255, avion sans équipe, type 9) | **10 / 10 conformes** |
| `cctv_net.s` (TAILLE 512) : harnais du test d'origine adapté | **27 / 27 OK** |
| `ecriture_releve.s` : harnais du test d'origine adapté (fichier ouvert une fois, texte ajouté, repli sur la sortie standard) | **OK** |
| Régénération des greffes avec `clang --target=x86_64-apple-macos` + l'éditeur de liens du dépôt, comparée aux modules | `vitesse_escadrille` **identique octet pour octet** (671 o) ; `cctv_net` identique (439 o) ; `ecriture_releve` identique (165 o) ; `grue_annulation` **différente** (976 o contre 932) : code généré différent, voir I3-d |
| Désassemblage (`objdump -D -b binary`) des octets « avant » de 13 sites de branchement | chaque zone remplacée = **instructions entières**, pas de coupe au milieu |
| Cibles de tous les `call`/`jmp`/accès `rip` des greffes comparées aux tables `JEU` des générateurs | grue 5, vitesse 10, CCTV 9, relevé 3, hélicos 25 cibles : **toutes dans les tables** (les « inconnues » étaient des chaînes et constantes lues comme du code, ou la seconde case d'état de la vitesse, 0x1029e5691) |
| Chevauchements d'octets entre **tous** les modules (`modules/` + `modules_en_reserve/`) | aucun entre modules actifs ; seuls recouvrements : copies identiques `modules/` ↔ réserve, et `helicos_ascenseur` ↔ `helicos_temoin` (exclusifs par conception) |
| Moteur `patchs_cc2.py` sur un **programme synthétique** (octets « avant » des modules écrits à leur place, le reste à zéro, md5 recalculé) : activer / réactiver / retirer / retirer deux fois pour chacun des 9 modules « programme », tous ensemble, module abîmé | **60 / 60 OK** |
| Barre `library_custom_6.lua` avec un faux jeu écrit en Lua pur (Lua 5.4) : enveloppes, clic avalé, clic hors barre transmis, écran < 200, équipe 16, erreur dans `cc2_vitesse`, module programme absent | **11 / 11 OK** |
| Syntaxe Lua 5.4 des 4 scripts (`horloge`, `journal`, `releve`, `vitesse_boutons`) | OK |
| Cas limites du moteur (B1, I1, I5, I6) | **reproduits**, détail dans chaque constat |

Note d'honnêteté : mon premier essai des crochets avait donné un ECHEC sur `xmm0-xmm15` ; c'était un défaut de **mon** harnais
(valeurs sentinelles mal déclarées en assembleur), corrigé ensuite. Les chiffres ci-dessus sont ceux de la version corrigée.

### 2.3 Ce qui n'a PAS pu être exécuté

- Tous les tests qui lisent le programme d'origine ou le jeu installé (§2.1). Donc : jamais vérifié que les octets « avant » des
  modules sont ceux du vrai programme, ni que les md5 annoncés (`773c3319…`, `f03c977f…`, `18e12e18…`, `8655d717…`) se retrouvent.
- La logique Lua de `horloge`, `journal`, `releve` (hors syntaxe) ; la barre sous Lua 5.3 ; `fichiers/effet_tele`.
- La logique C de `helicos_ascenseur.c` (aucun test d'exécution n'existe, voir I4) ; je ne l'ai relue qu'à l'œil.
- Tout ce qui demande le jeu (§5).

---

## 3. Constats

Définitions : **Bloquant** = peut abîmer l'installation ou une garantie annoncée, ou rend une fonction dangereuse à activer avec la
procédure actuelle. **Important** = défaut réel ou trou de test qui peut produire un mauvais comportement ou fausser une décision
avant le prochain essai ou portage. **Mineur** = incohérence, confort, dette.

### 3.1 Bloquants

#### B1 — Le menu de l'Atelier écrit des données périmées par-dessus un programme qui a changé entre-temps
- **Où** : `outil/patchs_cc2.py:169` (le programme n'est lu qu'une fois, dans `Atelier.__init__`), `:311` (`menu` crée l'atelier),
  `:326` (`input()` : l'utilisateur peut attendre des minutes), `:334` (`faire`), `:216-218` (`appliquer` réécrit `self.donnees`
  lu avant l'attente).
- **Scénario** (**EXÉCUTÉ** sur programme synthétique, la logique ne dépend pas du contenu) : le moddeur ouvre le menu → l'outil lit
  `build_mac` → Steam met à jour le jeu en tâche de fond (la mise à jour Windows du 28/10 est arrivée « pendant » qu'une étude
  lisait les fichiers) → le moddeur choisit « Activer helicos_approche_x2 ». `appliquer` n'est pas gêné : `etats()` et
  `programme_reconnu()` se calculent sur les **anciens** octets gardés en mémoire, puis `ecrire(self.programme, …)` remet
  **l'ancien programme + le patch** à la place du nouveau. Dans mon essai, un octet de la « nouvelle version » a disparu.
  **Conséquence probable** (**INFÉRÉ**) : un exécutable ancien avec des données récentes, alors que Steam se croit à jour. Cela
  contredit la promesse de `LISEZ-MOI.txt:49-50` et de la docstring `patchs_cc2.py:22-24`.
- **Aggravant** : la vérification « jeu fermé » n'est pas refaite avant d'écrire (voir I6).
- **Correctif proposé** : dans `appliquer`, juste avant toute écriture, relire le fichier (`lire(self.programme)`), comparer à
  `self.donnees` (ou à son md5) et refuser si différent ; refaire `programme_reconnu()` et la vérification `pgrep` à ce moment-là ;
  écrire seulement ensuite. Test à ajouter : ouvrir un `Atelier`, modifier le fichier, appeler `appliquer` → attendre `Refus`.

#### B2 — `helicos_ascenseur` (en réserve) : ne pas le remettre dans `outil/modules/`, et rien dans le dépôt ne l'en empêche
- **Où** : `outil/generateurs/helicos_ascenseur.c:321` (`pret`), `:482-493` (crochet H3), `generer_helicos_ascenseur.py:206-217`
  (`DOC_NORMAL`), `tests/test_helicos.py:65-148` (le teste comme s'il était livrable). Mesure : `etudes/MESURES_helicos.md:96-105`.
- **Ce qui s'est passé** (**LU**, essai du 24/10) : deux hélicos se sont percutés, le jeu a détruit un Razorbill. Le moddeur a rangé le
  module. Cause « probable, non vérifiée » notée : l'hélico qui descend sur la plateforme (x = 27,5) et un autre qui attend à
  `lift_upper_wait` (x = 12), à 15,5 m.
- **Ce que le code permet de dire** (**INFÉRÉ** de la lecture) : cette situation n'est pas un hasard de timing, elle est dans la
  conception. `pret` (L321) n'exige que « plateforme libre, en haut, aucun appareil en état de piste 7 » ; un appareil **en état 6**
  (il attend à x = 12 que l'ascenseur soit libre) n'empêche pas l'engagement. Et H3 (L482-493) fait justement **attendre à x = 12**
  tout appareil qui veut passer 6 → 7 pendant qu'un hélico descend (bit `ENGAGE`). On fabrique donc exprès la géométrie de la collision.
- **Pourquoi bloquant** : le module est dans `modules_en_reserve/`, et la docstring de sa sortie (`DOC_NORMAL`) ne mentionne pas
  l'échec. La phrase du générateur « on copie dans outil/modules/ celui qu'on veut tester » (L12-13) l'invite à le remettre. Aucun
  test ne fait tourner la logique `hl_tick` (contrairement à la grue), donc un correctif ne serait pas vérifiable hors jeu.
- **Correctif proposé** : (1) ajouter en tête de `DOC_NORMAL` et du module généré « ESSAI DU 24/10 : COLLISION DE DEUX HÉLICOS — NE
  PAS ACTIVER » ; (2) avant toute réactivation, exiger `mgr[0x24]` hors {5, 6, 7} **et** retenir à l'extérieur les appareils qui
  roulent vers le point d'attente tant qu'un hélico est engagé (pas seulement les empêcher de passer 6 → 7), ou décaler le point
  d'attente/d'appontage d'une distance sûre ; (3) écrire un faux gestionnaire pour `hl_tick` sur le modèle de
  `essai_grue_annulation.c` ; (4) voir M9 pour le reste du code.

### 3.2 Importants

#### I1 — Après un changement de build, l'outil refuse avec un message faux, ou plante, et « Tout remettre » ne marche plus
- **Où** : `patchs_cc2.py:162-171` (`__init__` calcule les tables), `:117-120` (contrôle des constantes « rip »), `:73-74`
  (`lire_f32`), `:337-355` (`main`), `:290-296`.
- **Scénario** (**EXÉCUTÉ**, fichiers factices de la bonne taille) :
  - fichier de même taille mais autre contenu (ce que donnerait un nouveau `build_mac` aux constantes décalées ; l'étude de la
    mise à jour Windows mesure un décalage des constantes de +0x38) : `ARRET : ascenseur_x2 : 0x10286995c ne vaut pas 2 x
    0x102869a64`. L'état des modules n'est **pas affiché**, et `--origine` (donc le bouton « Tout remettre CC2 d origine ») **fait
    le même ARRET** ;
  - fichier plus court (ou vide) : **traceback Python brut** `struct.error: unpack_from requires a buffer of at least 42375520
    bytes` ;
  - seul un fichier tout à zéro donne le message voulu (« le programme du jeu n'est pas celui que j'ai analysé (mise à jour
    Steam ?) »).
  Le vrai cas probable sur le Mac est le premier : le message accuse un module et des adresses au lieu de dire « le jeu a changé ».
- **Correctif proposé** : dans `Atelier.__init__`, attraper `struct.error` et l'échec des contrôles « rip » et les convertir en un
  état « programme non reconnu » (md5 actuel affiché, md5 attendu affiché) ; laisser `afficher()` et `--origine` fonctionner en
  lecture seule/avec retrait des seuls modules « fichier ». Tester avec les 3 fichiers factices ci-dessus.

#### I2 — ECO / NORMAL / FLANK : les textes promettent une vitesse de croisière que la mesure du 25/10 dément ; l'effet n'a jamais été observé en jeu
- **Où** : `outil/modules/vitesse_escadrille.py:2,6-7` et `vitesse_boutons.py:4` (« vitesse de croisière »),
  `fichiers/vitesse_boutons/library_custom_6.lua:3`, `etudes/ia_vitesse.md:9-14` (jamais mis à jour). Mesure :
  `DEMARRER_cc2_patchs.md:367`.
- **Fait mesuré** (**LU**) : en ECO (jeu d'origine), un Albatros et un Manta qui vont vers un point à 20 km croisent à ≈ 120 m/s
  (pas 48 / 72) ; le régulateur vise 120 m/s au-delà d'environ 800 m du point, quel que soit le plancher ; le test « près du
  point » a été arrêté, jamais terminé ; les modes ne changent donc la vitesse que **près du point**.
- **Ordre de grandeur** (**INFÉRÉ** de la formule de `ia_vitesse.md` §6, cible = S + a·(120 − S), a = (distance − 20)/780 borné à
  [0, 1] ; la borne haute de `a` y est dite « non identifiée ») : Albatros à 100 m du point, ECO ≈ 55, NORMAL ≈ 67, FLANK ≈ 141 m/s ;
  à 400 m, ≈ 83 / 90 / 132 ; au-delà de 800 m, **120 pour les trois**. Un trajet de 20 km dure donc presque autant en FLANK qu'en ECO.
- **Scénario de défaillance** : le moddeur choisit FLANK pour que ses avions arrivent plus vite ; le temps de transit ne change presque
  pas, mais la consommation augmente près des points (patrouille, escorte, attente à pleine manette : voir `ia_vitesse.md` §3).
  Décision prise sur une promesse fausse.
- **Autre point** : `library_custom_6.lua:31-39` règle **NORMAL tout seul** au premier affichage de la barre (le test le vérifie,
  `test_vitesse_boutons.py:106`) : installer les deux modules change le comportement des avions sans aucun clic. C'est documenté
  dans le module et `DEMARRER`, pas dans `LISEZ-MOI.txt`.
- **Correctif proposé** : réécrire les docstrings et le commentaire du Lua (« vitesse près du point visé »), ajouter un encart
  « mesure du 25/10 » à `ia_vitesse.md` ; terminer la mesure « à 300 m du porte-avions » ; décider si le défaut doit rester
  NORMAL ; si l'objectif est la vitesse de transit, il faut un autre patch (la constante 120 du régulateur, non fait).

#### I3 — `grue_annulation` : des hypothèses de registre et d'état que ni les tests ni le dépôt ne vérifient ; jamais essayé en jeu
- **Où** : `grue_annulation.c:131-134` et `:146` (`movq %rcx, %rdx` : « rcx = carte »), `:93-97`, `:100`.
- **a) `rcx` = la carte au crochet A** (0x1001a8c01) : `rcx` n'est pas un registre conservé par les appels ; la valeur ne vaut que
  si aucune instruction entre l'entrée de `docking_manager_air::undock` (0x1001a8bd4) et le crochet (45 octets plus loin) ne l'écrase.
  La signature (`partage_detail/12_symbol_index.txt:423` : `undock(c_vehicle_server&, c_vehicle_server_carrier&,
  c_map_server_base&)` sur le gestionnaire) place la carte en 4ᵉ argument, donc dans `rcx` à l'entrée : c'est cohérent, mais
  qu'elle y soit **encore** au crochet n'est contrôlé nulle part (`annuler_montee.md:85-88` l'affirme, le test ne le vérifie pas).
  **Scénario** : si c'est faux, le premier second appui valide appelle
  `(*carte)[0]` sur n'importe quoi → plantage du jeu. **Correctif** : script de contrôle (nécessite `build_mac_origine`) qui
  désassemble 0x1001a8bd4..0x1001a8c01 et échoue si `rcx` est écrit ou si un `call` y figure.
- **b) La grue est déclarée libre tout de suite quand l'avion n'est pas encore accroché** (L96-97) alors que sa liste `[5, 2]` est
  encore à jouer. **Scénario** (**INFÉRÉ**) : B est déjà dans la file de sortie ; A est annulé pendant que le crochet descend ; au
  tick suivant le jeu voit « grue libre » et réécrit la liste en `[1, 4, 2, 5]` : le crochet repart horizontalement alors qu'il est
  encore à moitié descendu. Au pire un défaut visuel ; la liste d'essais prévue (`annuler_montee.md` §7) ne couvre pas « annuler A
  alors que B attend dans la file ». **Variante vérifiée sur une copie de travail**
  (**EXÉCUTÉ**) : supprimer ces deux lignes laisse `ag_fin` libérer la grue à la fin des deux gestes (testé : libre après le 2ᵉ
  geste), au prix de quelques secondes. À décider en connaissant le comportement réel du jeu.
- **c)** Reste de rotation jusqu'à 0,01 rad (≈ 0,6°) accepté et jamais remis à zéro (le geste 3 est supprimé de la liste) ;
  l'annulation s'applique aussi à un hélico de la case 0x78 alors que tout est écrit pour « avion » ; NaN accepté (sans importance
  en pratique). Mineur, à noter pour l'essai en jeu.
- **d) « Module périmé ? »** Il n'existe aucun test « module à jour avec le .c » pour la grue (il n'y en a que pour la vitesse,
  `test_vitesse_escadrille.py:157-159`). Ma régénération donne 976 octets contre 932 : écart de **compilateur** (le code livré
  utilise `andps` pour la valeur absolue, le mien deux comparaisons) plutôt que preuve de péremption. Pour trancher sans
  compilateur identique j'ai exécuté **les octets livrés** (§2.2) : ils se comportent comme la source. À garder comme test.

#### I4 — Les tests ne protègent que sur le Mac du moddeur, et ne contrôlent pas la vivacité des registres aux points de branchement
- **Où** : `tests/*.py` (chemins `/Users/UTILISATEUR/…` en dur : `test_patchs.py:72,80`, `test_horloge.py:16`, `test_journal.py:18`,
  `test_vitesse_boutons.py:19`, `test_releve.py:20`) ; `clang -arch`, `arch -x86_64`, `nm -m`, `objdump` au format Apple.
- **Trous précis** :
  1. aucun test ne tourne hors du Mac (§2.1) ; `unittest discover` ne fonctionne pas ;
  2. aucun test ne vérifie qu'un registre écrasé par une greffe est **mort** au point de reprise : `_cctv_a` écrit `rdx`
     (voir I7), le crochet A de la grue lit `rcx` (I3a). Les harnais *déclarent* la liste des registres touchés
     (`test_ecriture_releve.py`, liste de clobbers) : le contrôle est circulaire ;
  3. `helicos_ascenseur.c` (494 lignes) n'a **aucun test d'exécution** ; `test_helicos.py` ne relit que les 3 branchements et les
     cibles ;
  4. pas de test « module à jour » pour grue, CCTV, relevé, hélicos ; les copies `modules/` ↔ `modules_en_reserve/` (4 modules
     identiques) ne sont comparées nulle part ;
  5. `test_patchs.py` écrit dans le dépôt (`fichiers/_test`, L335-336, nettoyé en `finally`) et lit directement le vrai programme
     et le vrai shader du jeu (L72, L80-84), au lieu d'une copie de référence.
- **Correctif proposé** : un mode « hors Mac » (`gcc`/`clang` natifs, `llvm-objdump`, noms ELF) comme celui que j'ai monté ; un script
  de vivacité de registres sur le programme d'origine ; une comparaison automatique `modules/` ↔ réserve ; `unittest` ou un lanceur
  unique qui dit clairement « X ignoré, il manque Y ».

#### I5 — Modules « fichier » : une nouvelle version d'un script bloque son propre retrait, et « Tout remettre » devient tout-ou-rien
- **Où** : `patchs_cc2.py:147-156` (`etat_fichier` compare au **fichier source actuel** du dépôt), `:207-209`.
- **Scénario** (**EXÉCUTÉ**) : `horloge` installé ; on corrige `fichiers/horloge/library_custom_1.lua` ; l'état devient `inconnu` ;
  `--activer horloge` **et** `--retirer horloge` répondent « le fichier … contient autre chose que l'original ou notre version ».
  Un seul fichier non reconnu fait aussi refuser `--origine` en bloc, avant toute écriture (le programme n'est alors pas restauré
  non plus) : **EXÉCUTÉ**, déclenché dans mon essai par un autre fichier (un `rom_0` factice sans le shader) ; même chemin de code
  (`:207-209` lève `Refus` sur le premier module non `actif`/`retire`).
- **Correctif proposé** : garder dans le module la liste des empreintes des versions déjà posées (ou enregistrer l'empreinte
  posée dans `sauvegarde/`), accepter « ancienne version de nous » comme `actif`, et dans `--origine` restaurer ce qui est sûr
  en signalant le reste, au lieu de tout refuser.

#### I6 — « Refuse de tourner si le jeu est ouvert » : trois trous
- **Où** : `patchs_cc2.py:290-296`.
- **Trous** : (1) la vérification est sautée dès qu'**une seule** des options `--programme` / `--rom` est donnée (**EXÉCUTÉ** avec
  un faux `pgrep` qui répond toujours « le jeu tourne » : défaut → « ferme d'abord Carrier Command 2 » ; `--programme x` seul ou
  `--rom x` seul → aucun refus ; l'exception qui suit dans mon essai vient du fichier absent, pas du jeu : l'autre chemin reste
  le **vrai**, sans vérification) ; (2) `pgrep` absent → `FileNotFoundError` non géré (**EXÉCUTÉ**) ;
  (3) la vérification n'est faite qu'une fois, avant l'attente du menu (B1).
- **Correctif proposé** : n'ignorer la vérification que si **les deux** chemins (et `--sauvegarde*`) sont donnés ; l'appeler depuis
  `appliquer` ; gérer l'absence de `pgrep`.

#### I7 — `cctv_net` : deux hypothèses non contrôlées (registre `rdx` au crochet A ; chemin du crochet B vers le crochet D), et les crochets de dessin n'ont jamais tourné en jeu
- **Où** : `outil/generateurs/cctv_net.s:19` (`leaq (%rax,%rcx), %rdx`), `:23` (`movq 0x18(%rdx), %rcx`), commentaire L12-13 ;
  `:59` (échelle à 4,0 écrite au crochet B), `:113` (remise à 0 au crochet D).
- **a) `rdx`** (**EXÉCUTÉ** pour le code ajouté, **LU** pour le reste) : le code d'origine remplacé (45 o) n'écrit pas `rdx` ; la
  greffe l'écrit à chaque création d'écran, et écrase `rcx`/`rax` autrement que l'original sur le chemin CCTV. Le commentaire
  affirme que ces registres sont écrasés juste après 0x1000ad77c ; aucun test ne le vérifie. Indice favorable (**LU**,
  `DEMARRER_cc2_patchs.md:364`) : le 25/10 une partie chargée (123 véhicules, 50 écrans) a été créée sans erreur avec les 14 modules,
  donc le crochet A a tourné — mais « l'affichage CCTV n'a pas été exercé » : B, C et D (dessin) n'ont **jamais** tourné en jeu.
- **b) Chemin B → D** : l'échelle 4,0 posée en B n'est remise à 0 qu'en D (0x10021cf13). Si une sortie de `render_screen` existe
  entre 0x10021ce85 et D (retour anticipé, autre branche), l'échelle reste à 4,0 et **tout** `element_clip::render` suivant
  (interface de pilotage, pause, overlay, qui partagent la fonction) est découpé 4 fois trop grand jusqu'au prochain écran.
  Le test vérifie les accès à la case, pas l'accessibilité de D depuis B.
- **Scénario** : (a) si `rdx` est vivant, tous les écrans du pont sont créés avec une valeur fausse (plantage possible au
  chargement) ; (b) interface de pilotage ou menu pause tronqués après l'affichage de l'écran CCTV.
- **Correctif proposé** : balayage linéaire du code d'origine à partir de 0x1000ad77c (première lecture/écriture de `rdx`, `rcx`,
  `rax`) et recherche de tout chemin de sortie de `render_screen` entre B et D, dans un test sur le programme d'origine ; puis essai
  en jeu : regarder l'écran CCTV, passer d'une caméra à l'autre, ouvrir le pilotage et la pause juste après.

#### I8 — Préparation du portage vers le nouveau build : les garde-fous actuels ne suffiront pas
- **Où** : `generer_*.py` (tables `JEU`), `patchs_cc2.py:96-125`, `helicos_pres_ascenseur.py:21,23`.
- **Constat** : les générateurs vérifient les octets d'origine **aux sites de branchement** (« octets d'origine inattendus ») mais
  **pas** les adresses des fonctions et données de `JEU` (une cinquantaine : `push_back`, `reset_waypoint_path`, `fopen`, tables…).
  Sur un nouveau build, une adresse non mise à jour produirait un module qui appelle autre chose, sans erreur à la génération.
  Les retouches « rip » de `helicos_pres_ascenseur` ont `facteur = None` : **aucune valeur** de constante n'est contrôlée
  (seule `helicos_approche_x2` vérifie « 100,0 = 2 × 50,0 »). Le md5 d'origine est copié dans 4 fichiers
  (`patchs_cc2.py:41`, `generer_cctv_net.py:29`, `generer_helicos_ascenseur.py:22`, `generer_ecriture_releve.py:28`).
  L'étude de mise à jour (`tour/etude_mise_a_jour/ETUDE.md` §9.3) mesure des décalages de code **non uniformes** (0xf0 à 0x130).
- **Correctif proposé** : pour chaque entrée de `JEU`, ajouter la signature attendue (les 8-16 premiers octets, ou une chaîne
  voisine) et la vérifier ; passer les valeurs attendues des constantes « rip » (pas seulement un facteur) ; importer un seul
  `MD5_ORIGINE` ; retrouver les sites par contexte, pas par décalage global.

### 3.3 Mineurs

- **M1 — `LISEZ-MOI.txt` périmé** (`:14` « Les patchs disponibles (24/10/2026) ») : il ne mentionne ni `pont_retour_x2`,
  `grue_annulation`, `cctv_net`, `vitesse_escadrille`, `vitesse_boutons`, ni leur effet par défaut (NORMAL). `:34`
  « presque plus de roulage » est trop fort : `MESURES_helicos.md:107-125` mesure « pont → hangar » de 0:40 à 0:30 et la piste suivante
  donnée 17-19 s après le toucher (25-33 s avant).
- **M2 — Notes qui ne suivent pas le code** : `etudes/annuler_montee.md:83` (« greffe de ~250 octets ») et `:101` (« assembleur pur,
  pas d'appel C ») alors que le crochet B appelle `_ag_fin` en C (932 octets au total) ; mêmes phrases dans
  `partage_detail/02_…`. `etudes/ETUDE_helicos_2e_ascenseur.md` est une **fiche de mission** (consignes, « ne pas gêner l'autre
  conversation »), pas un résultat ; elle n'a pas de statut final. `etudes/ia_vitesse.md:130` (« à trouver en phase 2 ») est périmé.
- **M3 — `generer_cctv_net.py:83` accepte TAILLE = 256**, valeur de l'idée Geometa n° 1499. Or la table d'origine contient déjà des
  images 256 × 256 (type 3) : avec 256, tous ces écrans seraient pris pour le CCTV et mis à l'échelle. Le cas
  `{256, 256, …, 0}` du harnais (`test_cctv_net.py:166`) l'attraperait, mais seulement sur le Mac. Refuser 256 dans le générateur.
- **M4 — `generer_vitesse_escadrille.py:24` : `CHEMIN = os.path.expanduser("~/Library/…")`** : le module généré dépend de la session
  qui le régénère (**EXÉCUTÉ** : dans le cloud, ce serait `/root/Library/…`) ; `generer_ecriture_releve.py:30` a, lui, un chemin
  en dur. Le test « module à jour » le signalerait, sur le Mac seulement. Mettre un chemin explicite ou un paramètre.
- **M5 — Commentaires de zones périmés** : `generer_cctv_net.py:35-37` parle d'une « zone prévue pour annuler la montée » à
  0x10005af40-0x10005c4e0 alors que la grue est à 0x100061200. Chaque générateur ne contrôle que sa propre place (l'outil attrape les
  recouvrements au chargement : vérifié, §2.2).
- **M6 — `releve_cc2.txt` sans limite** (`ecriture_releve.s`, `fopen "a"` jamais fermé) : environ 0,5 Mo par heure selon `LISEZ-MOI`,
  mais tout `print()` de n'importe quel mod y atterrit.
- **M7 — Copies maintenues à la main** : `modules/` et `modules_en_reserve/` ont 4 modules identiques (`cctv_net`, `ecriture_releve`,
  `helicos_approche_x2`, `helicos_pres_ascenseur`) ; seuls 2 générateurs écrivent dans les deux dossiers. Les copies de
  `partage_detail/workshop/` et `passation_windows/` divergent des sources (traductions) : à ne pas prendre pour référence.
- **M8 — `charger_modules`** (`patchs_cc2.py:79-93`) : un `.py` sans `TYPE` donne une trace `AttributeError` ; tous les `.py` sont exécutés.
- **M9 — `helicos_ascenseur.c`, robustesse pour une éventuelle réactivation** : aucun test de pointeur nul (`corps0`, `joint` à
  L241-243) ; `lacher_cargaison` (L201-216) détache la cargaison même si aucune baie n'est libre (`baie < …` L213) et l'appel se
  répète à chaque tick tant que `engage` et `h < 25` ; si `poser` échoue ensuite (L224), la cargaison est déjà lâchée.
- **M10 — `helicos_pres_ascenseur`** : le test (`test_helicos.py:190-191`) vérifie les **adresses** lues (« ## 0x102869af0 ») mais pas les
  **valeurs** 48,0 et 70,0 ; elles ne sont consignées que dans le commentaire généré. Voir I8.

---

## 4. Ce qui m'a paru solide

(Tout est **EXÉCUTÉ** ou **LU** comme indiqué ; rien de ceci ne prouve le comportement en jeu.)

1. **Découpe des sites** : les 13 zones remplacées par un `jmp` ou un `call` contiennent des instructions entières (désassemblage
   des octets « avant »). Les restes sont remplis de `nop` (ou `int3` pour la vitesse, ce qui rend visible un saut mal placé).
2. **Reprise propre au retour** : les greffes rejouent les instructions déplacées et rendent les indicateurs comme l'original.
   Crochets de la grue, **exécutés sur les octets livrés** : `rax rcx rdx rsi rdi r8-r11 r12 r13 xmm0-xmm15` intacts, ZF identique au
   `cmpl` d'origine. Même raisonnement vérifié par lecture pour `_vit_plancher` (les indicateurs finissent comme ceux de l'original,
   deux `push`/`pop` équilibrés, aucun appel). Réserve : ces `push` écrivent sous `rsp` ; c'est sans danger si `tick_control`
   n'utilise pas la zone rouge (**INFÉRÉ** : fonction non feuille) — à confirmer, §5-A.
3. **Vitesse** : 120 cas + 10 bornes (équipe 15 / 16 / 0xffffffff, table corrompue, avion sans équipe, Manta / autre type, équipe IA)
   conformes au modèle ; `rax` et `rcx` rendus intacts ; mode inconnu = jeu d'origine. La fonction Lua `cc2_vitesse` refuse les
   équipes hors 0..15 et les modes hors 1..3.
4. **CCTV** : la comparaison du nom de script lit exactement 23 octets (3 lectures de 8 octets, la dernière chevauchante) après avoir
   contrôlé la longueur 23 : pas de lecture au-delà de la chaîne. Les repères d'alignement SSE (`andps` en mémoire) tombent sur
   des adresses multiples de 16 (vérifié sur la grue : 0x100061590). Les cibles lues sont toutes dans les tables prévues.
5. **Moteur de patchs** (sur programme synthétique) : activer, réactiver, retirer, retirer deux fois, tous ensemble, retour à
   l'octet près ; module abîmé et programme d'une autre version refusés ; chevauchements détectés ; écriture atomique
   (`ecrire`, L64-70 : fichier temporaire + `os.replace`) ; relecture et contrôle de l'état après écriture (L240-243) ;
   analyse d'arguments stricte (L265-287).
6. **Garde d'identité du programme** : `programme_reconnu()` (md5 du programme **reconstruit** en remettant les « avant » des
   modules) bloque toute pose sur un autre build, et reste juste si un module est à moitié posé.
7. **Bonnes habitudes** : le test CCTV contrôle aussi qu'aucun saut du jeu n'atterrit au milieu des octets remplacés et que la case
   d'échelle n'est utilisée que par la greffe et le code mort ; la barre Lua est protégée par `pcall`, ne casse pas l'écran et se
   dégrade proprement sans le module programme ; `ecriture_releve` retombe sur la sortie standard si le fichier ne s'ouvre pas.
8. **Cohérence des chiffres** : adresses des constantes (48,0 à 0x102869af0, 120,0 à 0x1028697b8, 100,0 à 0x1028697ac, 144 à
   0x102869b2c…) concordent entre `ia_vitesse.md`, `helicos_pres_ascenseur.py`, `helicos_approche_x2.py` et la vitesse ; le décalage
   23,5 = 0,5 × (7 − (−40)) est exact et relu dans les octets ; les zones de code mort du `DEMARRER` (0x10005d000-0x10005d29f,
   0x100061200-0x1000615a4, 0x100061800-0x1000619b7, 0x100061a00-0x100061aa5, 0x100061b80-0x100061b9c) sont bien celles des modules.
9. **Honnêteté des notes** : `MESURES_helicos.md` consigne l'échec de l'ascenseur ; `DEMARRER` dit que la grue, le CCTV et la vitesse
   ne sont « pas essayés en jeu » et que la mesure de vitesse « n'a jamais été terminée ».

---

## 5. Non vérifiable sans le jeu (ou sans le programme d'origine)

À faire sur le Mac, par ordre d'utilité. Rien de ceci n'est établi par ce rapport.

**A. Avec `build_mac_origine`, sans lancer le jeu**
1. Lancer les tests existants tels quels (ils lisent le programme d'origine) pour confirmer que les md5 annoncés se retrouvent.
2. Balayage de registres : `rcx` entre 0x1001a8bd4 et 0x1001a8c01 (I3a) ; `rdx`, `rcx`, `rax` après 0x1000ad77c (I7) ; registres
   libres à 0x10283aed0 / 0x10283af78 (relevé).
3. Alignement de pile aux points d'entrée (`rsp` multiple de 16 à 0x1001a8c01, 0x1001ad9ad, 0x10283aed0, 0x1001acd94) : toutes les
   greffes l'affirment, aucun test ne le contrôle. Et absence de zone rouge dans `tick_control` (0x1001c26c0), qui permet les
   `push` de `_vit_plancher` sous `rsp`.
4. « Code mort » : confirmer qu'`ImGui::ShowDemoWindow` n'est référencée par aucune table de pointeurs (`__DATA`), pas seulement par
   des `call`/`jmp` relatifs ; les docstrings affirment « jamais appelé » (les tests CCTV vérifient les `call`/`jmp`, pas les pointeurs).
5. Cases mémoire « libres » : 0x1029e5680-0x1029e5691 (`g_vit_modes` / `g_vit_etat`), 0x102a2a864 (échelle CCTV), 0x102a2a828 (relevé),
   `base_funcs` à 0x1029dd310 (entrée réécrite dans une section rebasée par dyld).

**B. En jeu**
- *Grue* : second appui (a) pendant que la grue va à la baie, (b) quand elle tient l'avion, (c) pendant la rotation (doit refuser),
  (d) sur l'ascenseur (doit ne rien faire) ; (e) annuler A pendant que B attend (I3b) ; (f) sauvegarder puis recharger pendant un
  retour ; (g) un hélico dans la case 0x78.
- *CCTV* : les deux caméras, boutons ‹ ›, interface entière à la même place, les 34 autres écrans inchangés, courbes du lag avant /
  après, partie rechargée.
- *Vitesse* : mesurer la vitesse **près du point** (300 m) en ECO / NORMAL / FLANK pour un Albatros et un Manta ; vérifier que
  `update_get_screen_team_id()` est bien la même numérotation que `c_team_server+0x14` ; partie hébergée / invité.
- *Hélicos* (modules actifs) : avions et hélicos rappelés ensemble, navire en route, Petrel chargé, ascenseur occupé à l'arrivée.
- *Relevé* : taille du fichier après plusieurs heures ; comportement de `print()` si le dossier n'existe pas.
- *Après mise à jour Mac* : voir §6.3.

---

## 6. Les cas limites demandés

### 6.1 Hélicos sans ascenseur libre
- **Modules actifs** (`helicos_approche_x2`, `helicos_pres_ascenseur`) : ils ne changent que le point visé (50 → 100 m), le point
  visé maximal (z = 52 → −20), le seuil train / état atterrissage (20 → 70 m) et la hauteur visée (décalage de 23,5 m). Rien dans
  leurs octets ne touche à l'attente de l'ascenseur ni à la libération de la piste (**LU**). Si l'ascenseur n'est pas libre, l'hélico
  se pose puis attend comme dans le jeu d'origine à `lift_upper_wait` (`partage_detail/04_helicopters.txt` §1, **LU** des notes, non
  revérifié) ; la piste suivante n'est donnée qu'à son entrée dans la case ascenseur. Le point d'attente (x = 12, z = −32) est à
  ≈ 14 m du point de toucher (x = 0, z = −40) : d'après les notes, il n'y a qu'une case « piste », donc deux hélicos ne s'y trouvent
  pas en même temps (**INFÉRÉ**).
  **Jamais mesuré** : mélange avions + hélicos dans le même rappel, navire en mouvement, ascenseur occupé par un avion au rangement
  (mesures du 24/10 : 4 hélicos, navire à l'arrêt ; mesure du 25/10 : 4 avions avec tous les patchs).
- **`helicos_ascenseur` (réserve)** : `choisir` (L378-419) ne prend un hélico que si une place d'ascenseur est libre
  (`g_bay_index_attach` L384) ; `piloter` attend au-dessus de la plateforme au plus `TICKS_MAX` = 6 000 ticks (200 s) puis
  renvoie à la piste (`renvoyer_vers_piste`, L180-198) ; mais voir B2 et M9.

### 6.2 Annulation d'une « montée » pendant une sortie (grue_annulation)
| Moment de l'avion | Ce que fait le module | Preuve |
|---|---|---|
| Dans la file de sortie | rien de nouveau, le jeu annule déjà | **LU** (`annuler_montee.md` §2) |
| Grue en route vers la baie, ou en train de descendre | annule : liste `[5, 2]`, grue libérée tout de suite, avion « au hangar » | **EXÉCUTÉ** (octets livrés) ; effet en jeu inconnu ; I3b |
| Avion accroché, pas encore tourné (\|rot\| ≤ 0,01) | annule : liste `[4, 1, 5, 2]`, la grue le rapporte, le repose, revient | **EXÉCUTÉ** |
| Avion en train d'être retourné (côté droit) | refuse, comme avant | **EXÉCUTÉ** |
| Lâché au-dessus de l'ascenseur, ou liste vide | refuse | **EXÉCUTÉ** |
| **Sur l'ascenseur (la « montée » proprement dite)** | **refuse : `mgr[0x78] != id` → rien** | **LU** : l'étude a écarté ce cas (difficulté 8/10) |
| Sur la piste, en attente (dock_state 7) | l'original est rejoué (« vas-y ») | **EXÉCUTÉ** (crochet A) |
| Troisième appui pendant le retour | refuse (dock_state 4) | **EXÉCUTÉ** |
| Autre avion que celui de la grue | refuse | **EXÉCUTÉ** |
Donc « annuler la montée » au sens de l'ascenseur **n'est pas livré** ; le module n'annule que la phase grue. L'appui sur un avion qui
monte sur l'ascenseur reste sans effet ni retour visuel, comme avant.

### 6.3 Si le jeu change de build (28/10)
- Ce que dit l'étude (`tour/etude_mise_a_jour/ETUDE.md`) concerne l'**exe Windows** ; pour le Mac, rien n'est mesuré (ETUDE §3 f) :
  « Je n'y ai pas accès » ; §6 : tout y est **INFÉRÉ**). Le `MD5_ORIGINE` du Mac est celui du 05/01/2026 (`patchs_cc2.py:41`).
- **Si le `build_mac` du Mac a changé** : l'Atelier ne touchera pas au programme (garde md5 — solide) mais affichera le message de I1 ;
  Steam aura remplacé le programme par un exemplaire sans nos retouches (**INFÉRÉ**, c'est ce qui s'est passé sur Windows). Les
  modules Lua restent posés ; la barre de vitesse disparaît d'elle-même faute de `cc2_vitesse` (**EXÉCUTÉ** : « sans cc2_vitesse :
  pas de barre »), le relevé perd ses `print()` (**LU** : `releve.py:9`).
- **Pour porter** : voir I8. Tous les générateurs échoueront aux sites de branchement (« octets d'origine inattendus ») — c'est le
  bon comportement —, mais pas aux adresses de `JEU`. Les contrôles de la section 5-A sont à refaire sur le nouveau programme.
- **Avant de rouvrir le menu** : corriger B1 (sinon une mise à jour qui tombe pendant le menu est écrasée).

---

## 7. Annexe : comment refaire mes contrôles

Dossier de travail de la session (éphémère, **pas dans le dépôt**) :
`/tmp/claude-0/-home-user-cc2-patchs/[id]/scratchpad/`

| Contrôle | Fichier(s) |
|---|---|
| Chevauchements, cibles d'appels, désassemblage | `outils/chevauchements.py`, `outils/cibles.py`, `outils/desasm.py` |
| Moteur sur programme synthétique | `outils/moteur_synthetique.py` |
| Fausses versions du programme (I1) | `maj/` (+ commande `patchs_cc2.py --programme … --rom …`) |
| Grue, logique (source) / octets livrés / crochets | `run_grue/`, `run_grue_octets/essai_octets`, `run_grue_octets/crochets` |
| Variante « grue pas libérée tout de suite » | `variante_grue/` |
| Vitesse (harnais ELF + bornes) | `run_vit/` |
| CCTV, relevé | `run_cctv/`, `run_rel/` |
| Lanceur Lua fait maison + essai de la barre | `lua/runlua.c`, `lua/essai_vitesse.lua` |
| Régénération des greffes | `regen/` |

Principe commun : ne rien modifier dans le dépôt, travailler sur des copies, adapter seulement les noms de symboles Mach-O (`_nom` →
`nom`) pour compiler sous Linux. Le programme d'origine, lui, doit être fourni par le moddeur (`sauvegarde/build_mac_origine`) pour tout
ce qui dépend des octets réels.

# Revue indépendante — patchs « atterrissage » et « roulage retour »

Relecture du 29/10/2026, session cloud, branche `[branche]`. **Aucun fichier existant du dépôt n'a été modifié** ; ce rapport est le seul fichier ajouté. Aucun paquet installé, aucun accès réseau utilisé.

**Cette session n'a ni le jeu, ni Steam, ni `build_mac`, ni `carrier_command.exe`.** Je ne conclus donc nulle part qu'un patch « marche en jeu ». Quand une phrase dit « vérifié », c'est sur du texte, des octets reconstruits ou un faux programme synthétique, jamais sur le jeu.

Étiquettes de preuve : **LU** (relu dans un fichier) · **CALCULÉ** (recalculé par moi) · **EXÉCUTÉ** (rejoué sur un banc synthétique, voir §1) · **INFÉRÉ** (déduit, non prouvé).

Gravité :
- **Bloquant** : ne pas lancer la commande / ne pas poser / ne pas conclure tant que ce n'est pas levé.
- **Important** : le patch ou son outil peut mal se comporter, ou une décision repose sur une base fausse.
- **Mineur** : défaut de robustesse, de lisibilité ou de documentation.

---

## 0. En bref

| Axe demandé | Verdict | Détail |
|---|---|---|
| Octets d'origine vérifiés avant écriture, idempotence, retrait exact | **Solide côté Mac** (atelier) et côté Windows (`patch_exe.py`), sauf les pièges B1, I4, I5, M1 | §5 et constats |
| Refus si le jeu tourne | **Défaillant dans un cas** côté Mac (I5) ; côté Windows ne voit que `carrier_command.exe` (M12) | |
| Sauvegarde | Mac : reconstruite, jamais revérifiée (M6). Windows : exigée et vérifiée par sha256, mais mal utilisée au retrait (B1) | |
| Changement de build (28/10) | Les deux outils **refusent d'activer** sur un build inconnu. Mais `patch_exe.py retirer --sauvegarde` **écrase l'exe de Steam par l'ancien build** (B1), et `patch_exe.py` ne sait pas tenir deux builds (I3) | §3 |
| Arithmétique des octets | **Correcte** : 0 écart sur les 3 modules Mac décodés par `objdump`, 6 champs Windows recalculés | §5 |
| Modèle de circuit et simulation de file | Géométrie exacte (12 340 / 7 540 m ; 154,3 / 94,3 s ; fenêtre 1 032 + 1 029 m). **Calibration insuffisante** (tour réel, unités de temps, hétérogénéité) et **décision sur le créneau non cohérente avec le simulateur** (I6, I7) | |
| Cohérence notes / modules / générateurs | Adresses et valeurs cohérentes ; plusieurs promesses de texte plus larges que le code (M10) | |
| Tests | **Aucun ne peut tourner hors de la machine du moddeur avec le jeu exact** (I8) | §4 |
| Cas limites (plusieurs avions, hélicos, panne) | Non modélisés par le simulateur ; hélicos et panne : non vérifiables ici | §6 |

Un seul constat **bloquant** (B1). Les trois plus importants pour la suite : **I1** (le bloc de test de piste du créneau, jamais exécuté, repose sur un argument contredit par sa propre première instruction), **I2** (le port Windows de `pont_retour_x2` change tout ce qui lit un registre, pas seulement le roulage), **I7** (la conclusion « le créneau gagne au plus 27 s », tirée d'un seul essai, n'est pas cohérente avec le simulateur à l'occupation de piste mesurée).

---

## 1. Ce qui a pu et n'a pas pu être exécuté

**Exécuté (Python 3.13, GNU objdump ; rien installé) :**

| Quoi | Résultat |
|---|---|
| `python3 -I tests/test_patchs.py` | **Échec immédiat** : `FileNotFoundError` ligne 72 (`shutil.copyfile(P.PROGRAMME, …)` : le `build_mac` du moddeur est absent). Code de sortie 1. **Aucun des contrôles n'a tourné.** |
| Les 10 autres fichiers de `tests/` et `tour/outils/test_patch_exe.py` (11 au total) | Tous en échec pour la même raison : `sauvegarde/build_mac_origine` absent (5), module `lupa` absent (4), module `capstone` absent (1), `test_courbes.py` : `IndexError`. Je n'ai **pas** installé `lupa` ni `capstone` (installation = accès réseau + code tiers, à décider par le moddeur ; voir §4 pour des alternatives maison). |
| `outil/generateurs/simuler_file_atterrissage.py` | Tourne. Sortie reproduite (§7). |
| `tour/etudes_circuit_atterrissage/modele_circuit.py` | Tourne, ses `assert` passent (ordre 0→1→2→3→4→5→0 dans les deux cas). |
| `trajets_circuit.py` | Tourne sur **journaux synthétiques** que j'ai fabriqués (cercle R = 830, R = 1200, ovale). |
| Décodage `objdump` des octets avant/après de `atterrissage`, `pont_retour_x2`, `ascenseur_x2` | 0 écart (§5). |
| **Banc synthétique de l'atelier Mac** | Faux `build_mac` de 44 Mo où chaque module programme trouve ses octets d'origine ; `MD5_ORIGINE` remplacé **en mémoire** par le md5 du faux programme ; vrais modules, vraie `patchs_cc2.py`. Scénarios : cycle, idempotence, 6 permutations d'ordre, abîmé, build décalé, chevauchement, contrôle « jeu ouvert », atomicité, piège A/B. |
| **Banc synthétique de `patch_exe.py`** | Faux exe aléatoire de 11 353 600 octets avec les octets d'origine des JSON plantés, JSON copiés avec le sha256 du faux original, `tasklist` simulé par un script. Scénarios : cycle, build inconnu, retrait avec/sans sauvegarde, deux builds. |
| JSON Windows | Recoupements entre modules : 0. `va − offset` = `0x400c00` partout dans `.text`. Déplacements de saut S1–S3 et encodage des flottants recalculés à la main : identiques. |
| Modèle de roulage de `etudes/piste_et_pont.md` | Recalculé : 28,7 / 14,7 / 10,1 s (état 5) et 42,5 / 22,4 / 15,7 s (total), pour ×1 / ×2 / ×3. Conforme au tableau. |

**Non exécuté, faute du jeu ou d'un paquet absent :** `verifier_sites.py`, `generer_modules.py`, `generer_modules_atterrissage.py`, `analyse_registre.py` (tous exigent l'exe Windows et `capstone`) ; `generer_atterrissage.py` et `generer_pont_retour.py` (exigent le Mach-O d'origine **et** l'`objdump`/`as -arch` d'Apple, `as -arch x86_64` n'existe pas sur Linux) ; `tour/outils/test_patch_exe.py`. Les « 35 contrôles » et « 157 contrôles » cités dans les ETUDE sont donc **non reproduits ici**.

Mes scripts de banc sont dans `/tmp/claude-0/-home-user-cc2-patchs/[id]/scratchpad/` (`banc_atelier.py`, `banc_ab.py`, `verif_octets.py`, `sim_verif.py`, `roulage_modele.py`, `fab_log.py`, `pe_banc/`). Ils sont éphémères et **pas dans le dépôt** (consigne : rapport seul) ; je peux les y ajouter sous `tests/` si le moddeur le demande.

---

## 2. Constats

### BLOQUANT

#### B1 — `patch_exe.py retirer --sauvegarde` remplace tout l'exe sur un état « INCONNU » (rétrogradation silencieuse)
- **Où** : `tour/outils/patch_exe.py:255-262` (hors liste, mais la commande fautive est écrite dans le périmètre : `tour/etudes_roulage_retour/ETUDE.md:64`).
- **Preuve** : EXÉCUTÉ sur le banc synthétique. Avec un exe « nouveau build » (contenu différent) et une sauvegarde valide de l'ancien original :
  ```
  Etat      : INCONNU (41 endroit(s) ne contiennent ni l'original ni le patch … autre version du jeu ?)
  retirer SANS --sauvegarde  -> REFUS : etat INCONNU … Donne --sauvegarde …        (fichier inchangé)
  retirer AVEC --sauvegarde  -> Etat INCONNU : je remets la COPIE DE SAUVEGARDE entiere (tous les modules sont retires).
                                FAIT : fichier remplace par la sauvegarde (sha256 verifie).
                                sha256 du fichier = sha256 de l'ancien original
  ```
- **Scénario concret** : le `carrier_command.exe` de Steam est aujourd'hui `461E1262…` (état « INCONNU » pour l'outil, `tour/etude_mise_a_jour/ETUDE.md:46`). Quelqu'un rejoue le « Retour arrière » de `ETUDE.md:64` de l'étude roulage (`retirer … --module pont_retour_x2 --sauvegarde tour/sauvegardes/carrier_command_1.5.18_original.exe --cest-le-vrai-jeu`) pour « nettoyer ». L'outil remplace le build Steam du 28/10 par le build de juin `1C9A01C3…`, en affichant seulement « tous les modules sont retirés ». Conséquences (INFÉRÉES) : exe ancien + fichiers Steam du 28/10 ; l'horodatage PE ancien réactive le SDK `dinput8.dll` (`tour/etude_mise_a_jour/ETUDE.md:12`) ; Steam réécrasera à la prochaine vérification. Pas de perte de partie, mais c'est l'inverse de « retirer », sans avertissement ni sha256 du fichier remplacé affiché.
- **Correctif proposé** : n'autoriser le repli sur la sauvegarde que pour l'état `melange` (tous les endroits connus, mais module à moitié posé). Sur `inconnu`, **refuser**, afficher les deux sha256 (fichier courant, sauvegarde) et n'accepter qu'un drapeau explicite `--remplacer-par-la-sauvegarde` plus le préfixe du sha256 courant tapé par l'utilisateur. Retirer ou marquer « obsolète » la ligne `ETUDE.md:64` de l'étude roulage (le module a été effacé par Steam).

---

### IMPORTANT

#### I1 — Bloc de test de piste du créneau : l'argument « aucun registre attendu » est contredit par sa première instruction ; jamais exécuté
- **Où** : `tour/etudes_circuit_atterrissage/ETUDE.md:72`, `verifier_sites.py:31` et `:167` ; équivalent Mac : `outil/generateurs/generer_atterrissage.py:20` (bloc `0x1001af914`).
- **Constat (LU)** : l'ETUDE justifie les trois sauts S1/S2/S3 par « le bloc n'attend aucun registre (il relit tout dans la pile) ». Or `verifier_sites.py:167` vérifie lui-même que le bloc commence par `cmp dword ptr [edi], 1` (octets `833f01`) : une lecture **via `edi`**. Sur le chemin d'origine, le code qui précède le bloc (écriture de l'état 1→2) s'exécute avant ; sur les trois nouveaux chemins il est contourné. Ni l'ETUDE ni le script ne vérifient que `edi` (ni aucun autre registre ou drapeau lu avant d'être écrit dans le bloc) a la même valeur sur les deux types de chemin. Il n'existe pas ici d'équivalent de `analyse_registre.py` pour ce bloc.
- **Indice côté Mac** : l'ETUDE (`:81`) cite une réponse du Mac disant que le terme en x du test de distance est « le contenu d'un registre laissé par le code précédent », ce qui est **exactement** une dépendance à un registre vivant à l'entrée du même bloc. La fenêtre « 2,7 km » du Mac (1 031 + 1 684 m) pourrait donc dépendre du chemin d'entrée ; or les trois chemins ajoutés par le patch Mac n'ont jamais été distingués dans cette analyse. Le fichier cité (`passation_windows/REPONSES_mac_pour_la_tour_28-10.md`) **n'existe pas dans le dépôt** ; `REPONSES_mac_pour_la_tour.md` existe mais sa Q3 porte sur l'énergie 0,4. L'explication ne peut donc pas être vérifiée.
- **Scénario** : sur Windows, si `edi` n'est pas le pointeur du gestionnaire sur le chemin S1 (le compilateur peut le recharger entre l'écriture d'état et le bloc), `cmp [edi],1` lit une valeur quelconque : au mieux le test échoue toujours (aucun gain), au pire violation d'accès au premier avion en virage arrière (partie perdue ; le plantage au chargement de sauvegarde étant déjà connu, `ETUDE.md:113`).
- **Correctif** : avant toute pose du créneau sur le vrai exe, calculer l'ensemble des registres/drapeaux **vivants à l'entrée** du bloc `0x701a2a` (analyse en avant jusqu'à la première écriture) et montrer, pour chacun, que ses définitions atteignant le bloc sont identiques sur l'arête d'origine et sur S1/S2/S3. Ajouter ce contrôle à `verifier_sites.py`. À défaut, passer par un petit trampoline qui recharge `edi`. Et réconcilier la fenêtre Mac (2,7 km) avec la fenêtre Windows (2,06 km) **en retrouvant la source** du « registre laissé ».

#### I2 — Port Windows de `pont_retour_x2` : un seul chargement de registre commun, analyse non sûre et non archivée
- **Où** : `tour/etudes_roulage_retour/ETUDE.md:23-29` et `:70`, `analyse_registre.py:4`, `:8`, `:28`, `:44`, `:62`, `modules/pont_retour_x2.json`.
- **Constat (LU)** : sur le Mac, le patch modifie **trois** lectures de `30,0`, et `generer_pont_retour.py:68-74` prouve que chacune n'est atteinte que depuis son propre état (liste exacte des sauts sources). Sur Windows, le patch modifie **un seul** `movss xmm7,[30.0]` en début de boucle, et change donc **toute lecture de `xmm7` que cette définition atteint**. L'ETUDE en nomme deux (la queue `0x7007e3` des états 5-7, et la queue de roulage du **départ** `0x700c10`, « sur le chemin direct »). La garantie est plus faible que celle du Mac (« aucun nouveau risque »).
- **L'analyse n'est pas sûre** :
  - `analyse_registre.py:28` : tout `jmp` indirect hors de la table `tables` retourne `[]` (successeurs perdus) → des consommateurs atteints peuvent manquer ;
  - `analyse_registre.py:44` : l'effet des appels est désactivé (`if False:`) ; l'ETUDE (`:70`) l'admet (« suppose que les appels conservent `xmm7` ») ;
  - `:62` imprime un drapeau `st3mul` (le `mulss` de l'état 3, `0x6fedd5`) dont **aucun résultat n'est consigné** dans l'ETUDE ;
  - `:4` charge `verifier_sites.py` par un chemin absolu `C:\Users\UTILISATEUR\…` et `:8` fixe l'entrée `0x6FC7E0` ; pas de docstring ni d'usage ;
  - **la sortie complète n'est dans aucun fichier du dépôt** (seules deux adresses sont citées en prose).
- **Scénario** : tout autre consommateur de `xmm7` atteint par cette définition (progression de l'approche de l'état 3, état 4 « rails », entrée/sortie d'ascenseur, branche hélico) tourne silencieusement ×2. Le témoin « approche 0:52 » (utilisé par l'ETUDE circuit, `:120`) détecterait une dérive grossière, pas une petite ; le départ ×2 est déjà admis comme possible mais « à mesurer ».
- **Correctif** : (1) archiver la sortie complète et signée par un sha256 de l'exe analysé ; (2) rendre l'analyse conservatrice (tout `jmp` indirect inconnu = tous les blocs possibles ; appels = définition inconnue sauf preuve que l'appelé n'écrit pas `xmm7`) ; (3) reporter dans l'ETUDE **tous** les consommateurs, pas deux ; (4) ne pas reprendre ce choix à un seul site sur le nouveau build sans refaire l'analyse (les adresses ont bougé de 0 à `0x190`, `tour/etude_mise_a_jour/ETUDE.md:11`, `PASSATION.md` §2) ; (5) si la queue commune ne peut pas être isolée, le dire dans le **titre** du module (« roulage ×2, départs inclus ») plutôt que seulement dans l'avertissement.

#### I3 — `patch_exe.py` ne peut pas tenir deux builds : le plan de portage s'y heurte
- **Où** : `tour/outils/patch_exe.py:49-60` (`charger_tous`).
- **Preuve** : EXÉCUTÉ. Avec un JSON supplémentaire portant un autre `sha256_origine` dans `modules_exe/` : `REFUS : les modules ne partagent pas le meme sha256 d'origine.` (pour toutes les commandes, y compris `etat`).
- **Scénario** : le plan « nouveaux fichiers JSON pour le build `0x6ae228f3` » (`tour/etude_mise_a_jour/ETUDE.md:46`) coexiste mal avec les JSON de l'ancien build, toujours nécessaires pour la voie A (copies d'essai). L'outil se bloque dès le premier ajout.
- **Correctif** : un sous-dossier par build (`modules_exe/<8 premiers sha256>/`) choisi d'après le sha256 de `--exe` ; vérifier aussi `build.horodatage_pe` et `build.taille` du JSON contre l'en-tête du fichier (aujourd'hui seuls les octets et le sha256 comptent).

#### I4 — Atelier Mac : permuter le réglage A (réserve) et B (`modules/`) laisse un état « abîmé » que l'outil ne sait pas réparer
- **Où** : `outil/patchs_cc2.py:200-204` (refus sur « abîmé »), `outil/modules_en_reserve/atterrissage_creneau.py:9-10` et `outil/generateurs/generer_atterrissage.py:141-146` (la consigne « à utiliser si B est plus lent »).
- **Preuve** : EXÉCUTÉ (`banc_ab.py`). Réglage A actif (via le dossier de réserve), puis atelier standard (B) :
  ```
  etat de 'atterrissage' (B) : abime | programme reconnu : True
  retirer atterrissage -> REFUS : le module atterrissage est abime
  --origine            -> REFUS : le module atterrissage est abime
  activer atterrissage -> REFUS : le module atterrissage est abime
  ```
- **Scénario** : le moddeur active A pour essayer, puis rétablit le dossier standard (ou l'inverse). Les 3 retouches d'A sont un sous-ensemble de celles de B → B voit « 3 modifiées, 7 d'origine » = abîmé. Le bouton « Tout remettre CC2 d'origine » (`LISEZ-MOI.txt:11-12`, « le jeu redevient exactement celui de Steam ») **refuse**, alors que le programme est reconnu et que `original_reconstruit()` sait exactement quoi écrire. Seule issue : « Vérifier l'intégrité » dans Steam.
- **Correctif** : une commande `--reparer` qui, **si `programme_reconnu()`**, réécrit l'original reconstruit puis réapplique l'état demandé ; ou, sans nouveau mode, faire accepter à `--origine` les modules « abîmés » dès que le md5 reconstruit est bon (le refus d'un module abîmé protège contre un build inconnu, déjà couvert par le md5).

#### I5 — Atelier Mac : le contrôle « jeu fermé » est sauté dès qu'un seul chemin est surchargé
- **Où** : `outil/patchs_cc2.py:290-296` (`ouvrir`).
- **Preuve** : EXÉCUTÉ (`pgrep` simulé « jeu en cours »). Sans option : `ferme d'abord Carrier Command 2.` (OK). Avec **seulement** `--rom autre_dossier` (programme = le vrai) : **aucun refus**, `pgrep` n'est même pas appelé. `--sauvegarde` seul : refus (OK).
- **Scénario** : un essai « sur copie » lancé avec `--rom` seulement (le cas typique d'un test de fichier) écrit le **vrai** `build_mac` pendant que le jeu tourne. L'accident du 23/10 sur les options collées (`tests/test_patchs.py:348`) montre que ce genre de faute arrive.
- **Correctif** : tester le jeu dès que **l'un** des chemins écrit est le vrai : `if programme == PROGRAMME or rom == ROM: …pgrep…`. Mettre à jour la docstring (`:17-18`). Ajouter le test manquant.

#### I6 — Calibration du modèle et du simulateur : tour réel, unités de temps, vitesses hétérogènes
- **Où** : `outil/generateurs/simuler_file_atterrissage.py:11-21`, `tour/etudes_circuit_atterrissage/modele_circuit.py:23`, `ETUDE.md:189-191`, `essais/essai1_trajets.txt`.
- **(a) Le tour réel n'est pas le tour théorique, ni le même pour tous.** `essai1_trajets.txt` : avion 17 → 60 s/tour (r = 808 m), avion 18 → 64 s (r = 840 m), **avion 9 → 98 s/tour (r = 958 m)**, avion 10 → ajustement non concluant. CALCULÉ : 2π·808/60 = 84,6 m/s, mais 2π·958/98 = **61 m/s** (loin des 80 m/s « imposés »). L'ETUDE (`:190`) retient « ≈ 60 s » comme tour réel ; l'avion 9 contredit cette généralisation, et `ETUDE.md:120` annonce encore « ≈ 1:35 de plus au cercle » par tour perdu. Le simulateur suppose un tour unique de 94 s et des avions identiques, alors que la file mêle des types à tours différents (dépassements possibles).
- **(b) Deux bases de temps non réconciliées.** `ETUDE.md:191` : rapport mesuré ≈ 1,56 entre le journal affiché et celui du SDK. CALCULÉ : 60 s × 1,56 ≈ 94 s, le tour *théorique*. Je ne sais pas laquelle est juste, et la coïncidence est troublante. Tant que ce rapport n'est pas expliqué, **toute comparaison entre un chiffre du modèle/SDK et un chiffre du journal affiché est invalide** (occupation de piste 1:40, plancher 8:00-8:30, « attente perdue »).
- **(c) Géométrie de la fenêtre.** CALCULÉ : la fenêtre « distance à la porte < 1 000 m » vaut ±1 031 m pour r = 1 200, mais seulement **1,57-1,80 km (≈ 20-22 s)** pour les rayons réellement volés (808-958 m), au lieu des 2,06 km / 26 s annoncés. Le simulateur garde en plus la fenêtre **asymétrique du Mac** (`APRES = 1 684`, ligne 15) alors que l'ETUDE (`:81`) établit que Windows a 1 031 des deux côtés. Impact CALCULÉ (4 avions dispersés, O = 95 s) : créneau seul 491 → 512 s, réglage B 419 → 427 s : petit, mais non nul.
- **(d) Rayon et distance au bateau.** Le « 859 m au plus près du bateau » (`atterrissage.py:10`) est exact pour r = 1 200 (CALCULÉ : 2 059 − 1 200). Avec les rayons réels c'est ≥ 1,1 km : plus sûr, mais les notes ne le disent pas.
- **Correctif** : élucider le 1,56 d'abord (une mesure : un avion en attente, deux horloges) ; recaler `V`, le tour et la fenêtre par type d'avion sur `trajets_circuit.py` ; passer `APRES` à 1 031 pour Windows ; modéliser des vitesses de tour différentes par avion.

#### I7 — La décision sur le créneau n'est pas cohérente avec le simulateur à l'occupation de piste mesurée
- **Où** : `tour/etudes_circuit_atterrissage/ETUDE.md:94`, `:186-187`, `PASSATION.md` §4 ; `simuler_file_atterrissage.py`.
- **Constat** : l'ETUDE conclut, d'**un seul essai** au cercle (attentes perdues −1, +4, +23 s contre +11, +47, +34 s à l'ovale), que le créneau gagne « au plus l'attente perdue restante (27 s en tout) » et que « le cercle fait l'essentiel du gain ». Or l'occupation de piste mesurée est ≈ **100 s** (`:186`), juste au-dessus d'un tour de 94 s : zone où un petit retard fait perdre un tour entier, donc où un essai peut être favorable par chance. CALCULÉ avec le script committé (4 avions, circuit cercle, sans puis avec créneau) :

  | O (s) | groupés : cercle seul → **B** | dispersés (400 tirages) : cercle seul → **B** |
  |---|---|---|
  | 94 | 412 → 400 s | 453 → 418 s |
  | 96 | 414 → 402 s | 471 → 421 s |
  | **100** | **513 → 412 s** | **499 → 430 s** |
  | 104 | 607 → 428 s | 529 → 441 s |
  | 110 | 711 → 510 s | 561 → 459 s |

  Le modèle place donc la plus grande valeur du créneau **exactement** vers O ≈ 100-110 s (falaise du « tour perdu »), de 70 à 100 s sur 4 avions, soit 3 à 4 fois le « 27 s » de l'ETUDE. C'est la zone la plus sensible aux erreurs d'unité de I6(b).
- **Chiffres non reproductibles** : `ETUDE.md:94` cite « cercle seul 6:50-7:40 » et « créneau seul 8:30-9:40 ». Le script committé n'a **pas** de scénario « cercle seul » (seulement origine / A / B) ; mes rejeux donnent A groupé 576-586 s (9:36-9:46) et non 510-580 ; le « 8:30 » ne ressort qu'en dispersé.
- **Autre écart de texte** : `etudes/piste_et_pont.md:11` et `:77` annoncent « piste 88 s → ~62 s » ; c'est le cas **×3** (42 → 16 s, soit −26 s). Le module livré est **×2** (42 → 22 s, soit −20 s → ≈ 68 s). CALCULÉ : O = 62 reproduit 288 s (dispersés) et 368 s (groupés) ; les chiffres cités (279 s, 366 s) correspondent à **O = 60** ; pour O = 68 : 314 s et 374 s.
- **Correctif** : refaire la décision après I6 ; ajouter le scénario « cercle seul » au simulateur ; corriger `piste_et_pont.md` (×2 ≠ ×3).

#### I8 — Aucune suite de tests ne peut tourner hors de la machine du moddeur
- **Où** : `tests/test_patchs.py:72`, `:80`, `:16-27` (md5 fixes), `tests/` en général ; `tour/outils/test_patch_exe.py:15` (`capstone`).
- **Constat (EXÉCUTÉ)** : voir §1. `test_patchs.py` copie le **vrai** `build_mac` (chemin absolu du moddeur), lit le vrai `rom_0`, et compare à des md5 « calculés à part ». Sans le jeu exact, aucun contrôle n'est exécutable ; sur le Mac, après une mise à jour du jeu, le premier contrôle échoue (« programme reconnu ») alors que rien n'est cassé. Mon banc synthétique (§1) prouve qu'une fixture sans jeu est faisable en ~100 lignes pour la logique de l'atelier.
- **Correctif** : ajouter un test de fixture synthétique (faux binaire où chaque module trouve ses octets, `MD5_ORIGINE` injecté) pour : cycle, idempotence, permutations, abîmé, build décalé, chevauchements, I4, I5, M1. Garder `test_patchs.py` pour la validation contre le vrai binaire, en le rendant explicite (`SKIP` propre si le jeu manque).

---

### MINEUR

**M1 — Écriture non atomique entre programme et fichiers** (`patchs_cc2.py:211-238`). Le programme est écrit **avant** les vérifications qui peuvent encore refuser (copie d'original manquante, ligne 238). EXÉCUTÉ : `--retirer ascenseur_x2 effet_tele` sans copie de l'original du shader → `Refus` (« pas de copie de l'original »), **mais `ascenseur_x2` est déjà retiré**. Correctif : vérifier la présence de toutes les copies de retour avant la première écriture.

**M2 — Message cryptique ou trace brute sur un autre build / fichier absent** (`patchs_cc2.py:74`, `:117-120`, `:353`). EXÉCUTÉ : sur un build décalé, `Atelier.__init__` lève `Refus("ascenseur_x2 : 0x10286995c ne vaut pas 2 x 0x102869a64")` **avant** `programme_reconnu()` : le message prévu (« pas celui que j'ai analysé (mise à jour Steam ?) ») et l'avertissement de `afficher` (`:258-259`) ne sont **jamais atteints** ; le menu et « Tout remettre » ne s'ouvrent pas. Fichier tronqué → `struct.error` ; jeu absent → `FileNotFoundError` (`main` n'attrape que `Refus`). Sûr (rien n'est écrit), mais le message promis par `LISEZ-MOI.txt:49` (« il faudra refaire l'analyse ») n'est jamais affiché. Correctif : tester la taille et le md5 reconstruit **avant** les contrôles de constantes, ou attraper `struct.error`/`OSError`.

**M3 — `ecrire()` : pas de nettoyage, pas de `fsync`, relecture après remplacement** (`patchs_cc2.py:64-70`, `:240-243`). Si l'écriture échoue après création du `.tmp_patchs_cc2`, il reste dans `Contents/MacOS/`. La docstring (`:26-27`) promet « relit et contrôle » ; le contrôle (`apres = self.etats()`) vient **après** `os.replace` et ne ramène pas en arrière si `rates` est non vide. `patch_exe.py:ecrire_sur` (Windows) fait mieux (`fsync`, relecture du temporaire avant remplacement, `finally`). Correctif : aligner.

**M4 — Les chevauchements internes à un module ne sont pas détectés** (`patchs_cc2.py:133`, `occupe[i] != nom`). EXÉCUTÉ : deux retouches du même module sur les mêmes octets sont acceptées. Correctif : lever aussi pour `occupe[i] == nom` sur deux retouches distinctes.

**M5 — Contrôles de valeur absents pour `atterrissage`** (`atterrissage.py:23-28`, `facteur = None`). L'atelier ne vérifie à l'exécution ni `-1800`, ni `(1000, 1800)` aux constantes visées ; seul le md5 de l'original les couvre (suffisant tant qu'il est vérifié). Côté générateur : `generer_atterrissage.py:84` ne compare que **2 voies** du `addps` (les voies 2-3 sont ignorées), `:86` vérifie l'alignement mais **pas** que la nouvelle constante est dans une section en lecture seule (le générateur du pont a au moins un encadrement par intervalle, `generer_pont_retour.py:58`).

**M6 — Sauvegarde jamais revérifiée** (`patchs_cc2.py:212-214`). Si `sauvegarde/build_mac_origine` existe déjà (d'un ancien build), elle n'est ni comparée au md5 ni régénérée ; les générateurs la lisent ensuite comme « l'original » (`generer_atterrissage.py:17`).

**M7 — Les consommateurs des registres chargés par les `movss`/`comiss` redirigés ne sont pas analysés** (Mac `generer_atterrissage.py:37-38` ; Windows `verifier_sites.py` C2/C3). Pour l'état 3 Mac, l'auteur a trouvé un consommateur (`addss`, d'où `subss`) ; rien ne montre la recherche systématique pour `0x1001afaf2` (état 5) ni pour les `movss`/`comiss` Windows. Le cercle Mac a été validé en jeu et le cercle Windows a tourné (essai 1) : le risque est atténué, pas levé.

**M8 — Générateurs Mac uniquement** (`generer_atterrissage.py:48`, `:63` ; `generer_pont_retour.py:40`). `as -arch x86_64` et le format de commentaire `## 0x…` d'`objdump` sont ceux d'Apple ; non exécutables ici, non portables.

**M9 — `trajets_circuit.py` : l'ajustement de cercle ne discrimine pas un ovale** (`:78`, `:82-99`). EXÉCUTÉ sur journaux synthétiques :
  - cercle R = 1 200 → centre (−1 011 ; −1 795), r = 1 192, écart 23 m (le script retrouve la vérité) ;
  - cercle R = 830 → centre (−910 ; −1 766), r = 858, écart 67 m ;
  - **ovale d'origine → centre (−1 063 ; −1 715), r = 1 239, écart 75 m**, « 2,7 tours, 189 s/tour » : un « cercle ajusté » plausible, centré près du centre nominal, parce que le filtre `hypot(x+1000, z+1800) < 1500 and z < −700` ne garde que le demi-cercle arrière (commun au cercle et à l'ovale) plus des bouts de droite.

  Le centre de l'ovale synthétique est à ≈ 106 m du centre nominal, contre 20-30 m dans les mesures (`ETUDE.md:189`) : l'ajustement discrimine un peu, mais mon cercle R = 830 est lui-même décalé de ≈ 70 m par la contamination de l'approche finale, et le script imprime un « cercle » même pour un ovale. Il ne suffit donc **pas seul** ; **la preuve décisive est** l'étendue en z (jamais au-dessus de −150 m, contre +1 800 pour l'ovale), qui est correcte. De plus l'avion 10 (centre (−1 155 ; −1 626), r = 1 246, 8 points) n'est pas rapporté dans l'ETUDE. Autres défauts : `cercle()` divise par zéro si les points sont alignés ; `--navire` en dernier argument → `IndexError` (`:65-66`).

**M10 — Promesses plus larges que le code ou références mortes.**
- `atterrissage.py:8` et `LISEZ-MOI.txt:20-21` : « la piste peut être donnée sur **tout** le virage arrière (~2,7 km) » ; le demi-virage arrière fait 3,77 km (π·1 200) ; la fenêtre vaut 72 % (Mac) / 55 % (Windows) de celui-ci.
- `LISEZ-MOI.txt:14` : liste « disponibles (24/10) » sans `pont_retour_x2` (25/10), `grue_annulation`, `cctv_net`, `vitesse_*`.
- `ascenseur_x2.py:12`, `generer_pont_retour.py:18` : chemins `mods/cc2-ascenseur-x2/`, `mods/cc2-patchs/etudes/…` qui n'existent pas dans ce dépôt ; `ETUDE.md:81` cite un fichier absent (I1).
- `RAPPORT_modules.md:34` : « aucun octet commun … contrôle fait à la génération ». `generer_modules_atterrissage.py` initialise `deja = []` et n'y met que les sites de la même exécution ; le recoupement avec `ascenseur_x2`/`temps_x2` n'est fait que par `verifier_sites.py --sans-recouvrement` et le test. (J'ai recoupé les 6 JSON : 0 chevauchement.)
- `LISEZ-MOI.txt:22` « À utiliser AVEC l'ascenseur x2 » : aucune dépendance déclarée ni vérifiée par l'atelier ; `pont_retour_x2.py:8-9` suppose de même l'accélération et le plafond doublés.
- `ETUDE.md:81` (« 2,06 km est le bon calcul ») vs `simuler_file_atterrissage.py:15` : voir I6(c).

**M11 — Fidélité Windows vs Mac sur l'état 3.** `verifier_sites.py` C4 (facultatif, non retenu) : sans lui, l'état 3 vise 600 m devant l'avion pendant 1 tick, au lieu des 1 800 m du Mac validé (`atterrissage.py:29`). Négligeable (CALCULÉ : 1 tick, 2,7 m), mais ce n'est pas « exactement le comportement validé ».

**M12 — `patch_exe.py` : garde-fous étroits.** `--module` vaut `ascenseur_x2` par défaut, **y compris pour `retirer`** (`:270`) ; `jeu_ouvert()` ne regarde que `carrier_command.exe` (`:120`), pas les copies `carrier_command_test_cercle*.exe` ni `carrier_command_ancien_8E7FCBB6.exe` du même dossier (l'ETUDE circuit `:158` le sait). Sous Windows un exe en cours d'exécution ne peut pas être remplacé, donc le risque d'écrasement est limité, mais pas celui de patcher le vrai pendant qu'un essai tourne.

**M13 — Détails de code sans effet démontré.** `modele_circuit.py:31-37` : variables inutilisées (`x, z, etat, ZA`, `s, t, cap`) ; `verifier_sites.py:194` : le contrôle « octets d'origine lus = ceux de l'instruction décodée » est tautologique (le décodeur lit les mêmes octets) pour `rel32`/`imm32` (il ne l'est pas pour `abs32`) ; `simuler_file_atterrissage.py:61-64` : `TypeError` si une file ne finit pas dans `horizon = 3000` s (réel pour O ≳ 600 s : reproduit avec O = 900 s), choix de l'avion par **indice de liste** et non par ordre de file (`:37-43`).

---

## 3. Si le jeu change de build — synthèse

| Outil | Comportement sur un build inconnu | Verdict |
|---|---|---|
| Atelier Mac `patchs_cc2.py` | Refuse d'activer et de retirer ; n'écrit rien (EXÉCUTÉ). Mais le message est cryptique et le menu ne s'ouvre pas (M2). Le seul « build décalé » testé est un décalage de code **et** de constantes. | Sûr, mal expliqué |
| Windows `patch_exe.py activer` | `REFUS : état INCONNU` (EXÉCUTÉ). | Sûr |
| Windows `patch_exe.py retirer --sauvegarde` | **Remplace l'exe entier par l'ancien build** (EXÉCUTÉ). | **B1** |
| Windows `patch_exe.py` + JSON de deux builds | Se bloque pour toute commande (EXÉCUTÉ). | I3 |
| `generer_modules*.py`, `verifier_sites.py` | Refusent (`SHA_ORIGINE`, adresses figées, assertions) : échec sûr, mais **tout est à réécrire** pour le nouveau build ; `verifier_sites.py` fixe `DEBUT_FONCTION`, `SORTIE`, `BLOC_PISTE`, `CST_*`. | Sûr, travail à faire |
| Plan de portage | `PASSATION.md` §10 (circuit) parle de « retrouver les 6 sites par leurs octets voisins ». `tour/etude_mise_a_jour/PASSATION.md` §2 dit que le décalage « n'est PAS constant (0 à +0x190) » : chaque saut relatif S1-S3 et chaque adresse de constante doit être **recalculé et revérifié**, y compris que `SORTIE`/`BLOC_PISTE` restent des débuts d'instruction. Reprendre sans refaire I1 et I2 reproduirait les mêmes lacunes. | À encadrer |
| Mac | Le build Mac a très probablement aussi changé (INFÉRÉ par l'étude, `ETUDE.md` mise à jour §6) ; l'atelier le refusera. Rien dans ce dépôt n'indique si le Mac a été relu. | À vérifier par le moddeur (sha256 du `build_mac`) |

---

## 4. Trous de couverture des tests

Ce qui existe : `tests/test_patchs.py` couvre l'activation/le retrait des modules, la comparaison avec des md5 « calculés à part », le décodage `objdump` des 10 + 3 instructions d'`atterrissage` et de `pont_retour_x2`, le refus A+B, l'abîmé, le build différent (un octet), l'analyse stricte des arguments.

| Trou | Constat |
|---|---|
| Exécutable sans le jeu | Non (I8). |
| Refus « jeu ouvert » (`pgrep`) | **Aucun test** ; le défaut I5 est donc passé inaperçu. |
| Écritures non atomiques (programme + fichier) | Aucun test (M1). |
| Piège A/B | Seul « A et B ensemble dans `modules/` » est testé (`:274-278`), pas « A actif puis B » (I4). |
| Build décalé (code **et** constantes) | Le test (`:311-314`) ne modifie qu'un octet hors des sites ; le chemin réel d'une mise à jour (constantes déplacées) lève `Refus` à la construction (M2) et n'est pas couvert. |
| Chevauchement interne à un module | Non (M4). |
| Décodage de `ascenseur_x2` | Seuls les md5 sont comparés ; ni mnémonique ni cible. J'ai fait ce décodage ici (0 écart). |
| `DECODAGE_B` | Teste `attendu in lu` par sous-chaîne (`:153`) : ne vérifie pas le mnémonique pour les 4 `addps`/2 `movss`. |
| `modele_circuit.py`, `simuler_file_atterrissage.py`, `trajets_circuit.py` | Aucun test unitaire ; le modèle n'a que ses `assert` internes. Un test d'ovale/cercle sur journaux synthétiques (M9) manque. |
| Hélicos, plusieurs avions, panne | Rien (§6). |
| Windows (`patch_exe.py`) | Dépend de `capstone` ; mon banc sans `capstone` (faux exe + JSON) montre qu'on peut tester cycle, état inconnu, retrait avec sauvegarde, deux builds sans lui. |

**Alternatives maison, sans téléchargement tiers :** `objdump -D -b binary -m i386:x86-64 --adjust-vma=…` sur les octets d'un module (ce que fait `verif_octets.py`) remplace `capstone` pour les contrôles de cible/mnémonique sur les octets des JSON/modules ; la fixture synthétique remplace le jeu pour la logique de l'atelier. Les contrôles qui exigent le **vrai** binaire (relocations, sections, flot de données) restent à faire sur la machine du moddeur.

---

## 5. Ce qui m'a paru solide

- **Octets des modules Mac** (EXÉCUTÉ, `objdump`) : les 3 sauts d'`atterrissage` passent de `0x1001afb05` à `0x1001af914` avec les déplacements annoncés ; les 4 `addps` et 2 `movss` lisent bien `0x10286b920/930` et `0x102869adc` ; `addss` → `subss` (`f30f58c1` → `f30f5cc1`) ; les 3 `mulss` de `pont_retour_x2` lisent `0x1028699cc` ; les 34 retouches d'`ascenseur_x2` ont les mnémoniques et cibles annoncés. **0 écart** sur 47 retouches (10 + 3 + 34).
- **Contraintes de constantes d'`ascenseur_x2` + `pont_retour_x2`** : le système multiplicatif (0,025 → 0,05 → 0,1 ; 2,5 → 5 ; 30 → 15…) est **cohérent entre modules** (résolu par propagation, aucune contradiction), y compris la chaîne 0x102869978 → 0x1028697a4 → 0x1028697b0.
- **Atelier Mac** (EXÉCUTÉ sur faux binaire) : activation → réactivation = « rien à faire » ; retrait = md5 d'origine exact ; 6 permutations d'ordre d'activation/retrait → état final identique à chaque fois ; un octet changé sur un site actif → refus « abîmé » ; octet hors site → refus « pas celui que j'ai analysé » ; sauvegarde = original **reconstruit** (donc jamais une copie corrompue) ; chevauchement entre modules détecté ; écriture via fichier temporaire + `os.replace` ; analyse d'arguments stricte.
- **Windows `patch_exe.py`** (EXÉCUTÉ sur faux exe) : `activer` exige une sauvegarde au bon sha256, refuse un état inconnu ou mélangé, relit avant de remplacer, `--cest-le-vrai-jeu` sur chemin `steamapps`, `jeu_ouvert` inconnu → refus ; cycle activer/retirer de 3 modules → sha256 exact de l'original.
- **JSON Windows** (CALCULÉ) : les 6 champs du créneau et du cercle recalculés à la main (déplacements `0x104`→`0x2a`, `−0x235`→`−0x30f`, `−0x24f`→`−0x329`, flottants `0x44160000` = 600,0 et `0xc4e10000` = −1800,0) correspondent aux JSON et à `RAPPORT_modules.md` ; 0 chevauchement entre les 6 modules ; `va − offset` constant.
- **`generer_pont_retour.py:68-74`** : preuve que chaque `mulss` n'est atteint que depuis son état (liste exacte des sauts sources + instruction précédente qui tombe dedans ou non) : c'est la bonne méthode, et ce qui manque côté Windows (I2).
- **Géométrie du modèle** (CALCULÉ) : 12 340 / 7 540 m ; 154,3 / 94,3 s ; centre à 2 059 m du bateau (859 m au plus près) ; fenêtre 1 032 + 1 029 m ; l'état 3 dure 1 tick au cercle (et l'état 0 seulement 2) ; ordre 0→1→2→3→4→5→0 respecté. Le tableau de l'essai 1 (`ETUDE.md:166-183`) : toutes les différences d'heures recalculées sont exactes (1:51, 1:43, 2:12 ; moyenne 1:55 ; attentes perdues −1, +4, +23 s).
- **Tableau de roulage de `piste_et_pont.md`** (CALCULÉ) : 28,5 → 14,6 → 10,0 s et 42 → 22 → 16 s reproduits à ±0,3 s par la formule `v = min(v+0,1 ; 5 ; reste)`, `avance = v/(L×div)`.
- **Honnêteté des documents** : étiquettes LU/MESURÉ/INFÉRÉ ; « un essai ne conclut pas » (`ETUDE.md:185`) ; le cercle n'est mesuré qu'une fois et le créneau jamais (`PASSATION.md` §2).
- **La preuve de l'étendue en z** (M9) : jamais d'excursion à z = +1 800 sur 4 avions (max −153 à −291 m, approche finale incluse) est une vraie discrimination ovale/cercle.

---

## 6. Non vérifiable sans le jeu

À ne pas lire comme « ça marche » ni comme « ça ne marche pas » :

1. **Effet réel de chaque patch** : durées, gain (−30 %, 7:28 Mac, 8:58 tour), absence d'approche ratée. Sur Windows, **le cercle n'est pas démontré plus rapide** : 8:58 (cercle, n = 1) contre 8:47 et 10:10 (ovale, n = 2). Le créneau Windows n'a **jamais** tourné.
2. **Registres vivants à l'entrée du bloc de piste** (Mac `r14`, Windows `edi`) et le « registre laissé » du test de distance Mac (I1).
3. **Consommateurs de `xmm7`** du port Windows de `pont_retour_x2`, dont les départs ×2 et l'état 3 (I2).
4. **Géométrie d'approche depuis les points d'entrée du créneau** (jusqu'à ~1 km avant ou ~1 km après la porte) : le jeu rate l'approche si l'angle dépasse 0,45 rad entre 50 et 400 m du bout de piste (`DEMARRER_cc2_patchs.md:155`). Mac : 0 ratée sur 4 avions, un essai.
5. **Approche ratée** : l'avion est remis à l'état 3 ; au cercle, l'état 3 passe aussitôt à l'état 4 (centre z = −1 800) : l'avion revient du côté du pont vers un cercle situé 2 km derrière, au lieu de poursuivre l'ovale vers l'avant. Chemin au-dessus/près du bateau et d'avions en approche : non observé (`ETUDE.md:82`).
6. **Hélicos** : ils partagent la file (`docking_queue`) et l'unique case piste avec les avions mais ne sont **pas simulés**. INFÉRÉ : avant, les hélicos testent la piste à chaque tick (ils attendent sur place) et les avions un seul tick par tour ; après le créneau, les avions testent ~20-26 s sur ~94 s : l'équité entre les deux change, **non mesuré**. Altitudes d'attente (80 m contre 120 + 20 × rang) et distance ≥ 250 m au cercle nominal : pas de collision attendue (CALCULÉ pour les positions `x −100, z −240 − 60 × rang`), non vérifié en jeu.
7. **Pannes** : un avion détruit libère la piste (`etudes/piste_et_pont.md`, adresses `0x1001ad624`/`0x1001ae753`, LU) ; ascenseur détruit ou énergie basse : la piste reste réservée comme à l'origine. Avec `ascenseur_x2` la demande d'énergie double (0,4 → 0,8) : effet en cas de réseau électrique dégradé, non étudié.
8. **Sauvegarde/chargement à cheval sur le patch** : mon raisonnement (INFÉRÉ) à partir de la table de transitions : un avion à l'état 3 ou 5 avec z entre −1 800 et 600 franchit aussitôt le seuil −1 800 et rejoint le cercle ; aucune boucle bloquante visible. Non testé.
9. **Plateforme macOS** : que `pgrep -x build_mac` désigne bien le processus du jeu ; que `os.replace` sur le binaire de l'application ne soit pas bloqué par le contrôle d'intégrité de l'OS ; signature du binaire patché (validé en jeu le 23/10 par le moddeur, pas rejouable ici).
10. **Windows** : entrées de relocation (ASLR) des champs, section en lecture seule de `−1800,0`, usage exclusif de `[ebp-0x2a4]` par les états 4 et 5, compatibilité « ancien exe + fichiers Steam du 28/10 » (déjà notée INFÉRÉE), comportement en multijoueur (les invités n'ont rien à installer : jamais testé).
11. **Le 1,56** entre journaux (I6b) : une mesure suffirait.

---

## 7. Annexe — résultats chiffrés rejoués (pour contrôle)

Simulateur committé, sortie intacte :
```
Tour du circuit : origine 12340 m (154 s), cercle 7540 m (94 s)
4 avions groupes   O=90 110 130 150 170 s :
  origine      589 609 629 649 1132 s
  A creneau    576 596 616 636  810 s
  B A + cercle 396 510 562 739  759 s
4 avions disperses (400 essais) :
  origine      588 659 706 738  865 s
  A creneau    465 554 645 699  738 s
  B A + cercle 407 459 546 638  732 s
```
Rejeux (fenêtre symétrique `APRES = 1031`, 4 avions dispersés, O = 95 s) : A 491 → 512 s, B 419 → 427 s.

Occupation de piste (modèle `piste_et_pont.md`, B dispersés) : O = 88 → 401 s ; O = 68 (×2) → 314 s ; O = 62 (×3) → 288 s ; O = 60 → 279 s.

Fenêtre de piste vs rayon réel (CALCULÉ, cos α > (r² + 440 000)/(2 400 r)) : r = 1 200 → 2 062 m (25,8 s) ; r = 958 → 1 799 m (22,5 s) ; r = 840 → 1 624 m (20,3 s) ; r = 808 → 1 571 m (19,6 s).

*Aucune commande « retirer », « activer » ou « origine » n'a été lancée sur un vrai programme ; tout s'est passé sur des fichiers synthétiques du dossier de travail de la session.*

# Étude de portage des patchs d'exe sur le nouvel exe Steam (461E1262) — RAPPORT FINAL

Tout est fait HORS du jeu, sur les trois copies de `copies/`. Rien posé, rien lancé, aucun fichier existant du dépôt modifié, aucun accès au dossier du jeu, à %APPDATA% ni à Steam.
Étiquettes : **LU** (dans un fichier), **MESURÉ** (sortie d'un de mes scripts, fichier cité), **INFÉRÉ** (déduit), **RAPPORTÉ** (dit par une autre conversation, pas revérifié).

**Résumé en une phrase** : les 41 changements d'exe des 6 modules ont été retrouvés dans le nouvel exe, un par un, par désassemblage (même instruction, même valeur de constante), 6 JSON portés et une copie patchée par module (+ une avec tous) ont été fabriqués dans `travail/`, et `test_portage.py` répond OK partout ; **mais rien n'a été essayé en jeu : aucun module porté n'est « validé » tant que le moddeur ne l'a pas vu marcher.**

sha256 des copies, recalculés au début (MESURÉ, `travail/sortie_test_portage.txt` T1) : ORIGINAL `1C9A01C3…`, PATCHÉ `8E7FCBB6…`, NOUVEAU `461E1262…` : conformes aux valeurs de la tâche.

## Étape 1 — Composition de l'exe 8E7FCBB6 (MESURÉ : `etape1_composition.py`, test T2)
- Original et patché : même taille (11 353 600). 75 octets diffèrent, en 33 petits blocs ; **0 octet inexpliqué** (tout tombe dans les 4 octets d'un changement d'un JSON).
- `ascenseur_x2` : 32 changements sur 32 présents (dont celui de l'en-tête à 0x310). `temps_x2` : 1 sur 1.
- `pont_retour_x2` : **0 sur 1, ABSENT**. `atterrissage_cercle` 0/3, `atterrissage_creneau` 0/3, `helicos_approche_x2` 0/1 : absents.
- **Réponse au piège de la carte** : l'exe lancé à part (8E7FCBB6) = original + `ascenseur_x2` + `temps_x2` seulement. **Il n'a PAS `pont_retour_x2`.** Le 0C5DFE52 (« original + 3 modules ») de l'autre étude n'est pas dans mes copies : INFÉRÉ que son 3e module était `pont_retour_x2`, non vérifié.

## Étape 2 — Vérification par désassemblage (MESURÉ : `etape2_desasm.py` → `travail/etape2_desassemblage.txt`, `travail/analyse_sites.json`, `travail/resume_etape2.txt`)
Méthode : pour chaque changement, désassemblage (capstone, 32 bits) d'une fenêtre de 11 instructions (4 avant, 6 après) autour du site dans l'ORIGINAL ; recherche, dans le nouvel exe, du décalage (de −0x80 à +0x400) qui redonne **exactement les mêmes 11 instructions** (mnémoniques, registres, déplacements, tailles ; seules les adresses absolues 0x400000-0xEF7000 sont masquées). Un seul candidat attendu : c'est ce qui sort pour les 40 changements hors en-tête. La synchronisation du désassemblage se fait par vote (une fois, un départ au hasard tombait en milieu d'instruction : corrigé).
- Décalage du code trouvé : **+0x110 pour 39 sites, +0x130 pour `temps_x2`** (c'est ce que la 1re étude avait mesuré sur les octets : confirmé par le désassemblage).
- **Constantes pointées (30 + 2 + 1 + 1 = 34 pointeurs)** : la valeur flottante lue à l'adresse `avant` dans l'ancien exe est **identique au bit près** à celle lue à la nouvelle adresse (décalage +0x38 partout). Idem pour `apres` : 26 pointeurs vers .rdata (décalage +0x38, ou +0x0 pour les constantes 0xCE…, retrouvées par leurs 16 octets voisins, 1 seul candidat à chaque fois) avec valeur identique ; 4 pointeurs vers l'en-tête (voir étape 3). Exemples (ancien → nouveau) : 2,5 `[0xdb76c8]→[0xdb7700]` ; 5,0 `[0xdb7830]→[0xdb7868]` ; 0,1 `[0xce560c]` (inchangé) ; 600 `[0xdb7a70]→[0xdb7aa8]` / −1800 `[0xdb7e54]→[0xdb7e8c]` ; 30,0 `[0xdb798c]→[0xdb79c4]` / 15,0 `[0xdb7930]→[0xdb7968]` ; 50,0 → 100,0 pour l'hélico.
- **Les 34 champs-pointeurs sont dans la liste de relocation (.reloc) des deux exe** (MESURÉ) : l'exe est en `DYNAMIC_BASE` (0x8140), donc le chargeur corrige ces adresses ; en changer la valeur par une autre adresse du même exe reste valide. Les 3 immédiats et les 3 sauts ne sont PAS dans .reloc, comme attendu.
- **3 immédiats** (énergie 0,4→0,8 d'`ascenseur_x2` ; centre du cercle 600→−1800 d'`atterrissage_cercle` ; facteur de vitesse 1,0→2,0 de `temps_x2`) : même instruction dans les deux exe, octets `avant` identiques, `apres` inchangé.
- **3 sauts relatifs d'`atterrissage_creneau`** : le décalage est le même (+0x110) pour la source et pour les deux cibles (la sortie 0x701b04→0x701c14 et le « test de la piste » 0x701a2a→0x701b3a, vérifiées par 5 instructions chacune) ; les octets `apres` à écrire sont donc **identiques** à ceux de l'ancien exe.
- Note : les mises en page des fichiers diffèrent (`.rdata` commence à l'offset 0x8d5200 au lieu de 0x8d5000) ; mes `offset` portés viennent de la table des sections, pas d'un décalage supposé.

## Étape 3 — Le cas de l'en-tête (MESURÉ : `etape3_entete.py` → `travail/etape3_entete.txt`)
- `ascenseur_x2` change 4 octets à l'offset **0x310** (`00000000` → `898888bd` = le flottant −0,0666667, soit 2 × −1/30).
- L'en-tête PE (lu avec `struct`) : e_lfanew 0x128, 6 sections, la **table des sections finit exactement à 0x310** ; SizeOfHeaders = 0x400. Donc 0x310 est le **bourrage de zéros** juste après la table des sections (zéros de 0x310 à 0x3FF dans les trois exe, MESURÉ). L'en-tête est mappé en mémoire à partir de l'adresse 0x400000 (la VA 0x400310 est lisible).
- **Rôle** : le patch s'en sert comme petite case de stockage pour un flottant. 4 lectures du code (les 4 lectures « grue verticale −1/30 », blocs A à D) sont redirigées vers `[0x400310]` ; sans l'écriture à 0x310, ces 4 lectures liraient 0,0 et la grue ne descendrait plus. **Il faut donc le reproduire à l'identique sur le nouvel exe** : même offset 0x310, même valeur. C'est possible : la disposition de l'en-tête est la même (table finissant à 0x310, zéros après, SizeOfHeaders 0x400). Le JSON porté contient ce changement tel quel, et le test T4b vérifie « 1 écriture + 4 lectures vers 0x400310 ».
- Autres faits MESURÉS : CheckSum = 0 (rien à recalculer), pas de signature numérique (dossier 4 vide). Horodatage PE : 0x6a36c177 (ancien) → 0x6ae228f3 (nouveau).

## Étape 4 — Modules portés (MESURÉ : `etape4_generer_json.py`, dossier `modules_exe_nouvel_exe/`)
6 JSON, mêmes champs que les originaux (nom, description, avertissement, build, sha256_origine = `461E1262…`, sha256_patche, nb_changements, changements : va, offset, avant, apres, role, reglage, constante_va), plus un bloc `portage` par changement (ancien va/offset, instruction ancien/nouveau, type de champ) et un `build` du nouvel exe (taille 11 354 112, horodatage 0x6ae228f3, Steam 26277078). `constante_va` a été transposé (il valait le pointeur `apres` dans tous les cas : vérifié par le script, 0 exception). Le texte `role` est resté celui de l'original : les adresses citées dans ce texte sont celles de l'ANCIEN exe (les vraies sont dans les champs `va` / `apres`).

**Changements non portés : aucun** (`modules_exe_nouvel_exe/CHANGEMENTS_NON_PORTES.txt` dit « aucun » ; chaque changement a été retrouvé de façon unique). Réserve de fond, qui ne tient pas au portage : le changement d'`ascenseur_x2` « énergie 0,4→0,8 » est noté dans l'original comme « part ascenseur/grue présumée, à confirmer » (LU dans son `role`). Je ne l'ai pas écarté, car l'instruction est strictement la même, mais ce doute existe déjà sur l'ancien exe.

## Étape 5 — Copies patchées hors jeu (MESURÉ : `portage_appliquer.py`, lancé par `test_portage.py`)
`portage_appliquer.py` (écrit par moi ; `patch_exe.py` non modifié, non appelé) : n'écrit qu'un NOUVEAU fichier (temporaire, relu, sha256 vérifié, puis renommé), jamais l'entrée ; refuse tout chemin contenant `steamapps` ou `Carrier Command 2` ; refuse sortie = entrée ; refuse une entrée qui n'est pas exactement `461E1262…` (pour fabriquer) ; refuse si deux modules touchent le même octet. Chaque copie a été relue et comparée octet par octet à `461E1262…`, et le retrait redonne exactement `461E1262…` (sha256 vérifié) :

| copie (dans `travail/`) | changements | octets différents de 461E1262 | sha256 de la copie | retrait → 461E1262 exact |
|---|---|---|---|---|
| nouveau_ascenseur_x2.exe | 32 | 79 | 1D004BEF0B90C469FE3251FE8C67F871348DECC1E91F5D8113CFBBA41210C8A2 | oui |
| nouveau_temps_x2.exe | 1 | 2 | A2353B6A68A34C2B2CD0E42C0C42DB1DC2E3B73C5A09769C0CCD15B5A85C3EFB | oui |
| nouveau_pont_retour_x2.exe | 1 | 1 | 41A00F2CCA385B11B61E99C85B4A26B32E8D9A90F0BF55458DE0F4EB09FA3B0E | oui |
| nouveau_helicos_approche_x2.exe | 1 | 2 | 0DF816F7D5E73B964A4150E907AD5A863999C83ED2131D1AD28899EADEAFD727 | oui |
| nouveau_atterrissage_creneau.exe | 3 | 6 | DD55A1A54844250ACAF712D01C93AAB1F3DB27AB4B4B424BE890699A65A5FBC7 | oui |
| nouveau_atterrissage_cercle.exe | 3 | 6 | A8B4F4490DAC1F7551914C944A046C35C0CC1AA6CCC03BA461A9C43546FEB402 | oui |
| nouveau_TOUS.exe | 41 | 96 | 9B902B5C614D192EEBB3C87ECC1568CB0322E95652A5CD65B746D7DCDA234A41 | oui |

Dans chaque cas, seuls les octets prévus ont changé : l'ensemble des octets différents est inclus dans les 4 octets de chaque changement, et chacun vaut `apres`. Un changement peut ne modifier que 1 ou 2 octets sur 4 car les autres sont déjà égaux. Contrôle en plus : TOUS moins `temps_x2` = copie fabriquée avec les 5 autres (identique octet pour octet). Ces fichiers sont à moi (~11 Mo chacun, 16 fichiers dans `travail/`, ~180 Mo) ; le moddeur peut les effacer sans conséquence (`test_portage.py` les refabrique).

## Étape 6 — Tests (MESURÉ : `test_portage.py`, sortie complète dans `travail/sortie_test_portage.txt`)
Résultat : **RESULTAT GLOBAL : OK**, aucun ÉCHEC. Contrôles : sha256 des copies ; composition de 8E7FCBB6 ; 6 JSON cohérents ; 41 changements revérifiés (instructions, valeurs, relocations) ; en-tête ; 7 copies et 7 retraits ; équivalence `ascenseur_x2` + `temps_x2` portés avec 8E7FCBB6 (mêmes valeurs lues) ; refus des chemins interdits ; copies d'origine intactes. Limite honnête : le contrôle des instructions réutilise la même fonction (`analyse.match_at`) que l'analyse, ce n'est donc pas un deuxième avis indépendant ; les extraits de désassemblage sont à lire dans `travail/etape2_desassemblage.txt`.

## Étape 7 — Tableau final par module
| module | changements | retrouvés par désassemblage | valeur de constante vérifiée | ambigus / non portés | niveau de preuve |
|---|---|---|---|---|---|
| ascenseur_x2 | 32 (30 pointeurs, 1 immédiat, 1 en-tête) | 31 sur 31 hors en-tête | 30 pointeurs : `avant` identique ; 26 `apres` identiques ; 4 `apres` = en-tête (reproduit) | 0 | MESURÉ hors jeu. Équivalent à 8E7FCBB6 sur ce qui est lu. Déjà vu en jeu sur l'ANCIEN exe : RAPPORTÉ par les fiches, non revérifié |
| temps_x2 | 1 (immédiat) | 1 | sans objet (1,0 → 2,0 immédiat) | 0 | MESURÉ hors jeu ; même remarque pour le jeu |
| pont_retour_x2 | 1 (pointeur 30,0 → 15,0) | 1 | 30,0 et 15,0 identiques | 0 | MESURÉ hors jeu ; absent de 8E7FCBB6 : jamais confirmé par un exe lancé à part |
| helicos_approche_x2 | 1 (pointeur 50 → 100) | 1 | 50,0 et 100,0 identiques | 0 | MESURÉ hors jeu ; « jamais vu en jeu sur Windows » (LU dans le JSON) |
| atterrissage_creneau | 3 (sauts relatifs) | 3 | sans objet (cibles vérifiées) | 0 | MESURÉ hors jeu ; jamais vu en jeu (LU) |
| atterrissage_cercle | 3 (1 immédiat, 2 pointeurs) | 3 | 600 et −1800 identiques | 0 | MESURÉ hors jeu ; jamais vu en jeu (LU) |

## Ce qui n'est PAS prouvé
- **Aucun essai en jeu** : un module porté n'est validé que quand le moddeur l'a vu marcher. Même instruction + même constante ne prouve pas que le reste du programme n'a pas changé : j'ai comparé 11 instructions autour de chaque site, pas des fonctions entières. INFÉRÉ : le nouveau build est une recompilation quasi à l'identique (la 1re étude et mes mesures vont dans ce sens).
- Comment lancer un exe patché à part (avec quels fichiers du jeu autour) : non étudié ici, non testé. Le SDK `dinput8.dll` / `cc2x_frein.dll` n'est pas concerné par ce portage (profil par horodatage inactif, d'après la 1re étude, RAPPORTÉ). Une prochaine mise à jour Steam refera tout bouger : il faudra relancer l'étude.
- Multijoueur, sauvegardes, Mac : non vus.
- Je n'ai pas vérifié que mes copies sont identiques à celles du jeu (accès interdit) ; je me fie aux sha256 donnés par la tâche, qui correspondent.

## Ordre de pose conseillé (UN module à la fois, un essai en jeu entre chaque ; rien n'est posé)
Risque technique mesuré faible pour tous. 🟢 = 1 changement simple ; 🟡 = effet de jeu jamais vu ou plusieurs changements. Aucun 🔴 trouvé, mais aucun n'est essayé.
1. `temps_x2` 🟢 : 1 valeur, effet immédiatement visible (jeu 2× plus vite) ; MODE TEST, jamais en multijoueur.
2. `ascenseur_x2` 🟡 : 32 changements dont l'en-tête, mais c'est le module le plus testé sur l'ancien exe (RAPPORTÉ).
3. `pont_retour_x2` 🟡 : 1 changement ; effets de bord annoncés (le roulage de départ peut aussi aller ×2).
4. `helicos_approche_x2` 🟡 : 1 changement ; jamais vu en jeu sur Windows.
5. `atterrissage_creneau` 🟡 : 3 sauts ; change le circuit des avions des 2 porte-avions.
6. `atterrissage_cercle` 🟡 : 3 changements ; même remarque ; en dernier, car il modifie le tracé du circuit.
Tout retrait = refaire une copie depuis `461E1262…` (prouvé exact) ; le `carrier_command.exe` de Steam n'est jamais touché.

## Fichiers (tous dans `tour/etude_portage_credits/`)
`RAPPORT.md` ; `portage_appliquer.py` ; `test_portage.py` ; `portlib.py`, `analyse.py` (outils communs) ; `etape1_composition.py`, `etape2_desasm.py`, `etape3_entete.py`, `etape4_generer_json.py`, `etape_pe.py`, `resume2.py` ; `debug1.py`, `patch_chain.py` (échafaudage de mise au point) ; `modules_exe_nouvel_exe/` (6 JSON + `CHANGEMENTS_NON_PORTES.txt`) ; `travail/` (`analyse_sites.json`, `etape2_desassemblage.txt`, `resume_etape2.txt`, `etape3_entete.txt`, `sortie_test_portage.txt` et 16 copies d'exe).

## UNE question pour le moddeur
Veux-tu que je prépare, SANS rien poser ni lancer, la fiche de pose d'UN seul module (`temps_x2`) sur le nouvel exe (où mettre la copie patchée, comment la lancer à part, comment la retirer), pour que tu décides ensuite, séparément, d'un essai en jeu ?
Prochaine action concrète : répondre oui ou non à cette question. Ce rapport ne lance aucun essai en jeu.

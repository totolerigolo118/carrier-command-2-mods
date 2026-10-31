# Roulage de retour ×2 et approche des hélicos ×2 : portage sur Windows (28/10/2026)

> **Mise à jour 29/10 : lire `../idees_et_demandes/PASSATION.md`.** La mise à jour Steam du 28/10 21:30 a remplacé `carrier_command.exe` (nouvel exe `461E1262…`, sans patch) : `pont_retour_x2`, posé le 28/10 à 10:25, a été effacé (rapporté). Tout ce qui suit vise l'**ancien** exe (`1C9A01C3…`) ; les modules sont à re-porter.

Faite pendant ton absence, à ta demande (« les hélicos, la vitesse d'approche, roulage retour ×2 »). **Rien n'a été posé dans le jeu** : le vrai `carrier_command.exe` est toujours `8E7FCBB6…` (ascenseur ×2 + temps ×2), jeu **non lancé** (je n'en ai pas eu besoin : tout est de la lecture d'une copie de l'exe). Tout est testé **sur des copies**, dans un dossier temporaire. Rien n'est commité.

**Étiquettes** : **LU** = lu dans le fichier (désassemblage de la copie d'origine, notes du Mac) · **INFÉRÉ** = déduit, à vérifier · **TESTÉ** = vérifié sur une copie de l'exe par les outils (pas en jeu).

## 1. Résultat en deux lignes

| Module | Ce qu'il fait | Taille | Prêt ? |
|---|---|---|---|
| `pont_retour_x2` | les avions et hélicos qui reviennent roulent 2× plus vite sur le pont après le toucher (piste → ascenseur) | **1 retouche de 4 octets** | prêt, testé sur copie, **jamais vu en jeu** |
| `helicos_approche_x2` | les hélicos s'approchent ~2× plus vite (visée à 100 m devant au lieu de 50 m) | **1 retouche de 4 octets** | prêt, testé sur copie, **jamais vu en jeu** |

Fichiers : `modules/pont_retour_x2.json`, `modules/helicos_approche_x2.json`, générés par `generer_modules.py` (il relit chaque instruction et refuse d'écrire si un contrôle échoue). Analyse du flot de données : `analyse_registre.py`.

## 2. Roulage de retour ×2 (`pont_retour_x2`)

**Sur le Mac (LU `etudes/piste_et_pont.md`)** : après le toucher, l'avion roule 42 s sur le pont (états 5, 6, 7 : reculer sur la piste 28 s, aller à l'attente de l'ascenseur 7 s, monter sur la plateforme 7 s). Trois lectures de `30,0` (ticks par seconde, dans `t += v / (L × 30)`) redirigées vers `15,0` ont donné 0:51 → 0:32 par avion.

**Sur Windows (LU, désassemblage de la copie d'origine)** : le compilateur a organisé le code autrement.
- Le `30,0` est lu **une seule fois**, au début de la boucle de la file, et gardé dans le registre `xmm7` : `movss xmm7,[30.0]` en `0x006fdda9` (juste avant le saut par table des états de piste 3 à 7, `0x006fddde`).
- Les états 5, 6 et 7 **partagent une seule queue de calcul** : `mulss xmm0,xmm7` en `0x007007e3` (cinq sauts y arrivent : `0x7006ca` état 5, `0x700954/0x700969/0x700973` état 6, `0x700a84` état 7).
- Une analyse de flot (quelles lectures de `xmm7` reçoivent quelle valeur) montre que **cette queue reçoit uniquement la valeur chargée en `0x6fdda9`** (INFÉRÉ de l'analyse, pas vu en jeu).

**Le module** : une seule lecture redirigée, `0x6fdda9` : `30,0` (adresse `0xdb798c`) → `15,0` (adresse `0xdb7930`, constante **déjà présente** en lecture seule). Le champ de 4 octets a bien une entrée de relocation (le jeu change d'adresse à chaque lancement : c'est correct) (**TESTÉ**).

**Effet de bord à connaître (INFÉRÉ de l'analyse)** : une 2e queue de roulage lit aussi `xmm7`, en `0x00700c10` : c'est le roulage du **départ** (ascenseur → bout de piste). Sur le chemin « direct » (un emplacement sans avion qui se pose), elle reçoit aussi la valeur du début de boucle. Donc **le roulage des décollages pourrait aussi aller 2× plus vite** (en plus de l'ascenseur ×2, qui double déjà son accélération et son plafond en `0x6ffa68` et `0x6ffaef`). Ce n'est pas ce que le Mac faisait, mais c'est du même type que la piste « B' » du Mac (« rouler plus vite de l'ascenseur au bout de piste, à mesurer d'abord, risque faible »). **À mesurer** ; retrait en une commande si ça gêne. Pour l'éviter il faudrait de petits morceaux de code (greffe) : pas fait.

**Gain attendu (INFÉRÉ par analogie avec le Mac, non mesuré sur la tour)** : environ −20 s de roulage sur le pont par avion (42 s → 22 s), donc piste occupée ~20 s de moins par avion. Sur la tour, « pont → hangar » est aujourd'hui 0:55 (LU `JOURNAL_tour.md`).

## 3. Approche des hélicos ×2 (`helicos_approche_x2`)

**Sur le Mac (LU `partage_detail/04_helicopters.txt`)** : l'hélico vise un point sur l'axe de la piste 50 m devant lui ; le pilote automatique corrige à 0,1 par mètre, donc ~5 m/s et ~1 min d'approche. Viser 100 m devant donne ~10 m/s. Validé en jeu avec le module « toucher près de l'ascenseur » : approche 1:00 → 0:30, 4 hélicos 6:52 → 4:22.

**Sur Windows (LU)** : la partie réservée aux hélicos est le bloc `0x006fe198`–`0x006fe435` de l'état 3, atteint **seulement** si le test `get_is_rotor` est vrai (`call [vtable+0x4c]` / `test al,al` / `je 0x6fe436` en `0x6fe18e`–`0x6fe192`). Aucun autre saut n'y entre (**TESTÉ** par la recherche de tous les sauts vers ce bloc). Les avions passent par `0x6fe436` (seuil de 800 m) et ne sont pas touchés. Dans le bloc : `0x6fe1ab addss xmm0,[120.0]` (z visé au plus = début de piste + 120), **`0x6fe1b3 addss xmm2,[50.0]` (z visé = z de l'hélico + 50)**.

**Le module** : une lecture redirigée, `0x6fe1b3` : `50,0` (`0xdb79b8`) → `100,0` (`0xdb79e0`, déjà présente, lecture seule), relocation présente (**TESTÉ**).

**Ce que le Mac a validé et ce que je ne livre pas** : le Mac a validé **deux modules ensemble** (approche ×2 + « toucher près de l'ascenseur »). Le second demande, en plus de deux constantes (`0x6fe1ab` 120 → 48 et `0x6fe3e7` 20 → 70, que j'ai retrouvées sur Windows), **une greffe de 21 octets** (soustraire 23,5 avant le plancher −2,0 de la hauteur visée, `0x6fe31c`). Sans cette greffe, ces deux constantes seules feraient planer l'hélico à ~23 m au-dessus de l'ascenseur sans se poser : **je ne les ai pas mises dans un module**. L'approche ×2 **seule** n'a jamais été validée en jeu, même sur le Mac (INFÉRÉ : gain ≈ −30 s par hélico, le toucher restant au milieu de la piste).

## 4. Ce qui a été vérifié (TESTÉ, sur copies)

- La copie d'origine a bien la somme `1C9A01C3…341026`.
- `patch_exe.py activer` / `retirer` de chaque module, puis des quatre ensemble (`ascenseur_x2`, `temps_x2`, `pont_retour_x2`, `helicos_approche_x2`) : état « patché, cohérent avec l'original » ; retrait des deux nouveaux → on retombe exactement sur `8E7FCBB6…` ; retrait de tout → exactement l'original.
- Un seul octet change par module (l'octet bas de l'adresse : `8c → 30` et `b8 → e0`). Les instructions relues par le désassembleur après patch lisent bien `15,0` et `100,0`, longueur inchangée.
- Aucun chevauchement avec les modules existants (le générateur le vérifie). La suite de tests existante (`test_patch_exe.py`, 157 contrôles) passe avec les deux modules ajoutés.
- **Pas testé** : le comportement en jeu (rien n'a été lancé).

## 5. Pour les poser (rien de tout ça n'est fait, et il faut ton accord, jeu fermé)

1. Copier les deux `.json` de `tour/etudes_roulage_retour/modules/` dans `tour/outils/modules_exe/` (🟢 : deux fichiers texte ; la conversation « circuit » partage ce dossier : à faire quand elle a fini).
2. `python tour/outils/patch_exe.py activer --exe <vrai exe> --sauvegarde tour/sauvegardes/carrier_command_1.5.18_original.exe --module pont_retour_x2 --cest-le-vrai-jeu` (🟡 : modifie le vrai exe de 4 octets ; l'outil refuse si le jeu tourne ; retour : `… retirer --module pont_retour_x2`). **NE PAS UTILISER sur l'exe de Steam du 28/10 (état INCONNU : voir `patch_exe.py`) : cette commande était valable pour l'ancien build seulement, l'outil la refuse maintenant sur un autre build.**
3. Mesurer comme avant : 4 avions lancés puis rappelés, métrique **« pont → hangar »** (0:55 aujourd'hui). Attendu ≈ 0:35. Puis un 2e essai à part pour les hélicos.
4. Ne pas poser pendant un essai d'une autre conversation : la conversation « circuit » utilise une **copie d'essai** de l'exe dans le dossier du jeu, et la conversation « atterrissage à la main » a besoin du comportement actuel.

Multijoueur : les deux modules sont des **patchs du programme** : ils n'agissent que **chez l'hôte** (LU `partage_detail/08_constants_and_multiplayer.txt`), les invités n'ont rien à installer ; jamais testé avec de vrais joueurs.

## 5 bis. Pose sur le vrai jeu (journal)

- **28/10/2026 10:25 — `pont_retour_x2` POSÉ** (accord du moddeur : « pose pont_retour_x2 puis helicos_approche_x2 … un module à la fois, avec mesure entre les deux » ; puis « tu peux pas le faire tant que je ne suis pas chez moi ? »). Jeu fermé (aucun `carrier_command*` ni `dedicated_server` en cours, vérifié juste avant), `patch_exe.py activer … --cest-le-vrai-jeu`, code 0, « sha256 vérifié ». Vrai exe : `8E7FCBB6…` → **`0C5DFE52DFDF1AE0…`** (= attendu). Instruction relue dans le vrai exe : `movss xmm7,[0xdb7930]` (15,0). Aucun fichier temporaire laissé. Les JSON des deux modules ont été copiés dans `tour/outils/modules_exe/`.
- **`helicos_approche_x2` : PAS POSÉ** — attend la mesure de `pont_retour_x2` (un module à la fois). Un seul exe de test à la fois : les copies `carrier_command_test_cercle*.exe` ne sont pas touchées (elles portent l'ancien état).
- **Retour arrière** : `python tour/outils/patch_exe.py retirer --exe <vrai exe> --module pont_retour_x2 --sauvegarde tour/sauvegardes/carrier_command_1.5.18_original.exe --cest-le-vrai-jeu` (jeu fermé) → retombe sur `8E7FCBB6…`. **NE PAS UTILISER sur l'exe de Steam (état INCONNU : voir `patch_exe.py`)** : avec `--sauvegarde`, l'ancienne version de l'outil remplaçait TOUT le fichier sur un état « mélange » ou « inconnu » ; corrigé le 30/10/2026 (un exe inconnu ou d'un autre build est refusé, et la restauration complète exige en plus `--restaurer-tout-l-exe`, pour l'état « mélange » seulement). Pour retirer le module, ne pas donner `--sauvegarde`.
- **À mesurer** : 4 avions lancés puis rappelés, métrique « pont → hangar » (référence tour : 0:55 ; attendu ≈ 0:35), et regarder si le départ roule plus vite (effet de bord déduit §2).

## 6. Limites

- Tout est déduit du désassemblage d'une copie ; aucune partie jouée. Les deux modules sont minuscules et réversibles, mais « minuscule » ne veut pas dire « sans surprise » : surtout l'effet de bord sur les départs (§2).
- L'analyse de flot suppose que les appels de fonctions conservent `xmm7` (le compilateur le fait ici, d'après l'usage qu'il en fait) : vérifiée sur les lectures concernées, pas prouvée pour tout le programme.
- La greffe du « toucher près de l'ascenseur » (hélicos) reste à faire : elle demande du code ajouté (le SDK déjà posé, ou un chargeur à nous, ou un petit bloc de code dans le fichier).

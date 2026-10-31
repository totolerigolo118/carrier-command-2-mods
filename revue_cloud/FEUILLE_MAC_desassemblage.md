# FEUILLE MAC — répondre aux questions du désassemblage (suite de la revue cloud du 26/10/2026)

Pour la Claude Code du **Mac**. Lis d'abord `revue_cloud/RAPPORT_revue_2026-10-26.md` (les constats), puis cette feuille (comment y répondre).
Lis aussi `DEMARRER_cc2_patchs.md` sections 2 (règles avec le moddeur) et 3 (l'atelier).

## 0. En trois lignes pour le moddeur

- Une relecture a trouvé des **points douteux** dans les patchs CCTV, grue et vitesse, que seul le **programme d'origine du jeu** peut confirmer ou écarter.
- Cette feuille fait **lire** ce programme (rien n'est lancé, rien n'est modifié) et note les réponses dans un fichier.
- Après les réponses, Claude te dira quels patchs sont sûrs, lesquels corriger, et ce qu'il faudra essayer en jeu (toi seul, jeu fermé avant).

## 1. Règles (rappel, elles priment)

- Le moddeur ne code pas : français simple, **une seule question à la fois**, finir par la prochaine action concrète.
- **Ne jamais lancer ni fermer le jeu** sans le lui demander dans le message en cours.
- Cette feuille est en **lecture seule** : le programme lu est `sauvegarde/build_mac_origine` (jamais le jeu installé) ; les seuls autres fichiers lus sont les scripts Lua du jeu (un `grep`, comme le font déjà les tests). Aucune activation ni aucun retrait de patch pendant la lecture, sauf la précaution de l'étape 2 si le moddeur est d'accord.
- **Une réponse = des preuves** : copier dans `REPONSES_mac.md` les 3 à 15 lignes de désassemblage qui justifient la conclusion. Pas de « je pense » sans ligne à l'appui. Si une question ne se tranche pas, écrire « non tranché » et pourquoi.
- Ne **corrige** aucun module avant d'avoir la réponse ; toute correction suit « Ajouter un patch » (DEMARRER section 3, étapes 1 à 7) et l'accord du moddeur. Les générateurs sont à relancer **sur le Mac** (leur chemin de fichier dépend du compte).
- Le moddeur n'est pas obligé de rester : les étapes 3 et 4 se font sans lui. Il a des décisions à prendre aux étapes 1 et 2, puis à la fin (étape 5).

## 2. Préparation

```
cd <dossier de l'atelier>            # celui qui contient outil/, sauvegarde/, tests/ (= le dépôt cloné)
git status --short                    # s'il y a des fichiers modifiés qui ne sont pas à toi, ne pas y toucher
git fetch origin
git checkout -b mac/reponses-revue-26-10                # branche de travail : on ne touche pas à main
git merge origin/[branche]          # ne contient que des fichiers NOUVEAUX (revue_cloud/) : aucun conflit possible
ORIG="sauvegarde/build_mac_origine"
md5 -q "$ORIG"                        # doit afficher b0107170ddaf0245cbfee8a2d876aeb6
```
Si le `merge` demande une identité de commit : celle du dépôt (`git config user.email` = l'adresse noreply `[adresse retiree]`, jamais l'adresse professionnelle). Si le md5 est différent : **s'arrêter** et prévenir le moddeur (le programme n'est pas celui du 05/01/2026).

⚠️ Ne mets **jamais plusieurs options dans une variable** puis `$O` (piège zsh du 23/10). `"$ORIG"` seul, entre guillemets, est sans risque : c'est un seul argument.

L'outil : `revue_cloud/outils_mac/desasm.py` (python3, `objdump` et `nm` de Xcode). Trois commandes :
```
python3 revue_cloud/outils_mac/desasm.py lire   "$ORIG" DEBUT FIN [--reg rdx] [--drapeaux]
python3 revue_cloud/outils_mac/desasm.py sauts  "$ORIG" DEBUT:FIN [DEBUT:FIN ...]
python3 revue_cloud/outils_mac/desasm.py appels "$ORIG" CIBLE
```
`lire` marque `>>` les lignes qui citent un registre (toute sa famille : `rdx` = `rdx edx dx dl dh`) et, avec `--drapeaux`, `[F-ecrit]` / `[F-lit]`
(heuristique, à confirmer à l'œil). `sauts` fait **une passe** sur tout le programme (≈ 1 à 3 minutes) et liste les sauts ou appels directs qui
tombent **à l'intérieur** d'une plage (environ une minute : 33 secondes mesurées sous Linux pour 10 millions d'instructions ; le programme du jeu en a un peu moins de 10 millions ; mémoire ≈ 200 Mo). `appels` liste les sauts ou appels directs vers une adresse. En AT&T le **dernier opérande est la destination**
(`movq %rax, %rdx` écrit `rdx`) ; `cmp` et `test` n'écrivent aucun registre.

**Contrôle de l'outil sur le Mac (obligatoire, 30 secondes)** : l'outil n'a été essayé qu'avec l'`objdump` de Linux.
```
python3 revue_cloud/outils_mac/desasm.py lire "$ORIG" 0x1000ad74f 0x1000ad77c
```
Attendu : la 1re ligne est `movslq 0x60(%rax,%rcx), %rax` (c'est ce que dit `etudes/cctv_net.md` § 2.1), puis `movl $0x80, %r9d` et `movl $0x80, %r8d`, puis `cmpq $5, %rax` et `ja`.
Si le format est différent (adresses, `callq`, `##`), corriger les expressions régulières `RE_DIRECT` / `RE_INDIRECT` de `desasm.py` avant d'aller plus loin, et
le noter dans `REPONSES_mac.md`.

## 3. Étape 1 — trois vérifications qui ne demandent pas de désassemblage (5 minutes)

1. **`vitesse_escadrille.txt`** : `cat ~/Library/Application\ Support/Carrier\ Command\ 2/vitesse_escadrille.txt`. Si le fichier existe (probablement « 1 » laissé par les essais du 25/10), le noter. *Décision du moddeur* : le supprimer avant la première vraie partie (sinon le « premier lancement = NORMAL » n'a pas lieu).
2. **`color8` au chargement** : la barre (`fichiers/vitesse_boutons/library_custom_6.lua` lignes 21-25) appelle `color8(...)` **dès le chargement du fichier**, hors de toute fonction. Y a-t-il des scripts **d'origine** du jeu qui font pareil ? 
   ```
   ROMLUA="/Users/UTILISATEUR/Library/Application Support/Steam/steamapps/common/Carrier Command 2/carriercommand.app/Contents/Resources/rom_0/scripts"
   grep -n "color8(" "$ROMLUA"/*.lua | grep -v -E ":[0-9]+:[[:space:]]" | head -20
   ```
   (la 2e commande garde seulement les lignes qui ne commencent pas par une tabulation ou des espaces, donc probablement hors fonction ; regarder quelques lignes autour de chaque résultat pour confirmer). Si on en trouve (ex. une table de couleurs globale) : `color8` existe au chargement, la barre est sûre sur ce point → noter le fichier et la ligne. Si rien : c'est **le seul** endroit à le faire → risque : barre absente sans message. Correction d'une ligne (à proposer au moddeur) : construire `g_vit_couleurs` dans `vit_dessiner`, sous le `pcall`.
3. **Décisions de produit pour le moddeur** (voir `RAPPORT_revue_2026-10-26.md` § 3, points 1 à 3) : (a) la barre ne change presque pas la vitesse de **croisière** (≈ 2 %), elle agit surtout près du point ; (b) NORMAL s'applique **sans clic** au premier écran de contrôle (`g_vit_mode_defaut = 2`) ; (c) FLANK = carburant brûlé deux fois plus vite près d'un point. Lui demander, une question à la fois : mettre ECO par défaut pour le premier essai (`g_vit_mode_defaut = 1`) ? corriger l'en-tête de la barre et l'étude ? (rien à faire dans cette feuille, juste noter sa décision).

## 4. Étape 2 — avant tout, une précaution (à décider avec le moddeur)

`cctv_net`, `grue_annulation`, `vitesse_escadrille`, `vitesse_boutons` sont **actifs dans le jeu depuis le 25/10 et jamais essayés avec un joueur**. Le test du 25/10 (14 modules, chargement de la sauvegarde 18, 4 minutes) n'a pas planté, mais les écrans y étaient éteints.
Proposer au moddeur : **les retirer avant sa prochaine partie** (`Atelier CC2` → `--retirer cctv_net grue_annulation vitesse_escadrille vitesse_boutons`, jeu fermé) tant que les étapes 3 à 5 ne sont pas finies. C'est réversible. Noter sa décision.

## 5. Étape 3 — priorité A : courtes et décisives (≈ 20 minutes)

### A1. CCTV, greffe A : `rdx` est-il lu avant d'être réécrit ? (rapport point 4)
```
python3 revue_cloud/outils_mac/desasm.py lire "$ORIG" 0x1000ad74f 0x1000ad7a8 --reg rdx --reg rcx --reg r8 --reg r9
```
La greffe A remplace `0x1000ad74f..0x1000ad77c` et **écrit `rdx`** (le code d'origine ne le touche pas) ; elle revient à `0x1000ad77c`. Regarder les lignes **à partir de 0x1000ad77c jusqu'à l'appel de `create` (0x1000ad798)** :
pour `rdx` puis `rcx` : la **première** apparition est-elle une **écriture** (registre = dernier opérande : `mov ... %rdx`, `lea ... %rdx`, `xor`) → sans danger ; ou une **lecture** (source, ou dans une adresse `(%rdx,...)`), y compris comme argument 3 (`rdx`) ou 4 (`rcx`) de l'appel → **la greffe fausse l'argument : bug**.
- Écriture d'abord → noter « rdx mort ; rcx mort » avec les lignes.
- Lecture d'abord → noter « BUG » ; la correction (rapport point 4) est gratuite : prendre `rcx` comme pointeur dans `cctv_net.s` (lignes 19-21) puis `generer_cctv_net.py`, `tests/test_cctv_net.py` et `tests/test_patchs.py`.

### A2. Drapeaux vivants après chaque site remplacé (rapport point 5)
Sites et fin de bloc remplacé : CCTV A `0x1000ad77c`, B `0x10021ce85`, C `0x10015e6a8`, D `0x10021cf18` ; grue A `0x1001a8c0e`, B `0x1001ad9b2` ; vitesse `0x1001c2b8e`.
Pour chaque fin FIN :
```
python3 revue_cloud/outils_mac/desasm.py lire "$ORIG" FIN FIN+0x40 --drapeaux
```
(écrire l'adresse de fin + 0x40 en hexadécimal.) Règle : en partant de FIN, la **première** ligne marquée est `[F-ecrit]` → drapeaux **morts** (OK) ; est `[F-lit]` (un `jcc`, `cmov`, `set`, `adc`, `sbb`) **avant** tout `[F-ecrit]` → drapeaux **vivants** : la greffe doit les laisser comme le code d'origine → **bug à corriger** (le noter avec les lignes). Le rapport (point 5) signale surtout **B (FIN = 0x10021ce85)** puis **C (FIN = 0x10015e6a8)** : commencer par eux.

### A3. Aucun saut du jeu ne tombe au milieu d'un bloc remplacé (une seule passe)
```
python3 revue_cloud/outils_mac/desasm.py sauts "$ORIG" \
  0x1000ad74f:0x1000ad77c 0x10021ce70:0x10021ce85 0x10015e662:0x10015e6a8 0x10021cf13:0x10021cf18 \
  0x1001a8c01:0x1001a8c0e 0x1001ad9ad:0x1001ad9b2 0x1001c2b4b:0x1001c2b8e
```
Attendu : **0 saut direct vers l'intérieur** de chaque plage. Chaque saut trouvé = un `int3` (ou une instruction coupée) exécuté → plantage : **à noter en tête de la réponse** avec l'adresse source. Les **sauts indirects proches** listés (`jmp *%rax`) peuvent être des tables de sauts : pour chacun, lire ~20 lignes avant (`lire "$ORIG" <adresse-0x30> <adresse+1>`) à la recherche d'un `leaq .../(%rip)` suivi de `movslq (%rcx,%rax,4)` ; si la table existe, vérifier à la main que ses cibles ne tombent pas dans la plage. Si aucun indirect n'est proche : le noter.

### A4. Les adresses de fonctions du jeu appelées par la greffe de vitesse sont-elles les bonnes ? (rapport vitesse, [b])
Les 7 adresses de `outil/generateurs/generer_vitesse_escadrille.py` (table `JEU`, lignes ≈ 27-35) : `lua_gettop 0x1028278dc`, `lua_tointegerx 0x102827dc4`, `lua_pushinteger 0x10282801b`, et les stubs `_fclose 0x102867e42`, `_fgetc 0x102867e60`, `_fopen 0x102867e78`, `_fputs 0x102867e84`.
```
otool -Iv "$ORIG" | grep -E "0x1028278dc|0x102827dc4|0x10282801b|0x102867e42|0x102867e60|0x102867e78|0x102867e84"
nm -n "$ORIG" | grep -i -E "^0*10282(78dc|7dc4|801b)"
```
(si `otool -Iv` n'affiche pas ces adresses, lire chaque stub avec `desasm.py lire "$ORIG" 0x102867e60 0x102867e68` puis chercher le nom du pointeur dans `__DATA,__la_symbol_ptr` / `__got` avec `nm -m` ou `otool -Iv`). Attendu : exactement les noms ci-dessus, **chacun à sa place** (en particulier `_fgetc` en `0x102867e60`, jamais exercé en jeu). Une erreur de nom = plantage au 2e lancement du jeu après le premier clic de la barre.

### A5. Vitesse : `0x260(%r13)` est-il bien un pointeur d'équipe, et `+0x14` son numéro ? (rapport vitesse, [c])
```
python3 revue_cloud/outils_mac/desasm.py lire "$ORIG" 0x1001c2b2c 0x1001c2bb0 --reg r13 --reg rbx
```
Ce que la greffe suppose (`vitesse_escadrille.c`, plancher) : `r13` = l'avion, `rbx` = &vitesse, `0x260(%r13)` = pointeur d'équipe, `0x19(%rax)` = is_ai, `0x14(%rax)` = numéro d'équipe. À confirmer : (1) avant `0x1001c2b4b`, que valent `r13` et `rbx` ? (2) le même motif `mov 0x260(%r13),%rax` suivi d'un test de `0x19(%rax)` (ou de `0x14(%rax)`) existe-t-il ailleurs dans la même classe, par exemple dans le test de carburant de `c_vehicle_server_base::tick` (`nm -n "$ORIG" | grep -i "c_vehicle_server_base.*tick"`, puis `lire` sur la fonction, filtrée par `| grep -n "0x260("`) ? Si oui, noter l'adresse : c'est la preuve que `0x260` est bien un pointeur d'équipe. Question liée (plus tard, en jeu) : la ligne `moi=` du relevé donne-t-elle 1 pour l'équipe du moddeur ?

### A6. Grue, crochet A : d'où vient `rcx` ? l'alignement de pile ? la valeur de retour ? (rapport points 9 et 10)
Fonction `undock` : prologue vers `0x1001a8bd4`, crochet A à `0x1001a8c01`, épilogue `0x1001a8c0e`.
```
python3 revue_cloud/outils_mac/desasm.py lire "$ORIG" 0x1001a8bd4 0x1001a8c20 --reg rcx --reg rsp --reg rax
```
1. **`rcx`** : relever les instructions qui écrivent `rcx` avant `0x1001a8c01`, et comparer à ce que la greffe suppose : `outil/generateurs/grue_annulation.c` commentaire lignes 130-132 (« rdi gestionnaire, r14 avion, ebx son id, rcx carte ») et code lignes 145-147 (`movq %rcx, %rdx` avant `call ag_annuler`), `etudes/annuler_montee.md` ligne 87. Chercher aussi dans `cancel_undocking` l'appel virtuel 0 de la carte (`mov (%rcx),%rax ; call *(%rax)`) : est-ce **le même pointeur** ? 
2. **Alignement** : compter les `push` du prologue (chaque `push %rbp` compte) et le `sub $N, %rsp` éventuel. À l'entrée de la fonction `rsp ≡ 8 (mod 16)` ; au crochet, `rsp ≡ 8 − 8×(nb push) − N (mod 16)` ; il est **aligné** (≡ 0) si `8×(nb push) + N ≡ 8 (mod 16)`. Comparer à l'hypothèse écrite dans `grue_annulation.c` lignes 130-135 (« rsp aligné sur 16 ») et `etudes/annuler_montee.md` ligne 87 (pile alignée, nombre d'empilements).
3. **Épilogue `0x1001a8c0e`** : ne contient-il que des `pop` et `ret` ? l'appelant (`c_vehicle_server_carrier::undock`, `0x100193eaa`) lit-il `eax`/`al` au retour (`appels "$ORIG" 0x1001a8bd4`, puis `lire` sur chaque appelant, ~10 lignes après l'appel) ? La greffe met 0 ou 1 dans `eax`.

## 6. Étape 4 — priorité B : plus longues (à faire dans l'ordre, une par une)

### B1. Grue : les gestes 4 et 5 (rapport point 11)
Lire les deux fonctions de gestes : `lire "$ORIG" 0x1001ae940 0x1001aeb60`. Sans objet tenu (geste 5) et avec objet (geste 4) : la **remontée à 12 m** est-elle faite **hors** du `if` de la prise / du lâcher, ou dedans ? Un état de geste (avancement `0xc8`, phase) vit-il **hors de la liste** et faut-il le remettre à zéro quand on remplace la liste en plein geste ? Lire d'abord `etudes/annuler_montee.md` lignes 55-61 et 98 (ce que la greffe suppose).

### B2. Grue : le crochet B écrit 0x78 avant que le jeu le relise (rapport point 12)
```
python3 revue_cloud/outils_mac/desasm.py lire "$ORIG" 0x1001ad9a0 0x1001adb00 | grep -n "0x78("
python3 revue_cloud/outils_mac/desasm.py lire "$ORIG" 0x1001ae272 0x1001ae400 | grep -n "0x78(\|cmpl\|cmpb"
```
Après `0x1001ad9b2` (retour du crochet B), le jeu relit-il `0x78` **en mémoire** (et le teste `!= -1`) avant de lancer le roulage sur `load_lift_lower` ? Le roulage (`0x1001ae272`, `0x1001b10ce`) exige-t-il `dock_state = 3` ? **Et si on retire le module en plein retour** (sauvegarde faite pendant le mode 2) : l'avion avance-t-il quand même ? Cela décide si la phrase « retirer le module ne bloque rien » (DEMARRER ligne 321) est vraie.

### B3. Grue : ce que `take` pose et que l'annulation ne défait pas (rapport point 12)
`take` = `0x1001b0eb1`. `lire "$ORIG" 0x1001b0eb1 0x1001b1100`. Lister toutes les **écritures** sur l'avion, le gestionnaire et le porte-avions : **largeur de `0x21c`** (octet ? 32 bits ? — la greffe l'écrit en 32 bits avec un `movabs`), la consigne d'ascenseur `0x1538`, le chemin `load_lift_lower` (alloué où, libéré quand ?).

### B4. CCTV : toutes les sorties de `render_screen` passent-elles par le site D ? (rapport point 6)
`render_screen` démarre en `0x10021cc14` ; B = `0x10021ce70..0x10021ce85`, D = `0x10021cf13`.
```
python3 revue_cloud/outils_mac/desasm.py lire "$ORIG" 0x10021ce85 0x10021cf40
```
Entre B et D, y a-t-il un `ret`, ou un saut dont la cible est **> 0x10021cf18** ou vers l'épilogue de la fonction, **sans passer par `0x10021cf13`** ? Si oui : l'échelle reste à 4,0 jusqu'au prochain écran non-CCTV (scissors du pilotage ×4 sur une image).

### B5. CCTV : le viewport suit-il l'image ou la caméra ? (rapport point 7 — le plus important pour savoir si le patch marche)
```
otool -Iv "$ORIG" | grep -i -E "glviewport|glscissor|gldisable"
python3 revue_cloud/outils_mac/desasm.py appels "$ORIG" <adresse du stub de glViewport>
```
(`glScissor` = stub `0x10286807c` ; `appels "$ORIG" 0x10286807c` doit montrer **tous** les appelants : y en a-t-il d'autres que `element_clip::render` en `0x10015e662..` ?) Pour chaque appelant de `glViewport` dans le passage des écrans (`pass_screens`, `render_screen`) : d'où viennent largeur et hauteur — de l'**image** (`image+0x20/+0x24`, donc 512) ou de la **caméra d'interface** (128) ? Si c'est la caméra : l'interface est dessinée dans un coin ⇒ le patch ne marche pas tel quel. Noter aussi : quel tampon de profondeur est attaché aux images d'écran, de quelle taille ; que font les arguments `2, 8` de `mm_resource_handle_target::create` ; `create` garde-t-il largeur/hauteur telles quelles en `+0x20/+0x24` (pas de plafond ni d'arrondi) ?

### B6. Vitesse : `tick_control`, registres et drapeaux après le bloc, et l'accostage (rapport vitesse)
`lire "$ORIG" 0x1001c2b4b 0x1001c2bb0 --reg rax --reg rcx --reg rdx --reg rsi --reg rdi --reg r8 --reg r9 --reg r10 --reg r11 --drapeaux` : après `0x1001c2b8e`, jusqu'à `0x1001c2ba7`, quels registres sont **lus avant d'être écrits** ? (la greffe doit les laisser comme l'original ; le banc du cloud n'a comparé que `rax rcx xmm0 xmm1 0x2c8` + tous les registres sur le code des octets, pas la **vie** des registres dans le vrai jeu.) À quelle distance du porte-avions le gestionnaire d'accostage met-il `control_mode` à 3 : avant ou après les 800 derniers mètres où le plancher joue ? Le littéral 120 (`0x1028697b8`) est-il partagé (`appels` ne suffit pas : chercher les `mulss`/`movss` qui lisent `0x1028697b8(%rip)`) ?

## 7. Étape 5 — rendre compte

1. Créer `revue_cloud/REPONSES_mac.md` avec ce modèle, un bloc par question traitée :
```
## A1 — rdx avant l'appel create (CCTV, greffe A)
Verdict : RDX MORT | BUG | NON TRANCHÉ
Preuve (lignes copiées de desasm.py) :
    0x1000ad77c ...
    0x1000ad790 ...
Ce que ça change : (une phrase)
```
2. Résumé en tête de fichier : tableau « question → verdict ».
3. Commit + push **sur la branche de travail créée en section 2** (jamais sur `main` sans accord du moddeur) : `git add revue_cloud/REPONSES_mac.md && git commit -m "Réponses du désassemblage (revue du 26/10)" && git push -u origin mac/reponses-revue-26-10`. Identité du dépôt (section 12 de la passation), pas de mention « Claude » dans le message de commit. Le cloud pourra alors lire les réponses avec `git fetch`.
4. Dire au moddeur, en français simple et en **une phrase par patch**, ce qui est sûr, ce qui est douteux, ce qui demande une correction. Proposer la **prochaine action unique**.

## 8. Après les réponses : que faire (rien ne s'applique sans l'accord du moddeur)

| Résultat | Suite |
|---|---|
| A1 = BUG ou A2 = drapeaux vivants (CCTV) | corriger `cctv_net.s` (prendre `rcx`, ou comparer sans drapeaux : `lea -512(%rcx),%ecx` + `jecxz`), régénérer, relancer `tests/test_cctv_net.py` et `tests/test_patchs.py`, **puis seulement** réactiver |
| A3 = un saut tombe dans un bloc | ce site doit être déplacé ou le bloc élargi jusqu'à l'instruction qui contient la cible ; le patch concerné reste retiré jusque-là |
| A4 = un nom de stub est faux | corriger la table `JEU` du générateur ; ne pas réactiver `vitesse_escadrille` avant |
| A6 / B1 / B2 / B3 douteux | ne pas essayer l'annulation en jeu ; corriger la greffe d'abord ; le premier essai de la grue : sauvegarde n° 18, enregistrement juste avant, lancement normal d'abord, puis annulation « pas encore attrapé », puis « tenu » |
| B5 = le viewport suit la caméra | le patch CCTV ne peut pas marcher tel quel : étudier un 2e crochet (viewport) ou l'abandonner |
| Tout est propre | liste des essais en jeu dans `RAPPORT_revue_2026-10-26.md` § 6, **dans cet ordre** : barre de vitesse → roulage au retour (avions puis hélicos) → CCTV → grue |

Rappel : mettre à jour `DEMARRER_cc2_patchs.md` (état réel des patchs, ligne « pas encore mesuré » du roulage au retour, les quatre phrases de `RAPPORT_revue_2026-10-26.md` § 3 point 16) **après** que le moddeur a validé, pas avant.

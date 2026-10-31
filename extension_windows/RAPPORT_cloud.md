# Rapport de la session cloud : squelette de l'extension Windows

Date : 26/10/2026. Branche : celle de la session cloud, une branche à part (jamais `main` ; pas de PR, pas de fusion). Tout est dans `extension_windows/` ; rien d'autre n'a été touché.

## 1. Résumé

- **Compilateur : oui, on peut compiler du C Windows 32 bits ici.** `pip install ziglang==0.15.2` a suffi (Zig 0.15.2, la version que demande le SDK). Les deux autres pistes (paquet apt `gcc-mingw-w64-i686`, autre) n'ont pas été essayées : la première a marché. Détail et commandes exactes : `BUILD.txt`.
- **Le code est écrit et il compile** : la DLL `cc2x_cc2_patchs.dll` (32 bits, une seule fonction exportée, `cc2x_plugin_load`) se fabrique sans aucun avertissement. Elle n'est pas dans le dépôt (les `.dll` sont bloquées).
- **Il est testé sur Linux** : 48 tests / 732 contrôles réussis, plus le « tremplin » du crochet **exécuté pour de vrai** dans un programme 32 bits (138 contrôles), les mêmes tests refaits en 32 bits, et le côté Lua essayé avec un vrai Lua 5.3. En plus, j'ai **cassé le code exprès à 13 endroits** : les tests ont donné l'alerte à chaque fois. Sorties réelles plus bas.
- **Rien n'a tourné dans le jeu ni sous Windows.** Je n'ai aucune adresse du jeu Windows et je n'en ai inventé aucune : les 8 listes d'endroits à modifier sont **vides**, avec 14 repères `TODO(tower step N)`.
- Par défaut **tous les groupes sont éteints** : l'extension se contente de vérifier la version du jeu, de lire le fichier de réglages et d'écrire une ligne par groupe dans le journal.

## 2. Ce qui a été fait (liste courte ; l'explication simple est dans `README_FR.md`)

| Demandé | Où | Fait |
|---|---|---|
| A. Vérifier le compilateur | `BUILD.txt`, `build.py` | Oui. |
| Portier de version | `src/cp_pe.c`, `src/cc2_patchs.c` | Refuse sauf si : nom de version `1.5.18-win32` **et** horodatage PE `0x6a36c177` **et** taille `0x00af7000` (lus dans l'en-tête du programme du jeu). Écrit la raison, rend la main proprement. |
| Écriture sûre | `src/cp_patch.c`, `src/cp_win.c` | `cp_write` : vérifie les octets d'origine, écrit (VirtualProtect + FlushInstructionCache), relit. Tout-ou-rien par groupe avec retour arrière, refuse les chevauchements, idempotent, recale les adresses avec `api->va()`. La logique pure est séparée des appels Windows (qui sont dans `cp_win.c` seulement). |
| Nombres à nous | `src/cp_tunables.c` | Table alignée sur 16 octets, valeurs du Mac par défaut, modifiables dans l'ini ; aide `cp_abs_float_redirect` pour rediriger une lecture de constante après vérification des octets (et de la valeur de la constante d'origine). Les constantes du jeu ne sont jamais modifiées. |
| Groupes et ini | `src/cp_groups.c`, `src/cp_config.c`, `src/cp_ini.c`, `cc2_patchs.ini.example` | 8 groupes, un interrupteur chacun, tout éteint par défaut, analyseur écrit à la main, une ligne de journal par groupe (appliqué / sauté / refusé + raison). |
| Crochet sûr | `src/cp_hook.c`, `src/cp_hook.h` | Sauvegarde et restaure `xmm0`–`xmm7`, les drapeaux et les registres généraux autour d'un appel C ; contraintes sur les instructions déplacées documentées. |
| Table des modules | `src/cp_groups.c` | Listes **vides**, commentaire par groupe : nombre et types d'endroits attendus (partie 10), octets d'origine du Mac marqués `MAC-ONLY` (générés par `tools/mac_table_to_comments.py`, jamais utilisés comme données). |
| Côté Lua de la vitesse | `src/cp_speed.c`, `src/cc2_patchs.c`, `lua/cc2_vitesse_shim.lua` | Simple, donc fait : la fonction `cc2x.speed.mode(equipe [, mode])` suit le même contrat que `cc2_vitesse` du Mac ; un petit fichier Lua définit la fonction **globale** `cc2_vitesse` attendue par `library_custom_6.lua`. |
| C. Tests sur Linux | `tests/` | Voir plus bas. |
| D. Documents | `README_FR.md`, ce rapport | Oui. |

## 3. Ce qui compile

Dernière fabrication (sortie réelle de `python build.py`, chemins raccourcis) :

```
python -m ziglang cc -target x86-windows-gnu -std=c11 -O2 -Wall -Wextra -Wno-unused-parameter -Werror=implicit-function-declaration -fno-strict-aliasing -shared -I <sdk> -I src  <les 11 fichiers de src/>  -o dist/cc2x_cc2_patchs.dll   (ligne complète : voir BUILD.txt)
built extension_windows/dist/cc2x_cc2_patchs.dll (235008 bytes)
  machine 0x014c (0x014c = i386), PE32: True, DLL: True
  exports: cc2x_plugin_load
  imports: api-ms-win-crt-private-l1-1-0.dll, api-ms-win-crt-runtime-l1-1-0.dll, api-ms-win-crt-string-l1-1-0.dll, KERNEL32.dll, api-ms-win-crt-stdio-l1-1-0.dll, api-ms-win-crt-heap-l1-1-0.dll
check OK
```

La DLL est bien un fichier **PE32 / i386 / DLL** et exporte `cc2x_plugin_load`. Elle appelle la bibliothèque C universelle de Windows (présente depuis Windows 10) et `KERNEL32`, comme l'exemple du SDK. L'exemple `hello.c` du SDK compile aussi avec la même commande.

## 4. Ce qui a été testé et comment

`tests/run_tests.sh` fait cinq choses, toutes sur Linux :

1. **Tests unitaires et du point d'entrée** (gcc, avec les détecteurs d'erreurs mémoire AddressSanitizer et UBSan). Le jeu est remplacé par une **fausse mémoire** : un tableau d'octets placé à une adresse volontairement différente de `0x400000` (pour que le recalage des adresses soit réellement exercé), avec la possibilité de faire échouer ou de fausser la N-ième écriture. Les tests demandés y sont : mauvais octets d'origine → refusé et rien d'écrit ; une écriture qui échoue au 4ᵉ endroit → les 3 premiers sont remis ; chevauchement refusé (dans un groupe et entre deux groupes) ; deuxième application sans effet ; alignement de la table de nombres sur 16 octets ; analyse de l'ini (fins de ligne, commentaires, erreurs, nombres, 0/1/on/off) ; lecture de l'en-tête sur un **faux programme Windows construit à la main** (bon, mauvais horodatage, mauvaise taille, mauvais nom de version, en-têtes tronqués ou 64 bits). Ils couvrent aussi chaque type de retouche, le point d'entrée complet avec un faux SDK (« version inconnue → refus propre », « ini absent → tout sauté », « groupe allumé mais liste vide → refusé »), et le contrat de la fonction Lua de vitesse (les cas relevés par la sonde du 25/10 sont repris).
2. **Désassemblage du tremplin** avec `objdump` (pour le relire à l'œil).
3. **Exécution réelle du tremplin** dans un programme 32 bits sous Linux : une fonction de test remplit `xmm0`–`xmm7` et des registres, passe par le crochet ; le code C appelé **détruit tous les `xmm`** et les drapeaux. On vérifie que tout est restitué, que les modifications faites par le C sont prises en compte, que la pile est alignée sur 16 octets quelle que soit sa position, et que le sens de copie (DF) est remis à zéro pour le C. **Limite :** c'est Linux, pas Windows ; la convention d'appel (`cdecl`) est la même, mais ça ne prouve rien sur le jeu.
4. Les **mêmes tests unitaires compilés en 32 bits** (pour attraper les erreurs de taille de pointeur).
5. Le **côté Lua** avec un vrai Lua 5.3 (paquet `lupa`) : la fonction globale `cc2_vitesse` apparaît seulement si l'extension fournit `cc2x.speed.mode`, garde le nombre d'arguments (1 = lire, 2 = régler), et `library_custom_6.lua` marche par-dessus (NORMAL par défaut, puis FLANK ; barre cachée sans l'extension).

Sortie réelle de `tests/run_tests.sh` (dernière exécution, code de sortie 0) :

```
### 1. unit and entry-point tests (gcc (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0)
== cc2_patchs host tests ==
[ ok ] test_write_basic                               (8 checks)
[ ok ] test_write_wrong_expected_refused              (4 checks)
[ ok ] test_write_idempotent                          (5 checks)
[ ok ] test_write_failures_restore                    (5 checks)
[ ok ] test_group_all_sites_ok                        (9 checks)
[ ok ] test_group_wrong_bytes_refused_nothing_written (6 checks)
[ ok ] test_group_write_failure_rolls_back            (6 checks)
[ ok ] test_group_verify_failure_rolls_back           (3 checks)
[ ok ] test_group_rollback_failure_reported           (3 checks)
[ ok ] test_group_overlap_refused                     (5 checks)
[ ok ] test_group_overlap_with_other_group_refused    (5 checks)
[ ok ] test_group_second_apply_idempotent             (11 checks)
[ ok ] test_group_empty_and_malformed_refused         (7 checks)
[ ok ] test_group_revert                              (7 checks)
[ ok ] test_kind_abs_float_redirect_and_rebase        (6 checks)
[ ok ] test_kind_abs_float_unrebased_operand_refused  (3 checks)
[ ok ] test_kind_abs_float_stock_value_checked        (5 checks)
[ ok ] test_kind_abs_float_operand_outside_image_refused (4 checks)
[ ok ] test_kind_abs_float_vec4_needs_aligned_table   (9 checks)
[ ok ] test_kind_imm_with_float_from_tunable          (8 checks)
[ ok ] test_kind_imm_rebases_absolute_operands        (3 checks)
[ ok ] test_kind_jump_retargets_rel32                 (5 checks)
[ ok ] test_kind_jump_malformed_refused               (5 checks)
[ ok ] test_kind_hook_builds_trampoline               (11 checks)
[ ok ] test_kind_hook_displaced_absolute_operand      (3 checks)
[ ok ] test_kind_hook_refusals_leave_game_untouched   (32 checks)
[ ok ] test_hook_emit_layout                          (13 checks)
[ ok ] test_hook_emit_relocation_and_limits           (12 checks)
[ ok ] test_tunables_alignment                        (79 checks)
[ ok ] test_tunables_defaults_are_mac_values          (46 checks)
[ ok ] test_tunables_derive_follows_overrides         (13 checks)
[ ok ] test_ini_parser                                (15 checks)
[ ok ] test_number_and_bool_parsing                   (61 checks)
[ ok ] test_config_defaults_all_off                   (18 checks)
[ ok ] test_config_groups_and_tunables                (15 checks)
[ ok ] test_ini_example_matches_code                  (54 checks)
[ ok ] test_pe_parse_and_gate                         (19 checks)
[ ok ] test_pe_malformed                              (12 checks)
[ ok ] test_speed_contract                            (28 checks)
[ ok ] test_speed_floors                              (7 checks)
[ ok ] test_hook_callbacks                            (17 checks)
[ ok ] test_group_table                               (58 checks)
    (site tables hold 0 site(s) in total: 0 = nothing ported yet)
[ ok ] test_group_tables_wellformed                   (25 checks)
[ ok ] test_entry_refuses_unknown_builds              (21 checks)
      | 1 [cc2_patchs] cc2_patchs skeleton starting (SDK 0.4.0, game build 1.5.18-win32)
      | 1 [cc2_patchs] build gate: 1.5.18-win32, PE timestamp 0x6a36c177, SizeOfImage 0x00af7000: known build
      | 1 [cc2_patchs] no C:\Users\x\AppData\Roaming\Carrier Command 2\cc2x\cc2_patchs.ini: every group stays off
      | 1 [cc2_patchs] group energy_lift_crane_taxi: skipped (off in the ini, default)
      | 1 [cc2_patchs] group helicopters: skipped (off in the ini, default)
      | 1 [cc2_patchs] group return_taxi: skipped (off in the ini, default)
      | 1 [cc2_patchs] group landing_circuit: skipped (off in the ini, default)
      | 1 [cc2_patchs] group speed_modes: skipped (off in the ini, default)
      | 1 [cc2_patchs] group crane_cancel: skipped (off in the ini, default)
      | 1 [cc2_patchs] group cctv: skipped (off in the ini, default)
      | 1 [cc2_patchs] group recorder: skipped (off in the ini, default)
[ ok ] test_entry_known_build_no_ini_everything_off   (9 checks)
      | 1 [cc2_patchs] cc2_patchs skeleton starting (SDK 0.4.0, game build 1.5.18-win32)
      | 1 [cc2_patchs] build gate: 1.5.18-win32, PE timestamp 0x6a36c177, SizeOfImage 0x00af7000: known build
      | 2 [cc2_patchs] ini line 5: unknown group 'bogus'
      | 1 [cc2_patchs] read C:\Users\x\AppData\Roaming\Carrier Command 2\cc2x\cc2_patchs.ini (101 bytes, 1 warning(s), 1 tunable(s) overridden)
      | 2 [cc2_patchs] group energy_lift_crane_taxi: refused: site table is empty (not ported yet) [plan step 3]
      | 1 [cc2_patchs] group helicopters: skipped (off in the ini, default)
      | 1 [cc2_patchs] group return_taxi: skipped (off in the ini, default)
      | 2 [cc2_patchs] group landing_circuit: refused: site table is empty (not ported yet) [plan step 5]
      | 1 [cc2_patchs] group speed_modes: skipped (off in the ini, default)
      | 1 [cc2_patchs] group crane_cancel: skipped (off in the ini, default)
      | 1 [cc2_patchs] group cctv: skipped (off in the ini, default)
      | 1 [cc2_patchs] group recorder: skipped (off in the ini, default)
[ ok ] test_entry_group_on_but_table_empty_is_refused (9 checks)
[ ok ] test_entry_oversized_ini_warns                 (3 checks)
[ ok ] test_entry_lua_speed_stub_contract             (20 checks)

48 tests, 732 checks, 0 failed check(s)
RESULT: ALL PASS

### 2. trampoline disassembly (objdump, i386, intel syntax)
00000000 <.data>:
   0:	68 7c 00 00 00       	push   0x7c
   5:	9c                   	pushf
   6:	60                   	pusha
   7:	81 ec 80 00 00 00    	sub    esp,0x80
   d:	0f 11 04 24          	movups XMMWORD PTR [esp],xmm0
  11:	0f 11 4c 24 10       	movups XMMWORD PTR [esp+0x10],xmm1
  16:	0f 11 54 24 20       	movups XMMWORD PTR [esp+0x20],xmm2
  1b:	0f 11 5c 24 30       	movups XMMWORD PTR [esp+0x30],xmm3
  20:	0f 11 64 24 40       	movups XMMWORD PTR [esp+0x40],xmm4
  25:	0f 11 6c 24 50       	movups XMMWORD PTR [esp+0x50],xmm5
  2a:	0f 11 74 24 60       	movups XMMWORD PTR [esp+0x60],xmm6
  2f:	0f 11 7c 24 70       	movups XMMWORD PTR [esp+0x70],xmm7
  34:	89 e6                	mov    esi,esp
  36:	fc                   	cld
  37:	83 e4 f0             	and    esp,0xfffffff0
  3a:	83 ec 08             	sub    esp,0x8
  3d:	68 03 00 02 00       	push   0x20003
  42:	56                   	push   esi
  43:	b8 00 01 00 70       	mov    eax,0x70000100
  48:	ff d0                	call   eax
  4a:	89 f4                	mov    esp,esi
  4c:	0f 10 04 24          	movups xmm0,XMMWORD PTR [esp]
  50:	0f 10 4c 24 10       	movups xmm1,XMMWORD PTR [esp+0x10]
  55:	0f 10 54 24 20       	movups xmm2,XMMWORD PTR [esp+0x20]
  5a:	0f 10 5c 24 30       	movups xmm3,XMMWORD PTR [esp+0x30]
  5f:	0f 10 64 24 40       	movups xmm4,XMMWORD PTR [esp+0x40]
  64:	0f 10 6c 24 50       	movups xmm5,XMMWORD PTR [esp+0x50]
  69:	0f 10 74 24 60       	movups xmm6,XMMWORD PTR [esp+0x60]
  6e:	0f 10 7c 24 70       	movups xmm7,XMMWORD PTR [esp+0x70]
  73:	81 c4 80 00 00 00    	add    esp,0x80
  79:	61                   	popa
  7a:	9d                   	popf
  7b:	c3                   	ret
  7c:	8d 40 01             	lea    eax,[eax+0x1]
  7f:	0f 1f 00             	nop    DWORD PTR [eax]
  82:	e9 7f 0f 00 00       	jmp    0x1006

### 3. trampoline executed in a 32-bit process
== trampoline executed in a 32-bit process (pointer size 4) ==
  mode 0 (callback clobbers all xmm and flags, changes nothing): ok
  mode 1 (callback edits eax, ebx, xmm1, CF through the context): ok
  mode 2 (callback redirects with jump_to): ok

138 checks, 0 failed
RESULT: ALL PASS

### 4. the same unit tests compiled as a 32-bit program (pointer size 4, -Werror)
build/test_all32: ELF 32-bit LSB executable, Intel 80386, version 1 (SYSV), statically linked

48 tests, 732 checks, 0 failed check(s)
RESULT: ALL PASS

### 5. Lua shim (cc2_vitesse over cc2x.speed.mode) with a real Lua 5.3, optional
shim with plugin: global cc2_vitesse defined, contract and argument count kept
shim without plugin: no global (type(cc2_vitesse) == 'nil'), as library_custom_6.lua expects
shim with an existing cc2_vitesse: left alone
library_custom_6.lua vit_lire / vit_choisir work through the shim (NORMAL by default, then FLANK)
library_custom_6.lua without the plugin: vit_lire() == 0 (bar hidden)
LUA SHIM CHECK: ALL PASS
```

**Casse volontaire du code** (test des tests). J'ai modifié une copie du code à 13 endroits, un à la fois, et relancé tout : un test doit échouer à chaque fois. Résultat réel :

```
[M1 skip the original-bytes check of a group] exit=1, lines containing FAIL: 9
[M2 no rollback after a failed write] exit=1, lines containing FAIL: 12
[M3 absolute operand not rebased] exit=1, lines containing FAIL: 16
[M4 trampoline forgets to reload xmm3] exit=1, lines containing FAIL: 31
[M5 build gate ignores SizeOfImage] exit=1, lines containing FAIL: 9
[M6 overlap check removed] exit=1, lines containing FAIL: 6
[M7 second apply writes again (no idempotence)] exit=1, lines containing FAIL: 8
[M8 stack not aligned in the trampoline] exit=1, lines containing FAIL: 12
[M9 cld removed from the trampoline] exit=1, lines containing FAIL: 7
[M10 flags not restored (popfd removed)] exit=1, lines containing FAIL: 6
[M11 general registers not saved (pushad removed)] exit=1, lines containing FAIL: 6
[M12 tunable stock value not checked] exit=1, lines containing FAIL: 11
[M13 tunable table alignment not checked] exit=1, lines containing FAIL: 6
(exit=1 = le test a échoué = la casse a été détectée ; exit=0 aurait voulu dire « non détectée »)
```

Cet exercice a servi : une première version de mes tests laissait passer deux casses du tremplin (pile non alignée, sens de copie non remis à zéro) parce que le programme d'essai appelait toujours le crochet avec une pile déjà alignée. Les tests ont été complétés (4 positions de pile, sens de copie forcé) et attrapent maintenant les deux. Les tests ont aussi attrapé un **vrai défaut** de mon code pendant l'écriture : une table de nombres « non rattachée à une adresse » était déclarée alignée (corrigé).

## 5. Ce qui n'est PAS vérifié

- **Rien n'a tourné sous Windows ni dans le jeu.** Il n'y a ni Windows ni Wine ici. Les appels Windows (`VirtualProtect`, `VirtualQuery`, `VirtualAlloc`, `FlushInstructionCache`, `CreateFileA`…) sont **compilés mais jamais exécutés**.
- **La DLL n'a jamais été chargée par le SDK.** Le point d'entrée a été essayé avec un **faux SDK** de ma fabrication (journal, Lua, version), pas avec le vrai.
- **L'en-tête du programme** : le portier a été essayé sur un en-tête fabriqué à la main, pas sur le vrai `carrier_command.exe` (que personne n'a vu).
- **Le tremplin** n'a été exécuté que sous Linux 32 bits. Pas sous Windows, pas dans le jeu. Il ne sauvegarde pas les calculs de l'ancien processeur « x87 » ni le registre de contrôle des calculs à virgule (MXCSR) : inutile tant que le jeu n'en dépend pas à l'endroit du crochet, **à vérifier à chaque endroit choisi**. Un saut relatif caché dans les octets déplacés n'est **pas détectable** par le programme (seul le tout premier est recalé).
- **Le recalage des adresses (ASLR)** repose sur l'hypothèse que le chargeur de Windows corrige lui-même les adresses absolues dans le code du jeu quand il le déplace. Si le jeu n'est jamais déplacé (base `0x400000` toujours), ça ne change rien ; si l'hypothèse était fausse, la vérification des octets **refuserait** (message clair) plutôt que d'écrire de travers.
- **Le moment du chargement** : le SDK appelle l'extension dans le « verrou du chargeur » de Windows. On n'y fait que des lectures/écritures de mémoire et de fichier simples, pas de fil d'exécution ni de chargement de DLL, comme le demande le SDK, mais ça n'a pas été éprouvé.
- **Lua** : la vraie fonction C n'a pas tourné dans le vrai Lua du jeu ; le petit fichier Lua a été essayé avec un Lua 5.3 ordinaire et une fonction Python imitant le contrat.
- **Les valeurs** par défaut sont celles du Mac. `NORMAL` = 61 / 91 m/s est une **estimation** (déjà notée comme telle côté Mac).
- **Le groupe landing_circuit** est en un seul bloc (réglage B). Le réglage A seul (les 3 sauts) demandera de le scinder, si la simulation montre que B est plus lent.
- **Rien n'est vérifié pour les 7 autres groupes** : leurs listes sont vides, et les crochets de `speed_modes`, `crane_cancel`, `cctv` et `recorder` ne font **rien** pour l'instant (c'est voulu : une liste remplie trop tôt ne peut pas changer le jeu).

## 6. Ce que la tour doit trouver, groupe par groupe

Tous les repères de recherche sont dans la section 6 de la feuille et, pour chaque groupe, dans le commentaire de `src/cp_groups.c`. « Étape » = étape du plan (section 5 de la feuille). **Préalable (étape 1) :** pour chaque groupe, retrouver les endroits par les empreintes et remplir le tableau « Mac → Windows ».

| Groupe (clé de l'ini) | Équivalent Mac | Ce que la tour doit trouver | Étape |
|---|---|---|---|
| `energy_lift_crane_taxi` | `ascenseur_x2` : 34 retouches | **1** instruction qui écrit la part d'énergie 0,4 (à passer à 0,8) ; environ **33** instructions qui lisent des constantes : pas de la plateforme (0,025 et son négatif), crane horizontale (1/6) et verticale (1/30) et rotation (0,04) avec leurs négatifs, accélération du roulage (0,05) et plafond (2,5) **7 fois chacun**. Le compilateur Microsoft peut avoir fusionné les négatifs : le nombre peut différer. | 3 |
| `helicopters` | `helicos_approche_x2` + `helicos_pres_ascenseur` : 5 retouches | **3** lectures de constantes (visée 50 → 100 ; visée max 120 → 48 ; seuil de train 20 → 70) et **1** endroit juste avant le plancher −2,0 de la hauteur visée pour le crochet qui retire 23,5 (la greffe de 21 octets du Mac devient un simple crochet : 4 endroits au lieu de 5). Dire aussi **quel registre `xmm` contient la hauteur** (réglage `heli_height_xmm`). | 4 |
| `return_taxi` | `pont_retour_x2` : 3 retouches | **3** lectures de la constante partagée 30,0 aux trois tronçons de retour (états 5, 6, 7), à rediriger vers 15,0. | 5 |
| `landing_circuit` | `atterrissage` : 10 retouches | **3** sauts à rediriger vers le bloc qui donne la piste (et l'**adresse de ce bloc**), **1** instruction `addss` à changer en `subss`, **4** lectures de vecteurs de 4 nombres (alignement 16 octets), **2** lectures du nombre 600 (→ −1800). | 5 |
| `speed_modes` | `vitesse_escadrille` : 3 retouches | L'endroit où la vitesse visée des avions est bornée entre 48 / 72 et 144 (**1 ou 2** crochets) ; dans quels registres sont l'avion, son équipe et sa vitesse ; comment reconnaître un Manta. Le côté Lua est **déjà fait**. Corps du crochet à écrire dans `src/cp_hooks.c`. | 6 |
| `crane_cancel` | `grue_annulation` : 3 retouches | **2** crochets dans le gestionnaire des avions du porte-avions ; ses **décalages 32 bits** (par les analyseurs d'état sauvegardé) ; réécriture de la logique de `grue_annulation.c` (convention d'appel 32 bits). Seulement après les étapes 3 à 6. | 7 |
| `cctv` | `cctv_net` : 5 retouches | **4** endroits du rendu : taille d'image selon le type d'écran, taille de la caméra d'interface, rectangle de découpe, remise à zéro de l'échelle ; réécriture de la logique de `cctv_net.s`. Seulement si le moddeur le demande. | 8 |
| `recorder` | `ecriture_releve` : 3 retouches | Soit **2** crochets sur les deux lectures du flux de sortie de `print()`, soit **rien** (adapter `library_custom_5.lua` pour appeler `cc2x.log`, plus simple). À décider. | 8 |

## 7. Choses remarquées, à répercuter

1. **Octets d'origine : ceux du fichier.** Les tableaux doivent contenir les octets **du fichier `.exe`** (adresses absolues comprises, base `0x400000`), pas ceux relevés dans le jeu en marche : la couche d'écriture recale elle-même les adresses absolues si Windows a déplacé le programme. La feuille (section 4) dit « vérifie toi-même les octets d'origine » : c'est fait par cette couche, il suffit de lui donner les bons.
2. **`build.py` du SDK** attend `include/cc2x.h` ; ici l'en-tête est à la racine de `sdk_public_cc2x/`. Le `build.py` de ce dossier le trouve tout seul (option `--sdk` sinon).
3. **Fonction Lua de vitesse** : elle n'est enregistrée que si le groupe `speed_modes` est réellement appliqué. Pour essayer la barre ECO / NORMAL / FLANK **avant** que le crochet existe, il y a un interrupteur d'essai `lua_speed_stub = 1` (section `[debug]` de l'ini) : les boutons changent alors un nombre mais **aucune vitesse** (un avertissement le dit dans le journal). Le fichier `lua/cc2_vitesse_shim.lua` est à coller en tête de `library_custom_6.lua` sur la tour (je n'ai pas modifié `lua_a_installer/`).
4. **Journal** : le jeu écrit dans `cc2x.log` (dossier du jeu). Les lignes de l'extension ont la forme `[cc2_patchs] group <nom>: applied | skipped | refused: <raison> [plan step N]`.
5. **Registre de chevauchements du SDK** : l'extension n'utilise pas les fonctions d'écriture du SDK (`patch_*`), donc elle ne connaît pas leur registre de chevauchements. Elle compense en vérifiant les octets d'origine : un endroit déjà modifié par le SDK ou par une autre extension (par exemple Island Airfields) sera **refusé**, pas écrasé.
6. **Bibliothèque C** : la DLL importe une entrée de plus que l'exemple du SDK (`api-ms-win-crt-private`, pour `strchr`). Sans importance sous Windows 10 ou 11 ; à regarder en premier si la DLL refuse de se charger.
7. **Identité git** : le git global de cette machine avait une autre identité ; j'ai réglé l'identité **locale** du dépôt sur `[pseudo retire]` (adresse « noreply » de la feuille section 12, avec un `@` normal : l'énoncé en montrait un autre caractère) avant tout commit.

## 8. Crédit utilisé

Je n'ai pas d'outil pour lancer `/usage` et les informations de la session n'indiquent aucun crédit. **Le moddeur peut le lire lui-même avec `/usage`.** Seul repère disponible : le compteur de la session est passé d'environ 15,0 millions à environ 14,5 millions d'unités (les « tokens » restants), soit **environ 0,5 million consommé** ; ce n'est pas un montant en dollars. Les informations de la session affichent aussi un état d'alerte (« allowed_warning ») sur la **limite hebdomadaire** d'utilisation du compte : à surveiller avant de lancer d'autres tâches cloud.

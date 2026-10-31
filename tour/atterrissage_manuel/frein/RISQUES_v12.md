# Notice des risques : `cc2x_frein.dll` v12 (31/10/2026)

**Empreinte** : `941DFFB9F1671CB351A69B826B14E62AB9978390C888257DA699E8584ADC59B3` (240 640 octets), dans `C:\Users\UTILISATEUR\Documents\cc2-sdk-travail\dist\`. **Pas posée** au moment de l'écriture. Retour arrière : la v10 (`dist_v10\`, `66731A35…`, celle qui est dans le jeu aujourd'hui). La v11 (`dist_v11\`, `3CD7225D…`) n'a jamais été posée et ne doit pas l'être.

## En une phrase par cas

| Réglage | Ce que fait la v12 | Risque |
|---|---|---|
| `frein.ini` sans `recall_force` (comme aujourd'hui) | **exactement la v10** : frein, maintien, moteur coupé, tenue au rappel ; **aucun crochet** dans le jeu | 🟢 |
| `recall_force=1` au lancement, aucun rappel d'un avion tenu | 9 crochets posés au démarrage mais **inertes** (comme les 8 de la v10/v11, jamais un souci en 1420 s) | 🟢 |
| `recall_force=1`, ordre de retour d'un avion tenu, arrêté | H1/H2 (le jeu donne la piste, mesuré 3 fois), puis **H5** envoie l'avion au **test de toucher** du jeu, celui des hélicoptères ; si le test passe, **le jeu fait sa prise en charge** (pas de retour arrière, comme pour l'IA) | 🟡 |

## Ce qui change par rapport à la v10 (posée) et à la v11 (abandonnée)
1. **H4 supprimé** (forcer l'engagement : les portes B et C ne peuvent pas passer pour un avion arrêté, et un engagement sans prise en charge bloquait la piste pour toute la partie).
2. **H5** au même site (`0x6fe470`, 7 octets identiques) : pour l'avion signalé seulement, état de piste 3, piste à lui, baie libre de la bonne classe, vitesse < 2 m/s : `edi` = gestionnaire, `esi` = navire, saut en `0x6ff20a`. **Aucune écriture dans la mémoire du jeu.** Au plus 30 sauts par fenêtre (≈ 1 s), puis le jeu reprend son chemin normal (abandon propre).
3. **Sonde en lecture seule** en `0x6ff379` : la baie que le jeu obtient dans sa prise en charge.
4. **Suivi en lecture seule** après la prise en charge : `dock`, `flight`, `attached`, état de piste, carburant, jusqu'au hangar (`dock=4`) puis 20 s.
5. **Table par build** : ancien exe (`0x6a36c177`, nom `1.5.18-win32`) et build Steam du 28/10 (`0x6ae228f3`, nom `1.5.18-win32-6ae228f3`). Le plugin ne se charge que si le nom donné par le SDK **et** l'horodatage de l'exe lancé correspondent à la même ligne.
6. Journal : ligne de plugin jusqu'à 512 caractères (au lieu de 300 ; le SDK accepte 1024).

## Ce qui est prouvé (hors jeu)
- **Sites** (`outils/verifier_sites_v12.py`, sortie `frein/VERIF_sites_v12.txt`) : dans les deux exe, les 9 sites ont les octets attendus, **aucune relocation** dans les octets déplacés, **aucun saut ni appel direct de tout le programme** vers l'intérieur des octets déplacés ; cibles de H2 et H5 au début d'une instruction, la bonne ; **registres vivants en `0x6ff20a`** : `ebx` (constant dans la fonction), `edi`, `esi` (fournis par H5), **aucun xmm** ; aucun `push` en attente avant H5 (même profondeur de pile qu'à la cible).
- **Chemin des hélicos** (LU, `PISTE_v12_comme_un_helico.md`) : un hélico posé arrive en `0x6ff20a` par sa propre branche de l'état 3, sans engagement ; le bloc de prise en charge tourne donc à chaque hélico qui se pose.
- **Test hôte** (`tests/test_frein.c`, UBSan, `-Werror`) : **334 contrôles, 0 échec** (T28 H5, T29 prise en charge et suivi jusqu'au hangar, T30 verdicts, T31 fenêtre unique, T32 table du nouvel exe ; les tests de la v1 à la v10 inchangés) ; **12 pannes injectées** dans une copie du plugin (H5 sans `edi`, sans `esi`, mauvaise cible, sans contrôle du propriétaire, écrit en mémoire, sans budget, sans limite de vitesse, classe de baie ignorée, sonde qui modifie `eax`, horodatage non vérifié, mauvaise cible du nouvel exe, suivi qui freine) : **les 12 font échouer le test**.
- **Compilation** : 2 compilations identiques hors horodatage ; imports = ceux de la v11 **plus `GetModuleHandleA`** (lire l'horodatage de l'exe du jeu) ; aucune DLL réseau, registre, interface ; aucune chaîne suspecte ; 6 enveloppeurs xmm (un par corps de crochet).
- `tester_poser.py` 43/43, `tester_lancer.py` 29/29 ; `poser.py maj --a-blanc` sur le vrai dossier : « remplacer cc2x_frein.dll (notre version précédente) par la nouvelle », rien écrit.

## Ce qui n'est PAS prouvé (seul l'essai le dira)
| Inconnu | Si ça tourne mal | Gravité |
|---|---|---|
| Le 2e champ des roues (`≤ 0,1`) pour l'avion tenu au frein | le test de toucher refuse ; `VERDICT: TOUCH TEST NEVER PASSED` avec les valeurs ; abandon propre | 🟢 |
| Le saut H5 en vrai (jamais exécuté) | plantage du jeu (partie jetable) | 🟡 |
| Le joint qui tire un avion qui vient d'être tenu au frein (le plugin lâche dès la prise en charge, le jeu met frein 0 / adhérence 1) | l'avion bondit ou glisse ; « remonte », partie jetable | 🟡 |
| Le premier segment (≈ 30 m en ligne droite vers l'ascenseur) | obstacle sur le pont (rien vu dans les données) | 🟢-🟡 |
| L'ascenseur occupé | l'avion attend en bout de chemin, comme pour l'IA | 🟢 |
| La prise en charge ne se défait pas (comme pour l'IA) | piste occupée jusqu'à la fin du cycle normal | 🟡 |

## Couper vite
1. **Remonter dans l'avion** avant la prise en charge : le plugin lâche tout (mode pilote).
2. `recall_force=0` dans `frein.ini` : H5 et H1/H2 cessent d'agir en ≤ 3 s (les crochets restent posés mais inertes).
3. Fermer le jeu ; la partie est jetable.
4. Retour à la v10 : jeu fermé, copier `cc2-sdk-travail\dist_v10\cc2x_frein.dll` sur la DLL du jeu ; remettre `frein.ini.avant_v12`.

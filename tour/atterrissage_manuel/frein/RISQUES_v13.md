# Notice des risques : `cc2x_frein.dll` v13 (31/10/2026)

**Empreinte** : `22D04FE3F28D087403534732217779EE315A36EF33A547CD9F47253D03349113` (247 808 octets), dans `C:\Users\UTILISATEUR\Documents\cc2-sdk-travail-v13\dist\` (compilée **à part** pour ne pas écraser la v12 ni le SDK de retour arrière de `cc2-sdk-travail\dist\`). **POSÉE le 31/10** (accord du moddeur : « Oui, pose la v13 ») ; `frein.ini` inchangé (sans `heli_recall` : comportement v12). Ancienne : la v12 (`941DFFB9…`, copie dans `cc2-sdk-travail\dist_v12\`). Étude : `../ETUDE_v13_helicos.md`.

## En une phrase par cas

| Réglage de `frein.ini` au lancement | Ce que fait la v13 | Risque |
|---|---|---|
| tel qu'aujourd'hui (`recall_force=1`, **sans** `heli_recall`) | **exactement la v12** : mêmes 9 crochets, mêmes octets, aucun hélico regardé | 🟢 (= v12, 3 prises en charge sur 3 + Manta) |
| `recall_force=1` **et** `heli_recall=1` | 10e crochet **H6** posé, inerte tant qu'aucun hélico rappelé n'est posé sur le pont | 🟢 |
| idem, et on **rappelle un hélico posé, immobile, pilote parti** | H6 fait sauter au jeu son test « à moins de 100 m du point d'attente » : le jeu donne la piste tout de suite, puis fait **son** toucher et **sa** prise en charge (comme pour chaque hélico qu'il pose) | 🟡 |

## Ce qui change par rapport à la v12 (posée)
1. **H6** (`0x6fdcdd` ancien exe, `0x6fdded` nouvel exe ; 8 octets `mulss xmm2,xmm2 ; mulss xmm3,xmm3`) : pour l'hélico signalé seulement, continue au don de la piste (`0x6fdcf2` / `0x6fde02`) au lieu de la comparaison. **Rien n'est écrit dans la mémoire du jeu**, aucun registre changé. Un seul don par fenêtre (compté dans le crochet). Refuse s'il n'y a aucune baie libre de classe 1, si le navire n'est pas en mode accostage ou si la piste n'est pas libre.
2. **Signalement d'un hélico** : rappelé (`DOCK_STATE = 5`) alors que toutes ses roues touchent, < 1 m/s par rapport au navire, pilote parti, pas accroché. Une fenêtre de 10 s par rappel. Un seul appareil à la fois (un avion en cours fait attendre l'hélico, et l'inverse).
3. **Aucun frein ni moteur écrit pour un hélico** (contrôlé par le test et par une panne injectée).
4. Journal : lignes `heli N …` (position sur le pont), `HELI window open`, `HOOK H6 …`, `HELI balance`, `HELI VERDICT`, puis `TAKEN OVER` / `HANGAR` / `REFUEL` comme pour les avions.
5. Version annoncée dans le journal : `loaded (frein v13, …)` (les outils de lancement de `tour/essai_nouvel_exe/outils/` de cette worktree l'attendent).

## Ce qui est prouvé (hors jeu)
- **Sites** (`../outils/verifier_sites_v13.py` → `VERIF_sites_v13.txt`) : dans les deux exe, les **10 sites** ont les octets attendus, aucune relocation, aucun saut de tout le programme vers l'intérieur ; entre H6 et sa cible, seulement 4 calculs SSE sur des registres et le saut conditionnel (aucun accès mémoire, aucun `push`, aucun appel) ; **xmm2 et xmm3** (les seuls changés entre les deux) **ne sont pas vivants** à la cible ; `[ebp-0x270]` (l'hélico) et `[ebp-0x278]` (sa place dans la file) écrits par le jeu juste avant ; 14 faits du chemin des hélicos relus dans les deux exe (−100, −240, 10000, 20 m, 30 m, 10 m/s, les tests `vtable+0x4c`, la boucle de la file qui saute H1). Les mêmes octets sont présents dans les copies patchées `8E7FCBB6`, `5AF41B4D` et `2C9F8E47` (approche ×2).
- **Test hôte** (`tests/test_frein.c`, UBSan, `-Werror`) : **397 contrôles, 0 échec** (les 334 de la v12 inchangés + T33 : 63 contrôles hélicos).
- **18 pannes injectées** dans une copie du plugin (H6 sans budget, mauvaise cible, sans contrôle du véhicule, qui écrit en mémoire, sans contrôle des baies, sans contrôle du cadre, sans contrôle du mode / de la piste libre, qui change `esi`, site du nouvel exe faux, posé sans `heli_recall`, hélico freiné, fenêtre sans contrôle des roues, avec le pilote à bord, qui prend la place d'un avion, fermeture qui garde l'hélico signalé, pas de fin sur abandon, hélicos regardés sans `heli_recall`, H6 sans enveloppeur xmm) : **18 sur 18 font échouer le test**.
- **Compilation** : 2 compilations identiques hors horodatage ; **imports, exports, sections, TLS identiques à la v12** (comparaison par script) ; aucune chaîne suspecte ; 7 enveloppeurs xmm (un par corps de crochet).
- **Outils** (`tour/essai_nouvel_exe/outils/`, épinglés sur la v13, la v12 devient « précédente ») : `tester_poser` 36/0, `tester_lancer` 32/0, `tester_poser_sdk` 33/0, `tester_lancer_nouveau` 52/0, `tester_lancer_nouveau_helicos` 16/0 ; `poser.py maj --cest-le-vrai-jeu --a-blanc` sur le vrai dossier : le SDK à deux profils `E1DE25D5…` est accepté, « remplacer cc2x_frein.dll (notre version précédente) par la nouvelle », **rien écrit**.

## Ce qui n'est PAS prouvé (seul un essai le dira)
| Inconnu | Si ça tourne mal | Gravité |
|---|---|---|
| L'hélico reste-t-il posé quand le pilote le quitte (avant le rappel) ? | il décolle seul : la v13 ne le prend pas (pas « posé »), le jeu fait son retour normal | 🟢 |
| Le toucher passe pour un hélico posé à la main (2e champ des roues) | `HELI VERDICT: runway given, no take-over…` : l'hélico, qui a la piste, fait l'approche courte du jeu et se repose (fin normale de l'IA) | 🟢 |
| Le saut H6 en vrai (jamais exécuté) | plantage du jeu (partie jetable) | 🟡 |
| Le recul vers l'ascenseur depuis l'endroit où il est posé (ligne droite) | s'il est loin de l'axe ou près de l'îlot, il peut accrocher quelque chose en étant tiré ; « remonte », partie jetable | 🟡 |
| Un autre hélico devant lui dans la file | `SILENT` : rien de forcé, retour normal | 🟢 |
| La prise en charge ne se défait pas (comme pour l'IA) | piste occupée jusqu'à la fin du cycle normal | 🟡 |

## Couper vite
1. **Remonter dans l'hélico** avant la prise en charge : la fenêtre se ferme (`pilot back`).
2. `heli_recall=0` (ou `recall_force=0`) dans `frein.ini` : H6 cesse d'agir en ≤ 3 s (le crochet reste posé mais inerte).
3. Fermer le jeu ; la partie est jetable.
4. Retour à la v12 : jeu fermé, copier `C:\Users\UTILISATEUR\Documents\cc2-sdk-travail\dist_v12\cc2x_frein.dll` (`941DFFB9…`) sur la DLL du jeu ; enlever la ligne `heli_recall=1`.

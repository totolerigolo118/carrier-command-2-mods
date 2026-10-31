> ## ⛔ NE PAS UTILISER avant décision du moddeur (encadré ajouté le 30/10 sur demande de la coordination ; le reste de ce fichier est inchangé et **partiellement périmé**)
> Ne pas poser la v11, ne pas faire cet essai. Lecture indépendante re-vérifiée dans l'exe (`tour/etude_atterrissage_apres_engagement/RAPPORT.md`, worktree `atterrissage-apres-engagement-521262`) :
> 1. **La v11 échouerait très probablement aux portes B (pente verticale, `0x6fe6ab`) ou C (vitesse relative nulle → 0/0, `0x6fe721`-`0x6fe77b`), comme la v10.**
> 2. **Les critères fondés sur `attached_to` ci-dessous sont faux** : le jeu écrit `ATTACHED_TO` dès l'engagement (`0x6fe823`) ; **succès = `dock=6` et `flight=1` et état de piste 5** ; « ne pas alerter si `attached_to` ≠ 0 » et l'alerte (e) « sans `attached_to` » seraient aveugles ; le plugin lâche frein et maintien dès que `attached ≠ 0`.
> 3. **Le vrai danger est le cas rare où l'engagement passe** : état de piste 4 permanent (rien ne libère piste et baie 8 ; seule sortie : fermer le jeu), et rappel de baie dans le même tick (`0x6ff374`-`0x6ff388`, `[g+0x6c]` écrasé avant le contrôle). Détail : `frein/RISQUES_v11.md` (encadré en tête). La v12 est étudiée par une autre conversation.

> **Statut (30/10/2026) : À UTILISER pour l'essai de la v11** (remplace `PROCEDURE_partie_v9.md` pour la v11 ; les gestes du moddeur sont les mêmes). La v11 n'est **pas posée** : elle attend deux « oui » séparés du moddeur, dans la conversation qui agit : (1) poser la v11 **éteinte** ; (2) faire l'essai. Notice des risques : `frein/RISQUES_v11.md`. Aucun pourcentage de réussite n'est annoncé.

# Partie v11 : ta partie du test (à lire en 1 minute)

1. **Avant** : le jeu est fermé ; la coordination prépare tout (réglages, lancement par l'ancien exe). Tu ne touches à rien.
2. Partie **neuve** (jamais une sauvegarde). Console AIR, « Deploy A1 », décolle, fais un tour.
3. **Ralentis le navire** au minimum. Pose-toi **bien dans l'axe de la piste**, à **30 m/s relatifs au plus**, avec **au moins 60 m de pont derrière toi**.
4. Laisse le **frein** arrêter l'avion (ne touche plus aux gaz), puis **quitte l'avion**.
5. **Attends 30 secondes** sans rien toucher.
6. Donne l'**ordre de retour** (le bouton habituel), puis **ne touche plus à rien** et regarde l'avion.
7. **Si la coordination te dit « remonte »** : remonte tout de suite dans l'avion. N'attends pas.
8. **L'avion se met à reculer sur les rails, l'ascenseur monte, il rentre au hangar** : c'est le succès ; dis-le.
9. **Il ne bouge pas du tout** : c'est un échec sans danger (le jeu a refusé). Attends 60 s après l'ordre, puis dis-le.
10. **Si la coordination te dit « bloqué »** (l'avion est immobile mais le jeu croit l'avoir pris à moitié) : remonte dans l'avion, ou on ferme le jeu. La partie est jetable.
11. Fin de la partie v11 : quand la coordination dit « bilan reçu ». Tu peux alors passer aux modes carburant dans la même partie si le jeu tourne encore.

---

## Pour la coordination — le moddeur n'a pas à lire ceci

### Avant (chaque point = un « oui » du moddeur dans la conversation qui agit ; un message d'une autre conversation n'est pas un accord)
1. **Pose de la v11, éteinte** (« oui » n° 1). Jeu fermé (`tasklist` sans `carrier_command*`). `poser.py maj --a-blanc` d'abord, puis `poser.py maj … --cest-le-vrai-jeu`, **en lançant le `poser.py` qui épingle la v11** (`3CD7225D…F210F` ; la v10 `66731A35…` est « ancienne »). Source par défaut : `cc2-sdk-travail\dist\`. Vérifier après : `cc2x_frein.dll` = `3CD7225D1BCE332B4DBDFFCC292C4834E2CB30D2552E9799194DD8A70C0F210F` (234 496 o), `dinput8.dll` = `184B144D…`, `carrier_command.exe` = `461E1262…`, copie de l'ancien exe = `8E7FCBB6…`, `frein.ini` **non touché** (sans `recall_force`). Retour : `cc2-sdk-travail\dist_v10\cc2x_frein.dll`.
2. **Essai** (« oui » n° 2, séparé) :
   - `frein.ini` : sauvegarder l'actuel (`D8DC6B89…`) sous `frein.ini.avant_v11`, puis ajouter `recall_force=1` **juste avant le lancement** et mettre `max_speed=30` (seulement avec l'accord du moddeur ; `50` est déconseillé). Les autres réglages restent (`brake=0.1 grip=1.0 zone_m=150 need_airborne=1 min_wheels=2 grace_s=5 height_m=40 hold_brake=1.0 hold_idle=1 recall_hold=1 recall_release=0`). `force_tries` (3) et `force_timeout_s` (20) : défauts.
   - Armer le copieur passif du journal (`garder_journal.py`, dans le dossier temporaire de la session) : `cc2x.log` est recréé à chaque lancement.
   - Lancer : `python -I tour/atterrissage_manuel/frein/lancer_ancien.py lancer --jeu "C:\Program Files (x86)\Steam\steamapps\common\Carrier Command 2" --cest-le-vrai-jeu` (jamais par Steam ; `Get-Process carrier_command*` doit être vide avant). Partie NEUVE.
   - Au démarrage, lire dans `cc2x.log` : `CC2X 0.5.0 ready …`, `loaded (frein v11)`, **`recall_force=1: hooks H1 (0x7018ce), H2 (0x701a3d), H3 (0x6ff0fb, read only), 4 commit-gate probes (read only) and H4 (0x6fe470, forces the commit evaluation) installed`**, puis `settings: … recall_force=1 … hooks=1`. Si on lit `could NOT be installed` : **arrêt**, les octets du jeu ne sont pas ceux qu'on a lus (le plugin ne pose alors aucun crochet).
3. **Après** : jeu fermé, remettre `frein.ini` à l'état d'avant (sans `recall_force`), copier le journal dans `logs_parties\`, et **ne pas enchaîner un autre forçage** sans l'accord du moddeur.

### Lignes à chercher dans `cc2x.log` après l'ordre de retour (1 relevé par seconde)
| Ligne | Sens | Action |
|---|---|---|
| `RECALL start (dock 5, mode …)` puis `FORCE start (…): hooks H1/H2/H4 armed … the only window of this recall` (1 s plus tard) | la fenêtre s'ouvre, **une seule** pour ce rappel | rien |
| `HOOK H1 shown circuit state 1 (real element state 0, manager mode 1, runway slot -1)` ; `HOOK H2 skipped the 1000 m test … (try 1 of 3)` ; `dock=1` | le jeu donne la piste (comme en v10) | rien |
| **`HOOK H4 forced the commit evaluation (1 so far): … m from the runway middle … runway state 3 … -> continued at 0x6fe55b`** | **le jeu évalue enfin les portes A à E pour l'avion posé** (nouveau) | rien |
| `PROBE gate A/B|C/D|E … failed` | la porte qui bloque (même lecture que `LECTURE_SONDES_v10.md` §3) | noter |
| `HOOK H3 the game ABORTS the approach … bay=… fail=1 zone=1 … causes: …` | le jeu abandonne : `power=1.00` lu **une fois**, puis retour à 0 | rien si une seule fois |
| `RUNWAY state 3|4|5 (…), owner slot …, approach counter …` ; `COMMIT: the game's runway state is 4 …` | **l'engagement est passé** (état de piste 4) | attendre le tick suivant |
| `dock=6` et/ou `attached_to` ≠ 0, `flight=1`, `RECALL ended … (dock 6, attached N …)` | **la prise en charge a lieu** : `rel` peut monter (recul sur les rails) | **ne PAS alerter** ; l'avion quitte la zone vers l'ascenseur, `dock=4`, carburant qui monte = le succès complet |
| `FORCE window closed for good (aircraft not parked any more …)` | l'avion a bougé ou perdu le contact pendant qu'il était en file : la fenêtre est fermée pour ce rappel | l'avion reste tenu ; fin de l'essai |
| `FORCE timeout after 20 s` / `FORCE gave up after N tries` | fenêtre terminée | l'avion reste tenu |
| `FORCE balance (…): GRANTS n, ABANDONS m, GATES AB a CD c (C passed p) E e, H4 forced h (reached r)` | le bilan | noter |
| **`VERDICT: …`** | la conclusion écrite par le plugin (voir ci-dessous) | la lire au moddeur en français |

### Les verdicts (et ce qu'ils veulent dire)
- `the runway was never given (H1/H2 did not fire)` : rien n'a été forcé (le rappel n'a pas atteint le bloc de don de la piste).
- **`SILENT - H4 never ran, the game never came to 0x6fe470 for this aircraft (although it aborted the approach …)`** : c'est la situation de la v10 (le jeu abandonne, rien de ce qu'on a posé ne voit passer l'avion). Le site n'a pas été atteint pour l'avion signalé : lire le `HOOK H3` (`zone=…`, `z=…`).
- `H4 reached its site N time(s) but did not act: …` : le crochet est passé mais a refusé (raison écrite : `edi` différent de l'avion, gestionnaire illisible, état de piste ≠ 3, budget épuisé).
- `the commit evaluation ran and a gate FAILED: A/B | C | D | E` : l'évaluation a eu lieu et **telle porte** a échoué (c'est la réponse que la v10 cherchait). Lire les lignes `PROBE`.
- **`SILENT PROBES - H4 ran, no commit gate probe fired, yet the game aborted the approach: not a gate, read the H3 line`** : H4 a tourné, aucune sonde n'a tiré et le jeu abandonne quand même : la cause n'est pas une porte ; lire `HOOK H3` (`no-free-bay`, `target-passed`, `counter>3600`).
- `H4 ran, no gate failed, no abort: the commit went through (runway state now N, owner slot X)` : l'engagement est passé ; la suite (test de toucher, prise en charge) se lit dans `dock` / `attached_to`.

### Alertes « REMONTE » (pour l'avion signalé, `attached_to=0`)
(a) `rel` > 1,5 m/s sur deux relevés consécutifs et qui monte ; (b) `power`/`power_read` = 1.00 sur plus de 2 relevés avec `brk=1` ; (c) `wheels` < 3/3 avec `rel` > 1 ; (d) `HOOK H2 … (try k of 3)` avec k ≥ 3, ou plus de 3 `HOOK H4 forced`, ou un `HOOK H4 forced` sans `FORCE start` avant ; (e) `dock=1` sans `attached_to` pendant plus de 3 s après `HOOK H2`, ou `RUNWAY state 4` sans prise en charge pendant plus de 10 s après `COMMIT:` (dire « bloqué ») ; (f) `rel` > 0,5 m/s juste après `COMMIT:`. **Dire « remonte » au premier cas, pas au deuxième** (le 30/10, entre le premier `rel` à 2,3 m/s et le décollage : ~4 s). Ne pas alerter si `attached_to` ≠ 0 ou `dock=6`. Détail et retour arrière : `frein/RISQUES_v11.md`.

### Normal avec la v11 (pas d'alerte)
Une seule donation, `power_read=1.00` une fois (si le jeu abandonne), puis `rel` < 0,5 ; ou : H4, `COMMIT:`, `dock=6`/`attached_to` ≠ 0 et un recul régulier sur les rails.

> **Statut (31/10/2026) : À UTILISER pour l'essai de la v12** (remplace `PROCEDURE_partie_v11.md`, qui ne doit pas servir). La v12 est écrite et testée hors jeu, **pas encore posée**. Notice des risques : `frein/RISQUES_v12.md`. Pourquoi la v12 : `PISTE_v12_comme_un_helico.md`.

# Essai v12 : ta partie (2 minutes de lecture)

**Ce qu'on essaie** : tu poses l'avion à la main, le frein l'arrête, tu le quittes, tu donnes l'ordre de retour, et **le jeu le reprend comme il reprend un hélicoptère posé** : il le tire doucement vers l'ascenseur, le descend au hangar et le ravitaille.

**Avant de jouer** (rien à faire de ta part, sauf dire « oui ») :
1. Je pose la v12 dans le dossier du jeu, jeu fermé (ton « oui »).
2. Je prépare `frein.ini` pour l'essai : `recall_force=1` et `max_speed=35` (ton « oui », même message possible). Je garde une copie de l'ancien `frein.ini`.
3. Je lance une copie passive du journal (elle ne fait que lire).
4. Le jeu se lance avec **l'ancien exe** (pas le bouton Jouer de Steam). Soit tu me dis « oui, lance » et je le lance, soit tu tapes toi-même :

```bash
python -I "C:\Users\UTILISATEUR\Documents\cc2-patchs\.claude\worktrees\[dossier-de-travail]\tour\atterrissage_manuel\frein\lancer_ancien.py" lancer --jeu "C:\Program Files (x86)\Steam\steamapps\common\Carrier Command 2" --cest-le-vrai-jeu
```

(Le `lancer_ancien.py` de CETTE worktree : il connaît l'empreinte de la v12. Celui du dossier principal refuserait la v12 tant qu'elle n'est pas fusionnée.)

**Dans le jeu :**
1. **Partie neuve** (jamais une sauvegarde : le chargement plante). Steam doit être ouvert.
2. Console AIR, sors un avion (Albatross ou autre avion à ailes), décolle, fais un tour.
3. **Ralentis le navire** au minimum.
4. Pose-toi **dans l'axe de la piste**, **30 m/s relatifs au plus** si tu peux (le frein n'agit pas au-dessus de 35), avec le plus de pont possible devant toi.
5. Laisse le **frein** arrêter l'avion. Ne touche plus aux gaz. Puis **quitte l'avion**.
6. **Pas besoin d'attendre** (31/10, après les essais) : dès que l'avion est arrêté et que tu l'as quitté, le plugin le tient ; il ouvre sa fenêtre 1 s après l'ordre de retour. Garde le **navire lent** jusqu'au hangar : à 42 m/s le vent soulève l'avion arrêté et le frein ne le tient plus (avion 10 perdu le 31/10).
7. Donne l'**ordre de retour** (le bouton habituel), puis **ne touche plus à rien** et regarde l'avion pendant 1 minute.

**Ce que tu peux voir :**
- ✅ **Succès** : l'avion **recule ou glisse doucement** (≈ 2,5 m/s) sur une trentaine de mètres vers l'ascenseur, l'ascenseur le descend, il rentre au hangar. Dis-le-moi. Attends encore 20 s (je vérifie que le carburant monte).
- ⚪ **Rien ne bouge** au bout d'une minute : le jeu a refusé, **sans danger**. L'avion reste tenu au frein. Dis-le-moi : le journal dira pourquoi (souvent une valeur des roues), et on corrige.
- ⚠️ **Si je te dis « remonte »** : remonte **tout de suite** dans l'avion (le plugin rend alors la main). N'attends pas.
- ⚠️ **Il bondit, part vite ou sort du pont** : remonte dedans. La partie est jetable.

**À la fin** : dis « **fini** ». Je ferme le jeu moi-même, je remets `frein.ini` comme avant, je copie le journal et je te dis en français ce qui s'est passé.

---

## Pour moi (ou la coordination) : le moddeur n'a pas à lire ceci

### Avant (chaque point = un « oui » du moddeur dans CETTE conversation)
1. **Pose de la v12 éteinte.** Jeu fermé (`Get-Process carrier_command*` vide). `poser.py maj … --cest-le-vrai-jeu --a-blanc` puis sans `--a-blanc`. Vérifier après : `cc2x_frein.dll` = `941DFFB9F1671CB351A69B826B14E62AB9978390C888257DA699E8584ADC59B3` (240 640 o), `dinput8.dll` = `184B144D…`, `carrier_command.exe` = `461E1262…`, `carrier_command_ancien_8E7FCBB6.exe` = `8E7FCBB6…`, `frein.ini` non touché par la pose. Retour : copier `C:\Users\UTILISATEUR\Documents\cc2-sdk-travail\dist_v10\cc2x_frein.dll` (v10, `66731A35…`) sur la DLL du jeu, jeu fermé.
2. **`frein.ini` pour l'essai** : copie `frein.ini.avant_v12` (sha relu), puis `max_speed=35` (au lieu de 50) et une ligne `recall_force=1` **juste avant le lancement**. Le reste inchangé (`brake=0.1 grip=1.0 zone_m=150 need_airborne=1 min_wheels=2 grace_s=5 height_m=40 hold_brake=1.0 hold_idle=1 recall_hold=1 recall_release=0`, `flight_state=-1`, `brake_enabled=1`).
3. Copieur passif du journal (scratchpad de la session) : copie `cc2x.log` toutes les 20 s et à la fermeture vers `C:\Users\UTILISATEUR\Documents\cc2-sdk-travail\logs_parties\cc2x_<date>_frein_v12.log`.
4. Lancement : `lancer_ancien.py lancer` (jamais Steam). Un seul jeu à la fois.

### Au démarrage, `cc2x.log` doit montrer
- `CC2X 0.5.0 ready for Carrier Command 2 1.5.18-win32`
- `loaded (frein v12, build 1.5.18-win32, exe 0x6a36c177)`
- `recall_force=1: hooks H1 (0x7018ce), H2 (0x701a3d), H3 (0x6ff0fb, read only), 4 commit-gate probes (read only), H5 (0x6fe470, sends the aircraft to the touch test 0x6ff20a) and the take-over probe (0x6ff379, read only) installed`
- `settings: … max_speed=35 … recall_force=1 … hooks=1`

`could NOT be installed` ou `not loaded: the SDK says build …` = **arrêt** (rien n'est posé dans le jeu dans ce cas ; le plugin se comporte comme la v7 ou ne se charge pas).

### Lignes attendues après l'ordre de retour
| Ligne | Sens |
|---|---|
| `RECALL start (dock 5, …)` puis `FORCE start (…): hooks H1/H2/H5 armed …` | la fenêtre (unique) s'ouvre 1 s après le rappel |
| `HOOK H1 shown circuit state 1 …` ; `HOOK H2 skipped the 1000 m test … (try 1 of 3); dock=1` | le jeu donne la piste (MESURÉ v8-v10) |
| **`HOOK H5 sent the aircraft to the game's touch test (1 so far): … rel … wheels 3: field +0 = … field +4 = … preferred bay … free bays … lift owner …`** | nouveau : l'avion est envoyé au test de toucher ; **noter les deux champs des roues** |
| **`PROBE take-over block entered: the touch test PASSED, the game got bay N (limit M)`** | le test de toucher est passé, le jeu exécute sa prise en charge |
| `VERDICT: the touch test PASSED and the game ran its take-over block (bay N) …` | idem, écrit au moment où le plugin lâche l'avion |
| **`TAKEN OVER: dock 6, flight 1, runway state 5 - the game pushes the aircraft back to the lift`** | **succès de la prise en charge** |
| `FOLLOW +…s: dock=6 flight=1 attached=1 runway_state=5|6|7 fuel=…` | recul, attente/ascenseur, descente |
| **`HANGAR: dock 4 (stowed) …`** puis **`REFUEL check: … (it goes up: refuelling)`** | **le vrai but : rangé et ravitaillé** |

### Échecs possibles (tous lus dans `VERDICT:`)
- `TOUCH TEST NEVER PASSED - H5 sent the aircraft to it N time(s); last values: … field +4 = …` : le test du jeu refuse ; les valeurs disent pourquoi (vitesse > 10, une roue < 0,01, ou un 2e champ > 0,1). Sans danger : après 30 essais (≈ 1 s) le jeu abandonne proprement (`HOOK H3 … ABORTS`, `power=1.00` lu une fois), l'avion reste tenu.
- `the touch test PASSED but the game found no bay …` : pas de baie ; le jeu saute sa prise en charge, l'état de piste reste 3, il abandonne ensuite.
- `H5 reached its site N time(s) but did not act: …` : la raison est écrite (état de piste, propriétaire de la piste, pas de baie libre de la bonne classe, vitesse > 2 m/s…).
- `SILENT - H5 never ran …` : comme la v10 ; lire `HOOK H3`.
- `AFTER THE TAKE-OVER BLOCK: not the expected dock 6 / flight 1 / runway state 5 (…)` : le jeu a fait autre chose ; lire les `FOLLOW`.
- `UNEXPECTED: the game's runway state is 4 (committed)` : ne doit jamais arriver avec H5 ; si oui : **« remonte »**, puis fermer la partie (piste bloquée).
- `FOLLOW stopped after 300 s without dock 4 (…)` : l'avion attend (ascenseur occupé ?) ou s'est bloqué ; regarder l'écran.

### Alertes « REMONTE » (avant la prise en charge, `dock` 5 ou 1)
(a) `rel` > 1,5 m/s sur deux relevés qui montent ; (b) `power_read=1.00` plus de 2 relevés de suite avec `brk=1` ; (c) roues < 3/3 avec `rel` > 1 ; (d) `HOOK H2 … try k` avec k ≥ 3 ; (e) `UNEXPECTED: … runway state is 4`. Dire « remonte » au premier cas. **Après `TAKEN OVER`, un `rel` jusqu'à ~2,5 m/s est NORMAL** (l'avion est tiré par le jeu) : ne pas alerter.

### Après (« fini »)
Fermer le jeu (accord permanent du moddeur pour la fermeture après « fini »), vérifier la copie du journal, remettre `frein.ini.avant_v12` (sha relu), lire les lignes ci-dessus, écrire le résultat dans `JOURNAL_atterrissage.md`.

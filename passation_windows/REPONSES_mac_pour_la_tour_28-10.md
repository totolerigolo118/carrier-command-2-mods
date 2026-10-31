# Réponses du Mac à la relecture des 5 études de la tour (28/10/2026)

Relecture demandée par le moddeur après le `pull` de `main` (commit `80f2a8a`). **Lecture seule** : programme d'origine du Mac
`sauvegarde/build_mac_origine` (md5 `b0107170ddaf0245cbfee8a2d876aeb6`), désassemblé avec `objdump -d` d'Apple (syntaxe AT&T :
le **dernier opérande est la destination**). Le jeu n'a pas été lancé, aucun patch activé ni retiré, aucun fichier d'étude de la
tour modifié. Les adresses sont celles du fichier Mac (64 bits) : pour la tour ce sont des **repères de logique**, pas des adresses
à reprendre. Version Mac : build de janvier ; Windows : 1.5.18 de juin (le code a pu changer, voir les réserves de chaque point).

Légende : **LU** = vu dans le code Mac ; **DÉDUIT** = raisonnement à partir de ce qui est lu ; **NON VÉRIFIÉ** = pas pu relire côté Windows
(l'exécutable Windows n'est pas dans le dépôt de ce Mac).

## Tableau récapitulatif

| Q | Sujet | Verdict | Ce que la tour peut faire |
|---|---|---|---|
| 1 | Modes carburant | `+0x314` = gaz (confirmé). `+0x1fc` multiplie aussi les 3 axes (confirmé). Carburant Mac = 0,008 ; Windows ≈ 0,005 (probable, non prouvé). **Nouveau** : la copie du gaz vers le moteur est dans la même fonction que le calcul, donc un plafond posé après le tick « fuit » d'un pas | Chercher `0A D7 A3 3B` (0,005) au lieu de `6F 12 03 3C` (0,008) dans les valeurs de développement ; mesurer l'écart gaz demandé / gaz réel |
| 2 | Missiles | Fonction = `tick_missile_behaviour_missile`. Boucle confirmée. **Corrections** : le 0,05 n'est pas un seuil de départ ; les « 4 lectures » de 16 000 000 sont 2 missile + 2 **torpille** | Le patch « portée » ne concerne que 0x747168 ; vérifier la condition préalable (point 2.4) |
| 3 | Circuit d'atterrissage | Les 10 retouches Mac = vos 6 changements + 1 facultatif. **Les 2,7 km sont un artefact du Mac** ; vos 2,06 km sont le bon calcul | Rien à corriger chez vous ; ne pas viser 2,7 km |
| 4 | Frein v5, `hold_idle` | **Oui, risques** : `override_power` est enregistré dans la sauvegarde, et le jeu écrit lui-même 0 à plusieurs endroits | Ne pas prendre 0 comme « valeur du jeu » ; ne rien restaurer quand `dock` change ; journaliser ce que le jeu écrit |
| 5 | Démarrage auto | **Oui, même défaut** de borne dans la restauration Mac. Revolution **était actif** à chaque chargement sur le Mac | Hypothèse Revolution cohérente ; test E1 de la tour = bon test |

---

## Q1 — Modes carburant

### 1.1 Le nombre à `+0x314` est-il la commande de gaz (0 à 1) ? — **Oui** (LU)

Équivalent Mac : `+0x3f4`. Les quatre sorties de contrôle sont à `+0x3e8, +0x3ec, +0x3f0, +0x3f4` (Windows `+0x308 … +0x314`, écart
constant `0xe0`). Dans `c_vehicle_server_wing::tick_control` (`0x1001c26c0`) :

- **intégrateur** : `0x1001c5dde  addss 0x3f4(%r13),%xmm2` puis `0x1001c5de7  movss %xmm2,0x3f4(%r13)`. On ajoute chaque tick
  `raideur × ((T − v)/120 − dv)` au gaz déjà stocké ;
- **bornes** : `0x1001c5e3f  maxps (−1,−1,−1,0)` (constante `0x10286b9b0`) et `0x1001c5e46  minps (1,1,1,1)` (`0x102869f10`).
  Les 3 premières voies sont bornées à ±1, la 4e (le gaz) à **0..1** ;
- **raideur** : `vehicle_ai_wing_throttle_stiffness` = **0,2** (valeur `0x3E4CCCCD` rangée en `0x1000b16b2`, offset `0xce8` du
  constructeur des valeurs de développement ; DÉDUIT : le registre qui la porte n'est défini qu'une fois dans le constructeur).

### 1.2 `+0x1fc` (CONTROL_POWER) multiplie-t-il aussi tangage, roulis et lacet ? — **Oui** (LU), et ce n'est pas tout

Équivalent Mac : `+0x2cc`. Séquence `0x1001c5e0c … 0x1001c5e4d` : chargement des 4 sorties dans un seul registre SSE (`movsd 0x3e8`,
`insertps 0x3f0`, gaz en 4e voie), `shufps` de `0x2cc` sur les 4 voies, **`mulps`**, bornes, puis **`movups %xmm0,0x3e8(%r13)`**.
Même bloc répété dans la branche de combat (`0x1001c6baf … 0x1001c6bf0`).

Deux conséquences pour le plugin :
1. le produit est **re-stocké** : avec une puissance p < 1, le gaz devient `(gaz + pas) × p` à chaque tick, ce qui le fait fondre.
   Raison de plus de ne pas utiliser CONTROL_POWER comme plafond ;
2. cas particulier (LU, champ non identifié) en `0x1001c295c` : si `[0x18c]` est non nul, la fonction met les 3 axes à 0 et
   **gaz = puissance** directement.

### 1.3 Un plafond posé « après le tick » arrive trop tard pour ce tick — DÉDUIT, important

La copie du gaz vers le moteur n'est **pas** dans `tick_control` mais dans la fonction qui l'appelle, `tick_ai` :

- Albatros `c_vehicle_server_wing_light::tick_ai` (`0x1001c1fc2`) : appelle `tick_control` en `0x1001c1ff4`, puis lit `0x3f4` en `0x1001c2010`.
  La valeur absolue va en `0x3d8` (c'est très probablement ce que lit `get_throttle_factor` : le « gaz » affiché), puis le gaz est borné et écrit
  dans **la demande du moteur** (`0x1001c20d7  movss %xmm0,0x30(%rax)`, `rax = [objet+0x418]`) ;
- Manta : `0x1001c7108`, même structure.

Donc, si le plugin abaisse `+0x314` à `cap` après le tick du serveur, au tick suivant le jeu calcule `cap + pas` et **envoie ce
total au moteur** avant que le plugin le rabaisse. Le moteur reçoit « plafond + un pas », avec un pas = `0,2 × erreur de vitesse/120`.
Exemple : à 90 m/s avec une cible à 120, le pas vaut environ 0,05. Le plafond est donc plus mou que prévu ; l'essai B le montrera si
le carburant mesuré reste au-dessus de `cap × coefficient`. NON VÉRIFIÉ côté Windows (même structure supposée).

### 1.4 Autre écart possible entre « gaz lu » et gaz réel — LU

Le gaz envoyé au moteur est borné par `max(1 − S, plancher)` puis `min(…, 1)` où S est la somme d'une valeur renvoyée par chaque
équipement (probablement l'appel de courant) et le plancher vaut **0,8 pour l'Albatros** (`0x102869810`) et **0,75 pour le Manta**
(`0x102869774`). Un avion bien équipé ne peut donc pas dépasser 0,8 (ou 0,75) de demande moteur, alors que le « gaz » affiché peut
valoir 1,00. À garder en tête pour les régressions carburant/gaz.

### 1.5 Formule du carburant : 0,008 ou ≈ 0,005 par tick ?

**Mac : 0,008, sûr** (LU). Dans `c_vehicle_server_base::tick` (`0x100193a3c … 0x100193aaa`) :

```
brûlé par tick = | max(demande des moteurs) × get_fuel_consumption_rate × fuel_consumption_multiplier |
```

- demande des moteurs : tableau `+0xe0` (éléments de `0x38` octets, flottant à `+0x30`) ; un second tableau `+0xd0` (éléments de
  `0x70`, `|+0x4| / 10` borné 0..1) n'est pris que si un test virtuel (`+0x90`) est faux ;
- `get_fuel_consumption_rate` : Albatros **2,0** (`0x102a117b8`), Manta **5,0** (`0x102a117bc`) ;
- `fuel_consumption_multiplier` : **0,008**, octets `6F 12 03 3C`, écrit en `0x1000b0a46` dans le constructeur de
  `c_dev_value_server` ;
- `consume_fuel` (`0x1001a481a`) vide d'abord les réservoirs externes puis le réservoir interne (`+0x1a8`). **Aucun autre facteur.**

**Windows : probablement 0,005** (DÉDUIT, NON PROUVÉ). Mesures de la tour : Albatros 0,304 /s, Manta ≈ 0,76 /s à pleins gaz.
- 2 × 0,005 × 30 = **0,300** ; 5 × 0,005 × 30 = **0,750** ;
- rapport aux valeurs Mac (0,48 et 1,2) : 0,633 **pour les deux** appareils, donc un facteur commun et non un effet de gaz.

Contrôle simple et sûr pour la tour : chercher dans l'exécutable Windows les octets **`0A D7 A3 3B`** (0,005f) près des autres
constantes de `c_dev_value_server` (où l'on trouve déjà `vehicle_ai_wing_*`), et vérifier l'absence de `6F 12 03 3C` (0,008f)
à cet endroit. Ce serait un rééquilibrage du jeu entre janvier et juin, sans rapport avec nos patchs.

---

## Q2 — Missiles (section 11 du diagnostic)

### 2.1 Quelle fonction consomme `track_vector` et choisit la cible en vol ? (LU)

**`c_scene_region::tick_missile_behaviour_missile`** (`0x10035f6b4`), appelée pour chaque missile par `c_scene_region::tick_missiles`
(`0x10035a538`, appel en `0x10035a5f3`). Les trois autres comportements sont des fonctions sœurs : `…_torpedo` (`0x10035d29c`),
`…_bomb` (`0x100361690`), `…_robot_dog` (`0x1003615e0`).

Chaîne du vecteur : arme (`c_attachment_server_hardpoint::set_track_vector`, `0xf1c22`) → `create_missile` / `create_missile_internal`
(`0x1000e2380` / `0x1000e34dc`, qui rangent le `vec3f` dans le missile en `+0x1c0 … +0x1c8`) → lu dans `tick_missile_behaviour_missile`
en `0x10035f9b0` (condition préalable), `0x10035fbd4` (note d'un véhicule), `0x10036006b` (note d'un leurre), puis **réécrit chaque tick**
en `0x10036040c` une fois le missile accroché.

### 2.2 La boucle de guidage est confirmée (LU)

| Élément | Constante | Adresse de la constante | Lue en |
|---|---|---|---|
| portée² du détecteur | 16 000 000 | `0x102869cec` | `0x10035fb54` (véhicules), `0x10035ffe7` (leurres) |
| cône | 0,7 | `0x102869794` | `0x10035f9f0` (préalable), `0x10035fbc7` (candidat), `0x10036005e` (leurres) |
| exposant | 5,0 (appel `powf`, `0x10035fc56`) | `0x10286976c` | |
| poids de l'alignement | 0,9 | `0x1028698f8` | `0x10035fc5b` |
| distance de référence | 4 000 | `0x102869988` | `0x10035fc29` |
| bornes du terme distance | 0 et 1 | `0x1028697c4` / `0x102869730` | |
| poids de la distance | 0,1 | `0x1028697b0` | `0x10035fc68` |

Note retenue : `0,9 × cos⁵ + 0,1 × (1 − d/4000)` avec `d/4000` borné entre 0 et 1, où `cos` = produit scalaire entre le `track_vector`
et la direction missile → candidat. Ignorés : véhicule détruit (`+0x210`), même équipe (`+0x260` contre `+0x20` du missile) ; pour
l'anti-aérien (type 1, `cmpl $1,-0x1f0(%rbp)`) le véhicule doit répondre vrai à la méthode virtuelle `+0xb8` (cible aérienne).
Meilleure note initiale : **0** (`0x10035fa6e`), comparaison stricte `>` (`0x10035fc79`).

### 2.3 Deux corrections au diagnostic

1. **Le « 0,05 pour l'anti-aérien » n'est pas un seuil de départ.** Dans le code Mac, 0,05 (`0x1028697a4`) est rangé pour le type 1 en
   `0x1003602f0` dans une variable (`-0xf0(%rbp)`) qui sert ensuite au suivi de la cible accrochée (`0x100360401`, multiplication par une
   distance). Le seuil de départ est 0 pour tous les types.
2. **Les « 4 lectures » de 16 000 000 se répartissent ainsi** : `0x10035fb54` et `0x10035ffe7` dans le comportement du missile
   (véhicules, leurres), `0x10035d6be` et `0x10035dbaa` dans le comportement de la **torpille**. Les deux sites « non étudiés »
   de la tour (`0x749b98`, `0x74a234`) sont donc très probablement la torpille et non des contre-mesures. Conséquence : le patch ne
   changerait pas la torpille tant qu'on ne touche que `0x747168`.

### 2.4 Une condition que le diagnostic ne mentionne pas (LU)

Avant même de chercher, le Mac teste en `0x10035f9f0` que **le `track_vector` est dans un cône de 0,7 autour de l'axe avant du
missile**, sinon il saute toute la recherche. Puis le cône de 0,7 des candidats se mesure aussi **par rapport à l'axe avant du
missile**, pas par rapport au `track_vector`. (LU pour les produits scalaires et le seuil ; DÉDUIT que le vecteur de référence est
l'axe avant : c'est la 2e colonne de la matrice de rotation du missile, construite en `0x10035f8ee … 0x10035f974`.) La recherche est aussi sautée si le
missile est déjà guidé (`cmpb $0,0x1a1(%r13)`), pour le type 5 et pour le type d'objet `0x30` (non identifiés).
Équivalents approximatifs côté Windows d'après vos adresses : drapeau de guidage `0x175` (Mac `0x1a1`), vecteur `0x190` (Mac `0x1c0`).

À vérifier sur Windows avant de promettre l'effet du patch « portée » : un bateau à 8 km verrouillé hors du cône de 45° du missile
ne deviendrait **pas** candidat, même avec 10 km de portée. Le terme `1 − d/4000` vaut 0 au-delà de 4 km : la note d'un bateau lointain
est donc `0,9 × cos⁵` seulement, sans bonus de proximité (cela ne gêne pas ; une unité proche et bien alignée gagne quand même
jusqu'à 0,1 de bonus).

### 2.5 Ce qui n'est pas retracé

L'identifiant du candidat retenu est rangé en `+0x1fc` du missile (`0x100360865`) ; `+0x200` sert à retrouver le véhicule suivi
et à copier sa position en `+0x1a8 … +0x1b8` à chaque tick (`0x100360304 … 0x100360373`). Je n'ai pas retrouvé l'instruction qui met
`+0x1a1` à 1.

---

## Q3 — Circuit d'atterrissage

### 3.1 Les 10 retouches du Mac correspondent-elles à celles de Windows ? — **Oui**

(Fonction Mac : `c_vehicle_server_carrier::docking_manager_air::update`. Je n'ai relu que le côté Mac ; vos adresses sont reprises de votre
tableau.)

| n° Mac | Mac | Contenu (LU côté Mac) | Windows (votre étude) |
|---|---|---|---|
| 1 | `0x1001af900` | `jbe` de l'état 1 → bloc `0x1001af914` | S1 `0x007019fa` |
| 2 | `0x1001af85b` | `jbe` de l'état 2 → même bloc | S2 `0x00701d33` |
| 3 | `0x1001af867` | `jmp` du passage 2 → 3 → même bloc | S3 `0x00701d4e` |
| 4 à 7 | `0x1001af785, af7d4, afa98, afae7` | 4 `addps` : centre du virage avant, `(−1000, 600)` → `(−1000, −1800)` (constantes `0x10286b8c0/b900` → `b920/b930`) | C1 : une seule écriture de pile `0x00701379` |
| 8 | `0x1001af870` | seuil de l'état 3, 600 → −1800 | C2 `0x00701d5b` |
| 9 | `0x1001afaf2` | seuil de l'état 5, 600 → −1800 | C3 `0x00701f4e` |
| 10 | `0x1001af87b` | `addss` → `subss` | C4 (facultatif) `0x00701d65` |

Le 10e site est inutile chez vous : sur le Mac, `movss [600],%xmm1 ; ucomiss %xmm1,%xmm0 ; addss %xmm1,%xmm0` (`0x1001af870 … af87b`)
utilise le **même registre** comme seuil et comme décalage de visée. Changer le seuil obligeait à inverser l'addition. Chez vous les deux
lectures sont séparées : votre recommandation de ne pas le faire est correcte. Effet du site 10 sur le Mac : la visée passe de +600 à
+1 800 m devant l'avion, pendant 1 tick (l'état 3 ne dure plus qu'un tick avec le cercle).

### 3.2 Pourquoi 2,7 km dans mes notes et 2,06 km chez vous ? — **Artefact du Mac** (LU pour le code, DÉDUIT pour le contenu de `xmm1`)

Le bloc d'attribution de la piste (`0x1001af914`) commence par `cmpl $1,(%r14)` (mode accostage), `cmpl $-1,0x80(%r14)` (piste libre), puis :

```
movshdup %xmm0,%xmm0       ; z de l'avion
addss    [3000.0],%xmm0    ; z + 3000        (0x102869a28)
mulss    %xmm0,%xmm0       ; (z + 3000)²
addss    %xmm1,%xmm0       ; + (terme en x)  <-- registre xmm1 laissé par du code précédent
sqrtss                      ; distance
ucomiss  [1000.0]           ; < 1000 ?        (0x10286981c)
```

Le seuil est bien 1 000 m, comme chez vous. Mais le terme en x est **le contenu de `xmm1` au moment du saut**, qui dépend du site d'où l'on arrive :

- **site 1 (état 1)** : `xmm1 = (pos + (1000, 1800))²` calculé en `0x1001af8a7 … af8aa` → voie 0 = `(x + 1000)²`. C'est un **vrai test de distance**
  à la porte `(−1000, −3000)` : partie « avant » = **1 031 m** ;
- **site 2 (état 2)** : `xmm1` contient le vecteur normalisé tourné et multiplié par `0,7833` (constantes `0x10286b8d0 … b8f0`) ; sa voie 0 vaut
  `n.z × 0,7833`, soit moins de 0,8 en valeur absolue. Devant `(z + 3000)²` (≥ 10⁶) ce terme est **négligeable**. Le test devient
  `|z + 3000| < 1000`, c'est-à-dire **`z < −2000`** : sur le cercle de rayon 1 200, l'arc entre la porte et ce point est `1200 × arccos(200/1200)`
  = **1 684 m**. C'est la constante `APRES = 1684.0` de `outil/generateurs/simuler_file_atterrissage.py` (commentaire « z < −2000 »).

Total Mac : 1 031 + 1 684 = **2 715 m ≈ 2,7 km, ≈ 34 s à 80 m/s**, que mes notes ont présenté à tort comme la règle du jeu.
Chez vous le bloc relit tout dans la pile et appelle une vraie distance euclidienne : **2,06 km est le bon résultat pour Windows**.

Conséquence : la fenêtre Windows est environ **un quart plus courte** que celle sur laquelle le Mac avait mesuré 7:28 (une piste toutes les
1:31). Le cercle (l'essentiel du gain) n'est pas concerné. Si vos essais sont un peu moins bons que le Mac, ce n'est pas un défaut de port.
Pour retrouver exactement la fenêtre du Mac, il faudrait remplacer le test euclidien par un test sur le seul `z` : je ne le conseille pas.

---

## Q4 — Frein v5 (`hold_idle`) : risques

Rappel de la logique (`cc2x_frein.c`, lignes 230-243) : avion tenu (`holding`), `mode == 0`, `hold_idle=1` → `power` lu puis mis à 0 à chaque
tick ; `power_saved` rangé au premier tick ; `idle_end` remet `power_saved` **si la puissance vaut 0,0 exactement**.

### 4.1 `override_power` est enregistré dans la sauvegarde — LU + vérifié sur fichiers

`c_vehicle_server::parse_state_xml` (`0x100195772`) range : `override_target_velocity` → `+0x2c8` (`0x100195a4a`), **`override_power` → `+0x2cc`
(`0x100195a69`, valeur par défaut 1,0 si la balise manque)**, `override_taxi` → `+0x2d0`. Ce sont vos `CONTROL_SPEED` (`+0x1f8`),
`CONTROL_POWER` (`+0x1fc`), `CONTROL_TAXI` (`+0x200`). Je l'ai aussi contrôlé dans mes deux sauvegardes Mac : `save.xml` contient
`override_power="…"` pour 106 (slot 18) et 52 (slot 19) véhicules, dont **au moins 17 à 0** dans chacune (le jeu met donc lui-même 0 sur des véhicules rangés ou garés ; je n'ai pas relevé lesquels) et les
autres à 1,0.

→ **Risque A.** Une sauvegarde (surtout l'autosave) faite pendant que le plugin tient un avion à 0 enregistre ce 0. Au rechargement,
le plugin a perdu `power_saved` (`on_session` vide `g_track`), lit 0, démarre un nouvel « IDLE » avec `power_saved = 0`, puis à la fin
« remet » 0. Le moteur reste coupé jusqu'à ce que le jeu réécrive 1,0 lui-même.

### 4.2 Le jeu écrit lui-même 0 (et 1,0) à plusieurs endroits — LU

Écritures de la puissance du véhicule dans `docking_manager_air::update` : **1,0** en `0x1001af3a4, afdb1, b0958, b13a3, b24d4` ;
**0** en `0x1001b06b6`, `0x1001b1e25` et `0x1001b20ae` (ce dernier juste après un appel qui remet le frein à ses valeurs de repos
`(0, 1,0)` : `0x1001b20a6  callq *0x130(%rax)`). `docking_manager_surface::update` en fait de même ; `c_vehicle_server::undock_immediate`
met **1,0** (`0x1001b6090`).

→ **Risque B.** Le test `getf(POWER) == 0.0` de `idle_end` ne sait pas distinguer **notre** 0 d'un 0 que le jeu vient d'écrire au moment où il
prend l'avion en charge (`dock` passe à 5/6). Dans ce cas le plugin réécrit `power_saved` (typiquement 1,0) par-dessus le 0 voulu par le
jeu : le moteur est rallumé pendant le roulage ou la poussée. Vos tests ne couvrent que 0,4 comme valeur posée par le jeu (T22,
« recall: a power the game set itself is not overwritten »), jamais 0.

### 4.3 Autres points

- **Risque C — mémoire perdue** : `power_saved` est dans le plugin seulement. Une fin de session (`on_session`), un rechargement de DLL ou un
  plantage pendant l'IDLE perdent la valeur à restituer (voir A).
- **Risque D — avion bloqué** : un avion tenu avec `power = 0` et frein 1,0 ne décolle plus, même si le joueur lui donne des waypoints
  (mode 0). Seule la reprise en main (mode ≠ 0) ou la prise en charge par le jeu (`dock ≠ 0`) le libère. Pas dangereux, mais à savoir.
- **Sans conséquence** : le 0 annule aussi tangage/roulis/lacet (voir 1.2) ; sur un avion immobile, c'est sans effet. Le gaz repart de 0 à la
  restitution (intégrateur borné à 0, pas d'emballement).

### 4.4 Ce que je ferais (suggestion, à décider côté tour)

1. À `idle_end`, **ne rien restaurer si `dock ≠ 0`** (le jeu reprend la main : il réécrit lui-même 1,0 ou 0 selon l'état) ; ne restaurer que
   quand c'est le plugin seul qui arrête (pilote de retour, `hold_idle=0`).
2. Ne jamais accepter `power_saved == 0` : si la valeur lue au début est 0, utiliser **1,0** (valeur par défaut du jeu pour un véhicule sans
   override).
3. Restituer à la fin de session (`on_session`) pour tout avion en IDLE.
4. Avant de supposer quoi que ce soit, **journaliser** la valeur de `power` lue juste après le tick du jeu au moment où `dock` change, avec une
   ligne dédiée : on saura si le jeu pose 0 ou 1,0 à la prise en charge.
5. Ajouter deux tests : puissance posée par le jeu = 0,0 au rappel ; fin de session pendant l'IDLE.

NON VÉRIFIÉ : que les sites d'écriture Windows soient les mêmes que ceux du Mac (offsets SDK : power `0x1fc`, taxi `0x200`).

**Mise à jour (même jour) : la tour a depuis publié l'essai v5 (commit `596d2b3`). Voir l'addendum A en fin de fichier : il confirme
plusieurs points ci-dessus et précise la v6.**

---

## Q5 — Démarrage automatique : restauration des équipements

### 5.1 Ma fonction équivalente a-t-elle le même défaut ? — **Oui, structurellement** (LU)

Chemin Mac : `c_logic_server::load_game` (`0x100327436`) → `c_logic_server::parse_saved_game` (appel en `0x100329974`) →
**`c_vehicle_container_server::create_from_save_data`** (`0x10032adb6`). (`post_load_saved_game`, `0x10032a122`, est une passe
ultérieure : pas la restauration.)

Dans `create_from_save_data`, pour chaque véhicule enregistré :
1. `create_vehicle_internal` (`0x10032ae32`) ;
2. boucle sur les équipements enregistrés (indice `ebx`, de `0` à `[saved+0x80]`) : appel de **`c_vehicle_server::set_attachment`**
   (`0x10010313a`), qui **ignore sans erreur** un emplacement trop grand (`0x10010315c  cmpl %esi,0x208(%rdi) ; jbe`) : exactement votre `0x5E9D10` ;
3. **puis** `0x10032afdd  movq 0x200(%r15),%rax ; 0x10032afe8  movq (%rax,%rbx,8),%r12` : lecture de `véhicule.équipements[ebx]` **sans comparer
   `ebx` au nombre d'équipements (`+0x208`)**. Seul un test « vide ou non » suit (`0x10032afec`), puis `cmpl $0,0x58(%r12)` sur le résultat.

C'est la même erreur que votre `0x5EF512-0x5EF518`. Une autre boucle de la même fonction (`0x10032b20f  cmpl 0x208(%r12),%esi ; jae`) **a**,
elle, le contrôle de borne : l'oubli est local à la première.

Réserve (DÉDUIT) : lire un élément au-delà du tableau ne plante pas forcément sur le Mac. Si la mémoire qui suit est à zéro, le test « vide »
saute l'élément en silence ; si elle contient autre chose, c'est un plantage comme chez vous. Je n'ai **jamais chargé une sauvegarde sans
Revolution sur le Mac** : l'absence de plantage chez moi ne prouve rien tant que Revolution était présent (ci-dessous).

### 5.2 Revolution était-il actif quand mes sauvegardes ont chargé ? — **Oui**

- `~/Library/Application Support/Carrier Command 2/mods.xml` (dernière modification **3 septembre 2026**, donc inchangé pendant tous mes
  essais de chargement) liste `2937532682` (missiles) et **`3460002110` (Revolution 1.6-19)** ;
- `outil/tests_en_jeu/lancer_test.sh` ne touche pas à `mods.xml` ;
- mes notes (`DEMARRER_cc2_patchs.md`, ligne 204) le disent : « Mods actifs sur le Mac : 2937532682 et Revolution 3460002110 ».

Preuve par les données : la copie Mac de Revolution a les **mêmes** nombres d'emplacements que votre tableau (porte-avions 18, avion léger 9,
avion lourd 11, hélico léger 7, contre 14 / 6 / 9 / 5 sans Revolution), et mes sauvegardes dépassent le jeu normal mais tiennent dans Revolution :

| Sauvegarde Mac | porte-avions (0) | avion léger (8) | avion lourd (10) | hélico léger (12) | Dépasse le jeu normal ? | Dépasse Revolution ? |
|---|---|---|---|---|---|---|
| slot 18 (réécrite le 23/10) | **18** | **7** | 6 | 4 | oui (0 et 8) | non |
| slot 19 (autosave du 24/10) | **18** | **7** | 5 | 4 | oui (0 et 8) | non |

(Votre tableau donne pour « sauvegarde 18 (Mac, 2024) » 14 / 8 / 6 / 3 : ce n'est pas la sauvegarde 18 que j'ai aujourd'hui, c'est une
ancienne copie.)

→ L'hypothèse de la tour (« toutes les sauvegardes ont été faites avec Revolution et plantent dès qu'il est retiré ») est **cohérente** avec le
Mac : chez moi les mêmes sauvegardes chargent sans problème, avec Revolution actif. Le test « mêmes clics avec Revolution coché » reste le bon test.
Un test miroir côté Mac (retirer Revolution, charger le slot 18) est possible mais je ne l'ai **pas** fait (le jeu n'a pas été lancé).

---

## Ce qui n'a pas été vérifié (résumé)

- Rien n'a été relu dans l'exécutable Windows ; tous les parallèles sont des correspondances de logique.
- Le 0,005 de Windows est une déduction à partir des mesures (point 1.5).
- Le « plafond qui fuit » (1.3) est déduit de la structure Mac, pas observé.
- Le jeu n'a pas été lancé ; aucun essai n'a été fait.

---

## Addendum A — Essai v5 de la tour (`596d2b3`, lu le 28/10 après l'envoi de ce fichier)

Lecture seule, même méthode que ci-dessus. Résumé de ce que dit la tour (`JOURNAL_atterrissage.md`, entrée du 28/10 à 08:50) : l'avion 9 est
arrêté et tenu (`HOLD`, frein 1,0), `IDLE` démarre, la puissance lue reste à 0,00 (à 1 s et 10 s) donc **le jeu ne la remet pas** ; l'avion
reste sous 1 m/s pendant ~86 s de jeu avec deux « bosses » (roues 2/3 puis 1/3, hauteur 18 → 29 m, rebond environ toutes les 15 s) ;
à la seconde bosse le contact est perdu plus longtemps que `grace_s`, `IDLE ended` + `BRAKE released` **rendent la puissance 1,00** alors que
`mode=0` et qu'un waypoint reste (`wp=1`) ; l'avion accélère au milieu du pont et s'écrase. L'ordre de retour du moddeur (`dock=5 mode=3`)
arrive 0,5 s **après** le lâcher. La tour conclut que le crash vient du soulèvement puis du lâcher, pas de l'ordre de retour.

### A.1 Confirmé par le code Mac : la coupure tient parce que `tick_control` ne fait que lire la puissance (LU)

Dans `c_vehicle_server_wing::tick_control` les seuls accès à `+0x2cc` sont des **lectures** (`0x1001c2966`, `0x1001c5e1e`, `0x1001c6bc1`).
Les écritures sont dans le gestionnaire d'accostage (aux changements d'état) et dans `undock_immediate` (voir 4.2), jamais à chaque tick. Un 0
écrit par le plugin n'est donc remplacé que lorsque l'avion entre dans un de ces états. Cela colle avec « power read 0.00 before our write ».

### A.2 Pourquoi l'avion accélère après le lâcher (LU + DÉDUIT)

En mode 0 sans vitesse demandée, le programme remonte la vitesse visée à un plancher de **48 m/s pour l'Albatros** (`0x1001c2b52`, 72 pour le
Manta) et l'intégrateur de gaz pousse vers ce plancher (voir 1.1). Avec un waypoint présent (`wp=1`), dès que la puissance repasse à 1,0 l'IA
« veut voler » : l'accélération observée en est la conséquence normale, pas une anomalie. C'est exactement le risque C/D du 4.3 : la restitution
ne doit pas dépendre d'une perte de contact.

### A.3 L'hypothèse « l'IA tire le nez » vaut après la restitution, pas pendant les bosses (DÉDUIT)

Tant que la puissance vaut 0, les **quatre** sorties (tangage, roulis, lacet et gaz) sont multipliées par 0 (voir 1.2) : l'IA ne peut donc pas tirer
le nez, et les deux bosses (puissance 0, `wheels` 3/3 → 2/3 → 1/3) ne viennent pas d'une commande de vol. Elles viennent de la physique : vent relatif
de ~25 m/s sur les ailes, mouvement du pont, rebond des roues. La piste de la tour (ralentir le porte-avions après la pose) est cohérente avec cela.
Après la restitution à 1,0, en revanche, l'IA peut tirer le nez : le soulèvement final se superpose à l'accélération.

### A.4 À propos de la v6 envisagée (« ne rendre la poussée qu'à un signal explicite : `dock != 0`, pilote de retour »)

Le principe (ne **jamais** restituer sur une simple perte de contact) est bon. Deux nuances d'après le code Mac :

1. **`dock != 0` est justement le moment où le jeu écrit lui-même la puissance** (0 ou 1,0 selon l'état, voir 4.2). À ce signal il vaut mieux
   **cesser de forcer 0 sans rien réécrire**, et laisser le jeu décider ; restituer `power_saved` par-dessus risque de rallumer le moteur pendant la
   prise en charge. Je ne peux pas prouver que le jeu réécrit toujours la puissance à l'entrée de `dock = 5` : la décision doit venir d'une
   **ligne de journal** (valeur de `power` lue juste après le tick du jeu, au tick où `dock` change), pas d'une supposition.
2. **« Pilote de retour »** (mode ≠ 0) est un cas sûr pour restituer : le jeu n'écrit rien dans ce cas. Restituer **1,0 si `power_saved` vaut 0**
   (voir 4.4, point 2).

### A.5 Le waypoint restant (`wp=1`) est le vrai danger après le lâcher

Tant que la liste de waypoints n'est pas vide, rendre la puissance à 1,0 lance l'avion (A.2). Le moddeur le dit aussi : « il avait déjà un waypoint ».
Deux manières de le traiter : vider la liste **avant** de restituer la puissance (le SDK expose `WAYPOINTS` en écriture, voir le journal de la tour
du 27/10 à 16:10), ou tenir `power = 0` jusqu'à la prise en charge. Effacer le waypoint du joueur est une décision de jeu : à valider avec le moddeur.

### A.6 Ce que je n'ai pas pu conclure

`CONTROL_TAXI` : le Mac le lit dans la branche de mode 0 de `tick_control` (`0x1001c2c7a`), donc l'IA en tient compte ; je n'ai **pas** tracé son effet
sur le régulateur et n'en tire aucune conclusion. À l'essai en jeu, pas par supposition.

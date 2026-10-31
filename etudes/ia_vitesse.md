# Étude — vitesse des avions sous IA (Albatros, Manta)

25/10/2026, phase 1 (lecture seule du programme, rien modifié).

## 1. En bref

- **La piste du 25/10 était fausse** : le réglage `vehicle_ai_wing_cruise_speed` = 120 n'est **jamais lu** par la
  simulation (seule la cinématique d'intro lit sa copie « client »). Le changer ne ferait rien.
- **Ce qui fixe vraiment la vitesse** : en vol normal (aller à un point, patrouiller), l'IA ne demande **aucune vitesse
  particulière (0)**, et le programme remonte ce 0 à un **plancher** :
  - **Albatros : 48 m/s** (≈ 173 km/h) ;
  - **Manta : 72 m/s** (≈ 259 km/h).
  Plafond commun : 144 m/s. C'est pour ça qu'ils « traînent » : ils volent au plancher, ce qui correspond à la
  moitié de leur puissance que tu vois.
- **Ailleurs, rien à changer** : en combat aérien l'IA vise déjà 160 m/s (elle est à fond) ; dans le circuit
  d'atterrissage la vitesse est imposée à 80 m/s par le bateau (non touché par ce projet).
- **Pour tout le monde** : ce plancher vaut pour tous les avions pilotés par l'IA, **les avions ennemis compris**.
  Quand tu pilotes toi-même, rien ne change (probablement : non vérifié en jeu).

## 2. Comment l'IA règle les gaz

Chaque tick (30 par seconde), l'IA compare la vitesse visée à la vitesse de l'avion et pousse ou relâche la manette
petit à petit (comme un régulateur de vitesse de voiture). Elle se stabilise sur la puissance qui tient juste la
vitesse visée. Viser plus vite = plus de gaz ; viser plus vite que ce que l'avion peut atteindre = **plein gaz
en permanence**.

Moteurs (fichiers de l'avion) : Albatros 50, Manta 100 (le Manta pousse deux fois plus, même masse 1 t).

**Combien de % pour quelle vitesse ?** Le programme ne le dit pas directement (ça dépend de la résistance de l'air,
calculée par les gouvernes). Si on part de ton observation (≈ 50 % aux deux planchers) et d'une résistance qui croît
comme le carré de la vitesse (cas habituel), on obtient, **estimation à vérifier par une mesure** :

| | Jeu d'origine | 80 % | Plein gaz |
|---|---|---|---|
| Albatros | 48 m/s (173 km/h) | ≈ 61 m/s (220 km/h) | ≈ 68 m/s (245 km/h) |
| Manta | 72 m/s (259 km/h) | ≈ 91 m/s (328 km/h) | ≈ 102 m/s (367 km/h) |

Soit environ **+27 % de vitesse à 80 %** et **+41 % à plein gaz**. Le « plein gaz » est sûr (on vise 144, que
l'avion n'atteint pas : la manette reste au maximum) ; le « 80 % » demande de viser une vitesse précise, à
ajuster après un essai.

## 3. Effet sur le carburant

Le carburant brûlé est proportionnel à la puissance moteur (consommation Albatros 2, Manta 5, × 0,008 par tick ;
réservoirs 800 et 1200, +1000 par réservoir supplémentaire).

| Autonomie (sans réservoir en plus) | Jeu d'origine (≈ 50 %) | 80 % | Plein gaz |
|---|---|---|---|
| Albatros | ≈ 55 min | ≈ 35 min | ≈ 28 min |
| Manta | ≈ 33 min | ≈ 21 min | ≈ 17 min |
| Distance parcourue avec un plein | 100 % | ≈ 80 % | ≈ 70 % |

En clair : **à fond, ils arrivent ~40 % plus tôt mais tiennent deux fois moins longtemps en l'air**. Ces durées
supposent que l'avion vole tout le temps en croisière ; à vérifier en jeu.

## 4. Les solutions

### Solution 1 — une seule vitesse, plus haute (le plus simple)

Rediriger les deux planchers (48 et 72) vers d'autres valeurs déjà présentes dans le programme : 2 retouches
d'octets, module « programme » comme l'ascenseur ×2. Valeurs possibles sans rien ajouter : 60, 64, 72, 80, 96,
100, 120, 144.

- **Plein gaz** : les deux planchers à 144.
- **≈ 80 %** : Albatros 64, Manta 96 (à ajuster après l'essai).
- Effort : court (une partie de session), risque faible, tests sur copies comme d'habitude.
- Limite : **les avions ennemis aussi** vont plus vite (et brûlent plus). Pour ne toucher que les tiens, il
  faut une petite greffe qui regarde l'équipe de l'avion (quelques dizaines d'octets, comme celle des hélicos).

### Solution 2 — des modes Éco / Normal / À fond

Éco = jeu d'origine (48 / 72), Normal = ≈ 80 %, À fond = plein gaz.

Ce qu'il faut (3 morceaux) :
1. **Greffe de code C** dans le pilotage des avions (à la place des deux planchers) : elle lit le mode choisi et
   applique la vitesse correspondante, **seulement pour tes avions**.
2. **Un canal écran → programme** : les écrans du bateau (Lua) ne savent pas modifier un avion. On réutilise
   l'astuce du relevé : l'écran « écrit » un message (print) que notre greffe intercepte et range en mémoire. Le
   message est renvoyé toutes les quelques secondes, donc rien n'est perdu au chargement d'une partie.
3. **Des boutons** dessinés en Lua par-dessus un écran du bateau (emplacement `library_custom` libre : 6 à 9).

Deux variantes :
- **2a. Un mode pour toute l'escadrille** : un seul sélecteur (Éco / Normal / À fond). Effort : 1 à 2 sessions.
- **2b. Un mode par avion** : tu choisis l'avion puis son mode ; chaque avion garde le sien. Effort : 2a + environ
  une session (retrouver chaque avion par son numéro, petite liste de modes).

Où mettre les boutons : sur l'écran de contrôle des véhicules (celui où tu donnes les ordres ; il est remplacé par
le mod Revolution, il faudra trouver une place libre) ou sur l'écran du trafic aérien. Le choix visuel se fera sur
une maquette de 4 à 6 variantes, **après** ton choix de solution.

Limites : en multijoueur, ça ne marche que si c'est toi qui héberges la partie (la simulation tourne chez l'hôte).

## 5. Recommandation

Commencer par la **solution 1 en « plein gaz »** (rapide), l'essayer en jeu une fois pour mesurer la vraie vitesse
et la vraie autonomie avec l'horloge. Ça donne les chiffres réels du tableau ci-dessus. Ensuite, si tu veux choisir
selon la mission, passer à la solution 2a (le mode « À fond » sera déjà prêt et réglé).

## 6. Annexe technique (pour les prochaines sessions)

- `c_vehicle_server_wing::tick_control` (0x1001c26c0). `control_mode` (0x2a0) : 0 = points de passage, 3 = consigne
  du bateau (circuit d'atterrissage, saute ce calcul), 1 = autre.
- Mode 0 : `get_waypoint_position_direction_speed` (0x1001b78aa) renvoie une vitesse (0 en vol normal ; vitesse de
  l'objet suivi s'il en suit un), puis :
  - 0x1001c2b52 `maxss [0x102869af0]` (48.0, plancher de tous les avions) — octets `f3 0f 5f 0d 96 6f 6a 02` ;
  - 0x1001c2b5a `minss [0x102869b2c]` (144.0, plafond) ;
  - 0x1001c2b62 `movss %xmm1, 0x2c8(%r13)` (vitesse visée) ;
  - 0x1001c2b6b `cmpl $0xa, 0x90(%r13)` (type 10 = `chassis_air_wing_heavy` = Manta) ;
  - 0x1001c2b75 `maxss [0x102869b30]` (72.0, plancher du Manta) — octets `f3 0f 5f 05 b3 6f 6a 02` ;
  - 0x1001c2b7d `minss [0x102869b2c]` (144.0) ; 0x1001c2b85 `movss %xmm0, 0x2c8(%r13)`.
  Constantes déjà présentes (lecture seule) pour une redirection « rip » : 60 0x102869a44, 64 0x102869aa4,
  72 0x102869b30, 80 0x102869900, 96 0x102869c0c, 100 0x1028697ac, 120 0x1028697b8, 144 0x102869b2c,
  150 0x1028698b8, 160 0x102869a90.
- Gaz en vol normal (0x1001c5da0…0x1001c5de7) : cible T = S + a × (120 − S), avec S = 0x2c8 + correction bornée
  −10/+40 et a = clamp((distance horizontale au point visé − 20) / 780, 0, …) ; puis
  manette (0x3f4) += `vehicle_ai_wing_throttle_stiffness` × ((T − v) / 120 − Δv). Borne haute de `a` non
  identifiée (registre réutilisé) : en pratique, l'observation du moddeur (≈ 50 %) dit que l'IA reste au plancher.
- Commandes (0x3e8 tangage, 0x3ec, 0x3f0, 0x3f4 manette) × 0x2cc puis bornées à chaque tick (0x1001c5e3f :
  min (−1, −1, −1, 0), max (1, 1, 1, 1)) : la manette reste entre 0 et 1, donc viser 144 = plein gaz sans
  « emballement » quand il faut ralentir ensuite.
- Combat (drapeau −0x194) : même formule avec `vehicle_ai_wing_dogfight_target_speed` = 160 (bloc 0x1001c6b62).
- Les réglages « dev » serveur se lisent par `get_table()` + 0x98 + décalage dans `c_dev_value_server` (valeur =
  nom + 8). `vehicle_ai_wing_cruise_speed` (lu à +0xec0) et `_cruise_altitude` (+0xe98) : aucune lecture côté
  serveur.
- Moteur : `tick_force_emitter` (0x1001a7aa2), niveau réel qui suit la demande à 0,05 par tick
  (`vehicle_control_force_emitter_speed`), force = 10 × magnitude × niveau.
- Carburant : `c_vehicle_server_base::tick` (0x100193a3c…0x100193aaa) = max(|demande des moteurs|) ×
  `get_fuel_consumption_rate` (constants.txt `wing_light_fuel_consumption` 2, `wing_heavy_` 5) ×
  `fuel_consumption_multiplier` 0,008, par tick.
- À trouver en phase 2 si greffe : le champ « équipe » et le champ « numéro » du véhicule côté serveur.

## 7. Choix du moddeur (25/10)

- **Solution 2a** : un seul mode pour toute son escadrille, avions ennemis inchangés.
- Interface : **variante 1 de `etudes/maquette_vitesse_ia.html`** (barre de trois boutons en bas à droite de
  l'écran de contrôle des véhicules, à côté de l'horloge), **en anglais** : titre `SQUADRON SPEED`, boutons
  `ECO` / `NORMAL` / `FLANK` (couleurs de la maquette : vert, cyan, orange).
- Prévu pour la phase 2 : canal dans les deux sens par print() (« régler » et « relire » le mode, pour que les
  trois écrans de contrôle montrent le même), mode gardé d'une partie à l'autre dans un petit fichier, mode
  appliqué seulement à l'équipe de l'écran qui l'a choisi. Plan présenté au moddeur, en attente de son feu vert.

## 8. Phase 2 faite (25/10)

Modules `vitesse_escadrille` + `vitesse_boutons` écrits, testés sur copies et **activés dans le jeu** (14 modules,
md5 ce8dafec…). Détails techniques et essai à faire : `DEMARRER_cc2_patchs.md`, section 6 point 9.

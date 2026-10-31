# Mesures des retours d'hélicos (journal automatique, temps de jeu)

## Référence du 23/10/2026 — jeu sans patch hélicos

Modules actifs : ascenseur_x2, atterrissage (avions seulement), effet_tele, horloge, journal.
4 hélicos (2 Razorbill puis 2 Petrel, ordre exact pas sûr), lancés puis rappelés tout de suite, navire à l'arrêt.

| Hélico | piste | pont | hangar | approche (pont − piste) | pont → hangar |
|---|---|---|---|---|---|
| 1 | 0:49 | 1:49 | 2:28 | 1:00 | 0:39 |
| 2 | 2:16 | 3:21 | 4:06 | 1:05 | 0:45 |
| 3 | 3:54 | 4:52 | 5:29 | 0:58 | 0:37 |
| 4 | 5:17 | 6:13 | 6:52 | 0:56 | 0:39 |

**FINI en 6:52** (4 hélicos), piste donnée toutes les **1:29**, approche moyenne **1:00**, pont → hangar **0:40**,
**0 ratée**. Environ 8 min en temps réel.

Lecture : la piste suivante est donnée 25 à 33 s après chaque toucher (le temps que l'hélico roule jusqu'à
l'ascenseur). Un hélico occupe donc la piste ≈ 1:00 d'approche + ≈ 0:28 de roulage = 1:28. **L'approche
(1:00) est le plus gros morceau**, bien plus que les 25 s devinés dans l'étude.

## Essai du 24/10/2026 — module helicos_ascenseur (pose sur la plateforme + piste en parallèle)

Mêmes 4 hélicos. Le code ajouté a bien tourné : le 1er hélico a pris la voie ascenseur (piste 0:10, posé sur la
plateforme à 0:52, approche 0:42). Mais **deux hélicos se sont percutés** (le moddeur n'a pas vu où) : le journal de
partie du jeu note `destroy_vehicle` d'un Razorbill (type 12) sans tireur (attacker_team 0) à 06:26:19 UTC. Le jeu
n'a pas planté (aucun rapport de plantage). Fin estimée par le moddeur : ~6:14 pour les 3 restants. Journal photographié
à 1:02 seulement (1 hélico suivi).
Cause probable, non vérifiée : l'hélico qui descend sur la plateforme (x = 27,5) et un hélico qui attend au bord
(`lift_upper_wait`, x = 12, à 15,5 m) avec leurs rotors.
**Décision du moddeur** : la pose sur l'ascenseur n'est pas la priorité → module rangé en réserve, retiré du jeu.

## Essai du 24/10/2026 — approche ×2 + toucher près de l'ascenseur (VALIDÉ)

Modules actifs : ascenseur_x2, atterrissage, effet_tele, horloge, journal, **helicos_approche_x2** (point visé
100 m devant au lieu de 50 : ~10 m/s au lieu de ~5) et **helicos_pres_ascenseur** (toucher vers z = −40, à côté de
`taxi_a`, au lieu de z ≈ 7 à 30). Programme md5 c6dccf0c… vérifié.

| Hélico | piste | pont | hangar | approche | pont → hangar |
|---|---|---|---|---|---|
| 1 | 1:04 | 1:34 | 2:04 | 0:30 | 0:30 |
| 2 | 1:52 | 2:22 | 2:51 | 0:30 | 0:29 |
| 3 | 2:39 | 3:06 | 3:37 | 0:27 | 0:31 |
| 4 | 3:25 | 3:51 | 4:22 | 0:26 | 0:31 |

**FINI en 4:22** (référence 6:52, **−2:30, −36 %**), piste toutes les **0:47** (1:29), approche **0:28** (1:00),
pont → hangar **0:30** (0:40), **0 ratée**, aucune collision. La piste suivante est donnée 17-19 s après chaque
toucher (25-33 s avant). Le 1er hélico a reçu la piste plus tard qu'à la référence (1:04 contre 0:49 : il faut
d'abord rejoindre le point d'attente, sans rapport avec les patchs) ; de la 1re piste au dernier rangé :
3:18 contre 6:03 (**−45 %**). Le moddeur : « nettement plus rapide », toucher « légèrement à l'arrière du pont »
(avancer de quelques mètres : il a dit de ne pas s'en occuper). Essai unique, navire à l'arrêt.

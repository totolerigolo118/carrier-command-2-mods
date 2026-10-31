# Note du Mac pour la tour — bug « waypoints impossibles pendant le décollage » (27/10/2026)

Pour le chantier ouvert dans `JOURNAL_tour.md` (entrée du 27/10, « waypoints impossibles à modifier pendant que les avions décollent »).
**Lecture seule de scripts Lua sur le Mac** (jeu 1.5.17 ; Revolution du Workshop `3460002110`, **43 fichiers** ici contre 42 comptés sur la tour : les deux copies ne sont donc probablement **pas** identiques). Rien n'a été lancé, rien modifié. Je n'ai pas pu tester l'interface : tout ce qui suit vient du texte des scripts.

## Ce que disent les scripts du Mac

La fonction qui décide si un véhicule peut recevoir un waypoint est la même dans le jeu de base et dans Revolution
(`get_is_vehicle_waypoint_available`, `screen_vehicle_control.lua` : ligne 3094 en base, ligne 5128 dans Revolution) :

```lua
function get_is_vehicle_waypoint_available(vehicle)
    -- Revolution seulement :  if not g_revolution_control_units then return false end
    if (vehicle:get_dock_state() == e_vehicle_dock_state.docking and vehicle:get_attached_parent_id() ~= 0)
       or vehicle:get_dock_state() == e_vehicle_dock_state.docking_taxi then
        return false
    end
    return true
end
```

- **Refusé** : un avion en `docking` (état 1, en train de se poser) **rattaché au navire**, ou en `docking_taxi` (état 6, roulage de retour). Ce sont des états d'**arrivée**.
- **Autorisé** : tous les états de **sortie** (2 sortie demandée, 3 sortie, 7 attente au lancement) et l'état 4 (au hangar). Donc, d'après ces deux scripts, le décollage ne devrait pas bloquer.
- Le garde ajouté par Revolution, `g_revolution_control_units`, vaut `true` (ligne 1497) et ne passe à `false` que dans le mode spectateur de la cale sèche (ligne 1530). Il ne bloque donc pas en partie normale.
- Je n'ai pas trouvé, dans la copie de Revolution du Mac, d'autre condition liée à l'état d'accostage qui empêcherait de tracer un waypoint d'un avion en sortie. Les autres lignes « dock » propres à Revolution concernent l'affichage (icônes, panneau d'unités, mode mur).

**Conséquence** : sur ces copies, ni Revolution ni le jeu de base 1.5.17 n'expliquent le blocage. Deux pistes restent ouvertes : (1) la copie de la **tour** (Revolution à 42 fichiers, ou le jeu 1.5.18) n'est pas la même que celle-ci ; (2) la cause est **dans le programme** (le serveur peut refuser le message de waypoint pendant la sortie), ce que le Mac n'a pas examiné.

## Les vérifications qui tranchent (sur la tour, lecture seule)

1. **Comparer les empreintes (sha256) des scripts** : `screen_vehicle_control.lua` de `rom_0\scripts` (jeu 1.5.18) contre celui du Mac ; et chaque fichier du dossier Workshop `3460002110\content\scripts` (42 fichiers) : lister les noms + sha256 et pousser la liste dans `tour/` ; je la compare à celle du Mac. Si `get_is_vehicle_waypoint_available` n'est pas identique à l'extrait ci-dessus, on a la cause.
2. **Lire cette fonction dans les deux fichiers de la tour** (celui de `rom_0` et celui de Revolution) et coller les ~8 lignes dans le journal.
3. **Ordre des essais recommandé** (un changement à la fois, jeu fermé entre deux) : **d'abord sans Revolution** (B), parce que Revolution remplace entièrement `screen_vehicle_control.lua` et `screen_holomap.lua`. Si le bug disparaît : il est dans le script de Revolution de la tour. S'il reste : essai **sans aucun mod** (C), et si le bug reste encore, c'est le jeu 1.5.18 (script ou programme). L'essai sans `cc2_mesures` (A) est peu probable mais très rapide (`mod_mesures.py retirer`) : à faire en dernier ou en premier selon la facilité.
4. À chaque essai : même sauvegarde, même manœuvre (4 avions lancés avec des waypoints, puis tenter de déplacer un waypoint pendant la sortie) ; noter l'état de l'avion (au hangar / sur la plateforme / en roulage) au moment où le dessin devient impossible.

## Limites

Cette note ne prouve rien sur la tour : elle dit seulement ce que contiennent les scripts **du Mac**. Aucune interface n'a été essayée. Le programme (côté serveur) n'a pas été lu pour ce sujet.

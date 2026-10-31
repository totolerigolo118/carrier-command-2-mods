# Inventaire de la fausse API (généré par `python lancer.py --inventaire`, ne pas éditer à la main)

Statuts : **DOC** = décrit dans la documentation du dépôt ; **SCRIPT** = non documenté, appelé par un script du dépôt (forme de l'appel connue,
comportement deviné) ; **SUPPOSÉ** = rien ne l'établit, choix du banc (à confirmer en jeu).

## vehicule (poignee)

| Nom | Statut | Ce que fait la fausse version |
|---|---|---|
| `get` | SCRIPT | vrai si le vehicule existe encore ; la poignee, elle, est toujours renvoyee (jamais nil) |
| `get_id` | SCRIPT | identifiant entier |
| `get_team` | SCRIPT | numero d'equipe (0 = IA, doc 08) |
| `get_definition_index` | DOC | e_game_object_type du vehicule (doc 07) |
| `get_dock_state` | DOC | e_vehicle_dock_state 0..7 (partage_detail/03) |
| `get_dock_parent_id` | DOC | id du bateau d'accostage (doc 07/03) ; -1 SUPPOSE quand il n'y en a pas |
| `get_attached_parent_id` | SCRIPT | id du porte-avions auquel l'appareil est RATTACHE (lu dans screen_propulsion.lua d'apres library_custom_9) ; -1 SUPPOSE si aucun |
| `get_attached_vehicle_id` | SCRIPT | porte-avions : id du vehicule range dans la baie n ; -1 SUPPOSE si la baie est vide ou hors limites |
| `get_position_xz` | SCRIPT | vec2 (x(), y()) = x et z horizontaux en metres ; y() est donc le z du monde |
| `get_velocity_magnitude` | DOC | vitesse en m/s (ETUDE modes carburant, annexe B) |
| `get_linear_speed` | SUPPOSÉ | ABSENT par defaut (cas majoritaire du journal du 28/10 : '-' dans 96 % des lignes, numerique dans 4 % : contexte inconnu) ; avec jeu.avec_vitesse_gaz = true : vitesse en m/s |
| `get_throttle_factor` | SUPPOSÉ | ABSENT par defaut (cas majoritaire du journal du 28/10 : '-' dans 96 % des lignes, numerique dans 4 % : contexte inconnu) ; avec jeu.avec_vitesse_gaz = true : gaz 0..1 |
| `get_fuel_factor` | DOC | carburant restant 0..1 (annexe B) |
| `get_ammo_factor` | SCRIPT | munitions 0..1 |
| `get_waypoint_count` | SCRIPT | nombre de waypoints en file |
| `get_is_fuel_blocked` | SCRIPT | bool |
| `get_is_ammo_blocked` | SCRIPT | bool |
| `get_is_visible` | DOC | faux si le vehicule est cache par le brouillard (doc 07) |
| `clear_waypoints` | DOC | vide la liste des waypoints |
| `clear_attack_target` | DOC | sans effet visible ici |
| `add_waypoint` | DOC | ajoute un waypoint (x, z) et RENVOIE son numero (notes : `local wp = v:add_waypoint(..)` puis `set_target_vehicle(wp, ..)`, teste en jeu le 25/10) |
| `set_target_vehicle` | DOC | attache le waypoint a un vehicule (rappel = waypoint sur le porte-avions + cible) |

## lua du jeu

| Nom | Statut | Ce que fait la fausse version |
|---|---|---|
| `color8` | SCRIPT | color8(r, g, b, a) -> table {r, g, b, a} (le vrai type est inconnu ; les scripts ne font que le transmettre). Disponible des le chargement des fichiers (les onglets carburant l'appellent au chargement) |
| `e_game_object_type` | DOC | carrier 0, Albatros 8, Manta 10, Razorbill 12, Petrel 14 (partage_detail/08) |
| `e_active_input` | SUPPOSÉ | { keyboard = 0, gamepad = 1 } |
| `atlas_icons` | SUPPOSÉ | { column_pending = 1 } |
| `print` | DOC | le jeu jette stdout ; le banc le capture dans ctx.prints |

## dessin

| Nom | Statut | Ce que fait la fausse version |
|---|---|---|
| `update_ui_get_text_size` | SUPPOSÉ | (texte, largeur, indicateur) -> 5 * #texte, 9 (meme doublure que tests/test_horloge.py ; la vraie police est inconnue) |
| `update_ui_text` | SCRIPT | (x, y, texte, largeur, alignement, couleur, ?) : enregistre le texte dans ctx.dessin.textes ; types verifies comme le ferait une liaison C |
| `update_ui_rectangle` | SCRIPT | (x, y, w, h, couleur) : enregistre le rectangle dans ctx.dessin.rects |
| `update_ui_rectangle_outline` | SCRIPT | (x, y, w, h, couleur) : enregistre le contour |

## evenements

| Nom | Statut | Ce que fait la fausse version |
|---|---|---|
| `update_ui_event` | DOC | (nom, arguments...) : enregistre l'evenement dans jeu.evenements ; AUCUN effet de jeu n'est simule (la partie ne se charge pas) ; nom inconnu = avertissement |
| `update_set_host_password` | SCRIPT | (texte) : memorise le mot de passe d'hebergement dans jeu.mot_de_passe_hote (boite aux lettres du script d'essai auto) |

## temps

| Nom | Statut | Ce que fait la fausse version |
|---|---|---|
| `update_get_time_since_epoch` | DOC | secondes reelles (flottant) ; SUPPOSE : depuis 1970 |

## monde

| Nom | Statut | Ce que fait la fausse version |
|---|---|---|
| `update_get_logic_tick` | DOC | tick de simulation entier, 30 par seconde de jeu ; present dans les ecrans de bord |
| `update_get_map_vehicle_count` | DOC | nombre de vehicules de la carte (y compris caches par le brouillard) |
| `update_get_map_vehicle_by_index` | DOC | poignee du i-eme vehicule, i de 0 a count-1 ; hors limites : poignee dont get() est faux (SUPPOSE) |
| `update_get_map_vehicle_by_id` | DOC | poignee du vehicule d'identifiant id ; get() faux s'il n'existe pas |
| `update_get_screen_vehicle` | DOC | le vehicule de l'ecran (le porte-avions) ; get() faux s'il n'y en a pas |
| `update_get_screen_team_id` | DOC | equipe de l'ecran (= celle du joueur) |
| `update_get_peer_count` | SCRIPT | nombre de joueurs (pairs) de la partie ; utilise par tour/auto sous pcall |
| `update_get_peer_team` | SCRIPT | equipe du i-eme pair (i a partir de 0) |
| `update_get_is_focus_local` | DOC | vrai si le joueur local est sur cet ecran (partage_detail/07) ; toujours vrai ici (SUPPOSE) |
| `update_get_active_input_type` | SCRIPT | e_active_input courant ; e_active_input.keyboard par defaut (reglable : ctx.entree) |

## menu (frontend)

| Nom | Statut | Ce que fait la fausse version |
|---|---|---|
| `update_get_save_slots` | DOC | liste de { slot_index, display_name, save_name, time } (partage_detail/07) |
| `update_get_mod_details` | DOC | liste de { id, is_enabled, manifest = { name } } (tour/etudes_demarrage_auto/ETUDE.md section 2) ; relue a chaque appel, donc un scenario peut cocher/decocher un mod en cours de route (SUPPOSE : le vrai menu des mods se comporte ainsi) |
| `update_get_join_password` | DOC | mot de passe de connexion, partage par TOUS les contextes (jeu.mot_de_passe_connexion) ; "" au depart (SUPPOSE) |
| `update_set_join_password` | DOC | change ce mot de passe commun (verrou entre contextes) |

## overlay

| Nom | Statut | Ce que fait la fausse version |
|---|---|---|
| `update_set_is_visible` | SCRIPT | (bool) : memorise la visibilite de la couche dans ctx.visible |

## ecran

| Nom | Statut | Ce que fait la fausse version |
|---|---|---|
| `begin_get_screen_name` | DOC | nom de l'ecran (ex. screen_veh_m) ; absent de l'ecran de pilotage (partage_detail/07) |

## cc2x

| Nom | Statut | Ce que fait la fausse version |
|---|---|---|
| `has` | DOC | vrai si un plugin a enregistre la fonctionnalite (ici : "modes" quand le plugin est charge) |
| `log` | DOC | ecrit ses arguments (separes par une espace, SUPPOSE) sur UNE ligne de cc2x.log ; 900 caracteres au plus (VERDICT_relecture_SDK.md : lua_world.c) : la fausse version REFUSE le depassement (avertissement + ligne tronquee) |
| `vehicles` | DOC | tableau de TOUS les vehicules du serveur (LUA_API.md : sans argument). En 0.5 le banc SUPPOSE qu'un argument numerique filtre par equipe (library_custom_3 le suppose) ; opts.equipe_ignoree=true montre le cas contraire |
| `vehicle` | DOC | un vehicule ou nil |
| `tiles` | DOC | tableau des tuiles (vide ici : aucun script du depot ne s'en sert) |
| `tile` | DOC | une tuile ou nil (toujours nil ici) |
| `tick` | SCRIPT | tick logique du serveur (entier) ; absent de la doc 0.4.0, appele par library_custom_3.lua ; SUPPOSE identique a update_get_logic_tick |

## cc2x.modes (plugin v3)

| Nom | Statut | Ce que fait la fausse version |
|---|---|---|
| `set` | DOC | LU dans cc2x_modes.c : set(id, mode), id entier 1..0x7fffffff, mode 0 NORMAL / 1 ECO / 2 FLANK -> true ; sinon false (arguments faux ou table pleine : 64 avions) |
| `get` | DOC | get(id) -> mode demande (0..2), actif (0 rien / 1 ECO / 2 FLANK : ce qui est ecrit en ce moment), tenu (bool) ; nil si id invalide |
| `hold` | DOC | hold(id) : "le joueur pilote cet avion", le plugin lache les gaz pendant 90 ticks (3 s) ; -> true, false si id invalide |
| `status` | DOC | status() -> { version = 3, enabled, eco_cap_light, eco_cap_heavy, flank_floor_light, flank_floor_heavy } |

## g_ui

| Nom | Statut | Ce que fait la fausse version |
|---|---|---|
| `begin_window` | SCRIPT | empile une fenetre (titre, x, y, w, h, icone, flag, niveau) sur window_stack ET region_stack (SUPPOSE) ; contenu a x+2, y+12 |
| `end_window` | SCRIPT | depile la fenetre ET sa region ; erreur si la pile est vide |
| `get_window` | SCRIPT | fenetre du dessus (cx, cy = curseur de mise en page en coordonnees d'ecran, is_active) |
| `get_region` | SCRIPT | largeur utile de la region courante (nombre) |
| `hoverable` | SCRIPT | vrai si le pointeur du banc est dans le rectangle (x, y, w, h) ; 5e argument ignore |
| `spacer` | SCRIPT | descend le curseur de mise en page de n unites |
| `text_basic` | SCRIPT | ecrit une ligne (texte, couleur1, couleur2) dans la fenetre et descend de 11 unites (SUPPOSE) |


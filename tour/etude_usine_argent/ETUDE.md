# Tourelle-usine qui produit de l'argent — note d'état (29/10/2026, étude arrêtée avant sa rédaction complète)

## 1. Objectif
Le moddeur veut une nouvelle tourelle qui serait en fait une usine et produirait de l'argent à long terme.

## 2. Déjà établi (LU = lu dans un fichier · INFÉRÉ = déduit, à vérifier · MESURÉ = rien : le jeu n'a jamais été lancé)
- LU « Argent » = les **devises** de l'équipe : `team:get_currency()`, comptes par jour (`rom_0/scripts/screen_currency.lua` l.25-27, 59-91, 97). Gains : capture d'îles, contrôle d'îles (« lentement »), destruction d'ennemis ; dépense : fabrication (`rom_0/locale/localization.csv` l.1050-1053).
- LU Les coûts sont dans `constants.txt` (tourelles posables 1000 / 1250 / 1500, l.162-164 ; 60 s). Les **revenus** n'y sont pas (308 constantes du fichier + 6 cachées sans lien, lecture de l'exe). INFÉRÉ : revenus codés dans le programme.
- LU Tourelle posable = véhicule « tourelle stationnaire » (`game_objects/stationary_turret.xml`, 1 emplacement), 3 articles n° 55-57 posés sur des emplacements fixes de l'île (`screen_vehicle_control.lua` l.512-517, 3058-3075 ; `library_enum.lua` l.2079-2085).
- LU La liste des objets est figée (102 types, 61 articles : `library_enum.lua` l.12-117 et 2027-2087) ; leurs noms de fichiers sont en dur dans l'exe (copie d'origine `tour/sauvegardes/carrier_command_1.5.18_original.exe`, offset 0x965edc). INFÉRÉ : un nouveau type par XML seul est impossible.
- LU Le Lua ne peut pas créditer l'argent (seulement `get_currency*`, exe 0x972328 ; `partage_detail/07_lua_api_and_hooks.txt` l.49). Il peut compter les tourelles, renommer, afficher.
- LU Les mods Workshop installés ne créent aucun type : Revolution change `stationary_turret.xml` (tourelle à roues), Tactical Ops ajoute écrans et emplacements au porte-avions. Fil Steam des moddeurs (Bredroll 2023-2024) : pas de nouveaux types ; il dit aussi « coûts non modifiables », contredit par `partage_detail/08_constants_and_multiplayer.txt` §1 (temps de production ×0,5 noté « works » sur Mac, non refait sur la tour).
- LU Mod = envoyé aux joueurs qui rejoignent ; patch exe et DLL = hôte seulement (`08_…` §3 ; `tour/etudes_modes_carburant/ETUDE.md` §3.5). Jamais testé avec de vrais joueurs.
- LU Un compte d'argent fait 28 octets (id, début, fin, 4 sources), lu en 0x5a9d30 de la copie d'origine de l'exe.

## 3. Pistes et risque
- 🟢 Baisser les coûts / durées dans `constants.txt` (mod) : « argent plus facile » sans nouvel objet. Il remplace tout le fichier : fusionner avec `pack_moddeur` s'il est actif.
- 🟢 Plus d'îles de départ (réglage de nouvelle partie, `screen_menu_main.lua` l.1126) : INFÉRÉ plus de revenu.
- 🟢 Mod Lua : renomme l'une des 3 tourelles « Usine » et compte les usines ; ne verse rien.
- 🟡 Patch exe : multiplier le revenu des îles (fonction non localisée) ; hôte seulement.
- 🟡 Plugin DLL (chargeur maison) : compte les tourelles-usines et appelle la fonction interne d'ajout ; effort L ; hôte/solo ; INFÉRÉ à régler après mesure : ~25 par minute de jeu, plafond ~6 usines par équipe.
- 🔴 Écrire le solde en mémoire à l'aveugle (désynchro, plantage) : déconseillé. Nouvel objet par XML : non.

## 4. PAS examiné
La fonction d'ajout d'argent dans l'exe (un balayage rapide n'a rien donné) · le revenu réel des îles (jamais mesuré, seulement des anecdotes Steam) · le sort d'une usine si l'île est perdue · les emplacements (« markers ») de tourelles · l'effet réel de `constants.txt` sur les coûts des tourelles · Island Airfields et « Island turret placement QoL » (non installés) · sauvegardes et `mods.xml` (interdits) · la mise à jour Steam du 28/10 21:30 a recompilé l'exe : mes adresses (exe d'origine du dépôt) sont à revérifier.

## 5. Prochaine action et décision
- Action : mesurer le revenu actuel, sans aucun fichier : écran « Rapport de devises » (`screen_inv_top_r`), noter le solde toutes les 5 min sur 30 min sans rien dépenser.
- Décision à demander au moddeur : « On commence par cette mesure (aucun risque, rien de touché) ? oui / non »

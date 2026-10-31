# Enregistreur de carte (CC2MAP) : consignes pour la conversation de la tour

À lire en entier avant de toucher à quoi que ce soit. Écrit par le Mac le 27/10/2026. **Rien de ceci n'a encore tourné dans le vrai jeu** : le script a seulement été essayé dans un faux jeu, sous Lua 5.1, 5.3 et 5.4.

## Règles du moddeur (rappel)
- Aucun risque inutile. Pour chaque action : ce qu'elle fait, le risque (🟢 / 🟡 / 🔴), une alternative plus sûre.
- Un accord séparé pour chaque installation, chaque fichier du jeu modifié et chaque lancement ou fermeture du jeu.
- Français simple, une seule question à la fois, finir par la prochaine action concrète.
- **Le Mac ne modifie pas `tour/`** : tout ce que tu produis reste de ton côté.

## À quoi ça sert
Le moddeur veut rejouer une de ses parties en timelapse sur une carte (page `carte_rejeu.html`, sur le Mac). Il faut donc un fichier qui note, pendant la partie, la position de toutes les unités de toutes les équipes, des missiles et des îles. Le script `cc2map_enregistreur.lua` fait ça, en **lecture seule** : il appelle `cc2x.vehicles()`, `cc2x.tiles()` et `update_get_missile_*` et écrit par `cc2x.log(...)`. Il n'utilise ni `io`, ni `os`, ni réseau, ni `load`, et ne change rien dans le jeu. Il ne fait rien si CC2X (api ≥ 4) n'est pas là.

## Étapes (une à la fois, avec l'accord du moddeur à chaque fois)
1. **Relire le script en entier** (122 lignes) et le dire au moddeur : ce qu'il lit, ce qu'il écrit. Vérifier sa structure avec `verifier_blocs_lua.py` et, si possible, le charger dans `lua_sonde.py` (Lua 5.1). 🟢
2. **Vérifier l'état du SDK** (lecture seule) : `dinput8.dll` CC2X **0.5.0** présente dans le dossier du jeu ? (l'étude d'atterrissage l'a posée en « phase 1 »), `cc2x.log` présent et à jour ? Si la DLL n'est pas là : on s'arrête et on demande au moddeur, pas d'installation de ton propre chef. 🟢
3. **Installer comme mod local** `cc2_carte` (même méthode que `cc2_mesures` : `mod.xml`, `thumbnail.png`, `content/scripts/library_custom_N.lua`, ligne ajoutée dans `mods.xml` avec sauvegarde datée). Prendre un `N` libre (le Mac propose **6** ; vérifier qu'aucun mod actif ne l'utilise). Accord requis. 🟡
4. **Le moddeur lance une partie NEUVE** (pas de chargement de sauvegarde : le chargement plante le jeu sur la tour) et joue une dizaine de minutes en gardant un écran de contrôle des véhicules ou la table holographique allumé. Accord requis pour tout lancement par toi.
5. **Contrôle après 1 minute** : `cc2x.log` doit contenir des lignes `CC2MAP|H|`, `CC2MAP|V|` et `CC2MAP|T|`. Si aucune ligne `V` : l'écran choisi n'est pas mis à jour ; essayer d'autres noms d'écran (liste `SCREENS` en haut du script).
6. **À constater et noter dans ton journal** (ce sont les inconnues) :
   - le préfixe que `cc2x.log` ajoute devant chaque ligne ; la page le supporte, elle cherche `CC2MAP|` n'importe où dans la ligne ;
   - les lignes (jusqu'à 270 caractères) sont-elles coupées ? le fichier est-il tronqué ou renouvelé ? vidé à chaque lancement ?
   - `cc2x.vehicles()` contient-il bien **les unités ennemies hors de vue** et les avions rangés au hangar (la doc du SDK le promet) ?
   - les lignes `CC2MAP|M|` apparaissent-elles quand un missile est tiré ? `m:get_id()` existe-t-il (identifiants stables) ?
   - le jeu ralentit-il ? (le script lit 120 unités toutes les 10 s par écran : très léger, mais à mesurer avec l'affichage SIM).
7. **Récupérer le résultat sans rien d'autre** : ne pas envoyer `cc2x.log` entier (il peut contenir des chemins du Mac ou de la tour). Extraire seulement les lignes utiles :
   `findstr "CC2MAP" cc2x.log > carte_partie.log`
   puis donner `carte_partie.log` au moddeur, qui le charge dans la page.
8. **Retrait** : supprimer le mod et restaurer `mods.xml` depuis la sauvegarde datée.

## Format (version 1)
```
CC2MAP|H|<tick>|1                                  début de session
CC2MAP|V|<tick>|<p>/<n>|id,def,équipe,x,z,cap;…    unités (toutes équipes), toutes les 10 s
CC2MAP|T|<tick>|<p>/<n>|id,équipe,x,z;…            îles, toutes les 60 s
CC2MAP|M|<tick>|<p>/<n>|id,def,équipe,x,z;…        missiles, toutes les 0,5 s tant qu'il y en a
```
x, z en mètres ; cap en degrés (0 = vers +z, sens horaire) ; tick du serveur (30 par seconde) ; une ligne = au plus 10 éléments ; `p/n` = partie p sur n.
Volume mesuré dans le faux jeu : environ 1,4 Mo par heure et par écran enregistreur ; deux écrans = le double (la page supprime les doublons).

## Limites connues
- Les écrans du jeu ne sont mis à jour que s'ils sont actifs : sans joueur devant la table ou un écran de contrôle, il peut manquer des instantanés. D'où plusieurs écrans dans `SCREENS`.
- Hors partie hébergée ou solo, les listes de CC2X sont vides.
- Les vraies côtes des îles ne sont pas enregistrées (v2 possible avec `cc2x.raycast`).

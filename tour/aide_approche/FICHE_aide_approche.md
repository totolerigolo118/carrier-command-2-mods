# Aide à l'approche : des portes pour atterrir à la main (2/11/2026)

**État : écrit et vérifié hors jeu (syntaxe). Jamais lancé dans le jeu. Rien posé dans `%APPDATA%`.**

## Ce que ça affiche

Quand tu pilotes **à la main** un avion (ou un hélico) à moins de 1500 m de ton porte-avions, le HUD de l'appareil montre :

- **6 rectangles (« portes »)** à 100, 200, 300, 450, 600 et 800 m derrière le point de toucher, posés sur la pente de 0,14 (≈ 8°) que vise l'IA. Cyan = simple repère.
- **La prochaine porte devant toi** est en double trait et prend la couleur du verdict :
  - **vert** : dans l'axe (±12 m), à la bonne hauteur (±10 m), vitesse relative au navire ≤ 30 m/s ;
  - **orange** : un des trois est hors tolérance ;
  - **rouge** : trop vite (> 36 m/s par rapport au navire).
- **Un texte en haut au centre** : `APPROACH  LAT +3  HEIGHT -5  SPD 34 SPEED` (écart latéral en m, écart de hauteur en m, vitesse relative en m/s, puis ce qui est hors tolérance : AXIS, HEIGHT, SPEED).

Les portes disparaissent quand tu as dépassé le point de toucher de 160 m.

## Réglages

Tout est dans le bloc `AP` en haut de `mod/content/scripts/library_custom_2.lua` : point de toucher (`z_toucher = -50`), pente, distances des portes, taille, tolérances, vitesses. Je les ai déduits des données (nœuds de piste z −68 / +82, pont y ≈ 20, pente de l'IA ≈ 0,14) : **à ajuster en jouant**.

## À vérifier au premier essai (hypothèses non prouvées)

1. L'origine du navire (`get_position`) est bien le repère des nœuds de piste : sinon les portes seront décalées en hauteur ou en longueur (régler `y_pont` / `z_toucher`).
2. Le signe de l'écart latéral (« + » = à droite du navire) : si c'est inversé, le chiffre seul est inversé, les portes restent justes.
3. Les portes s'affichent bien en transparence dans le HUD, pas seulement à l'écran de contrôle.
4. Les inclinaisons du navire (tangage, roulis) sont ignorées : léger écart par mer agitée.

## Installation (à ne faire qu'avec ton « oui », jeu fermé)

- **Ce que ça fait** : copie le dossier `mod` (1 fichier Lua + `mod.xml`) dans `%APPDATA%\Carrier Command 2\mods\aide_approche`, puis ajoute une ligne dans `mods.xml`.
- **Risque : 🟢 faible.** Aucun exécutable, aucune DLL, aucun réseau, aucune écriture hors de l'affichage. Au pire une erreur est avalée et les portes n'apparaissent pas.
- **Emplacement Lua** : `library_custom_2.lua`, libre. Déjà pris : 1, 4, 7, 9 (`cc2_mesures`), 3 et 5 (`cc2_modes`), 6 (`cc2_carte`) ; 7 et 8 par `camera_libre` / `boite_noire` (inactifs). Ne pas activer un mod qui utilise aussi le 2.

Ligne à ajouter dans `%APPDATA%\Carrier Command 2\mods.xml`, dans `<active_mod_folders>` :

```xml
<path value="C:\Users\UTILISATEUR\AppData\Roaming\Carrier Command 2\mods\aide_approche"/>
```

## Retrait

Supprimer cette ligne de `mods.xml` (le dossier peut rester ou être effacé).

## Vérification faite

`python -I tour/outils/lua_syntaxe.py tour/aide_approche/mod/content/scripts/library_custom_2.lua` : 0 erreur. `lua_inconnus.py` : seuls deux noms « inconnus », ce sont mes propres variables globales.

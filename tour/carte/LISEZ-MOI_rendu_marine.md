# Rejeu « carte marine » (rendu choisi le 28/10/2026)

Le rejeu de la page du Mac (`carte_timelapse/carte_rejeu.html`), avec un autre affichage : **carte marine** (îles hachurées, cadre
gradué au km, échelle, rose des vents), **couleurs du radar tactique** (fond noir, équipe 1 cyan, équipe 2 rouge, IA des îles ambre),
**pictos du jeu** pour toutes les unités (Albatros, Manta…), petits pour rester nets. Tout se fait en local, sur la tour.

## Ce que ça change par rapport à la page du Mac
- **Équipe 1 seule par défaut** ; le bouton « IA des îles » (panneau « Afficher ») affiche aussi les autres.
- **Plus d'étiquettes « +N MIN »** sur la route du porte-avions (elles s'empilaient). Il reste l'horloge et les heures du journal.
- **Unités sur le pont** (à moins de 120 m de leur porte-avions) : non dessinées, seul le porte-avions l'est. Le compteur « Forces » les compte.
- **Fausses pertes de l'IA** : quand 8 unités de l'IA ou plus disparaissent d'un coup, c'est le jeu qui décharge une île, pas une destruction : non comptée.
- Un bouton par partie, la dernière se charge toute seule. Seules les lignes `CC2MAP|` des journaux sont lues.

## Fabriquer la page
1. Récupérer le dossier du Mac (lecture seule, ne modifie rien) :
   ```
   git fetch origin
   git archive origin/mac-carte-enregistreur carte_timelapse | tar -x -C <dossier neuf et vide>
   ```
2. Construire (le script refuse d'écraser une sortie existante) :
   ```
   python -I tour/carte/fabriquer_marine.py <dossier neuf>/carte_timelapse <sortie>/carte_marine.html ^
     "Partie 1 (20 min)=tour/carte/carte_partie_2026-10-27.log" "Partie 2 (11 min, missiles)=tour/carte/carte_partie_2026-10-27_2.log"
   ```
3. Ouvrir `carte_marine.html` dans **Chrome** (double-clic ou glisser-déposer). Pas de serveur nécessaire.

La page reproduite à partir de ces sources a été comparée (sha256) à celle qui a été regardée : identique.

## Fichiers
- `dessin_marine.js` : tout le rendu (fond, cadre, îles, routes, unités, infobulles).
- `fabriquer_marine.py` : prend le modèle du Mac, applique les changements (chaque remplacement vérifie qu'il trouve son motif une seule fois), insère le rendu, les journaux et les pictos.
- Les journaux de parties, le diagnostic et `cc2map_enregistreur_diag.lua` sont dans ce même dossier.

## À ne pas faire
**La page produite contient les pictos et la police du jeu : usage personnel. Ne pas la partager, ne pas la commiter** (voir
`carte_timelapse/NE_PAS_PARTAGER.txt` côté Mac). Ne la fabriquer qu'hors du dépôt.

## Vérifié / pas vérifié
- Vérifié : page chargée dans le navigateur intégré (moteur Chromium) sur la partie 2 à 0:00, 7:50 et 9:09, sans erreur dans la console ; icônes, trace du porte-avions, un missile de l'équipe 1.
- Vérifié aussi : la bascule « IA des îles » (partie 2 : 19 → 91 unités, 12 → 19 événements, sans erreur dans la console).
- Pas regardé : la partie 1 dans ce rendu, et l'aspect visuel avec l'IA affichée. Safari n'est pas visé (tout se fait ici, dans Chrome).
- Défauts connus : le nom « Porte-avions » peut chevaucher un nom d'île voisin. Avec l'IA affichée, 4 lignes « perd … » de l'IA restent dans le journal de la partie 2 (groupes de moins de 8 unités, pas contrôlés : certains peuvent être des îles déchargées).

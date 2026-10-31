# Carte holographique de CC2 : rejeu d'une partie (27/10/2026)

**But** : voir toute la carte (îles, porte-avions, unités des équipes 1, 2 et de l'IA des îles, missiles) et rejouer une partie en timelapse, dans le style de la table holographique du jeu. Équipe 1 = bleu clair, équipe 2 = jaune, IA des îles = rouge.

## Les fichiers
| Fichier | Rôle |
|---|---|
| `carte_rejeu.html` | **la page à ouvrir dans Safari**. Bouton Démo, ou « Charger un enregistrement » (ou glisser-déposer). Facultatif : charger aussi une sauvegarde `save.xml` pour la vraie taille des îles. |
| `enregistreur/cc2map_enregistreur.lua` | le script qui enregistre pendant la partie (à poser sur la tour, voir `enregistreur/LISEZ-MOI_tour.md`) |
| `enregistreur/essai_enregistreur.py` | banc de test hors jeu (faux jeu + lupa) : `python3 -I essai_enregistreur.py scenario_demo.json cc2map_enregistreur.lua sortie.log --lua53` (aussi `--lua51`, `--lua54`, `--doublon`) |
| `enregistreur/fabriquer_rejeu.py` + `modele_rejeu.html` + `police_lanapixel.css` | reconstruisent `carte_rejeu.html` |
| `maquette_carte_cc2_holo.html`, `maquette_carte_cc2.html` | les deux séries de maquettes (le look 1 de la 2e a été choisi) |
| `icones/` | pictos extraits du jeu de base : **usage perso, ne pas partager** (voir `NE_PAS_PARTAGER.txt`) |
| `sources_maquette/` | de quoi refaire la maquette holographique (vérifié le 27/10 : même fichier, octet pour octet) : `python3 -I sources_maquette/fabriquer_maquette3.py <save.xml> sources_maquette/carte_tpl5.html <dossier>/maquette.html`. Il lit les pictos dans `<dossier>/icones/` et écrit `<dossier>/enregistreur/scenario_demo.json` (créer ces deux dossiers). Il faut un `save.xml` du jeu, non fourni. La 1re série de maquettes (`maquette_carte_cc2.html`) est là telle quelle, sans ses sources. |
| `TEXTE_POUR_LA_TOUR.md` | le texte à coller dans une conversation neuve sur la tour |

## Utiliser la page
Ouvrir `carte_rejeu.html` dans Safari. ▶ lance le rejeu ; la barre de temps se clique et se fait glisser (traits colorés = événements) ; ×1 à ×600 = vitesse de rejeu ; survoler une unité la nomme. Le journal se remplit tout seul : salves de missiles, unités perdues, îles qui changent de camp. La courbe montre la distance entre les deux porte-avions.

## Ce qui est vérifié, ce qui ne l'est pas
- **Vérifié hors jeu** : l'enregistreur sous Lua 5.1, 5.3 et 5.4 (même résultat) ; la page sur un faux enregistrement de 10 minutes (61 instantanés, 18 missiles, routes, distance 21,5 → 7,0 km) ; doublons de deux écrans retirés ; perte d'une unité et prise d'une île détectées ; deux parties à la suite ; journal avec lignes parasites.
- **Jamais essayé dans le vrai jeu** : comportement de `cc2x.log` (préfixe, coupure, taille), écrans réellement mis à jour, lecture des missiles, présence des unités cachées. Le premier vrai enregistrement dira.
- **Heuristiques** : un missile est dit « arrivé sur cible » s'il finit à moins de 650 m d'une unité ennemie ; un autre cas est « perdu ou intercepté ». Une unité absente de l'instantané suivant est dite « perdue ».
- Formes d'îles indicatives. Zones de vision : pas encore.

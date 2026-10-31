# Plugin « plafond de gaz » (ÉCO) : ce que c'est, les risques, comment le poser et le retirer

Préparé le 28/10/2026, **hors du jeu**. Rien n'est posé : ni dans le jeu, ni dans `%APPDATA%`, ni dans `mods.xml`.

## En une phrase

Un petit programme (`cc2x_modes.dll`, 216 Ko, écrit par nous, code source relu dans `cc2x_modes.c`) que le jeu charge au lancement
depuis notre mod `cc2_modes`. **Il commence par observer** (il lit la commande de gaz de tes avions et l'écrit dans `cc2x.log`),
et **seulement sur ton accord** il baisse cette commande à un plafond (0,65 par défaut) pour les avions en ÉCO.

## Ce qui est déjà fait et vérifié (🟢, hors jeu)

- Le code est compilé avec Zig (comme le plugin de frein), deux fois, avec le même résultat ; la DLL n'importe **aucune** fonction réseau,
  de lancement de programme, de fichiers autre que la lecture de `modes.ini` ; aucune chaîne suspecte (`RAPPORT_compilation.md`).
- **38 contrôles automatiques réussis** sur un faux jeu : n'écrit jamais en mode observation ; plafonne seulement les avions listés et seulement
  l'excès ; ne touche jamais une équipe de l'IA, un hélicoptère, un avion au sol, rattaché, en file d'atterrissage, à moins de 1 500 m de
  son porte-avions ou sans porte-avions ; ignore les valeurs absurdes (NaN, > 1) ; relit les réglages toutes les 3 s ; refuse de se charger sur une autre version du jeu,
  ou si les 8 octets de code du jeu qu'on lui a décrits ne sont pas exactement ceux attendus.
- L'outil de pose est essayé sur une fausse copie (pose, 2e pose refusée, retrait, `mods.xml` identique).

## Ce qui n'est PAS prouvé

1. **Que le champ qu'on lit/écrit (octet 0x314 de l'avion) est bien la commande de gaz.** C'est ce que dit le désassemblage de la fonction
   de pilotage des ailes (une commande bornée de 0 à 1, à côté de trois commandes bornées de −1 à 1 : tangage, roulis, lacet), mais ce n'est
   pas encore vu en jeu. **C'est exactement le rôle de l'étape A (observation).**
2. Que le jeu **obéit** à la valeur baissée : la vitesse devrait se stabiliser vers 90 m/s à 0,65 et le carburant tomber vers 0,20 par seconde (Albatros).
3. Que l'IA se comporte bien à vitesse réduite (virages, montée, combat : à 0,65 de gaz l'Albatros n'a presque pas de réserve de poussée).

## Les risques, par étape

| Étape | Ce que ça fait | Risque | Pourquoi | Comment on s'en protège |
|---|---|---|---|---|
| **P : poser le fichier** | copie `cc2x_modes.dll` dans `…\mods\cc2_modes\content\cc2x\` (jamais dans le dossier du jeu) ; `mods.xml` ne change pas | 🟢 | un fichier de plus dans un dossier de mod à nous | `retirer-plugin` ; l'outil refuse si le jeu tourne |
| **A : lancer le jeu avec le plugin, en observation** | le plugin est chargé et **lit** un nombre par avion toutes les 5 s ; n'écrit rien dans le jeu | 🟡 faible | du code natif tourne dans le jeu avec tes droits ; un bogue dans NOTRE code peut faire planter le jeu (lecture d'un pointeur invalide) ; rien d'autre n'est modifié | partie neuve jetable ; 38 tests ; vérification du code du jeu avant chargement ; retrait en supprimant un fichier |
| **B : activer le plafond** (`eco_enabled=1` dans `modes.ini`, avec ton accord, une fois A validée) | écrit un nombre (≤ 0,65) dans le champ de gaz des avions en ÉCO, à chaque tick | 🟡 moyen | si le champ n'était pas le gaz, on écrirait au mauvais endroit (comportement bizarre, au pire plantage) ; un avion plafonné peut décrocher ou perdre de l'altitude en virage serré ou en montée | A d'abord (on compare avec les gaz mesurés) ; plafond ≥ 0,55 ; zone libre de 1 500 m autour du bateau ; **un seul avion d'abord** ; `eco_enabled=0` coupe en 3 s, même jeu ouvert |

**Niveau global : 🟡** (du code natif dans le jeu). **Pas de risque pour tes sauvegardes** : on n'y touche pas, et on ne joue ces essais que sur une
**partie neuve jetable**. Pas de risque de fuite : aucun accès réseau (imports vérifiés).

## Alternatives plus sûres

- Rester à la maquette (🟢) : l'onglet « sans effet » est déjà posé ; on peut le regarder encore sans rien de plus.
- Étape A seule (observation) et s'arrêter là : on saura si le champ est le bon sans jamais rien écrire.
- Mod de données (`constants.txt`) : baisser la consommation de tous les avions (🟢, retirable) : pas de modes ni de vitesse plus basse.

## Poser, essayer, retirer (quand tu diras oui)

```bash
python tour/etudes_modes_carburant/mod_modes.py poser-plugin      # jeu fermé ; copie la DLL dans le mod cc2_modes
python tour/etudes_modes_carburant/mod_modes.py etat              # doit dire : plugin cc2x_modes.dll conforme
python tour/etudes_modes_carburant/mod_modes.py retirer-plugin    # jeu fermé ; supprime ce seul fichier
```

Réglages : `%APPDATA%\Carrier Command 2\cc2x\modes.ini` (modèle : `modes.ini.example`). **Sans fichier : observation seulement.**
Le fichier est relu toutes les 3 s : on peut l'écrire ou le changer jeu ouvert ; ce sera fait avec ton accord à chaque fois.

Ce que le plugin n'a pas encore : **FLANK** (non programmé : il demande de relever la vitesse visée par l'IA, étape 3a) et le **lien avec l'onglet SPEED**
(pour l'instant ÉCO se choisit par numéro d'avion dans `modes.ini`).

# Plugin v8 « prise en charge au sol » : ce que c'est, les risques, comment tout couper (29/10/2026)

*Pour le moddeur. Rien n'est posé : cette page décrit ce qui serait posé si tu dis oui.*

## En deux phrases
Tu poses l'avion à la main, le frein l'arrête (comme aujourd'hui). Au bouton de retour, le jeu ne reprenait pas l'avion parce qu'il le croit « en vol, en file d'attente ». La v8 fait croire au jeu, **pour cet avion seulement**, qu'il vient de passer le portillon d'entrée : le jeu lui donne alors lui-même la piste, valide le toucher et fait le reste (recul sur les rails, ascenseur, hangar, ravitaillement).

## Ce que font les deux crochets
Ce sont deux petits morceaux de code que le plugin place dans la fonction du jeu qui gère l'atterrissage des avions sur le porte-avions (adresses de l'**ancien exe** : `0x7018ce` et `0x701a3d`). Ils ne s'activent **que** si tout ceci est vrai en même temps : `recall_force=1`, l'avion est celui que le plugin tient au frein depuis au moins 1 s après le rappel, il est immobile, et c'est lui que le jeu est en train de traiter.
- **Crochet 1** : au moment où le jeu lit « où en est cet avion dans la file », il lui montre « il a passé le portillon » (au lieu de « début du tour »). On ne modifie **pas** la file du jeu : on lui montre une copie.
- **Crochet 2** : le jeu vérifie ensuite que l'avion est à moins de 1 000 m du portillon ; ton avion posé est à ~1 200 m. Le crochet saute ce seul test. Le jeu a déjà vérifié avant que le porte-avions est en mode accostage et que la piste est libre ; le crochet vérifie encore ces deux points avant d'agir.
Ensuite c'est **le code du jeu** qui écrit « piste donnée à cet avion », passe en approche finale, valide le toucher (avion lent, roues au sol, baie libre) et exécute la prise en charge.

## Ce que ça touche
- **Dans le jeu en marche** : seulement ces deux endroits de code, et seulement si `recall_force=1` **au démarrage du jeu**. Avec `recall_force=0` (réglage par défaut) les crochets ne sont **même pas posés** : la v8 se comporte alors comme la v7.
- **Sur le disque** : rien de plus que la v7 (la DLL `cc2x_frein.dll` dans le dossier du jeu et `frein.ini`). L'exe n'est pas modifié.
- Le plugin n'écrit **rien** dans la mémoire interne du jeu (ni la file, ni le gestionnaire). Il continue de tenir le frein et le moteur à 0 de l'avion tant que le jeu ne l'a pas pris en charge.

## Niveau de risque : 🟡 (moyen)
Parce que c'est du code ajouté dans une grande fonction du jeu, **jamais essayé en jeu**. Limites : un seul avion, 3 essais au plus (`force_tries`), 20 s au plus (`force_timeout_s`), aucun effet si l'on revient au réglage 0. Alternative plus sûre : ne rien poser et rester à la v7 (l'avion reste simplement tenu au frein).

## Ce qui peut mal tourner
1. **Le jeu plante** (mauvais endroit, ou le jeu ne s'attend pas à ça) : on perd la partie en cours (partie jetable). Les crochets vérifient les octets du jeu avant d'être posés (sinon ils ne se posent pas et la v8 devient une v7).
2. **Le jeu juge l'approche ratée** (angle de l'avion, pas de baie libre, avion trop près du bout de piste) et **remet l'avion en file d'attente** : il écrit alors « moteur à 1,0 et frein à 0 » **pendant un instant** (un tick, 1/30 s). Le plugin remet moteur à 0 et frein au maximum au tick suivant. Il y a donc un risque très court que l'avion bouge un peu ; il est tenu en 40 s de test, loin du bord.
3. **Rien ne se passe** (le porte-avions n'est pas en mode accostage, ou la piste est déjà prise) : le journal le dit (`manager mode`, `runway slot`), l'avion reste tenu au frein.
4. **L'avion est pris en charge mais fait autre chose que prévu** (recul vers le mauvais endroit) : à surveiller à l'écran ; couper avec les moyens ci-dessous.

## Comment tout couper
- **En quelques secondes, en jeu** : mets `recall_force=0` dans `frein.ini` (relu en 3 s) : les crochets ne font plus rien. Mets aussi `recall_hold=0` si tu veux que le plugin lâche l'avion (⚠ attention : lâcher le frein, c'est ce qui l'a fait reculer ; ne le fais que si l'avion est loin du bord).
- **Remonter dans l'avion** : le plugin lâche tout et te rend le moteur.
- **Jeu fermé** : remettre `recall_force=0` ; ou revenir à la v7 (`cc2-sdk-travail\dist_v7\cc2x_frein.dll`) ; ou `poser.py retirer` pour enlever le plugin.

## Ce que tu devrais faire à l'essai (partie neuve, ancien exe via `lancer_ancien.py`)
1. `recall_force=1` doit être dans `frein.ini` **avant** de lancer le jeu (je le règle, avec ta permission, jeu fermé). Je vérifie dans `cc2x.log` la ligne `recall_force=1: hooks H1 (0x7018ce) and H2 (0x701a3d) installed`.
2. Comme pour la v7 : navire ralenti, tu poses l'avion en dessous de 30 m/s relatifs, avec au moins 60 m de pont derrière ; le frein l'arrête ; tu le quittes ; tu attends 30 s.
3. Tu donnes l'ordre de retour et tu ne touches plus à rien pendant 40 s. Tu me dis ce que tu vois.
4. Dans le journal je cherche : `FORCE start`, `HOOK H1 shown circuit state 1 (real element state …, manager mode …, runway slot …)`, `HOOK H2 skipped the 1000 m test`, puis `dock=1` (accostage), `attached` ≠ 0, `dock=6`, `flight=1` (= le jeu a pris l'avion), puis l'avion qui quitte la zone vers l'ascenseur, enfin `dock=4` (rangé) et le carburant qui remonte. Sinon : `FORCE gave up` / `FORCE timeout`, et l'avion reste tenu.

## Ce qui reste inconnu (ne se tranche qu'en jeu)
l'état réel de l'avion dans la file au moment du rappel (le journal l'écrira) ; si le porte-avions est bien en « mode accostage » à ce moment ; s'il y a une baie libre ; si le jeu accepte le toucher d'un avion déjà immobile ; si un instant de poussée au tick d'abandon suffit à faire bouger l'avion.

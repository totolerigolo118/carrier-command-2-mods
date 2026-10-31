# Plugin v9 : ce qui change par rapport à la v8, risques, essai (30/10/2026)

*Pour le moddeur. Rien n'est posé : la v8 est toujours dans le jeu, éteinte. Ceci décrit ce qu'on poserait si tu dis oui.*

## Ce que l'essai de la v8 (30/10, 08:07) a montré
Les crochets ont marché : le jeu a donné la piste à l'avion 9 (`dock=1`). Mais le jeu a ensuite **abandonné l'approche à chaque tick**, en remettant à chaque fois la poussée à 1,0 et le frein à 0, et ma v8 lui redonnait la piste au tick suivant : **173 fois en 5 secondes**. La poussée écrite par le jeu a battu notre frein, l'avion a roulé, puis décollé. Le plafond de 3 essais n'a pas tenu, parce que l'abandon et la nouvelle donation de la piste se font **dans le même tick** du jeu, et ma v8 ne comptait qu'entre deux ticks.

## Ce que la v9 change
1. **Le plafond est compté dans les crochets.** Au début d'une fenêtre d'essai, le plugin ouvre un « budget » (`force_tries`, 3 par défaut). Chaque fois que le crochet 2 donne la piste, le budget baisse de 1 ; à 0, **les crochets 1 et 2 ne font plus rien**, quel que soit le nombre de ticks. Au pire, l'avion reçoit la poussée 1,0 du jeu pendant 3 ticks (3/30 s), puis le plugin le tient de nouveau.
2. **Un coupe-boucle.** Si, après une donation, l'avion revient dans la file d'attente avec l'état « 3 » (= le jeu a abandonné l'approche et l'a remis en file), le crochet 1 **ne le force plus jamais** dans cet essai : donc en pratique **une seule donation**, un seul abandon à observer, au lieu de la boucle de la v8. Le budget de 3 reste une deuxième sécurité.
3. **Un troisième crochet (H3), en lecture seule**, au début du chemin « approche ratée » du jeu (`0x6ff0fb`). Il ne modifie ni registre, ni mémoire, ni le déroulement : il note seulement, pour l'avion qu'on a signalé, **pourquoi** le jeu abandonne : indice de baie (−1 = aucune baie libre), indicateur d'échec, compteur d'approche, écart `z` au point visé, état de piste. Le journal en tire les causes possibles : `no-free-bay`, `target-passed` (point visé dépassé), `angle>0.45rad` (avion mal aligné avec la piste), `counter>3600`. Cinq lignes au plus par essai, de la forme `HOOK H3 the game ABORTS the approach (n so far): bay=… fail=… z=… counter=… runway_state=… causes: …`. À la fin de l'essai, une ligne de bilan : `FORCE balance (…): GRANTS n, ABANDONS m`.

## Niveau de risque : 🟡 (inchangé)
Trois petits crochets au lieu de deux, dans la même grande fonction du jeu ; le nouveau ne fait que lire. Il n'y a plus de boucle de donation à volonté. Limites : un seul avion, 3 donations, 20 s. Comme avant, **les crochets ne sont posés que si `recall_force=1` au démarrage du jeu** ; avec `recall_force=0` (ou rien) la v9 est une v7.

## Ce qu'on espère apprendre à l'essai
Pas forcément que l'avion soit repris : **savoir pourquoi le jeu refuse**. Comment lire le journal :
- `no-free-bay` : le jeu n'a pas de baie de hangar libre à proposer pour cet avion (il faut comprendre pourquoi : A1 ne libère-t-il pas sa baie ?).
- `target-passed` : le point que le jeu vise en fin de piste est **déjà derrière** l'avion (le repère de la piste ne correspond pas à ce que je croyais).
- `angle>0.45rad` : l'avion posé n'est pas assez aligné avec la piste (26° au plus) : on pourra demander au moddeur de se poser plus droit.
- aucune cause listée : autre chose, il faudra lire plus loin dans le code.

## Comment tout couper (identique à la v8)
`recall_force=0` dans `frein.ini` (relu en 3 s : les crochets ne font plus rien) ; remonter dans l'avion (le plugin lâche tout et rend le moteur) ; jeu fermé : remettre la v8 (`cc2-sdk-travail\dist_v8\cc2x_frein.dll`) ou la v7 (`dist_v7\`) ou `poser.py retirer`.

## L'essai, si tu es d'accord (partie neuve jetable, ancien exe)
Comme les précédents : navire ralenti, atterrissage sous 30 m/s relatifs avec au moins 60 m de pont derrière, le frein arrête l'avion, tu le quittes, tu attends 30 s, tu donnes l'ordre de retour, **tu ne touches plus à rien**. Cette fois, **dès que le journal montre l'avion qui accélère** (je le surveille), je te le dirai : tu remontes dans l'avion (le plugin lâche et te rend le moteur) pour ne pas laisser le jeu l'envoyer voler. `recall_force=1` est ajouté juste avant le lancement et retiré après.

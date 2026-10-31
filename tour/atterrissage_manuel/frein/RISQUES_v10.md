> **Statut (30/10/2026) : v10 posée (éteinte) et essayée ; la v11 est écrite hors jeu (non posée) : voir `RISQUES_v11.md`.** Ce fichier décrit la v10 telle qu'elle est dans le jeu.

# Plugin v10 : diagnostic des « portes d'engagement » (30/10/2026)

*Pour le moddeur. Rien n'est posé : la v9 est dans le jeu, éteinte. Ceci décrit ce qu'on poserait si tu dis oui. La v10 ne force rien de plus que la v9 : elle sert à comprendre.*

## Pourquoi cette version
L'essai de la v9 a montré que les crochets donnent bien la piste à l'avion, mais que le jeu **l'abandonne aussitôt**. Je croyais que c'était l'angle ; en relisant le code j'ai vu que c'est autre chose : dans la **zone finale** (moins de 200 m du milieu de la piste), le jeu abandonne tout avion qui ne s'est pas déjà **engagé** (état de piste 4) plus tôt, entre 400 m et 200 m. Pour s'engager, l'avion doit passer **cinq portes** (A à E). Un avion garé sur le pont ne les a jamais passées. Et sauter un seul de ces tests ne servirait à rien tant qu'on ne sait pas lesquels bloquent.

## Ce que la v10 ajoute (rien ne change pour le jeu)
- **Le diagnostic H3 est corrigé** : il n'affirme plus « angle ». Il écrit la zone (`zone=1` = zone finale), les écarts `x` (latéral), `y` (vertical), `z` (le long de la piste) et la cause probable `not-committed-in-final-zone`.
- **Quatre sondes en lecture seule**, posées aux endroits où le jeu constate qu'une porte échoue :
  - `PROBE gate A/B … failed` : A = le vecteur vers le point du chemin est nul ; B = le décalage latéral dépasse la limite (−0,08).
  - `PROBE gate C/D … failed` : C = la direction fait plus de 18° avec celle attendue ; D = le test interne du jeu répond « non » (la sonde « C passée » permet de distinguer).
  - `PROBE gate E … failed` : l'indice de baie est invalide.
- Chaque sonde **ne modifie aucun registre, aucun drapeau, aucune adresse de saut, aucune mémoire du jeu** (c'est vérifié par un test sur un faux jeu : avant/après identique). Elle n'agit que pour **l'avion qu'on a signalé** (jamais un avion de l'IA), seulement si `recall_force=1`, et écrit 8 lignes au plus par essai. À la fin, la ligne de bilan donne les comptes : `GRANTS n, ABANDONS m, GATES AB a CD c (C passed p) E e`.

## Un point technique corrigé avant la pose : les registres SSE (xmm)
Le relais du SDK pour les crochets sauvegarde les registres généraux mais **pas les registres SSE (xmm0 à xmm7)**, et le code du jeu y garde des valeurs vivantes à nos sites (relevé sur l'exe d'origine : xmm0 après les deux premiers crochets, xmm4 et xmm5 après les autres). Le code de nos crochets n'utilise aucune instruction SSE, mais il appelle `VirtualQuery` et le SDK, qui pourraient les toucher. **Chaque crochet passe donc par un petit enveloppeur en assembleur qui sauvegarde xmm0–xmm7 puis les restitue** (vérifié par un test qui charge les huit registres avec des motifs, appelle le crochet en entier, et compare ; un contrôle négatif prouve que le test détecte une corruption).

## Niveau de risque : 🟡 (inchangé), un peu plus de crochets mais en lecture
La v10 pose **sept** petits crochets au lieu de trois (deux de la v9 qui agissent, un de diagnostic, quatre sondes en lecture seule), dans la même grande fonction du jeu, **seulement si `recall_force=1` au démarrage**. Les quatre nouveaux sont posés à des endroits dont on a vérifié les octets, qu'aucun saut ne traverse, et qui ne sont pas relogés par le jeu. Un crochet de plus = un peu plus de chances de plantage si le jeu n'est pas exactement celui qu'on a lu ; en cas d'octets différents le plugin ne pose rien. Alternative plus sûre : ne rien poser.

## Ce que dira le journal, et ce qu'on en tire
- **Porte A** : le vecteur est nul : l'avion est sur le point du chemin (peu probable).
- **Porte B** : l'avion est trop décalé sur le côté par rapport au chemin → on pourrait essayer de se poser plus au milieu du pont, ou comprendre quel côté.
- **Porte C** : la direction vers le chemin fait plus de 18° avec celle attendue → à l'arrêt, il n'y a pas de bonne direction : forcer cette porte est possible mais intrusif.
- **Porte D** : le test interne du jeu répond « non » (probablement lié à l'état de l'avion : en vol / au sol, ou à l'équipe) → à lire dans le code.
- **Porte E** : pas de baie valide pour cet avion → autre problème (baie déjà réservée).
- **Aucune porte** (aucune ligne PROBE) : l'avion n'est pas évalué du tout (hors des 400 m, etc.) → il faudra relire le haut de l'état 3.
La **décision** qui en découle : si une seule porte bloque et qu'on comprend pourquoi, on pourra proposer **un** crochet de forçage ciblé (jamais plusieurs à la fois) ; sinon on s'arrête là et on garde le frein de la v7.

## Comment tout couper
`recall_force=0` dans `frein.ini` (relu en 3 s : tous les crochets cessent d'agir, y compris les sondes) ; remonter dans l'avion ; jeu fermé : remettre la v9 (`cc2-sdk-travail\dist_v9\cc2x_frein.dll`), la v8 (`dist_v8\`) ou la v7 (`dist_v7\`), ou `poser.py retirer`.

## L'essai (si tu es d'accord, avec la procédure habituelle)
Même déroulé que PROCEDURE_partie_v9.md. La différence est dans ce que je lis : les lignes `HOOK H3 … zone=… x=… y=… z=…`, `PROBE gate …`, puis `FORCE balance (…)`.

## Un mot sur `max_speed=50` dans `frein.ini` (demandé par la coordination)
Avec `max_speed=50` le frein agit jusqu'à 50 m/s relatifs. Deux risques mesurés auparavant : (1) **la course d'arrêt** : à `brake=0,1` l'avion s'arrête en 5,6 s et 72 m depuis 28 m/s ; à 50 m/s il lui faudrait ~250 m, plus que le pont (~180 m) : **il sortirait du pont par l'avant** ; (2) **la secousse du premier contact** : à 53 m/s on a mesuré −9,4 m/s en 0,1 s au premier appui du frein (note de la v3), ce qui peut basculer un petit avion. Conseil : rester à `max_speed=30` à 35, ou monter `brake` si on veut freiner plus fort à haute vitesse (à tester d'abord).

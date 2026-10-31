# Procédure de la partie test du 30/10/2026 : v8 (atterrissage à la main) puis modes carburant, dans UNE seule partie

Écrite par la coordination le 30/10 vers 08 h 15. **Rien de ceci n'a été lancé.** Les protocoles détaillés des deux conversations (`atterrissage-main`, `modes-carburant`) sont en préparation : s'ils diffèrent, ils priment sur cette page pour leur partie. Étiquettes : **MESURÉ** (vu en jeu ou dans un journal), **INFÉRÉ** (déduit).

## 0. Ce qui est déjà en place (vérifié en lecture seule)
- Plugin de frein **v8 posé ÉTEINT** (`cc2x_frein.dll` 0C8D68AD…, `recall_force` absent de `frein.ini` = 0, donc aucun crochet posé : elle se comporte comme la v7).
- Modes carburant : **onglet v2 et plugin v3 posés** dans le mod `cc2_modes`, en observation (`eco_enabled=0`), jamais lancés en jeu.
- Jeu normal fermé ; ancien exe `carrier_command_ancien_8E7FCBB6.exe` présent (lancé par `lancer_ancien.py`, jamais par Steam).

## 1. Ce qu'il faut AVANT de lancer (dans cet ordre, un oui du moddeur par ligne marquée « oui »)
1. Les correctifs des modes carburant (garde-fou « pilote » de l'onglet, lecture stricte de `modes.ini`) sont écrits et testés hors jeu : **en cours** chez `modes-carburant`. Sans eux, la ligne « id N: HELD » risque de ne pas apparaître.
2. **Oui n°1 : poser l'onglet et le plugin corrigés** dans le mod (fichiers seulement, jeu fermé, 🟢).
3. **Oui n°2 : ajouter `recall_force=1` à `frein.ini` (sauvegarde d'abord) et lancer l'ancien exe** (🟡 : crochets dans le code d'atterrissage du navire, jamais essayés en jeu, partie jetable).
4. Conditions : `Get-Process carrier_command*` vide, Steam ouvert, **partie NEUVE jetable** (jamais une sauvegarde : le chargement plante), un seul jeu à la fois.

## 2. Déroulé de la partie
**A. Lancement.** `atterrissage-main` lance l'ancien exe et vérifie `cc2x.log` : « CC2X 0.5.0 ready », « [frein] … recall_force=1 … hooks H1 and H2 installed » (sinon « could NOT be installed » : on fait alors la partie en v7), « [modes] loaded ». Nouvelle partie : NEW GAME > CUSTOM > START (réglages mémorisés).

**B. Partie v8 (atterrissage à la main) : 10 à 15 min.**
1. Sors l'avion 9 (celui des essais précédents ; la conversation te confirme le numéro). **Ralentis le porte-avions au minimum** avant de poser.
2. Tu pilotes, tu poses à **moins de 30 m/s relatifs**, avec **au moins 60 m de pont derrière toi**. Le frein s'enclenche seul (« BRAKE start ») et arrête l'avion en ~5 s (MESURÉ 4,7 à 5,8 s).
3. Tu quittes l'avion et tu **attends 30 s** (le moteur passe à 0, « IDLE »).
4. Tu donnes **l'ordre de retour**, puis tu **ne touches plus à rien pendant 40 s** et tu dis ce que tu vois (l'ascenseur monte ? l'avion recule sur les rails ?).
5. Succès dans le journal : `FORCE start`, `HOOK H1 …`, `HOOK H2 skipped the 1000 m test`, puis `dock=1`, `dock=6`, `attached` ≠ 0, `flight=1`, puis `dock=4` et le carburant qui remonte. Échec bénin : `FORCE gave up` / `FORCE timeout` : l'avion reste tenu au frein, on ne touche à rien. **Chance annoncée : ~35 % au 1er essai** (estimation de la conversation, pas une mesure).
6. Coupures : `recall_force=0` dans `frein.ini` (3 s) ; remonter dans l'avion ; fermer le jeu (toi seul). Ne lâche pas le frein si l'avion est près du bord arrière.
7. Tu dis « v8 terminée » (réussie ou non) : on passe aux modes. **Ne mets jamais en mode l'avion que tu pilotes ou qui est tenu au frein.**

**C. Modes carburant en observation (rien d'activé) : ~5 min.**
1. Clique un avion de la carte : l'onglet **SPEED** (sous LOADOUT) doit afficher « OBSERVATION : SANS EFFET » et une autonomie estimée.
2. Dans le journal : « id N: HELD » pour l'avion que tu as piloté en B (= le garde-fou pilote marche en vrai).

**D. ÉCO sur un avion (seulement avec un oui séparé à ce moment-là) : ~10 min.**
1. **Oui n°3 (🟡 moyen)** : `enabled=1` dans `modes.ini` (sauvegarde d'abord, par `modes-carburant`).
2. Sors UN autre avion, qui vole **seul à plus de 6 km du porte-avions**, que tu ne pilotes pas. Clique **ÉCO** sur lui.
3. Attends 2 à 3 min. Valeurs mesurées le 28/10 sur l'Albatros : vitesse ~119 → ~80 m/s, carburant −22 % par seconde (INFÉRÉ : le même résultat attendu).
4. Coupure : `enabled=0` (3 s) ou clic NORMAL. **FLANK** seulement après un ÉCO réussi et un nouvel oui.

**E. Fin.** Tu fermes le jeu et tu dis « fini ». Copie du journal (copieur passif armé `…_frein_v8`) ; `recall_force=0` et `enabled=0` remis (jeu fermé, sauvegarde d'abord) ; vérification des sommes ; rapport avec les lignes du journal.

## 3. Durée et risques
~30 à 40 min au total. Risques : v8 🟡 (plantage possible ; l'approche ratée remet l'avion en file avec un instant de poussée) ; modes en observation 🟢 ; ÉCO 🟡 moyen. Partie jetable : aucune sauvegarde en jeu.

## 4. Retour arrière (jeu fermé)
- v8 → v7 : copier `cc2-sdk-travail\dist_v7\cc2x_frein.dll` sur la DLL du jeu ; `recall_force` retiré de `frein.ini` (sauvegarde `frein.ini.avant_…`).
- Modes : `python -I tour/etudes_modes_carburant/mod_modes.py mettre-a-jour --etape interface` (onglet v1) ; `retirer-plugin` ; tout : `retirer`.

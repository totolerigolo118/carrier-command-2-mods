> **Mise à jour (30/10/2026, v11 écrite hors jeu) : pour un essai de la v11, utiliser `PROCEDURE_partie_v11.md`** (mêmes gestes pour le moddeur, nouvelles lignes de journal, verdicts et alertes). Ce fichier reste valable pour la v9/v10.
>
> **Statut (30/10/2026) : UTILISABLE** pour toute partie d'essai de la prise en charge (v10 posée, v11 éventuelle) : les gestes du moddeur ne changent pas. Les seuils d'alerte détaillés et la lecture des sondes sont dans `LECTURE_SONDES_v10.md`. À savoir : atterrir à **30 m/s relatifs au plus** (le réglage `max_speed=50` de `frein.ini` est déconseillé) ; `recall_force=1` est ajouté juste avant le lancement et retiré après ; lancement par `lancer_ancien.py` (ancien exe).

# Partie v9 : ta partie du test (à lire en 1 minute)

1. **Avant** : le jeu est fermé ; la coordination ajoute `recall_force=1` à `frein.ini` juste avant de lancer l'ancien exe (et le retire après). Tu ne touches à rien.
2. Partie **neuve**. Console AIR, « Deploy A1 », décolle, fais un tour.
3. **Ralentis le navire** au minimum. Pose-toi **bien aligné avec la piste** (le jeu refuse un avion trop de travers), à **30 m/s relatifs au plus**, avec **au moins 60 m de pont derrière toi**.
4. Laisse le **frein** arrêter l'avion (ne touche plus aux gaz), puis **quitte l'avion**.
5. **Attends 30 secondes** sans rien toucher.
6. Donne l'**ordre de retour** (le bouton habituel), puis **ne touche plus à rien** et regarde l'avion.
7. **Si la coordination te dit « remonte »** : remonte tout de suite dans l'avion (comme tu l'as fait le 30/10 à 08:13). N'attends pas.
8. **L'avion se met à reculer sur les rails, l'ascenseur monte, il rentre au hangar** : c'est le succès ; dis-le.
9. **Il ne bouge pas du tout** : c'est un échec sans danger (le jeu a refusé). Attends 60 s après l'ordre, puis dis-le.
10. Fin de la partie v9 : quand la coordination dit « bilan reçu ». Tu peux alors passer aux modes carburant dans la même partie (reprends l'avion à la main si besoin).

---

## Pour la coordination (lecture du journal en direct, 1 relevé par seconde) — le moddeur n'a pas à lire ceci

**Lignes à chercher dans `cc2x.log` après l'ordre de retour** (`RECALL start`, puis `FORCE start` 1 s après) :
- **Info (ne rien dire)** : `HOOK H1 shown circuit state 1`, `HOOK H2 skipped the 1000 m test (try 1 of 3)`, `HOOK H3 the game ABORTS the approach … bay=… fail=… z=… counter=… causes: …` (la cause est ce qu'on cherche), `FORCE balance (…): GRANTS n, ABANDONS m`.
- **SUCCÈS** : `dock=6` **et/ou** `attached_to` différent de 0 **et** `flight=1` ; ensuite `rel` peut monter (recul sur les rails, ~5 à 10 m/s) : **ne PAS alerter si `attached_to` ≠ 0 ou `dock=6`**. Puis l'avion quitte la zone vers l'ascenseur, `dock=4`, carburant qui monte.
- **ÉCHEC sans danger** : `FORCE gave up` / `FORCE timeout`, ou `GRANTS 1, ABANDONS 1`, avec `rel` < 0,5 et `brk=1` ; l'avion reste immobile.
- **DANGER → dire « REMONTE » tout de suite** si, pour l'avion flaggé, `attached_to=0` **et** l'un de ces cas : (a) `rel` > 1,5 m/s sur deux relevés consécutifs et qui monte ; (b) `power`/`power_read` = 1.00 pendant plus de 2 relevés avec `brk=1` ; (c) `wheels` < 3/3 avec `rel` > 1 ; (d) `HOOK H2 … (try k of 3)` avec k ≥ 3 ; (e) `dock=1` sans `attached_to` pendant plus de 3 s. Rappel du 30/10 : entre le premier `rel` 2,3 m/s et le décollage il s'est écoulé ~4 s : dire « remonte » **au premier** cas, pas au deuxième.
- Normal avec la v9 (pas d'alerte) : une seule donation puis `dock=5` de nouveau, `power_read=1.00` **une fois** (l'abandon du jeu), `rel` < 0,5 ensuite.

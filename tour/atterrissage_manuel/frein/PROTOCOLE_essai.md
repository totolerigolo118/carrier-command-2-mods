# Protocole d'essai du frein (étape 5) — à suivre par le moddeur, avec une SAUVEGARDE JETABLE

Rien de ce qui suit ne se fait avant la pose des deux DLL (étape 4, accord séparé) et jamais sur la sauvegarde de référence. Le jeu doit être **fermé** pour la pose et le retrait. Tout est **éteint par défaut** : à la pose, `frein.ini` contient `brake_enabled=0` (le plugin regarde et écrit dans `cc2x.log`, il ne freine rien).

## Depuis le 29/10 — le jeu normal n'active plus le SDK : lancer l'ANCIEN exe
La mise à jour Steam du 28/10 a remplacé `carrier_command.exe` ; le SDK reste **inactif** dessus (horodatage de compilation inconnu). Pour tout essai du frein, on lance **l'ancien exe de tous nos essais**, copié à côté du jeu, directement (pas par Steam) : `python -I tour/atterrissage_manuel/frein/lancer_ancien.py etat|copier|lancer|retirer --jeu <dossier du jeu> --cest-le-vrai-jeu`. `lancer` vérifie tout (pas de jeu ouvert, Steam ouvert, DLL aux sha256 épinglés), lance, puis lit `cc2x.log` et dit si le SDK s'est activé (`OK : le SDK est actif…` ou `ATTENTION … INACTIF`). Le jeu se ferme comme d'habitude ; `retirer` supprime la copie.

## Phase 0 — le jeu démarre-t-il, et la tour suit-elle ?
1. Lancer le jeu et démarrer une **PARTIE NEUVE** (NEW GAME), navire à l'arrêt. **Ne pas charger de sauvegarde** : depuis le 27/10 le chargement d'une sauvegarde plante (indépendamment de nos DLL, cause en cours d'étude par l'autre conversation). Si le jeu est occupé par l'autre conversation (essais automatiques), attendre son signal.
2. Lire l'affichage **SIM** après ~20 s : avant le SDK il valait **×1,33** ; une baisse nette = le SDK coûte trop cher (voir le verdict de relecture, condition 3).
3. Dire à Claude « c'est lancé » : il lit `cc2x.log` et confirme `CC2X 0.5.0 ready for Carrier Command 2 1.5.18-win32` et `plugin cc2x_frein.dll loaded`. **Arrêt** si le build n'est pas reconnu, si le plugin n'est pas chargé ou si le jeu plante.

## Phase 1 — observation, rien n'est freiné (2 atterrissages)
1. Lancer un avion (Manta ou Albatros), le laisser décoller, **le prendre en main**. **Noter EXACTEMENT ce qui fait sortir l'avion** (quel écran, quel bouton, dans quel ordre, ce que l'on voit à chaque clic) : l'essai automatique de l'autre conversation n'arrive pas à faire décoller les avions (ordres acceptés, avions restés rangés, le joueur n'est pas « aux commandes de la console »). Ta description débloque les deux études.
2. Faire un tour, se présenter **en finale dans l'axe**, train sorti, vitesse basse, **toucher le pont, rester sur la piste**.
3. Une ligne à Claude : « posé, il glisse » (ou ce qui s'est passé). Claude lit `cc2x.log` : numéro de l'avion (`id`), `flight`, `dock`, `attached`, contacts des roues, vitesse, distance, `armed`, `eligible`.
4. **Objectif** : voir `eligible=1` pour l'avion posé à la main (sinon on corrige le plugin avant la phase 2), et **`eligible=0` pour les avions de l'IA** pendant leur sortie / retour (lancer puis rappeler 2 avions pour le vérifier).

## Phase 1 bis (27/10, après les 2 premiers atterrissages) — plugin v2
Mesuré en phase 1 : l'avion posé à la main reste `flight=2` au contact (réglage `flight_state=-1`, fait) et **n'a presque jamais les 3 roues au sol** (le train avant reste en l'air) ; les rebonds hacheraient le frein. La v2 du plugin ajoute `min_wheels` (nombre de roues exigé, 0 = toutes) et `grace_s` (frein tenu après un rebond), défauts = comportement de la v1, et n'arme que si **aucune** roue ne touche (une rotation au décollage sur 2 roues n'arme jamais). Pose : `poser.py maj` (remplace **seulement** `cc2x_frein.dll` v1 par la v2, jeu fermé, accord séparé du moddeur).

## Phase 2 — le frein (3 atterrissages : un doux, un plus dur)
0. Pilotage : porte-avions à pleine vitesse dans le sens de l'approche (la vitesse relative tombe à ~8-11 m/s), **toucher au DÉBUT du pont (côté poupe, ~−90 m du centre)**, ~50 % des gaz jusqu'au contact puis gaz à zéro.
1. Claude règle `frein.ini` : `brake_enabled=1`, `only_id=<numéro de l'avion piloté>`, `brake=1.0`, `grip=1.0`, `flight_state=-1`, `min_wheels=2`, `grace_s=1` ; **v3 (après le 1er freinage réel, 27/10)** : `height_m=40` (le pont est à +19,8 m, une zone de ±20 m laisse un petit rebond la quitter et relâche le frein), `max_speed=30` (aucun freinage au-delà de 30 m/s relatifs ; à 53 m/s : −9,4 m/s en 0,1 s) et `brake` d'abord à 0,1 (relu toutes les 3 s : **pas besoin de relancer le jeu**).
2. Même manœuvre. Claude lit `cc2x.log` : `BRAKE start`, `STOPPED after … s, … m` (distance de freinage sur le pont). **Réussi si** l'avion s'arrête avant le bout de piste (~150 m).
3. Si l'avion ne s'arrête pas : on essaie `grip` / `brake` autres **dans la plage 0..1** ; aller au-delà demande une nouvelle compilation et ton accord.
4. **Coupure immédiate** si un problème apparaît : `brake_enabled=0` (relâché en ≤ 3 s).

## Vérification IA obligatoire en fin d'essai
Lancer puis rappeler 4 avions de l'IA, plugin actif : `cc2x.log` doit montrer **0 freinage** pour eux, ils doivent rentrer normalement (piste non bloquée), le journal des retours doit rester comparable (pont > hangar ≈ 0:55).

## Conditions d'arrêt (puis `poser.py retirer`, jeu fermé)
Plantage au démarrage ; build non reconnu ; SIM nettement plus bas ; avion de l'IA freiné ; piste bloquée.

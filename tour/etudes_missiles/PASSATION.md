# Passation : étude « verrou T et missiles » (fiche écrite le 29/10/2026)

Cette fiche se suffit à elle-même. Preuves détaillées : `tour/etudes_missiles/DIAGNOSTIC.md` (déjà commité et poussé par une autre session,
commit `80f2a8a`). Réponses du Mac : `passation_windows/REPONSES_mac_pour_la_tour_28-10.md` (branche `origin/mac/reponses-tour-28-10`, Q2).

## ÉTAT À LA PASSATION (29/10/2026)

1. **Objectif :** le moddeur verrouille un bateau (T, cadre rouge bien dessus), tire, et le missile va sur l'unité la plus proche (près de l'île) ; il veut qu'il aille sur la cible verrouillée.
2. **Établi** (LU = vu dans le code, MESURÉ = vu en jeu, INFÉRÉ = déduit ; **rien n'est MESURÉ**) :
   - LU : le verrou T est décidé par un script Lua du jeu (`vehicle_hud.lua`) ; le programme relit la cible et l'envoie à l'arme ; T ne verrouille que des ennemis « observés ».
   - LU (exe Windows ancien build + Mac) : l'arme ne donne au missile qu'**une direction**, pas l'identité de la cible ; **en vol le missile cherche seul** : ennemis à
     **moins de 4 000 m**, **cône de 45°** devant son nez, note 0,9 × alignement⁵ + 0,1 × proximité ; le premier retenu devient sa cible. L'écran laisse verrouiller jusqu'à 10 km.
   - INFÉRÉ : un bateau verrouillé à plus de 4 km n'est pas candidat au départ, une défense de l'île entrée avant lui est prise (non confirmé en jeu).
   - **Verdict : Lua impossible ; petit patch de l'exe possible** (faire lire 100 000 000 au lieu de 16 000 000 à un seul endroit, risque 🟡, voir détails).
3. **Posé en ce moment : rien** (ni jeu, ni `%APPDATA%`, ni `mods.xml`, ni DLL, ni exe). Hors dépôt : `missiles_verrou_T_note.md` (dossier de notes de la session) et
   des scripts Python temporaires (lecture seule) dans le dossier temporaire de la session. Rien à retirer.
4. **Attend le moddeur** (questions restées sans réponse, mot pour mot) :
   - « Je prépare ce patch sur une copie seulement ? »
   - « Je corrige DIAGNOSTIC.md avec ces trois points ? » (les 3 corrections du Mac, plus bas)
   - (information) « dis-moi à peu près à quelle distance du bateau tu tires, et si c'est le missile IR ou l'anti-aérien. »
5. **Prochaine action unique :** redemander au moddeur, en français simple, « Je prépare ce patch sur une copie seulement ? » (copie du **nouvel** exe) avec la distance et le type
   de missile ; ne rien appliquer sans son oui explicite.
6. **Pièges / à ne PAS faire :** ne jamais changer la valeur partagée 16 000 000 (4 lectures : 2 missile, 2 torpille), rediriger seulement l'instruction « véhicules » du missile ;
   le patch ne suffit pas si le bateau est hors du cône de 45° au tir ; ne pas présenter l'explication comme prouvée ; ne pas lancer/fermer le jeu ni toucher à `mods.xml`,
   aux DLL (`dinput8.dll`, `cc2x_frein.dll`, `frein.ini`) ou à l'exe sans accord ; ne pas toucher aux leurres ni aux torpilles.
7. **Non commité, à moi :** `tour/etudes_missiles/PASSATION.md` (cette fiche). `DIAGNOSTIC.md` est commité et poussé mais **sans** les corrections du Mac (elles attendent l'accord du moddeur).
8. **Mise à jour Steam du 28/10** (info de la session de coordination, non vérifiée par moi : nouvel exe `461E1262…`, sans patch) : toutes les **adresses de l'exe citées valent pour l'ANCIEN
   build** (`1C9A01C3…` ; le `8E7FCBB6…` patché ne touche pas ce code) ; le nouvel exe est recompilé, le code est décalé : retrouver les emplacements **par le contexte** (signature plus bas).

## Détails

**Mods (dernière lecture de `mods.xml`, 27/10 14:22)** : 2937532682 « Gentle Missile Speed Buff » (XML seulement ; ne touche ni le missile IR ni les roquettes), `cc2_mesures`, `cc2_carte`.
Revolution absent à ce moment-là (il a son propre `vehicle_hud.lua`, non analysé en détail). Liste à relire : elle a pu changer.

**Les 3 corrections du Mac à appliquer à DIAGNOSTIC.md (si le moddeur dit oui)**
1. « Seuil de départ 0,05 pour l'anti-aérien » (section 11) est **faux** : le seuil de départ est 0 pour tous les types ; 0,05 sert au suivi de la cible déjà accrochée.
2. Les 4 lectures de 16 000 000 : **2 pour le missile** (véhicules, leurres) et **2 pour la torpille** (mes notes disaient « autres groupes / contre-mesures »). Le patch ne change pas les torpilles.
3. Condition manquante : avant toute recherche, le missile vérifie que la direction de départ est dans un **cône de 0,7 (45°) autour de son axe avant** ; le cône des candidats se mesure
   aussi par rapport à l'axe avant du missile. (Le Mac n'a pas retrouvé l'instruction qui met le missile en mode « accroché » : sans effet sur le patch.)
   Noms Mac : `c_scene_region::tick_missile_behaviour_missile`, `tick_missiles`, `set_track_vector`.

**Signature pour retrouver le site dans le nouvel exe (ancien build, base 0x400000)**
- Boucle de traitement des missiles : 0x746a70 → 0x74ccb0. Site à patcher : **0x747168**, `movss xmm1,[16 000 000]` (`f3 0f 10 0d <adresse>`), qui suit le calcul de distance² d'un véhicule
  (`lea ecx,[ecx+0x48]` puis `call`) et précède `comiss` / `jbe`. Avant lui : test « détruit » (`cmp byte [esi+0x164],0`) et test d'équipe (`[esi+0x1a8]` contre `[edi+0x14]`) ; dans la même
  boucle : test de cône contre 0,7 et un appel de puissance 5,0.
- À ne pas toucher : 0x74772c (leurres), 0x749b98 et 0x74a234 (torpilles). Vérification : `tour/outils/lister_lectures.py` avec la valeur 16000000 doit donner **4** lectures.
- La valeur 100 000 000 existait **une fois** dans `.rdata` (ancien build) : à re-vérifier dans le nouvel exe, sinon l'ajouter comme pour `ascenseur_x2` (bourrage de l'en-tête).
- Repères de l'arme (ancien build) : cible verrouillée (type, identifiant) à +0x12c / +0x130, vecteur de départ à +0x110.

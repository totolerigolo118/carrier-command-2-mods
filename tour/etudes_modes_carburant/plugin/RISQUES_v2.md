# Plugin v2 (ÉCO par type + FLANK en plancher de gaz) : ce qui change, les risques, comment le poser

Préparé le 28/10/2026, **hors du jeu**. Rien n'est posé de la v2 : le plugin installé est toujours la v1 (sha256 `AB2D5343…`).
Lire d'abord `RISQUES_pose.md` (les risques généraux de la v1, qui restent valables).

## Ce que la v2 ajoute

| Nouveauté | Ce que ça fait |
|---|---|
| **ÉCO par type** | plafond Albatros `eco_cap_light` (0,55 à 1,0 ; 0,65 par défaut) et plafond Manta `eco_cap_heavy` (0,30 à 1,0 ; 0,35 par défaut) : la croisière du Manta n'utilise que 0,47 de gaz, l'ancien minimum de 0,55 ne le ralentissait jamais |
| **FLANK = plancher de gaz** | pour les avions listés (`flank_ids`, ou `flank_all`), si le jeu laisse un gaz **plus bas** que le plancher (1,0 par défaut, minimum 0,50), le plugin le remonte. Même mécanisme que ÉCO, dans l'autre sens : aucun patch du code du jeu |
| **Zones libres séparées** | ÉCO : rien à moins de 1 500 m du bateau ; FLANK : rien à moins de **6 000 m** (un avion rapide a besoin de place pour ralentir) |
| **Conflits** | un avion demandé à la fois en ÉCO et en FLANK reste NORMAL (avertissement dans le journal) |
| **Compatibilité** | les noms de la v1 (`eco_enabled`, `eco_cap`, `free_zone_m`) marchent toujours ; `enabled=0` l'emporte sur `eco_enabled=1` |

Vérifié hors jeu : **72 contrôles automatiques réussis** (dont tous ceux de la v1), DLL 218 624 octets, sha256 `8B3A5A87…DB35`, deux compilations identiques,
aucun import réseau / processus, chaînes suspectes aucune (`RAPPORT_compilation.md`). Outil de mise à jour essayé sur fausse copie.

## Ce que la relecture du Mac a confirmé ou ajouté (voir ETUDE.md §13)

- Le champ de gaz et le plafond « qui fuit d'un pas » sont confirmés par le code du Mac et correspondent exactement à notre essai (écrit 0,65 → appliqué 0,72).
- **Nouveau risque pour FLANK** : le moteur ne reçoit que `min(gaz, max(1 − S, 0,8 Albatros / 0,75 Manta))`, S dépendant de l'équipement : un avion très chargé pourrait ne pas dépasser 0,8 (Albatros) / 0,75 (Manta) même avec un plancher de 1,0. Le gain de FLANK sera alors plus faible que nos mesures (faites avec des avions peu chargés).

## Ce qui n'est PAS prouvé (à vérifier à l'essai)

1. **Que FLANK en plancher produise la vitesse attendue.** Le gaz appliqué sera le plancher **moins** le pas de régulation de l'IA (elle veut ralentir quand
   l'avion dépasse sa vitesse visée de ~120 m/s) : mon estimation grossière est **≈ 130 m/s pour l'Albatros** (sa croisière en fait déjà 119 : peu de gain) et
   **≈ 230 m/s pour le Manta** (pas les 290 de la main). À mesurer.
2. **Le comportement de l'IA à très grande vitesse** : suivi des points de passage, virages très larges (à 230 m/s un virage serré demande plusieurs km), dépassement
   du point puis demi-tour. **Jamais mesuré** : le moddeur a volé le Manta à 290 m/s à la main sans incident, pas l'IA.
3. **ÉCO du Manta à 0,35** : ralentira-t-il sans décrocher ? Estimation : gaz appliqué ≈ 0,42, vitesse ≈ 100-110 m/s ; **jamais mesuré** à ce régime.
4. **Un avion piloté à la main n'est pas détecté** (le jeu dit « mode 0 » aussi pour lui) : s'il est dans la liste, le plugin écrase **tes** gaz. Règle : ne jamais lister l'avion qu'on pilote.

## Les risques, par étape (🟡 global)

| Étape | Ce que ça fait | Risque | Comment on s'en protège |
|---|---|---|---|
| **M : mise à jour du fichier** (`mettre-a-jour-plugin`) | remplace la v1 par la v2 dans le mod `cc2_modes` ; dossier du jeu, `mods.xml` inchangés | 🟢 | jeu fermé exigé ; ne remplace que la v1 connue ; retrait = `retirer-plugin` |
| **A2 : lancer avec la v2, `enabled=0`** | observation seule, comme la v1 (rien n'est écrit) | 🟡 faible | mêmes protections que la v1 ; partie neuve jetable |
| **B2 : ÉCO du Manta** (`enabled=1`, `eco_ids=<Manta>`) | écrit un gaz ≤ 0,35 dans le Manta de l'IA | 🟡 moyen | un seul avion ; il ne doit pas décrocher : s'il perd de l'altitude ou ralentit sous ~70 m/s je coupe (`enabled=0`, 3 s) ; zone libre 1 500 m |
| **C : FLANK** (`flank_ids=<avion>`) | écrit un gaz ≥ plancher dans l'avion de l'IA | 🟡 **moyen à élevé** | **un seul avion, loin (> 6 km), plancher d'abord à 0,8** (pas 1,0) ; vol droit vers un point lointain d'abord, jamais près d'îles ni de reliefs ; l'ordre de retour arrête FLANK **mais l'avion arrive vite** : le rappeler **à plus de 10 km** ; coupure `enabled=0` en 3 s. Au pire on perd un avion de la partie jetable (crash contre un relief, point dépassé) |

Aucun risque pour tes sauvegardes (essais en **partie neuve jetable** seulement). Pas de fuite de données (aucun accès réseau). Dépendance : le plugin suppose le
chargeur du SDK (`dinput8.dll`, API 3) : si une autre conversation remplace ce chargeur (une conversation « chargeur maison » travaille), il faudra revérifier que le plugin
se charge encore.

## Alternatives plus sûres

- Rester à la v1 posée (ÉCO de l'Albatros, validé) : rien à faire.
- Faire seulement **M puis A2 puis B2** (ÉCO du Manta) et laisser FLANK de côté.
- FLANK « à la main » : tu pilotes à pleins gaz quand tu veux de la vitesse (déjà possible, sans plugin).
- FLANK par le code du jeu (étape 3a : relever la vitesse visée de l'IA) : plus invasif (🟡/🔴), plus complet (vitesse visée et zones gérées par l'IA elle-même).

## Poser, essayer, retirer (quand tu diras oui, jeu fermé)

```bash
python tour/etudes_modes_carburant/mod_modes.py mettre-a-jour-plugin   # remplace la v1 par la v2 ; mods.xml et dossier du jeu intacts
python tour/etudes_modes_carburant/mod_modes.py etat                   # doit dire : v2 conforme
python tour/etudes_modes_carburant/mod_modes.py retirer-plugin         # retire le plugin (v1 ou v2)
```

Réglages : `%APPDATA%\Carrier Command 2\cc2x\modes.ini` (modèle : `plugin/modes.ini.example`). Sans fichier, ou avec `enabled=0` : observation seulement.

# Pourquoi les copies du bouton « Hold On Deck » n'ont aucun effet (analyse de l'exe, 30/10/2026)

Hors jeu, lecture seule de `carrier_command_ancien_8E7FCBB6.exe` (11 353 600 o). Rien n'a été lancé, posé ni modifié.
Étiquettes : **LU** (désassemblage de l'exe, contrôlé par `verifier_liaison_par_nom.py`, 17 contrôles OK), **MESURÉ** (vu par le moddeur en jeu ou par un script), **INFÉRÉ** (déduit, pas vu), **INCONNU**.
Aucun pourcentage de réussite : les estimations passées se sont toutes révélées fausses.

## En une phrase
**LU** : le jeu relie la fonction « Hold » au PREMIER bouton nommé exactement `vehicle_control_air_hold`, une seule fois, au démarrage de la partie. Un second bouton n'est jamais relié, même s'il porte le même nom. **Donc aucun mod XML ne peut fabriquer une copie qui marche** : on peut seulement DÉPLACER l'original.

## LU (adresses mémoire de l'ancien exe ; la section `.rdata` commence au fichier 0x8D5000 = mémoire 0xCD6000)
1. La chaîne `vehicle_control_air_hold` : fichier 0x920258 = mémoire **0xD21258**. Trois instructions la poussent : 0x6E4D20 et 0x6E4D97 (fonction 0x6E4100) et 0x6EDAB6 (fonction 0x6ED1C0).
2. **Trois recherches par nom** utilisent ce nom, chacune dans la liste des boutons (ou des voyants) du porte-avions :
   - 0x63E1F0 : cherche le **voyant** `vehicle_control_air_hold` (celui du XML, ligne 2370, type 3, panneau 0). Message d'erreur : « indicator not found: ».
   - 0x63DDB0 : cherche le **bouton** (état « affichage », 16 octets par bouton). Message : « button not found: ».
   - 0x63F360 : cherche le **bouton** (état « logique », 8 octets par bouton). Le résultat est rangé dans l'objet du porte-avions à l'adresse +0x560. **C'est celui-ci que lit la logique des avions** (voir 4).
3. **Comment une recherche marche** (0x63F360, 0x63DDB0, 0x63E1F0 sont des jumelles) : elle parcourt la liste dans l'ordre, du n° 0 vers le haut, compare le nom lettre à lettre et **s'arrête au premier nom identique**. Si aucun : elle écrit −1 et note « button not found: <nom> » au journal. Si trouvé : elle garde (a) le numéro, (b) un pointeur vers l'état en cours de CE numéro, (c) un pointeur vers sa définition. Chaque élément de la liste fait 0x58 octets (boutons) ; le nom est au début. Cette liaison est faite **une seule fois**, à la création du porte-avions (fonctions d'initialisation 0x704F00 → 0x6ED1C0, et 0x6F5830 → 0x6E4100).
4. **Comment l'état « Hold » est lu pour les avions** : la fonction 0x63F570 répond « oui » si l'état existe, que son octet 0 n'est pas nul **et** que son octet 2 n'est pas nul (avec l'argument 1 que le code lui passe). Elle est appelée par la fonction du porte-avions 0x6FC730 en **deux endroits** (appels en 0x6FCD74 et 0x6FD942), toujours avec le repère rangé à +0x560. Juste à côté, le code écrit l'état de l'avion := 7 (« undock_holding », avion retenu) en 0x6FCD6A et 0x6FD95C. Un balayage de tout le code montre que **ces deux appels sont les seuls à lire ce repère dans la classe du porte-avions**.
5. **Le lecteur XML d'un `<button>`** (fonction 0x59DC70) ne lit que : `name`, `display_name_loc`, `button_panel_index`, `button_cover_index`, `transform`, `type`, `help_tag`. Pour un `<indicator>` : `name`, `display_name_loc`, `button_panel_index`, `transform`, `type`, `mesh`, `bounds`. **Aucun champ « alias », « lié à », « groupe », « miroir ».**
6. Il n'existe pas de fonction Lua « Hold On Deck » : parmi les noms de fonctions de l'exe contenant `hold`, seuls `get_is_hold_fire` / `set_is_hold_fire` (le « tir retenu », autre chose) existent.

## MESURÉ
- (le moddeur, 30/10, ancien exe) Les deux copies s'affichent et s'enfoncent, mais n'enclenchent pas l'original et les avions décollent ; l'original ne bouge pas les copies.
- (coordination) La chaîne `vehicle_control_air_hold` n'existe qu'une fois dans l'exe ; `vehicle_control_air_bay_0` et le help_tag `veh_con_button_hold_air` n'y sont pas (le jeu cherche `vehicle_control_air_bay_` + un numéro, qu'il fabrique lui-même).
- (script) `verifier_liaison_par_nom.py` : tous les contrôles ci-dessus passent sur l'ancien exe.

## INFÉRÉ (jamais vu en jeu)
- L'ordre de la liste = l'ordre des `<button>` dans le fichier XML (c'est l'ordre normal d'un chargement, non vérifié ligne à ligne).
- Un appui change l'état de SON numéro de bouton seulement. C'est ce que le moddeur a vu : la copie s'enfonce, personne ne la lit.
- Octet 2 de l'état logique = « enclenché », octet 0 = « actif ». Je n'ai pas encore trouvé le code qui écrit ces octets au moment de l'appui.

## INCONNU
- Le code qui traite l'appui (qui écrit l'octet 2).
- Si le voyant `vehicle_control_air_hold` s'allume à cause de l'état du bouton ou à cause de l'état des avions.
- Le nouvel exe (jeu à jour) : mêmes idées probables, mais autres adresses ; non analysé.

## Ce que ça change pour le mod XML
| Idée | Verdict | Pourquoi |
|---|---|---|
| Copie de MÊME nom, placée APRÈS l'original | **ne marche pas** | l'original est le premier trouvé ; la copie n'est jamais reliée |
| Copie de MÊME nom, placée AVANT l'original | marche… mais l'original devient mort | la copie devient le « premier » ; c'est un déplacement avec un faux bouton en plus : pire qu'un vrai déplacement. Non fabriquée |
| Copies de noms différents (essai du 30/10) | **ne marche pas** (mesuré) | jamais reliées |
| **DÉPLACER l'original** (`button_panel_index` 8 ou 7 + nouvel emplacement) | marche (INFÉRÉ, jamais essayé) | le nom ne change pas, la liaison se fait au premier trouvé. Le bouton disparaît de la console des avions. Le voyant (`vehicle_control_air_hold`, panneau 0, mesh 14) peut rester sur la console des avions ou être déplacé avec |

Le moddeur avait refusé le déplacement (« je veux qu'il soit copié »). Il n'est proposé que comme repli.

## Autres routes
**Plugin du SDK (route qui respecte « copie, original intact »).** Le SDK du moddeur (`cc2x.h`, comme le frein) sait poser un « crochet » dans le code de l'exe : à un endroit choisi, on reçoit les registres et on peut en changer un avant que le jeu continue (**LU** dans `cc2x.h`, lignes 40-55). Idée à valider avant d'écrire une ligne :
- poser deux crochets juste après les deux appels de 0x63F570 (en 0x6FCD79 et 0x6FD947, là où le code teste la réponse) ; si une copie est enclenchée, répondre « oui » aussi.
- **Lecture seule** : on ne modifie rien dans l'état du jeu ; avant de lire une copie, le plugin vérifie son nom (la définition de la copie suit celle de l'original dans la liste ; le plugin a le pointeur vers l'original à +0x560+8).
- Limites prévues : l'original ne bouge pas quand on appuie sur la copie ; pour relâcher, il faut désenclencher le bouton qu'on a enclenché ; le voyant peut ne pas s'allumer.
- Prérequis : écrire et compiler le plugin hors jeu, poser une DLL (« oui » séparé, fichier protégé), essai en jeu avec l'ANCIEN exe seulement (le SDK ne se charge que là). Le mod actuel `cc2_hold_copies` fournit déjà les copies visibles.
- Risque : 🟡 (un crochet mal placé fait planter le jeu ; le frein utilise déjà ce même SDK ; INFÉRÉ : on retire un plugin en enlevant sa DLL). Variante « miroir » qui écrit dans l'état des boutons : 🔴 (plus complète, plus risquée).

**Écran Lua au Helm** (une case « Hold On Deck » sur un écran). Les écrans du jeu sont bien des scripts Lua (`rom_0\scripts\screen_*.lua`, ex. la case « Hold fire », ligne 393 de `screen_vehicle_control.lua`), mais il n'y a **aucune fonction Lua** pour le Hold des avions (point 6). Il faudrait forcer l'état des avions à la main (état 7) avec le SDK, c'est-à-dire refaire la logique du jeu, et remplacer un script du jeu par mod. 🔴, non recommandé.

## Fichiers
- `verifier_liaison_par_nom.py` : relit l'exe (`python -I -B`, lecture seule, aucun réseau) et refait les 17 contrôles ; à relancer si le jeu change.
- Rien posé, rien commité.

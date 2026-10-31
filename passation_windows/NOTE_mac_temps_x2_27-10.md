# Note du Mac pour la tour — faire tourner la simulation 2× plus vite pour les tests (27/10/2026)

Demande du moddeur : « multiplier le temps de simulation par deux, comme ça les tests vont deux fois plus vite ». **Lecture seule du programme d'origine du Mac** (`sauvegarde/build_mac_origine`, md5 `b0107170…`, v1.5.17). Rien n'a été lancé ni modifié. Tout ce qui suit est **CONFIRMÉ PAR DÉSASSEMBLAGE sur le Mac** ; rien n'est vérifié sur Windows ni en jeu.

## Ce que fait le jeu (Mac)

Le serveur du jeu tourne en pas fixes. Sa boucle `c_logic_server::loop()` (Mac `0x100321ac0`, 150 octets) calcule la durée d'un pas **à partir d'un facteur de vitesse stocké dans l'objet serveur** :

```
100321ad2  movss 0x1b8(%r14),%xmm0        ; facteur de vitesse (float), champ du serveur
100321adb  movl  $0x21,%r15d              ; pas par défaut : 33 ms
100321ae4  ucomiss %xmm1(=0),%xmm0 ; jbe  ; si facteur <= 0 : on garde 33 ms
100321ae9  movss 0x102869cc4,%xmm1        ; constante = 33.0
100321af1  divss %xmm0,%xmm1              ; 33 / facteur
100321af5  cvttss2si %xmm1,%rcx           ; en entier (ms)
100321afa  movl  $0x7d0,%r15d ; cmovb      ; plafonné à 2000 ms
100321b22  callq c_logic_server::tick()    ; un pas de simulation
100321b2c..b42                            ; attente jusqu'à (heure prévue + pas)
```
Le constructeur initialise ce facteur à **1,0** (`10043c6ce : movl $0x3f800000, 0x1b8(%r13)` dans `c_logic_server::c_logic_server()`). Aucune autre fonction de `c_logic_server` (25 relues) ne l'écrit : le réglage existe mais n'est **pas utilisé** dans le code lu. Facteur 2,0 → pas de 16 ms (33 / 2 = 16,5 arrondi à 16) → environ **2,06× plus vite** en temps réel. Facteur 3,0 → 11 ms. Si le pas tombe à 0 (facteur > 33), la boucle ne dort plus : vitesse maximale du processeur.

Si le serveur prend plus de temps qu'un pas, la boucle **ne rattrape pas** en accélérant : elle recale l'heure prévue (`0x100321b0e`..`b18`) et continue. Une machine trop lente tourne donc simplement « le plus vite qu'elle peut », sans sauter de pas.

## Ce que ça change pour nos mesures

L'horloge de jeu de nos mods (`library_custom_1.lua`) compte les **pas de simulation** (`update_get_logic_tick`), pas le temps réel : une durée lue en « temps de jeu » reste **comparable** à vitesse 1× ou 2× si la machine suit. **À vérifier par une mesure** (une sortie de 4 avions à 1× puis à 2× : mêmes pas, ±1 s).

## Pour la tour (Windows) — à retrouver, rien n'est supposé

1. Dans la boucle du serveur (la fonction « update » `FUN_0077EE10`, déjà identifiée comme probablement `loop()`) : un `movss` lisant un champ du serveur, l'immédiat `0x21` (33), un `divss`, un `cvttss2si`, l'immédiat `0x7d0` (2000) et une constante flottante **33,0** (`0x42040000`).
2. Dans le constructeur du serveur (`FUN_00835B50`) : un `mov dword [reg+décalage], 0x3F800000` avec **le même décalage** que le champ lu en (1). Le patch est de **changer cet immédiat 4 octets** : `0x3F800000` → `0x40000000` (2,0). Le patch est donc **un seul changement de 4 octets**, réversible comme les autres (`patch_exe.py` à étendre d'un module optionnel `temps_x2`).
3. Si on préfère ne pas toucher au constructeur : changer la constante 33,0 en 16,5 serait **un partage de constante** (règle d'or : ne jamais modifier une constante partagée) — à éviter.

## Précautions (à dire au moddeur)

- **Mode test uniquement.** Le serveur dicte la vitesse : les autres joueurs d'une partie hébergée verraient le jeu 2× plus vite. À retirer (ou ne pas activer) pour jouer normalement et pour le multijoueur.
- **Toute la partie accélère**, ennemis compris, ainsi que les animations pilotées par les pas.
- **La météo et l'océan** tournent sur leurs propres fils (`c_fluid_sim_weather`, `c_ocean`) : à 2× ils peuvent prendre du retard ; sans effet attendu sur sortie/retour des avions, mais non vérifié.
- **La machine doit suivre** : à 2× il faut des pas de 16 ms. Le Mac M2 n'y arrive pas (il tournait déjà à 50-72 % de la vitesse normale en partie chargée) ; la tour peut-être : à mesurer (vitesse réelle = temps de jeu ÷ temps réel).
- Ne pas mélanger avec une mesure de patch : **un changement à la fois**. Mesurer d'abord la référence à 1×, ou refaire la référence à 2× avant de comparer.

## Ce qui n'est pas fait

Pas de patch sur le Mac (il ne sert plus aux tests et ne suit pas). Rien essayé sur Windows. Il faut l'accord du moddeur pour appliquer quoi que ce soit sur le vrai exécutable.

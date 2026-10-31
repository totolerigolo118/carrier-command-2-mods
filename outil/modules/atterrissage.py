# -*- coding: utf-8 -*-
"""Atterrissages plus rapides (reglage B) : creneau elargi + circuit d'attente en cercle.

FICHIER GENERE par outil/generateurs/generer_atterrissage.py (ne pas modifier a la main).
Fonction : c_vehicle_server_carrier::docking_manager_air::update, circuit d'attente des avions
(les helicos ne sont pas concernes). Logique d'origine : un avion ne recoit la piste qu'au tick ou il
passe le bas du virage arriere (la « porte », 3 km derriere le bateau), une fois par tour de 12,3 km.
Ici : la piste peut etre donnee sur tout le virage arriere (~2,7 km, ~35 s de vol), et le virage
avant se fait sur le meme cercle que l'arriere : tour de 7,5 km (94 s a 80 m/s) au lieu de 12,3 km.
Cercle de centre (-1000, -1800), rayon 1200 m (repere du bateau), a 859 m au plus pres du bateau.
Choisi par le moddeur le 23/10/2026. Le reglage A seul est dans modules_en_reserve/atterrissage_creneau.py.
"""
NOM = "atterrissage"
TITRE = "Atterrissages : creneau elargi + circuit en cercle"
TYPE = "programme"

RETOUCHES = [
    # creneau elargi
    ("imm", 0x1001af900, "0f86ff010000", "0f860e000000"),  # jbe 0x1001afb05 -> 0x1001af914 : etat 1 : tester la piste a chaque tick, pas seulement au bas du virage
    ("imm", 0x1001af85b, "0f86a4020000", "0f86b3000000"),  # jbe 0x1001afb05 -> 0x1001af914 : etat 2 : tester la piste pendant le reste du virage arriere
    ("imm", 0x1001af867, "e999020000", "e9a8000000"),  # jmp 0x1001afb05 -> 0x1001af914 : etat 2 -> 3 : tester la piste aussi au moment du changement
    # circuit en cercle
    ("rip", 0x1001af785, "0f580d34c16b02", 0x10286b8c0, 0x10286b920, None),  # addps (1000.0, 1800.0) : etat 4 : centre du virage (-1000, 600) -> (-1000, -1800)
    ("rip", 0x1001af7d4, "0f582525c16b02", 0x10286b900, 0x10286b930, None),  # addps (-1000.0, -1800.0) : etat 4 : idem (retour au repere)
    ("rip", 0x1001afa98, "0f580d21be6b02", 0x10286b8c0, 0x10286b920, None),  # addps (1000.0, 1800.0) : etat 5 : idem
    ("rip", 0x1001afae7, "0f582512be6b02", 0x10286b900, 0x10286b930, None),  # addps (-1000.0, -1800.0) : etat 5 : idem (retour au repere)
    ("rip", 0x1001af870, "f30f100d5c9f6b02", 0x1028697d4, 0x102869adc, None),  # movss (-1800.0,) : etat 3 : fin de la ligne droite z > 600 -> z > -1800
    ("rip", 0x1001afaf2, "f30f100dda9c6b02", 0x1028697d4, 0x102869adc, None),  # movss (-1800.0,) : etat 5 : fin du virage z < 600 -> z < -1800
    ("imm", 0x1001af87b, "f30f58c1", "f30f5cc1"),  # addss %xmm1, %xmm0 -> subss %xmm1, %xmm0 : etat 3 : la cible reste 1800 m devant l'avion (z - (-1800)) au lieu de z + 600
]

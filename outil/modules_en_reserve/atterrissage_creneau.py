# -*- coding: utf-8 -*-
"""Atterrissages (reglage A) : creneau elargi seul, circuit d'origine.

FICHIER GENERE par outil/generateurs/generer_atterrissage.py (ne pas modifier a la main).
Fonction : c_vehicle_server_carrier::docking_manager_air::update, circuit d'attente des avions
(les helicos ne sont pas concernes). Logique d'origine : un avion ne recoit la piste qu'au tick ou il
passe le bas du virage arriere (la « porte », 3 km derriere le bateau), une fois par tour de 12,3 km.
Ici : la piste peut etre donnee sur tout le virage arriere (~2,7 km, ~35 s de vol).
EN RESERVE : touche les memes octets que le module atterrissage (reglage B), donc les deux ne
peuvent pas etre dans outil/modules/ en meme temps. A utiliser si le reglage B se revele plus lent.
"""
NOM = "atterrissage_creneau"
TITRE = "Atterrissages : creneau elargi (circuit d'origine)"
TYPE = "programme"

RETOUCHES = [
    # creneau elargi
    ("imm", 0x1001af900, "0f86ff010000", "0f860e000000"),  # jbe 0x1001afb05 -> 0x1001af914 : etat 1 : tester la piste a chaque tick, pas seulement au bas du virage
    ("imm", 0x1001af85b, "0f86a4020000", "0f86b3000000"),  # jbe 0x1001afb05 -> 0x1001af914 : etat 2 : tester la piste pendant le reste du virage arriere
    ("imm", 0x1001af867, "e999020000", "e9a8000000"),  # jmp 0x1001afb05 -> 0x1001af914 : etat 2 -> 3 : tester la piste aussi au moment du changement
]

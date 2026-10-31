# -*- coding: utf-8 -*-
"""Helicos : toucher sur la piste pres de l'ascenseur (z = -40) au lieu du milieu de la piste.

FICHIER GENERE par outil/generateurs/generer_helicos_ascenseur.py. Demande du moddeur le 24/10/2026 (« qu'il
atterrisse plus proche de l'ascenseur et pas qu'il aille jusqu'au bout de la piste »).
Jeu d'origine (partie helico de l'approche, docking_manager_air::update) : hauteur visee = 0,5 x (7 - z)
bornee -2..80 (7 = milieu de la piste) et point vise au plus z = runway_start + 120 = 52 : l'helico touche vers
z = 7..30 puis roule ~55-80 m en arriere jusqu'a taxi_a (z = -44). Ici, pour les helicos seulement :
  - hauteur visee = 0,5 x (-40 - z) (meme pente) : greffe de 3 instructions (subss 23,5 avant le maxss -2),
    branchee a 0x1001ad57a, logee a la fin du code mort de ImGui::ShowDemoWindow ;
  - point vise au plus z = runway_start + 48 = -20 (constante 48.0 lue a la place de 120.0) ;
  - train sorti et etat « atterrissage » a moins de 70 m du milieu de piste (z > -63) au lieu de 20 m (z > -13).
Les avions ne passent par aucune de ces instructions. Le Petrel lache toujours son vehicule juste avant de toucher.
"""
NOM = "helicos_pres_ascenseur"
TITRE = "Helicos : toucher pres de l'ascenseur (z = -40)"
TYPE = "programme"

RETOUCHES = [
    # movss 120.0 -> 48.0 : point vise au plus z = -20 (120.0 -> 48.0)
    ("rip", 0x1001ad3fc, "f30f100db4c36b02", 0x1028697b8, 0x102869af0, None),
    # movss 20.0 -> 70.0 : train sorti a z > -63 (20.0 -> 70.0)
    ("rip", 0x1001b1066, "f30f1005ce876b02", 0x10286983c, 0x1028698a0, None),
    # code ajoute (28 octets) : subss 23.5 ; maxss -2.0 ; jmp 0x1001ad582
    ("imm", 0x100061b80, "02e8ba618002e95cc0ffff4889c3488d3ddb889c02eb224889c3488d", "f30f5c0d10000000f30f5f0dc07c8002e9edb914000f1f000000bc41"),
    # maxss -2.0, %xmm1 -> jmp 0x100061b80 (hauteur visee de l'helico decalee de 23.5 m)
    ("imm", 0x1001ad57a, "f30f5f0dcec26b02", "e90146ebff909090"),
]

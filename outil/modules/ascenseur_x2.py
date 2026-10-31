# -*- coding: utf-8 -*-
"""Ascenseur x2 : sorties et retours d'avions environ 2x plus rapides, contre 2x plus d'energie
pour le systeme ASCENSEUR/GRUE. Valide en jeu le 23/10/2026 : 4 avions 3:50 -> 2:15 (temps de jeu).

  - energie  : part maximale du systeme ascenseur/grue 0,4 -> 0,8
               (c_vehicle_carrier_server_power_manager::build)
  - ascenseur: pas de la plateforme 0,025 -> 0,05 m/tick (c_vehicle_server_carrier::tick_server_type)
  - grue     : grue du hangar, horizontal 1/6 -> 1/3, vertical 1/30 -> 1/15 m/tick,
               rotation 0,04 -> 0,08 rad/tick (docking_manager_air::update)
  - roulage  : avions sur le pont, acceleration 0,05 -> 0,1 et plafond 2,5 -> 5 m/s
               (7 blocs dans docking_manager_air::update)
Detail et methode : mods/cc2-ascenseur-x2/ et la fiche DEMARRER de l'atelier.
"""
NOM = "ascenseur_x2"
TITRE = "Ascenseur x2 : avions 2x plus vite, energie x2"
TYPE = "programme"

RETOUCHES = [
    ("imm", 0x10019f0ad, "41c78718010000cdcccc3e", "41c78718010000cdcc4c3f"),
    # ascenseur
    ("rip", 0x10019455a, "f30f5f0d02556d02", 0x102869a64, 0x10286995c, 2),  # maxss
    ("rip", 0x100194562, "f30f5d0d0e546d02", 0x102869978, 0x1028697a4, 2),  # minss
    ("rip", 0x100194583, "f30f5e1ded536d02", 0x102869978, 0x1028697a4, 2),  # divss
    # grue
    ("rip", 0x1001ae8bc, "f30f103d10b26b02", 0x102869ad4, 0x102869750, 2),  # movss
    ("rip", 0x1001aea04, "f30f103dc8b06b02", 0x102869ad4, 0x102869750, 2),  # movss
    ("rip", 0x1001ae8c8, "f30f10158cae6b02", 0x10286975c, 0x1028b232c, 2),  # movss
    ("rip", 0x1001aea10, "f30f101d44ad6b02", 0x10286975c, 0x1028b232c, 2),  # movss
    ("rip", 0x1001ae8d4, "f30f5f35fcb06b02", 0x1028699d8, 0x102869c7c, 2),  # maxss
    ("rip", 0x1001ae968, "f30f5f1d68b06b02", 0x1028699d8, 0x102869c7c, 2),  # maxss
    ("rip", 0x1001aea1c, "f30f5f35b4af6b02", 0x1028699d8, 0x102869c7c, 2),  # maxss
    ("rip", 0x1001aeab8, "f30f5f1d18af6b02", 0x1028699d8, 0x102869c7c, 2),  # maxss
    ("rip", 0x1001aeba7, "f30f5f1d29ae6b02", 0x1028699d8, 0x102869c7c, 2),  # maxss
    ("rip", 0x1001ae8dc, "f30f5d35f0b06b02", 0x1028699d4, 0x102869b80, 2),  # minss
    ("rip", 0x1001ae970, "f30f100d5cb06b02", 0x1028699d4, 0x102869b80, 2),  # movss
    ("rip", 0x1001aea24, "f30f5d35a8af6b02", 0x1028699d4, 0x102869b80, 2),  # minss
    ("rip", 0x1001aeac0, "f30f100d0caf6b02", 0x1028699d4, 0x102869b80, 2),  # movss
    ("rip", 0x1001aebaf, "f30f100d1dae6b02", 0x1028699d4, 0x102869b80, 2),  # movss
    ("rip", 0x1001aeb2b, "f30f5f0dd1ae6b02", 0x102869a04, 0x102869974, 2),  # maxss
    ("rip", 0x1001aeb33, "f30f101d95ac6b02", 0x1028697d0, 0x10286986c, 2),  # movss
    # roulage
    ("rip", 0x1001ad6f9, "f30f5825a3c06b02", 0x1028697a4, 0x1028697b0, 2),  # addss
    ("rip", 0x1001adf35, "f30f582567b86b02", 0x1028697a4, 0x1028697b0, 2),  # addss
    ("rip", 0x1001ae02a, "f30f582572b76b02", 0x1028697a4, 0x1028697b0, 2),  # addss
    ("rip", 0x1001ae104, "f30f582598b66b02", 0x1028697a4, 0x1028697b0, 2),  # addss
    ("rip", 0x1001ae2c1, "f30f581ddbb46b02", 0x1028697a4, 0x1028697b0, 2),  # addss
    ("rip", 0x1001ae6e0, "f30f5825bcb06b02", 0x1028697a4, 0x1028697b0, 2),  # addss
    ("rip", 0x1001b010f, "f30f58258d966b02", 0x1028697a4, 0x1028697b0, 2),  # addss
    ("rip", 0x1001ad701, "f30f1015b3c06b02", 0x1028697bc, 0x10286976c, 2),  # movss
    ("rip", 0x1001adf41, "f30f101573b86b02", 0x1028697bc, 0x10286976c, 2),  # movss
    ("rip", 0x1001ae036, "f30f10157eb76b02", 0x1028697bc, 0x10286976c, 2),  # movss
    ("rip", 0x1001ae110, "f30f1015a4b66b02", 0x1028697bc, 0x10286976c, 2),  # movss
    ("rip", 0x1001ae2cd, "f30f1025e7b46b02", 0x1028697bc, 0x10286976c, 2),  # movss
    ("rip", 0x1001ae6e8, "f30f1015ccb06b02", 0x1028697bc, 0x10286976c, 2),  # movss
    ("rip", 0x1001b0117, "f30f10159d966b02", 0x1028697bc, 0x10286976c, 2),  # movss
]

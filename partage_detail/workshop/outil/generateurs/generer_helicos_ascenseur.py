#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generates the "helicopters on the elevator" modules from helicos_ascenseur.c.

1. compiles the graft (the block of machine code added to the executable; clang -arch x86_64),
   normal version and CONTROL version (which does nothing);
2. links it itself (mini linker) at address 0x10005af40, in the dead code of
   ImGui::ShowDemoWindow (never called by the game, neither by call nor by address);
3. writes the workshop modules: 1 "imm" patch for the added code + 3 hooks.

The "before" bytes are read from the rebuilt original executable (sauvegarde/build_mac_origine).
Usage: python3 outil/generateurs/generer_helicos_ascenseur.py
  -> outil/modules_en_reserve/helicos_ascenseur.py and outil/modules_en_reserve/helicos_temoin.py
     (copy into outil/modules/ the one you want to test: never both, they touch the same bytes)
"""
import hashlib, os, struct, subprocess, sys, tempfile

ICI = os.path.dirname(os.path.abspath(__file__))
OUTIL = os.path.dirname(ICI)
SOURCE = os.path.join(ICI, "helicos_ascenseur.c")
ORIGINE = os.path.join(os.path.dirname(OUTIL), "sauvegarde", "build_mac_origine")
RESERVE = os.path.join(OUTIL, "modules_en_reserve")
MD5_ORIGINE = "b0107170ddaf0245cbfee8a2d876aeb6"
BASE_FICHIER = 0x100000000

ZONE_DEBUT, ZONE_FIN = 0x10005af40, 0x100061c00     # ImGui::ShowDemoWindow(bool*) 0x10005af39 .. 0x100061c00

# game functions and data called by the graft (C names with "_", asm labels without)
JEU = {
    "_g_mul_m33_v3": 0x100005262,          # operator*(mat33_f64 const&, vec3_f64 const&)
    "_g_bay_index_attach": 0x10010c9ca,    # c_vehicle_server::get_available_vehicle_bay_index(e_vehicle_attachment_type, unsigned char)
    "_g_bay_index_type": 0x10010bc7e,      # c_vehicle_server::get_available_vehicle_bay_index(e_game_object_type, unsigned char)
    "_g_dock_immediate": 0x10010bd1a,      # c_vehicle_server::dock_immediate(c_map_server_base&, c_vehicle_server&, unsigned int)
    "_g_undock_immediate": 0x1001b5ffc,    # c_vehicle_server::undock_immediate(c_map_server_base&, mm_physics_scene&, c_vehicle_server&)
    "_g_set_attached_to": 0x10010cce8,     # c_vehicle_server::set_attached_to_vehicle_id(c_map_server_base&, unsigned int)
    "_g_set_att_transform": 0x10010ccb4,   # c_vehicle_server::vehicle_attachment::set_attachment_transform(mat34_f64 const&)
    "_g_create_physics": 0x1001b5292,      # c_vehicle_server::vehicle_attachment::create_physics(c_vehicle_server&, c_vehicle_server&)
    "_g_push_joint": 0x1000b431e,          # mm_vector<mm_physics_object_joint*>::push_back()
    "_g_push_event": 0x1000e3e24,          # mm_vector<c_message_server_to_client_tick::event*>::push_back()
    "_g_queue_erase": 0x1001a9508,         # mm_vector<docking_manager_air::queue_vehicle>::erase(unsigned int)
    "_g_queue_push": 0x10019a8c6,          # mm_vector<docking_manager_air::queue_vehicle>::push_back()
    "_g_mm_string_ctor": 0x1001d1484,      # mm_string::mm_string(char const*)
    "_g_get_link": 0x1001b5b86,            # c_game_object_definition::get_graph_link_by_name(mm_string const&) const
    "_g_path_from_link_rev": 0x1001b6138,  # c_vehicle_server_carrier::path_data::create_from_graph_link_reverse(...)
    "_g_new": 0x102867d04,                 # stub __Znwm (operator new)
    "_g_free": 0x102867e90,                # stub _free
    "_g_event_vtable": 0x1029c6090,        # vtable for event_vehicle_set_attached_to_vehicle + 0x10
    "_g_str_load_lift_lower": 0x10291e877, # "load_lift_lower"
    "g_ret_ace50": 0x1001ace50, "g_ret_acda9": 0x1001acda9,     # returns of H1
    "g_ret_ae787": 0x1001ae787, "g_ret_ae780": 0x1001ae780,     # returns of H2
    "g_ret_ae07c": 0x1001ae07c, "g_ret_b151b": 0x1001b151b,     # returns of H3
    "g_moins2": 0x102869850,                                     # -2.0 (minimum target height of the helicopter)
    "g_ret_ad582": 0x1001ad582,                                  # return of the touchdown near the elevator
}

# hooks: address, expected original bytes, graft entry point, description
BRANCHEMENTS = [
    (0x1001acd94, "4c896d904183be80000000ff", "_hl_h1", "entry of the return mode: movq %r13,-0x70(%rbp) ; cmpl $-1,0x80(%r14)"),
    (0x1001ad7af, "e9cc0f0000", "_hl_h2", "exit of the return mode: jmp 0x1001ae780"),
    (0x1001ae071, "41837e7cff0f849f340000", "_hl_h3", "taxiing 6 -> 7: cmpl $-1,0x7c(%r14) ; je 0x1001b151b"),
]

DRAPEAUX = ["-arch", "x86_64", "-O2", "-c", "-ffreestanding", "-fno-builtin", "-fno-stack-protector",
            "-fno-asynchronous-unwind-tables", "-fno-unwind-tables", "-fno-exceptions", "-fno-math-errno",
            "-mno-red-zone", "-fno-common", "-Wall", "-Wextra", "-Werror"]
SECTIONS_PRISES = ["__text", "__literal4", "__literal8", "__literal16", "__const"]


class Erreur(Exception):
    pass


def compiler(temoin, dossier):
    sortie = os.path.join(dossier, "temoin.o" if temoin else "greffe.o")
    cmd = ["clang"] + DRAPEAUX + (["-DTEMOIN", "-Wno-unused-function"] if temoin else []) + ["-o", sortie, SOURCE]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        raise Erreur("compilation: " + r.stderr)
    return open(sortie, "rb").read()


def lire_objet(o):
    magic, cpu, _, typ, ncmds, _, _, _ = struct.unpack_from("<IiiIIIII", o, 0)
    if magic != 0xfeedfacf or cpu != 0x01000007 or typ != 1:
        raise Erreur("x86_64 Mach-O object expected")
    pos, sections, syms = 32, [], []
    for _ in range(ncmds):
        cmd, taille = struct.unpack_from("<II", o, pos)
        if cmd == 0x19:
            nsect = struct.unpack_from("<I", o, pos + 64)[0]
            for k in range(nsect):
                s = pos + 72 + 80 * k
                nom = o[s:s + 16].rstrip(b"\0").decode()
                seg = o[s + 16:s + 32].rstrip(b"\0").decode()
                addr, size, off, align, reloff, nreloc = struct.unpack_from("<QQIIII", o, s + 32)
                sections.append(dict(nom=nom, seg=seg, addr=addr, size=size, off=off, align=align,
                                     reloff=reloff, nreloc=nreloc))
        elif cmd == 0x2:
            symoff, nsyms, stroff, _ = struct.unpack_from("<IIII", o, pos + 8)
            for k in range(nsyms):
                strx, ntype, nsect, _, val = struct.unpack_from("<IBBHQ", o, symoff + 16 * k)
                nom = o[stroff + strx:o.index(b"\0", stroff + strx)].decode()
                syms.append(dict(nom=nom, type=ntype, sect=nsect, val=val))
        pos += taille
    return sections, syms


def relier(o, base):
    sections, syms = lire_objet(o)
    for s in sections:
        if s["nom"] not in SECTIONS_PRISES and s["seg"] != "__LD":
            if s["size"]:
                raise Erreur("unexpected section %s,%s" % (s["seg"], s["nom"]))
    prises = [s for s in sections if s["nom"] in SECTIONS_PRISES and s["size"]]
    adresse = base
    for s in prises:
        a = 1 << s["align"]
        adresse = (adresse + a - 1) // a * a
        s["neuve"] = adresse
        adresse += s["size"]
    fin = adresse
    image = bytearray(b"\xcc" * (fin - base))     # int3 between the sections
    for s in prises:
        image[s["neuve"] - base:s["neuve"] - base + s["size"]] = o[s["off"]:s["off"] + s["size"]]

    def sect_de(n):      # section number 1.. of the object
        return sections[n - 1]

    def adresse_symbole(sym):
        if sym["type"] & 0x0e == 0x0e:        # N_SECT: defined in the graft
            s = sect_de(sym["sect"])
            if "neuve" not in s:
                raise Erreur("symbol %s in a section that was not taken" % sym["nom"])
            return s["neuve"] + sym["val"] - s["addr"]
        if sym["nom"] not in JEU:
            raise Erreur("unknown symbol: " + sym["nom"])
        return JEU[sym["nom"]]

    relocs = []
    for s in prises:
        for k in range(s["nreloc"]):
            r_addr, info = struct.unpack_from("<iI", o, s["reloff"] + 8 * k)
            num, pcrel, longueur, externe, typ = info & 0xffffff, (info >> 24) & 1, (info >> 25) & 3, (info >> 27) & 1, info >> 28
            if not pcrel or longueur != 2 or typ not in (1, 2, 6, 7, 8):
                raise Erreur("unsupported relocation: type %d pcrel %d length %d at %#x" % (typ, pcrel, longueur, r_addr))
            biais = {1: 0, 2: 0, 6: 1, 7: 2, 8: 4}[typ]
            p_neuf = s["neuve"] + r_addr
            p_vieux = s["addr"] + r_addr
            stocke = struct.unpack_from("<i", image, p_neuf - base)[0]
            if externe:
                # the assembler stores (addend - bias): real target = symbol + stored + bias (like ld64)
                sym = syms[num]
                cible = adresse_symbole(sym) + stocke + biais
                nom = sym["nom"]
            else:
                cs = sect_de(num)
                cible_vieille = p_vieux + 4 + biais + stocke
                if "neuve" not in cs or not cs["addr"] <= cible_vieille <= cs["addr"] + cs["size"]:
                    raise Erreur("local relocation outside section at %#x" % p_vieux)
                cible = cs["neuve"] + cible_vieille - cs["addr"]
                nom = cs["nom"]
            disp = cible - (p_neuf + 4 + biais)
            if not -2 ** 31 <= disp < 2 ** 31:
                raise Erreur("displacement too large at %#x" % p_neuf)
            struct.pack_into("<i", image, p_neuf - base, disp)
            relocs.append((p_neuf, cible, nom))
    points = {}
    for sym in syms:
        if sym["type"] & 0x0e == 0x0e and sym["type"] & 0x01:
            points[sym["nom"]] = adresse_symbole(sym)
    return bytes(image), points, relocs


def ecrire_module(chemin, nom, titre, doc, retouches, md5_modifie):
    lignes = ['# -*- coding: utf-8 -*-', '"""' + doc.strip() + '\n"""',
              'NOM = %r' % nom, 'TITRE = %r' % titre, 'TYPE = "programme"',
              '# md5 of the executable with this module alone: %s' % md5_modifie, '', 'RETOUCHES = [']
    for va, avant, apres, commentaire in retouches:
        lignes.append('    # %s' % commentaire)
        lignes.append('    ("imm", %#x, "%s", "%s"),' % (va, avant, apres))
    lignes.append(']')
    open(chemin, "w").write("\n".join(lignes) + "\n")


def generer(temoin, programme, dossier):
    o = compiler(temoin, dossier)
    image, points, relocs = relier(o, ZONE_DEBUT)
    if ZONE_DEBUT + len(image) > ZONE_FIN:
        raise Erreur("the graft exceeds the free zone")
    off = ZONE_DEBUT - BASE_FICHIER
    retouches = [(ZONE_DEBUT, programme[off:off + len(image)].hex(), image.hex(),
                  "added code (%d bytes) in place of ImGui::ShowDemoWindow, never called" % len(image))]
    for va, attendu, point, commentaire in BRANCHEMENTS:
        o2 = va - BASE_FICHIER
        n = len(attendu) // 2
        if programme[o2:o2 + n].hex() != attendu:
            raise Erreur("unexpected original bytes at %#x" % va)
        saut = b"\xe9" + struct.pack("<i", points[point] - (va + 5))
        retouches.append((va, attendu, (saut + b"\x90" * (n - 5)).hex(),
                          "%s -> jmp %s (%#x)" % (commentaire, point, points[point])))
    modifie = bytearray(programme)
    for va, avant, apres, _ in retouches:
        modifie[va - BASE_FICHIER:va - BASE_FICHIER + len(avant) // 2] = bytes.fromhex(apres)
    return retouches, hashlib.md5(modifie).hexdigest(), points, relocs, len(image)


DOC_NORMAL = """Helicopters landing directly on the elevator (two landings at the same time).

GENERATED FILE by outil/generateurs/generer_helicos_ascenseur.py from helicos_ascenseur.c
(do not edit by hand). Design: both helicopters (Razorbill, Petrel); waiting above the platform if it
is lowered; if the landing fails, the helicopter lands on the runway; only player carriers (a team that has
a connected player), not AI ones.
An "elevator lane" (field 0x84 of the air docking manager, unused during returns) takes one helicopter
from the queue at a time: it flies to above the platform, lands on it and goes down at once.
Meanwhile the other aircraft land on the runway as before. An aircraft taxiing to the elevator waits if a
helicopter is going down onto it (and the other way round).
Code added in the dead code of ImGui::ShowDemoWindow + 3 hooks in docking_manager_air::update.
Reference measurement (without this module): part 04 of the notes."""

DOC_TEMOIN = """CONTROL (TEMOIN) version of the "helicopters on the elevator" graft: changes nothing in the game.

GENERATED FILE by outil/generateurs/generer_helicos_ascenseur.py (-DTEMOIN version). Same hooks
and same location as the real module, but the function called on each tick does nothing. Used to
check in game, before any change of behaviour, that the added code runs without crashing (recalling an
aircraft is enough: the hook is crossed on every tick of the returns)."""


DOC_APPROCHE = """Helicopter approach to the RUNWAY twice as fast (~5 m/s -> ~10 m/s).

GENERATED FILE by outil/generateurs/generer_helicos_ascenseur.py.
In the original game, a helicopter landing on the runway aims at a point 50 m ahead of it (at most z = 52);
the autopilot corrects the error at 0.1 per metre, hence ~5 m/s and ~1:00 of approach (measured 2026-10-23).
Here the aimed point is 100 m ahead (constant 100.0, already present, read in place of 50.0): ~10 m/s
on the long straight line, same end of approach (the aimed point stays capped at z = 52). Instruction
specific to helicopters (after the get_is_rotor test at 0x1001ad3e1): planes are not affected. Does not touch
the helicopters of the elevator lane (module helicos_ascenseur), which have their own piloting."""

APPROCHE = (0x1001ad3ef, "f30f1005b5c46b02", 0x1028698ac, 0x1028697ac, 2.0)   # movss 50.0 -> 100.0


def ecrire_module_approche(programme):
    va, avant, ancienne, nouvelle, facteur = APPROCHE
    o = va - BASE_FICHIER
    if programme[o:o + 8].hex() != avant:
        raise Erreur("unexpected original bytes at %#x" % va)
    if va + 8 + struct.unpack_from("<i", programme, o + 4)[0] != ancienne:
        raise Erreur("the instruction at %#x does not read %#x" % (va, ancienne))
    lire = lambda a: struct.unpack_from("<f", programme, a - BASE_FICHIER)[0]
    if lire(nouvelle) != facteur * lire(ancienne):
        raise Erreur("constant %#x: %r instead of %r" % (nouvelle, lire(nouvelle), facteur * lire(ancienne)))
    chemin = os.path.join(RESERVE, "helicos_approche_x2.py")
    lignes = ['# -*- coding: utf-8 -*-', '"""' + DOC_APPROCHE + '\n"""', 'NOM = "helicos_approche_x2"',
              'TITRE = "Helicopters: runway approach 2x faster"', 'TYPE = "programme"', '',
              'RETOUCHES = [',
              '    # movss 50.0 -> 100.0: distance of the aimed point ahead of the helicopter (runway approach)',
              '    ("rip", %#x, "%s", %#x, %#x, %r),' % APPROCHE, ']']
    open(chemin, "w").write("\n".join(lignes) + "\n")
    print("helicos_approche_x2: 1 patch (%#x) -> %s" % (va, os.path.relpath(chemin, os.path.dirname(OUTIL))))


DOC_PRES = """Helicopters: touch down on the runway near the elevator (z = -40) instead of mid-runway.

GENERATED FILE by outil/generateurs/generer_helicos_ascenseur.py. Goal: land closer to the elevator
rather than going all the way to the end of the runway.
Original game (helicopter part of the approach, docking_manager_air::update): aimed height = 0.5 x (7 - z)
clamped to -2..80 (7 = middle of the runway) and aimed point at most z = runway_start + 120 = 52: the helicopter
touches down around z = 7..30 then taxis ~55-80 m back to taxi_a (z = -44). Here, for helicopters only:
  - aimed height = 0.5 x (-40 - z) (same slope): graft of 3 instructions (subss 23.5 before the maxss -2),
    hooked at 0x1001ad57a, housed at the end of the dead code of ImGui::ShowDemoWindow;
  - aimed point at most z = runway_start + 48 = -20 (constant 48.0 read in place of 120.0);
  - landing gear down and "landing" state at less than 70 m from mid-runway (z > -63) instead of 20 m (z > -13).
Planes go through none of these instructions. The Petrel always releases its vehicle just before touching down."""

Z_TOUCHER = -40.0
PRES = [
    (0x1001ad3fc, "f30f100db4c36b02", 0x1028697b8, 0x102869af0, "movss 120.0 -> 48.0: aimed point at most z = -20"),
    (0x1001b1066, "f30f1005ce876b02", 0x10286983c, 0x1028698a0, "movss 20.0 -> 70.0: landing gear down at z > -63"),
]
CROCHET_PRES = (0x1001ad57a, "f30f5f0dcec26b02")      # maxss -2.0, %xmm1
ZONE_PRES = 0x100061b80                               # end of the dead code of ImGui::ShowDemoWindow
ASM_PRES = """
.text
.globl _pa_crochet
_pa_crochet:
    subss L_decalage(%%rip), %%xmm1
    maxss g_moins2(%%rip), %%xmm1
    jmp g_ret_ad582
.p2align 2
L_decalage:
    .long 0x%08x
"""


def ecrire_module_pres(programme, dossier):
    decalage = 0.5 * (7.0 - Z_TOUCHER)          # middle of the runway (runway_start + runway_end) / 2 = 7
    lire = lambda a: struct.unpack_from("<f", programme, a - BASE_FICHIER)[0]
    retouches = []
    for va, avant, ancienne, nouvelle, commentaire in PRES:
        o = va - BASE_FICHIER
        if programme[o:o + 8].hex() != avant or va + 8 + struct.unpack_from("<i", programme, o + 4)[0] != ancienne:
            raise Erreur("unexpected instruction at %#x" % va)
        retouches.append((va, avant, ancienne, nouvelle, commentaire, lire(ancienne), lire(nouvelle)))
    source = os.path.join(dossier, "pres.s")
    open(source, "w").write(ASM_PRES % struct.unpack("<I", struct.pack("<f", decalage))[0])
    objet = os.path.join(dossier, "pres.o")
    r = subprocess.run(["clang", "-arch", "x86_64", "-c", "-o", objet, source], capture_output=True, text=True)
    if r.returncode:
        raise Erreur("assembly: " + r.stderr)
    image, points, relocs = relier(open(objet, "rb").read(), ZONE_PRES)
    if ZONE_PRES + len(image) > ZONE_FIN:
        raise Erreur("the graft exceeds the free zone")
    va, avant = CROCHET_PRES
    if programme[va - BASE_FICHIER:va - BASE_FICHIER + 8].hex() != avant:
        raise Erreur("unexpected original bytes at %#x" % va)
    saut = b"\xe9" + struct.pack("<i", points["_pa_crochet"] - (va + 5)) + b"\x90" * 3
    o = ZONE_PRES - BASE_FICHIER
    chemin = os.path.join(RESERVE, "helicos_pres_ascenseur.py")
    lignes = ['# -*- coding: utf-8 -*-', '"""' + DOC_PRES + '\n"""', 'NOM = "helicos_pres_ascenseur"',
              'TITRE = "Helicopters: touchdown near the elevator (z = -40)"', 'TYPE = "programme"', '',
              'RETOUCHES = [']
    for va2, avant2, ancienne, nouvelle, commentaire, v1, v2 in retouches:
        lignes.append('    # %s (%r -> %r)' % (commentaire, v1, v2))
        lignes.append('    ("rip", %#x, "%s", %#x, %#x, None),' % (va2, avant2, ancienne, nouvelle))
    lignes.append('    # added code (%d bytes): subss %r ; maxss -2.0 ; jmp 0x1001ad582' % (len(image), decalage))
    lignes.append('    ("imm", %#x, "%s", "%s"),' % (ZONE_PRES, programme[o:o + len(image)].hex(), image.hex()))
    lignes.append('    # maxss -2.0, %%xmm1 -> jmp %#x (helicopter aimed height shifted by %r m)' % (points["_pa_crochet"], decalage))
    lignes.append('    ("imm", %#x, "%s", "%s"),' % (va, avant, saut.hex()))
    lignes.append(']')
    open(chemin, "w").write("\n".join(lignes) + "\n")
    print("helicos_pres_ascenseur: 2 constants + %d bytes added at %#x -> %s"
          % (len(image), ZONE_PRES, os.path.relpath(chemin, os.path.dirname(OUTIL))))


def main():
    programme = open(ORIGINE, "rb").read()
    if hashlib.md5(programme).hexdigest() != MD5_ORIGINE:
        raise Erreur("sauvegarde/build_mac_origine is not the expected original executable")
    ecrire_module_approche(programme)
    with tempfile.TemporaryDirectory(prefix="greffe_cc2_") as dossier:
        ecrire_module_pres(programme, dossier)
    with tempfile.TemporaryDirectory(prefix="greffe_cc2_") as dossier:
        for temoin in (True, False):
            retouches, md5_modifie, points, relocs, taille = generer(temoin, programme, dossier)
            nom = "helicos_temoin" if temoin else "helicos_ascenseur"
            titre = ("Helicopters on the elevator: CONTROL (changes nothing)" if temoin
                     else "Helicopters landed on the elevator (2 landings at a time)")
            chemin = os.path.join(RESERVE, nom + ".py")
            ecrire_module(chemin, nom, titre, DOC_TEMOIN if temoin else DOC_NORMAL, retouches, md5_modifie)
            print("%s: %d bytes of code, %d links, md5 with this module alone %s" % (nom, taille, len(relocs), md5_modifie))
            for p, a in sorted(points.items(), key=lambda x: x[1]):
                print("    %-10s %#x" % (p, a))
            print("    -> " + os.path.relpath(chemin, os.path.dirname(OUTIL)))


if __name__ == "__main__":
    try:
        main()
    except Erreur as e:
        sys.exit("ERROR: %s" % e)

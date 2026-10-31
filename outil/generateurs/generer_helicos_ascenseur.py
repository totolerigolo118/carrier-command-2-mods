#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Genere les modules « helicos sur l'ascenseur » a partir de helicos_ascenseur.c.

1. compile la greffe (clang -arch x86_64), version normale et version TEMOIN (qui ne fait rien) ;
2. la relie elle-meme (mini editeur de liens) a l'adresse 0x10005af40, dans le code mort de
   ImGui::ShowDemoWindow (jamais appele par le jeu, ni par appel ni par adresse) ;
3. ecrit les modules de l'atelier : 1 retouche « imm » pour le code ajoute + 3 branchements.

Les octets « avant » sont lus dans le programme d'origine reconstruit (sauvegarde/build_mac_origine).
Usage : python3 outil/generateurs/generer_helicos_ascenseur.py
  -> outil/modules_en_reserve/helicos_ascenseur.py et outil/modules_en_reserve/helicos_temoin.py
     (on copie dans outil/modules/ celui qu'on veut tester : jamais les deux, ils touchent les memes octets)
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

# fonctions et donnees du jeu appelees par la greffe (noms C avec « _ », etiquettes asm sans)
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
    "g_ret_ace50": 0x1001ace50, "g_ret_acda9": 0x1001acda9,     # retours de H1
    "g_ret_ae787": 0x1001ae787, "g_ret_ae780": 0x1001ae780,     # retours de H2
    "g_ret_ae07c": 0x1001ae07c, "g_ret_b151b": 0x1001b151b,     # retours de H3
    "g_moins2": 0x102869850,                                     # -2.0 (hauteur visee minimale de l'helico)
    "g_ret_ad582": 0x1001ad582,                                  # retour du toucher pres de l'ascenseur
}

# branchements : adresse, octets d'origine attendus, point d'entree de la greffe, longueur remplacee
BRANCHEMENTS = [
    (0x1001acd94, "4c896d904183be80000000ff", "_hl_h1", "entree du mode retours : movq %r13,-0x70(%rbp) ; cmpl $-1,0x80(%r14)"),
    (0x1001ad7af, "e9cc0f0000", "_hl_h2", "sortie du mode retours : jmp 0x1001ae780"),
    (0x1001ae071, "41837e7cff0f849f340000", "_hl_h3", "roulage 6 -> 7 : cmpl $-1,0x7c(%r14) ; je 0x1001b151b"),
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
        raise Erreur("compilation : " + r.stderr)
    return open(sortie, "rb").read()


def lire_objet(o):
    magic, cpu, _, typ, ncmds, _, _, _ = struct.unpack_from("<IiiIIIII", o, 0)
    if magic != 0xfeedfacf or cpu != 0x01000007 or typ != 1:
        raise Erreur("objet Mach-O x86_64 attendu")
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
                raise Erreur("section inattendue %s,%s" % (s["seg"], s["nom"]))
    prises = [s for s in sections if s["nom"] in SECTIONS_PRISES and s["size"]]
    adresse = base
    for s in prises:
        a = 1 << s["align"]
        adresse = (adresse + a - 1) // a * a
        s["neuve"] = adresse
        adresse += s["size"]
    fin = adresse
    image = bytearray(b"\xcc" * (fin - base))     # int3 entre les sections
    for s in prises:
        image[s["neuve"] - base:s["neuve"] - base + s["size"]] = o[s["off"]:s["off"] + s["size"]]

    def sect_de(n):      # numero de section 1.. de l'objet
        return sections[n - 1]

    def adresse_symbole(sym):
        if sym["type"] & 0x0e == 0x0e:        # N_SECT : defini dans la greffe
            s = sect_de(sym["sect"])
            if "neuve" not in s:
                raise Erreur("symbole %s dans une section non prise" % sym["nom"])
            return s["neuve"] + sym["val"] - s["addr"]
        if sym["nom"] not in JEU:
            raise Erreur("symbole inconnu : " + sym["nom"])
        return JEU[sym["nom"]]

    relocs = []
    for s in prises:
        for k in range(s["nreloc"]):
            r_addr, info = struct.unpack_from("<iI", o, s["reloff"] + 8 * k)
            num, pcrel, longueur, externe, typ = info & 0xffffff, (info >> 24) & 1, (info >> 25) & 3, (info >> 27) & 1, info >> 28
            if not pcrel or longueur != 2 or typ not in (1, 2, 6, 7, 8):
                raise Erreur("relocation non geree : type %d pcrel %d longueur %d a %#x" % (typ, pcrel, longueur, r_addr))
            biais = {1: 0, 2: 0, 6: 1, 7: 2, 8: 4}[typ]
            p_neuf = s["neuve"] + r_addr
            p_vieux = s["addr"] + r_addr
            stocke = struct.unpack_from("<i", image, p_neuf - base)[0]
            if externe:
                # l'assembleur stocke (addend - biais) : cible reelle = symbole + stocke + biais (comme ld64)
                sym = syms[num]
                cible = adresse_symbole(sym) + stocke + biais
                nom = sym["nom"]
            else:
                cs = sect_de(num)
                cible_vieille = p_vieux + 4 + biais + stocke
                if "neuve" not in cs or not cs["addr"] <= cible_vieille <= cs["addr"] + cs["size"]:
                    raise Erreur("relocation locale hors section a %#x" % p_vieux)
                cible = cs["neuve"] + cible_vieille - cs["addr"]
                nom = cs["nom"]
            disp = cible - (p_neuf + 4 + biais)
            if not -2 ** 31 <= disp < 2 ** 31:
                raise Erreur("deplacement trop grand a %#x" % p_neuf)
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
              '# md5 du programme avec ce module seul : %s' % md5_modifie, '', 'RETOUCHES = [']
    for va, avant, apres, commentaire in retouches:
        lignes.append('    # %s' % commentaire)
        lignes.append('    ("imm", %#x, "%s", "%s"),' % (va, avant, apres))
    lignes.append(']')
    open(chemin, "w").write("\n".join(lignes) + "\n")


def generer(temoin, programme, dossier):
    o = compiler(temoin, dossier)
    image, points, relocs = relier(o, ZONE_DEBUT)
    if ZONE_DEBUT + len(image) > ZONE_FIN:
        raise Erreur("la greffe depasse la zone libre")
    off = ZONE_DEBUT - BASE_FICHIER
    retouches = [(ZONE_DEBUT, programme[off:off + len(image)].hex(), image.hex(),
                  "code ajoute (%d octets) a la place de ImGui::ShowDemoWindow, jamais appele" % len(image))]
    for va, attendu, point, commentaire in BRANCHEMENTS:
        o2 = va - BASE_FICHIER
        n = len(attendu) // 2
        if programme[o2:o2 + n].hex() != attendu:
            raise Erreur("octets d'origine inattendus a %#x" % va)
        saut = b"\xe9" + struct.pack("<i", points[point] - (va + 5))
        retouches.append((va, attendu, (saut + b"\x90" * (n - 5)).hex(),
                          "%s -> jmp %s (%#x)" % (commentaire, point, points[point])))
    modifie = bytearray(programme)
    for va, avant, apres, _ in retouches:
        modifie[va - BASE_FICHIER:va - BASE_FICHIER + len(avant) // 2] = bytes.fromhex(apres)
    return retouches, hashlib.md5(modifie).hexdigest(), points, relocs, len(image)


DOC_NORMAL = """Helicos poses directement sur l'ascenseur (deux atterrissages en meme temps).

FICHIER GENERE par outil/generateurs/generer_helicos_ascenseur.py a partir de helicos_ascenseur.c
(ne pas modifier a la main). Choix du moddeur le 23/10/2026 : les deux helicos (Razorbill, Petrel) ;
attente au-dessus de la plateforme si elle est descendue ; si la pose echoue, il se pose sur la piste ;
seulement les porte-avions des joueurs (une equipe qui a un joueur connecte), pas ceux de l'IA.
Une « voie ascenseur » (case 0x84 du gestionnaire des avions, inutilisee pendant les retours) prend un
helico de la file a la fois : il vole jusqu'au-dessus de la plateforme, se pose dessus et descend aussitot.
Pendant ce temps les autres appareils se posent sur la piste comme avant. Un appareil qui roule vers
l'ascenseur attend si un helico est en train de descendre dessus (et inversement).
Code ajoute dans le code mort de ImGui::ShowDemoWindow + 3 branchements dans docking_manager_air::update.
Mesure de reference (sans ce module) : etudes/MESURES_helicos.md."""

DOC_TEMOIN = """TEMOIN de la greffe « helicos sur l'ascenseur » : ne change rien au jeu.

FICHIER GENERE par outil/generateurs/generer_helicos_ascenseur.py (version -DTEMOIN). Memes branchements
et meme emplacement que le vrai module, mais la fonction appelee a chaque tick ne fait rien. Sert a
verifier en jeu, avant tout changement de comportement, que le code ajoute s'execute sans planter
(rappeler un appareil suffit : le branchement est traverse a chaque tick des retours)."""


DOC_APPROCHE = """Approche des helicos vers la PISTE deux fois plus rapide (~5 m/s -> ~10 m/s).

FICHIER GENERE par outil/generateurs/generer_helicos_ascenseur.py. Demande du moddeur le 24/10/2026.
Dans le jeu d'origine, un helico qui se pose sur la piste vise un point 50 m devant lui (au plus z = 52) ;
le pilote automatique corrige l'ecart a 0,1 par metre, d'ou ~5 m/s et ~1:00 d'approche (mesure du 23/10).
Ici le point vise est 100 m devant lui (constante 100.0 deja presente, lue a la place de 50.0) : ~10 m/s
sur la longue ligne droite, meme fin d'approche (le point vise reste borne a z = 52). Instruction propre
aux helicos (apres le test get_is_rotor a 0x1001ad3e1) : les avions ne sont pas concernes. Ne touche pas
les helicos de la voie ascenseur (module helicos_ascenseur), qui ont leur propre pilotage."""

APPROCHE = (0x1001ad3ef, "f30f1005b5c46b02", 0x1028698ac, 0x1028697ac, 2.0)   # movss 50.0 -> 100.0


def ecrire_module_approche(programme):
    va, avant, ancienne, nouvelle, facteur = APPROCHE
    o = va - BASE_FICHIER
    if programme[o:o + 8].hex() != avant:
        raise Erreur("octets d'origine inattendus a %#x" % va)
    if va + 8 + struct.unpack_from("<i", programme, o + 4)[0] != ancienne:
        raise Erreur("l'instruction a %#x ne lit pas %#x" % (va, ancienne))
    lire = lambda a: struct.unpack_from("<f", programme, a - BASE_FICHIER)[0]
    if lire(nouvelle) != facteur * lire(ancienne):
        raise Erreur("constante %#x : %r au lieu de %r" % (nouvelle, lire(nouvelle), facteur * lire(ancienne)))
    chemin = os.path.join(RESERVE, "helicos_approche_x2.py")
    lignes = ['# -*- coding: utf-8 -*-', '"""' + DOC_APPROCHE + '\n"""', 'NOM = "helicos_approche_x2"',
              'TITRE = "Helicos : approche de la piste 2x plus rapide"', 'TYPE = "programme"', '',
              'RETOUCHES = [',
              '    # movss 50.0 -> 100.0 : distance du point vise devant l\'helico (approche de la piste)',
              '    ("rip", %#x, "%s", %#x, %#x, %r),' % APPROCHE, ']']
    open(chemin, "w").write("\n".join(lignes) + "\n")
    print("helicos_approche_x2 : 1 retouche (%#x) -> %s" % (va, os.path.relpath(chemin, os.path.dirname(OUTIL))))


DOC_PRES = """Helicos : toucher sur la piste pres de l'ascenseur (z = -40) au lieu du milieu de la piste.

FICHIER GENERE par outil/generateurs/generer_helicos_ascenseur.py. Demande du moddeur le 24/10/2026 (« qu'il
atterrisse plus proche de l'ascenseur et pas qu'il aille jusqu'au bout de la piste »).
Jeu d'origine (partie helico de l'approche, docking_manager_air::update) : hauteur visee = 0,5 x (7 - z)
bornee -2..80 (7 = milieu de la piste) et point vise au plus z = runway_start + 120 = 52 : l'helico touche vers
z = 7..30 puis roule ~55-80 m en arriere jusqu'a taxi_a (z = -44). Ici, pour les helicos seulement :
  - hauteur visee = 0,5 x (-40 - z) (meme pente) : greffe de 3 instructions (subss 23,5 avant le maxss -2),
    branchee a 0x1001ad57a, logee a la fin du code mort de ImGui::ShowDemoWindow ;
  - point vise au plus z = runway_start + 48 = -20 (constante 48.0 lue a la place de 120.0) ;
  - train sorti et etat « atterrissage » a moins de 70 m du milieu de piste (z > -63) au lieu de 20 m (z > -13).
Les avions ne passent par aucune de ces instructions. Le Petrel lache toujours son vehicule juste avant de toucher."""

Z_TOUCHER = -40.0
PRES = [
    (0x1001ad3fc, "f30f100db4c36b02", 0x1028697b8, 0x102869af0, "movss 120.0 -> 48.0 : point vise au plus z = -20"),
    (0x1001b1066, "f30f1005ce876b02", 0x10286983c, 0x1028698a0, "movss 20.0 -> 70.0 : train sorti a z > -63"),
]
CROCHET_PRES = (0x1001ad57a, "f30f5f0dcec26b02")      # maxss -2.0, %xmm1
ZONE_PRES = 0x100061b80                               # fin du code mort de ImGui::ShowDemoWindow
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
    decalage = 0.5 * (7.0 - Z_TOUCHER)          # milieu de piste (runway_start + runway_end) / 2 = 7
    lire = lambda a: struct.unpack_from("<f", programme, a - BASE_FICHIER)[0]
    retouches = []
    for va, avant, ancienne, nouvelle, commentaire in PRES:
        o = va - BASE_FICHIER
        if programme[o:o + 8].hex() != avant or va + 8 + struct.unpack_from("<i", programme, o + 4)[0] != ancienne:
            raise Erreur("instruction inattendue a %#x" % va)
        retouches.append((va, avant, ancienne, nouvelle, commentaire, lire(ancienne), lire(nouvelle)))
    source = os.path.join(dossier, "pres.s")
    open(source, "w").write(ASM_PRES % struct.unpack("<I", struct.pack("<f", decalage))[0])
    objet = os.path.join(dossier, "pres.o")
    r = subprocess.run(["clang", "-arch", "x86_64", "-c", "-o", objet, source], capture_output=True, text=True)
    if r.returncode:
        raise Erreur("assemblage : " + r.stderr)
    image, points, relocs = relier(open(objet, "rb").read(), ZONE_PRES)
    if ZONE_PRES + len(image) > ZONE_FIN:
        raise Erreur("la greffe depasse la zone libre")
    va, avant = CROCHET_PRES
    if programme[va - BASE_FICHIER:va - BASE_FICHIER + 8].hex() != avant:
        raise Erreur("octets d'origine inattendus a %#x" % va)
    saut = b"\xe9" + struct.pack("<i", points["_pa_crochet"] - (va + 5)) + b"\x90" * 3
    o = ZONE_PRES - BASE_FICHIER
    chemin = os.path.join(RESERVE, "helicos_pres_ascenseur.py")
    lignes = ['# -*- coding: utf-8 -*-', '"""' + DOC_PRES + '\n"""', 'NOM = "helicos_pres_ascenseur"',
              'TITRE = "Helicos : toucher pres de l\'ascenseur (z = -40)"', 'TYPE = "programme"', '',
              'RETOUCHES = [']
    for va2, avant2, ancienne, nouvelle, commentaire, v1, v2 in retouches:
        lignes.append('    # %s (%r -> %r)' % (commentaire, v1, v2))
        lignes.append('    ("rip", %#x, "%s", %#x, %#x, None),' % (va2, avant2, ancienne, nouvelle))
    lignes.append('    # code ajoute (%d octets) : subss %r ; maxss -2.0 ; jmp 0x1001ad582' % (len(image), decalage))
    lignes.append('    ("imm", %#x, "%s", "%s"),' % (ZONE_PRES, programme[o:o + len(image)].hex(), image.hex()))
    lignes.append('    # maxss -2.0, %%xmm1 -> jmp %#x (hauteur visee de l\'helico decalee de %r m)' % (points["_pa_crochet"], decalage))
    lignes.append('    ("imm", %#x, "%s", "%s"),' % (va, avant, saut.hex()))
    lignes.append(']')
    open(chemin, "w").write("\n".join(lignes) + "\n")
    print("helicos_pres_ascenseur : 2 constantes + %d octets ajoutes a %#x -> %s"
          % (len(image), ZONE_PRES, os.path.relpath(chemin, os.path.dirname(OUTIL))))


def main():
    programme = open(ORIGINE, "rb").read()
    if hashlib.md5(programme).hexdigest() != MD5_ORIGINE:
        raise Erreur("sauvegarde/build_mac_origine n'est pas le programme d'origine attendu")
    ecrire_module_approche(programme)
    with tempfile.TemporaryDirectory(prefix="greffe_cc2_") as dossier:
        ecrire_module_pres(programme, dossier)
    with tempfile.TemporaryDirectory(prefix="greffe_cc2_") as dossier:
        for temoin in (True, False):
            retouches, md5_modifie, points, relocs, taille = generer(temoin, programme, dossier)
            nom = "helicos_temoin" if temoin else "helicos_ascenseur"
            titre = ("Helicos sur l'ascenseur : TEMOIN (ne change rien)" if temoin
                     else "Helicos poses sur l'ascenseur (2 atterrissages a la fois)")
            chemin = os.path.join(RESERVE, nom + ".py")
            ecrire_module(chemin, nom, titre, DOC_TEMOIN if temoin else DOC_NORMAL, retouches, md5_modifie)
            print("%s : %d octets de code, %d liens, md5 avec ce module seul %s" % (nom, taille, len(relocs), md5_modifie))
            for p, a in sorted(points.items(), key=lambda x: x[1]):
                print("    %-10s %#x" % (p, a))
            print("    -> " + os.path.relpath(chemin, os.path.dirname(OUTIL)))


if __name__ == "__main__":
    try:
        main()
    except Erreur as e:
        sys.exit("ERREUR : %s" % e)

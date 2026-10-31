"""Compte, dans le code entier de deux exe, les accès mémoire [registre + décalage] pour les décalages de champs du SDK.
Si la structure d'un objet avait changé entre les deux builds, les nombres d'accès à ses décalages changeraient.
Lit aussi les relocations : les 3 cases de la table du serveur sont-elles relocalisées dans le nouvel exe ?

Usage : python -I -B compter_decalages.py <ancien.exe> <nouveau.exe>
"""
import collections
import struct
import sys

import capstone as cs

DECALAGES = {'v_id': 0x80, 'v_definition': 0x84, 'v_bodies': 0x8c, 'v_wheels': 0xac, 'v_team': 0x108, 'v_attached': 0x10c,
             'v_dock_vehicle': 0x114, 'v_dock_tile': 0x118, 'v_dock_airfield': 0x11c, 'v_fuel': 0x120,
             'v_waypoints': 0x140, 'v_sync_count': 0x150, 'v_attachments': 0x15c, 'v_flight_state': 0x170,
             'v_dock_state': 0x174, 'v_hp': 0x180, 'v_team_object': 0x1a8, 'v_control_mode': 0x1d0,
             'v_control_target': 0x1d8, 'v_control_speed': 0x1f8, 'v_control_power': 0x1fc, 'v_control_taxi': 0x200,
             'v_sync_data': 0x230, 's_vehicle_map': 0x344, 's_vehicles': 0x37c, 's_tile_map': 0x42c, 's_tiles': 0x440,
             's_broadcast': 0x514, 'i_airfields': 0x154, 'env_nodes': 0x180, 'a_dock_queue': 0xcc, 'a_undock_queue': 0xdc,
             'a_tile': 0xf0, 'a_end_node': 0xb4, 'a_start_node': 0xb8, 'a_path': 0xbc}


def lire(p):
    b = open(p, 'rb').read()
    e = struct.unpack_from('<I', b, 0x3c)[0]
    n = struct.unpack_from('<H', b, e + 6)[0]
    opt = struct.unpack_from('<H', b, e + 20)[0]
    dllcar = struct.unpack_from('<H', b, e + 24 + 70)[0]
    reloc = struct.unpack_from('<II', b, e + 24 + 96 + 8 * 5)
    secs = []
    for i in range(n):
        s = e + 24 + opt + 40 * i
        vs, rva, rs, rp = struct.unpack_from('<IIII', b, s + 8)
        secs.append((b[s:s + 8].rstrip(b'\0'), rva, vs, rp, rs))
    return b, secs, dllcar, reloc


def off(secs, rva):
    for _, r, vs, rp, rs in secs:
        if r <= rva < r + min(vs, rs):
            return rp + rva - r


def compter(p):
    b, secs, _, _ = lire(p)
    _, rva, vs, rp, rs = secs[0]
    md = cs.Cs(cs.CS_ARCH_X86, cs.CS_MODE_32)
    md.skipdata = True
    voulus = set(DECALAGES.values())
    c = collections.Counter()
    for i in md.disasm(b[rp:rp + min(vs, rs)], 0x400000 + rva):
        s = i.op_str
        if '[' in s and '+ 0x' in s:
            for part in s.split('[')[1:]:
                expr = part.split(']')[0]
                if '+ 0x' in expr and '*' not in expr.split('+ 0x')[-1]:
                    try:
                        v = int(expr.split('+ 0x')[-1], 16)
                    except ValueError:
                        continue
                    if v in voulus:
                        c[v] += 1
    return c


def relocalisees(p, vas):
    b, secs, dllcar, (rrva, rtaille) = lire(p)
    o, fin = off(secs, rrva), off(secs, rrva) + rtaille
    cibles = set()
    while o < fin:
        page, taille = struct.unpack_from('<II', b, o)
        if not taille:
            break
        for k in range((taille - 8) // 2):
            e, = struct.unpack_from('<H', b, o + 8 + 2 * k)
            if e >> 12 == 3:
                cibles.add(0x400000 + page + (e & 0xfff))
        o += taille
    return dllcar, {hex(v): v in cibles for v in vas}


def main():
    a, n = sys.argv[1:3]
    print('relocations ancien (DllCharacteristics, cases 0xd34bc4/8/c) :', relocalisees(a, [0xd34bc4, 0xd34bc8, 0xd34bcc]))
    print('relocations nouveau (DllCharacteristics, cases 0xd34bfc/0xd34c00/0xd34c04) :', relocalisees(n, [0xd34bfc, 0xd34c00, 0xd34c04]))
    ca, cn = compter(a), compter(n)
    print('\n%-18s %-6s %8s %8s %s' % ('champ', 'décal.', 'ancien', 'nouveau', 'écart'))
    for nom, v in DECALAGES.items():
        print('%-18s %#-6x %8d %8d %+d' % (nom, v, ca[v], cn[v], cn[v] - ca[v]))


if __name__ == '__main__':
    main()

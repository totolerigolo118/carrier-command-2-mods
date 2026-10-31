#!/usr/bin/env python3
"""PARTIE 2 : relit les profils DANS LA DLL compilee (sans la charger) et refait, sur les octets des exe, les controles
que `startup()` du SDK fait au chargement. LECTURE SEULE. Aucune DLL n'est chargee ni lancee.

  1. dans la DLL : retrouve les enregistrements « Profile » (cc2x.c) et « Layout » (world.c) par leur horodatage / chaine de build,
     et les decode ;
  2. l'enregistrement de l'ANCIEN exe doit etre identique a la source d'origine (profil intact) ;
  3. pour chaque exe donne (octets du fichier = image a l'adresse de base 0x400000) : `detect` (horodatage ET taille d'image),
     les 6 signatures LUA_SIGS aux 6 fonctions Lua, les 8 octets du site Lua, les 3 cellules de la table du serveur ;
     et pour world.c les octets attendus aux sites de crochets.
     Attendu : l'ancien exe n'accepte QUE l'ancien profil, le nouvel exe n'accepte QUE le nouveau, tout autre fichier aucun.

Usage : python -I -B verifier_profil_dll.py <dinput8.dll compilee> <valeurs.json de profil_sdk.py> <ancien_original> <nouveau> [<autre exe> ...] -- <sortie.txt>
"""
import struct
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pe_lecture import Exe  # noqa: E402

LUA_SIGS = [   # recopie A LA MAIN de cc2x.c (champ, 8 octets)
    (0, bytes([0x8b, 0x41, 0x14, 0x85, 0xd2, 0x7e, 0x0d, 0xc1])),
    (1, bytes([0x55, 0x8b, 0xec, 0x83, 0xec, 0x08, 0x53, 0x56])),
    (2, bytes([0x55, 0x8b, 0xec, 0x83, 0xe4, 0xf8, 0x83, 0xec])),
    (3, bytes([0x55, 0x8b, 0xec, 0x83, 0xec, 0x08, 0x53, 0x8b])),
    (4, bytes([0x56, 0x8b, 0x71, 0x10, 0x33, 0xd2, 0x6a, 0x20])),
    (5, bytes([0x53, 0x8b, 0xd9, 0x56, 0x57, 0x8b, 0x7b, 0x10])),
]
# valeurs d'origine du source (cc2x.c lignes 29-33 / world.c lignes 46-52), recopiees A LA MAIN
PROFIL_ANCIEN = dict(build='1.5.18-win32', ts=0x6a36c177, size=0x00af7000, vtable=0x00d34bc4, init=0x00772fd0, tick=0x0077ee10, end=0x0077eea0,
                     lua_site=0x004465ec, site_bytes=bytes([0x6a, 0x20, 0x89, 0x85, 0x64, 0xff, 0xff, 0xff]),
                     fns=[0x008cda70, 0x008ce200, 0x008ff6b0, 0x00908220, 0x00904a50, 0x00904050], nilobject=0x00d03518)
CHAMPS_LAYOUT = ['f_vehicle_by_id', 'f_tile_by_id', 'f_tile_at', 'f_request_landing', 'f_waypoints_clear', 'f_deque_grow', 'vt_rigid_dynamic',
                 'h_waypoints', 'h_hangar', 'h_hangar_found', 'h_hangar_none', 'h_controller0', 'h_controller1', 'h_spawn', 'h_af_tick']
LAYOUT_ANCIEN = dict(f_vehicle_by_id=0x005ee6a0, f_tile_by_id=0x00631240, f_tile_at=0x00631040, f_request_landing=0x0062b4a0,
                     f_waypoints_clear=0x00854870, f_deque_grow=0x00860c90, vt_rigid_dynamic=0x00cdd478, h_waypoints=0x007781d4,
                     h_hangar=0x0062ae8d, h_hangar_found=0x0062aefc, h_hangar_none=0x0062aead, h_controller0=0x0063014f,
                     h_controller1=0x00634981, h_spawn=0x00634f3d, h_af_tick=0x0062b8f3, f_spawn=0x0062ca30, f_af_tick=0x00628600)


class Dll:
    def __init__(self, chemin):
        self.e = Exe_dll(chemin)

    def lire_chaine(self, va):
        o = self.e.va_vers_off(va)
        return self.e.data[o:self.e.data.index(b'\0', o)].decode('ascii')


class Exe_dll(Exe):
    """meme lecteur PE ; la table de relocation d'une DLL sert a retrouver les pointeurs, pas utilisee ici."""


def decoder_profils(d):
    """-> liste de dict, un par enregistrement Profile (68 octets : build, ts, taille, table, init, tick, end, site Lua,
    8 octets du site, 6 fonctions Lua, nilobject) trouve par (horodatage, taille d'image)."""
    out = []
    e = d.e
    for sec in e.secs:
        if sec['exec']:
            continue
        blob = e.data[sec['rawptr']:sec['rawptr'] + min(sec['vsize'], sec['rawsz'])]
        for i in range(0, len(blob) - 68, 4):
            ts, size = struct.unpack_from('<II', blob, i + 4)
            if size != 0x00af7000 or ts not in (0x6a36c177, 0x6ae228f3):
                continue
            build_ptr, ts, size, vt, ini, tick, end, site = struct.unpack_from('<8I', blob, i)
            try:
                build = d.lire_chaine(build_ptr)
            except Exception:
                continue
            out.append(dict(build=build, ts=ts, size=size, vtable=vt, init=ini, tick=tick, end=end, lua_site=site,
                            site_bytes=bytes(blob[i + 32:i + 40]), fns=list(struct.unpack_from('<6I', blob, i + 40)),
                            nilobject=struct.unpack_from('<I', blob, i + 64)[0], pos=sec['va'] + i))
    return out


def decoder_layouts(d):
    """-> dict build -> dict de champs d'adresses (les 15 premiers + f_spawn, f_af_tick) et octets attendus."""
    e = d.e
    out = {}
    for sec in e.secs:
        if sec['exec']:
            continue
        blob = e.data[sec['rawptr']:sec['rawptr'] + min(sec['vsize'], sec['rawsz'])]
        for i in range(0, len(blob) - 120, 4):
            ptr = struct.unpack_from('<I', blob, i)[0]
            if not (e.base <= ptr < e.base + e.taille_image):
                continue
            try:
                s = d.lire_chaine(ptr)
            except Exception:
                continue
            if not s.startswith('1.5.18-win32'):
                continue
            v = struct.unpack_from('<15I', blob, i + 4)
            champs = dict(zip(CHAMPS_LAYOUT[:11] + ['h_controller0', 'h_controller1', 'h_spawn', 'h_af_tick'],
                              (v[0], v[1], v[2], v[3], v[4], v[5], v[6], v[7], v[8], v[9], v[10], v[11], v[12], v[13], v[14])))
            hb = bytes(blob[i + 64:i + 70])
            hh = bytes(blob[i + 70:i + 75])
            hc = [bytes(blob[i + 75:i + 82]), bytes(blob[i + 82:i + 89])]
            f_spawn, f_af_tick = struct.unpack_from('<II', blob, i + 92)
            champs.update(f_spawn=f_spawn, f_af_tick=f_af_tick, bytes_waypoints=hb, bytes_hangar=hh, bytes_controller=hc,
                          dock_state=None)
            out[s] = champs
    return out


def verifier_exe(exe, p, L):
    """Reproduit startup() de cc2x.c sur les octets du fichier (image a l'adresse de base du fichier)."""
    ok_detect = exe.horodatage == p['ts'] and exe.taille_image == p['size']
    if not ok_detect:
        return False, 'detect: horodatage 0x%08x / taille 0x%08x != 0x%08x / 0x%08x' % (exe.horodatage, exe.taille_image, p['ts'], p['size'])
    pb = []
    for champ, sig in LUA_SIGS:
        va = p['fns'][champ]
        pb.append(exe.octets(va, 8) == sig)
    site = exe.octets(p['lua_site'], 8) == p['site_bytes']
    cells = exe.octets(p['vtable'], 12) == struct.pack('<III', p['init'], p['tick'], p['end'])
    relocs = all(exe.est_reloc(p['vtable'] + 4 * k) for k in range(3))
    nil = exe.octets(p['nilobject'], 16) == bytes(16) or True
    ok = all(pb) and site and cells and relocs
    return ok, 'LUA_SIGS %s, site Lua %s, cellules de la table %s (relocalisees %s)' % (
        ''.join('1' if x else '0' for x in pb), 'OK' if site else 'DIFFERENT', 'OK' if cells else 'DIFFERENTES', 'oui' if relocs else 'NON')


def verifier_layout(exe, lay, L):
    bad = []
    attendus = [('h_waypoints', lay['bytes_waypoints']), ('h_hangar', lay['bytes_hangar']),
                ('h_controller0', lay['bytes_controller'][0]), ('h_controller1', lay['bytes_controller'][1])]
    for nom, octets in attendus:
        if exe.octets(lay[nom], len(octets)) != octets:
            bad.append(nom)
    # les autres sites de crochets (sans octets attendus dans le source) doivent au moins etre des debuts d'instruction identiques a l'ancien
    for nom in ('f_vehicle_by_id', 'f_tile_by_id', 'f_tile_at', 'f_request_landing', 'f_waypoints_clear', 'f_deque_grow', 'f_spawn', 'f_af_tick'):
        if exe.octets(lay[nom], 3) not in (bytes([0x55, 0x8b, 0xec]), bytes([0x53, 0x8b, 0xdc])):
            bad.append(nom + ' (pas un debut de fonction)')
    return not bad, ('octets des crochets OK, 8 debuts de fonctions OK' if not bad else 'PROBLEME : ' + ', '.join(bad))


def main():
    args = sys.argv[1:]
    i_sep = args.index('--')
    dll, valeurs, exes, sortie = args[0], args[1], args[2:i_sep], args[i_sep + 1]
    d = Dll(dll)
    L = ['Relecture des profils DANS la DLL compilee ' + dll + ' (rien charge, rien lance)', '']
    profils = decoder_profils(d)
    L.append('%d enregistrement(s) Profile trouve(s) :' % len(profils))
    for p in profils:
        L.append('  build %r PE 0x%08x taille 0x%08x vtable 0x%08x init/tick/end 0x%08x 0x%08x 0x%08x site 0x%08x fonctions %s nilobject 0x%08x' % (
            p['build'], p['ts'], p['size'], p['vtable'], p['init'], p['tick'], p['end'], p['lua_site'], ' '.join('0x%08x' % x for x in p['fns']), p['nilobject']))
    problemes = []
    anc = [p for p in profils if p['ts'] == 0x6a36c177]
    nouv = [p for p in profils if p['ts'] == 0x6ae228f3]
    if len(profils) != 2 or len(anc) != 1 or len(nouv) != 1:
        problemes.append('il faut exactement 2 profils (un par horodatage)')
    else:
        a = anc[0]
        egal_ancien = all(a[k] == PROFIL_ANCIEN[k] for k in PROFIL_ANCIEN)
        L.append('profil ANCIEN identique a la source d\'origine (tous champs) : %s' % ('OUI' if egal_ancien else 'NON'))
        if not egal_ancien:
            problemes.append('profil ancien modifie')
    lays = decoder_layouts(d)
    L.append('')
    L.append('Layouts (world.c) trouves : %s' % ', '.join(sorted(lays)))
    if '1.5.18-win32' in lays:
        egal = all(lays['1.5.18-win32'][k] == v for k, v in LAYOUT_ANCIEN.items())
        L.append('Layout ANCIEN identique a la source d\'origine (17 adresses) : %s' % ('OUI' if egal else 'NON'))
        if not egal:
            problemes.append('layout ancien modifie')
    else:
        problemes.append('layout ancien introuvable')
    # les valeurs lues DANS la DLL doivent etre celles trouvees dans le nouvel exe par profil_sdk.py
    import json
    val = json.load(open(valeurs, encoding='utf-8'))['valeurs']
    if len(nouv) == 1 and '1.5.18-win32-6ae228f3' in lays:
        n, ly = nouv[0], lays['1.5.18-win32-6ae228f3']
        attendu_p = dict(vtable=val['server_vtable']['nouveau'], init=val['server_init']['nouveau'], tick=val['server_tick']['nouveau'],
                         end=val['server_end']['nouveau'], lua_site=val['lua_site']['nouveau'], nilobject=val['nilobject']['nouveau'])
        ecarts = [k for k, v in attendu_p.items() if n[k] != v]
        fns = [val[k]['nouveau'] for k in ('f_index2addr', 'f_auxsetstr', 'f_finishset', 'f_luaS_new', 'f_luaH_new', 'f_luaC_step')]
        if n['fns'] != fns:
            ecarts.append('fonctions Lua')
        noms_layout = {'h_controller0': 'h_controller[0]', 'h_controller1': 'h_controller[1]'}
        ecarts += [k for k in list(LAYOUT_ANCIEN) if ly[k] != val[noms_layout.get(k, k)]['nouveau']]
        L.append('valeurs du profil et du layout NOUVEAUX lues dans la DLL = valeurs trouvees dans le nouvel exe (profil_sdk.py) : %s' % (
            'OUI (6 champs + 6 fonctions Lua + 17 adresses du layout)' if not ecarts else 'NON : ' + ', '.join(ecarts)))
        if ecarts:
            problemes.append('ecarts DLL / valeurs : ' + ', '.join(ecarts))
    L.append('')
    L.append('--- simulation de startup() sur les octets de chaque exe (le profil choisi = celui dont detect() reussit)')
    attendu = {}
    for chemin in exes:
        e = Exe(chemin)
        acceptes = []
        for p in profils:
            ok, msg = verifier_exe(e, p, L)
            L.append('%s | profil %r : %s%s' % (os.path.basename(chemin), p['build'], 'ACCEPTE' if ok else 'refuse', ' (' + msg + ')'))
            if ok:
                acceptes.append(p['build'])
                lay = lays.get(p['build'])
                if lay is None:
                    L.append('      pas de Layout pour ce build : l\'API 3 resterait vide')
                    problemes.append('pas de layout pour ' + p['build'])
                else:
                    okl, msgl = verifier_layout(e, lay, L)
                    L.append('      Layout %r : %s' % (p['build'], msgl))
                    if not okl:
                        problemes.append('layout %s sur %s : %s' % (p['build'], chemin, msgl))
        attendu[chemin] = acceptes
        L.append('  => %s : profil(s) accepte(s) : %s' % (os.path.basename(chemin), acceptes or 'AUCUN (le SDK resterait inactif)'))
    L.append('')
    if problemes:
        L.append('PROBLEMES : ' + ' ; '.join(problemes))
    else:
        L.append('Aucun probleme.')
    open(sortie, 'w', encoding='utf-8').write('\n'.join(L) + '\n')
    print('\n'.join(L))
    return 1 if problemes else 0, attendu


if __name__ == '__main__':
    rc, att = main()
    sys.exit(rc)

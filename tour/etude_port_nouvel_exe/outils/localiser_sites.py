#!/usr/bin/env python3
"""PARTIE 1, etape A : retrouve les sites des modules d'exe de l'ANCIEN build (1.5.18, 1C9A01C3...) dans le NOUVEL exe de
Steam (461E1262...), par le CONTEXTE desassemble, sans rien deviner.

LECTURE SEULE sur les deux exe (jamais modifies). Ecrit seulement : un JSON de resultats et un rapport texte.

Methode, pour chaque champ de 4 octets d'un module :
  1. dans l'ancien exe, on retrouve l'instruction qui contient le champ (capstone, balayage lineaire du code) ;
  2. on prend N instructions avant et N apres ; on construit un motif d'octets ou les champs qui changent forcement
     d'un build a l'autre sont des jokers : adresses absolues (celles qui ont une entree de relocation) et deplacements
     relatifs des call / jmp / jcc ;
  3. on cherche ce motif dans TOUT le code du nouvel exe ; on garde le plus grand N qui donne UNE SEULE occurrence ;
     zero occurrence ou plusieurs = le site est declare INTROUVABLE / AMBIGU (on ne devine pas) ;
  4. on controle ce que le joker cachait : meme section, memes octets pour une constante lue en lecture seule,
     correspondance coherente (une meme ancienne adresse -> toujours la meme nouvelle adresse) ;
  5. on controle l'ordre (les sites restent dans le meme ordre) et l'absence de doublon.

Usage : python -I -B localiser_sites.py <ancien_original.exe> <nouveau.exe> <dossier_modules_ancien> <sortie.json> <sortie.txt>
"""
import bisect
import glob
import json
import os
import re
import struct
import sys
from array import array
from collections import defaultdict

from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import X86_OP_MEM

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pe_lecture import Exe  # noqa: E402

# Par defaut tout .text est balaye (le balayage commence toujours au debut de .text pour rester aligne). Memoire : addr/taille en
# tableaux compacts, mnemoniques internes, operandes recalcules a la demande.
TAILLES_FENETRE = (64, 48, 40, 32, 24, 20, 16, 12, 10, 8, 6, 5, 4, 3)
N_MIN = 4          # en dessous, le contexte est juge trop court pour accepter un site


class _Operandes:
    """B.op[i] : texte des operandes de l'instruction i, desassemble a la demande."""

    def __init__(self, bal):
        self.bal = bal

    def __getitem__(self, i):
        bal = self.bal
        md = Cs(CS_ARCH_X86, CS_MODE_32)
        md.skipdata = True
        for _, _, _, op in md.disasm_lite(bal.exe.octets(bal.addr[i], bal.size[i]), bal.addr[i]):
            return op
        return ''


class Balayage:
    """Instructions du code d'un exe : adresse, taille, mnemonique (operandes a la demande)."""

    def __init__(self, exe, debut=0, fin=0x7FFFFFFF):
        self.exe = exe
        s = exe.sec_nom('.text')
        buf = exe.data[s['rawptr']:s['rawptr'] + min(s['vsize'], s['rawsz'])]
        md = Cs(CS_ARCH_X86, CS_MODE_32)
        md.skipdata = True
        self.addr, self.size, self.mn = array('I'), array('B'), []
        for a, sz, mn, _ in md.disasm_lite(buf, s['va']):
            if a >= debut:
                if a >= fin:
                    break
                self.addr.append(a)
                self.size.append(sz)
                self.mn.append(sys.intern(mn))
        self.op = _Operandes(self)
        self.texte = buf
        self.va_texte = s['va']

    def index_contenant(self, va, n=4):
        i = bisect.bisect_right(self.addr, va) - 1
        if i < 0 or self.addr[i] + self.size[i] < va + n:
            return None
        return i

    def champs_variables(self, i):
        """Positions (dans l'instruction i) des champs de 4 octets qui changent d'un build a l'autre."""
        a, sz = self.addr[i], self.size[i]
        raw = self.exe.octets(a, sz)
        champs = {}
        for p in range(0, sz - 3):
            if self.exe.est_reloc(a + p):
                champs[p] = 'abs'
        if sz == 5 and raw[0] in (0xE8, 0xE9):
            champs[1] = 'call' if raw[0] == 0xE8 else 'jmp'
        elif sz == 6 and raw[0] == 0x0F and 0x80 <= raw[1] <= 0x8F:
            champs[2] = 'jcc'
        return champs

    def motif(self, i0, i1):
        """(motif regex, cle) pour les instructions i0..i1 incluses ; cle = octets avec jokers a zero."""
        morceaux, cle = [], bytearray()
        for i in range(i0, i1 + 1):
            a, sz = self.addr[i], self.size[i]
            raw = self.exe.octets(a, sz)
            ch = self.champs_variables(i)
            p = 0
            while p < sz:
                if p in ch:
                    morceaux.append(b'.{4}')
                    cle += b'\0\0\0\0'
                    p += 4
                else:
                    morceaux.append(re.escape(raw[p:p + 1]))
                    cle += raw[p:p + 1]
                    p += 1
        return re.compile(b''.join(morceaux), re.S), bytes(cle)


def retrouver(BA, BN, i):
    """Cherche dans le nouvel exe le contexte (N instructions avant / apres) de l'instruction i de l'ancien.
    -> ((N, i0, i1, position dans .text du nouvel exe), None) si UNE seule occurrence, sinon (None, (statut, raison))."""
    raison = None
    for N in TAILLES_FENETRE:
        i0, i1 = max(0, i - N), min(len(BA.addr) - 1, i + N)
        motif, _ = BA.motif(i0, i1)
        hits = [m_.start() for m_ in motif.finditer(BN.texte)]
        if len(hits) == 1:
            return (N, i0, i1, hits[0]), None
        if len(hits) > 1:
            return None, ('AMBIGU', '%d occurrences du contexte de %d+%d instructions' % (len(hits), N, N))
    return None, ('INTROUVABLE', 'aucun motif de >= 3 instructions de chaque cote ne se retrouve')


def classer_champ(B, i, va_champ):
    """Type du champ de 4 octets a va_champ dans l'instruction i : abs / rel32 / imm."""
    exe = B.exe
    fo = va_champ - B.addr[i]
    ch = B.champs_variables(i)
    if fo in ch:
        return 'abs' if ch[fo] == 'abs' else 'rel32'
    return 'imm'


def lire_modules(dossier):
    mods = {}
    for p in sorted(glob.glob(os.path.join(dossier, '*.json'))):
        with open(p, 'r', encoding='utf-8') as f:
            m = json.load(f)
        mods[m['nom']] = m
    return mods


def main():
    if len(sys.argv) != 6:
        sys.exit(__doc__)
    p_old, p_new, d_mod, p_json, p_txt = sys.argv[1:6]
    A, Bx = Exe(p_old), Exe(p_new)
    if A.sha != '1C9A01C3007CB2BEC2A04D716812CF9F24C87EFA11056395C89DDD7D2C341026':
        sys.exit("REFUS : le 1er exe n'est pas l'ancien original 1C9A01C3...")
    if Bx.sha != '461E12623BACB7DE29CA27B4614425C87E8DF2C8327A5E958A957C850EFFE42A':
        sys.exit("REFUS : le 2e exe n'est pas le nouvel exe de Steam 461E1262...")
    mods = lire_modules(d_mod)
    BA, BN = Balayage(A), Balayage(Bx)
    lignes = []
    resultats = []
    carte_abs = defaultdict(set)      # ancienne adresse -> nouvelles adresses (constantes / globales lues)
    carte_rel = defaultdict(set)      # ancienne cible -> nouvelles cibles (calls / sauts)
    problemes = []

    def log(s=''):
        lignes.append(s)

    log('Localisation des sites par le contexte desassemble (capstone). LECTURE SEULE.')
    log('ancien : %s  sha %s' % (A.chemin, A.sha))
    log('nouveau: %s  sha %s' % (Bx.chemin, Bx.sha))
    log('zone balayee : tout .text ; instructions ancien %d, nouveau %d' % (len(BA.addr), len(BN.addr)))
    log()

    for nom, m in mods.items():
        for c in m['changements']:
            va = c['va']
            r = dict(module=nom, va_ancien=va, offset_ancien=c['offset'], avant=c['avant'], apres=c['apres'],
                     reglage=c['reglage'], statut=None)
            resultats.append(r)
            if va < A.base + A.taille_en_tetes:
                # valeur ajoutee dans le bourrage de l'en-tete : pas d'instruction
                nul_a = all(b == 0 for b in A.data[A.fin_table_sections:A.taille_en_tetes])
                nul_n = all(b == 0 for b in Bx.data[Bx.fin_table_sections:Bx.taille_en_tetes])
                ok = (nul_a and nul_n and A.fin_table_sections == Bx.fin_table_sections
                      and A.taille_en_tetes == Bx.taille_en_tetes and Bx.data[va - Bx.base:va - Bx.base + 4] == bytes(4))
                r.update(type='cave_entete', statut='sur' if ok else 'PROBLEME', va_nouveau=va, offset_nouveau=va - Bx.base,
                         contexte='bourrage nul de l\'en-tete : 0x%x-0x%x dans les deux exe, octets du champ = 00000000' % (
                             A.fin_table_sections, A.taille_en_tetes))
                log('%-22s 0x%08x en-tete (hors code) -> 0x%08x %s : %s' % (nom, va, va, r['statut'], r['contexte']))
                if not ok:
                    problemes.append((nom, va, 'bourrage de l\'en-tete non nul / different'))
                continue
            i = BA.index_contenant(va)
            if i is None:
                r.update(statut='INTROUVABLE', contexte='aucune instruction ne contient le champ dans l\'ancien exe')
                problemes.append((nom, va, r['contexte']))
                log('%-22s 0x%08x INTROUVABLE (%s)' % (nom, va, r['contexte']))
                continue
            typ = classer_champ(BA, i, va)
            fo = va - BA.addr[i]
            # octets d'origine du champ conformes au JSON ?
            if A.octets(va, 4).hex() != c['avant']:
                r.update(statut='PROBLEME', contexte='les octets de l\'ancien original ne sont pas ceux du JSON')
                problemes.append((nom, va, r['contexte']))
                continue
            trouve, raison = retrouver(BA, BN, i)
            if raison:
                r.update(statut=raison[0], contexte=raison[1])
            if trouve is None:
                if r['statut'] is None:
                    r.update(statut='INTROUVABLE', contexte='aucun motif de >= %d instructions de chaque cote ne se retrouve' % 3)
                problemes.append((nom, va, r['statut'] + ' : ' + r['contexte']))
                log('%-22s 0x%08x %s (%s)' % (nom, va, r['statut'], r['contexte']))
                continue
            N, i0, i1, pos = trouve
            if N < N_MIN:
                r.update(statut='INCERTAIN', contexte='contexte trop court (%d instructions de chaque cote)' % N)
                problemes.append((nom, va, r['contexte']))
                log('%-22s 0x%08x INCERTAIN (%s)' % (nom, va, r['contexte']))
                continue
            va_debut_new = BN.va_texte + pos
            decal = va_debut_new - BA.addr[i0]
            va_new = va + decal
            # --- controles de ce que les jokers cachaient, instruction par instruction
            j = BN.addr.index(va_debut_new) if False else bisect.bisect_left(BN.addr, va_debut_new)
            assert BN.addr[j] == va_debut_new, 'le motif ne commence pas sur une frontiere d\'instruction du nouvel exe'
            nb_ref, nb_ref_diff, diffs = 0, 0, []
            for k in range(i1 - i0 + 1):
                ia, ib = i0 + k, j + k
                assert BA.size[ia] == BN.size[ib] and BA.mn[ia] == BN.mn[ib], 'instruction differente (ne devrait pas arriver)'
                cha, chb = BA.champs_variables(ia), BN.champs_variables(ib)
                assert cha.keys() == chb.keys(), 'jokers differents'
                for p, gen in cha.items():
                    ta = struct.unpack('<I', A.octets(BA.addr[ia] + p, 4))[0]
                    tb = struct.unpack('<I', Bx.octets(BN.addr[ib] + p, 4))[0]
                    if gen == 'abs':
                        nb_ref += 1
                        # lecture seule et non executable : on compare les octets pointes
                        sa, sb = A.section(ta), Bx.section(tb)
                        if sa is None or sb is None or sa['nom'] != sb['nom']:
                            nb_ref_diff += 1
                            diffs.append('0x%08x : section differente 0x%08x/0x%08x' % (BA.addr[ia], ta, tb))
                        elif not sa['ecriture'] and not sa['exec'] and sa['nom'] != '(en-tete)':
                            if A.octets(ta, 4) != Bx.octets(tb, 4):
                                nb_ref_diff += 1
                                diffs.append('0x%08x : constante differente %s / %s' % (BA.addr[ia], A.octets(ta, 4).hex(), Bx.octets(tb, 4).hex()))
                        carte_abs[ta].add(tb)
                    else:
                        fin_a, fin_b = BA.addr[ia] + BA.size[ia], BN.addr[ib] + BN.size[ib]
                        ra = struct.unpack('<i', A.octets(BA.addr[ia] + p, 4))[0]
                        rb = struct.unpack('<i', Bx.octets(BN.addr[ib] + p, 4))[0]
                        carte_rel[fin_a + ra].add(fin_b + rb)
            # etendue du contexte identique (en instructions, sans joker sur le champ du site)
            ia0, ib0 = i, j + (i - i0)

            def egal(ia, ib):
                if not (0 <= ia < len(BA.addr) and 0 <= ib < len(BN.addr)):
                    return False
                if BA.size[ia] != BN.size[ib] or BA.mn[ia] != BN.mn[ib]:
                    return False
                ra, rb = bytearray(A.octets(BA.addr[ia], BA.size[ia])), bytearray(Bx.octets(BN.addr[ib], BN.size[ib]))
                for p in BA.champs_variables(ia):
                    ra[p:p + 4] = bytes(4)
                for p in BN.champs_variables(ib):
                    rb[p:p + 4] = bytes(4)
                return ra == rb
            av = 0
            while egal(ia0 - av - 1, ib0 - av - 1):
                av += 1
            ap = 0
            while egal(ia0 + ap + 1, ib0 + ap + 1):
                ap += 1
            ibs = ib0
            # l'instruction du site elle-meme
            site_ok = egal(i, ibs)
            va_new_ins = BN.addr[ibs]
            va_champ_new = va_new_ins + fo
            r.update(type=typ, va_nouveau=va_champ_new, offset_nouveau=Bx.va_vers_off(va_champ_new),
                     instruction_ancien='0x%08x %s %s' % (BA.addr[i], BA.mn[i], BA.op[i]),
                     instruction_nouveau='0x%08x %s %s' % (va_new_ins, BN.mn[ibs], BN.op[ibs]),
                     fenetre=N, etendue_avant=av, etendue_apres=ap, decalage=va_champ_new - va,
                     references_dans_fenetre=nb_ref, references_differentes=nb_ref_diff, differences=diffs[:5],
                     statut='sur' if site_ok else 'PROBLEME')
            r['contexte'] = 'contexte unique de %d+%d instructions ; identique sur %d avant / %d apres' % (N, N, av, ap)
            r['instruction_site_ancien'] = BA.op[i]
            r['mn'] = BA.mn[i]
            r['taille_ins'] = BA.size[i]
            r['champ_dans_ins'] = fo
            # controles specifiques au type
            if typ == 'abs':
                ta = struct.unpack('<I', A.octets(va, 4))[0]
                tb = struct.unpack('<I', Bx.octets(va_champ_new, 4))[0]
                r['cible_ancien'], r['cible_nouveau'] = ta, tb
                r['est_reloc_nouveau'] = Bx.est_reloc(va_champ_new)
                r['valeur_lue_ancien'] = A.f32(ta)
                r['valeur_lue_nouveau'] = Bx.f32(tb)
                if not Bx.est_reloc(va_champ_new) or A.f32(ta) != Bx.f32(tb) or A.nom_section(ta) != Bx.nom_section(tb):
                    r['statut'] = 'PROBLEME'
                    problemes.append((nom, va, 'operande: relocation absente ou constante differente'))
            elif typ == 'imm':
                r['est_reloc_nouveau'] = Bx.est_reloc(va_champ_new)
                if Bx.est_reloc(va_champ_new) or Bx.octets(va_champ_new, 4).hex() != c['avant']:
                    r['statut'] = 'PROBLEME'
                    problemes.append((nom, va, 'immediat different dans le nouvel exe'))
            else:
                ra = struct.unpack('<i', A.octets(va, 4))[0]
                rb = struct.unpack('<i', Bx.octets(va_champ_new, 4))[0]
                r['cible_ancien'], r['cible_nouveau'] = va + 4 + ra, va_champ_new + 4 + rb
            if r['statut'] != 'sur' and not any(p[1] == va and p[0] == nom for p in problemes):
                problemes.append((nom, va, 'instruction du site differente'))
            log('%-22s 0x%08x -> 0x%08x (%+#x) %-5s ctx %d+%d, identique %d/%d instr., %s' % (
                nom, va, va_champ_new, va_champ_new - va, typ, N, N, av, ap, r['statut']))
            log('        ancien  %s' % r['instruction_ancien'])
            log('        nouveau %s' % r['instruction_nouveau'])

    # --- coherence globale
    log()
    log('--- Coherence globale')
    incoh_abs = {a: sorted(b) for a, b in carte_abs.items() if len(b) > 1}
    incoh_rel = {a: sorted(b) for a, b in carte_rel.items() if len(b) > 1}
    log('references absolues vues dans les fenetres : %d anciennes adresses ; correspondances multiples : %d' % (len(carte_abs), len(incoh_abs)))
    for a, b in list(incoh_abs.items())[:10]:
        log('   0x%08x -> %s' % (a, ' '.join('0x%08x' % x for x in b)))
    log('cibles relatives (call/jmp/jcc) vues : %d ; correspondances multiples : %d' % (len(carte_rel), len(incoh_rel)))
    for a, b in list(incoh_rel.items())[:10]:
        log('   0x%08x -> %s' % (a, ' '.join('0x%08x' % x for x in b)))
    code = [r for r in resultats if r.get('type') not in (None, 'cave_entete')]
    tri = sorted(code, key=lambda r: r['va_ancien'])
    ordre_ok = all(tri[k]['va_nouveau'] < tri[k + 1]['va_nouveau'] for k in range(len(tri) - 1))
    doublons = len({r['va_nouveau'] for r in code}) != len(code)
    log('ordre conserve : %s ; doublons de nouvelle adresse : %s' % ('oui' if ordre_ok else 'NON', 'OUI' if doublons else 'non'))
    if not ordre_ok:
        problemes.append(('*', 0, 'ordre des sites non conserve'))
    if doublons:
        problemes.append(('*', 0, 'deux sites sur la meme nouvelle adresse'))
    log()
    log('--- Resume')
    par_statut = defaultdict(int)
    for r in resultats:
        par_statut[r['statut']] += 1
    log('statuts : ' + ', '.join('%s=%d' % kv for kv in sorted(par_statut.items())))
    log('decalages observes (champ nouveau - ancien) : ' + ', '.join(
        '%+#x x%d' % (d, n) for d, n in sorted(defaultdict(int, {}).items())) if False else '')
    dec = defaultdict(int)
    for r in code:
        dec[r['decalage']] += 1
    log('decalages observes : ' + ', '.join('%+#x (x%d)' % (d, n) for d, n in sorted(dec.items())))
    if problemes:
        log('PROBLEMES (on s\'arrete sur ces sites, rien n\'est devine) :')
        for nom, va, msg in problemes:
            log('   %s 0x%08x : %s' % (nom, va, msg))
    with open(p_json, 'w', encoding='utf-8') as f:
        json.dump(dict(resultats=resultats, problemes=problemes, carte_abs={'0x%08x' % a: ['0x%08x' % x for x in sorted(b)] for a, b in carte_abs.items()},
                       carte_rel={'0x%08x' % a: ['0x%08x' % x for x in sorted(b)] for a, b in carte_rel.items()}),
                  f, indent=1, ensure_ascii=False)
    with open(p_txt, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lignes) + '\n')
    print('\n'.join(lignes))
    return 1 if problemes else 0


if __name__ == '__main__':
    sys.exit(main())

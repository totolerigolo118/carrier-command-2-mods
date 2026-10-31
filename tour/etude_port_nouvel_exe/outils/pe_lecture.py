#!/usr/bin/env python3
"""Lecture seule d'un exe 32 bits (PE) : sections, relocations, desassemblage capstone.
Utilise par les outils de portage de tour/etude_port_nouvel_exe/outils/. Ecrit RIEN dans l'exe."""
import hashlib
import struct

from capstone import Cs, CS_ARCH_X86, CS_MODE_32


class Exe:
    def __init__(self, chemin):
        with open(chemin, 'rb') as f:
            self.data = f.read()
        d = self.data
        self.chemin = chemin
        self.sha = hashlib.sha256(d).hexdigest().upper()
        pe = struct.unpack_from('<I', d, 0x3C)[0]
        assert d[pe:pe + 4] == b'PE\0\0'
        self.pe = pe
        self.nsec = struct.unpack_from('<H', d, pe + 6)[0]
        self.horodatage = struct.unpack_from('<I', d, pe + 8)[0]
        optsz = struct.unpack_from('<H', d, pe + 20)[0]
        opt = pe + 24
        self.opt = opt
        self.base = struct.unpack_from('<I', d, opt + 28)[0]
        self.taille_image = struct.unpack_from('<I', d, opt + 56)[0]
        self.taille_en_tetes = struct.unpack_from('<I', d, opt + 60)[0]
        self.dll_caracteristiques = struct.unpack_from('<H', d, opt + 70)[0]
        self.secs = []
        for i in range(self.nsec):
            o = opt + optsz + 40 * i
            nom = d[o:o + 8].rstrip(b'\0').decode()
            vsize, va, rawsz, rawptr = struct.unpack_from('<IIII', d, o + 8)
            fl = struct.unpack_from('<I', d, o + 36)[0]
            self.secs.append(dict(nom=nom, va=self.base + va, vsize=vsize, rawsz=rawsz, rawptr=rawptr, flags=fl,
                                  exec=bool(fl & 0x20000000), ecriture=bool(fl & 0x80000000)))
        self.fin_table_sections = opt + optsz + 40 * self.nsec
        # relocations HIGHLOW : ensemble des RVA qui portent une adresse absolue
        reloc_rva, reloc_size = struct.unpack_from('<II', d, opt + 96 + 5 * 8)
        self.relocs = set()
        p = self.va_vers_off(self.base + reloc_rva)
        fin = p + reloc_size
        while p < fin:
            page, blk = struct.unpack_from('<II', d, p)
            if blk < 8:
                break
            for k in range((blk - 8) // 2):
                e = struct.unpack_from('<H', d, p + 8 + 2 * k)[0]
                if (e >> 12) == 3:
                    self.relocs.add(page + (e & 0xFFF))
            p += blk

    def va_vers_off(self, va):
        if self.base <= va < self.base + self.taille_en_tetes:
            return va - self.base
        for s in self.secs:
            if s['va'] <= va < s['va'] + min(s['vsize'], s['rawsz']):
                return s['rawptr'] + va - s['va']
        raise ValueError('adresse non couverte par le fichier : 0x%08x' % va)

    def off_vers_va(self, off):
        if off < self.taille_en_tetes:
            return self.base + off
        for s in self.secs:
            if s['rawptr'] <= off < s['rawptr'] + min(s['vsize'], s['rawsz']):
                return s['va'] + off - s['rawptr']
        raise ValueError('decalage hors sections : 0x%x' % off)

    def section(self, va):
        if self.base <= va < self.base + self.taille_en_tetes:
            return dict(nom='(en-tete)', exec=False, ecriture=False)
        for s in self.secs:
            if s['va'] <= va < s['va'] + s['vsize']:
                return s
        return None

    def nom_section(self, va):
        s = self.section(va)
        return s['nom'] if s else '?'

    def octets(self, va, n):
        o = self.va_vers_off(va)
        return self.data[o:o + n]

    def u32(self, va):
        return struct.unpack('<I', self.octets(va, 4))[0]

    def f32(self, va):
        return struct.unpack('<f', self.octets(va, 4))[0]

    def est_reloc(self, va):
        return (va - self.base) in self.relocs

    def sec_nom(self, nom):
        return next(s for s in self.secs if s['nom'] == nom)


def desasm(exe, va, n_octets, detail=True):
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    md.detail = detail
    return list(md.disasm(exe.octets(va, n_octets), va))

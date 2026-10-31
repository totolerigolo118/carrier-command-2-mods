"""Etape 3 : lecture de l'en-tete PE avec struct (sans bibliotheque). Lecture seule."""
import sys, os, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import portlib as P

NOMS_DIR = ['export', 'import', 'ressources', 'exceptions', 'signature(securite)', 'reloc', 'debug', 'copyright', 'global_ptr', 'tls', 'load_config', 'bound_import', 'IAT', 'delay_import', 'clr', 'reserve']
for f in (P.F_ORIG, P.F_PATCH, P.F_NEW):
    e = P.Exe(f)
    b = e.b
    pe = e.pe
    print('=====', os.path.basename(f), P.sha(b)[:8])
    print('e_lfanew 0x%x ; sections : table de 0x%x a 0x%x (%d sections x 40 octets)' % (pe['e_lfanew'], pe['sec_table_off'], pe['sec_table_end'], pe['nsec']))
    o = pe['opt_off']
    dllchar = struct.unpack_from('<H', b, o + 70)[0]
    print('SizeOfHeaders 0x%x ; DllCharacteristics 0x%04x (DYNAMIC_BASE=%s, NX=%s) ; Characteristics 0x%x (RELOCS_STRIPPED=%s)' % (
        pe['hdrsize'], dllchar, bool(dllchar & 0x40), bool(dllchar & 0x100), pe['chars'], bool(pe['chars'] & 1)))
    print('CheckSum 0x%x ; horodatage 0x%08x ; nb dossiers de donnees ' % (pe['checksum'], pe['ts']), struct.unpack_from('<I', b, o + 92)[0])
    dd = o + 96
    for i in range(16):
        rva, sz = struct.unpack_from('<II', b, dd + 8 * i)
        if rva or sz:
            print('   dossier %-20s rva 0x%x taille 0x%x' % (NOMS_DIR[i], rva, sz))
    print('fin des dossiers de donnees : 0x%x' % (dd + 128))
    seg = b[0x2f0:0x400]
    print('octets 0x2f0..0x3ff :', seg.hex())
    nz = [i for i in range(0x310, 0x400) if b[i] != 0]
    print('octets non nuls entre 0x310 et 0x3ff :', [hex(x) for x in nz])
    print('4 octets a 0x310 :', b[0x310:0x314].hex())
    # signature numerique ?
    rva, sz = struct.unpack_from('<II', b, dd + 8 * 4)
    print('signature numerique (dossier 4) :', 'oui' if rva else 'non')
    print('section de la VA 0x400310 :', e.sec_of_va(0x400310))

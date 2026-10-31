"""Verifie, en LECTURE SEULE, ce sur quoi repose la synchronisation du plugin cc2x_hold v2 (voir PLUGIN_hold_v2.md).
Usage : python -I -B verifier_synchro_v2.py <exe ancien original 1C9A01C3> <exe ancien patche 8E7FCBB6> <nouvel exe 461E1262>
Ne lance rien, n'ecrit rien, aucun reseau, aucune bibliotheque en dehors de Python. Sortie : controles OK / ECHEC (code 1 si un echec)."""
import hashlib
import struct
import sys

SHA = {'ancien': '1C9A01C3007CB2BE', 'patche': '8E7FCBB6CE27BD3D', 'nouveau': '461E12623BACB7DE'}
if len(sys.argv) != 4:
    sys.exit(__doc__)
echecs = []


def controle(ok, texte):
    print(('OK     ' if ok else 'ECHEC  ') + texte)
    if not ok:
        echecs.append(texte)


class Exe:
    def __init__(self, chemin):
        self.d = open(chemin, 'rb').read()
        e = struct.unpack_from('<I', self.d, 0x3c)[0]
        self.ts = struct.unpack_from('<I', self.d, e + 8)[0]
        n, osz = struct.unpack_from('<H', self.d, e + 6)[0], struct.unpack_from('<H', self.d, e + 20)[0]
        self.base = struct.unpack_from('<I', self.d, e + 24 + 28)[0]
        self.secs = [struct.unpack_from('<8sIIII', self.d, e + 24 + osz + 40 * i)[1:] for i in range(n)]

    def off(self, va):
        for vs, rva, rs, rp in self.secs:
            if rva <= va - self.base < rva + min(vs, rs):
                return rp + va - self.base - rva
        raise ValueError(hex(va))

    def lit(self, va, n):
        o = self.off(va)
        return self.d[o:o + n]

    def u32(self, va):
        return struct.unpack('<I', self.lit(va, 4))[0]

    def octets(self, va, hexa):
        return self.lit(va, len(hexa) // 2) == bytes.fromhex(hexa)

    def relocations(self):
        """adresses (image) que Windows reecrit quand il charge l'exe ailleurs qu'a sa base (table .reloc, type 3 = HIGHLOW)"""
        e = struct.unpack_from('<I', self.d, 0x3c)[0]
        rva, taille = struct.unpack_from('<II', self.d, e + 24 + 96 + 5 * 8)
        r, o = set(), self.off(self.base + rva)
        fin = o + taille
        while o < fin:
            page, bloc = struct.unpack_from('<II', self.d, o)
            if bloc < 8:
                break
            for k in range((bloc - 8) // 2):
                v = struct.unpack_from('<H', self.d, o + 8 + 2 * k)[0]
                if v >> 12 == 3:
                    r.add(self.base + page + (v & 0xfff))
            o += bloc
        return r

    def motif(self, va, hexa):
        """les octets en va correspondent au motif hexadecimal ('??' = n'importe quel octet)"""
        b = self.lit(va, len(hexa) // 2)
        return len(b) == len(hexa) // 2 and all(hexa[2 * i] == '?' or b[i] == int(hexa[2 * i:2 * i + 2], 16) for i in range(len(b)))

    def cible(self, va):
        """cible d'un call rel32 (e8) en va, sinon None"""
        b = self.lit(va, 5)
        return va + 5 + struct.unpack('<i', b[1:])[0] if b[0] == 0xe8 else None

    def appels(self, cible):
        """toutes les adresses de 'call cible' (e8 rel32) dans les sections du fichier"""
        r = []
        for vs, rva, rs, rp in self.secs:
            i, fin = rp, rp + min(vs, rs)
            while True:
                i = self.d.find(b'\xe8', i, fin - 4)
                if i < 0:
                    break
                va = self.base + rva + i - rp
                if va + 5 + struct.unpack_from('<i', self.d, i + 1)[0] == cible:
                    r.append(va)
                i += 1
        return r


GROUPE = ('8b74243433c0894424148b0a85c9740c8039007407c644242301eb09c64424230085c974233987e40500000f94c08801'
          '8b02c74004000000008b0285c074098038007404b001eb0232c038442423746933c9894c2418394e0c765e0f1f800000'
          '00008b0285c0740a803800c6442430017505c6442430008b56088b0603d18b4c241c6a00ff742434ff71fc8bca2b4e04'
          '3b5604ffb7800000000f42ca8b0c888b4964e8????????8b4c24188b54241c41894c24183b4e0c72a98b44241483c20c'
          '408954241c8944241483f8060f8238ffffff33c9894c2414')
ENVOI = ('558bec6aff68????????64a10000000050515657a1????????33c5508d45f464a3000000008bf16a10e8????????8bf8'
         '83c404897df0c707????????c745fc00000000c707????????c745fcffffffff8b4e148b560c3bca751c8d0412b92000'
         '00003bc10f42c18d4e0850e8????????8b4e148b560c8b46104148894e1403c18bc82bca3bc20f42c88b4608893c888b'
         '45088947048b450c8947088a451088470c8a451488470d8b4df464890d00000000595f5e8be55dc21000')

exes = {}
for nom, chemin in zip(('ancien', 'patche', 'nouveau'), sys.argv[1:]):
    exes[nom] = Exe(chemin)
    h = hashlib.sha256(exes[nom].d).hexdigest().upper()
    controle(h.startswith(SHA[nom]), f'exe {nom} : empreinte {h[:16]}... (attendu {SHA[nom]}...)')
a, p, n = exes['ancien'], exes['patche'], exes['nouveau']
controle(a.ts == p.ts == 0x6a36c177 and n.ts == 0x6ae228f3, 'horodatages PE : ancien et patche 6a36c177, nouveau 6ae228f3')

print('\n1. ce que le plugin utilise (memes adresses que dans cc2x_hold.c)')
ABS = {'ancien': [0xc97dbd, 0xe1db44, 0xd1ee70, 0xd2523c], 'patche': [0xc97dbd, 0xe1db44, 0xd1ee70, 0xd2523c],
       'nouveau': [0xc97f5d, 0xe1db44, 0xd1eea0, 0xd25258]}          # enq_abs de la table du plugin
V1 = {'ancien': [(0x6fcd62, 0x18), (0x6fd93a, 0x10), (0x63f570, 0x27)], 'patche': [(0x6fcd62, 0x18), (0x6fd93a, 0x10), (0x63f570, 0x27)],
      'nouveau': [(0x6fce72, 0x18), (0x6fda4a, 0x10), (0x63f670, 0x27)]}
for nom, e, groupe, envoi in (('ancien', a, 0x70600e, 0x565ce0), ('patche', p, 0x70600e, 0x565ce0), ('nouveau', n, 0x70611e, 0x565e00)):
    rel = e.relocations()
    dans = sorted(r - envoi for r in rel if envoi <= r < envoi + 0xba)
    controle(dans == [0x06, 0x15, 0x38, 0x45], f'{nom} : Windows reloge exactement 4 adresses dans la fonction d\'envoi (offsets {[hex(x) for x in dans]})')
    controle([e.u32(envoi + k) for k in (0x06, 0x15, 0x38, 0x45)] == ABS[nom], f'{nom} : ces 4 adresses valent, dans le fichier, celles de la table du plugin')
    controle(not any(va <= r < va + t for r in rel for va, t in [(groupe, 0xd8)] + V1[nom]),
             f'{nom} : aucune relocalisation dans le bloc du groupe ni dans les zones de la v1')
    controle(e.motif(groupe, GROUPE), f'{nom} : bloc du groupe de 6 boutons en {groupe:#x} (216 octets, avec "push [edi+0x80]" et "mov ecx,[ecx+0x64]")')
    controle(e.cible(groupe + 0xa2) == envoi, f'{nom} : en {groupe + 0xa2:#x}, appel de la fonction d\'envoi {envoi:#x}')
    controle(e.octets(groupe + 0xd2, '33c9894c2414'), f'{nom} : site du crochet {groupe + 0xd2:#x} = "xor ecx,ecx ; mov [esp+0x14],ecx"')
    controle(e.motif(envoi, ENVOI), f'{nom} : fonction d\'envoi {envoi:#x} conforme jusqu\'a son "ret 0x10" (186 octets)')
    vt = e.u32(envoi + 0x45)
    controle(e.octets(e.u32(vt + 4), 'b814000000c3'), f'{nom} : le message construit est du type 20 (vtable {vt:#x})')
    k = len(e.appels(envoi))
    controle(k == 12, f'{nom} : la fonction d\'envoi est appelee en 12 endroits du jeu (trouve {k})')

print('\n2. qui ecrit l\'octet 0 des boutons (ancien exe)')
controle(a.octets(0x5d5587, '807d0c007413803a005f0f94c088025b5dc20c008a450c8802'),
         'appui 0x5d5530 : type interrupteur -> octet 0 inverse ; sinon octet 0 = valeur')
controle(sorted(a.appels(0x5d5530)) == [0x77b436, 0x782574], 'appui 0x5d5530 appele seulement en 0x77b436 et 0x782574 (les deux traitements des ordres)')
controle(a.cible(0x77b4ca) == 0x565ce0 and a.octets(0x77b4ac, '6a01'),
         'apres l\'appui 0x77b436 : message 20 a chaque joueur, drapeau 1 ("push 1" en 0x77b4ac, envoi en 0x77b4ca)')
controle(a.cible(0x78259b) == 0x565ce0 and a.octets(0x782590, '6a01'), 'apres l\'appui 0x782574 : message 20, drapeau 1 (0x782590, envoi en 0x78259b)')
controle(a.octets(0x706033, '3987e40500000f94c088018b02c7400400000000') and a.cible(0x7060b0) == 0x565ce0,
         'groupe de 6 boutons : octet 0 := "est le choisi" (0x70603c), puis message 20 a chaque joueur, drapeau 0 (envoi en 0x7060b0)')
controle(a.cible(0x6f0a68) == 0x565ce0 and a.octets(0x6f0a0d, 'c60000'), 'panneau d\'autodestruction 0x6f0950 : ecrit l\'octet 0 puis message 20, drapeau 0')
controle(a.octets(0x6c4a60, '8b8bd40000008a04d18844d101'), 'mise a jour 0x6c4330 : octet 1 := octet 0 pour chaque bouton (0x6c4a60)')
controle(sorted(a.appels(0x63f570)) == [0x6fcd74, 0x6fd942], 'lecteur Hold 0x63f570 appele seulement en 0x6fcd74 et 0x6fd942')

print('\n3. ce que voient les joueurs (ancien exe)')
controle(sorted(a.appels(0x5ceb10)) == [0x75cfb0, 0x78340a], 'application du message 20 chez le joueur 0x5ceb10 : appelee en 0x75cfb0 et 0x78340a')
controle(a.octets(0x75cf97, '0fb64f0d510fb64f0c51ff7708'), 'en 0x75cf97 : drapeau (+0xd), valeur (+0xc), bouton (+8) du message passes a 0x5ceb10')
controle(a.octets(0x5ced55, '8b434803ff8a4d10884cf80c'), 'en 0x5ced55 : etat d\'affichage du joueur [+0x48] + bouton*16, octet +0xc := valeur (toujours)')
controle(a.octets(0x5cebda, '807d14000f8471010000'), 'en 0x5cebda : le son du clic seulement si drapeau != 0')

print('\n4. l\'exe patche 8E7FCBB6 (celui que le moddeur lance) ne change rien a ces endroits')
for va, t in ((0x70600e, 0xd8), (0x565ce0, 0xba), (0x5d5530, 0x80), (0x5ceb10, 0x270), (0x6fcd62, 0x18), (0x6fd93a, 0x10), (0x63f570, 0x27)):
    controle(a.lit(va, t) == p.lit(va, t), f'patche = original de {va:#x} a {va + t:#x}')

print()
print('RESULTAT :', 'TOUT EST CONFORME' if not echecs else '%d ECHEC(S)' % len(echecs))
sys.exit(1 if echecs else 0)

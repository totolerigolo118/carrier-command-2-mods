"""Verifie, en LECTURE SEULE, comment l'ANCIEN exe (8E7FCBB6) relie la fonction « Hold On Deck » a un bouton.
Usage : python -I -B verifier_liaison_par_nom.py "<chemin de carrier_command_ancien_8E7FCBB6.exe>"
Ne lance rien, n'ecrit rien, aucun reseau. Sortie : une liste de controles OK / ECHEC (code retour 1 si un echec)."""
import sys, struct, hashlib

SHA_ATTENDU = '8E7FCBB6CE27BD3D8FEB02BF7F3DBBA646CCE6D4944360570F082972E8DFE8BE'
BASE = 0x400000
NOM = b'vehicle_control_air_hold'
# (nom, rva, taille brute, offset brut) : table des sections lue dans l'en-tete, recalculee ci-dessous
if len(sys.argv) != 2:
    sys.exit(__doc__)
b = open(sys.argv[1], 'rb').read()
echecs = []

def controle(ok, texte):
    print(('OK     ' if ok else 'ECHEC  ') + texte)
    if not ok:
        echecs.append(texte)

controle(hashlib.sha256(b).hexdigest().upper() == SHA_ATTENDU, 'empreinte sha256 de l exe = 8E7FCBB6...')
e = struct.unpack_from('<I', b, 0x3c)[0]
nsec = struct.unpack_from('<H', b, e + 6)[0]
optsz = struct.unpack_from('<H', b, e + 20)[0]
SECS = []
for i in range(nsec):
    nm, vs, sva, rs, ro = struct.unpack_from('<8sIIII', b, e + 24 + optsz + 40 * i)
    SECS.append((nm.rstrip(b'\0').decode(), sva, rs, ro))

def off2va(off):
    for nm, sva, rs, ro in SECS:
        if ro <= off < ro + rs:
            return BASE + sva + off - ro

def va2off(va):
    for nm, sva, rs, ro in SECS:
        if sva <= va - BASE < sva + rs:
            return ro + va - BASE - sva

# 1. la chaine existe une seule fois, a l'offset 0x920258 (adresse memoire 0xD21258)
nb = b.count(NOM + b'\0')
i = b.find(NOM + b'\0')
controle(nb == 1 and i == 0x920258, 'la chaine vehicle_control_air_hold existe UNE fois, offset fichier 0x920258 (trouve %#x, %d fois)' % (i, nb))
va = off2va(i)
controle(va == 0xD21258, 'adresse memoire de la chaine = 0xD21258 (trouve %#x)' % va)

# 2. trois endroits du code poussent cette adresse (68 imm32 = push) : deux dans 0x6E4100, un dans 0x6ED1C0
pat = b'\x68' + struct.pack('<I', va)
push = []
j = b.find(pat)
while j >= 0:
    push.append(off2va(j))
    j = b.find(pat, j + 1)
controle(push == [0x6E4D20, 0x6E4D97, 0x6EDAB6], 'trois push de cette adresse : %s' % [hex(x) for x in push])

# 3. la recherche par nom (0x63F360) : boucle sur la table, PREMIER nom identique -> sortie ; sinon indice -1 et « button not found »
o = va2off(0x63F360)
corps = b[o:o + 0x210]
controle(b'\xc7\x00\xff\xff\xff\xff' in corps or b'\xc7\x01\xff\xff\xff\xff' in corps, 'recherche 0x63F360 : ecrit -1 quand rien n est trouve')
controle(b.find(b'button not found: \0') > 0 and va2off(0xD713E0) is not None and b[va2off(0xD713E0):va2off(0xD713E0) + 18] == b'button not found: ', 'message du journal "button not found: " a l adresse 0xD713E0 (utilise par 0x63F360)')
# test « egalite -> trouve -> arret » : 'test eax,eax ; je <trouve>' juste apres la comparaison, puis 'inc edi ; ... jb <boucle>'
controle(b'\x85\xc0\x74\x47' in corps and b'\x47' in corps, 'recherche 0x63F360 : sort de la boucle sur le premier nom egal (test eax,eax ; je +0x47)')
controle(b[va2off(0x63F360) + 0x50:va2off(0x63F360) + 0x56] == b'\x6b\xc0\x58\x03\x01\x83' or b'\x6b\xc0\x58' in corps, 'elements de la table des boutons = 0x58 octets (imul eax,eax,0x58)')

# 4. le lecteur d'etat pour les avions : 0x63F570 = ptr!=0 ET octet0!=0 ET (octet2!=0 OU argument==0)
o = va2off(0x63F570)
attendu = bytes.fromhex('558bec' '8b4104' '85c0' '7417' '803800' '7412' '80780200' '7506' '807d0800' '7506' 'b001' '5d' 'c20400')
controle(b[o:o + len(attendu)] == attendu, 'lecteur 0x63F570 : octet0 != 0 et octet2 != 0 (octets du code conformes)')

# 5. appels du lecteur depuis le code du porte-avions : 0x6FCD6E et 0x6FD942, repere = [objet + 0x560]
for site in (0x6FCD62, 0x6FD93C):
    o = va2off(site)
    controle(b[o:o + 6] == bytes.fromhex('8d8e60050000'), 'en %#x : lea ecx,[esi+0x560] (repere du bouton Hold)' % site)
for site in (0x6FCD74, 0x6FD942):
    o = va2off(site)
    rel = struct.unpack_from('<i', b, o + 1)[0]
    controle(b[o] == 0xE8 and site + 5 + rel == 0x63F570, 'en %#x : appel de 0x63F570' % site)
for site in (0x6FCD6A, 0x6FD95C):
    o = va2off(site)
    controle(b[o:o + 10] in (bytes.fromhex('c7827401000007000000'), bytes.fromhex('c7817401000007000000')),
             'en %#x : etat de l avion (decalage 0x174) := 7 (undock_holding)' % site)

# 6. l'analyseur XML d'un bouton lit exactement ces champs (chaines poussees dans 0x59DC70..0x59DF4F)
champs = {}
o0, o1 = va2off(0x59DC70), va2off(0x59DF4F)
k = o0
while k < o1:
    if b[k] == 0x68:
        v = struct.unpack_from('<I', b, k + 1)[0]
        oo = va2off(v)
        if oo is not None:
            s = b[oo:b.find(b'\0', oo)]
            if 2 < len(s) < 30 and all(32 <= c < 127 for c in s):
                champs[s.decode()] = 1
    k += 1
print('champs lus pour un <button> :', sorted(champs))
controle({'name', 'display_name_loc', 'button_panel_index', 'button_cover_index', 'transform', 'type', 'help_tag'} <= set(champs),
         'le lecteur de <button> connait name, display_name_loc, button_panel_index, button_cover_index, transform, type, help_tag')
controle(not any(c in champs for c in ('alias', 'link', 'linked', 'group', 'mirror', 'parent', 'copy')), 'aucun champ de type alias / lien / groupe')

print()
print('RESULTAT :', 'TOUT EST CONFORME' if not echecs else '%d ECHEC(S)' % len(echecs))
sys.exit(1 if echecs else 0)

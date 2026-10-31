"""Verifications en LECTURE SEULE pour la relecture du SDK CC2X (etape 2).
N'ecrit rien, ne lance rien : lit des fichiers, calcule des empreintes, compare des adresses.
Usage : python -I verifier_sdk.py <dossier_du_clone_SDK> <depot_cc2_patchs>
"""
import hashlib, json, os, re, struct, sys
from pathlib import Path

clone = Path(sys.argv[1]); depot = Path(sys.argv[2])
copie = depot / 'passation_windows' / 'sdk_public_cc2x'
GAME = Path(r'C:\Program Files (x86)\Steam\steamapps\common\Carrier Command 2')
APPDATA = Path(os.environ['APPDATA']) / 'Carrier Command 2'

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()

print('== 1. Le depot actuel contre notre copie du 25/10 (SOURCE.txt) ==')
# (fichier de la copie, fichier dans le clone)
paires = [('CHANGELOG.md','CHANGELOG.md'),('LUA_API.md','docs/LUA_API.md'),('PLUGINS.md','docs/PLUGINS.md'),
          ('README.md','README.md'),('README_PLAYERS.txt','docs/README_PLAYERS.txt'),('WORLD_API.md','docs/WORLD_API.md'),
          ('build.py','build.py'),('cc2x.h','include/cc2x.h'),('examples_hello_plugin/hello.c','examples/hello_plugin/hello.c'),
          ('src/cc2x.c','src/cc2x.c'),('src/world.c','src/world.c')]
for a, b in paires:
    pa, pb = copie / a, clone / b
    same = sha(pa) == sha(pb)
    na = len(pa.read_bytes().splitlines()); nb = len(pb.read_bytes().splitlines())
    print(f'  {b:38s} {"IDENTIQUE" if same else "CHANGE   "}  copie {na:4d} lignes -> clone {nb:4d} lignes')

print('\n== 2. Adresses du SDK (cc2x.c, world.c) contre NOS changements de l\'executable ==')
adr = {}
for f in ('src/cc2x.c', 'src/world.c'):
    t = (clone / f).read_text(encoding='utf-8')
    for m in re.finditer(r'0x[0-9a-fA-F]{6,8}\b', t):
        v = int(m.group(0), 16)
        if 0x400000 <= v < 0x1000000 and v != 0x00af7000:
            adr.setdefault(v, f)
print(f'  {len(adr)} adresses distinctes citees par le SDK')
nos = []
for mod in ('ascenseur_x2', 'temps_x2'):
    d = json.loads((depot / 'tour/outils/modules_exe' / f'{mod}.json').read_text(encoding='utf-8'))
    for c in d['changements']: nos.append((c['va'], mod))
print(f'  {len(nos)} changements de 4 octets chez nous')
best = min(((abs(a - v), a, v, mod) for a in adr for v, mod in nos))
print(f'  plus petite distance : {best[0]} octets (SDK {best[1]:#x} / nous {best[2]:#x}, {best[3]})')
chev = [(a, v, mod) for a in adr for v, mod in nos if abs(a - v) < 16]
print(f'  adresses du SDK a moins de 16 octets d\'un de nos changements : {len(chev)}')
for a, v, mod in chev: print('   !', hex(a), hex(v), mod)

print('\n== 3. Executable reel : l\'en-tete que le SDK controle (horodatage PE + taille d\'image) ==')
exe = GAME / 'carrier_command.exe'
b = exe.read_bytes()
pe = struct.unpack_from('<I', b, 0x3c)[0]
ts = struct.unpack_from('<I', b, pe + 8)[0]
size_img = struct.unpack_from('<I', b, pe + 24 + 56)[0]
print(f'  horodatage {ts:#010x} (attendu 0x6a36c177) ; taille d\'image {size_img:#010x} (attendu 0x00af7000)')
print('  sha256 actuel', sha(exe).upper())
# octets verifies par le SDK au demarrage (cc2x.c) : ils doivent etre ceux de l'original
def va2off(va):
    nsec = struct.unpack_from('<H', b, pe + 6)[0]; opt = struct.unpack_from('<H', b, pe + 20)[0]
    base = struct.unpack_from('<I', b, pe + 24 + 28)[0]
    for i in range(nsec):
        o = pe + 24 + opt + 40 * i
        vs, vaddr, rs, rp = struct.unpack_from('<IIII', b, o + 8)
        if base + vaddr <= va < base + vaddr + max(vs, rs): return rp + (va - base - vaddr)
attendus = {0x004465ec: bytes([0x6a,0x20,0x89,0x85,0x64,0xff,0xff,0xff]),
            0x008cda70: bytes([0x8b,0x41,0x14,0x85,0xd2,0x7e,0x0d,0xc1]),
            0x008ce200: bytes([0x55,0x8b,0xec,0x83,0xec,0x08,0x53,0x56]),
            0x008ff6b0: bytes([0x55,0x8b,0xec,0x83,0xe4,0xf8,0x83,0xec]),
            0x00908220: bytes([0x55,0x8b,0xec,0x83,0xec,0x08,0x53,0x8b]),
            0x00904a50: bytes([0x56,0x8b,0x71,0x10,0x33,0xd2,0x6a,0x20]),
            0x00904050: bytes([0x53,0x8b,0xd9,0x56,0x57,0x8b,0x7b,0x10])}
ok = 0
for va, att in attendus.items():
    o = va2off(va); got = b[o:o+8]
    ok += got == att
    print(f'  octets en {va:#010x} : {"conformes" if got == att else "DIFFERENTS " + got.hex()}')
print(f'  {ok}/{len(attendus)} sites de controle conformes (l\'executable patche passe les controles du SDK)')
for sl, ex in ((0x00d34bc4, 0x00772fd0), (0x00d34bc8, 0x0077ee10), (0x00d34bcc, 0x0077eea0)):
    o = va2off(sl); v = struct.unpack_from('<I', b, o)[0]
    print(f'  case de table {sl:#010x} contient {v:#010x} (attendu {ex:#010x}) : {"OK" if v == ex else "DIFFERENT (relogee ? lue sur disque avant relocation)"}')

print('\n== 4. Mods actifs : un dossier cc2x serait charge par le SDK ==')
xml = (APPDATA / 'mods.xml').read_text(encoding='utf-8')
for m in re.finditer(r'<path value="([^"]+)"', xml):
    d = Path(m.group(1))
    print(f'  {d} : existe={d.exists()}  content/cc2x={(d/"content"/"cc2x").exists()}  cc2x={(d/"cc2x").exists()}')
print('  dinput8.dll deja dans le dossier du jeu :', (GAME / 'dinput8.dll').exists())
print('  cc2x.ini dans le dossier du jeu :', (GAME / 'cc2x.ini').exists(), '; dossier cc2x dans le dossier du jeu :', (GAME / 'cc2x').exists())
print('  dossier de reglages (AppData / Carrier Command 2 / cc2x) :', (APPDATA / 'cc2x').exists())
print('  autres dinput8.dll trouvees dans les mods locaux :', [str(p) for p in (APPDATA / 'mods').rglob('dinput8.dll')])

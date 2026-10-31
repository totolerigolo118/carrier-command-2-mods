import re, sys
# (fichier objdump, plage, ancienne constante, nouvelle constante, groupe)
REGLES = [
    ("tick_raw.s", 0x10019455a, 0x100194590, 0x102869a64, 0x10286995c, "ascenseur"),
    ("tick_raw.s", 0x10019455a, 0x100194590, 0x102869978, 0x1028697a4, "ascenseur"),
    ("dock_air_raw.s", 0x1001ae82c, 0x1001aec08, 0x102869ad4, 0x102869750, "grue"),
    ("dock_air_raw.s", 0x1001ae82c, 0x1001aec08, 0x10286975c, 0x1028b232c, "grue"),
    ("dock_air_raw.s", 0x1001ae82c, 0x1001aec08, 0x1028699d8, 0x102869c7c, "grue"),
    ("dock_air_raw.s", 0x1001ae82c, 0x1001aec08, 0x1028699d4, 0x102869b80, "grue"),
    ("dock_air_raw.s", 0x1001ae82c, 0x1001aec08, 0x102869a04, 0x102869974, "grue"),
    ("dock_air_raw.s", 0x1001ae82c, 0x1001aec08, 0x1028697d0, 0x10286986c, "grue"),
    ("dock_air_raw.s", 0x1001accd8, 0x1001b2618, 0x1028697a4, 0x1028697b0, "roulage"),
    ("dock_air_raw.s", 0x1001accd8, 0x1001b2618, 0x1028697bc, 0x10286976c, "roulage"),
]
d = sys.argv[1]
for fic, lo, hi, old, new, g in REGLES:
    for line in open(d + "/" + fic):
        m = re.match(r"\s*([0-9a-f]+):\s+((?:[0-9a-f]{2} )+)\s*(\S+)", line)
        if not m: continue
        va = int(m.group(1), 16)
        if not (lo <= va < hi) or ("0x%x" % old) not in line: continue
        octets = m.group(2).split()
        fin = va + len(octets)
        disp = int.from_bytes(bytes.fromhex("".join(octets[-4:])), "little", signed=True)
        assert fin + disp == old, (hex(va), line)
        print('    (0x%x, "%s", 0x%x, 0x%x, "%s", "%s"),' % (va, "".join(octets), old, new, g, m.group(3)))

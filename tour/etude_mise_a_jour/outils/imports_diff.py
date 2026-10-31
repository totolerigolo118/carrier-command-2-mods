import struct, sys, re
def imports(b):
    e = struct.unpack_from('<I', b, 0x3c)[0]
    nsec = struct.unpack_from('<H', b, e+6)[0]; optsz = struct.unpack_from('<H', b, e+20)[0]
    opt = e + 24; so = opt + optsz
    secs = [struct.unpack_from('<8sIIII', b, so+40*i) for i in range(nsec)]
    def r2o(rva):
        for n, vs, va, rs, ro in secs:
            if va <= rva < va + max(vs, rs): return ro + rva - va
    rva_imp = struct.unpack_from('<I', b, opt+104)[0]
    res = {}
    p = r2o(rva_imp)
    while True:
        oft, _, _, name, ft = struct.unpack_from('<IIIII', b, p)
        if name == 0: break
        o = r2o(name); dll = b[o:b.index(b'\0', o)].decode().lower()
        q = r2o(oft or ft); fs = set()
        while True:
            v = struct.unpack_from('<I', b, q)[0]
            if v == 0: break
            if v & 0x80000000: fs.add('#%d' % (v & 0xffff))
            else:
                o2 = r2o(v) + 2; fs.add(b[o2:b.index(b'\0', o2)].decode())
            q += 4
        res[dll] = fs; p += 20
    return res
A = open(sys.argv[1], 'rb').read(); B = open(sys.argv[2], 'rb').read()
ia, ib = imports(A), imports(B)
print('DLL importees: ancien', len(ia), 'nouveau', len(ib), '| DLL seulement dans un des deux:', sorted(set(ia) ^ set(ib)))
print('fonctions importees: ancien', sum(map(len, ia.values())), 'nouveau', sum(map(len, ib.values())))
for d in sorted(set(ia) & set(ib)):
    if ia[d] != ib[d]:
        print(' ', d, 'ajoutees:', sorted(ib[d]-ia[d]), 'retirees:', sorted(ia[d]-ib[d]))
print('=> table des imports identique' if ia == ib else '=> table des imports DIFFERENTE')
for kw in (b'dinput8', b'cc2x', b'VirtualProtect', b'IsDebuggerPresent', b'CheckRemoteDebugger', b'MinHook', b'CryptHash', b'BCrypt', b'WinVerifyTrust', b'tamper', b'integrity', b'checksum', b'anti'):
    ca = A.count(kw) + A.count(kw.decode().encode('utf-16le')); cb = B.count(kw) + B.count(kw.decode().encode('utf-16le'))
    print('  motif %-22s ancien %d  nouveau %d' % (kw.decode(), ca, cb))

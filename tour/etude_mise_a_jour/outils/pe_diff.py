import struct, sys, hashlib, difflib

def pe_info(b):
    e = struct.unpack_from('<I', b, 0x3c)[0]
    assert b[e:e+4] == b'PE\0\0'
    machine, nsec, ts, _, _, optsz, chars = struct.unpack_from('<HHIIIHH', b, e+4)
    opt = e + 24
    magic = struct.unpack_from('<H', b, opt)[0]
    entry = struct.unpack_from('<I', b, opt+16)[0]
    imgbase = struct.unpack_from('<I', b, opt+28)[0]
    sizeimg, sizehdr, chk = struct.unpack_from('<III', b, opt+56)
    secs = []
    so = opt + optsz
    for i in range(nsec):
        n, vs, va, rs, ro = struct.unpack_from('<8sIIII', b, so + 40*i)
        secs.append((n.rstrip(b'\0').decode(), vs, va, rs, ro))
    return dict(ts=ts, entry=entry, imgbase=imgbase, sizeimg=sizeimg, sizehdr=sizehdr, chk=chk, secs=secs, opt=opt, e=e)

def load(p):
    return open(p, 'rb').read()

def main(a, b):
    A, B = load(a), load(b)
    print('A', a, len(A), hashlib.sha256(A).hexdigest())
    print('B', b, len(B), hashlib.sha256(B).hexdigest())
    ia, ib = pe_info(A), pe_info(B)
    for k in ('ts', 'entry', 'imgbase', 'sizeimg', 'sizehdr', 'chk'):
        print(k, hex(ia[k]), hex(ib[k]))
    print('sections A'); [print(' ', s[0], 'vs=%x va=%x rawsz=%x rawoff=%x' % s[1:]) for s in ia['secs']]
    print('sections B'); [print(' ', s[0], 'vs=%x va=%x rawsz=%x rawoff=%x' % s[1:]) for s in ib['secs']]
    # header diffs
    print('header diffs (first 0x400):')
    for i in range(0x400):
        if A[i] != B[i]:
            print('  off %x  %02x -> %02x' % (i, A[i], B[i]))
    # per-section compare
    for sa, sb in zip(ia['secs'], ib['secs']):
        ra = A[sa[4]:sa[4]+sa[3]]
        rb = B[sb[4]:sb[4]+sb[3]]
        if ra == rb:
            print('section', sa[0], 'identique')
            continue
        n = min(len(ra), len(rb))
        # contiguous differences (same offset)
        runs = []
        i = 0
        while i < n:
            if ra[i] != rb[i]:
                j = i
                while j < n and (ra[j] != rb[j]):
                    j += 1
                runs.append((i, j))
                i = j
            else:
                i += 1
        print('section', sa[0], 'tailles', len(ra), len(rb), 'runs differents (meme offset):', len(runs))
        for (i, j) in runs[:60]:
            va = sa[2] + i
            print('   +%x..%x (VA 0x%x) len %d  A=%s  B=%s' % (i, j, ia['imgbase'] + va, j - i, ra[i:min(j, i+16)].hex(), rb[i:min(j, i+16)].hex()))
        if len(runs) > 60:
            print('   ... %d runs au total' % len(runs))

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])

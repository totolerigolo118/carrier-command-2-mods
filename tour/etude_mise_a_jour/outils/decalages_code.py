import sys
A = open(sys.argv[1], 'rb').read(); B = open(sys.argv[2], 'rb').read()
# .text : raw offset 0x400, A size 0x8d4c00, B size 0x8d4e00
ra, sa = 0x400, 0x8d4c00
rb, sb = 0x400, 0x8d4e00
W = 32
last = None; out = []
for i in range(0, sa - W, 0x80):
    w = A[ra+i:ra+i+W]
    if w.count(0) > 24 or len(set(w)) < 6: continue
    lo = rb + i; hi = min(rb + sb, lo + 0x240 + W)
    ds = []; p = B.find(w, lo, hi)
    while p != -1 and len(ds) < 3:
        ds.append(p - lo); p = B.find(w, p + 1, hi)
    if len(ds) == 1:
        d = ds[0]
        if d != last:
            out.append((i, d)); last = d
print('transitions de decalage .text (octets) [offset_ancien_dans_.text, decalage]:')
for i, d in out[:40]: print('  +0x%x  VA 0x%x  decalage +0x%x' % (i, 0x401000 + i, d))
print('nb de transitions:', len(out))

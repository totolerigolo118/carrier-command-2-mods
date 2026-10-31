import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import portlib as P
for f in (P.F_ORIG,P.F_PATCH,P.F_NEW):
    e=P.Exe(f); p=e.pe
    print(os.path.basename(f))
    for k in p:
        if k != 'secs':
            v = p[k]
            print('   ', k, hex(v) if isinstance(v,int) else v)
    for s in e.secs: print('  ',s[0],hex(s[1]),hex(s[2]),hex(s[3]),hex(s[4]),hex(s[5]))

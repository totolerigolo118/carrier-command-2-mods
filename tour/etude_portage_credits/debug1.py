import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from analyse import *
import json
a = json.load(open(P.TRAVAIL + 'analyse_sites.json'))
c = a['ascenseur_x2'][17]
print(c['va'], hex(c['va']), c['avant'])
va = c['va']
for d in (0x110,):
    co, io = P.chain(old, va)
    cn, inn = P.chain(new, va + d)
    print(io, inn, len(co), len(cn))
    for x, y in zip(co, cn):
        print('  ', 'OK ' if sig(x) == sig(y) else 'XX ', fmt(x), '|', fmt(y))
print(hex(va), old.b[old.va2off(va)-3:old.va2off(va)].hex(), new.b[new.va2off(va+0x110)-3:new.va2off(va+0x110)].hex())

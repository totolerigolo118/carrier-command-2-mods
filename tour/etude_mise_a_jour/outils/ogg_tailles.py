import csv, sys, collections
def load(p):
    d = {}
    with open(p, encoding='utf-8-sig', newline='') as f:
        for r in csv.reader(f, delimiter='\t'):
            if len(r) >= 3 and r[1].isdigit():
                d[r[0]] = r
    return d
A = load('avant/jeu_fichiers.tsv'); B = load('apres/jeu_fichiers.tsv')
oggs = [k for k in A if k.lower().endswith('.ogg') and k in B]
print('ogg dans les deux listes:', len(oggs))
chg = [k for k in oggs if A[k][3] != B[k][3]]
print('ogg dont le sha256 differe (avant douteux):', len(chg))
dsz = collections.Counter(int(B[k][1]) - int(A[k][1]) for k in oggs)
print('ogg: delta de taille (apres-avant) -> nb de fichiers (10 plus frequents):')
for v, n in dsz.most_common(10): print('  ', v, n)
dd = collections.Counter((A[k][2], B[k][2]) for k in oggs)
print('dates (avant, apres) les plus frequentes:')
for v, n in dd.most_common(5): print('  ', v, n)
tot = sum(int(B[k][1]) for k in oggs)
print('taille totale ogg apres (octets):', tot)

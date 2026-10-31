import json,glob,re,struct,os
OLD=r'C:\Users\UTILISATEUR\Documents\cc2-patchs\tour\sauvegardes\carrier_command_1.5.18_original.exe'
A=open(OLD,'rb').read(); B=open('exe_new/carrier_command_NEW.exe','rb').read()
BASE=0x400000
def secs(b):
    e=struct.unpack_from('<I',b,0x3c)[0]; n=struct.unpack_from('<H',b,e+6)[0]; o=struct.unpack_from('<H',b,e+20)[0]
    return [struct.unpack_from('<8sIIII',b,e+24+o+40*i) for i in range(n)]
SB=secs(B)
def off2va(S,off):
    for nm,vs,sva,rs,ro in S:
        if ro<=off<ro+rs: return BASE+sva+off-ro, nm.rstrip(b'\0').decode()
    return None,None
tot=0;ok=0;rows=[]
for p in sorted(glob.glob(r'C:\Users\UTILISATEUR\Documents\cc2-patchs\tour\outils\modules_exe\*.json')):
    m=json.load(open(p,encoding='utf-8'))
    for c in m['changements']:
        o=c['offset']
        if o<0x400:  # header padding
            rows.append((m['nom'],hex(c['va']),'en-tete (hors code)','-')); tot+=1; continue
        tot+=1
        res=None
        for L in (12,10,8,6,5,4):
            pre=A[o-L:o]; suf=A[o+4:o+4+L]
            rx=re.compile(re.escape(pre)+b'.{4}'+re.escape(suf),re.S)
            hits=[h.start()+L for h in rx.finditer(B)]
            if len(hits)==1:
                res=(L,hits[0]);break
            if len(hits)==0: continue
            if len(hits)>1: continue
        if res:
            L,no=res; va,sn=off2va(SB,no); ok+=1
            rows.append((m['nom'],hex(c['va']),'-> nouveau '+hex(va)+' '+sn,'ctx%d avant_nouveau=%s'%(L,B[no:no+4].hex()+(' (=ancien)' if B[no:no+4]==A[o:o+4] else ' (DIFFERENT: '+A[o:o+4].hex()+')'))))
        else:
            rows.append((m['nom'],hex(c['va']),'non retrouve par contexte (octets voisins modifies)','-'))
for r in rows: print(*r)
print('retrouves',ok,'sur',tot)

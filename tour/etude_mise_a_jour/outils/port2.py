import json,glob,struct
OLD=r'C:\Users\UTILISATEUR\Documents\cc2-patchs\tour\sauvegardes\carrier_command_1.5.18_original.exe'
A=open(OLD,'rb').read(); B=open('exe_new/carrier_command_NEW.exe','rb').read()
ok=bad=0; lines=[]
for p in sorted(glob.glob(r'C:\Users\UTILISATEUR\Documents\cc2-patchs\tour\outils\modules_exe\*.json')):
    m=json.load(open(p,encoding='utf-8'))
    for c in m['changements']:
        o=c['offset']
        if o<0x400: continue
        va=c['va']
        shift = 0x130 if va>0x800000 else 0x110
        old=A[o:o+4]; new=B[o+shift:o+shift+4]
        ov=struct.unpack('<I',old)[0]; nv=struct.unpack('<I',new)[0]
        # context equality of the 6 bytes before
        pre_eq = A[o-6:o]==B[o+shift-6:o+shift]
        kind='ptr .rdata' if 0xcd6000<=ov<0xe1d000 else ('autre')
        exp=(ov+0x38)&0xffffffff if kind=='ptr .rdata' else ov
        good = (nv==exp) and pre_eq if kind=='ptr .rdata' else (nv==ov or pre_eq)
        ok+=good; bad+=(not good)
        lines.append('%-20s %s +0x%x  ancien=%s nouveau=%s  attendu(+0x38 si const)=%08x  %s'%(m['nom'],hex(va),shift,old.hex(),new.hex(),exp,'OK' if good else 'A VERIFIER'))
print('\n'.join(l for l in lines if 'A VERIFIER' in l))
print('sites code/const:',ok+bad,' coherents (decalage uniforme):',ok,' a verifier:',bad)

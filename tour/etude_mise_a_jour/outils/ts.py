import re,struct,datetime,os
G=r'C:\Program Files (x86)\Steam\steamapps\common\Carrier Command 2'
OLD=r'C:\Users\UTILISATEUR\Documents\cc2-patchs\tour\sauvegardes\carrier_command_1.5.18_original.exe'
def ts(p):
    b=open(p,'rb').read(0x400); e=struct.unpack_from('<I',b,0x3c)[0]
    t=struct.unpack_from('<I',b,e+8)[0]; sz=struct.unpack_from('<I',b,e+24+56)[0]
    return hex(t), datetime.datetime.fromtimestamp(t,datetime.UTC).strftime('%Y-%m-%d %H:%M'), hex(sz)
for p in ['exe_new/carrier_command_NEW.exe',OLD,'exe_new/dedicated_server_NEW.exe',G+r'\carrier_command_vr.exe',G+r'\mod_dev_kit\bin\build_content.exe',G+r'\carrier_command_test_cercle.exe']:
    print(os.path.basename(p), ts(p))
for p in ['exe_new/carrier_command_NEW.exe',OLD]:
    b=open(p,'rb').read()
    print(os.path.basename(p),'versions texte:',set(m.group(0) for m in re.finditer(rb'1\.5\.\d+',b)))
    for m in re.finditer(rb'[ -~]{0,30}1\.5\.1\d[ -~]{0,30}',b): print('   ',m.start(),m.group(0)[:80])

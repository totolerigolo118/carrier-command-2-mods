import struct
OLD=r'C:\Users\UTILISATEUR\Documents\cc2-patchs\tour\sauvegardes\carrier_command_1.5.18_original.exe'
A=open(OLD,'rb').read(); B=open('exe_new/carrier_command_NEW.exe','rb').read()
BASE=0x400000
def secs(b):
    e=struct.unpack_from('<I',b,0x3c)[0]; n=struct.unpack_from('<H',b,e+6)[0]; o=struct.unpack_from('<H',b,e+20)[0]
    return [struct.unpack_from('<8sIIII',b,e+24+o+40*i) for i in range(n)]
SA,SB=secs(A),secs(B)
def rd(b,S,va,n):
    r=va-BASE
    for nm,vs,sva,rs,ro in S:
        if sva<=r<sva+max(vs,rs): return b[ro+r-sva:ro+r-sva+n]
    return None
SIG={0x8cda70:'8b4114 85d2 7e0d c1',0x8ce200:'558bec83ec0853 56',0x8ff6b0:'558bec83e4f883ec',0x908220:'558bec83ec08538b',0x904a50:'568b7110 33d2 6a20',0x904050:'538bd9565 78b7b10'}
print('--- cases de table serveur (SDK attend 0x772fd0, 0x77ee10, 0x77eea0)')
for va in (0xd34bc4,0xd34bc8,0xd34bcc):
    print(hex(va),'ancien',rd(A,SA,va,4)[::-1].hex(),'nouveau',rd(B,SB,va,4)[::-1].hex())
print('--- site Lua 0x4465ec (SDK attend 6a20 8985 64ffffff)')
print('ancien',rd(A,SA,0x4465ec,8).hex(),'nouveau',rd(B,SB,0x4465ec,8).hex())
print('--- 6 debuts de fonctions Lua (8 octets)')
for va in (0x8cda70,0x8ce200,0x8ff6b0,0x908220,0x904a50,0x904050):
    print(hex(va),'ancien',rd(A,SA,va,8).hex(),'nouveau',rd(B,SB,va,8).hex())
print('--- nilobject 0xd03518 (rdata)')
print('ancien',rd(A,SA,0xd03518,16).hex(),'nouveau',rd(B,SB,0xd03518,16).hex())
print('--- 0x71dbbf')
print('ancien',rd(A,SA,0x71dbbf,12).hex(),'nouveau',rd(B,SB,0x71dbbf,12).hex())
# where did the old server tick function go ? search old fn prologue bytes (32) in new
for name,va in (('server_init',0x772fd0),('server_tick',0x77ee10),('server_end',0x77eea0)):
    pat=rd(A,SA,va,16)
    hits=[i for i in range(0x400,0x8d5000) if B[i:i+16]==pat] if False else []
    import re
    hits=[m.start() for m in re.finditer(re.escape(pat),B)]
    print(name,hex(va),'prologue',pat.hex(),'-> trouve dans nouveau a offsets',[hex(h) for h in hits[:5]], '(VA', [hex(BASE+0x1000+h-0x400) for h in hits[:5]],')')

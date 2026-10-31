import re
OLD=r'C:\Users\UTILISATEUR\Documents\cc2-patchs\tour\sauvegardes\carrier_command_1.5.18_original.exe'
def strs(p):
    b=open(p,'rb').read()
    return set(m.group(0) for m in re.finditer(rb'[A-Za-z_][A-Za-z0-9_ .:/\()\-,%\[\]\'"=<>!?]{9,}',b))
o=strs(OLD); n=strs('exe_new/carrier_command_NEW.exe')
def good(s):
    t=s.decode('latin1'); alpha=sum(c.isalpha() or c in ' _' for c in t)
    return alpha/len(t)>0.8
print('NEW only:'); [print('  +',s.decode()[:140]) for s in sorted(n-o) if good(s)]
print('OLD only:'); [print('  -',s.decode()[:140]) for s in sorted(o-n) if good(s)]

import json,glob,os,hashlib
B=os.path.dirname(os.path.abspath(__file__))
R=B+'/copies/'
o=open(R+'carrier_command_ORIGINAL_1C9A01C3.exe','rb').read()
p=open(R+'carrier_command_PATCHE_8E7FCBB6.exe','rb').read()
print(len(o),len(p))
diff=[i for i in range(len(o)) if o[i]!=p[i]]
print('octets differents:',len(diff))
blocs=[]
for i in diff:
    if blocs and i-blocs[-1][1]<=1: blocs[-1][1]=i
    else: blocs.append([i,i])
print('blocs:',[(hex(a),b-a+1) for a,b in blocs])
mods={}
for f in sorted(glob.glob(B+'/../outils/modules_exe/*.json')):
    m=json.load(open(f)); mods[m['nom']]=m
couverts=set()
for n,m in mods.items():
    pat=0;org=0;autre=0
    for c in m['changements']:
        r=p[c['offset']:c['offset']+4].hex()
        ro=o[c['offset']:c['offset']+4].hex()
        assert ro==c['avant'],(n,c)
        if r==c['apres']: pat+=1; couverts.update(range(c['offset'],c['offset']+4))
        elif r==c['avant']: org+=1
        else: autre+=1
    print(n,'patche',pat,'origine',org,'autre',autre,'sur',len(m['changements']))
reste=[i for i in diff if i not in couverts]
print('octets differents non expliques par un module:',len(reste))
print('sha patche',hashlib.sha256(p).hexdigest().upper())

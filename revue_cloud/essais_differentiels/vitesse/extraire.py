# Extrait du module genere (outil/modules/vitesse_escadrille.py) les octets reels : greffe, branchement,
# octets d'origine. Ecrit greffe.bin, branch_avant.bin, branch.bin a cote de ce script.
import importlib.util, os
ICI = os.path.dirname(os.path.abspath(__file__))
MODULE = os.path.join(ICI, "..", "..", "..", "outil", "modules", "vitesse_escadrille.py")
spec = importlib.util.spec_from_file_location("m", MODULE)
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
for nom, octets in (("greffe.bin", m.RETOUCHES[0][3]), ("branch_avant.bin", m.RETOUCHES[1][2]),
                    ("branch.bin", m.RETOUCHES[1][3])):
    open(os.path.join(ICI, nom), "wb").write(bytes.fromhex(octets))

import os
p = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'portlib.py')
s = open(p, encoding='utf-8').read()
s = s.replace('back + 40)', 'back + 100)')
open(p, 'w', encoding='utf-8').write(s)

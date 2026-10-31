import sys, struct, importlib.util
from collections import defaultdict, deque
from capstone.x86 import X86_REG_XMM0, X86_REG_XMM2, X86_REG_XMM5, X86_REG_XMM7, X86_OP_IMM, X86_OP_MEM
spec = importlib.util.spec_from_file_location('vs', r'C:\Users\UTILISATEUR\Documents\cc2-patchs\tour\etudes_circuit_atterrissage\verifier_sites.py')
vs = importlib.util.module_from_spec(spec); spec.loader.exec_module(vs)
img = vs.Image(sys.argv[1])
REG = {'xmm7':X86_REG_XMM7,'xmm5':X86_REG_XMM5,'xmm2':X86_REG_XMM2}[sys.argv[2]]
ENTRY = 0x6FC7E0
lo, hi = 0x6F5000, 0x713200
o = img.off(lo)
ins_all = list(img.md.disasm(bytes(img.data[o:o+hi-lo]), lo))
I = {i.address:i for i in ins_all}
order = [i.address for i in ins_all]
nxt = {order[k]:order[k+1] for k in range(len(order)-1)}
tables = {0x6fddde:(0x701fa8,5), 0x700ef2:(0x701fbc,5), 0x7018da:(0x701fd0,6), 0x703338:(0x703e18,4)}
def succs(a):
    i = I[a]
    m = i.mnemonic
    out = []
    if m == 'ret': return out
    if m == 'jmp':
        op = i.operands[0]
        if op.type == X86_OP_IMM: return [op.imm & 0xFFFFFFFF]
        # jump table
        for ja,(tb,n) in tables.items():
            if a == ja or (a-6 <= ja <= a+6 and i.operands[0].type==X86_OP_MEM and (i.operands[0].mem.disp&0xFFFFFFFF)==tb):
                return [struct.unpack('<I', img.octets(tb+4*k,4))[0] for k in range(n)]
        return []
    if m.startswith('j'):
        t = i.operands[0].imm & 0xFFFFFFFF
        out = [t]
    if a in nxt: out.append(nxt[a])
    return out
# defs: a def is identified by address of writing instruction (or 'CALL@addr'); entry = 'ENTRY'
IN = defaultdict(set)
IN[ENTRY] = {'ENTRY'}
wl = deque([ENTRY]); seen=set()
while wl:
    a = wl.popleft()
    if a not in I: continue
    i = I[a]
    cur = set(IN[a])
    rd, wr = i.regs_access()
    if False:
        cur = {'CALL@%x' % a}
    elif REG in wr:
        cur = {'DEF@%x' % a}
    for s in succs(a):
        if s not in I: continue
        if not cur <= IN[s] or s not in seen:
            IN[s] |= cur
            seen.add(s)
            wl.append(s)
uses = []
for a in sorted(seen | {ENTRY}):
    i = I[a]
    rd, wr = i.regs_access()
    if REG in rd and a>=0x6fdd00 and a<=0x701000:
        uses.append((a, i, sorted(IN[a])))
for a,i,d in uses:
    print('%x %-7s %-28s <- %s' % (a, i.mnemonic, i.op_str, ' '.join(d)))
print('reached', len(seen), 'hoist1', 0x6fdda9 in seen, 'tailA', 0x7007e3 in seen, 'tailB', 0x700c10 in seen, 'st3mul', 0x6fedd5 in seen)
print(hex(ENTRY), I.get(ENTRY) and I[ENTRY].mnemonic)

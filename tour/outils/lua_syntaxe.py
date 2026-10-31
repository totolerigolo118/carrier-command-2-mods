#!/usr/bin/env python3
"""Verificateur de SYNTAXE Lua 5.3, fait maison (pas de programme tiers, rien n'est execute).

    python -I lua_syntaxe.py fichier.lua [dossier ...]      verifie les fichiers (et tous les *.lua des dossiers)
    python -I lua_syntaxe.py -q ...                          n'affiche que les erreurs et le total

Il lit chaque fichier, le decoupe en lexemes puis le fait passer dans une grammaire de Lua 5.3 (celle de lparser.c) :
instructions, expressions avec les priorites de Lua, constructeurs de tables, fonctions, boucles, goto / etiquettes,
et `break` hors d'une boucle. Il s'arrete a la PREMIERE erreur de chaque fichier, comme le compilateur de Lua
(« fichier:ligne: message pres de 'lexeme' »). Code de sortie 1 s'il y a au moins une erreur.

Il ne verifie PAS le sens du programme (variables inconnues, types, appels) : seulement qu'il se compile.
Il est verifie par test_lua_syntaxe.py (cas bons et mauvais) et sur tous les scripts Lua du jeu (aucune erreur attendue).
Les attributs de Lua 5.4 (`local x <const>`) et l'operateur `//` entier existant en 5.3 : le premier est refuse, le second accepte.
"""
import os
import re
import sys

KEYWORDS = {'and', 'break', 'do', 'else', 'elseif', 'end', 'false', 'for', 'function', 'goto', 'if', 'in', 'local', 'nil',
            'not', 'or', 'repeat', 'return', 'then', 'true', 'until', 'while'}
BLOCK_FOLLOW = {'else', 'elseif', 'end', 'until'}
OPS3 = {'...'}
OPS2 = {'==', '~=', '<=', '>=', '//', '::', '<<', '>>', '..'}
OPS1 = set('+-*/%^#&~|<>=(){}[];:,.')
BINARY = {  # operateur : (priorite gauche, priorite droite), comme lparser.c
    '+': (10, 10), '-': (10, 10), '*': (11, 11), '%': (11, 11), '^': (14, 13), '/': (11, 11), '//': (11, 11),
    '&': (6, 6), '|': (4, 4), '~': (5, 5), '<<': (7, 7), '>>': (7, 7), '..': (9, 8),
    '==': (3, 3), '<': (3, 3), '<=': (3, 3), '~=': (3, 3), '>': (3, 3), '>=': (3, 3), 'and': (2, 2), 'or': (1, 1)}
UNARY_PRIORITY = 12
NUM_DEC = re.compile(r'(\d+\.?\d*|\.\d+)([eE][+-]?\d+)?')
NUM_HEX = re.compile(r'0[xX]([0-9a-fA-F]*)(\.([0-9a-fA-F]*))?([pP][+-]?\d+)?')


class LuaSyntaxError(Exception):
    def __init__(self, line, msg, near=None):
        super().__init__(msg)
        self.line, self.msg, self.near = line, msg, near

    def __str__(self):
        return '%d: %s%s' % (self.line, self.msg, (" pres de '%s'" % self.near) if self.near is not None else '')


class Tok:
    __slots__ = ('t', 'v', 'line')

    def __init__(self, t, v, line):
        self.t, self.v, self.line = t, v, line

    def text(self):
        return '<fin du fichier>' if self.t == 'eof' else str(self.v)


# ------------------------------------------------------------------ lexeur
def long_bracket_level(s, i):
    """Si s[i:] commence par [=*[ renvoie le nombre de '=' (niveau), sinon -1."""
    if s[i] != '[':
        return -1
    j = i + 1
    while j < len(s) and s[j] == '=':
        j += 1
    return (j - i - 1) if j < len(s) and s[j] == '[' else -1


def read_long(s, i, level, line, what):
    """s[i] est le premier '[' ; renvoie (texte, nouvel_index, nouvelle_ligne)."""
    start = i + level + 2
    close = ']' + '=' * level + ']'
    end = s.find(close, start)
    if end < 0:
        raise LuaSyntaxError(line, 'chaine ou commentaire long non termine (%s)' % what)
    body = s[start:end]
    return body, end + len(close), line + s.count('\n', i, end + len(close))


def lex(s):
    toks, i, n, line = [], 0, len(s), 1
    if s.startswith('#'):                      # ligne de shebang
        j = s.find('\n')
        i = n if j < 0 else j
    while i < n:
        c = s[i]
        if c == '\n':
            line += 1; i += 1; continue
        if c in ' \t\r\f\v':
            i += 1; continue
        if c == '-' and s.startswith('--', i):
            lvl = long_bracket_level(s, i + 2) if i + 2 < n else -1
            if lvl >= 0:
                _, i, line = read_long(s, i + 2, lvl, line, 'commentaire')
            else:
                j = s.find('\n', i)
                i = n if j < 0 else j
            continue
        if c.isalpha() or c == '_':
            m = re.compile(r'[A-Za-z_][A-Za-z0-9_]*').match(s, i)
            w = m.group()
            toks.append(Tok('kw' if w in KEYWORDS else 'name', w, line))
            i = m.end(); continue
        if c.isdigit() or (c == '.' and i + 1 < n and s[i + 1].isdigit()):
            m = NUM_HEX.match(s, i) if s.startswith(('0x', '0X'), i) else None
            if m:
                if not (m.group(1) or m.group(3)):
                    raise LuaSyntaxError(line, 'nombre mal forme', s[i:i + 3])
            else:
                m = NUM_DEC.match(s, i)
            end = m.end()
            if end < n and (s[end].isalnum() or s[end] == '_' or s[end] == '.'):
                raise LuaSyntaxError(line, 'nombre mal forme', s[i:end + 1])
            toks.append(Tok('num', s[i:end], line))
            i = end; continue
        if c == '"' or c == "'":
            q, j, ok = c, i + 1, False
            while j < n:
                d = s[j]
                if d == q:
                    ok = True; break
                if d == '\n':
                    break
                if d == '\\':
                    j += 1
                    if j >= n:
                        break
                    e = s[j]
                    if e in 'abfnrtv\\"\'':
                        j += 1
                    elif e == '\n':
                        line += 1; j += 1
                    elif e == '\r':
                        j += 1
                        if j < n and s[j] == '\n':
                            j += 1
                        line += 1
                    elif e == 'x':
                        if not re.compile(r'[0-9a-fA-F]{2}').match(s, j + 1):
                            raise LuaSyntaxError(line, "sequence d'echappement invalide", '\\x')
                        j += 3
                    elif e == 'z':
                        j += 1
                        while j < n and s[j] in ' \t\r\n\f\v':
                            if s[j] == '\n':
                                line += 1
                            j += 1
                    elif e.isdigit():
                        m = re.compile(r'\d{1,3}').match(s, j)
                        if int(m.group()) > 255:
                            raise LuaSyntaxError(line, "sequence d'echappement decimale trop grande", '\\' + m.group())
                        j = m.end()
                    elif e == 'u':
                        m = re.compile(r'u\{[0-9a-fA-F]+\}').match(s, j)
                        if not m:
                            raise LuaSyntaxError(line, "sequence d'echappement invalide", '\\u')
                        j = m.end()
                    else:
                        raise LuaSyntaxError(line, "sequence d'echappement invalide", '\\' + e)
                else:
                    j += 1
            if not ok:
                raise LuaSyntaxError(line, 'chaine non terminee', s[i:i + 20].split('\n')[0])
            toks.append(Tok('str', s[i:j + 1], line))
            i = j + 1; continue
        if c == '[':
            lvl = long_bracket_level(s, i)
            if lvl >= 0:
                body, i2, line2 = read_long(s, i, lvl, line, 'chaine')
                toks.append(Tok('str', '[[...]]', line))
                i, line = i2, line2
                continue
            if i + 1 < n and s[i + 1] == '=':
                raise LuaSyntaxError(line, 'delimiteur de chaine longue invalide', '[=')
        if s.startswith('...', i):
            toks.append(Tok('op', '...', line)); i += 3; continue
        if s[i:i + 2] in OPS2:
            toks.append(Tok('op', s[i:i + 2], line)); i += 2; continue
        if c in OPS1:
            toks.append(Tok('op', c, line)); i += 1; continue
        raise LuaSyntaxError(line, 'caractere inattendu', c)
    toks.append(Tok('eof', '<eof>', line))
    return toks


# ------------------------------------------------------------------ analyseur
class Parser:
    def __init__(self, toks):
        self.toks, self.p = toks, 0
        self.loop = 0

    # --- utilitaires
    @property
    def cur(self):
        return self.toks[self.p]

    def peek(self, k=1):
        return self.toks[min(self.p + k, len(self.toks) - 1)]

    def is_(self, v, kind=None):
        t = self.cur
        return t.v == v and t.t in (('kw', 'op') if kind is None else (kind,))

    def error(self, msg, tok=None):
        t = tok or self.cur
        raise LuaSyntaxError(t.line, msg, t.text())

    def accept(self, v):
        if self.is_(v):
            self.p += 1
            return True
        return False

    def expect(self, v, opener=None, line=None):
        if self.is_(v):
            self.p += 1
            return
        if opener and line and line != self.cur.line:
            self.error("'%s' attendu (pour fermer '%s' de la ligne %d)" % (v, opener, line))
        self.error("'%s' attendu" % v)

    def name(self):
        if self.cur.t != 'name':
            self.error('nom attendu')
        v = self.cur.v
        self.p += 1
        return v

    # --- blocs et instructions
    def chunk(self):
        self.block()
        if self.cur.t != 'eof':
            self.error("'<fin du fichier>' attendu")

    def block(self):
        while True:
            t = self.cur
            if t.t == 'eof' or (t.t == 'kw' and t.v in BLOCK_FOLLOW):
                return
            if t.t == 'kw' and t.v == 'return':
                self.p += 1
                if not (self.cur.t == 'eof' or (self.cur.t == 'kw' and self.cur.v in BLOCK_FOLLOW) or self.is_(';')):
                    self.explist()
                self.accept(';')
                c = self.cur
                if not (c.t == 'eof' or (c.t == 'kw' and c.v in BLOCK_FOLLOW)):
                    self.error("'return' doit etre la derniere instruction du bloc ; fin de bloc attendue")
                return
            self.statement()

    def statement(self):
        t = self.cur
        if t.t == 'op' and t.v == ';':
            self.p += 1
        elif t.t == 'op' and t.v == '::':
            self.p += 1
            self.name()
            self.expect('::')
        elif t.t == 'kw':
            v = t.v
            if v == 'if':
                self.if_stat()
            elif v == 'while':
                self.p += 1
                self.expr()
                self.expect('do')
                self.loop += 1
                self.block()
                self.loop -= 1
                self.expect('end', 'while', t.line)
            elif v == 'do':
                self.p += 1
                self.block()
                self.expect('end', 'do', t.line)
            elif v == 'for':
                self.for_stat()
            elif v == 'repeat':
                self.p += 1
                self.loop += 1
                self.block()
                self.loop -= 1
                self.expect('until', 'repeat', t.line)
                self.expr()
            elif v == 'function':
                self.p += 1
                self.name()
                while self.accept('.'):
                    self.name()
                if self.accept(':'):
                    self.name()
                self.body(t.line)
            elif v == 'local':
                self.p += 1
                if self.accept('function'):
                    self.name()
                    self.body(t.line)
                else:
                    self.name()
                    if self.is_('<'):
                        self.error("les attributs <const> / <close> n'existent pas en Lua 5.3")
                    while self.accept(','):
                        self.name()
                        if self.is_('<'):
                            self.error("les attributs <const> / <close> n'existent pas en Lua 5.3")
                    if self.accept('='):
                        self.explist()
            elif v == 'break':
                if self.loop == 0:
                    self.error("'break' hors d'une boucle")
                self.p += 1
            elif v == 'goto':
                self.p += 1
                self.name()
            else:
                self.exprstat()
        else:
            self.exprstat()

    def if_stat(self):
        line = self.cur.line
        self.p += 1
        self.expr()
        self.expect('then')
        self.block()
        while self.is_('elseif'):
            self.p += 1
            self.expr()
            self.expect('then')
            self.block()
        if self.accept('else'):
            self.block()
        self.expect('end', 'if', line)

    def for_stat(self):
        line = self.cur.line
        self.p += 1
        self.name()
        if self.is_('=') :
            self.p += 1
            self.expr()
            self.expect(',')
            self.expr()
            if self.accept(','):
                self.expr()
        elif self.is_(',') or self.is_('in'):
            while self.accept(','):
                self.name()
            self.expect('in')
            self.explist()
        else:
            self.error("'=' ou 'in' attendu")
        self.expect('do')
        self.loop += 1
        self.block()
        self.loop -= 1
        self.expect('end', 'for', line)

    def exprstat(self):
        kind = self.suffixedexp()
        if self.is_('=') or self.is_(','):
            if kind not in ('var', 'index'):
                self.error('erreur de syntaxe (la cible de l\'affectation n\'est pas assignable)')
            while self.accept(','):
                k = self.suffixedexp()
                if k not in ('var', 'index'):
                    self.error('erreur de syntaxe (la cible de l\'affectation n\'est pas assignable)')
            self.expect('=')
            self.explist()
        elif kind != 'call':
            self.error('erreur de syntaxe')

    def body(self, line):
        self.expect('(')
        if not self.is_(')'):
            while True:
                if self.accept('...'):
                    break
                self.name()
                if not self.accept(','):
                    break
        self.expect(')')
        saved, self.loop = self.loop, 0
        self.block()
        self.loop = saved
        self.expect('end', 'function', line)

    # --- expressions
    def explist(self):
        self.expr()
        while self.accept(','):
            self.expr()

    def expr(self):
        self.subexpr(0)

    def subexpr(self, limit):
        t = self.cur
        if (t.t == 'kw' and t.v == 'not') or (t.t == 'op' and t.v in ('-', '#', '~')):
            self.p += 1
            self.subexpr(UNARY_PRIORITY)
        else:
            self.simpleexp()
        while True:
            t = self.cur
            op = t.v if t.t in ('op', 'kw') and t.v in BINARY else None
            if op is None:
                return
            left, right = BINARY[op]
            if left <= limit:
                return
            self.p += 1
            self.subexpr(right)

    def simpleexp(self):
        t = self.cur
        if t.t in ('num', 'str'):
            self.p += 1
        elif t.t == 'kw' and t.v in ('nil', 'true', 'false'):
            self.p += 1
        elif t.t == 'op' and t.v == '...':
            self.p += 1
        elif t.t == 'op' and t.v == '{':
            self.constructor()
        elif t.t == 'kw' and t.v == 'function':
            self.p += 1
            self.body(t.line)
        else:
            self.suffixedexp()

    def primaryexp(self):
        t = self.cur
        if t.t == 'name':
            self.p += 1
            return 'var'
        if t.t == 'op' and t.v == '(':
            self.p += 1
            self.expr()
            self.expect(')', '(', t.line)
            return 'paren'
        self.error('expression inattendue')

    def suffixedexp(self):
        kind = self.primaryexp()
        while True:
            t = self.cur
            if t.t == 'op' and t.v == '.':
                self.p += 1
                self.name()
                kind = 'index'
            elif t.t == 'op' and t.v == '[':
                self.p += 1
                self.expr()
                self.expect(']')
                kind = 'index'
            elif t.t == 'op' and t.v == ':':
                self.p += 1
                self.name()
                self.funcargs()
                kind = 'call'
            elif (t.t == 'op' and t.v in ('(', '{')) or t.t == 'str':
                self.funcargs()
                kind = 'call'
            else:
                return kind

    def funcargs(self):
        t = self.cur
        if t.t == 'str':
            self.p += 1
        elif t.t == 'op' and t.v == '{':
            self.constructor()
        elif t.t == 'op' and t.v == '(':
            self.p += 1
            if not self.is_(')'):
                self.explist()
            self.expect(')', '(', t.line)
        else:
            self.error('arguments de fonction attendus')

    def constructor(self):
        line = self.cur.line
        self.expect('{')
        while not self.is_('}'):
            t = self.cur
            if t.t == 'op' and t.v == '[':
                self.p += 1
                self.expr()
                self.expect(']')
                self.expect('=')
                self.expr()
            elif t.t == 'name' and self.peek().t == 'op' and self.peek().v == '=':
                self.p += 2
                self.expr()
            else:
                self.expr()
            if not (self.accept(',') or self.accept(';')):
                break
        self.expect('}', '{', line)


def verifier_texte(texte):
    """Renvoie None si la syntaxe est bonne, sinon une chaine « ligne: message pres de 'x' » (premiere erreur)."""
    try:
        Parser(lex(texte)).chunk()
    except LuaSyntaxError as e:
        return str(e)
    except RecursionError:
        return '0: expression trop imbriquee'
    return None


def verifier_fichier(chemin):
    with open(chemin, 'rb') as f:
        octets = f.read()
    texte = octets.decode('utf-8', errors='replace')
    return verifier_texte(texte)


def lister(cible):
    if os.path.isdir(cible):
        for rep, _, fichiers in os.walk(cible):
            for f in sorted(fichiers):
                if f.lower().endswith('.lua'):
                    yield os.path.join(rep, f)
    else:
        yield cible


def main(argv):
    silencieux = '-q' in argv
    cibles = [a for a in argv if not a.startswith('-')]
    if not cibles:
        print(__doc__)
        return 2
    sys.setrecursionlimit(20000)
    total = erreurs = 0
    for c in cibles:
        for chemin in lister(c):
            total += 1
            res = verifier_fichier(chemin)
            if res:
                erreurs += 1
                print('ERREUR %s:%s' % (chemin, res))
            elif not silencieux:
                print('OK     %s' % chemin)
    print('%d fichier(s) verifie(s), %d erreur(s)' % (total, erreurs))
    return 1 if erreurs else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))

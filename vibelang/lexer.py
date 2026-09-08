"""VIBE lexer. No natural-language keywords exist in this language;
every construct is a sigil. Identifiers are user-chosen and may be any script."""


class LexError(Exception):
    pass


class Tok:
    __slots__ = ("kind", "val", "line", "col")

    def __init__(self, kind, val, line, col):
        self.kind = kind
        self.val = val
        self.line = line
        self.col = col

    def __repr__(self):
        return "Tok(%s,%r,%d:%d)" % (self.kind, self.val, self.line, self.col)

    def is_p(self, *vals):
        return self.kind == "P" and self.val in vals


# Longest-match-first punctuation table. Order matters.
PUNCT = [
    "$$", "$~", "$",
    "@!", "@",
    "%|", "%",
    "??",
    "*<", "*>", "*",
    "<<", ">>", "<=", ">=", "<", ">",
    "==", "!=", "!",
    "&&", "||", "&", "|",
    "\\\\", "\\",
    "?", ":", "^", "~", "#", "'",
    "+", "-", "/",
    "(", ")", "{", "}", "[", "]",
    ",", ".", "=",
]

IDENT_START = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_")
IDENT_CONT = IDENT_START | set("0123456789")
DIGITS = set("0123456789")

ESCAPES = {
    "n": 10, "t": 9, "r": 13, "0": 0, "\\": 92, "'": 39, '"': 34, "e": 27,
    "`": 96,
}


def _ident_start(ch):
    return ch in IDENT_START or ord(ch) > 127


def _ident_cont(ch):
    return ch in IDENT_CONT or ord(ch) > 127


class Lexer:
    def __init__(self, src, filename="<vibe>"):
        self.src = src
        self.file = filename
        self.i = 0
        self.n = len(src)
        self.line = 1
        self.col = 1
        self.toks = []

    def err(self, msg):
        raise LexError("%s:%d:%d: %s" % (self.file, self.line, self.col, msg))

    def _adv(self, k=1):
        for _ in range(k):
            if self.i < self.n and self.src[self.i] == "\n":
                self.line += 1
                self.col = 1
            else:
                self.col += 1
            self.i += 1

    def push(self, kind, val, line, col):
        self.toks.append(Tok(kind, val, line, col))

    def run(self):
        src = self.src
        while self.i < self.n:
            ch = src[self.i]

            if ch in " \t\r":
                self._adv()
                continue

            if ch == ";":  # comment to end of line
                while self.i < self.n and src[self.i] != "\n":
                    self._adv()
                continue

            if ch == "\n":
                line, col = self.line, self.col
                self._adv()
                # collapse runs of newlines into a single NL token
                if self.toks and self.toks[-1].kind != "NL":
                    self.push("NL", "\n", line, col)
                continue

            line, col = self.line, self.col

            if ch in DIGITS:
                self.lex_number(line, col)
                continue

            if _ident_start(ch):
                j = self.i
                while j < self.n and _ident_cont(src[j]):
                    j += 1
                name = src[self.i:j]
                self._adv(j - self.i)
                self.push("ID", name, line, col)
                continue

            if ch == '"':
                self.lex_string(line, col)
                continue

            if ch == "`":
                self.lex_char(line, col)
                continue

            for p in PUNCT:
                if src.startswith(p, self.i):
                    self._adv(len(p))
                    self.push("P", p, line, col)
                    break
            else:
                self.err("unexpected character %r" % ch)

        if self.toks and self.toks[-1].kind != "NL":
            self.push("NL", "\n", self.line, self.col)
        self.push("EOF", None, self.line, self.col)
        return self.toks

    def lex_number(self, line, col):
        src = self.src
        j = self.i
        if src.startswith("0x", j) or src.startswith("0X", j):
            k = j + 2
            while k < self.n and (src[k] in "0123456789abcdefABCDEF_"):
                k += 1
            v = int(src[j + 2:k].replace("_", ""), 16)
            self._adv(k - j)
            self.push("INT", v, line, col)
            return
        if src.startswith("0b", j) or src.startswith("0B", j):
            k = j + 2
            while k < self.n and src[k] in "01_":
                k += 1
            v = int(src[j + 2:k].replace("_", ""), 2)
            self._adv(k - j)
            self.push("INT", v, line, col)
            return
        if src.startswith("0o", j) or src.startswith("0O", j):
            k = j + 2
            while k < self.n and src[k] in "01234567_":
                k += 1
            v = int(src[j + 2:k].replace("_", ""), 8)
            self._adv(k - j)
            self.push("INT", v, line, col)
            return
        k = j
        while k < self.n and (src[k] in DIGITS or src[k] == "_"):
            k += 1
        isf = False
        if k < self.n and src[k] == "." and k + 1 < self.n and src[k + 1] in DIGITS:
            isf = True
            k += 1
            while k < self.n and (src[k] in DIGITS or src[k] == "_"):
                k += 1
        if k < self.n and src[k] in "eE":
            m = k + 1
            if m < self.n and src[m] in "+-":
                m += 1
            if m < self.n and src[m] in DIGITS:
                isf = True
                k = m
                while k < self.n and src[k] in DIGITS:
                    k += 1
        text = src[j:k].replace("_", "")
        self._adv(k - j)
        if isf:
            self.push("FLT", float(text), line, col)
        else:
            self.push("INT", int(text), line, col)

    def _escape(self):
        """Consume one (possibly escaped) character, return its bytes."""
        src = self.src
        ch = src[self.i]
        if ch != "\\":
            self._adv()
            return ch.encode("utf-8")
        self._adv()
        if self.i >= self.n:
            self.err("unterminated escape")
        e = src[self.i]
        if e == "x":
            self._adv()
            h = src[self.i:self.i + 2]
            if len(h) < 2:
                self.err("bad \\x escape")
            self._adv(2)
            return bytes([int(h, 16)])
        if e in ESCAPES:
            self._adv()
            return bytes([ESCAPES[e]])
        self.err("unknown escape \\%s" % e)

    def lex_string(self, line, col):
        self._adv()  # opening quote
        out = bytearray()
        while True:
            if self.i >= self.n:
                self.err("unterminated string")
            if self.src[self.i] == '"':
                self._adv()
                break
            if self.src[self.i] == "\n":
                self.err("newline in string")
            out += self._escape()
        self.push("STR", bytes(out), line, col)

    def lex_char(self, line, col):
        # `a  -> byte literal. Backtick prefix, single byte, no closing mark.
        self._adv()
        if self.i >= self.n:
            self.err("unterminated byte literal")
        b = self._escape()
        if len(b) != 1:
            self.err("byte literal must be a single byte")
        self.push("INT", b[0], line, col)


def lex(src, filename="<vibe>"):
    return Lexer(src, filename).run()

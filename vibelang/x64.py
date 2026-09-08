"""Direct x86-64 machine code encoder.

Emits instruction bytes into a buffer. No external assembler is involved:
every byte of a VIBE binary is produced here.
"""

import struct

# general purpose registers
RAX, RCX, RDX, RBX, RSP, RBP, RSI, RDI = range(8)
R8, R9, R10, R11, R12, R13, R14, R15 = range(8, 16)

GP_NAMES = ["rax", "rcx", "rdx", "rbx", "rsp", "rbp", "rsi", "rdi",
            "r8", "r9", "r10", "r11", "r12", "r13", "r14", "r15"]

# condition codes
CC = {"o": 0x0, "no": 0x1, "b": 0x2, "ae": 0x3, "e": 0x4, "ne": 0x5,
      "be": 0x6, "a": 0x7, "s": 0x8, "ns": 0x9, "p": 0xA, "np": 0xB,
      "l": 0xC, "ge": 0xD, "le": 0xE, "g": 0xF}

SIGNED_CC = {"==": "e", "!=": "ne", "<": "l", "<=": "le", ">": "g", ">=": "ge"}
UNSIGNED_CC = {"==": "e", "!=": "ne", "<": "b", "<=": "be", ">": "a", ">=": "ae"}

INVERT_CC = {"e": "ne", "ne": "e", "l": "ge", "ge": "l", "le": "g",
             "g": "le", "b": "ae", "ae": "b", "be": "a", "a": "be"}

# /digit groups for the 81 /r immediate-arithmetic form
ALU_DIGIT = {"+": 0, "|": 1, "&": 4, "-": 5, "^": 6, "cmp": 7}
# opcodes for the reg,reg form  (r/m64, r64)
ALU_MR = {"+": 0x01, "|": 0x09, "&": 0x21, "-": 0x29, "^": 0x31, "cmp": 0x39}


class Mem:
    """[base + index*scale + disp]  or  [rip + label]"""
    __slots__ = ("base", "disp", "index", "scale", "rip_label")

    def __init__(self, base=None, disp=0, index=None, scale=1, rip_label=None):
        self.base = base
        self.disp = disp
        self.index = index
        self.scale = scale
        self.rip_label = rip_label


def rip(label):
    return Mem(rip_label=label)


class Asm:
    def __init__(self):
        self.buf = bytearray()
        self.labels = {}
        self.fixups = []       # (offset, size, kind, target, addend)

    # -- raw -----------------------------------------------------------------
    def b(self, *bs):
        self.buf.extend(bs)

    def raw(self, data):
        self.buf.extend(data)

    @property
    def pos(self):
        return len(self.buf)

    def label(self, name):
        self.labels[name] = len(self.buf)

    def _fix(self, kind, target, addend=0):
        self.fixups.append([len(self.buf), 4, kind, target, addend])
        self.buf.extend(b"\0\0\0\0")

    # -- encoding primitives -------------------------------------------------
    def _rex(self, w, reg, rm_base, index=0, force=False):
        r = 1 if (reg is not None and reg >= 8) else 0
        x = 1 if (index is not None and index >= 8) else 0
        bb = 1 if (rm_base is not None and rm_base >= 8) else 0
        val = 0x40 | (w << 3) | (r << 2) | (x << 1) | bb
        if val != 0x40 or force:
            self.b(val)

    def _modrm_rr(self, reg, rm):
        self.b(0xC0 | ((reg & 7) << 3) | (rm & 7))

    def _modrm_m(self, reg, m):
        if m.rip_label is not None:
            self.b(0x00 | ((reg & 7) << 3) | 5)
            # rip-relative displacement is patched once layout is known
            self._fix("rip", m.rip_label)
            return
        base = m.base
        disp = m.disp
        idx = m.index
        if idx is not None:
            scale_bits = {1: 0, 2: 1, 4: 2, 8: 3}[m.scale]
            if disp == 0 and (base & 7) != 5:
                mod = 0
            elif -128 <= disp <= 127:
                mod = 1
            else:
                mod = 2
            self.b((mod << 6) | ((reg & 7) << 3) | 4)
            self.b((scale_bits << 6) | ((idx & 7) << 3) | (base & 7))
        else:
            if disp == 0 and (base & 7) != 5:
                mod = 0
            elif -128 <= disp <= 127:
                mod = 1
            else:
                mod = 2
            self.b((mod << 6) | ((reg & 7) << 3) | (base & 7))
            if (base & 7) == 4:  # rsp / r12 need a SIB byte
                self.b(0x24)
        if idx is not None or True:
            if disp == 0 and (base & 7) != 5:
                pass
            elif -128 <= disp <= 127:
                self.b(disp & 0xFF)
            else:
                self.buf.extend(struct.pack("<i", disp))

    def _op_rm(self, opcode, w, reg, rm, prefix=(), force_rex=False, esc=False):
        """Encode `opcode reg, rm` where rm is a register number or Mem."""
        for p in prefix:
            self.b(p)
        if isinstance(rm, Mem):
            self._rex(w, reg, rm.base if rm.rip_label is None else 0,
                      rm.index, force_rex)
            if esc:
                self.b(0x0F)
            if isinstance(opcode, tuple):
                self.b(*opcode)
            else:
                self.b(opcode)
            self._modrm_m(reg, rm)
        else:
            self._rex(w, reg, rm, 0, force_rex)
            if esc:
                self.b(0x0F)
            if isinstance(opcode, tuple):
                self.b(*opcode)
            else:
                self.b(opcode)
            self._modrm_rr(reg, rm)

    # -- moves ---------------------------------------------------------------
    def mov_rr(self, dst, src, w=1):
        if dst == src and w == 1:
            return
        self._op_rm(0x8B, w, dst, src)

    def mov_rm(self, dst, mem, w=1):
        """dst <- [mem] (64-bit unless w=0 -> 32-bit, zero-extending)"""
        self._op_rm(0x8B, w, dst, mem)

    def mov_mr(self, mem, src, w=1):
        self._op_rm(0x89, w, src, mem)

    def mov_ri(self, dst, imm):
        imm &= 0xFFFFFFFFFFFFFFFF
        if imm == 0:
            self._op_rm(0x31, 1, dst, dst)   # xor dst, dst
            return
        if imm <= 0x7FFFFFFF:
            # mov r32, imm32 (zero-extends to 64)
            self._rex(0, 0, dst)
            self.b(0xB8 + (dst & 7))
            self.buf.extend(struct.pack("<I", imm))
            return
        s = struct.unpack("<q", struct.pack("<Q", imm))[0]
        if -0x80000000 <= s <= 0x7FFFFFFF:
            self._rex(1, 0, dst)
            self.b(0xC7)
            self._modrm_rr(0, dst)
            self.buf.extend(struct.pack("<i", s))
            return
        self._rex(1, 0, dst)
        self.b(0xB8 + (dst & 7))
        self.buf.extend(struct.pack("<Q", imm))

    def mov_mi32(self, mem, imm):
        """store a 32-bit sign-extended immediate to a 64-bit location"""
        self._op_rm(0xC7, 1, 0, mem)
        self.buf.extend(struct.pack("<i", imm))

    def movzx(self, dst, rm, size):
        if size == 1:
            self._op_rm(0xB6, 1, dst, rm, esc=True, force_rex=False)
        elif size == 2:
            self._op_rm(0xB7, 1, dst, rm, esc=True)
        elif size == 4:
            self._op_rm(0x8B, 0, dst, rm)   # 32-bit mov zero-extends
        else:
            self._op_rm(0x8B, 1, dst, rm)

    def movsx(self, dst, rm, size):
        if size == 1:
            self._op_rm(0xBE, 1, dst, rm, esc=True)
        elif size == 2:
            self._op_rm(0xBF, 1, dst, rm, esc=True)
        elif size == 4:
            self._op_rm(0x63, 1, dst, rm)   # movsxd
        else:
            self._op_rm(0x8B, 1, dst, rm)

    def store_sized(self, mem, src, size):
        if size == 1:
            self._op_rm(0x88, 0, src, mem, force_rex=(src >= 4))
        elif size == 2:
            self._op_rm(0x89, 0, src, mem, prefix=(0x66,))
        elif size == 4:
            self._op_rm(0x89, 0, src, mem)
        else:
            self._op_rm(0x89, 1, src, mem)

    def lea(self, dst, mem):
        self._op_rm(0x8D, 1, dst, mem)

    # -- arithmetic ----------------------------------------------------------
    def alu_rr(self, op, dst, src):
        self._op_rm(ALU_MR[op], 1, src, dst)

    def alu_rm(self, op, dst, mem):
        self._op_rm(ALU_MR[op] + 2, 1, dst, mem)

    def alu_ri(self, op, dst, imm):
        d = ALU_DIGIT[op]
        if -128 <= imm <= 127:
            self._rex(1, 0, dst)
            self.b(0x83)
            self._modrm_rr(d, dst)
            self.b(imm & 0xFF)
        else:
            self._rex(1, 0, dst)
            self.b(0x81)
            self._modrm_rr(d, dst)
            self.buf.extend(struct.pack("<i", imm))

    def imul_rr(self, dst, src):
        self._op_rm(0xAF, 1, dst, src, esc=True)

    def imul_ri(self, dst, src, imm):
        self._rex(1, dst, src)
        self.b(0x69)
        self._modrm_rr(dst, src)
        self.buf.extend(struct.pack("<i", imm))

    def neg(self, r):
        self._rex(1, 0, r)
        self.b(0xF7)
        self._modrm_rr(3, r)

    def not_(self, r):
        self._rex(1, 0, r)
        self.b(0xF7)
        self._modrm_rr(2, r)

    def cqo(self):
        self.b(0x48, 0x99)

    def idiv(self, r):
        self._rex(1, 0, r)
        self.b(0xF7)
        self._modrm_rr(7, r)

    def div(self, r):
        self._rex(1, 0, r)
        self.b(0xF7)
        self._modrm_rr(6, r)

    def shift_cl(self, kind, r):
        d = {"<<": 4, ">>u": 5, ">>": 7}[kind]
        self._rex(1, 0, r)
        self.b(0xD3)
        self._modrm_rr(d, r)

    def shift_imm(self, kind, r, imm):
        d = {"<<": 4, ">>u": 5, ">>": 7}[kind]
        self._rex(1, 0, r)
        self.b(0xC1)
        self._modrm_rr(d, r)
        self.b(imm & 0x3F)

    def test_rr(self, a, b):
        self._op_rm(0x85, 1, b, a)

    def cmp_ri(self, r, imm):
        self.alu_ri("cmp", r, imm)

    def setcc(self, cc, r):
        self._rex(0, 0, r, force=(r >= 4))
        self.b(0x0F, 0x90 + CC[cc])
        self._modrm_rr(0, r)

    # -- control flow --------------------------------------------------------
    def jmp(self, target):
        self.b(0xE9)
        self._fix("rel", target)

    def jcc(self, cc, target):
        self.b(0x0F, 0x80 + CC[cc])
        self._fix("rel", target)

    def call(self, target):
        self.b(0xE8)
        self._fix("rel", target)

    def call_r(self, r):
        self._rex(0, 0, r)
        self.b(0xFF)
        self._modrm_rr(2, r)

    def ret(self):
        self.b(0xC3)

    def push(self, r):
        self._rex(0, 0, r)
        self.b(0x50 + (r & 7))

    def pop(self, r):
        self._rex(0, 0, r)
        self.b(0x58 + (r & 7))

    def syscall(self):
        self.b(0x0F, 0x05)

    def ud2(self):
        self.b(0x0F, 0x0B)

    def rep_movsb(self):
        self.b(0xF3, 0xA4)

    def rep_stosb(self):
        self.b(0xF3, 0xAA)

    def cld(self):
        self.b(0xFC)

    # -- SSE -----------------------------------------------------------------
    def _sse(self, pfx, opcode, reg, rm, w=0):
        if pfx:
            self.b(pfx)
        if isinstance(rm, Mem):
            base = rm.base if rm.rip_label is None else None
            idx = rm.index
        else:
            base, idx = rm, None
        self._rex(w, reg, base, idx)
        self.b(0x0F, opcode)
        if isinstance(rm, Mem):
            self._modrm_m(reg, rm)
        else:
            self._modrm_rr(reg, rm)

    def movsd_load(self, xmm, rm, bits=64):
        self._sse(0xF2 if bits == 64 else 0xF3, 0x10, xmm, rm)

    def movsd_store(self, rm, xmm, bits=64):
        self._sse(0xF2 if bits == 64 else 0xF3, 0x11, xmm, rm)

    def fbin(self, op, xmm, rm, bits=64):
        opc = {"+": 0x58, "-": 0x5C, "*": 0x59, "/": 0x5E}[op]
        self._sse(0xF2 if bits == 64 else 0xF3, opc, xmm, rm)

    def ucomis(self, xmm, rm, bits=64):
        if bits == 64:
            self._sse(0x66, 0x2E, xmm, rm)
        else:
            self._sse(None, 0x2E, xmm, rm)

    def xorps(self, xmm, rm):
        self._sse(None, 0x57, xmm, rm)

    def cvtsi2sd(self, xmm, r, bits=64):
        self._sse(0xF2 if bits == 64 else 0xF3, 0x2A, xmm, r, w=1)

    def cvttsd2si(self, r, xmm, bits=64):
        self._sse(0xF2 if bits == 64 else 0xF3, 0x2C, r, xmm, w=1)

    def cvtsd2ss(self, dst, src):
        self._sse(0xF2, 0x5A, dst, src)

    def cvtss2sd(self, dst, src):
        self._sse(0xF3, 0x5A, dst, src)

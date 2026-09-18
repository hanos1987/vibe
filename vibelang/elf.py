"""Minimal static ELF64 executable writer.

Produces a freestanding x86-64 Linux binary: no interpreter, no dynamic
sections, no libc. Two PT_LOAD segments (r-x text+rodata, rw- data).
"""

import struct

BASE = 0x400000
PAGE = 0x1000

ET_EXEC = 2
EM_X86_64 = 0x3E
PT_LOAD = 1
PF_X, PF_W, PF_R = 1, 2, 4


def align_up(x, a):
    return (x + a - 1) & ~(a - 1)


def build_elf(code, rodata, data, entry_off, symbols=()):
    """code/rodata/data are bytes; entry_off is an offset into `code`.

    Returns (elf_bytes, text_vaddr, rodata_vaddr, data_vaddr).
    The caller must already have resolved every relocation using the
    addresses produced by `plan_layout` below.
    """
    ehsize = 64
    phentsize = 56
    phnum = 2
    hdr_size = ehsize + phentsize * phnum

    code_off = align_up(hdr_size, 16)
    ro_off = align_up(code_off + len(code), 16)
    text_end = ro_off + len(rodata)

    data_off = align_up(text_end, PAGE)
    text_vaddr = BASE
    data_vaddr = BASE + 0x200000 + data_off

    entry = BASE + code_off + entry_off

    out = bytearray()
    # -- ELF header
    out += b"\x7fELF" + bytes([2, 1, 1, 0]) + b"\0" * 8
    out += struct.pack("<HHI", ET_EXEC, EM_X86_64, 1)
    out += struct.pack("<QQQ", entry, ehsize, 0)      # entry, phoff, shoff
    out += struct.pack("<I", 0)                        # flags
    out += struct.pack("<HHHHHH", ehsize, phentsize, phnum, 64, 0, 0)

    # -- program headers
    out += struct.pack("<IIQQQQQQ", PT_LOAD, PF_R | PF_X, 0, text_vaddr,
                       text_vaddr, text_end, text_end, PAGE)
    out += struct.pack("<IIQQQQQQ", PT_LOAD, PF_R | PF_W, data_off, data_vaddr,
                       data_vaddr, len(data), len(data), PAGE)

    assert len(out) == hdr_size
    out += b"\0" * (code_off - len(out))
    out += code
    out += b"\0" * (ro_off - len(out))
    out += rodata
    assert len(out) == text_end
    if data:
        out += b"\0" * (data_off - len(out))
        out += data
    if symbols:
        out += symtab(out, code_off, len(code), ro_off, len(rodata),
                      data_off, len(data), text_vaddr, data_vaddr, symbols)
    return bytes(out)


def symtab(out, code_off, code_len, ro_off, ro_len, data_off, data_len,
           text_vaddr, data_vaddr, symbols):
    """Section headers and a symbol table, appended after the loaded
    bytes. Nothing loads them; they are for gdb, perf and objdump. The
    ELF header's shoff/shnum/shstrndx are patched to point at them.

    symbols: [(name, code_offset, size)] for functions.
    """
    SHT_PROGBITS, SHT_SYMTAB, SHT_STRTAB = 1, 2, 3
    SHF_WRITE, SHF_ALLOC, SHF_EXEC = 1, 2, 4
    strtab = bytearray(b"\0")
    syms = bytearray(b"\0" * 24)               # null symbol
    # section symbols first so gdb attributes addresses to sections
    for (name, off, size) in symbols:
        nidx = len(strtab)
        strtab += name.encode("utf-8") + b"\0"
        # st_name, st_info (GLOBAL FUNC), st_other, st_shndx (.text = 1)
        syms += struct.pack("<IBBHQQ", nidx, (1 << 4) | 2, 0, 1,
                            text_vaddr + code_off + off, size)
    shstr = bytearray(b"\0")
    names = {}
    for n in (".text", ".rodata", ".data", ".symtab", ".strtab", ".shstrtab"):
        names[n] = len(shstr)
        shstr += n.encode() + b"\0"
    body = bytearray()
    sym_off = len(out)
    body += syms
    str_off = sym_off + len(body)
    body += strtab
    shstr_off = sym_off + len(body)
    body += shstr
    while (sym_off + len(body)) % 8:
        body += b"\0"
    sh_off = sym_off + len(body)

    def sh(name, typ, flags, addr, off, size, link=0, info=0, align=1, ent=0):
        return struct.pack("<IIQQQQIIQQ", name, typ, flags, addr, off, size,
                           link, info, align, ent)
    hdrs = sh(0, 0, 0, 0, 0, 0)
    hdrs += sh(names[".text"], SHT_PROGBITS, SHF_ALLOC | SHF_EXEC,
               text_vaddr + code_off, code_off, code_len, align=16)
    hdrs += sh(names[".rodata"], SHT_PROGBITS, SHF_ALLOC,
               text_vaddr + ro_off, ro_off, ro_len, align=8)
    hdrs += sh(names[".data"], SHT_PROGBITS, SHF_ALLOC | SHF_WRITE,
               data_vaddr, data_off, data_len, align=8)
    hdrs += sh(names[".symtab"], SHT_SYMTAB, 0, 0, sym_off, len(syms),
               link=5, info=1, align=8, ent=24)
    hdrs += sh(names[".strtab"], SHT_STRTAB, 0, 0, str_off, len(strtab))
    hdrs += sh(names[".shstrtab"], SHT_STRTAB, 0, 0, shstr_off, len(shstr))
    body += hdrs
    # patch e_shoff, e_shnum, e_shstrndx
    out[40:48] = struct.pack("<Q", sh_off)
    out[60:62] = struct.pack("<H", 7)
    out[62:64] = struct.pack("<H", 6)
    return bytes(body)


def plan_layout(code_len, rodata_len):
    """Addresses the code will be placed at, so relocations can be resolved
    before the final bytes are laid out."""
    hdr_size = 64 + 56 * 2
    code_off = align_up(hdr_size, 16)
    ro_off = align_up(code_off + code_len, 16)
    text_end = ro_off + rodata_len
    data_off = align_up(text_end, PAGE)
    return {
        "code_off": code_off,
        "code_vaddr": BASE + code_off,
        "ro_off": ro_off,
        "ro_vaddr": BASE + ro_off,
        "data_off": data_off,
        "data_vaddr": BASE + 0x200000 + data_off,
    }

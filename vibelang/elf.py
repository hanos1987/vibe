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


def build_elf(code, rodata, data, entry_off):
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
    return bytes(out)


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

---
file: vibelang/stdlib/heap.vibe
file-hash: dc61057c584494d22c872a491be4a72798bd8541
note-hash: 36333a2cccc9b88b
---

# vibelang/stdlib/heap.vibe

## What it is
A VIBE library with a real allocator that can free, plus containers: a growable byte buffer/string builder, a generic growable array, and hash maps keyed by string or integer.

## How to navigate it
- Allocator: `new`, `del`, `cap_of`, `renew`. Size classes from 32 bytes doubling; each block has a 16-byte header; freed blocks go on per-class lists; very large requests get their own mmap.
- `%Buf` with `b*` functions (`bpc`, `bps`, `bpn`, `bpf`, `bpu`, `bpx`, `bstr`...).
- `%Vec<T>` with `vnew`, `vpush`, `vpop`, `vlast`, `vdel`...
- `%Map<V>` (`mnew`, `mset`, `mget`, `mfind`, `mgrow`, `mdel`...) and `%IMap<V>` (`i*`): open addressing, grows at 70% load.

## What it interacts with
Includes std.vibe (`<<"std.vibe"`), using its `mm`, `mu`, `cp`, `set`, `lock`, `unlock`, `ln`, and sys.vibe's `alloc`. Programs include it themselves; front.py reports an error telling you to include it when a feature needs it.

## Why it exists
Most programs need freeable memory and containers.

## Helpful notes
- Thread-safe via the `hlock` spin lock.
- Map keys are not copied: the key's bytes must outlive the entry.
- Deleted map entries are tombstones (`st` = 2); `used` counts them.

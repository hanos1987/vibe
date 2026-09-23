---
file: examples/snake.vibe
file-hash: acc92a367775021d5a01ea52e25f9a4492f7b216
note-hash: 45179968c693094d
---

# examples/snake.vibe

## What it is
An example program: the snake game in the terminal, with no libc; raw mode via ioctl, input via read, timing via nanosleep.

## How to navigate it
Sections are marked by `; ----` comments: output buffer, terminal, random, snake, drawing, main. Globals at the top hold board size, the snake ring buffer `body` and the occupancy grid `occ`.

## What it interacts with
It includes std.vibe (the standard library in vibelang/stdlib/std.vibe, which pulls in sys.vibe) for `cp` and the `%Str` type; README.md points to it as the games/terminal-UI example. No test script runs it; install.sh and packaging/mkdeb.sh copy examples/ into the installed share folder.

## Why it exists
It shows VIBE handling raw terminal mode, non-blocking input and frame timing.

## Helpful notes
Controls: wasd or arrow keys, q to quit. It uses raw syscall numbers (16 ioctl, 35 nanosleep, 228 clock_gettime) and termios byte offsets directly, so it is Linux x86-64 specific.

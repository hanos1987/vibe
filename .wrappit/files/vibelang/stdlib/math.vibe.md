---
file: vibelang/stdlib/math.vibe
file-hash: ad1a53458d299e36252035e41764623280f04091
note-hash: 4e3e1f097b817c29
---

# vibelang/stdlib/math.vibe

## What it is
Floating-point maths in VIBE: constants (`M_PI`, `M_TAU`, `M_E`, `M_LN2`) and `fabs`, `floor`, `ceil`, `fmod`, `fmin`, `fmax`, `sqrt`, `exp`, `lg` (natural log), `log10`, `sin`, `cos`, `tan`, `pow`, `hypot`.

## How to navigate it
One short function each, top to bottom. `exp` uses range reduction plus a Taylor series; `lg` splits mantissa and exponent and uses an atanh series; `sin` reduces to [-pi, pi] and uses a Taylor series; `cos`/`tan`/`pow`/`hypot` build on those.

## What it interacts with
Includes std.vibe (`<<"std.vibe"`) and uses its `abs`. Uses the compiler intrinsics `\sqrt`, `\bits`, `\fbits`. Programs include it explicitly.

## Why it exists
Maths functions without libm.

## Helpful notes
- The comment on `sqrt` says Newton's method, but the code just calls the `\sqrt` intrinsic.
- `floor`, `ceil` and `fmod` convert through s64, so they are wrong for values beyond s64 range.
- `lg` of zero or less returns -1e308; `exp` over 709 returns 1e308 instead of infinity.
- `pow` with a negative base truncates the exponent to an integer.

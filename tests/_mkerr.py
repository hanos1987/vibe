import os

d = os.path.join(os.path.dirname(os.path.abspath(__file__)), "err")
os.makedirs(d, exist_ok=True)

cases = {
    "e01_mixed_ops.vibe": ("no operator precedence", """@! () s64 {
  ^ (1 + 2 * 3)
}
"""),
    "e02_nonexhaustive.vibe": ("not exhaustive", """%| R { |A(s64), |B }
@! () s64 {
  $ r %R = %R|B
  ?? r {
    |A(x) { ^ x }
  }
  ^ 0
}
"""),
    "e03_type_mismatch.vibe": ("expected s64, got b", """@! () s64 {
  $ x s64 = (1 == 1)
  ^ x
}
"""),
    "e04_immutable.vibe": ("immutable", """@! () s64 {
  $ x s64 = 1
  x = 2
  ^ x
}
"""),
    "e05_bad_field.vibe": ("has no field", """%P { a s64 }
@! () s64 {
  $ p %P = %P{ a: 1 }
  ^ p.zz
}
"""),
    "e06_arity.vibe": ("takes 2 argument", """@ f (a s64, b s64) s64 { ^ (a + b) }
@! () s64 {
  ^ f(1)
}
"""),
    "e07_width_mix.vibe": ("never converts silently", """@! () s64 {
  $ a s64 = 1
  $ b s32 = 2
  ^ (a + b)
}
"""),
    "e08_chained_cmp.vibe": ("does not chain", """@! () s64 {
  $ x b = (1 < 2 < 3)
  ^ 0
}
"""),
    "e09_missing_field.vibe": ("missing field", """%P { a s64, b s64 }
@! () s64 {
  $ p %P = %P{ a: 1 }
  ^ p.a
}
"""),
    "e10_no_entry.vibe": ("no entry function", """@ f () s64 { ^ 1 }
"""),
    "e11_unknown_name.vibe": ("unknown name", """@! () s64 {
  ^ nope
}
"""),
    "e12_break_outside.vibe": ("outside a loop", """@! () s64 {
  *<
  ^ 0
}
"""),
}

for name, (err, body) in cases.items():
    with open(os.path.join(d, name), "w") as fh:
        fh.write("; err: %s\n%s" % (err, body))
print("wrote %d error tests" % len(cases))

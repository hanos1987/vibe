"""Differential fuzzer: random programs must behave identically with and
without the optimiser.   python3 tests/fuzz.py 0 1000   (run from a scratch dir)"""
import random, sys, os, subprocess
sys.dont_write_bytecode = True
sys.path.insert(0, os.environ.get("VIBEROOT", os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from vibelang.front import build
from vibelang.codegen import compile_program
from vibelang.cli import stdlib_dir
TYPES = ["s64","u64","s32","u32","s16","u16","s8","u8"]
BITS = {"s64":64,"u64":64,"s32":32,"u32":32,"s16":16,"u16":16,"s8":8,"u8":8}
def lit(t, r):
    b = BITS[t]; hi = (1 << (b - (1 if t[0]=="s" else 0))) - 1
    v=str(r.choice([0,1,2,3,7,hi,hi-1,r.randint(0,hi), r.randint(0,min(hi,300))]))
    return v if t=="s64" else "%s(%s)"%(t,v)
class G:
    def __init__(s, r): s.r=r; s.vars={}; s.n=0; s.lines=[]; s.ind=1; s.depth=0
    def emit(s, l): s.lines.append("  "*s.ind + l)
    def expr(s, t, d=0):
        r=s.r
        cands=[v for v,(vt,_) in s.vars.items() if vt==t]
        k=r.random()
        if d>3 or k<0.25:
            if cands and r.random()<0.7: return r.choice(cands)
            return lit(t,r)
        if k<0.35:
            t2=r.choice(TYPES)
            if t2!=t: return "%s(%s)"%(t,s.expr(t2,d+1))
        if k<0.42: return "(-%s)"%s.expr(t,d+1) if False else "-(%s)"%s.wrap(s.expr(t,d+1))
        if k<0.48: return "~(%s)"%s.wrap(s.expr(t,d+1))
        if k<0.55:
            return "%s(%s)"%(t, "s64(%s)"%s.cond(d+1)) if t!="s64" else "s64(%s)"%s.cond(d+1)
        if k<0.62 and t=="s64":
            return "arr[(%s & 15)]"%s.wrap(s.expr("s64",d+1))
        if getattr(s,"sigs",None) and r.random()<0.25:
            ks=[k for k,st in enumerate(s.sigs) if st==t]
            if ks: return "g%d(%s, %s)"%(r.choice(ks),s.expr(t,d+1),s.expr(t,d+1))
        op=r.choice(["+","-","*","&","|","^","<<",">>","/","%","+","-","*"])
        a=s.expr(t,d+1); b=s.expr(t,d+1)
        if op in("/","%"): b="((%s & 7) + 1)"%s.wrap(b)
        if op in("<<",">>"): b="(%s & %d)"%(s.wrap(b), min(BITS[t]-1, 31))
        return "(%s %s %s)"%(s.wrap(a),op,s.wrap(b))
    def wrap(s,e): return e
    def cond(s,d=0):
        r=s.r; t=r.choice(TYPES)
        c="(%s %s %s)"%(s.expr(t,d+1), r.choice(["==","!=","<","<=",">",">="]), s.expr(t,d+1))
        k=r.random()
        if d<2 and k<0.2: return "(%s && %s)"%(c,s.cond(d+1))
        if d<2 and k<0.4: return "(%s || %s)"%(c,s.cond(d+1))
        if k<0.5: return "!%s"%c
        return c
    def newvar(s):
        t=s.r.choice(TYPES); n="v%d"%s.n; s.n+=1
        s.emit("$~ %s %s = %s"%(n,t,s.expr(t))); s.vars[n]=(t,True)
    def stmt(s):
        r=s.r; k=r.random()
        muts=[v for v,(t,m) in s.vars.items() if m]
        if k<0.25 or not muts: s.newvar(); return
        if k<0.55:
            v=r.choice(muts); s.emit("%s = %s"%(v,s.expr(s.vars[v][0]))); return
        if k<0.65:
            s.emit("arr[(%s & 15)] = %s"%(s.expr("s64"),s.expr("s64"))); return
        if k<0.72:
            v=r.choice(list(s.vars)); s.emit("h = ((h * 31) + s64(%s))"%v if s.vars[v][0]!="s64" else "h = ((h * 31) + %s)"%v); return
        if s.depth>=3: s.newvar(); return
        saved=dict(s.vars)
        if k<0.87:
            s.emit("? %s {"%s.cond()); s.ind+=1; s.depth+=1
            for _ in range(r.randint(1,4)): s.stmt()
            s.ind-=1; s.vars=dict(saved)
            if r.random()<0.5:
                s.emit("} : {"); s.ind+=1
                for _ in range(r.randint(1,3)): s.stmt()
                s.ind-=1; s.vars=dict(saved)
            s.emit("}"); s.depth-=1
        else:
            c="c%d"%s.n; s.n+=1
            s.emit("$~ %s s64 = 0"%c)
            s.emit("* (%s < %d) {"%(c,r.randint(1,6))); s.ind+=1; s.depth+=1
            s.emit("%s = (%s + 1)"%(c,c))
            s.vars[c]=("s64",False)
            for _ in range(r.randint(1,5)):
                s.stmt()
                if r.random()<0.1: s.emit("? %s {"%s.cond()); s.emit("  "+r.choice(["*<","*>"])); s.emit("}")
            s.ind-=1; s.vars=dict(saved); s.vars[c]=("s64",False)
            s.emit("}"); s.depth-=1
def helpers(r):
    out=[]; sigs=[]
    for k in range(4):
        t=r.choice(TYPES); g=G(r); g.vars={"a":(t,True),"b":(t,True)}
        g.noarr=True
        for _ in range(r.randint(0,3)): g.stmt()
        body="\n".join(g.lines)
        out.append("@ g%d (a %s, b %s) %s {\n  $~ h s64 = 1\n%s\n  ^ %s\n}"%(k,t,t,t,body,g.expr(t)))
        sigs.append(t)
    return "\n".join(out), sigs
def gen(seed):
    r=random.Random(seed); hs,sigs=helpers(r); g=G(r); g.sigs=sigs
    g.vars={"p0":("s64",True),"p1":("u32",True),"p2":("s16",True),"p3":("u8",True)}
    for _ in range(r.randint(5,25)): g.stmt()
    for v,(t,_) in list(g.vars.items()):
        g.emit("h = ((h * 31) + %s)"%(v if t=="s64" else "s64(%s)"%v))
    body="\n".join(g.lines)
    return '''<<"std.vibe"
$~ arr [16]s64
@ f (p0 s64, p1 u32, p2 s16, p3 u8) s64 {
  $~ h s64 = 7
%s
  $~ k s64 = 0
  * (k < 16) {
    h = ((h * 31) + arr[k])
    k = (k + 1)
  }
  ^ h
}
@! () s64 {
  px(u64(f(3, 4000000000, s16(p()), 200)))
  nl()
  px(u64(f((0 - 77), 5, 9, 0)))
  nl()
  ^ 0
}
@ p () s64 { ^ (0 - 1234) }
%s
'''%(body,hs)
def run(path, opt):
    prog=build(path, include_dirs=[stdlib_dir()])
    blob=compile_program(prog, opt)
    out=path+(".o1" if opt else ".o0")
    open(out,"wb").write(blob); os.chmod(out,0o755)
    p=subprocess.run([out],capture_output=True,timeout=10)
    return p.returncode, p.stdout
a,b=int(sys.argv[1]),int(sys.argv[2])
os.makedirs("fz",exist_ok=True)
bad=0
for seed in range(a,b):
    src=gen(seed); path="fz/s%d.vibe"%seed
    open(path,"w").write(src)
    try:
        r1=run(path,True); r0=run(path,False)
    except Exception as e:
        print("seed",seed,"EXC",type(e).__name__,str(e)[:200]); bad+=1; continue
    if r1!=r0:
        print("seed",seed,"MISMATCH",r1,r0); bad+=1
    else:
        os.remove(path); os.remove(path+".o1"); os.remove(path+".o0")
print("done bad=",bad)

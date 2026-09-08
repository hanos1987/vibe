"""Generate the C reference programs, matching the VIBE ones statement for
statement so the comparison measures code generation and nothing else."""
import os

HERE = os.path.dirname(os.path.abspath(__file__))

FILES = {
"fib.c": r"""
#include <stdio.h>
long fib(long n){ if(n<2) return n; return fib(n-1)+fib(n-2); }
int main(void){ printf("%ld\n", fib(35)); return 0; }
""",

"sieve.c": r"""
#include <stdio.h>
#include <sys/mman.h>
int main(void){
  long n = 10000000;
  unsigned char *p = mmap(0, n+1, PROT_READ|PROT_WRITE,
                          MAP_PRIVATE|MAP_ANONYMOUS, -1, 0);
  if(p == MAP_FAILED) return 1;
  long cnt = 0;
  for(long i=2;i<=n;i++){
    if(p[i]==0){
      cnt++;
      for(long j=i*i;j<=n;j+=i) p[j]=1;
    }
  }
  printf("%ld\n", cnt);
  return 0;
}
""",

"matmul.c": r"""
#include <stdio.h>
#include <sys/mman.h>
int main(void){
  long n = 400;
  long sz = n*n*8;
  long *a = mmap(0, sz, PROT_READ|PROT_WRITE, MAP_PRIVATE|MAP_ANONYMOUS, -1, 0);
  long *b = mmap(0, sz, PROT_READ|PROT_WRITE, MAP_PRIVATE|MAP_ANONYMOUS, -1, 0);
  long *c = mmap(0, sz, PROT_READ|PROT_WRITE, MAP_PRIVATE|MAP_ANONYMOUS, -1, 0);
  for(long i=0;i<n;i++)
    for(long j=0;j<n;j++){
      a[i*n+j] = (i+j)%7;
      b[i*n+j] = (i-j)%5;
    }
  for(long i=0;i<n;i++)
    for(long j=0;j<n;j++){
      long s=0;
      for(long k=0;k<n;k++) s += a[i*n+k]*b[k*n+j];
      c[i*n+j]=s;
    }
  long sum=0;
  for(long i=0;i<n*n;i++) sum += c[i];
  printf("%ld\n", sum);
  return 0;
}
""",

"mandel.c": r"""
#include <stdio.h>
int main(void){
  long w=900,h=900,maxit=100,total=0;
  for(long py=0;py<h;py++){
    for(long px=0;px<w;px++){
      double cr = (double)px/300.0 - 2.0;
      double ci = (double)py/300.0 - 1.5;
      double zr=0.0, zi=0.0;
      long it=0;
      for(;it<maxit;it++){
        double zr2=zr*zr, zi2=zi*zi;
        if(zr2+zi2 > 4.0) break;
        double t = zr2-zi2+cr;
        zi = 2.0*zr*zi + ci;
        zr = t;
      }
      total += it;
    }
  }
  printf("%ld\n", total);
  return 0;
}
""",
}

for name, body in FILES.items():
    with open(os.path.join(HERE, name), "w") as fh:
        fh.write(body.lstrip())
print("wrote %d C reference programs" % len(FILES))

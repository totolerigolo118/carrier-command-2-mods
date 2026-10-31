#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <stdint.h>
#include <math.h>
extern unsigned char g_in[0x190], g_out[0x190];
extern void run_regs(void *entry);
extern void orig_a(), orig_b(), orig_c(), orig_d(), cave_a(), cave_b(), cave_c(), cave_d();
extern float g_echelle;
static const char *RN[16]={"rax","rbx","rcx","rdx","rsi","rdi","rbp","rsp","r8","r9","r10","r11","r12","r13","r14","r15"};
static uint64_t rnd64(void){ return ((uint64_t)rand()<<42) ^ ((uint64_t)rand()<<21) ^ (uint64_t)rand() ^ ((uint64_t)rand()<<60); }
static void fill(void){ for (int i=0;i<0x190;i++) g_in[i]=rand(); uint64_t fl = 0x202 | (rnd64() & 0x8d5); memcpy(g_in+0x88,&fl,8); }
static unsigned char outA[0x190];
static int diffs[16+1+16];
static void run(void *e, unsigned char *dst, float ech){ g_echelle=ech; run_regs(e); memcpy(dst,g_out,0x190); }
static void report(const char *nom, unsigned char *a, unsigned char *b, float ea, float eb, long *cnt){
  for(int i=0;i<16;i++){ if(i==7) continue; if(memcmp(a+8*i,b+8*i,8)) cnt[i]++; }
  uint64_t fa,fb; memcpy(&fa,a+0x88,8); memcpy(&fb,b+0x88,8); if((fa^fb)&0x8d5) cnt[16]++;
  for(int i=0;i<16;i++) if(memcmp(a+0x90+16*i,b+0x90+16*i,16)) cnt[17+i]++;
  if(memcmp(&ea,&eb,4)) cnt[33]++;
}
static void print(const char *nom,long *cnt,int n){
  printf("%s (%d essais) registres/flags/xmm/memoire differents :", nom, n);
  int any=0;
  for(int i=0;i<16;i++) if(cnt[i]){printf(" %s(%ld)",RN[i],cnt[i]);any=1;}
  if(cnt[16]){printf(" FLAGS(%ld)",cnt[16]);any=1;}
  for(int i=0;i<16;i++) if(cnt[17+i]){printf(" xmm%d(%ld)",i,cnt[17+i]);any=1;}
  if(cnt[33]){printf(" g_echelle(%ld)",cnt[33]);any=1;}
  if(!any) printf(" aucun");
  printf("\n");
}
struct mm { char *p; unsigned len; unsigned pad; };
int main(void){
  srand(12345);
  static unsigned char defs[16*0x78];
  const char *scripts[]={"scripts/screen_navigation.lua","scripts/screen_cctv.lux","scripts/screen_cctv.lua2","","scripts/screen_cXtv.lua",NULL,"scripts/screen_holomap.lua"};
  long cnt[40]={0}; int n=0;
  for (int k=0;k<2000;k++){
    int idx=rand()%16; unsigned char *e=defs+idx*0x78; memset(e,0x55,0x78);
    const char *s=scripts[rand()%7]; struct mm m={NULL,0,0}; if(s){m.len=strlen(s); m.p=strdup(s);} memcpy(e+0x18,&m,16);
    int type=rand()%9-1; memcpy(e+0x60,&type,4);
    fill(); uint64_t v=(uint64_t)(uintptr_t)defs; memcpy(g_in+0x00,&v,8); v=idx*0x78; memcpy(g_in+0x10,&v,8);
    unsigned char a[0x190],b[0x190]; run(orig_a,a,0); float ea=g_echelle; run(cave_a,b,0); report("A",a,b,ea,g_echelle,cnt); n++;
  }
  print("A non-CCTV",cnt,n);
  memset(cnt,0,sizeof cnt); n=0;
  unsigned dims[][2]={{128,128},{256,128},{512,256},{256,256},{64,32},{512,128},{128,512},{513,512},{511,512}};
  for (int k=0;k<2000;k++){
    unsigned char img[0x40]; memset(img,0x77,sizeof img); int j=rand()%9; memcpy(img+0x20,&dims[j][0],4); memcpy(img+0x24,&dims[j][1],4);
    fill(); uint64_t v=(uint64_t)(uintptr_t)img; memcpy(g_in+0x70,&v,8);
    float ech = (rand()&1)?4.0f:0.0f;
    unsigned char a[0x190],b[0x190]; run(orig_b,a,ech); float ea=g_echelle; run(cave_b,b,ech); report("B",a,b,ea,g_echelle,cnt); n++;
  }
  print("B non-CCTV",cnt,n);
  memset(cnt,0,sizeof cnt); n=0;
  for (int k=0;k<2000;k++){
    float el[8]; for(int i=0;i<8;i++) el[i]=(rand()%20000-2000)/10.0f*(rand()%5?1:0.01f);
    fill(); uint64_t v=(uint64_t)(uintptr_t)el; memcpy(g_in+0x28,&v,8);
    unsigned char a[0x190],b[0x190]; run(orig_c,a,0); float ea=g_echelle; run(cave_c,b,0); report("C",a,b,ea,g_echelle,cnt); n++;
  }
  print("C echelle=0",cnt,n);
  memset(cnt,0,sizeof cnt); n=0;
  for (int k=0;k<2000;k++){
    fill();
    unsigned char a[0x190],b[0x190]; run(orig_d,a,4.0f); float ea=g_echelle; run(cave_d,b,4.0f); report("D",a,b,ea,g_echelle,cnt); n++;
  }
  print("D",cnt,n);
  return 0;
}

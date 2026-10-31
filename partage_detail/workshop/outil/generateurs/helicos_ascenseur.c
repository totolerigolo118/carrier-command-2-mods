/*
 * Patch "helicopters set down on the lift" for Carrier Command 2 (build_mac of 2026-01-05, md5 b0107170...).
 *
 * Compiled by generer_helicos_ascenseur.py (clang -arch x86_64), then placed in the dead code of
 * ImGui::ShowDemoWindow (0x10005af39..0x100061c00, never called by the game). Three hooks in
 * c_vehicle_server_carrier::docking_manager_air::update (0x1001accd8):
 *   H1 0x1001acd94  entry of the "returns" mode: calls hl_tick on every tick;
 *   H2 0x1001ad7af  exit of the "returns" mode: forbidden while the lift lane is occupied;
 *   H3 0x1001ae071  taxiing state 6 -> 7 (towards the lift): waits if a helicopter is descending onto the platform.
 *
 * Lift lane = field 0x84 of the manager (vehicle_id_rotor_takeoff, saved by the game, unused during returns).
 * One helicopter at a time; the other aircraft land on the runway as before.
 * Lane state in two free fields of the manager (padding, never read by the game):
 *   0x9c  0xA5 << 24 | engaged << 23 | tick counter (23 bits)
 *   0x114 0xB6 << 24 | id of the last helicopter sent back to the runway (24 bits)
 * Game reference frame: y up, mat34_f64 matrices = 9 doubles of rotation followed by the translation (+0x48).
 * All matrix x vector multiplications go through the game's function (same convention).
 */

typedef unsigned int u32;
typedef unsigned short u16;
typedef unsigned char u8;
typedef unsigned long long u64;

#define AT(p, o)    ((char *)(p) + (o))
#define I32(p, o)   (*(int *)AT(p, o))
#define U32(p, o)   (*(u32 *)AT(p, o))
#define U16(p, o)   (*(u16 *)AT(p, o))
#define U8(p, o)    (*(u8 *)AT(p, o))
#define U64(p, o)   (*(u64 *)AT(p, o))
#define F32(p, o)   (*(float *)AT(p, o))
#define F64(p, o)   (*(double *)AT(p, o))
#define PTR(p, o)   (*(void **)AT(p, o))
#define VFN(obj, off) ((*(void ***)(obj))[(off) / 8])

#define HIDDEN __attribute__((visibility("hidden")))

typedef struct { double x, y, z; } vec3d;
typedef struct { float x, y, z, w; } vec3f;

/* game functions and data (addresses given to the generator) */
extern void g_mul_m33_v3(vec3d *out, const double *m, const vec3d *v) HIDDEN;
extern u32 g_bay_index_attach(void *carrier, u32 attach_type, u32 hint) HIDDEN;
extern u32 g_bay_index_type(void *carrier, u32 object_type, u32 hint) HIDDEN;
extern void g_dock_immediate(void *carrier, void *map, void *child, u32 bay) HIDDEN;
extern void g_undock_immediate(void *parent, void *map, void *scene, void *child) HIDDEN;
extern void g_set_attached_to(void *veh, void *map, u32 parent_id) HIDDEN;
extern void g_set_att_transform(void *att, const double *m) HIDDEN;
extern void g_create_physics(void *att, void *parent, void *child) HIDDEN;
extern void **g_push_joint(void *vec) HIDDEN;
extern void **g_push_event(void *vec) HIDDEN;
extern void g_queue_erase(void *vec, u32 index) HIDDEN;
extern u32 *g_queue_push(void *vec) HIDDEN;
extern void g_mm_string_ctor(void *str, const char *s) HIDDEN;
extern void *g_get_link(void *def, const void *str) HIDDEN;
extern void g_path_from_link_rev(void *vec, void *def, void *link) HIDDEN;
extern void *g_new(u64 size) HIDDEN;
extern void g_free(void *p) HIDDEN;
extern char g_event_vtable[] HIDDEN;          /* vtable for event_vehicle_set_attached_to_vehicle + 0x10 */
extern char g_str_load_lift_lower[] HIDDEN;   /* "load_lift_lower" */

typedef u8 (*fn_bool)(void *);
typedef void (*fn_gear)(void *, u32);
typedef void (*fn_limits)(void *, float, float);
typedef void (*fn_velocity)(vec3f *, void *);
typedef void (*fn_map_dock)(void *, u32, u32, u32);
typedef void (*fn_void)(void *);

/* settings */
#define TAG_ETAT      0xA5u
#define TAG_REFUS     0xB6u
#define ENGAGE        (1u << 23)
#define TICKS_MAX     6000        /* 200 s in the lane without landing -> runway */
#define PORTEE        1500.0      /* m: a helicopter farther away stays in the original queue */
#define H_ATTENTE     15.0        /* m above the platform */
#define V_APPROCHE    18.0        /* m/s approach speed (on top of the ship's speed) */

static double rac(double x) { return __builtin_sqrt(x > 0.0 ? x : 0.0); }
static double borne(double x, double a, double b) { return x < a ? a : (x > b ? b : x); }

static u32 anneau(u32 tete, u32 i, u32 cap)
{
    u32 k = tete + i;
    return k < cap ? k : k - cap;
}

static void *vehicule(void *vcont, u32 id)
{
    u32 n = U32(vcont, 0x60), cap = U32(vcont, 0x58), tete = U32(vcont, 0x5c);
    void **tab = (void **)PTR(vcont, 0x50);
    for (u32 i = 0; i < n; i++) {
        void *v = tab[anneau(tete, i, cap)];
        if (v && U32(v, 0x8c) == id)
            return v;
    }
    return 0;
}

static double *corps0(void *veh)
{
    void **tab = (void **)PTR(veh, 0xa0);
    u32 cap = U32(veh, 0xa8), tete = U32(veh, 0xac);
    return (double *)tab[tete < cap ? tete : tete - cap];
}

static vec3f vitesse(void *veh)
{
    vec3f r;
    void *phys = PTR(corps0(veh), 0xf0);
    ((fn_velocity)VFN(phys, 0x138))(&r, phys);
    return r;
}

/* platform point (ship frame) and its orientation, like the game's lift logic */
static float *noeud(void *carrier, u32 index)
{
    void *def = PTR(carrier, 0x98);
    return (float *)AT(PTR(def, 0x220), anneau(U32(def, 0x22c), index, U32(def, 0x228)) * 0x48 + 0x14);
}

static void matrice_ascenseur(void *carrier, void *mgr, double *m)
{
    float *f = noeud(carrier, U32(mgr, 0xa4));
    for (int k = 0; k < 12; k++)
        m[k] = f[k];
    m[10] += F32(carrier, 0x1518);
}

static vec3d vers_monde(const double *c, vec3d local)
{
    vec3d r;
    g_mul_m33_v3(&r, c, &local);
    r.x += c[9]; r.y += c[10]; r.z += c[11];
    return r;
}

static vec3d tourner(const double *m, vec3d v)
{
    vec3d r;
    g_mul_m33_v3(&r, m, &v);
    return r;
}

static int joueurs_a_bord(void *carrier, void *peers)
{
    u32 n = U32(peers, 0x10), cap = U32(peers, 0x8), tete = U32(peers, 0xc);
    void **tab = (void **)PTR(peers, 0);
    u32 equipe = U32(carrier, 0x188);
    for (u32 i = 0; i < n; i++) {
        void *p = tab[anneau(tete, i, cap)];
        if (p && U32(p, 0x70) == equipe)
            return 1;
    }
    return 0;
}

static u32 etat_lire(void *mgr)
{
    u32 e = U32(mgr, 0x9c);
    return (e >> 24) == TAG_ETAT ? e : (TAG_ETAT << 24);
}

static void liberer(void *mgr)
{
    I32(mgr, 0x84) = -1;
    U32(mgr, 0x9c) = TAG_ETAT << 24;
}

static void train(void *veh, int baisse)
{
    ((fn_gear)VFN(veh, 0x138))(veh, baisse ? 1 : 0);
}

static void reglages_vol(void *veh, float a, float b)
{
    ((fn_limits)VFN(veh, 0x130))(veh, a, b);
}

/* failure: like a failed approach in the game, the helicopter goes back into the queue and will use the runway */
static void renvoyer_vers_piste(void *mgr, void *veh)
{
    u32 id = U32(veh, 0x8c);
    reglages_vol(veh, 0.0f, 1.0f);
    F32(veh, 0x2cc) = 1.0f;
    u32 *el = g_queue_push(AT(mgr, 0x48));
    el[0] = id;
    el[1] = 3;
    el[2] = 0;
    U64(veh, 0x21c) = 0x500000002ull;
    u32 n = U32(veh, 0x208);
    void **roues = (void **)PTR(veh, 0x200);
    for (u32 i = 0; i < n; i++)
        if (roues[i])
            U8(roues[i], 0x134) = 1;
    train(veh, 0);
    U32(mgr, 0x114) = (TAG_REFUS << 24) | (id & 0xffffffu);
    liberer(mgr);
}

/* the Petrel drops its vehicle into the hangar, as during the game's approach */
static void lacher_cargaison(void *carrier, void *veh, void *vcont, void *map, void *scene)
{
    u32 n = U32(veh, 0x1f8);
    for (u32 i = 0; i < n; i++) {
        u32 id = U32(AT(PTR(veh, 0x1f0), i * 0x70), 0x68);
        if (!id)
            continue;
        void *cargo = vehicule(vcont, id);
        if (!cargo)
            continue;
        g_undock_immediate(veh, map, scene, cargo);
        u32 baie = g_bay_index_type(carrier, U32(cargo, 0x90), U8(cargo, 0x234));
        if (baie < U32(carrier, 0x1f8))
            g_dock_immediate(carrier, map, cargo, baie);
    }
}

/* set down on the platform: attachment identical to the game's touchdown (0x1001b2061), then hand-over to
   the lift as at the end of taxiing state 7 (0x1001ae13a) */
static int poser(void *mgr, void *carrier, void *veh, void *map, void *peers, void *scene)
{
    void *def = PTR(carrier, 0x98);
    u32 baie = g_bay_index_attach(carrier, 1, U8(veh, 0x234));
    if (baie >= U32(def, 0x140))
        return 0;
    u32 vid = U32(veh, 0x8c), cid = U32(carrier, 0x8c);

    reglages_vol(veh, 0.0f, 1.0f);
    F32(veh, 0x2cc) = 0.0f;
    void *att = AT(PTR(carrier, 0x1f0), baie * 0x70);
    g_set_attached_to(veh, map, cid);
    U64(veh, 0x198) = 0;
    I32(veh, 0x1a0) = -1;
    U8(veh, 0x234) = (u8)baie;
    double m[12];
    matrice_ascenseur(carrier, mgr, m);
    if (U32(att, 0x68) != vid)
        U32(att, 0x68) = vid;
    g_set_att_transform(att, m);
    g_create_physics(att, carrier, veh);
    void *joint = PTR(att, 0x60);
    *g_push_joint(AT(scene, 0x60)) = joint;
    ((fn_void)VFN(joint, 0x10))(joint);
    ((fn_map_dock)VFN(map, 0x40))(map, cid, baie, vid);
    U64(veh, 0x21c) = 0x600000001ull;
    u32 nr = U32(veh, 0x208);
    void **roues = (void **)PTR(veh, 0x200);
    for (u32 i = 0; i < nr; i++)
        if (roues[i])
            U8(roues[i], 0x134) = 0;
    u32 np = U32(peers, 0x10), cap = U32(peers, 0x8), tete = U32(peers, 0xc);
    void **pairs = (void **)PTR(peers, 0);
    for (u32 i = 0; i < np; i++) {
        void *pair = pairs[anneau(tete, i, cap)];
        void *ev = g_new(0x10);
        PTR(ev, 0) = g_event_vtable;
        *g_push_event(AT(PTR(pair, 0x68), 0x10)) = ev;
        U32(ev, 8) = vid;
        U16(ev, 0xc) = (u16)cid;
    }

    /* the lift takes the helicopter; the game lowers it and taxis it to the crane */
    I32(mgr, 0x7c) = (int)vid;
    I32(mgr, 0x8c) = (int)baie;
    if (U32(mgr, 0xd8)) {
        g_free(PTR(mgr, 0xd0));
        PTR(mgr, 0xd0) = 0;
        U32(mgr, 0xd8) = 0;
    }
    U64(mgr, 0xdc) = 0;
    U64(mgr, 0xe8) = 0;
    u64 chaine[2];
    g_mm_string_ctor(chaine, g_str_load_lift_lower);
    void *lien = g_get_link(def, chaine);
    if ((void *)chaine[0]) {
        g_free((void *)chaine[0]);
        chaine[1] = 0;
    }
    g_path_from_link_rev(AT(mgr, 0xd0), def, lien);
    liberer(mgr);
    return 1;
}

/* 1 = all wheels in contact (same test as the game), 0 = no, -1 = no wheel known */
static int roues_au_contact(void *veh)
{
    u32 n = U32(veh, 0xd8);
    if (!n)
        return -1;
    char *r = (char *)PTR(veh, 0xd0);
    for (u32 i = 0; i < n; i++) {
        float compression = F32(r, i * 0x70), glisse = F32(r, i * 0x70 + 4);
        if (compression < 0.01f || glisse > 0.1f)
            return 0;
    }
    return 1;
}

static void piloter(void *mgr, void *carrier, void *veh, void *vcont, void *map, void *peers, void *scene)
{
    u32 e = etat_lire(mgr);
    u32 ticks = (e & 0x7fffffu) + 1;
    int engage = (e & ENGAGE) != 0;

    double *c = corps0(carrier);
    double *p = corps0(veh);
    double nm[12];
    matrice_ascenseur(carrier, mgr, nm);
    vec3d haut = vers_monde(c, (vec3d){ nm[9], nm[10], nm[11] });
    vec3d cap_ascenseur = tourner(c, tourner(nm, (vec3d){ 0.0, 0.0, 1.0 }));
    vec3d cap_bateau = tourner(c, (vec3d){ 0.0, 0.0, 1.0 });
    vec3f vb = vitesse(carrier), vh = vitesse(veh);

    double dx = haut.x - p[9], dz = haut.z - p[11];
    double d = rac(dx * dx + dz * dz);
    double h = p[10] - haut.y;
    double rx = vh.x - vb.x, ry = vh.y - vb.y, rz = vh.z - vb.z;
    double vrel = rac(rx * rx + ry * ry + rz * rz);

    /* platform free, at the top, and no aircraft taxiing onto it (runway state 7) */
    int pret = I32(mgr, 0x7c) == -1 && F32(carrier, 0x1518) > -0.01f && I32(mgr, 0x24) != 7;
    if (engage && (I32(mgr, 0x7c) != -1 || d > 8.0))
        engage = 0;
    if (!engage && pret && d < 3.0 && vrel < 2.0 && h < 25.0)
        engage = 1;

    if (engage && h < 25.0)
        lacher_cargaison(carrier, veh, vcont, map, scene);
    int contact = roues_au_contact(veh);
    if (engage && d < 4.0 && vrel < 4.0 && ((contact == 1 && h < 8.0) || (contact == -1 && h < 3.0))) {
        if (poser(mgr, carrier, veh, map, peers, scene))
            return;
    }
    if (ticks > TICKS_MAX) {
        renvoyer_vers_piste(mgr, veh);
        return;
    }

    /* target: above the platform (higher when coming from far), or on it if engaged */
    double hc = engage ? -2.0 : (d < 40.0 ? H_ATTENTE : borne(H_ATTENTE + 0.25 * (d - 40.0), H_ATTENTE, 60.0));
    vec3d cible = vers_monde(c, (vec3d){ nm[9], nm[10] + hc, nm[11] });

    /* desired velocity = ship velocity + approach towards the platform; heading = direction of travel when far,
       then the platform's heading (ship stopped) or the ship's heading (ship under way) near the goal */
    double vx = vb.x, vz = vb.z;
    double ux = d > 0.01 ? dx / d : 0.0, uz = d > 0.01 ? dz / d : 0.0;
    double s = V_APPROCHE < 0.3 * d ? V_APPROCHE : 0.3 * d;
    vx += ux * s;
    vz += uz * s;
    double nv = rac(vx * vx + vz * vz);
    double lx = nv > 1.0 ? vx / nv : ux, lz = nv > 1.0 ? vz / nv : uz;
    double vb_h = rac((double)vb.x * vb.x + (double)vb.z * vb.z);
    double px = vb_h > 1.5 ? cap_bateau.x : cap_ascenseur.x, pz = vb_h > 1.5 ? cap_bateau.z : cap_ascenseur.z;
    double w = borne((d - 2.0) / 6.0, 0.0, 1.0);
    double ax = w * lx + (1.0 - w) * px, az = w * lz + (1.0 - w) * pz;
    double na = rac(ax * ax + az * az);
    if (na < 1e-6) { ax = px; az = pz; na = rac(ax * ax + az * az); }
    if (na < 1e-6) { ax = 0.0; az = 1.0; na = 1.0; }
    ax /= na;
    az /= na;

    I32(veh, 0x220) = 1;
    I32(veh, 0x2a0) = 3;
    F64(veh, 0x2a8) = cible.x;
    F64(veh, 0x2b0) = cible.y;
    F64(veh, 0x2b8) = cible.z;
    F32(veh, 0x2c0) = (float)ax;
    F32(veh, 0x2c4) = (float)az;
    F32(veh, 0x2c8) = (float)(vx * ax + vz * az);
    F32(veh, 0x2cc) = 1.0f;
    reglages_vol(veh, 0.6f, 1.0f);
    if (d < 60.0)
        train(veh, 1);

    U32(mgr, 0x9c) = (TAG_ETAT << 24) | (engage ? ENGAGE : 0) | (ticks & 0x7fffffu);
}

static void choisir(void *mgr, void *carrier, void *vcont, void *peers)
{
    u32 n = U32(mgr, 0x58);
    if (!n || !joueurs_a_bord(carrier, peers))
        return;
    void *def = PTR(carrier, 0x98);
    if (g_bay_index_attach(carrier, 1, 0xff) >= U32(def, 0x140))
        return;
    u32 refus = U32(mgr, 0x114);
    u32 banni = (refus >> 24) == TAG_REFUS ? (refus & 0xffffffu) : 0xffffffffu;
    double *c = corps0(carrier);
    double nm[12];
    matrice_ascenseur(carrier, mgr, nm);
    vec3d haut = vers_monde(c, (vec3d){ nm[9], nm[10], nm[11] });
    u32 cap = U32(mgr, 0x50), tete = U32(mgr, 0x54);
    u32 *file = (u32 *)PTR(mgr, 0x48);
    for (u32 i = 0; i < n; i++) {
        u32 *el = file + 3 * anneau(tete, i, cap);
        u32 id = el[0];
        if ((id & 0xffffffu) == banni)
            continue;
        void *v = vehicule(vcont, id);
        if (!v || !((fn_bool)VFN(v, 0xa0))(v))
            continue;
        double *p = corps0(v);
        double dx = haut.x - p[9], dz = haut.z - p[11];
        if (dx * dx + dz * dz > PORTEE * PORTEE)
            continue;
        g_queue_erase(AT(mgr, 0x48), i);
        u32 reste = U32(mgr, 0x58);
        cap = U32(mgr, 0x50);
        tete = U32(mgr, 0x54);
        file = (u32 *)PTR(mgr, 0x48);
        for (u32 k = 0; k < reste; k++)
            file[3 * anneau(tete, k, cap) + 2] = 0;
        I32(mgr, 0x84) = (int)id;
        U32(mgr, 0x9c) = TAG_ETAT << 24;
        train(v, 1);
        I32(v, 0x220) = 1;
        return;
    }
}

HIDDEN void hl_tick(void *mgr, void *carrier, void *vcont, void *map, void *peers, void *scene)
{
#ifdef TEMOIN
    (void)mgr; (void)carrier; (void)vcont; (void)map; (void)peers; (void)scene;
#else
    int id = I32(mgr, 0x84);
    if (id != -1) {
        void *v = vehicule(vcont, (u32)id);
        if (!v || I32(v, 0x220) != 1 || !((fn_bool)VFN(v, 0xa0))(v)) {
            liberer(mgr);
            return;
        }
        piloter(mgr, carrier, v, vcont, map, peers, scene);
        return;
    }
    choisir(mgr, carrier, vcont, peers);
#endif
}

/* hooks: game registers at the entry of the "returns" mode (0x1001acd94):
   r14 manager, r15 ship, r8 vehicle container, r13 map, rbx players, -0x80(%rbp) physics scene;
   rsp 16-byte aligned. Every register the game may still read is saved. */
__asm__(
    ".text\n"
    ".p2align 4\n"
    ".globl _hl_h1\n"
    "_hl_h1:\n"
    "    movq %r13, -0x70(%rbp)\n"
    "    pushq %rax\n pushq %rcx\n pushq %rdx\n pushq %rsi\n pushq %rdi\n"
    "    pushq %r8\n pushq %r9\n pushq %r10\n pushq %r11\n"
    "    subq $264, %rsp\n"
    "    movdqu %xmm0, 0(%rsp)\n movdqu %xmm1, 16(%rsp)\n movdqu %xmm2, 32(%rsp)\n movdqu %xmm3, 48(%rsp)\n"
    "    movdqu %xmm4, 64(%rsp)\n movdqu %xmm5, 80(%rsp)\n movdqu %xmm6, 96(%rsp)\n movdqu %xmm7, 112(%rsp)\n"
    "    movdqu %xmm8, 128(%rsp)\n movdqu %xmm9, 144(%rsp)\n movdqu %xmm10, 160(%rsp)\n movdqu %xmm11, 176(%rsp)\n"
    "    movdqu %xmm12, 192(%rsp)\n movdqu %xmm13, 208(%rsp)\n movdqu %xmm14, 224(%rsp)\n movdqu %xmm15, 240(%rsp)\n"
    "    movq %r14, %rdi\n"
    "    movq %r15, %rsi\n"
    "    movq %r8, %rdx\n"
    "    movq %r13, %rcx\n"
    "    movq %rbx, %r8\n"
    "    movq -0x80(%rbp), %r9\n"
    "    call _hl_tick\n"
    "    movdqu 0(%rsp), %xmm0\n movdqu 16(%rsp), %xmm1\n movdqu 32(%rsp), %xmm2\n movdqu 48(%rsp), %xmm3\n"
    "    movdqu 64(%rsp), %xmm4\n movdqu 80(%rsp), %xmm5\n movdqu 96(%rsp), %xmm6\n movdqu 112(%rsp), %xmm7\n"
    "    movdqu 128(%rsp), %xmm8\n movdqu 144(%rsp), %xmm9\n movdqu 160(%rsp), %xmm10\n movdqu 176(%rsp), %xmm11\n"
    "    movdqu 192(%rsp), %xmm12\n movdqu 208(%rsp), %xmm13\n movdqu 224(%rsp), %xmm14\n movdqu 240(%rsp), %xmm15\n"
    "    addq $264, %rsp\n"
    "    popq %r11\n popq %r10\n popq %r9\n popq %r8\n"
    "    popq %rdi\n popq %rsi\n popq %rdx\n popq %rcx\n popq %rax\n"
    "    cmpl $-1, 0x80(%r14)\n"
    "    movq %r14, %rax\n"
    "    jne g_ret_ace50\n"
    "    jmp g_ret_acda9\n"
    "\n"
    ".p2align 4\n"
    ".globl _hl_h2\n"
    "_hl_h2:\n"
    "    cmpl $-1, 0x84(%r14)\n"
    "    jne g_ret_ae787\n"
    "    jmp g_ret_ae780\n"
    "\n"
    ".p2align 4\n"
    ".globl _hl_h3\n"
    "_hl_h3:\n"
    "    cmpl $-1, 0x7c(%r14)\n"
    "    jne g_ret_ae07c\n"
    "    cmpl $-1, 0x84(%r14)\n"
    "    je g_ret_b151b\n"
    "    cmpb $0xa5, 0x9f(%r14)\n"
    "    jne g_ret_b151b\n"
    "    testb $0x80, 0x9e(%r14)\n"
    "    jnz g_ret_ae07c\n"
    "    jmp g_ret_b151b\n"
);

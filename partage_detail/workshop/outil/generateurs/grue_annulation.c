/*
 * Patch "cancel the launch of an aircraft already picked up by the crane" for Carrier Command 2
 * (build_mac of 2026-01-05, md5 b0107170...). public tracker request no. 20652, study part 02 of the notes, section 5.
 *
 * Compiled by generer_grue_annulation.py (clang -arch x86_64), placed in the dead code of
 * ImGui::ShowDemoWindow (never called by the game). Two hooks:
 *   A 0x1001a8c01  docking_manager_air::undock, aircraft already in the crane/lift/runway: the game only does
 *                  something if the aircraft is waiting at launch (dock_state 7); otherwise we call ag_annuler.
 *   B 0x1001ad9ad  docking_manager_air::update, launch mode, just before "end of crane -> lift":
 *                  ag_fin releases the crane when an aircraft brought back to its bay has been set down.
 *
 * Aircraft manager (carrier + 0x15e8): 0x00 mode (2 = launch), 0x08 list of crane moves (ring buffer of
 * ints: +0 pointer, +8 capacity, +0xc head, +0x10 count), 0x20 the crane is holding the aircraft,
 * 0x78 id of the crane's aircraft, 0x88 its bay. Moves: 1 go to the bay, 2 return above the lift,
 * 3 rotate, 4 grab then raise (when already holding: raise), 5 set down then raise (when holding
 * nothing: raise). Carrier: 0x1548 crane rotation (0 or pi).
 * Aircraft: 0x8c id, 0x220 dock_state (3 launching, 4 in the hangar), 0x21c launch phase (0 in the hangar).
 * While being carried, the aircraft stays stowed in its bay: only the bay position follows the hook.
 */

typedef unsigned int u32;
typedef unsigned char u8;

#define AT(p, o)    ((char *)(p) + (o))
#define U32(p, o)   (*(u32 *)AT(p, o))
#define U8(p, o)    (*(u8 *)AT(p, o))
#define F32(p, o)   (*(float *)AT(p, o))
#define PTR(p, o)   (*(void **)AT(p, o))
#define VFN(obj, off) ((*(void ***)(obj))[(off) / 8])

#define HIDDEN __attribute__((visibility("hidden")))

#define AUCUN       0xffffffffu
#define OFF_CARRIER 0x15e8        /* the aircraft manager is embedded in the carrier */
#define ROT_MAX     0.01f         /* rad: beyond this, the aircraft has started to be rotated -> refuse */

/* game functions (addresses in the generator's JEU table) */
extern u32 *g_push_geste(void *liste);                      /* mm_vector<e_crane_state>::push_back() */
extern void g_vider_route(void *route);                     /* mm_vector<c_vehicle_waypoint_data>::clear() */
extern void g_reset_route(void *veh);                       /* c_vehicle_server::reset_waypoint_path() */

typedef void (*fn_carte)(void *, u32, void *, void *, u32);

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

static int geste_present(void *mgr, u32 geste)
{
    u32 *tab = (u32 *)PTR(mgr, 0x08);
    u32 cap = U32(mgr, 0x10), tete = U32(mgr, 0x14), n = U32(mgr, 0x18);
    for (u32 i = 0; i < n; i++)
        if (tab[anneau(tete, i, cap)] == geste)
            return 1;
    return 0;
}

static void nouvelle_liste(void *mgr, const u32 *gestes, u32 n)
{
    U32(mgr, 0x14) = 0;
    U32(mgr, 0x18) = 0;
    for (u32 i = 0; i < n; i++)
        *g_push_geste(AT(mgr, 0x08)) = gestes[i];
}

/* 2nd press of the bay button while the crane has already picked up the aircraft (launch in progress).
   Returns 1 if the launch is cancelled, 0 if the game is left to proceed (too late or other case). */
HIDDEN int ag_annuler(void *mgr, void *veh, void *carte)
{
    static const u32 sans_avion[] = { 5, 2 };          /* raise, return to rest */
    static const u32 avec_avion[] = { 4, 1, 5, 2 };    /* raise, go to the bay, set down, return */
    void *carrier = AT(mgr, -OFF_CARRIER);
    u32 id = U32(veh, 0x8c);
    float rot;

    if (U32(mgr, 0x00) != 2 || U32(mgr, 0x78) != id || U32(veh, 0x220) != 3)
        return 0;
    if (!U8(mgr, 0x20)) {
        if (!geste_present(mgr, 4))        /* already released above the lift */
            return 0;
        nouvelle_liste(mgr, sans_avion, 2);
        U32(mgr, 0x78) = AUCUN;            /* the aircraft has not moved: the crane is free immediately */
        U32(mgr, 0x88) = AUCUN;
    } else {
        rot = F32(carrier, 0x1548);
        if (rot > ROT_MAX || rot < -ROT_MAX)   /* already being turned around above the lift */
            return 0;
        nouvelle_liste(mgr, avec_avion, 4);    /* 0x78 kept: the aircraft follows the hook to its bay */
    }
    U32(veh, 0x220) = 4;
    U32(veh, 0x21c) = 0;
    /* as in docking_manager_air::cancel_undocking: route cleared, map notified */
    g_vider_route(AT(veh, 0x1d0));
    g_reset_route(veh);
    ((fn_carte)VFN(carte, 0))(carte, id, AT(veh, 0x300), AT(veh, 0x1d0), U32(veh, 0x1e8));
    return 1;
}

/* Launch mode, on every tick: when the crane has finished setting down a returned aircraft (dock_state 4
   in the crane, which the original game never does in launch mode), it is released instead of handing the
   aircraft over to the lift. State read from the saved game: an interrupted return resumes on load. */
HIDDEN void ag_fin(void *mgr, void *vcont)
{
    void *v;
    u32 id = U32(mgr, 0x78);

    if (U32(mgr, 0x00) != 2 || U32(mgr, 0x18) != 0 || id == AUCUN || U8(mgr, 0x20))
        return;
    v = vehicule(vcont, id);
    if (v && U32(v, 0x220) == 4) {
        U32(mgr, 0x78) = AUCUN;
        U32(mgr, 0x88) = AUCUN;
    }
}

#ifndef ESSAI
/* A: game registers at 0x1001a8c01: rdi manager, r14 aircraft, ebx its id, rcx map; rsp 16-byte aligned;
   returns to the epilogue 0x1001a8c0e, which reads no register.
   B: at 0x1001ad9ad, r14 manager, vehicle container at -0x38(%rbp), rsp 16-byte aligned; landing point
   of 4 game jumps: every register is saved, then cmpl $0,0x18(%r14) is replayed. */
__asm__(
    ".text\n"
    ".p2align 4\n"
    ".globl _ag_a\n"
    "_ag_a:\n"
    "    cmpl $7, 0x220(%r14)\n"
    "    jne 1f\n"
    "    movl %ebx, 0x28(%rdi)\n"
    "    jmp g_ret_a8c0e\n"
    "1:\n"
    "    movq %r14, %rsi\n"
    "    movq %rcx, %rdx\n"
    "    call _ag_annuler\n"
    "    jmp g_ret_a8c0e\n"
    "\n"
    ".p2align 4\n"
    ".globl _ag_b\n"
    "_ag_b:\n"
    "    pushq %rax\n pushq %rcx\n pushq %rdx\n pushq %rsi\n pushq %rdi\n"
    "    pushq %r8\n pushq %r9\n pushq %r10\n pushq %r11\n"
    "    subq $264, %rsp\n"
    "    movdqu %xmm0, 0(%rsp)\n movdqu %xmm1, 16(%rsp)\n movdqu %xmm2, 32(%rsp)\n movdqu %xmm3, 48(%rsp)\n"
    "    movdqu %xmm4, 64(%rsp)\n movdqu %xmm5, 80(%rsp)\n movdqu %xmm6, 96(%rsp)\n movdqu %xmm7, 112(%rsp)\n"
    "    movdqu %xmm8, 128(%rsp)\n movdqu %xmm9, 144(%rsp)\n movdqu %xmm10, 160(%rsp)\n movdqu %xmm11, 176(%rsp)\n"
    "    movdqu %xmm12, 192(%rsp)\n movdqu %xmm13, 208(%rsp)\n movdqu %xmm14, 224(%rsp)\n movdqu %xmm15, 240(%rsp)\n"
    "    movq %r14, %rdi\n"
    "    movq -0x38(%rbp), %rsi\n"
    "    call _ag_fin\n"
    "    movdqu 0(%rsp), %xmm0\n movdqu 16(%rsp), %xmm1\n movdqu 32(%rsp), %xmm2\n movdqu 48(%rsp), %xmm3\n"
    "    movdqu 64(%rsp), %xmm4\n movdqu 80(%rsp), %xmm5\n movdqu 96(%rsp), %xmm6\n movdqu 112(%rsp), %xmm7\n"
    "    movdqu 128(%rsp), %xmm8\n movdqu 144(%rsp), %xmm9\n movdqu 160(%rsp), %xmm10\n movdqu 176(%rsp), %xmm11\n"
    "    movdqu 192(%rsp), %xmm12\n movdqu 208(%rsp), %xmm13\n movdqu 224(%rsp), %xmm14\n movdqu 240(%rsp), %xmm15\n"
    "    addq $264, %rsp\n"
    "    popq %r11\n popq %r10\n popq %r9\n popq %r8\n"
    "    popq %rdi\n popq %rsi\n popq %rdx\n popq %rcx\n popq %rax\n"
    "    cmpl $0, 0x18(%r14)\n"
    "    jmp g_ret_ad9b2\n"
);
#endif

/* Patch "squadron speed" for Carrier Command 2 (build_mac of 2026-01-05, md5 b0107170...).
 *
 * Study: part 05 of the notes. Feature: on the vehicle control screen, choose the cruise speed of the
 * player's own AI-controlled aircraft (ECO / NORMAL / FLANK).
 *
 * 1. _vit_plancher (assembly, further down) replaces 0x1001c2b4b..0x1001c2b8e of
 *    c_vehicle_server_wing::tick_control: when flying to a point (control_mode 0), the target speed there is
 *    clamped to [48, 144] (Albatros) or [72, 144] (Manta, type 10). Here the floor depends on the mode chosen
 *    for the aircraft's team (table g_vit_modes); an AI-controlled team (is_ai_controlled), no mode or an
 *    unknown mode = original game behaviour. Registers xmm0/xmm1 and the field at 0x2c8 end up exactly as
 *    in the original game.
 * 2. vit_lua is a Lua function "cc2_vitesse" (it takes the place of dofile in base_funcs, which neither the
 *    game nor mods use):
 *      cc2_vitesse(team)        -> the team's mode (0 = not chosen yet)
 *      cc2_vitesse(team, mode)  -> sets the mode (1 ECO, 2 NORMAL, 3 FLANK), returns it
 *    The last mode chosen is kept in a small file (CHEMIN) and restored on the first call of a later run.
 *
 * Writable memory: end of the ShowDemoWindowWidgets()::text buffer (0x1029e5680..0x1029e56a0, __data,
 * zeros in the file), which only the dead code of the ImGui demo reads.
 */

#ifndef CHEMIN
#error "CHEMIN must be provided by the generator (-DCHEMIN=...)"
#endif

typedef struct lua_State lua_State;
typedef struct FILE FILE;

extern int g_lua_gettop(lua_State *L);
extern long long g_lua_tointegerx(lua_State *L, int idx, int *isnum);
extern void g_lua_pushinteger(lua_State *L, long long n);
extern FILE *g_fopen(const char *chemin, const char *mode);
extern int g_fgetc(FILE *f);
extern int g_fputs(const char *s, FILE *f);
extern int g_fclose(FILE *f);

/* modes per team number (0..15); etat[0] = file already read, etat[1] = mode stored in the file */
extern unsigned char g_vit_modes[16] __attribute__((visibility("hidden")));
extern unsigned char g_vit_etat[2] __attribute__((visibility("hidden")));

#define NB_EQUIPES 16
#define MODE_MAX 3

static const char chemin[] = CHEMIN;
static const char lecture[] = "r";
static const char ecriture[] = "w";

static int lire_fichier(void)
{
    FILE *f = g_fopen(chemin, lecture);
    if (!f)
        return 0;
    int c = g_fgetc(f);
    g_fclose(f);
    return (c >= '1' && c <= '0' + MODE_MAX) ? c - '0' : 0;
}

static void ecrire_fichier(int mode)
{
    FILE *f = g_fopen(chemin, ecriture);
    if (!f)
        return;
    char texte[3] = { (char)('0' + mode), '\n', 0 };
    g_fputs(texte, f);
    g_fclose(f);
}

int vit_lua(lua_State *L)
{
    int n = g_lua_gettop(L);
    long long equipe = g_lua_tointegerx(L, 1, 0);
    long long mode = 0;
    if (equipe >= 0 && equipe < NB_EQUIPES) {
        if (!g_vit_etat[0]) {
            g_vit_etat[0] = 1;
            g_vit_etat[1] = (unsigned char)lire_fichier();
        }
        if (n >= 2) {
            long long m = g_lua_tointegerx(L, 2, 0);
            if (m >= 1 && m <= MODE_MAX) {
                g_vit_modes[equipe] = (unsigned char)m;
                if (m != g_vit_etat[1]) {
                    ecrire_fichier((int)m);
                    g_vit_etat[1] = (unsigned char)m;
                }
            }
        } else if (g_vit_modes[equipe] == 0) {
            g_vit_modes[equipe] = g_vit_etat[1];
        }
        mode = g_vit_modes[equipe];
    }
    g_lua_pushinteger(L, mode);
    return 1;
}

/* Lua name of the function (pointed to by the "dofile" entry of base_funcs). */
const char vit_nom_lua[] = "cc2_vitesse";

/* Speed floors (m/s) per mode: { Albatros (and any other aircraft), Manta }.
 * 0 = no mode and 1 = ECO: original game. NORMAL = estimate of about 80 % power (study,
 * section 2), to be tuned after in-game testing. FLANK = the ceiling: the throttle stays at maximum. */
const float vit_planchers[MODE_MAX + 1][2] = {
    { 48.0f, 72.0f },
    { 48.0f, 72.0f },
    { 61.0f, 91.0f },
    { 144.0f, 144.0f },
};
const float vit_plafond = 144.0f;

/* Hook at 0x1001c2b4b (67 bytes replaced). Entry: rbx -> speed returned by
 * get_waypoint_position_direction_speed, r13 = the aircraft. rax and rcx are saved; flags are free
 * (the game recomputes them at 0x1001c2ba7 before reading them). No call: stack intact. */
__asm__(
    ".text\n"
    ".globl _vit_plancher\n"
    "_vit_plancher:\n"
    "    movss (%rbx), %xmm0\n"                 /* replays 0x1001c2b4b */
    "    pushq %rax\n"
    "    pushq %rcx\n"
    "    xorl %ecx, %ecx\n"                     /* mode 0 = original game */
    "    movq 0x260(%r13), %rax\n"              /* the aircraft's team (c_team_server*) */
    "    testq %rax, %rax\n"
    "    je 1f\n"
    "    cmpb $0, 0x19(%rax)\n"                 /* is_ai_controlled: enemy aircraft unchanged */
    "    jne 1f\n"
    "    movl 0x14(%rax), %eax\n"               /* team number */
    "    cmpl $16, %eax\n"
    "    jae 1f\n"
    "    leaq _g_vit_modes(%rip), %rcx\n"
    "    movzbl (%rcx,%rax), %ecx\n"
    "    cmpl $3, %ecx\n"
    "    jbe 1f\n"
    "    xorl %ecx, %ecx\n"
    "1:\n"
    "    leaq _vit_planchers(%rip), %rax\n"
    "    movaps %xmm0, %xmm1\n"
    "    maxss (%rax,%rcx,8), %xmm1\n"           /* 0x1001c2b52 : maxss 48 */
    "    minss _vit_plafond(%rip), %xmm1\n"     /* 0x1001c2b5a : minss 144 */
    "    movss %xmm1, 0x2c8(%r13)\n"
    "    cmpl $0xa, 0x90(%r13)\n"               /* Manta? */
    "    jne 2f\n"
    "    maxss 4(%rax,%rcx,8), %xmm0\n"          /* 0x1001c2b75 : maxss 72 */
    "    minss _vit_plafond(%rip), %xmm0\n"
    "    movss %xmm0, 0x2c8(%r13)\n"
    "2:\n"
    "    popq %rcx\n"
    "    popq %rax\n"
    "    jmp _g_ret_2b8e\n"                     /* game continues: movl 0x318(%r13), %esi */
);

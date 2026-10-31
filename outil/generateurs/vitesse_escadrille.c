/* Greffe « vitesse de l'escadrille » pour Carrier Command 2 (build_mac du 05/01/2026, md5 b0107170...).
 *
 * Etude : etudes/ia_vitesse.md. Demande du moddeur le 25/10/2026 : choisir sur l'ecran de controle des
 * vehicules la vitesse de croisiere de SES avions sous IA (ECO / NORMAL / FLANK).
 *
 * 1. _vit_plancher (assembleur, plus bas) remplace 0x1001c2b4b..0x1001c2b8e de
 *    c_vehicle_server_wing::tick_control : en vol vers un point (control_mode 0), la vitesse visee y est
 *    bornee a [48, 144] (Albatros) ou [72, 144] (Manta, type 10). Ici le plancher depend du mode choisi par
 *    l'equipe de l'avion (table g_vit_modes) ; equipe pilotee par l'IA, sans mode ou mode inconnu = jeu
 *    d'origine. Les registres xmm0/xmm1 et la case 0x2c8 finissent exactement comme dans le jeu d'origine.
 * 2. vit_lua est une fonction Lua « cc2_vitesse » (elle prend la place de dofile dans base_funcs, que ni le
 *    jeu ni les mods n'utilisent) :
 *      cc2_vitesse(equipe)        -> mode de l'equipe (0 = pas encore choisi)
 *      cc2_vitesse(equipe, mode)  -> regle le mode (1 ECO, 2 NORMAL, 3 FLANK), le renvoie
 *    Le dernier mode choisi est garde dans un petit fichier (CHEMIN) et repris au premier appel suivant.
 *
 * Memoire inscriptible : fin du tampon ShowDemoWindowWidgets()::text (0x1029e5680..0x1029e56a0, __data,
 * zeros dans le fichier), que seul le code mort de la demo ImGui lit.
 */

#ifndef CHEMIN
#error "CHEMIN doit etre fourni par le generateur (-DCHEMIN=...)"
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

/* modes par numero d'equipe (0..15) ; etat[0] = fichier deja lu, etat[1] = mode du fichier */
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

/* Nom Lua de la fonction (pointe par l'entree « dofile » de base_funcs). */
const char vit_nom_lua[] = "cc2_vitesse";

/* Planchers de vitesse (m/s) par mode : { Albatros (et tout avion), Manta }.
 * 0 = pas de mode et 1 = ECO : jeu d'origine. NORMAL = estimation d'environ 80 % de puissance (etude,
 * section 2), a ajuster apres l'essai en jeu. FLANK = le plafond : la manette reste au maximum. */
const float vit_planchers[MODE_MAX + 1][2] = {
    { 48.0f, 72.0f },
    { 48.0f, 72.0f },
    { 61.0f, 91.0f },
    { 144.0f, 144.0f },
};
const float vit_plafond = 144.0f;

/* Branchement a 0x1001c2b4b (67 octets remplaces). Entree : rbx -> vitesse renvoyee par
 * get_waypoint_position_direction_speed, r13 = l'avion. rax et rcx sont sauvegardes ; drapeaux libres
 * (le jeu les recalcule a 0x1001c2ba7 avant de les lire). Aucun appel : pile intacte. */
__asm__(
    ".text\n"
    ".globl _vit_plancher\n"
    "_vit_plancher:\n"
    "    movss (%rbx), %xmm0\n"                 /* rejoue 0x1001c2b4b */
    "    pushq %rax\n"
    "    pushq %rcx\n"
    "    xorl %ecx, %ecx\n"                     /* mode 0 = jeu d'origine */
    "    movq 0x260(%r13), %rax\n"              /* equipe de l'avion (c_team_server*) */
    "    testq %rax, %rax\n"
    "    je 1f\n"
    "    cmpb $0, 0x19(%rax)\n"                 /* is_ai_controlled : avions ennemis inchanges */
    "    jne 1f\n"
    "    movl 0x14(%rax), %eax\n"               /* numero de l'equipe */
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
    "    cmpl $0xa, 0x90(%r13)\n"               /* Manta ? */
    "    jne 2f\n"
    "    maxss 4(%rax,%rcx,8), %xmm0\n"          /* 0x1001c2b75 : maxss 72 */
    "    minss _vit_plafond(%rip), %xmm0\n"
    "    movss %xmm0, 0x2c8(%r13)\n"
    "2:\n"
    "    popq %rcx\n"
    "    popq %rax\n"
    "    jmp _g_ret_2b8e\n"                     /* suite du jeu : movl 0x318(%r13), %esi */
);

/* Out-of-game test of the logic of grue_annulation.c on a fake aircraft manager.
   Compiled by tests/test_grue_annulation.py: clang -arch x86_64 -DESSAI, run through Rosetta.
   The game functions are replaced by imitations that record their calls. */
#define ESSAI
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define g_push_geste  faux_push_geste
#define g_vider_route faux_vider_route
#define g_reset_route faux_reset_route
#include "../outil/generateurs/grue_annulation.c"

static int echecs, n_vider, n_reset, n_carte;
static unsigned carte_id, carte_e8;
static void *carte_300, *carte_1d0, *veh_courant;

/* faithful imitation of mm_vector<e_crane_state>::push_back (0x10019a450): grows when full (x2, min 32) */
u32 *faux_push_geste(void *v)
{
    u32 cap = U32(v, 8), n = U32(v, 0x10), k;
    if (n == cap) {
        u32 nc = cap * 2 > 32 ? cap * 2 : 32, *t = calloc(nc, 4), *a = PTR(v, 0);
        for (u32 i = 0; i < n; i++) t[i] = a[anneau(U32(v, 0xc), i, cap)];
        PTR(v, 0) = t; U32(v, 8) = nc; U32(v, 0xc) = 0; cap = nc;
    }
    U32(v, 0x10) = n + 1;
    k = U32(v, 0xc) + n;
    if (k >= cap) k -= cap;
    return (u32 *)PTR(v, 0) + k;
}
void faux_vider_route(void *r) { n_vider += r == AT(veh_courant, 0x1d0); }
void faux_reset_route(void *v) { n_reset += v == veh_courant; }
static void faux_carte_fn(void *c, u32 id, void *a, void *b, u32 e)
{ (void)c; n_carte++; carte_id = id; carte_300 = a; carte_1d0 = b; carte_e8 = e; }
static void *vtable_carte[1] = { (void *)faux_carte_fn };
static void **objet_carte[1] = { vtable_carte };
static void *carte = objet_carte;

static unsigned char porte_avions[0x15e8 + 0x200];
static void *mgr = porte_avions + 0x15e8;
static unsigned char avion[0x400], autre[0x400];
static u32 gestes[8];

static void verifier(const char *nom, int c) { printf("  %-62s %s\n", nom, c ? "OK" : "FAIL"); echecs += !c; }

/* ring list of capacity 6, head = tete, then contents */
static void preparer(u32 mode, u32 dock, int tient, float rot, u32 tete, const u32 *l, u32 n)
{
    memset(porte_avions, 0, sizeof porte_avions); memset(avion, 0, sizeof avion); memset(gestes, 0xee, sizeof gestes);
    U32(avion, 0x8c) = 41; U32(avion, 0x220) = dock; U32(avion, 0x21c) = 1; U32(avion, 0x1e8) = 0x77;
    U32(mgr, 0) = mode; U32(mgr, 0x78) = 41; U32(mgr, 0x88) = 3; U8(mgr, 0x20) = (u8)tient;
    F32(porte_avions, 0x1548) = rot;
    PTR(mgr, 0x08) = gestes; U32(mgr, 0x10) = 6; U32(mgr, 0x14) = tete; U32(mgr, 0x18) = n;
    for (u32 i = 0; i < n; i++) gestes[anneau(tete, i, 6)] = l[i];
    n_vider = n_reset = n_carte = 0; veh_courant = avion;
}
static int liste_vaut(const u32 *l, u32 n)
{
    if (U32(mgr, 0x18) != n) return 0;
    for (u32 i = 0; i < n; i++)
        if (((u32 *)PTR(mgr, 0x08))[anneau(U32(mgr, 0x14), i, U32(mgr, 0x10))] != l[i]) return 0;
    return 1;
}
static int intact(u32 dock, u32 n)
{ return U32(avion, 0x220) == dock && U32(avion, 0x21c) == 1 && U32(mgr, 0x78) == 41 && U32(mgr, 0x88) == 3
         && U32(mgr, 0x18) == n && n_vider + n_reset + n_carte == 0; }

int main(void)
{
    static const u32 lancement[] = { 1, 4, 2, 5 }, retourne[] = { 1, 4, 2, 3, 5, 3 };
    static const u32 sans[] = { 5, 2 }, avec[] = { 4, 1, 5, 2 };
    u32 l[6];

    printf("ag_annuler: accepted cases\n");
    preparer(2, 3, 0, 0, 4, lancement, 4);            /* the crane is heading to the bay (ring wraps around) */
    verifier("crane on its way to the bay -> cancelled", ag_annuler(mgr, avion, carte) == 1);
    verifier("  moves = go up, return to rest", liste_vaut(sans, 2));
    verifier("  crane freed at once (0x78 = 0x88 = -1)", U32(mgr, 0x78) == AUCUN && U32(mgr, 0x88) == AUCUN);
    verifier("  aircraft in the hangar (dock 4, phase 0)", U32(avion, 0x220) == 4 && U32(avion, 0x21c) == 0);
    verifier("  path cleared, map told with the right fields", n_vider == 1 && n_reset == 1 && n_carte == 1
             && carte_id == 41 && carte_300 == AT(avion, 0x300) && carte_1d0 == AT(avion, 0x1d0) && carte_e8 == 0x77);

    l[0] = 4; l[1] = 2; l[2] = 3; l[3] = 5; l[4] = 3;
    preparer(2, 3, 0, 0, 0, l, 5);                    /* lowering to grab */
    verifier("crane going down to grab -> cancelled", ag_annuler(mgr, avion, carte) == 1 && liste_vaut(sans, 2));

    l[0] = 5; l[1] = 2; l[2] = 1; l[3] = 4; l[4] = 2; l[5] = 5;
    preparer(2, 3, 0, 0, 5, l, 6);                    /* leftover of a previous return + new pick-up */
    verifier("leftover of a previous return + pick-up -> cancelled", ag_annuler(mgr, avion, carte) == 1 && liste_vaut(sans, 2));

    l[0] = 2; l[1] = 5;
    preparer(2, 3, 1, 0, 2, l, 2);                    /* holding the aircraft, heading to the lift */
    verifier("holding the aircraft, on its way to the elevator -> cancelled", ag_annuler(mgr, avion, carte) == 1);
    verifier("  moves = go up, go to the bay, put down, return", liste_vaut(avec, 4));
    verifier("  crane kept (the aircraft follows the hook)", U32(mgr, 0x78) == 41 && U32(mgr, 0x88) == 3);
    verifier("  aircraft in the hangar", U32(avion, 0x220) == 4 && U32(avion, 0x21c) == 0 && n_carte == 1);

    l[0] = 5;
    preparer(2, 3, 1, 0, 0, l, 1);                    /* lowering to set down above the lift (bay not rotated) */
    verifier("going down to put it on the elevator, not turned -> cancelled", ag_annuler(mgr, avion, carte) == 1 && liste_vaut(avec, 4));
    preparer(2, 3, 1, -0.005f, 0, l, 1);
    verifier("residual rotation -0.005 -> cancelled", ag_annuler(mgr, avion, carte) == 1);

    printf("ag_annuler: refused cases (nothing must change)\n");
    l[0] = 3; l[1] = 5; l[2] = 3;
    preparer(2, 3, 1, 0.4f, 0, l, 3);
    verifier("being turned (rotation 0.4) -> refused", ag_annuler(mgr, avion, carte) == 0 && intact(3, 3));
    preparer(2, 3, 1, 3.1415927f, 0, l + 1, 2);
    verifier("turned (pi), going down to put it down -> refused", ag_annuler(mgr, avion, carte) == 0 && intact(3, 2));
    preparer(2, 3, 0, 3.1415927f, 0, l + 2, 1);
    verifier("released, the crane straightens up -> refused", ag_annuler(mgr, avion, carte) == 0 && intact(3, 1));
    l[0] = 5;
    preparer(2, 3, 0, 0, 0, l, 1);
    verifier("released, the crane goes up -> refused", ag_annuler(mgr, avion, carte) == 0 && intact(3, 1));
    preparer(2, 3, 0, 0, 0, l, 0);
    verifier("empty list (taxiing to the elevator) -> refused", ag_annuler(mgr, avion, carte) == 0 && intact(3, 0));
    preparer(1, 3, 0, 0, 0, lancement, 4);
    verifier("storing mode -> refused", ag_annuler(mgr, avion, carte) == 0 && intact(3, 4));
    preparer(2, 4, 1, 0, 0, avec, 4);
    verifier("aircraft already brought back (3rd press) -> refused", ag_annuler(mgr, avion, carte) == 0 && intact(4, 4));
    preparer(2, 3, 0, 0, 0, lancement, 4);
    memcpy(autre, avion, sizeof avion); U32(autre, 0x8c) = 42; veh_courant = autre;
    verifier("aircraft other than the crane one -> refused", ag_annuler(mgr, autre, carte) == 0 && intact(3, 4));

    printf("ag_fin\n");
    {
        void *tab[3]; unsigned char vcont[0x80];
        memset(vcont, 0, sizeof vcont);
        memset(autre, 0, sizeof autre); U32(autre, 0x8c) = 7;
        tab[0] = autre; tab[1] = 0; tab[2] = avion;
        PTR(vcont, 0x50) = tab; U32(vcont, 0x58) = 3; U32(vcont, 0x5c) = 1; U32(vcont, 0x60) = 3;
        preparer(2, 4, 0, 0, 0, l, 0);
        ag_fin(mgr, vcont);
        verifier("aircraft brought back and put down, empty list -> crane freed", U32(mgr, 0x78) == AUCUN && U32(mgr, 0x88) == AUCUN);
        preparer(2, 3, 0, 0, 0, l, 0); ag_fin(mgr, vcont);
        verifier("aircraft in a normal launch -> nothing (goes to the elevator)", U32(mgr, 0x78) == 41);
        l[0] = 2; preparer(2, 4, 0, 0, 0, l, 1); ag_fin(mgr, vcont);
        verifier("return not finished (move left) -> nothing", U32(mgr, 0x78) == 41);
        preparer(2, 4, 1, 0, 0, l, 0); ag_fin(mgr, vcont);
        verifier("crane still holds the aircraft -> nothing", U32(mgr, 0x78) == 41);
        preparer(1, 4, 0, 0, 0, l, 0); ag_fin(mgr, vcont);
        verifier("storing mode -> nothing", U32(mgr, 0x78) == 41);
        preparer(2, 4, 0, 0, 0, l, 0); U32(avion, 0x8c) = 99; ag_fin(mgr, vcont);
        verifier("aircraft not found -> nothing", U32(mgr, 0x78) == 41);
        preparer(2, 4, 0, 0, 0, l, 0); U32(mgr, 0x78) = AUCUN; ag_fin(mgr, vcont);
        verifier("crane empty -> nothing", U32(mgr, 0x78) == AUCUN && U32(mgr, 0x88) == 3);
    }

    printf("full run: aircraft held, cancelled, moves played one by one\n");
    {
        void *tab[1] = { avion }; unsigned char vcont[0x80]; u32 etapes = 0;
        memset(vcont, 0, sizeof vcont);
        PTR(vcont, 0x50) = tab; U32(vcont, 0x58) = 1; U32(vcont, 0x60) = 1;
        preparer(2, 3, 1, 0, 3, retourne + 2, 4);       /* holding, heading to the lift, bay rotated */
        ag_annuler(mgr, avion, carte);
        while (U32(mgr, 0x18)) {                         /* the game plays and removes the 1st move */
            u32 g = ((u32 *)PTR(mgr, 0x08))[U32(mgr, 0x14)];
            if (g == 5) U8(mgr, 0x20) = 0;               /* set down = release */
            U32(mgr, 0x14) = anneau(U32(mgr, 0x14), 1, U32(mgr, 0x10)); U32(mgr, 0x18)--;
            ag_fin(mgr, vcont);
            if (U32(mgr, 0x78) == AUCUN) break;
            etapes++;
        }
        ag_fin(mgr, vcont);
        verifier("4 moves played, then crane freed", etapes == 3 && U32(mgr, 0x78) == AUCUN && U32(mgr, 0x18) == 0);
        verifier("the aircraft never went to the elevator (dock 4)", U32(avion, 0x220) == 4);
    }

    printf("LOGIC RESULT: %s\n", echecs ? "THERE ARE FAILURES" : "all good");
    return echecs != 0;
}

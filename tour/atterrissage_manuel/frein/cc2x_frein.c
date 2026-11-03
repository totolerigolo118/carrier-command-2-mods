/* SPDX-License-Identifier: GPL-3.0-or-later */
/*
 * cc2x_frein.dll (v15) - test plugin: wheel brake for a fixed-wing aircraft landed by hand on the carrier (and, v13, the hangar for a helicopter landed by hand;
 * v14, the recall without the map; v15, a helicopter held on the deck once its pilot has left it).
 * Built against cc2x.h of the CC2X SDK (GPL-3.0-or-later): shared under the same license, see tour/atterrissage_manuel/.
 *
 * Settings: %APPDATA%\Carrier Command 2\cc2x\frein.ini ([frein], re-read every 3 s, see frein.ini.example).
 * Everything is off by default: with brake_enabled=0 the plugin only logs what it sees (phase 1).
 *
 * An aircraft is braked (vehicle_brakes(brake, grip) each server tick) only if ALL of these hold:
 * fixed wing, human team, not attached to the carrier, dock state 0, flight state = "flight_state"
 * (1 = on the ground, -1 = ignored), at least "min_wheels" wheels in contact (0 = every wheel; 2 = the
 * two main wheels of a normal landing, nose wheel still up), within zone_m of its team's carrier
 * (height +-height_m, default 20: the deck is at about +19.8 m, so 20 is too tight, use 40), AND it has flown since the game last handled it ("armed": NO wheel in contact for
 * ~1 s). The last condition keeps the brake off a takeoff roll, even on two wheels. Never touched: AI
 * teams, attached, docking / undocking, helicopters. As soon as an aircraft stops being eligible:
 * vehicle_brakes(0, 1.0). "max_speed" (default 0 = off): no braking above that speed relative to the
 * carrier. "hold_brake" (default 0 = off): once the aircraft is parked (relative speed < 1 m/s) the brake
 * goes up to that value and stays there, so a stopped aircraft neither drifts nor takes off on its own,
 * until it is no longer eligible (the game takes it over, a recall sets dock state 5). "grace_s" (default 0 = off): after a bounce the brake is held that long
 * before being released, as long as the aircraft stays in the other conditions.
 * "hold_idle" (default 0 = off; v5): measured on 28/10, even the full hold brake does not stop the AI from
 * taking off once the pilot leaves (control mode 0, engine power 1.0: the aircraft creeps then rolls). With
 * hold_idle=1 a HELD aircraft in AI control (mode 0) gets CONTROL_POWER = 0 (engine idle) every tick; the value
 * the game had is put back as soon as that stops (pilot back, brake released, game takes it over).
 * v6 (28/10 test: at the recall the game leaves power at 0, our "put back 1.0" at that very tick made the aircraft take off and roll to
 * the end of the deck): when the game takes the aircraft over (dock state != 0, attached) nothing is put back, the game owns the engine;
 * a saved power of 0 is put back as 1.0; the engine is also given back when the session ends; and a held aircraft with hold_idle=1 is
 * kept held (brake + idle) through any loss of wheel contact while it stays in the zone and below max_speed.
 * v7 (29/10 test: at the recall the aircraft, brake released and engine at 0, rolled backwards off the deck and fell in the sea - the game
 * does not put a hand-landed aircraft in its landing process): DIAGNOSTIC, off by default. With recall_hold=1 a held aircraft is NOT
 * let go when the recall sets dock state 5 (queued, not attached, pilot gone): brake and idle engine are kept for recall_hold_s seconds
 * (default 40; with recall_release=1 everything is let go after that, like v6; with 0 it stays held) and one "RECALL" line per second
 * (then every 5 s) logs what the game asks of the aircraft (control mode, speed, target, taxi, dock state, dock vehicle, attached to,
 * flight state, waypoints, relative speed, distance to the carrier centre, wheels). If the game takes the aircraft over (dock state other
 * than 5, attached), the pilot comes back or it leaves the zone, the hold ends as in v6.
 * v8 (29/10 test of v7: the game treats the recalled aircraft as a FLYING aircraft of its landing queue, it never lands it from the deck):
 * EXPERIMENTAL, off by default (recall_force=0; the hooks are installed only if recall_force=1 when the game starts, so a plain v8 patches
 * nothing). With recall_force=1 and the v7 recall hold running, for ONE aircraft id at a time (the held, recalled, parked one) two
 * mid-function hooks in the game's carrier landing code do what the game itself does when an aircraft reaches the landing gate:
 *   H1 (0x7018ce, where the queue element of the aircraft is read): the circuit state of THAT element is seen as 1 (after the gate);
 *   H2 (0x701a3d, in the "give the runway" block): the 1000 m distance test to the gate is skipped.
 * The game then runs its own code: runway given, final approach, touch test (slow, all wheels down, free bay) and take-over (bay, joint,
 * dock state 6, push-back on rails). We write nothing in the game's memory, we only keep brake and idle engine while dock state is 5 or 1.
 * force_tries (default 3) = H2 firings at most; force_timeout_s (default 20) = forcing window; then the aircraft stays held as in v7.
 * v9 (30/10 test of v8: the hooks worked - dock state 1, runway given - but the game ABORTED the approach at every tick, wrote engine power
 * 1.0 and brake 0 each time (abort path 0x6ff0f1), and our hooks gave the runway again at the next tick: 173 grants in 5 s, the aircraft took
 * off; the tick-side cap of 3 tries was bypassed because abort and new grant happen inside ONE game tick):
 *   - the budget of grants is now counted INSIDE the hooks (g_force_budget = force_tries at the start of a forcing window, H2 decrements it,
 *     H1 stops showing circuit state 1 when it is 0);
 *   - loop breaker: after one grant, the same element back in the queue with REAL circuit state 3 (= the game aborted the approach and re-queued the
 *     aircraft) is never forced again in that window; at the end of a window one line gives the balance "GRANTS n, ABANDONS m";
 * v10 (30/10 test of v9: GRANTS 1, ABANDONS 1, no loop, no take-off. The abort is not an "angle" problem: inside 200 m of the runway middle the game
 * aborts every approach that has not COMMITTED (runway state 4) in the 400..200 m band; the commit needs gates A-E, see PLAN_prise_en_charge.md 11):
 * DIAGNOSTIC ONLY, nothing is forced more than in v9. H3 now logs the zone flag and the x/y/z offsets and no longer claims an angle; four
 * READ-ONLY probes (patch_mid hooks that change no register, flag, jump or memory) tell WHICH commit gate fails for the flagged aircraft:
 *   0x6febda = gate A/B failed (zero-length vector to the path node / lateral component < -0.08),
 *   0x6febe7 = gate C/D failed (direction dot <= 0.95 / the game's virtual check false; 0x6fe788 tells that C was passed),
 *   0x6febc0 = gate E failed (bay index out of range).
 * xmm0-xmm7: the SDK's relay for patch_mid saves the general registers and the flags but NOT the SSE registers, and the game's code keeps live
 * values in them at our sites (liveness read on the original exe: xmm0 after H1/H2, xmm4 after H3, xmm4 and xmm5 after the probes). Our hook
 * code contains no SSE instruction, but it calls VirtualQuery and the SDK, which are free to use them: every hook is therefore registered through
 * a small assembly wrapper that saves xmm0-xmm7 on the stack and restores them after the C body.
 *   - H3 (0x6ff0fb, the start of the game's abort path, READ ONLY): for the flagged aircraft it records why the game aborts - bay index
 *     (-1 = no free bay), failure flag, approach counter, offset z to the target point, runway state - and on_tick logs it with the derived cause.
 * v11 (30/10 big test of v10: aircraft parked 12 m from the runway middle, perfectly on the axis (-0.6 m / +1.7 m), bay 8 free, and none of the four probes
 * fired: the game does not even EVALUATE the commit for an aircraft inside 200 m of the runway middle. At 0x6fe467 it compares that distance with 200: below, it
 * only stores 1 in the zone byte ([ebp-0x205], 0x6fe470) and goes on at 0x6fe477, skipping the evaluation; between 200 and 400 m the evaluation (gates A-E, 0x6fe55b)
 * runs and sets runway state 4; in the final zone with state 3 the game aborts the approach at 0x6ff0f1):
 *   - H4 (0x6fe470, the displaced instruction IS the store "mov byte [ebp-0x205],1", 7 bytes, nothing in the game jumps into it): for the flagged aircraft only, while the
 *     runway state is 3 (given by H1/H2, not committed yet), we do that store ourselves and continue at 0x6fe55b: we replay the path the game takes at 200..400 m.
 *     The store is kept (value 1) so that a failed gate ends as in the v10 test (the game aborts, the aircraft goes back to its queue, our loop breaker stops there)
 *     instead of the evaluation being repeated every tick; when the commit passes the runway state becomes 4 and the game's own check skips the abort. The four v10 probes
 *     stay and say which gate fails. H4 acts at most force_tries times per window. It is a patch_mid hook like the others, so it goes through the same xmm wrapper.
 *   - ONE forcing window per recall (v10 reopened a second window 10 s after the first closed silently, with a fresh budget and a fresh loop breaker): once opened, a
 *     window can only END (gave up, timeout, aircraft no longer parked while queued, take-over, pilot back...), never restart, until the recall is over (release()).
 *     The closing is logged ("FORCE window closed for good").
 *   - runway watch (read only): once H4 has acted, one line per change of the manager's runway state (and every 5 s) with its owner slot and approach counter, a
 *     "COMMIT" line when the state becomes 4, and at the end of the window a VERDICT line that names what happened, including the "silent" cases (the game aborted but
 *     H4 never ran; H4 ran, the probes stayed silent and the game still aborted).
 * v12 (31/10, independent read of the commit code, tour/etude_atterrissage_apres_engagement/: gates B (descent slope) and C (moving towards the path node) can never
 * pass for a parked aircraft, and a commit without take-over would block the runway for good; H4 was never tried and is REMOVED):
 *   - H5, on the H4 site (0x6fe470, same 7 bytes): for the flagged aircraft only, while the runway state is 3 and the runway owner is that aircraft, it continues at the
 *     game's touch test (0x6ff20a) instead of the final-zone store. That is where the game's HELICOPTERS go: their branch of state 3 (call [vtable+0x4c] true, 0x6fe187)
 *     never commits, it reaches 0x6ff20a and, slow and on their three wheels, the take-over block 0x6ff368 (bay, joint, dock state 6, flight state 1, runway state 5,
 *     push-back path) - see PISTE_v12_comme_un_helico.md. Registers live at 0x6ff20a: ebx (the function's stack anchor, constant), edi = the landing manager,
 *     esi = the carrier (outils/verifier_sites_v12.py): H5 sets edi and esi and writes NOTHING in memory (the game stores the zone byte itself at 0x6ff23a). If the
 *     touch test fails, the game does nothing that tick and H5 may try again at the next one (at most H5_MAX_JUMPS per window); once that budget is used up the game
 *     takes its own path and aborts the approach cleanly, as measured three times. H5 refuses when no bay of the aircraft class is free.
 *   - a READ-ONLY probe at 0x6ff379 (right after the take-over block's bay call) records the bay the game got for the flagged aircraft.
 *   - success is dock state 6 AND flight state 1 AND runway state 5 (ATTACHED_TO appears with the commit or the take-over, it proves nothing alone); after the
 *     take-over the plugin lets go (as before) and FOLLOWS the aircraft, read only: dock, flight, attached, runway state, fuel, until dock state 4 (stowed).
 *   - one table of addresses per game build: the 1.5.18 exe (PE timestamp 0x6a36c177, SDK build "1.5.18-win32") and the Steam build of 28/10 (0x6ae228f3, SDK build
 *     "1.5.18-win32-6ae228f3"); the build name given by the SDK AND the PE timestamp of the running exe must both match one entry, otherwise the plugin does not load.
 * v13 (31/10, after three take-overs out of three with v12): HELICOPTERS landed by hand (Razorbill, Petrel), OFF by default (heli_recall=0: no helicopter is even looked
 * at and H6 is not installed, the plugin is exactly v12). Read in the exe (tour/atterrissage_manuel/ETUDE_v13_helicos.md): a recalled helicopter never reaches H1 (the
 * queue loop sends every helicopter to a holding point, 0x7016dd, and skips the circuit code); the game gives the runway to a helicopter in its own block (0x6fdba7,
 * manager mode 1, runway free, the FIRST helicopter of the queue) only when it is within 100 m of its first holding point, x -100 (+x = the carrier's left) and 240 m
 * behind it. Then, in the same tick, its state 3 runs the helicopters' branch: no commit, no cone test, the touch test and the take-over block (the v12 path).
 *   - H6 (0x6fdcdd, 8 bytes "mulss xmm2,xmm2 ; mulss xmm3,xmm3", inside that block): for the flagged helicopter only it continues at the grant (0x6fdcf2) instead of the
 *     100 m comparison. Nothing is written in memory; ONE grant per window (budget counted in the hook); refused when no bay of class 1 is free.
 *   - the helicopter is flagged when it is recalled (dock state 5) while it stands on the deck: every wheel touching, < 1 m/s relative to the carrier, pilot gone, not
 *     attached; one window of 10 s per recall. No brake and no engine write for helicopters. H3 and the take-over probe (read only) and the FOLLOW serve them as well.
 *   - if the game does not take it over (touch test refused, abort), the helicopter just does what a recalled helicopter does without us: it flies its own approach.
 * v14 (31/10, the modder: the aircraft should go back to the hangar by itself once he has left it): AUTOMATIC RECALL, OFF by default (auto_recall=0). Read in the exe
 * (tour/atterrissage_manuel/CONCEPTION_retour_auto.md): the map's recall order ends in ONE function of the carrier, its virtual function +0x7c (0x707330), which queues the
 * aircraft and sets dock state 5; the server calls it for the player's order as carrier->[+0x7c](server + 0x344, aircraft id) (0x7784e9 -> 0x5ebf80). With auto_recall=1
 * (and recall_force=1 with its hooks installed, recall_hold=1, brake_enabled=1) the plugin makes that same call ONCE per landing, from the server tick, for an aircraft it
 * holds, stopped, wheels down, dock state 0, not attached, whose pilot has been gone for auto_recall_s seconds (default 5) - and, with heli_recall=1 and H6, for a
 * helicopter standing on the deck. Before the call it checks that the carrier's table is the one read for this build and that its entry +0x7c is that function;
 * otherwise nothing is called. Then everything goes on as after the map's order (v12 / v13). Nothing is written in the game's memory by the plugin itself.
 * v15 (02/11 test: Albatross and Manta went to the hangar by themselves, but the Razorbill was lifted off by the game's AI 0.5 s after its pilot left it, engine power
 * 1.00, control mode 0): with heli_recall=1 (H6 installed), brake_enabled=1 and hold_idle=1, a helicopter that its PILOT has just left (control mode 1 -> other, the
 * R key included) while it stands on the deck (every wheel touching, < 1 m/s, dock state 0) is HELD like a parked aircraft since v5: engine power 0 and the hold brake
 * every tick, until the game takes it over, the pilot comes back, it leaves the zone, or its recall window ends without a take-over (then the engine is given back
 * and the game flies it as it would without us). A helicopter never piloted (the game's own) is never held; planes are exactly as in v14.
 */
#include <math.h>
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <windows.h>
#include "cc2x.h"

#define LOG(level, ...) A->log("frein", level, __VA_ARGS__)

#define TICKS_PER_S 30.0
#define CFG_PERIOD 90             /* ticks between two reads of the ini */
#define ARM_TICKS 30              /* ~1 s with a wheel off the ground = it has flown */
#define HEIGHT_M 20.0
#define STOP_SPEED 0.3            /* m/s relative to the carrier */
#define HOLD_SPEED 1.0            /* below this the "hold" brake takes over, and stays (latched) until the aircraft is released */
#define CONTACT_MIN 0.01f         /* the game's own touchdown test uses >= 0.01 */
#define MAX_TRACK 32
#define MAX_CARRIERS 8
#define MAX_WHEELS 8
#define LOG_CAP 4000
#define CHASSIS_CARRIER 0         /* e_game_object_type */
#define MODE_PILOT 1              /* CONTROL_MODE while a player pilots the aircraft (0 = its waypoints, 3 = fly to the target) */
#define SITE_LEN 6
#define SITE8_LEN 8
#define SITE_H5_LEN 7
#define SITE_CAP_LEN 9
#define FORCE_DELAY_TICKS 30      /* the recall must have been held this long (1 s) before we force anything */
#define FORCE_MAX_SPEED 1.0       /* m/s relative to the carrier: only a parked aircraft is forced */
#define H5_MAX_JUMPS 30           /* v12: touch tests H5 may ask for in one window (one per game tick, ~1 s), then the game's own path (abort) */
#define H5_MAX_REL 2.0f           /* m/s: H5 does not send an aircraft that moves faster than that to the touch test (the game's own limit is 10) */
#define BAY_CLASS_AIR 1           /* the class the take-over block asks of a bay (push 1 before call 0x5ec1e0) */
#define MAX_BAYS 64
#define FOLLOW_MAX_TICKS (300 * 30)   /* v12: follow a taken-over aircraft at most 5 min */
#define FOLLOW_AFTER_STOW (20 * 30)   /* and 20 s more once stowed, to see the fuel go up */
#define HELI_WINDOW_TICKS (10 * 30)   /* v13: a recalled helicopter's window: 10 s */
#define HELI_MAX_REL 1.0              /* v13: m/s relative to the carrier: a helicopter "stands" on the deck below that */
#define SERVER_VEHICLE_MAP 0x344      /* v14: the "world" the game passes to its find-by-id and to the carrier's dock request: server + 0x344 in both builds (0x7784e1 / 0x7785d1) */
#define CARRIER_DOCK_SLOT 0x7c        /* v14: the carrier's virtual function "dock request" (world, aircraft id) */

/* v12: image VAs of the hook sites, one entry per game build (outils/verifier_sites_v12.py checks every one in both exes, read only). In the carrier's landing
 * function the Steam build of 28/10 is the 1.5.18 code moved by +0x110. Comments give the 1.5.18 values, see PLAN_prise_en_charge.md and PISTE_v12_comme_un_helico.md. */
typedef struct {
    uint32_t stamp;               /* PE timestamp of carrier_command.exe */
    const char *build;            /* the SDK's game_build string for that exe */
    uint32_t h1, h2, h2_goto;     /* 0x7018ce queue element read; 0x701a3d "give the runway" block; 0x701a8a after its 1000 m test */
    uint32_t h3;                  /* 0x6ff0fb start of the "approach failed" path, read only */
    uint32_t pab, pcd, pe, pc;    /* v10 read-only probes: 0x6febda gates A/B failed, 0x6febe7 C/D failed, 0x6febc0 E failed, 0x6fe788 C passed */
    uint32_t h5, h5_goto;         /* 0x6fe470 the final-zone store (H5); 0x6ff20a the touch test */
    uint32_t cap;                 /* 0x6ff379 "mov [edi+0x6c],eax" right after the take-over block's bay call, read only */
    uint32_t h6, h6_goto;         /* v13: 0x6fdcdd the helicopters' 100 m test before the runway is given (H6); 0x6fdcf2 the grant */
    uint32_t carrier_vt, dock_fn; /* v14: 0xd596cc the carrier's table of virtual functions; 0x707330 its entry +0x7c, the dock request (NOT a hook: only compared, then called) */
} Sites;
static const Sites k_builds[] = {
    {0x6a36c177u, "1.5.18-win32", 0x7018ceu, 0x701a3du, 0x701a8au, 0x6ff0fbu, 0x6febdau, 0x6febe7u, 0x6febc0u, 0x6fe788u, 0x6fe470u, 0x6ff20au, 0x6ff379u, 0x6fdcddu, 0x6fdcf2u,
     0xd596ccu, 0x707330u},
    {0x6ae228f3u, "1.5.18-win32-6ae228f3", 0x7019deu, 0x701b4du, 0x701b9au, 0x6ff20bu, 0x6feceau, 0x6fecf7u, 0x6fecd0u, 0x6fe898u, 0x6fe580u, 0x6ff31au, 0x6ff489u, 0x6fddedu, 0x6fde02u,
     0xd596ecu, 0x707440u},
};
static const Sites *S = &k_builds[0];

static uint32_t exe_stamp(void) {          /* PE timestamp of the running exe (the game) */
    const uint8_t *m = (const uint8_t *)GetModuleHandleA(NULL);
    if (!m || ((const IMAGE_DOS_HEADER *)m)->e_magic != IMAGE_DOS_SIGNATURE) return 0;
    const IMAGE_NT_HEADERS32 *nt = (const IMAGE_NT_HEADERS32 *)(m + ((const IMAGE_DOS_HEADER *)m)->e_lfanew);
    return nt->Signature == IMAGE_NT_SIGNATURE ? nt->FileHeader.TimeDateStamp : 0;
}
static uint32_t (*g_exe_stamp)(void) = exe_stamp;    /* the host test points it at a fake */

typedef struct {
    int enabled, need_airborne, flight_state;   /* flight_state: required value, -1 = any */
    double height_m;                            /* half-height of the zone around the carrier centre; the deck is at ~+19.8 m */
    double max_speed;                           /* never brake above this speed relative to the carrier (m/s), 0 = no limit */
    int min_wheels;                             /* wheels in contact needed, 0 = all of them */
    int hold_idle;                              /* 1 = engine power forced to 0 on a held aircraft in AI control (mode 0) */
    int recall_hold, recall_release;            /* v7: keep a held aircraft held when the recall sets dock state 5; 1 = let go after recall_hold_ticks */
    int recall_hold_ticks;
    int recall_force, force_tries, force_timeout_ticks;   /* v8: the two hooks, see the header */
    int grace_ticks;                            /* hold the brake this long after contact is lost, 0 = release at once */
    int heli_recall;                            /* v13: 1 = a recalled helicopter standing on the deck is given the runway at once (H6, needs recall_force=1 too) */
    int auto_recall, auto_recall_ticks;         /* v14: 1 = the plugin asks the carrier's own recall once the pilot has been gone that long */
    float brake, grip;
    float hold_brake;                           /* brake once parked (relative speed < HOLD_SPEED), 0 = off; only used if > brake */
    double zone_m;
    uint32_t only_id;                           /* 0 = any eligible aircraft */
} Cfg;

typedef struct {
    uint32_t id, sig, last_beat;
    int used, seen, inzone, air_ticks, lost_ticks, armed, braking, stopped, holding, idling, idle_ticks, recall, recall_ticks;
    int force, force_ticks, force_tries, force_done, h1_seen, h2_seen, h1_logged, h3_seen, h3_logged, h3_base, gab_seen, gcd_seen, ge_seen, gab_base, gcd_base, ge_base, gcp_base, gate_logged;   /* v8, v9, v10 */
    int h5_base, h5_seen, h5r_base, h5r_seen, h5_logged, rw_state, rw_ticks, rw_logged, committed, taken;   /* v11/v12: H5 counters at the start of the window, what was logged, the runway watch */
    int cap_base, cap_seen;                     /* v12: take-over probe counter at the start of the window */
    int hwin, hwin_ticks, h6_base, h6_seen, h6r_base, h6r_seen, h6_logged;   /* v13, helicopters: window 0 none / 1 open / 2 done for this recall; H6 counters */
    int auto_ticks, auto_done;                  /* v14: ticks the automatic recall's conditions have held; 1 = already asked for this landing */
    int was_pilot;                              /* v15, helicopters: control mode was 1 (a pilot) at the previous tick; a hold starts only when that pilot leaves */
    uint32_t t_start;
    double dist, power_saved;                   /* power_saved: the game's engine power when we started to idle it */
} Track;

static const cc2x_api *A;
static char g_ini[MAX_PATH * 2];
static Cfg g_cfg, g_shown;
static int g_shown_valid;
static Track g_track[MAX_TRACK];
static uint32_t g_tick;
static int g_logged;
/* v8 hook state. The hooks run in the game's server thread, inside the carrier's landing update, like on_tick: no lock needed. */
static int g_hooks_ok;                         /* both hooks installed */
static volatile uint32_t g_force_id;           /* the aircraft the hooks may act on, 0 = none (set by on_tick only) */
static volatile int g_h1_ours;                 /* H1 saw the flagged element in this iteration: H2 may act */
static volatile uint32_t g_h1_count, g_h2_count, g_h1_real_state;
static volatile int32_t g_h1_mode, g_h1_slot;  /* the manager's mode and runway slot as H1 saw them (read only) */
static uint32_t g_fake_elem[3];                /* {id, 1, field}: what H1 shows the game instead of the real queue element */
static volatile uint32_t g_grants;                 /* v9: grants (H2 firings) in the current forcing window */
static volatile int g_force_budget;            /* v9: grants (H2 firings) still allowed in this forcing window, counted inside the hooks */
static volatile uint32_t g_h3_count, g_h3_flag, g_h3_counter;     /* H3: aborts of the flagged aircraft's approach and what the game's code had at that moment */
static volatile int32_t g_h3_bay, g_h3_state;
static volatile float g_h3_z;
static float g_h3_x, g_h3_y;                    /* v10: the lateral and vertical offsets of the aircraft to the target point, as the game had them */
static volatile uint32_t g_h3_zone;             /* v10: [ebp-0x205], the "final zone" byte (1 inside 200 m of the runway middle) */
static volatile uint32_t g_gate_ab, g_gate_cd, g_gate_e, g_gate_cpass;   /* v10 read-only probes: how often each commit gate failed / C was passed */
static volatile int g_c_ok, g_cd_was_d;         /* gate C passed in this iteration; the last C/D failure was D */
static float g_ab_vec[3];                       /* the vector slots [ebp-0x294], [ebp-0x244], [ebp-0x284] at the last A/B failure */
/* v12 H5 state, same thread as the hooks and on_tick */
static volatile uint32_t g_h5_reached, g_h5_count, g_h5_counter;   /* H5: visits of its site for the flagged aircraft / times it jumped / the game's approach counter at the last jump */
static volatile int g_h5_budget;                /* H5 jumps still allowed in this forcing window (counted inside the hook) */
static volatile int32_t g_h5_state, g_h5_why;   /* runway state seen at the last visit; why the last visit did not jump, see h5_why_text */
static float g_h5_dist, g_h5_rel;               /* at the last jump: distance to the runway middle ([ebp-0x25c]) and speed relative to the carrier from the game's frame */
static int32_t g_h5_owner, g_h5_lift, g_h5_pref, g_h5_pref_free, g_h5_free, g_h5_nw;   /* runway owner, lift owner, preferred bay, is it free, free bays, wheels */
static float g_h5_w0[3], g_h5_w4[3];            /* the two wheel fields the touch test compares (>= 0.01 and <= 0.1), wheels 0-2 */
static volatile uint32_t g_cap_count;           /* v12 read-only probe: the take-over block ran for the flagged aircraft */
static volatile int32_t g_cap_bay, g_cap_limit; /* the bay the game got there, and the limit it compares it with (out of range = no take-over) */
static volatile uintptr_t g_mgr;                /* the landing manager H5 saw: only READ afterwards (runway watch, verdict, follow), reset at each window and session */
/* v13 H6 state (helicopters), same thread */
static int g_h6_ok;                             /* H6 installed (recall_force=1 and heli_recall=1 when the game started) */
static volatile uint32_t g_h6_reached, g_h6_count;  /* H6: visits of its site for the flagged helicopter / runway grants */
static volatile int g_h6_budget, g_h6_why;      /* grants still allowed in this window (counted inside the hook); why the last visit did not act */
static volatile int32_t g_h6_free, g_h6_index;  /* at the last grant: free bays of class 1, the helicopter's place in the landing queue */
/* v14: the automatic recall. The call goes through g_dock_call (the host test points it at a fake); g_server is the server the SDK gives each tick. */
typedef void(__attribute__((thiscall)) *DockFn)(void *carrier, void *world, uint32_t id);
static void dock_call_game(uintptr_t fn, void *carrier, void *world, uint32_t id) { ((DockFn)fn)(carrier, world, id); }
static void (*g_dock_call)(uintptr_t fn, void *carrier, void *world, uint32_t id) = dock_call_game;
static void *g_server;
static uint32_t g_auto_calls;                   /* v14: carrier dock requests made by the plugin in this session */
static uint32_t g_follow_id, g_follow_ticks, g_follow_stowed;   /* v12: the aircraft followed after its take-over (read only) */
static int g_follow_sig, g_follow_lines;
static double g_follow_fuel;

static double clampd(double v, double lo, double hi) { return v < lo ? lo : v > hi ? hi : v; }

static double ini_num(const char *key, double def) {
    char buf[32], dflt[32], *c;
    snprintf(dflt, sizeof(dflt), "%g", def);
    GetPrivateProfileStringA("frein", key, dflt, buf, sizeof(buf), g_ini);
    if ((c = strchr(buf, ','))) *c = '.';        /* "1,0" typed by a French keyboard */
    return atof(buf);
}

static int cfg_same(const Cfg *a, const Cfg *b) {
    return a->enabled == b->enabled && a->need_airborne == b->need_airborne && a->flight_state == b->flight_state &&
           a->min_wheels == b->min_wheels && a->grace_ticks == b->grace_ticks && a->height_m == b->height_m &&
           a->max_speed == b->max_speed && a->hold_brake == b->hold_brake && a->hold_idle == b->hold_idle && a->recall_hold == b->recall_hold && a->recall_release == b->recall_release &&
           a->recall_hold_ticks == b->recall_hold_ticks && a->recall_force == b->recall_force && a->force_tries == b->force_tries &&
           a->force_timeout_ticks == b->force_timeout_ticks && a->brake == b->brake && a->grip == b->grip && a->zone_m == b->zone_m && a->only_id == b->only_id &&
           a->heli_recall == b->heli_recall && a->auto_recall == b->auto_recall && a->auto_recall_ticks == b->auto_recall_ticks;
}

static void read_cfg(void) {
    Cfg c;
    c.enabled = g_ini[0] && ini_num("brake_enabled", 0) != 0;
    c.brake = (float)clampd(ini_num("brake", 1.0), 0.0, 1.0);       /* the SDK documents 0..1: do not go above without the modder */
    c.grip = (float)clampd(ini_num("grip", 1.0), 0.0, 1.0);
    c.zone_m = clampd(ini_num("zone_m", 150), 10, 1000);
    c.only_id = (uint32_t)clampd(ini_num("only_id", 0), 0, 4e9);
    c.need_airborne = ini_num("need_airborne", 1) != 0;
    c.flight_state = (int)clampd(ini_num("flight_state", CC2X_FLIGHT_GROUND), -1, 2);
    c.min_wheels = (int)clampd(ini_num("min_wheels", 0), 0, MAX_WHEELS);
    c.grace_ticks = (int)(clampd(ini_num("grace_s", 0), 0, 5) * TICKS_PER_S + 0.5);
    c.height_m = clampd(ini_num("height_m", HEIGHT_M), 5, 100);
    c.max_speed = clampd(ini_num("max_speed", 0), 0, 300);
    c.hold_brake = (float)clampd(ini_num("hold_brake", 0), 0.0, 1.0);
    c.hold_idle = ini_num("hold_idle", 0) != 0;
    c.recall_hold = ini_num("recall_hold", 0) != 0;
    c.recall_release = ini_num("recall_release", 0) != 0;
    c.recall_hold_ticks = (int)(clampd(ini_num("recall_hold_s", 40), 5, 600) * TICKS_PER_S + 0.5);
    c.recall_force = ini_num("recall_force", 0) != 0;
    c.force_tries = (int)clampd(ini_num("force_tries", 3), 1, 10);
    c.force_timeout_ticks = (int)(clampd(ini_num("force_timeout_s", 20), 5, 120) * TICKS_PER_S + 0.5);
    c.heli_recall = ini_num("heli_recall", 0) != 0;
    c.auto_recall = ini_num("auto_recall", 0) != 0;
    c.auto_recall_ticks = (int)(clampd(ini_num("auto_recall_s", 5), 2, 60) * TICKS_PER_S + 0.5);
    g_cfg = c;
    if (!g_shown_valid || !cfg_same(&g_cfg, &g_shown)) {
        g_shown = g_cfg;
        g_shown_valid = 1;
        LOG(CC2X_LOG_INFO, "settings: brake_enabled=%d brake=%.2f grip=%.2f zone_m=%.0f only_id=%u need_airborne=%d flight_state=%d "
            "min_wheels=%d grace_s=%.1f height_m=%.0f max_speed=%.0f hold_brake=%.2f hold_idle=%d recall_hold=%d recall_hold_s=%.0f recall_release=%d recall_force=%d force_tries=%d force_timeout_s=%.0f hooks=%d "
            "heli_recall=%d heli_hook=%d auto_recall=%d auto_recall_s=%.0f", c.enabled, c.brake, c.grip,
            c.zone_m, c.only_id, c.need_airborne, c.flight_state, c.min_wheels, c.grace_ticks / TICKS_PER_S, c.height_m,
            c.max_speed, c.hold_brake, c.hold_idle, c.recall_hold, c.recall_hold_ticks / TICKS_PER_S, c.recall_release,
            c.recall_force, c.force_tries, c.force_timeout_ticks / TICKS_PER_S, g_hooks_ok, c.heli_recall, g_h6_ok, c.auto_recall, c.auto_recall_ticks / TICKS_PER_S);
    }
}

static Track *track_of(uint32_t id) {
    Track *free_slot = NULL;
    for (int i = 0; i < MAX_TRACK; ++i) {
        if (g_track[i].used && g_track[i].id == id) return &g_track[i];
        if (!g_track[i].used && !free_slot) free_slot = &g_track[i];
    }
    if (free_slot) { memset(free_slot, 0, sizeof(Track)); free_slot->used = 1; free_slot->id = id; }
    return free_slot;
}

static void note(int level, const char *fmt, ...) {
    char text[512];                                  /* v12: the H5 line is ~330 characters; the SDK itself allows 1024 */
    va_list ap;
    if (g_logged >= LOG_CAP && level < CC2X_LOG_WARN) return;
    if (++g_logged == LOG_CAP) LOG(CC2X_LOG_WARN, "log cap reached: only warnings from now on");
    va_start(ap, fmt);
    vsnprintf(text, sizeof(text), fmt, ap);
    va_end(ap);
    LOG(level, "%s", text);
}

static void idle_end(Track *t, void *v, const char *why) {
    if (!t->idling) return;
    t->idling = 0;
    if (!v) { note(CC2X_LOG_INFO, "id %u: IDLE ended (%s), aircraft gone", t->id, why); return; }
    double now = A->getf(v, CC2X_VEHICLE_CONTROL_POWER, 0);
    int dock = (int)A->geti(v, CC2X_VEHICLE_DOCK_STATE, 0), attached = A->geti(v, CC2X_VEHICLE_ATTACHED_TO, 0) != 0;
    int pilot = A->geti(v, CC2X_VEHICLE_CONTROL_MODE, 0) == MODE_PILOT;    /* v7: a pilot back in the seat needs the engine even if the recall left dock 5 */
    if ((dock != 0 || attached) && !pilot) {          /* v6: the game takes the aircraft over (recall = dock 5, docking...): it owns the engine, we put nothing back */
        note(CC2X_LOG_INFO, "id %u: IDLE ended (%s): the game takes over (dock %d, attached %d), engine power read %.2f and left alone, after %.1f s",
             t->id, why, dock, attached, now, t->idle_ticks / TICKS_PER_S);
        return;
    }
    double back = t->power_saved > 0.0 ? t->power_saved : 1.0;       /* v6: a saved 0 (autosave while idling) would keep the engine off: use the game's default 1.0 */
    if (now == 0.0) A->setf(v, CC2X_VEHICLE_CONTROL_POWER, 0, back);   /* ours: give it back (not if the game set another value) */
    note(CC2X_LOG_INFO, "id %u: IDLE ended (%s), engine power back to %.2f after %.1f s", t->id, why, back, t->idle_ticks / TICKS_PER_S);
}

static int readable(const void *p, size_t n);

static const char *h5_why_text(int why) {
    switch (why) {
    case 1: return "edi was not the flagged aircraft";
    case 2: return "the landing manager or the carrier was not readable";
    case 3: return "the runway state was not 3 (not given, or already taken over)";
    case 4: return "the runway owner was not this aircraft";
    case 5: return "the H5 budget of the window was used up";
    case 6: return "no free bay of the aircraft class on the carrier";
    case 7: return "the aircraft moved faster than 2 m/s relative to the carrier";
    default: return "no refusal recorded";
    }
}

static const char *h6_why_text(int why) {
    switch (why) {
    case 1: return "edi was not the landing manager of the game's frame";
    case 2: return "the landing manager or the carrier was not readable";
    case 3: return "the carrier was not in docking mode or the runway was not free";
    case 5: return "the H6 budget of the window (one grant) was used up";
    case 6: return "no free bay of class 1 on the carrier";
    default: return "no refusal recorded";
    }
}

static void follow_start(uint32_t id) {
    g_follow_id = id; g_follow_ticks = 0; g_follow_stowed = 0; g_follow_sig = -1; g_follow_lines = 0; g_follow_fuel = -1.0;
}

/* Everything the hooks recorded in this window, then ONE verdict line (v12). The runway state is read from the manager H5 saw (read only). */
static void force_balance(const Track *t, const char *why) {
    int ab = (int)g_h3_count - t->h3_base, gab = (int)g_gate_ab - t->gab_base, gcd = (int)g_gate_cd - t->gcd_base, gcp = (int)g_gate_cpass - t->gcp_base,
        ge = (int)g_gate_e - t->ge_base, h5 = (int)g_h5_count - t->h5_base, reached = (int)g_h5_reached - t->h5r_base, cap = (int)g_cap_count - t->cap_base;
    int32_t rs = -99, slot = -99;
    note(CC2X_LOG_INFO, "id %u: FORCE balance (%s): GRANTS %u, ABANDONS %d, GATES AB %d CD %d (C passed %d) E %d, H5 jumps %d (reached %d), TAKE-OVER block %d", t->id, why,
         (unsigned)g_grants, ab, gab, gcd, gcp, ge, h5, reached, cap);
    if (g_mgr && readable((void *)g_mgr, 0xe0)) { rs = *(const int32_t *)(g_mgr + 0x1c); slot = *(const int32_t *)(g_mgr + 0x5c); }
    if (!g_grants)
        note(CC2X_LOG_INFO, "id %u: VERDICT: the runway was never given (H1/H2 did not fire), nothing was forced", t->id);
    else if (cap && (g_cap_bay < 0 || g_cap_bay >= g_cap_limit))
        note(CC2X_LOG_INFO, "id %u: VERDICT: the touch test PASSED but the game found no bay for the take-over (bay %d, limit %d): it skipped the take-over block", t->id,
             (int)g_cap_bay, (int)g_cap_limit);
    else if (cap)
        note(CC2X_LOG_INFO, "id %u: VERDICT: the touch test PASSED and the game ran its take-over block (bay %d); runway state now %d, owner slot %d - success needs dock 6, "
             "flight 1, runway state 5, see the FOLLOW lines", t->id, (int)g_cap_bay, (int)rs, (int)slot);
    else if (!h5 && !reached)
        note(CC2X_LOG_INFO, "id %u: VERDICT: SILENT - H5 never ran, the game never came to 0x%x for this aircraft%s", t->id, S->h5,
             ab ? " (although it aborted the approach, see the H3 line)" : "");
    else if (!h5)
        note(CC2X_LOG_INFO, "id %u: VERDICT: H5 reached its site %d time(s) but did not act: %s", t->id, reached, h5_why_text(g_h5_why));
    else
        note(CC2X_LOG_INFO, "id %u: VERDICT: TOUCH TEST NEVER PASSED - H5 sent the aircraft to it %d time(s); last values: rel %.2f m/s (game wants <= 10), %d wheels, "
             "field +0 = %.3f %.3f %.3f (game wants >= 0.01), field +4 = %.3f %.3f %.3f (game wants <= 0.1)%s", t->id, h5, (double)g_h5_rel, (int)g_h5_nw,
             (double)g_h5_w0[0], (double)g_h5_w0[1], (double)g_h5_w0[2], (double)g_h5_w4[0], (double)g_h5_w4[1], (double)g_h5_w4[2],
             ab ? "; then the game aborted the approach (H3 line)" : "");
}

static void force_off(uint32_t id) {
    if (g_force_id != id) return;
    g_force_id = 0; g_force_budget = 0; g_h5_budget = 0;
}

static void release(Track *t, const char *why) {
    void *v = A->find(CC2X_WORLD_VEHICLES, t->id);
    idle_end(t, v, why);
    if (v) A->vehicle_brakes(v, 0.0f, 1.0f);           /* the game's own "rest" values */
    note(CC2X_LOG_INFO, "id %u: BRAKE released (%s) after %.1f s, %.0f m", t->id, why,
         (g_tick - t->t_start) / TICKS_PER_S, t->dist);
    t->braking = 0;
    t->holding = 0;
    t->recall = 0;
    t->recall_ticks = 0;
    if (t->force) force_balance(t, why);
    if (t->force && (int)g_cap_count != t->cap_base) follow_start(t->id);     /* v12: the game ran its take-over block: watch what it does with the aircraft */
    if (t->force) force_off(t->id);
    t->force = 0; t->force_ticks = 0; t->force_tries = 0; t->force_done = 0;      /* the recall is over: a new recall may open ONE new window */
}

static double vlen(const double *a, const double *b) {
    return sqrt((a[0] - b[0]) * (a[0] - b[0]) + (a[1] - b[1]) * (a[1] - b[1]) + (a[2] - b[2]) * (a[2] - b[2]));
}

static int readable(const void *p, size_t n) {
    MEMORY_BASIC_INFORMATION mbi;
    if (!p || !VirtualQuery(p, &mbi, sizeof(mbi)) || mbi.State != MEM_COMMIT) return 0;
    if (mbi.Protect & (PAGE_NOACCESS | PAGE_GUARD)) return 0;
    return (uintptr_t)p + n <= (uintptr_t)mbi.BaseAddress + mbi.RegionSize;
}

/* H1, at 0x7018ce: eax = the queue element {id, circuit state, field} the game just fetched, edi = the carrier's landing manager (the lea
 * right before is "lea ecx,[edi+0x34]"). The displaced code is "mov eax,[eax+4] ; cmp eax,5": for the flagged aircraft we hand it a copy of the
 * element whose circuit state is 1 (the game's own state after the gate), the real element is not written. */
__attribute__((used, noinline)) static void hook_h1_body(cc2x_cpu *cpu, void *user) {
    const uint32_t *el = (const uint32_t *)(uintptr_t)cpu->eax;
    (void)user;
    g_h1_ours = 0;
    if (!g_cfg.recall_force || !g_force_id || g_force_budget <= 0 || !readable(el, 12) || el[0] != g_force_id) return;
    if (g_grants > 0 && el[1] == 3) return;          /* loop breaker: re-queued with state 3 after a grant = the game aborted the approach, leave it alone */
    g_h1_real_state = el[1];
    g_h1_mode = readable((void *)(uintptr_t)cpu->edi, 0x60) ? *(const int32_t *)(uintptr_t)cpu->edi : -99;
    g_h1_slot = readable((void *)(uintptr_t)cpu->edi, 0x60) ? *(const int32_t *)((uintptr_t)cpu->edi + 0x5c) : -99;
    g_fake_elem[0] = el[0]; g_fake_elem[1] = 1; g_fake_elem[2] = el[2];
    cpu->eax = (uint32_t)(uintptr_t)g_fake_elem;
    g_h1_ours = 1;
    g_h1_count++;
}

/* H2, at 0x701a3d, inside the game's "give the runway" block: the game has just checked [edi]==1 (carrier in docking mode) and
 * [edi+0x5c]==-1 (runway free). The code that follows computes the distance to the gate and wants it < 1000 m. For the element H1 flagged
 * in this same iteration we continue after that test; the game then writes the runway owner, the runway state, takes the element out of the
 * queue and sets dock state 1 itself. The skipped code only fills scratch locals. */
__attribute__((used, noinline)) static void hook_h2_body(cc2x_cpu *cpu, void *user) {
    (void)user;
    if (!g_cfg.recall_force || !g_h1_ours || !g_force_id || g_force_budget <= 0) return;
    g_h1_ours = 0;
    if (!readable((void *)(uintptr_t)cpu->edi, 0x60) || *(const int32_t *)(uintptr_t)cpu->edi != 1 || *(const int32_t *)((uintptr_t)cpu->edi + 0x5c) != -1) return;
    cpu->jump_to = (uint32_t)A->va(S->h2_goto);
    g_force_budget--;
    g_grants++;
    g_h2_count++;
}

/* H3, at 0x6ff0fb = "mov ecx,[ebp-0x1fc]", the first instruction of the game's "approach failed" path (reached only when the bay index was -1 or the
 * failure flag was set, and the runway state was not 4). READ ONLY. At that point: eax = bay index from the call at 0x6ff0da, [ebp-0x1fc] = the
 * aircraft, [ebp-0x224] = the failure flag (angle > 0.45 rad, target point passed, or approach counter > 3600), [ebp-0x278] = the offset z of the
 * aircraft to the target point (float), edi = the manager ([edi+0x1c] runway state, [edi+0xd4] approach counter). */
__attribute__((used, noinline)) static void hook_h3_body(cc2x_cpu *cpu, void *user) {
    const uint8_t *frame = (const uint8_t *)(uintptr_t)cpu->ebp;
    void *mine;
    (void)user;
    if (!g_cfg.recall_force || !g_force_id || !readable(frame - 0x300, 0x310)) return;
    mine = A->find(CC2X_WORLD_VEHICLES, g_force_id);
    if (!mine || *(const uint32_t *)(frame - 0x1fc) != (uint32_t)(uintptr_t)mine) return;
    g_h3_zone = frame[-0x205];
    memcpy(&g_h3_x, frame - 0x2cc, 4);
    memcpy(&g_h3_y, frame - 0x270, 4);
    g_h3_bay = (int32_t)cpu->eax;
    g_h3_flag = *(const uint32_t *)(frame - 0x224);
    memcpy((void *)&g_h3_z, frame - 0x278, 4);
    if (readable((void *)(uintptr_t)cpu->edi, 0xe0)) {
        g_h3_state = *(const int32_t *)((uintptr_t)cpu->edi + 0x1c);
        g_h3_counter = *(const uint32_t *)((uintptr_t)cpu->edi + 0xd4);
    } else { g_h3_state = -99; g_h3_counter = 0; }
    g_h3_count++;
}

/* The v10 probes. READ ONLY: they change no register, no flag, no jump target and no memory of the game. Each runs only for the flagged aircraft
 * (the aircraft pointer of the game's frame, [ebp-0x1fc], equals the flagged vehicle) and only records which commit gate failed.
 * user = 1: gates A/B failed (0x6febda), 2: C/D failed (0x6febe7), 3: E failed (0x6febc0), 4: C passed (0x6fe788). */
__attribute__((used, noinline)) static void hook_probe_body(cc2x_cpu *cpu, void *user) {
    const uint8_t *frame = (const uint8_t *)(uintptr_t)cpu->ebp;
    void *mine;
    if (!g_cfg.recall_force || !g_force_id || !readable(frame - 0x300, 0x310)) return;
    mine = A->find(CC2X_WORLD_VEHICLES, g_force_id);
    if (!mine || *(const uint32_t *)(frame - 0x1fc) != (uint32_t)(uintptr_t)mine) return;
    switch ((int)(intptr_t)user) {
    case 1: memcpy(&g_ab_vec[0], frame - 0x294, 4); memcpy(&g_ab_vec[1], frame - 0x244, 4); memcpy(&g_ab_vec[2], frame - 0x284, 4);
            g_c_ok = 0; g_gate_ab++; break;
    case 2: g_cd_was_d = g_c_ok; g_c_ok = 0; g_gate_cd++; break;
    case 3: g_c_ok = 0; g_gate_e++; break;
    case 4: g_c_ok = 1; g_gate_cpass++; break;
    default: break;
    }
}

/* Bay i of the carrier is free for the class asked, as the game's own search 0x5ec1e0 decides: occupant [bays + i*0x70 + 0x64] == 0 and the class stored in the
 * carrier model's node table ([model+0xe0] entries of 64 bytes, [model+0xe4] count, [model+0xe8] first index, class at +0x3c) equals 'cls'. Read only. */
static int bay_free(const uint8_t *ship, uint32_t i, uint32_t cls) {
    const uint8_t *bays = (const uint8_t *)(uintptr_t)*(const uint32_t *)(ship + 0x154), *model = (const uint8_t *)(uintptr_t)*(const uint32_t *)(ship + 0x88), *tab;
    uint32_t cnt, first, k;
    if (!readable(bays + i * 0x70, 0x70) || !readable(model, 0xf0) || *(const uint32_t *)(bays + i * 0x70 + 0x64) != 0) return 0;
    tab = (const uint8_t *)(uintptr_t)*(const uint32_t *)(model + 0xe0); cnt = *(const uint32_t *)(model + 0xe4); first = *(const uint32_t *)(model + 0xe8);
    k = first + i;
    if (k >= cnt) k -= cnt;
    return readable(tab + (size_t)k * 64, 64) && *(const uint32_t *)(tab + (size_t)k * 64 + 0x3c) == cls;
}

/* H5 (v12), at the H4 site 0x6fe470 = "mov byte [ebp-0x205],1": the game's branch for an aircraft less than 200 m from the runway middle (the "final zone"). There the
 * game stores the zone byte and goes on to abort every approach that has not committed. For the flagged aircraft only, while the runway state is 3 and the runway owner
 * ([manager+0x5c]) is that aircraft, H5 continues at the game's touch test 0x6ff20a, the point the game's helicopters reach from their own branch of state 3: relative
 * speed <= 10 m/s, every wheel touching (field +0 >= 0.01) with field +4 <= 0.1, then the take-over block (bay, joint, dock 6, flight 1, runway state 5, push-back).
 * Registers live at 0x6ff20a: ebx (unchanged), edi = the manager, esi = the carrier; here edi is the aircraft, so H5 sets edi = [ebp-0x204] and esi = [ebp-0x200].
 * Nothing is written in the game's memory (0x6ff23a stores the zone byte itself). Before jumping H5 reads (only) what it logs and what could make the jump useless:
 * a free bay of the aircraft class (as the game's search 0x5ec1e0), the speed relative to the carrier from the game's own frame (P = [ebp-0x2e4], [ebp-0x234],
 * [ebp-0x23c], Q = [ebp-0x2dc], [ebp-0x2d4], [ebp-0x2a4], the vectors the touch test subtracts), the wheels' two fields. If any check fails it changes nothing:
 * the relay runs the displaced store and the game goes on as it would without us (abort, as measured three times). */
__attribute__((used, noinline)) static void hook_h5_body(cc2x_cpu *cpu, void *user) {
    const uint8_t *frame = (const uint8_t *)(uintptr_t)cpu->ebp, *mgr, *ship, *plane, *wh;
    void *mine;
    float p[3], q[3];
    uint32_t nbays, nw;
    (void)user;
    if (!g_cfg.recall_force || !g_force_id || !readable(frame - 0x300, 0x310)) return;
    mine = A->find(CC2X_WORLD_VEHICLES, g_force_id);
    if (!mine || *(const uint32_t *)(frame - 0x1fc) != (uint32_t)(uintptr_t)mine) return;
    g_h5_reached++;
    plane = (const uint8_t *)mine;
    mgr = (const uint8_t *)(uintptr_t)*(const uint32_t *)(frame - 0x204);
    ship = (const uint8_t *)(uintptr_t)*(const uint32_t *)(frame - 0x200);
    g_h5_state = readable(mgr, 0xe0) ? *(const int32_t *)(mgr + 0x1c) : -99;
    if (cpu->edi != (uint32_t)(uintptr_t)mine) { g_h5_why = 1; return; }
    if (g_h5_state == -99 || !readable(ship, 0x160) || !readable(plane, 0x1a0)) { g_h5_why = 2; return; }
    if (g_h5_state != 3) { g_h5_why = 3; return; }
    g_h5_owner = *(const int32_t *)(mgr + 0x5c);
    if ((uint32_t)g_h5_owner != g_force_id) { g_h5_why = 4; return; }
    if (g_h5_budget <= 0) { g_h5_why = 5; return; }
    nbays = *(const uint32_t *)(ship + 0x158);
    if (nbays > MAX_BAYS) nbays = MAX_BAYS;
    g_h5_pref = plane[0x188];
    g_h5_pref_free = (uint32_t)g_h5_pref < nbays && bay_free(ship, (uint32_t)g_h5_pref, BAY_CLASS_AIR);
    g_h5_free = 0;
    for (uint32_t i = 0; i < nbays; ++i) g_h5_free += bay_free(ship, i, BAY_CLASS_AIR);
    if (!g_h5_free) { g_h5_why = 6; return; }
    memcpy(&p[0], frame - 0x2e4, 4); memcpy(&p[1], frame - 0x234, 4); memcpy(&p[2], frame - 0x23c, 4);
    memcpy(&q[0], frame - 0x2dc, 4); memcpy(&q[1], frame - 0x2d4, 4); memcpy(&q[2], frame - 0x2a4, 4);
    g_h5_rel = sqrtf((p[0] - q[0]) * (p[0] - q[0]) + (p[1] - q[1]) * (p[1] - q[1]) + (p[2] - q[2]) * (p[2] - q[2]));
    if (!(g_h5_rel <= H5_MAX_REL)) { g_h5_why = 7; return; }
    nw = *(const uint32_t *)(plane + 0xb0);
    wh = (const uint8_t *)(uintptr_t)*(const uint32_t *)(plane + 0xac);
    g_h5_nw = (int32_t)nw;
    for (uint32_t i = 0; i < 3; ++i) {
        g_h5_w0[i] = g_h5_w4[i] = -1.0f;
        if (i < nw && readable(wh + i * 0x70, 8)) { memcpy(&g_h5_w0[i], wh + i * 0x70, 4); memcpy(&g_h5_w4[i], wh + i * 0x70 + 4, 4); }
    }
    memcpy(&g_h5_dist, frame - 0x25c, 4);
    g_h5_counter = *(const uint32_t *)(mgr + 0xd4);
    g_h5_lift = *(const int32_t *)(mgr + 0x58);
    g_mgr = (uintptr_t)mgr;
    cpu->edi = (uint32_t)(uintptr_t)mgr;
    cpu->esi = (uint32_t)(uintptr_t)ship;
    cpu->jump_to = (uint32_t)A->va(S->h5_goto);
    g_h5_budget--;
    g_h5_count++;
}

/* Take-over probe (v12), at 0x6ff379 = "mov [edi+0x6c],eax ; mov ecx,[esi+0x88]", right after the take-over block's call to the bay search. READ ONLY: no register,
 * flag, jump or memory is changed. For the flagged aircraft ([ebp-0x1fc]) it records the bay the game got (eax) and the limit it is compared with next
 * ([[esi+0x88]+0xec]; out of range = the game skips the take-over). */
__attribute__((used, noinline)) static void hook_cap_body(cc2x_cpu *cpu, void *user) {
    const uint8_t *frame = (const uint8_t *)(uintptr_t)cpu->ebp, *model;
    void *mine;
    (void)user;
    if (!g_cfg.recall_force || !g_force_id || !readable(frame - 0x300, 0x310)) return;
    mine = A->find(CC2X_WORLD_VEHICLES, g_force_id);
    if (!mine || *(const uint32_t *)(frame - 0x1fc) != (uint32_t)(uintptr_t)mine) return;
    g_cap_bay = (int32_t)cpu->eax;
    model = readable((void *)(uintptr_t)cpu->esi, 0x90) ? (const uint8_t *)(uintptr_t)*(const uint32_t *)((uintptr_t)cpu->esi + 0x88) : NULL;
    g_cap_limit = model && readable(model, 0xf0) ? *(const int32_t *)(model + 0xec) : -1;
    g_cap_count++;
}

/* H6 (v13), at 0x6fdcdd = "mulss xmm2,xmm2 ; mulss xmm3,xmm3", in the game's block that gives the runway to a HELICOPTER (manager mode 1, runway free, the first helicopter
 * of the landing queue, 0x6fdba7). The game has just computed where that helicopter is against its first holding point (x -100, z -240 in the carrier's frame) and wants it
 * within 100 m (squared distance < 10000 at 0x6fdce9); [ebp-0x270] = the helicopter, [ebp-0x278] = its place in the queue, edi = the manager, [ebp-0x200] = the carrier.
 * For the flagged helicopter only, H6 continues at 0x6fdcf2, the grant itself: the game writes the runway owner, runway state 3, approach counter 0, lowers the gear, sets dock
 * state 1 and takes the helicopter out of the queue; in the same tick its state 3 runs the helicopters' branch (0x6fe198) and, for a helicopter standing slowly on its wheels,
 * the touch test and the take-over block, as for every helicopter the game lands. Skipped: the two squares, the sum and the comparison (xmm2 and xmm3 are written again before
 * they are read, outils/verifier_sites_v13.py). Nothing is written in memory. ONE grant per window (budget counted here); refused when no bay of class 1 is free. */
__attribute__((used, noinline)) static void hook_h6_body(cc2x_cpu *cpu, void *user) {
    const uint8_t *frame = (const uint8_t *)(uintptr_t)cpu->ebp, *mgr = (const uint8_t *)(uintptr_t)cpu->edi, *ship;
    void *mine;
    uint32_t nbays;
    (void)user;
    if (!g_cfg.recall_force || !g_cfg.heli_recall || !g_force_id || !readable(frame - 0x300, 0x310)) return;
    mine = A->find(CC2X_WORLD_VEHICLES, g_force_id);
    if (!mine || *(const uint32_t *)(frame - 0x270) != (uint32_t)(uintptr_t)mine) return;
    g_h6_reached++;
    if (cpu->edi != *(const uint32_t *)(frame - 0x204)) { g_h6_why = 1; return; }
    ship = (const uint8_t *)(uintptr_t)*(const uint32_t *)(frame - 0x200);
    if (!readable(mgr, 0xe0) || !readable(ship, 0x160)) { g_h6_why = 2; return; }
    if (*(const int32_t *)mgr != 1 || *(const int32_t *)(mgr + 0x5c) != -1) { g_h6_why = 3; return; }
    if (g_h6_budget <= 0) { g_h6_why = 5; return; }
    nbays = *(const uint32_t *)(ship + 0x158);
    if (nbays > MAX_BAYS) nbays = MAX_BAYS;
    g_h6_free = 0;
    for (uint32_t i = 0; i < nbays; ++i) g_h6_free += bay_free(ship, i, BAY_CLASS_AIR);
    if (!g_h6_free) { g_h6_why = 6; return; }
    g_h6_index = *(const int32_t *)(frame - 0x278);
    g_mgr = (uintptr_t)mgr;
    cpu->jump_to = (uint32_t)A->va(S->h6_goto);
    g_h6_budget--;
    g_h6_count++;
}

/* Assembly wrappers: what the SDK's relay calls (cdecl, cpu and user on the stack). They keep xmm0-xmm7 exact around the C body. */
#define XMM_WRAP(NAME, BODY)                                                                                                       \
    __attribute__((naked, used)) static void NAME(cc2x_cpu *cpu, void *user) {                                                    \
        __asm__("subl $0x80, %esp\n\t"                                                                                             \
                "movups %xmm0, 0x00(%esp)\n\t" "movups %xmm1, 0x10(%esp)\n\t" "movups %xmm2, 0x20(%esp)\n\t" "movups %xmm3, 0x30(%esp)\n\t" \
                "movups %xmm4, 0x40(%esp)\n\t" "movups %xmm5, 0x50(%esp)\n\t" "movups %xmm6, 0x60(%esp)\n\t" "movups %xmm7, 0x70(%esp)\n\t" \
                "pushl 0x88(%esp)\n\t" "pushl 0x88(%esp)\n\t"                                                                      \
                "call _" #BODY "\n\t"                                                                                              \
                "addl $8, %esp\n\t"                                                                                                \
                "movups 0x00(%esp), %xmm0\n\t" "movups 0x10(%esp), %xmm1\n\t" "movups 0x20(%esp), %xmm2\n\t" "movups 0x30(%esp), %xmm3\n\t" \
                "movups 0x40(%esp), %xmm4\n\t" "movups 0x50(%esp), %xmm5\n\t" "movups 0x60(%esp), %xmm6\n\t" "movups 0x70(%esp), %xmm7\n\t" \
                "addl $0x80, %esp\n\t"                                                                                             \
                "ret\n\t");                                                                                                        \
    }
XMM_WRAP(hook_h1, hook_h1_body)
XMM_WRAP(hook_h2, hook_h2_body)
XMM_WRAP(hook_h3, hook_h3_body)
XMM_WRAP(hook_probe, hook_probe_body)
XMM_WRAP(hook_h5, hook_h5_body)
XMM_WRAP(hook_cap, hook_cap_body)
XMM_WRAP(hook_h6, hook_h6_body)

static const uint8_t k_h6_bytes[SITE8_LEN] = {0xf3, 0x0f, 0x59, 0xd2, 0xf3, 0x0f, 0x59, 0xdb};    /* mulss xmm2,xmm2 ; mulss xmm3,xmm3 */
static const uint8_t k_h5_bytes[SITE_H5_LEN] = {0xc6, 0x85, 0xfb, 0xfd, 0xff, 0xff, 0x01};      /* mov byte [ebp-0x205],1 */
static const uint8_t k_cap_bytes[SITE_CAP_LEN] = {0x89, 0x47, 0x6c, 0x8b, 0x8e, 0x88, 0x00, 0x00, 0x00};   /* mov [edi+0x6c],eax ; mov ecx,[esi+0x88] */
static const uint8_t k_p8_bytes[SITE8_LEN] = {0xf3, 0x0f, 0x10, 0x8d, 0xa4, 0xfd, 0xff, 0xff};     /* movss xmm1,[ebp-0x25c] (the three failure join points) */
static const uint8_t k_pc_bytes[SITE_LEN] = {0x8b, 0x8d, 0xb4, 0xfd, 0xff, 0xff};                  /* mov ecx,[ebp-0x24c] */
static const uint8_t k_h1_bytes[SITE_LEN] = {0x8b, 0x40, 0x04, 0x83, 0xf8, 0x05};     /* mov eax,[eax+4] ; cmp eax,5 */
static const uint8_t k_h2_bytes[SITE_LEN] = {0x8d, 0x85, 0x28, 0xfd, 0xff, 0xff};     /* lea eax,[ebp-0x2d8] */
static const uint8_t k_h3_bytes[SITE_LEN] = {0x8b, 0x8d, 0x04, 0xfe, 0xff, 0xff};     /* mov ecx,[ebp-0x1fc] */

static int install_hooks(const cc2x_api *a, int with_h6) {
    if (!a->patch_begin || !a->patch_mid || !a->patch_commit || !a->va) return 0;
    a->patch_begin("frein");
    if (!a->patch_mid(S->h1, SITE_LEN, k_h1_bytes, hook_h1, NULL) || !a->patch_mid(S->h2, SITE_LEN, k_h2_bytes, hook_h2, NULL) ||
        !a->patch_mid(S->h3, SITE_LEN, k_h3_bytes, hook_h3, NULL) ||
        !a->patch_mid(S->pab, SITE8_LEN, k_p8_bytes, hook_probe, (void *)(intptr_t)1) || !a->patch_mid(S->pcd, SITE8_LEN, k_p8_bytes, hook_probe, (void *)(intptr_t)2) ||
        !a->patch_mid(S->pe, SITE8_LEN, k_p8_bytes, hook_probe, (void *)(intptr_t)3) || !a->patch_mid(S->pc, SITE_LEN, k_pc_bytes, hook_probe, (void *)(intptr_t)4) ||
        !a->patch_mid(S->h5, SITE_H5_LEN, k_h5_bytes, hook_h5, NULL) || !a->patch_mid(S->cap, SITE_CAP_LEN, k_cap_bytes, hook_cap, NULL) ||
        (with_h6 && !a->patch_mid(S->h6, SITE8_LEN, k_h6_bytes, hook_h6, NULL))) {
        if (a->patch_abort) a->patch_abort();
        return 0;
    }
    return a->patch_commit() != 0;
}

/* v14: ask the carrier's own dock request for this aircraft: the very call the server makes for the map's recall order (0x5ebf80: carrier->[+0x7c](server + 0x344, id)).
 * From on_tick only, at most once per landing (auto_done), and only if the carrier's table and its entry +0x7c are exactly those read for this build. */
static void auto_recall_try(Track *t, void *v, void *carrier, const char *what) {
    uintptr_t want_vt = A->va(S->carrier_vt), want_fn = A->va(S->dock_fn), vt = 0, fn = 0;
    int dock;
    t->auto_done = 1;
    if (!carrier || !readable(carrier, 4) || !g_server || !readable(g_server, SERVER_VEHICLE_MAP + 0x10)) {
        note(CC2X_LOG_WARN, "id %u: AUTO RECALL not asked: %s", t->id, !carrier ? "no carrier of its team" : "the carrier or the server is not readable");
        return;
    }
    vt = *(const uint32_t *)carrier;
    if (vt == want_vt && readable((const void *)vt, CARRIER_DOCK_SLOT + 4)) fn = *(const uint32_t *)(vt + CARRIER_DOCK_SLOT);
    if (vt != want_vt || fn != want_fn) {
        note(CC2X_LOG_WARN, "id %u: AUTO RECALL not asked: the carrier's table 0x%x (entry +0x7c 0x%x) is not the one read for this build (0x%x, 0x%x)", t->id,
             (unsigned)vt, (unsigned)fn, (unsigned)want_vt, (unsigned)want_fn);
        return;
    }
    g_auto_calls++;
    g_dock_call(fn, carrier, (uint8_t *)g_server + SERVER_VEHICLE_MAP, t->id);
    dock = (int)A->geti(v, CC2X_VEHICLE_DOCK_STATE, 0);
    note(CC2X_LOG_INFO, "id %u: AUTO RECALL: %s, pilot gone %.0f s: asked the carrier's own dock request (as for the map's recall order) -> dock %d%s", t->id, what,
         g_cfg.auto_recall_ticks / TICKS_PER_S, dock, dock == CC2X_DOCK_QUEUED ? " (queued: the usual recall follows)" : " (the game did not queue it; not asked again)");
}

/* v14: the countdown of the automatic recall, shared by aircraft and helicopters. 'ok' = every condition holds this tick. */
static void auto_recall_tick(Track *t, void *v, void *carrier, int ok, const char *what, const char *why_not) {
    if (ok) {
        if (t->auto_ticks == 0)
            note(CC2X_LOG_INFO, "id %u: AUTO RECALL armed (%s, pilot gone): the carrier is asked in %.0f s unless the pilot comes back", t->id, what, g_cfg.auto_recall_ticks / TICKS_PER_S);
        if (++t->auto_ticks >= g_cfg.auto_recall_ticks) auto_recall_try(t, v, carrier, what);
    } else if (t->auto_ticks) {
        if (!t->auto_done) note(CC2X_LOG_INFO, "id %u: AUTO RECALL cancelled (%s)", t->id, why_not);
        t->auto_ticks = 0;
    }
}

static void check_aircraft(void *v, const cc2x_body *cb, int have_carrier, void *carrier) {
    uint32_t id = (uint32_t)A->geti(v, CC2X_VEHICLE_ID, 0);
    Track *t = track_of(id);
    cc2x_body b;
    if (!t || !A->body_get(v, &b)) return;
    t->seen = 1;

    int nw = A->count(v, CC2X_VEHICLE_WHEELS), touching = 0, mask = 0;
    float cmin = 1e9f;
    if (nw > MAX_WHEELS) nw = MAX_WHEELS;
    for (int i = 0; i < nw; ++i) {
        float c = (float)A->getf(v, CC2X_VEHICLE_WHEEL_CONTACT, i);
        if (c < cmin) cmin = c;
        if (c > CONTACT_MIN) { touching++; mask |= 1 << i; }
    }
    int need = (g_cfg.min_wheels <= 0 || g_cfg.min_wheels > nw) ? nw : g_cfg.min_wheels;
    int contact = nw > 0 && touching >= need;           /* enough wheels on the deck to brake */
    int attached = A->geti(v, CC2X_VEHICLE_ATTACHED_TO, 0) != 0;
    int dock = (int)A->geti(v, CC2X_VEHICLE_DOCK_STATE, 0);
    int flight = (int)A->geti(v, CC2X_VEHICLE_FLIGHT_STATE, 0);

    if (touching == 0) { if (t->air_ticks < 1 << 20) t->air_ticks++; if (t->air_ticks >= ARM_TICKS) t->armed = 1; }
    else t->air_ticks = 0;                              /* armed = no wheel at all on anything for ~1 s: a takeoff rotation never arms */
    if (attached || dock != 0) t->armed = 0;           /* the game handles it: it must fly again to be braked */
    if (contact) t->lost_ticks = 0;
    else if (t->lost_ticks < 1 << 20) t->lost_ticks++;

    double dx = b.pos[0] - cb->pos[0], dz = b.pos[2] - cb->pos[2], dy = b.pos[1] - cb->pos[1];
    double dist = sqrt(dx * dx + dz * dz);
    int inzone = have_carrier && dist <= g_cfg.zone_m && fabs(dy) <= g_cfg.height_m;
    double vrel = have_carrier ? vlen(b.vel, cb->vel) : 0.0;
    int base = inzone && !attached && dock == 0 && (g_cfg.flight_state < 0 || flight == g_cfg.flight_state) &&
               (!g_cfg.need_airborne || t->armed) && (!g_cfg.only_id || g_cfg.only_id == id) &&
               (g_cfg.max_speed <= 0 || vrel <= g_cfg.max_speed);      /* too fast: a hard brake would tip it, let it roll */
    int eligible = base && contact;
    /* bounce: keep the brake on for a moment; v6: a parked aircraft kept idle (hold_idle) stays held whatever the contact, as long as it stays in the
     * other conditions (zone, speed, no dock state): letting go on a lost wheel gave it full power half airborne in the 28/10 test */
    int mode = (int)A->geti(v, CC2X_VEHICLE_CONTROL_MODE, 0), taxi = (int)A->geti(v, CC2X_VEHICLE_CONTROL_TAXI, 0);
    int nwp = A->count(v, CC2X_VEHICLE_WAYPOINTS);
    /* v7 diagnostic: the recall (dock state 5, not attached, pilot gone) does not let go of an aircraft we hold, for recall_hold_ticks */
    int recall = g_cfg.recall_hold && t->braking && t->holding && inzone && (dock == CC2X_DOCK_QUEUED || (g_cfg.recall_force && g_hooks_ok && dock == CC2X_DOCK_DOCKING && t->force)) && !attached && mode != MODE_PILOT &&
                 (!g_cfg.only_id || g_cfg.only_id == id) && !(g_cfg.recall_release && t->recall_ticks >= g_cfg.recall_hold_ticks);
    int hold = (base && t->braking && (t->lost_ticks <= g_cfg.grace_ticks || (t->holding && g_cfg.hold_idle))) || recall;
    uint32_t sig = (uint32_t)(flight & 3) | (uint32_t)(dock & 7) << 2 | (uint32_t)attached << 5 | (uint32_t)(mode & 7) << 6 |
                   (uint32_t)(taxi & 1) << 9 | (uint32_t)mask << 10 | (uint32_t)(nwp > 7 ? 7 : nwp) << 18 | (uint32_t)t->armed << 21 |
                   (uint32_t)eligible << 22 | (uint32_t)inzone << 23 | (uint32_t)t->braking << 24 | (uint32_t)t->idling << 25 | (uint32_t)t->recall << 26;
    if (inzone && (sig != t->sig || !t->inzone || (contact && g_tick - t->last_beat >= (uint32_t)TICKS_PER_S))) {
        note(CC2X_LOG_INFO, "id %u t=%.1f: flight=%d dock=%d attached=%d mode=%d taxi=%d power=%.2f wp=%d wheels=%d/%d(min %.2f) "
             "speed=%.1f rel=%.1f dist=%.0f dy=%.1f armed=%d eligible=%d brk=%d", id, g_tick / TICKS_PER_S, flight, dock, attached, mode,
             taxi, A->getf(v, CC2X_VEHICLE_CONTROL_POWER, 0), nwp, touching, nw, cmin, vlen(b.vel, (double[3]){0, 0, 0}), vrel,
             dist, dy, t->armed, eligible, t->braking);
        t->sig = sig;
        t->last_beat = g_tick;
    } else if (!inzone && t->inzone) {
        note(CC2X_LOG_INFO, "id %u: left the zone (dist %.0f, dy %.1f)", id, dist, dy);
    }
    t->inzone = inzone;

    if (g_cfg.enabled && (eligible || hold)) {
        if (!t->braking) {
            t->braking = 1; t->stopped = 0; t->holding = 0; t->t_start = g_tick; t->dist = 0; t->auto_ticks = 0; t->auto_done = 0;   /* v14: a new landing may be recalled once */
            note(CC2X_LOG_INFO, "id %u: BRAKE start (brake %.2f grip %.2f) rel speed %.1f m/s, %.0f m from the carrier centre",
                 id, g_cfg.brake, g_cfg.grip, vrel, dist);
        }
        float b_now = g_cfg.brake;
        if (g_cfg.hold_brake > g_cfg.brake && (t->holding || vrel < HOLD_SPEED)) {      /* parked on the deck: hold it, latched */
            if (!t->holding) note(CC2X_LOG_INFO, "id %u: HOLD (brake %.2f) rel speed %.2f m/s", id, g_cfg.hold_brake, vrel);
            t->holding = 1;
            b_now = g_cfg.hold_brake;
        }
        double p = A->getf(v, CC2X_VEHICLE_CONTROL_POWER, 0);      /* read before any write of ours */
        A->vehicle_brakes(v, b_now, g_cfg.grip);
        if (t->holding && g_cfg.hold_idle && (mode == 0 || recall)) {      /* parked, pilot gone, the AI in control (or recalled, v7): no engine, it must not take off */
            if (!t->idling) {
                t->idling = 1; t->idle_ticks = 0; t->power_saved = p;
                note(CC2X_LOG_INFO, "id %u: IDLE (AI in control, engine power %.2f -> 0)", id, p);
            } else if (t->idle_ticks == (int)TICKS_PER_S || t->idle_ticks == (int)(10 * TICKS_PER_S)) {
                note(CC2X_LOG_INFO, "id %u: IDLE check after %.0f s: power read %.2f before our write (0 = the game leaves it)", id,
                     t->idle_ticks / TICKS_PER_S, p);
            }
            A->setf(v, CC2X_VEHICLE_CONTROL_POWER, 0, 0.0);
            t->idle_ticks++;
        } else {
            idle_end(t, v, mode != 0 ? "no longer in AI control" : "no longer held");
        }
        if (recall) {
            if (!t->recall) {
                t->recall = 1; t->recall_ticks = 0;
                note(CC2X_LOG_INFO, "id %u: RECALL start (dock %d, mode %d, wp %d): brake kept at %.2f and engine kept at 0 for %.0f s, then %s", id,
                     dock, mode, nwp, b_now, g_cfg.recall_hold_ticks / TICKS_PER_S,
                     g_cfg.recall_release ? "everything is let go (v6 behaviour)" : "still held (recall_release=0)");
            }
            if (t->recall_ticks % (int)TICKS_PER_S == 0 && (t->recall_ticks < g_cfg.recall_hold_ticks || t->recall_ticks % (int)(5 * TICKS_PER_S) == 0))
                note(CC2X_LOG_INFO, "id %u RECALL +%.1fs: mode=%d speed_ctl=%.1f target=(%.0f,%.0f,%.0f) taxi=%d dock=%d dock_vehicle=%u attached_to=%u "
                     "flight=%d wp=%d power_read=%.2f rel=%.2f dist=%.0f wheels=%d/%d", id, t->recall_ticks / TICKS_PER_S, mode,
                     A->getf(v, CC2X_VEHICLE_CONTROL_SPEED, 0), A->getf(v, CC2X_VEHICLE_CONTROL_TARGET, 0), A->getf(v, CC2X_VEHICLE_CONTROL_TARGET, 1),
                     A->getf(v, CC2X_VEHICLE_CONTROL_TARGET, 2), taxi, dock, (unsigned)A->geti(v, CC2X_VEHICLE_DOCK_VEHICLE, 0),
                     (unsigned)A->geti(v, CC2X_VEHICLE_ATTACHED_TO, 0), flight, nwp, p, vrel, dist, touching, nw);
            t->recall_ticks++;
            if (g_cfg.recall_force && g_hooks_ok) {                  /* v8: flag this aircraft for the hooks */
                if (t->h1_seen != (int)g_h1_count && g_force_id == id && (!t->h1_logged || (int)g_h1_count - t->h1_seen >= 150)) {
                    note(CC2X_LOG_INFO, "id %u: HOOK H1 shown circuit state 1 (real element state %u, manager mode %d, runway slot %d), %u time(s)", id,
                         (unsigned)g_h1_real_state, (int)g_h1_mode, (int)g_h1_slot, (unsigned)g_h1_count);
                    t->h1_seen = (int)g_h1_count; t->h1_logged = 1;
                }
                if (t->h2_seen != (int)g_h2_count && g_force_id == id) {
                    t->force_tries += (int)g_h2_count - t->h2_seen;
                    t->h2_seen = (int)g_h2_count;
                    note(CC2X_LOG_INFO, "id %u: HOOK H2 skipped the 1000 m test: the game gives the runway itself (try %d of %d); dock=%d attached=%d", id,
                         t->force_tries, g_cfg.force_tries, dock, attached);
                }
                if (t->h3_seen != (int)g_h3_count && g_force_id == id) {
                    float z = g_h3_z;
                    if (t->h3_logged < 5)
                        note(CC2X_LOG_INFO, "id %u: HOOK H3 the game ABORTS the approach (%u so far): bay=%d fail=%u zone=%u x=%.1f y=%.1f z=%.1f counter=%u runway_state=%d causes:%s%s%s%s", id, (unsigned)g_h3_count, (int)g_h3_bay, (unsigned)g_h3_flag, (unsigned)g_h3_zone, (double)g_h3_x, (double)g_h3_y, (double)z, (unsigned)g_h3_counter, (int)g_h3_state,
                             g_h3_bay == -1 ? " no-free-bay" : "", g_h3_counter > 3600 ? " counter>3600" : "",
                             (g_h3_flag && g_h3_counter <= 3600 && z > 0.0f) ? " target-passed" : "",
                             (g_h3_zone == 1 && g_h3_state == 3) ? " not-committed-in-final-zone" : "");
                    t->h3_logged++; t->h3_seen = (int)g_h3_count;
                }
                if (g_force_id == id && t->gate_logged < 8) {
                    if (t->gab_seen != (int)g_gate_ab) {
                        float l2 = g_ab_vec[0] * g_ab_vec[0] + g_ab_vec[1] * g_ab_vec[1] + g_ab_vec[2] * g_ab_vec[2];
                        note(CC2X_LOG_INFO, "id %u: PROBE gate A/B of the commit failed (%u so far): vector slots (%.3f, %.3f, %.3f) -> %s", id, (unsigned)g_gate_ab,
                             (double)g_ab_vec[0], (double)g_ab_vec[1], (double)g_ab_vec[2], l2 < 0.25f ? "A: zero-length vector to the path node" : "B: lateral component of the unit vector < -0.08");
                        t->gab_seen = (int)g_gate_ab; t->gate_logged++;
                    }
                    if (t->gcd_seen != (int)g_gate_cd) {
                        note(CC2X_LOG_INFO, "id %u: PROBE gate C/D of the commit failed (%u so far; C passed %u times) -> %s", id, (unsigned)g_gate_cd, (unsigned)g_gate_cpass,
                             g_cd_was_d ? "D: the game's virtual check returned false (the direction dot > 0.95 was fine)" : "C: direction dot <= 0.95 (more than 18 degrees)");
                        t->gcd_seen = (int)g_gate_cd; t->gate_logged++;
                    }
                    if (t->ge_seen != (int)g_gate_e) {
                        note(CC2X_LOG_INFO, "id %u: PROBE gate E of the commit failed (%u so far): bay index out of range", id, (unsigned)g_gate_e);
                        t->ge_seen = (int)g_gate_e; t->gate_logged++;
                    }
                }
                /* v12: what H5 did (read only), up to six lines per window; a refusal is logged only until H5 has jumped once */
                if (g_force_id == id && t->h5_logged < 6) {
                    if (t->h5_seen != (int)g_h5_count) {
                        note(CC2X_LOG_INFO, "id %u: HOOK H5 sent the aircraft to the game's touch test (%u so far): %.0f m from the runway middle, runway state %d, owner %d, "
                             "approach counter %u, rel %.2f m/s, wheels %d: field +0 = %.3f %.3f %.3f, field +4 = %.3f %.3f %.3f, preferred bay %d (%s), free bays %d, lift owner %d "
                             "-> continued at 0x%x", id, (unsigned)g_h5_count, (double)g_h5_dist, (int)g_h5_state, (int)g_h5_owner, (unsigned)g_h5_counter, (double)g_h5_rel,
                             (int)g_h5_nw, (double)g_h5_w0[0], (double)g_h5_w0[1], (double)g_h5_w0[2], (double)g_h5_w4[0], (double)g_h5_w4[1], (double)g_h5_w4[2],
                             (int)g_h5_pref, g_h5_pref_free ? "free" : "not free", (int)g_h5_free, (int)g_h5_lift, S->h5_goto);
                        t->h5_seen = (int)g_h5_count; t->h5r_seen = (int)g_h5_reached; t->h5_logged++;
                    } else if (t->h5r_seen != (int)g_h5_reached && (int)g_h5_count == t->h5_base) {
                        note(CC2X_LOG_INFO, "id %u: HOOK H5 reached its site (%u visit(s) so far) but did not act: %s (runway state seen %d)", id, (unsigned)g_h5_reached,
                             h5_why_text(g_h5_why), (int)g_h5_state);
                        t->h5r_seen = (int)g_h5_reached; t->h5_logged++;
                    }
                }
                if (g_force_id == id && t->cap_seen != (int)g_cap_count) {
                    note(CC2X_LOG_INFO, "id %u: PROBE take-over block entered: the touch test PASSED, the game got bay %d (limit %d)%s", id, (int)g_cap_bay, (int)g_cap_limit,
                         g_cap_bay < 0 || g_cap_bay >= g_cap_limit ? " -> out of range, the game skips the take-over" : "");
                    t->cap_seen = (int)g_cap_count;
                }
                /* runway watch (read only), once H5 has jumped: the manager's runway state, owner slot and approach counter */
                if (g_force_id == id && (int)g_h5_count != t->h5_base && g_mgr && readable((void *)g_mgr, 0xe0)) {
                    int32_t st = *(const int32_t *)(g_mgr + 0x1c), slot = *(const int32_t *)(g_mgr + 0x5c);
                    uint32_t ctr = *(const uint32_t *)(g_mgr + 0xd4);
                    if ((!t->rw_ticks || st != t->rw_state || t->rw_ticks % (int)(5 * TICKS_PER_S) == 0) && t->rw_logged < 16) {
                        note(CC2X_LOG_INFO, "id %u: RUNWAY state %d (3 approach, 4 committed, 5 push-back on the rails), owner slot %d, approach counter %u; aircraft dock=%d attached=%d",
                             id, (int)st, (int)slot, (unsigned)ctr, dock, attached);
                        t->rw_logged++;
                    }
                    if (st == 4 && !t->committed) {
                        t->committed = 1;
                        note(CC2X_LOG_WARN, "id %u: UNEXPECTED: the game's runway state is 4 (committed): H5 never leads there; a commit without take-over keeps the runway", id);
                    }
                    t->rw_state = st; t->rw_ticks++;
                }
                /* v11: ONE window per recall. A window opens once; it then only ends (gave up, timeout, aircraft no longer parked while queued), it never restarts until the recall is over. */
                int ready = dock == CC2X_DOCK_QUEUED && t->recall_ticks >= FORCE_DELAY_TICKS && vrel < FORCE_MAX_SPEED && contact && (!g_force_id || g_force_id == id);
                int want = !t->force_done && ready;
                if (want && t->force_tries >= g_cfg.force_tries) { t->force_done = 1; want = 0; note(CC2X_LOG_INFO, "id %u: FORCE gave up after %d tries (dock %d)", id, t->force_tries, dock); force_balance(t, "gave up"); }
                if (want && t->force_ticks >= g_cfg.force_timeout_ticks) { t->force_done = 1; want = 0; note(CC2X_LOG_INFO, "id %u: FORCE timeout after %.0f s (dock %d)", id, t->force_ticks / TICKS_PER_S, dock); force_balance(t, "timeout"); }
                if (want && !t->force) {
                    t->force = 1; t->force_ticks = 0; t->h1_seen = (int)g_h1_count; t->h2_seen = (int)g_h2_count; t->h1_logged = 0; t->h3_seen = (int)g_h3_count; t->h3_logged = 0; t->h3_base = (int)g_h3_count;
                    t->gab_seen = t->gab_base = (int)g_gate_ab; t->gcd_seen = t->gcd_base = (int)g_gate_cd; t->ge_seen = t->ge_base = (int)g_gate_e; t->gcp_base = (int)g_gate_cpass; t->gate_logged = 0;
                    t->h5_base = t->h5_seen = (int)g_h5_count; t->h5r_base = t->h5r_seen = (int)g_h5_reached; t->h5_logged = 0; t->rw_state = t->rw_ticks = t->rw_logged = t->committed = 0;
                    t->cap_base = t->cap_seen = (int)g_cap_count;
                    g_force_budget = g_cfg.force_tries; g_h5_budget = H5_MAX_JUMPS; g_grants = 0; g_mgr = 0; g_h5_why = 0;
                    note(CC2X_LOG_INFO, "id %u: FORCE start (recall held %.1f s, dock %d, rel %.2f m/s): hooks H1/H2/H5 armed for this aircraft, tries 0 of %d, window %.0f s, the only window of this recall",
                         id, t->recall_ticks / TICKS_PER_S, dock, vrel, g_cfg.force_tries, g_cfg.force_timeout_ticks / TICKS_PER_S);
                }
                if (want) { g_force_id = id; t->force_ticks++; }
                else if (g_force_id == id && dock != CC2X_DOCK_DOCKING) force_off(id);
                if (!want && dock == CC2X_DOCK_QUEUED && t->force) {
                    if (!t->force_done) {          /* the window was open and the aircraft is no longer parked: it ends for good (v10 let a second one open 10 s later with a fresh budget) */
                        t->force_done = 1;
                        note(CC2X_LOG_INFO, "id %u: FORCE window closed for good (aircraft not parked any more: rel %.2f m/s, wheels in contact %d, recall held %.1f s); no other window for this recall",
                             id, vrel, contact, t->recall_ticks / TICKS_PER_S);
                        force_balance(t, "window closed");
                    }
                    t->force = 0;
                }
            }
        }
        t->dist += vrel / TICKS_PER_S;
        if (!t->stopped && vrel < STOP_SPEED) {
            t->stopped = 1;
            note(CC2X_LOG_INFO, "id %u: STOPPED after %.1f s, %.0f m on the deck", id, (g_tick - t->t_start) / TICKS_PER_S, t->dist);
        }
        /* v14: the automatic recall of a held, stopped aircraft whose pilot is gone (needs the hooks: without them the game would treat it as a flying aircraft) */
        auto_recall_tick(t, v, have_carrier ? carrier : NULL,
                         g_cfg.auto_recall && g_cfg.recall_hold && g_cfg.recall_force && g_hooks_ok && t->holding && t->stopped && contact && dock == 0 && !attached &&
                         mode != MODE_PILOT && vrel < FORCE_MAX_SPEED && !g_force_id && !t->auto_done && (!g_cfg.only_id || g_cfg.only_id == id),
                         "held and stopped", !g_cfg.auto_recall ? "auto_recall=0" : mode == MODE_PILOT ? "pilot back" : dock != 0 ? "recalled already, or docking" :
                         g_force_id ? "another aircraft is being recalled" : "no longer held and stopped");
    } else if (t->braking) {
        if (t->force) force_off(id);
        if (t->recall) note(CC2X_LOG_INFO, "id %u: RECALL ended after %.1f s (dock %d, attached %d, mode %d)", id, t->recall_ticks / TICKS_PER_S, dock, attached, mode);
        release(t, g_cfg.enabled ? "no longer eligible" : "brake_enabled=0");
    }
}

/* v13: where a body stands in the carrier's frame (x across, +x = the carrier's left; z along the deck, + = forward), metres, from the carrier's orientation. For the log only:
 * the game measures from its model's origin, which may differ a little from the body's (the runway nodes of the model: z -68 rear end, +7 middle, +82 front end). */
static void deck_xz(const cc2x_body *cb, const cc2x_body *b, double *x, double *z) {
    double d[3] = {b->pos[0] - cb->pos[0], b->pos[1] - cb->pos[1], b->pos[2] - cb->pos[2]};
    double ux = -cb->rot[0], uy = -cb->rot[1], uz = -cb->rot[2], w = cb->rot[3];      /* the inverse rotation */
    double tx = 2 * (uy * d[2] - uz * d[1]), ty = 2 * (uz * d[0] - ux * d[2]), tz = 2 * (ux * d[1] - uy * d[0]);
    *x = d[0] + w * tx + (uy * tz - uz * ty);
    *z = d[2] + w * tz + (ux * ty - uy * tx);
}

/* v13: end of a helicopter's window: one balance line, one verdict line, the hook off. */
static void heli_close(Track *t, const char *why) {
    int r = (int)g_h6_reached - t->h6r_base, g = (int)g_h6_count - t->h6_base, ab = (int)g_h3_count - t->h3_base, cap = (int)g_cap_count - t->cap_base;
    note(CC2X_LOG_INFO, "id %u: HELI balance (%s): H6 visits %d, GRANTS %d, ABORTS %d, TAKE-OVER block %d", t->id, why, r, g, ab, cap);
    if (cap && (g_cap_bay < 0 || g_cap_bay >= g_cap_limit))
        note(CC2X_LOG_INFO, "id %u: HELI VERDICT: runway given and touch test PASSED, but the game found no bay (bay %d, limit %d): no take-over", t->id, (int)g_cap_bay, (int)g_cap_limit);
    else if (cap)
        note(CC2X_LOG_INFO, "id %u: HELI VERDICT: runway given, touch test PASSED, the game ran its take-over block (bay %d) - see the FOLLOW lines", t->id, (int)g_cap_bay);
    else if (g && ab)
        note(CC2X_LOG_INFO, "id %u: HELI VERDICT: runway given, then the game ABORTED the landing (H3 line): the helicopter flies its own approach, as without us", t->id);
    else if (g)
        note(CC2X_LOG_INFO, "id %u: HELI VERDICT: runway given, no take-over in the window (touch test not passed: the helicopter was no longer on its wheels?) - the game's own "
             "landing goes on", t->id);
    else if (r)
        note(CC2X_LOG_INFO, "id %u: HELI VERDICT: H6 saw the helicopter %d time(s) but did not act: %s", t->id, r, h6_why_text(g_h6_why));
    else
        note(CC2X_LOG_INFO, "id %u: HELI VERDICT: SILENT - the game never looked at this helicopter for the runway (runway not free, or another helicopter first in the queue)", t->id);
    if (g_force_id == t->id) { g_force_id = 0; g_h6_budget = 0; }
    if (cap) follow_start(t->id);
    t->hwin = 2;
}

/* v15: end of a helicopter's hold. give_power = put the engine back (pilot back, recall over without a take-over...); 0 = the game owns it (take-over). v may be NULL. */
static void heli_hold_end(Track *t, void *v, const char *why, int give_power) {
    double back = t->power_saved > 0.0 ? t->power_saved : 1.0;      /* as idle_end: a saved 0 would keep the engine off */
    if (!t->holding) return;
    t->holding = 0;
    if (v) {
        A->vehicle_brakes(v, 0.0f, 1.0f);                           /* the game's own "rest" values */
        if (give_power && A->getf(v, CC2X_VEHICLE_CONTROL_POWER, 0) == 0.0) A->setf(v, CC2X_VEHICLE_CONTROL_POWER, 0, back);
    }
    note(CC2X_LOG_INFO, "id %u: HELI HOLD ended (%s) after %.1f s: brake released%s", t->id, why, t->idle_ticks / TICKS_PER_S,
         !v ? ", helicopter gone" : give_power ? ", engine power back" : ", engine left to the game");
}

/* v15: hold a helicopter on the deck once its pilot has left it (02/11: the game's AI lifts it off 0.5 s later), so that the automatic recall (v14) or the map's recall
 * and H6 (v13) can give it to the game's take-over. Only a helicopter that WAS piloted (control mode 1 at the previous tick), standing on the deck with dock state 0. */
static void heli_hold_tick(Track *t, void *v, int standing, int inzone, int dock, int attached, int mode, int touching, int nw) {
    int cfg = g_cfg.enabled && g_cfg.hold_idle && g_cfg.heli_recall && g_cfg.recall_force && g_hooks_ok && g_h6_ok;
    float b = g_cfg.hold_brake > 0.0f ? g_cfg.hold_brake : 1.0f;
    if (!t->holding) {
        if (cfg && standing && dock == 0 && !attached && mode != MODE_PILOT && t->was_pilot) {
            t->holding = 1; t->idle_ticks = 0; t->power_saved = A->getf(v, CC2X_VEHICLE_CONTROL_POWER, 0);
            note(CC2X_LOG_INFO, "id %u: HELI HOLD (pilot gone, standing on the deck): engine power %.2f -> 0, brake %.2f, until the take-over or the pilot's return", t->id,
                 t->power_saved, (double)b);
        }
    } else if (!cfg) heli_hold_end(t, v, "settings", 1);
    else if (mode == MODE_PILOT) heli_hold_end(t, v, "pilot back", 1);
    else if (attached || dock == CC2X_DOCK_TAXI || dock == CC2X_DOCK_DOCKED) heli_hold_end(t, v, "the game takes it over", 0);
    else if (!inzone) heli_hold_end(t, v, "left the zone", 1);
    else if (dock != 0 && dock != CC2X_DOCK_QUEUED && dock != CC2X_DOCK_DOCKING) heli_hold_end(t, v, "dock state changed", 1);
    else if (dock == CC2X_DOCK_QUEUED && t->hwin == 2) heli_hold_end(t, v, "recall window over without a take-over: the game flies it", 1);
    if (t->holding) {
        if (t->idle_ticks == (int)TICKS_PER_S || t->idle_ticks == (int)(10 * TICKS_PER_S))
            note(CC2X_LOG_INFO, "id %u: HELI HOLD check after %.0f s: power read %.2f before our write (0 = the game leaves it), wheels %d/%d", t->id,
                 t->idle_ticks / TICKS_PER_S, A->getf(v, CC2X_VEHICLE_CONTROL_POWER, 0), touching, nw);
        A->setf(v, CC2X_VEHICLE_CONTROL_POWER, 0, 0.0);
        A->vehicle_brakes(v, b, g_cfg.grip);
        t->idle_ticks++;
    }
    t->was_pilot = mode == MODE_PILOT;
}

/* v13: a human helicopter near its carrier. Writes nothing but through H6 and, v15, the hold above (engine 0 and brake while its pilot is gone). One window per recall. */
static void check_heli(void *v, const cc2x_body *cb, int have_carrier, void *carrier) {
    uint32_t id = (uint32_t)A->geti(v, CC2X_VEHICLE_ID, 0);
    Track *t = track_of(id);
    cc2x_body b;
    double lx = 0, lz = 0;
    if (!t || !A->body_get(v, &b)) return;
    t->seen = 1;
    int nw = A->count(v, CC2X_VEHICLE_WHEELS), touching = 0, mask = 0;
    float cmin = 1e9f;
    if (nw > MAX_WHEELS) nw = MAX_WHEELS;
    for (int i = 0; i < nw; ++i) {
        float c = (float)A->getf(v, CC2X_VEHICLE_WHEEL_CONTACT, i);
        if (c < cmin) cmin = c;
        if (c > CONTACT_MIN) { touching++; mask |= 1 << i; }
    }
    int attached = A->geti(v, CC2X_VEHICLE_ATTACHED_TO, 0) != 0, dock = (int)A->geti(v, CC2X_VEHICLE_DOCK_STATE, 0);
    int flight = (int)A->geti(v, CC2X_VEHICLE_FLIGHT_STATE, 0), mode = (int)A->geti(v, CC2X_VEHICLE_CONTROL_MODE, 0);
    double dx = b.pos[0] - cb->pos[0], dz = b.pos[2] - cb->pos[2], dy = b.pos[1] - cb->pos[1];
    double dist = sqrt(dx * dx + dz * dz), vrel = have_carrier ? vlen(b.vel, cb->vel) : 0.0;
    int inzone = have_carrier && dist <= g_cfg.zone_m && fabs(dy) <= g_cfg.height_m;
    int standing = inzone && nw > 0 && touching == nw && vrel < HELI_MAX_REL && !attached;
    if (have_carrier) deck_xz(cb, &b, &lx, &lz);
    uint32_t sig = (uint32_t)(flight & 3) | (uint32_t)(dock & 7) << 2 | (uint32_t)attached << 5 | (uint32_t)(mode & 7) << 6 | (uint32_t)mask << 9 |
                   (uint32_t)standing << 17 | (uint32_t)(t->hwin & 3) << 18;
    if (inzone && (sig != t->sig || !t->inzone || ((dock == CC2X_DOCK_QUEUED || t->hwin == 1) && g_tick - t->last_beat >= (uint32_t)TICKS_PER_S))) {
        note(CC2X_LOG_INFO, "heli %u t=%.1f: flight=%d dock=%d attached=%d mode=%d power=%.2f wheels=%d/%d(min %.2f) rel=%.2f dist=%.0f dy=%.1f deck x=%.1f z=%.1f standing=%d window=%d",
             id, g_tick / TICKS_PER_S, flight, dock, attached, mode, A->getf(v, CC2X_VEHICLE_CONTROL_POWER, 0), touching, nw, cmin, vrel, dist, dy, lx, lz, standing, t->hwin);
        t->sig = sig;
        t->last_beat = g_tick;
    } else if (!inzone && t->inzone) {
        note(CC2X_LOG_INFO, "heli %u: left the zone (dist %.0f, dy %.1f)", id, dist, dy);
    }
    t->inzone = inzone;

    heli_hold_tick(t, v, standing, inzone, dock, attached, mode, touching, nw);                      /* v15 */
    if (touching == 0) t->auto_done = 0;                                                              /* v14: flying again: its next landing may be recalled once */
    if (!g_cfg.recall_force || !g_hooks_ok || !g_h6_ok) { if (t->hwin == 1) heli_close(t, "recall_force=0"); t->auto_ticks = 0; return; }
    if (t->hwin == 2 && dock != CC2X_DOCK_QUEUED && dock != CC2X_DOCK_DOCKING) t->hwin = 0;        /* that recall is over: the next one may open a window */
    auto_recall_tick(t, v, have_carrier ? carrier : NULL, g_cfg.auto_recall && standing && dock == 0 && mode != MODE_PILOT && !g_force_id && !t->auto_done && t->hwin == 0,
                     "standing on the deck", !g_cfg.auto_recall ? "auto_recall=0" : mode == MODE_PILOT ? "pilot back" : dock != 0 ? "recalled already, or docking" :
                     g_force_id ? "another aircraft is being recalled" : "no longer standing on the deck");
    if (t->hwin == 0 && dock == CC2X_DOCK_QUEUED && standing && mode != MODE_PILOT && (!g_force_id || g_force_id == id)) {
        t->hwin = 1; t->hwin_ticks = 0; t->h6_logged = 0;
        t->h6_base = t->h6_seen = (int)g_h6_count; t->h6r_base = t->h6r_seen = (int)g_h6_reached;
        t->h3_base = t->h3_seen = (int)g_h3_count; t->h3_logged = 0; t->cap_base = t->cap_seen = (int)g_cap_count;
        g_force_id = id; g_h6_budget = 1; g_h6_why = 0; g_mgr = 0;
        note(CC2X_LOG_INFO, "id %u: HELI window open (recalled helicopter standing on the deck: rel %.2f m/s, %d/%d wheels, deck x %.1f z %.1f): H6 armed, one grant at most, %.0f s",
             id, vrel, touching, nw, lx, lz, HELI_WINDOW_TICKS / TICKS_PER_S);
    }
    if (t->hwin != 1) return;
    t->hwin_ticks++;
    if (t->h6_seen != (int)g_h6_count) {
        note(CC2X_LOG_INFO, "id %u: HOOK H6 skipped the helicopters' 100 m test: the game gives the runway itself (queue place %d, free bays %d); dock=%d", id, (int)g_h6_index,
             (int)g_h6_free, dock);
        t->h6_seen = (int)g_h6_count; t->h6r_seen = (int)g_h6_reached;
    } else if (t->h6r_seen != (int)g_h6_reached && t->h6_logged < 3) {
        note(CC2X_LOG_INFO, "id %u: HOOK H6 reached its site (%u visit(s) so far) but did not act: %s", id, (unsigned)g_h6_reached, h6_why_text(g_h6_why));
        t->h6r_seen = (int)g_h6_reached; t->h6_logged++;
    }
    if (t->h3_seen != (int)g_h3_count && t->h3_logged < 3) {
        note(CC2X_LOG_INFO, "id %u: HOOK H3 the game ABORTS the helicopter's landing (%u so far): bay=%d fail=%u counter=%u runway_state=%d", id, (unsigned)g_h3_count,
             (int)g_h3_bay, (unsigned)g_h3_flag, (unsigned)g_h3_counter, (int)g_h3_state);
        t->h3_seen = (int)g_h3_count; t->h3_logged++;
    }
    if (t->cap_seen != (int)g_cap_count) {
        note(CC2X_LOG_INFO, "id %u: PROBE take-over block entered: the touch test PASSED, the game got bay %d (limit %d)%s", id, (int)g_cap_bay, (int)g_cap_limit,
             g_cap_bay < 0 || g_cap_bay >= g_cap_limit ? " -> out of range, the game skips the take-over" : "");
        t->cap_seen = (int)g_cap_count;
    }
    if ((int)g_cap_count != t->cap_base) heli_close(t, "take-over");
    else if ((int)g_h6_count != t->h6_base && (int)g_h3_count != t->h3_base) heli_close(t, "the game aborted");
    else if (mode == MODE_PILOT) heli_close(t, "pilot back");
    else if (!inzone) heli_close(t, "left the zone");
    else if (dock != CC2X_DOCK_QUEUED && dock != CC2X_DOCK_DOCKING) heli_close(t, "dock state changed");
    else if (dock == CC2X_DOCK_QUEUED && !standing && (int)g_h6_count == t->h6_base) heli_close(t, "no longer standing on the deck");
    else if (t->hwin_ticks >= HELI_WINDOW_TICKS) heli_close(t, "timeout");
}

/* v12: after the game's take-over, follow the aircraft (READ ONLY) until it is stowed (dock 4), then 20 s more for the fuel; one line per change and every 5 s. */
static void follow_tick(void) {
    void *v;
    int dock, flight, attached, sig;
    int32_t rs = -99;
    double fuel;
    if (!g_follow_id) return;
    v = A->find(CC2X_WORLD_VEHICLES, g_follow_id);
    if (!v) { note(CC2X_LOG_WARN, "id %u: FOLLOW: the aircraft is gone after %.1f s (destroyed? look at the screen)", g_follow_id, g_follow_ticks / TICKS_PER_S); g_follow_id = 0; return; }
    dock = (int)A->geti(v, CC2X_VEHICLE_DOCK_STATE, 0); flight = (int)A->geti(v, CC2X_VEHICLE_FLIGHT_STATE, 0);
    attached = A->geti(v, CC2X_VEHICLE_ATTACHED_TO, 0) != 0; fuel = A->getf(v, CC2X_VEHICLE_FUEL, 0);
    if (g_mgr && readable((void *)g_mgr, 0xe0)) rs = *(const int32_t *)(g_mgr + 0x1c);
    sig = (dock & 7) | (flight & 3) << 3 | attached << 5 | (rs & 15) << 6;
    if (g_follow_ticks == 0)
        note(CC2X_LOG_INFO, "id %u: %s (dock %d, flight %d, attached %d, runway state %d)", g_follow_id,
             dock == CC2X_DOCK_TAXI && flight == CC2X_FLIGHT_GROUND && rs == 5 ? "TAKEN OVER: dock 6, flight 1, runway state 5 - the game pushes the aircraft back to the lift"
                                                                             : "AFTER THE TAKE-OVER BLOCK: not the expected dock 6 / flight 1 / runway state 5", dock, flight, attached, (int)rs);
    if ((sig != g_follow_sig || g_follow_ticks % (uint32_t)(5 * TICKS_PER_S) == 0) && g_follow_lines < 60) {
        note(CC2X_LOG_INFO, "id %u FOLLOW +%.1fs: dock=%d flight=%d attached=%d runway_state=%d fuel=%.1f", g_follow_id, g_follow_ticks / TICKS_PER_S, dock, flight,
             attached, (int)rs, fuel);
        g_follow_lines++;
    }
    g_follow_sig = sig;
    if (dock == CC2X_DOCK_DOCKED && !g_follow_stowed) {
        g_follow_stowed = g_follow_ticks ? g_follow_ticks : 1; g_follow_fuel = fuel;
        note(CC2X_LOG_INFO, "id %u: HANGAR: dock 4 (stowed) %.1f s after the take-over, fuel %.1f", g_follow_id, g_follow_ticks / TICKS_PER_S, fuel);
    }
    if (g_follow_stowed && g_follow_ticks - g_follow_stowed >= FOLLOW_AFTER_STOW) {
        note(CC2X_LOG_INFO, "id %u: REFUEL check: fuel %.1f at the stowing, %.1f 20 s later (%s); end of the follow", g_follow_id, g_follow_fuel, fuel,
             fuel > g_follow_fuel ? "it goes up: refuelling" : "not up (yet)");
        g_follow_id = 0; return;
    }
    if (++g_follow_ticks >= FOLLOW_MAX_TICKS && !g_follow_stowed) {
        note(CC2X_LOG_WARN, "id %u: FOLLOW stopped after %.0f s without dock 4 (last: dock %d, flight %d, runway state %d)", g_follow_id, g_follow_ticks / TICKS_PER_S, dock, flight, (int)rs);
        g_follow_id = 0;
    }
}

static void on_tick(void *server, void *user) {
    int ncar = 0, n = A->count(NULL, CC2X_WORLD_VEHICLES);
    cc2x_body cbody[MAX_CARRIERS];
    uint32_t cteam[MAX_CARRIERS];
    void *cveh[MAX_CARRIERS];                                   /* v14: the carriers themselves (the automatic recall calls one of their functions) */

    memset(cbody, 0, sizeof(cbody));
    memset(cveh, 0, sizeof(cveh));
    g_server = server;
    if (g_tick++ % CFG_PERIOD == 0) read_cfg();
    for (int i = 0; i < MAX_TRACK; ++i) g_track[i].seen = 0;
    for (int i = 0; i < n && ncar < MAX_CARRIERS; ++i) {
        void *v = A->ref(NULL, CC2X_WORLD_VEHICLES, i);
        if (v && A->geti(v, CC2X_VEHICLE_DEFINITION, 0) == CHASSIS_CARRIER && A->body_get(v, &cbody[ncar])) {
            cteam[ncar] = (uint32_t)A->geti(v, CC2X_VEHICLE_TEAM, 0);
            cveh[ncar] = v;
            ncar++;
        }
    }
    for (int i = 0; i < n; ++i) {
        void *v = A->ref(NULL, CC2X_WORLD_VEHICLES, i);
        uint32_t team;
        int best = -1, wing, heli;
        double best_d = 1e30;
        if (!v || A->geti(v, CC2X_VEHICLE_TEAM_IS_AI, 0)) continue;
        wing = A->geti(v, CC2X_VEHICLE_IS_WING, 0) != 0;
        heli = !wing && g_cfg.heli_recall && A->geti(v, CC2X_VEHICLE_IS_ROTOR, 0);     /* v13: helicopters only with heli_recall=1 */
        if (!wing && !heli) continue;
        team = (uint32_t)A->geti(v, CC2X_VEHICLE_TEAM, 0);
        for (int k = 0; k < ncar; ++k) {                         /* nearest carrier of its own team */
            double d = fabs(A->getf(v, CC2X_VEHICLE_POS, 0) - cbody[k].pos[0]) + fabs(A->getf(v, CC2X_VEHICLE_POS, 2) - cbody[k].pos[2]);
            if (cteam[k] == team && d < best_d) { best_d = d; best = k; }
        }
        if (wing) check_aircraft(v, best >= 0 ? &cbody[best] : &cbody[0], best >= 0, best >= 0 ? cveh[best] : NULL);
        else check_heli(v, best >= 0 ? &cbody[best] : &cbody[0], best >= 0, best >= 0 ? cveh[best] : NULL);
    }
    for (int i = 0; i < MAX_TRACK; ++i)
        if (g_track[i].used && !g_track[i].seen) {            /* gone, or no longer a human wing aircraft (or a watched helicopter) */
            if (g_track[i].braking) release(&g_track[i], "aircraft gone");
            if (g_track[i].hwin == 1) heli_close(&g_track[i], "helicopter gone or no longer watched");
            if (g_track[i].holding && !g_track[i].braking)                           /* v15: a held helicopter no longer watched (heli_recall=0) gets its engine back */
                heli_hold_end(&g_track[i], A->find(CC2X_WORLD_VEHICLES, g_track[i].id), "helicopter gone or no longer watched", 1);
            g_track[i].used = 0;
        }
    follow_tick();
}

static void on_session(void *server, int started, void *user) {
    if (!started)                                              /* v6: give the engine back to any aircraft still idled (the plugin forgets power_saved with g_track) */
        for (int i = 0; i < MAX_TRACK; ++i) {
            if (g_track[i].used && g_track[i].idling) idle_end(&g_track[i], A->find(CC2X_WORLD_VEHICLES, g_track[i].id), "session ended");
            if (g_track[i].used && g_track[i].holding && !g_track[i].braking)      /* v15: a held helicopter */
                heli_hold_end(&g_track[i], A->find(CC2X_WORLD_VEHICLES, g_track[i].id), "session ended", 1);
        }
    memset(g_track, 0, sizeof(g_track));
    g_force_id = 0; g_h1_ours = 0; g_h1_count = g_h2_count = g_h3_count = 0; g_force_budget = 0; g_grants = 0;
    g_gate_ab = g_gate_cd = g_gate_e = g_gate_cpass = 0; g_c_ok = g_cd_was_d = 0;
    g_h5_reached = g_h5_count = g_h5_counter = 0; g_h5_budget = 0; g_h5_state = g_h5_why = 0; g_mgr = 0;
    g_cap_count = 0; g_cap_bay = g_cap_limit = 0; g_follow_id = 0;
    g_h6_reached = g_h6_count = 0; g_h6_budget = 0; g_h6_why = 0; g_h6_free = g_h6_index = 0;
    g_auto_calls = 0; g_server = started ? server : NULL;
    g_tick = 0;
    g_logged = 0;
    g_shown_valid = 0;                                         /* log the settings again at the first read */
    LOG(CC2X_LOG_INFO, "session %s", started ? "started" : "ended");
}

CC2X_EXPORT int cc2x_plugin_load(const cc2x_api *a) {
    const Sites *s = NULL;
    uint32_t stamp;
    if (a->api_version < 3 || a->size < sizeof(cc2x_api) || !a->game_build) return 0;
    for (size_t k = 0; k < sizeof(k_builds) / sizeof(k_builds[0]); ++k)
        if (!strcmp(a->game_build, k_builds[k].build)) s = &k_builds[k];
    if (!s) return 0;                                                   /* v12: a build we have no addresses for */
    stamp = g_exe_stamp();
    if (stamp != s->stamp) {                                            /* the SDK's build name and the running exe must agree */
        if (a->log) a->log("frein", CC2X_LOG_ERROR, "not loaded: the SDK says build %s but the exe has PE timestamp 0x%08x (expected 0x%08x)", s->build, stamp, s->stamp);
        return 0;
    }
    S = s;
    A = a;
    g_ini[0] = 0;
    if (a->config_dir && a->config_dir[0]) snprintf(g_ini, sizeof(g_ini), "%s\\frein.ini", a->config_dir);
    g_shown_valid = 0;
    g_hooks_ok = 0;
    g_h6_ok = 0;
    if (g_ini[0] && ini_num("recall_force", 0) != 0) {                 /* v8: the hooks exist only if asked for at start-up; otherwise nothing of the game is patched */
        int with_h6 = ini_num("heli_recall", 0) != 0;                   /* v13: H6 only if heli_recall=1 at start-up as well */
        g_hooks_ok = install_hooks(a, with_h6);
        g_h6_ok = g_hooks_ok && with_h6;
        if (g_hooks_ok) a->log("frein", CC2X_LOG_INFO, "recall_force=1: hooks H1 (0x%x), H2 (0x%x), H3 (0x%x, read only), 4 commit-gate probes (read only), H5 (0x%x, sends the aircraft to the touch test 0x%x) and the take-over probe (0x%x, read only) installed, inactive until an aircraft is flagged", S->h1, S->h2, S->h3, S->h5, S->h5_goto, S->cap);
        else a->log("frein", CC2X_LOG_ERROR, "recall_force=1 but the hooks could NOT be installed (game build differs?): v15 behaves like v7");
        if (g_h6_ok) a->log("frein", CC2X_LOG_INFO, "heli_recall=1: hook H6 (0x%x, gives the runway to the flagged helicopter: continues at 0x%x) installed too, inactive until a helicopter is flagged", S->h6, S->h6_goto);
    }
    a->on_server_tick(on_tick, NULL);
    a->on_session(on_session, NULL);
    LOG(CC2X_LOG_INFO, "loaded (frein v15, build %s, exe 0x%08x); ini %s; brake off unless brake_enabled=1", S->build, S->stamp, g_ini[0] ? g_ini : "(none)");
    return 1;
}

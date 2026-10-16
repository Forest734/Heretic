//
// Copyright(C) 1993-1996 Id Software, Inc.
// Copyright(C) 1993-2008 Raven Software
// Copyright(C) 2005-2014 Simon Howard
// Copyright(C) 2016 Fabian Greffrath
//
// This program is free software; you can redistribute it and/or
// modify it under the terms of the GNU General Public License
// as published by the Free Software Foundation; either version 2
// of the License, or (at your option) any later version.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// DESCRIPTION:
//	[crispy] Archiving: Extended SaveGame I/O.
//

#include <stdio.h>
#include <stdlib.h>

#include "config.h"
#include "doomtype.h"
#include "doomdef.h"
#include "deh_main.h"
#include "m_misc.h"
#include "p_extsaveg.h"
#include "p_local.h"
#include "z_zone.h"

#define MAX_LINE_LEN 260
#define MAX_STRING_LEN 80

static char *line, *string;

static void P_WritePackageTarname (const char *key)
{
    M_snprintf(line, MAX_LINE_LEN, "%s %s\n", key, PACKAGE_VERSION);
    fputs(line, SaveGameFP);
}

// markpoints[]

extern void AM_GetMarkPoints (int *n, long *p);
extern void AM_SetMarkPoints (int n, long *p);

static void P_WriteMarkPoints (const char *key)
{
    int n;
    long p[20];

    AM_GetMarkPoints(&n, p);

    if (p[0] != -1)
    {
        M_snprintf(line, MAX_LINE_LEN, "%s %d %ld %ld %ld %ld %ld %ld %ld %ld %ld %ld %ld %ld %ld %ld %ld %ld %ld %ld %ld %ld\n",
                   key, n,
                   p[0], p[1], p[2], p[3], p[4],
                   p[5], p[6], p[7], p[8], p[9],
                   p[10], p[11], p[12], p[13], p[14],
                   p[15], p[16], p[17], p[18], p[19]);
        fputs(line, SaveGameFP);
    }
}

static void P_ReadMarkPoints (const char *key)
{
    int n;
    long p[20];

    if (sscanf(line, "%s %d %ld %ld %ld %ld %ld %ld %ld %ld %ld %ld %ld %ld %ld %ld %ld %ld %ld %ld %ld %ld\n",
               string, &n,
               &p[0], &p[1], &p[2], &p[3], &p[4],
               &p[5], &p[6], &p[7], &p[8], &p[9],
               &p[10], &p[11], &p[12], &p[13], &p[14],
               &p[15], &p[16], &p[17], &p[18], &p[19]) == 22 &&
        !strncmp(string, key, MAX_STRING_LEN))
    {
        AM_SetMarkPoints(n, p);
    }
}

// [heretic] entrygear: episode, map, health, armour, backpack, weapons,
// ammo, then the artifacts

static void P_WriteEntryGear (const char *key)
{
    const entrygear_t *g = &entrygear;
    int i;

    if (g->episode != gameepisode || g->map != gamemap)
    {
        return;
    }

    fprintf(SaveGameFP, "%s %d %d %d %d %d %d %d %d %d", key,
            g->episode, g->map, g->health, g->armorpoints, g->armortype,
            g->backpack, g->readyweapon, g->weapons, g->readyArtifact);
    for (i = 0; i < NUMAMMO; i++)
    {
        fprintf(SaveGameFP, " %d %d", g->ammo[i], g->maxammo[i]);
    }
    fprintf(SaveGameFP, " %d", g->inventorySlotNum);
    for (i = 0; i < g->inventorySlotNum; i++)
    {
        fprintf(SaveGameFP, " %d %d", g->inventory[i].type, g->inventory[i].count);
    }
    fputs("\n", SaveGameFP);
}

static void P_ReadEntryGear (const char *key)
{
    const int fixed = 9 + 2 * NUMAMMO + 1;
    int v[9 + 2 * NUMAMMO + 1 + 2 * NUMINVENTORYSLOTS];
    entrygear_t g;
    char *p, *end;
    int i, n;

    p = strstr(line, key) + strlen(key);
    for (n = 0; n < arrlen(v); n++)
    {
        v[n] = strtol(p, &end, 10);
        if (end == p)
        {
            break;
        }
        p = end;
    }

    if (n < fixed || v[fixed - 1] < 0 || v[fixed - 1] > NUMINVENTORYSLOTS
     || n != fixed + 2 * v[fixed - 1]
     || v[0] != gameepisode || v[1] != gamemap || v[2] <= 0
     || v[6] < 0 || v[6] >= NUMWEAPONS || !(v[7] & (1 << v[6]))
     || v[8] < arti_none || v[8] >= NUMARTIFACTS)
    {
        return;
    }

    g.episode = v[0];
    g.map = v[1];
    g.health = v[2];
    g.armorpoints = v[3];
    g.armortype = v[4];
    g.backpack = v[5] != 0;
    g.readyweapon = v[6];
    g.weapons = v[7];
    g.readyArtifact = v[8];
    for (i = 0; i < NUMAMMO; i++)
    {
        g.ammo[i] = v[9 + 2 * i];
        g.maxammo[i] = v[10 + 2 * i];
    }
    g.inventorySlotNum = v[fixed - 1];
    memset(g.inventory, 0, sizeof(g.inventory));
    for (i = 0; i < g.inventorySlotNum; i++)
    {
        g.inventory[i].type = v[fixed + 2 * i];
        g.inventory[i].count = v[fixed + 2 * i + 1];
        if (g.inventory[i].type <= arti_none || g.inventory[i].type >= NUMARTIFACTS)
        {
            return;
        }
    }

    entrygear = g;
}

typedef struct
{
    const char *key;
    void (* extsavegwritefn) (const char *key);
    void (* extsavegreadfn) (const char *key);
    const int pass;
} extsavegdata_t;

static const extsavegdata_t extsavegdata[] =
{
    // [crispy] @FORKS: please change this if you are going to introduce incompatible changes!
    {"crispy-heretic", P_WritePackageTarname, NULL, 0},
    {"markpoints", P_WriteMarkPoints, P_ReadMarkPoints, 1},
    {"entrygear", P_WriteEntryGear, P_ReadEntryGear, 1}, // [heretic]
};

void P_WriteExtendedSaveGameData (void)
{
    int i;

    line = malloc(MAX_LINE_LEN);

    for (i = 0; i < arrlen(extsavegdata); i++)
    {
        extsavegdata[i].extsavegwritefn(extsavegdata[i].key);
    }

    free(line);
}

static void P_ReadKeyValuePairs (int pass)
{
    while (fgets(line, MAX_LINE_LEN, SaveGameFP))
    {
        if (sscanf(line, "%s", string) == 1)
        {
            int i;

            for (i = 1; i < arrlen(extsavegdata); i++)
            {
                if (extsavegdata[i].extsavegreadfn &&
                    extsavegdata[i].pass == pass &&
                    !strncmp(string, extsavegdata[i].key, MAX_STRING_LEN))
                {
                    extsavegdata[i].extsavegreadfn(extsavegdata[i].key);
                }
            }
        }
    }
}

void P_ReadExtendedSaveGameData (void)
{
    line = malloc(MAX_LINE_LEN);
    string = malloc(MAX_STRING_LEN);

    // [crispy] only second pass for Heretic
    P_ReadKeyValuePairs(1);

    free(line);
    free(string);
}

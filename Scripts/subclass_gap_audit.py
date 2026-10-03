"""Subclass 13-20 gap audit (2026-10-03): for every playable subclass (ClassDescription with a parent class), the
class's expected 13-20 subclass feature levels (2024 rules) and the half-casters' subclass spells at 13/17, against
the Apotheosis progression nodes. Reads the bg3-data MCP index (~/.cache/bg3-data-mcp/cache/index.sqlite).
Run: python3 Scripts/subclass_gap_audit.py"""
import sqlite3,os,json,re
c=sqlite3.connect(os.path.expanduser('~/.cache/bg3-data-mcp/cache/index.sqlite'))
cd={}
for layer,u,n,a in c.execute("select layer,uuid,name,attrs from staticdata where kind like 'ClassDescription%' order by rank"):
    cd[u]=(n,json.loads(a))
byname={}
for u,(n,a) in cd.items():
    byname.setdefault(n,[]).append((u,a))
cls_of={}; table_of={}
for u,(n,a) in cd.items():
    p=a.get('ParentGuid')
    if p and p!='00000000-0000-0000-0000-000000000000' and p in cd:
        cls_of[n]=cd[p][0]; table_of[n]=a.get('ProgressionTableUUID')
EXP={'Barbarian':[14],'Bard':[14],'Cleric':[17],'Druid':[14],'Fighter':[15,18],'Monk':[17],'Paladin':[15,20],
     'Ranger':[15],'Rogue':[13,17],'Sorcerer':[14,18],'Warlock':[14],'Wizard':[14],'Artificer':[15]}
SPELLS={'Paladin','Ranger','Artificer'}
NO_SPELL_TABLE={'BeastMaster','Hunter'}  # no subclass spell table
KNOWN_EMPTY={'Glory':(17,),'Ancients':(17,),'FeyWanderer':(17,),'HollowWarden':(13,),'Armorer':(17,)}  # every spell missing in BG3
apo={}
for t,lv,a in c.execute("select table_uuid,level,attrs from prog where layer='apotheosis'"):
    apo.setdefault(t,{})[int(lv)]=json.loads(a)
low={}
for t,lv,a,l in c.execute("select table_uuid,level,attrs,layer from prog where layer in ('base','dnd55e') order by rank"):
    low.setdefault(t,{})[int(lv)]=json.loads(a)
out=[]
for sub,cl in sorted(cls_of.items(), key=lambda x:(x[1],x[0])):
    if cl not in EXP: continue
    t=table_of.get(sub)
    if t not in low: continue   # not a playable subclass table in base/dnd55e
    have=apo.get(t,{})
    miss=[f"L{L}" for L in EXP[cl] if L not in have]
    if cl in SPELLS and sub not in NO_SPELL_TABLE:
        for L in (13,17):
            if L in KNOWN_EMPTY.get(sub, ()):
                continue
            sel=(have.get(L) or {}).get('Selectors','') or ''
            if 'AddSpells' not in sel: miss.append(f"spells{L}")
    if miss: out.append(f"{cl:10s} {sub:28s} {t}  missing: {', '.join(miss)}")
print('\n'.join(out)); print(len(out),'subclasses with gaps')

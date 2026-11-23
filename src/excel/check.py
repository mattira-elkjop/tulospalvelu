import sys, subprocess, glob, datetime
sys.path.insert(0,'.')
import build as B
from openpyxl import load_workbook
S=glob.glob('/root/.claude/skills/synced/*/xlsx/scripts/recalc.py')[0]
wb=B.build('/tmp/d0.xlsx',demo=True)
rows,pens=wb._demo
G={};A={};U={}
for sc,a1,a2 in rows:
    G[sc]=G.get(sc,0)+1
    for a in (a1,a2):
        if a: A[a]=A.get(a,0)+1
for n,m in pens: U[n]=U.get(n,0)+m
names={p[0]:p[1] for p in B.PLAYERS}
def exp(stat, hide=True):
    out=[]
    for i,(n,_,_) in enumerate(B.PLAYERS):
        g,a,u=G.get(n,0),A.get(n,0),U.get(n,0)
        p=g+a
        key={'Poäng':(p,g),'Mål':(g,p),'Assist':(a,g),'Utvisningsminuter':(u,0)}[stat]
        out.append((key,-i,n,g,a,p,u))
    out.sort(reverse=True)
    v=lambda t:{'Poäng':t[5],'Mål':t[3],'Assist':t[4],'Utvisningsminuter':t[6]}[stat]
    return [t for t in out if (v(t)>0 or not hide)]
ok=True
for stat,top,hide in [('Poäng','Alla','Ja'),('Mål','Alla','Ja'),('Assist','10','Ja'),('Utvisningsminuter','Alla','Ja'),('Poäng','Alla','Nej')]:
    w=load_workbook('/tmp/d0.xlsx')
    w['Telefonvy']['C1']=stat; w['Telefonvy']['C2']=top; w['Telefonvy']['C3']=hide
    w['Datorvy']['D1']=stat; w['Datorvy']['D2']=top; w['Datorvy']['D3']=hide
    w.save('/tmp/d1.xlsx')
    subprocess.run(['python3',S,'/tmp/d1.xlsx','90'],capture_output=True)
    r=load_workbook('/tmp/d1.xlsx',data_only=True)
    e=exp(stat,hide=(hide=='Ja'))
    if top!='Alla': e=e[:int(top)]
    for sh,(c0,r0) in (('Telefonvy',(1,9)),('Datorvy',(2,12))):
        ws=r[sh]; got=[]
        for k in range(30):
            row=r0+k
            nr=ws.cell(row,c0+1).value
            if nr in (None,''): break
            if sh=='Telefonvy': vals=[ws.cell(row,c0+j).value for j in (3,4,5,6)]
            else: vals=[ws.cell(row,c0+j).value for j in (4,5,6,7)]
            got.append((nr,tuple(vals)))
        want=[(t[2],(t[3],t[4],t[5],t[6])) for t in e]
        if got!=want:
            ok=False; print('MISMATCH',sh,stat,top,hide); print(got[:6]); print(want[:6])
        else: print('ok',sh,stat,top,hide,len(got),'rows')
print('ALL OK' if ok else 'FAIL')

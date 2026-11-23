from playwright.sync_api import sync_playwright
url='file:///home/claude/v2/Lagets_poangliga.html'
def C(pg,sel): pg.click(sel); pg.wait_for_timeout(60)
with sync_playwright() as p:
    b=p.chromium.launch(); ctx=b.new_context(viewport={'width':390,'height':844},device_scale_factor=2,accept_downloads=True)
    pg=ctx.new_page(); errs=[]
    pg.on('pageerror',lambda e:errs.append(str(e))); pg.on('console',lambda m: m.type=='error' and errs.append(m.text))
    pg.goto(url); pg.wait_for_timeout(300)
    # database file
    C(pg,'[data-a=tab][data-v=data]')
    with pg.expect_download() as dl: C(pg,'[data-a=exp-dl]')
    dl.value.save_as('MIF_U13_databas.csv')
    idm={n:i for n,i in pg.evaluate("players.map(p=>[p.nr,p.id])")}
    P=lambda n:f'[data-id={idm[n]}]'
    C(pg,'[data-a=tab][data-v=matcher]')
    C(pg,'#pm-toggle')
    # match 1
    C(pg,'[data-a=m-new]'); pg.fill('#mf-opp','Kiekko IK')
    for n in [5,6,7,10,11,19,20,90]: C(pg,'[data-a=mf-tog]'+P(n))
    pg.screenshot(path='form.png',full_page=False)
    C(pg,'[data-a=mf-save]')
    # goal 10 <- 5,6 on ice +7,11
    C(pg,'[data-a=ev-new][data-t=g]')
    for n in [10,5,6]: C(pg,'[data-a=ev-pick]'+P(n))
    for n in [7,11]: C(pg,'[data-a=ev-ice]'+P(n))
    pg.screenshot(path='goal.png')
    C(pg,'[data-a=ev-save]')
    # goal against, same as previous
    C(pg,'[data-a=ev-new][data-t=ga]'); C(pg,'[data-a=ice-prev]'); C(pg,'[data-a=ev-save]')
    # penalty 20 4min
    C(pg,'[data-a=ev-new][data-t=u]'); C(pg,'[data-a=ev-pid]'+P(20)); C(pg,'[data-a=min][data-v="4"]'); C(pg,'[data-a=ev-save]')
    # edit goal: change scorer to 11
    C(pg,'[data-a=ev-edit][data-t=g]'); C(pg,'[data-a=ev-pick]'+P(10)); C(pg,'[data-a=ev-pick]'+P(11)); C(pg,'[data-a=ev-save]')
    pg.screenshot(path='match.png',full_page=True)
    # match 2 copy lineup minus 90 plus 91
    C(pg,'[data-a=m-back]'); C(pg,'[data-a=m-new]'); C(pg,'[data-a=mf-last]'); C(pg,'[data-a=mf-tog]'+P(90)); C(pg,'[data-a=mf-tog]'+P(91)); C(pg,'[data-a=mf-save]')
    C(pg,'[data-a=ev-new][data-t=g]'); C(pg,'[data-a=ev-pick]'+P(19)); C(pg,'[data-a=ev-save]')
    # remove 19 from lineup -> must be kept
    C(pg,'[data-a=mf-edit]'); C(pg,'[data-a=mf-tog]'+P(19)); C(pg,'[data-a=mf-save]')
    print('toast:',pg.inner_text('.toast span'))
    pg.reload(); pg.wait_for_timeout(300)
    st=pg.evaluate("Object.fromEntries(computeStats().filter(r=>r.gp).map(r=>[r.p.nr,[r.gp,r.g,r.a,r.pts,r.u,r.pm]]))")
    print(st)
    exp={5:[2,0,1,1,0,1],6:[2,0,1,1,0,1],7:[2,0,0,0,0,1],10:[2,0,0,0,0,-1],11:[2,1,0,1,0,1],19:[2,1,0,1,0,0],20:[2,0,0,0,4,0],90:[1,0,0,0,0,0],91:[1,0,0,0,0,0]}
    # goal1 after edit: scorer 11, a 5,6; ice = 11,5,6,7 + previously 10 (stays in e.ice? 10 was locked as scorer, not in e.ice) 
    print('match', st=={str(k):v for k,v in exp.items()} or st)
    C(pg,'[data-a=tab][data-v=lista]'); pg.screenshot(path='lista.png')
    C(pg,'[data-a=stat][data-v=pm]'); pg.screenshot(path='lista_pm.png')
    # export / import roundtrip
    C(pg,'[data-a=tab][data-v=data]')
    with pg.expect_download() as dl: C(pg,'[data-a=exp-dl]')
    dl.value.save_as('rt.csv')
    ctx2=b.new_context(); p2=ctx2.new_page(); p2.on('pageerror',lambda e:errs.append(str(e)))
    p2.goto(url); p2.click('[data-a=tab][data-v=data]'); p2.set_input_files('#imp-file','rt.csv'); p2.wait_for_timeout(200)
    p2.click('[data-a=imp-do]'); p2.click('[data-a=imp-do]'); p2.wait_for_timeout(200)
    st2=p2.evaluate("Object.fromEntries(computeStats().filter(r=>r.gp).map(r=>[r.p.nr,[r.gp,r.g,r.a,r.pts,r.u,r.pm]]))")
    print('roundtrip equal', st2==st, p2.evaluate("cur().pm"))
    # old v1 csv import
    p2.click('[data-a=tab][data-v=data]'); p2.set_input_files('#imp-file','/home/claude/local/roundtrip.csv'); p2.wait_for_timeout(200)
    p2.click('[data-a=imp-do]'); p2.click('[data-a=imp-do]'); p2.wait_for_timeout(200)
    print('old csv', p2.evaluate("[cur().matches.length,cur().matches[0].players.length,cur().matches[0].auto,cur().goals.length,cur().pens.length]"))
    # old v1 localStorage migration
    ctx3=b.new_context(); p3=ctx3.new_page(); p3.on('pageerror',lambda e:errs.append(str(e)))
    p3.goto(url)
    p3.evaluate("""localStorage.setItem('lp_data_v1',JSON.stringify({v:1,changes:2,seasons:[{id:'s',lag:'MIF',serie:'',sasong:'x',created:1,players:[{id:'a',nr:1,name:'A B',pos:'UP'},{id:'b',nr:2,name:'C D',pos:'UP'}],goals:[{id:'g1',scorer:'a',a1:'b',a2:null,date:'2026-11-01',opp:'X',ts:1},{id:'g2',scorer:'b',a1:null,a2:null,date:'2026-11-08',opp:'Y',ts:2}],pens:[{id:'u',pid:'a',min:2,date:'2026-11-08',opp:'Y',ts:3}]}]}))""")
    p3.reload(); p3.wait_for_timeout(200)
    print('migrated', p3.evaluate("Object.fromEntries(computeStats().map(r=>[r.p.nr,[r.gp,r.g,r.a,r.u]]))"), p3.evaluate("cur().matches.length"))
    print('errors',errs); b.close()

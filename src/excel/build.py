import sys, random, datetime
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.formatting.rule import FormulaRule, DataBarRule
from openpyxl.workbook.defined_name import DefinedName
from openpyxl.chart import BarChart, Reference
from openpyxl.chart.label import DataLabelList

FONT = "Arial"
NAVY, BLUE, LIGHT, BAND = "0B2545", "13315C", "EAF0F8", "F3F6FA"
YEL, GREYF = "FFF8DC", "F2F2F2"
GOLD, SILVER, BRONZE, HILITE = "F6C945", "CBD2DB", "E3A877", "FFE9A8"

P1, P2 = 9, 48          # Spelare data rows
M1, M2 = 7, 306         # Matcher data rows

PLAYERS = [
    (5, "Spelare 5", "UP"), (6, "Spelare 6", "UP"), (7, "Spelare 7", "UP"),
    (10, "Spelare 10", "UP"), (11, "Spelare 11", "UP"), (13, "Spelare 13", "UP"),
    (19, "Spelare 19", "UP"), (20, "Spelare 20", "UP"), (21, "Spelare 21", "UP"),
    (22, "Spelare 22", "UP"), (24, "Spelare 24", "UP"), (30, "Spelare 30", "UP"),
    (41, "Spelare 41", "UP"), (43, "Spelare 43", "UP"), (49, "Spelare 49", "UP"),
    (90, "Spelare 90", "MV"), (91, "Spelare 91", "MV"), (92, "Spelare 92", "MV"),
]

def f(size=11, bold=False, color="000000", italic=False):
    return Font(name=FONT, size=size, bold=bold, color=color, italic=italic)

def fill(c):
    return PatternFill("solid", start_color=c, end_color=c)

thin = Side(style="thin", color="D5DCE6")
BOX = Border(left=thin, right=thin, top=thin, bottom=thin)

def style_range(ws, rng, font=None, fl=None, al=None, border=None, nf=None):
    for row in ws[rng]:
        for c in row:
            if font: c.font = font
            if fl: c.fill = fl
            if al: c.alignment = al
            if border: c.border = border
            if nf: c.number_format = nf

CENTER = Alignment(horizontal="center", vertical="center")
LEFT = Alignment(horizontal="left", vertical="center")

def build(path, demo=False):
    wb = Workbook()

    # ------------------------------------------------------------------ Spelare
    sp = wb.active
    sp.title = "Spelare"
    sp.sheet_properties.tabColor = NAVY
    for col, w in zip("ABCDEFGH", [9, 28, 12, 7, 8, 8, 8, 9]):
        sp.column_dimensions[col].width = w
    sp.column_dimensions["I"].width = 3
    sp.column_dimensions["J"].width = 100
    style_range(sp, "A1:H1", fl=fill(NAVY))
    sp["A1"] = "Spelare & lag"; sp["A1"].font = f(18, True, "FFFFFF"); sp["A1"].alignment = LEFT
    sp.row_dimensions[1].height = 34
    sp["A2"] = "Gula celler fyller du i. Grå celler räknas ut automatiskt."
    sp["A2"].font = f(9, italic=True, color="666666")
    for r, (lab, val) in zip((3, 4, 5), [("Lag", "MIF"), ("Serie", "U13 Valkoinen, lohko 3b"),
                                         ("Säsong", "2026–2027")]):
        sp[f"A{r}"] = lab; sp[f"A{r}"].font = f(10, True)
        sp[f"B{r}"] = val; sp[f"B{r}"].font = f(11, True, "0000FF")
        sp[f"B{r}"].fill = fill(YEL); sp[f"B{r}"].border = BOX
    sp["A7"] = "Spelarlista – fyll på uppifrån och ned utan tomma rader (max 40 spelare)."
    sp["A7"].font = f(9, italic=True, color="666666")
    for c, h in zip("ABCDEFGH", ["Nr", "Namn", "Lag", "Pos", "Mål", "Assist", "Poäng", "Utv.min"]):
        sp[f"{c}8"] = h
    style_range(sp, "A8:H8", font=f(10, True, "FFFFFF"), fl=fill(BLUE), al=CENTER, border=BOX)
    sp["B8"].alignment = LEFT
    sp.row_dimensions[8].height = 22

    MR = lambda col: f"Matcher!${col}${M1}:${col}${M2}"
    for i, r in enumerate(range(P1, P2 + 1)):
        if i < len(PLAYERS):
            nr, name, pos = PLAYERS[i]
            sp[f"A{r}"], sp[f"B{r}"], sp[f"C{r}"], sp[f"D{r}"] = nr, name, "MIF", pos
        sp[f"E{r}"] = f'=IF($A{r}="","",COUNTIF({MR("C")},$A{r}))'
        sp[f"F{r}"] = f'=IF($A{r}="","",COUNTIF({MR("D")},$A{r})+COUNTIF({MR("E")},$A{r}))'
        sp[f"G{r}"] = f'=IF($A{r}="","",E{r}+F{r})'
        sp[f"H{r}"] = f'=IF($A{r}="","",SUMIF({MR("L")},$A{r},{MR("M")}))'
        # sorteringsnycklar (dolda): värde*1e7 + sekundärt*1e4 + (100-radnr) => unikt heltal
        t = f"(100-(ROW()-{P1 - 1}))"
        sp[f"T{r}"] = f'=IF($A{r}="","",G{r}*10000000+E{r}*10000+{t})'
        sp[f"U{r}"] = f'=IF($A{r}="","",E{r}*10000000+G{r}*10000+{t})'
        sp[f"V{r}"] = f'=IF($A{r}="","",F{r}*10000000+E{r}*10000+{t})'
        sp[f"W{r}"] = f'=IF($A{r}="","",H{r}*10000000+{t})'
    style_range(sp, f"A{P1}:D{P2}", font=f(11, color="0000FF"), fl=fill(YEL), border=BOX, al=CENTER)
    style_range(sp, f"B{P1}:B{P2}", al=LEFT)
    style_range(sp, f"E{P1}:H{P2}", font=f(11, color="444444"), fl=fill(GREYF), border=BOX, al=CENTER)
    style_range(sp, f"G{P1}:G{P2}", font=f(11, True, "222222"))
    sp["T8"], sp["U8"], sp["V8"], sp["W8"] = "Nyckel Poäng", "Nyckel Mål", "Nyckel Assist", "Nyckel Utv"
    for c in "TUVW":
        sp.column_dimensions[c].hidden = True
    sp.freeze_panes = "A9"

    help_lines = [
        ("Så här använder du arket", True),
        ("1. Spelare: skriv in nummer, namn, lag och position (gula celler).", False),
        ("2. Matcher: efter varje match, skriv datum + spelarnummer för mål, assist och utvisningar. Välj nummer i rullistan.", False),
        ("3. Telefonvy / Datorvy: välj lista (Poäng, Mål, Assist eller Utvisningsminuter) i de gula cellerna överst.", False),
        ("    Poängen räknas automatiskt: poäng = mål + assist. Delad placering får samma siffra.", False),
        ("", False),
        ("Nytt lag eller ny säsong", True),
        ("1. Arkiv > Spara som kopia (så behåller du den gamla säsongen).", False),
        ("2. Spelare: ändra B3:B5, markera A9:D48 och tryck Delete, skriv in de nya spelarna.", False),
        ("3. Matcher: markera A7:E306 och tryck Delete, markera sedan J7:M306 och tryck Delete.", False),
        ("    Radera inte de grå kolumnerna – de innehåller formler.", False),
        ("", False),
        ("Gränser: max 40 spelare och 300 mål- samt 300 utvisningsrader per fil.", False),
        ("Källa för spelarlistan: tulospalvelu.leijonat.fi (U13 Valkoinen, lohko 3b, säsong 2027). Position MV = målvakt, UP = utespelare.", False),
    ]
    for i, (t, b) in enumerate(help_lines):
        c = sp[f"J{3 + i}"]; c.value = t; c.font = f(10, b, NAVY if b else "333333")

    wb.defined_names["Spelarnummer"] = DefinedName(
        "Spelarnummer",
        attr_text=f"OFFSET(Spelare!$A${P1},0,0,MAX(1,COUNT(Spelare!$A${P1}:$A${P2})),1)")
    dvp = DataValidation(type="list", formula1='"MV,UP"', allow_blank=True)
    sp.add_data_validation(dvp); dvp.add(f"D{P1}:D{P2}")

    # ------------------------------------------------------------------ Matcher
    mt = wb.create_sheet("Matcher")
    mt.sheet_properties.tabColor = "2E7D32"
    for col, w in zip("ABCDEFGHIJKLMN", [12, 18, 10, 10, 10, 20, 20, 20, 3, 12, 18, 10, 9, 22]):
        mt.column_dimensions[col].width = w
    style_range(mt, "A1:N1", fl=fill(NAVY))
    mt["A1"] = "Matcher – mål, assist och utvisningar"; mt["A1"].font = f(18, True, "FFFFFF")
    mt["A1"].alignment = LEFT; mt.row_dimensions[1].height = 34
    mt["A2"] = "En rad per mål (vänster) och en rad per utvisning (höger). Välj spelarnummer i rullistan – namnet visas automatiskt."
    mt["A3"] = "Rad 6 är bara ett exempel och räknas inte med. Datum och motståndare är valfria och påverkar inte statistiken."
    for a in ("A2", "A3"):
        mt[a].font = f(9, italic=True, color="555555")
    mt["A4"] = "MÅL & ASSIST"; mt["J4"] = "UTVISNINGAR"
    style_range(mt, "A4:H4", font=f(10, True, "FFFFFF"), fl=fill("2E7D32"), al=LEFT)
    style_range(mt, "J4:N4", font=f(10, True, "FFFFFF"), fl=fill("B23A3A"), al=LEFT)
    gh = ["Datum", "Motståndare", "Mål (nr)", "Assist 1 (nr)", "Assist 2 (nr)", "Målskytt", "Assist 1", "Assist 2"]
    ph = ["Datum", "Motståndare", "Spelare (nr)", "Minuter", "Spelare"]
    for c, h in zip("ABCDEFGH", gh): mt[f"{c}5"] = h
    for c, h in zip("JKLMN", ph): mt[f"{c}5"] = h
    style_range(mt, "A5:H5", font=f(10, True, "FFFFFF"), fl=fill(BLUE), al=Alignment(horizontal="center", vertical="center", wrap_text=True), border=BOX)
    style_range(mt, "J5:N5", font=f(10, True, "FFFFFF"), fl=fill(BLUE), al=Alignment(horizontal="center", vertical="center", wrap_text=True), border=BOX)
    mt.row_dimensions[5].height = 30
    # exempelrad
    ex = {"A6": datetime.date(2026, 11, 15), "B6": "Exempel IK", "C6": 11, "D6": 6, "E6": 7,
          "J6": datetime.date(2026, 11, 15), "K6": "Exempel IK", "L6": 20, "M6": 2}
    for k, v in ex.items(): mt[k] = v
    style_range(mt, "A6:H6", font=f(10, italic=True, color="999999"), al=CENTER, border=BOX)
    style_range(mt, "J6:N6", font=f(10, italic=True, color="999999"), al=CENTER, border=BOX)
    mt["A6"].number_format = mt["J6"].number_format = "yyyy-mm-dd"

    look = lambda cell: (f'=IF({cell}="","",IFERROR(INDEX(Spelare!$B${P1}:$B${P2},'
                         f'MATCH({cell},Spelare!$A${P1}:$A${P2},0)),"okänt nr"))')
    for r in range(M1, M2 + 1):
        mt[f"F{r}"] = look(f"$C{r}"); mt[f"G{r}"] = look(f"$D{r}"); mt[f"H{r}"] = look(f"$E{r}")
        mt[f"N{r}"] = look(f"$L{r}")
    style_range(mt, f"A{M1}:E{M2}", font=f(11, color="0000FF"), fl=fill(YEL), al=CENTER, border=BOX)
    style_range(mt, f"J{M1}:M{M2}", font=f(11, color="0000FF"), fl=fill(YEL), al=CENTER, border=BOX)
    style_range(mt, f"F{M1}:H{M2}", font=f(11, color="444444"), fl=fill(GREYF), al=LEFT, border=BOX)
    style_range(mt, f"N{M1}:N{M2}", font=f(11, color="444444"), fl=fill(GREYF), al=LEFT, border=BOX)
    style_range(mt, f"A{M1}:A{M2}", nf="yyyy-mm-dd"); style_range(mt, f"J{M1}:J{M2}", nf="yyyy-mm-dd")
    style_range(mt, f"B{M1}:B{M2}", al=LEFT); style_range(mt, f"K{M1}:K{M2}", al=LEFT)
    mt.freeze_panes = "A7"

    dv = DataValidation(type="list", formula1="=Spelarnummer", allow_blank=True, showErrorMessage=True,
                        errorTitle="Okänt spelarnummer",
                        error="Numret finns inte i fliken Spelare. Välj ett nummer från rullistan.")
    mt.add_data_validation(dv); dv.add(f"C{M1}:E{M2}"); dv.add(f"L{M1}:L{M2}")
    dvm = DataValidation(type="list", formula1='"2,4,5,10,20"', allow_blank=True, showErrorMessage=True,
                         errorStyle="warning", errorTitle="Ovanlig utvisningstid",
                         error="Vanliga tider är 2, 4, 5, 10 och 20 minuter. Fortsätta ändå?")
    mt.add_data_validation(dvm); dvm.add(f"M{M1}:M{M2}")
    red = Font(name=FONT, color="C00000", bold=True)
    for rng in (f"F{M1}:H{M2}", f"N{M1}:N{M2}"):
        tl = rng.split(":")[0]
        mt.conditional_formatting.add(rng, FormulaRule(formula=[f'{tl}="okänt nr"'], font=red))
    mt.conditional_formatting.add(f"C{M1}:E{M2}", FormulaRule(
        formula=[f'AND(C{M1}<>"",COUNTIF($C{M1}:$E{M1},C{M1})>1)'], fill=fill("F8C9C9")))

    # ------------------------------------------------------------------ Telefonvy
    ph_ = wb.create_sheet("Telefonvy")
    ph_.sheet_properties.tabColor = "F6C945"
    ph_.sheet_view.showGridLines = False
    for col, w in zip("ABCDEFG", [5, 5, 22, 7, 7, 8, 7]):
        ph_.column_dimensions[col].width = w
    for c in "IJKLMN": ph_.column_dimensions[c].hidden = True
    R0, N = 9, 30          # första dataraden, antal rader
    RL = R0 + N - 1
    KEYS = f"Spelare!$T${P1}:$W${P2}"
    # kontroller
    ctrl = [(1, "Lista", "Poäng", '"Poäng,Mål,Assist,Utvisningsminuter"'),
            (2, "Visa topp", "Alla", '"Alla,5,10,15,20"'),
            (3, "Dölj nollor", "Ja", '"Ja,Nej"')]
    for r, lab, val, lst in ctrl:
        ph_.merge_cells(f"A{r}:B{r}"); ph_.merge_cells(f"C{r}:G{r}")
        ph_[f"A{r}"] = lab; ph_[f"A{r}"].font = f(8, color="666666"); ph_[f"A{r}"].alignment = Alignment(vertical="center", wrap_text=True)
        ph_[f"C{r}"] = val
        style_range(ph_, f"C{r}:G{r}", font=f(11, True, "0000FF"), fl=fill(YEL), al=CENTER, border=BOX)
        d = DataValidation(type="list", formula1=lst, allow_blank=False)
        ph_.add_data_validation(d); d.add(f"C{r}")
        ph_.row_dimensions[r].height = 22
    ph_["I1"] = '=IF($C$1="Poäng",1,IF($C$1="Mål",2,IF($C$1="Assist",3,4)))'
    ph_["I2"] = '=IF($C$2="Alla",99,$C$2*1)'
    ph_.merge_cells("A4:G4")
    ph_["A4"] = "Scrolla ned så att inställningarna ovan inte syns i skärmbilden"
    ph_["A4"].font = f(8, italic=True, color="999999"); ph_.row_dimensions[4].height = 14
    # banner
    for r in (5, 6): ph_.merge_cells(f"A{r}:G{r}")
    style_range(ph_, "A5:G6", fl=fill(NAVY))
    ph_["A5"] = '=Spelare!$B$3&"  ·  "&CHOOSE($I$1,"Poängliga","Målliga","Assistliga","Utvisningsliga")'
    ph_["A5"].font = f(20, True, "FFFFFF"); ph_["A5"].alignment = Alignment(horizontal="left", vertical="center", indent=1)
    ph_["A6"] = '=Spelare!$B$4&"  ·  "&Spelare!$B$5'
    ph_["A6"].font = f(10, color="A9B8CE"); ph_["A6"].alignment = Alignment(horizontal="left", vertical="center", indent=1)
    ph_.row_dimensions[5].height = 38; ph_.row_dimensions[6].height = 20
    ph_.merge_cells("A7:G7")
    ph_["A7"] = (f'="Lag: "&COUNT({MR("C")})&" mål  ·  "&(COUNT({MR("D")})+COUNT({MR("E")}))'
                 f'&" assist  ·  "&SUM({MR("M")})&" utv.min"')
    style_range(ph_, "A7:G7", font=f(10, True, NAVY), fl=fill(LIGHT), al=Alignment(horizontal="left", vertical="center", indent=1))
    ph_.row_dimensions[7].height = 22
    for c, h in zip("ABCDEFG", ["#", "Nr", "Spelare", "Mål", "Ass", "Poäng", "Utv"]): ph_[f"{c}8"] = h
    style_range(ph_, "A8:G8", font=f(11, True, "FFFFFF"), fl=fill(BLUE), al=CENTER)
    ph_["C8"].alignment = LEFT; ph_.row_dimensions[8].height = 24
    for i in range(N):
        r = R0 + i
        ph_[f"I{r}"] = i + 1
        ph_[f"J{r}"] = f'=IFERROR(LARGE(INDEX({KEYS},0,$I$1),I{r}),"")'
        ph_[f"K{r}"] = f'=IF(J{r}="","",MATCH(J{r},INDEX({KEYS},0,$I$1),0))'
        ph_[f"L{r}"] = f'=IF(K{r}="","",INT(J{r}/10000000))'
        ph_[f"M{r}"] = f'=IF(K{r}="",FALSE,AND(I{r}<=$I$2,OR($C$3="Nej",L{r}>0)))'
        ph_[f"N{r}"] = (f'=IF(M{r},1,"")' if i == 0 else f'=IF(M{r},IF(L{r}=L{r-1},N{r-1},I{r}),"")')
        ph_[f"A{r}"] = f'=IF($M{r},$N{r},"")'
        ph_[f"B{r}"] = f'=IF($M{r},INDEX(Spelare!$A${P1}:$A${P2},$K{r}),"")'
        ph_[f"C{r}"] = f'=IF($M{r},INDEX(Spelare!$B${P1}:$B${P2},$K{r}),"")'
        for col, sc in zip("DEFG", "EFGH"):
            ph_[f"{col}{r}"] = f'=IF($M{r},INDEX(Spelare!${sc}${P1}:${sc}${P2},$K{r}),"")'
        ph_.row_dimensions[r].height = 26
    style_range(ph_, f"A{R0}:G{RL}", font=f(13), al=CENTER)
    style_range(ph_, f"C{R0}:C{RL}", al=Alignment(horizontal="left", vertical="center", indent=0))
    style_range(ph_, f"A{R0}:A{RL}", font=f(13, True, NAVY))
    style_range(ph_, f"D{R0}:G{RL}", nf='0;-0;"-"')
    ph_.conditional_formatting.add(f"D{R0}:G{RL}", FormulaRule(
        formula=[f'AND($C{R0}<>"",COLUMN(D{R0})=CHOOSE($I$1,6,4,5,7))'],
        fill=fill(HILITE), font=Font(name=FONT, bold=True, size=14)))
    for val, col in ((1, GOLD), (2, SILVER), (3, BRONZE)):
        ph_.conditional_formatting.add(f"A{R0}:A{RL}", FormulaRule(formula=[f'AND($C{R0}<>"",$A{R0}={val})'], fill=fill(col)))
    ph_.conditional_formatting.add(f"A{R0}:G{RL}", FormulaRule(
        formula=[f'AND($C{R0}<>"",MOD(ROW(),2)=0)'], fill=fill(BAND),
        border=Border(bottom=Side(style="thin", color="D5DCE6"))))
    ph_.conditional_formatting.add(f"A{R0}:G{RL}", FormulaRule(
        formula=[f'$C{R0}<>""'], border=Border(bottom=Side(style="thin", color="D5DCE6"))))
    ph_.page_setup.orientation = "portrait"
    ph_.sheet_properties.pageSetUpPr.fitToPage = True
    ph_.page_setup.fitToWidth = 1; ph_.page_setup.fitToHeight = 0
    ph_.print_area = f"A1:G{RL}"

    # ------------------------------------------------------------------ Datorvy
    pc = wb.create_sheet("Datorvy")
    pc.sheet_properties.tabColor = "1F77B4"
    pc.sheet_view.showGridLines = False
    for col, w in zip("ABCDEFGHIJK", [2, 6, 6, 26, 7, 9, 9, 9, 9, 30, 3]):
        pc.column_dimensions[col].width = w
    HC = ["Z", "AA", "AB", "AC", "AD", "AE", "AF"]
    for c in HC: pc.column_dimensions[c].hidden = True
    for r, (lab, val, lst) in zip((1, 2, 3), [(c[1], c[2], c[3]) for c in ctrl]):
        pc.merge_cells(f"B{r}:C{r}")
        pc[f"B{r}"] = lab; pc[f"B{r}"].font = f(9, color="666666")
        pc[f"D{r}"] = val; pc[f"D{r}"].font = f(11, True, "0000FF"); pc[f"D{r}"].fill = fill(YEL)
        pc[f"D{r}"].alignment = CENTER; pc[f"D{r}"].border = BOX
        d = DataValidation(type="list", formula1=lst, allow_blank=False)
        pc.add_data_validation(d); d.add(f"D{r}")
    pc["Z1"] = '=IF($D$1="Poäng",1,IF($D$1="Mål",2,IF($D$1="Assist",3,4)))'
    pc["Z2"] = '=IF($D$2="Alla",99,$D$2*1)'
    pc.merge_cells("B5:J5"); pc.merge_cells("B6:J6")
    style_range(pc, "B5:J6", fl=fill(NAVY))
    pc["B5"] = '=Spelare!$B$3&"  ·  "&CHOOSE($Z$1,"Poängliga","Målliga","Assistliga","Utvisningsliga")'
    pc["B5"].font = f(24, True, "FFFFFF"); pc["B5"].alignment = Alignment(horizontal="left", vertical="center", indent=1)
    pc["B6"] = '=Spelare!$B$4&"  ·  Säsong "&Spelare!$B$5'
    pc["B6"].font = f(11, color="A9B8CE"); pc["B6"].alignment = Alignment(horizontal="left", vertical="center", indent=1)
    pc.row_dimensions[5].height = 42; pc.row_dimensions[6].height = 22
    cards = [("B", "D", "Mål (lag)", f'=COUNT({MR("C")})'),
             ("E", "G", "Assist", f'=COUNT({MR("D")})+COUNT({MR("E")})'),
             ("H", "I", "Utv.min", f'=SUM({MR("M")})'),
             ("J", "J", "Spelare med poäng", f'=COUNTIF(Spelare!$G${P1}:$G${P2},">0")')]
    for a, b, lab, fm in cards:
        if a != b: pc.merge_cells(f"{a}8:{b}8"); pc.merge_cells(f"{a}9:{b}9")
        pc[f"{a}8"] = lab; pc[f"{a}9"] = fm
        style_range(pc, f"{a}8:{b}8", font=f(9, True, "666666"), fl=fill(LIGHT), al=CENTER)
        style_range(pc, f"{a}9:{b}9", font=f(22, True, NAVY), fl=fill(LIGHT), al=CENTER)
    pc.row_dimensions[9].height = 36
    H, D0, DN = 11, 12, 30
    DL = D0 + DN - 1
    for c, h in zip("BCDEFGHI", ["#", "Nr", "Spelare", "Pos", "Mål", "Assist", "Poäng", "Utv.min"]):
        pc[f"{c}{H}"] = h
    pc[f"J{H}"] = '=CHOOSE($Z$1,"Poäng","Mål","Assist","Utv.min")'
    style_range(pc, f"B{H}:J{H}", font=f(11, True, "FFFFFF"), fl=fill(BLUE), al=CENTER)
    pc[f"D{H}"].alignment = LEFT; pc.row_dimensions[H].height = 26
    pc[f"AF{H}"] = f"=J{H}"
    for i in range(DN):
        r = D0 + i
        pc[f"Z{r}"] = i + 1
        pc[f"AA{r}"] = f'=IFERROR(LARGE(INDEX({KEYS},0,$Z$1),Z{r}),"")'
        pc[f"AB{r}"] = f'=IF(AA{r}="","",MATCH(AA{r},INDEX({KEYS},0,$Z$1),0))'
        pc[f"AC{r}"] = f'=IF(AB{r}="","",INT(AA{r}/10000000))'
        pc[f"AD{r}"] = f'=IF(AB{r}="",FALSE,AND(Z{r}<=$Z$2,OR($D$3="Nej",AC{r}>0)))'
        pc[f"AE{r}"] = (f'=IF(AD{r},1,"")' if i == 0 else f'=IF(AD{r},IF(AC{r}=AC{r-1},AE{r-1},Z{r}),"")')
        pc[f"AF{r}"] = f'=IF(AD{r},AC{r},"")'
        pc[f"B{r}"] = f'=IF($AD{r},$AE{r},"")'
        pc[f"C{r}"] = f'=IF($AD{r},INDEX(Spelare!$A${P1}:$A${P2},$AB{r}),"")'
        pc[f"D{r}"] = f'=IF($AD{r},INDEX(Spelare!$B${P1}:$B${P2},$AB{r}),"")'
        pc[f"E{r}"] = f'=IF($AD{r},INDEX(Spelare!$D${P1}:$D${P2},$AB{r}),"")'
        for col, sc in zip("FGHI", "EFGH"):
            pc[f"{col}{r}"] = f'=IF($AD{r},INDEX(Spelare!${sc}${P1}:${sc}${P2},$AB{r}),"")'
        pc[f"J{r}"] = f'=IF($AD{r},$AC{r},"")'
        pc.row_dimensions[r].height = 22
    style_range(pc, f"B{D0}:J{DL}", font=f(12), al=CENTER)
    style_range(pc, f"D{D0}:D{DL}", al=LEFT)
    style_range(pc, f"B{D0}:B{DL}", font=f(12, True, NAVY))
    style_range(pc, f"F{D0}:J{DL}", nf='0;-0;"-"')
    style_range(pc, f"AF{D0}:AF{DL}", nf="0;;;")
    pc.conditional_formatting.add(f"F{D0}:I{DL}", FormulaRule(
        formula=[f'AND($D{D0}<>"",COLUMN(F{D0})=CHOOSE($Z$1,8,6,7,9))'], fill=fill(HILITE),
        font=Font(name=FONT, bold=True, size=12)))
    for val, col in ((1, GOLD), (2, SILVER), (3, BRONZE)):
        pc.conditional_formatting.add(f"B{D0}:B{DL}", FormulaRule(formula=[f'AND($D{D0}<>"",$B{D0}={val})'], fill=fill(col)))
    pc.conditional_formatting.add(f"B{D0}:J{DL}", FormulaRule(
        formula=[f'AND($D{D0}<>"",MOD(ROW(),2)=0)'], fill=fill(BAND),
        border=Border(bottom=Side(style="thin", color="D5DCE6"))))
    pc.conditional_formatting.add(f"B{D0}:J{DL}", FormulaRule(
        formula=[f'$D{D0}<>""'], border=Border(bottom=Side(style="thin", color="D5DCE6"))))
    pc.conditional_formatting.add(f"J{D0}:J{DL}", DataBarRule(start_type="num", start_value=0, end_type="max", color="5B8DEF"))

    ch = BarChart(); ch.type = "bar"; ch.style = 10
    ch.title = "Topp 10"; ch.title.overlay = False
    ch.add_data(Reference(pc, min_col=32, min_row=H, max_row=D0 + 9), titles_from_data=True)
    ch.set_categories(Reference(pc, min_col=4, min_row=D0, max_row=D0 + 9))
    ch.legend = None; ch.roundedCorners = False
    ch.x_axis.scaling.orientation = "maxMin"; ch.x_axis.delete = False
    ch.y_axis.delete = True; ch.y_axis.majorGridlines = None
    ch.dataLabels = DataLabelList(); ch.dataLabels.showVal = True
    ch.dataLabels.showSerName = ch.dataLabels.showCatName = ch.dataLabels.showLegendKey = False
    ch.series[0].graphicalProperties.solidFill = BLUE
    ch.gapWidth = 40; ch.visible_cells_only = False
    ch.width, ch.height = 17, 11
    pc.add_chart(ch, "L5")
    pc.page_setup.orientation = "landscape"
    pc.sheet_properties.pageSetUpPr.fitToPage = True
    pc.page_setup.fitToWidth = 1; pc.page_setup.fitToHeight = 0

    # ------------------------------------------------------------------ demo
    if demo:
        random.seed(3)
        nums = [p[0] for p in PLAYERS if p[2] == "UP"]
        w = [5, 2, 3, 6, 4, 1, 3, 2, 1, 1, 2, 1, 2, 1, 1]
        rows = []
        for i in range(36):
            sc = random.choices(nums, w)[0]
            a1 = random.choice([n for n in nums if n != sc]) if random.random() < .8 else None
            a2 = random.choice([n for n in nums if n not in (sc, a1)]) if a1 and random.random() < .5 else None
            rows.append((sc, a1, a2))
        for i, (sc, a1, a2) in enumerate(rows):
            r = M1 + i
            mt[f"A{r}"] = datetime.date(2026, 10, 4) + datetime.timedelta(days=7 * (i // 6))
            mt[f"B{r}"] = "Demo IK"
            mt[f"C{r}"], mt[f"D{r}"], mt[f"E{r}"] = sc, a1, a2
        pens = [(20, 2), (43, 2), (20, 4), (6, 2), (11, 2), (43, 10), (5, 2), (22, 2), (20, 2)]
        for i, (n, m) in enumerate(pens):
            r = M1 + i
            mt[f"J{r}"] = datetime.date(2026, 10, 4) + datetime.timedelta(days=7 * (i // 3))
            mt[f"K{r}"] = "Demo IK"; mt[f"L{r}"] = n; mt[f"M{r}"] = m
        wb._demo = (rows, pens)
    wb.active = 0
    wb.save(path)
    return wb


if __name__ == "__main__":
    build(sys.argv[1], demo=(len(sys.argv) > 2 and sys.argv[2] == "demo"))

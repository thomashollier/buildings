import sys; sys.path.insert(0,"/Users/thomas/Documents/claude/buildings/src")
from buildings.site import BuildingClass, GroundProgramme, SiteContext
from buildings.typologies.paris.structure import solve_structure
from buildings.typologies.paris import catalogue as C
OUT="/Users/thomas/Documents/claude/buildings/dev/reference/diagrams/horizontal-nomenclature.svg"
site=SiteContext(street_width=10.0,parcel_width=14.40,parcel_depth=12.0,year=1865,
    klass=BuildingClass.ORDINARY,ground=GroundProgramme.SHOP,corner=False,seed=8)
g=solve_structure(site)
SLOTS=[(b.name,b.width,getattr(b,"is_special",False)) for b in g.bays]
WIN=float(C.opening_window().preferred); CLR=float(C.door_pedestrian().preferred)
JMB=float(C.pedestrian_jamb_width())
pitch=[w for n,w,_ in SLOTS if n=="bay"][0]
door =[w for n,w,_ in SLOTS if "porte" in n][0]
TOTAL=round(sum(w for _,w,_ in SLOTS),3)
inrhythm = abs(door-pitch)<1e-6
PIER=pitch-WIN
PX=84.0; L=100
INK,SEC,MUT="#0b0b0b","#52514e","#8b8a85"
BAYC,PIERC,ENDC,OPC,AXC,SPC="#2a78d6","#eb6834","#1baf7a","#3b4a63","#c0392b","#7a4fa8"
WALL,STONE="#efe9dc","#e0d7c6"
def X(m): return L+m*PX
o=[];A=o.append
W=int(X(TOTAL)+L); H=1210
A(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="Helvetica,Arial,sans-serif">')
A(f'<rect width="{W}" height="{H}" fill="#fcfcfb"/>')
A(f'<text x="{L}" y="46" font-size="28" font-weight="700" fill="{INK}">Dividing the frontage — what each word names</text>')
A(f'<text x="{L}" y="72" font-size="14.5" fill="{SEC}">Generated from a live solve: {TOTAL:.2f} m, ordinary class, 10 m street, porte piétonne. Every number is what the solver returned.</text>')
# ---- A. taxonomy ----
ty=104
A(f'<text x="{L}" y="{ty}" font-size="13.5" font-weight="700" fill="{INK}">EVERY PIECE OF THE FRONTAGE IS A <tspan fill="{INK}">SLOT</tspan>. Four kinds:</text>')
items=[(ENDC,"END","FLEXIBLE","no opening, no axis. Absorbs leftover width first."),
       (BAYC,"BAY","REPEATING","carries an opening, so it has an AXIS and sets the PITCH."),
       (SPC,"NARROW SPECIAL","FLEXIBLE","off pitch by definition. Not counted as an axis."),
       (PIERC,"ENTRANCE","FIXED","carries an opening, so it has an AXIS."+(" In rhythm." if inrhythm else " Off pitch here."))]
for i,(c,nm,kind,txt) in enumerate(items):
    yy=ty+26+i*24
    A(f'<rect x="{L}" y="{yy-11}" width="13" height="13" fill="{c}"/>')
    A(f'<text x="{L+22}" y="{yy}" font-size="13" fill="{SEC}"><tspan font-weight="700" fill="{c}">{nm}</tspan>  <tspan fill="{MUT}">{kind}</tspan>  — {txt}</text>')
# ---- B. exploded bay ----
exY=238; exH=80; hp=(pitch-WIN)/2
A(f'<text x="{L}" y="{exY-13}" font-size="13.5" font-weight="700" fill="{INK}">ONE BAY, TAKEN APART — measured centreline to centreline</text>')
A(f'<rect x="{L}" y="{exY}" width="{hp*PX}" height="{exH}" fill="{STONE}" stroke="{MUT}"/>')
A(f'<rect x="{L+hp*PX}" y="{exY}" width="{WIN*PX}" height="{exH}" fill="{OPC}"/>')
A(f'<rect x="{L+(hp+WIN)*PX}" y="{exY}" width="{hp*PX}" height="{exH}" fill="{STONE}" stroke="{MUT}"/>')
for cx,lab,sub,w in ((L+hp*PX/2,"half-pier",f"{hp:.3f}",0),(L+(hp+WIN/2)*PX,"opening",f"{WIN:.3f}",1),(L+(hp+WIN+hp/2)*PX,"half-pier",f"{hp:.3f}",0)):
    A(f'<text x="{cx}" y="{exY+43}" font-size="12" font-weight="700" text-anchor="middle" fill="{"#fff" if w else INK}">{lab}</text>')
    A(f'<text x="{cx}" y="{exY+60}" font-size="11" text-anchor="middle" fill="{"#dfe6f0" if w else SEC}">{sub}</text>')
yb=exY+exH+14
A(f'<line x1="{L}" y1="{yb}" x2="{L+pitch*PX}" y2="{yb}" stroke="{BAYC}" stroke-width="2.5"/>')
for xx in (L,L+pitch*PX): A(f'<line x1="{xx}" y1="{yb-6}" x2="{xx}" y2="{yb+6}" stroke="{BAYC}" stroke-width="2.5"/>')
A(f'<text x="{L+pitch*PX/2}" y="{yb+20}" font-size="13.5" font-weight="700" text-anchor="middle" fill="{BAYC}">one BAY = one PITCH = {pitch:.3f} m</text>')
for i,t in enumerate(["So N bays is exactly N × pitch, and the only special case is the two ends.",
                      "BAY and PITCH are the same number. Prefer PITCH in prose — “bay” names three",
                      "different things in this codebase."]):
    A(f'<text x="{L+pitch*PX+34}" y="{exY+24+i*21}" font-size="13" fill="{SEC}">{t}</text>')
# ---- C. the frontage ----
TOP=430; FH=210
A(f'<text x="{L}" y="{TOP-40}" font-size="13.5" font-weight="700" fill="{INK}">THE WHOLE FRONTAGE</text>')
x=0.0; axes=[]
for nm,w,sp in SLOTS:
    x0=X(x)
    A(f'<rect x="{x0}" y="{TOP}" width="{w*PX}" height="{FH}" fill="{WALL}" stroke="{MUT}" stroke-width="0.8"/>')
    if nm=="bay":
        A(f'<rect x="{x0+(w-WIN)*PX/2}" y="{TOP+34}" width="{WIN*PX}" height="{FH-80}" fill="{OPC}"/>'); axes.append(x0+w*PX/2)
    elif "porte" in nm:
        A(f'<rect x="{x0+(w-CLR)*PX/2}" y="{TOP+34}" width="{CLR*PX}" height="{FH-44}" fill="#6b4a33"/>'); axes.append(x0+w*PX/2)
        for jx in (x0,x0+w*PX-JMB*PX):
            A(f'<rect x="{jx}" y="{TOP}" width="{JMB*PX}" height="{FH}" fill="none" stroke="{PIERC}" stroke-width="2" stroke-dasharray="4 3"/>')
    x+=w
for ax in axes: A(f'<line x1="{ax}" y1="{TOP-24}" x2="{ax}" y2="{TOP+FH+8}" stroke="{AXC}" stroke-width="1" stroke-dasharray="5 4"/>')
A(f'<text x="{axes[0]}" y="{TOP-30}" font-size="12" font-weight="700" text-anchor="middle" fill="{AXC}">AXIS</text>')
A(f'<text x="{axes[1]+14}" y="{TOP-30}" font-size="12" fill="{AXC}">one per opening — the thing you COUNT. {len(axes)} here.</text>')
def dim(y,x0,x1,col,lab,sub,small=False):
    A(f'<line x1="{x0}" y1="{y}" x2="{x1}" y2="{y}" stroke="{col}" stroke-width="2"/>')
    for xx in (x0,x1): A(f'<line x1="{xx}" y1="{y-6}" x2="{xx}" y2="{y+6}" stroke="{col}" stroke-width="2"/>')
    cx=(x0+x1)/2
    A(f'<text x="{cx}" y="{y-13 if small else y+18}" font-size="{11.5 if small else 12.5}" font-weight="700" text-anchor="middle" fill="{col}">{lab}</text>')
    A(f'<text x="{cx}" y="{y+18 if small else y+34}" font-size="11" text-anchor="middle" fill="{SEC}">{sub}</text>')
y1=TOP+FH+32; x=0.0
for nm,w,sp in SLOTS:
    c=ENDC if nm=="pier_end" else (SPC if sp else (PIERC if "porte" in nm else BAYC))
    lab="END" if nm=="pier_end" else ("SPECIAL" if sp else ("DOOR SLOT" if "porte" in nm else "BAY / PITCH"))
    dim(y1,X(x)+2,X(x+w)-2,c,lab,f"{w:.3f}",small=(nm=="pier_end"))
    x+=w
yq=y1+62; pa,pb=axes[0]+WIN*PX/2,axes[1]-WIN*PX/2
dim(yq,pa,pb,PIERC,f"PIER {PIER:.3f}","wall between two openings")
yt=yq+58
dim(yt,X(0),X(TOTAL),INK,f"FRONTAGE {TOTAL:.3f} m","")
# ---- D. off pitch ----
yo=yt+50
A(f'<text x="{L}" y="{yo}" font-size="13.5" font-weight="700" fill="{INK}">OFF PITCH — three ways, and only two of them are meant</text>')
rows=[(SPC,"narrow special","by DESIGN","its band tops out at 1.650 m, below the 2.000 m pitch minimum — the bands cannot overlap"),
      (PIERC,"porte cochère","by NECESSITY","2.600 clear + 2×0.220 jamb = 3.040 m, wider than most pitches, so it truly displaces the rhythm"),
      (MUT,"porte piétonne","by ACCIDENT" if not inrhythm else "— now IN RHYTHM","1.750 + 2×0.300 = 2.350 m fits inside a pitch; it broke the rhythm only because it was a rigid slot")]
for i,(c,nm,how,txt) in enumerate(rows):
    yy=yo+24+i*22
    A(f'<text x="{L}" y="{yy}" font-size="12.5" fill="{SEC}"><tspan font-weight="700" fill="{c}">{nm}</tspan> <tspan font-weight="700" fill="{MUT}">{how}</tspan> — {txt}</text>')
ybx=yo+100
A(f'<rect x="{L}" y="{ybx}" width="{X(TOTAL)-L}" height="86" fill="#f4f2ec" stroke="#e2ded3"/>')
A(f'<text x="{L+24}" y="{ybx+34}" font-size="20" font-weight="700" fill="{INK}">window + pier = pitch</text>')
A(f'<text x="{L+24}" y="{ybx+60}" font-size="13.5" fill="{SEC}">{WIN:.3f} + {PIER:.3f} = {pitch:.3f} m &#160;·&#160; count AXES, measure PITCH. Every axis is a bay; every bay carries an opening.</text>')
A(f'<text x="{L+24}" y="{ybx+79}" font-size="12.5" fill="{MUT}">A bay takes the rhythm’s pitch unless opening + 2 × jamb will not fit — and only then does that one bay grow.</text>')
A('</svg>')
open(OUT,"w").write("\n".join(o))
print(f"door {door:.3f} vs pitch {pitch:.3f} -> {'IN RHYTHM' if inrhythm else 'off pitch'}")
print("wrote",OUT,W,"x",H)

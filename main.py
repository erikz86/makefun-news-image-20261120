"""Deterministic, dependency-free bitmap newspaper. No input files are read."""
import os
import struct
import zlib
import math

W = H = 1024
PAPER=(243,236,219); INK=(26,24,20); GREY=(74,68,58); RED=(164,30,30)
BLUE=(30,56,94); SKY=(178,205,222); SEA=(44,96,128); GOLD=(198,152,32)
GREEN=(34,110,62); RULE=(140,132,118); WHITE=(255,255,255); BROWN=(122,84,52)
# Each glyph is seven rows of five binary pixels, authored for this page.
FONT = {}
GLYPHS = {
'A':'01110 10001 10001 11111 10001 10001 10001','B':'11110 10001 10001 11110 10001 10001 11110',
'C':'01111 10000 10000 10000 10000 10000 01111','D':'11110 10001 10001 10001 10001 10001 11110',
'E':'11111 10000 10000 11110 10000 10000 11111','F':'11111 10000 10000 11110 10000 10000 10000',
'G':'01111 10000 10000 10111 10001 10001 01111','H':'10001 10001 10001 11111 10001 10001 10001',
'I':'11111 00100 00100 00100 00100 00100 11111','J':'00111 00010 00010 00010 10010 10010 01100',
'K':'10001 10010 10100 11000 10100 10010 10001','L':'10000 10000 10000 10000 10000 10000 11111',
'M':'10001 11011 10101 10101 10001 10001 10001','N':'10001 11001 10101 10011 10001 10001 10001',
'O':'01110 10001 10001 10001 10001 10001 01110','P':'11110 10001 10001 11110 10000 10000 10000',
'Q':'01110 10001 10001 10001 10101 10010 01101','R':'11110 10001 10001 11110 10100 10010 10001',
'S':'01111 10000 10000 01110 00001 00001 11110','T':'11111 00100 00100 00100 00100 00100 00100',
'U':'10001 10001 10001 10001 10001 10001 01110','V':'10001 10001 10001 10001 10001 01010 00100',
'W':'10001 10001 10001 10101 10101 10101 01010','X':'10001 10001 01010 00100 01010 10001 10001',
'Y':'10001 10001 01010 00100 00100 00100 00100','Z':'11111 00001 00010 00100 01000 10000 11111',
'0':'01110 10001 10011 10101 11001 10001 01110','1':'00100 01100 00100 00100 00100 00100 01110',
'2':'01110 10001 00001 00010 00100 01000 11111','3':'11110 00001 00001 01110 00001 00001 11110',
'4':'00010 00110 01010 10010 11111 00010 00010','5':'11111 10000 10000 11110 00001 00001 11110',
'6':'01110 10000 10000 11110 10001 10001 01110','7':'11111 00001 00010 00100 01000 01000 01000',
'8':'01110 10001 10001 01110 10001 10001 01110','9':'01110 10001 10001 01111 00001 00001 01110',
' ':'00000 00000 00000 00000 00000 00000 00000','-':'00000 00000 00000 11111 00000 00000 00000',
'.':'00000 00000 00000 00000 00000 00110 00110',',':'00000 00000 00000 00000 00110 00100 01000',
"'":'00100 00100 01000 00000 00000 00000 00000','$':'00100 01111 10100 01110 00101 11110 00100',
'%':'11001 11010 00100 01000 10110 00110 00000','/':'00001 00010 00010 00100 01000 01000 10000'}
FONT={c:rows.split() for c,rows in GLYPHS.items()}
PIX=bytearray(bytes(PAPER)*(W*H))
TEXT_BOXES=[]
def rect(x,y,w,h,c):
    assert 0<=x<=x+w<=W and 0<=y<=y+h<=H
    row=bytes(c)*w
    for yy in range(y,y+h): PIX[(yy*W+x)*3:(yy*W+x+w)*3]=row
def line(x0,y0,x1,y1,c,thick=1):
    dx=abs(x1-x0); sx=1 if x0<x1 else -1
    dy=-abs(y1-y0); sy=1 if y0<y1 else -1; err=dx+dy
    while True:
        rect(x0,y0,thick,thick,c)
        if x0==x1 and y0==y1: break
        e=2*err
        if e>=dy: err+=dy; x0+=sx
        if e<=dx: err+=dx; y0+=sy
def outline(x,y,w,h,c,t=1):
    rect(x,y,w,t,c); rect(x,y+h-t,w,t,c); rect(x,y,t,h,c); rect(x+w-t,y,t,h,c)
def circle(cx,cy,r,c):
    for dy in range(-r,r+1):
        dx=math.isqrt(r*r-dy*dy); rect(cx-dx,cy+dy,2*dx+1,1,c)
def polygon(points,c):
    for y in range(min(p[1] for p in points),max(p[1] for p in points)+1):
        xs=[]
        for (x1,y1),(x2,y2) in zip(points,points[1:]+points[:1]):
            if min(y1,y2)<=y<max(y1,y2): xs.append(x1+(y-y1)*(x2-x1)/(y2-y1))
        xs.sort()
        for a,b in zip(xs[::2],xs[1::2]):
            lo=math.ceil(a); hi=math.floor(b)
            if hi>=lo: rect(lo,y,hi-lo+1,1,c)
def star(x,y,r,c):
    polygon([(round(x+math.cos(-math.pi/2+i*math.pi/5)*(r if i%2==0 else r*.42)),round(y+math.sin(-math.pi/2+i*math.pi/5)*(r if i%2==0 else r*.42))) for i in range(10)],c)
def advance(s): return 11 if s==2 else 6*s
def width(t,s): return len(t)*advance(s)-(advance(s)-5*s) if t else 0
def text(t,x,y,s=2,c=INK):
    assert t.isascii() and t==t.upper()
    assert 0<=x and x+width(t,s)<=W and 0<=y and y+7*s<=H
    TEXT_BOXES.append((x,y,x+width(t,s),y+7*s,t))
    for ch in t:
        for yy,row in enumerate(FONT[ch]):
            for xx,v in enumerate(row):
                if v=='1': rect(x+xx*s,y+yy*s,s,s,c)
        x+=advance(s)
def centered(t,y,s=2,c=INK,x=24,w=976): text(t,x+(w-width(t,s))//2,y,s,c)
def wrap(t,w,s=2):
    rows=[]; current=''
    for word in t.split():
        trial=(current+' '+word).strip()
        if width(trial,s)>w:
            assert current; rows.append(current); current=word
        else: current=trial
    if current: rows.append(current)
    assert all(width(row,s)<=w for row in rows)
    return rows
def paragraphs(items,x,y,w,bottom,gap=10):
    count=0
    for i,p in enumerate(items):
        if i: y+=gap
        for row in wrap(p,w): text(row,x,y,2,GREY); y+=20; count+=1
    assert y-6<=bottom,(items,y,bottom)
    return count

def render():
    outline(6,6,1012,1012,INK,2); outline(12,12,1000,1000,RULE)
    centered('THE WORLD TODAY',30,6); rect(24,106,976,2,INK)
    centered('FRIDAY, 20 NOVEMBER 2026  -  SHENZHEN - WASHINGTON - LONDON',116)
    rect(24,138,976,1,RULE)
    centered('THREE CHAIRS, NO TREATY',150,4,RED)
    centered('TRUMP, XI AND PUTIN MEET IN SHENZHEN - AND LEAVE WITH NO ARMS DEAL',192)
    rect(24,216,976,3,INK)
    rect(24,228,476,224,SKY)
    for x,y,w in [(30,300,38),(74,275,40),(120,310,30),(158,257,38),(204,291,44),(256,270,30),(294,301,43),(345,253,35),(391,283,42),(445,305,48)]:
        rect(x,y,w,115 if y<330 else 90,BLUE)
        for xx in range(x+7,x+w-4,12):
            for yy in range(y+9,365,16): rect(xx,yy,3,5,GOLD)
    for x in [91,231,371]: rect(x,241,3,151,INK)
    rect(94,244,80,42,WHITE)
    for yy in range(244,286,7): rect(94,yy,80,3,RED)
    rect(94,244,34,24,BLUE)
    for xx in range(98,125,7):
        for yy in range(248,266,7): rect(xx,yy,2,2,WHITE)
    rect(234,244,80,42,RED); star(249,258,9,GOLD)
    for xx,yy in [(264,249),(272,256),(272,266),(263,275)]: star(xx,yy,3,GOLD)
    rect(374,244,80,14,WHITE); rect(374,258,80,14,BLUE); rect(374,272,80,14,RED)
    rect(24,379,476,73,PAPER)
    for x in [107,247,387]:
        rect(x,345,34,42,INK); rect(x-4,380,42,8,INK); rect(x,388,4,24,INK); rect(x+30,388,4,24,INK)
    rect(66,385,392,18,BROWN); rect(80,403,8,17,BROWN); rect(436,403,8,17,BROWN)
    centered('THE TRILATERAL TABLE - SHENZHEN',432,2,INK,24,476)
    lead=['THE FIRST MEETING OF THE THREE NUCLEAR POWERS ENDS WITHOUT AN AGREEMENT. NO DEAL WAS EXPECTED, A SENIOR US OFFICIAL SAID.', 'NEW START, THE TREATY THAT CAPPED US AND RUSSIAN ARSENALS, EXPIRED IN FEBRUARY. CHINA SAYS JOINING TALKS IS NEITHER FAIR NOR REALISTIC.', 'UKRAINE WAS NOT ON THE AGENDA. THE LEADERS MET ON THE SIDELINES OF APEC IN SHENZHEN.']
    assert paragraphs(lead,516,228,484,452)<=10
    rect(24,466,976,1,RULE)
    text('THE GULF WAR WIDENS',24,480,3); text('GRANDTHROPIC DAY',524,480,3)
    rect(24,512,476,92,SKY); rect(24,559,476,45,SEA); circle(73,535,15,GOLD)
    for x,y,r in [(298,541,13),(310,531,16),(329,521,9),(286,549,10)]: circle(x,y,r,RULE)
    polygon([(269,568),(280,536),(290,555),(302,540),(315,570)],RED)
    polygon([(279,568),(285,550),(291,562),(299,552),(303,568)],GOLD)
    rect(201,544,33,24,INK); rect(207,538,22,8,RED)
    polygon([(123,565),(401,565),(376,588),(149,588)],INK); line(143,576,386,576,RED,2)
    for x in range(39,480,69): line(x,596,x+34,596,WHITE)
    rect(524,512,476,92,PAPER); outline(539,521,294,72,RULE)
    for yy in [540,560,580]: line(540,yy,832,yy,RULE)
    pts=[(549,580),(581,571),(616,577),(653,553),(691,558),(729,539),(766,544),(817,526)]
    for a,b in zip(pts,pts[1:]): line(*a,*b,GREEN,3)
    for x,y in pts: circle(x,y,4,GREEN)
    text('ANT',554,527,2,GREEN); circle(919,557,40,GOLD); text('VI',897,543,4)
    paragraphs(['IRAN FIRED ON US BASES IN KUWAIT AND BAHRAIN AFTER THE US HIT A MISSILE SITE ON QESHM ISLAND.', 'THE TANKER NAVIG8 MESSI BURNED IN THE STRAIT OF HORMUZ. 18 SHIP ATTACKS HAVE BEEN COUNTED THERE THIS MONTH.'],24,614,476,728,gap=0)
    paragraphs(['GTA VI IS OUT WORLDWIDE AFTER 13 YEARS. PRE-ORDERS TOPPED 15.9 MILLION COPIES, WORTH $1.54 BILLION.', 'ON THE SAME DAY, ANTHROPIC LISTS ON NASDAQ AS ANT, PRICED AT $83 A SHARE IN AN $81 BILLION IPO.'],524,614,476,728,gap=0)
    rect(24,736,976,1,RULE)
    briefs=[('UKRAINE','THE KERCH BRIDGE IS HIT AGAIN. ITS ROAD ARCH FALLS INTO THE STRAIT.'),('HEALTH','EBOLA IN DR CONGO PASSES 11,200 CASES AND 5,500 DEATHS. SEVEN IN TEN CHILDREN UNDER FIVE DO NOT SURVIVE.'),('WEATHER',"SEVERE CYCLONE AKVAN BEARS DOWN ON INDIA'S EAST COAST, WITH WINDS OF 90 TO 110 KM/H.")]
    for x,(title,body) in zip([24,352,680],briefs):
        text(title,x,750,2,RED); paragraphs([body],x,780,312,884)
    for x in [343,671]: rect(x,750,1,134,RULE)
    rect(24,896,976,40,INK)
    centered('TTWO $209 - ANT $83 - GTA VI 15.88M PRE-ORDERS - GOLD $3,663 - SP 500 -2.02%',908,2,WHITE)
    centered('ONE IMAGE, ONE DAY, THE WHOLE WORLD - FRIDAY 20 NOVEMBER 2026',958)
    centered('THE WORLD TODAY',984,1)
    # Text rectangles must never overlap, including across columns and panels.
    for i,a in enumerate(TEXT_BOXES):
        for b in TEXT_BOXES[i+1:]:
            assert not (a[0]<b[2] and b[0]<a[2] and a[1]<b[3] and b[1]<a[3]),(a,b)

def png():
    def chunk(kind,data):
        return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data)&0xffffffff)
    raw=b''.join(b'\0'+PIX[y*W*3:(y+1)*W*3] for y in range(H))
    return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',W,H,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(raw,9))+chunk(b'IEND',b'')

if __name__=='__main__':
    render()
    destination=os.environ.get('MAKEFUN_OUTPUT_DIR','/output')
    os.makedirs(destination,exist_ok=True)
    with open(os.path.join(destination,'entry.png'),'wb') as output: output.write(png())

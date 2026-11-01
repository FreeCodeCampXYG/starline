"""生成冰雾浅蓝底、黑客松高对比版产品介绍海报。"""

from pathlib import Path
import sys
import math

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(r"D:\MyPro\brainwave")
OUT = ROOT / "outputs" / "health-reminder-poster"
OUT.mkdir(parents=True, exist_ok=True)
W, H = 2400, 5400
BG = "#EEF7FB"
NAVY = "#071A3A"
BLUE = "#1556D8"
CYAN = "#42DDE9"
LIME = "#B6F22E"
ORANGE = "#FF7657"
GREY = "#5D718C"
LINE = "#C6D9E6"
WHITE = "#FFFFFF"
CN = r"C:\Windows\Fonts\STXINGKA.TTF"
CN_BOLD = r"C:\Windows\Fonts\msyhbd.ttc"
EN = r"C:\Windows\Fonts\AGENCYB.TTF"


def ft(size, en=False, art=False):
    """加载中文艺术字体、中文重体或窄体英文字体。"""
    path = EN if en else CN if art else CN_BOLD
    return ImageFont.truetype(path, size=size, index=0)


def txt(draw, xy, value, size, fill=NAVY, en=False, art=False, anchor="la"):
    """绘制海报文字。"""
    draw.text(xy, value, font=ft(size, en, art), fill=fill, anchor=anchor)


def soft_panel(canvas, box, radius=35):
    """绘制带柔和投影的浅色产品卡片。"""
    x, y, w, h = box
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    ImageDraw.Draw(layer).rounded_rectangle((x+12, y+24, x+w+12, y+h+24), radius=radius, fill=(18, 70, 120, 30))
    layer = layer.filter(ImageFilter.GaussianBlur(26))
    canvas.paste(layer, (0, 0), layer)
    ImageDraw.Draw(canvas).rounded_rectangle((x, y, x+w, y+h), radius=radius, fill=WHITE, outline=(255,255,255,220), width=4)


def wave(canvas, points, color, width=8):
    """绘制发光声波。"""
    layer = Image.new("RGBA", canvas.size, (0,0,0,0))
    ImageDraw.Draw(layer).line(points, fill=color, width=30, joint="curve")
    layer = layer.filter(ImageFilter.GaussianBlur(16))
    canvas.paste(layer, (0,0), layer)
    ImageDraw.Draw(canvas).line(points, fill=color, width=width, joint="curve")


def sphere(canvas, cx, cy, r):
    """绘制钴蓝声波球体。"""
    draw = ImageDraw.Draw(canvas)
    for i in range(220, 0, -1):
        q = i / 220
        t = 1 - q
        col = (int(4 + 24*t), int(30 + 92*t), int(105 + 140*t))
        draw.ellipse((cx-r*q, cy-r*q, cx+r*q, cy+r*q), fill=col)
    draw.ellipse((cx-r, cy-r, cx+r, cy+r), outline=CYAN, width=9)
    for i in range(-2, 4):
        yy = cy + i*r*.22
        ww = math.sqrt(max(1, r*r-(yy-cy)**2))
        draw.arc((cx-ww, yy-r*.18, cx+ww, yy+r*.18), 180, 360, fill=CYAN if i%2 else BLUE, width=5)
    pts=[]
    for i in range(140):
        t=i/139
        x=cx-r*.86+t*r*1.72
        env=math.sin(math.pi*t)**.55
        y=cy-(.12+abs(math.sin(t*17*math.pi))*.27)*r*env
        pts.append((x,y))
    wave(canvas,pts,(28,168,255,255),9)
    draw=ImageDraw.Draw(canvas)
    draw.arc((cx-r*1.43,cy-r*.43,cx+r*1.43,cy+r*.43),185,355,fill=LIME,width=7)
    draw.arc((cx-r*1.56,cy-r*.53,cx+r*1.56,cy+r*.53),195,345,fill=BLUE,width=5)
    for x,y,c in ((cx-r*.96,cy-r*.28,LIME),(cx+r*.86,cy-r*.1,CYAN),(cx+r*.2,cy+r*.95,ORANGE)):
        draw.ellipse((x-14,y-14,x+14,y+14),fill=c)


def mode_row(draw, x, y, number, title, desc, color):
    """绘制编号式产品能力信息。"""
    txt(draw,(x,y),number,78,color,en=True)
    draw.line((x+126,y+8,x+126,y+92),fill=color,width=4)
    txt(draw,(x+190,y+4),title,45,NAVY)
    txt(draw,(x+190,y+63),desc,27,GREY)


def main():
    """生成产品介绍风格的冰雾浅蓝海报。"""
    canvas=Image.new("RGBA",(W,H),BG)
    draw=ImageDraw.Draw(canvas)
    # Large soft color fields.
    layer=Image.new("RGBA",canvas.size,(0,0,0,0))
    ld=ImageDraw.Draw(layer)
    ld.ellipse((-500,500,1300,2400),fill=(66,221,233,70))
    ld.ellipse((1300,700,2900,2500),fill=(45,105,235,54))
    layer=layer.filter(ImageFilter.GaussianBlur(150)); canvas.paste(layer,(0,0),layer)
    draw=ImageDraw.Draw(canvas)
    board=ROOT/"主板图.jpeg"
    avatar=Path(r"C:\Users\xiaoy\AppData\Local\Temp\codex-clipboard-ee7e27d5-a335-4122-aeb1-3db9d6734c30.jpg")

    # Header
    txt(draw,(135,85),"焊门子弟   /   AI HARDWARE",28,GREY,en=True)
    if avatar.exists():
        av=Image.open(avatar).convert("RGB").resize((154,154))
        mask=Image.new("L",(154,154),0); ImageDraw.Draw(mask).ellipse((0,0,154,154),fill=255)
        av.putalpha(mask); canvas.paste(av,(2110,55),av)
        ImageDraw.Draw(canvas).ellipse((2110,55,2264,209),outline=WHITE,width=6)
    txt(draw,(135,285),"故事搭子",245,BLUE,art=True)
    txt(draw,(150,590),"一声唤醒，故事就开始了。",58,NAVY)
    txt(draw,(155,680),"VOICE-FIRST DESKTOP COMPANION",29,BLUE,en=True)
    draw.rounded_rectangle((155,760,640,835),radius=38,fill=BLUE)
    txt(draw,(397,798),"故事  /  笑话  /  专注",28,WHITE,anchor="mm")

    # Main hero card
    soft_panel(canvas,(100,980,2200,2060),radius=48)
    draw=ImageDraw.Draw(canvas)
    txt(draw,(170,1060),"产品概念 / PRODUCT CONCEPT",24,BLUE,en=True)
    txt(draw,(170,1125),"把一个声音入口，做成桌面上的陪伴。",52,NAVY)
    txt(draw,(170,1210),"两天原型先完成唤醒、切换内容和真实音频回应。",30,GREY)
    sphere(canvas,1580,1790,465)
    draw=ImageDraw.Draw(canvas)
    txt(draw,(1580,1265),"AUDIO WORLD",24,BLUE,en=True,anchor="ma")
    if board.exists():
        photo=Image.open(board).convert("RGB").resize((510,760))
        mask=Image.new("L",photo.size,0); ImageDraw.Draw(mask).rounded_rectangle((0,0,510,760),radius=24,fill=255)
        photo.putalpha(mask); canvas.paste(photo,(210,1370),photo)
        ImageDraw.Draw(canvas).rounded_rectangle((210,1370,720,2130),radius=24,outline=BLUE,width=6)
    draw=ImageDraw.Draw(canvas)
    txt(draw,(210,2160),"ESP32-S3  /  REAL PROTOTYPE",21,BLUE,en=True)
    # Floating audio player overlay
    ui=(820,2540,1400,650)
    soft_panel(canvas,ui,radius=35); draw=ImageDraw.Draw(canvas)
    txt(draw,(ui[0]+55,ui[1]+46),"NOW PLAYING",21,BLUE,en=True)
    txt(draw,(ui[0]+55,ui[1]+105),"月亮邮差",50,NAVY)
    txt(draw,(ui[0]+55,ui[1]+168),"故事模式  ·  第 01 章",26,GREY)
    draw.rounded_rectangle((ui[0]+55,ui[1]+225,ui[0]+ui[2]-55,ui[1]+240),radius=7,fill=LINE)
    draw.rounded_rectangle((ui[0]+55,ui[1]+225,ui[0]+ui[2]*.55,ui[1]+240),radius=7,fill=BLUE)
    pts=[]
    for i in range(68):
        x=ui[0]+60+i*18; h=22+(i*31%108); pts.extend([(x,ui[1]+335-h/2),(x+8,ui[1]+335+h/2)])
    for i in range(0,len(pts),2):
        x0,y0=pts[i]; x1,y1=pts[i+1]; draw.rounded_rectangle((x0,y0,x1,y1),radius=3,fill=BLUE if i<74 else "#B9CEE7")
    for i,(lab,col) in enumerate((("故事",BLUE),("笑话",ORANGE),("专注",CYAN))):
        x=ui[0]+55+i*425
        draw.rounded_rectangle((x,ui[1]+465,x+375,ui[1]+545),radius=40,fill=WHITE,outline=col,width=3)
        draw.ellipse((x+23,ui[1]+492,x+49,ui[1]+518),fill=col)
        txt(draw,(x+78,ui[1]+480),lab,27,NAVY)
    txt(draw,(ui[0]+ui[2]-48,ui[1]+602),"CONCEPT UI",18,GREY,en=True,anchor="ra")

    # Function section
    sec=3500
    layered=ImageDraw.Draw(canvas)
    txt(layered,(135,sec),"三种桌面时刻",100,BLUE,art=True)
    txt(layered,(145,sec+145),"一个语音入口，从陪伴开始。",34,GREY)
    mode_row(layered,145,sec+300,"01","故事模式","继续讲 · 换一个",BLUE)
    mode_row(layered,870,sec+300,"02","笑话模式","唤醒后 · 再来一个",ORANGE)
    mode_row(layered,1595,sec+300,"03","专注模式","未来接入 · 计时提醒",CYAN)

    # Roadmap
    road=4160
    txt(layered,(145,road),"从一个故事入口，扩展成个人 AI 搭子。",42,NAVY)
    layered.line((170,road+110,2230,road+110),fill="#B8CDDF",width=5)
    for i,(tag,title,desc,col) in enumerate((("NOW","48H 原型","唤醒 / 故事 / 笑话",BLUE),("NEXT","AI 扩展","模型 / 连续对话",ORANGE),("FUTURE","个人计划","状态 / 建议 / 番茄钟",CYAN))):
        x=170+i*730; layered.ellipse((x,road+87,x+46,road+133),fill=col)
        txt(layered,(x,road+165),tag,20,col,en=True); txt(layered,(x,road+203),title,32,NAVY); txt(layered,(x,road+252),desc,23,GREY)

    # Hardware signature
    y=4780
    layered.rounded_rectangle((140,y,2260,5235),radius=34,fill=NAVY)
    txt(layered,(200,y+55),"HARDWARE SIGNATURE",21,LIME,en=True)
    vals=[("ESP32-S3","16 MB FLASH"),("FLASH VENDOR 0x46","FLASH ID 0x4018"),("MAC 68:EE:8F:44:B5:8C","TAIL B5:8C")]
    for i,pair in enumerate(vals):
        for j,val in enumerate(pair):
            x=200+j*1000; yy=y+115+i*92; txt(layered,(x,yy),val,25,WHITE if i==0 else "#B9D0E1",en=(i==0 and j==1))
    txt(layered,(W//2,5320),"焊门子弟  /  方案示意 · 原型开发中",23,BLUE,anchor="mm")

    png=OUT/"story-companion-iceblue-hackathon-v3-2400x5400.png"; pdf=OUT/"story-companion-iceblue-hackathon-v3-2400x5400.pdf"
    canvas.convert("RGB").save(png,format="PNG",optimize=True); canvas.convert("RGB").save(pdf,format="PDF",resolution=76.2)
    print(png); print(pdf)


if __name__=="__main__":
    main()

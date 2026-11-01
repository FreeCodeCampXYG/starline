"""生成冰雾浅蓝、钴蓝声波与层叠艺术字体版故事搭子海报。"""

from pathlib import Path
import math

from PIL import Image, ImageDraw, ImageFilter, ImageFont
from render_health_poster import fit_image

ROOT = Path(r"D:\MyPro\brainwave")
OUT = ROOT / "outputs" / "health-reminder-poster"
OUT.mkdir(parents=True, exist_ok=True)
W, H = 2400, 5400
BG = "#EAF5FA"
INK = "#101D38"
BLUE = "#164FE8"
BLUE2 = "#2D8DFF"
CYAN = "#62E4F2"
LIME = "#D7F45B"
ORANGE = "#FF885D"
WHITE = "#FFFFFF"
MUTED = "#5E718E"
LINE = "#C7D9E6"

FONT_CN = r"C:\Windows\Fonts\msyhbd.ttc"
FONT_ART = r"C:\Windows\Fonts\STXINGKA.TTF"
FONT_KAI = r"C:\Windows\Fonts\STKAITI.TTF"
FONT_EN = r"C:\Windows\Fonts\AGENCYB.TTF"


def f(size, en=False):
    """加载标题用中文重体或英文字体。"""
    return ImageFont.truetype(FONT_EN if en else FONT_CN, size=size, index=0)


def tx(draw, xy, value, size, color=INK, bold=True, anchor="la", en=False):
    """统一绘制中英文文字。"""
    draw.text(xy, value, font=f(size, en), fill=color, anchor=anchor)


def shadow(canvas, box, radius=38, blur=30, offset=(14, 26), color=(26, 74, 116, 34)):
    """绘制轻柔的悬浮阴影。"""
    x, y, w, h = box
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    ImageDraw.Draw(layer).rounded_rectangle((x+offset[0],y+offset[1],x+w+offset[0],y+h+offset[1]),radius=radius,fill=color)
    layer = layer.filter(ImageFilter.GaussianBlur(blur))
    canvas.paste(layer, (0, 0), layer)


def layered_type(canvas, xy, value, size, fill, depth=18, outline=None, artistic=True):
    """用多层错位挤出和细描边制作艺术标题字。"""
    x, y = xy
    ft = ImageFont.truetype(FONT_ART if artistic else FONT_CN, size=size, index=0)
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for step in range(depth, 0, -1):
        d.text((x + step*1.4, y + step*1.25), value, font=ft, fill="#9BC5EF", stroke_width=2, stroke_fill="#9BC5EF")
    d.text((x, y), value, font=ft, fill=fill, stroke_width=7, stroke_fill=outline or fill)
    d.text((x, y), value, font=ft, fill=fill, stroke_width=2, stroke_fill="#F8FFFF")
    canvas.alpha_composite(layer)
    # 狭长高光形成雕塑感字面反射。
    d = ImageDraw.Draw(canvas)
    bbox = d.textbbox((x,y),value,font=ft,stroke_width=3)
    d.line((bbox[0]+25,bbox[1]+22,bbox[2]-35,bbox[1]+22),fill=(255,255,255,205),width=7)


def glow_line(canvas, points, color, width=8, blur=28):
    """绘制有柔光的钴蓝声波线。"""
    layer = Image.new("RGBA", canvas.size, (0,0,0,0))
    ImageDraw.Draw(layer).line(points, fill=color, width=blur, joint="curve")
    layer = layer.filter(ImageFilter.GaussianBlur(blur//2))
    canvas.paste(layer,(0,0),layer)
    ImageDraw.Draw(canvas).line(points,fill=color,width=width,joint="curve")


def draw_sphere(canvas, cx, cy, r):
    """绘制带径向高光和声波轨道的抽象音频星球。"""
    draw=ImageDraw.Draw(canvas)
    for i in range(260,0,-1):
        q=i/260
        x0=cx-r*q; y0=cy-r*q; x1=cx+r*q; y1=cy+r*q
        t=1-q
        col=(int(4+25*t),int(28+86*t),int(95+140*t),255)
        draw.ellipse((x0,y0,x1,y1),fill=col)
    draw.ellipse((cx-r,cy-r,cx+r,cy+r),outline=CYAN,width=8)
    # Curved latitude paths and audio trace.
    for i, col in enumerate((BLUE2,CYAN,WHITE,CYAN)):
        yy=cy-r*0.58+i*r*0.35
        ww=math.sqrt(max(0,r*r-(yy-cy)**2))
        draw.arc((cx-ww,yy-r*.24,cx+ww,yy+r*.24),180,360,fill=col,width=5)
    wave=[]
    for i in range(150):
        t=i/149
        x=cx-r*.84+t*r*1.68
        env=math.sin(math.pi*t)**0.55
        y=cy-(.10+abs(math.sin(t*18*math.pi))*.28)*r*env
        wave.append((x,y))
    glow_line(canvas,wave,(78,178,255,255),9,35)
    draw=ImageDraw.Draw(canvas)
    # orbit traces pass behind and in front of the sphere for depth.
    draw.arc((cx-r*1.42,cy-r*.42,cx+r*1.42,cy+r*.42),185,355,fill=BLUE,width=8)
    draw.arc((cx-r*1.56,cy-r*.52,cx+r*1.56,cy+r*.52),195,345,fill=LIME,width=5)
    for x,y,c in ((cx-r*.98,cy-r*.24,LIME),(cx+r*.88,cy-r*.05,CYAN),(cx+r*.1,cy+r*.95,ORANGE)):
        draw.ellipse((x-15,y-15,x+15,y+15),fill=c)


def card(draw, box, number, title, desc, accent):
    """绘制浅色分层功能栏。"""
    x,y,w,h=box
    draw.rounded_rectangle((x,y,x+w,y+h),radius=30,fill=WHITE,outline=LINE,width=4)
    draw.rounded_rectangle((x,y,x+15,y+h),radius=7,fill=accent)
    tx(draw,(x+48,y+42),number,25,accent,en=True)
    tx(draw,(x+48,y+94),title,42,INK)
    tx(draw,(x+48,y+165),desc,26,MUTED,bold=False)


def main():
    """生成 4:9 产品介绍海报。"""
    canvas=Image.new("RGBA",(W,H),BG)
    draw=ImageDraw.Draw(canvas)
    # Soft color fields remain subtle; the cobalt subject carries the contrast.
    glow=Image.new("RGBA",canvas.size,(0,0,0,0))
    gd=ImageDraw.Draw(glow)
    gd.ellipse((-300,500,1200,2100),fill=(98,228,242,58))
    gd.ellipse((1380,900,2760,2500),fill=(75,132,255,45))
    glow=glow.filter(ImageFilter.GaussianBlur(110)); canvas.paste(glow,(0,0),glow)
    draw=ImageDraw.Draw(canvas)
    board=Path(r"D:\MyPro\brainwave\主板图.jpeg")
    avatar=Path(r"C:\Users\xiaoy\AppData\Local\Temp\codex-clipboard-ee7e27d5-a335-4122-aeb1-3db9d6734c30.jpg")

    # Top identity and large layered title.
    tx(draw,(135,80),"焊门子弟   /   AI HARDWARE",29,MUTED,en=True)
    if avatar.exists():
        av=fit_image(avatar,(0,0,160,160),radius=80)
        canvas.paste(av,(2110,55),av if av.mode=="RGBA" else None)
        ImageDraw.Draw(canvas).ellipse((2110,55,2270,215),outline=WHITE,width=7)
    layered_type(canvas,(130,285),"故事搭子",275,BLUE,depth=27,outline=WHITE,artistic=True)
    draw=ImageDraw.Draw(canvas)
    tagline_font=ImageFont.truetype(FONT_KAI,size=62,index=0)
    draw.text((150,620),"一声唤醒，故事就开始了。",font=tagline_font,fill=INK,stroke_width=1,stroke_fill=INK)
    tx(draw,(155,720),"DESKTOP AI AUDIO COMPANION",27,BLUE,en=True)
    draw.rounded_rectangle((155,785,660,855),radius=35,fill=BLUE)
    tx(draw,(407,820),"故事  /  笑话  /  专注",28,WHITE,anchor="mm")

    # Hero composition with floating audio planet and actual development board.
    hero=(95,990,2210,2140)
    shadow(canvas,hero,radius=55,blur=38,offset=(8,32),color=(35,94,153,25))
    draw=ImageDraw.Draw(canvas)
    draw.rounded_rectangle((hero[0],hero[1],hero[0]+hero[2],hero[1]+hero[3]),radius=55,fill=(255,255,255,225),outline=WHITE,width=5)
    tx(draw,(165,1065),"VOICE BECOMES A WORLD",27,BLUE,en=True)
    tx(draw,(165,1125),"把声音，变成一个可以进入的世界。",48,INK)
    draw_sphere(canvas,1535,1940,525)
    draw=ImageDraw.Draw(canvas)
    tx(draw,(1535,2530),"STORY MODE  ·  AUDIO CORE",22,MUTED,en=True,anchor="ma")
    # Hardware photo floating as a layered evidence tile.
    if board.exists():
        photo=fit_image(board,(0,0,530,770),radius=25)
        shadow(canvas,(190,1440,570,840),radius=25,blur=28,offset=(14,22),color=(11,36,71,50))
        if photo.mode=="RGBA": canvas.paste(photo,(190,1440),photo)
        else: canvas.paste(photo,(190,1440))
        ImageDraw.Draw(canvas).rounded_rectangle((190,1440,720,2210),radius=25,outline=WHITE,width=7)
    draw=ImageDraw.Draw(canvas)
    tx(draw,(190,2245),"ESP32-S3 / REAL PROTOTYPE",22,BLUE,en=True)
    # UI player intersects hero edge as a floating layer.
    ui=(935,2760,1320,660)
    shadow(canvas,ui,radius=38,blur=28,offset=(10,18),color=(22,63,121,28))
    draw=ImageDraw.Draw(canvas)
    draw.rounded_rectangle((ui[0],ui[1],ui[0]+ui[2],ui[1]+ui[3]),radius=38,fill=WHITE,outline="#D8E5F2",width=4)
    tx(draw,(ui[0]+52,ui[1]+44),"NOW PLAYING",21,BLUE,en=True)
    tx(draw,(ui[0]+52,ui[1]+100),"月亮邮差",48,INK)
    tx(draw,(ui[0]+52,ui[1]+165),"故事模式  ·  第 01 章",26,MUTED,bold=False)
    draw.rounded_rectangle((ui[0]+52,ui[1]+225,ui[0]+ui[2]-52,ui[1]+239),radius=7,fill=LINE)
    draw.rounded_rectangle((ui[0]+52,ui[1]+225,ui[0]+ui[2]*.57,ui[1]+239),radius=7,fill=BLUE)
    # floating waveform and mode buttons
    for i in range(64):
        x=ui[0]+60+i*18
        hh=18+(i*43%90)
        draw.rounded_rectangle((x,ui[1]+330-hh//2,x+8,ui[1]+330+hh//2),radius=4,fill=BLUE if i<37 else "#AFC8EA")
    for i,(label,col) in enumerate((("故事",BLUE),("笑话",ORANGE),("专注",CYAN))):
        x=ui[0]+50+i*405
        draw.rounded_rectangle((x,ui[1]+450,x+360,ui[1]+530),radius=40,fill="#F5F9FD",outline=col,width=3)
        draw.ellipse((x+22,ui[1]+477,x+48,ui[1]+503),fill=col)
        tx(draw,(x+75,ui[1]+466),label,27,INK)
    tx(draw,(ui[0]+ui[2]-50,ui[1]+590),"CONCEPT UI",18,MUTED,en=True,anchor="ra")

    # Modes in typographic editorial layout.
    section=3590
    layered_type(canvas,(130,section),"三种桌面时刻",96,BLUE,depth=8,outline=WHITE,artistic=True)
    draw=ImageDraw.Draw(canvas)
    tx(draw,(145,section+135),"一个语音入口，从陪伴开始。",34,MUTED)
    card(draw,(145,section+260,660,300),"01","故事模式","继续讲 · 换一个",BLUE)
    card(draw,(870,section+260,660,300),"02","笑话模式","唤醒后 · 再来一个",ORANGE)
    card(draw,(1595,section+260,660,300),"03","专注模式","未来接入 · 计时提醒",CYAN)

    # Layered future roadmap.
    road=4320
    draw=ImageDraw.Draw(canvas)
    tx(draw,(145,road),"从一个故事入口，扩展成个人 AI 搭子。",42,INK)
    draw.line((175,road+105,2225,road+105),fill="#AFC6DF",width=5)
    for i,(tag,title_,desc,col) in enumerate((("NOW","48H 原型","唤醒 / 故事 / 笑话",BLUE),("NEXT","AI 扩展","模型 / 连续对话",ORANGE),("FUTURE","个人计划","状态 / 建议 / 番茄钟",CYAN))):
        x=170+i*730
        draw.ellipse((x,road+82,x+46,road+128),fill=col)
        tx(draw,(x,road+160),tag,20,col,en=True)
        tx(draw,(x,road+198),title_,32,INK)
        tx(draw,(x,road+248),desc,23,MUTED,bold=False)

    # Hardware signature footer.
    y=4805
    draw.rounded_rectangle((140,y,2260,5235),radius=34,fill=INK)
    tx(draw,(200,y+48),"HARDWARE SIGNATURE",21,LIME,en=True)
    specs=[("ESP32-S3","16 MB FLASH"),("FLASH VENDOR 0x46","FLASH ID 0x4018"),("MAC 68:EE:8F:44:B5:8C","TAIL B5:8C")]
    for i,pair in enumerate(specs):
        for j,val in enumerate(pair):
            x=200+j*1000; yy=y+105+i*92
            tx(draw,(x,yy),val,26,WHITE if i==0 else "#BDD1E4",True,en=(j==1 and i==0))
    tx(draw,(W//2,5320),"焊门子弟  /  方案示意 · 原型开发中",23,BLUE,anchor="mm")

    png=OUT/"story-companion-iceblue-art-type-v2-2400x5400.png"
    pdf=OUT/"story-companion-iceblue-art-type-v2-2400x5400.pdf"
    canvas.convert("RGB").save(png,format="PNG",optimize=True)
    canvas.convert("RGB").save(pdf,format="PDF",resolution=76.2)
    print(png);print(pdf)


if __name__=="__main__":
    main()

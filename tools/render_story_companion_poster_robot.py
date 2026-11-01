"""生成加入机器人产品形态示意的故事搭子产品海报。"""

from pathlib import Path
import sys
import math

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

ROOT = Path(r"D:\MyPro\brainwave")
OUT = ROOT / "outputs" / "health-reminder-poster"
OUT.mkdir(parents=True, exist_ok=True)
W, H = 2400, 5400
BG = "#EAF5FA"
NAVY = "#071A3A"
BLUE = "#1556D8"
CYAN = "#42DDE9"
LIME = "#B6F22E"
ORANGE = "#FF7657"
GREY = "#5D718C"
LINE = "#C6D9E6"
WHITE = "#FFFFFF"
FONT_ART = r"C:\Windows\Fonts\STXINGKA.TTF"
FONT_BOLD = r"C:\Windows\Fonts\msyhbd.ttc"
FONT_EN = r"C:\Windows\Fonts\AGENCYB.TTF"


def ft(size, en=False, art=False):
    """加载海报字体。"""
    path = FONT_EN if en else FONT_ART if art else FONT_BOLD
    return ImageFont.truetype(path, size=size, index=0)


def txt(draw, xy, value, size, fill=NAVY, en=False, art=False, anchor="la"):
    """绘制统一文字。"""
    draw.text(xy, value, font=ft(size, en, art), fill=fill, anchor=anchor)


def soft_panel(canvas, box, radius=35):
    """绘制带柔和投影的白色卡片。"""
    x, y, w, h = box
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    ImageDraw.Draw(layer).rounded_rectangle((x+12, y+24, x+w+12, y+h+24), radius=radius, fill=(18, 70, 120, 28))
    layer = layer.filter(ImageFilter.GaussianBlur(26))
    canvas.paste(layer, (0, 0), layer)
    ImageDraw.Draw(canvas).rounded_rectangle((x, y, x+w, y+h), radius=radius, fill=WHITE, outline=(255,255,255,220), width=4)


def glow_line(canvas, points, color, width=8, blur=28):
    """绘制发光声波连接线。"""
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    ImageDraw.Draw(layer).line(points, fill=color, width=blur, joint="curve")
    layer = layer.filter(ImageFilter.GaussianBlur(blur // 2))
    canvas.paste(layer, (0, 0), layer)
    ImageDraw.Draw(canvas).line(points, fill=color, width=width, joint="curve")


def sphere(canvas, cx, cy, r):
    """绘制抽象声波球体。"""
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
    pts = []
    for i in range(140):
        t = i / 139
        x = cx-r*.86+t*r*1.72
        env = math.sin(math.pi*t)**.55
        y = cy-(.12+abs(math.sin(t*17*math.pi))*.27)*r*env
        pts.append((x, y))
    glow_line(canvas, pts, (28,168,255,255), 9, 35)
    draw = ImageDraw.Draw(canvas)
    draw.arc((cx-r*1.43, cy-r*.43, cx+r*1.43, cy+r*.43), 185, 355, fill=LIME, width=7)
    draw.arc((cx-r*1.56, cy-r*.53, cx+r*1.56, cy+r*.53), 195, 345, fill=BLUE, width=5)


def card(draw, box, number, title, desc, color):
    """绘制编号式能力卡。"""
    x, y, w, h = box
    draw.rounded_rectangle((x,y,x+w,y+h), radius=30, fill=WHITE, outline=LINE, width=4)
    draw.rounded_rectangle((x,y,x+15,y+h), radius=7, fill=color)
    txt(draw, (x+48,y+42), number, 25, color, en=True)
    txt(draw, (x+48,y+94), title, 42, NAVY)
    txt(draw, (x+48,y+165), desc, 26, GREY)


def rounded_photo(canvas, path, box, radius=30, border=BLUE):
    """把图片放到有层次的产品卡片中。"""
    x, y, w, h = box
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    ImageDraw.Draw(layer).rounded_rectangle((x+12,y+24,x+w+12,y+h+24),radius=radius,fill=(18,70,120,38))
    layer=layer.filter(ImageFilter.GaussianBlur(28)); canvas.paste(layer,(0,0),layer)
    image = ImageOps.fit(Image.open(path).convert("RGB"), (w,h), method=Image.Resampling.LANCZOS, centering=(0.5,0.5)).convert("RGBA")
    mask=Image.new("L",(w,h),0); ImageDraw.Draw(mask).rounded_rectangle((0,0,w,h),radius=radius,fill=255); image.putalpha(mask)
    canvas.paste(image,(x,y),image)
    ImageDraw.Draw(canvas).rounded_rectangle((x,y,x+w,y+h),radius=radius,outline=border,width=6)


def main():
    """生成加入机器人产品形态的海报。"""
    canvas=Image.new("RGBA",(W,H),BG)
    draw=ImageDraw.Draw(canvas)
    # Soft ice-blue background fields.
    layer=Image.new("RGBA",canvas.size,(0,0,0,0)); ld=ImageDraw.Draw(layer)
    ld.ellipse((-500,500,1300,2400),fill=(66,221,233,65)); ld.ellipse((1300,700,2900,2500),fill=(45,105,235,52))
    layer=layer.filter(ImageFilter.GaussianBlur(150)); canvas.paste(layer,(0,0),layer)
    draw=ImageDraw.Draw(canvas)
    board=ROOT/"主板图.jpeg"
    robot=Path(r"C:\Users\xiaoy\AppData\Local\Temp\codex-clipboard-e855b18f-a926-44b2-9af8-8bb6eb5a669c.png")
    avatar=Path(r"C:\Users\xiaoy\AppData\Local\Temp\codex-clipboard-ee7e27d5-a335-4122-aeb1-3db9d6734c30.jpg")

    txt(draw,(135,85),"焊门子弟   /   AI HARDWARE",28,GREY,en=True)
    if avatar.exists():
        av=ImageOps.fit(Image.open(avatar).convert("RGB"),(154,154),method=Image.Resampling.LANCZOS).convert("RGBA")
        mask=Image.new("L",(154,154),0); ImageDraw.Draw(mask).ellipse((0,0,154,154),fill=255); av.putalpha(mask); canvas.paste(av,(2110,55),av)
        ImageDraw.Draw(canvas).ellipse((2110,55,2264,209),outline=WHITE,width=6)
    txt(draw,(135,285),"故事搭子",245,BLUE,art=True)
    txt(draw,(150,590),"一声唤醒，故事就开始了。",58,NAVY)
    txt(draw,(155,680),"VOICE-FIRST DESKTOP COMPANION",29,BLUE,en=True)
    draw.rounded_rectangle((155,760,640,835),radius=38,fill=BLUE)
    txt(draw,(397,798),"故事  /  笑话  /  专注",28,WHITE,anchor="mm")

    # Product hero: robot form on right, real board on left, audio sphere behind.
    hero=(95,980,2210,2280)
    soft_panel(canvas,hero,radius=48); draw=ImageDraw.Draw(canvas)
    txt(draw,(165,1060),"PRODUCT FORM / 产品形态",24,BLUE,en=True)
    txt(draw,(165,1125),"从开发板，到一个会回应的桌面搭子。",52,NAVY)
    txt(draw,(165,1210),"机器人外观为产品形态示意，核心体验从语音入口开始。",30,GREY)
    sphere(canvas,1650,1850,470)
    draw=ImageDraw.Draw(canvas)
    if board.exists():
        rounded_photo(canvas,board,(180,1390,460,700),radius=28,border=BLUE)
    txt(draw,(180,2130),"CURRENT / ESP32-S3",20,BLUE,en=True)
    if robot.exists():
        rounded_photo(canvas,robot,(1510,1260,610,900),radius=35,border=CYAN)
    draw=ImageDraw.Draw(canvas)
    txt(draw,(1510,2205),"FUTURE FORM / CONCEPT",20,BLUE,en=True)
    glow_line(canvas,[(630,1740),(930,1740),(1140,1870)],BLUE,8,30)
    glow_line(canvas,[(1490,1780),(1270,1870)],LIME,7,26)
    txt(draw,(1140,2420),"HARDWARE  →  VOICE  →  COMPANION",22,GREY,en=True,anchor="ma")

    # Audio player floats in front of the hero panel.
    ui=(760,2810,1500,650); soft_panel(canvas,ui,radius=35); draw=ImageDraw.Draw(canvas)
    txt(draw,(ui[0]+55,ui[1]+45),"NOW PLAYING",21,BLUE,en=True)
    txt(draw,(ui[0]+55,ui[1]+100),"月亮邮差",50,NAVY)
    txt(draw,(ui[0]+55,ui[1]+165),"故事模式  ·  第 01 章",26,GREY)
    draw.rounded_rectangle((ui[0]+55,ui[1]+225,ui[0]+ui[2]-55,ui[1]+240),radius=7,fill=LINE)
    draw.rounded_rectangle((ui[0]+55,ui[1]+225,ui[0]+ui[2]*.56,ui[1]+240),radius=7,fill=BLUE)
    for i in range(70):
        x=ui[0]+60+i*18; h=22+(i*31%108); draw.rounded_rectangle((x,ui[1]+335-h//2,x+8,ui[1]+335+h//2),radius=3,fill=BLUE if i<39 else "#B9CEE7")
    for i,(lab,col) in enumerate((("故事",BLUE),("笑话",ORANGE),("专注",CYAN))):
        x=ui[0]+55+i*450; draw.rounded_rectangle((x,ui[1]+465,x+390,ui[1]+545),radius=40,fill=WHITE,outline=col,width=3); draw.ellipse((x+23,ui[1]+492,x+49,ui[1]+518),fill=col); txt(draw,(x+78,ui[1]+480),lab,27,NAVY)
    txt(draw,(ui[0]+ui[2]-48,ui[1]+602),"CONCEPT UI",18,GREY,en=True,anchor="ra")

    sec=3630
    txt(draw,(135,sec),"三种桌面时刻",100,BLUE,art=True); txt(draw,(145,sec+145),"一个语音入口，从陪伴开始。",34,GREY)
    card(draw,(145,sec+260,660,300),"01","故事模式","继续讲 · 换一个",BLUE)
    card(draw,(870,sec+260,660,300),"02","笑话模式","唤醒后 · 再来一个",ORANGE)
    card(draw,(1595,sec+260,660,300),"03","专注模式","未来接入 · 计时提醒",CYAN)

    road=4300; txt(draw,(145,road),"从一个故事入口，扩展成个人 AI 搭子。",42,NAVY); draw.line((170,road+110,2230,road+110),fill="#B8CDDF",width=5)
    for i,(tag,title,desc,col) in enumerate((("NOW","48H 原型","唤醒 / 故事 / 笑话",BLUE),("NEXT","AI 扩展","模型 / 连续对话",ORANGE),("FUTURE","个人计划","状态 / 建议 / 番茄钟",CYAN))):
        x=170+i*730; draw.ellipse((x,road+87,x+46,road+133),fill=col); txt(draw,(x,road+165),tag,20,col,en=True); txt(draw,(x,road+203),title,32,NAVY); txt(draw,(x,road+252),desc,23,GREY)

    y=4840; draw.rounded_rectangle((140,y,2260,5265),radius=34,fill=NAVY); txt(draw,(200,y+55),"HARDWARE SIGNATURE",21,LIME,en=True)
    vals=[("ESP32-S3","16 MB FLASH"),("FLASH VENDOR 0x46","FLASH ID 0x4018"),("MAC 68:EE:8F:44:B5:8C","TAIL B5:8C")]
    for i,pair in enumerate(vals):
        for j,val in enumerate(pair): x=200+j*1000; yy=y+115+i*92; txt(draw,(x,yy),val,25,WHITE if i==0 else "#B9D0E1",en=(i==0 and j==1))
    txt(draw,(W//2,5350),"焊门子弟  /  产品形态示意 · 原型开发中",23,BLUE,anchor="mm")

    png=OUT/"story-companion-robot-product-poster-2400x5400.png"; pdf=OUT/"story-companion-robot-product-poster-2400x5400.pdf"
    canvas.convert("RGB").save(png,format="PNG",optimize=True); canvas.convert("RGB").save(pdf,format="PDF",resolution=76.2); print(png); print(pdf)


if __name__=="__main__": main()

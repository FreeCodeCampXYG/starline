"""生成 3D 产品渲染感的故事搭子海报。"""

from collections import deque
from pathlib import Path
import math

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps, ImageChops

ROOT = Path(r"D:\MyPro\brainwave")
OUT = ROOT / "outputs" / "health-reminder-poster"
OUT.mkdir(parents=True, exist_ok=True)
W, H = 2400, 5400
BG_TOP = (4, 12, 33)
BG_BOT = (8, 28, 66)
WHITE = "#F6FBFF"
BLUE = "#2866FF"
NAVY = "#071A3A"
CYAN = "#49E8F2"
LIME = "#C8FA46"
ORANGE = "#FF825C"
MUTED = "#9BAFC9"
FONT_ART = r"C:\Windows\Fonts\STXINGKA.TTF"
FONT_BOLD = r"C:\Windows\Fonts\msyhbd.ttc"
FONT_EN = r"C:\Windows\Fonts\AGENCYB.TTF"


def font(size, en=False, art=False):
    """加载中文艺术字、中文粗体或窄体英文字体。"""
    path = FONT_EN if en else FONT_ART if art else FONT_BOLD
    return ImageFont.truetype(path, size=size, index=0)


def text(draw, xy, value, size, fill=WHITE, en=False, art=False, anchor="la"):
    """绘制海报文字。"""
    draw.text(xy, value, font=font(size, en, art), fill=fill, anchor=anchor)


def vertical_gradient():
    """建立深钴蓝摄影棚背景。"""
    img = Image.new("RGB", (W, H))
    pix = img.load()
    for y in range(H):
        t = y / (H - 1)
        c = tuple(int(BG_TOP[k] * (1-t) + BG_BOT[k] * t) for k in range(3))
        for x in range(W):
            pix[x, y] = c
    return img.convert("RGBA")


def glow(canvas, box, color, blur=95, alpha=110):
    """添加体积光晕。"""
    layer = Image.new("RGBA", canvas.size, (0,0,0,0))
    ImageDraw.Draw(layer).ellipse(box, fill=(*color, alpha))
    layer = layer.filter(ImageFilter.GaussianBlur(blur))
    canvas.paste(layer, (0,0), layer)


def make_subject_cutout(path):
    """通过边缘连通的中性灰背景分割机器人参考图。"""
    src = Image.open(path).convert("RGB")
    w, h = src.size
    px = src.load()
    seen = bytearray(w*h)
    q = deque()

    def is_bg(x, y):
        r,g,b = px[x,y]
        # Reference backdrop is nearly uniform 200-gray; preserve brighter shell and dark screen.
        return max(abs(r-200), abs(g-200), abs(b-200)) <= 5

    for x in range(w):
        if is_bg(x,0): q.append((x,0))
        if is_bg(x,h-1): q.append((x,h-1))
    for y in range(h):
        if is_bg(0,y): q.append((0,y))
        if is_bg(w-1,y): q.append((w-1,y))

    while q:
        x,y=q.popleft()
        idx=y*w+x
        if seen[idx]: continue
        if not is_bg(x,y): continue
        seen[idx]=1
        if x>0: q.append((x-1,y))
        if x+1<w: q.append((x+1,y))
        if y>0: q.append((x,y-1))
        if y+1<h: q.append((x,y+1))

    mask = Image.new("L", (w,h), 255)
    mpx = mask.load()
    for y in range(h):
        for x in range(w):
            if seen[y*w+x]: mpx[x,y]=0
    # Slightly soften only the cut edge to remove pixel stair-stepping.
    mask = mask.filter(ImageFilter.GaussianBlur(1.0))
    src.putalpha(mask)
    bbox = mask.getbbox()
    return src.crop(bbox) if bbox else src


def place_3d_subject(canvas, subject, box):
    """给机器人抠图添加投影、厚度和冷色轮廓光。"""
    x,y,w,h=box
    obj=subject.copy()
    obj.thumbnail((w,h), Image.Resampling.LANCZOS)
    ox=x+(w-obj.width)//2
    oy=y+(h-obj.height)//2
    alpha=obj.getchannel("A")

    # Deep extrusion shadow, offset to create physical depth.
    shadow_alpha=ImageChops.offset(alpha, 28, 55).filter(ImageFilter.GaussianBlur(30))
    shadow=Image.new("RGBA",obj.size,(0,7,25,0)); shadow.putalpha(shadow_alpha.point(lambda v:int(v*.72)))
    canvas.alpha_composite(shadow,(ox+4,oy+20))

    # Cyan rim light behind the white product.
    rim=alpha.filter(ImageFilter.MaxFilter(31))
    rim=ImageChops.subtract(rim,alpha).filter(ImageFilter.GaussianBlur(13))
    rim_layer=Image.new("RGBA",obj.size,(48,214,255,0)); rim_layer.putalpha(rim.point(lambda v:int(v*.9)))
    canvas.alpha_composite(rim_layer,(ox-2,oy+5))

    # Small warm contact shadow under the robot feet/base.
    glow(canvas,(ox+obj.width*.16,oy+obj.height*.82,ox+obj.width*.86,oy+obj.height*1.02),(47,119,255),65,85)
    canvas.alpha_composite(obj,(ox,oy))
    return (ox,oy,obj.width,obj.height)


def neon_wave(canvas, cx, cy, width, amplitude, color, phase=0):
    """绘制具有发光厚度的声音波形。"""
    pts=[]
    for i in range(160):
        t=i/159
        x=cx-width/2+t*width
        envelope=math.sin(math.pi*t)**0.6
        y=cy+math.sin(t*16*math.pi+phase)*amplitude*envelope
        pts.append((x,y))
    layer=Image.new("RGBA",canvas.size,(0,0,0,0))
    ImageDraw.Draw(layer).line(pts,fill=color,width=34,joint="curve")
    layer=layer.filter(ImageFilter.GaussianBlur(25)); canvas.paste(layer,(0,0),layer)
    ImageDraw.Draw(canvas).line(pts,fill=color,width=9,joint="curve")


def main():
    """生成 4:9 深色 3D 产品概念海报 PNG 和 PDF。"""
    canvas=vertical_gradient()
    draw=ImageDraw.Draw(canvas)
    robot_path=Path(r"C:\Users\xiaoy\AppData\Local\Temp\codex-clipboard-e855b18f-a926-44b2-9af8-8bb6eb5a669c.png")
    avatar_path=Path(r"C:\Users\xiaoy\AppData\Local\Temp\codex-clipboard-ee7e27d5-a335-4122-aeb1-3db9d6734c30.jpg")
    board_path=ROOT/"主板图.jpeg"

    # Studio glows create a layered 3D stage.
    glow(canvas,(780,820,2250,2940),(27,92,255),190,105)
    glow(canvas,(60,1750,1050,2900),(33,235,245),150,48)
    draw=ImageDraw.Draw(canvas)
    # Sparse perspective floor lines.
    horizon=3370
    for i in range(13):
        y=horizon+i*i*10
        draw.line((0,y,W,y),fill=(21,60,115,110),width=2)
    for x in range(-1200,3600,340):
        draw.line((W//2,horizon,x,H),fill=(20,56,110,100),width=2)

    # Top ID and avatar.
    text(draw,(130,95),"焊门子弟  /  AI HARDWARE",29,MUTED,en=True)
    if avatar_path.exists():
        avatar=ImageOps.fit(Image.open(avatar_path).convert("RGB"),(160,160),method=Image.Resampling.LANCZOS).convert("RGBA")
        mask=Image.new("L",(160,160),0); ImageDraw.Draw(mask).ellipse((0,0,160,160),fill=255); avatar.putalpha(mask)
        canvas.paste(avatar,(2090,65),avatar); ImageDraw.Draw(canvas).ellipse((2090,65,2250,225),outline=CYAN,width=6)

    # Art-directed typography with dimensional extrusion.
    draw=ImageDraw.Draw(canvas)
    text(draw,(130,300),"一声唤醒",125,WHITE)
    text(draw,(130,445),"故事开场",210,LIME)
    text(draw,(145,720),"你的桌面 AI 音频伙伴",42,WHITE)
    text(draw,(150,795),"STORY  /  JOKE  /  FOCUS",28,CYAN,en=True)

    # Big robot hero, isolated and volumetric.
    if robot_path.exists():
        subject=make_subject_cutout(robot_path)
        robot_box=place_3d_subject(canvas,subject,(690,1030,1370,2140))
    else:
        robot_box=None

    # Layered orbital sound rings wrap around the product without obscuring it.
    draw=ImageDraw.Draw(canvas)
    for inset,col,width in [(0,BLUE,8),(66,CYAN,6),(132,LIME,4)]:
        draw.arc((555+inset,1010+inset,2220-inset,2840-inset),198,344,fill=col,width=width)
    neon_wave(canvas,1450,2850,1400,95,(46,191,255,255),phase=.3)
    draw=ImageDraw.Draw(canvas)
    text(draw,(1450,2965),"SOUND  →  STORY  →  RESPONSE",27,CYAN,en=True,anchor="ma")
    text(draw,(1450,3020),"产品形态示意 · 当前为 48H 原型方向",26,MUTED,anchor="ma")

    # Small real board tile as prototype evidence, set in a floating 3D frame.
    if board_path.exists():
        board=ImageOps.fit(Image.open(board_path).convert("RGB"),(410,570),method=Image.Resampling.LANCZOS).convert("RGBA")
        mask=Image.new("L",board.size,0); ImageDraw.Draw(mask).rounded_rectangle((0,0,410,570),radius=28,fill=255); board.putalpha(mask)
        card=Image.new("RGBA",(450,650),(255,255,255,0)); ImageDraw.Draw(card).rounded_rectangle((0,0,450,650),radius=35,fill=(255,255,255,245),outline=CYAN,width=5); card.alpha_composite(board,(20,20))
        card=card.rotate(-7,expand=True,resample=Image.Resampling.BICUBIC)
        sh=Image.new("RGBA",canvas.size,(0,0,0,0)); sh.alpha_composite(card,(150,2310)); sh=sh.filter(ImageFilter.GaussianBlur(24)); canvas.paste(sh,(0,0),sh); canvas.alpha_composite(card,(135,2285))
    draw=ImageDraw.Draw(canvas)
    text(draw,(160,2960),"ESP32-S3  /  PROTOTYPE CORE",20,CYAN,en=True)

    # Floating audio UI as the front-most layer.
    ui=(860,3180,1390,690)
    glow(canvas,(ui[0]-40,ui[1]-35,ui[0]+ui[2]+40,ui[1]+ui[3]+55),(28,90,245),45,42)
    draw=ImageDraw.Draw(canvas)
    draw.rounded_rectangle((ui[0]+10,ui[1]+18,ui[0]+ui[2]+10,ui[1]+ui[3]+18),radius=38,fill=(0,6,25,160))
    draw.rounded_rectangle((ui[0],ui[1],ui[0]+ui[2],ui[1]+ui[3]),radius=38,fill="#F4FAFF",outline=CYAN,width=6)
    text(draw,(ui[0]+55,ui[1]+45),"NOW PLAYING",22,BLUE,en=True)
    text(draw,(ui[0]+55,ui[1]+105),"月亮邮差",48,NAVY)
    text(draw,(ui[0]+55,ui[1]+168),"故事模式  ·  第 01 章",26,MUTED)
    draw.rounded_rectangle((ui[0]+55,ui[1]+225,ui[0]+ui[2]-55,ui[1]+240),radius=8,fill="#CFDDEB")
    draw.rounded_rectangle((ui[0]+55,ui[1]+225,ui[0]+ui[2]*.56,ui[1]+240),radius=8,fill=BLUE)
    for i in range(72):
        x=ui[0]+60+i*17; hh=24+(i*29%116)
        draw.rounded_rectangle((x,ui[1]+345-hh//2,x+8,ui[1]+345+hh//2),radius=4,fill=BLUE if i<40 else "#BCD1E7")
    modes=[("故事",BLUE),("笑话",ORANGE),("专注",CYAN)]
    for i,(label,col) in enumerate(modes):
        x=ui[0]+55+i*435
        draw.rounded_rectangle((x,ui[1]+485,x+380,ui[1]+565),radius=40,fill=WHITE,outline=col,width=4)
        draw.ellipse((x+22,ui[1]+512,x+50,ui[1]+540),fill=col)
        text(draw,(x+75,ui[1]+500),label,27,NAVY)
    text(draw,(ui[0]+ui[2]-45,ui[1]+632),"CONCEPT UI",18,MUTED,en=True,anchor="ra")

    # Product modes on a high-contrast dark section.
    y=4030
    draw=ImageDraw.Draw(canvas)
    text(draw,(135,y),"三种桌面时刻",72,WHITE,art=True)
    text(draw,(140,y+92),"一个语音入口，从陪伴开始。",32,MUTED)
    data=[("01","故事模式","叫它讲一个故事，也可以随时换一个。",CYAN),
          ("02","笑话模式","一句唤醒，切换轻松内容，听完再来一个。",LIME),
          ("03","专注模式","未来接入计时与休息提醒。",ORANGE)]
    for i,(num,title_,desc,col) in enumerate(data):
        yy=y+190+i*170
        text(draw,(150,yy),num,64,col,en=True)
        draw.line((300,yy-5,300,yy+85),fill=col,width=5)
        text(draw,(360,yy),title_,43,WHITE)
        text(draw,(360,yy+62),desc,27,MUTED)
        if i<2: draw.line((360,yy+133,2210,yy+133),fill=(28,62,103,255),width=3)

    # Compact roadmap footer.
    y=4660
    draw.rectangle((0,y,W,y+430),fill="#08142C")
    text(draw,(145,y+50),"现在做故事，未来慢慢懂你。",43,WHITE)
    futures=[("NOW","48H 原型","唤醒 / 故事 / 笑话",LIME),("NEXT","AI 扩展","模型 / 连续对话",CYAN),("FUTURE","个人计划","状态 / 建议 / 番茄钟",ORANGE)]
    for i,(tag,title_,desc,col) in enumerate(futures):
        x=155+i*735
        draw.rectangle((x,y+155,x+14,y+340),fill=col)
        text(draw,(x+38,y+155),tag,19,col,en=True)
        text(draw,(x+38,y+195),title_,31,WHITE)
        text(draw,(x+38,y+245),desc,23,MUTED)

    # Technical signature and careful concept label.
    y=5140
    text(draw,(140,y),"ESP32-S3",27,WHITE)
    text(draw,(440,y),"16 MB FLASH",26,WHITE)
    text(draw,(820,y),"0x46  /  0x4018",24,CYAN,en=True)
    text(draw,(1320,y),"MAC TAIL  B5:8C",24,MUTED,en=True)
    text(draw,(2260,y),"焊门子弟",26,LIME,anchor="ra")
    text(draw,(W//2,5310),"产品形态示意  ·  原型开发中",25,CYAN,anchor="ma")

    png=OUT/"story-companion-3d-hero-poster-2400x5400.png"
    pdf=OUT/"story-companion-3d-hero-poster-2400x5400.pdf"
    canvas.convert("RGB").save(png,format="PNG",optimize=True)
    canvas.convert("RGB").save(pdf,format="PDF",resolution=76.2)
    print(png); print(pdf)


if __name__=="__main__":
    main()

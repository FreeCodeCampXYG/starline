"""生成黑客松发布视觉风格的故事搭子产品海报。"""

from pathlib import Path
import sys
import math

from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, str(Path(__file__).parent))
from render_health_poster import font, fit_image, text  # noqa: E402

ROOT = Path(r"D:\MyPro\brainwave")
OUT = ROOT / "outputs" / "health-reminder-poster"
OUT.mkdir(parents=True, exist_ok=True)
W, H = 2400, 5400
BLACK = "#03070D"
WHITE = "#F6F8FA"
GREEN = "#2CFF62"
BLUE = "#147BFF"
CYAN = "#00E5FF"
ORANGE = "#FF9A32"
GREY = "#B8C2CE"
DIM = "#536171"
CN_BOLD = r"C:\Windows\Fonts\msyhbd.ttc"
EN_CONDENSED = r"C:\Windows\Fonts\AGENCYB.TTF"


def display_text(draw, xy, value, size, fill, family="cn", anchor="la", stroke=0, stroke_fill=None):
    """绘制标题用的中文重体或窄体英文字。"""
    path = CN_BOLD if family == "cn" else EN_CONDENSED
    f = ImageFont.truetype(path, size=size, index=0)
    draw.text(xy, value, font=f, fill=fill, anchor=anchor, stroke_width=stroke, stroke_fill=stroke_fill)


def glow(canvas, box, color, blur=75, alpha=140):
    """在黑色底图上叠加霓虹色光晕。"""
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    ImageDraw.Draw(layer).ellipse(box, fill=(*color, alpha))
    layer = layer.filter(ImageFilter.GaussianBlur(blur))
    canvas.paste(layer, (0, 0), layer)


def neon_line(canvas, points, color, width=7, blur=22):
    """绘制霓虹数据线。"""
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    ImageDraw.Draw(layer).line(points, fill=color, width=blur, joint="curve")
    layer = layer.filter(ImageFilter.GaussianBlur(blur // 2))
    canvas.paste(layer, (0, 0), layer)
    ImageDraw.Draw(canvas).line(points, fill=color, width=width, joint="curve")


def circuit_texture(draw):
    """沿边缘绘制弱化电路纹理和数据字符装饰。"""
    for x in range(28, W, 90):
        if x < 300 or x > W - 300:
            for y in range(40, H, 110):
                if (x // 90 + y // 110) % 3 == 0:
                    r = 4 + ((x + y) % 9)
                    c = GREEN if (x + y) % 4 else BLUE
                    draw.rectangle((x, y, x + r, y + r), fill=c)
    for side in (45, W - 45):
        for y in range(120, H - 100, 170):
            c = BLUE if y % 2 else GREEN
            draw.line((side, y, side + (45 if side < W/2 else -45), y), fill=c, width=3)
            draw.line((side + (45 if side < W/2 else -45), y, side + (45 if side < W/2 else -45), y + 55), fill=c, width=3)
            text(draw, (side + (55 if side < W/2 else -100), y + 70), "01", 16, DIM, True)


def draw_audio_planet(canvas, cx, cy, r):
    """绘制蓝色声波星球作为主视觉。"""
    glow(canvas, (cx-r-100, cy-r-100, cx+r+100, cy+r+100), (20, 90, 255), 130, 115)
    draw = ImageDraw.Draw(canvas)
    # Sphere surface with cyan latitude rings.
    draw.ellipse((cx-r, cy-r, cx+r, cy+r), fill="#061C43", outline=CYAN, width=8)
    for i in range(-5, 6):
        yy = cy + i * r * 0.16
        ww = math.sqrt(max(0, r*r - (yy-cy)*(yy-cy)))
        if ww > 0:
            draw.arc((cx-ww, yy-r*.28, cx+ww, yy+r*.28), 180, 360, fill=BLUE if i % 2 else CYAN, width=5)
    # Audio waveform crossing the sphere.
    wave=[]
    for i in range(121):
        t=i/120
        x=cx-r*.88+t*r*1.76
        envelope=math.sin(math.pi*t)**0.65
        amp=(0.1+0.9*abs(math.sin(t*15*math.pi)))*r*.31*envelope
        wave.append((x,cy-amp))
    neon_line(canvas,wave,(40,140,255,255),9,36)
    draw=ImageDraw.Draw(canvas)
    # Orbital audio rings.
    draw.arc((cx-r*1.38,cy-r*.44,cx+r*1.38,cy+r*.44),185,355,fill=GREEN,width=7)
    draw.arc((cx-r*1.52,cy-r*.55,cx+r*1.52,cy+r*.55),188,350,fill=BLUE,width=5)
    for x,y,color in [(cx-r*.92,cy-r*.35,GREEN),(cx+r*.78,cy-r*.20,CYAN),(cx+r*.28,cy+r*.83,ORANGE)]:
        draw.ellipse((x-13,y-13,x+13,y+13),fill=color)


def mode_row(draw, y, number, title_, desc, x=130, color=GREEN):
    """绘制编号式功能介绍栏。"""
    text(draw,(x,y),number,88,color,True)
    draw.line((x+145,y-5,x+145,y+105),fill=color,width=4)
    text(draw,(x+215,y),title_,52,WHITE,True)
    text(draw,(x+215,y+65),desc,31,GREY)


def main():
    """输出 4:9 黑客松霓虹科技海报 PNG 和 PDF。"""
    canvas=Image.new("RGBA",(W,H),BLACK)
    draw=ImageDraw.Draw(canvas)
    circuit_texture(draw)
    board=ROOT/"主板图.jpeg"
    avatar=Path(r"C:\Users\xiaoy\AppData\Local\Temp\codex-clipboard-ee7e27d5-a335-4122-aeb1-3db9d6734c30.jpg")

    # Header strip
    text(draw,(130,90),"焊门子弟",36,WHITE,True)
    draw.rounded_rectangle((480,88,820,150),radius=10,fill=GREEN)
    text(draw,(650,119),"AI+硬件",30,BLACK,True,"mm")
    draw.rectangle((850,88,1035,150),outline=GREEN,width=4)
    text(draw,(942,119),"48H",29,GREEN,True,"mm")
    display_text(draw,(2250,100),"DESKTOP AI COMPANION   /   01",27,GREY,"en","ra")
    if avatar.exists():
        img=fit_image(avatar,(0,0,148,148),radius=74)
        canvas.paste(img,(2090,175),img if img.mode=="RGBA" else None)
        ImageDraw.Draw(canvas).ellipse((2090,175,2238,323),outline=WHITE,width=5)

    # Large punchy headline.
    display_text(draw,(132,292),"一声唤醒",164,WHITE,stroke=2,stroke_fill=WHITE)
    display_text(draw,(132,468),"故事开场",190,GREEN,stroke=2,stroke_fill=GREEN)
    draw.rectangle((142,720,178,788),fill=GREEN)
    text(draw,(215,718),"你的桌面 AI 音频伙伴",40,WHITE,True)
    text(draw,(215,778),"故事  /  笑话  /  专注",26,GREY,True)

    # Hero visual, embedded hardware photo and audio planet.
    draw_audio_planet(canvas,1510,1710,570)
    draw=ImageDraw.Draw(canvas)
    display_text(draw,(1510,1050),"VOICE BECOMES A WORLD",34,CYAN,"en","ma")
    text(draw,(1510,2360),"STORY MODE / AUDIO CORE",23,GREY,True,"ma")
    if board.exists():
        # angled photo card for kinetic editorial rhythm
        photo=fit_image(board,(0,0,540,800),radius=24).convert("RGBA")
        card=Image.new("RGBA",(600,920),(0,0,0,0))
        cd=ImageDraw.Draw(card)
        cd.rounded_rectangle((8,8,592,912),radius=30,fill=(8,18,31,245),outline=(44,255,98,255),width=6)
        card.alpha_composite(photo,(30,30))
        card=card.rotate(7,expand=True,resample=Image.Resampling.BICUBIC)
        shadow=Image.new("RGBA",canvas.size,(0,0,0,0))
        shadow.alpha_composite(card,(120,1460))
        shadow=shadow.filter(ImageFilter.GaussianBlur(22))
        canvas.paste(shadow,(0,0),shadow)
        canvas.alpha_composite(card,(90,1400))
    draw=ImageDraw.Draw(canvas)
    text(draw,(140,2350),"ESP32-S3",25,GREEN,True)
    text(draw,(140,2395),"REAL PROTOTYPE",20,GREY,True)

    # Concept player as a floating UI panel
    ui=(1070,2530,1200,620)
    draw.rounded_rectangle((ui[0]+16,ui[1]+22,ui[0]+ui[2]+16,ui[1]+ui[3]+22),radius=35,fill="#06101B",outline=BLUE,width=5)
    display_text(draw,(ui[0]+55,ui[1]+48),"NOW PLAYING",25,CYAN,"en")
    display_text(draw,(ui[0]+55,ui[1]+105),"月亮邮差",57,WHITE,stroke=1,stroke_fill=WHITE)
    text(draw,(ui[0]+55,ui[1]+175),"故事模式  ·  第 01 章",27,GREY)
    wave=[]
    for i in range(70):
        x=ui[0]+55+i*15
        h=22+(i*37%105)
        wave.append((x,ui[1]+335-h//2))
    neon_line(canvas,wave,(0,229,255,255),7,25)
    draw=ImageDraw.Draw(canvas)
    draw.ellipse((ui[0]+55,ui[1]+430,ui[0]+130,ui[1]+505),fill=GREEN)
    draw.polygon([(ui[0]+84,ui[1]+448),(ui[0]+84,ui[1]+487),(ui[0]+113,ui[1]+468)],fill=BLACK)
    for i,(label,col) in enumerate([("故事",GREEN),("笑话",ORANGE),("专注",BLUE)]):
        x=ui[0]+230+i*280
        draw.rounded_rectangle((x,ui[1]+438,x+240,ui[1]+505),radius=30,fill="#101C2B",outline=col,width=3)
        text(draw,(x+120,ui[1]+471),label,26,WHITE,True,"mm")
    text(draw,(ui[0]+ui[2]-40,ui[1]+560),"CONCEPT UI",18,DIM,True,"ra")

    # Three feature rails
    base=3270
    mode_row(draw,base,"01","故事模式","叫它讲一个故事，也可以随时换一个。",color=GREEN)
    draw.line((135,base+145,2265,base+145),fill="#17334A",width=3)
    mode_row(draw,base+190,"02","笑话模式","一句唤醒，切换轻松内容，听完再来一个。",color=ORANGE)
    draw.line((135,base+335,2265,base+335),fill="#17334A",width=3)
    mode_row(draw,base+380,"03","专注模式","后续接入计时与休息提醒，让桌面陪你进入状态。",color=BLUE)

    # Roadmap band
    y=3910
    draw.rectangle((0,y,W,y+500),fill="#071221")
    text(draw,(135,y+60),"从一个故事入口，扩展成个人 AI 搭子",45,WHITE,True)
    items=[("NOW","48H 原型","唤醒 / 故事 / 笑话",GREEN),("NEXT","AI 扩展","模型 / 连续对话",CYAN),("FUTURE","个人计划","状态 / 建议 / 番茄钟",ORANGE)]
    for i,(tag,title_,desc,col) in enumerate(items):
        x=150+i*740
        draw.rectangle((x,y+185,x+18,y+365),fill=col)
        text(draw,(x+45,y+185),tag,21,col,True)
        text(draw,(x+45,y+225),title_,35,WHITE,True)
        text(draw,(x+45,y+285),desc,25,GREY)

    # Hardware signature / footer
    y=4500
    text(draw,(135,y),"HARDWARE SIGNATURE",22,GREEN,True)
    text(draw,(135,y+55),"ESP32-S3",38,WHITE,True)
    text(draw,(550,y+55),"16 MB FLASH",34,WHITE,True)
    text(draw,(1080,y+55),"FLASH ID 0x4018",31,CYAN,True)
    text(draw,(1740,y+55),"焊门子弟",33,GREEN,True)
    text(draw,(135,y+120),"FLASH VENDOR 0x46",22,GREY,True)
    text(draw,(670,y+120),"MAC 68:EE:8F:44:B5:8C",22,GREY,True)
    text(draw,(1640,y+120),"原型开发中",22,GREY,True)
    # QR placeholder omitted: no fake scannable code.
    for yy in range(4760,H,90):
        draw.line((80,yy,2320,yy),fill="#0A1C2B",width=2)
    text(draw,(135,H-200),"STORY FIRST  /  BUILD WHAT'S NEXT",26,CYAN,True)

    png=OUT/"story-companion-neon-poster-type-v2-2400x5400.png"
    pdf=OUT/"story-companion-neon-poster-type-v2-2400x5400.pdf"
    canvas.convert("RGB").save(png,format="PNG",optimize=True)
    canvas.convert("RGB").save(pdf,format="PDF",resolution=76.2)
    print(png);print(pdf)


if __name__=="__main__":
    main()

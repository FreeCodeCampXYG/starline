"""生成高级消费电子发布风格的故事搭子产品介绍海报。"""

from pathlib import Path
import sys

from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, str(Path(__file__).parent))
from render_health_poster import font, fit_image, text, line_wrap  # noqa: E402

ROOT = Path(r"D:\MyPro\brainwave")
OUT = ROOT / "outputs" / "health-reminder-poster"
OUT.mkdir(parents=True, exist_ok=True)
W, H = 2400, 5400
BG = "#F4F7F7"
WHITE = "#FFFFFF"
INK = "#11191C"
MUTED = "#66767A"
CYAN = "#28B9B4"
CYAN_DARK = "#176D70"
LIME = "#C7E96D"
GOLD = "#E8B64C"
ORANGE = "#E98561"
LINE = "#DCE5E5"
SOFT = "#E8F1F0"


def shadow_panel(canvas, box, radius=36, fill=WHITE, shadow=(15, 36, 47, 28), blur=28):
    """绘制柔和投影的产品 UI 面板。"""
    x, y, w, h = box
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    ld.rounded_rectangle((x + 8, y + 20, x + w + 8, y + h + 20), radius=radius, fill=shadow)
    layer = layer.filter(ImageFilter.GaussianBlur(blur))
    canvas.paste(layer, (0, 0), layer)
    ImageDraw.Draw(canvas).rounded_rectangle((x, y, x + w, y + h), radius=radius, fill=fill)


def icon_book(draw, cx, cy, color=CYAN_DARK, s=1):
    """绘制书本模式线性图标。"""
    draw.rounded_rectangle((cx - 48*s, cy - 35*s, cx - 4*s, cy + 35*s), radius=int(8*s), outline=color, width=max(4, int(6*s)))
    draw.rounded_rectangle((cx + 4*s, cy - 35*s, cx + 48*s, cy + 35*s), radius=int(8*s), outline=color, width=max(4, int(6*s)))
    draw.line((cx, cy - 32*s, cx, cy + 32*s), fill=color, width=max(3, int(4*s)))


def icon_laugh(draw, cx, cy, color=CYAN_DARK, s=1):
    """绘制笑话模式线性图标。"""
    draw.rounded_rectangle((cx - 43*s, cy - 36*s, cx + 43*s, cy + 28*s), radius=int(16*s), outline=color, width=max(4, int(6*s)))
    draw.polygon([(cx - 16*s, cy + 28*s), (cx - 35*s, cy + 51*s), (cx + 2*s, cy + 28*s)], fill=color)
    draw.ellipse((cx - 23*s, cy - 12*s, cx - 14*s, cy - 3*s), fill=color)
    draw.ellipse((cx + 14*s, cy - 12*s, cx + 23*s, cy - 3*s), fill=color)
    draw.arc((cx - 20*s, cy - 3*s, cx + 20*s, cy + 20*s), 5, 175, fill=color, width=max(3, int(4*s)))


def icon_timer(draw, cx, cy, color=CYAN_DARK, s=1):
    """绘制专注计时模式线性图标。"""
    draw.ellipse((cx - 43*s, cy - 43*s, cx + 43*s, cy + 43*s), outline=color, width=max(4, int(6*s)))
    draw.line((cx, cy, cx, cy - 26*s), fill=color, width=max(4, int(6*s)))
    draw.line((cx, cy, cx + 23*s, cy + 15*s), fill=color, width=max(4, int(6*s)))
    draw.line((cx - 17*s, cy - 55*s, cx + 17*s, cy - 55*s), fill=color, width=max(4, int(6*s)))


def waveform(draw, x, y, width, height, color=CYAN, count=48, phase=0):
    """绘制用于播放器概念 UI 的平滑音频波形。"""
    points = []
    for i in range(count + 1):
        t = i / count
        amp = (0.18 + 0.82 * abs(__import__("math").sin((t * 5.7 + phase) * 3.14159)))
        envelope = abs(__import__("math").sin(t * 3.14159)) ** 0.55
        points.append((x + t * width, y + height/2 - amp * envelope * height/2))
    draw.line(points, fill=color, width=7, joint="curve")


def main():
    """绘制故事搭子产品发布风格海报。"""
    canvas = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(canvas)
    board_path = ROOT / "主板图.jpeg"
    avatar_path = Path(r"C:\Users\xiaoy\AppData\Local\Temp\codex-clipboard-ee7e27d5-a335-4122-aeb1-3db9d6734c30.jpg")

    # Header: minimal editorial product identity.
    text(draw, (145, 95), "焊门子弟   /   AI HARDWARE", 31, MUTED, True)
    if avatar_path.exists():
        avatar = fit_image(avatar_path, (0, 0, 150, 150), radius=75)
        canvas.paste(avatar, (2100, 55), avatar)
        draw.ellipse((2100, 55, 2250, 205), outline=WHITE, width=8)
    text(draw, (145, 250), "故事搭子", 205, INK, True)
    text(draw, (155, 515), "一声唤醒，故事就开始了。", 73, CYAN_DARK, True)
    text(draw, (158, 650), "你的桌面 AI 音频伙伴", 42, MUTED)
    text(draw, (2250, 610), "01  /  DESKTOP COMPANION", 26, MUTED, True, "ra")

    # Hero: real board photograph + deliberately conceptual audio UI.
    hero_y = 850
    shadow_panel(canvas, (120, hero_y, 2160, 1960), radius=54, fill=WHITE, shadow=(8, 26, 33, 24), blur=32)
    draw = ImageDraw.Draw(canvas)
    text(draw, (205, hero_y + 85), "A LITTLE VOICE, A BIGGER WORLD", 27, CYAN_DARK, True)
    text(draw, (205, hero_y + 145), "把故事，放到桌面上。", 67, INK, True)
    text(draw, (205, hero_y + 250), "唤醒它，选个模式，然后听故事。", 35, MUTED)

    # Board is the factual hardware hero; framed as a real development prototype.
    board_box = (205, hero_y + 390, 750, 1270)
    if board_path.exists():
        board = fit_image(board_path, (0, 0, board_box[2], board_box[3]), radius=30)
        canvas.paste(board, (board_box[0], board_box[1]))
    draw = ImageDraw.Draw(canvas)
    draw.rounded_rectangle((board_box[0], board_box[1], board_box[0]+board_box[2], board_box[1]+board_box[3]), radius=30, outline=LINE, width=5)
    text(draw, (205, hero_y + 1695), "ESP32-S3   /   16 MB FLASH", 27, MUTED, True)

    # Floating audio UI panel, clearly treated as a concept interface rather than device display.
    ui_box = (1080, hero_y + 390, 1050, 1040)
    shadow_panel(canvas, ui_box, radius=42, fill="#F9FCFB", shadow=(28, 44, 52, 20), blur=24)
    draw = ImageDraw.Draw(canvas)
    text(draw, (ui_box[0] + 58, ui_box[1] + 55), "NOW PLAYING", 24, MUTED, True)
    text(draw, (ui_box[0] + 58, ui_box[1] + 112), "故事模式", 54, INK, True)
    text(draw, (ui_box[0] + 58, ui_box[1] + 190), "月亮邮差 · 第 01 章", 30, MUTED)
    # Progress line and playback control.
    draw.rounded_rectangle((ui_box[0]+60, ui_box[1]+282, ui_box[0]+ui_box[2]-60, ui_box[1]+296), radius=8, fill=LINE)
    draw.rounded_rectangle((ui_box[0]+60, ui_box[1]+282, ui_box[0]+ui_box[2]*0.58, ui_box[1]+296), radius=8, fill=CYAN)
    draw.ellipse((ui_box[0]+60, ui_box[1]+380, ui_box[0]+180, ui_box[1]+500), fill=CYAN_DARK)
    draw.polygon([(ui_box[0]+108, ui_box[1]+412),(ui_box[0]+108,ui_box[1]+468),(ui_box[0]+151,ui_box[1]+440)], fill=WHITE)
    text(draw, (ui_box[0]+215, ui_box[1]+405), "轻声讲述  ·  随时切换", 29, MUTED)
    waveform(draw, ui_box[0]+60, ui_box[1]+610, ui_box[2]-120, 170, CYAN_DARK, count=55, phase=0.15)
    # Three compact mode selectors.
    modes = [("故事", CYAN_DARK), ("笑话", GOLD), ("专注", MUTED)]
    for i,(label,color) in enumerate(modes):
        x=ui_box[0]+60+i*310
        draw.rounded_rectangle((x,ui_box[1]+835,x+270,ui_box[1]+920),radius=42,fill=SOFT if i==0 else WHITE,outline=LINE,width=3)
        draw.ellipse((x+24,ui_box[1]+860,x+50,ui_box[1]+886),fill=color)
        text(draw,(x+72,ui_box[1]+852),label,28,INK,True)
    text(draw, (ui_box[0]+ui_box[2]-54, ui_box[1]+975), "CONCEPT UI", 21, MUTED, True, "ra")

    # Story aura integrated behind the player, not a decorative grid.
    glow = Image.new("RGBA", canvas.size, (0,0,0,0))
    gd=ImageDraw.Draw(glow)
    gd.ellipse((1570,hero_y+1020,2140,hero_y+1590),fill=(40,185,180,38))
    glow=glow.filter(ImageFilter.GaussianBlur(70))
    canvas.paste(glow,(0,0),glow)
    draw=ImageDraw.Draw(canvas)
    for r,c,w in [(265,CYAN,8),(325,"#A7D9D1",5),(385,GOLD,4)]:
        draw.arc((1600-r,hero_y+1290-r,1600+r,hero_y+1290+r),205,325,fill=c,width=w)
    text(draw,(1600,hero_y+1730),"VOICE  →  STORY  →  RESPONSE",24,CYAN_DARK,True,"ma")

    # Product promise: clean typography and three usage modes.
    section_y=3000
    text(draw,(145,section_y),"你的声音入口，\n先从陪伴开始。",83,INK,True)
    line_wrap(draw,"先完成一个能唤醒、能切换内容、能发出声音回应的桌面原型。未来能力留在路线里，今天先把体验做好。",145,section_y+230,2050,38,MUTED,16)
    modes_top=section_y+470
    draw.line((145,modes_top,2255,modes_top),fill=LINE,width=4)
    columns=[
      (145,"01","故事模式","叫它讲一个故事，\n也可以随时换一个。",CYAN_DARK,"book"),
      (875,"02","笑话模式","一句唤醒，切换轻松\n内容，听完再来一个。",GOLD,"laugh"),
      (1605,"03","专注模式","接入计时与休息提醒，\n让桌面陪你进入状态。",ORANGE,"timer")]
    for x,num,title,body,color,icon in columns:
        draw.ellipse((x,modes_top+75,x+100,modes_top+175),fill=color)
        text(draw,(x+50,modes_top+125),num,27,WHITE,True,"mm")
        cx=x+325; cy=modes_top+125
        if icon=="book":
            draw.rounded_rectangle((cx-38,cy-29,cx-4,cy+29),radius=7,outline=color,width=5)
            draw.rounded_rectangle((cx+4,cy-29,cx+38,cy+29),radius=7,outline=color,width=5)
            draw.line((cx,cy-27,cx,cy+27),fill=color,width=4)
        elif icon=="laugh":
            draw.rounded_rectangle((cx-42,cy-34,cx+42,cy+24),radius=14,outline=color,width=5)
            draw.ellipse((cx-20,cy-10,cx-12,cy-2),fill=color); draw.ellipse((cx+12,cy-10,cx+20,cy-2),fill=color)
            draw.arc((cx-18,cy-4,cx+18,cy+17),5,175,fill=color,width=4)
        else:
            draw.ellipse((cx-39,cy-39,cx+39,cy+39),outline=color,width=5)
            draw.line((cx,cy,cx,cy-23),fill=color,width=5); draw.line((cx,cy,cx+22,cy+14),fill=color,width=5)
        text(draw,(x,modes_top+225),title,49,INK,True)
        yy=modes_top+300
        for body_line in body.split("\n"):
            line_wrap(draw,body_line,x,yy,585,31,MUTED,10)
            yy += 48
        draw.line((x,modes_top+460,x+585,modes_top+460),fill=LINE,width=3)

    # Roadmap presented as editorial timeline, not a stack of cards.
    roadmap_y=3840
    text(draw,(145,roadmap_y),"从一个声音原型，长成个人 AI 搭子。",58,INK,True)
    text(draw,(145,roadmap_y+85),"NOW",23,CYAN_DARK,True)
    draw.line((145,roadmap_y+145,2255,roadmap_y+145),fill=LINE,width=5)
    milestones=[(165,"48H 原型","唤醒 · 故事 · 笑话 · 音频回应",CYAN_DARK),(900,"AI 扩展","模型接入 · 连续对话 · 内容生成",GOLD),(1635,"个人计划","状态录入 · 方案建议 · 番茄钟",ORANGE)]
    for x,title,desc,color in milestones:
        draw.ellipse((x,roadmap_y+122,x+46,roadmap_y+168),fill=color)
        text(draw,(x,roadmap_y+205),title,39,INK,True)
        line_wrap(draw,desc,x,roadmap_y+265,590,28,MUTED,9)

    # Technical identity footer.
    spec_y=4470
    draw.rounded_rectangle((145,spec_y,2255,5140),radius=36,fill=INK)
    text(draw,(215,spec_y+60),"HARDWARE SIGNATURE",24,GOLD,True)
    specs=[("CHIP","ESP32-S3"),("FLASH","16 MB"),("VENDOR","0x46"),("FLASH ID","0x4018"),("MAC","68:EE:8F:44:B5:8C"),("TAIL","B5:8C")]
    for i,(label,value) in enumerate(specs):
        col=i%3; row=i//3
        x=215+col*670; y=spec_y+145+row*210
        text(draw,(x,y),label,22,"#9BB7B7",True)
        text(draw,(x,y+45),value,36,WHITE,True)
    text(draw,(215,spec_y+575),"焊门子弟   /   AI+硬件   /   原型开发中",24,"#9BB7B7",True)
    text(draw,(W//2,5265),"故事先开始，未来慢慢长出来。",30,CYAN_DARK,True,"ma")

    png=OUT/"story-companion-product-poster-2400x5400.png"
    pdf=OUT/"story-companion-product-poster-2400x5400.pdf"
    canvas.save(png,format="PNG",optimize=True)
    canvas.save(pdf,format="PDF",resolution=76.2)
    print(png); print(pdf)


if __name__=="__main__":
    main()

"""生成夸张液态玻璃字风格的故事搭子产品海报。"""

from pathlib import Path
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageChops, ImageOps

sys.path.insert(0, str(Path(__file__).parent))
from render_health_poster import font, fit_image, text  # noqa: E402

ROOT = Path(r"D:\MyPro\brainwave")
OUT = ROOT / "outputs" / "health-reminder-poster"
OUT.mkdir(parents=True, exist_ok=True)
W, H = 2400, 5400
INK = "#071934"
BLUE = "#1747F5"
CYAN = "#45E8F0"
LIME = "#D8FF40"
ORANGE = "#FF704B"
PAPER = "#F4F6F2"
MUTED = "#607089"


def gradient(size, stops):
    """生成多色竖向渐变。"""
    w, h = size
    image = Image.new("RGB", size)
    draw = ImageDraw.Draw(image)
    for y in range(h):
        t = y / max(1, h - 1)
        for i in range(len(stops) - 1):
            t0, c0 = stops[i]
            t1, c1 = stops[i + 1]
            if t0 <= t <= t1:
                q = (t - t0) / (t1 - t0)
                rgb = tuple(int(c0[k] * (1 - q) + c1[k] * q) for k in range(3))
                draw.line((0, y, w, y), fill=rgb)
                break
    return image


def glow(canvas, box, color, blur=75, alpha=100):
    """添加柔和的大色光晕。"""
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    ImageDraw.Draw(layer).ellipse(box, fill=(*color, alpha))
    layer = layer.filter(ImageFilter.GaussianBlur(blur))
    canvas.paste(layer, (0, 0), layer)


def liquid_title(canvas, value, xy, size, width, height):
    """用渐变、挤出、亮边和镜面高光制作液态玻璃标题。"""
    mask = Image.new("L", (width, height), 0)
    md = ImageDraw.Draw(mask)
    ft = font(size, True)
    bbox = md.textbbox((0, 0), value, font=ft, stroke_width=5)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    scale = min((width - 100) / tw, (height - 80) / th, 1.0)
    if scale < 1:
        ft = font(max(24, int(size * scale)), True)
        bbox = md.textbbox((0, 0), value, font=ft, stroke_width=5)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    tx = (width - tw) // 2 - bbox[0]
    ty = (height - th) // 2 - bbox[1]
    md.text((tx, ty), value, font=ft, fill=255, stroke_width=7, stroke_fill=255)

    # 深色挤出层提供厚重的立体字边。
    extrude = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    em = Image.new("L", (width, height), 0)
    for dx, dy in [(0, 10), (0, 20), (0, 30), (0, 40), (0, 50)]:
        shifted = ImageChops.offset(mask, dx, dy)
        em = ImageChops.lighter(em, shifted)
    ex = Image.new("RGBA", (width, height), (7, 25, 70, 240))
    ex.putalpha(em)
    extrude.alpha_composite(ex)
    canvas.alpha_composite(extrude, xy)

    fill = gradient((width, height), [
        (0.0, (255, 255, 255)), (0.25, (170, 255, 250)),
        (0.52, (50, 214, 244)), (0.78, (62, 104, 255)), (1.0, (255, 255, 255))
    ]).convert("RGBA")
    fill.putalpha(mask)

    # 彩色边缘高光和柔和反射，让平面字像浇铸透明水凝胶。
    outline = mask.filter(ImageFilter.MaxFilter(31))
    edge = ImageChops.subtract(outline, mask).filter(ImageFilter.GaussianBlur(9))
    edge_layer = Image.new("RGBA", (width, height), (216, 255, 64, 0))
    edge_layer.putalpha(edge.point(lambda p: min(170, int(p * 0.8))))
    fill.alpha_composite(edge_layer)
    highlight = Image.new("RGBA", (width, height), (255, 255, 255, 0))
    hd = ImageDraw.Draw(highlight)
    hd.arc((30, 5, width - 30, height * 0.62), 195, 345, fill=(255, 255, 255, 210), width=15)
    highlight.putalpha(ImageChops.multiply(highlight.getchannel("A"), mask))
    fill.alpha_composite(highlight)
    canvas.alpha_composite(fill, xy)


def rounded_photo(canvas, path, box, radius=28):
    """将真实设备照片放进带投影的浮动玻璃卡片。"""
    x, y, w, h = box
    shadow = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.rounded_rectangle((x + 15, y + 26, x + w + 15, y + h + 26), radius=radius, fill=(2, 12, 35, 100))
    shadow = shadow.filter(ImageFilter.GaussianBlur(26))
    canvas.paste(shadow, (0, 0), shadow)
    photo = fit_image(path, (0, 0, w, h), radius=radius)
    if photo.mode == "RGBA":
        canvas.paste(photo, (x, y), photo)
    else:
        canvas.paste(photo, (x, y))
    ImageDraw.Draw(canvas).rounded_rectangle((x, y, x + w, y + h), radius=radius, outline=(255, 255, 255, 210), width=5)


def pill(draw, box, label, color, selected=False):
    """绘制胶囊式模式切换控件。"""
    x, y, w, h = box
    fill = color if selected else "#FFFFFF"
    outline = color
    txt = "#FFFFFF" if selected else INK
    draw.rounded_rectangle((x, y, x + w, y + h), radius=h // 2, fill=fill, outline=outline, width=4)
    text(draw, (x + w / 2, y + h / 2), label, 29, txt, True, "mm")


def main():
    """生成 4:9 故事搭子液态玻璃主题海报。"""
    canvas = Image.new("RGBA", (W, H), PAPER)
    glow(canvas, (-300, 500, 1050, 1850), (69, 232, 240), 120, 78)
    glow(canvas, (1450, 900, 2700, 2100), (216, 255, 64), 150, 75)
    glow(canvas, (500, 2500, 1700, 3700), (255, 112, 75), 160, 55)
    draw = ImageDraw.Draw(canvas)
    board = ROOT / "主板图.jpeg"
    avatar = Path(r"C:\Users\xiaoy\AppData\Local\Temp\codex-clipboard-266d5fd1-5fe0-4e9d-a104-d6ca9e1422b0.png")
    if not avatar.exists():
        avatar = Path(r"C:\Users\xiaoy\AppData\Local\Temp\codex-clipboard-ee7e27d5-a335-4122-aeb1-3db9d6734c30.jpg")

    # Header identity and avatar.
    text(draw, (125, 100), "焊门子弟   /   AI HARDWARE", 30, MUTED, True)
    if avatar.exists():
        pic = fit_image(avatar, (0, 0, 168, 168), radius=84)
        canvas.paste(pic, (2100, 55), pic if pic.mode == "RGBA" else None)
        ImageDraw.Draw(canvas).ellipse((2100, 55, 2268, 223), outline=WHITE, width=9)

    # Hero typography.
    text(draw, (125, 310), "声音，", 150, INK, True)
    text(draw, (125, 490), "有了形状。", 150, INK, True)
    text(draw, (145, 725), "A voice becomes a world.", 38, CYAN_DARK, True)
    liquid_title(canvas, "故事搭子", (80, 850), 285, 2200, 500)
    draw = ImageDraw.Draw(canvas)
    text(draw, (145, 1375), "一声唤醒，故事就开始了。", 51, INK, True)
    text(draw, (150, 1460), "桌面 AI 音频伙伴  ·  故事 / 笑话 / 专注", 32, MUTED)

    # Main product stage: bright studio cyclorama and oversized translucent orb.
    stage = (90, 1630, 2220, 2130)
    draw.rounded_rectangle((stage[0], stage[1], stage[0] + stage[2], stage[1] + stage[3]), radius=58, fill=(255, 255, 255, 210), outline=(255, 255, 255, 245), width=5)
    glow(canvas, (1120, 1750, 2230, 2870), (69, 232, 240), 95, 60)
    draw = ImageDraw.Draw(canvas)
    # Sculptural liquid audio orb.
    for r, col, w in [(370, CYAN, 13), (445, LIME, 8), (520, ORANGE, 6)]:
        draw.arc((1640-r, 2245-r, 1640+r, 2245+r), 195, 345, fill=col, width=w)
    draw.ellipse((1320, 1940, 1960, 2580), fill="#E9FCFA", outline=CYAN, width=10)
    draw.ellipse((1370, 1990, 1910, 2530), fill="#FFFFFF", outline="#B6F3EE", width=6)
    # glossy liquid droplets
    for x, y, r in [(1420, 2040, 25), (1855, 2110, 18), (1500, 2470, 14), (1810, 2440, 28)]:
        draw.ellipse((x-r, y-r, x+r, y+r), fill=(255, 255, 255, 230), outline=CYAN, width=4)
        draw.arc((x-r+5, y-r+5, x+r-5, y+r-5), 205, 300, fill=WHITE, width=4)
    # Voice rings and waveform imply audio-only core, no camera dependency.
    for r in [560, 620, 685]:
        draw.arc((1640-r, 2245-r, 1640+r, 2245+r), 205, 315, fill=(40, 90, 255, 170), width=5)
    wave = []
    for i in range(55):
        x = 1270 + i * 14
        amp = 24 + (i * 37 % 94)
        wave.append((x, 2685 - amp))
    draw.line(wave, fill=CYAN_DARK, width=8, joint="curve")

    # Real development board photograph as a small but clear hardware artifact.
    if board.exists():
        rounded_photo(canvas, board, (235, 1930, 570, 820), 36)
    draw = ImageDraw.Draw(canvas)
    text(draw, (235, 2790), "ESP32-S3  /  REAL PROTOTYPE", 23, MUTED, True)
    text(draw, (1640, 2820), "语音核心 · 概念视觉", 28, MUTED, True, "ma")

    # Concept UI module, polished media player interface.
    ui = (930, 3030, 1330, 720)
    shadow = Image.new("RGBA", canvas.size, (0,0,0,0))
    ImageDraw.Draw(shadow).rounded_rectangle((ui[0]+10,ui[1]+18,ui[0]+ui[2]+10,ui[1]+ui[3]+18),radius=45,fill=(7,25,52,42))
    shadow=shadow.filter(ImageFilter.GaussianBlur(24)); canvas.paste(shadow,(0,0),shadow)
    draw=ImageDraw.Draw(canvas)
    draw.rounded_rectangle((ui[0],ui[1],ui[0]+ui[2],ui[1]+ui[3]),radius=45,fill=WHITE,outline="#DFE9E7",width=4)
    text(draw,(ui[0]+60,ui[1]+48),"NOW PLAYING",22,MUTED,True)
    text(draw,(ui[0]+60,ui[1]+110),"月亮邮差",53,INK,True)
    text(draw,(ui[0]+60,ui[1]+184),"故事模式 · 第 01 章",29,MUTED)
    draw.rounded_rectangle((ui[0]+60,ui[1]+250,ui[0]+ui[2]-60,ui[1]+265),radius=8,fill="#E0E9E8")
    draw.rounded_rectangle((ui[0]+60,ui[1]+250,ui[0]+ui[2]*0.58,ui[1]+265),radius=8,fill=CYAN)
    draw.ellipse((ui[0]+60,ui[1]+330,ui[0]+160,ui[1]+430),fill=BLUE)
    draw.polygon([(ui[0]+100,ui[1]+355),(ui[0]+100,ui[1]+405),(ui[0]+139,ui[1]+380)],fill=WHITE)
    # abstract waveform control
    for i in range(59):
        x=ui[0]+230+i*15
        h=25+(i*31%85)
        draw.rounded_rectangle((x,ui[1]+380-h//2,x+7,ui[1]+380+h//2),radius=3,fill=CYAN_DARK if i<34 else "#C5DDDA")
    pill(draw,(ui[0]+60,ui[1]+520,330,100),"故事",CYAN_DARK,True)
    pill(draw,(ui[0]+500,ui[1]+520,330,100),"笑话",GOLD)
    pill(draw,(ui[0]+940,ui[1]+520,330,100),"专注",INK)
    text(draw,(ui[0]+ui[2]-55,ui[1]+670),"概念界面示意",21,MUTED,False,"ra")

    # Product description and mode list.
    y=3890
    text(draw,(135,y),"一个语音入口，\n三种桌面时刻。",73,INK,True)
    text(draw,(135,y+210),"先做能唤醒、能切换、能回应的陪伴体验。",34,MUTED)
    cols=[("01","故事模式","叫它讲一个故事，\n也可以随时换一个。",CYAN_DARK),
          ("02","笑话模式","一句唤醒，切换轻松内容。",GOLD),
          ("03","专注模式","接入计时和休息提醒。",ORANGE)]
    for i,(num,title_,desc,color) in enumerate(cols):
        x=135+i*735
        draw=ImageDraw.Draw(canvas)
        draw.line((x,y+350,x+625,y+350),fill=color,width=9)
        text(draw,(x,y+395),num,24,color,True)
        text(draw,(x,y+445),title_,42,INK,True)
        for li,s in enumerate(desc.split("\n")):
            text(draw,(x,y+510+li*42),s,27,MUTED)

    # Future path; reserved as aspiration, clearly marked.
    road_y=4550
    draw=ImageDraw.Draw(canvas)
    text(draw,(135,road_y),"从故事开始，慢慢长成个人 AI 搭子。",43,INK,True)
    draw.line((155,road_y+112,2245,road_y+112),fill="#C9D8D6",width=5)
    future=[("NOW","48H 原型","唤醒 / 故事 / 笑话",CYAN_DARK),("NEXT","AI 扩展","模型 / 连续对话",GOLD),("FUTURE","个人计划","状态 / 建议 / 番茄钟",ORANGE)]
    for i,(tag,title_,desc,color) in enumerate(future):
        x=160+i*735
        draw.ellipse((x,road_y+91,x+42,road_y+133),fill=color)
        text(draw,(x,road_y+175),tag,20,color,True)
        text(draw,(x,road_y+212),title_,34,INK,True)
        text(draw,(x,road_y+260),desc,25,MUTED)

    # Compact hardware identity strip.
    y=4960
    draw.rounded_rectangle((135,y,2265,5280),radius=28,fill=INK)
    text(draw,(190,y+42),"ESP32-S3",32,WHITE,True)
    text(draw,(580,y+42),"16 MB FLASH",32,WHITE,True)
    text(draw,(1110,y+42),"FLASH ID 0x4018",30,CYAN,True)
    text(draw,(1640,y+42),"焊门子弟",30,LIME,True)
    text(draw,(190,y+122),"FLASH VENDOR 0x46",23,"#B1C4C4",True)
    text(draw,(760,y+122),"MAC 68:EE:8F:44:B5:8C",23,"#B1C4C4",True)
    text(draw,(1635,y+122),"原型开发中",23,"#B1C4C4",True)

    png=OUT/"story-companion-product-poster-2400x5400.png"
    pdf=OUT/"story-companion-product-poster-2400x5400.pdf"
    canvas.save(png,format="PNG",optimize=True)
    canvas.save(pdf,format="PDF",resolution=76.2)
    print(png); print(pdf)


if __name__=="__main__":
    main()

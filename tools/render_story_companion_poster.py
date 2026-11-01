"""生成故事搭子 AI+硬件原型的科技展板海报。"""

from pathlib import Path
import sys

from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, str(Path(__file__).parent))
from render_health_poster import font, fit_image, text, line_wrap  # noqa: E402


ROOT = Path(r"D:\MyPro\brainwave")
OUT = ROOT / "outputs" / "health-reminder-poster"
OUT.mkdir(parents=True, exist_ok=True)

WIDTH = 2400
HEIGHT = 5400
BG = "#071316"
PANEL = "#0D2227"
PANEL_2 = "#102D32"
INK = "#E7F5F0"
MUTED = "#8FB4B1"
CYAN = "#64E6DB"
CYAN_DARK = "#167B83"
GOLD = "#F3C35B"
ORANGE = "#F18455"
LIME = "#B9E56C"
GRID = "#17383D"


def glow_line(canvas, points, color, width=8, blur=24):
    """绘制带光晕的语音或数据连接线。"""
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    layer_draw = ImageDraw.Draw(layer)
    layer_draw.line(points, fill=color, width=blur, joint="curve")
    layer = layer.filter(ImageFilter.GaussianBlur(blur // 2))
    canvas.paste(layer, (0, 0), layer)
    ImageDraw.Draw(canvas).line(points, fill=color, width=width, joint="curve")


def dots(draw, x, y, cols, rows, spacing, color):
    """绘制克制的技术点阵。"""
    for row in range(rows):
        for col in range(cols):
            if (row + col) % 3 == 0:
                r = 3 + ((row * 7 + col * 3) % 4)
                draw.ellipse((x + col * spacing - r, y + row * spacing - r,
                              x + col * spacing + r, y + row * spacing + r), fill=color)


def frame(draw, box, color=CYAN_DARK, width=5):
    """绘制主板照片的技术定位框。"""
    x, y, w, h = box
    draw.rectangle((x, y, x + w, y + h), outline=color, width=width)
    mark = 34
    for sx, sy in ((x, y), (x + w, y), (x, y + h), (x + w, y + h)):
        dx = mark if sx == x else -mark
        dy = mark if sy == y else -mark
        draw.line((sx, sy, sx + dx, sy), fill=CYAN, width=width)
        draw.line((sx, sy, sx, sy + dy), fill=CYAN, width=width)


def draw_story_orb(canvas, cx, cy, radius):
    """绘制代表语音故事入口的发光核心。"""
    draw = ImageDraw.Draw(canvas)
    glow = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    glow_draw.ellipse((cx - radius, cy - radius, cx + radius, cy + radius), fill=(100, 230, 219, 70))
    glow = glow.filter(ImageFilter.GaussianBlur(70))
    canvas.paste(glow, (0, 0), glow)
    draw = ImageDraw.Draw(canvas)
    draw.ellipse((cx - radius, cy - radius, cx + radius, cy + radius), fill=PANEL_2, outline=CYAN, width=8)
    draw.arc((cx - radius - 80, cy - radius - 80, cx + radius + 80, cy + radius + 80), 205, 340, fill=GOLD, width=18)
    draw.arc((cx - radius - 125, cy - radius - 125, cx + radius + 125, cy + radius + 125), 210, 330, fill=ORANGE, width=9)
    # 书本符号
    book_w, book_h = 240, 170
    draw.rounded_rectangle((cx - book_w, cy - book_h, cx - 15, cy + book_h), radius=22, fill=CYAN_DARK, outline=CYAN, width=6)
    draw.rounded_rectangle((cx + 15, cy - book_h, cx + book_w, cy + book_h), radius=22, fill=CYAN_DARK, outline=CYAN, width=6)
    draw.line((cx, cy - book_h + 10, cx, cy + book_h - 10), fill=GOLD, width=8)
    draw.arc((cx - book_w + 45, cy - 65, cx - 45, cy + 65), 210, 330, fill=INK, width=6)
    draw.arc((cx + 45, cy - 65, cx + book_w - 45, cy + 65), 210, 330, fill=INK, width=6)
    # 声音波形
    wave = []
    for index in range(31):
        x = cx - 310 + index * 20
        amp = 18 + ((index * 17) % 90)
        wave.append((x, cy + radius + 170 - amp))
    draw.line(wave, fill=CYAN, width=8, joint="curve")


def draw_mode_node(draw, cx, cy, title, subtitle, color, icon):
    """绘制故事、笑话和专注模式节点。"""
    draw.ellipse((cx - 94, cy - 94, cx + 94, cy + 94), fill=PANEL_2, outline=color, width=7)
    if icon == "book":
        draw.rectangle((cx - 40, cy - 35, cx - 5, cy + 35), outline=color, width=7)
        draw.rectangle((cx + 5, cy - 35, cx + 40, cy + 35), outline=color, width=7)
        draw.line((cx, cy - 35, cx, cy + 35), fill=color, width=5)
    elif icon == "joke":
        draw.rounded_rectangle((cx - 45, cy - 38, cx + 45, cy + 28), radius=16, outline=color, width=7)
        draw.polygon([(cx - 15, cy + 28), (cx - 40, cy + 58), (cx + 3, cy + 28)], outline=color)
        draw.ellipse((cx - 23, cy - 10, cx - 13, cy), fill=color)
        draw.ellipse((cx + 13, cy - 10, cx + 23, cy), fill=color)
        draw.arc((cx - 25, cy - 2, cx + 25, cy + 24), 10, 170, fill=color, width=5)
    else:
        draw.arc((cx - 48, cy - 48, cx + 48, cy + 48), 40, 320, fill=color, width=9)
        draw.line((cx, cy, cx, cy - 30), fill=color, width=7)
        draw.line((cx, cy, cx + 26, cy + 18), fill=color, width=7)
    text(draw, (cx, cy + 130), title, 37, INK, True, "ma")
    text(draw, (cx, cy + 185), subtitle, 27, MUTED, False, "ma")


def card(draw, box, stage, title, body, color):
    """绘制当前、下一步和未来能力卡片。"""
    x, y, w, h = box
    draw.rounded_rectangle((x, y, x + w, y + h), radius=30, fill=PANEL_2, outline=color, width=5)
    text(draw, (x + 48, y + 45), stage.upper(), 25, color, True)
    text(draw, (x + 48, y + 105), title, 49, INK, True)
    line_wrap(draw, body, x + 48, y + 190, w - 95, 30, MUTED, 10)


def spec_row(draw, x, y, label, value, color=INK):
    """绘制硬件规格行。"""
    text(draw, (x, y), label.upper(), 25, MUTED, True)
    text(draw, (x, y + 44), value, 43, color, True)


def main():
    """生成故事搭子科技海报 PNG 与 PDF。"""
    canvas = Image.new("RGB", (WIDTH, HEIGHT), BG)
    draw = ImageDraw.Draw(canvas)
    board_path = ROOT / "主板图.jpeg"
    avatar_path = Path(r"C:\Users\xiaoy\AppData\Local\Temp\codex-clipboard-ee7e27d5-a335-4122-aeb1-3db9d6734c30.jpg")

    for x in range(80, WIDTH, 160):
        draw.line((x, 0, x, HEIGHT), fill=GRID, width=2)
    for y in range(80, HEIGHT, 160):
        draw.line((0, y, WIDTH, y), fill=GRID, width=2)
    dots(draw, 1520, 860, 9, 10, 62, CYAN_DARK)
    dots(draw, 160, 4350, 12, 7, 58, CYAN_DARK)

    # 顶部身份区
    draw.rectangle((0, 0, WIDTH, 18), fill=GOLD)
    text(draw, (145, 125), "AI HARDWARE / 48H PROTOTYPE", 30, CYAN, True)
    text(draw, (145, 210), "焊门子弟", 78, INK, True)
    text(draw, (145, 360), "故事搭子", 196, CYAN, True)
    text(draw, (150, 610), "一声唤醒，故事就开始了", 76, GOLD, True)
    text(draw, (150, 735), "故事模式  ·  笑话模式  ·  专注模式  ·  AI 扩展", 34, MUTED)
    draw.line((145, 805, 2250, 805), fill=CYAN_DARK, width=5)
    draw.line((145, 805, 760, 805), fill=CYAN, width=9)

    if avatar_path.exists():
        avatar = fit_image(avatar_path, (0, 0, 260, 260), radius=130)
        canvas.paste(avatar, (1960, 135), avatar)
        draw.ellipse((1960, 135, 2220, 395), outline=GOLD, width=9)
    text(draw, (2250, 470), "PROJECT 01", 28, MUTED, True, "ra")

    # 中央产品英雄区
    hero_y = 960
    draw.rounded_rectangle((125, hero_y, 2275, 2850), radius=36, fill=PANEL, outline=CYAN_DARK, width=5)
    text(draw, (190, hero_y + 90), "DESKTOP AI COMPANION", 30, GOLD, True)
    text(draw, (190, hero_y + 175), "桌面上，一个会讲故事的搭子", 72, INK, True)
    line_wrap(draw, "先用两天做出一个能被叫醒、能切换内容、能真实回应的语音原型，再把 AI 能力一点点接进来。", 195, hero_y + 300, 1120, 36, MUTED, 13)

    board_box = (190, hero_y + 660, 610, 880)
    if board_path.exists():
        board = fit_image(board_path, (0, 0, board_box[2], board_box[3]), radius=22)
        canvas.paste(board, (board_box[0], board_box[1]))
    frame(draw, board_box, CYAN, 5)
    text(draw, (190, hero_y + 1590), "01 / CORE BOARD", 28, CYAN, True)
    text(draw, (190, hero_y + 1645), "ESP32-S3 主控原型", 37, INK, True)

    draw_story_orb(canvas, 1700, hero_y + 1400, 280)
    draw = ImageDraw.Draw(canvas)
    text(draw, (1700, hero_y + 835), "VOICE STORY ENGINE", 28, CYAN, True, "ma")
    text(draw, (1700, hero_y + 1990), "语音唤醒 / 内容播放 / 模式切换", 30, MUTED, False, "ma")

    # 主板到音频核心的连接线
    glow_line(canvas, [(800, hero_y + 1100), (1080, hero_y + 1100), (1270, hero_y + 1400)], CYAN, 8)
    draw = ImageDraw.Draw(canvas)
    draw.polygon([(1270, hero_y + 1400), (1218, hero_y + 1374), (1235, hero_y + 1425)], fill=CYAN)
    text(draw, (900, hero_y + 1000), "HARDWARE → AUDIO", 27, CYAN, True)

    # 模式名称留在版式标题与路线卡中，主视觉只保留声音核心，避免信息互相遮挡。
    text(draw, (1700, hero_y + 2050), "故事  /  笑话  /  专注", 31, MUTED, True, "ma")

    # 能力路线图
    roadmap_y = 3070
    text(draw, (150, roadmap_y), "MVP → NEXT → FUTURE", 31, GOLD, True)
    card(draw, (150, roadmap_y + 105, 650, 390), "NOW / 48H", "两天原型", "语音唤醒、故事与笑话切换、音频反馈。", CYAN)
    card(draw, (875, roadmap_y + 105, 650, 390), "NEXT", "AI 扩展", "接入模型、内容生成、连续对话和更多表达方式。", GOLD)
    card(draw, (1600, roadmap_y + 105, 650, 390), "FUTURE", "个人计划", "个人状态信息录入、方案评估、计划制定和番茄钟。", ORANGE)

    # 极简产品定位
    quote_y = 3740
    draw.line((150, quote_y, 2250, quote_y), fill=CYAN_DARK, width=4)
    text(draw, (150, quote_y + 90), "先做一个会讲故事的搭子，再让它慢慢懂你。", 59, INK, True)
    text(draw, (150, quote_y + 190), "当前重点是语音入口与真实互动，其他能力为可扩展方向。", 34, MUTED)
    text(draw, (2250, quote_y + 135), "OPEN ENDED BY DESIGN", 27, CYAN, True, "ra")

    # 硬件身份铭牌
    spec_y = 4140
    draw.rounded_rectangle((150, spec_y, 2250, 5010), radius=34, fill=PANEL, outline=CYAN_DARK, width=5)
    text(draw, (220, spec_y + 70), "DEVICE IDENTITY", 29, GOLD, True)
    text(draw, (220, spec_y + 145), "硬件身份铭牌", 55, INK, True)
    spec_row(draw, 220, spec_y + 295, "CHIP", "ESP32-S3")
    spec_row(draw, 1200, spec_y + 295, "FLASH", "16 MB")
    spec_row(draw, 220, spec_y + 500, "FLASH VENDOR", "0x46", CYAN)
    spec_row(draw, 1200, spec_y + 500, "FLASH ID", "0x4018", CYAN)
    spec_row(draw, 220, spec_y + 705, "MAC", "68:EE:8F:44:B5:8C")
    spec_row(draw, 1200, spec_y + 705, "TAIL", "B5:8C", GOLD)
    draw.line((220, spec_y + 855, 2180, spec_y + 855), fill=CYAN_DARK, width=4)
    text(draw, (220, spec_y + 895), "焊门子弟  /  AI+硬件  /  故事搭子", 29, MUTED, True)

    text(draw, (WIDTH // 2, 5165), "方案示意  ·  原型开发中", 35, CYAN, True, "ma")
    text(draw, (WIDTH // 2, 5270), "故事先开始，未来慢慢长出来。", 30, MUTED, False, "ma")

    png_path = OUT / "story-companion-poster-tech-2400x5400.png"
    pdf_path = OUT / "story-companion-poster-tech-2400x5400.pdf"
    canvas.save(png_path, format="PNG", optimize=True)
    canvas.save(pdf_path, format="PDF", resolution=76.2)
    print(png_path)
    print(pdf_path)


if __name__ == "__main__":
    main()

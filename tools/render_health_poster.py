"""生成 AI+硬件健康提醒助手的高分辨率展会海报。"""

from pathlib import Path
import math

from PIL import Image, ImageDraw, ImageFont, ImageOps


ROOT = Path(r"D:\MyPro\brainwave")
OUT = ROOT / "outputs" / "health-reminder-poster"
OUT.mkdir(parents=True, exist_ok=True)

WIDTH = 2400
HEIGHT = 5400

BG = "#F3F8F4"
INK = "#172326"
MINT = "#CDEDE3"
TEAL = "#157A78"
TEAL_DARK = "#0E4E55"
GOLD = "#F1B84B"
ORANGE = "#E6794D"
WHITE = "#FFFFFF"
MUTED = "#547174"
LINE = "#B8D4CE"


def font(size: int, bold: bool = False):
    """加载 Windows 中文字体，保证海报中文不会依赖字体替换。"""
    path = r"C:\Windows\Fonts\msyhbd.ttc" if bold else r"C:\Windows\Fonts\msyh.ttc"
    return ImageFont.truetype(path, size=size, index=0)


def fit_image(path: Path, box: tuple[int, int, int, int], radius: int = 0):
    """把本地图片裁切到指定区域，并可选生成圆角蒙版。"""
    x, y, w, h = box
    image = Image.open(path).convert("RGB")
    image = ImageOps.fit(image, (w, h), method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))
    if radius <= 0:
        return image
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, w, h), radius=radius, fill=255)
    image.putalpha(mask)
    return image


def text(draw, xy, value, size, fill=INK, bold=False, anchor="la"):
    """绘制统一字体的海报文字。"""
    draw.text(xy, value, font=font(size, bold), fill=fill, anchor=anchor)


def line_wrap(draw, value, x, y, max_width, size, fill=MUTED, line_gap=18, bold=False):
    """按像素宽度换行绘制说明文字。"""
    current = ""
    rows = []
    for char in value:
        candidate = current + char
        if draw.textlength(candidate, font=font(size, bold)) > max_width and current:
            rows.append(current)
            current = char
        else:
            current = candidate
    if current:
        rows.append(current)
    for index, row in enumerate(rows):
        text(draw, (x, y + index * (size + line_gap)), row, size, fill, bold)
    return y + len(rows) * (size + line_gap)


def draw_pose(draw, cx, cy, scale, bad=False):
    """绘制人体姿态关键点示意，不伪装成真实人脸识别结果。"""
    color = ORANGE if bad else TEAL
    points = {
        "head": (cx, cy - 260 * scale),
        "neck": (cx, cy - 80 * scale),
        "ls": (cx - 155 * scale, cy - 25 * scale),
        "rs": (cx + 155 * scale, cy + 25 * scale),
        "lh": (cx - 110 * scale, cy + 250 * scale),
        "rh": (cx + 115 * scale, cy + 250 * scale),
        "le": (cx - 230 * scale, cy + 190 * scale),
        "re": (cx + 240 * scale, cy + 220 * scale),
    }
    skeleton = [("head", "neck"), ("neck", "ls"), ("neck", "rs"), ("ls", "lh"), ("rs", "rh"), ("ls", "le"), ("rs", "re"), ("lh", "rh")]
    for a, b in skeleton:
        draw.line((points[a], points[b]), fill=color, width=max(8, int(15 * scale)), joint="curve")
    for point in points.values():
        x, y = point
        r = max(18, int(28 * scale))
        draw.ellipse((x - r, y - r, x + r, y + r), fill=WHITE, outline=color, width=max(5, int(9 * scale)))
    draw.arc((cx - 290 * scale, cy - 420 * scale, cx + 290 * scale, cy + 180 * scale), 205, 340, fill=color, width=max(6, int(10 * scale)))


def draw_camera(draw, x, y, scale=1.0):
    """绘制摄像头和检测视线的简化硬件图标。"""
    w, h = int(280 * scale), int(190 * scale)
    draw.rounded_rectangle((x, y, x + w, y + h), radius=int(35 * scale), fill=TEAL_DARK)
    draw.rounded_rectangle((x + 30 * scale, y + 35 * scale, x + w - 30 * scale, y + h - 35 * scale), radius=int(20 * scale), outline=MINT, width=max(5, int(8 * scale)))
    cx, cy = x + w * 0.72, y + h * 0.5
    r = 48 * scale
    draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=GOLD, outline=WHITE, width=max(4, int(7 * scale)))
    draw.ellipse((cx - r * 0.4, cy - r * 0.4, cx + r * 0.4, cy + r * 0.4), fill=INK)
    draw.line((x + w * 0.2, y + h, x + w * 0.2, y + h + 110 * scale), fill=TEAL_DARK, width=max(8, int(14 * scale)))
    draw.line((x + w * 0.8, y + h, x + w * 0.8, y + h + 110 * scale), fill=TEAL_DARK, width=max(8, int(14 * scale)))
    draw.line((x + w * 0.2, y + h + 110 * scale, x + w * 0.8, y + h + 110 * scale), fill=TEAL_DARK, width=max(8, int(14 * scale)))


def draw_rgb_ring(draw, cx, cy, r):
    """绘制桌面反馈灯圈的平面示意。"""
    for offset, color in ((0, GOLD), (18, TEAL), (36, ORANGE)):
        draw.arc((cx - r + offset, cy - r + offset, cx + r - offset, cy + r - offset), 210, 335, fill=color, width=24)
    draw.ellipse((cx - r + 58, cy - r + 58, cx + r - 58, cy + r - 58), fill=WHITE, outline=LINE, width=8)


def card(draw, box, title, body, accent=TEAL):
    """绘制工作流信息卡。"""
    x, y, w, h = box
    draw.rounded_rectangle((x, y, x + w, y + h), radius=34, fill=WHITE, outline=LINE, width=5)
    draw.rounded_rectangle((x, y, x + 20, y + h), radius=10, fill=accent)
    text(draw, (x + 55, y + 48), title, 54, INK, True)
    line_wrap(draw, body, x + 55, y + 132, w - 100, 34, MUTED, 12)


def main():
    """生成高分辨率健康提醒硬件作品海报 PNG 与 PDF。"""
    canvas = Image.new("RGB", (WIDTH, HEIGHT), BG)
    draw = ImageDraw.Draw(canvas)

    board_path = ROOT / "主板图.jpeg"
    camera_path = ROOT / "硬件开发说明书" / "assets" / "camera-adapter-front.jpg"
    avatar_path = Path(r"C:\Users\xiaoy\AppData\Local\Temp\codex-clipboard-ee7e27d5-a335-4122-aeb1-3db9d6734c30.jpg")

    # 顶部深色身份区
    draw.rectangle((0, 0, WIDTH, 790), fill=INK)
    draw.rectangle((0, 0, WIDTH, 18), fill=GOLD)
    text(draw, (150, 125), "AI + 硬件赛道", 42, MINT, True)
    text(draw, (150, 220), "焊门子弟", 78, WHITE, True)
    text(draw, (150, 335), "坐好搭子", 170, GOLD, True)
    text(draw, (155, 555), "别把椅子坐出工龄", 82, WHITE, True)
    text(draw, (158, 675), "AI 桌面健康提醒助手  ·  坐姿检测  ·  语音提醒  ·  灯光反馈", 34, MINT)

    # 队伍头像
    if avatar_path.exists():
        avatar = fit_image(avatar_path, (0, 0, 260, 260), radius=130)
        canvas.paste(avatar, (WIDTH - 430, 115), avatar)
        draw.ellipse((WIDTH - 430, 115, WIDTH - 170, 375), outline=GOLD, width=10)
    text(draw, (WIDTH - 300, 410), "TEAM", 32, MINT, True, "ma")

    # 中央英雄区
    hero_y = 920
    draw.rounded_rectangle((120, hero_y, WIDTH - 120, 2480), radius=55, fill=MINT)
    text(draw, (190, hero_y + 90), "看见坐姿，听懂提醒", 72, TEAL_DARK, True)
    line_wrap(draw, "让桌面设备成为一个懂分寸的健康搭子：发现前倾、歪头和肩部倾斜，及时用语音与灯光给出轻提醒。", 195, hero_y + 210, 1040, 38, TEAL_DARK, 14)

    # 真实硬件照片
    if board_path.exists():
        board = fit_image(board_path, (0, 0, 530, 700), radius=32)
        canvas.paste(board, (170, hero_y + 620), board if board.mode == "RGBA" else None)
        draw.rounded_rectangle((170, hero_y + 620, 700, hero_y + 1320), radius=32, outline=WHITE, width=8)
    text(draw, (435, hero_y + 1370), "ESP32-S3 主控原型", 34, TEAL_DARK, True, "ma")

    # 相机 + 姿态示意
    draw_camera(draw, 980, hero_y + 500, 1.1)
    draw.line((1320, hero_y + 720, 1740, hero_y + 720), fill=TEAL, width=8)
    draw.line((1740, hero_y + 720, 1740, hero_y + 890), fill=TEAL, width=8)
    draw.polygon([(1740, hero_y + 890), (1708, hero_y + 840), (1772, hero_y + 840)], fill=TEAL)
    draw_pose(draw, 1810, hero_y + 1450, 1.15, bad=True)
    text(draw, (1830, hero_y + 1010), "姿态状态", 38, ORANGE, True, "ma")
    text(draw, (1810, hero_y + 1980), "前倾 / 歪头 / 肩部倾斜", 32, TEAL_DARK, True, "ma")
    draw_rgb_ring(draw, 940, hero_y + 1870, 170)
    text(draw, (940, hero_y + 2115), "RGB 反馈", 34, TEAL_DARK, True, "ma")
    draw.arc((760, hero_y + 1440, 1120, hero_y + 1800), 200, 315, fill=GOLD, width=12)
    draw.arc((735, hero_y + 1415, 1145, hero_y + 1825), 200, 315, fill=TEAL, width=12)
    text(draw, (940, hero_y + 2190), "轻提醒，不打断", 34, MUTED, False, "ma")

    # 流程带
    flow_y = 2640
    text(draw, (150, flow_y), "一个完整的健康提醒闭环", 64, INK, True)
    text(draw, (150, flow_y + 100), "采集  →  判断  →  回应", 42, TEAL, True)
    flow = [("01", "采集", "语音唤醒\n摄像头观察姿态"), ("02", "判断", "本地识别\n进入智能工作流"), ("03", "回应", "语音提醒\nRGB 灯光反馈")]
    start_x = 150
    card_w = 650
    for idx, (number, title, body) in enumerate(flow):
        x = start_x + idx * 760
        draw.rounded_rectangle((x, flow_y + 220, x + card_w, flow_y + 600), radius=32, fill=WHITE, outline=LINE, width=5)
        draw.ellipse((x + 45, flow_y + 265, x + 150, flow_y + 370), fill=GOLD if idx == 0 else TEAL)
        text(draw, (x + 97, flow_y + 318), number, 30, INK if idx == 0 else WHITE, True, "mm")
        text(draw, (x + 190, flow_y + 285), title, 52, INK, True)
        for line_idx, body_line in enumerate(body.split("\n")):
            text(draw, (x + 190, flow_y + 390 + line_idx * 55), body_line, 34, MUTED)
        if idx < 2:
            draw.line((x + card_w + 28, flow_y + 410, x + card_w + 100, flow_y + 410), fill=TEAL, width=10)
            draw.polygon([(x + card_w + 100, flow_y + 410), (x + card_w + 68, flow_y + 385), (x + card_w + 68, flow_y + 435)], fill=TEAL)

    # 两个工作流
    work_y = 3440
    text(draw, (150, work_y), "两条现场可演示工作流", 64, INK, True)
    card(draw, (150, work_y + 160, 1000, 470), "语音开工", "唤醒桌面搭子，确认专注任务与状态，设备用语音和灯光给出开始反馈。", GOLD)
    card(draw, (1250, work_y + 160, 1000, 470), "坐姿提醒", "摄像头观察上半身姿态，连续异常后轻声提醒，并用 RGB 状态灯提示需要调整坐姿。", TEAL)

    # 技术身份铭牌
    spec_y = 4110
    draw.rounded_rectangle((150, spec_y, WIDTH - 150, 5050), radius=45, fill=TEAL_DARK)
    text(draw, (220, spec_y + 80), "HARDWARE IDENTITY", 34, GOLD, True)
    text(draw, (220, spec_y + 160), "硬件身份铭牌", 58, WHITE, True)
    specs = [
        ("芯片", "ESP32-S3"),
        ("Flash", "16 MB"),
        ("Flash Vendor", "0x46"),
        ("Flash ID", "0x4018"),
        ("MAC", "68:EE:8F:44:B5:8C"),
        ("尾号", "B5:8C"),
    ]
    for idx, (label, value) in enumerate(specs):
        col = idx % 2
        row = idx // 2
        x = 230 + col * 1080
        y = spec_y + 340 + row * 150
        text(draw, (x, y), label.upper(), 28, MINT, True)
        text(draw, (x, y + 48), value, 48, WHITE, True)
    draw.line((220, spec_y + 830, WIDTH - 220, spec_y + 830), fill=TEAL, width=5)
    text(draw, (220, spec_y + 870), "原型方案  ·  AI+硬件  ·  焊门子弟", 34, MINT, True)

    # 页脚状态
    text(draw, (WIDTH // 2, 5160), "方案示意｜原型开发中", 36, TEAL_DARK, True, "ma")
    text(draw, (WIDTH // 2, 5260), "让每一次坐直，都有一个轻松的理由。", 30, MUTED, False, "ma")

    png_path = OUT / "health-reminder-poster-2400x5400.png"
    pdf_path = OUT / "health-reminder-poster-2400x5400.pdf"
    canvas.save(png_path, format="PNG", optimize=True)
    # 2400x5400 at 76.2 dpi maps to the requested 800x1800 mm print size.
    canvas.save(pdf_path, format="PDF", resolution=76.2)
    print(png_path)
    print(pdf_path)


if __name__ == "__main__":
    main()

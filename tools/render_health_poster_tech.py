"""生成更偏科技展板风格的 AI+硬件健康提醒海报。"""

from pathlib import Path
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageOps

sys.path.insert(0, str(Path(__file__).parent))
from render_health_poster import font, fit_image, text, line_wrap, draw_pose  # noqa: E402


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


def neon_line(canvas, points, color, width=7, glow=26):
    """绘制带柔和光晕的数据连线。"""
    glow_layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow_layer)
    glow_draw.line(points, fill=color, width=glow, joint="curve")
    glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(glow // 2))
    canvas.paste(glow_layer, (0, 0), glow_layer)
    ImageDraw.Draw(canvas).line(points, fill=color, width=width, joint="curve")


def dot_matrix(draw, x, y, cols, rows, spacing, color, alpha_step=1):
    """绘制低密度点阵背景，增强技术系统感。"""
    for row in range(rows):
        for col in range(cols):
            if (row + col) % 3 == 0:
                r = 3 + ((row * 7 + col * 3) % 4)
                draw.ellipse((x + col * spacing - r, y + row * spacing - r,
                              x + col * spacing + r, y + row * spacing + r), fill=color)


def frame(draw, box, color=CYAN_DARK, width=5):
    """绘制硬件照片的技术边框。"""
    x, y, w, h = box
    draw.rectangle((x, y, x + w, y + h), outline=color, width=width)
    mark = 34
    for sx, sy in ((x, y), (x + w, y), (x, y + h), (x + w, y + h)):
        dx = mark if sx == x else -mark
        dy = mark if sy == y else -mark
        draw.line((sx, sy, sx + dx, sy), fill=CYAN, width=width)
        draw.line((sx, sy, sx, sy + dy), fill=CYAN, width=width)


def spec_row(draw, x, y, label, value, value_color=INK):
    """绘制单行硬件规格。"""
    text(draw, (x, y), label.upper(), 26, MUTED, True)
    text(draw, (x, y + 45), value, 45, value_color, True)


def main():
    """生成科技展板风格的高分辨率海报 PNG 与 PDF。"""
    canvas = Image.new("RGB", (WIDTH, HEIGHT), BG)
    draw = ImageDraw.Draw(canvas)
    board_path = ROOT / "主板图.jpeg"
    avatar_path = Path(r"C:\Users\xiaoy\AppData\Local\Temp\codex-clipboard-ee7e27d5-a335-4122-aeb1-3db9d6734c30.jpg")

    # 细网格与点阵，只在边缘和留白区出现，避免压过主体。
    for x in range(80, WIDTH, 160):
        draw.line((x, 0, x, HEIGHT), fill=GRID, width=2)
    for y in range(80, HEIGHT, 160):
        draw.line((0, y, WIDTH, y), fill=GRID, width=2)
    dot_matrix(draw, 1500, 850, 9, 10, 62, CYAN_DARK)
    dot_matrix(draw, 160, 4380, 12, 7, 58, CYAN_DARK)

    # 顶部品牌区
    draw.rectangle((0, 0, WIDTH, 18), fill=GOLD)
    text(draw, (145, 125), "AI HARDWARE / DESKTOP HEALTH", 30, CYAN, True)
    text(draw, (145, 210), "焊门子弟", 78, INK, True)
    text(draw, (145, 360), "坐好搭子", 196, CYAN, True)
    text(draw, (150, 610), "别把椅子坐出工龄", 80, GOLD, True)
    text(draw, (150, 735), "感知方案  ·  状态判断  ·  轻量反馈", 34, MUTED)
    draw.line((145, 805, 2250, 805), fill=CYAN_DARK, width=5)
    draw.line((145, 805, 690, 805), fill=CYAN, width=9)

    # 头像与项目编号
    if avatar_path.exists():
        avatar = fit_image(avatar_path, (0, 0, 260, 260), radius=130)
        canvas.paste(avatar, (1960, 135), avatar)
        draw.ellipse((1960, 135, 2220, 395), outline=GOLD, width=9)
    text(draw, (2250, 470), "PROJECT 01", 28, MUTED, True, "ra")

    # 主视觉技术场
    hero_y = 960
    draw.rounded_rectangle((125, hero_y, 2275, 2850), radius=36, fill=PANEL, outline=CYAN_DARK, width=5)
    text(draw, (190, hero_y + 90), "HUMAN STATE / DESKTOP COMPANION", 30, GOLD, True)
    text(draw, (190, hero_y + 175), "一个会观察状态的桌面硬件原型", 72, INK, True)
    line_wrap(draw, "把复杂的识别与提醒，变成桌面上看得见、听得懂、不会打扰人的反馈。", 195, hero_y + 300, 1080, 36, MUTED, 13)

    # 主板照片与编号
    board_box = (190, hero_y + 650, 625, 910)
    if board_path.exists():
        board = fit_image(board_path, (0, 0, board_box[2], board_box[3]), radius=22)
        canvas.paste(board, (board_box[0], board_box[1]))
    frame(draw, board_box, CYAN, 5)
    text(draw, (190, hero_y + 1605), "01 / CORE BOARD", 28, CYAN, True)
    text(draw, (190, hero_y + 1660), "ESP32-S3 主控原型", 37, INK, True)

    # 中央连接线与人体状态图
    sensor_x, sensor_y = 1080, hero_y + 720
    draw.rounded_rectangle((sensor_x, sensor_y, sensor_x + 290, sensor_y + 195), radius=30, fill=CYAN_DARK, outline=CYAN, width=5)
    draw.ellipse((sensor_x + 180, sensor_y + 50, sensor_x + 250, sensor_y + 120), fill=GOLD, outline=INK, width=5)
    draw.ellipse((sensor_x + 202, sensor_y + 72, sensor_x + 228, sensor_y + 98), fill=BG)
    draw.line((sensor_x + 62, sensor_y + 195, sensor_x + 62, sensor_y + 320), fill=CYAN, width=12)
    draw.line((sensor_x + 228, sensor_y + 195, sensor_x + 228, sensor_y + 320), fill=CYAN, width=12)
    draw.line((sensor_x + 62, sensor_y + 320, sensor_x + 228, sensor_y + 320), fill=CYAN, width=12)
    text(draw, (sensor_x, sensor_y - 50), "SENSOR INPUT / 方案组件", 28, CYAN, True)

    pose_cx, pose_cy = 1770, hero_y + 1480
    # 大环形扫描圈
    for radius, color, start in ((490, CYAN_DARK, 210), (410, CYAN, 215), (330, ORANGE, 220)):
        draw.arc((pose_cx - radius, pose_cy - radius, pose_cx + radius, pose_cy + radius), start, start + 105, fill=color, width=8)
    draw_pose(draw, pose_cx, pose_cy, 1.0, bad=True)
    text(draw, (pose_cx, hero_y + 805), "人体状态", 42, ORANGE, True, "ma")
    text(draw, (pose_cx, hero_y + 2290), "姿态 / 专注 / 休息", 30, MUTED, True, "ma")
    neon_line(canvas, [(sensor_x + 290, sensor_y + 100), (1450, sensor_y + 100), (1450, pose_cy - 370), (pose_cx - 310, pose_cy - 370)], CYAN, 7)
    draw = ImageDraw.Draw(canvas)
    draw.polygon([(pose_cx - 310, pose_cy - 370), (pose_cx - 355, pose_cy - 398), (pose_cx - 355, pose_cy - 342)], fill=CYAN)
    text(draw, (1360, hero_y + 1160), "状态信号", 28, CYAN, True)

    # 右下反馈灯圈
    ring_cx, ring_cy = 1090, hero_y + 2240
    for offset, color in ((0, GOLD), (22, CYAN), (44, ORANGE)):
        draw.arc((ring_cx - 170 + offset, ring_cy - 170 + offset, ring_cx + 170 - offset, ring_cy + 170 - offset), 210, 340, fill=color, width=26)
    draw.ellipse((ring_cx - 105, ring_cy - 105, ring_cx + 105, ring_cy + 105), fill=PANEL_2, outline=CYAN_DARK, width=6)
    text(draw, (ring_cx, ring_cy + 220), "RGB / VOICE FEEDBACK", 26, MUTED, True, "ma")
    neon_line(canvas, [(ring_cx + 170, ring_cy), (1450, ring_cy), (1450, hero_y + 2300), (1600, hero_y + 2300)], GOLD, 7)
    draw = ImageDraw.Draw(canvas)

    # 三段式数据流
    flow_y = 3060
    text(draw, (150, flow_y), "SENSE  →  THINK  →  RESPOND", 31, GOLD, True)
    steps = [("01", "感知", "语音 / 姿态 / 桌面状态", CYAN), ("02", "判断", "智能体与场景工作流", GOLD), ("03", "回应", "语音提醒 / 灯光反馈", ORANGE)]
    for idx, (num, title, desc, color) in enumerate(steps):
        x = 150 + idx * 740
        draw.rounded_rectangle((x, flow_y + 100, x + 650, flow_y + 390), radius=26, fill=PANEL_2, outline=color, width=4)
        draw.ellipse((x + 35, flow_y + 145, x + 135, flow_y + 245), outline=color, width=7)
        text(draw, (x + 85, flow_y + 194), num, 28, color, True, "mm")
        text(draw, (x + 175, flow_y + 135), title, 48, INK, True)
        text(draw, (x + 175, flow_y + 235), desc, 29, MUTED)
        if idx < 2:
            neon_line(canvas, [(x + 670, flow_y + 245), (x + 720, flow_y + 245)], color, 6, 18)
            draw = ImageDraw.Draw(canvas)

    # 少量幽默文案，保持科技板式的克制。
    quote_y = 3660
    draw.line((150, quote_y, 2250, quote_y), fill=CYAN_DARK, width=4)
    text(draw, (150, quote_y + 85), "你的桌面搭子，偶尔管你坐姿。", 62, INK, True)
    text(draw, (150, quote_y + 185), "提醒有分寸，反馈有温度。", 36, MUTED)
    text(draw, (2250, quote_y + 130), "PROTOTYPE / IN PROGRESS", 28, CYAN, True, "ra")

    # 硬件身份铭牌
    spec_y = 4050
    draw.rounded_rectangle((150, spec_y, 2250, 4950), radius=34, fill=PANEL, outline=CYAN_DARK, width=5)
    text(draw, (220, spec_y + 70), "DEVICE IDENTITY", 29, GOLD, True)
    text(draw, (220, spec_y + 145), "硬件身份铭牌", 55, INK, True)
    spec_row(draw, 220, spec_y + 300, "CHIP", "ESP32-S3", INK)
    spec_row(draw, 1200, spec_y + 300, "FLASH", "16 MB", INK)
    spec_row(draw, 220, spec_y + 510, "FLASH VENDOR", "0x46", CYAN)
    spec_row(draw, 1200, spec_y + 510, "FLASH ID", "0x4018", CYAN)
    spec_row(draw, 220, spec_y + 720, "MAC", "68:EE:8F:44:B5:8C", INK)
    spec_row(draw, 1200, spec_y + 720, "TAIL", "B5:8C", GOLD)
    draw.line((220, spec_y + 875, 2180, spec_y + 875), fill=CYAN_DARK, width=4)
    text(draw, (220, spec_y + 910), "焊门子弟  /  AI+硬件  /  桌面健康提醒助手", 29, MUTED, True)

    text(draw, (WIDTH // 2, 5120), "方案示意  ·  原型开发中", 35, CYAN, True, "ma")
    text(draw, (WIDTH // 2, 5230), "让每一次坐直，都有一个轻松的理由。", 30, MUTED, False, "ma")

    png_path = OUT / "health-reminder-poster-tech-2400x5400.png"
    pdf_path = OUT / "health-reminder-poster-tech-2400x5400.pdf"
    canvas.save(png_path, format="PNG", optimize=True)
    canvas.save(pdf_path, format="PDF", resolution=76.2)
    print(png_path)
    print(pdf_path)


if __name__ == "__main__":
    main()

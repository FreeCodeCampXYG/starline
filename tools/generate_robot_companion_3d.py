"""生成可打印的故事搭子机器人分件模型。

模型依据用户提供的外观参考图重建，重点保留可打印的圆角机身、面板、摄像头位、
扬声器区域和主板托架。安装孔位和外设精确尺寸尚未全部实测，因此需要通过参数
调整，不把概念图里的比例当成实物尺寸。
"""

from __future__ import annotations

import argparse
import math
import textwrap
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Sequence

from PIL import Image, ImageDraw


Vec3 = tuple[float, float, float]
Face = tuple[int, int, int]


MATERIALS = {
    "white": (0.93, 0.94, 0.93, "#F0F2F0"),
    "black": (0.03, 0.04, 0.05, "#080A0D"),
    "cyan": (0.35, 0.95, 1.00, "#70F3FF"),
    "green": (0.08, 0.52, 0.26, "#1A9B59"),
    "gray": (0.44, 0.48, 0.50, "#7A8588"),
    "dark_gray": (0.16, 0.18, 0.19, "#292F32"),
    "blue": (0.08, 0.42, 0.80, "#1672CC"),
}


@dataclass
class Mesh:
    """一个轻量三角网格容器，避免依赖专用 CAD 库。"""

    name: str
    vertices: list[Vec3] = field(default_factory=list)
    faces: list[Face] = field(default_factory=list)

    def vertex(self, p: Vec3) -> int:
        self.vertices.append((float(p[0]), float(p[1]), float(p[2])))
        return len(self.vertices) - 1

    def triangle(self, a: int, b: int, c: int) -> None:
        self.faces.append((a, b, c))

    def quad(self, a: int, b: int, c: int, d: int) -> None:
        self.triangle(a, b, c)
        self.triangle(a, c, d)

    def add_mesh(self, other: "Mesh") -> None:
        """把一个局部网格并入当前零件。"""

        offset = len(self.vertices)
        self.vertices.extend(other.vertices)
        self.faces.extend((a + offset, b + offset, c + offset) for a, b, c in other.faces)


@dataclass
class Part:
    name: str
    material: str
    mesh: Mesh


def normalize(v: Vec3) -> Vec3:
    length = math.sqrt(sum(x * x for x in v))
    if length < 1e-9:
        return (0.0, 0.0, 1.0)
    return (v[0] / length, v[1] / length, v[2] / length)


def cross(a: Vec3, b: Vec3) -> Vec3:
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def sub(a: Vec3, b: Vec3) -> Vec3:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def add(a: Vec3, b: Vec3) -> Vec3:
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def scale(v: Vec3, k: float) -> Vec3:
    return (v[0] * k, v[1] * k, v[2] * k)


def rounded_loop_xz(width: float, height: float, radius: float, z0: float, segments: int = 8) -> list[tuple[float, float]]:
    """返回圆角矩形的 x-z 周边点。"""

    radius = max(0.1, min(radius, width / 2 - 0.1, height / 2 - 0.1))
    cx = width / 2
    top = z0 + height
    centers = [
        (cx - radius, top - radius, 0.0, 90.0),
        (-cx + radius, top - radius, 90.0, 180.0),
        (-cx + radius, z0 + radius, 180.0, 270.0),
        (cx - radius, z0 + radius, 270.0, 360.0),
    ]
    points: list[tuple[float, float]] = []
    for center_x, center_z, start, end in centers:
        for i in range(segments + 1):
            angle = math.radians(start + (end - start) * i / segments)
            points.append((center_x + radius * math.cos(angle), center_z + radius * math.sin(angle)))
    return points[:-1]


def rounded_loop_xy(width: float, depth: float, radius: float, z: float, segments: int = 8) -> list[tuple[float, float, float]]:
    """返回 z 固定的圆角矩形周边点。"""

    radius = max(0.1, min(radius, width / 2 - 0.1, depth / 2 - 0.1))
    hx = width / 2
    hy = depth / 2
    centers = [
        (hx - radius, hy - radius, 0.0, 90.0),
        (-hx + radius, hy - radius, 90.0, 180.0),
        (-hx + radius, -hy + radius, 180.0, 270.0),
        (hx - radius, -hy + radius, 270.0, 360.0),
    ]
    points: list[tuple[float, float, float]] = []
    for center_x, center_y, start, end in centers:
        for i in range(segments + 1):
            angle = math.radians(start + (end - start) * i / segments)
            points.append((center_x + radius * math.cos(angle), center_y + radius * math.sin(angle), z))
    return points[:-1]


def add_rounded_prism_xz(mesh: Mesh, width: float, height: float, depth: float, radius: float, z0: float, y: float) -> None:
    """添加沿 y 方向挤出的圆角矩形实心件。"""

    profile = rounded_loop_xz(width, height, radius, z0)
    front = [mesh.vertex((x, y + depth / 2, z)) for x, z in profile]
    back = [mesh.vertex((x, y - depth / 2, z)) for x, z in profile]
    front_center = mesh.vertex((0.0, y + depth / 2, z0 + height / 2))
    back_center = mesh.vertex((0.0, y - depth / 2, z0 + height / 2))
    n = len(profile)
    for i in range(n):
        j = (i + 1) % n
        mesh.triangle(front_center, front[i], front[j])
        mesh.triangle(back_center, back[j], back[i])
        mesh.quad(front[i], back[i], back[j], front[j])


def add_ring_xz(
    mesh: Mesh,
    outer_width: float,
    outer_height: float,
    inner_width: float,
    inner_height: float,
    depth: float,
    outer_radius: float,
    inner_radius: float,
    z0: float,
    y: float,
) -> None:
    """添加圆角矩形环，用作面板边框或机身开口边缘。"""

    outer_profile = rounded_loop_xz(outer_width, outer_height, outer_radius, z0)
    inner_z0 = z0 + (outer_height - inner_height) / 2
    inner_profile = rounded_loop_xz(inner_width, inner_height, inner_radius, inner_z0)
    outer_front = [mesh.vertex((x, y + depth / 2, z)) for x, z in outer_profile]
    outer_back = [mesh.vertex((x, y - depth / 2, z)) for x, z in outer_profile]
    inner_front = [mesh.vertex((x, y + depth / 2, z)) for x, z in inner_profile]
    inner_back = [mesh.vertex((x, y - depth / 2, z)) for x, z in inner_profile]
    n = len(outer_profile)
    for i in range(n):
        j = (i + 1) % n
        mesh.quad(outer_front[i], outer_front[j], inner_front[j], inner_front[i])
        mesh.quad(outer_back[j], outer_back[i], inner_back[i], inner_back[j])
        mesh.quad(outer_front[i], outer_back[i], outer_back[j], outer_front[j])
        mesh.quad(inner_front[j], inner_back[j], inner_back[i], inner_front[i])


def add_rounded_plate_xy(mesh: Mesh, width: float, depth: float, thickness: float, radius: float, z: float) -> None:
    """添加平放在打印床上的圆角矩形底板。"""

    bottom = rounded_loop_xy(width, depth, radius, z)
    top = rounded_loop_xy(width, depth, radius, z + thickness)
    bottom_ids = [mesh.vertex(p) for p in bottom]
    top_ids = [mesh.vertex(p) for p in top]
    bottom_center = mesh.vertex((0.0, 0.0, z))
    top_center = mesh.vertex((0.0, 0.0, z + thickness))
    n = len(bottom)
    for i in range(n):
        j = (i + 1) % n
        mesh.triangle(bottom_center, bottom_ids[j], bottom_ids[i])
        mesh.triangle(top_center, top_ids[i], top_ids[j])
        mesh.quad(bottom_ids[i], bottom_ids[j], top_ids[j], top_ids[i])


def add_box(mesh: Mesh, xmin: float, xmax: float, ymin: float, ymax: float, zmin: float, zmax: float) -> None:
    """添加长方体。"""

    v = [
        mesh.vertex((xmin, ymin, zmin)),
        mesh.vertex((xmax, ymin, zmin)),
        mesh.vertex((xmax, ymax, zmin)),
        mesh.vertex((xmin, ymax, zmin)),
        mesh.vertex((xmin, ymin, zmax)),
        mesh.vertex((xmax, ymin, zmax)),
        mesh.vertex((xmax, ymax, zmax)),
        mesh.vertex((xmin, ymax, zmax)),
    ]
    mesh.quad(v[0], v[1], v[2], v[3])
    mesh.quad(v[4], v[7], v[6], v[5])
    mesh.quad(v[0], v[4], v[5], v[1])
    mesh.quad(v[1], v[5], v[6], v[2])
    mesh.quad(v[2], v[6], v[7], v[3])
    mesh.quad(v[3], v[7], v[4], v[0])


def add_cylinder_y(mesh: Mesh, x: float, y0: float, y1: float, z: float, radius: float, segments: int = 24) -> None:
    """添加轴线沿 y 的圆柱，适合眼睛、镜头和麦克风孔装饰。"""

    a = [mesh.vertex((x + radius * math.cos(2 * math.pi * i / segments), y0, z + radius * math.sin(2 * math.pi * i / segments))) for i in range(segments)]
    b = [mesh.vertex((x + radius * math.cos(2 * math.pi * i / segments), y1, z + radius * math.sin(2 * math.pi * i / segments))) for i in range(segments)]
    ca = mesh.vertex((x, y0, z))
    cb = mesh.vertex((x, y1, z))
    for i in range(segments):
        j = (i + 1) % segments
        mesh.quad(a[i], a[j], b[j], b[i])
        mesh.triangle(ca, a[j], a[i])
        mesh.triangle(cb, b[i], b[j])


def add_ring_y(mesh: Mesh, x: float, y0: float, y1: float, z: float, outer: float, inner: float, segments: int = 32) -> None:
    """添加轴线沿 y 的圆环。"""

    of = [mesh.vertex((x + outer * math.cos(2 * math.pi * i / segments), y1, z + outer * math.sin(2 * math.pi * i / segments))) for i in range(segments)]
    inf = [mesh.vertex((x + inner * math.cos(2 * math.pi * i / segments), y1, z + inner * math.sin(2 * math.pi * i / segments))) for i in range(segments)]
    ob = [mesh.vertex((x + outer * math.cos(2 * math.pi * i / segments), y0, z + outer * math.sin(2 * math.pi * i / segments))) for i in range(segments)]
    inb = [mesh.vertex((x + inner * math.cos(2 * math.pi * i / segments), y0, z + inner * math.sin(2 * math.pi * i / segments))) for i in range(segments)]
    for i in range(segments):
        j = (i + 1) % segments
        mesh.quad(of[i], of[j], inf[j], inf[i])
        mesh.quad(ob[j], ob[i], inb[i], inb[j])
        mesh.quad(of[i], ob[i], ob[j], of[j])
        mesh.quad(inf[j], inb[j], inb[i], inf[i])


def add_cylinder_z(mesh: Mesh, x: float, y: float, z0: float, z1: float, radius: float, segments: int = 20) -> None:
    """添加轴线沿 z 的圆柱。"""

    a = [mesh.vertex((x + radius * math.cos(2 * math.pi * i / segments), y + radius * math.sin(2 * math.pi * i / segments), z0)) for i in range(segments)]
    b = [mesh.vertex((x + radius * math.cos(2 * math.pi * i / segments), y + radius * math.sin(2 * math.pi * i / segments), z1)) for i in range(segments)]
    ca = mesh.vertex((x, y, z0))
    cb = mesh.vertex((x, y, z1))
    for i in range(segments):
        j = (i + 1) % segments
        mesh.quad(a[i], b[i], b[j], a[j])
        mesh.triangle(ca, a[i], a[j])
        mesh.triangle(cb, b[j], b[i])


def add_cylinder_between(mesh: Mesh, p1: Vec3, p2: Vec3, radius: float, segments: int = 16) -> None:
    """添加两点之间的圆柱，用于可选手臂和连接杆。"""

    direction = normalize(sub(p2, p1))
    helper = (0.0, 0.0, 1.0) if abs(direction[2]) < 0.85 else (0.0, 1.0, 0.0)
    u = normalize(cross(direction, helper))
    v = normalize(cross(direction, u))
    a: list[int] = []
    b: list[int] = []
    for i in range(segments):
        angle = 2 * math.pi * i / segments
        radial = add(scale(u, math.cos(angle) * radius), scale(v, math.sin(angle) * radius))
        a.append(mesh.vertex(add(p1, radial)))
        b.append(mesh.vertex(add(p2, radial)))
    ca = mesh.vertex(p1)
    cb = mesh.vertex(p2)
    for i in range(segments):
        j = (i + 1) % segments
        mesh.quad(a[i], a[j], b[j], b[i])
        mesh.triangle(ca, a[j], a[i])
        mesh.triangle(cb, b[i], b[j])


def add_uv_sphere(mesh: Mesh, center: Vec3, radius: float, lat_segments: int = 10, lon_segments: int = 20) -> None:
    """添加低多边形球体，适合快速打印的关节和脚垫。"""

    ids: list[list[int]] = []
    for lat in range(lat_segments + 1):
        phi = math.pi * lat / lat_segments
        row: list[int] = []
        for lon in range(lon_segments):
            theta = 2 * math.pi * lon / lon_segments
            row.append(mesh.vertex((center[0] + radius * math.sin(phi) * math.cos(theta), center[1] + radius * math.sin(phi) * math.sin(theta), center[2] + radius * math.cos(phi))))
        ids.append(row)
    for lat in range(lat_segments):
        for lon in range(lon_segments):
            a = ids[lat][lon]
            b = ids[lat][(lon + 1) % lon_segments]
            c = ids[lat + 1][(lon + 1) % lon_segments]
            d = ids[lat + 1][lon]
            if lat != 0:
                mesh.triangle(a, b, c)
            if lat != lat_segments - 1:
                mesh.triangle(a, c, d)


def add_tube_polyline(mesh: Mesh, points: Sequence[Vec3], radius: float) -> None:
    """用圆柱和球节点生成一条可拆的弧形线条。"""

    for a, b in zip(points, points[1:]):
        add_cylinder_between(mesh, a, b, radius, segments=12)
    for point in points:
        add_uv_sphere(mesh, point, radius, lat_segments=6, lon_segments=12)


def make_model() -> list[Part]:
    """创建机器人外壳、外观零件和电子托架。"""

    # 这些是第一版展示模型的机械参数；主板外形沿用已确认的 60 x 40 mm 名义尺寸。
    body_width = 110.0
    body_height = 140.0
    body_depth = 50.0
    body_z0 = 8.0
    body_radius = 24.0
    wall = 3.0
    front_y = body_depth / 2

    parts: list[Part] = []

    body = Mesh("body_shell")
    outer_profile = rounded_loop_xz(body_width, body_height, body_radius, body_z0)
    inner_profile = rounded_loop_xz(body_width - wall * 2, body_height - wall * 2, body_radius - wall, body_z0 + wall)
    outer_front = [body.vertex((x, front_y, z)) for x, z in outer_profile]
    outer_back = [body.vertex((x, -front_y, z)) for x, z in outer_profile]
    inner_front = [body.vertex((x, front_y - wall, z)) for x, z in inner_profile]
    inner_back = [body.vertex((x, -front_y + wall, z)) for x, z in inner_profile]
    n = len(outer_profile)
    for i in range(n):
        j = (i + 1) % n
        body.quad(outer_front[i], outer_front[j], inner_front[j], inner_front[i])
        body.quad(outer_back[j], outer_back[i], inner_back[i], inner_back[j])
        body.quad(outer_front[i], outer_back[i], outer_back[j], outer_front[j])
        body.quad(inner_front[j], inner_back[j], inner_back[i], inner_front[i])
    parts.append(Part("01_body_shell", "white", body))

    face_bezel = Mesh("face_bezel")
    add_ring_xz(face_bezel, 83, 58, 75, 50, 3.0, 14, 11, 83, front_y + 0.5)
    parts.append(Part("02_face_bezel", "white", face_bezel))

    face = Mesh("face_panel")
    add_rounded_prism_xz(face, 75, 50, 2.3, 11, 86, front_y + 2.0)
    parts.append(Part("03_face_black_panel", "black", face))

    eyes = Mesh("eyes")
    add_cylinder_y(eyes, -19, front_y + 3.0, front_y + 4.4, 112, 7.2)
    add_cylinder_y(eyes, 19, front_y + 3.0, front_y + 4.4, 112, 7.2)
    parts.append(Part("04_eyes", "cyan", eyes))

    mouth = Mesh("mouth")
    smile_points = [(-10, front_y + 3.2, 106), (-6, front_y + 3.2, 103.7), (0, front_y + 3.2, 102.7), (6, front_y + 3.2, 103.7), (10, front_y + 3.2, 106)]
    # 每段保留很小的端部间隙，避免相交圆柱造成非流形笑脸；切片后视觉仍是一条连续笑脸。
    for start, end in zip(smile_points, smile_points[1:]):
        direction = normalize(sub(end, start))
        trimmed_start = add(start, scale(direction, 0.18))
        trimmed_end = add(end, scale(direction, -0.18))
        add_cylinder_between(mouth, trimmed_start, trimmed_end, 1.35, segments=16)
    parts.append(Part("05_smile", "cyan", mouth))

    bay_bezel = Mesh("camera_bay_bezel")
    add_ring_xz(bay_bezel, 82, 62, 70, 50, 3.0, 12, 9, 27, front_y + 0.5)
    parts.append(Part("06_camera_bay_bezel", "white", bay_bezel))

    bay_back = Mesh("camera_bay_back")
    add_rounded_prism_xz(bay_back, 70, 50, 1.8, 9, 33, front_y + 1.7)
    parts.append(Part("07_camera_bay_back", "white", bay_back))

    camera_board = Mesh("camera_board")
    add_rounded_prism_xz(camera_board, 42, 42, 2.2, 3.0, 37, front_y + 3.0)
    parts.append(Part("08_camera_board_placeholder", "green", camera_board))

    camera_parts = Mesh("camera_lens")
    add_ring_y(camera_parts, 0, front_y + 4.0, front_y + 7.0, 58, 10.0, 7.5)
    add_cylinder_y(camera_parts, 0, front_y + 5.0, front_y + 7.6, 58, 6.8, 32)
    parts.append(Part("09_camera_lens", "black", camera_parts))

    camera_glass = Mesh("camera_glass")
    add_cylinder_y(camera_glass, 0, front_y + 7.4, front_y + 8.0, 58, 5.0, 32)
    parts.append(Part("10_camera_glass", "cyan", camera_glass))

    camera_mount = Mesh("camera_mount")
    for x in (-18, 18):
        for z in (41, 75):
            add_cylinder_y(camera_mount, x, front_y + 4.0, front_y + 5.8, z, 2.4, 16)
    parts.append(Part("11_camera_mount_posts", "gray", camera_mount))

    mic = Mesh("mic_holes")
    for x in (-12, -6, 0, 6, 12):
        add_cylinder_y(mic, x, front_y + 2.9, front_y + 4.2, 25.5, 1.5, 16)
    parts.append(Part("12_microphone_holes", "black", mic))

    speaker = Mesh("speaker")
    add_rounded_prism_xz(speaker, 52, 17, 1.8, 7, 10, front_y + 1.8)
    # 白色栅格条表达实际开孔位置，打印时可作为独立贴片或参考。
    for x in (-18, -12, -6, 0, 6, 12, 18):
        add_box(speaker, x - 1.0, x + 1.0, front_y + 2.7, front_y + 3.4, 13, 24)
    parts.append(Part("13_speaker_grille", "black", speaker))

    speaker_bars = Mesh("speaker_bars")
    for x in (-18, -12, -6, 0, 6, 12, 18):
        add_box(speaker_bars, x - 0.8, x + 0.8, front_y + 3.5, front_y + 4.0, 13, 24)
    parts.append(Part("14_speaker_grille_bars", "white", speaker_bars))

    base = Mesh("base")
    add_rounded_plate_xy(base, 88, 42, 3.0, 15, 5.5)
    parts.append(Part("15_base_plate", "white", base))

    feet = Mesh("feet")
    add_uv_sphere(feet, (-34, -10, 5.0), 6.0, lat_segments=6, lon_segments=12)
    add_uv_sphere(feet, (34, -10, 5.0), 6.0, lat_segments=6, lon_segments=12)
    parts.append(Part("16_feet", "black", feet))

    back = Mesh("back_cover")
    add_rounded_prism_xz(back, 100, 124, 2.2, 19, 12, -front_y - 1.0)
    # 背盖上留一个简洁的散热/走线开口视觉区。
    for x in (-18, -12, -6, 0, 6, 12, 18):
        add_box(back, x - 1.0, x + 1.0, -front_y - 2.5, -front_y - 1.2, 122, 130)
    parts.append(Part("17_removable_back_cover", "white", back))

    tray = Mesh("board_tray")
    # 主板资料尺寸为 60 x 40 x 1.6 mm；托架外轮廓增加装配余量。
    add_rounded_plate_xy(tray, 72, 46, 3.0, 4.0, 31.0)
    for x in (-28, 28):
        for y in (-16, 16):
            add_cylinder_z(tray, x, y, 34.0, 42.0, 2.8, 16)
            add_cylinder_z(tray, x, y, 42.0, 43.2, 3.8, 16)
    parts.append(Part("18_mainboard_tray_60x40", "gray", tray))

    extension = Mesh("extension_sockets")
    # 只保留贴身的小扩展安装位，避免改变参考图的机身轮廓。
    add_box(extension, -57, -54, -4, 4, 82, 90)
    add_box(extension, 54, 57, -4, 4, 82, 90)
    parts.append(Part("19_side_extension_reserve", "white", extension))

    # 手臂为可选分件，主体不依赖它们；这样可以先打印机身和电子托架。
    for side, sign in (("left", -1.0), ("right", 1.0)):
        arm = Mesh(f"arm_{side}")
        shoulder = (sign * 57, 0, 96)
        elbow = (sign * 61, 0, 86)
        wrist = (sign * 62, 0, 76)
        hand = (sign * 62, 0, 69)
        add_uv_sphere(arm, shoulder, 6.2, lat_segments=8, lon_segments=16)
        add_cylinder_between(arm, shoulder, elbow, 4.8, segments=14)
        add_uv_sphere(arm, elbow, 4.5, lat_segments=8, lon_segments=16)
        add_cylinder_between(arm, elbow, wrist, 4.2, segments=14)
        add_uv_sphere(arm, hand, 5.8, lat_segments=8, lon_segments=16)
        for dx, dz in ((-2.8, -2.5), (0, -3.5), (2.8, -2.5)):
            add_cylinder_between(arm, (sign * 62 + sign * dx, -1, 67), (sign * 62 + sign * dx, -1, 62 + dz), 1.5, segments=10)
        parts.append(Part(f"20_arm_{side}_optional", "white", arm))

    return parts


def normal_for(vertices: list[Vec3], face: Face) -> Vec3:
    a, b, c = (vertices[i] for i in face)
    return normalize(cross(sub(b, a), sub(c, a)))


def write_ascii_stl(path: Path, mesh: Mesh) -> None:
    """写出 Bambu Studio 可读取的 ASCII STL。"""

    with path.open("w", encoding="ascii", newline="\n") as stream:
        stream.write(f"solid {mesh.name}\n")
        for face in mesh.faces:
            normal = normal_for(mesh.vertices, face)
            stream.write(f"  facet normal {normal[0]:.7g} {normal[1]:.7g} {normal[2]:.7g}\n")
            stream.write("    outer loop\n")
            for index in face:
                x, y, z = mesh.vertices[index]
                stream.write(f"      vertex {x:.7g} {y:.7g} {z:.7g}\n")
            stream.write("    endloop\n")
            stream.write("  endfacet\n")
        stream.write(f"endsolid {mesh.name}\n")


def write_obj(path: Path, parts: list[Part]) -> None:
    """写出带颜色材质的预览 OBJ。"""

    mtl_path = path.with_suffix(".mtl")
    with mtl_path.open("w", encoding="utf-8", newline="\n") as stream:
        for name, (_, _, _, color) in MATERIALS.items():
            rgb = tuple(int(color[i : i + 2], 16) / 255 for i in (1, 3, 5))
            stream.write(f"newmtl {name}\nKd {rgb[0]:.4f} {rgb[1]:.4f} {rgb[2]:.4f}\nKa 0.1 0.1 0.1\nKs 0.1 0.1 0.1\n\n")
    vertex_offset = 1
    with path.open("w", encoding="utf-8", newline="\n") as stream:
        stream.write(f"mtllib {mtl_path.name}\n")
        stream.write("# Story Companion robot concept assembly, units: mm\n")
        for part in parts:
            stream.write(f"o {part.name}\nusemtl {part.material}\n")
            for x, y, z in part.mesh.vertices:
                stream.write(f"v {x:.6f} {y:.6f} {z:.6f}\n")
            for a, b, c in part.mesh.faces:
                stream.write(f"f {a + vertex_offset} {b + vertex_offset} {c + vertex_offset}\n")
            vertex_offset += len(part.mesh.vertices)


def xml_escape(value: str) -> str:
    return value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def write_3mf(path: Path, parts: list[Part]) -> None:
    """写出多对象 3MF，方便 Bambu Studio 一次导入预览。"""

    material_names = list(MATERIALS)
    material_index = {name: index for index, name in enumerate(material_names)}
    objects: list[str] = []
    build: list[str] = []
    for object_id, part in enumerate(parts, start=2):
        vertices = "".join(f'<vertex x="{x:.6f}" y="{y:.6f}" z="{z:.6f}" />' for x, y, z in part.mesh.vertices)
        triangles = "".join(f'<triangle v1="{a}" v2="{b}" v3="{c}" />' for a, b, c in part.mesh.faces)
        objects.append(f'<object id="{object_id}" type="model" pid="1" pindex="{material_index[part.material]}"><mesh><vertices>{vertices}</vertices><triangles>{triangles}</triangles></mesh></object>')
        build.append(f'<item objectid="{object_id}" />')
    base = ''.join(f'<base name="{xml_escape(name)}" displaycolor="{color[3]}" />' for name, color in MATERIALS.items())
    model = f'''<?xml version="1.0" encoding="UTF-8"?>
<model xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02" unit="millimeter" xml:lang="zh-CN">
  <metadata name="Title">故事搭子机器人概念分件模型</metadata>
  <metadata name="Designer">Codex procedural model</metadata>
  <resources><basematerials id="1">{base}</basematerials>{''.join(objects)}</resources>
  <build>{''.join(build)}</build>
</model>
'''
    content_types = '''<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml" />
  <Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml" />
</Types>
'''
    rels = '''<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel" />
</Relationships>
'''
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", content_types)
        archive.writestr("_rels/.rels", rels)
        archive.writestr("3D/3dmodel.model", model)


def project_point(point: Vec3, width: int, height: int) -> tuple[float, float, float]:
    """把模型投影成一个简单的等距预览，避免依赖 3D 软件。"""

    x, y, z = point
    sx = x - y * 0.55
    sy = z + y * 0.28
    return sx, -sy, y + z * 0.05


def write_preview(path: Path, parts: list[Part]) -> None:
    """输出一个可快速查看的模型预览图。"""

    width, height = 900, 900
    image = Image.new("RGB", (width, height), (229, 232, 235))
    draw = ImageDraw.Draw(image)
    projected: list[tuple[float, str, list[tuple[float, float]], tuple[int, int, int]]] = []
    all_points = [p for part in parts for p in part.mesh.vertices]
    raw = [project_point(p, width, height) for p in all_points]
    minx = min(x for x, _, _ in raw)
    maxx = max(x for x, _, _ in raw)
    miny = min(y for _, y, _ in raw)
    maxy = max(y for _, y, _ in raw)
    scale_value = min((width - 100) / max(1.0, maxx - minx), (height - 100) / max(1.0, maxy - miny))
    cx = (minx + maxx) / 2
    cy = (miny + maxy) / 2
    for part in parts:
        color_hex = MATERIALS[part.material][3]
        color = tuple(int(color_hex[i : i + 2], 16) for i in (1, 3, 5))
        projected_vertices = []
        depths = []
        for point in part.mesh.vertices:
            x, y, depth = project_point(point, width, height)
            projected_vertices.append(((x - cx) * scale_value + width / 2, (y - cy) * scale_value + height / 2))
            depths.append(depth)
        for a, b, c in part.mesh.faces:
            polygon = [projected_vertices[a], projected_vertices[b], projected_vertices[c]]
            depth = (depths[a] + depths[b] + depths[c]) / 3
            brightness = 0.72 + 0.28 * max(0.0, min(1.0, (part.mesh.vertices[a][2] / 150)))
            shade = tuple(max(0, min(255, int(channel * brightness))) for channel in color)
            projected.append((depth, part.name, polygon, shade))
    projected.sort(key=lambda item: item[0])
    for _, _, polygon, color in projected:
        draw.polygon(polygon, fill=color)
    draw.rounded_rectangle((26, 26, 874, 874), radius=28, outline=(150, 156, 160), width=2)
    draw.text((44, 42), "Story Companion / first printable concept", fill=(25, 28, 30))
    draw.text((44, 70), "110 x 50 x 148 mm approx.  Mainboard tray: 60 x 40 mm", fill=(70, 74, 78))
    image.save(path)


def write_front_preview(path: Path, parts: list[Part]) -> None:
    """输出参考图角度的正面预览，便于检查外观比例是否偏离。"""

    width, height = 900, 900
    image = Image.new("RGB", (width, height), (229, 232, 235))
    draw = ImageDraw.Draw(image)
    all_points = [p for part in parts for p in part.mesh.vertices]
    minx = min(p[0] for p in all_points)
    maxx = max(p[0] for p in all_points)
    minz = min(p[2] for p in all_points)
    maxz = max(p[2] for p in all_points)
    scale_value = min((width - 130) / max(1.0, maxx - minx), (height - 120) / max(1.0, maxz - minz))
    cx = (minx + maxx) / 2
    cz = (minz + maxz) / 2
    projected: list[tuple[float, str, list[tuple[float, float]], tuple[int, int, int]]] = []
    for part in parts:
        color_hex = MATERIALS[part.material][3]
        color = tuple(int(color_hex[i : i + 2], 16) for i in (1, 3, 5))
        points = [((p[0] - cx) * scale_value + width / 2, (cz - p[2]) * scale_value + height / 2, p[1]) for p in part.mesh.vertices]
        for a, b, c in part.mesh.faces:
            polygon = [(points[index][0], points[index][1]) for index in (a, b, c)]
            # y 越大越靠前，后画的三角面覆盖前面的面。
            depth = (points[a][2] + points[b][2] + points[c][2]) / 3
            projected.append((depth, part.name, polygon, color))
    projected.sort(key=lambda item: item[0])
    for _, _, polygon, color in projected:
        draw.polygon(polygon, fill=color)
    draw.rounded_rectangle((26, 26, 874, 874), radius=28, outline=(150, 156, 160), width=2)
    draw.text((44, 42), "Reference-faithful front view / Story Companion", fill=(25, 28, 30))
    draw.text((44, 70), "Exterior shape fixed from the supplied reference image", fill=(70, 74, 78))
    image.save(path)


def write_scad(path: Path) -> None:
    """写出一份可继续编辑的 OpenSCAD 参数骨架。"""

    content = r'''// 故事搭子机器人概念模型参数骨架
// 单位：mm。此文件用于继续修改外观与装配间隙。
body_w = 110;
body_h = 140;
body_d = 50;
wall = 3;
mainboard_w = 60;
mainboard_d = 40;
camera_w = 42;
speaker_w = 52;

module rounded_body() {
    // 预览外形：圆角长方体，后续可替换为带后盖的 hollow shell。
    minkowski() {
        cube([body_w - 24, body_d - 12, body_h - 24], center=true);
        sphere(r=12, $fn=32);
    }
}

module mainboard_tray() {
    // 60 x 40 mm 主板托架，孔位未实测，先保留可调支柱空间。
    difference() {
        cube([mainboard_w + 12, mainboard_d + 6, 3], center=true);
        for (x=[-28,28]) for (y=[-16,16])
            translate([x,y,0]) cube([7,4,5], center=true);
    }
}

module camera_window() {
    // 摄像头转接板外形未实测，42 mm 为第一版占位参数。
    translate([0, body_d/2 + 1, 58]) cube([camera_w, 3, camera_w], center=true);
}

module speaker_window() {
    translate([0, body_d/2 + 2, 17]) cube([speaker_w, 3, 17], center=true);
}

// 默认显示装配占位模型；可在 OpenSCAD 中继续添加孔、卡扣和后盖。
rounded_body();
mainboard_tray();
camera_window();
speaker_window();
'''
    path.write_text(content, encoding="utf-8", newline="\n")


def write_readme(path: Path, parts: list[Part]) -> None:
    """写出模型说明和导入步骤。"""

    total_triangles = sum(len(part.mesh.faces) for part in parts)
    content = f'''# 故事搭子机器人 3D 模型 v1（已停用的草稿）

**本目录不作打印定稿。** 外观与用户参考图不够接近，部分开孔只是视觉占位；新的演示模型见 `../story-companion-reference-3d/`。后面的早期设计说明仅保留作草稿记录。

这是根据用户提供的白色机器人概念图制作的第一版可打印分件模型。外观轮廓、脸板、胸前摄像头模块、底部扬声器和两侧手臂按参考图保持；内部主板托架和后盖作为装配结构单独处理。

## 文件

- `robot_companion_v1.3mf`：多对象彩色装配预览，可尝试直接用 Bambu Studio 打开。
- `robot_companion_preview.obj` / `.mtl`：带颜色的外观预览。
- `01_body_shell.stl`：机身空腔壳体，后部开放。
- `03_face_black_panel.stl`、`04_eyes.stl`、`05_smile.stl`：面板外观零件。
- `06_camera_bay_bezel.stl` 至 `11_camera_mount_posts.stl`：摄像头预留和镜头装饰。
- `13_speaker_grille.stl`、`14_speaker_grille_bars.stl`：扬声器区域。
- `17_removable_back_cover.stl`：可拆后盖。
- `18_mainboard_tray_60x40.stl`：给 60 × 40 mm 主板使用的独立托架。
- `20_arm_left_optional.stl`、`20_arm_right_optional.stl`：可选手臂，可以先不打印。
- `robot_companion_v1.scad`：OpenSCAD 参数骨架，便于继续调整外形。

## 第一版参数

- 机身约 `110 × 50 × 148 mm`。
- 主板托架按资料标注的 `60 × 40 × 1.6 mm` 名义外形设计，固定孔位置没有套用未知孔距，使用四个独立支柱作为占位。
- 摄像头占位板约 `42 × 42 mm`；摄像头转接板精确尺寸、孔距和排线方向仍需实测。
- 扬声器前框约 `52 × 17 mm`；具体扬声器外形和开孔位置仍需实测。
- 机身前后采用分件结构，方便拆装和修改。

## 外观边界

这版把外观当作固定输入：后续只调整主板托架、摄像头安装槽、扬声器开孔和后盖内部空间，不主动改变机身比例、脸板位置、胸前模块位置或手臂形态。概念图没有提供原始 CAD，因此模型是按图片重建的可打印近似版；如果要做到外观与原作者模型完全一致，需要原始 3D 文件或尺寸图。

## 导入 Bambu Studio

优先打开 `robot_companion_v1.3mf`。如果软件提示格式或对象异常，使用 `File > Import` 分别导入各个 STL；第一次建议只打印 `01_body_shell.stl`、`17_removable_back_cover.stl` 和 `18_mainboard_tray_60x40.stl`，手臂和装饰件属于可选件。

这是一版依据概念图的近似模型，面板视觉和安装位置已经做成分件，主板孔位、摄像头和扬声器的最终装配尺寸仍要用实物测量后修改。脚本生成的网格共 {total_triangles:,} 个三角面。
'''
    path.write_text(textwrap.dedent(content), encoding="utf-8", newline="\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="生成故事搭子机器人分件 3D 模型")
    parser.add_argument("--out-dir", type=Path, default=Path("outputs/robot-companion-3d"))
    args = parser.parse_args()
    out_dir = args.out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    parts = make_model()
    for part in parts:
        write_ascii_stl(out_dir / f"{part.name}.stl", part.mesh)
    write_obj(out_dir / "robot_companion_preview.obj", parts)
    write_3mf(out_dir / "robot_companion_v1.3mf", parts)
    write_preview(out_dir / "robot_companion_preview.png", parts)
    write_front_preview(out_dir / "robot_companion_front_reference.png", parts)
    write_scad(out_dir / "robot_companion_v1.scad")
    write_readme(out_dir / "README.md", parts)
    print(f"生成完成：{out_dir}")
    print(f"零件数量：{len(parts)}")
    print(f"STL 数量：{len(parts)}")
    print(f"3MF：{out_dir / 'robot_companion_v1.3mf'}")


if __name__ == "__main__":
    main()

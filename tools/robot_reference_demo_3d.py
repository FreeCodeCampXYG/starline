"""根据用户提供的机器人正面图生成可旋转的三维概念模型。

正面造型以图片为参考；深度和背面没有原始资料，采用示意尺寸。
脚本不生成可直接生产的结构件，避免把外观网格误认为硬件安装设计。
"""

from __future__ import annotations

import argparse
import base64
import gzip
import json
import math
import zipfile
from dataclasses import dataclass
from pathlib import Path

import manifold3d as md
import numpy as np
import trimesh


OUTLINE = {"width": 102.0, "height": 157.0, "depth": 61.0, "center_z": 80.0}
PALETTE = {
    "ceramic": ("#e7e8e5", 0.55, 0.12),
    "shadow_white": ("#c8cbc9", 0.75, 0.08),
    "metal": ("#9da8a7", 0.32, 0.6),
    "dark": ("#10151b", 0.23, 0.2),
    "lens": ("#070e22", 0.12, 0.35),
    "cyan": ("#8bf5f2", 0.25, 0.04),
    "green": ("#09733a", 0.48, 0.12),
    "gold": ("#d7bb52", 0.3, 0.6),
    "joint": ("#8d9899", 0.55, 0.35),
    "blue": ("#303e98", 0.18, 0.25),
}


@dataclass
class Part:
    """一个带材质名称的三维部件。"""

    name: str
    material: str
    shape: md.Manifold


def squircle(width: float, height: float, center_z: float, exponent: float = 3.4, segments: int = 128) -> np.ndarray:
    """生成带圆润顶部和底部的封闭正面轮廓。"""

    values = []
    for angle in np.linspace(0, 2 * np.pi, segments, endpoint=False):
        c, s = math.cos(angle), math.sin(angle)
        x = width / 2 * math.copysign(abs(c) ** (2 / exponent), c)
        z = center_z + height / 2 * math.copysign(abs(s) ** (2 / exponent), s)
        values.append((x, z))
    return np.asarray(values, dtype=np.float64)


def rounded_rect(width: float, height: float, radius: float, center_z: float, steps: int = 12) -> np.ndarray:
    """生成逆时针的圆角矩形，可用于开窗和面板。"""

    radius = min(radius, width / 2 - 0.01, height / 2 - 0.01)
    corners = [
        (width / 2 - radius, center_z + height / 2 - radius, 0, 90),
        (-width / 2 + radius, center_z + height / 2 - radius, 90, 180),
        (-width / 2 + radius, center_z - height / 2 + radius, 180, 270),
        (width / 2 - radius, center_z - height / 2 + radius, 270, 360),
    ]
    return np.asarray(
        [(x + radius * math.cos(math.radians(a)), z + radius * math.sin(math.radians(a)))
         for x, z, start, end in corners for a in np.linspace(start, end, steps, endpoint=False)],
        dtype=np.float64,
    )


def xz_prism(profile: np.ndarray, front_y: float, depth: float) -> md.Manifold:
    """将正面轮廓沿深度方向拉伸，前方为 y 正方向。"""

    return md.CrossSection([profile]).extrude(depth).rotate((90, 0, 0)).translate((0, front_y, 0))


def rounded_prism(width: float, height: float, radius: float, center_z: float, front_y: float, depth: float) -> md.Manifold:
    """创建沿深度方向的圆角实体。"""

    return xz_prism(rounded_rect(width, height, radius, center_z), front_y, depth)


def rounded_ring(outer: tuple[float, float, float], inner: tuple[float, float, float], center_z: float, front_y: float, depth: float) -> md.Manifold:
    """创建真实中空的面板装饰边框。"""

    ow, oh, rr = outer
    iw, ih, ir = inner
    return rounded_prism(ow, oh, rr, center_z, front_y, depth) - rounded_prism(iw, ih, ir, center_z, front_y + 1, depth + 2)


def ellipsoid(x: float, y: float, z: float, rx: float, ry: float, rz: float) -> md.Manifold:
    """创建一个表面平滑的椭球。"""

    return md.Manifold.sphere(1, 32).scale((rx, ry, rz)).translate((x, y, z))


def tube_between(a: tuple[float, float, float], b: tuple[float, float, float], radius: float) -> md.Manifold:
    """通过两个球的凸包生成圆润连杆。"""

    return md.Manifold.batch_hull([md.Manifold.sphere(radius, 24).translate(a), md.Manifold.sphere(radius, 24).translate(b)])


def disk_y(x: float, front_y: float, z: float, radius: float, depth: float, segments: int = 48) -> md.Manifold:
    """创建朝前的圆片；可堆叠表达镜头和螺丝。"""

    return md.Manifold.cylinder(depth, radius, circular_segments=segments).rotate((90, 0, 0)).translate((x, front_y, z))


def ring_y(x: float, front_y: float, z: float, outer: float, inner: float, depth: float) -> md.Manifold:
    """创建朝前的圆环。"""

    return disk_y(x, front_y, z, outer, depth) - disk_y(x, front_y + 0.5, z, inner, depth + 1)


def body_shape() -> md.Manifold:
    """把多层截面放样为圆润机身，再开出面板和背部空间。"""

    vertices: list[list[float]] = []
    faces: list[list[int]] = []
    segments = 128
    # 正面向前、背面向后收窄，保证正视轮廓接近用户提供的图片。
    layers = [(-30.0, 0.84), (-28.5, 0.92), (-24.0, 0.98), (-17.0, 1.0),
              (14.0, 1.0), (22.0, 0.985), (27.0, 0.95), (30.5, 0.89)]
    for y, factor in layers:
        for x, z in squircle(OUTLINE["width"] * factor, OUTLINE["height"] * factor, OUTLINE["center_z"], 3.3, segments):
            vertices.append([float(x), y, float(z)])
    for layer in range(len(layers) - 1):
        for i in range(segments):
            j = (i + 1) % segments
            a, b = layer * segments + i, layer * segments + j
            c, d = (layer + 1) * segments + j, (layer + 1) * segments + i
            faces.extend([[a, b, c], [a, c, d]])
    back_center, front_center = len(vertices), len(vertices) + 1
    vertices.extend([[0, layers[0][0], OUTLINE["center_z"]], [0, layers[-1][0], OUTLINE["center_z"]]])
    for i in range(segments):
        j = (i + 1) % segments
        faces.append([back_center, j, i])
        faces.append([front_center, (len(layers) - 1) * segments + i, (len(layers) - 1) * segments + j])
    mesh = trimesh.Trimesh(vertices=np.asarray(vertices), faces=np.asarray(faces), process=True)
    mesh.fix_normals(multibody=False)
    if not mesh.is_watertight or mesh.volume <= 0:
        raise RuntimeError("机身外形不是有效的闭合网格")
    body = md.Manifold(md.Mesh(np.asarray(mesh.vertices, dtype=np.float32), np.asarray(mesh.faces, dtype=np.uint32)))
    # 背部和两个正面窗口只用于可视化结构；尺寸还需要实物重新设计。
    back_cavity = rounded_prism(84, 138, 23, 80, 18, 55)
    face_window = rounded_prism(75.0, 51, 17, 120.5, 33, 11)
    chest_window = rounded_prism(73, 69, 16, 49.5, 33, 10)
    body = body - back_cavity - face_window - chest_window
    if body.status() != md.Error.NoError or body.is_empty():
        raise RuntimeError(f"机身布尔运算失败：{body.status()}")
    return body


def add_arm(parts: list[Part], sign: int) -> None:
    """按参考图添加紧贴身体的短手臂和手指示意。"""

    side = "left" if sign < 0 else "right"
    parts.append(Part(f"{side}_shoulder", "joint", ellipsoid(sign * 55.5, 6, 88, 5.5, 5, 5.5)))
    parts.append(Part(f"{side}_shoulder_cap", "cyan", ellipsoid(sign * 55.6, 10.2, 88.2, 3.5, 1.0, 3.5)))
    parts.append(Part(f"{side}_upper_arm", "joint", tube_between((sign * 56, 3, 84), (sign * 61, 3, 72), 3.8)))
    parts.append(Part(f"{side}_sleeve", "ceramic", ellipsoid(sign * 63, 4, 59, 9.1, 8, 12.7)))
    parts.append(Part(f"{side}_wrist", "joint", ellipsoid(sign * 63, 4, 46, 4.6, 4.2, 4.4)))
    parts.append(Part(f"{side}_hand", "ceramic", ellipsoid(sign * 63, 4, 41.5, 6.6, 4, 5.5)))
    for finger, (dx, end_dx, end_z) in enumerate(((-4.1, -6.0, 31), (0, 0.0, 28.5), (4.1, 5.4, 31)), 1):
        p1 = (sign * (63 + dx), 4, 39)
        p2 = (sign * (63 + end_dx), 4, end_z)
        parts.append(Part(f"{side}_finger_{finger}", "ceramic", tube_between(p1, p2, 2.0)))


def make_parts() -> list[Part]:
    """制作可旋转展示用的机器人组件。"""

    parts = [Part("rounded_white_body", "ceramic", body_shape())]
    # 五官和胸部窗口与身体分层，颜色仅用于演示。
    parts += [
        Part("face_edge_metal", "metal", rounded_ring((77.5, 53.5, 18), (74.0, 50.0, 16.4), 120.5, 30.7, 1.8)),
        Part("face_black_screen", "dark", rounded_prism(74.0, 50.0, 16.4, 120.5, 27.0, 1.5)),
        Part("left_eye", "cyan", ellipsoid(-16.0, 28.0, 121.2, 6.3, 1.5, 6.8)),
        Part("right_eye", "cyan", ellipsoid(16.0, 28.0, 121.2, 6.3, 1.5, 6.8)),
    ]
    smile_points = [(-7.4, 28, 112.5), (-4.2, 28, 110.2), (0, 28, 109.4), (4.2, 28, 110.2), (7.4, 28, 112.5)]
    smile = md.Manifold.batch_boolean([tube_between(a, b, 1.15) for a, b in zip(smile_points, smile_points[1:])], md.OpType.Add)
    parts.append(Part("smile", "cyan", smile))
    parts += [
        Part("chest_outer_trim", "shadow_white", rounded_ring((75, 71, 17), (70, 66, 14), 49.5, 30.7, 1.1)),
        Part("chest_inner_trim", "ceramic", rounded_ring((70, 66, 14), (66, 62, 12), 49.5, 29.7, 3.0)),
        Part("chest_recess_back", "shadow_white", rounded_prism(66, 62, 12, 49.5, 23.3, 1.2)),
        Part("camera_board", "green", rounded_prism(41, 39, 2.5, 50.5, 25.7, 1.8)),
    ]
    for x in (-17.3, 17.3):
        for z in (34, 67):
            parts.append(Part(f"mount_{x}_{z}", "gold", ring_y(x, 26.3, z, 1.7, 0.7, 0.6)))
    parts += [
        Part("lens_mount", "metal", rounded_prism(19, 19, 3.4, 51, 28.0, 2.4)),
        Part("lens_outer", "dark", disk_y(0, 30.2, 51, 7.6, 3.0)),
        Part("lens_trim", "metal", ring_y(0, 30.5, 51, 6.6, 5.5, 0.7)),
        Part("lens_glass", "lens", disk_y(0, 30.8, 51, 5.2, 0.8)),
        Part("lens_reflection", "blue", disk_y(-0.6, 31.0, 51.7, 2.9, 0.3)),
    ]
    # 小元件仅用于接近参考图的视觉密度，不对应真实 PCB 布局。
    for i, (x, z, w, h) in enumerate(((-12.5, 53, 5, 9), (12.5, 52, 5, 11), (-11, 38, 7, 3), (11, 38, 7, 3))):
        profile = rounded_rect(w, h, 0.7, z) + np.array([x, 0])
        parts.append(Part(f"pcb_chip_{i}", "dark", xz_prism(profile, 26.3, 0.8)))
    for x in (-19.5, 19.5):
        for index in range(5):
            profile = rounded_rect(1.4, 1.3, 0.2, 43 + index * 3) + np.array([x, 0])
            parts.append(Part(f"pcb_pad_{x}_{index}", "gold", xz_prism(profile, 26.4, 0.4)))
    parts += [
        Part("upper_small_port", "dark", rounded_prism(12, 4, 1.8, 86.0, 31.2, 1.0)),
        Part("speaker_border", "shadow_white", rounded_prism(30, 11.5, 5.5, 8.5, 30.1, 2.0)),
        Part("speaker_dark", "dark", rounded_prism(27, 9, 4.2, 8.5, 31.0, 1.2)),
    ]
    for x in (-9, -6, -3, 0, 3, 6, 9):
        profile = rounded_rect(1.5, 7.5, 0.7, 8.5) + np.array([x, 0])
        parts.append(Part(f"speaker_bar_{x}", "ceramic", xz_prism(profile, 31.6, 0.8)))
    parts.append(Part("left_foot", "shadow_white", ellipsoid(-32, -2, 2.5, 7, 8, 3.5)))
    parts.append(Part("right_foot", "shadow_white", ellipsoid(32, -2, 2.5, 7, 8, 3.5)))
    add_arm(parts, -1)
    add_arm(parts, 1)
    return parts


def shape_mesh(shape: md.Manifold) -> trimesh.Trimesh:
    """转换为三角网格，并拒绝空或失败的几何。"""

    if shape.status() != md.Error.NoError or shape.is_empty():
        raise RuntimeError(f"生成的部件为空或无效：{shape.status()}")
    mesh = shape.to_mesh()
    result = trimesh.Trimesh(vertices=np.asarray(mesh.vert_properties)[:, :3], faces=np.asarray(mesh.tri_verts), process=True)
    if not result.is_watertight:
        raise RuntimeError("生成的部件不是闭合网格")
    return result


def write_demo(parts: list[Part], output: Path, three_path: Path) -> None:
    """生成离线可旋转预览和带材质 GLB。"""

    scene = trimesh.Scene()
    serializable = []
    for part in parts:
        mesh = shape_mesh(part.shape)
        color = PALETTE[part.material][0]
        rgba = [int(color[i:i + 2], 16) for i in (1, 3, 5)] + [255]
        mesh.visual.vertex_colors = np.tile(rgba, (len(mesh.vertices), 1))
        scene.add_geometry(mesh, node_name=part.name, geom_name=part.name)
        serializable.append({
            "name": part.name,
            "material": part.material,
            "vertices": np.round(mesh.vertices, 4).reshape(-1).tolist(),
            "faces": mesh.faces.reshape(-1).tolist(),
        })
    # glTF 以米计量且 y 轴向上；浏览器和 3MF 仍保持毫米、z 轴向上的建模坐标。
    scene.apply_transform(np.array([[0.001, 0, 0, 0], [0, 0, 0.001, 0], [0, -0.001, 0, 0], [0, 0, 0, 1]]))
    glb = scene.export(file_type="glb")
    (output / "story_companion_reference_demo.glb").write_bytes(glb)
    write_3mf_preview(output / "story_companion_appearance_preview.3mf", parts)
    # 机械尺寸只是占位，不输出标为生产就绪的 STL。
    packed = base64.b64encode(gzip.compress(json.dumps(serializable, separators=(",", ":")).encode(), compresslevel=9)).decode()
    template = (Path(__file__).with_name("robot_reference_demo_template.html")).read_text(encoding="utf-8")
    html = template.replace("__PACKED_MODEL__", packed).replace("__PALETTE__", json.dumps(PALETTE, ensure_ascii=False))
    html = html.replace("__THREE_SOURCE__", three_path.read_text(encoding="utf-8"))
    (output / "打开查看机器人3D.html").write_text(html, encoding="utf-8", newline="\n")


def write_3mf_preview(path: Path, parts: list[Part]) -> None:
    """生成便于在切片软件查看的 3MF 外观模型，并保持各部件独立。"""

    materials = list(PALETTE)
    material_xml = "".join(
        f'<base name="{name}" displaycolor="{PALETTE[name][0]}" />' for name in materials
    )
    objects = []
    items = []
    for object_id, part in enumerate(parts, 2):
        mesh = shape_mesh(part.shape)
        vertices = "".join(f'<vertex x="{x:.5f}" y="{y:.5f}" z="{z:.5f}" />' for x, y, z in mesh.vertices)
        triangles = "".join(f'<triangle v1="{a}" v2="{b}" v3="{c}" />' for a, b, c in mesh.faces)
        objects.append(
            f'<object id="{object_id}" type="model" name="{part.name}" pid="1" pindex="{materials.index(part.material)}">'
            f'<mesh><vertices>{vertices}</vertices><triangles>{triangles}</triangles></mesh></object>'
        )
        items.append(f'<item objectid="{object_id}" />')
    model = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<model xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02" unit="millimeter" xml:lang="zh-CN">'
        '<metadata name="Title">故事搭子外观预览：非打印定稿</metadata><resources>'
        f'<basematerials id="1">{material_xml}</basematerials>{"".join(objects)}</resources>'
        f'<build>{"".join(items)}</build></model>'
    )
    types = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml" />'
        '<Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml" /></Types>'
    )
    rels = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Target="/3D/3dmodel.model" Id="rel0" '
        'Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel" /></Relationships>'
    )
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", types)
        archive.writestr("_rels/.rels", rels)
        archive.writestr("3D/3dmodel.model", model)


def main() -> None:
    """生成离线 3D 演示文件和可编辑生成代码入口。"""

    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--three", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    parts = make_parts()
    write_demo(parts, args.output, args.three)
    print(f"已生成 {len(parts)} 个可视部件；输出目录：{args.output}")


if __name__ == "__main__":
    main()

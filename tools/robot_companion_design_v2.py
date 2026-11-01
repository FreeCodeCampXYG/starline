"""生成故事搭子外观、换肤与结构示意的离线演示。

正面以用户提供的机器人图片为参考；背面、内部零件和打印摆放均为概念示意。
本程序不生成设备 G-code，也不将示意结构作为可直接打印的工程设计。
"""

from __future__ import annotations

import argparse
import base64
import gzip
import json
import math
from pathlib import Path

import manifold3d as md
import numpy as np
import trimesh

import robot_reference_demo_3d as base


def outline_reference() -> np.ndarray:
    """根据参考图的正视比例构建机身轮廓，深度仍是示意。"""

    anchors = np.asarray([
        (0.3, 0.7), (1.5, 15), (2.5, 23), (5, 31), (10, 38), (18, 44),
        (30, 48), (48, 50.5), (75, 51), (98, 50), (114, 48.5),
        (128, 46), (139, 42), (148, 35), (154, 25), (158.5, 14), (160, 0.7),
    ], dtype=float)
    right = []
    for i in range(len(anchors) - 1):
        z0, x0 = anchors[i]
        z1, x1 = anchors[i + 1]
        dz = z1 - z0
        prev = anchors[max(0, i - 1)]
        nxt = anchors[min(len(anchors) - 1, i + 2)]
        slope0 = (x1 - prev[1]) / max(1e-6, z1 - prev[0])
        slope1 = (nxt[1] - x0) / max(1e-6, nxt[0] - z0)
        for step in range(20):
            t = step / 20
            t2, t3 = t * t, t * t * t
            h00, h10 = 2 * t3 - 3 * t2 + 1, t3 - 2 * t2 + t
            h01, h11 = -2 * t3 + 3 * t2, t3 - t2
            x = h00 * x0 + h10 * dz * slope0 + h01 * x1 + h11 * dz * slope1
            right.append((x, z0 + dz * t))
    right.append((anchors[-1, 1], anchors[-1, 0]))
    # 将右侧由下到上、左侧由上到下拼成轮廓；上下的小段自然闭合。
    return np.asarray(right + [(-x, z) for x, z in reversed(right)], dtype=np.float64)


def reference_body() -> md.Manifold:
    """按照片轮廓制作圆润壳体并保留正面窗口和背部空间。"""

    profile = outline_reference()
    n = len(profile)
    vertices: list[list[float]] = []
    faces: list[list[int]] = []
    layers = []
    # 多切片平滑放样，减少稀疏截面在渲染中形成的横向折带。
    for index in range(49):
        t = index / 48
        y = -30.0 + 60.5 * t
        if t < 0.25:
            factor = 0.84 + 0.16 * (0.5 - 0.5 * math.cos(math.pi * t / 0.25))
        elif t > 0.78:
            factor = 0.84 + 0.16 * (0.5 + 0.5 * math.cos(math.pi * (t - 0.78) / 0.22))
        else:
            factor = 1.0
        layers.append((y, factor))
    for y, factor in layers:
        for x, z in profile:
            vertices.append([float(x * factor), y, float(80 + (z - 80) * factor)])
    for layer in range(len(layers) - 1):
        for i in range(n):
            j = (i + 1) % n
            a, b = layer * n + i, layer * n + j
            c, d = (layer + 1) * n + j, (layer + 1) * n + i
            faces.extend([[a, b, c], [a, c, d]])
    back_center, front_center = len(vertices), len(vertices) + 1
    vertices.extend([[0, layers[0][0], 80], [0, layers[-1][0], 80]])
    for i in range(n):
        j = (i + 1) % n
        faces.append([back_center, j, i])
        faces.append([front_center, (len(layers) - 1) * n + i, (len(layers) - 1) * n + j])
    mesh = trimesh.Trimesh(vertices=np.asarray(vertices), faces=np.asarray(faces), process=True)
    mesh.fix_normals(multibody=False)
    if not mesh.is_watertight or mesh.volume <= 0:
        raise RuntimeError("参考机身轮廓无法形成闭合网格")
    body = md.Manifold(md.Mesh(np.asarray(mesh.vertices, dtype=np.float32), np.asarray(mesh.faces, dtype=np.uint32)))
    # 窗口和背仓仅表现外观；未测孔位之前不得将其视为可装配结构。
    cavity = base.rounded_prism(84, 138, 23, 80, 18, 55)
    face = base.rounded_prism(75, 51, 17, 120.5, 33, 11)
    chest = base.rounded_prism(73, 69, 16, 49.5, 33, 10)
    result = body - cavity - face - chest
    if result.status() != md.Error.NoError or result.is_empty():
        raise RuntimeError(f"机身窗口处理失败：{result.status()}")
    return result


def internal_parts() -> list[base.Part]:
    """创建用于解释空间分配的内部占位件，不模拟实际接线。"""

    parts = [
        base.Part("diagram_main_board", "green", base.rounded_prism(40, 60, 2.5, 84, -3.4, 1.6)),
        base.Part("diagram_cpu", "metal", base.rounded_prism(20, 18, 2.0, 91, -5.4, 1.8)),
        base.Part("diagram_audio_board", "green", base.rounded_prism(23, 26, 2, 98, -2, 1.6).translate((25, 0, 0))),
        base.Part("diagram_speaker", "dark", base.disk_y(24, -1.5, 43, 11, 5)),
        base.Part("diagram_speaker_cone", "joint", base.disk_y(24, -6.7, 43, 7, 1.1)),
        base.Part("diagram_microphone", "metal", base.disk_y(-26, -3, 115, 3, 3)),
        base.Part("diagram_tray", "shadow_white", base.rounded_prism(47, 67, 4, 84, -1.2, 2)),
    ]
    # 线仅表示留有走线空间，颜色和端点不代表 GPIO 或真实电气连接。
    for index, (a, b) in enumerate([
        ((-12, -4, 54), (7, -4, 43)),
        ((7, -4, 43), (16, -4, 43)),
        ((-20, -4, 102), (-24, -4, 112)),
    ]):
        parts.append(base.Part(f"diagram_wire_{index}", "cyan", base.tube_between(a, b, 0.6)))
    return parts


def make_parts() -> list[base.Part]:
    """复用已确认的主要正面特征，新增可拆后盖和内部示意。"""

    parts = base.make_parts()
    parts[0] = base.Part("rounded_white_body", "ceramic", reference_body())
    # 接缝只补充参考图可见的前表面细节，不据此声称机械连接方式已确定。
    seam = md.Manifold.cube((115, 14, 0.38)).translate((-57.5, 19, 90.4))
    seam_band = parts[0].shape ^ seam
    parts[0] = base.Part("rounded_white_body", "ceramic", parts[0].shape - seam)
    parts.append(base.Part("head_body_seam", "joint", seam_band))
    # 金属固定耳和小螺丝补足胸前凹槽的细节，仍属于外观而非真实孔位合同。
    for x in (-29, 29):
        for z in (27, 73):
            ear = base.rounded_rect(8.5, 3.0, 0.7, z) + np.array([x, 0])
            parts.append(base.Part(f"chest_clip_{x}_{z}", "metal", base.xz_prism(ear, 28.8, 1.2)))
            parts.append(base.Part(f"chest_screw_{x}_{z}", "dark", base.disk_y(x, 29.1, z, 0.8, 0.4)))
    parts.append(base.Part("chest_lower_screw", "joint", base.ring_y(0, 30.8, 16.2, 1.6, 0.8, 0.6)))
    for sign in (-1, 1):
        sleeve = md.Manifold.batch_hull([
            base.ellipsoid(sign * 63, 4, 49, 8.6, 7.0, 2.2),
            base.ellipsoid(sign * 61.5, 4, 68, 5.0, 5.5, 2.5),
        ])
        sleeve_name = f"{'left' if sign < 0 else 'right'}_sleeve"
        parts = [base.Part(p.name, p.material, sleeve) if p.name == sleeve_name else p for p in parts]
        for index in range(3):
            z = 75.0 + index * 3.0
            x = sign * (59.5 - index * 1.1)
            parts.append(base.Part(f"{'left' if sign < 0 else 'right'}_arm_ridge_{index}", "shadow_white", base.ellipsoid(x, 3, z, 4.4, 4.6, 0.8)))
    parts.append(base.Part("rear_cover", "ceramic", base.rounded_prism(82, 129, 23, 80, -29.8, 2.5)))
    parts.append(base.Part("rear_trim", "shadow_white", base.rounded_ring((82, 129, 23), (79, 126, 21), 80, -32.4, 0.7)))
    for index, x in enumerate((-8, -4, 0, 4, 8)):
        slot = base.rounded_rect(2, 10, 0.8, 28) + np.array([x, 0])
        parts.append(base.Part(f"rear_vent_{index}", "joint", base.xz_prism(slot, -32.6, 0.4)))
    parts.extend(internal_parts())
    return parts


def write_preview(parts: list[base.Part], output: Path, three: Path, reference: Path) -> None:
    """保存自包含网页及仅用于展示的三维文件。"""

    objects = []
    scene = trimesh.Scene()
    for part in parts:
        mesh = base.shape_mesh(part.shape)
        color = base.PALETTE[part.material][0]
        rgba = [int(color[i:i + 2], 16) for i in (1, 3, 5)] + [255]
        mesh.visual.vertex_colors = np.tile(rgba, (len(mesh.vertices), 1))
        scene.add_geometry(mesh, node_name=part.name, geom_name=part.name)
        objects.append({
            "name": part.name,
            "material": part.material,
            "vertices": np.round(mesh.vertices, 4).reshape(-1).tolist(),
            "faces": mesh.faces.reshape(-1).tolist(),
        })
    # 真实几何剖成三段只用于演示分件，尚未加入定位销、螺丝或装配公差。
    upper_and_mid, lower = parts[0].shape.split_by_plane((0, 0, 1), 53.0)
    upper, middle = upper_and_mid.split_by_plane((0, 0, 1), 103.0)
    sliced_objects = []
    for name, shape, offset in (("上段机壳", upper, 28), ("中段机壳", middle, 0), ("下段机壳", lower, -28)):
        mesh = base.shape_mesh(shape)
        sliced_objects.append({"name": name, "offset": offset, "vertices": np.round(mesh.vertices, 4).reshape(-1).tolist(), "faces": mesh.faces.reshape(-1).tolist()})
    original_volume = parts[0].shape.volume()
    cut_volume = sum(s.volume() for s in (upper, middle, lower))
    if not math.isclose(original_volume, cut_volume, rel_tol=1e-6):
        raise RuntimeError("剖切后机壳体积不守恒")
    payload = base64.b64encode(gzip.compress(json.dumps(objects, separators=(",", ":")).encode(), compresslevel=9)).decode()
    cuts_payload = base64.b64encode(gzip.compress(json.dumps(sliced_objects, separators=(",", ":")).encode(), compresslevel=9)).decode()
    img = "data:image/png;base64," + base64.b64encode(reference.read_bytes()).decode()
    template = Path(__file__).with_name("robot_companion_design_v2.html").read_text(encoding="utf-8")
    page = (template.replace("__THREE_SOURCE__", three.read_text(encoding="utf-8"))
            .replace("__PACKED_MODEL__", payload)
            .replace("__PACKED_CUTS__", cuts_payload)
            .replace("__PALETTE__", json.dumps(base.PALETTE, ensure_ascii=False))
            .replace("__REFERENCE_IMAGE__", img))
    (output / "打开故事搭子设计演示.html").write_text(page, encoding="utf-8", newline="\n")
    # 内部占位件只展示空间分配，不写入 3MF，避免被误认为真实装配件。
    printable_appearance = [p for p in parts if not p.name.startswith("diagram_")]
    base.write_3mf_preview(output / "机器人外观预览_未切片.3mf", printable_appearance)
    scene.apply_transform(np.array([[0.001, 0, 0, 0], [0, 0, 0.001, 0], [0, -0.001, 0, 0], [0, 0, 0, 1]]))
    (output / "故事搭子外观演示.glb").write_bytes(scene.export(file_type="glb"))
    print(f"演示部件 {len(parts)} 个，其中 {len(parts) - len(printable_appearance)} 个为内部示意")


def main() -> None:
    """在指定目录生成新版离线设计演示。"""

    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--three", type=Path, required=True)
    parser.add_argument("--reference", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    write_preview(make_parts(), args.output, args.three, args.reference)
    print(f"已生成：{args.output}")


if __name__ == "__main__":
    main()

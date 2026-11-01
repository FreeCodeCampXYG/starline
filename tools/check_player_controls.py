"""经已连接 USB 串口验证播放器操作；生成低幅测试音，临时服务，不保存串口原文。"""
from __future__ import annotations

import argparse
import array
import functools
import http.server
import json
import math
from pathlib import Path
import re
import threading
import time

import serial


def main() -> None:
    """测试暂停/继续/停止及串口状态，不能用命令入队成功代替扬声器听感。"""
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", required=True)
    parser.add_argument("--host-ip", required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    media = root / "现场音频测试"
    pcm = media / "player_control_probe.pcm"
    sample_rate = 16000
    # 幅值远低于满幅，避免测试音过响；不改写设备已保存的音量。
    samples = array.array("h", (int(500 * math.sin(2 * math.pi * 330 * i / sample_rate)) for i in range(sample_rate * 24)))
    pcm.write_bytes(samples.tobytes())
    requests: list[str] = []

    class Handler(http.server.SimpleHTTPRequestHandler):
        def log_message(self, format: str, *values: object) -> None:
            if self.path == "/player_control_probe.pcm":
                requests.append(str(values[1]) if len(values) > 1 else "request")

    server = http.server.ThreadingHTTPServer(("0.0.0.0", 18080), functools.partial(Handler, directory=str(media)))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    log: list[str] = []
    device = serial.Serial()
    device.port, device.baudrate, device.timeout = args.port, 115200, 0.1
    device.dtr, device.rts = False, False

    def observe(seconds: float) -> str:
        end = time.monotonic() + seconds
        chunks = []
        while time.monotonic() < end:
            chunks.append(device.read(device.in_waiting or 1))
        text = b"".join(chunks).decode("utf-8", errors="replace")
        log.append(text)
        return text

    def command(value: str, seconds: float) -> str:
        device.write((value + "\r\n").encode("ascii"))
        return observe(seconds)

    try:
        device.open()
        observe(0.5)
        command(f"play_url http://{args.host_ip}:18080/player_control_probe.pcm", 4)
        pause = command("player pause", 1.0)
        paused_a = command("player status", 0.5)
        observe(1.0)
        paused_b = command("player status", 0.5)
        resume = command("player resume", 1.0)
        resumed = command("player status", 0.5)
        stopped = command("player stop", 1.5)
        idle = command("player status", 0.5)
        all_text = "\n".join(log)

        def position(text: str):
            match = re.search(r"state=(\d+) operation=(\d+) position=(\d+)", text)
            return {"state": int(match[1]), "operation": int(match[2]), "position_ms": int(match[3])} if match else None

        result = {
            "scope": "USB串口+低幅PCM HTTP+真实应用操作；不代表网页/平台云转发或主观听感通过",
            "http_requests": requests,
            "pause_command_ok": bool(re.search(r"cloud control action=1 resource=0 ret=0", pause)),
            "resume_command_ok": bool(re.search(r"cloud control action=2 resource=0 ret=0", resume)),
            "stop_command_ok": bool(re.search(r"cloud control action=3 resource=0 ret=0", stopped)),
            "paused_first": position(paused_a), "paused_second": position(paused_b),
            "resumed": position(resumed),
            "idle_after_stop": "player-control-v1: idle" in idle,
            "audio_events": re.findall(r"event=(\d+) operation=(\d+) result=(-?\d+) position=(\d+)", all_text),
            "flow_control_busy_seen": "flow control" in all_text.lower() or "flow-control" in all_text.lower() or "tx gate busy" in all_text.lower(),
            "diagnostic_errors": [re.sub(r"https?://\S+", "[URL]", line) for line in all_text.splitlines()
                                  if re.search(r"fail|error|busy|unsupported|invalid|position|player|control|pipeline|decoder|ret=", line, re.I)
                                  and not re.search(r"password|secret|token|credential|license|payload|authorization", line, re.I)][-30:],
        }
        destination = root / "outputs" / "story-companion-player-firmware" / "hardware-control-check.json"
        destination.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(result, ensure_ascii=True, indent=2))
    finally:
        if device.is_open:
            device.close()
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    main()

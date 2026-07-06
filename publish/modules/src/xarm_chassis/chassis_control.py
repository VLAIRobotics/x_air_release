#!/usr/bin/env python3
import subprocess
import threading
import time
import signal
import sys

CHASSIS_STATE = "stop"
LIFT_STATE = "lift_stop"
RUNNING = True

CHASSIS_FRAMES = {
    "stop": {"left": "601#2B18230000000000", "right": "603#2B18330000000000"},
    "left": {"left": "601#2B182300E9FFFFFF", "right": "603#2B183300E9FFFFFF"},
    "right": {"left": "601#2B18230018000000", "right": "603#2B18330018000000"},
    "forward": {"left": "601#2B18230017000000", "right": "603#2B183300E8FFFFFF"},
    "backward": {"left": "601#2B182300E8FFFFFF", "right": "603#2B18330018000000"}
}

LIFT_FRAMES = {
    "lift_stop": "600#0000000000000000",
    "lift_up": "600#0000000000000002",
    "lift_down": "600#0000000000000001"
}

SEND_INTERVAL = 0.2


def cansend(frame):
    subprocess.run(["cansend", "can2", frame], check=False)


def sender_thread():
    global CHASSIS_STATE, LIFT_STATE
    while RUNNING:
        chassis = CHASSIS_FRAMES.get(CHASSIS_STATE, CHASSIS_FRAMES["stop"])
        lift = LIFT_FRAMES.get(LIFT_STATE, LIFT_FRAMES["lift_stop"])
        cansend(chassis["left"])
        cansend(chassis["right"])
        cansend(lift)
        time.sleep(SEND_INTERVAL)


def cleanup(signum=None, frame=None):
    global RUNNING
    print("\n正在停止底盘和立柱...")
    cansend("601#2B18230000000000")
    cansend("603#2B18330000000000")
    cansend("600#0000000000000000")
    RUNNING = False
    sys.exit(0)


def main():
    global CHASSIS_STATE, LIFT_STATE
    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    t = threading.Thread(target=sender_thread, daemon=True)
    t.start()

    print("===== 底盘控制 =====")
    print("底盘运动 (1-5):")
    print("  1. 静止")
    print("  2. 左转")
    print("  3. 右转")
    print("  4. 前进")
    print("  5. 后退")
    print("立柱控制 (6-8):")
    print("  6. 立柱上升")
    print("  7. 立柱下降")
    print("  8. 立柱静止")
    print("q. 退出")
    print("")

    while True:
        try:
            cmd = input("请输入命令 [1-8/q]: ").strip()
            if cmd == "1":
                CHASSIS_STATE = "stop"
                print(f"→ 底盘: 静止  |  立柱: {LIFT_STATE.replace('lift_', '')}")
            elif cmd == "2":
                CHASSIS_STATE = "left"
                print(f"→ 底盘: 左转  |  立柱: {LIFT_STATE.replace('lift_', '')}")
            elif cmd == "3":
                CHASSIS_STATE = "right"
                print(f"→ 底盘: 右转  |  立柱: {LIFT_STATE.replace('lift_', '')}")
            elif cmd == "4":
                CHASSIS_STATE = "forward"
                print(f"→ 底盘: 前进  |  立柱: {LIFT_STATE.replace('lift_', '')}")
            elif cmd == "5":
                CHASSIS_STATE = "backward"
                print(f"→ 底盘: 后退  |  立柱: {LIFT_STATE.replace('lift_', '')}")
            elif cmd == "6":
                LIFT_STATE = "lift_up"
                print(f"→ 底盘: {CHASSIS_STATE}  |  立柱: 上升")
            elif cmd == "7":
                LIFT_STATE = "lift_down"
                print(f"→ 底盘: {CHASSIS_STATE}  |  立柱: 下降")
            elif cmd == "8":
                LIFT_STATE = "lift_stop"
                print(f"→ 底盘: {CHASSIS_STATE}  |  立柱: 静止")
            elif cmd == "q":
                cleanup()
            elif cmd == "":
                continue
            else:
                print("无效命令，请输入 1-8 或 q")
        except EOFError:
            cleanup()


if __name__ == "__main__":
    main()

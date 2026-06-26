#!/usr/bin/env python3
"""
底盘CAN监听脚本
功能：监听CAN总线，识别底盘控制消息并显示

支持的CAN帧识别：
  125 AA BB CC DD 03 00 00 00 → 前进
  126 AA BB CC DD 04 00 00 00 → 后退
  127 EE FF 11 22 05 00 00 00 → 左转
  128 EE FF 11 22 06 00 00 00 → 右转
  12A CC DD EE FF 07 00 00 00 → 前后摇杆中位
  12B DD CC BB AA 08 00 00 00 → 左右摇杆中位
"""

import subprocess
import threading
import time
import signal
import sys


class ChassisMonitor:
    def __init__(self, can_interface='can2'):
        self.can_interface = can_interface
        self.running = True
        self.candump_process = None

        # CAN帧映射表
        self.can_actions = {
            '125': {'pattern': 'AA BB CC DD 03', 'action': '前进'},
            '126': {'pattern': 'AA BB CC DD 04', 'action': '后退'},
            '127': {'pattern': 'EE FF 11 22 05', 'action': '左转'},
            '128': {'pattern': 'EE FF 11 22 06', 'action': '右转'},
            '12A': {'pattern': 'CC DD EE FF 07', 'action': '前后摇杆中位'},
            '12B': {'pattern': 'DD CC BB AA 08', 'action': '左右摇杆中位'},
        }

        print(f"========================================")
        print(f"    底盘CAN监听器")
        print(f"========================================")
        print(f"CAN接口: {self.can_interface}")
        print(f"监听CAN ID: 125, 126, 127, 128, 12A, 12B")
        print(f"========================================")
        print(f"按 Ctrl+C 退出")
        print(f"")

    def parse_can_frame(self, line):
        """解析CAN帧"""
        try:
            # 格式: can2  125   [08]  AA BB CC DD 03 00 00 00
            parts = line.split()
            if len(parts) >= 5:
                interface = parts[0]
                can_id = parts[1]
                dlc = parts[2].strip('[]')
                data = ' '.join(parts[3:11])
                return {
                    'interface': interface,
                    'can_id': can_id,
                    'dlc': dlc,
                    'data': data
                }
            return None
        except Exception as e:
            return None

    def identify_action(self, can_frame):
        """识别动作"""
        if can_frame and can_frame['can_id'] in self.can_actions:
            action_info = self.can_actions[can_frame['can_id']]
            if can_frame['data'].startswith(action_info['pattern']):
                return action_info['action']
        return None

    def start_listening(self):
        """开始监听"""
        try:
            self.candump_process = subprocess.Popen(
                ['candump', self.can_interface],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            while self.running:
                line = self.candump_process.stdout.readline()
                if not line:
                    time.sleep(0.001)
                    continue

                line = line.strip()
                if line:
                    can_frame = self.parse_can_frame(line)
                    if can_frame:
                        action = self.identify_action(can_frame)
                        if action:
                            timestamp = time.strftime('%H:%M:%S')
                            print(f"[{timestamp}] {can_frame['can_id']} {can_frame['data']} → {action}")
                        else:
                            # 显示未识别的帧
                            # print(f"[{time.strftime('%H:%M:%S')}] {can_frame['can_id']} {can_frame['data']} → 未知")
                            pass

        except Exception as e:
            print(f"[ERROR] 监听失败: {e}")

    def stop_listening(self):
        """停止监听"""
        self.running = False
        if self.candump_process:
            try:
                self.candump_process.terminate()
                self.candump_process.wait(timeout=2)
                print("\n[INFO] CAN监听已停止")
            except Exception as e:
                print(f"[ERROR] 停止监听失败: {e}")


def main():
    monitor = ChassisMonitor()

    def signal_handler(sig, frame):
        print("\n[INFO] 收到退出信号")
        monitor.stop_listening()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    monitor.start_listening()


if __name__ == '__main__':
    main()
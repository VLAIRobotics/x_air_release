#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import can

CHASSIS_FRAMES = {
    "stop": {"id": 0x601, "data": [0x2B, 0x18, 0x23, 0x00, 0x00, 0x00, 0x00, 0x00], "right_id": 0x603, "right_data": [0x2B, 0x18, 0x33, 0x00, 0x00, 0x00, 0x00, 0x00]},
    "left": {"id": 0x601, "data": [0x2B, 0x18, 0x23, 0x00, 0xE9, 0xFF, 0xFF, 0xFF], "right_id": 0x603, "right_data": [0x2B, 0x18, 0x33, 0x00, 0xE9, 0xFF, 0xFF, 0xFF]},
    "right": {"id": 0x601, "data": [0x2B, 0x18, 0x23, 0x00, 0x18, 0x00, 0x00, 0x00], "right_id": 0x603, "right_data": [0x2B, 0x18, 0x33, 0x00, 0x18, 0x00, 0x00, 0x00]},
    "forward": {"id": 0x601, "data": [0x2B, 0x18, 0x23, 0x00, 0x17, 0x00, 0x00, 0x00], "right_id": 0x603, "right_data": [0x2B, 0x18, 0x33, 0x00, 0xE8, 0xFF, 0xFF, 0xFF]},
    "backward": {"id": 0x601, "data": [0x2B, 0x18, 0x23, 0x00, 0xE8, 0xFF, 0xFF, 0xFF], "right_id": 0x603, "right_data": [0x2B, 0x18, 0x33, 0x00, 0x18, 0x00, 0x00, 0x00]}
}

LIFT_FRAMES = {
    "lift_stop": {"id": 0x600, "data": [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]},
    "lift_up": {"id": 0x600, "data": [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x02]},
    "lift_down": {"id": 0x600, "data": [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01]}
}

SEND_INTERVAL = 0.2


class ChassisControlROS2(Node):

    def __init__(self):
        super().__init__('chassis_control_ros2')

        self.chassis_state = "stop"
        self.lift_state = "lift_stop"

        self.bus = can.interface.Bus(
            channel='can2',
            interface='socketcan'
        )
        self.get_logger().info('CAN bus can2 opened')

        self.sub = self.create_subscription(
            String,
            '/chassis/cmd',
            self.cmd_callback,
            10
        )

        self.timer = self.create_timer(
            SEND_INTERVAL,
            self.can_send_loop
        )

        self.get_logger().info('Chassis control ROS2 node started')

    def cmd_callback(self, msg: String):
        cmd = msg.data.strip().lower()
        if cmd in CHASSIS_FRAMES:
            self.chassis_state = cmd
            self.get_logger().info(f'Chassis state: {cmd}, Lift state: {self.lift_state}')
        elif cmd in LIFT_FRAMES:
            self.lift_state = cmd
            self.get_logger().info(f'Chassis state: {self.chassis_state}, Lift state: {cmd}')
        else:
            self.get_logger().warn(f'Invalid command: {cmd}')

    def can_send_loop(self):
        chassis = CHASSIS_FRAMES.get(self.chassis_state, CHASSIS_FRAMES["stop"])
        lift = LIFT_FRAMES.get(self.lift_state, LIFT_FRAMES["lift_stop"])
        try:
            msg_left = can.Message(
                arbitration_id=chassis["id"],
                data=chassis["data"],
                is_extended_id=False
            )
            msg_right = can.Message(
                arbitration_id=chassis["right_id"],
                data=chassis["right_data"],
                is_extended_id=False
            )
            msg_lift = can.Message(
                arbitration_id=lift["id"],
                data=lift["data"],
                is_extended_id=False
            )
            self.bus.send(msg_left)
            self.bus.send(msg_right)
            self.bus.send(msg_lift)
        except can.CanError:
            self.get_logger().error('CAN send failed')

    def destroy_node(self):
        self.get_logger().info('Stopping chassis and lift...')
        chassis = CHASSIS_FRAMES["stop"]
        lift = LIFT_FRAMES["lift_stop"]
        try:
            msg_left = can.Message(
                arbitration_id=chassis["id"],
                data=chassis["data"],
                is_extended_id=False
            )
            msg_right = can.Message(
                arbitration_id=chassis["right_id"],
                data=chassis["right_data"],
                is_extended_id=False
            )
            msg_lift = can.Message(
                arbitration_id=lift["id"],
                data=lift["data"],
                is_extended_id=False
            )
            self.bus.send(msg_left)
            self.bus.send(msg_right)
            self.bus.send(msg_lift)
        except can.CanError:
            pass
        self.bus.shutdown()
        super().destroy_node()


def main():
    rclpy.init()
    node = ChassisControlROS2()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
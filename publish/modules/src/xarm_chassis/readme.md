STM32 Control - CAN底盘通信与摇杆控制模块

实现以下功能：
摇杆数据发送：接收ROS话题数据，转换为CAN报文发送给硬件

底盘数据接收：从CAN总线接收底盘速度数据，并发布ROS话题
按钮通道数据：接收并发布多个通道按钮状态
上位机直接控制：通过交互式脚本直接发送CAN帧控制底盘运动状态和立柱升降

CAN 数据格式
发送报文 (ID: 0x050)（其中角速度没有发送）
| 字节 | 数据类型 | 含义 | 范围 |
|------|---------|------|------|
| 0-1 | int16_t | vx (X轴速度) | -800 ~ 800 |
| 2-3 | int16_t | vy (Y轴速度) | -800 ~ 800 |
| 4-5 | int16_t | vw (角速度)  | -800 ~ 800 |
| 6 | uint8_t | 预留 | 0 |
| 7 | uint8_t | 升降台控制 | 0/1/2 |

上下状态编码：
`0`: 无上下动作
`1`: 向下
`2`: 向上

接收报文 (ID: 0x051)
| 字节 | 数据类型 | 含义 | 说明 |
|------|---------|------|------|
| 0-1 | int16_t | vx (X轴速度) | 底盘实际速度反馈 |
| 2-3 | int16_t | vy (Y轴速度) | 底盘实际速度反馈 |
| 4-5 | int16_t | vw (角速度) | 底盘实际速度反馈 |
| 7 (bit 0) | uint8_t | ch5 | 按钮状态 (1 bit) |
| 7 (bit 1) | uint8_t | ch6 | 按钮状态 (1 bit) |
| 7 (bit 2-3) | uint8_t | ch7 | 按钮状态 (2 bits) |
| 7 (bit 4-5) | uint8_t | ch8 | 按钮状态 (2 bits) |
| 7 (bit 6) | uint8_t | ch9 | 按钮状态 (1 bit) |

---

订阅的ROS话题
| 话题名称 | 消息类型 | 说明 |
|---------|---------|------|
| /dual_xarm/joystick | Float64MultiArray | 摇杆数据 [x, y, z, button] |
| /dual_xarm/py_motor_target | Float64MultiArray | 电机目标位置 (取第3个元素作为上下值) |

话题数据格式
/dual_xarm/joystick:
data[0]: x (左右方向) ∈ [-1.0, 1.0]
data[1]: y (前后方向) ∈ [-1.0, 1.0]
data[2]: z (旋转)    ∈ [-1.0, 1.0]
data[3]: button      ∈ [0.0, 1.0]

/dual_xarm/py_motor_target:
data[2]: updown (上下控制) ∈ [-1.0, 0.0, 1.0]
         -1: 向下
          0: 无动作
          1: 向上

发布的ROS话题
| 话题名称 | 消息类型 | 说明 |
|---------|---------|------|
| /stm32/chassis_data | Float64MultiArray | 底盘速度反馈 |
| /stm32/channel_data | Float64MultiArray | 按钮通道状态 |

 话题数据格式

/stm32/chassis_data:
data[0]: vx  - X轴速度
data[1]: vy  - Y轴速度
data[2]: vw  - 角速度


/stm32/channel_data:
data[0]: ch5_state  - 第5通道按钮状态
data[1]: ch6_state  - 第6通道按钮状态
data[2]: ch7_state  - 第7通道按钮状态
data[3]: ch8_state  - 第8通道按钮状态
data[4]: ch9_state  - 第9通道按钮状态

![alt text](image.png)


##  主要参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| max_speed | 800 | 最大速度值 |
| can_id | 0x050 | 发送CAN报文ID |
| send_hz | 200.0 | CAN发送频率 (Hz) |
| channel | 'can2' | CAN总线通道 |


### 监听话题

# 监听底盘数据
ros2 topic echo /stm32/chassis_data
# 监听通道数据
ros2 topic echo /stm32/channel_data
# 监听摇杆输入
ros2 topic echo /dual_xarm/joystick


### 发送流程 (摇杆 → CAN)

```
1. 接收 /dual_xarm/joystick 话题
2. 数据验证（长度、有效性检查）
3. 接收 /dual_xarm/py_motor_target 话题（上下值）
4. 定时（200Hz）执行 can_send_loop():
   - 解析摇杆数据 (x, y)
   - 映射到速度值 (vx, vy) [-800, 800]
   - 转换上下值为状态码 (0/1/2)
   - 打包为CAN报文
   - 发送到CAN总线
5. 日志输出速度数据

### 接收流程 (CAN → ROS)

1. 单独线程执行 can_recv_loop()（后台运行）
2. 监听CAN总线（timeout=1s）
3. 接收到ID 0x051的报文
4. 解析CAN数据：
   - 提取速度值 (vx, vy, vw)
   - 提取按钮状态 (ch5-ch9)
5. 发布ROS话题：
   - /stm32/chassis_data (速度)
   - /stm32/channel_data (按钮)
6. 日志输出接收数据



##  日志输出示例

[INFO] CAN bus can2 opened
[INFO] CAN receive thread started
[INFO] Joystick → CAN node started
Joystick: x=0.50, y=-0.30, down=0 → vx=400, vy=-240, vw=0, updown=0
[DEBUG] CAN sent: vx=400, vy=-240, vw=0, updown=0
[INFO] Chassis: vx=400, vy=-240, vw=0
[INFO] Channels: ch5=0, ch6=1, ch7=2, ch8=1, ch9=0

---

上位机直接控制：chassis_control.py

### 控制架构

```
上位机 (Python脚本)
    ↓ CAN总线 (can2)
下位机 (STM32底盘控制器)
    ↓ 电机驱动
底盘运动
```

### 独立控制模型

底盘运动和立柱控制为**两个独立状态变量**，可同时控制：

```
CHASSIS_STATE (底盘): stop / left / right / forward / backward
LIFT_STATE (立柱):   lift_stop / lift_up / lift_down
```

### 运动状态与CAN帧映射

**底盘控制帧：**

| 状态 | 左轮 CAN 帧 | 右轮 CAN 帧 |
|------|------------|------------|
| 静止 | `601#2B18230000000000` | `603#2B18330000000000` |
| 左转 | `601#2B182300E9FFFFFF` | `603#2B183300E9FFFFFF` |
| 右转 | `601#2B18230018000000` | `603#2B18330018000000` |
| 前进 | `601#2B18230017000000` | `603#2B183300E8FFFFFF` |
| 后退 | `601#2B182300E8FFFFFF` | `603#2B18330018000000` |

**立柱控制帧：**

| 状态 | 立柱 CAN 帧 |
|------|------------|
| 立柱静止 | `600#0000000000000000` |
| 立柱上升 | `600#0000000000000002` |
| 立柱下降 | `600#0000000000000001` |

### 使用方法

```bash
# 运行控制脚本
python3 chassis_control.py

# 或直接执行（需赋予执行权限）
chmod +x chassis_control.py
./chassis_control.py
```

### 命令说明

| 输入 | 功能 | 说明 |
|------|------|------|
| 1 | 底盘静止 | 仅改变底盘状态 |
| 2 | 底盘左转 | 仅改变底盘状态 |
| 3 | 底盘右转 | 仅改变底盘状态 |
| 4 | 底盘前进 | 仅改变底盘状态 |
| 5 | 底盘后退 | 仅改变底盘状态 |
| 6 | 立柱上升 | 仅改变立柱状态 |
| 7 | 立柱下降 | 仅改变立柱状态 |
| 8 | 立柱静止 | 仅改变立柱状态 |
| q | 退出 | 发送停止命令 |

### 技术参数

| 参数 | 值 | 说明 |
|------|-----|------|
| CAN通道 | can2 | 发送CAN帧的总线通道 |
| 发送频率 | 5Hz | 每0.2秒发送一次 |
| 发送方式 | 三轮同时发送 | 左/右轮/立柱帧连续发送 |

### 退出行为

- 输入 `q` 或按 `Ctrl+C` 退出时，自动发送静止CAN帧，确保底盘和立柱停止运动

---

## ROS2 底盘控制 (chasis_control_ros2.py)

### 功能说明

通过 ROS2 话题订阅方式接收控制命令，转换为 CAN 帧发送给底盘控制器。支持独立控制底盘运动和立柱升降，适用于集成到 ROS2 系统中的场景。

### 控制架构

```
ROS2 话题发布者
    ↓ /chassis/cmd (String)
ROS2 Node (chassis_control_ros2)
    ↓ CAN总线 (can2)
下位机 (STM32底盘控制器)
    ↓ 电机驱动
底盘运动 + 立柱升降
```

### 独立控制模型

底盘运动和立柱控制为**两个独立状态变量**，可同时控制：

```
chassis_state: stop / left / right / forward / backward
lift_state:   lift_stop / lift_up / lift_down
```

### 订阅的 ROS2 话题

| 话题名称 | 消息类型 | 说明 |
|---------|---------|------|
| /chassis/cmd | std_msgs/String | 底盘运动命令或立柱控制命令 |

### 命令格式

**底盘控制命令：**

| 命令值 | 功能 |
|--------|------|
| stop | 底盘静止 |
| left | 底盘左转 |
| right | 底盘右转 |
| forward | 底盘前进 |
| backward | 底盘后退 |

**立柱控制命令：**

| 命令值 | 功能 |
|--------|------|
| lift_stop | 立柱静止 |
| lift_up | 立柱上升 |
| lift_down | 立柱下降 |

### 使用方法

```bash
# 运行 ROS2 节点
ros2 run package_name chasis_control_ros2

# 控制底盘（不影响立柱）
ros2 topic pub /chassis/cmd std_msgs/msg/String "data: 'stop'"
ros2 topic pub /chassis/cmd std_msgs/msg/String "data: 'left'"
ros2 topic pub /chassis/cmd std_msgs/msg/String "data: 'right'"
ros2 topic pub /chassis/cmd std_msgs/msg/String "data: 'forward'"
ros2 topic pub /chassis/cmd std_msgs/msg/String "data: 'backward'"

# 控制立柱（不影响底盘）
ros2 topic pub /chassis/cmd std_msgs/msg/String "data: 'lift_stop'"
ros2 topic pub /chassis/cmd std_msgs/msg/String "data: 'lift_up'"
ros2 topic pub /chassis/cmd std_msgs/msg/String "data: 'lift_down'"

# 组合控制示例：底盘前进的同时立柱上升
ros2 topic pub /chassis/cmd std_msgs/msg/String "data: 'forward'"
ros2 topic pub /chassis/cmd std_msgs/msg/String "data: 'lift_up'"
```

### 技术参数

| 参数 | 值 | 说明 |
|------|-----|------|
| CAN通道 | can2 | 发送CAN帧的总线通道 |
| 发送频率 | 5Hz | 每0.2秒发送一次 |
| 发送方式 | 三轮同时发送 | 左/右轮/立柱帧连续发送 |
| CAN ID | 0x601 / 0x603 / 0x600 | 左/右轮/立柱控制帧ID |

### 退出行为

- 节点关闭时自动发送静止 CAN 帧，确保底盘和立柱停止运动


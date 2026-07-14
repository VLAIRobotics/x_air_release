# CHANGELOG

所有版本的变更记录。格式参考 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)。

版本号遵循 `vMAJOR.MINOR.PATCH`，发布前在本文件顶部 `[Unreleased]` 节填写改动，发布时将其移至新版本条目。

---

## [Unreleased]

<!-- 在这里记录尚未发布的改动，发布时将本节内容移动到新版本条目 -->
---

## [v1.4.0] - 2026-07-13

### 新功能
- `xarm_ui`：数据采集页面新增相机图像显示，支持胸部相机、左腕相机、右腕相机多路预览。
- 新增 `multi_realsense` 多相机模块，支持 RealSense 相机检测、单相机启动和多相机启动配置。

### 优化
- `xarm_chassis`：优化底盘和升降柱控制，支持新固件下底盘运动与升降柱状态独立控制。
- `xarm_ui`：优化相机启动流程，新增左右腕相机序列号重复选择校验，并在相机运行时锁定配置项。
- 更新底盘控制资源包和 `xarm_teleop` 的 `aarch64` 预编译库。

### 文档
- 完善底盘控制使用文档，补充新旧固件兼容说明、直接控制模式、ROS2 控制模式和 CAN 数据格式。

---

## [v1.3.0] - 2026-07-06

### 新功能
- 新增UI控制模块 `xarm_ui`

### 优化
- `xarm_ros2`：提升控制精度，改进控制回路与参数，降低抖动并提高轨迹跟踪精度。

### 文档
- 新增ui使用文档（`06_xarm_ui使用文档.md`）

---

## [v1.2.0] - 2026-06-26

### 新功能
- `xarm_teleop`：新增 `xarm_teleop_set_home_position` 接口，支持运行时自定义遥操作初始位置
- 新增底盘控制模块 `xarm_chassis`

### 优化
- `xarm_teleop`：将 home position 调整逻辑移至 `xarm_teleop_start`，修复双臂会话初始化时序问题

### 文档
- 新增底盘使用文档（`05_xarm_chassis使用文档.md`）
- 更新 xarm_action 使用文档
---

## [v1.1.0] - 2026-06-23

### 新功能
- 预编译库新增 `aarch64` 架构支持，兼容 `x86_64` / `aarch64` 双平台


### 修复
- `xarm_description`：修正 joint2 关节下限参数（0.0 → -1.7）
- `xarm_ros2`：修复 launch 脚本中重复 source ROS 环境及 `BIN_PATH` 未定义的问题
- 修复 shell 脚本缺少可执行权限

---

## [v1.0.0] - 2026-05-14

### 新功能
- 初始发布：xarm_teleop 遥操作基础功能
- 预编译库支持 `x86_64` 架构

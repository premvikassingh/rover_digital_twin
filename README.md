# Autonomous Pick-and-Place Rover: ROS 2 Digital Twin

This repository contains the ROS 2 Humble simulation workspace for an autonomous pick-and-place rover. It serves as a digital twin for physical hardware integrating a differential-drive chassis, an OAK-D spatial camera, and a 5-DOF Waveshare RoArm-M3 manipulator running on a Jetson Orin Nano.

## System Architecture

The workspace is divided into two primary ROS 2 packages:

1. **`rover_simulation`**: Contains the physical parameters and 3D environment.
   - **URDF Model**: Custom robot description featuring the chassis, wheels, camera link, and the 5-DOF robotic arm.
   - **Gazebo Plugins**: 
     - `libgazebo_ros_diff_drive.so` for proportional wheel control.
     - `libgazebo_ros_joint_state_publisher.so` & `libgazebo_ros_joint_pose_trajectory.so` for arm kinematics and joint control.
   - Gravity is disabled on the arm links (`<gravity>false</gravity>`) to simulate the holding torque of the physical servo motors.

2. **`pick_place`**: Contains the Python-based autonomous brain.
   - **`drive_pick_controller.py`**: A closed-loop state machine node that subscribes to target coordinates and publishes hardware commands.

## State Machine Logic

The autonomous controller operates in two distinct phases based on real-time `PoseStamped` coordinate data (e.g., ArUco marker tracking):

* **Standby**: On boot, the arm is commanded to a vertical standby posture to maintain a safe center of gravity.
* **Phase 1: DRIVING (Distance > 0.25m)**: The node reads the X (forward) and Y (lateral) coordinates of the target. It applies proportional control math (`linear.x = 0.5 * x`, `angular.z = 1.0 * y`) to dynamically steer and drive the rover toward the target.
* **Phase 2: PICKING (Distance <= 0.25m)**: Once the rover is within the physical reach threshold, the node publishes a zero-velocity `Twist` command to lock the wheels. It immediately publishes a `JointTrajectory` to fold the 5-DOF arm down into the exact picking coordinates.

## Dependencies
* Ubuntu 22.04 (WSL2 / Native)
* ROS 2 Humble
* Gazebo 11
* `gazebo_ros_pkgs`

## Running the Digital Twin

**1. Launch the Gazebo Simulation**
```bash
source install/setup.bash
ros2 launch rover_simulation sim.launch.py
2. Start the Autonomous Controller

Bash
source install/setup.bash
ros2 run pick_place drive_controller
3. Trigger Target Detection (Testing)
Publish a close-range coordinate to trigger the Drive-to-Pick transition:

Bash
ros2 topic pub --once /aruco_pose geometry_msgs/msg/PoseStamped "{header: {frame_id: 'camera_link'}, pose: {position: {x: 0.2, y: 0.0, z: 0.0}}}"

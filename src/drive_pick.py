import time
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped
from std_msgs.msg import Int32, Float64
from sensor_msgs.msg import JointState

class DrivePickController(Node):
    def __init__(self):
        super().__init__('pick_place_controller')
        # 1. The Eyes: Subscribe to the physical OAK-D ArUco topic
        self.sub = self.create_subscription(PoseStamped, '/aruco_pose', self.pose_callback, 10)
        
        # 2. The Wheels: Publishers for the physical Arduino serial bridge
        self.left_pub = self.create_publisher(Int32, '/left_pwm', 10)
        self.right_pub = self.create_publisher(Int32, '/right_pwm', 10)
        
        # 3. The Arm: Publishers for the Waveshare RoArm hardware
        self.arm_pub = self.create_publisher(JointState, '/move_joint_cmd', 10)
        self.gripper_pub = self.create_publisher(Float64, '/gripper_cmd', 10)
        
        self.state = 'DRIVING'
        
        # 1-second delay before standing up to safe posture
        self.timer = self.create_timer(1.0, self.publish_standby_pose)

    def publish_standby_pose(self):
        if self.state == 'DRIVING':
            self.get_logger().info('Initializing arm to standby posture...')
            msg = JointState()
            msg.name = ['joint1_pan', 'joint2_shoulder', 'joint3_elbow', 'joint4_wrist', 'joint5_gripper']
            msg.position = [0.0, -1.04, 2.61, -1.57, 0.0] # Safe driving posture
            self.arm_pub.publish(msg)
            
            # Ensure gripper is open to start
            open_cmd = Float64()
            open_cmd.data = 1.0 # Verify your open value (usually 1.0 or 3.14)
            self.gripper_pub.publish(open_cmd)
            
            self.timer.cancel()

    def pose_callback(self, msg):
        if self.state == 'DONE':
            return
            
        x = msg.pose.position.x
        y = msg.pose.position.y

        # PHASE 1: Closed-Loop Driving
        if x > 0.25 and self.state == 'DRIVING':
            # Convert physical distance into basic PWM motor speeds (Max ~150 to keep it safe)
            base_pwm = int(min(x * 80, 150)) 
            turn_pwm = int(y * 50)
            
            left_speed = base_pwm - turn_pwm
            right_speed = base_pwm + turn_pwm
            
            # Publish to the Arduino hardware bridge
            self.left_pub.publish(Int32(data=left_speed))
            self.right_pub.publish(Int32(data=right_speed))
            
            self.get_logger().info(f'Target at {x:.2f}m. Driving: L={left_speed} R={right_speed}')
        
        # PHASE 2 & 3: Stop, Pick, and Place
        elif x <= 0.25 and self.state == 'DRIVING':
            self.get_logger().info('Target in reach! Locking wheels.')
            # Stop the motors immediately
            self.left_pub.publish(Int32(data=0))
            self.right_pub.publish(Int32(data=0))
            
            self.state = 'PICKING'
            self.execute_pick_and_place()

    def execute_pick_and_place(self):
        # NOTE: Using time.sleep() blocks the node from reading new camera frames 
        # while picking, which is exactly what we want so the rover doesn't twitch.
        
        msg = JointState()
        msg.name = ['joint1_pan', 'joint2_shoulder', 'joint3_elbow', 'joint4_wrist', 'joint5_gripper']
        
        # --- THE PICK ---
        self.get_logger().info('Reaching for object...')
        msg.position = [0.0, -0.8, 0.5, -0.5, 0.0]
        self.arm_pub.publish(msg)
        time.sleep(2.0) # Wait for physical servos to lower

        self.get_logger().info('Closing gripper...')
        grip_cmd = Float64()
        grip_cmd.data = 0.0 # Verify your closed value
        self.gripper_pub.publish(grip_cmd)
        time.sleep(1.5) # Wait for claws to secure object
        
        # --- THE PLACE (Cabin Drop) ---
        self.get_logger().info('Swinging over cabin...')
        # INSERT YOUR 5 ANGLES HERE
        msg.position = [0.0, 0.0, 0.0, 0.0, 0.0] 
        self.arm_pub.publish(msg)
        time.sleep(3.0) # Longer delay for the heavy swing backward
        
        self.get_logger().info('Releasing object...')
        grip_cmd.data = 1.0 # Verify your open value
        self.gripper_pub.publish(grip_cmd)
        time.sleep(1.0)
        
        # --- RETURN TO STANDBY ---
        self.get_logger().info('Returning to safe driving posture...')
        msg.position = [0.0, -1.04, 2.61, -1.57, 0.0]
        self.arm_pub.publish(msg)
        time.sleep(2.0)
        
        self.get_logger().info('Cycle Complete!')
        self.state = 'DONE' # Script stops here. Change to 'DRIVING' if you want it to hunt the next block!

def main(args=None):
    rclpy.init(args=args)
    node = DrivePickController()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
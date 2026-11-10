import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist, PoseStamped
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint

class DrivePickController(Node):
    def __init__(self):
        super().__init__('pick_place_controller')
        self.sub = self.create_subscription(PoseStamped, '/aruco_pose', self.pose_callback, 10)
        self.vel_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.arm_pub = self.create_publisher(JointTrajectory, '/set_joint_trajectory', 10)
        self.state = 'DRIVING'
        
        # 1-second delay before standing up
        self.timer = self.create_timer(1.0, self.publish_standby_pose)

    def publish_standby_pose(self):
        if self.state == 'DRIVING':
            traj = JointTrajectory()
            traj.joint_names = ['joint1_pan', 'joint2_shoulder', 'joint3_elbow', 'joint4_wrist', 'joint5_gripper']
            point = JointTrajectoryPoint()
            # Standby: Straight up!
            point.positions = [0.0, 0.0, 0.0, 0.0, 0.0] 
            point.time_from_start.sec = 1
            traj.points.append(point)
            self.arm_pub.publish(traj)
            self.timer.cancel()

    def pose_callback(self, msg):
        if self.state == 'DONE':
            return
            
        x = msg.pose.position.x
        y = msg.pose.position.y

        if x > 0.25 and self.state == 'DRIVING':
            twist = Twist()
            twist.linear.x = 0.5 * x
            twist.angular.z = 1.0 * y
            self.vel_pub.publish(twist)
            self.get_logger().info('Target spotted! Driving...')
        
        elif x <= 0.25 and self.state == 'DRIVING':
            self.vel_pub.publish(Twist())
            self.get_logger().info('Target in reach. Deploying arm.')
            self.state = 'PICKING'
            self.execute_pick()

    def execute_pick(self):
        traj = JointTrajectory()
        traj.joint_names = ['joint1_pan', 'joint2_shoulder', 'joint3_elbow', 'joint4_wrist', 'joint5_gripper']
        point = JointTrajectoryPoint()
        # Pick: Reaching forward over the camera
        point.positions = [0.0, -0.8, 0.5, -0.5, 0.0]
        point.time_from_start.sec = 2
        traj.points.append(point)
        self.arm_pub.publish(traj)
        self.state = 'DONE'

def main(args=None):
    rclpy.init(args=args)
    node = DrivePickController()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
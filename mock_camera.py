import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped

class MockCamera(Node):
    def __init__(self):
        super().__init__('mock_camera')
        self.pub = self.create_publisher(PoseStamped, '/aruco_pose', 10)
        self.timer = self.create_timer(0.1, self.timer_callback) # Runs at 10Hz
        self.x = 2.0
        self.y = 0.5

    def timer_callback(self):
        msg = PoseStamped()
        msg.header.frame_id = 'camera_link'
        msg.pose.position.x = self.x
        msg.pose.position.y = self.y
        msg.pose.position.z = 0.0
        self.pub.publish(msg)

        self.get_logger().info(f'Camera sees target at X: {self.x:.2f}m, Y: {self.y:.2f}m')

        # Decrease the distance simulating forward movement
        if self.x > 0.2:
            self.x -= 0.02
            self.y -= 0.0055
        else:
            self.get_logger().info('Target reached 0.2m! Shutting down mock camera.')
            self.timer.cancel()

def main(args=None):
    rclpy.init(args=args)
    node = MockCamera()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()

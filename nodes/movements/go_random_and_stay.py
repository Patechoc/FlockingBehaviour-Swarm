#!/usr/bin/env python
import rospy
from random import randrange
from swarm.msg import QuadStamped

if __name__ == '__main__':
    pub = rospy.Publisher('des_pos', QuadStamped, queue_size=1)
    rospy.init_node('go_up_and_stay', anonymous=True)
    rate = rospy.Rate(100)
    
    quad = QuadStamped();
    quad.header.frame_id = 'world'
    quad.x = 0
    quad.y = 0
    quad.z = 0
    quad.yaw = 0

    try:
        while not rospy.is_shutdown():
            quad.header.stamp = rospy.Time.now()
            if quad.header.stamp.secs >= 2:
                if quad.x == 0: quad.x = randrange(-10,11,1) / 10.0
                if quad.y == 0: quad.y = randrange(-10,11,1) / 10.0
                if quad.z == 0: quad.z = randrange(3,11,1) / 10.0
            pub.publish(quad)
            rospy.loginfo("[%f, %f, %f - %f]", quad.x, quad.y, quad.z, quad.yaw)
            rate.sleep()

    except rospy.ROSInterruptException:
        pass

    finally:
        quad.header.stamp = rospy.Time.now()
        quad.x = 0
        quad.y = 0
        quad.z = 0
        pub.publish(quad)
        rospy.loginfo("End of node")

#!/usr/bin/env python
import message_filters, rospy, sys
from math import sqrt
from geometry_msgs.msg import Vector3
from swarm.msg import QuadStamped, QuadState

def multiple_callback(*args):
    global a_pot, a_slip, pub, quad, n

    # Repulsion & alignment:
    D = 0.65
    r0_r = 1.5
    r1_r = 1.0
    
    c_frict = 0.3
    r0_a = 2.0
    r1_a = 0.8
    r2_a = 0.5
    
    dist = Vector3()
    
    for i in range(n):
        a_pot[i].x = 0.0
        a_pot[i].y = 0.0
        a_pot[i].z = 0.0

        a_slip[i].x = 0.0
        a_slip[i].y = 0.0
        a_slip[i].z = 0.0

    for i in range(n):
        for j in range(i,n):
            if not(i==j):
                dist.x = args[j].pos.x - args[i].pos.x
                dist.y = args[j].pos.y - args[i].pos.y
                dist.z = args[j].pos.z - args[i].pos.z
                d = sqrt(dist.x*dist.x + dist.y*dist.y + dist.z*dist.z)

                if d<r0_r:
                    a_pot[i].x += min(r1_r,r0_r-d)*dist.x / d
                    a_pot[i].y += min(r1_r,r0_r-d)*dist.y / d
                    a_pot[i].z += min(r1_r,r0_r-d)*dist.z / d
                    a_pot[j].x -= a_pot[i].x
                    a_pot[j].y -= a_pot[i].y
                    a_pot[j].z -= a_pot[i].z

                m = max(d-(r0_a-r2_a),r1_a)
                m = m * m
                a_slip[i].x += (args[j].vel.x - args[i].vel.x) / m
                a_slip[i].y += (args[j].vel.y - args[i].vel.y) / m
                a_slip[i].z += (args[j].vel.z - args[i].vel.z) / m
                a_slip[j].x -= a_slip[i].x
                a_slip[j].y -= a_slip[i].y
                a_slip[j].z -= a_slip[i].z
        
        a_pot[i].x *= - D
        a_pot[i].y *= - D
        a_pot[i].z *= - D
        # rospy.loginfo("i: %i, a_pot [%f, %f, %f]", i, a_pot[i].x, a_pot[i].y, a_pot[i].z)

        a_slip[i].x *= c_frict
        a_slip[i].y *= c_frict
        a_slip[i].y *= c_frict
        rospy.loginfo("i: %i, a_slip [%f, %f, %f]", i, a_slip[i].x, a_slip[i].y, a_slip[i].z)

        # Final movements:
        quad[i].x = args[i].pos.x + a_pot[i].x # + a_slip[i].x
        quad[i].y = args[i].pos.y + a_pot[i].y # + a_slip[i].y
        quad[i].z = args[i].pos.z + a_pot[i].z # + a_slip[i].z

        # Go up at 1 second:
        if (quad[i].header.stamp.secs == 1):
            quad[i].z = 1.0;
            
        # rospy.loginfo("i: %i, quad [%f, %f, %f]", i, quad[i].x, quad[i].y, quad[i].z)

    # Publish:
    try:
        for i in range(n):
            quad[i].header.stamp = rospy.Time.now()
            pub[i].publish(quad[i])
    except rospy.ROSException:
        pass

if __name__ == '__main__':
    rospy.init_node('reynolds', anonymous=True)
    argv = sys.argv
    rospy.myargv(argv)
    n = int(argv[1])

    sub = []
    pub = []
    quad = []
    a_pot = []
    a_slip = []
    for i in range(n):
        sub.append(message_filters.Subscriber('/uav' + str(i) + '/next_generation', QuadState))
        pub.append(rospy.Publisher('/uav' + str(i) + '/des_pos', QuadStamped, queue_size=n*10))
        quad.append(QuadStamped())
        quad[i].header.frame_id = 'world'
        xy = rospy.get_param('/uav' + str(i))
        quad[i].x = xy['x']; quad[i].y = xy['y']; quad[i].z = 0.0; quad[i].yaw = 0.0
        a_pot.append(Vector3())
        a_slip.append(Vector3())

    ts = message_filters.ApproximateTimeSynchronizer(sub, n*10, 0.015)

    try:
        ts.registerCallback(multiple_callback)
        rospy.loginfo("Start spinning")
        rospy.spin()

    except rospy.ROSInterruptException:
        pass

    finally:
        for i in range(n):
            quad[i].header.stamp = rospy.Time.now()
            xy = rospy.get_param('/uav' + str(i))
            quad[i].x = xy['x']; quad[i].y = xy['y']; quad[i].z = 0.0; quad[i].yaw = 0.0
            pub[i].publish(quad[i])
        rospy.loginfo("End of node")

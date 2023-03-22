#!/usr/bin/env python

import rospy 
from sensor_msgs.msg import Image 
from std_msgs.msg import Int8, Header
from geometry_msgs.msg import PointStamped, Point, PoseStamped, Pose
from nav_msgs.msg import Odometry
from cv_bridge import CvBridge # Package to convert between ROS and OpenCV Images
import cv2 
import numpy as np
 
# initialize the HOG descriptor/person detector
hog = cv2.HOGDescriptor()
hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
pub_poi = rospy.Publisher('/poi', PoseStamped, queue_size=10)
bridge = CvBridge()
global current_pose, poi_pose
current_pose = Pose()
poi_list = []

class Waypoint:
    def __init__(self, x = 0, y = 0, z = 0):
        self.x = x
        self.y = y
        self.z = z
        self.pt = Point(x,y,z)
    def ps(self):
        return PointStamped(header=Header(stamp=rospy.Time.now(),frame_id='map'), point=self.pt)

def callback(data):
    global poi_pose
    rawraw = bridge.imgmsg_to_cv2(data, desired_encoding='passthrough')
    raw = cv2.resize(cv2.cvtColor(rawraw, cv2.COLOR_BGR2RGB), (0,0), fx=2,fy=2)
    #raw = cv2.imread('/home/tim/keith/man_standing.jpg')
    gray = cv2.cvtColor(raw, cv2.COLOR_BGR2GRAY)

    # detect people in the image
    boxes, weights = hog.detectMultiScale(gray, padding=(8, 8), winStride=(8,8))
    for (x, y, w, h) in boxes:
        # display the detected boxes in the colour picture
        cv2.rectangle(raw, (x, y), (x+w, y+h), (0, 255, 0), 2)
        #rospy.loginfo(h)
        d = -1.21*np.log(0.00138*h-0.159)
        #rospy.loginfo(d)
        if compare_pose(2):
            pub_poi.publish(PoseStamped(header=Header(stamp=rospy.Time.now(),frame_id='human'), pose=current_pose))
            poi_pose = current_pose
            poi_list.append(poi_pose)
            rospy.loginfo('man') 
    #rospy.loginfo('spotted ' + str(len(boxes)))
    
    #find doors
    (T, thresh) = cv2.threshold(gray, 5, 255, cv2.THRESH_BINARY_INV)
    cnts = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for c in cnts[0]:
        cv2.drawContours(raw, [c], -1, (0, 255, 0), 3)
        if compare_pose(2):
            pub_poi.publish(PoseStamped(header=Header(stamp=rospy.Time.now(),frame_id='door'), pose=current_pose))
            poi_list.append(current_pose)
            rospy.loginfo('door')

    cv2.imshow("hunter", raw)
    
    cv2.waitKey(1)

def compare_pose(r):
    global current_pose
    for po in poi_list:
        dx = current_pose.position.x - po.position.x
        dy = current_pose.position.y - po.position.y
        if abs(dx) < r or abs(dy) < r:
            #rospy.loginfo(len(poi_list))
            return False
    return True

def get_pos(data):
    global current_pose 
    current_pose = data.pose.pose
    #rospy.loginfo(current_pose)

def get_dist(a, b):
    return np.sqrt((a.x-b.x)**2 + (a.y-b.y)**2)
  
if __name__ == '__main__':

    rospy.init_node('hunter')
    engage = False
    rospy.sleep(2)

    rospy.Subscriber('/camera/image', Image, callback)
    rospy.Subscriber('/state_estimation', Odometry, get_pos)
    rospy.spin()
    
    cv2.destroyAllWindows()
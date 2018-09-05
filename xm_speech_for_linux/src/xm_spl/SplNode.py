#!/usr/bin/env python3
import rospy
import pyserial
from xm_msgs.srv import *

class SplNode():
    def __init__(self):
        rospy.init_node("xmSplNode")
        rospy.on_shutdown(self.shutdown)
        self.ser = pyserial.ComThread()
        self.count =0
        if self.ser.start() is True:
            print ("open serialport successfully")
        self.server = rospy.Service("xm_spl",xm_Spl,self.response) 
        rospy.spin()

    def response(self,req):
        res = xm_SplResponse()
        if req.wish is False:
            print ("hehe")
            return res
        else:
            while True:
                self.count +=1
                result = self.ser.analysisMessage()
                rospy.sleep(0.2)
                if result is not None or self.count >100:
                    self.count =0
                    break
            if result is None:
                print ("timeout")
                return res
            else:
                print ("get the angle of speaker^_^")
                try:
                    res.angle = result['content']['info']['angle']
                except:
                    rospy.logwarn("the network is broken")
                    return res
                return res
    def shutdown(self):
        rospy.loginfo("i will stop spl function")
        self.ser.stop()

if __name__ =="__main__":
    SplNode()

    
            
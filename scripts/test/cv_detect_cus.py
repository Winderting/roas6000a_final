import os
# Import ROS libraries and messages
import rospy
from sensor_msgs.msg import Image

# Import OpenCV libraries and tools
import cv2
from cv_bridge import CvBridge, CvBridgeError
import numpy as np


def hog(img, bin_n=16):
    gx = cv2.Sobel(img, cv2.CV_32F, 1, 0)
    gy = cv2.Sobel(img, cv2.CV_32F, 0, 1)
    mag, ang = cv2.cartToPolar(gx, gy)
    bins = np.int32(bin_n*ang/(2*np.pi))    # quantizing binvalues in (0...16)
    bin_cells = bins[:10,:10], bins[10:,:10], bins[:10,10:], bins[10:,10:]
    mag_cells = mag[:10,:10], mag[10:,:10], mag[:10,10:], mag[10:,10:]
    hists = [np.bincount(b.ravel(), m.ravel(), bin_n) for b, m in zip(bin_cells, mag_cells)]
    hist = np.hstack(hists)     # hist is a 64 bit vector
    return hist


# Define a function to show the image in an OpenCV Window
def show_image(img):
    cv2.imshow('Image Window', img)
    cv2.waitKey(1)

# Define a callback for the Image message
def image_callback(img_msg):
    # log some info about the image topic
    rospy.loginfo(img_msg.header)

    # Try to convert the ROS Image message to a CV2 Image
    try:
        cv_image = bridge.imgmsg_to_cv2(img_msg, 'passthrough')
    except CvBridgeError, e:
        rospy.logerr("CvBridge Error: {0}".format(e))

    # Flip the image 90deg
    # cv_image = cv2.transpose(cv_image)
    cv_image = cv2.flip(cv_image,1)

    # Detection using general harr
    # no recognition
    det_img = face_detection_harr(cv_image)
    #  image color
    det_img = cv2.cvtColor(det_img, cv2.COLOR_BGR2RGB)
    # Show the detected image
    show_image(det_img)


# face detection
def face_detection_harr(img):
    classes_dir = "../label/classes.txt"
    f = open(classes_dir,"r")
    classes = f.readlines()
    classes = [x.strip() for x in classes]

    face_cascade = cv2.CascadeClassifier('../haarcascade_frontalface_default.xml')
    # Read the input image
    img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(img_gray, 1.1, 4)
    
    font = cv2.FONT_HERSHEY_SIMPLEX 
    if len(faces)!=0:
        rospy.loginfo('face found')
        # temporarily, then use NMS
        faces = [faces[0]]

    # LBPHFaceRecognizer
    face_recognizer = cv2.face.createLBPHFaceRecognizer()
    face_recognizer.load('../face_recognizer_file.xml')

    # SVM
    # svm = cv2.ml.SVM_load("../recognizer_file.dat")

    # similar to NMS

    # Draw rectangle around the faces

    for (x, y, w, h) in faces:
        cv2.rectangle(img, (x, y), (x+w, y+h), (255, 0, 0), 2)
        Id, conf = face_recognizer.predict(img_gray[x:x+w,y:y+h])
        
        # feature = hog(img_gray[x:x+w,y:y+h])
        # feature = np.array(feature).astype('float32')
        # feature = np.reshape(np.array(feature),(1,-1))
        # _, Id = svm.predict(feature)
        img = cv2.putText(img, 'face detected', (img.shape[0]-120,10), font, 0.5, (255, 0, 0), 2)
        img = cv2.putText(img, "%s"%classes[int(Id)], (x,y-5), font, 0.5, (255, 0, 0), 2)

    
    return img
    # Display the output
    # cv2.imshow('img', img)
    # cv2.waitKey()



if __name__ =='__main__':
    # Initialize the ROS Node named 'camera_opencv', allow multiple nodes to be run with this name
    rospy.init_node('camera_opencv', anonymous=True)
    # Print "Hello ROS!" to the Terminal and to a ROS Log file located in ~/.ros/log/loghash/*.log
    rospy.loginfo('Hello ROS!')

    # Initialize the CvBridge class
    bridge = CvBridge()
    # Initalize a subscriber to the "/camera/rgb/image_raw" topic with the function "image_callback" as a callback
    sub_image = rospy.Subscriber('/vrep/image', Image, image_callback)

    # Initialize an OpenCV Window named "Image Window"
    cv2.namedWindow('Image Window', 1)

    # Loop to keep the program from shutting down unless ROS is shut down, or CTRL+C is pressed
    while not rospy.is_shutdown():
        rospy.spin()
import cv2
import mediapipe as mp
import time
import sys
from bisect import *
from config import *
import numpy as np
from collections import deque
from keras.models import load_model
import pandas as pd
import matplotlib.pyplot as plt
from Feature_extractor import Rubine_feature_extractor
import pickle
import math

class MultiStroke_HandTracking(object):
    """
    Class for utility functions required for MultiStroke HandTracking.
    """
    def __init__(self):
        pass

    def check_end_stroke(self, x, y):
        """Checks for the end of the stroke - 
        index and middle fingers are present at distance <60pixels and within an angle between -0.1 to 0.4 degrees.

        Args:
            x (List): x-coordinates of all the hand landmarks
            y (List): y-coordinates of all the hand landmarks

        Returns:
            bool: if the index and middle fingers are present in mentioned orientations, then True else False
        """
        # print("Checking if stroke ended...")
        try:
            dist = math.sqrt((x[8]-x[12])**2 + (y[8]-y[12])**2)
            slope1 = (y[12]-y[9])/(x[12]-x[9])
            slope2 = (y[8]-y[5])/(x[8]-x[5])
            theta = math.atan2(slope1 - slope2, 1+slope1*slope2)
            print(dist, theta)
            if dist <= stroke_end_dist_threshold and stroke_end_slope_min_threshold <= theta <= stroke_end_slope_max_threshold:
                return True
        except:
            pass

        return False

    def erase_check(self, x, y):
        """
        Check if palm is open or not
        :param x: List[int] List of x-coordinates of 20 palm Landmarks
        :param y: List[int] List of y-coordinates of 20 palm Landmarks
        :return bool: True if palm is open otherwise False
        """
        flag = True
        """
        Index Finger
        """
        xx = np.array([x[6] - x[5], x[8] - x[5]])
        yy = np.array([y[6] - y[5], y[8] - y[5]])
        arr = np.arctan2(xx, yy)

        if (abs(arr[1] - arr[0]) > 0.17):
            return False

        """
        Middle Finger
        """
        xx = np.array([x[10] - x[9], x[12] - x[9]])
        yy = np.array([y[10] - y[9], y[12] - y[9]])
        arr = np.arctan2(xx, yy)

        if (abs(arr[1] - arr[0]) > 0.17):
            return False

        """
        Ring Finger
        """
        xx = np.array([x[14] - x[13], x[16] - x[13]])
        yy = np.array([y[14] - y[13], y[16] - y[13]])
        arr = np.arctan2(xx, yy)

        if (abs(arr[1] - arr[0]) > 0.21):
            return False

        """
        Little Finger
        """
        xx = np.array([x[18] - x[17], x[20] - x[17]])
        yy = np.array([y[18] - y[17],  y[20] - y[17]])
        arr = np.arctan2(xx, yy)

        if (abs(arr[1] - arr[0]) > 0.17 ):
            return False

        """
        Thumb
        """
        xx = np.array([x[4] - x[3],  x[2] - x[1]])
        yy = np.array([y[4] - y[3],  y[2] - y[1]])
        arr = np.arctan2(xx, yy)
        if (abs(arr[1] - arr[0]) > 0.21):
            return False
        print("returning TRUEEEEEEEEEE")
        return True

    # def erase_check(self, x,y):
    #     """
    #     Check if palm is open or not

    #     :param x: List[int] List of x-coordinates of 20 palm Landmarks
    #     :param y: List[int] List of y-coordinates of 20 palm Landmarks
    #     :return bool: True if palm is open otherwise False
    #     """
    #     flag = True
    #     """
    #     Index Finger
    #     """
    #     xx   = np.array([x[6]-x[5],x[7]-x[5],x[8]-x[5]])
    #     yy   = np.array([y[6]-y[5],y[7]-y[5],y[8]-y[5]])
    #     arr  = np.arctan2(xx,yy)

    #     if(abs(arr[1]-arr[0]) > 0.17 or abs(arr[2]-arr[0]) > 0.17):
    #         return False

    #     """
    #     Middle Finger
    #     """
    #     xx  = np.array([x[10] - x[9], x[11] - x[9], x[12] - x[9]])
    #     yy  = np.array([y[10] - y[9], y[11] - y[9], y[12] - y[9]])
    #     arr = np.arctan2(xx, yy)

    #     if (abs(arr[1] - arr[0]) > 0.17 or abs(arr[2] - arr[0]) > 0.17):
    #         return False

    #     """
    #     Ring Finger
    #     """
    #     xx = np.array([x[14] - x[13], x[15] - x[13], x[16] - x[13]])
    #     yy = np.array([y[14] - y[13], y[15] - y[13], y[16] - y[13]])
    #     arr = np.arctan2(xx, yy)

    #     if (abs(arr[1] - arr[0]) > 0.21 or abs(arr[2] - arr[0]) > 0.21):
    #         return False

    #     """
    #     Little Finger
    #     """
    #     xx = np.array([x[18] - x[17], x[19] - x[17], x[20] - x[17]])
    #     yy = np.array([y[18] - y[17], y[19] - y[17], y[20] - y[17]])
    #     arr = np.arctan2(xx, yy)

    #     if (abs(arr[1] - arr[0]) > 0.17 or abs(arr[2] - arr[0]) > 0.17):
    #         return False

    #     """
    #     Thumb
    #     """
    #     xx = np.array([x[4] - x[3], x[3] - x[2], x[2] - x[1]])
    #     yy = np.array([y[4] - y[3], y[3] - y[2], y[2] - y[1]])
    #     arr = np.arctan2(xx, yy)
    #     if (abs(arr[2] - arr[0]) > 0.21):
    #         return False

    #     return True

    def draw_points(self, index_points):
        """
        Draw points on the image plane using the index_points as coordinates.

        :param List[List[int]] index_points: coordinates for drawing
        :return None
        """
        for index, item in enumerate(index_points):
            if index == len(index_points) -1:
                break
            cv2.line(img, item, index_points[index + 1], [255, 0, 0], 2)

    def createStrokes(self, index_points, cx, cy, ct):
        """
        1. Checks for the first time only after 15 index points are captured (Approx for a sec) and then for every input
        2. Tries to find the time which was almost 1 sec (kept at 0.9 sec) prior to the current time
        3. If such a time is found, then finds the average of all the x and y coordinates during
        the last second and checks if the hand was actually stationary (checks if the distance in either x or y
        direction is less than 2.0 pixels).
        4. If the hand has not moved in the last second, then a new stroke is created

        :param List[List[int]] index_points: Coordinate points captured
        :param int cx : current x-coordinate
        :param int cy : current y-coordinate
        :param int ct : current timestamp

        :return bool : True if new stroke to be created else False
        """
        if len(index_points) > init_index_points_count:
            lb = bisect_left(timestamps, ct-1, lo = max(0,len(timestamps)-init_index_points_count), hi = len(timestamps))
            if len(index_points[lb:]) != 0:
                if ct - timestamps[lb] >= new_stroke_time_threshold:
                    avg_x = 0
                    avg_y = 0
                    for index_point in index_points[lb:]:
                        avg_x += index_point[0]
                        avg_y += index_point[1]
                    avg_x /= len(index_points[lb:])
                    avg_y /= len(index_points[lb:])
                    # print(avg_x, avg_y)

                    if abs(avg_x - cx) < index_points_change_threshold or abs(avg_y - cy) < index_points_change_threshold:
                        """
                        Create new stroke                       
                        """
                        return True
        return False

    def classify(self, df, path="models/RandomForest.sav"):
        model = pickle.load(open(path, 'rb'))
        pred  = model.predict(df)

        return pred

if __name__ == '__main__':
    cap  = cv2.VideoCapture(0)
    msht = MultiStroke_HandTracking()

    mpHands = mp.solutions.hands
    hands   = mpHands.Hands(max_num_hands = 1)
    mpDraw  = mp.solutions.drawing_utils

    pTime = 0
    cTime = 0

    init_time = time.time()

    index_points = []
    timestamps   = []
    strokes      = dict()

    stroke_count   = 0
    hand_init_flag = False

    hand_init_time = float()

    draw_flag = True

    final_pred = ''
    pred_flag = False

    erase_flag = False

    cnn_model = load_model('models/emnist_cnn_model.h5')
    letters = {1: 'a', 2: 'b', 3: 'c', 4: 'd', 5: 'e', 6: 'f', 7: 'g', 8: 'h', 9: 'i', 10: 'j',
                11: 'k', 12: 'l', 13: 'm', 14: 'n', 15: 'o', 16: 'p', 17: 'q', 18: 'r', 19: 's', 20: 't',
                21: 'u', 22: 'v', 23: 'w', 24: 'x', 25: 'y', 26: 'z', 27: '-'}
    while True:
        index_points = []
        timestamps   = []
        strokes      = dict()

        stroke_count   = 0
        hand_init_flag = False

        hand_init_time = float()

        draw_flag = True

        final_pred = ''
        pred_flag = False

        erase_flag = False

        count = 0
        queue = deque([])

        end_stroke_cnt = 0
        end_stroke_queue = deque([])

        while True:

            success, img = cap.read()
            img = cv2.flip(img, 1)

            imgRGB  = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            h, w, c = img.shape
            # print("Dimensions !! {} {} {}".format(h, w, c))

            results = hands.process(imgRGB)

            if results.multi_hand_landmarks:

                if hand_init_flag == False:
                    hand_init_time = time.time()
                    hand_init_flag = True

                x = [0] * 21
                y = [0] * 21
                enter = False
                end_stroke_enter = False

                for handLms in results.multi_hand_landmarks:
                    for i, lm in enumerate(handLms.landmark):
                        enter  = True
                        end_stroke_enter = True

                        cx, cy = int(lm.x * w), int(lm.y * h)
                        x[i]   = cx
                        y[i]   = cy

                        if i == 8:
                            ct = time.time()-hand_init_time
                            print(cx, cy, ct)

                            if ct >= hand_init_time_threshold:
                                index_points.append((cx, cy))
                                timestamps.append(ct)

                                if msht.createStrokes(index_points, cx, cy, ct) and stroke_count == 0:
                                    stroke_count += 1
                                    print("stroke_count:", stroke_count)
                                    strokes[stroke_count] = []
                                
                                if stroke_count > 0 and draw_flag:
                                    strokes[stroke_count].append((cx, cy))
                                    # print(strokes)
                                    # print("-"*20)
                    for stroke in strokes:
                        msht.draw_points(strokes[stroke])
                                
                    mpDraw.draw_landmarks(img, handLms, mpHands.HAND_CONNECTIONS)
                # print("index_points:", index_points)
                # print("strokes:", strokes, len(strokes))

                if len(queue) == 20:
                    if queue[0] == True:
                        count = count-1
                    queue.popleft()

                if enter == True and msht.erase_check(x,y) == True:
                    queue.append(True)
                    count = count+1
                else:
                    queue.append(False)
                if count >= 16:
                    index_points = []
                    strokes = dict()
                    stroke_count = 0
                    # strokes[0] = []
                    erase_flag = True
                    print("BREAKING")
                    break

                if len(end_stroke_queue) == 10 and erase_flag == False:
                    if end_stroke_queue[0] == True:
                        end_stroke_cnt = end_stroke_cnt-1
                    end_stroke_queue.popleft()

                if end_stroke_enter == True and msht.check_end_stroke(x,y) == True and erase_flag == False:
                    end_stroke_queue.append(True)
                    end_stroke_cnt = end_stroke_cnt+1
                else:
                    draw_flag = True
                    end_stroke_queue.append(False)
                    for key in strokes:
                        msht.draw_points(strokes[key])
                    

                if end_stroke_cnt >= 8 and erase_flag == False:
                    draw_flag = False
                    stroke_count += 1
                    strokes[stroke_count] = []
                    print("Stroke ended!!!")
                    sketch_points = []
                    for key in strokes:
                        sketch_points.extend(strokes[key])
                        msht.draw_points(strokes[key])
                    """
                    Rubine feature extraction from x, y coordinates:
                    """
                    if len(sketch_points)>10:
                        df = pd.DataFrame(columns=["x", "y"])

                        df["x"], df["y"] = zip(*sketch_points)
                        feature_extractor = Rubine_feature_extractor(df)
                        feature_df = feature_extractor.all_features(df)
                        # print(feature_df)
                        final_df = pd.DataFrame([feature_df])
                        pred = msht.classify(final_df.fillna(0))
                        final_pred = pred
                        cv2.putText(img, str(pred), (50, 400), cv2.FONT_HERSHEY_COMPLEX, 3,
                                    (255, 0, 255))
                        pred_flag = True
                        print(pred)
                        # msht.draw_points(index_points)
                        # image = np.zeros((480, 640))
                        # # image = np.zeros((720, 1280))
                        # # image[index_points[:,0], index_points[:,1]] = 1
                        # image[list(zip(*index_points))[0], list(zip(*index_points))[1]] = 1
                        # newImage = cv2.resize(image, (28, 28))
                        # newImage = np.array(newImage)
                        # newImage = newImage.astype('float32')/255

                        # # prediction1 = mlp_model.predict(newImage.reshape(1,28,28))[0]
                        # # prediction1 = np.argmax(prediction1)

                        # prediction2 = cnn_model.predict(newImage.reshape(1,28,28,1))[0]
                        # prediction2 = np.argmax(prediction2)
                        # final_pred = str(letters[int(prediction2) + 1])
                        # pred_flag = True
                        # cv2.putText(img, "Convolution Neural Network:  " + final_pred, (50, 400),
                        #             cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                        # print(letters[int(prediction2) + 1])
                        # break

            else:
                if len(strokes) != 0:
                    print("Hand is out of drawing area!!!") 
                for stroke in strokes:           
                    msht.draw_points(strokes[stroke])
                pred_flag = False

            cTime = time.time()
            fps   = 1 / (cTime-pTime)
            pTime = cTime
            cv2.putText(img, str(int(fps)), (10, 70), cv2.FONT_HERSHEY_COMPLEX, 3, (255, 0, 255))
            if pred_flag == False:
                cv2.putText(img, str(final_pred), (50, 400), cv2.FONT_HERSHEY_COMPLEX, 3,
                                    (255, 0, 255))

            # print(i, img)
            cv2.imshow("Image", img)
            cv2.waitKey(1)

    print("count is ",count)
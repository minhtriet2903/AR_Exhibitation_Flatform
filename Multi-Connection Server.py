#!/usr/bin/env python3
import socket
import selectors
import types
import cv2
import numpy as np
import math
import matplotlib.pyplot as plt
from objloader_simple import *
from PIL import Image
from matplotlib import cm
import time
import glob


# HOST = '127.0.0.1'  # Standard loopback interface address (localhost)
HOST = '192.168.1.6'  # Standard loopback interface address (localhost)
PORT = 8080  # Port to listen on (non-privileged ports are > 1023)


def compare_image(original):
    orb = cv2.ORB_create()
    # Find keypoints and descriptors with ORB
    keypoints1, descriptors1 = orb.detectAndCompute(original, None)

    # Load all the images
    all_images_to_compare = []
    titles = []
    res_image = ""
    max_similarity = 0
    for f in glob.iglob("images\*"):
        image = cv2.imread(f)
        titles.append(f)
        all_images_to_compare.append(image)
    for image_to_compare, title in zip(all_images_to_compare, titles):
        # 1) Check if 2 images are equals
        if original.shape == image_to_compare.shape:
            print("The images have same size and channels")
            difference = cv2.subtract(original, image_to_compare)
            b, g, r = cv2.split(difference)

            if cv2.countNonZero(b) == 0 and cv2.countNonZero(g) == 0 and cv2.countNonZero(r) == 0:
                print("Similarity: 100% (equal size and channels)")
                break

        # 2) Check for similarities between the 2 images
        keypoints2, descriptors2 = orb.detectAndCompute(image_to_compare, None)
        # Create a BFMatcher object.
        # It will find all of the matching keypoints on two images
        bf = cv2.BFMatcher_create(cv2.NORM_HAMMING, crossCheck=True)
        matches = bf.match(descriptors1, descriptors2)

        good_points = []
        for m in matches:
            if m.distance > 0.7:
                good_points.append(m)

        number_keypoints = 0
        if len(keypoints1) >= len(keypoints2):
            number_keypoints = len(keypoints1)
        else:
            number_keypoints = len(keypoints2)

        # print("Title: " + title)
        percentage_similarity = len(good_points) / number_keypoints * 100
        # print("Similarity: " + str(int(percentage_similarity)) + "\n")
        if percentage_similarity > max_similarity:
            max_similarity = percentage_similarity
            res_image = title

    print("res_image: " + res_image)
    print("max_similarity: " + str(int(max_similarity)))

    slpit_res_image = res_image.split("\\");
    title_index = slpit_res_image.__len__() - 1;
    image_name = slpit_res_image[1].split(".")
    print(image_name[0])
    return image_name[0]


sel = selectors.DefaultSelector()


def projection_matrix(camera_parameters, homography):
    homography = homography * (-1)
    rot_and_transl = np.dot(np.linalg.inv(camera_parameters), homography)
    col_1 = rot_and_transl[:, 0]
    col_2 = rot_and_transl[:, 1]
    col_3 = rot_and_transl[:, 2]

    # normalise vectors
    l = math.sqrt(np.linalg.norm(col_1, 2) * np.linalg.norm(col_2, 2))
    rot_1 = col_1 / l
    rot_2 = col_2 / l
    translation = col_3 / l

    # compute the orthonormal basis
    c = rot_1 + rot_2
    p = np.cross(rot_1, rot_2)
    d = np.cross(c, p)
    rot_1 = np.dot(c / np.linalg.norm(c, 2) + d / np.linalg.norm(d, 2), 1 / math.sqrt(2))
    rot_2 = np.dot(c / np.linalg.norm(c, 2) - d / np.linalg.norm(d, 2), 1 / math.sqrt(2))
    rot_3 = np.cross(rot_1, rot_2)

    # finally, compute the 3D projection matrix from the model to the current frame
    projection = np.stack((rot_1, rot_2, rot_3, translation)).T

    return np.dot(camera_parameters, projection)


# project cube or model
def render(img, obj, projection, model, color=False):

    vertices = obj.vertices
    scale_matrix = np.eye(3) * 6
    h, w = model.shape

    for face in obj.faces:
        face_vertices = face[0]
        points = np.array([vertices[vertex - 1] for vertex in face_vertices])
        points = np.dot(points, scale_matrix)
        # render model in the middle of the reference surface. To do so,
        # model points must be displaced
        points = np.array([[p[0] + w / 2, p[1] + h / 2, p[2]] for p in points])
        dst = cv2.perspectiveTransform(points.reshape(-1, 1, 3), projection)
        imgpts = np.int32(dst)

        cv2.fillConvexPoly(img, imgpts, (80, 27, 211))
    return img


def accept_wrapper(sock):
    conn, addr = sock.accept()  # Should be ready to read
    print("accepted connection from", addr)
    conn.setblocking(False)
    data = types.SimpleNamespace(addr=addr, inb=b"", outb=b"")

    events = selectors.EVENT_READ | selectors.EVENT_WRITE
    sel.register(conn, events, data=data)

def service_connection(key, mask):
    sock = key.fileobj
    data = key.data
    if mask & selectors.EVENT_READ:
        recv_data = sock.recv(1024)  # Should be ready to read
        if recv_data:
            data.outb += recv_data
        else:
            print('closing connection to', data.addr)
            sel.unregister(sock)
            sock.close()
    if mask & selectors.EVENT_WRITE:
        if data.outb:
            image_size = int.from_bytes(data.outb[1:4], "big")
            print(image_size)
            # print('echoing', repr(data.outb), 'to', data.addr)
            if image_size > 0 and len(data.outb[4:]) == image_size:
                input_data = data.outb[4:]
                flag = 0

                # Load reference image and convert it to gray scale
                referenceImage = cv2.imread('./img/referenceImage.jpg', 0)

                # Initiate ORB detector
                orb = cv2.ORB_create()

                res = np.frombuffer(input_data, dtype=np.uint8)
                sourceImage = cv2.imdecode(res, 0)
                model_name = compare_image(sourceImage)
                referenceImage = cv2.imread('./images/'+model_name+'.jpg', 0)
                # print(referenceImage)
                # print("src image ",sourceImage)
                # find the keypoints with ORB
                referenceImagePts = orb.detect(referenceImage, None)
                sourceImagePts = orb.detect(sourceImage, None)

                # compute the descriptors with ORB
                referenceImagePts, referenceImageDsc = orb.compute(referenceImage, referenceImagePts)
                sourceImagePts, sourceImageDsc = orb.compute(sourceImage, sourceImagePts)

                #  Paint the key points over the original image
                referenceImageFeatures = cv2.drawKeypoints(referenceImage, referenceImagePts,
                                                           referenceImage, color=(0, 255, 0), flags=0)
                sourceImageFeatures = cv2.drawKeypoints(sourceImage, sourceImagePts,
                                                        sourceImage, color=(0, 255, 0), flags=0)

                MIN_MATCHES = 30

                # create brute force  matcher object
                bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)

                # Compute model keypoints and its descriptors
                referenceImagePts, referenceImageDsc = orb.detectAndCompute(referenceImage, None)

                # Compute scene keypoints and its descriptors
                sourceImagePts, sourceImageDsc = orb.detectAndCompute(sourceImage, None)

                # Match frame descriptors with model descriptors
                matches = bf.match(referenceImageDsc, sourceImageDsc)

                # Sort them in the order of their distance
                matches = sorted(matches, key=lambda x: x.distance)

                # Apply the homography transformation if we have enough good matches
                if len(matches) > MIN_MATCHES:
                    # Get the good key points positions
                    sourcePoints = np.float32([referenceImagePts[m.queryIdx].pt for m in matches]).reshape(-1, 1, 2)
                    destinationPoints = np.float32([sourceImagePts[m.trainIdx].pt for m in matches]).reshape(-1, 1, 2)

                    # Obtain the homography matrix
                    homography, mask = cv2.findHomography(sourcePoints, destinationPoints, cv2.RANSAC, 5.0)
                    matchesMask = mask.ravel().tolist()

                    # Apply the perspective transformation to the source image corners
                    h, w = referenceImage.shape
                    corners = np.float32([[0, 0], [0, h - 1], [w - 1, h - 1], [w - 1, 0]]).reshape(-1, 1, 2)
                    transformedCorners = cv2.perspectiveTransform(corners, homography)

                    # Draw a polygon on the second image joining the transformed corners
                    sourceImageMarker = cv2.polylines(sourceImage, [np.int32(transformedCorners)], True,
                                                      255, 5, cv2.LINE_AA)

                else:
                    print("Not enough matches are found - %d/%d" % (len(matches), MIN_MATCHES))
                    matchesMask = None

                # Draw the matches
                drawParameters = dict(matchColor=(0, 255, 0), singlePointColor=None,
                                      matchesMask=matchesMask, flags=2)
                result = cv2.drawMatches(referenceImage, referenceImagePts, sourceImageMarker,
                                         sourceImagePts, matches, None, **drawParameters)

                # Camera parameters
                camera_parameters = np.array([[1000, 0, 320], [0, 1000, 240], [0, 0, 1]])

                # Load 3D model from OBJ file
                obj = OBJ('models/' + model_name + '.obj', swapyz=True)

                # Apply the homography transformation if we have enough good matches
                if len(matches) > MIN_MATCHES:
                    # Get the good key points positions
                    sourcePoints = np.float32([referenceImagePts[m.queryIdx].pt for m in matches]).reshape(-1, 1, 2)
                    destinationPoints = np.float32([sourceImagePts[m.trainIdx].pt for m in matches]).reshape(-1, 1, 2)

                    # Obtain the homography matrix
                    homography, _ = cv2.findHomography(sourcePoints, destinationPoints, cv2.RANSAC, 5.0)
                    matchesMask = mask.ravel().tolist()

                    # Apply the perspective transformation to the source image corners
                    h, w = referenceImage.shape
                    corners = np.float32([[0, 0], [0, h - 1], [w - 1, h - 1], [w - 1, 0]]).reshape(-1, 1, 2)
                    transformedCorners = cv2.perspectiveTransform(corners, homography)

                    # Draw a polygon on the second image joining the transformed corners
                    frame = cv2.polylines(sourceImage, [np.int32(transformedCorners)], True, 255, 3, cv2.LINE_AA)

                    # obtain 3D projection matrix from homography matrix and camera parameters
                    projection = projection_matrix(camera_parameters, homography)

                    # project cube or model
                    frame = render(frame, obj, projection, referenceImage, False)

                # print("frame", frame)
                flag = 1
                img_encoded = cv2.imencode('.jpg', frame)[1].tobytes()
                print(img_encoded)
                im = Image.fromarray(np.uint8(cm.gist_earth(frame) * 255))
                sock.send(bytes(str(len(img_encoded)), 'utf8'))  # Should be ready to write
                time.sleep(1)
                sock.send(img_encoded)  # Should be ready to write
                time.sleep(1)
                print('closing connection to', data.addr)
                sel.unregister(sock)
                sock.close()


lsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
lsock.bind((HOST, PORT))
lsock.listen()
print("listening on", (HOST, PORT))
lsock.setblocking(False)
sel.register(lsock, selectors.EVENT_READ, data=None)

try:
    while True:
        events = sel.select(timeout=None)
        for key, mask in events:
            if key.data is None:
                accept_wrapper(key.fileobj)
            else:
                service_connection(key, mask)
except KeyboardInterrupt:
    print("caught keyboard interrupt, exiting")
finally:
    sel.close()
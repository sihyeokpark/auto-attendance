import face_recognition
import cv2
import numpy as np
import os
import time
import csv

# openCV 카메라를 오픈하는 api
video_capture = cv2.VideoCapture(0)

########################################
# face_recognition Library를 사용하여
# 딥러닝 기반으로 제작된 dlib의 최첨단 얼굴 인식 기능을 사용하여 구축 했습니다.
# 이 모델은 Labeled Faces in the Wild 기준으로 99.38%의 정확도를 가집니다.
# How to use face_recognition API
# https://face-recognition.readthedocs.io/en/latest/face_recognition.html

# 이미지 학습(?) 시간 체크
start_time = time.time()

# Load a sample picture and learn how to recognize it.
path = "faces"
file_list = os.listdir(path)

imgList = []
faceEncodingList = []
faceNameList = []
encoding = []

# 얼굴 배열 읽어오기
openFile = './faces/face_detecting.csv'
with open(openFile, 'r') as f:
    rdr = csv.reader(f)
    for i, line in enumerate(rdr):
        nparr = np.array(line)
        floatarr = nparr.astype(np.float64)
        faceEncodingList.append(floatarr)

# 이름 배열 읽어오기
openFile = './faces/face_detecting_name.csv'
with open(openFile, 'r') as f:
    rdr = csv.reader(f)
    for i, line in enumerate(rdr):
        faceNameList.append(''.join(line))

print(time.time() - start_time)


# Create arrays of known face encodings and their names
# known_face_encodings = faceEncodingList
# known_face_names = faceNameList

known_face_encodings = faceEncodingList
known_face_names = faceNameList
########################################

# Initialize some variables
face_locations = []
face_encodings = []
face_names = []
process_this_frame = True

while True:
    ret, frame = video_capture.read()
    if ret < 0:
        print("카메라가 열리지 않았습니다 다시 한번 확인해 주세요.")
        pass

    # Resize frame of video to 1/4 size for faster face recognition processing
    small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)

    # Convert the image from BGR color (which OpenCV uses) to RGB color (which face_recognition uses)
    rgb_small_frame = small_frame[:, :, ::-1]

    # Only process every other frame of video to save time
    if process_this_frame:
        # Find all the faces and face encodings in the current frame of video
        face_locations = face_recognition.face_locations(rgb_small_frame)
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

        face_names = []
        for face_encoding in face_encodings:
            # See if the face is a match for the known face(s)
            matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
            name = "Unknown"

            # # If a match was found in known_face_encodings, just use the first one.
            # if True in matches:
            #     first_match_index = matches.index(True)
            #     name = known_face_names[first_match_index]

            # Or instead, use the known face with the smallest distance to the new face
            face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
            best_match_index = np.argmin(face_distances)
            if matches[best_match_index]:
                name = known_face_names[best_match_index]

            face_names.append(name)


    process_this_frame = not process_this_frame

    # 인식이 된 최초의 시간을 버퍼에 저장한 후에 이름과 출석 시간을 보여준다..
    # 현재 시간을 알아오는 PYTHON

    # Display the results
    for (top, right, bottom, left), name in zip(face_locations, face_names):
        now = time.localtime()
        print(f"{time.strftime('%Y.%m.%d: %H:%M:%S', now)} - {face_names} 출석 완료.")
        # Scale back up face locations since the frame we detected in was scaled to 1/4 size
        top *= 4
        right *= 4
        bottom *= 4
        left *= 4

        # Draw a box around the face
        cv2.rectangle(frame, (left, top), (right, bottom), (255, 0, 0), 1)

        # Draw a label with a name below the face
        cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (255, 0, 0), cv2.FILLED)
        font = cv2.FONT_HERSHEY_DUPLEX
        cv2.putText(frame, name, (left + 6, bottom - 6), font, 1.0, (255, 255, 255), 1)

    # Display the resulting image
    cv2.imshow('Video', frame)

    # Hit 'q' on the keyboard to quit!
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release handle to the webcam
video_capture.release()
cv2.destroyAllWindows()

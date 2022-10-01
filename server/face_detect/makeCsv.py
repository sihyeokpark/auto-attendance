import face_recognition
import numpy as np
import os
import time
import csv

########################################
# face_recognition Library를 사용하여
# 딥러닝 기반으로 제작된 dlib의 최첨단 얼굴 인식 기능을 사용하여 구축 했습니다.
# 이 모델은 Labeled Faces in the Wild 기준으로 99.38%의 정확도를 가집니다.
# How to use face_recognition API
# https://face-recognition.readthedocs.io/en/latest/face_recognition.html

def makeCsv():
    # 이미지 학습(?) 시간 체크
    start_time = time.time()

    # Load a sample picture and learn how to recognize it.
    path = "face_detect/faces"
    file_list = os.listdir(path)

    imgList = []
    faceEncodingList = []
    faceNameList = []

    # 얼굴 배열을 face_detection.csv 에 저장
    openFile = './face_detect/faces/face_detecting.csv'
    with open(openFile, 'w+', newline='') as f:
        writer = csv.writer(f)
        for file in file_list:
            extension = file.split('.')[1]
            if extension == 'jpg':
                img = face_recognition.load_image_file(f"face_detect/faces/{file}")
                imgList.append(img)
                encoding = face_recognition.face_encodings(img)
                if len(encoding) <= 0:
                    print(f'Error: {file}에서 얼굴을 인식하지 못했습니다.')
                else:
                    writer.writerow(encoding[0].tolist())
                    faceEncodingList.append(encoding[0])

    # 이름 배열을 face_detection_name.csv 에 저장
    openFile = './face_detect/faces/face_detecting_name.csv'
    with open(openFile, 'w+', newline='') as f:
        writer = csv.writer(f)
        for file in file_list:
            extension = file.split('.')[1]
            if extension == 'jpg':
                writer.writerow(file.split('_')[0])
                faceNameList.append(file.split('_')[0])

    # 걸린 시간 측정
    print(time.time() - start_time)

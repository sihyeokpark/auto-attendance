import numpy as np
import cv2
import dlib
import math

faceCascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml' )
predictor = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")

# 얼굴의 각 구역의 포인트들을 구분해 놓기
JAWLINE_POINTS = list(range(0, 17))
RIGHT_EYEBROW_POINTS = list(range(17, 22))
LEFT_EYEBROW_POINTS = list(range(22, 27))
NOSE_POINTS = list(range(27, 36))
RIGHT_EYE_POINTS = list(range(36, 42))
LEFT_EYE_POINTS = list(range(42, 48))
MOUTH_OUTLINE_POINTS = list(range(48, 61))
MOUTH_INNER_POINTS = list(range(61, 68))

""" 
    def = dlib를 이용 얼굴과 눈을 찾는 함수
    input = 그레이 스케일 이미지
    output = 얼굴 중요 68개의 포인트 에 그려진 점 + 이미지
"""

def getSlope(point1, point2):
    x1 = point1.item(0)
    y1 = point1.item(1)
    x2 = point2.item(0)
    y2 = point2.item(1)
    if (x2 - x1) == 0:
        return 0
    return (y2 - y1)/(x2 - x1)

def detect(gray, frame):
    # 일단, 등록한 Cascade classifier 를 이용 얼굴을 찾음
    faces = faceCascade.detectMultiScale(gray, scaleFactor=1.05, minNeighbors=5, minSize=(100, 100),
                                         flags=cv2.CASCADE_SCALE_IMAGE)

    # 얼굴에서 랜드마크를 찾자
    for (x, y, w, h) in faces:
        # 오픈 CV 이미지를 dlib용 사각형으로 변환하고
        dlib_rect = dlib.rectangle(int(x), int(y), int(x + w), int(y + h))
        # 랜드마크 포인트들 지정
        landmarks = np.matrix([[p.x, p.y] for p in predictor(frame, dlib_rect).parts()])
        # 원하는 포인트들을 넣는다, 지금은 전부
        landmarks_display = landmarks[0:68]
        # 눈만 = landmarks_display = landmarks[RIGHT_EYE_POINTS, LEFT_EYE_POINTS]

        # 포인트 출력
        for idx, point in enumerate(landmarks_display):
            pos = (point[0, 0], point[0, 1])
            cv2.circle(frame, pos, 2, color=(0, 255, 255), thickness=-1)

        # 18 19 20 21 22, 23 24 25 26 27 번 점 (눈썹)
        eyebrows = [[18, 19, 20, 21, 22], [23, 24, 25, 26, 27]]
        # 28, 34 점 (코 끝과 끝)
        noseSlope = getSlope(landmarks[27], landmarks[34])
        noseAngle = math.atan(noseSlope) * 180 / math.pi
        print(noseAngle)

        eyebrowsSlope = [[], []]
        # f = open("박시혁.txt", 'w')
        for i in range(2):
            for j in range(len(eyebrows[i])-1):
                eyebrowsSlope[i].append(getSlope(landmarks[eyebrows[i][j]-1], landmarks[eyebrows[i][j+1]-1]))
                # f.write(str(eyebrowsSlope[i][j]) + ',')
        # print(eyebrowsSlope)
        # f.close()

    return frame


# 웹캠에서 이미지 가져오기
video_capture = cv2.VideoCapture(0)

while True:
    # 웹캠 이미지를 프레임으로 자름
    _, frame = video_capture.read()
    # 그리고 이미지를 그레이스케일로 변환
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # 만들어준 얼굴 눈 찾기
    canvas = detect(gray, frame)
    # 찾은 이미지 보여주기
    cv2.imshow("haha", canvas)

    # q를 누르면 종료
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
# 끝
video_capture.release()
cv2.destroyAllWindows()
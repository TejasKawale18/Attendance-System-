import os
import cv2
import pickle
import time
import csv
import numpy as np
from datetime import datetime
from win32com.client import Dispatch
from sklearn.neighbors import KNeighborsClassifier


def speak(text):
    speaker = Dispatch("SAPI.SpVoice")
    speaker.Speak(text)


# Fix Haarcascade File Path
cascade_path = 'haarcascade_frontalface_default.xml'
if not os.path.exists(cv2.data.haarcascades + cascade_path):
    print("Error: Haarcascade file not found! Download from OpenCV GitHub.")
    exit()

facedetect = cv2.CascadeClassifier(cv2.data.haarcascades + cascade_path)

# Load Training Data
try:
    with open('data/names.pkl', 'rb') as f:
        LABELS = pickle.load(f)
    with open('data/faces_data.pkl', 'rb') as f:
        FACES = pickle.load(f)
except FileNotFoundError:
    print("Error: Training data files missing! Train the model first.")
    exit()

# Validate Data Consistency
if len(FACES) == 0 or len(LABELS) == 0:
    print("Error: Empty training data found! Ensure faces and labels exist.")
    exit()

if len(FACES) != len(LABELS):
    print(f"Error: Mismatch! Faces: {len(FACES)}, Labels: {len(LABELS)}")
    exit()

print(f'Shape of Faces Matrix: {FACES.shape}')

# Train KNN Model
knn = KNeighborsClassifier(n_neighbors=5)
knn.fit(FACES, LABELS)

# Attendance Setup
imgBackground = cv2.imread("background.png")
COL_NAMES = ['NAME', 'TIME']
os.makedirs("Attendance", exist_ok=True)

video = cv2.VideoCapture(1)  # Ensure the correct camera index
if not video.isOpened():
    print("Error: Could not open webcam. Check if another program is using it.")
    exit()

while True:
    ret, frame = video.read()
    if not ret:
        print("Error: Camera frame capture failed.")
        break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = facedetect.detectMultiScale(gray, 1.3, 5)
    attendance_list = []  # Store multiple detections

    for (x, y, w, h) in faces:
        crop_img = cv2.resize(frame[y:y + h, x:x + w], (50, 50)).flatten().reshape(1, -1)

        try:
            output = knn.predict(crop_img)[0]  # Ensure output is a single label
        except ValueError:
            print("Error: Invalid face data shape for prediction.")
            continue  # Skip to the next detected face

        # Timestamp
        ts = time.time()
        date = datetime.fromtimestamp(ts).strftime("%d-%m-%Y")
        timestamp = datetime.fromtimestamp(ts).strftime("%H:%M:%S")
        attendance_file = f"Attendance/Attendance_{date}.csv"
        exist = os.path.isfile(attendance_file)

        # Draw Face Box & Name
        cv2.rectangle(frame, (x, y), (x + w, y + h), (50, 50, 255), 2)
        cv2.rectangle(frame, (x, y - 40), (x + w, y), (50, 50, 255), -1)
        cv2.putText(frame, str(output), (x, y - 15), cv2.FONT_HERSHEY_COMPLEX, 1, (255, 255, 255), 1)

        # Store Attendance
        attendance_list.append([str(output), timestamp])

    imgBackground[162:162 + 480, 55:55 + 640] = frame
    cv2.imshow("Frame", imgBackground)

    k = cv2.waitKey(1)

    if k == ord('o'):
        speak("Attendance Taken")
        time.sleep(2)

        with open(attendance_file, "a", newline='') as csvfile:
            writer = csv.writer(csvfile)
            if not exist:
                writer.writerow(COL_NAMES)
            writer.writerows(attendance_list)  # Write all detected faces

    if k == ord('q'):
        break

video.release()
cv2.destroyAllWindows()






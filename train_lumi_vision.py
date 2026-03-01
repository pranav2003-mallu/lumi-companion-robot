import cv2
import os
import numpy as np
import time

def main():
    print("========================================")
    print("Welcome to Lumi's Vision Training!")
    print("========================================")
    print("We will capture 30 pictures of your face to teach Lumi who you are.")
    print("Please look directly at your laptop camera.")
    print("Make sure your face is well-lit.")
    print("Starting in 3 seconds...")
    time.sleep(3)

    # Initialize webcam
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open camera 0. Trying camera 1...")
        cap = cv2.VideoCapture(1)
        if not cap.isOpened():
            print("Error: Could not open any camera.")
            return

    # Load Haar cascade
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

    count = 0
    print("Capturing faces... Please move your head slightly to capture different angles.")

    faces_data = []
    labels = []
    
    while count < 30:
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame.")
            break

        frame = cv2.flip(frame, 1) # Mirror the image
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Detect face
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.3, minNeighbors=5)
        
        for (x, y, w, h) in faces:
            count += 1
            # Crop the face from the grayscale image
            face_img = gray[y:y+h, x:x+w]
            
            # Store data for training
            faces_data.append(face_img)
            labels.append(1) # Assuming ID '1' belongs to Mallu
            
            # Draw a green rectangle and text on the colored frame to show progress
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
            cv2.putText(frame, f"Capturing: {count}/30", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            
            # Only take one face per frame for training
            break 
            
        cv2.imshow("Lumi Vision Trainer (Press 'q' to cancel)", frame)
        # Wait 150ms between captures so it doesn't take all 30 pictures in half a second
        if cv2.waitKey(150) & 0xFF == ord('q'):
            print("Cancelled by user.")
            break

    cap.release()
    cv2.destroyAllWindows()

    if count < 30:
        print("Training stopped before capturing 30 faces. Please run the script again and stay in frame.")
        return

    print("Capture complete! Compiling your face into Lumi's brain...")
    
    # Train the recognizer
    try:
        recognizer = cv2.face.LBPHFaceRecognizer_create()
        recognizer.train(faces_data, np.array(labels))
        
        # Save the model
        model_path = "/home/mallu/app_ui/lumi_ws/src/lumi_ui/lumi_ui/lumi_face_model.yml"
        recognizer.write(model_path)
        print("========================================")
        print(f"Success! Model trained and saved to {model_path}.")
        print("Lumi now knows exactly what you look like! 🎉")
        print("Next, I will connect this file into Lumi's live face tracker script.")
        print("========================================")
    except AttributeError:
        print("\nERROR: cv2.face module not found.")
        print("To fix this, you need to install the contrib package. Run this command:")
        print("pip3 install opencv-contrib-python")
    except Exception as e:
        print(f"Error during training: {e}")

if __name__ == "__main__":
    main()

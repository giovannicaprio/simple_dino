import cv2
import numpy as np
import mediapipe as mp
from collections import deque

class JumpDetector:
    def __init__(self):
        # Initialize MediaPipe Pose
        self.mp_pose = mp.solutions.pose
        self.mp_draw = mp.solutions.drawing_utils
        self.pose = self.mp_pose.Pose(
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        
        # Initialize camera
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            raise ValueError("Could not open camera")
        
        # Previous y positions of hips to detect movement (using a buffer for smoothing)
        self.hip_positions = deque(maxlen=5)
        self.jump_threshold = 0.03  # Adjusted threshold for better sensitivity
        self.is_jumping_state = False
        self.jump_cooldown = 0
        
    def is_jumping(self):
        success, image = self.cap.read()
        if not success:
            print("Failed to grab frame")
            return False
        
        # Convert the BGR image to RGB
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Process the image and detect poses
        results = self.pose.process(image_rgb)
        
        # Convert back to BGR for OpenCV display
        image = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR)
        
        jump_detected = False
        
        if results.pose_landmarks:
            # Draw the pose landmarks on the image
            self.mp_draw.draw_landmarks(
                image, 
                results.pose_landmarks, 
                self.mp_pose.POSE_CONNECTIONS
            )
            
            # Get hip landmarks
            left_hip = results.pose_landmarks.landmark[self.mp_pose.PoseLandmark.LEFT_HIP]
            right_hip = results.pose_landmarks.landmark[self.mp_pose.PoseLandmark.RIGHT_HIP]
            
            # Calculate average hip height
            current_hip_y = (left_hip.y + right_hip.y) / 2
            
            # Add current position to buffer
            self.hip_positions.append(current_hip_y)
            
            # Only process if we have enough positions in our buffer
            if len(self.hip_positions) == 5:
                # Calculate movement (difference between average of first 2 and last 2 positions)
                past_pos = sum(list(self.hip_positions)[:2]) / 2
                current_pos = sum(list(self.hip_positions)[-2:]) / 2
                movement = past_pos - current_pos
                
                # Draw movement value on screen
                cv2.putText(
                    image,
                    f"Movement: {movement:.4f}",
                    (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (0, 255, 0) if movement > self.jump_threshold else (0, 0, 255),
                    2
                )
                
                # Detect jump with cooldown
                if movement > self.jump_threshold and not self.is_jumping_state and self.jump_cooldown == 0:
                    jump_detected = True
                    self.is_jumping_state = True
                    self.jump_cooldown = 10  # frames of cooldown
                elif movement < self.jump_threshold/2:
                    self.is_jumping_state = False
                
                if self.jump_cooldown > 0:
                    self.jump_cooldown -= 1
        
        # Display jump status
        status = "JUMP!" if jump_detected else "Standing"
        cv2.putText(
            image,
            status,
            (10, 70),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0) if jump_detected else (0, 0, 255),
            2
        )
        
        # Show the image
        cv2.imshow('Jump Detection', image)
        
        return jump_detected
    
    def release(self):
        self.cap.release()
        cv2.destroyAllWindows()

# Test the jump detection
if __name__ == "__main__":
    try:
        detector = JumpDetector()
        print("Jump Detection Test")
        print("Jump to see if it's detected")
        print("Press 'q' to quit")
        
        while True:
            if detector.is_jumping():
                print("Jump detected!")
                
            # Check for 'q' key to quit
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
            
    except Exception as e:
        print(f"Error occurred: {e}")
    finally:
        if 'detector' in locals():
            detector.release()

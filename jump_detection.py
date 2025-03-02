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
        
        # Initialize camera with lower resolution
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            raise ValueError("Could not open camera")
        # Set lower resolution for better performance
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
        
        # Previous y positions of hips to detect movement (using a larger buffer for better smoothing)
        self.hip_positions = deque(maxlen=10)  # Increased buffer size
        self.jump_threshold = 0.05  # Increased threshold for less sensitivity
        self.min_positions = 8  # Minimum positions needed for reliable detection
        self.is_jumping_state = False
        self.jump_cooldown = 15  # Increased cooldown to prevent rapid jumps
        
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
            
            # Only process if we have enough positions in our buffer for reliable detection
            if len(self.hip_positions) >= self.min_positions:
                # Calculate movement using weighted averages
                past_positions = list(self.hip_positions)[:4]  # First 4 positions
                current_positions = list(self.hip_positions)[-4:]  # Last 4 positions
                
                # Calculate weighted averages (more recent positions have higher weight)
                past_pos = sum(p * (i+1) for i, p in enumerate(past_positions)) / sum(range(1, len(past_positions) + 1))
                current_pos = sum(p * (i+1) for i, p in enumerate(current_positions)) / sum(range(1, len(current_positions) + 1))
                
                movement = past_pos - current_pos
                
                # Draw movement value on screen with color coding
                color = (0, 255, 0) if movement > self.jump_threshold else (
                    (255, 165, 0) if movement > self.jump_threshold/2 else (0, 0, 255)
                )
                cv2.putText(
                    image,
                    f"Movement: {movement:.4f}",
                    (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    color,
                    2
                )
                
                # Detect jump with improved conditions
                if (movement > self.jump_threshold and 
                    not self.is_jumping_state and 
                    self.jump_cooldown == 0 and 
                    movement < 0.15):  # Maximum threshold to prevent false positives
                    jump_detected = True
                    self.is_jumping_state = True
                    self.jump_cooldown = 15  # Increased frames of cooldown
                elif movement < self.jump_threshold/3:  # Require more settling before allowing new jump
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

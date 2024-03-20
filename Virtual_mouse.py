import cv2
import mediapipe as mp
import pyautogui
import math

mp_drawing = mp.solutions.drawing_utils
mp_hands = mp.solutions.hands

class Gestures:
    PALM = 0
    FIST = 1
    TWO_FINGER_CLOSED = 2
    PINCH = 3
    SCROLL_UP = 4

class HandTracker:
    def __init__(self):
        self.hand_landmarks = None

    def update(self, results):
        self.hand_landmarks = results.multi_hand_landmarks[0] if results.multi_hand_landmarks else None


class MouseController:
    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.prev_x = 0
        self.prev_y = 0

    def scroll_up(self):
        pyautogui.scroll(18)  # Adjust the argument to control scroll speed

    def move(self, x, y):
        # Interpolate between previous and current positions for smooth movement
        interpolated_x = self.prev_x + 0.2 * (x - self.prev_x)
        interpolated_y = self.prev_y + 0.2 * (y - self.prev_y)
        pyautogui.moveTo(interpolated_x, interpolated_y)

        # Update previous position
        self.prev_x = interpolated_x
        self.prev_y = interpolated_y

    def click(self):
        pyautogui.doubleClick()  # Perform a double-click action


class GestureController:
    def __init__(self, screen_width, screen_height):
        self.hand_tracker = HandTracker()
        self.mouse_controller = MouseController(screen_width, screen_height)

    def calculate_distance(self, point1, point2):
        return math.sqrt((point1.x - point2.x) ** 2 + (point1.y - point2.y) ** 2)

    def detect_gesture(self):
        if not self.hand_tracker.hand_landmarks:
            return Gestures.PALM

        index_finger_tip = self.hand_tracker.hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
        thumb_tip = self.hand_tracker.hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP]

        # Calculate the distance between thumb and index finger tips
        distance_thumb_index = self.calculate_distance(index_finger_tip, thumb_tip)

        # Check if the distance between thumb and index finger tips is below a threshold
        if distance_thumb_index < 0.03:  # Adjust the threshold as needed
            print("Thumb and Index Finger Touching - Double Clicking")
            self.mouse_controller.click()
            return Gestures.PINCH

        # Check if the index finger is above a certain threshold for scroll action
        if index_finger_tip.y < 0.2:  # Adjust the threshold as needed
            print("Index Finger Up - Scrolling Up")
            self.mouse_controller.scroll_up()
            return Gestures.SCROLL_UP

        # Your other gesture detection logic here

        print("No Gesture Detected")
        return Gestures.PALM

    def run(self):
        cap = cv2.VideoCapture(0)

        with mp_hands.Hands(max_num_hands=2, min_detection_confidence=0.5, min_tracking_confidence=0.3) as hands:

            while cap.isOpened():
                success, image = cap.read()

                if not success:
                    print("Ignoring empty camera frame.")
                    continue

                image = cv2.cvtColor(cv2.flip(image, 1), cv2.COLOR_BGR2RGB)
                image.flags.writeable = False
                results = hands.process(image)
                image.flags.writeable = True
                image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

                self.hand_tracker.update(results)
                gesture = self.detect_gesture()

                if self.hand_tracker.hand_landmarks:
                    index_finger_tip = self.hand_tracker.hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
                    hand_x = int(index_finger_tip.x * self.mouse_controller.screen_width)
                    hand_y = int(index_finger_tip.y * self.mouse_controller.screen_height)
                    self.mouse_controller.move(hand_x, hand_y)

                if results.multi_hand_landmarks:
                    for landmarks in results.multi_hand_landmarks:
                        mp_drawing.draw_landmarks(image, landmarks, mp_hands.HAND_CONNECTIONS)

                cv2.imshow('Gesture Controller', image)

                if cv2.waitKey(5) & 0xFF == 27:  # Press 'Esc' to exit
                    break

        cap.release()
        cv2.destroyAllWindows()

# Run the GestureController
screen_width, screen_height = pyautogui.size()
gesture_controller = GestureController(screen_width, screen_height)
gesture_controller.run()

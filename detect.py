import cv2
import numpy as np
import mediapipe as mp
from mediapipe.framework.formats import landmark_pb2
from mediapipe.tasks.python import vision
from mediapipe.tasks.python import BaseOptions
import pyautogui


MARGIN = 10  # pixels
FONT_SIZE = 2
FONT_THICKNESS = 2
HANDEDNESS_TEXT_COLOR = (88, 205, 54)  # vibrant green

def thumb_linearity_check(points):
    """
    Check linearity of points 0, 1, 2, 3, 4 of the thumb.
    Returns True if the points form an approximate straight line.
    """
    total_deviation = 0
    num_segments = len(points) - 1

    for i in range(num_segments - 1):
        # Get vectors for consecutive segments
        v1 = (points[i + 1].x - points[i].x, points[i + 1].y - points[i].y)
        v2 = (points[i + 2].x - points[i + 1].x, points[i + 2].y - points[i + 1].y)

        # Compute the cross product (indicates deviation from linearity)
        cross_product = abs(v1[0] * v2[1] - v1[1] * v2[0])

        # Accumulate deviation
        total_deviation += cross_product

    average_deviation = total_deviation / num_segments
    return average_deviation < 0.02  # Adjust threshold based on testing


def get_finger_states(hand_landmarks, handedness):
    """
    Determine if fingers are open or closed.
    Includes thumb detection using linearity.
    """
    FINGER_TIPS = [4, 8, 12, 16, 20]  # Thumb, Index, Middle, Ring, Pinky tips
    FINGER_PIPS = [3, 6, 10, 14, 18]  # Thumb IP, Index PIP, Middle PIP, Ring PIP, Pinky PIP

    states = []

    # Thumb logic: check linearity of points 0, 1, 2, 3, 4
    thumb_points = [hand_landmarks[i] for i in range(5)]
    thumb_linearity = thumb_linearity_check(thumb_points)

    # Thumb open/closed determination based on handedness and linearity
    if handedness == "Left":
        # Thumb tip to IP should form a straight line
        if hand_landmarks[4].x > hand_landmarks[3].x and thumb_linearity:
            states.append(True)  # Open
        else:
            states.append(False)  # Closed
    else:  # Right Hand
        if hand_landmarks[4].x < hand_landmarks[3].x and thumb_linearity:
            states.append(True)  # Open
        else:
            states.append(False)  # Closed

    # Logic for other fingers (vertical check)
    for tip, pip in zip(FINGER_TIPS[1:], FINGER_PIPS[1:]):
        if hand_landmarks[tip].y < hand_landmarks[pip].y:  # Tip above PIP means finger is open
            states.append(True)  # Open
        else:
            states.append(False)  # Closed

    return states


def distance_between_points(point1, point2):
    """
    Calculate the Euclidean distance between two normalized keypoints.
    """
    return np.sqrt((point1.x - point2.x) ** 2 + (point1.y - point2.y) ** 2)


def move_cursor_with_index_finger(index_tip, frame_width, frame_height):
    cursor_x = int(index_tip.x * frame_width)
    cursor_y = int((index_tip.y * frame_height)+50)
    pyautogui.moveTo(cursor_x, cursor_y)


def draw_landmarks_on_image(rgb_image, detection_result):
    if detection_result.hand_landmarks is None:
        return rgb_image

    annotated_image = np.copy(rgb_image)

    hand_landmarks_list = detection_result.hand_landmarks
    handedness_list = detection_result.handedness

    for idx in range(len(hand_landmarks_list)):
        hand_landmarks = hand_landmarks_list[idx]
        handedness = handedness_list[idx][0].category_name  # Access handedness
        corrected_handedness = "Right" if handedness == "Left" else "Left"

        finger_states = get_finger_states(hand_landmarks, corrected_handedness)

        hand_landmarks_proto = landmark_pb2.NormalizedLandmarkList()
        hand_landmarks_proto.landmark.extend([
            landmark_pb2.NormalizedLandmark(
                x=landmark.x, y=landmark.y, z=landmark.z) for landmark in hand_landmarks
        ])
        mp.solutions.drawing_utils.draw_landmarks(
            annotated_image,
            hand_landmarks_proto,
            mp.solutions.hands.HAND_CONNECTIONS,
            mp.solutions.drawing_styles.get_default_hand_landmarks_style(),
            mp.solutions.drawing_styles.get_default_hand_connections_style())

        height, width, _ = annotated_image.shape
        x_coordinates = [landmark.x for landmark in hand_landmarks]
        y_coordinates = [landmark.y for landmark in hand_landmarks]
        text_x = int(min(x_coordinates) * width)
        text_y = int(min(y_coordinates) * height) - MARGIN

        cv2.putText(
            annotated_image,
            corrected_handedness,
            (text_x, text_y),
            cv2.FONT_HERSHEY_DUPLEX,
            FONT_SIZE,
            HANDEDNESS_TEXT_COLOR,
            FONT_THICKNESS,
            cv2.LINE_AA
        )

        finger_labels = ["Thumb", "Index", "Middle", "Ring", "Pinky"]
        for i, state in enumerate(finger_states):
            cv2.putText(
                annotated_image,
                f"{finger_labels[i]}: {'Open' if state else 'Closed'}",
                (text_x, text_y + (i + 1) * 20),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                HANDEDNESS_TEXT_COLOR,
                1,
                cv2.LINE_AA
            )

    return annotated_image


def perform_gesture_actions(controlling_hand, controlling_handedness, finger_states, frame_width, frame_height):
    """
    Perform actions (cursor move, click, scroll, drag) based on finger states.
    """
    actions = {
        "click": False,
        "scroll": False,
        "drag": None,
    }

    if controlling_hand:
        # If only the index finger is open, move the cursor with it
        if finger_states[1] and all(not state for idx, state in enumerate(finger_states) if idx != 1):
            index_tip = controlling_hand[8]
            move_cursor_with_index_finger(index_tip, frame_width, frame_height)

        # Click if thumb and index are open, and others closed
        if finger_states[0] and finger_states[1] and all(not state for state in finger_states[2:]):
            pyautogui.click()
            print("Clicked")
            actions["click"] = True

        # Scroll if index and middle are open, others closed
        if finger_states[1] and finger_states[2] and all(not state for idx, state in enumerate(finger_states) if idx not in [1, 2]):
            index_tip = controlling_hand[8]
            middle_tip = controlling_hand[12]
            actions["scroll-down"] = (index_tip, middle_tip)
            print("Scroll down")

        if finger_states[1] and finger_states[2] and finger_states[3]  and all(
                not state for idx, state in enumerate(finger_states) if idx not in [1, 2, 3]):
            index_tip = controlling_hand[8]
            middle_tip = controlling_hand[12]
            actions["scroll-up"] = (index_tip, middle_tip)
            print("Scroll up")

    return actions
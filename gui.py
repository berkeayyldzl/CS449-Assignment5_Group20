import cv2
import math
import numpy as np
import pyautogui
import mediapipe as mp
from mediapipe.tasks.python import vision
from mediapipe.tasks.python import BaseOptions

from detect import (
    get_finger_states,
    draw_landmarks_on_image,
    perform_gesture_actions
)

# Import submenu handlers
from channels import open_channels_menu
from changeSound import open_changesound_menu
from settings import open_settings_menu

# Button configuration for radial menu
BUTTONS = [
    {"label": "Settings"},
    {"label": "Change Sound"},
    {"label": "Turn Off"},
    {"label": "Channels"},
    {"label": "Back"}
]

# Controls for menu and exit
show_menu = False
current_menu = None
screen_exit = False  # Global flag for exiting the program


def draw_menu_button(frame, cursor_position, click_flag):
    global show_menu, current_menu

    # Only draw the menu button if the main radial menu and no submenu is active
    if show_menu or current_menu is not None:
        return

    x, y, w, h = 20, 20, 200, 80
    button_color = (200, 200, 200)  # Light gray background
    hover_color = (0, 255, 0)       # Green highlight on hover
    text_color = (0, 0, 0)          # Black text
    font = cv2.FONT_HERSHEY_DUPLEX

    cursor_x, cursor_y = cursor_position
    is_hovered = (x <= cursor_x <= x + w) and (y <= cursor_y - 50 <= y + h)

    # Change color if hovered
    color = hover_color if is_hovered else button_color

    # Draw the button
    cv2.rectangle(frame, (x, y), (x + w, y + h), color, -1)

    # Draw the label "Menu"
    label = "Menu"
    text_scale = 1.0
    text_thickness = 2
    text_size = cv2.getTextSize(label, font, text_scale, text_thickness)[0]
    text_x = x + (w - text_size[0]) // 2
    text_y = y + (h + text_size[1]) // 2

    cv2.putText(
        frame,
        label,
        (text_x, text_y),
        font,
        text_scale,
        text_color,
        text_thickness,
        cv2.LINE_AA
    )

    # Toggle the menu state if clicked
    if is_hovered and click_flag:
        show_menu = True
        print("Menu toggled:", show_menu)


def draw_circular_selector(frame, cursor_position, click_flag):
    global show_menu, current_menu, screen_exit

    if not show_menu:
        return  # Do not draw if show_menu is False

    height, width, _ = frame.shape
    center_x = width // 2
    center_y = height // 2

    N = len(BUTTONS)
    angle_step = 360 / N

    outer_radius = min(center_x, center_y) - 50
    inner_radius = outer_radius // 2

    line_color = (100, 100, 100)       # Lighter grey for wedge lines
    text_color = (255, 255, 255)       # White text
    highlight_color = (0, 255, 0)      # Green for highlight on hover
    font = cv2.FONT_HERSHEY_DUPLEX

    overlay = frame.copy()
    cv2.circle(overlay, (center_x, center_y), outer_radius, (120, 120, 120), -1)
    alpha = 0.3
    cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)

    cursor_x, cursor_y = cursor_position
    dx = cursor_x - center_x
    dy = cursor_y - center_y
    dist = math.sqrt(dx * dx + dy * dy)
    angle = (math.degrees(math.atan2(dy, dx)) + 360) % 360

    hovered_index = None
    if inner_radius < dist < outer_radius:
        hovered_index = int(angle // angle_step)

    for i, button in enumerate(BUTTONS):
        start_angle = i * angle_step
        end_angle = start_angle + angle_step

        sx = int(center_x + outer_radius * math.cos(math.radians(start_angle)))
        sy = int(center_y + outer_radius * math.sin(math.radians(start_angle)))
        cv2.line(frame, (center_x, center_y), (sx, sy), line_color, 2)

        ex = int(center_x + outer_radius * math.cos(math.radians(end_angle)))
        ey = int(center_y + outer_radius * math.sin(math.radians(end_angle)))
        cv2.line(frame, (center_x, center_y), (ex, ey), line_color, 2)

        mid_angle = math.radians(start_angle + angle_step / 2)
        label_radius = (inner_radius + outer_radius) // 2
        lx = int(center_x + label_radius * math.cos(mid_angle))
        ly = int(center_y + label_radius * math.sin(mid_angle))

        is_hovered = (hovered_index == i)
        if is_hovered:
            hover_overlay = frame.copy()
            arc_points = 50
            wedge_points = []

            for j in range(arc_points + 1):
                a = math.radians(start_angle + j * (angle_step / arc_points))
                x = int(center_x + outer_radius * math.cos(a))
                y = int(center_y + outer_radius * math.sin(a))
                wedge_points.append((x, y))

            for j in range(arc_points + 1):
                a = math.radians(end_angle - j * (angle_step / arc_points))
                x = int(center_x + inner_radius * math.cos(a))
                y = int(center_y + inner_radius * math.sin(a))
                wedge_points.append((x, y))

            wedge_polygon = np.array(wedge_points, dtype=np.int32)
            cv2.fillPoly(hover_overlay, [wedge_polygon], highlight_color)
            cv2.addWeighted(hover_overlay, 0.3, frame, 0.7, 0, frame)

            # Handle click
            if click_flag:
                print(f"{button['label']} clicked!")
                if button["label"] == "Back":
                    show_menu = False
                elif button["label"] == "Channels":
                    show_menu = False
                    current_menu = "channels"
                elif button["label"] == "Change Sound":
                    show_menu = False
                    current_menu = "changeSound"
                elif button["label"] == "Settings":
                    show_menu = False
                    current_menu = "settings"
                elif button["label"] == "Turn Off":
                    print("Device turned off (placeholder)")
                    screen_exit = True

        text_scale = 0.7
        text_thickness = 2
        text_size = cv2.getTextSize(button["label"], font, text_scale, text_thickness)[0]
        text_x = lx - text_size[0] // 2
        text_y = ly + text_size[1] // 2
        cv2.putText(frame, button["label"], (text_x, text_y),
                    font, text_scale, text_color, text_thickness, cv2.LINE_AA)


def handle_submenus(frame, cursor_position, click_flag, actions):
    global current_menu, show_menu

    def set_current_menu(menu_name):
        global current_menu, show_menu
        current_menu = menu_name
        if menu_name is None:
            show_menu = False

    if current_menu == "channels":
        open_channels_menu(frame, cursor_position, click_flag, set_current_menu, actions)
    elif current_menu == "changeSound":
        open_changesound_menu(frame, cursor_position, click_flag, set_current_menu, actions)
    elif current_menu == "settings":
        open_settings_menu(frame, cursor_position, click_flag, set_current_menu, actions)


cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Error: Could not open webcam.")
    exit()

print("Press 'q' to exit.")

base_options = BaseOptions(model_asset_path='hand_landmarker.task')
options = vision.HandLandmarkerOptions(
    base_options=base_options,
    num_hands=2
)

dragging = False
avg_y_previous = None

with vision.HandLandmarker.create_from_options(options) as detector:
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame.")
            break
        frame = cv2.flip(frame, 1)

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)

        detection_result = detector.detect(mp_image)

        right_hand = None
        left_hand = None

        if detection_result.hand_landmarks:
            for idx, hand_landmarks in enumerate(detection_result.hand_landmarks):
                handedness = detection_result.handedness[idx][0].category_name
                corrected_handedness = "Right" if handedness == "Left" else "Left"

                if corrected_handedness == "Right":
                    right_hand = hand_landmarks
                elif corrected_handedness == "Left":
                    left_hand = hand_landmarks

        controlling_hand = right_hand or left_hand
        controlling_handedness = "Right" if right_hand else "Left"

        finger_states = []
        if controlling_hand:
            finger_states = get_finger_states(controlling_hand, controlling_handedness)

        actions = perform_gesture_actions(controlling_hand, controlling_handedness, finger_states, frame.shape[1], frame.shape[0])

        cursor_position = pyautogui.position()
        click_flag = actions.get("click", False)

        annotated_image = draw_landmarks_on_image(rgb_frame, detection_result)

        if current_menu is not None:
            handle_submenus(annotated_image, cursor_position, click_flag, actions)
        else:
            draw_menu_button(annotated_image, cursor_position, click_flag)
            draw_circular_selector(annotated_image, cursor_position, click_flag)

        cv2.imshow('Annotated Frame', cv2.cvtColor(annotated_image, cv2.COLOR_RGB2BGR))

        if cv2.waitKey(1) & 0xFF == ord('q') or screen_exit:
            print("Exiting program...")
            break

cap.release()
cv2.destroyAllWindows()
print("Program terminated successfully.")
import cv2
import numpy as np

# Initialize a global volume level
volume_level = 50  # Initial volume level (0-100)

def open_changesound_menu(frame, cursor_position, click_flag, set_current_menu_callback, actions):
    global volume_level

    # Dimensions
    height, width, _ = frame.shape

    # -------------------------
    # Draw the Exit Button
    # -------------------------
    # Position and size of the exit button
    btn_x, btn_y = 20, 20
    btn_w, btn_h = 200, 100
    button_color = (200, 200, 200)  # Light gray background
    hover_color = (0, 255, 0)       # Green highlight on hover
    text_color = (0, 0, 0)          # Black text
    font = cv2.FONT_HERSHEY_DUPLEX
    label = "Exit"

    cursor_x, cursor_y = cursor_position
    # Check if hovered
    is_hovered = (btn_x <= cursor_x <= btn_x + btn_w) and (btn_y <= cursor_y-50 <= btn_y + btn_h)
    color = hover_color if is_hovered else button_color

    # Draw the button rectangle
    cv2.rectangle(frame, (btn_x, btn_y), (btn_x + btn_w, btn_y + btn_h), color, -1)

    # Put the "Exit" text in the center of the button
    text_scale = 1.0
    text_thickness = 2
    text_size = cv2.getTextSize(label, font, text_scale, text_thickness)[0]
    text_x = btn_x + (btn_w - text_size[0]) // 2
    text_y = btn_y + (btn_h + text_size[1]) // 2
    cv2.putText(frame, label, (text_x, text_y), font, text_scale, text_color, text_thickness, cv2.LINE_AA)

    # If hovered and clicked, go back to the main menu
    if is_hovered and click_flag:
        set_current_menu_callback(None)
        print("Returned to main menu from Change Sound")
        return

    # -------------------------
    # Update Volume Level Based on Gestures
    # -------------------------
    if actions.get("scroll-up"):
        volume_level = min(volume_level + 5, 100)  # Increase volume
        print(f"Volume increased to {volume_level}")
    if actions.get("scroll-down"):
        volume_level = max(volume_level - 5, 0)    # Decrease volume
        print(f"Volume decreased to {volume_level}")

    # -------------------------
    # Draw the "Change Sound Menu" title
    # -------------------------
    text = "Change Sound Menu"
    text_scale = 1.2
    text_color = (0, 255, 255)
    text_thickness = 3
    text_size = cv2.getTextSize(text, font, text_scale, text_thickness)[0]
    title_x = (width - text_size[0]) // 2
    title_y = (height // 4)  # Position the title roughly at 1/4th of the screen
    cv2.putText(frame, text, (title_x, title_y), font, text_scale, text_color, text_thickness, cv2.LINE_AA)

    # -------------------------
    # Draw a Volume Bar
    # -------------------------
    # Define the dimensions of the volume bar
    bar_width = 500
    bar_height = 50
    bar_x = (width - bar_width) // 2
    bar_y = (height // 2) - (bar_height // 2)

    # Define colors for active and inactive parts
    active_color = (0, 255, 0)    # Green for active volume
    inactive_color = (50, 50, 50) # Dark gray for inactive volume

    # Calculate the filled portion based on volume_level
    filled_width = int((volume_level / 100) * bar_width)

    # Draw the filled volume
    cv2.rectangle(frame, (bar_x, bar_y), (bar_x + filled_width, bar_y + bar_height), active_color, -1)

    # Draw the inactive volume
    cv2.rectangle(frame, (bar_x + filled_width, bar_y), (bar_x + bar_width, bar_y + bar_height), inactive_color, -1)

    # Optional: draw a border around the whole bar
    cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_width, bar_y + bar_height), (255, 255, 255), 2)

    # -------------------------
    # Display Current Volume Level as Text
    # -------------------------
    volume_text = f"Volume: {volume_level}%"
    text_scale = 1.0
    text_thickness = 2
    text_size = cv2.getTextSize(volume_text, font, text_scale, text_thickness)[0]
    text_x = (width - text_size[0]) // 2
    text_y = bar_y + bar_height + 50  # Position below the volume bar
    cv2.putText(frame, volume_text, (text_x, text_y), font, text_scale, (255, 255, 255), text_thickness, cv2.LINE_AA)

    # -------------------------
    # Additional UI elements can go here
    # -------------------------

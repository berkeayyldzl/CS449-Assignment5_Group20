import cv2
import numpy as np

# Global variables
scroll_offset = 0
selected_channel = "No Channel Selected"  # Default selected channel

def open_channels_menu(frame, cursor_position, click_flag, set_current_menu_callback, actions):
    """
    Displays a vertical channels menu with a scrollbar and an exit button.
    Allows selecting channels and displaying the currently selected channel.
    """
    global scroll_offset, selected_channel

    # Dimensions
    height, width, _ = frame.shape
    font = cv2.FONT_HERSHEY_DUPLEX

    # -------------------------
    # Draw the Exit Button
    # -------------------------
    btn_x, btn_y = 20, 20
    btn_w, btn_h = 200, 100
    button_color = (200, 200, 200)  # Light gray background
    hover_color = (0, 255, 0)       # Green highlight on hover
    text_color = (0, 0, 0)          # Black text
    label = "Exit"

    cursor_x, cursor_y = cursor_position
    is_hovered = (btn_x <= cursor_x <= btn_x + btn_w) and (btn_y <= cursor_y - 50 <= btn_y + btn_h)
    color = hover_color if is_hovered else button_color

    cv2.rectangle(frame, (btn_x, btn_y), (btn_x + btn_w, btn_y + btn_h), color, -1)
    text_scale = 1.0
    text_thickness = 2
    text_size = cv2.getTextSize(label, font, text_scale, text_thickness)[0]
    text_x = btn_x + (btn_w - text_size[0]) // 2
    text_y = btn_y + (btn_h + text_size[1]) // 2
    cv2.putText(frame, label, (text_x, text_y), font, text_scale, text_color, text_thickness, cv2.LINE_AA)

    if is_hovered and click_flag:
        set_current_menu_callback(None)
        print("Returned to main menu from Channels Menu")
        return

    # -------------------------
    # Handle Scrolling
    # -------------------------
    total_channels = 20
    visible_channels = 10
    channel_height = 50
    max_offset = total_channels - visible_channels

    if actions.get("scroll-up"):
        scroll_offset = max(scroll_offset - 1, 0)
        print(f"Scroll up: {scroll_offset}")
    if actions.get("scroll-down"):
        scroll_offset = min(scroll_offset + 1, max_offset)
        print(f"Scroll down: {scroll_offset}")

    # -------------------------
    # Draw the Channels List
    # -------------------------
    channels = [f"Channel {i+1}" for i in range(total_channels)]
    list_x, list_y = 300, 150
    list_w, list_h = width - 350, height - 200

    cv2.rectangle(frame, (list_x, list_y), (list_x + list_w, list_y + list_h), (50, 50, 50), -1)

    for i in range(visible_channels):
        channel_index = i + scroll_offset
        if channel_index >= total_channels:
            break

        item_y = list_y + i * channel_height
        channel_label = channels[channel_index]

        # Check if channel is hovered
        is_channel_hovered = (list_x <= cursor_x <= list_x + list_w and
                              item_y <= cursor_y - 50 <= item_y + channel_height)

        color = (0, 255, 0) if is_channel_hovered else (255, 255, 255)
        if is_channel_hovered and click_flag:
            selected_channel = channel_label
            print(f"Selected {channel_label}")

        cv2.putText(frame, channel_label, (list_x + 20, item_y + 35),
                    font, 1.0, color, 2, cv2.LINE_AA)

    # -------------------------
    # Draw the Scrollbar
    # -------------------------
    scrollbar_x = list_x + list_w - 20
    scrollbar_y = list_y
    scrollbar_h = list_h
    scrollbar_w = 10

    scrollbar_handle_h = int((visible_channels / total_channels) * scrollbar_h)
    scrollbar_handle_y = scrollbar_y + int((scroll_offset / max_offset) * (scrollbar_h - scrollbar_handle_h))

    cv2.rectangle(frame, (scrollbar_x, scrollbar_y), (scrollbar_x + scrollbar_w, scrollbar_y + scrollbar_h),
                  (100, 100, 100), -1)
    cv2.rectangle(frame, (scrollbar_x, scrollbar_handle_y),
                  (scrollbar_x + scrollbar_w, scrollbar_handle_y + scrollbar_handle_h),
                  (0, 255, 0), -1)

    # -------------------------
    # Draw the Selected Channel
    # -------------------------
    selected_text = f"Current Channel: {selected_channel}"
    selected_text_scale = 1.0
    selected_text_thickness = 2
    selected_text_size = cv2.getTextSize(selected_text, font, selected_text_scale, selected_text_thickness)[0]
    selected_text_x = (width - selected_text_size[0]) // 2
    selected_text_y = 80
    cv2.putText(frame, selected_text, (selected_text_x, selected_text_y), font, selected_text_scale,
                (0, 255, 255), selected_text_thickness, cv2.LINE_AA)
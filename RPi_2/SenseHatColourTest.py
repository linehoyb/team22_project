from sense_hat import SenseHat
import time

# Initialize the Sense HAT
sense = SenseHat()

# Clear the LED matrix
sense.clear()

# Define colors for each row
colors = [
    (255, 0, 0),    # Red
    (255, 165, 0),  # Orange
    (255, 255, 0),  # Yellow
    (0, 255, 0),    # Green
    (0, 255, 255),  # Cyan
    (0, 0, 255),    # Blue
    (128, 0, 128),  # Purple
    (255, 255, 255) # White
]

try:
    while True:
        # Loop through colors and set each row to a different color
        for i in range(8):
            sense.set_pixels([colors[i]] * 8) # Set each pixel in the row to the corresponding color
            time.sleep(1)

except KeyboardInterrupt:
    # Clear the display and exit when Ctrl+C is pressed
    sense.clear()

#!/usr/bin/env python3
import cv2
import numpy as np
from tqdm import tqdm


def is_similar_image(img1, img2, threshold=0.9):
    """
    Check if two images are similar.

    :param img1: First image array.
    :param img2: Second image array.
    :param threshold: Threshold for similarity (0.9 by default).
    :return: Boolean indicating if images are similar.
    """
    if img1.shape != img2.shape:
        raise AssertionError("Images must have the same shape.")
    similarity = np.sum(img1 == img2) / np.prod(img1.shape)
    return similarity > threshold


def find_loop_point(video_path):
    """
    Find the point in the video where the content starts looping.

    :param video_path: Path to the video file.
    :return: Time in seconds where the loop starts or None if not found.

    Important Considerations:
    - Accuracy: This method might not be highly accurate if the looped content has slight variations
      or if the video quality is low.
    - Performance: The script can be slow for long videos. Consider increasing the interval between
      frames to improve performance, but this may reduce accuracy.
    - Threshold Adjustments: The similarity threshold may need to be adjusted based on specific video content.
    """
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    prev_frame = None

    for frame_index in tqdm(range(total_frames), desc="Analyzing Video"):
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
        ret, frame = cap.read()
        if not ret:
            break

        # Convert frame to grayscale for easier comparison
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        if prev_frame is not None:
            if is_similar_image(gray_frame, prev_frame):
                # Loop detected
                cap.release()
                return frame_index / fps

        prev_frame = gray_frame

    cap.release()
    return None


def main():
    video_path = "C:\\Users\\Krishna\\Videos\\Live Wallpapers\\The Drive.mp4"
    loop_point = find_loop_point(video_path)
    if loop_point is not None:
        print(
            f"Original Duration (before loop starts): {loop_point[0]} seconds and {loop_point[1]} frames"
        )
    else:
        print("No loop detected in the video.")


if __name__ == "__main__":
    main()

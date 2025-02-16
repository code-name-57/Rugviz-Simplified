import cv2
import numpy as np

def apply_rug_to_background(background_image, rug_image, homography_points):
    h_bg, w_bg = background_image.shape[:2]
    h_rug, w_rug = rug_image.shape[:2]

    # Define source and destination points.
    src_pts = np.float32([[0, 0], [w_rug, 0], [w_rug, h_rug], [0, h_rug]])
    dst_pts = np.float32(homography_points)

    # Compute the perspective transform matrix.
    matrix = cv2.getPerspectiveTransform(src_pts, dst_pts)

    # Warp the rug image onto the background canvas.
    warped_rug = cv2.warpPerspective(rug_image, matrix, (w_bg, h_bg))

    # Create a mask representing the destination polygon.
    mask = np.zeros((h_bg, w_bg), dtype=np.uint8)
    cv2.fillConvexPoly(mask, dst_pts.astype(np.int32), 255)
    mask_inv = cv2.bitwise_not(mask)

    # Black-out the area on the background where the rug will be placed.
    background_part = cv2.bitwise_and(background_image, background_image, mask=mask_inv)

    # Extract the rug region using the mask.
    rug_part = cv2.bitwise_and(warped_rug, warped_rug, mask=mask)

    # Combine the background and the warped rug.
    result = cv2.add(background_part, rug_part)
    return result
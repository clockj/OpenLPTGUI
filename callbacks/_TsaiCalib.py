import cv2
import numpy as np
class TsaiCalib:
    
    def __init__(self) -> None:

        pass

    def greet(self):
        print(f"Hello, {self.name}!")
        
        # Define the chessboard size
        chessboard_size = (9, 6)

        # Prepare object points, like (0,0,0), (1,0,0), (2,0,0) ....,(8,5,0)
        object_points = np.zeros((chessboard_size[0] * chessboard_size[1], 3), np.float32)
        object_points[:, :2] = np.mgrid[0:chessboard_size[0], 0:chessboard_size[1]].T.reshape(-1, 2)

        # Arrays to store object points and image points from all the images
        object_points_list = []  # 3D points in real world space
        image_points_list = []  # 2D points in image plane

        # Load images for calibration
        image_paths = ['image1.jpg', 'image2.jpg', 'image3.jpg']  # Replace with your image paths

        for image_path in image_paths:
            # Read the image
            image = cv2.imread(image_path)
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

            # Find chessboard corners
            ret, corners = cv2.findChessboardCorners(gray, chessboard_size, None)

            # If corners are found, add object points and image points
            if ret:
                object_points_list.append(object_points)
                image_points_list.append(corners)

        # Perform camera calibration
        ret, camera_matrix, distortion_coeffs, rvecs, tvecs = cv2.calibrateCamera(
            object_points_list, image_points_list, gray.shape[::-1], None, None
        )

        # Print the camera matrix and distortion coefficients
        print("Camera Matrix:")
        print(camera_matrix)
        print("\nDistortion Coefficients:")
        print(distortion_coeffs)


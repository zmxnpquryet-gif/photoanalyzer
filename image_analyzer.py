import cv2
import numpy as np

def calculate_sharpness(image_path):
    """
    Calculate the variance of the Laplacian, which is a measure of the sharpness of the image.
    Uses cv2.imdecode to safely read paths with unicode/Korean characters.
    """
    try:
        # Avoid cv2.imread for non-ascii paths on Windows
        with open(image_path, "rb") as f:
            chunk = f.read()
        chunk_arr = np.frombuffer(chunk, dtype=np.uint8)
        image = cv2.imdecode(chunk_arr, cv2.IMREAD_GRAYSCALE)
        
        if image is None:
            return 0.0

        # Optional: Resize to speed up calculation if the image is too large
        # we do a fixed resize to make sharpness comparable 
        height, width = image.shape
        if height > 1000 or width > 1000:
            scale = 1000.0 / max(height, width)
            image = cv2.resize(image, (0,0), fx=scale, fy=scale, interpolation=cv2.INTER_AREA)

        variance = cv2.Laplacian(image, cv2.CV_64F).var()
        return variance
    except Exception as e:
        print(f"Error calculating sharpness for {image_path}: {e}")
        return 0.0

def calculate_chromatic_aberration(image_path):
    """
    Estimate sum of absolute differences between channels to determine CA level.
    """
    try:
        with open(image_path, "rb") as f:
            chunk = f.read()
        chunk_arr = np.frombuffer(chunk, dtype=np.uint8)
        image = cv2.imdecode(chunk_arr, cv2.IMREAD_COLOR)

        if image is None:
            return 0.0
            
        height, width, _ = image.shape
        if height > 800 or width > 800:
            scale = 800.0 / max(height, width)
            image = cv2.resize(image, (0,0), fx=scale, fy=scale, interpolation=cv2.INTER_AREA)

        B, G, R = cv2.split(image)
        
        # Calculate Canny edges on Green channel as baseline
        edges_G = cv2.Canny(G, 100, 200)
        
        # Mask channels with edges to see difference only at high contrast areas
        mask_G = edges_G > 0
        diff_B = np.abs(G.astype(np.float32) - B.astype(np.float32))
        diff_R = np.abs(G.astype(np.float32) - R.astype(np.float32))
        
        # Mean difference within edge zones
        ca_score = 0.0
        edge_pixels = np.sum(mask_G)
        if edge_pixels > 0:
            ca_score = (np.sum(diff_B[mask_G]) + np.sum(diff_R[mask_G])) / (2.0 * edge_pixels)
            
        return float(ca_score)
    except Exception as e:
        print(f"Error calculating CA for {image_path}: {e}")
        return 0.0

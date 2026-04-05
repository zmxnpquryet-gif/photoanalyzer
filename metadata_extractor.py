import os
from pathlib import Path
import exifread
import pandas as pd

def parse_fraction(value_str):
    try:
        parts = value_str.split('/')
        if len(parts) == 1:
            return float(parts[0])
        elif len(parts) == 2:
            return float(parts[0]) / float(parts[1]) if float(parts[1]) != 0 else 0
    except ValueError:
        return None
    return None

def extract_metadata_from_file(filepath):
    metadata = {
        'filepath': str(filepath),
        'filename': os.path.basename(filepath),
        'focal_length': None,
        'aperture': None,
        'shutter_speed': None,
        'iso': None,
        'camera_model': None,
        'lens_model': None,
        'resolution': None,
    }
    
    try:
        with open(filepath, 'rb') as f:
            tags = exifread.process_file(f, details=False)
            
            # Focal Length
            if 'EXIF FocalLength' in tags:
                metadata['focal_length'] = parse_fraction(str(tags['EXIF FocalLength']))
            
            # Aperture
            if 'EXIF FNumber' in tags:
                metadata['aperture'] = parse_fraction(str(tags['EXIF FNumber']))
                
            # Shutter Speed (Exposure Time)
            if 'EXIF ExposureTime' in tags:
                val = str(tags['EXIF ExposureTime'])
                # Store as string for shutter speed if fraction, float if decimal
                metadata['shutter_speed'] = val
            
            # ISO
            # Check ISO speed ratings
            if 'EXIF ISOSpeedRatings' in tags:
                try:
                    metadata['iso'] = int(str(tags['EXIF ISOSpeedRatings']))
                except ValueError:
                    pass
            
            # Camera Model
            if 'Image Model' in tags:
                metadata['camera_model'] = str(tags['Image Model']).strip()
                
            # Lens Model
            if 'EXIF LensModel' in tags:
                metadata['lens_model'] = str(tags['EXIF LensModel']).strip()
                
            # Resolution
            width = tags.get('EXIF ExifImageWidth')
            length = tags.get('EXIF ExifImageLength')
            if not width or not length:
                width = tags.get('Image ImageWidth')
                length = tags.get('Image ImageLength')
                
            if width and length:
                w_val = int(str(width))
                h_val = int(str(length))
                # Store string representation 
                metadata['resolution'] = f"{w_val}x{h_val}"
                
    except Exception as e:
        print(f"Error parsing EXIF for {filepath}: {e}")
        
    return metadata

def extract_metadata_from_directory(directory_path, progress_callback=None):
    valid_extensions = {'.jpg', '.jpeg', '.png', '.tiff', '.tif'}
    results = []
    
    path = Path(directory_path)
    if not path.exists() or not path.is_dir():
        return pd.DataFrame()
        
    image_files = []
    for ext in valid_extensions:
        image_files.extend(path.rglob(f"*{ext}"))
        image_files.extend(path.rglob(f"*{ext.upper()}"))
        
    total_files = len(image_files)
    
    for i, filepath in enumerate(image_files):
        meta = extract_metadata_from_file(filepath)
        results.append(meta)
        if progress_callback:
            progress_callback(int((i + 1) / total_files * 100))
            
    df = pd.DataFrame(results)
    return df

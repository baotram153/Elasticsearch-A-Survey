import pydicom
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import os
from io import BytesIO
from PIL import Image

from helpers.constants import KW_NAME_DICT
from typing import List

def get_metadata(dicom: pydicom.Dataset) -> dict:
    pass    

def load_from_dir(dir_path: Path):
    """Load all DICOM IMA files from a directory."""
    for series_dir in sorted(os.listdir(dir_path)):
        if os.path.isdir(os.path.join(dir_path, series_dir)):
            for localizer_series in sorted(os.listdir(os.path.join(dir_path, series_dir))):
                if os.path.isdir(os.path.join(dir_path, series_dir, localizer_series)):
                    for file in os.listdir(os.path.join(dir_path, series_dir, localizer_series)):
                        if file.endswith((".ima", ".dcm")):
                            dicom = load_dicom(os.path.join(dir_path, series_dir, localizer_series, file))
                            # logic to read info from dicom to es
                            pass

def load_dicom(path: Path) -> np.ndarray:
    """Load a DICOM IMA file and return the pixel array as a NumPy array."""
    dicom = pydicom.dcmread(path)
    return dicom

def list_keywords(dicom: pydicom.Dataset):
    for elem in dicom:
        print(f"{elem.name:30s}: {elem.value}")

def dicom_to_array(dicom: pydicom.Dataset) -> np.ndarray:
    """Convert DICOM pixel data to a NumPy array."""
    return dicom.pixel_array

def show_dicom(dicom: pydicom.Dataset):
    """Display the DICOM image using matplotlib."""
    img = dicom_to_array(dicom)
    plt.imshow(img, cmap="gray")
    plt.title("DICOM Image")
    plt.show()
    
def get_metadata(dicom: pydicom.Dataset) -> dict:
    """Extract metadata from a DICOM file."""
    metadata = {}
    for key in KW_NAME_DICT.keys():
        default = KW_NAME_DICT[key][1] if isinstance(KW_NAME_DICT[key], List) else None
        metadata[key] = dicom.get(key, default)
    return metadata
    
def get_kw_name_dict(dicom: pydicom.Dataset) -> dict:
    """Get a dictionary of keyword names and their values from a DICOM file."""
    kw_name_dict = {}
    for elem in dicom:
        kw_name_dict[elem.keyword] = elem.name
    return kw_name_dict

def dicom_to_png_bytes(dicom: pydicom.Dataset) -> bytes:
    arr = dicom.pixel_array.astype(np.float32)
    arr_min, arr_max = arr.min(), arr.max()
    if arr_max > arr_min:
        arr = (arr - arr_min) / (arr_max - arr_min) * 255.0     # normalize image to [0, 255]
    arr = arr.astype(np.uint8)
    img = Image.fromarray(arr)
    if img.mode != "L":
        img = img.convert("L")
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer.getvalue()

if __name__ == "__main__":
    # dicom = load_dicom(Path("0215\L-SPINE_CLINICAL_LIBRARIES_20160530_125557_550000\LOCALIZER_0002\LOCALIZER_0_0215_002.ima"))
    # dicom = load_dicom(Path("0215\L-SPINE_CLINICAL_LIBRARIES_20160530_125557_550000\LOCALIZER_0001\LOCALIZER_0_0215_001.ima"))
    # dicom = load_dicom(Path("0215\L-SPINE_CLINICAL_LIBRARIES_20160530_131017_168000\POSDISP_[4]_T2_TSE_TRA_384_5001\POSDISP_[4]_0215_001.ima"))
    dicom = load_dicom(Path("images/0046/C-SPINE_C-SPINE_20160204_102511_459000/LOCALIZER_0001/LOCALIZER_0_0046_003.ima"))
    print(dicom['PatientID'])
    print(np.min(dicom.pixel_array), np.max(dicom.pixel_array))
    print(dicom['BitsStored'])
    print(dicom['PixelData'])
    print(f"Keys: {len(dict(dicom).keys())}")
    # plt.imshow(dicom.pixel_array, cmap="gray")
    # plt.show()
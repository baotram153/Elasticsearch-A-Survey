from ima_loader import load_dicom, dicom_to_array
from base64 import b64encode
from models import BaseEmbedder, ResNet50Embedder
import numpy as np

def check_image_embedding(dicom_path, model: BaseEmbedder):
    inputs = []
    dicom = load_dicom(dicom_path)
    img_array = dicom_to_array(dicom)
    print("Original image shape:", img_array.shape)
    inputs.append(img_array)

    embedding = model.embed(inputs)
    print(f"Embedding shape: {embedding.shape}, Embedding: {embedding}")
    
    encoding_str = b64encode(embedding.numpy().astype(np.float32).tobytes()).decode('utf-8')
    print(f"Encoding string length: {len(encoding_str)}, Encoding string (first 100 chars): {encoding_str[:100]}")
    return embedding

if __name__ == "__main__":
    model = ResNet50Embedder()
    check_image_embedding("images/0215/L-SPINE_CLINICAL_LIBRARIES_20160530_125557_550000/LOCALIZER_0001/LOCALIZER_0_0215_001.ima", model)
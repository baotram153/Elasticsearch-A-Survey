"""
Upload all items recursively in a local directory to an Azure Blob Storage container.
"""

import os
from azure.storage.blob import BlobServiceClient, ContainerClient
from azure.core.exceptions import ResourceExistsError
from dotenv import load_dotenv
import requests

from matplotlib import pyplot as plt
from PIL import Image
from io import BytesIO

import sys
sys.path.append("D:\Bachelor\Curriculum\HK251\DBMS\elastic-search")

from helpers.ima_loader import load_dicom, show_dicom, dicom_to_png_bytes

class AzureHelper:
    def __init__(self, connection_string: str, container_name: str):
        self.blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        self.container_client = self.blob_service_client.get_container_client(container_name
                                                                              )
    # get azure blob client
    def get_blob_service_client(self) -> BlobServiceClient:
        return self.blob_service_client

    # get azure container client
    def get_container_client(self) -> ContainerClient:
        return self.container_client
    
    # change container client
    def change_container_client(self, container_name: str):
        self.container_client = self.blob_service_client.get_container_client(container_name)

    def upload_dicom_to_container(self, local_directory: str):
        for root, _, files in os.walk(local_directory):
            for file in files:
                file_path = os.path.join(root, file)
                blob_path = os.path.relpath(file_path, local_directory).replace("\\", "/")
                try:
                    with open(file_path, "rb") as data:
                        self.container_client.upload_blob(name=blob_path, data=data)
                    print(f"Uploaded {file_path} to {blob_path}")
                except ResourceExistsError:
                    print(f"Blob {blob_path} already exists. Skipping upload.")
                
    # load dicom from link to azure blob
    def load_dicom_from_blob_relpath(self, blob_path: str):
        blob_client = self.container_client.get_blob_client(blob_path)
        downloader = blob_client.download_blob()
        dicom_data = downloader.readall()
        
        # save to temp file
        os.makedirs(os.path.dirname(blob_path), exist_ok=True)
        temp_path = blob_path
        with open(temp_path, "wb") as f:
            f.write(dicom_data)
        
        dicom = load_dicom(temp_path)
        print(f"Patient's age: {dicom['PatientAge']}")
        show_dicom(dicom)
        
        # remove temp file
        os.remove(temp_path)
        
    def load_dicom_from_url(self, url: str):
        response = requests.get(url)
        if response.status_code == 200:
            dicom_data = response.content
            temp_path = "/".join(url.split("/")[3:])
            os.makedirs(os.path.dirname(temp_path), exist_ok=True)
            with open(temp_path, "wb") as f:
                f.write(dicom_data)
            dicom = load_dicom(temp_path)
            print(f"Patient's age: {dicom['PatientAge']}")
            show_dicom(dicom)
            os.remove(temp_path)
        else:
            print(f"Failed to download DICOM file. Status code: {response.status_code}")
            
    def load_image_from_url(self, url: str):
        response = requests.get(url)
        if response.status_code == 200:
            img = Image.open(BytesIO(response.content))
            return img
        else:
            print(f"Failed to download image file. Status code: {response.status_code}")
            
    def upload_img_to_container(self, local_directory: str):
        for root, _, files in os.walk(local_directory):
            for idx, file in enumerate(files):
                file_path = os.path.join(root, file)
                blob_path = os.path.relpath(file_path, local_directory).replace("\\", "/").replace(".ima", ".png")
                try:
                    dicom = load_dicom(file_path)
                    img = dicom_to_png_bytes(dicom)
                    self.container_client.upload_blob(name=blob_path, data=img)
                    if idx % 10 == 0:
                        print(f"Uploaded {file_path} to {blob_path}")
                except ResourceExistsError:
                    print(f"Blob {blob_path} already exists. Skipping upload.")

    def get_azure_blob_url(self, blob_path: str) -> str:
        blob_client = self.container_client.get_blob_client(blob_path)
        return blob_client.url
    
    def show_images_from_response(self, response, image_field='image_link', size=(4,4)):
        hits = response['hits']['hits']
        imgs = []
        for hit in hits:
            source = hit['_source']
            if image_field in source:
                img_link = source[image_field]
                if isinstance(img_link, str):
                    # assume base64 encoded
                    imgs.append(self.load_image_from_url(img_link))
                elif isinstance(img_link, list):
                    imgs.extend([self.load_image_from_url(link) for link in img_link])
                else:
                    print("Unknown image data format")
                    continue
            else:
                raise ValueError(f"Field '{image_field}' not found in document source")
        
        # for img in imgs:
        #     plt.figure(figsize=size)
        #     plt.imshow(img, cmap='gray')
        #     plt.axis('off')
        #     plt.show()
        n = len(imgs)
        cols = 4
        rows = (n + cols - 1) // cols

        fig, axes = plt.subplots(rows, cols, figsize=(4*cols, 4*rows))  # scale here
        axes = axes.flatten()

        for ax, img in zip(axes, imgs):
            ax.imshow(img, cmap='gray')
            ax.axis('off')
        
                    
        
if __name__ == "__main__":
    load_dotenv()
    
    # local_directory = "images/0001"
    connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    container_name = os.getenv("AZURE_BLOB_STORAGE_CONTAINER_NAME")
    azure_helper = AzureHelper(connection_string, container_name)
    
    # local directory
    local_dir = "images"
    azure_helper.upload_img_to_container(local_dir)
    
    # azure_link = "https://esimagedatastorage.blob.core.windows.net/mri-images/L-SPINE_LSS_20160309_091629_240000/LOCALIZER_0001/LOCALIZER_0_0001_001.ima"
    # blob_relpath = "L-SPINE_LSS_20160309_091629_240000/LOCALIZER_0001/LOCALIZER_0_0001_001.ima"
    # azure_helper.load_dicom_from_blob_relpath(blob_relpath)
    # azure_helper.load_dicom_from_url(azure_link)
import PIL
import elasticsearch as es
from elasticsearch import Elasticsearch
import os
from pprint import pprint
from io import BytesIO
from PIL import Image

from helpers.ima_loader import load_dicom, dicom_to_array, get_metadata
from base64 import b64encode

from helpers.azure_helper import AzureHelper
from helpers.data_processor import read_diagnosis_data

import numpy as np

from pydicom.valuerep import DSfloat, IS, PersonName
from pydicom.uid import UID
from pydicom.multival import MultiValue

class ESHelper:
    def __init__(self, es_client: Elasticsearch, index="my-idx", delete_old_idx=False):
        self.es_client = es_client
        self.index = index
        self.delete_old_idx = delete_old_idx
        if delete_old_idx:
            self.es_client.indices.delete(index=self.index, ignore=[404])  # ignore not found
        self.check_idx_exists()
    def ping(self):
        return self.es_client.ping()
        
    def check_idx_exists(self): 
        if not self.es_client.indices.exists(index=self.index):
            self.es_client.indices.create(index=self.index)
            
    def get_index_info(self):
        res = self.es_client.search(index=self.index, body={"query": {"match_all": {}}}, size=1)
        if res['hits']['total']['value'] > 0:
            print("First document:")
            pprint(res['hits']['hits'][0]['_source'])
            
        # total = self._get_total_docs_num()
        # print(f"Index '{self.index}' contains {total} documents.")
        
        count = self.es_client.count(index=self.index, body={
            "query": {"match_all": {}}
        })
        
        print(f"Total number of docs in index: {count['count']}")
    
    def _get_total_docs_num(self):
        # used to learn about deep paging
        # enable sort on _id 
        self.es_client.cluster.put_settings(
            body={
                "transient": {
                    "indices.id_field_data.enabled": True
                }
            }
        )
        res = self.es_client.search(
            index=self.index,
            body={
                "query": {"match_all": {}},
                "sort": [{"_id": "asc"}],
            },
            size=1000,
        )
        hits = res['hits']['hits']
        total_docs = res['hits']['total']['value']
        while hits:
            last_sort = hits[-1]["sort"]
            res = self.es_client.search(
                index=self.index,
                body={
                    "query": {"match_all": {}},
                    "sort": [{"_id": "asc"}]
                },
                size=1000,
                search_after=last_sort
                
            )
            n_docs = res['hits']['total']['value']
            total_docs += n_docs
            print(f"Retrieved {total_docs} documents so far...")
        return total_docs
            
    
    def _to_native(self, o):
        if isinstance(o, (str, int, float, bool)) or o is None:
            return o
        if isinstance(o, np.integer):
            return int(o)
        if isinstance(o, np.floating):
            return float(o)
        if isinstance(o, (list, tuple, MultiValue)):
            return [self._to_native(x) for x in o]
        if isinstance(o, dict):
            return {str(k): self._to_native(v) for k, v in o.items()}
        if isinstance(o, DSfloat):
            return float(o)
        if isinstance(o, IS):
            return int(o)
        if isinstance(o, (UID, PersonName)):
            return str(o)
        # last resort
        try:
            return o.item()
        except Exception:
            return str(o)

    def save_single_img_to_es(self, img, metadata: dict = {}, link: str = None):
        # convert any numpy arrays in metadata to lists for JSON serialization
        sanitized_metadata = self._to_native(metadata)
        doc = {
            "image": img,
            **sanitized_metadata
        }
        if link:
            doc["image_link"] = link
        try:
            self.es_client.index(index=self.index, body=doc)
            return True
        except Exception as e:
            print(f"Error indexing document: {e}")
            return False
        
    def update_img_link_in_es(self, dicom_path: str, new_link: str):
        dicom = load_dicom(dicom_path)
        sop_instance_uid = dicom['SOPInstanceUID'].value
        self.es_client.update_by_query(
            index=self.index,
            body={
                "script": {
                    "source": "ctx._source['image_link'] = params.new_link",
                    "params": {
                        "new_link": new_link
                    }
                },
                "query": {
                    "term": {
                        "SOPInstanceUID.keyword": sop_instance_uid  # compare as is, not tokenized
                    }
                }
            }
        )
        
    def get_index_mapping(self):
        mapping = self.es_client.indices.get_mapping(index=self.index)
        return mapping["images"]["mappings"]["properties"]
    
    def encode_image_to_base64(self, image) -> str:
        buffered = BytesIO()
        image.save(buffered, format="JPEG")
        img_bytes = buffered.getvalue()
        img_base64 = b64encode(img_bytes).decode('utf-8')
        return img_base64

    def from_folder_to_es(self, img_folder: str, diagnosis_path: str, mode='embed', azure_helper: AzureHelper = None, model=None):
        """
        Modes include:
        - 'embed': use model to generate embeddings and store them in ES
        - 'link': store a link to the image in ES
        - 'raw': store raw images in ES
        """
        radiologist_notes = read_diagnosis_data(diagnosis_path)
        count = 0
        print(f"Processing folder: {img_folder}")
        for series_dir in sorted(os.listdir(img_folder)):
            print(f"Reading folder: {series_dir}")
            series_path = os.path.join(img_folder, series_dir)
            if os.path.isdir(series_path):
                for session in sorted(os.listdir(series_path)):
                    session_path = os.path.join(series_path, session)
                    if os.path.isdir(session_path):
                        for localizer_series in sorted(os.listdir(session_path)):
                            localizer_path = os.path.join(session_path, localizer_series)
                            if os.path.isdir(localizer_path):
                                for file in os.listdir(localizer_path):
                                    count += 1
                                    if file.endswith((".ima", ".dcm")):
                                        dicom = load_dicom(os.path.join(localizer_path, file))
                                        img = dicom_to_array(dicom)
                                        metadata = get_metadata(dicom)
                                        
                                        if mode == 'embed':
                                            # save embedding from model output
                                            assert model is not None, "Model must be provided for embedding mode"
                                            embedding = model.embed([img])
                                            # encoding_str = b64encode(embedding.numpy().astype(np.float32).tobytes()).decode('utf-8')
                                            # img = encoding_str
                                            link = azure_helper.get_azure_blob_url(f"{series_dir}/{session}/{localizer_series}/{file.replace('.ima', '.png').replace('.dcm', '.png')}")
                                            img = list(embedding.squeeze().numpy().astype(np.float32))
                                        if mode == 'link':
                                            # save link to storage
                                            link = azure_helper.get_azure_blob_url(f"{series_dir}/{session}/{localizer_series}/{file.replace('.ima', '.png').replace('.dcm', '.png')}")
                                            img = link
                                        if mode == 'raw':
                                            # save encoding string of image
                                            img = self.encode_image_to_base64(Image.fromarray(img.astype(np.uint8)))
                                            link = None
                                        self.save_single_img_to_es(img, metadata, link)
                                        if (count % 1000 == 0): print(f"Image idx {count} saved to ES")                        
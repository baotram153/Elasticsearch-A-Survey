from torchvision.models import resnet50, ResNet50_Weights
print("Torchvision loaded")
import numpy as np

import torch, torch.nn as nn
print("Torch loaded")
import torchvision.transforms as T
print("Transforms loaded")
from PIL import Image
import timm
print("Timm loaded")
# from transformers import AutoProcessor, AutoModel

def _device():
    return "cuda" if torch.cuda.is_available() else "cpu"

def _norm(x):  # L2 normalize
    return x / (x.norm(dim=-1, keepdim=True) + 1e-12)

class BaseEmbedder:
    def __init__(self, size=224):
        self.device = _device()
        self.transform = T.Compose([
            T.Resize(size, interpolation=T.InterpolationMode.BICUBIC),
            T.CenterCrop(size),
            T.ToTensor(),
            T.Normalize(mean=(0.485,0.456,0.406), std=(0.229,0.224,0.225)), # mean and std of ImageNet dataset
        ])
        self.model = None
        self.dim = None

    @torch.no_grad()
    def embed(self, images, batch_size=64, fp16=True):
        if type(images[0]) is not Image.Image:
            # grayscale to RGB
            images = [Image.fromarray(np.uint8(img)).convert("RGB") for img in images]
        # if images[0].ndim == 2:
        #     images = [img.unsqueeze(0).repeat(3,1,1) for img in images]
        self.model.eval()
        dev = self.device
        out = []
        for i in range(0, len(images), batch_size):
            batch = images[i:i+batch_size]
            px = torch.stack([self.transform(img) for img in batch]).to(dev)   # (B, 3, H, W)
            with torch.amp.autocast("cuda", enabled=fp16 and dev=="cuda"):
                feats = self.forward_pixels(px)  # (B, D)
            out.append(feats)
        x = torch.cat(out, dim=0)
        return _norm(x).cpu()

    def forward_pixels(self, px):  # override
        raise NotImplementedError

# CNN model
class ResNet50Embedder(BaseEmbedder):
    def __init__(self):
        super().__init__(size=224)
        m = resnet50(weights=ResNet50_Weights.IMAGENET1K_V2)
        print(m)
        self.dim = 2048
        self.model = nn.Sequential(*list(m.children())[:-1])  # pool layer output (B, 2048, 1, 1)
        self.model.to(self.device)

    def forward_pixels(self, px):
        x = self.model(px)           # (B, 2048, 1, 1)
        return x.squeeze(-1).squeeze(-1)  # (B, 2048)
    
# Transformer
class ViT_B16_Embedder(BaseEmbedder):
    def __init__(self):
        super().__init__(size=224)
        self.model = timm.create_model("vit_base_patch16_224", pretrained=True, num_classes=0, global_pool="avg")
        self.dim = self.model.num_features
        self.model.to(self.device)

    def forward_pixels(self, px):
        return self.model(px)  # (B, D)
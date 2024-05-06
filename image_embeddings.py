import torch
import clip
from PIL import Image
import os
import certifi

os.environ["SSL_CERT_FILE"] = certifi.where()


def extract_feature_vector(image_path):
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model, preprocess = clip.load("ViT-B/32", device=device)

    image = preprocess(Image.open(image_path)).unsqueeze(0).to(device)

    with torch.no_grad():
        feature_vector = model.encode_image(image)

    return feature_vector.cpu().numpy()


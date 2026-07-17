import os
import json
import torch
import torch.nn as nn
# pyrefly: ignore [missing-import]
from torchvision import transforms
from PIL import Image
# pyrefly: ignore [missing-import]
import timm

from config import MODEL_PATH, CLASS_NAMES_PATH, IMAGE_SIZE, IMAGENET_MEAN, IMAGENET_STD

# ==========================================
# DEVICE DETECTION
# ==========================================
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# ==========================================
# CLASS NAMES
# ==========================================
# We load class names if available, else we provide dummy placeholders
if os.path.exists(CLASS_NAMES_PATH):
    with open(CLASS_NAMES_PATH, "r") as f:
        class_names = json.load(f)
else:
    # A dummy list to avoid breaking if class_names.json is missing initially
    class_names = [f"Class_{i}" for i in range(1000)]

# ==========================================
# MODEL ARCHITECTURE
# ==========================================
class ConvolutionalNetwork(nn.Module):
    def __init__(self, num_classes):
        super().__init__()
        self.base_model = timm.create_model(
            "resnet18",
            pretrained=False, # Changed to False because HuggingFace is returning a 504 error, and you will load your own weights anyway
            num_classes=num_classes
        )

    def forward(self, x):
        return self.base_model(x)

# ==========================================
# MODEL LOADING
# ==========================================
num_classes = len(class_names)
model = ConvolutionalNetwork(num_classes)

# ==========================================
# AUTO-DOWNLOAD MODEL FROM HF HUB IF MISSING
# ==========================================
if not os.path.exists(MODEL_PATH):
    print("Model weights not found locally. Attempting to download from Hugging Face Hub...")
    try:
        from huggingface_hub import hf_hub_download
        downloaded_path = hf_hub_download(
            repo_id="aryansoni20/PlantCare-AI-model",
            filename="plant_disease_resnet18.pth",
            local_dir=os.path.dirname(MODEL_PATH)
        )
        print(f"Model downloaded to {downloaded_path}")
    except Exception as e:
        print(f"WARNING: Could not download model from HF Hub: {e}")

if os.path.exists(MODEL_PATH):
    try:
        model.load_state_dict(torch.load(MODEL_PATH, map_location=device))
        print(f"Model successfully loaded from {MODEL_PATH}")
    except Exception as e:
        print(f"Error loading model weights: {e}")
else:
    print(f"WARNING: Model weights not found at {MODEL_PATH}. Using untrained model weights for now.")

model.to(device)
model.eval()

# ==========================================
# IMAGE PREPROCESSING
# ==========================================
transform = transforms.Compose([
    transforms.Resize(IMAGE_SIZE),
    transforms.CenterCrop(IMAGE_SIZE),
    transforms.ToTensor(),
    transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD)
])

# ==========================================
# PREDICTION FUNCTION
# ==========================================
def predict_disease(image_path: str, original_filename: str = ""):
    """
    Predict plant leaf disease using the loaded PyTorch model.
    Reads the image, converts to RGB, applies transformations,
    predicts, applies softmax, and returns JSON structure.
    """
    try:
        img = Image.open(image_path).convert("RGB")
    except Exception as e:
        raise ValueError(f"Invalid image file: {e}")
        
    img_tensor = transform(img).unsqueeze(0).to(device)
    
    with torch.no_grad():
        outputs = model(img_tensor)
        probabilities = torch.nn.functional.softmax(outputs, dim=1)[0]
        
    # Get top 5 predictions
    # k is min(5, num_classes) in case there are fewer than 5 classes
    k = min(5, num_classes)
    topk_prob, topk_indices = torch.topk(probabilities, k)
    
    top5 = []
    for i in range(k):
        idx = topk_indices[i].item()
        prob = float(topk_prob[i].item()) # Keep as 0-1 float for the UI math
        
        raw_cls_name = class_names[idx] if idx < len(class_names) else f"Unknown_Class_{idx}"
        # Format "Potato___healthy" to "Potato - Healthy"
        cls_name = raw_cls_name.replace("___", " - ").replace("__", " - ").replace("_", " ")
        
        top5.append({
            "class": cls_name,
            "confidence": prob
        })
        
    # Ensure there's always a return structure even if k < 1 (which shouldn't happen)
    prediction = top5[0]["class"] if top5 else "Unknown"
    confidence = top5[0]["confidence"] if top5 else 0.0
    
    is_healthy = "healthy" in prediction.lower()
    severity = "Low" if is_healthy else "High"
    
    return {
        "disease": prediction,
        "is_healthy": is_healthy,
        "severity": severity,
        "confidence": confidence,
        "top_5": top5
    }

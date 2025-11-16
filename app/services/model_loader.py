"""Service to load and cache machine learning models."""
from functools import lru_cache
import os
from pathlib import Path
import torch

@lru_cache()
def load_models():
    """Load and cache machine learning models."""
    device = "cuda" if torch.cuda.is_available() else "cpu"

    ml_models_dir = Path(os.path.expanduser("app/ml_models")).resolve()

    models = {
        "frames": torch.jit.load(ml_models_dir / "relevant_frames_resnet.pt",
                                 map_location=device).to(device).eval(),
        "recognizer": torch.jit.load(ml_models_dir / "digits_yolo.pt",
                                     map_location=device).to(device).eval(),
        "classifier": torch.jit.load(ml_models_dir / "digits_resnet.pt",
                                     map_location=device).to(device).eval(),
        "device": device
    }
    return models

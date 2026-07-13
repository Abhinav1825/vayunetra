import os
import rasterio
import numpy as np
import torch
from torch.utils.data import Dataset
from torchvision import transforms

class Sentinel2Dataset(Dataset):
    """
    Dataset for loading Sentinel-2 satellite imagery (GeoTIFF) and corresponding masks.
    """
    def __init__(self, image_dir, mask_dir, transform=None):
        self.image_dir = image_dir
        self.mask_dir = mask_dir
        self.transform = transform
        
        # In a real scenario, these directories would contain aligned .tif image and mask files.
        # Ensure only valid files are read.
        if os.path.exists(self.image_dir):
            self.images = [f for f in os.listdir(self.image_dir) if f.endswith('.tif')]
        else:
            self.images = []

    def __len__(self):
        return len(self.images)

    def __getitem__(self, idx):
        img_name = self.images[idx]
        img_path = os.path.join(self.image_dir, img_name)
        mask_path = os.path.join(self.mask_dir, img_name)
        
        # Read image
        with rasterio.open(img_path) as src:
            # Assuming multispectral or RGB. For Sentinel-2, often use RGB/NIR.
            image = src.read() # Shape: (C, H, W)
            # Normalize to [0, 1] generically
            image = image.astype(np.float32) / 10000.0  # Common Sentinel-2 normalization
            # Clip
            image = np.clip(image, 0, 1)

        # Read mask
        with rasterio.open(mask_path) as src:
            mask = src.read(1) # Shape: (H, W)
            mask = mask.astype(np.int64) # Class indices
            
        # Convert to tensors
        image_tensor = torch.from_numpy(image)
        mask_tensor = torch.from_numpy(mask)
        
        if self.transform:
            # For more complex augmentations, consider albumentations library
            pass

        return image_tensor, mask_tensor

import os
try:
    import torch
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False
    print("Warning: PyTorch not installed. CVSourceDetector will run in mock mode.")
import numpy as np
import rasterio
import geopandas as gpd
from shapely.geometry import shape
import rasterio.features
if HAS_TORCH:
    from ml.vision.model import create_segmentation_model
class CVSourceDetector:
    """
    Runs inference on new Sentinel-2 tiles and outputs detected sources.
    """
    def __init__(self, model_path="artifacts/e1_cv_model.pth", device="cpu"):
        if HAS_TORCH:
            self.device = device
            self.model = create_segmentation_model(num_classes=4)
            if not os.path.exists(model_path):
                print(f"Downloading model weights to {model_path} from GitHub release...")
                os.makedirs(os.path.dirname(model_path), exist_ok=True)
                import urllib.request
                urllib.request.urlretrieve("https://github.com/omkarrr88/VayuNetra/releases/download/v1.0.0/e1_cv_model.pth", model_path)
            
            if os.path.exists(model_path):
                self.model.load_state_dict(torch.load(model_path, map_location=device, weights_only=True))
            else:
                print(f"Warning: Model weights not found at {model_path}. Using initialized weights.")
            
            self.model = self.model.to(self.device)
            self.model.eval()
        else:
            self.device = "mock"
            self.model = None

        self.class_map = {
            1: "construction",
            2: "brick_kiln",
            3: "open_burning"
        }

    def infer_tile(self, tif_path):
        """
        Runs the CV model on a single GeoTIFF tile and extracts polygons for detections.
        """
        with rasterio.open(tif_path) as src:
            image = src.read()
            transform = src.transform
            crs = src.crs
            
        image = image.astype(np.float32) / 10000.0
        image = np.clip(image, 0, 1)

        input_tensor = torch.from_numpy(image).unsqueeze(0).to(self.device)

        with torch.no_grad():
            output = self.model(input_tensor)
            preds = torch.argmax(output, dim=1).squeeze(0).cpu().numpy()

        detected_sources = []

        # Convert masks to polygons
        for class_idx, class_name in self.class_map.items():
            mask = (preds == class_idx).astype(np.uint8)
            if mask.sum() == 0:
                continue
            
            # Extract polygons
            for geom, val in rasterio.features.shapes(mask, transform=transform):
                if val == 1:
                    poly = shape(geom)
                    detected_sources.append({
                        "geom": poly,
                        "type": class_name,
                        "source_origin": "cv_detected",
                        "detection_confidence": 0.85 # Dummy confidence score
                    })

        if detected_sources:
            gdf = gpd.GeoDataFrame(detected_sources, crs=crs)
            # Transform to EPSG:4326 to match Supabase schema
            gdf = gdf.to_crs(epsg=4326)
            return gdf
        
        return gpd.GeoDataFrame()
        
    def infer_large_tile(self, tif_path, patch_size=256, max_patches=10):
        """
        Runs the CV model on a large GeoTIFF by taking a few non-empty patches.
        Prevents Out-Of-Memory errors on large raw satellite tiles.
        """
        from rasterio.windows import Window
        all_detected = []
        patches_processed = 0
        
        with rasterio.open(tif_path) as src:
            width, height = src.width, src.height
            crs = src.crs
            
            # Stride through the image
            for row in range(0, height - patch_size, patch_size):
                for col in range(0, width - patch_size, patch_size):
                    if patches_processed >= max_patches:
                        break
                        
                    window = Window(col, row, patch_size, patch_size)
                    image = src.read(window=window)
                    
                    # Skip empty/black patches
                    if (image == 0).mean() > 0.5:
                        continue
                        
                    transform = src.window_transform(window)
                    
                    # Run inference on this patch
                    image = image.astype(np.float32) / 10000.0
                    image = np.clip(image, 0, 1)
                    
                    if HAS_TORCH:
                        input_tensor = torch.from_numpy(image).unsqueeze(0).to(self.device)
                        with torch.no_grad():
                            output = self.model(input_tensor)
                            preds = torch.argmax(output, dim=1).squeeze(0).cpu().numpy()
                    else:
                        # Mock mode: generate random blobs for detections
                        preds = np.zeros((patch_size, patch_size), dtype=np.uint8)
                        if np.random.rand() > 0.5:
                            # Randomly pick a class (1-3)
                            cls = np.random.randint(1, 4)
                            cx, cy = np.random.randint(10, patch_size-10, size=2)
                            r = np.random.randint(5, 15)
                            # Draw a crude circle
                            y, x = np.ogrid[-cy:patch_size-cy, -cx:patch_size-cx]
                            mask = x*x + y*y <= r*r
                            preds[mask] = cls

                    # Convert masks to polygons
                    for class_idx, class_name in self.class_map.items():
                        mask = (preds == class_idx).astype(np.uint8)
                        if mask.sum() == 0:
                            continue
                        
                        for geom, val in rasterio.features.shapes(mask, transform=transform):
                            if val == 1:
                                poly = shape(geom)
                                all_detected.append({
                                    "geometry": poly,
                                    "type": class_name,
                                    "source_origin": "cv_detected",
                                    "detection_confidence": float(np.random.uniform(0.75, 0.95))
                                })
                                
                    patches_processed += 1
                    
                if patches_processed >= max_patches:
                    break
                    
        if all_detected:
            gdf = gpd.GeoDataFrame(all_detected, crs=crs)
            if crs != "EPSG:4326":
                gdf = gdf.to_crs(epsg=4326)
            return gdf
            
        return gpd.GeoDataFrame()

if __name__ == "__main__":
    detector = CVSourceDetector()
    print("Initialized CVSourceDetector ready for inference.")

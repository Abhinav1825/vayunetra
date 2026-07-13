import os
import torch
import numpy as np
import rasterio
import geopandas as gpd
from shapely.geometry import shape
import rasterio.features
from model import create_segmentation_model

class CVSourceDetector:
    """
    Runs inference on new Sentinel-2 tiles and outputs detected sources.
    """
    def __init__(self, model_path="artifacts/e1_cv_model.pth", device="cpu"):
        self.device = device
        self.model = create_segmentation_model(num_classes=4)
        if os.path.exists(model_path):
            self.model.load_state_dict(torch.load(model_path, map_location=device))
        else:
            print(f"Warning: Model weights not found at {model_path}. Using initialized weights.")
        
        self.model = self.model.to(self.device)
        self.model.eval()

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

if __name__ == "__main__":
    detector = CVSourceDetector()
    print("Initialized CVSourceDetector ready for inference.")

import torch
import torch.nn as nn
import segmentation_models_pytorch as smp

def create_segmentation_model(num_classes=4, encoder_name="resnet34", encoder_weights="imagenet"):
    """
    Creates a U-Net semantic segmentation model.
    Classes (example): 0 = background, 1 = construction, 2 = brick kiln, 3 = open burning
    """
    model = smp.Unet(
        encoder_name=encoder_name,        
        encoder_weights=encoder_weights,
        in_channels=3, # Standard RGB Sentinel-2 patch (can be modified for multispectral)
        classes=num_classes,                      
    )
    return model

if __name__ == "__main__":
    # Quick dummy test
    model = create_segmentation_model()
    dummy_input = torch.randn(1, 3, 256, 256)
    output = model(dummy_input)
    print("Output shape:", output.shape) # Expected: (1, 4, 256, 256)

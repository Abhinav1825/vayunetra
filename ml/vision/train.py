import os
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from dataset import Sentinel2Dataset
from model import create_segmentation_model
import segmentation_models_pytorch as smp

# Intended to be run in Colab/Kaggle environments
def train_model(data_dir, epochs=10, batch_size=8, learning_rate=1e-3, device="cuda"):
    """
    Main training loop for the E1 Sentinel-2 CV Model.
    """
    if not torch.cuda.is_available():
        print("Warning: CUDA not available. Training on CPU will be extremely slow.")
        device = "cpu"

    image_dir = os.path.join(data_dir, "images")
    mask_dir = os.path.join(data_dir, "masks")
    
    # Initialize dataset
    dataset = Sentinel2Dataset(image_dir=image_dir, mask_dir=mask_dir)
    if len(dataset) == 0:
        print(f"No data found in {data_dir}. Cannot start training.")
        return

    dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True)

    # Initialize model
    model = create_segmentation_model(num_classes=4)
    model = model.to(device)

    # Loss and Optimizer
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=learning_rate)

    print(f"Starting training on {device} for {epochs} epochs...")
    for epoch in range(epochs):
        model.train()
        epoch_loss = 0.0

        for images, masks in dataloader:
            images = images.to(device)
            masks = masks.to(device)

            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, masks)
            loss.backward()
            optimizer.step()

            epoch_loss += loss.item()

        print(f"Epoch {epoch+1}/{epochs} | Loss: {epoch_loss/len(dataloader):.4f}")

    # Save the trained model artifact
    os.makedirs("artifacts", exist_ok=True)
    torch.save(model.state_dict(), "artifacts/e1_cv_model.pth")
    print("Training complete. Model saved to artifacts/e1_cv_model.pth")

if __name__ == "__main__":
    # Placeholder path, in reality this points to Kaggle dataset
    # train_model(data_dir="/kaggle/input/sentinel2-cv-dataset")
    print("Ready for Kaggle/Colab execution.")

'''
Implementation of the Denoising Autoencoder in PyTorch. Dataset used to perform this task is MNIST.
The input is binarized and Binary Cross Entropy has been used as the loss function.
The hidden layer contains 64 units.
To train a DAE, we can simply add some random noise to the data and create corrupted inputs.
In this case 20% noise has been added to the input.
'''

import os
import torch
from torch import nn
from torch.autograd import Variable
from torch.utils.data import DataLoader
from torchvision import transforms
from torchvision.datasets import MNIST
from torchvision.utils import save_image


# ===================================== DEFINE HYPERPARAMETERS ==================================
# Define Hyperparameters
num_epochs = 200
batch_size = 128
learning_rate = 1e-3
noise_value = 0.4


# ====================================== FUNCTIONS - DATA OPERATIONS ============================

# create directory 'auto_output' in which input and output will be saved
if not os.path.exists('./de_auto_output'):
    os.mkdir('./de_auto_output')


# function to visualise the image
def to_img(x):
    x = x.view(x.size(0), 1, 28, 28)
    return x


# function to create noise
def add_noise(img):
    noise = torch.randn(img.size()) * noise_value
    noisy_img = img + noise
    return noisy_img


# function to plot sample image
def plot_sample_img(img, name):
    img = img.view(1, 28, 28)
    save_image(img, './sample_{}.png'.format(name))


# normalization where the entire range of values of X from min_value to max_value
def min_max_normalization(tensor, min_value, max_value):
    min_tensor = tensor.min()
    tensor = (tensor - min_tensor)
    max_tensor = tensor.max()
    tensor = tensor / max_tensor
    tensor = tensor * (max_value - min_value) + min_value
    return tensor


# Rounds the values of a tensor to the nearest integer, element-wise.
def tensor_round(tensor):
    return torch.round(tensor)


# ========================================= INPUT DATA =========================================

# create Transforms which will perform operations on the dataset. All operations in one varible
img_transform = transforms.Compose([
    transforms.ToTensor(),  # transform input images to Tensor
    transforms.Lambda(lambda tensor:min_max_normalization(tensor, 0, 1)),  # normalization (0,1)
    transforms.Lambda(lambda tensor:tensor_round(tensor))  # round the values of tensor
])

# download MNIST dataset if not downloaded
dataset = MNIST('./data', transform=img_transform, download=True)
# load previously downloaded data in batches and shuffle
dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True)


# ========================================== NEURAL NETWORK ====================================

class denoising_autoencoder(nn.Module):
    def __init__(self):
        super(denoising_autoencoder, self).__init__()
        self.encoder = nn.Sequential(
            nn.Linear(28 * 28, 256),
            nn.ReLU(True),
            nn.Linear(256, 64),
            nn.ReLU(True))
        self.decoder = nn.Sequential(
            nn.Linear(64, 256),
            nn.ReLU(True),
            nn.Linear(256, 28 * 28),
            nn.Sigmoid())

    def forward(self, x):
        x = self.encoder(x)
        x = self.decoder(x)
        return x


model = denoising_autoencoder().cuda()
# definition of the LOSS FUNCTION: Binary Cross Entropy
criterion = nn.BCELoss()
# type of OPTIMIZER: Adam
optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate, weight_decay=1e-5)


# =========================================== TRAINING =========================================

for epoch in range(num_epochs):
    for data in dataloader:
        img, _ = data
        img = img.view(img.size(0), -1)
        noisy_img = add_noise(img)
        noisy_img = Variable(noisy_img).cuda()
        img = Variable(img).cuda()
        # ===================forward=====================
        output = model(noisy_img)
        loss = criterion(output, img)
        MSE_loss = nn.MSELoss()(output, img)
        # ===================backward====================
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
    # ===================log========================
    print('epoch [{}/{}], loss:{:.4f}, MSE_loss:{:.4f}'
          .format(epoch + 1, num_epochs, loss.data[0], MSE_loss.data[0]))
    if epoch % 10 == 0:
        x = to_img(img.cpu().data)
        x_hat = to_img(output.cpu().data)
        x_noisy = to_img(noisy_img.cpu().data)
        weights = to_img(model.encoder[0].weight.cpu().data)
        save_image(x, './de_auto_output/x_{}.png'.format(epoch))
        save_image(x_hat, './de_auto_output/x_hat_{}.png'.format(epoch))
        save_image(x_noisy, './de_auto_output/x_noisy_{}.png'.format(epoch))
        save_image(weights, './de_auto_output/filters_epoch_{}.png'.format(epoch))

torch.save(model.state_dict(), './sim_dautoencoder.pth')

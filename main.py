import argparse
from model.TransMIL import TransMIL
import torch
import os
from torch.utils.data import DataLoader
from dataset import *
import cv2
import numpy as np

parser = argparse.ArgumentParser(description='Create heatmaps')
#use clam create_feature_fp.py you can get .h5 file
parser.add_argument('--h5_path', type=str, default='h5-files/')
#thumbnail img dir
parser.add_argument('--thumbnail_path', type=str, default='images/')
#mean min max
parser.add_argument('--head_fusion', type=str, default= 'mean')
parser.add_argument('--model_path', type=str, default='model/test.ckpt')
parser.add_argument('--model_name', type=str, default='TransMIL')
parser.add_argument('--device', type=str, default='cuda:0')
#Determine the maximum size of the wsi using qupath, divide this size by the thumbnail size
#int
parser.add_argument('--downsample', type=int, default=64)
#patch-size
parser.add_argument('--patch_size', type=int, default=448)
args = parser.parse_args()

def load_model(model_name, mode_path):
    if model_name == 'TransMIL':
        param = torch.load(mode_path)['state_dict']
        new_param = {k[6:]: v for k, v in param.items()}
        model = TransMIL(n_classes=2, head_fusion='mean')
        model.load_state_dict(new_param)
    return model

def get_attn(attns):
    result = torch.eye(attns[0].size(-1)).to(attns[0].device)
    for attn in attns:
        I = torch.eye(attn.size(-1)).to(attn.device)
        attn = (attn + 1.0*I)/2
        attn = attn / attn.sum(dim=-1)
        result = torch.matmul(attn, result)
    return result
def main(args):
    model = load_model(args.model_name, args.model_path)
    attn_dataset = Attn_Dateset(args.h5_path, args.thumbnail_path)
    attn_dataloader = DataLoader(attn_dataset, batch_size=1, shuffle=False)
    model.to(device=args.device)
    model.eval()
    with torch.no_grad():
        for batch in attn_dataloader:
            coords, feature, img_path = batch
            img_path = img_path[0]
            feature = feature.to(args.device)
            results_dict, attns = model(feature)
            result = torch.eye(attns[0].size(-1)).to(attns[0].device)
            for attn in attns:
                torch.cuda.empty_cache()
                torch.cuda.empty_cache()
                torch.cuda.empty_cache()
                torch.cuda.empty_cache()
                torch.cuda.empty_cache()
                torch.cuda.empty_cache()
                I = torch.eye(attn.size(-1)).to(attns[0].device)
                a = (attn + 1.0*I)/2
                a = a / a.sum(dim=-1)
                result = torch.matmul(a, result)
            attns = result[0, 0 , 1 :].to('cpu')
            attns = attns / (attns.mean() * 0.8)
            print(attns.mean())
            downsample = args.downsample
            downsample_patchsize = int(args.patch_size//downsample)
            img = cv2.imread(img_path)
        
            mask = np.zeros((int(img.shape[0]),int(img.shape[1])))
            mask1 = np.ones((int(downsample_patchsize),int(downsample_patchsize)))
            coords = coords.numpy()[0]
            for i in range(coords.shape[0]):
                x = int(coords[i][1]//downsample)
                y = int(coords[i][0]//downsample)
                if x+downsample_patchsize < mask.shape[0] and y+downsample_patchsize < mask.shape[1]:
                    mask[x:x+downsample_patchsize,y:y+downsample_patchsize] = attns[i]*mask1
            print(mask.max())
            img = np.float32(img)/255
            mask = cv2.resize(mask,(img.shape[1],img.shape[0]))
            heatmap = cv2.applyColorMap(np.uint8(255*mask),cv2.COLORMAP_JET)
            heatmap = np.float32(heatmap) / 255
            cam = heatmap + np.float32(img)
            cam = cam / np.max(cam)
            savepath1 = "out/out1/" + img_path[7:]
            savepath2 = "out/out2/" + img_path[7:]
            cv2.imwrite(savepath1, np.uint8(255 * cam))
            cv2.imwrite(savepath2, heatmap*255)
            print("finish")
if __name__ == '__main__':
    main(args)
    pass
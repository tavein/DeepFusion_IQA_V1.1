from __future__ import print_function
import torch
import numpy as np
from PIL import Image
import inspect, re
import numpy as np
import os
import collections
import time


def tic():
    globals()['tt'] = time.clock()

def toc():
    print('\nElapsed time: %.8f seconds\n' % (time.clock()-globals()['tt']))

def synthesize_matting(F, alpha, B=None):
    """
    Synthesize hazy image base on optical model
    I = J * t + A * (1 - t)

    or

    Synthesize image using Forground F, Background B and alpha matte
    I = F * alpha + B * (1 - alpha)
    """

    if B is None:
        B = 1

    return F * alpha.expand_as(F) + B * (1 - alpha.expand_as(F))

def reverse_matting(I, t, A=1, t0=0.01):
    """
    Recover haze-free image using hazy image and depth
    J = (I - A) / max(t, t0) + A
    """

    t_clamp = torch.clamp(t, t0, 1)
    J = (I-A) / t_clamp.expand_as(I)  + A
    return torch.clamp(J, -1, 1)

# Converts a Tensor into a Numpy array
# |imtype|: the desired type of the converted numpy array
def tensor2im(image_tensor, imtype=np.uint8):
    image_numpy = image_tensor.cpu().float().numpy()#image_tensor[0].cpu().float().numpy()
    image_numpy = np.squeeze(image_numpy)#去除size为1的维度
    if image_numpy.ndim == 3:
        image_numpy = (np.transpose(image_numpy, (1, 2, 0)) + 1) / 2.0 * 255.0#数据是-1~1范围需要+1再/2   维度交换c,h,w 转换成h,w,c 因为numpy转img的时候要求numpy的格式是h,w,c
    else:
        image_numpy = image_numpy * 255.0
    return image_numpy.astype(imtype)

def tensor2img(image_tensor, imtype=np.float32):
    image_numpy = image_tensor.cpu().float().numpy()#image_tensor[0].cpu().float().numpy()
    image_numpy = (np.squeeze(image_numpy))#去除size为1的维度

    return image_numpy.astype(imtype)

def tensor2np(image_tensor):
    image_numpy = np.clip(image_tensor.squeeze().cpu().float().numpy(),0,1)#image_tensor[0].cpu().float().numpy()
    return image_numpy


def diagnose_network(net, name='network'):
    mean = 0.0
    count = 0
    for param in net.parameters():
        if param.grad is not None:
            mean += torch.mean(torch.abs(param.grad.data))
            count += 1
    if count > 0:
        mean = mean / count
    print(name)
    print(mean)


def save_image(image_numpy, image_path):
    Image.fromarray(image_numpy.astype(np.uint8)).save(image_path)


def info(object, spacing=10, collapse=1):
    """Print methods and doc strings.
    Takes module, class, list, dictionary, or string."""
    methodList = [e for e in dir(object) if isinstance(getattr(object, e), collections.Callable)]
    processFunc = collapse and (lambda s: " ".join(s.split())) or (lambda s: s)
    print( "\n".join(["%s %s" %
                     (method.ljust(spacing),
                      processFunc(str(getattr(object, method).__doc__)))
                     for method in methodList]) )

def varname(p):
    for line in inspect.getframeinfo(inspect.currentframe().f_back)[3]:
        m = re.search(r'\bvarname\s*\(\s*([A-Za-z_][A-Za-z0-9_]*)\s*\)', line)
        if m:
            return m.group(1)

def print_numpy(x, val=True, shp=False):
    x = x.astype(np.float64)
    if shp:
        print('shape,', x.shape)
    if val:
        x = x.flatten()
        print('mean = %3.3f, min = %3.3f, max = %3.3f, median = %3.3f, std=%3.3f' % (
            np.mean(x), np.min(x), np.max(x), np.median(x), np.std(x)))


def mkdirs(paths):
    if isinstance(paths, list) and not isinstance(paths, str):
        for path in paths:
            mkdir(path)
    else:
        mkdir(paths)


def mkdir(path):
    if not os.path.exists(path):
        os.makedirs(path)

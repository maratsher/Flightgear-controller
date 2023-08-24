'''
Created on Jun 8, 2023

@author: esamkin
'''
import numpy as np


def cor2center(a):
    """
    (xl, yl, xr, yr) to (cx, cy, w, h)
    """
    cx, cy = (a[2:] + a[:2]) * 0.5
    w, h = a[2:] - a[:2]
    return cx, cy, w, h


def center2cor(a):
    """
    (cx, cy, w, h) to (xl, yl, xr, yr)
    """
    half_wh = a[2:] / 2
    xl, yl = a[:2] - half_wh
    xr, yr = a[:2] + half_wh
    return xl, yl, xr, yr


class Anchors:
    """This generate anchors.

    Parameters
    ----------
    stride : int
        Anchor stride
    ratios : tuple
        Anchor ratios
    scales : tuple
        Anchor scales
    size : int
        anchor size
    """

    def __init__(self, stride, ratios, scales, image_center=0, size=0):
        self.stride = stride
        self.ratios = ratios
        self.scales = scales
        self.image_center = image_center
        self.size = size
        self.anchor_num = len(self.scales) * len(self.ratios)
        self.anchors = None
        self.generate_anchors()

    def generate_anchors(self):
        """generate anchors based on predefined configuration"""
        self.anchors = np.zeros((self.anchor_num, 4), dtype=np.float32)
        size = self.stride * self.stride
        count = 0
        for r in self.ratios:
            ws = int(np.sqrt(size * 1. / r))
            hs = int(ws * r)

            for s in self.scales:
                w = ws * s
                h = hs * s
                self.anchors[count][:] = [-w * 0.5, -h * 0.5, w * 0.5, h * 0.5][:]
                count += 1

    def generate_all_anchors(self, im_c, size):
        """
        generate all anchors

        Parameters
        ----------
        im_c: int
            image center
        size:
            image size
        """
        if self.image_center == im_c and self.size == size:
            return False
        self.image_center = im_c
        self.size = size

        a0x = im_c - size // 2 * self.stride
        ori = np.array([a0x] * 4, dtype=np.float32)
        zero_anchors = self.anchors + ori

        x1 = zero_anchors[:, 0]
        y1 = zero_anchors[:, 1]
        x2 = zero_anchors[:, 2]
        y2 = zero_anchors[:, 3]

        x1, y1, x2, y2 = map(lambda x: x.reshape(self.anchor_num, 1, 1),
                             [x1, y1, x2, y2])
        cx, cy, w, h = cor2center([x1, y1, x2, y2])

        disp_x = np.arange(0, size).reshape(1, 1, -1) * self.stride
        disp_y = np.arange(0, size).reshape(1, -1, 1) * self.stride

        cx = cx + disp_x
        cy = cy + disp_y

        # broadcast
        zero = np.zeros((self.anchor_num, size, size), dtype=np.float32)
        cx, cy, w, h = map(lambda x: x + zero, [cx, cy, w, h])
        x1, y1, x2, y2 = center2cor([cx, cy, w, h])

        self.all_anchors = (np.stack([x1, y1, x2, y2]).astype(np.float32),
                            np.stack([cx, cy, w, h]).astype(np.float32))
        return True


def softmax(x, axis=1):
    e_x = np.exp(x)
    return np.divide(e_x, e_x.sum(axis=axis, keepdims=True))


def get_scale(bbox_w, bbox_h):
    pad = (bbox_w + bbox_h) * 0.5
    return np.sqrt((bbox_w + pad) * (bbox_h + pad))


def change(hw_r):
    return np.maximum(hw_r, 1. / hw_r)


if __name__ == '__main__':
    from mxnet import ndarray as nd

    x = np.random.uniform(0, 1, (1, 10, 3, 3))
    x_nd = nd.array(x)
    # print(x,x_nd)
    # print(nd.softmax(x_nd, axis=1))
    # print((softmax(x)))
    x = np.transpose(x, (1, 2, 3, 0)).reshape((2, -1))
    x = np.transpose(x, axes=(1, 0))
    x = softmax(x)
    x_nd = nd.transpose(x_nd, axes=(1, 2, 3, 0))
    x_nd = nd.reshape(x_nd, shape=(2, -1))
    x_nd = nd.transpose(x_nd, axes=(1, 0))
    x_nd = nd.softmax(x_nd, axis=1)
    print(x, x_nd.asnumpy())
    print('*' * 80)
    x = x[:, 1]
    x_nd = nd.slice_axis(x_nd, axis=1, begin=1, end=2)
    x_nd = nd.squeeze(x_nd, axis=1)
    print(x - x_nd.asnumpy())

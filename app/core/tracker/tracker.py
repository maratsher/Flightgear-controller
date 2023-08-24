"""
Created on Jun 8, 2023

@author: esamkin
"""
import cv2
import numpy as np
import onnxruntime as ort

from app.core.tracker.utils import softmax, get_scale, change, Anchors


class Tracker:
    def __init__(self, backbone='backbone.onnx', rpn_head='rpn.onnx'):
        self.backbone_session = ort.InferenceSession(backbone, providers=['CUDAExecutionProvider'])
        self.head_session = ort.InferenceSession(rpn_head, providers=['CUDAExecutionProvider'])
        self.template_size = 127
        self.search_size = 287
        self.context_amount = 0.5
        self.stride = 8
        self.scale = [8]
        self.anchor_ratio = [0.33, 0.5, 1, 2, 3]
        self.penalty_1 = 0.16  # change asp r
        self.penalty_2 = 0.4
        self.penalty_3 = 0.3
        self.score = 1

        self.score_size = (self.search_size - self.template_size) // self.stride + 1
        self.anchor_num = len(self.anchor_ratio) * len(self.scale)
        self.best_score_id = None
        self.anchor = self._generate_anchor()
        hanning = np.hanning(self.score_size)
        window = np.outer(hanning, hanning)
        self.window = np.tile(window.flatten(), self.anchor_num)

    def select_obj(self, img, bbox):
        self.center_bbox = np.array([bbox[0] + (bbox[2] - 1) / 2, bbox[1] + (bbox[3] - 1) / 2])
        # size  (w,h)
        self.size = np.array([bbox[2], bbox[3]])
        # z crop size
        w_z = self.size[0] + self.context_amount * np.sum(self.size)
        h_z = self.size[1] + self.context_amount * np.sum(self.size)
        s_z = round(np.sqrt(w_z * h_z))
        self.channel_average = np.mean(img, axis=(0, 1))
        z = self.get_subwindow(
            img, self.center_bbox,
            self.template_size,
            s_z, self.channel_average)
        # emb tesor
        self._z = self.backbone_session.run(
            None,
            {'data': z})

    def search_obj(self, x):
        # calculate z crop size
        w_z = self.size[0] + self.context_amount * np.sum(self.size)
        h_z = self.size[1] + self.context_amount * np.sum(self.size)
        s_z = np.sqrt(w_z * h_z)
        scale_z = self.template_size / s_z
        s_x = s_z * (self.search_size / self.template_size)
        x_crop = self.get_subwindow(x, self.center_bbox,
                                    self.search_size,
                                    round(s_x), self.channel_average)
        self._x = self.backbone_session.run(
            None,
            {'data': x_crop})

        self.score, self.loc = self.head_session.run(
            ['conv3_fwd', 'conv7_fwd'],
            {'data0': self._z[0], 'data1': self._x[0]})

        self._get_score()
        self._convert_bbox()

        # scale penalty，
        s_c = change(get_scale(self.loc[2, :], self.loc[3, :]) /
                     (get_scale(self.size[0] * scale_z, self.size[1] * scale_z)))

        # proportion penalty.
        r_c = change((self.size[0] / self.size[1]) /
                     (self.loc[2, :] / self.loc[3, :]))
        penalty = np.exp(-(r_c * s_c - 1) * self.penalty_1)
        self.score *= penalty
        # window penalty
        self.score = self.score * (1 - self.penalty_2) + \
                     self.window * self.penalty_2
        best_score_idx = np.argmax(self.score)
        bbox = self.loc[:, best_score_idx] / scale_z
        penalty_lr = penalty[best_score_idx] * self.score[best_score_idx] * self.penalty_3
        center_x = bbox[0] + self.center_bbox[0]
        center_y = bbox[1] + self.center_bbox[1]
        # smooth bbox
        width = self.size[0] * (1 - penalty_lr) + bbox[2] * penalty_lr
        height = self.size[1] * (1 - penalty_lr) + bbox[3] * penalty_lr
        center_x, center_y, width, height = self._bbox_clip(
            center_x, center_y, width, height, x.shape[:2])

        # update for new x
        self.center_bbox = np.array([center_x, center_y])
        self.size = np.array([width, height])

        bbox = [int(center_x - width / 2),
                int(center_y - height / 2),
                int(width),
                int(height)]
        best_score = self.score[best_score_idx]

        return best_score, bbox

    def _get_score(self, ):
        """
        Transform tensor from rpn to subconfidence.
        Produse max_confidence and it's possition.  
        """
        self.score = np.transpose(self.score, (1, 2, 3, 0)).reshape((2, -1))
        self.score = np.transpose(self.score, axes=(1, 0))
        self.score = softmax(self.score, axis=1)[:, 1]

    def _convert_bbox(self, ):
        self.loc = np.transpose(self.loc, (1, 2, 3, 0)).reshape((4, -1))
        self.loc[0, :] = self.loc[0, :] * self.anchor[:, 2] + self.anchor[:, 0]
        self.loc[1, :] = self.loc[1, :] * self.anchor[:, 3] + self.anchor[:, 1]
        self.loc[2, :] = np.exp(self.loc[2, :]) * self.anchor[:, 2]
        self.loc[3, :] = np.exp(self.loc[3, :]) * self.anchor[:, 3]

    def _generate_anchor(self):
        """
        generate score map anchors based on predefined configuration

        Parameters
        ----------
            score_size : int
                score map size

        Returns
        ----------
            score map anchor
        """

        anchors = Anchors(self.stride,
                          self.anchor_ratio,
                          self.scale)
        anchor = anchors.anchors
        x_min, y_min, x_max, y_max = anchor[:, 0], anchor[:, 1], anchor[:, 2], anchor[:, 3]
        anchor = np.stack([(x_min + x_max) * 0.5, (y_min + y_max) * 0.5, x_max - x_min, y_max - y_min], 1)
        total_stride = anchors.stride
        anchor_num = anchor.shape[0]
        anchor = np.tile(anchor, self.score_size * self.score_size).reshape((-1, 4))
        ori = - (self.score_size // 2) * total_stride
        x_x, y_y = np.meshgrid([ori + total_stride * dx for dx in range(self.score_size)],
                               [ori + total_stride * dy for dy in range(self.score_size)])
        x_x, y_y = np.tile(x_x.flatten(), (self.anchor_num, 1)).flatten(), \
            np.tile(y_y.flatten(), (self.anchor_num, 1)).flatten()
        anchor[:, 0], anchor[:, 1] = x_x.astype(np.float32), y_y.astype(np.float32)
        return anchor

    def _bbox_clip(self, center_x, center_y, width, height, boundary):
        center_x = max(0, min(center_x, boundary[1]))
        center_y = max(0, min(center_y, boundary[0]))
        width = max(10, min(width, boundary[1]))
        height = max(10, min(height, boundary[0]))
        return center_x, center_y, width, height

    def get_subwindow(self, img, pos, model_sz, original_sz, avg_chans):
        """
        Adjust the position of the frame to prevent the boundary from being exceeded.
        If the boundary is exceeded,
        the average value of each channel of the image is used to replace the exceeded value.
        Parameters
        ----------
        im : np.ndarray
            BGR based image
        pos : list
            center position
        model_sz : array
            exemplar size, x is 127, z is 287 in ours
        original_sz: array
            original size
        avg_chans : array
            channel average
        ctx : mxnet.Context
            Context such as mx.cpu(), mx.gpu(0).
        Returns
        -------
            rejust window though avg channel
        """
        if isinstance(pos, float):
            pos = [pos, pos]
        im_sz = img.shape
        original_c = (original_sz + 1) / 2
        context_xmin = np.floor(pos[0] - original_c + 0.5)
        context_xmax = context_xmin + original_sz - 1
        context_ymin = np.floor(pos[1] - original_c + 0.5)
        context_ymax = context_ymin + original_sz - 1
        left_pad = int(max(0., -context_xmin))
        top_pad = int(max(0., -context_ymin))
        right_pad = int(max(0., context_xmax - im_sz[1] + 1))
        bottom_pad = int(max(0., context_ymax - im_sz[0] + 1))

        context_xmin = context_xmin + left_pad
        context_xmax = context_xmax + left_pad
        context_ymin = context_ymin + top_pad
        context_ymax = context_ymax + top_pad
        im_h, im_w, im_c = img.shape

        if any([top_pad, bottom_pad, left_pad, right_pad]):
            # If there is a pad, use the average channels to complete
            size = (im_h + top_pad + bottom_pad, im_w + left_pad + right_pad, im_c)
            te_im = np.zeros(size, np.uint8)
            te_im[top_pad:top_pad + im_h, left_pad:left_pad + im_w, :] = img
            if top_pad:
                te_im[0:top_pad, left_pad:left_pad + im_w, :] = avg_chans
            if bottom_pad:
                te_im[im_h + top_pad:, left_pad:left_pad + im_w, :] = avg_chans
            if left_pad:
                te_im[:, 0:left_pad, :] = avg_chans
            if right_pad:
                te_im[:, im_w + left_pad:, :] = avg_chans
            im_patch = te_im[int(context_ymin):int(context_ymax + 1),
                       int(context_xmin):int(context_xmax + 1), :]
        else:
            # If there is no pad, crop Directly
            im_patch = img[int(context_ymin):int(context_ymax + 1),
                       int(context_xmin):int(context_xmax + 1), :]
        if not np.array_equal(model_sz, original_sz):
            im_patch = cv2.resize(im_patch, (model_sz, model_sz))
        im_patch = im_patch.transpose(2, 0, 1)
        im_patch = im_patch[np.newaxis, :, :, :]
        im_patch = im_patch.astype(np.float32)
        return im_patch


if __name__ == '__main__':
    from time import time

    net = Tracker()

    X = np.random.normal(0, 1, (287, 287, 3)).astype('float32')
    Z = np.random.normal(0, 1, (127, 127, 3)).astype('float32')

    net.select_obj(Z, (64, 64, 127, 127))

    net.search_obj(X)

    n = 200
    tic = time()
    print(net.anchor.shape)
    for i in range(n):
        print(net.search_obj(X))
    print((time() - tic) / n)
    print(net.score.shape, net.loc.shape, net.score)

import os, sys
os.chdir('/home/' + sys.argv[1] + '/CTPN')
os.environ['GLOG_minloglevel'] = '2'

from cfg import Config as cfg
from other import resize_im, CaffeModel
import cv2, caffe
import requests
from detectors import TextProposalDetector, TextDetector

NET_DEF_FILE="models/deploy.prototxt"
MODEL_FILE="models/ctpn_trained_model.caffemodel"

caffe.set_mode_gpu()
caffe.set_device(cfg.TEST_GPU_ID)

if (sys.argv[2]=="0"):
    im_file = sys.argv[3]
else:
    f = open(sys.argv[4], 'wb')
    f.write(requests.get(sys.argv[3]).content)
    f.close()
    im_file = sys.argv[4]
    
# initialize the detectors
text_proposals_detector=TextProposalDetector(CaffeModel(NET_DEF_FILE, MODEL_FILE))
text_detector=TextDetector(text_proposals_detector)

im=cv2.imread(im_file)

im, f=resize_im(im, cfg.SCALE, cfg.MAX_SCALE)
text_lines=text_detector.detect(im)

s = "{\n  \"Lines\": " + str(len(text_lines)) + ", "
s += "\n  \"Regions\": ["

idx = 0
for box in text_lines:
    idx += 1
    s += "\n    {\"BoundingBox\": \""
    for index in range(len(box)):
        if index == len(box) - 1:
            s += "\", \"Accuracy\": \"" + str(round(box[index],2)) + "\"}"
            if idx < len(text_lines):
                s += ", "
        else:
            s += str(int(round(box[index]/f)))
            if index < len(box) -2:
                s +=  ","

s += "\n  ]\n}\n"

print s

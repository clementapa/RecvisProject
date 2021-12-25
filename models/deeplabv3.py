from torchvision.models.segmentation import deeplabv3_resnet50
from models.base import BASE_LitModule
"""
https://pytorch.org/vision/stable/models.html#torchvision.models.segmentation.deeplabv3_resnet50
"""

class Deeplabv3(BASE_LitModule):
    def __init__(self, config) -> None:
        super(Deeplabv3, self).__init__(config)
        
        self.config = config
        # model pre-trained on COCO train2017 which contains the same classes as Pascal VOC
        self.net = deeplabv3_resnet50(pretrained=True, num_classes=21)
                
    def forward(self, x):
        dic = self.net(x)
        return dic['out']
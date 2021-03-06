from __future__ import division
import torch
import numpy as np
import time
from PIL import Image
from torch.optim import SGD

from torch.autograd import Variable
from torch.utils.data import DataLoader
from utils.accuracy import *
from utils.resnet import *

from utils.output_precess import *
from utils.dataset import *
from utils.loss import *
from models import *


def main(model,train_data_file,val_data_file,data_dir,label_dir,base_lr = 0.01,power = 0.9,num_epochs= 144):
    #init model
    model.eval()
    model.cuda(0)

    #load data
    train_data_loader = DataLoader(VOC2012(train_data_file,data_dir,label_dir,target_size=512,
            crop_size=320,zoom_range=[0.5,1.5],rotation=0.,channel_shift = 20,
            mirror=True,label_cval=255,ignore_label = 255,nb_class =21,task = 'Train'),
            num_workers=8,batch_size=16,shuffle=True)


    #split param
    fcov_params = list(map(id,model.fconv.parameters()))
    base_params = filter(lambda p:id(p) not in fcov_params,model.parameters())

    #compile model
    #optimizer = SGD(model.parameters(),lr=1e-2,momentum=0.9,weight_decay=1e-4,nesterov=True)
    optimizer = SGD([{'params':base_params},
                     {'params':model.fconv.parameters(),'lr':10*base_lr}],lr=base_lr,momentum=0.9,
                    weight_decay=1e-4,nesterov=True)

    #poly
    def lr_poly(base_lr, iter, max_iter, power):
        return base_lr * ((1 - float(iter) / max_iter) ** (power))

    print '---Begin Training---'
    print '---Total: %d Epochs---'%(num_epochs)
    print '---Base lr:%f---Momentim:%f---Weight Decay:%f---'%(base_lr,0.9,1e-4)
    for epoch in range(num_epochs):
        # train
        print 'Epoch:%d' %(epoch)
        model.eval()
        for step,(images,labels) in enumerate(train_data_loader):
            t1=time.clock()
            optimizer.zero_grad()
            images = images.cuda(0)
            labels = labels.cuda(0)
            inputs = Variable(images)
            targets = Variable(labels)
            outputs = model(inputs)
            #loss,acc = Sparse_Cross_Entropy(outputs,targets)
            loss ,acc= Sparse_Cross_Entropy(outputs,targets)
            #acc = Pixel_Accuracy(outputs,targets)
            loss.backward()
            optimizer.step()
            lr_ = lr_poly(base_lr=base_lr, iter=epoch*661+step+1, max_iter=num_epochs*661, power=power)
            optimizer = SGD(model.parameters(),lr=lr_,momentum=0.9,weight_decay=1e-4,nesterov=True)
            #optimizer = SGD([{'params': base_params},
                             #{'params': model.fconv.parameters(), 'lr': lr_ * 10}], lr=lr_, momentum=0.9,
                            #weight_decay=1e-4, nesterov=True)
            t2=time.clock()
            print "-----------Epoch:%d-----Iter:%d-----------" %(epoch,step)
            print 'Time:%fs(%f iter/s)----lr:%f-----Loss:%f' %(t2-t1,1/(t2-t1),lr_,loss.data[0])
            print 'Accuracy:',acc,'%'
    
        torch.save(model.state_dict(),'/home/alex/PyTorch/initmodel/resnet50_weight.pth')
if __name__ =='__main__':
    model = resnet50(bn_momentum=0.95)
    train_data_file = '/home/alex/Data/VOClarge/VOC2012/ImageSets/Segmentation/train.txt'
    val_data_file = '/home/alex/Data/VOClarge/VOC2012/ImageSets/Segmentation/val.txt'
    data_dir = '/home/alex/Data/VOClarge/VOC2012/JPEGImages'
    label_dir = '/home/alex/Data/VOClarge/VOC2012/SegmentationClass'
    base_lr = 0.001
    power = 0.9
    num_epochs = 48

    main(model,train_data_file,val_data_file,data_dir,label_dir)

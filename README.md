# COV Project
Repo containing everything COV project related.

## About

Project is being executed for lecture `COV`, and implements `SEG_1` part of assignment, which is person segmentation.
This means our solution should detect and mark parts in a picture belonging to a single person. This should also work if multiple people are visible within one image.

*TODO add procedure here*

## Participants:

* Dorian Karaban
* Fabian Kastner
* Paul Hörmann

## Repo Structure

* doc: Project Documentation (latex)
* src: Project Source (python)
* ref: Project References (pdf / other)
* presi: Project Presentation

## Setup

### Data

http://human-pose.mpi-inf.mpg.de/#download

For training this data should be extracted and placed in `/data` directory in the repository root, same for the annotations.

### General
* Clone Repo: `git clone git@github.com:poel22/covproject.git`

### Doc
* TODO add latex make procedure

### Source
* TODO add src setup guide

## Online References
* Guide with U-net: https://medium.com/analytics-vidhya/humans-image-segmentation-with-unet-using-tensorflow-keras-fd6cb43b06e5
* Blogpost from lecture notes: https://www.pyimagesearch.com/2017/09/11/object-detection-with-deep-learning-and-opencv/
* Link for SSD multibox detection: https://arxiv.org/abs/1512.02325 (pdf also included in /ref)
* Blogpost Semantic Segmentation: https://towardsdatascience.com/understanding-semantic-segmentation-with-unet-6be4f42d4b47
* Blogpost Transposed Convolution: https://naokishibuya.medium.com/up-sampling-with-transposed-convolution-9ae4f2df52d0
* Guide Feature Map Visualization: https://www.analyticsvidhya.com/blog/2020/11/tutorial-how-to-visualize-feature-maps-directly-from-cnn-layers/
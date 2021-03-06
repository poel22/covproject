import os
import pickle
import logging
import shutil
from datetime import datetime

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
logging.getLogger('tensorflow').setLevel(logging.FATAL)

import numpy as np
from tqdm import tqdm
import tensorflow as tf
import matplotlib.pyplot as plt
from PIL import Image, ImageOps
from tensorflow.keras.preprocessing.image import ImageDataGenerator

from unet import UNet


def set_tf_loglevel(level):
    if level >= logging.FATAL:
        os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
    if level >= logging.ERROR:
        os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
    if level >= logging.WARNING:
        os.environ['TF_CPP_MIN_LOG_LEVEL'] = '1'
    else:
        os.environ['TF_CPP_MIN_LOG_LEVEL'] = '0'
    logging.getLogger('tensorflow').setLevel(level)


def preprocess_data(data_dir, size):
    file_names = np.array(os.listdir(data_dir))

    # might need tweaking if file names or sorting differs
    image_file_names = file_names[1::4]
    mask_file_names = file_names[3::4]

    # combine masks of identical input image to combined masks
    prev_image_array = None
    prev_mask_arrays = []

    for index, (image_file_name, mask_file_name) in tqdm(enumerate(zip(image_file_names, mask_file_names))):

        # resize images
        image = Image.open(os.path.join(data_dir, image_file_name))
        image_resized = image.resize(size, Image.ANTIALIAS)
        image_resized_array = np.asarray(image_resized)
        
        # resize, grayscale and binary threshold masks
        mask = Image.open(os.path.join(data_dir, mask_file_name))
        mask_resized = mask.resize(size, Image.ANTIALIAS)
        mask_resized_grayscale = ImageOps.grayscale(mask_resized)
        mask_resized_grayscale_binary = mask_resized_grayscale.point(lambda p: p > 0 and 255)
        mask_resized_grayscale_binary_array = np.asarray(mask_resized_grayscale_binary)

        if (prev_image_array is None) or (np.array_equal(image_resized_array, prev_image_array)):
            if prev_image_array is None:
                prev_image_array = image_resized_array.copy()
            prev_mask_arrays.append(mask_resized_grayscale_binary_array.copy())
        else:
            combined_mask = prev_mask_arrays[0].copy()
            for i in range(1, len(prev_mask_arrays)):
                combined_mask = np.add(combined_mask, prev_mask_arrays[i])

            combined_mask[combined_mask > 255] = 255

            image = Image.fromarray(prev_image_array)
            mask = Image.fromarray(combined_mask)

            out_dir_image = "data/images"
            out_dir_mask = "data/masks"

            if not os.path.exists(out_dir_image):
                os.makedirs(out_dir_image)
            if not os.path.exists(out_dir_mask):
                os.makedirs(out_dir_mask)

            image.save(os.path.join(out_dir_image,"{0}.png".format(index)))
            mask.save(os.path.join(out_dir_mask,"{0}.png".format(index)))

            prev_image_array = image_resized_array.copy()
            prev_mask_arrays = [mask_resized_grayscale_binary_array.copy()]


def split_data():
    inDir_img = "data/images"    
    inDir_mask = "data/masks"    
    splits = 0.7,0.15,0.15
    assert (splits[0] + splits[1] + splits[2]) == 1.0

    img_filenames = os.listdir(inDir_img)    
    size = len(img_filenames)

    # determine split size
    split_train = int(size * splits[0])
    split_valid = int(size * splits[1])
    split_test = int(size * splits[2])    
    print("size", size)
    print("split size", split_train, split_valid, split_test)
    print("size", split_train + split_valid + split_test)    
    #assert size == (split_train + split_valid + split_test)

    # shuffle 
    np.random.shuffle(img_filenames)
    train_set = img_filenames[:split_train]
    valid_set = img_filenames[split_train:(split_train+split_valid)]
    test_set = img_filenames[(split_train+split_valid):]
    print("final set size: ", len(train_set), len(valid_set), len(test_set))
    assert(len(train_set) + len(valid_set) + len(test_set) == size)

    # create path for images
    trainDir = os.path.join(inDir_img,"train")
    validDir = os.path.join(inDir_img,"valid")
    testDir = os.path.join(inDir_img,"test")
    if not os.path.exists(trainDir):
        os.makedirs(trainDir)
    if not os.path.exists(validDir):
        os.makedirs(validDir)
    if not os.path.exists(testDir):
        os.makedirs(testDir)
    
    # move images
    for f in train_set:
        source = os.path.join(inDir_img, f)
        destination = os.path.join(trainDir, f)
        shutil.move(source, destination)
    for f in valid_set:
        source = os.path.join(inDir_img, f)
        destination = os.path.join(validDir, f)
        shutil.move(source, destination)
    for f in test_set:
        source = os.path.join(inDir_img, f)
        destination = os.path.join(testDir, f)
        shutil.move(source, destination)

    # create path for masks
    trainDir = os.path.join(inDir_mask,"train")
    validDir = os.path.join(inDir_mask,"valid")
    testDir = os.path.join(inDir_mask,"test")
    if not os.path.exists(trainDir):
        os.makedirs(trainDir)
    if not os.path.exists(validDir):
        os.makedirs(validDir)
    if not os.path.exists(testDir):
        os.makedirs(testDir)

    # move masks
    for f in train_set:
        source = os.path.join(inDir_mask, f)
        destination = os.path.join(trainDir, f)
        shutil.move(source, destination)
    for f in valid_set:
        source = os.path.join(inDir_mask, f)
        destination = os.path.join(validDir, f)
        shutil.move(source, destination)
    for f in test_set:
        source = os.path.join(inDir_mask, f)
        destination = os.path.join(testDir, f)
        shutil.move(source, destination)


def get_data_size(dir, dataset):
    return len(os.listdir(os.path.join(dir, dataset)))


def get_data(dir):
    file_names = np.array(os.listdir(dir))
    data = np.asarray([np.asarray(Image.open(os.path.join(dir, file_name))) for file_name in file_names])

    # grayscale images only have 3 dims(num_images, height, width), but DataGenerator requires 4 dims(num_images, height, width, color_channels)
    if len(data.shape) < 4:
        data = np.expand_dims(data, 3)
    return data


def get_data_generators(batch_size, dir):

    # set parameters for data augmentation
    # data_gen_args = dict(featurewise_center=True,
    #                     featurewise_std_normalization=True,
    #                     rotation_range=90,
    #                     width_shift_range=0.1,
    #                     height_shift_range=0.1,
    #                     zoom_range=0.2)

    data_gen_args = dict(rotation_range=90,
                        width_shift_range=0.1,
                        height_shift_range=0.1,
                        zoom_range=0.2)

    image_datagen = ImageDataGenerator(**data_gen_args)
    mask_datagen = ImageDataGenerator(**data_gen_args)

    images = get_data(os.path.join(dir, 'images/train'))
    masks = get_data(os.path.join(dir, 'masks/train'))

    # set seed to transform images and masks equally
    seed = 1

    image_datagen.fit(images, seed=seed)
    mask_datagen.fit(masks, seed=seed)

    image_generator = image_datagen.flow(images, batch_size=batch_size, seed=seed)
    mask_generator = mask_datagen.flow(masks, batch_size=batch_size, seed=seed)

    return image_generator, mask_generator


def main():
    DATA_DIR = "data/"
    SIZE = 256, 144

    # preprocess inputs, combine masks and transform to grayscale binary
    # preprocess_data(DATA_DIR, SIZE)
    # split_data()

    BATCH_SIZE = 512

    image_generator, mask_generator = get_data_generators(BATCH_SIZE, DATA_DIR)

    # test_image_file_names = np.array(os.listdir(os.path.join(DATA_DIR, 'images/'))[-5:])
    # test_mask_file_names = np.array(os.listdir(os.path.join(DATA_DIR, 'masks/'))[-5:])
    # test_images = np.asarray([np.asarray(Image.open(os.path.join(os.path.join(DATA_DIR, 'images/'), test_image_file_name))) for test_image_file_name in test_image_file_names])
    # test_masks = np.asarray([np.asarray(Image.open(os.path.join(os.path.join(DATA_DIR, 'masks/'), test_mask_file_name))) for test_mask_file_name in test_mask_file_names])
    
    # valid data
    val_images = get_data("data/images/valid")
    val_masks = get_data("data/masks/valid")

    # test data
    test_images = get_data("data/images/test")
    test_masks = get_data("data/masks/test")

    model = UNet(SIZE)

    # TODO find correct metric and loss
    model.compile(optimizer='adam', metrics=['mse'], loss='mse')

    DATA_SIZE = get_data_size(DATA_DIR, "images/train")
    EPOCHS = 100

    # TODO validation split

    # train
    start = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
    for epoch in range(EPOCHS):
        now = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
        print("[{0} - {1} Epoch {2}]".format(start, now, epoch + 1))
        
        BATCH_ITERATION = 1
        for image_batch, mask_batch in zip(image_generator, mask_generator):

            # break on overflow images if DATA_SIZE % BATCH_SIZE != 0
            if BATCH_ITERATION * BATCH_SIZE > DATA_SIZE: break
            
            history = model.fit(image_batch, mask_batch, validation_data=(val_images, val_masks))
            pickle.dump(history.history, open("histories/{0}.pickle".format(epoch), "wb"))

            BATCH_ITERATION += 1
  
        # every tenth epoch save weights and plot predictions
        if (epoch > 0) and (epoch % 10 == 0):

            model.save_weights("weights/{0}.ckpt".format(epoch))

            predicted_masks = model.predict(test_images)

            fig, ax = plt.subplots(5, 3)
            fig.set_size_inches(14, 12)
            for i in range(5): 
                image = test_images[i]
                mask = test_masks[i]
                predicted_mask = predicted_masks[i]

                ax[i][0].imshow(image)
                if i == 0: ax[i][0].title.set_text('Image')
                ax[i][0].axis('off')
                
                ax[i][1].imshow(np.squeeze(mask))
                if i == 0: ax[i][1].title.set_text('Mask')
                ax[i][1].axis('off')
                
                ax[i][2].imshow(np.squeeze(predicted_mask))
                if i == 0: ax[i][2].title.set_text('Predicted Mask')
                ax[i][2].axis('off')

            # plt.show()
            fig.savefig("plots/{0}.png".format(epoch))
            # plt.close()

    # TODO test, test split
    
    # TODO visualize results





if __name__ == "__main__":
    # os.environ['CUDA_VISIBLE_DEVICES'] = '-1'
    os.environ['TF_FORCE_GPU_ALLOW_GROWTH'] = 'true'
    print("GPU") if len(tf.config.experimental.list_physical_devices('GPU')) > 0 else print("CPU")
    main()

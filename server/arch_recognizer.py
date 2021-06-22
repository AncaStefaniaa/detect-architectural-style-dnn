from keras.applications.mobilenet_v2 import preprocess_input
from keras.preprocessing import image
import numpy as np
import os
from pickle import load
from keras.models import load_model

def normalize(scaler, data):
    result = scaler.transform(data)
    return result

def determine_arch(img_path, features_model, clf_model, scaler):
    img = image.load_img(img_path, target_size=(224, 224))

    img_arr = image.img_to_array(img)
    img_arr = np.expand_dims(img_arr, axis = 0)
    img_arr = preprocess_input(img_arr)

    features = features_model.predict(img_arr)
    features = np.squeeze(features)

    features = normalize(scaler, [features])
    
    predictions = clf_model.predict(features)
    label = np.argmax(predictions)

    return label

from pickle import load

# mobilenet_model = load_model("./best_mobilenet.h5")
# cnn_model = load_model('./best_model_yet.h5')
# sc = load(open('best_scaler.pkl', 'rb'))

# print (determine_arch('C:/Users/sandu.petrasco/Desktop/CNN/splitted_dataset/train/Ancient Egyptian architecture/16_2.jpg', mobilenet_model, cnn_model, sc))
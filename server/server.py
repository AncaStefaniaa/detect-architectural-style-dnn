import subprocess
import pickle
from keras.models import load_model
from flask import Flask, flash, redirect, render_template, request, session, abort, url_for, jsonify
from PIL import Image
import sys
import pyrebase
from flask_cors import CORS
import uuid
from requests.exceptions import HTTPError
import json
from datetime import datetime

import arch_recognizer as ar

# vgg_filename = './vgg-model.h5'
# vgg_model = load_model(vgg_filename)

# clf_filename = './clf-model.sav'
# clf_model = pickle.load(open(clf_filename, 'rb'))

mobilenet_filename = './best_mobilenet.h5'
mobilenet_model = load_model(mobilenet_filename)

cnn_filename = './best_model_yet.h5'
cnn_model = load_model(cnn_filename)

scaler = pickle.load(open('best_scaler.pkl', 'rb'))

app = Flask(__name__)
CORS(app)

class image_info:
    def __init__(self, id, photo_id, style, url, latitude, longitude, address, favorite, datetime):
        self.id = id
        self.photo_id = photo_id
        self.style = style
        self.url = url
        self.latitude = latitude
        self.longitude = longitude
        self.address = address
        self.favorite = favorite
        self.datetime = datetime

# old_config = {
#     "apiKey": "AIzaSyA5f6fiJjhp-XGkSVYIcVQc3XDEheSXrZo",
#     "authDomain": "testapp-61fb3.firebaseapp.com",
#     "databaseURL": "https://testapp-61fb3-default-rtdb.europe-west1.firebasedatabase.app/",
#     "projectId": "testapp-61fb3",
#     "storageBucket": "testapp-61fb3.appspot.com",
#     "messagingSenderId": "147582448580",
#     "appId": "1:147582448580:web:3ba07b897931c0c2476a91",
#     "measurementId": "G-YSZLQ6Y66Y",
#     "serviceAccount": "serviceAccountCredentials_old.json"
# }

config = {
    "apiKey": "AIzaSyCeJhhVq5ixanrgd7D2C2nCjwQpEzY0wAo",
    "authDomain": "archsmarter-68e3e.firebaseapp.com",
    "databaseURL": "https://archsmarter-68e3e-default-rtdb.europe-west1.firebasedatabase.app/",
    "projectId": "archsmarter-68e3e",
    "storageBucket": "archsmarter-68e3e.appspot.com",
    "messagingSenderId": "432304571578",
    "appId": "1:432304571578:web:ed7187ad249777ce0bee83",
    "measurementId": "G-J80ZRQRB0S",
    "serviceAccount": "serviceAccountCredentials.json"
}

# init database
firebase = pyrebase.initialize_app(config)

auth = firebase.auth()
db = firebase.database()
stg = firebase.storage()

user_db = {"username": "", "email": "", "uid": ""}

def treat_http_error(err):
    error_json = err.args[1]
    error = json.loads(error_json)['error']

    err_code = error['code']
    err_message = error['message']

    print (err_code, err_message)
    return err_message, err_code
 
@app.route("/register", methods = ["POST"])
def register():
    try:
        new_user = request.json

        email = new_user['email']
        password = new_user['password']
        username = new_user['username']

        auth.create_user_with_email_and_password(email, password)
        user = auth.sign_in_with_email_and_password(email, password)
        user_id = user["localId"]
        
        global user_db
        
        user_db["email"] = user["email"]
        user_db["uid"] = user_id
        user_db["username"] = username

        default_profile_photo_url = "https://firebasestorage.googleapis.com/v0/b/archsmarter-68e3e.appspot.com/o/user_profile%2Fdefault.jpg?alt=media&token=089bd7ce-8280-461c-8c27-4b24368dbcdc"
        data = {"name": username, "email": email, "profile_photo": default_profile_photo_url}
        db.child("users").child(user_id).set(data)

        return jsonify(result = str(user_id)) 
    except HTTPError as err:
        return treat_http_error(err)
    except:
        return "Unknown error", 666

@app.route("/login", methods = ["POST"])
def login():   
    try_user = request.json

    email = try_user["email"]
    password = try_user["password"]

    try:
        user = auth.sign_in_with_email_and_password(email, password)
        user_id = user["localId"]
        
        global user_db

        user_db["email"] = user["email"]
        user_db["uid"] = user_id

        data = db.child("users").get()
        user_db["username"] = data.val()[user_id]["name"]

        return jsonify(result = str(user_id))
    except HTTPError as err:
        return treat_http_error(err)
    except:
        return "Unknown error", 666

@app.route("/reset_password", methods = ["POST"])
def reset_password():
    try:
        email = request.json["email"]
        auth.send_password_reset_email(email)

        return jsonify(result = "true") 
    except HTTPError as err:
        return treat_http_error(err)
    except:
        return "Unknown error", 666

@app.route("/change_photo", methods = ["POST"])
def change_photo():
    if 'file' not in request.files:
        print ('no file in request')
        return 'no file in request'
        
    user_id = request.form.get('userId')
    image_file = request.files.get('file', '')
    image_file.save("profile.jpg")

    path = "user_profile/" + user_id + "/profile.jpg"

    try:
        stg.child(path).put("profile.jpg")
        url = stg.child(path).get_url(None)

        user_info = db.child("users").child(user_id).get().val()
        data = {"name": user_info["name"], "email": user_info["email"], "profile_photo": url}
        db.child("users").child(user_id).set(data)

        return jsonify(result = url)
    except HTTPError as err:
        return treat_http_error(err)
    except:
        return "Unknown error", 666

@app.route("/get_user_info", methods = ["GET"])
def get_user_info():
    user_id = request.args.get('userId')

    try:
        user_info = db.child("users").child(user_id).get().val()

        return jsonify(result = user_info)
    except HTTPError as err:
        return treat_http_error(err)
    except:
        return "Unknown error", 666

@app.route("/send_feedback", methods = ["POST"])
def send_feedback():
    user_id = request.json["userId"]
    feedback = request.json["feedback"]

    try:
        username = db.child("users").get().val()[user_id]["name"]
        
        data = {"username": username, "feedback": feedback}
        db.child("feedback").push(data)

        return jsonify(result = "true")
    except HTTPError as err:
        return treat_http_error(err)
    except:
        return "Unknown error", 666

@app.route("/get_feedback", methods = ["GET"])
def get_feedback():
    try:
        data = db.child("feedback").get().val()

        if not data:
            return jsonify(result = [])

        return jsonify(result = data)
    except HTTPError as err:
        return treat_http_error(err)
    except:
        return "Unknown error", 666

@app.route("/delete_image", methods = ["POST"])
def delete_image():
    try:
        user_id = request.json["userId"]
        photo_id = request.json["photoId"]

        path = "user_buildings/" + user_id + "/" + photo_id + ".jpg"
        
        stg.delete(path)
        db.child("buildings").child(photo_id).remove()
        
        data = db.child("common_gallery").get().val()

        if not data:
            return jsonify(result = "true")
        
        delete_key = ""
        for key in data:
            if data[key]["photoId"] == photo_id:
                delete_key = key

        if delete_key != "":
            db.child("common_gallery").child(delete_key).remove()

        return jsonify(result = "true") 
    except HTTPError as err:
        return treat_http_error(err)
    except:
        return "Unknown error", 666

@app.route("/add_image", methods = ["POST"])
def add_image():
    if 'file' not in request.files:
        print ('no file in request')
        return 'no file in request'

    user_id = request.form.get('userId')
    latitude = request.form.get('latitude')
    longitude = request.form.get('longitude')
    style = request.form.get('style')
    address = request.form.get('address')

    date_time = datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
    photo_id = uuid.uuid4().hex

    image_file = request.files.get('file', '')
    image_file.save("temp.jpg")

    path = "user_buildings/" + user_id + "/" + photo_id + ".jpg"

    data = {"userId": user_id, "latitude": latitude, "longitude": longitude, "style": style, "address": address, "favorite": False, "datetime": date_time}

    try:
        stg.child(path).put("temp.jpg")

        db.child("buildings").child(photo_id).set(data)

        return jsonify(photoId = photo_id)
    except HTTPError as err:
        return treat_http_error(err)
    except:
        return "Unknown error", 666

@app.route("/get_images", methods = ["GET"])
def get_images():
    user_id = request.args.get('userId')
    
    datas = []
    try:
        files = stg.child("").list_files()

        for file in files:
            if user_id in file.name:
                photo_id = file.name.split('/')[-1].split('.')[0]
                
                data = db.child("buildings").child(photo_id).get().val()
                
                if data is None:
                    continue

                id = len(datas)
                style = data["style"]
                latitude = data["latitude"]
                longitude = data["longitude"]
                datetime = data["datetime"]
                address = data["address"]
                favorite = data["favorite"]

                url = stg.child(file.name).get_url(None)

                image_obj = image_info(id, photo_id, style, url, latitude, longitude, address, favorite, datetime)
                datas.append(image_obj.__dict__)

        return jsonify(result = datas)
    except HTTPError as err:
        return treat_http_error(err)
    except:
        return "Unknown error", 666

@app.route('/favorite_status', methods = ['POST'])
def change_favourite_status():
    photo_id = request.json["photoId"]
    is_favorite = request.json["isFavorite"]

    try:
        data = db.child("buildings").child(photo_id).get().val()
        data["favorite"] = is_favorite
        db.child("buildings").child(photo_id).set(data)

        return jsonify(result = "true")
    except HTTPError as err:
        return treat_http_error(err)
    except:
        return "Unknown error", 666

@app.route('/share_photo', methods = ['POST'])
def share_photo():
    user_id = request.json["userId"]
    photo_id = request.json["photoId"]
    photo_url = request.json["photoUrl"]
    arch_style = request.json["archStyle"]
    message = request.json["message"]

    username = db.child("users").get().val()[user_id]["name"]

    try:
        data = { "photoId": photo_id, "photoUrl": photo_url, "archStyle": arch_style, "voteUserIds": [user_id], "postedBy": username, "message": message }
        db.child("common_gallery").push(data)

        return jsonify(result = "true")
    except HTTPError as err:
        return treat_http_error(err)
    except:
        return "Unknown error", 666

@app.route('/was_shared', methods = ['GET'])
def was_shared():
    user_id = request.json["userId"]
    photo_url = request.json["photoUrl"]

    try:
        data = db.child("common_gallery").get().val()

        for key in data:
            saved_url = data[key]["photoUrl"]
            if saved_url == photo_url:
                return jsonify(shared = "true")

        return jsonify(shared = "false")
    except HTTPError as err:
        return treat_http_error(err)
    except:
        return "Unknown error", 666

@app.route('/shared_photos', methods = ['GET'])
def shared_photos():
    try:
        data = db.child("common_gallery").get().val()

        result = []
        if not data:
            return jsonify(result = result)
        
        for key in data:
            result.append(data[key])
        
        return jsonify(result = result)
    except HTTPError as err:
        return treat_http_error(err)
    except:
        return "Unknown error", 666

@app.route('/vote_photo', methods = ['POST'])
def vote_photo():
    user_id = request.json["userId"]
    photo_id = request.json["photoId"]

    try:
        data = db.child("common_gallery").get().val()
        
        for key in data:
            if data[key]["photoId"] == photo_id:
                data[key]["voteUserIds"].append(user_id)
                break
        
        db.child("common_gallery").set(data)
        return jsonify(result = "true")
    except HTTPError as err:
        return treat_http_error(err)
    except:
        return "Unknown error", 666

@app.route('/arch_recognition', methods = ['POST'])
def request_board_analyze():
    if 'file' not in request.files:
        print ('no file in request')
        return 'no file in request'

    image_name = 'file.jpg'

    image_file = request.files.get('file', '')
    image_file.save(image_name)

    arch = ar.determine_arch(image_name, mobilenet_model, cnn_model, scaler)
    print (arch)

    return jsonify(arch = str(arch))

if __name__ == '__main__':
    app.run(host = '0.0.0.0', port = 3000, threaded = False)

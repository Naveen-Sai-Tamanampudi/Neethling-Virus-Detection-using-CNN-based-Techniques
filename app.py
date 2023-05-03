from flask import Flask, render_template, request,redirect, url_for, session
from flask_session import Session
import urllib, hashlib
from pymongo import MongoClient
from scipy import stats
from efficientnet.tfkeras import EfficientNetB4

def create_app():
    client= MongoClient("mongodb+srv://naveen:"+urllib.parse.quote("tns@9900")+"@capstone-project.1aslv4m.mongodb.net/test")

    from tensorflow.keras.models import load_model
    from tensorflow.keras.preprocessing import image

    model1 = load_model('../Code/Considerable DL Models/inception_15.h5')
    model2 = load_model('../Code/Considerable DL Models/efficient_15.h5')
    model3 = load_model('../Code/Considerable DL Models/VGG_15.h5')

    model1.make_predict_function()
    model2.make_predict_function()
    model3.make_predict_function()


    def predict_label(img_path,model):
        i = image.load_img(img_path, target_size=(256,256))
        i = image.img_to_array(i)/255.0
        i = i.reshape(1, 256,256,3)
        p = model.predict(i)
        return p


    app=Flask(__name__)
    app.db=client.SDP
    SESSION_TYPE = 'filesystem'
    app.config.from_object(__name__)
    Session(app)


    @app.route("/")
    def home():
        return render_template("home.html")

    @app.route("/register",methods=["GET","POST"])
    def register():
        if request.method == "POST":
            username = request.form.get("username")
            email=request.form.get("email")
            phone=request.form.get("phone")
            pwd = request.form.get("password")

            details=[username,email,phone,pwd]
            for i in details:
                if i=='':
                    return render_template("register.html", str="One/More Fields are Empty.")

            if app.db.users.count_documents({"username" : username}) != 0 or app.db.users.count_documents({"email" : email}):
                return render_template("register.html",str="Please choose a different Username/Email-ID")

            password=hashlib.sha256(pwd.encode())
            app.db.users.insert_one({"username":username, "password":password.hexdigest(),"email":email,"phone":phone})
            return redirect(url_for('login'))
        return render_template("register.html")

    @app.route("/login", methods=["GET","POST"])
    def login():
        if request.method == "POST":
            id = request.form.get("username")
            pwd = request.form.get("password")
            password=hashlib.sha256(pwd.encode())
            if app.db.users.count_documents({"username" : id,"password":password.hexdigest()}) == 1 or app.db.users.count_documents({"email" : id,"password":password.hexdigest()}):
                session['user']=id
                return redirect(url_for('predict'))
            else:
                return render_template("login.html",str="Incorrect Username/Email-ID or Password")
        return render_template("login.html",str="")

    @app.route("/details")
    def details():
        if app.db.users.count_documents({"username" : session["user"]}) != 0:
            res=app.db.users.find_one({"username":session["user"]})
            return render_template("details.html",res=res)
        
        res=app.db.users.find_one({"email":session["user"]})
        return render_template("details.html",res=res)

    @app.route("/logout")
    def logout():
        session["user"]=""
        return redirect(url_for('login'))

    @app.route("/predict", methods=["GET","POST"])
    def predict():
        if request.method=="GET":
            if not session["user"]:
                return redirect(url_for('login'))

        if request.method == "POST":
            img = request.files['image']
            img_path = "static/" + img.filename	
            if img_path=="static/":
                return render_template("predict.html",str="Please choose an image to predict")
            img.save(img_path)

            out1=1 if predict_label(img_path,model1)>0.5 else 0
            out2=1 if predict_label(img_path,model2)>0.5 else 0
            out3=1 if predict_label(img_path,model3)>0.5 else 0
            
            out=stats.mode([out1,out2,out3])[0]
            if(out==0):
                return render_template("predict.html", str="The Cow/Buffalo is affected by Neethling Virus")
            else:
                return render_template("predict.html", str="The Cow/Buffalo is Healthy")
        return render_template("predict.html",str="")
    return app

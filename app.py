import os
from flask import (
    Flask, flash, render_template,
    redirect, request, session, url_for)
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
if os.path.exists("env.py"):
    import env

#   CONFIRGURATION
app = Flask(__name__)

app.config["MONGO_DBNAME"] = os.environ.get("MONGO_DBNAME")
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
app.secret_key = os.environ.get("SECRET_KEY")

mongo = PyMongo(app)


@app.route("/")
def get_smoothies():
    smoothies = mongo.db.smoothies.find()
    return render_template("index.html", smoothies=smoothies)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # to check if the username already exists in the db
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            flash("Username already exists")
            return redirect(url_for("register"))

        register = {
            "username": request.form.get("username").lower(),
            "firstname": request.form.get("firstname"),
            "lastname": request.form.get("lastname"),
            "email": request.form.get("email").lower(),
            "password": generate_password_hash(request.form.get("password"))
        }
        mongo.db.users.insert_one(register)

        # put the new user in to 'session' cookie
        session['user'] = request.form.get("username").lower()
        flash("Registration Successful!")
        return redirect(url_for("profile", username=session["user"]))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # check if username already exists in db
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            # ensure hashed password matches user input
            if check_password_hash(
                    existing_user["password"], request.form.get("password")):
                session["user"] = request.form.get("username").lower()
                flash("Welcome, {}".format(
                    request.form.get("username")))
                return redirect(url_for(
                    "profile", username=session["user"]))
            else:
                # invalid password match
                flash("Incorrect Username and/or Password")
                return redirect(url_for("login"))

        else:
            # username doesn't exist
            flash("Incorrect Username and/or Password")
            return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/profile/<username>", methods=["GET", "POST", "DELETE"])
def profile(username):
    if request.method == "GET":
    # grab the user's username from the db
        user = mongo.db.users.find_one(
            {"username": session["user"]})
    # username = mongo.db.users.find_one(
    #     {"username": session["user"]})["username"]

        if session["user"]:
            return render_template("add_smoothie.html", user=user)

        return redirect(url_for("login"))


@app.route("/delete/<username>", methods=["POST"])
def delete_profile(username):
    if request.method == "POST":
        mongo.db.users.delete_one(
            {"username": session["user"]})
        session["user"] = None
        return render_template("delete.html")


@app.route("/edit_profile/<username>", methods=["GET", "POST"])
def edit_profile(username):
    if request.method == "POST":
        # to check if the username already exists in the db

        edit_profile = {
            "firstname": request.form.get("firstname"),
            "lastname": request.form.get("lastname"),
            "email": request.form.get("email").lower(),
            "password": generate_password_hash(request.form.get("password"))
        }
        mongo.db.users.update_one({"username": username},
        {"$set": edit_profile})

        # put the new user in to 'session' cookie
        return redirect(url_for("profile", username=session["user"]))

    elif request.method == "GET":
        user = mongo.db.users.find_one(
            {"username": username})

        if user:
            return render_template("edit_profile.html", user=user)


@app.route("/logout")
def logout():
    # remove user from session cookies
    flash("You have been logged out")
    session.pop("user")
    return redirect(url_for("login"))


def format_columns(columns):
    output = []
    for string in columns:
        string = string.split("_")
        string_list = []
        for word in string:
            if word != "id":
                word = word.title()
                string_list.append(word)
        final_column = " ".join(string_list)
        if len(final_column) > 0:
            output.append(final_column)
    return output


@app.route("/smoothie", methods=["GET", "POST"])
def smoothie():
    categories = mongo.db.categories.find().sort("category_name", 1)
    categories = list(categories)
    if request.method == "POST":
        smoothie = {
            "category_name": request.form.get("category")
        }
        smoothies = mongo.db.smoothies.find(smoothie)
        if type(smoothies[0]) == dict:
            cols = smoothies[0].keys()
            #   formatting required for front-end. Cols value to be a list.
            cols = format_columns(cols)
        else:
            cols = []
        return render_template(
            "smoothie.html", categories=categories,
            results=smoothies, columns=cols)
    return render_template("smoothie.html", categories=categories)


@app.route("/get_categories")
def get_categories():
    categories = list(mongo.db.categories.find().sort("category_name", 1))
    return render_template("categories.html", categories=categories)


if __name__ == "__main__":
    app.run(host=os.environ.get("IP"),
            port=int(os.environ.get("PORT")),
            debug=True)

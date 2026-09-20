from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, make_response, session
from flask_bcrypt import Bcrypt
from flask_login import login_user, login_required, logout_user, current_user
from models import db, User
import werkzeug.exceptions
from werkzeug.utils import secure_filename
import os
import server_utils


login_bp = Blueprint('login_bp', __name__)
bcrypt = Bcrypt()

# signup functions
# signup form
@login_bp.route('/signup_form')
def signup_form():
    return render_template("signup_form_test.html")

# signup action
@login_bp.route('/signup', methods=['POST'])
def signup():
    email = request.form.get('email')
    name = request.form.get('username')
    password = request.form.get('password')
    
    # redirect path
    redir = request.form.get('redir')

    # not all forms filled out
    if not (email and name and password):
        flash('Please fill out all forms before signing up.')
        return redirect(redir + "?signup")
    
    # check for duplicate email
    user = User.query.filter_by(email=email).first()
    if(user is not None):
        flash('Email address already in use')
        return redirect(redir + "?signup")
    

    new_user = User(email=email, name=name, password=password)
    db.session.add(new_user)
    db.session.commit()
    login_user(new_user)

    flash('Successfully signed up')
    return redirect(redir)

# LOGIN FORM
@login_bp.route('/login_form')
def login_form():
    return render_template("login_form_test.html")


# LOGIN ACTION
@login_bp.route('/login', methods=['POST'])
def login():
    # get form data
    email = request.form.get('email')
    password = request.form.get('password')
    remember = request.form.get('remember', default = False)
    # redirect path
    redir = request.form.get('redir')

    # search for a user with the entered email
    user = User.query.filter_by(email=email).first()
    # validate credentials
    if (user) and (bcrypt.check_password_hash(user.password, password)):
        if(user.is_2fa_enabled == True): # 2FA is enabled
            session["email"] = email # store user email in session to use with the OTP form (can't be modified on user end)
            if(redir is not None):
                return redirect(url_for("login_bp.otp_check") + "?remember=" + str(remember) + "&redir=" + redir)
            else:
                return redirect(url_for("login_bp.otp_check") + "?remember=" + str(remember))
        else:
            user.authenticated = True
            db.session.add(user)
            db.session.commit()
            login_user(user, remember=remember)
        # correct login
        return redirect(redir)
    
    # incorrect login
    flash('Login failed, incorrect username or password.')
    return redirect(redir + "?login")

## OTP
# OTP checking form
@login_bp.route('/otp_check', methods=['POST', 'GET'])
def otp_check():
    if(session['email'] is None):
        return redirect("/")
    # redirect path and remember option
    redir = request.args.get('redir', default="/")
    remember = request.args.get('remember', default=False, type=bool)

    return render_template("otp_check.html", redir = redir, remember = remember)

@login_bp.route('/verify_otp', methods=['POST'])
def verify_otp():
    
    if(current_user.is_authenticated):
        # user is doing 2fa setup or adding a new device
        code = request.form["code"]
        if current_user.verify_otp(code) is True: 
            current_user.is_2fa_enabled = True
            db.session.commit()
            flash("2FA successfully enabled!")
            return redirect(url_for("interface_bp.account_pg"))
        else:
            flash("Incorrect code.")
            return redirect(url_for("login_bp.setup_otp"))
    else:
        code = request.form.get("code", default="")
        redir = request.form.get("redir", default="/")
        remember = request.form.get("remember", default=False, type=bool)
        user = User.query.filter_by(email=session["email"]).first() # get user based on session email

        if user.verify_otp(code) is True: # code is correct, log in user
            user.authenticated = True
            db.session.add(user)
            db.session.commit()
            login_user(user, remember=remember)
            return redirect(redir)
        else: # code is incorrect
            flash("Incorrect code.")
            return redirect(url_for("login_bp.otp_check") + "?remember=" + str(remember))
    
#OTP setup page
@login_bp.route('/setup_otp')
@login_required
def setup_otp():
   return(render_template("otp_setup.html"))
   pass



# pages that need a login to view

@login_bp.route('/log_out')
@login_required
def log_out():
    logout_user()
    return redirect(url_for('interface_bp.home_page'))


@login_bp.route('/login_test')
@login_required
def login_test():
    return render_template('login_check.html', username=current_user.name)

## UPLOAD PFP


@login_bp.route('/upload_profile_image', methods=['POST'])
@login_required
def upload_pfp():
    user_page = url_for('interface_bp.account_pg')
    # check if a file was uploaded
    if 'file' not in request.files:
        flash('Profile image file not uploaded.')
        return redirect(user_page)
    file = request.files['file']

    upload_success = server_utils.upload_image(file, "profiles", current_user.id)

    if(upload_success[0] == False):
        flash(upload_success[1])
        return redirect(user_page)
    else:
        current_user.pfp_url = upload_success[1]
        db.session.commit()

    return redirect(user_page)

## UPDATE USER DATA

@login_bp.route('/update_user_data', methods=['POST'])
@login_required
def update_user_data():
    email = request.form.get("email")
    username = request.form.get("username")

    # check username length
    if(len(username) > 48):
        flash("Username too long, must be 48 characters or shorter.")
        response = make_response("Updating user data failed.")
        response.mimetype = "text/plain"
        return response

    current_user.email = email
    current_user.name = username
    db.session.commit()

    flash("User data updated!")
    response = make_response("User credentials updated.")
    response.mimetype = "text/plain"
    return response

@login_bp.route('/update_user_password', methods=['POST'])
@login_required
def update_user_password():
    password = request.form.get("password")

    current_user.password = bcrypt.generate_password_hash(password)
    flash("Password updated!")
    return redirect(url_for('interface_bp.account_pg'))


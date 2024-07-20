# import statements
from flask import Flask, render_template, url_for, redirect, session, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user
from flask_wtf import FlaskForm
from wtforms import PasswordField, SubmitField, EmailField
from wtforms.validators import InputRequired, Length, Email
from flask_bcrypt import Bcrypt
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib, random, string, re
from math import radians, sin, cos, sqrt, atan2
import os

# Create an absolute path for the database file
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, 'database.db')

# initializes Flask app with a database URI and a secret key for session management
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_PATH}'
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'thisisasecretkey')

# initializes database and password hashing
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

# initializes login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# sets up a user loader to extract user data from the database
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# define User model in the database with various columns
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(80), nullable=False)
    code = db.Column(db.String(6), nullable=False)

# Ensure the database is initialized within an application context
with app.app_context():
    print("Creating all database tables...")
    db.create_all()
    print("All tables created.")

# define various forms
class RegisterForm(FlaskForm):
    username = EmailField(validators=[InputRequired(), Email(), Length(min=4, max=100)], render_kw={"placeholder": "Email"})
    password = PasswordField(validators=[InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Password"})
    submit = SubmitField("Register")

class LoginForm(FlaskForm):
    username = EmailField(validators=[InputRequired(), Email(), Length(min=4, max=100)], render_kw={"placeholder": "Email"})
    password = PasswordField(validators=[InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Password"})
    submit = SubmitField("Login")


class ConfirmForm(FlaskForm):
    username = EmailField(validators=[InputRequired(), Email(), Length(min=4, max=100)], render_kw={"placeholder": "Email"})
    submit = SubmitField("Confirm")

class CodeForm(FlaskForm):
    code = PasswordField(validators=[InputRequired(), Length(min=6, max=6)], render_kw={"placeholder": "Authentication Code"})
    submit = SubmitField("Submit")

class ResetForm(FlaskForm):
    password = PasswordField(validators=[InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Password"})
    submit = SubmitField("Confirm")

# route for login, it checks if the input matches the data in the database and redirects the user if true
@app.route('/', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user)
            return redirect(url_for('home'))
        else:
            flash('Invalid username or password', 'danger')
    return render_template('login.html', form=form)

# route to handle logout which redirects user back to login page
@app.route('/logout', methods=['GET', 'POST'])
def logout():
    logout_user()
    return redirect(url_for('login'))

# route for homepage
@app.route('/home', methods=['GET', 'POST'])
@login_required
def home():
    return render_template('home.html')

# generate, hash and store a 6-digit code
def generate_and_store_code():
    code = ''.join(random.choices(string.digits, k=6))
    hashed_code = bcrypt.generate_password_hash(code).decode('utf-8')
    session['code'] = hashed_code
    return code

# route to handle register. It checks if the email already exists then it will give error message.
# If not, generates and stores code, sends to user's email and redirects to authentication page
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        existing_user_username = User.query.filter_by(username=form.username.data).first()
        if existing_user_username:
            flash('That email already exists, choose a different email', 'danger')
        else:
            code = generate_and_store_code()
            session['username'] = form.username.data
            session['password'] = form.password.data
            send_authentication_email(form.username.data, code)
            flash('An authentication code has been sent to your email.', 'info')
            return redirect(url_for('code_reg'))
    return render_template('register.html', form=form)

# route to handle authentication code for register. checks if the input matches the code, if yes, adds the user and redirects to login
@app.route('/code_reg', methods=['GET', 'POST'])
def code_reg():
    form = CodeForm()
    if form.validate_on_submit():
        entered_code = form.code.data
        stored_code = session.get('code')
        # encrypt using bcrypt
        if bcrypt.check_password_hash(stored_code, entered_code):
            session.pop('code')
            hashed_password = bcrypt.generate_password_hash(session['password']).decode('utf-8')
            new_user = User(username=session['username'], password=hashed_password, code="000000")
            db.session.add(new_user)
            db.session.commit()
            session.pop('username')
            session.pop('password')
            flash('Registration successful. You can now log in.', 'success')
            return redirect(url_for('login'))
        else:
            flash('Invalid code. Please try again.', 'danger')
    return render_template('code_reg.html', form=form)

# ask for email input. If email matches, sends code to the email and redirects to check code page
@app.route('/confirm', methods=['GET', 'POST'])
def confirm():
    form = ConfirmForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            code = generate_and_store_code()
            session['username'] = form.username.data
            send_authentication_email(form.username.data, code)
            flash('An authentication code has been sent to your email.', 'info')
            return redirect(url_for('check_code'))
        else:
            flash('Email does not exist in our records. Please enter a valid email.', 'danger')
    return render_template('confirm.html', form=form)

# route to check the authentication code. If the code matches, redirects the user to reset page
@app.route('/code', methods=['GET', 'POST'])
def check_code():
    form = CodeForm()
    if form.validate_on_submit():
        entered_code = form.code.data
        stored_code = session.get('code')
        if stored_code and bcrypt.check_password_hash(stored_code, entered_code):
            session.pop('code')
            return redirect(url_for('reset'))
        else:
            flash('Invalid code. Please try again.', 'danger')
    return render_template('code.html', form=form)

# route for change password page
@app.route('/reset', methods=['GET', 'POST'])
def reset():
    form = ResetForm()
    # retrieve the user from the session. If not matched, redirects to confirm
    username = session.get('username')
    if not username:
        return redirect(url_for('confirm'))
    # check if the user exists in the database; if not, redirect to the 'confirm' route
    user = User.query.filter_by(username=username).first()
    if not user:
        return redirect(url_for('confirm'))

    if form.validate_on_submit():
        # encrypt again the new password
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user.password = hashed_password
        db.session.commit()
        session.pop('username')
        flash('Password reset successful. You can now log in with your new password.', 'success')
        return redirect(url_for('login'))
        
    return render_template('reset.html', form=form)

# function to send authentication email containing a code
def send_authentication_email(username, code):
    smtp_server = 'smtp.gmail.com'
    smtp_port = 587
    email_user = 'hieuminh23405@gmail.com'  # Replace with your email
    email_password = 'ztls pfjz xddh xuup'     # Replace with your password

    smtp = smtplib.SMTP(smtp_server, smtp_port)
    smtp.ehlo()
    smtp.starttls()
    smtp.login(email_user, email_password)

    msg = MIMEMultipart()
    msg['Subject'] = "Authentication Code"
    msg.attach(MIMEText(f"This is the authentication code: {code}", 'plain'))

    smtp.sendmail(from_addr=email_user, to_addrs=username, msg=msg.as_string())
    smtp.quit()



# route for about us page
@app.route('/about', methods=['GET', 'POST'])
def about():
    return render_template('about.html')

# Calculate distance between two points using Haversine formula
def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0  # Earth radius in kilometers
    dlat = radians(lat2 - lat1)
    dlon = radians(lon1 - lon2)
    a = sin(dlat / 2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    distance = R * c
    return distance

# creating lists to store GPS and calculated data
def process_csv_data(csv_files):
    all_data = []
    total_distances = []
    total_time_seconds_all = []
    average_speeds = []
    fuel_consumptions = []

    for csv_file in csv_files:
        previous_lat = None
        previous_lon = None
        total_distance = 0
        total_time_seconds = 0

        data_list = []

        # open the CSV file
        with open(csv_file, 'r') as file:
            # iterate over each line in the file
            for line in file:
                # remove any trailing newline characters
                line = line.strip()

                try:
                    # split the string into time and coordinates part
                    time_part, coords_part = line.split(',', 1)

                    # extract time
                    time = time_part.split('T')[1].split('.')[0]  # Extracts time part excluding milliseconds and 'Z'
                    time_in_seconds = sum(int(x) * 60 ** i for i, x in enumerate(reversed(time.split(':'))))

                    # extract coordinates
                    coordinates = re.search(r'{"lat":([\d.]+),"lon":([\d.]+)}', coords_part)
                    if coordinates:
                        lat = float(coordinates.group(1))
                        lon = float(coordinates.group(2))
                    else:
                        continue  # skip lines where the coordinates do not match the pattern

                    # calculate distance from the previous point
                    distance = 0
                    if previous_lat is not None and previous_lon is not None:
                        distance = haversine(previous_lat, previous_lon, lat, lon)
                        total_distance += distance
                        total_time_seconds += (time_in_seconds - previous_time_in_seconds)

                    previous_lat = lat
                    previous_lon = lon
                    previous_time_in_seconds = time_in_seconds

                    """
                    Explanation of why there is a list and a dictionary for storing data.
                    Lists of Dictionaries: Detailed storage of individual GPS data points.
                    Aggregated Lists: Efficient storage of summary metrics for quick access and computation.
                    """

                    # store the parsed data into a list of dictionaries
                    data = {
                        'time': time,
                        'latitude': lat,
                        'longitude': lon,
                        'distance': distance
                    }
                    data_list.append(data)
                
                except (IndexError, ValueError):
                    # handle the case where the line does not match the expected format
                    continue

        # calculate total time spent and fuel consumption
        total_time_hours = total_time_seconds / 3600
        # formula for motorbike
        fuel_consumption = total_distance / 50.4

        # calculate average speed (total_distance in km / total_time_seconds in hours)
        if total_time_seconds > 0:
            average_speed = total_distance / total_time_hours
        else:
            average_speed = 0

        # round calculations for display
        total_distance = round(total_distance, 2)
        average_speed = round(average_speed, 2)
        fuel_consumption = round(fuel_consumption, 2)

        # format total time for display
        total_time = f'{total_time_seconds // 3600}h {total_time_seconds % 3600 // 60}m {total_time_seconds % 60}s'

        all_data.append(data_list)
        total_distances.append(total_distance)
        total_time_seconds_all.append(total_time_seconds)
        average_speeds.append(average_speed)
        fuel_consumptions.append(fuel_consumption)

    return all_data, total_distances, total_time_seconds_all, average_speeds, fuel_consumptions

# route for map page
@app.route('/map')
def map():
    csv_files = ['gps.csv', 'gps_1.csv', 'gps_2.csv']  # List of CSV files
    all_data, total_distances, total_time_seconds_all, average_speeds, fuel_consumptions = process_csv_data(csv_files)

    # format total time for display
    total_times = [
        f'{total_time_seconds // 3600}h {total_time_seconds % 3600 // 60}m {total_time_seconds % 60}s'
        for total_time_seconds in total_time_seconds_all
    ]

    return render_template('map.html', data=all_data, total_distances=total_distances, average_speeds=average_speeds, fuel_consumptions=fuel_consumptions, total_times=total_times)

# route for feedback page
@app.route('/feedback', methods=['GET', 'POST'])
def feedback():
    if request.method == 'POST':
        country = request.form['country']
        subject = request.form['subject']
        return redirect(url_for('thank_you'))
    return render_template('feedback.html')

# route for thank you page
@app.route('/thank')
def thank_you():
    return render_template('thank.html')

# run the app
if __name__ == '__main__':
    app.run(debug=True)

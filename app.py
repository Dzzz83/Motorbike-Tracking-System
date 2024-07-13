from flask import Flask, render_template, url_for, redirect, session, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user
from flask_wtf import FlaskForm
from wtforms import PasswordField, SubmitField, EmailField
from wtforms.validators import InputRequired, Length, ValidationError, Email
from flask_bcrypt import Bcrypt
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib, random, string, re
from math import radians, sin, cos, sqrt, atan2

# Initialize Flask app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SECRET_KEY'] = "thisisasecretkey"

# Initialize database
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

# Initialize login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Define User model
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(80), nullable=False)
    code = db.Column(db.String(6), nullable=False)

# Define forms
class RegisterForm(FlaskForm):
    username = EmailField(validators=[InputRequired(), Email(), Length(min=4, max=100)], render_kw={"placeholder": "Email"})
    password = PasswordField(validators=[InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Password"})
    submit = SubmitField("Register")

    def validate_username(self, username):
        existing_user_username = User.query.filter_by(username=username.data).first()
        if existing_user_username:
            raise ValidationError("That username already exists. Please choose a different name.")

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


# Function to handle logout
@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# Route for homepage
@app.route('/home', methods=['GET', 'POST'])
@login_required
def home():
    return render_template('home.html')

# Generate, hash and store a 6-digit code
def generate_and_store_code():
    code = ''.join(random.choices(string.digits, k=6))
    hashed_code = bcrypt.generate_password_hash(code).decode('utf-8')
    session['code'] = hashed_code
    return code
# route to handle register
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        code = generate_and_store_code()
        session['username'] = form.username.data
        session['password'] = form.password.data
        send_authentication_email(form.username.data, code) # send the code to the registered email
        flash('An authentication code has been sent to your email.', 'info')
        return redirect(url_for('code_reg'))
    return render_template('register.html', form=form)

# route to handle authentication code for register
@app.route('/code_reg', methods=['GET', 'POST'])
def code_reg():
    form = CodeForm()
    if form.validate_on_submit():
        entered_code = form.code.data
        stored_code = session.get('code')
        # encrypt using bycrypt
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


@app.route('/confirm', methods=['GET', 'POST'])
def confirm():
    form = ConfirmForm()
    if form.validate_on_submit():
        code = generate_and_store_code()
        session['username'] = form.username.data
        send_authentication_email(form.username.data, code)
        flash('An authentication code has been sent to your email.', 'info')
        return redirect(url_for('check_code'))
    return render_template('confirm.html', form=form)


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


@app.route('/reset', methods=['GET', 'POST'])
def reset():
    form = ResetForm()
    username = session.get('username')
    if not username:
        return redirect(url_for('confirm'))
    
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


# Function to send authentication email containing a code
def send_authentication_email(username, code):
    smtp = smtplib.SMTP('smtp.gmail.com', 587)
    smtp.ehlo()
    smtp.starttls()
    smtp.login('hieuminh23405@gmail.com', 'ztls pfjz xddh xuup')

    msg = MIMEMultipart()
    msg['Subject'] = "Authentication Code"
    msg.attach(MIMEText(f"This is the authentication code: {code}", 'plain'))

    smtp.sendmail(from_addr="your_email@gmail.com", to_addrs=username, msg=msg.as_string())
    smtp.quit()

# Route for about us page
@app.route('/about', methods=['GET', 'POST'])
def about():
    return render_template('about.html')

# Calculate distance between two points
def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0  # Earth radius in kilometers
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    distance = R * c
    return distance

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
        first_time = None

        data_list = []

        # Open the CSV file
        with open(csv_file, 'r') as file:
            # Iterate over each line in the file
            for line in file:
                # Remove any trailing newline characters
                line = line.strip()

                try:
                    # Split the string into time and coordinates part
                    time_part, coords_part = line.split(',', 1)

                    # Extract time
                    time = time_part.split('T')[1].split('.')[0]  # Extracts time part excluding milliseconds and 'Z'
                    time_in_seconds = sum(int(x) * 60 ** i for i, x in enumerate(reversed(time.split(':'))))

                    # Extract coordinates
                    coordinates = re.search(r'{"lat":([\d.]+),"lon":([\d.]+)}', coords_part)
                    if coordinates:
                        lat = float(coordinates.group(1))
                        lon = float(coordinates.group(2))
                    else:
                        continue  # Skip lines where the coordinates do not match the pattern

                    # Calculate distance from the previous point
                    distance = 0
                    if previous_lat is not None and previous_lon is not None:
                        distance = haversine(previous_lat, previous_lon, lat, lon)
                        total_distance += distance
                        total_time_seconds += (time_in_seconds - previous_time_in_seconds)
                    else:
                        first_time = time_in_seconds

                    previous_lat = lat
                    previous_lon = lon
                    previous_time_in_seconds = time_in_seconds

                    # Store the parsed data into a list of dictionaries
                    data = {
                        'time': time,
                        'latitude': lat,
                        'longitude': lon,
                        'distance': distance
                    }
                    data_list.append(data)
                
                except (IndexError, ValueError):
                    # Handle the case where the line does not match the expected format
                    continue

        # Calculate total time spent and fuel consumption
        total_time_hours = total_time_seconds / 3600
        fuel_consumption = total_distance / 50.4

        # Calculate average speed (total_distance in km / total_time_seconds in hours)
        if total_time_seconds > 0:
            average_speed = total_distance / total_time_hours
        else:
            average_speed = 0

        # Round calculations for display
        total_distance = round(total_distance, 2)
        average_speed = round(average_speed, 2)
        fuel_consumption = round(fuel_consumption, 2)

        # Format total time for display
        total_time = f'{total_time_seconds // 3600}h {total_time_seconds % 3600 // 60}m {total_time_seconds % 60}s'

        all_data.append(data_list)
        total_distances.append(total_distance)
        total_time_seconds_all.append(total_time_seconds)
        average_speeds.append(average_speed)
        fuel_consumptions.append(fuel_consumption)

    return all_data, total_distances, total_time_seconds_all, average_speeds, fuel_consumptions



@app.route('/map')
def map():
    csv_files = ['gps.csv', 'gps_1.csv', 'gps_2.csv']  # List of your CSV files
    all_data, total_distances, total_time_seconds_all, average_speeds, fuel_consumptions = process_csv_data(csv_files)

    # Format total time for display
    total_times = [
        f'{total_time_seconds // 3600}h {total_time_seconds % 3600 // 60}m {total_time_seconds % 60}s'
        for total_time_seconds in total_time_seconds_all
    ]

    return render_template('map.html', data=all_data, total_distances=total_distances, average_speeds=average_speeds, fuel_consumptions=fuel_consumptions, total_times=total_times)



# Route for feedback page
@app.route('/feedback', methods=['GET', 'POST'])
def feedback():
    if request.method == 'POST':
        country = request.form['country']
        subject = request.form['subject']
        return redirect(url_for('thank_you'))
    return render_template('feedback.html')

# Route for thank you page
@app.route('/thank')
def thank_you():
    return render_template('thank.html')

# Run the app
if __name__ == '__main__':
    app.run(debug=True)

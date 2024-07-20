## README

### Overview
This project is a Flask web application with user authentication, password reset functionality, GPS data processing, and data visualization on maps using Leaflet.js. The application allows users to register, log in, reset their passwords, and view their GPS data on a map.

### Features
- **User Registration and Authentication**: Users can register and log in using email and password. An authentication code is sent to the user's email for verification.
- **Password Reset**: Users can reset their passwords by confirming their email and entering an authentication code sent to their email.
- **GPS Data Processing**: The application processes CSV files containing GPS data, calculates distances, times, average speeds, and fuel consumption.
- **Map Visualization**: Visualize the GPS data on a map using Leaflet.js.
- **Feedback Form**: Users can submit feedback through a form.

### Dependencies
- Flask
- Flask-SQLAlchemy
- Flask-Login
- Flask-WTF
- WTForms
- Flask-Bcrypt
- email-validator
- smtplib
- email
- random
- string
- re
- math
- os

### Note
The code should be run with Python 3.9 or 3.8.

### Installation

#### Create and activate a virtual environment:

##### On macOS and Linux:
```bash
python3 -m venv venv
source venv/bin/activate
```

##### On Windows:
```bash
python -m venv venv
venv\Scripts\activate
```

#### Install the required packages:

##### On macOS and Linux:
```bash
pip3 install Flask Flask-SQLAlchemy Flask-Login Flask-WTF WTForms Flask-Bcrypt email-validator
```

##### On Windows:
```bash
pip install Flask Flask-SQLAlchemy Flask-Login Flask-WTF WTForms Flask-Bcrypt email-validator
```

### Run the application:

##### On macOS and Linux:
```bash
python3 app.py
```

##### On Windows:
```bash
python app.py
```

When you run the application, the `database.db` file will be automatically created in the directory.

### Configuration
- **Database URI**: Configured in `app.config['SQLALCHEMY_DATABASE_URI']`. The current setup uses SQLite.
- **Secret Key**: Set a secret key for session management in `app.config['SECRET_KEY']`.
- **Email Credentials**: Update the email credentials in the `send_authentication_email` function to enable sending emails for authentication codes.

### File Structure
- `app.py`: Main application file containing route definitions and logic.
- `templates/`: Directory containing HTML templates.
- `static/`: Directory for static files (CSS).

### Routes
- `/`: Login page.
- `/logout`: Logout route.
- `/home`: Homepage (requires login).
- `/register`: Registration page.
- `/code_reg`: Page for entering the registration authentication code.
- `/confirm`: Page for confirming the email for password reset.
- `/code`: Page for entering the password reset authentication code.
- `/reset`: Page for resetting the password.
- `/about`: About us page.
- `/map`: Page for visualizing GPS data on a map.
- `/feedback`: Feedback form page.
- `/thank`: Thank you page after submitting feedback.

### GPS Data Processing
The `process_csv_data` function reads and processes GPS data from CSV files placed directly in the project directory. It calculates distances using the Haversine formula, total time spent, average speed, and fuel consumption. The processed data is then displayed on the map.

#### CSV Files
- Ensure the CSV files (`gps.csv`, `gps_1.csv`, `gps_2.csv`) containing GPS data are placed in the project directory before running the application.
- Each CSV file should have lines in the following format:
  ```
  time_part, {"lat":latitude,"lon":longitude}
  ```
  Example:
  ```
  2024-07-19T15:23:05.000Z, {"lat":37.7749,"lon":-122.4194}
  ```

### Haversine Formula
The Haversine formula is used to calculate the great-circle distance between two points on the Earth's surface, given their latitude and longitude.

### Running the Application
To run the application, execute the following command:

##### On macOS and Linux:
```bash
python3 app.py
```

##### On Windows:
```bash
python app.py
```

### Feedback
Users can submit their feedback through the feedback form. The submitted feedback is currently redirected to a thank you page.

### Important Notes
- Ensure you have updated the email credentials in the `send_authentication_email` function.
- The database file `database.db` will be created automatically when the application is run for the first time.
- `app.py` contains a clone email credentials to send email automatically. Make sure the email credentials are correctly set up to send authentication codes.

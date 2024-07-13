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
- smtplib
- email
- random
- string
- re
- math

### Installation
1. Clone the repository:
   ```bash
   git clone <repository_url>
   cd <repository_directory>
   ```

2. Create and activate a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. Install the required packages:
   ```bash
   pip install Flask Flask-SQLAlchemy Flask-Login Flask-WTF WTForms Flask-Bcrypt
   ```

4. Set up the database:

 P/s: The "database.db" provided in the code has already been set up so you don't need to set it up again. However, you should check if the database
   is still functional by confirming 'user' appears using the command below (2) . If the database is somehow corrupted, delete 'database.db' and create a new one
   manually by using the command below (1).
  1.  Initializing 'database.db'
   ```bash
   python || python3
   from app import db
   db.create_all()
   ```
   2. To check if the database has been successfully created.
   ```bash
   sqlite3 database.db
   .tables
   ```
   If 'user' appears, the database is created successfully. 
   
  
6. Run the application:
   ```bash
   flask run
   ```

### Configuration
- **Database URI**: Configure the database URI in `app.config['SQLALCHEMY_DATABASE_URI']`. The current setup uses SQLite.
- **Secret Key**: Set a secret key for session management in `app.config['SECRET_KEY']`.
- **Email Credentials**: Update the email credentials in the `send_authentication_email` function to enable sending emails for authentication codes.

### File Structure
- `app.py`: Main application file containing route definitions and logic.
- `templates/`: Directory containing HTML templates.
- `static/`: Directory for static files (CSS).
- `gps_data/`: Directory for storing GPS data CSV files.

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
The `process_csv_data` function reads and processes GPS data from CSV files. It calculates distances using the Haversine formula, total time spent, average speed, and fuel consumption. The processed data is then displayed on the map.

### Haversine Formula
The Haversine formula is used to calculate the great-circle distance between two points on the Earth's surface, given their latitude and longitude.

### Running the Application
To run the application, execute the following command:
```bash
python app.py
```

Make sure the email credentials are correctly set up to send authentication codes.

### Feedback
Users can submit their feedback through the feedback form. The submitted feedback is currently redirected to a thank you page.

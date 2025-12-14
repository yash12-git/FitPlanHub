# FitHub - Fitness Plan Platform (Task 2)

Hi TRUEiGTECH Team,

This is my submission for the Software Engineer Task Round. I chose Task 2 (FitPlanHub).

Per the instructions allowing different tech stacks, I built this using Python (FastAPI) and MySQL because it allowed me to build a robust, type-safe backend quickly within the 12-hour deadline. The frontend is built with vanilla HTML/JS to keep it lightweight.

# Tech Stack
- Backend: Python 3.10+, FastAPI, SQLAlchemy
- Database: MySQL
- Frontend: Vanilla JavaScript, HTML5, CSS3
- Authentication: JWT (JSON Web Tokens) with Bcrypt hashing

# Features Implemented
1.  Role-Based Auth:
    - Sign up as a Client or a Coach.
    - Different dashboards based on the selected role.
2.  Coach Dashboard:
    - Create and publish workout plans.
    - View active library of uploaded plans.
3.  Client Dashboard:
    - Personal Feed: Shows workouts only from coaches the user follows.
    - Discovery: Browse a list of all coaches.
    - Interactions: Follow/Unfollow coaches.
    - Subscription Simulation: Content is locked/blurred until the user clicks "Unlock/Buy".

# Prerequisites
- Python installed.
- MySQL Server running (e.g., via MySQL Workbench or XAMPP).

# Step 1: Database Setup
1. Open your MySQL client.
2. Create a new database named `FitHub`.
3. Run the SQL script provided in `database_setup.sql` (located in the root folder) to create the tables.

# Step 2: Backend Configuration
1. Open `main.py`.
2. Go to line 20(`DB_CONNECTION`).
3. Update the `root:password` part with your local MySQL credentials.
 # Example:
 DB_CONNECTION = "mysql+pymysql://root:my_actual_password@localhost/FitHub"
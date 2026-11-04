# FIT-NEST PRO
### Smart Fitness Management & Personal Wellness Platform

FIT-NEST PRO is a Flask-powered fitness management web application designed to help users manage workouts, nutrition, body measurements, fitness goals, and personal progress through a centralized dashboard.

---

## 📌 Project Overview

FIT-NEST PRO is a web-based fitness management system developed using Python and Flask. The application provides users with tools to track their fitness activities, monitor body metrics, manage nutrition, and maintain healthy routines.

The platform also includes administrative features for reviewing and managing application activity.

## ✨ Features

### 👤 User Authentication
- User Registration and Login
- Secure Password Hashing
- Session-Based Authentication
- Separate Admin Login

### 🏋️ Workout Management
- Workout and Exercise Library
- Workout Logging
- Workout History
- Exercise Categories:
  - Chest
  - Back
  - Shoulders
  - Biceps
  - Triceps
  - Legs
- Smart Weekly Workout Planner

### 🥗 Nutrition Management
- Daily Meal Diary
- Nutrition Tracking
- Calorie Estimation
- Protein Estimation
- Smart Meal Suggestions

### 📊 Fitness Progress Tracking
- BMI Calculator
- Weight Tracking
- Progress Visualization
- Fitness Goal Management
- Body Measurements Tracking

### 💧 Wellness Tools
- Water Tracker
- Workout Timer
- Fitness Reminders
- Fitness Assistant
- Gamification System
- Points and Badges

### 🛡️ Admin Dashboard
- Separate Administrator Authentication
- Admin Dashboard
- Analytics and Statistics
- Application Activity Overview

## 🛠️ Technologies Used

| Technology | Purpose |
|---|---|
| Python | Backend Programming |
| Flask | Web Application Framework |
| SQLite | Database Management |
| HTML5 | Web Page Structure |
| CSS3 | Styling and UI Design |
| JavaScript | Interactive Functionality |
| Bootstrap 5 | Responsive UI Framework |
| Jinja2 | Template Rendering |
| Chart.js | Data Visualization |
| Werkzeug | Password Hashing and Security |

## 📂 Project Structure

```text
FIT-NEST-PRO/
│
├── Flask Project.py
├── fitnest_pro.db
├── requirements.txt
├── README.md
│
├── templates/
│   └── HTML Templates
│
├── static/
│   ├── css/
│   ├── js/
│   └── images/
│
└── .gitignore
```

*Note: The directory structure may vary depending on the project implementation.*

## ⚙️ Installation & Setup

### Prerequisites

- Python 3.10 or later
- pip
- Git

### Step 1: Clone the Repository

```bash
git clone https://github.com/YOUR-USERNAME/FIT-NEST-PRO.git
```

### Step 2: Navigate to the Project Directory

```bash
cd FIT-NEST-PRO
```

### Step 3: Create a Virtual Environment

For Windows:

```bash
python -m venv venv
```

Activate the environment:

```powershell
.\venv\Scripts\Activate.ps1
```

### Step 4: Install Dependencies

```bash
pip install -r requirements.txt
```

If the requirements file is not available:

```bash
pip install Flask
```

### Step 5: Run the Application

```bash
python "Flask Project.py"
```

### Step 6: Open in Browser

Visit the local address displayed in your terminal, usually:

```text
http://127.0.0.1:5000/
```

## 🗄️ Database

FIT-NEST PRO uses SQLite for storing application data.

The database manages information such as:

- User Accounts
- Workout Records
- Nutrition and Meal Entries
- Weight History
- Fitness Goals
- Body Measurements
- Application Data

## 📸 Screenshots

Add screenshots of your application to showcase its interface.

Suggested screenshots:

- Login Page
- User Dashboard
- Workout Planner
- Nutrition Dashboard
- Progress Tracking
- Admin Dashboard

Example:

```markdown
![FIT-NEST PRO Dashboard](screenshots/dashboard.png)
```

## 🔐 Security

- Passwords are stored using secure password hashing.
- User authentication is handled through Flask sessions.
- Secret keys should be configured using environment variables.
- Sensitive credentials should never be uploaded to GitHub.
- Database files containing private user data should be excluded from version control.

## 🎯 Project Objectives

- Develop a web-based fitness management platform.
- Provide centralized workout and nutrition tracking.
- Monitor users' fitness progress.
- Encourage healthy lifestyle habits.
- Implement authentication and database management.
- Develop a responsive and user-friendly interface.

## 🚀 Future Enhancements

- AI-Based Personalized Workout Recommendations
- Advanced Nutrition Analysis
- Fitness Report Export
- Enhanced Progress Analytics
- Cloud Database Integration
- Mobile Application Integration

## 🎓 Project Information

**Project Name:** FIT-NEST PRO  
**Project Type:** Web-Based Fitness Management System  
**Domain:** Health & Fitness Technology  
**Backend:** Python Flask  
**Database:** SQLite  
**Project Purpose:** Academic Major Project

## ⚠️ Disclaimer

FIT-NEST PRO is developed for educational and fitness-management purposes. BMI calculations, calorie estimates, and fitness recommendations are informational and should not be considered professional medical advice.

## 📄 License

This project is currently intended for educational purposes. A license can be added to define permissions for usage, modification, and distribution.

### FIT-NEST PRO
**Track Your Fitness. Manage Your Goals. Build a Healthier Lifestyle.**

# LibraFlow-Library-Management-System
A web-based Library Management System built with Python, Flask &amp; SQLite
# 📚 LibraFlow – Library Management System

A fully functional web-based Library Management System built with **Python, Flask, and SQLite**.

## 🚀 Features
- Secure login & registration (SHA-256 password hashing)
- Add, delete, and search books with quantity tracking
- Issue and return books with due date management
- Automatic overdue fine calculation (₹5/day)
- Live inventory dashboard with bar chart
- CSV export of book catalogue
- Role-based session authentication

## 🛠️ Tech Stack
| Layer | Technology |
|---|---|
| Backend | Python, Flask |
| Database | SQLite (3 normalized tables) |
| Frontend | HTML, CSS, Jinja2 Templates |
| Auth | Session-based + SHA-256 hashing |

## ⚙️ How to Run
1. Install dependencies: `pip install -r requirements.txt`
2. Run the app: `python app.py`
3. Open browser → `http://127.0.0.1:5000`
4. Login → username: `admin` | password: `1234`

## 📊 Database Schema
- **users** – accounts with hashed passwords
- **books** – catalogue with title, author, quantity
- **issued** – loan records with issue & due dates

## 👩‍💻 Author
Renushree P | B.Tech CSE (IoT) | B.S. Abdur Rahman Crescent Institute

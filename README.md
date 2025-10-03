# Car Rental Management System

![Project Banner](./assets/banner.png) <!-- Placeholder for a top banner image -->

## Overview
This project is a **Car Rental Management System** built using **Flask (Python)** and **MySQL**, with additional features like:
- Customer & Admin authentication
- Car browsing, filtering, and booking
- Rental lifecycle management (ongoing, completed, cancelled)
- Reward points & tier system (Bronze, Silver, Gold)
- Admin dashboard with revenue and activity tracking
- AI-powered FAQ Chatbot (RAG pipeline with FAISS & SentenceTransformers)

The system is designed for both **customers** (to rent cars, earn rewards, view history) and **admins** (to manage cars, customers, rentals, and revenue).

---

## Features

### Customers
- Register/Login with session management  
- Browse cars with **search, filters, sorting (price, status)**  
- Rent cars with **date validation**  
- View & complete rentals  
- Earn reward points based on spending (1 point = ₹100)  
- Track reward tier progression (Bronze → Silver → Gold)  

### Admins
- Secure admin login & session-based access control  
- Dashboard with **total revenue, active rentals, available cars, recent activities**  
- Manage customers & cars  
- Approve/Complete/Cancel rentals  
- Track customer reward points and history  

### Chatbot (RAG Integration)
- **Knowledge base powered by FAISS + SentenceTransformer**  
- Answers FAQs related to the rental system  
- Fallback response if no relevant match found  

---

## Project Structure

car-rental-system/

│

├── app.py # Main Flask app

├── templates/ # HTML Templates (Jinja2)

│ ├── home.html

│ ├── login.html

│ ├── cars.html

│ └── admin/

│ ├── admin_login.html

│ ├── admin_dashboard.html

│ └── customers.html

│

├── static/ # CSS, JS, Images

│ ├── css/

│ ├── js/

│ └── images/

│

├── combined_knowledge_base.json # Chatbot Q&A knowledge base

├── requirements.txt

└── README.md



---

## 🛠️ Tech Stack
- **Backend:** Flask (Python)
- **Database:** MySQL (with connection pooling)
- **AI/ML:** SentenceTransformers, FAISS (for chatbot RAG pipeline)
- **Frontend:** HTML, CSS, Jinja2 templates
- **Other:** dotenv for config, logging, session management

---

## 📸 Screenshots / Visuals

### 🏠 Home Page
![Home Page](./assets/home_page.png)

### 🚘 Car Listings
![Car Listings](./assets/cars.png)

### 📊 Admin Dashboard
![Admin Dashboard](./assets/admin_dashboard.png)

### 🎁 Rewards Page
![Rewards](./assets/rewards.png)

*(Add screenshots in `/assets/` folder and update the paths above)*

---

## Prerequisites
- Python 3.8+
- MySQL Server
- Virtual Environment (recommended)

---


## Rewards System

Bronze: 0 – 499 points

Silver: 500 – 999 points

Gold: 1000+ points

Points are automatically awarded on rental completion.

---

## Future Enhancements

- Real-time car availability (with sensors/GPS simulation)

- Advanced NLP for chatbot (GPT-powered responses)

- Mobile app version

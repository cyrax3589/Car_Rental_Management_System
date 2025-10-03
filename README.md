# Car Rental Management System

<img width="1898" height="429" alt="Untitled-1" src="https://github.com/user-attachments/assets/f4ddcb64-30d0-42ec-811d-bbf2d56c95f1" />



---


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

## Tech Stack
- **Backend:** Flask (Python)
- **Database:** MySQL (with connection pooling)
- **AI/ML:** SentenceTransformers, FAISS (for chatbot RAG pipeline)
- **Frontend:** HTML, CSS, Jinja2 templates
- **Other:** dotenv for config, logging, session management

---

## Screenshots / Visuals

### Home Page
<img width="1901" height="909" alt="image" src="https://github.com/user-attachments/assets/1506d8f4-0dd3-4102-8b8a-80614a2b41a9" />


### Car Listings
<img width="1895" height="341" alt="image" src="https://github.com/user-attachments/assets/009126cd-ea0d-4819-9eb8-91a6a100929e" />
<img width="1897" height="912" alt="image" src="https://github.com/user-attachments/assets/b91958d6-b594-4f6b-8c65-698f8df7eccf" />


### Admin Dashboard
<img width="1898" height="909" alt="image" src="https://github.com/user-attachments/assets/07121174-a18f-4d3d-8ce8-04e55fa3db16" />
<img width="1902" height="501" alt="image" src="https://github.com/user-attachments/assets/fde1ab95-3b7f-428c-b0ba-ac2f39233bf0" />


### Rewards Page
<img width="1895" height="910" alt="image" src="https://github.com/user-attachments/assets/70323f4e-1823-4525-857e-e6efecd96603" />
<img width="1899" height="902" alt="image" src="https://github.com/user-attachments/assets/79ce59e0-509a-46f7-8496-12de599134d0" />
<img width="1897" height="225" alt="image" src="https://github.com/user-attachments/assets/6926a162-5fb4-4276-880f-3ddd5e34fbe9" />



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

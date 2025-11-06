# 🩺 FormFlow – Dynamic Form & Workflow Management System

**FormFlow** is a Django REST Framework–based web application designed to create, manage, and automate dynamic forms and multi-step workflows. It enables authenticated users to build customizable forms, organize them into categories, collect structured responses, and define complex business processes consisting of sequential or parallel steps.  

The project aims to provide a flexible backend foundation for applications that require dynamic data collection, workflow automation, and user interaction through configurable forms.  

---

## 🧩 Project Description
FormFlow was developed as a collaborative university project with a modular and scalable architecture in mind. It separates core components into clear domains — authentication, forms, fields, responses, categories, and process management — each handling a specific layer of functionality.

Users can register, verify their account via OTP, log in securely using JWT authentication, and manage their profiles. Once authenticated, users can create forms with various question types, group them under categories, collect answers from participants, and track the flow of submissions through defined processes.

The application is backend-only but can easily integrate with any frontend client such as React, Vue, or Angular.

---

## ⚙️ Technologies Used
- **Python 3.12+**
- **Django 5+**
- **Django REST Framework**
- **PostgreSQL / SQLite**
- **JWT Authentication**
- **OTP & Email Verification**
- **Postman (for testing)**

---

## 🧠 System Architecture
FormFlow follows the **MVT (Model–View–Template)** architecture and RESTful API design principles.  
Each app is structured to ensure modularity and maintainability:

- `users/` → Authentication, registration, profile, and OTP logic  
- `forms/` → Core logic for creating and managing forms  
- `fields/` → Handles dynamic question fields within forms  
- `responses/` → Stores and manages user responses  
- `categories/` → Organizes forms into logical groups  
- `processes/` → Defines multi-step workflows and execution instances  

---

## 🚀 Installation & Setup
To set up and run the project locally:

```bash
git clone https://github.com/Tahash44/dynamic-form-flow.git
cd dynamic-form-flow
python -m venv venv
source venv/bin/activate      # or venv\Scripts\activate on Windows
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```
---
   
## 👥 Team Members

| Name | Role |
|------|------|
| Tahash44 | Team Lead |
| Alikhoshakhlagh | Backend Developer & Testing & Debugging |
| aliakbari77 | Backend Developer |
| fathali-codes | Backend Developer |
| pouryaenayati | Backend Developer |
| Mehrshad3 | Backend Developer |

---

### © 2025 Team FormFlow — Developed for Quera


# Crowdsourced Infrastructure Issue Reporter

A Django-based platform for reporting and tracking infrastructure issues in your city. Users can report issues, view their status, and upvote/downvote them without needing an account.
See my Work [Issue-Reporter](https://issue-reporter-uazm.onrender.com/)

---



## 🚀 Features

- **Report Issues**: Submit issues with location, category, description, and images.
- **Google Maps Integration**: Select locations manually or use GPS.
- **Community Voting**: Upvote/downvote issues.
- **Issue Status Tracking**: Monitor issue progress (Pending, In Progress, Resolved).
- **Before & After Comparison**: View resolved issues with images.
- **Admin Dashboard**: Manage reports and update statuses.

---



## 📌 Setup Instructions

### 1️⃣ Clone the Repository
```bash
git clone <your-repo-url>
cd backend
```

### 2️⃣ Create & Activate Virtual Environment *(Recommended)*
```bash
# On Windows
python -m venv venv
venv\Scripts\activate

# On Mac/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3️⃣ Install Dependencies
```bash
pip install -r requirements.txt
```

### 4️⃣ Apply Migrations
```bash
python manage.py migrate
```

### 5️⃣ Run the Development Server
```bash
python manage.py runserver
```

The server should now be running at `http://127.0.0.1:8000/`

---

## 🛠 Environment Variables
Create a `.env` file in the root directory and add the following:
```
SECRET_KEY=your_secret_key
DEBUG=True
GOOGLE_MAPS_API_KEY=your_google_maps_api_key
```
we have used leaflet for maps
---

## 🖼 Image Recognition API Setup
If using Hugging Face models for image verification:
```bash
pip install transformers torch
```
Or manually download models and place them in the cache as described in the documentation.

---

## 📌 Deployment
To deploy on **Heroku**, **AWS**, or any cloud service:
1. Install dependencies: `pip install gunicorn` (if using Heroku)
2. Set up environment variables on the hosting platform.
3. Configure `ALLOWED_HOSTS` in `settings.py`
4. Run `python manage.py collectstatic` before deployment.

---

## 🤝 Contributing
1. Fork the repository.
2. Create a new branch (`git checkout -b feature-branch`).
3. Make your changes and commit (`git commit -m "Your changes"`).
4. Push to the branch (`git push origin feature-branch`).
5. Open a Pull Request.

---

## 📜 License
This project is licensed under the MIT License.

### 🌟 Enjoy coding! Let me know if you need further refinements! 🚀


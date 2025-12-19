# 🏦 DummyBank

A full-stack banking application demonstration built with **FastAPI**, **Streamlit**, and **HTML/CSS/JavaScript**.

## 📋 Features

- **User Authentication** (Login/Register)
- **Account Management** (View accounts and balances)
- **Transactions**
  - Deposit money
  - Withdraw money
  - Transfer between accounts
  - View transaction history
- **Multiple Frontend Options**
  - Streamlit web app
  - HTML/CSS/JavaScript static site
- **RESTful API** with FastAPI
- **Real-time Updates**
- **Responsive Design**

## 🏗️ Project Structure

```
DummyBank/
├── backend/
│   ├── main.py              # FastAPI backend application
│   └── requirements.txt     # Backend dependencies
├── frontend/
│   ├── streamlit_app.py     # Streamlit frontend application
│   ├── requirements.txt     # Frontend dependencies
│   └── pages/               # Additional Streamlit pages (optional)
├── static/
│   ├── index.html          # Landing page
│   ├── login.html          # Login/Register page with dashboard
│   ├── css/
│   │   └── style.css       # Styles
│   └── js/
│       └── main.js         # JavaScript functionality
└── README.md
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- pip (Python package manager)

### Installation

1. **Clone or download the project**

2. **Install Backend Dependencies**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

3. **Install Frontend Dependencies (for Streamlit)**
   ```bash
   cd ../frontend
   pip install -r requirements.txt
   ```

### Running the Application

#### Option 1: FastAPI Backend + Streamlit Frontend

1. **Start the FastAPI backend** (Terminal 1):
   ```bash
   cd backend
   python main.py
   ```
   The API will be available at: `http://localhost:8000`

2. **Start the Streamlit frontend** (Terminal 2):
   ```bash
   cd frontend
   streamlit run streamlit_app.py
   ```
   The Streamlit app will open automatically in your browser

#### Option 2: FastAPI Backend + HTML Frontend

1. **Start the FastAPI backend** (Terminal 1):
   ```bash
   cd backend
   python main.py
   ```

2. **Serve the static HTML files** (Terminal 2):
   ```bash
   cd static
   python -m http.server 8080
   ```
   Open your browser and navigate to: `http://localhost:8080`

## 🔑 Demo Credentials

**Username:** demo  
**Password:** demo123

The demo account has a pre-loaded savings account with $5,000.

## 📚 API Documentation

Once the backend is running, visit `http://localhost:8000/docs` for interactive API documentation (Swagger UI).

### Main Endpoints

- **POST** `/api/register` - Register new user
- **POST** `/api/login` - Login user
- **GET** `/api/accounts` - Get user accounts
- **GET** `/api/account/{account_number}` - Get specific account
- **GET** `/api/transactions/{account_number}` - Get account transactions
- **POST** `/api/deposit` - Deposit money
- **POST** `/api/withdraw` - Withdraw money
- **POST** `/api/transfer` - Transfer money between accounts
- **GET** `/api/user/profile` - Get user profile

## 💻 Technology Stack

### Backend
- **FastAPI** - Modern, fast web framework for building APIs
- **JWT** - JSON Web Tokens for authentication
- **Pydantic** - Data validation using Python type annotations
- **Uvicorn** - ASGI server

### Frontend
- **Streamlit** - Python web app framework
- **HTML5/CSS3** - Static web pages
- **JavaScript (ES6+)** - Client-side functionality
- **Fetch API** - HTTP requests

## 🎨 Features by Frontend

### Streamlit Features
- Interactive forms
- Real-time balance updates
- Transaction history
- Quick actions (Deposit, Withdraw, Transfer)
- Responsive layout

### HTML Features
- Modern, clean UI
- Tab-based login/register
- Dashboard with account overview
- Transaction management
- Fully responsive design

## 🔒 Security Features

- Password hashing (SHA-256)
- JWT-based authentication
- Token expiration (24 hours)
- Protected API endpoints
- CORS middleware configured

## 🗄️ Data Storage

Currently uses **in-memory storage** for demonstration purposes. For production:
- Replace with PostgreSQL/MySQL
- Add SQLAlchemy ORM
- Implement proper database migrations
- Add data persistence

## 🛠️ Development

### Adding New Features

1. **Backend**: Add new endpoints in `backend/main.py`
2. **Streamlit**: Update `frontend/streamlit_app.py`
3. **HTML**: Update `static/*.html` and `static/js/main.js`

### Testing the API

Use the interactive API docs at `http://localhost:8000/docs` or use curl:

```bash
# Login
curl -X POST "http://localhost:8000/api/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"demo","password":"demo123"}'

# Get accounts (replace TOKEN with actual token)
curl -X GET "http://localhost:8000/api/accounts" \
  -H "Authorization: Bearer TOKEN"
```

## 📝 Future Enhancements

- [ ] Database integration (PostgreSQL)
- [ ] Account types (Checking, Savings, Credit)
- [ ] Loan management
- [ ] Bill payments
- [ ] Mobile app (React Native)
- [ ] Email notifications
- [ ] Two-factor authentication
- [ ] Transaction categories and analytics
- [ ] Export statements (PDF)
- [ ] Admin dashboard

## 🤝 Contributing

This is a demonstration project. Feel free to fork and enhance it for your needs!

## ⚠️ Disclaimer

This is a **dummy banking application** for demonstration and educational purposes only. 
**DO NOT use in production** without implementing:
- Proper security measures
- Database with encryption
- Compliance with banking regulations
- Professional security audit

## 📄 License

This project is open source and available for educational purposes.

## 🙋 Support

For questions or issues, please refer to the API documentation at `/docs` endpoint.

---

**Built with ❤️ for learning purposes**
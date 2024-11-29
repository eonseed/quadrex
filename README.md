# Budget Tracker

A modern, user-friendly web application for personal budget management built with Flask and HTMX.

## Features

- 🔐 User Authentication
  - Secure login and registration
  - Password hashing and protection
  - Session management

- 💰 Transaction Management
  - Add, edit, and delete transactions
  - Categorize income and expenses
  - Filter transactions by type and category
  - Date-based organization

- 📊 Categories
  - Custom category creation
  - Category-based filtering
  - Icon support for visual recognition

- ⚡ Modern UI/UX
  - Dynamic updates with HTMX
  - Responsive design with TailwindCSS
  - Beautiful components with DaisyUI
  - Dark mode support

## Tech Stack

- **Backend**
  - Python 3.12
  - Flask (Web Framework)
  - SQLAlchemy (ORM)
  - Flask-Login (Authentication)
  - SQLite (Database)

- **Frontend**
  - HTMX (Dynamic Interactions)
  - TailwindCSS (Styling)
  - DaisyUI (Component Library)

## Project Structure

```
budget_tracker/
├── app/
│   ├── __init__.py          # App initialization and configuration
│   ├── models.py            # Database models
│   ├── auth/               # Authentication blueprint
│   │   ├── __init__.py
│   │   └── routes.py
│   ├── categories/         # Categories blueprint
│   │   ├── __init__.py
│   │   └── routes.py
│   ├── transactions/       # Transactions blueprint
│   │   ├── __init__.py
│   │   └── routes.py
│   ├── main/              # Main blueprint
│   │   ├── __init__.py
│   │   └── routes.py
│   └── templates/          # Jinja2 templates
│       ├── auth/
│       ├── categories/
│       ├── transactions/
│       ├── base.html
│       └── index.html
├── instance/              # Instance-specific files
│   └── budget.db         # SQLite database
├── migrations/           # Database migrations
├── tests/               # Test suite
├── .env                 # Environment variables
├── .gitignore          # Git ignore rules
├── config.py           # Configuration settings
├── requirements.txt    # Python dependencies
└── run.py             # Application entry point
```

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/budget_tracker.git
cd budget_tracker
```

2. Create and activate virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. Initialize the database:
```bash
flask db upgrade
```

6. Run the development server:
```bash
flask run
```

The application will be available at `http://localhost:5000`

## Development

### Database Migrations

To create a new migration after model changes:

```bash
flask db migrate -m "Description of changes"
flask db upgrade
```

### Running Tests

```bash
python -m pytest
```

### Code Style

This project follows PEP 8 style guide. To check code style:

```bash
flake8 .
```

## Security

- All routes requiring authentication are protected
- Passwords are hashed using bcrypt
- CSRF protection enabled
- User input is validated and sanitized
- Database queries are protected against SQL injection

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Flask documentation and community
- HTMX for modern UI without complex JavaScript
- TailwindCSS and DaisyUI for beautiful styling

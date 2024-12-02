# Quadrex (pronounced KWA-deks)

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

A modern, user-friendly web application for personal financial management built with Flask and HTMX.

## Brand Story

The name "Quadrex" (KWA-deks) is inspired by the concept of "quad," representing four key aspects of personal finance:

* **Four Basic Arithmetic Operations:** Addition, subtraction, multiplication, and division are the fundamental building blocks of any financial tracking system. Quadrex helps you manage these operations on your income and expenses.
* **Quarterly Financial Periods:** Many people and businesses organize their finances around quarters of the year (Q1, Q2, Q3, Q4). Quadrex can help you track and analyze your finances on a quarterly basis.

The "-rex" suffix adds a sense of power and mastery, suggesting that users can take control of their finances with confidence. Together, Quadrex represents a powerful tool for mastering your financial journey through systematic organization and analysis.

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
quadrex/
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
│   └── quadrex.db        # SQLite database
├── migrations/           # Database migrations
├── tests/               # Test suite
├── .env                 # Environment variables
├── .gitignore          # Git ignore rules
├── config.py           # Configuration settings
├── requirements.txt    # Python dependencies
└── run.py             # Application entry point
```

**## Installation**

1. Clone the repository:

    ```bash
    git clone https://github.com/eonseed/quadrex.git
    cd quadrex
    ```

2. Install uv:
    ```bash
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```

3. Install dependencies and synchronize project:
    ```bash
    uv sync
    ```

4. Set up environment variables:

    ```bash
    cp .env.example .env
    # Edit .env with your configuration
    ```

5. Initialize the database:

    ```bash
    uv run flask db upgrade
    ```

6. Run the development server:

    ```bash
    uv run flask run
    ```

    The application will be available at `http://localhost:5000`

**## Development**

**### Database Migrations**

To create a new migration after model changes:

```bash
uv run flask db migrate -m "Description of changes"
uv run flask db upgrade
```

### Running Tests

```bash
uv run pytest
```

### Code Style

This project follows PEP 8 style guide. To check code style:

```bash
uv run ruff check
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

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.

This means you are free to:
- Use this software for any purpose
- Change the software to suit your needs
- Share the software with others
- Share the changes you make

Under the following conditions:
- If you modify and distribute this software, you must also make your source code available under the GPL
- You must include the original copyright and license notices
- You must state significant changes made to the software

For more details, see the [GNU General Public License v3.0](https://www.gnu.org/licenses/gpl-3.0.html).

## Acknowledgments

- Flask documentation and community
- HTMX for modern UI without complex JavaScript
- TailwindCSS and DaisyUI for beautiful styling

# Budget Tracker

A modern budget tracking application built with Flask, SQLAlchemy, and HTMX.

## Features

- Track income and expenses
- Categorize transactions
- View budget analytics
- Responsive UI with TailwindCSS and DaisyUI
- Real-time updates with HTMX

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. Initialize the database:
```bash
flask db upgrade
```

5. Run the development server:
```bash
flask run
```

## Development

- Database migrations: `flask db migrate -m "migration message"`
- Apply migrations: `flask db upgrade`
- Build CSS: `npm run build-css`

# Grocery Expiry Tracker

A web application to track grocery items and their expiry dates, built with Flask and SQLite.

## Features

- User Authentication (Register/Login)
- Add, Edit, and Delete grocery items
- Track expiry dates
- Categorize items (Dairy, Meat, Vegetables, etc.)
- Recipe suggestions for items nearing expiry
- Filter items by category
- Sort by expiry date
- Quantity management
- Notes for each item

## Tech Stack

- Python 3.x
- Flask
- SQLite
- SQLAlchemy
- Bootstrap 5
- Spoonacular API (for recipe suggestions)

## Setup

1. Clone the repository:
```bash
git clone https://github.com/MaahiMishra12222768/grocery_expiry_tracker.git
cd grocery_expiry_tracker
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python app.py
```

4. Open in browser:
```
http://127.0.0.1:5000
```

## Configuration

1. Create a `config.py` file with your Spoonacular API key:
```python
SPOONACULAR_API_KEY = "your_api_key_here"
```

## Features in Detail

1. **User Authentication**
   - Secure password hashing
   - Session management
   - User-specific data

2. **Item Management**
   - Add new items with expiry dates
   - Edit existing items
   - Mark items as used
   - Add notes and quantities

3. **Smart Features**
   - Recipe suggestions based on ingredients
   - Expiry date tracking
   - Category-based organization

## Contributing

Feel free to fork this repository and submit pull requests for any improvements!

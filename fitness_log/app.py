from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# In-memory stores
user_nutrition_totals = {}
user_fitness_data = {}

# Initialize DB and create a test user if not present
def init_db():
    with sqlite3.connect("database.db") as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL
            )
        ''')
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE username = ?", ('admin',))
        if not cur.fetchone():
            hashed_pw = generate_password_hash('admin')
            conn.execute("INSERT INTO users (username, password) VALUES (?, ?)", ('admin', hashed_pw))
            conn.commit()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        with sqlite3.connect("database.db") as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM users WHERE username=?", (username,))
            result = cur.fetchone()

            if result and check_password_hash(result[2], password):
                session['username'] = username
                flash('Login successful!', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid username or password.', 'error')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('Logged out successfully.', 'success')
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))

    username = session['username']
    totals = user_nutrition_totals.get(username)
    fitness = user_fitness_data.get(username)
    return render_template('dashboard.html', user=username, totals=totals, fitness=fitness)

@app.route('/nutrition', methods=['GET', 'POST'])
def nutrition():
    if 'username' not in session:
        return redirect(url_for('login'))

    username = session['username']

    if request.method == 'POST':
        names = request.form.getlist('food_name')
        quantities = request.form.getlist('quantity')
        calories = request.form.getlist('calories')
        proteins = request.form.getlist('protein')
        carbs = request.form.getlist('carbs')
        fats = request.form.getlist('fat')

        totals = {"calories": 0.0, "protein": 0.0, "carbs": 0.0, "fat": 0.0}

        for i in range(len(names)):
            try:
                qty = float(quantities[i])
                totals['calories'] += qty * float(calories[i])
                totals['protein'] += qty * float(proteins[i])
                totals['carbs'] += qty * float(carbs[i])
                totals['fat'] += qty * float(fats[i])
            except (ValueError, IndexError):
                continue

        user_nutrition_totals[username] = totals
        flash('Nutrition totals calculated successfully!', 'success')
        return redirect(url_for('nutrition'))

    totals = user_nutrition_totals.get(username)
    return render_template('nutrition.html', totals=totals)

@app.route('/fitness', methods=['GET', 'POST'])
def fitness():
    if 'username' not in session:
        return redirect(url_for('login'))

    username = session['username']
    fitness_data = None

    if request.method == 'POST':
        try:
            steps = int(request.form['steps'])
            workout_minutes = float(request.form['workout_minutes'])
            activity_type = request.form['activity_type']

            # Distance in kilometers and step calories
            distance_km = round(steps * 0.0008, 2)  # 0.8 meters per step
            step_calories = round(steps * 0.04, 2)  # 0.04 kcal per step

            # Calories per minute by activity
            calorie_burn_rates = {
                'walking': 4,
                'running': 10,
                'cycling': 8,
                'yoga': 3,
                'strength training': 6
            }

            workout_calories = round(workout_minutes * calorie_burn_rates.get(activity_type, 5), 2)
            total_calories = step_calories + workout_calories

            fitness_data = {
                'steps': steps,
                'distance_km': distance_km,
                'step_calories': step_calories,
                'activity_type': activity_type,
                'workout_minutes': workout_minutes,
                'workout_calories': workout_calories,
                'total_calories': total_calories
            }

            user_fitness_data[username] = fitness_data
            flash('Fitness data calculated successfully!', 'success')
        except Exception:
            flash('Error calculating fitness data. Please check your inputs.', 'error')

    fitness_data = user_fitness_data.get(username)
    return render_template('fitness.html', fitness=fitness_data)

@app.route('/category/<name>')
def category(name):
    return render_template('category.html', name=name)

@app.route('/plan/<name>')
def plan(name):
    return render_template('plan.html', name=name)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)


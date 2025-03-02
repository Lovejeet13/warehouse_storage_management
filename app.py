from flask import Flask, render_template, request, redirect, flash
import mysql.connector
from decimal import Decimal

app = Flask(__name__)
app.secret_key = "supersecretkey"  # Required for flashing messages

# Database connection
def get_db_connection():
    conn = mysql.connector.connect(
        host='localhost',  # Assuming MySQL is running locally
        user='root',  # Your MySQL username
        password='123456',  # Your MySQL password
        database='farm_storage'  # Database name
    )
    return conn


# Home route to input farmer info
@app.route('/')
def home():
    return render_template('index.html')


# Route to search and display warehouses based on state, crop, and quantity
@app.route('/search', methods=['POST'])
def search():
    state = request.form.get('state')
    crop_name = request.form.get('crop_name')
    quantity = request.form.get('quantity')

    # Validate inputs
    if not state or not crop_name or not quantity:
        flash("All fields are required!", "error")
        return redirect('/')

    if not quantity.isdigit():
        flash("Quantity must be a number!", "error")
        return redirect('/')

    quantity = Decimal(quantity)  # Convert quantity to Decimal

    # Connect to database
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Fetch warehouses from the selected state
    cursor.execute('SELECT * FROM warehouses WHERE state = %s', (state,))
    warehouses = cursor.fetchall()

    # Calculate price based on quantity
    for warehouse in warehouses:
        warehouse['total_price'] = round(Decimal(str(warehouse['price_per_kg'])) * quantity, 2)

    cursor.close()
    conn.close()

    # Render search results and ensure 'state' is passed properly
    return render_template('search_results.html', warehouses=warehouses, crop_name=crop_name, quantity=quantity, state=state)


# Route to store the farmer's selected warehouse information and crop details
@app.route('/store_crop', methods=['POST'])
def store_crop():
    farmer_name = request.form.get('farmer_name')
    state = request.form.get('state')
    district = request.form.get('district')
    crop_name = request.form.get('crop_name')
    warehouse_id = request.form.get('warehouse_id')
    quantity = request.form.get('quantity')

    # Debugging print statement
    print(f"Received Data: {farmer_name}, {state}, {district}, {crop_name}, {warehouse_id}, {quantity}")

    # Validate all fields
    if not all([farmer_name, state, district, crop_name, warehouse_id, quantity]):
        flash("All fields are required!", "error")
        return redirect('/')

    # Convert quantity to Decimal
    try:
        quantity = Decimal(quantity)
    except:
        flash("Invalid quantity!", "error")
        return redirect('/')

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Insert farmer information
        cursor.execute('INSERT INTO farmers (name, state, district, crop_name) VALUES (%s, %s, %s, %s)',
                       (farmer_name, state, district, crop_name))
        conn.commit()

        # Get the last inserted farmer ID
        farmer_id = cursor.lastrowid

        # Insert storage information
        cursor.execute('INSERT INTO storage (farmer_id, warehouse_id, crop_name, quantity) VALUES (%s, %s, %s, %s)',
                       (farmer_id, warehouse_id, crop_name, quantity))
        conn.commit()

        flash("Crop stored successfully!", "success")

    except mysql.connector.Error as err:
        flash(f"Database Error: {err}", "error")

    finally:
        cursor.close()
        conn.close()

    # ✅ Redirect to the 'View Data' page instead of home page
    return redirect('/view_data')


# Route to display all stored data in the table
@app.route('/view_data')
def view_data():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(''' 
        SELECT f.name AS farmer_name, f.state, f.district, f.crop_name, 
               w.warehouse_name, w.address, w.mobile_number, w.price_per_kg,
               s.quantity, (w.price_per_kg * s.quantity) AS total_price
        FROM storage s
        JOIN farmers f ON s.farmer_id = f.id
        JOIN warehouses w ON s.warehouse_id = w.id
    ''')
    data = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('view_data.html', data=data)


if __name__ == '__main__':
    app.run(debug=True)

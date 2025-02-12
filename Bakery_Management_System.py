import mysql.connector
import bcrypt
from datetime import datetime
class DatabaseConnection:
    def __init__(self):
        self.connection = self.create_connections()
    def create_connections(self):
        try:
            connection=mysql.connector.connect(
                host='localhost',
                username='root',
                password='None2002@123',
                database='bakery_management'
            )
            if connection.is_connected():
                print("Connected to MYSQL Database")
            return connection
        except mysql.connector.Error as e:
            print(f"Error connected to MYSQL: {e}")
            return None
class Authentication:
    def __init__(self):
        self.logged_in_user=None
    def register(self,connection,username,password,role):
        try:
            if role not in ['manager','cashier']:
                print("Invalid role. Please select 'manager' or 'cashier'.")
                return
            cursor=connection.cursor()
            cursor.execute("SELECT COUNT(*) FROM users")
            user_count = cursor.fetchone()[0]
            if user_count == 0:
                cursor.execute("ALTER TABLE users AUTO_INCREMENT = 1")
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            insert_query=''' INSERT INTO users(username,password,role) VALUES(%s,%s,%s)'''
            cursor.execute(insert_query,(username, hashed_password.decode('utf-8'),role))
            connection.commit()
            print(f"User {username} registered successfully as {role}.")
        except Exception as e:
            print(f"Error registration user: {e}")

    def login(self,connection,username,password):
        try:            
            cursor=connection.cursor()
            insert_query='''SELECT password ,role FROM users WHERE username=%s'''
            cursor.execute(insert_query,(username,))
            res=cursor.fetchone()
            if not res:
                print("Invalid username or password")
                return None
            stored_password,role=res
            if bcrypt.checkpw(password.encode('utf-8'),stored_password.encode('utf-8')):
                print(f"Login successful! Welcome, {username} ({role}).")
                self.logged_in_user = username
                self.user_role = role
                return self.user_role
            else:
                print("Invalid username or password.")
                return None
        except Exception as e:
            print(f"Error during login: {e}")
            return None
    def logout(self):
        if self.logged_in_user:
            print(f"{self.logged_in_user} logged out successfully!")
            self.user_role = None
            self.logged_in_user = None
        else:
            print("No user is currently logged in.")
class Inventory:
    def add_item(self, connection, item_name, price, stock):
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT COUNT(*) FROM inventory")
            count = cursor.fetchone()[0]
            if count == 0:
                cursor.execute("ALTER TABLE inventory AUTO_INCREMENT = 1")
            cursor.execute("SELECT id FROM inventory WHERE item_name = %s", (item_name,))
            existing_item = cursor.fetchone()
            if existing_item:
                print(f"Item '{item_name}' already exists. Use 'Update Stock' instead.")
                return
            cursor.execute("INSERT INTO inventory (item_name, price, quantity) VALUES (%s, %s, %s)",
                           (item_name, price, stock))
            connection.commit()
            cursor.execute("SELECT id FROM inventory WHERE item_name = %s", (item_name,))
            cursor.fetchone()[0]
            connection.commit()
            cursor.close()
            print(f"Item added to inventory.")
        except mysql.connector.Error as e:
            print(f"Error adding item: {e}")
        
    def update_stock(self, connection, item_name, quantity_sold):
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT id, quantity, price FROM inventory WHERE item_name = %s", (item_name,))
            res = cursor.fetchone()
            if not res:
                print(f"Item '{item_name}' does not exist.")
                return
            item_id, current_stock, price = res
            if current_stock < quantity_sold:
                print(f"Insufficient stock. Available: {current_stock}")
                return
            cursor.execute("UPDATE inventory SET quantity = quantity - %s WHERE id = %s", (quantity_sold, item_id))
            cursor.execute("SELECT COUNT(*) FROM sales")
            count = cursor.fetchone()[0]
            if count == 0:
                cursor.execute("ALTER TABLE sales AUTO_INCREMENT = 1")
            cursor.execute("INSERT INTO sales (inventory_id, item_name, quantity, price, sale_date) VALUES (%s, %s, %s, %s, NOW())", 
               (item_id, item_name, quantity_sold, price))
            connection.commit()
            cursor.close()
            print(f"Stock updated and sale recorded for {item_name}.")
        except mysql.connector.Error as e:
            print(f"Error updating stock: {e}")
        
    def remove_item(self,connection,item_id):
        try:
            cursor=connection.cursor()
            cursor.execute("SELECT item_name FROM inventory WHERE id = %s", (item_id,))
            item = cursor.fetchone()
            if not item:
                print(f"Item ID {item_id} not found in inventory.")
                return
            item_name = item[0]
            cursor.execute("DELETE FROM sales WHERE inventory_id = %s", (item_id,))
            cursor.execute("DELETE FROM inventory WHERE id = %s", (item_id,))
            connection.commit()
            print(f"Item {item_name} removed from inventory.")
        except Exception as e:
            print(f"Error removed item: {e}")
            return None
        
    def display_inventory(self,connection):
        try:
           cursor=connection.cursor()
           cursor.execute("SELECT id, item_name, price, quantity FROM inventory")
           rows=cursor.fetchall()
           if not rows:
               price("Inventory is empty")
               return
           print("--- Inventory ---")
           for row in rows:
               item_id, item_name, price, stock = row
               print(f"Item ID: {item_id}, Name: {item_name}, Price: ${price}, Stock: {stock}")
        except Exception as e:
          print(f"Error: {e}") 

class Cart:
    def __init__(self):
        self.cart={}
    def add_to_cart(self,connection, item_id, quantity):
        cursor = connection.cursor()
        cursor.execute("SELECT item_name FROM inventory WHERE id = %s", (item_id,))
        result = cursor.fetchone()
        if result:
            item_name = result[0]
            if item_id in self.cart:
                self.cart[item_id] += quantity
            else:
                self.cart[item_id] = quantity
            print(f"Item ID: {item_id} ({item_name}) added to cart. Quantity: {quantity}")
        else:
            print("Invalid Item ID. Item not found in inventory.")
    def remove_from_cart(self,connection, item_id):
        cursor = connection.cursor()
        cursor.execute("SELECT item_name FROM inventory WHERE id = %s", (item_id,))
        result = cursor.fetchone()
        if not result:
            print("Invalid Item ID. Item not found in inventory.")
            return
        item_name=result[0]
        if item_id in self.cart:
            del self.cart[item_id]
            print(f"Item {item_id} removed from cart.")
        else:
            print("Item not found in cart.")

    def generate_bill(self,connection):
        total = 0
        print("--- BILL ---")
        cursor = connection.cursor()
        for item_id, quantity in self.cart.items():
            cursor.execute("SELECT item_name, price FROM inventory WHERE id = %s", (item_id,))
            result = cursor.fetchone()
            if not result:
                print(f"Item ID {item_id} not found in inventory. Skipping...")
                continue
            item_name, price = result
            item_total = quantity * price
            total += item_total
            print(f"{item_name}: {quantity} x ${price:.2f} = ${item_total:.2f}")
        print(f"Total Amount: ${total:.2f}")
        print("Thank you for your purchase!")
class Sales:
    def sales_report(self, connection, period):
        total_sales=0
        valid_periods = ["daily", "weekly", "monthly"]
        if period not in valid_periods:
            print("Invalid period. Please enter 'daily', 'weekly', or 'monthly'.")
            return
        try:
            cursor = connection.cursor()
            query = """
                SELECT item_name, SUM(quantity) AS total_quantity, SUM(price * quantity) AS total_revenue,(SUM(price * quantity) / SUM(quantity)) AS price
                FROM sales 
                WHERE sale_date >= NOW() - INTERVAL %s DAY
                GROUP BY item_name
            """
            days = {"daily": 1, "weekly": 7, "monthly": 30}.get(period, 1)
            cursor.execute(query, (days,))
            results = cursor.fetchall()
            
            if not results:
                print("No sales data available for the selected period.")
                return
            
            period_title = {"daily": "Daily", "weekly": "Weekly", "monthly": "Monthly"}.get(period, "Daily")
            print(f"--- {period_title} Sales Report ---")
            for row in results:
                item_name, total_quantity, total_revenue, unit_price = row
                print(f"{item_name}: Sold {total_quantity} @ ${unit_price:.2f} each")
                total_sales =total_sales+ total_revenue
            print(f"Total Sales: ${total_sales:.2f}")
        except Exception as e:
            print(f"Error generating sales report: {e}")

    def custom_report(self,connection, start_date, end_date):
        try:
            cursor = connection.cursor()
            query = '''SELECT item_name, SUM(quantity), price,DATE(sale_date) FROM sales WHERE DATE(sale_date) BETWEEN %s AND %s GROUP BY item_name, price,DATE(sale_date)'''
            cursor.execute(query, (start_date, end_date))
            rows = cursor.fetchall()
            if not rows:
                print("No sales data found for the selected period.")
                return
            total_sales = 0
            print(f"--- Custom Sales Report from {start_date} to {end_date} ---")
            for row in rows:
                item_name, quantity, price,sale_date  = row
                total = quantity * price
                total_sales += total
                print(f"{item_name}: Sold {quantity} @ ${price:.2f} each on {sale_date}")
            print(f"Total Sales: ${total_sales:.2f}")
        except Exception as e:
            print(f"Error generating custom report: {e}")
def main_menu(connection):
    auth=Authentication()
    inventory=Inventory()
    cart=Cart()
    sales=Sales()
    while True:
        print("\n Bakery Management System")
        print("1. Register")
        print("2. Login") 
        print("3. Add Item")
        print("4. Update Stock")
        print("5. Sales Report")
        print("6. Custom Report")
        print("7. Display Inventory")
        print("8. Remove Item")
        print("9. Add to Cart")
        print("10. Remove From Cart")
        print("11. Generate Bill")    
        print("12. Logout")
        print("13. Exit")

        choice=input("Enter your choice: ")
        if choice=='1':
            username=input("Enter username: ")
            password=input("Enter Password: ")
            role = input("Enter role (manager/cashier): ")
            auth.register(connection,username,password,role)

        elif choice=='2':
            if auth.logged_in_user:
                print("Already logged in.")
            else:
                username=input("Enter username: ")
                password=input("Enter Password: ")
                auth.login(connection,username,password)
        elif choice=='12':
                auth.logout()
                
        elif choice=='13':
            connection.close()
            print("Exiting the system. Goodbye!")
            break
        elif choice=='3':
                item_name = input("Enter item name: ")
                price = float(input("Enter item price: "))
                stock = int(input("Enter stock quantity: "))
                inventory.add_item(connection,item_name, price, stock)   
                print("Only Manager have the Access to add the items.") 

        elif choice=='4':
            item_name = input("Enter item name: ")
            quantity_sold = int(input("Enter quantity sold: "))
            inventory.update_stock(connection,item_name, quantity_sold)
        elif choice=='5':
            period = input("Enter report period (daily/weekly/monthly): ")
            sales.sales_report(connection, period)

        elif choice=='6':
            start_date = input("Enter start date (YYYY-MM-DD): ")
            end_date = input("Enter end date (YYYY-MM-DD): ")
            sales.custom_report(connection, start_date, end_date)
        
        elif choice=='7':
            inventory.display_inventory(connection)

        elif choice=='8':
            item_id = int(input("Enter item ID to remove: "))
            inventory.remove_item(connection,item_id)

        elif choice=='9':
            item_id = int(input("Enter item ID: "))
            quantity = int(input("Enter quantity: "))
            cart.add_to_cart(connection, item_id, quantity)

        elif choice=='10':
            item_id = int(input("Enter Item id to remove from cart: "))
            cart.remove_from_cart(connection,item_id)

        elif choice=='11':
            cart.generate_bill(connection)
            
        else:
            print("Invalid choice.")   

if __name__=="__main__":
    db=DatabaseConnection()
    if db.connection:
        main_menu(db.connection)



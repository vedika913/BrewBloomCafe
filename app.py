from os import name
from werkzeug.security import generate_password_hash, check_password_hash
from bson import ObjectId
from flask import Flask, render_template, request, redirect, session, abort
from database import users, coffees, orders, messages
from datetime import datetime




app = Flask(__name__, template_folder="pages")
app.secret_key = "CoffeeShopSecret123"



    
#home 


@app.route("/")
def home():

    coffee_list = list(coffees.find())

    return render_template(
        "index.html",
        coffees=coffee_list
    )
    
    

# MENU

@app.route("/menu")
def menu():

    coffee_list = list(coffees.find())

    return render_template(
        "menu.html",
        coffees=coffee_list
    )
    
    


# ABOUT

@app.route("/about")
def about():
    return render_template("about.html")




# CONTACT
@app.route("/contact", methods=["GET", "POST"])
def contact():

    if request.method == "POST":

        name = request.form.get("name")
        email = request.form.get("email")
        mobile = request.form.get("mobile")
        message = request.form.get("message")

        messages.insert_one({
            "name": name,
            "email": email,
            "mobile": mobile,
            "message": message,
            "created_at": datetime.now()
        })

        # IMPORTANT: redirect after saving
        return redirect("/contact?success=1")

    success = request.args.get("success")

    return render_template(
        "contact.html",
        success=success
    )




# REGISTER


@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        mobile = request.form["mobile"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        if password != confirm_password:
            return "Passwords do not match!"

        existing_user = users.find_one({"email": email})

        if existing_user:
            return "Email already registered!"

        new_user = {
            "name": name,
            "email": email,
            "mobile": mobile,
            "password": generate_password_hash(password),
            "role": "user"
        }

        users.insert_one(new_user)

        return redirect("/login")

    return render_template("register.html")





# LOGIN

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        entered_password = request.form["password"]

        # Find the user by email
        user = users.find_one({"email": email})

        if not user:
            return "Invalid Email or Password"

        stored_password = user.get("password", "")

        # Check whether the password is already hashed
        is_hashed = stored_password.startswith(("scrypt:", "pbkdf2:"))

        if is_hashed:
            password_correct = check_password_hash(
                stored_password, entered_password
            )
        else:
            # Temporary support for existing plain-text passwords
            password_correct = stored_password == entered_password

        if not password_correct:
            return "Invalid Email or Password"

        # Convert a legacy plain-text password to a hash
        if not is_hashed:
            users.update_one(
                {"_id": user["_id"]},
                {
                    "$set": {
                        "password": generate_password_hash(entered_password)
                    }
                }
            )

        # Clear any previous session data
        session.clear()

        # Set session data
        session["user"] = user.get("name", "")
        session["email"] = user["email"]
        session["role"] = str(user.get("role", "user")).strip().lower()

        print("Logged-in email:", session["email"])
        print("Logged-in role:", repr(session["role"]))

        # Redirect based on role
        if session["role"] == "admin":
            return redirect("/admin")

        return redirect("/dashboard")

    return render_template("login.html")



# LOGOUT

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")








# USER DASHBOARD

@app.route("/dashboard")
def dashboard():

    if "user" not in session:
        return redirect("/login")

    if session.get("role") == "admin":
        return redirect("/admin")

    return render_template(
        "dashboard.html",
        username=session["user"]
    )
    
    





# ADD TO CART

@app.route("/order/<id>")
def order(id):

    if "user" not in session:
        return redirect("/login")

    coffee = coffees.find_one({"_id": ObjectId(id)})

    if coffee is None:
        return "Coffee not found!"

    order = {
        "user_name": session["user"],
        "user_email": session["email"],
        "coffee_name": coffee["name"],
        "price": coffee["price"],
        "status": "Pending"
    }

    orders.insert_one(order)

    return redirect("/cart")







# CART

@app.route("/cart")
def cart():

    if "user" not in session:
        return redirect("/login")

    cart_items = list(
        orders.find({
            "user_email": session["email"],
            "status": "Pending"
        })
    )

    total = sum(item["price"] for item in cart_items)

    return render_template(
        "cart.html",
        cart_items=cart_items,
        total=total
    )







# REMOVE ITEM FROM CART

@app.route("/remove-cart/<id>")
def remove_cart(id):

    if "user" not in session:
        return redirect("/login")

    orders.delete_one({
    "_id": ObjectId(id),
    "user_email": session["email"]
})
    return redirect("/cart")






# CHECKOUT PAGE

@app.route("/checkout")
def checkout():

    if "user" not in session:
        return redirect("/login")

    cart_items = list(
        orders.find({
            "user_email": session["email"],
            "status": "Pending"
        })
    )

    total = sum(item["price"] for item in cart_items)

    return render_template(
        "checkout.html",
        cart_items=cart_items,
        total=total
    )







# PLACE ORDER

@app.route("/place-order", methods=["POST"])
def place_order():

    if "user" not in session:
        return redirect("/login")

    orders.update_many(
        {
            "user_email": session["email"],
            "status": "Pending"
        },
        {
            "$set": {
                "status": "Order Placed"
            }
        }
    )

    return render_template("success.html")









# MY ORDERS

@app.route("/orders")
def my_orders():

    if "user" not in session:
        return redirect("/login")

    my_orders = list(
        orders.find({
            "user_email": session["email"]
        }).sort("_id", -1)
    )

    return render_template(
        "orders.html",
        orders=my_orders
    )
    
    
    
    



    
# ADMIN DASHBOARD
@app.route("/admin")
def admin():
    # User must be logged in
    if "user" not in session:
        return redirect("/login")

    # User must have the admin role
    if session.get("role") != "admin":
        return "Access Denied", 403

    # Dashboard statistics
    total_users = users.count_documents({})
    total_coffees = coffees.count_documents({})
    total_orders = orders.count_documents({})

    # Latest 10 orders
    recent_orders = list(
        orders.find().sort("_id", -1).limit(10)
    )

    return render_template(
        "admin/admin_dashboard.html",
        total_users=total_users,
        total_coffees=total_coffees,
        total_orders=total_orders,
        recent_orders=recent_orders
    )








# ADMIN USERS
@app.route("/admin/users")
def admin_users():

    if "user" not in session:
        return redirect("/login")

    if session.get("role") != "admin":
        return "Access Denied!"

    user_list = list(users.find())

    return render_template(
        "admin/admin_users.html",
        users=user_list
    )








# USER DETAILS

@app.route("/admin/user/<id>")
def admin_user(id):

    if "user" not in session:
        return redirect("/login")

    if session.get("role") != "admin":
        return "Access Denied!"

    # Find selected user
    user = users.find_one({
        "_id": ObjectId(id)
    })

    if not user:
        return "User not found"

    # Get all users
    all_users = list(users.find())

    # Find this user's position
    user_number = 1

    for index, u in enumerate(all_users, start=1):
        if str(u["_id"]) == str(user["_id"]):
            user_number = index
            break

    # Find customer's orders
    user_orders = list(
        orders.find({
            "user_email": user.get("email")
        })
    )

    return render_template(
        "admin/user_details.html",
        user=user,
        orders=user_orders,
        user_number=user_number
    )







# DELETE USER


@app.route("/delete-user/<id>")
def delete_user(id):

    if session.get("role") != "admin":
        return "Access Denied!"

    users.delete_one({"_id": ObjectId(id)})

    return redirect("/admin/users")








# ADMIN ORDERS

@app.route("/admin/orders")
def admin_orders():

    if "user" not in session:
        return redirect("/login")

    if session.get("role") != "admin":
        return "Access Denied!"

    order_list = list(orders.find())

    return render_template(
        "admin/admin_orders.html",
        orders=order_list
    )





# COMPLETE ORDER

@app.route("/complete-order/<id>")
def complete_order(id):

    if session.get("role") != "admin":
        return "Access Denied!"

    orders.update_one(
        {"_id": ObjectId(id)},
        {
            "$set": {
                "status": "Completed"
            }
        }
    )

    return redirect("/admin/orders")





# DELETE ORDER

@app.route("/delete-order/<id>")
def delete_order(id):

    if session.get("role") != "admin":
        return "Access Denied!"

    orders.delete_one({"_id": ObjectId(id)})

    return redirect("/admin/orders")




#messsages

@app.route("/admin/messages")
def admin_messages():

    if "user" not in session:
        return redirect("/login")

    if session.get("role") != "admin":
        return "Access Denied!"

    message_list = list(messages.find())

    return render_template(
        "admin/admin_messages.html",
        messages=message_list
    )




#coffees

@app.route("/admin/coffees")
def admin_coffees():

    if session.get("role") != "admin":
        return "Access Denied"

    coffee_list = list(coffees.find())

    return render_template(
        "admin/admin_coffees.html",
        coffees=coffee_list
    )
    
    
    
#add coffee
import os
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = "static/images"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


@app.route("/addcoffee", methods=["GET", "POST"])
def addcoffee():

    if request.method == "POST":

        name = request.form["name"]
        category = request.form["category"]
        price = float(request.form["price"])

        image = request.files["image"]

        if image and image.filename:

            filename = secure_filename(image.filename)

            image.save(
                os.path.join(app.config["UPLOAD_FOLDER"], filename)
            )

            coffees.insert_one({
                "name": name,
                "category": category,
                "price": price,
                "image": filename
            })

            return redirect("/admin/coffees")

    return render_template("admin/addcoffee.html")


    
#upadte order status

@app.route("/update-status/<id>/<status>")
def update_status(id, status):

    if session.get("role") != "admin":
        return "Access Denied"

    orders.update_one(
        {"_id": ObjectId(id)},
        {
            "$set": {
                "status": status
            }
        }
    )

    return redirect("/admin/orders")










#new order
@app.route("/admin/new-order", methods=["GET", "POST"])
def admin_new_order():

    # Only admin can access
    if session.get("role") != "admin":
        return redirect("/login")

    # Display the new order form
    if request.method == "GET":
        coffee_list = list(coffees.find())
        return render_template(
            "new_order.html",
            coffees=coffee_list
        )

    # Get customer and order details
    customer_name = request.form.get("customer_name", "").strip()
    order_type = request.form.get("order_type", "Dine-in")
    table_number = request.form.get("table_number", "").strip()
    payment_method = request.form.get("payment_method", "Cash")

    if not customer_name:
        return "Please enter the customer name.", 400

    if order_type == "Dine-in" and not table_number:
        return "Please enter the table number.", 400

    # Get all selected coffee IDs and quantities
    coffee_ids = request.form.getlist("coffee_id")
    quantities = request.form.getlist("quantity")

    if len(coffee_ids) != len(quantities):
        return "Invalid coffee order form.", 400

    items = []
    total_price = 0.0

    # Process each coffee row
    for coffee_id, quantity_text in zip(coffee_ids, quantities):

        # Skip unused rows
        if not coffee_id:
            continue

        try:
            quantity = int(quantity_text)
        except (ValueError, TypeError):
            return "Please enter a valid quantity.", 400

        if quantity < 1:
            return "Quantity must be at least 1.", 400

        try:
            coffee = coffees.find_one({
                "_id": ObjectId(coffee_id)
            })
        except Exception:
            return "Invalid coffee selected.", 400

        if not coffee:
            return "Coffee not found.", 404

        unit_price = float(coffee["price"])
        subtotal = round(unit_price * quantity, 2)
        total_price += subtotal

        items.append({
            "coffee_id": str(coffee["_id"]),
            "coffee_name": coffee["name"],
            "quantity": quantity,
            "unit_price": unit_price,
            "subtotal": subtotal
        })

    if not items:
        return "Please select at least one coffee.", 400

    # Create one bill for all selected coffees
    now = datetime.now()
    bill_number = "BB-" + now.strftime("%Y%m%d%H%M%S%f")

    order = {
        "user_name": customer_name,
        "user_email": "Counter Customer",
        "customer_name": customer_name,
        "order_type": order_type,
        "table_number": (
            table_number if order_type == "Dine-in" else ""
        ),

        # New multiple-item structure
        "items": items,

        # Keep these fields for older pages that expect them
        "coffee_name": ", ".join(
            item["coffee_name"] for item in items
        ),
        "quantity": sum(item["quantity"] for item in items),
        "price": round(total_price, 2),

        "payment_method": payment_method,
        "status": "delivered",
        "created_at": now,
        "bill_number": bill_number,
        "source": "counter"
    }

    orders.insert_one(order)

    return redirect("/admin/orders")






#edit coffee

@app.route("/editcoffee/<id>", methods=["GET", "POST"])
def editcoffee(id):

    coffee = coffees.find_one({
        "_id": ObjectId(id)
    })

    if not coffee:
        return "Coffee not found"

    if request.method == "POST":

        name = request.form["name"]
        category = request.form["category"]
        price = float(request.form["price"])

        image = request.files.get("image")

        update_data = {
            "name": name,
            "category": category,
            "price": price
        }

        # If owner selects a new photo
        if image and image.filename:

            from werkzeug.utils import secure_filename
            import os

            filename = secure_filename(image.filename)

            image.save(
                os.path.join(
                    app.config["UPLOAD_FOLDER"],
                    filename
                )
            )

            update_data["image"] = filename

        coffees.update_one(
            {"_id": ObjectId(id)},
            {"$set": update_data}
        )

        return redirect("/admin/coffees")

    return render_template(
        "admin/editcoffee.html",
        coffee=coffee
    )
    
    
    
    
    
    
   
    
#delete message admin

@app.route("/admin/delete-message/<id>")
def delete_message(id):

    # Only admin can delete
    if "role" not in session or session["role"] != "admin":
        return redirect("/login")

    messages.delete_one({
        "_id": ObjectId(id)
    })

    return redirect("/admin/messages")


    
    
    
# bill
@app.route("/bill/<order_id>")
def view_bill(order_id):

    # Check that the order ID is valid
    try:
        order = orders.find_one({
            "_id": ObjectId(order_id)
        })
    except Exception:
        abort(404)

    if not order:
        abort(404)

    # Allow admin to view any order bill
    if session.get("role") != "admin":

        # Customers must be logged in
        customer_email = session.get("email")

        if not customer_email:
            return redirect("/login")

        # Customers can view only their own orders
        if order.get("user_email") != customer_email:
            abort(403)

    # Generate bill number for old and new orders
    bill_number = order.get("bill_number") or (
        "BB-" + str(order["_id"])[-8:].upper()
    )

    # Get order date
    order_date = order.get("created_at")

    return render_template(
        "bill.html",
        order=order,
        bill_number=bill_number,
        order_date=order_date
    )
    
    
    
    
    
    
    
    
    
    
#my bills

@app.route("/my-bills")
def my_bills():
    if "email" not in session:
        return redirect("/login")

    customer_email = session["email"]

    customer_orders = list(
        orders.find({
            "user_email": customer_email
        }).sort("_id", -1)
    )

    return render_template(
        "my_bills.html",
        orders=customer_orders
    )

    
    
    
    
    
    
    
    
    
#my profile
@app.route("/profile", methods=["GET", "POST"])
def profile():
    # Require login
    if "email" not in session:
        return redirect("/login")

    # Find the logged-in customer's own account
    customer = users.find_one({"email": session["email"]})

    if not customer:
        session.clear()
        return redirect("/login")

    message = ""
    error = ""

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        username = request.form.get("username", "").strip()
        mobile = request.form.get("mobile", "").strip()
        address = request.form.get("address", "").strip()

        # Basic validation
        if not name or not username:
            error = "Name and username are required."

        elif not mobile.isdigit() or len(mobile) != 10:
            error = "Enter a valid 10-digit mobile number."

        else:
            # Check that another account is not using this username
            existing_user = users.find_one({
                "username": username,
                "email": {"$ne": session["email"]}
            })

            if existing_user:
                error = "This username is already taken."

            else:
                # Update only the logged-in customer's record
                users.update_one(
                    {"_id": customer["_id"]},
                    {
                        "$set": {
                            "name": name,
                            "username": username,
                            "mobile": mobile,
                            "address": address
                        }
                    }
                )

                # Refresh the customer data and dashboard session
                customer = users.find_one({"_id": customer["_id"]})
                session["user"] = customer.get("name", name)

                message = "Your profile was updated successfully!"

    return render_template(
        "profile.html",
        customer=customer,
        message=message,
        error=error
    )
    
    
# RUN APPLICATION

if __name__ == "__main__":
    app.run(debug=True)   
    
    
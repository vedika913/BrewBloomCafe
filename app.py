from os import name

from bson import ObjectId
from flask import Flask, render_template, request, redirect, session
from database import users, coffees, orders, messages

app = Flask(__name__, template_folder="pages")
app.secret_key = "CoffeeShopSecret123"



    
# HOME
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

    success = False

    if request.method == "POST":

        name = request.form.get("name")
        email = request.form.get("email")
        phone = request.form.get("phone")
        message = request.form.get("message")

        # Insert ONLY ONCE
        messages.insert_one({
            "name": name,
            "email": email,
            "phone": phone,
            "message": message
        })

        return redirect("/contact?success=1")

    if request.args.get("success") == "1":
        success = True

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
            "password": password,
            "role": "user"
        }

        users.insert_one(new_user)

        return redirect("/login")

    return render_template("register.html")





# LOGIN

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        user = users.find_one({
            "email": email,
            "password": password
        })

        if not user:
            return "Invalid Email or Password"

        session["user"] = user["name"]
        session["email"] = user["email"]
        session["role"] = user["role"]

        print(session["role"])   # Debug

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

    orders.delete_one({"_id": ObjectId(id)})

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

    if "user" not in session:
        return redirect("/login")

    if session.get("role") != "admin":
        return "Access Denied"

    total_users = users.count_documents({})
    total_coffees = coffees.count_documents({})
    total_orders = orders.count_documents({})

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

    user = users.find_one({"_id": ObjectId(id)})

    return render_template(
        "admin/user_details.html",
        user=user
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
    
@app.route("/addcoffee", methods=["GET", "POST"])
def addcoffee():

    if "user" not in session:
        return redirect("/login")

    if session.get("role") != "admin":
        return "Access Denied!"

    if request.method == "POST":

        name = request.form["name"]
        category = request.form["category"]
        price = float(request.form["price"])
        image = request.form["image"]

        coffees.insert_one({
            "name": name,
            "category": category,
            "price": price,
            "image": image
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
    if "role" not in session or session["role"] != "admin":
        return redirect("/login")


    # GET request
    if request.method == "GET":

        coffee_list = list(coffees.find())

        return render_template(
            "new_order.html",
            coffees=coffee_list
        )


    # POST request

    customer_name = request.form.get("customer_name")

    order_type = request.form.get("order_type")

    table_number = request.form.get("table_number")

    coffee_id = request.form.get("coffee_id")

    quantity = int(request.form.get("quantity"))

    payment_method = request.form.get("payment_method")


    # Find selected coffee

    coffee = coffees.find_one({
        "_id": ObjectId(coffee_id)
    })


    if not coffee:

        return "Coffee not found"


    # Calculate total

    total_price = float(coffee["price"]) * quantity


    # Create counter order

    order = {

        "user_email": "Counter", 
        
        "user_name": name,

        "order_type": order_type,

        "customer_name": customer_name,

        "table_number": table_number
            if order_type == "Dine-in"
            else "",

        "coffee_name": coffee["name"],

        "quantity": quantity,

        "price": total_price,

        "payment_method": payment_method,

        "status": "delivered"

    }


    orders.insert_one(order)


    return redirect("/admin/orders")





# RUN APPLICATION

if __name__ == "__main__":
    app.run(debug=True)   
    
    
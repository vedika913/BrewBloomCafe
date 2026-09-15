from database import coffees

coffee_list = [

    {
        "name": "Espresso",
        "price": 120,
        "image": "espresso.jpg",
        "category": "Hot Coffee"
    },

    {
        "name": "Cappuccino",
        "price": 180,
        "image": "cappuccino.jpg",
        "category": "Hot Coffee"
    },

    {
        "name": "Latte",
        "price": 200,
        "image": "latte.jpg",
        "category": "Hot Coffee"
    },

    {
        "name": "Cold Coffee",
        "price": 150,
        "image": "coldcoffee.jpg",
        "category": "Cold Coffee"
    }

]

coffees.insert_many(coffee_list)

print("Coffee items inserted successfully!")
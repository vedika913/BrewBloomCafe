let cart = [];
function addToCart(name, price) {
    cart.push({
        name: name,
        price: price
    });
    alert(name + "added to cart!");
    console.log(cart);
}

function toggleTable() {

    const orderType =
        document.getElementById("orderType").value;

    const tableBox =
        document.getElementById("tableBox");

    if (orderType === "Dine-in") {

        tableBox.style.display = "block";

    } else {

        tableBox.style.display = "none";

    }

}




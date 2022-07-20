
function makeAjaxRequest(requestType, url, data, callBack){
    $.ajax({
            type:requestType,
            url: url,
            data:data,
            success: callBack
        }
    );
}


function updateCartDetails(itemsInCart){
    let navElementCart = document.getElementById('navElementCart');
    navElementCart.innerHTML = itemsInCart == 0? "Cart" : "Cart (" + itemsInCart + ")";
}

function addToCart(productId){
    
    makeAjaxRequest(
        'GET',
        "/myshop/cart/addToCart",
        {
            productId: productId,
        },
        function( data ) 
        {
            let product = document.getElementById("Product_"+productId);
            product.innerHTML = "Remove from Cart"
            product.classList.remove('btn-primary');
            product.classList.add('btn-danger');
            product.onclick = ()=>{
                removeFromCart(productId);
            };
            updateCartDetails(data['itemsInCart']);
        }
    );
}

function removeFromCart(productId){

    makeAjaxRequest(
        "GET",
        "/myshop/cart/removeFromCart",
        {
            productId: productId,
        },
        function( data ) 
        {
            let product = document.getElementById("Product_"+productId);
            product.innerHTML = "Add to Cart"
            product.classList.remove('btn-danger');
            product.classList.add('btn-primary');
            product.onclick = ()=>{
                addToCart(productId);
            };
            updateCartDetails(data['itemsInCart']);
        }
    );
}


function removeProductFromCart__CartPage(productId){

    makeAjaxRequest(
        "GET",
        "/myshop/cart/removeFromCart",
        {
            productId: productId,
        },
        function( data ) 
        {
            let product = document.getElementById("cartItem_"+productId);
            updateCartDetails(data['itemsInCart']);
            product.parentNode.removeChild(product);

            if( data['itemsInCart'] == 0 ){
                let noItemInCart = document.getElementById("noItemInCart");
                let userDetailsContainer = document.getElementById("userDetailsContainer");
                userDetailsContainer.style.display = "none";
                noItemInCart.style.display = "flex";
            }
        }
    );
}



function changeCartItemQuantity(productId, incrementBy){

    let productQty = document.getElementById("product_" + productId + "_qty").innerHTML;
    productQty = productQty.replace(" Unit(s)", "");

    if( incrementBy == -1 && productQty == 1 ){
        alert("Product Quantity can't be zero. You can remove it.");
        return;
    }

    makeAjaxRequest(
        "GET",
        "/myshop/cart/changeCartItemQuanity",
        {
            productId: productId,
            incrementBy : incrementBy,
        },
        function( data ) 
        {
            let productQty = document.getElementById("product_" + productId + "_qty");
            productQty.innerText = data['productQty'] + " Unit(s)";
        }
    );
}




// Getting the count of items in the cart //
function initializeUtilities(){
    
    makeAjaxRequest(
        "GET",
        "/myshop/cart/getCartItemsCount",
        {},
        function( data ) 
        {
            updateCartDetails(data['itemsInCart']);
        }
    );
}
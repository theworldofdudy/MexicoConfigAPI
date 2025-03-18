const API_URL = "http://127.0.0.1:8000";

// Detectar clic en el botón "paramVal"
document.addEventListener("DOMContentLoaded", function () {

    // Detectar clic en el botón "paramVal"
    const btnParamVal = document.querySelector(".btn-large i.left").parentElement;
    const btnTitulosVal = document.querySelector(".btn-large i.right").parentElement;
    
    btnParamVal.addEventListener("click", function () {
        console.log("Botón paramVal clickeado");
    
        fetch(`${API_URL}/param`)
            .then(response => response.json())
            .then(data => {
                document.querySelector(".collection").innerHTML = "";
                Object.entries(data).forEach(([key, value]) => {
                    const item = document.createElement("a");
                    item.href = "#!";
                    item.classList.add("collection-item");
                    item.innerHTML = `<span class="badge">${value}</span>${key}`;
                    document.querySelector(".collection").appendChild(item);
                }); // ✅ Se cierra correctamente el forEach()
                document.querySelector(".card-title").innerText = "";
            }) // ✅ Se cierra correctamente el .then()
            .catch(error => console.error("Error fetching data:", error)); // .catch() está fuera del bloque .then()

        /*         // Hacer la petición al API
        fetch(`${API_URL}/param`)
            .then(response => response.json())
            .then(data => {
                document.querySelector(".card-title").innerText = JSON.stringify(data, null, 2);
            })
            .catch(error => console.error("Error fetching data:", error));*/
    
    });



    btnTitulosVal.addEventListener("click", function () {
        console.log("Botón titulosVal clickeado");

        fetch(`${API_URL}/titulos`)
        .then(response => response.json())
        .then(data => {
            document.querySelector(".collection").innerHTML = "";
            Object.entries(data).forEach(([key, value]) => {
                const item = document.createElement("a");
                item.href = "#!";
                item.classList.add("collection-item");
                item.innerHTML = `<span class="badge">${value}</span>${key}`;
                document.querySelector(".collection").appendChild(item);
            }); // ✅ Se cierra correctamente el forEach()
            document.querySelector(".card-title").innerText = "";
        }) // ✅ Se cierra correctamente el .then()
        .catch(error => console.error("Error fetching data:", error)); // .catch() está fuera del bloque .then()



/*         // Hacer la petición al API
        fetch(`${API_URL}/titulos`)
            .then(response => response.json())
            .then(data => {
                document.querySelector(".card-title").innerText = JSON.stringify(data, null, 2);
            })
            .catch(error => console.error("Error fetching data:", error)); */
    });


});
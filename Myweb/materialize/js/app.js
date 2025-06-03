const API_URL = "http://127.0.0.1:8000";

function clearCollection() {
    // Vaciar todo el contenido dinámico
    const collection = document.querySelector(".collection");
    collection.innerHTML = "";

    // Ocultar el input si existe
    const wrapper = document.getElementById('ctlRegisterWrapper');
    if (wrapper) {
        wrapper.style.display = 'none';
    }

    // Limpiar el contenido del textarea si existe
    const textarea = document.getElementById('ctlRegisterTextarea');
    if (textarea) {
        textarea.value = '';
    }

    // Actualizar Materialize
    M.updateTextFields();
}

// Detectar clic en el botón "paramVal"
document.addEventListener("DOMContentLoaded", function () {

    // Detectar clic en el botón "paramVal"
    const btnParamVal = document.getElementById("btnParamVal");
    const btnTitulosVal = document.getElementById("btnTitulosVal");
    const btnCtlRegister = document.getElementById("btnCtlRegister");
    const btnSendRegister = document.getElementById("btnSendRegister");

    btnParamVal.addEventListener("click", function () {
        console.log("Botón paramVal clickeado");
        clearCollection();

        fetch(`${API_URL}/param`)
            .then(response => response.json())
            .then(data => {
                document.querySelector(".collection").innerHTML = ""; // Limpiar la colección previa
                console.log("Data received:", data);

                Object.entries(data).forEach(([key, value]) => {
                    const item = document.createElement("a");
                    item.href = "#!";
                    item.classList.add("collection-item");

                    // Si la clave es "zones" y tiene un array, creamos una sub-collection
                    if (key === "zones" && Array.isArray(value)) {
                        console.log("Zones detected");
                        item.innerHTML = `<b>${key}</b>`; // Only title
                        const subCollection = document.createElement("div");
                        subCollection.classList.add("collection", "sub-collection");

                        value.forEach(zone => {
                            const subItem = document.createElement("a");
                            subItem.href = "#!";
                            subItem.classList.add("collection-item");
                            subItem.textContent = zone; // Mostramos el contenido del array
                            subCollection.appendChild(subItem);
                        });

                        item.appendChild(subCollection); // Agregamos la sub-colección al item principal
                    } else {
                        // Si no es "zones", agregar como un item normal con badge
                        item.innerHTML = `<span class="badge">${value}</span>${key}`;
                    }

                    document.querySelector(".collection").appendChild(item);
                });
                document.querySelector(".card-title").innerText = "INFORMACIÓN DE PARÁMETROS ACTUALIZADA";
            })
            .catch(error => console.error("Error fetching data:", error));
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

        clearCollection();

        fetch(`${API_URL}/titulos2`)
            .then(response => response.json())
            .then(data => {

                document.querySelector(".collection").innerHTML = "";

                const jsondata = data.data;
                Object.entries(jsondata).forEach(([titulo, index]) => {
                    console.log("Index: ", index, "Titulo: ", titulo);
                    const titItem = document.createElement("a");
                    titItem.href = "#!";
                    titItem.classList.add("collection-tit-item")

                    document.querySelector(".collection").appendChild(titItem);

                    index.forEach((line, subIndex) => {
                        const item = document.createElement("a");
                        item.href = "#!";
                        item.classList.add("collection-item");
                        item.textContent = line;
                        document.querySelector(".collection").appendChild(item);
                    });

                }); //  Se cierra correctamente el forEach()
                document.querySelector(".card-title").innerText = "INFORMACIÓN DE TÍTULOS ACTUALIZADA";
            }) // Se cierra correctamente el .then()
            .catch(error => console.error("Error fetching data:", error)); // .catch() está fuera del bloque .then()
    });

    btnCtlRegister.addEventListener('click', function () {

        document.querySelector(".card-title").innerText = " Copie el registro a procesar en el campo de texto y pulse el botón para aceptar";
        clearCollection();

        const wrapper = document.getElementById('ctlRegisterWrapper');

        if (!wrapper) {
            console.error("ctlRegisterWrapper no está definido en el HTML.");
            return;
        }

        if (wrapper.style.display === 'none') {
            wrapper.style.display = 'block';

            const textarea = document.getElementById('ctlRegisterTextarea');
            M.textareaAutoResize(textarea);
            M.updateTextFields();
        } else {
            console.log("El campo ya está visible.");
        }

    });

    btnSendRegister.addEventListener('click', function () {

        console.log("Botón Send Register clickeado");
        // Vaciar todo el contenido dinámico
        const collection = document.querySelector(".collection");
        collection.innerHTML = "";

        const text = document.getElementById("ctlRegisterTextarea").value;

        fetch("http://127.0.0.1:8000/register", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ registerString: text })
        })
            .then(response => response.json())
            .then(data => {
                document.getElementById("data").textContent = data.processed_text;
                console.log("Data received:", data);

                Object.entries(data).forEach(([key, value]) => {
                    const item = document.createElement("a");
                    item.href = "#!";
                    item.classList.add("collection-item");

                    item.innerHTML = `<span class="badge">${value}</span>${key}`;
                    document.querySelector(".collection").appendChild(item);
                });
            })
            .catch(error => console.error("Error:", error));
    });


});

/*     btnTitulosVal.addEventListener("click", function () {
        console.log("Botón titulosVal clickeado");

        fetch(`${API_URL}/titulos`)
        .then(response => response.json())
        .then(data => {
            document.querySelector(".collection").innerHTML = "";
            Object.entries(data).forEach(([index, titulo]) => {
                const titItem = document.createElement("a");
                titItem.href = "#!";
                titItem.classList.add("collection-tit-item");
                Object.entries(data).forEach(([key, value]) => {
                    const item = document.createElement("a");
                    item.href = "#!";
                    item.classList.add("collection-item");
                        // Si la clave es "TransferTimes" y tiene un array, creamos una sub-collection
                        if (key.trim() === "TransferTimes") {
                            console.log("Key detected: ", key, "Value:", value, "Type:", typeof value);
                            console.log("TransferTimes detected");
                            item.innerHTML = `<b>${key}</b>`; // Only title
                            const subCollection = document.createElement("div");
                            subCollection.classList.add("collection", "sub-collection");

                            value.forEach(transfer  => {
                                const subItem = document.createElement("a");
                                subItem.href = "#!";
                                subItem.classList.add("collection-item");
                                subItem.textContent = transfer ; // Mostramos el contenido del array
                                subCollection.appendChild(subItem);
                            });

                            item.appendChild(subCollection); // Agregamos la sub-colección al item principal
                        } else {
                            // Si no es "zones", agregar como un item normal con badge
                            item.innerHTML = `<span class="badge">${value}</span>${key}`;
                        }

                        document.querySelector(".collection").appendChild(item);
                }); // Se cierra correctamente el forEach()
            
                titItem.innerHTML = `<span class="badge">${titulo}</span>${index}`;
            });
            document.querySelector(".card-title").innerText = "INFORMACIÓN DE TÍTULOS ACTUALIZADA";
        }) // Se cierra correctamente el .then()
        .catch(error => console.error("Error fetching data:", error)); // .catch() está fuera del bloque .then()
    }); */


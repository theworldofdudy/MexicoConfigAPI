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
                document.querySelector(".collection").innerHTML = ""; // Limpiar la colección previa

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

                }); // ✅ Se cierra correctamente el forEach()
                        });
            document.querySelector(".card-title").innerText = "INFORMACIÓN DE TÍTULOS ACTUALIZADA";
        }) // ✅ Se cierra correctamente el .then()
        .catch(error => console.error("Error fetching data:", error)); // .catch() está fuera del bloque .then()
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
                }); // ✅ Se cierra correctamente el forEach()
            
                titItem.innerHTML = `<span class="badge">${titulo}</span>${index}`;
            });
            document.querySelector(".card-title").innerText = "INFORMACIÓN DE TÍTULOS ACTUALIZADA";
        }) // ✅ Se cierra correctamente el .then()
        .catch(error => console.error("Error fetching data:", error)); // .catch() está fuera del bloque .then()
    }); */

document.addEventListener('DOMContentLoaded', () => {
    // Elementos del DOM
    const dogImage = document.getElementById('dog-image');
    const saveButton = document.getElementById('save-dog');
    const petNameInput = document.getElementById('pet-name');
    const breedSelect = document.getElementById('breed-select');
    const petsList = document.getElementById('pets-list');
    const getDogButton = document.getElementById('get-dog');
    const completeAdoptionBtn = document.getElementById('complete-adoption');
    const adopterNameInput = document.getElementById('adopter-name');
    const adopterEmailInput = document.getElementById('adopter-email');
    const adopterPhoneInput = document.getElementById('adopter-phone');

    // Configuración de la API
    const API_BASE_URL = 'http://localhost:5000';

    // Estado
    let currentSelectedPet = null;

    // Inicialización
    init();

    function init() {
        setupEventListeners();
        fetchBreeds();
        loadPets();
    }

    function setupEventListeners() {
        getDogButton.addEventListener('click', fetchRandomDog);
        saveButton.addEventListener('click', savePet);
        petsList.addEventListener('click', handlePetCardClick);
        completeAdoptionBtn.addEventListener('click', completeAdoption);
    }

    async function fetchRandomDog() {
        try {
            showLoading('#dog-image-container', 'Cargando perro...');
            const response = await fetch(`${API_BASE_URL}/api/dogs/random`);
            const data = await response.json();

            if (data.image_url) {
                dogImage.src = data.image_url;
                dogImage.onload = () => {
                    saveButton.disabled = false;
                    hideLoading('#dog-image-container');
                };
            } else {
                throw new Error('No se recibió imagen válida');
            }
        } catch (error) {
            console.error('Error al obtener perro:', error);
            showTempMessage('Error al cargar perro aleatorio', 'error');
            hideLoading('#dog-image-container');
        }
    }

    async function fetchBreeds() {
        try {
            showLoading('#breed-select-container', 'Cargando razas...');
            const response = await fetch(`${API_BASE_URL}/api/dogs/breeds`);
            const data = await response.json();

            breedSelect.innerHTML = '<option value="">Selecciona una raza...</option>';
            data.breeds.forEach(breed => {
                const option = document.createElement('option');
                option.value = breed;
                option.textContent = breed;
                breedSelect.appendChild(option);
            });
        } catch (error) {
            console.error('Error al cargar razas:', error);
            showTempMessage('Error al cargar razas', 'error');
        } finally {
            hideLoading('#breed-select-container');
        }
    }

    async function savePet() {
        const nombre = petNameInput.value.trim();
        const imagen_url = dogImage.src;
        const raza = breedSelect.value;

        if (!nombre) {
            showTempMessage('Por favor ingresa un nombre', 'error');
            return;
        }

        try {
            saveButton.disabled = true;
            showLoading('#pets-list', 'Guardando mascota...');

            const response = await fetch(`${API_BASE_URL}/api/mascotas`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ nombre, imagen_url, raza })
            });

            if (response.ok) {
                showTempMessage('Mascota guardada', 'success');
                petNameInput.value = '';
                loadPets();
            } else {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Error al guardar');
            }
        } catch (error) {
            console.error('Error al guardar:', error);
            showTempMessage(`Error: ${error.message}`, 'error');
        } finally {
            saveButton.disabled = false;
            hideLoading('#pets-list');
        }
    }

    async function loadPets() {
        try {
            showLoading('#pets-list', 'Cargando mascotas...');
            const response = await fetch(`${API_BASE_URL}/api/mascotas`);
            const mascotas = await response.json();
            renderPets(mascotas);
        } catch (error) {
            console.error('Error al cargar mascotas:', error);
            petsList.innerHTML = `
                <div class="error-message">
                    <i class="fas fa-exclamation-triangle"></i>
                    <p>Error al cargar mascotas</p>
                </div>
            `;
        } finally {
            hideLoading('#pets-list');
        }
    }

    function renderPets(mascotas) {
        if (mascotas.length === 0) {
            petsList.innerHTML = `
                <div class="no-pets">
                    <i class="fas fa-search"></i>
                    <p>No hay mascotas guardadas aún</p>
                </div>
            `;
            return;
        }

        petsList.innerHTML = mascotas.map(pet => `
            <div class="pet-card ${pet.adoptado ? 'adoptado' : ''}" data-id="${pet.id}">
                <button class="delete-btn" aria-label="Eliminar mascota">
                    <i class="fas fa-times"></i>
                </button>
                <img src="${pet.imagen_url}" alt="${pet.nombre}" loading="lazy">
                <div class="pet-card-content">
                    <h3>${pet.nombre}</h3>
                    <p><strong>Raza:</strong> ${pet.raza || 'Desconocida'}</p>
                    ${pet.adoptado ? '<span class="badge-adoptado">Adoptado</span>' : `
                        <button class="select-pet-btn">
                            <i class="fas fa-paw"></i> Seleccionar para adopción
                        </button>
                    `}
                </div>
            </div>
        `).join('');
    }

    function handlePetCardClick(event) {
        const deleteBtn = event.target.closest('.delete-btn');
        const selectBtn = event.target.closest('.select-pet-btn');
        const petCard = event.target.closest('.pet-card');

        if (deleteBtn) {
            deletePet(petCard.dataset.id);
        } else if (selectBtn) {
            selectPetForAdoption(petCard);
        }
    }

    async function deletePet(petId) {
        if (!confirm('¿Eliminar esta mascota?')) return;

        try {
            showLoading('#pets-list', 'Eliminando...');
            const response = await fetch(`${API_BASE_URL}/api/mascotas/${petId}`, {
                method: 'DELETE'
            });

            if (response.ok) {
                showTempMessage('Mascota eliminada', 'success');
                loadPets();
            } else {
                throw new Error('No se pudo eliminar');
            }
        } catch (error) {
            console.error('Error al eliminar:', error);
            showTempMessage('Error al eliminar', 'error');
        } finally {
            hideLoading('#pets-list');
        }
    }

    function selectPetForAdoption(petCard) {
        const petId = petCard.dataset.id;
        const petName = petCard.querySelector('h3').textContent;
        const petImage = petCard.querySelector('img').src;
        const petBreed = petCard.querySelector('p').textContent.replace('Raza: ', '');

        currentSelectedPet = { id: petId, name: petName, image: petImage, breed: petBreed };

        document.querySelectorAll('.pet-card').forEach(card => card.classList.remove('selected'));
        petCard.classList.add('selected');

        document.getElementById('selected-pet-name').textContent = petName;
        document.getElementById('selected-pet-image').src = petImage;
        document.getElementById('selected-pet-breed').textContent = petBreed;
        document.getElementById('selected-pet-display').style.display = 'block';
        document.getElementById('no-pet-selected').style.display = 'none';
    }

    async function completeAdoption() {
        if (!currentSelectedPet) {
            showTempMessage("Selecciona una mascota primero", "error");
            return;
        }

        const nombre = adopterNameInput.value.trim();
        const email = adopterEmailInput.value.trim();
        const telefono = adopterPhoneInput.value.trim();

        if (!nombre || !email || !telefono) {
            showTempMessage("Completa todos los campos", "error");
            return;
        }

        try {
            completeAdoptionBtn.disabled = true;
            showLoading('.adoption-form', 'Registrando adopción...');

            const response = await fetch(`${API_BASE_URL}/api/adopciones`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    mascota_id: currentSelectedPet.id,
                    nombre,
                    email,
                    telefono
                })
            });

            if (response.ok) {
                showTempMessage("¡Adopción registrada!", "success");
                loadPets();
                resetAdoptionForm();
            } else {
                const err = await response.json();
                throw new Error(err.error || "Error al registrar adopción");
            }
        } catch (error) {
            console.error("Error en adopción:", error);
            showTempMessage(`Error: ${error.message}`, "error");
        } finally {
            completeAdoptionBtn.disabled = false;
            hideLoading('.adoption-form');
        }
    }

    function resetAdoptionForm() {
        adopterNameInput.value = '';
        adopterEmailInput.value = '';
        adopterPhoneInput.value = '';
        currentSelectedPet = null;

        document.getElementById('selected-pet-display').style.display = 'none';
        document.getElementById('no-pet-selected').style.display = 'block';
        document.querySelectorAll('.pet-card').forEach(card => card.classList.remove('selected'));
    }

    // Utilidades visuales
    function showTempMessage(message, type = 'error') {
        const msg = document.createElement('div');
        msg.className = `temp-message ${type}`;
        msg.innerHTML = `
            <i class="fas fa-${type === 'error' ? 'exclamation-circle' : 'check-circle'}"></i>
            <span>${message}</span>
        `;
        document.body.appendChild(msg);

        setTimeout(() => {
            msg.classList.add('fade-out');
            setTimeout(() => msg.remove(), 300);
        }, 3000);
    }

    function showLoading(containerSelector, text = 'Cargando...') {
        const container = document.querySelector(containerSelector);
        const loadingDiv = document.createElement('div');
        loadingDiv.className = 'loading-container';
        loadingDiv.innerHTML = `
            <div class="loading-spinner"></div>
            <p class="loading-text">${text}</p>
        `;
        container.appendChild(loadingDiv);
    }

    function hideLoading(containerSelector) {
        const container = document.querySelector(containerSelector);
        const loadingDiv = container.querySelector('.loading-container');
        if (loadingDiv) {
            loadingDiv.remove();
        }
    }
});

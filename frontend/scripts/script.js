/* Navigation Menu Functions */
function openNav() {
    document.getElementById("mySidenav").style.width = "250px";
}

function closeNav() {
    document.getElementById("mySidenav").style.width = "0";
}

/* Modal Functions */
function openModal(modalId) {
    document.getElementById(modalId).style.display = "block";
    closeNav(); // Close menu when opening modal
}

function closeModal(modalId) {
    document.getElementById(modalId).style.display = "none";
}

// Close modal if user clicks outside of it
window.onclick = function(event) {
    if (event.target.classList.contains('modal')) {
        event.target.style.display = "none";
    }
}

function showLoader() {
    // Show loader
    document.getElementById('loader').style.display = 'flex';
    
    // Update button text and state
    const btn = document.querySelector('.btn-simulate');
    if (btn) {
        btn.innerText = "Running Simulation & Updating View...";
        btn.disabled = true;
        btn.style.opacity = "0.7";
        btn.style.cursor = "not-allowed";
    }
}

function openModal(id) {
    document.getElementById(id).classList.remove('hidden');
}

function closeModal(id) {
    document.getElementById(id).classList.add('hidden');
}

// ── Mobile sidebar drawer ──
(function () {
    const sidebar  = document.getElementById('sidebar');
    const overlay  = document.getElementById('sidebar-overlay');
    const toggleBtn = document.getElementById('sidebar-toggle');
    const closeBtn  = document.getElementById('sidebar-close');

    if (!sidebar) return;

    function openSidebar() {
        sidebar.classList.add('open');
        overlay.classList.add('active');
        document.body.style.overflow = 'hidden';
    }

    function closeSidebar() {
        sidebar.classList.remove('open');
        overlay.classList.remove('active');
        document.body.style.overflow = '';
    }

    toggleBtn?.addEventListener('click', openSidebar);
    closeBtn?.addEventListener('click', closeSidebar);
    overlay?.addEventListener('click', closeSidebar);

    // Close drawer when user navigates away via a nav link
    sidebar.querySelectorAll('.nav-item').forEach(function (link) {
        link.addEventListener('click', closeSidebar);
    });
}());



class AuthApp{
    #loginForm = document.getElementById('login-form')
    #loginInput = document.getElementById('login-email')
    #passwordInput = document.getElementById('login-password')
    constructor(){
        this.#loginForm.addEventListener('submit', e =>{
            this._loginUser(e, this.#loginInput, this.#passwordInput)
        })

    }

    _loginUser(e, login , password){
        e.preventDefault()
        console.log(login.value, password.value)
        // fake login ->> fix later when Auth models created
        window.location.href = '/'
    }
}

if(window.location.href == "/api/users/login"){
    let authApp = new AuthApp()
}
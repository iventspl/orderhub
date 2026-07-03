function openModal(id) {
    document.getElementById(id).classList.remove('hidden');
}

function closeModal(id) {
    document.getElementById(id).classList.add('hidden');
}



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
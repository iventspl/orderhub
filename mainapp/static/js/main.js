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


// sidebar active state handling
// forget it will be done via views and page
// const navItems = document.querySelector('.nav')
// const navItemsElements = document.querySelectorAll('.nav-link')

// if(navItems){
//     navItems.addEventListener('click', e=>{
//         const clickedLink = e.target.closest('.nav-link');
//         if(!clickedLink) return
//         if(navItemsElements){
//             navItemsElements.forEach(el=>{
//                 el.classList.remove('active')
//             })
//             clickedLink.classList.add('active')
//         }

//     })
// }
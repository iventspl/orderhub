
class UsersApp{
    #loginLink = document.querySelector('button[data-login-tab="login"]')
    #registerLink = document.querySelector('button[data-login-tab="register"]')
    
    constructor(){
        // this._initRegisterForm()

        this.#loginLink?.addEventListener('click', e =>{
            e.preventDefault()
            window.location.href = '/users/login'
        })

        this.#registerLink?.addEventListener('click', e =>{
            e.preventDefault()
            window.location.href = '/users/register'
        })
    }

    // _initRegisterForm(){
    //     const registerForm = document.getElementById('register-form')
    //     if(registerForm){
    //         registerForm.addEventListener('submit', e =>{
    //             this._registerUser(e, registerForm)
    //         })
    //     }
    // }
}

const usersApp = new UsersApp()
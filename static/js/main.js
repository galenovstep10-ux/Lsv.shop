// main.js - исправленная версия

// Получаем элементы
const modal = document.getElementById("modal-register");
const profileBtn = document.getElementById("profile-btn");
const closeBtn = document.querySelector(".close-btn");
const toast = document.getElementById("success-toast");
const formRegister = document.getElementById("form-register");
const formLogin = document.getElementById("form-login");
const toggleForm = document.getElementById("toggle-form");
const modalTitle = document.getElementById("modal-title");

let isLoginMode = false;

// Проверка localStorage
if (localStorage.getItem("isLoggedIn") === "true") {
  isLoginMode = true;
}

// Функция переключения форм
function showForm(login) {
  if (login) {
    formRegister.style.display = "none";
    formLogin.style.display = "block";
    modalTitle.textContent = "Вход";
    toggleForm.textContent = "Нет аккаунта? Зарегистрироваться";
  } else {
    formRegister.style.display = "block";
    formLogin.style.display = "none";
    modalTitle.textContent = "Регистрация";
    toggleForm.textContent = "Уже зарегистрированы? Войти";
  }
}

// Открыть модальное окно
if (profileBtn) {
  profileBtn.addEventListener("click", function(e) {
    e.preventDefault();
    modal.style.display = "flex";
    showForm(isLoginMode);
  });
}

// Закрыть по крестику
if (closeBtn) {
  closeBtn.addEventListener("click", function() {
    modal.style.display = "none";
  });
}

// Закрыть по клику вне окна
window.addEventListener("click", function(e) {
  if (e.target === modal) {
    modal.style.display = "none";
  }
});

// Переключение между формами
if (toggleForm) {
  toggleForm.addEventListener("click", function(e) {
    e.preventDefault();
    isLoginMode = !isLoginMode;
    showForm(isLoginMode);
  });
}

// Отправка формы регистрации
if (formRegister) {
  formRegister.addEventListener("submit", function(e) {
    e.preventDefault();
    modal.style.display = "none";
    toast.textContent = "Вы успешно зарегистрировались";
    toast.classList.add("show");
    setTimeout(function() {
      toast.classList.remove("show");
    }, 3000);
    isLoginMode = true;
    localStorage.setItem("isLoggedIn", "true");
  });
}

// Отправка формы входа
if (formLogin) {
  formLogin.addEventListener("submit", function(e) {
    e.preventDefault();
    modal.style.display = "none";
    toast.textContent = "Вы вошли в систему";
    toast.classList.add("show");
    setTimeout(function() {
      toast.classList.remove("show");
    }, 3000);
    localStorage.setItem("isLoggedIn", "true");
  });
}
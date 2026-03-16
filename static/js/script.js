// Таймер обратного отсчета
const endDate = new Date("2026-03-23T00:00:00").getTime(); // можно поправить дату
const timer = document.getElementById("timer");
if (timer) {
  setInterval(() => {
    const now = new Date().getTime();
    const diff = endDate - now;

    if (diff <= 0) {
      timer.innerHTML = "Сегодня день чемпионата!";
      return;
    }

    const days = Math.floor(diff / (1000 * 60 * 60 * 24));
    const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
    const mins = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));

    timer.innerHTML = `${days} дн. ${hours} ч. ${mins} мин.`;
  }, 1000);
}

// Скрипт для "прилипающей" навигации (кроме главной страницы)
window.addEventListener("scroll", function () {
  const nav = document.querySelector(".main-nav");

  // если это главная страница (у навигации есть класс .no-stick) — выходим
  if (!nav || nav.classList.contains("no-stick")) return;

  if (window.scrollY > 50) {
    nav.classList.add("scrolled");
  } else {
    nav.classList.remove("scrolled");
  }
});

// Анимация появления блоков при прокрутке
const elements = document.querySelectorAll('.slide-up');
const observer = new IntersectionObserver(entries => {
  entries.forEach(entry => {
    if (entry.isIntersecting) entry.target.classList.add('show');
  });
});
elements.forEach(el => observer.observe(el));

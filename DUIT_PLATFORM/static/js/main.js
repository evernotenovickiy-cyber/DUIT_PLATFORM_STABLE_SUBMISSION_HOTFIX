document.addEventListener("DOMContentLoaded", function () {
  // Мобильное меню
  var toggle = document.querySelector(".navbar__toggle");
  var navbar = document.querySelector(".navbar");
  if (toggle && navbar) {
    var mobileMenu = document.getElementById("mobile-menu");
    function setMenu(open) {
      navbar.classList.toggle("is-open", open);
      document.body.classList.toggle("menu-open", open);
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
      toggle.setAttribute("aria-label", open ? "Закрыть меню" : "Открыть меню");
      if (mobileMenu) mobileMenu.setAttribute("aria-hidden", open ? "false" : "true");
    }
    toggle.addEventListener("click", function () {
      setMenu(!navbar.classList.contains("is-open"));
    });
    if (mobileMenu) mobileMenu.querySelectorAll("a").forEach(function (link) {
      link.addEventListener("click", function () { setMenu(false); });
    });
    document.addEventListener("keydown", function (event) {
      if (event.key === "Escape") setMenu(false);
    });
  }

  // Подсказка о количестве выбранных фото при создании/редактировании услуги
  var photoInput = document.querySelector('input[name="photos"]');
  var photoHint = document.querySelector("[data-photo-count]");
  if (photoInput && photoHint) {
    photoInput.addEventListener("change", function () {
      var count = photoInput.files ? photoInput.files.length : 0;
      photoHint.textContent = count
        ? "Выбрано файлов: " + count
        : "";
    });
  }

  // Подтверждение удаления
  document.querySelectorAll("[data-confirm]").forEach(function (form) {
    form.addEventListener("submit", function (event) {
      var message = form.getAttribute("data-confirm");
      if (!window.confirm(message)) {
        event.preventDefault();
      }
    });
  });
});

// Плавное появление блоков при прокрутке. Не мешает работе сайта,
// а при prefers-reduced-motion CSS сразу показывает контент без анимации.
document.addEventListener("DOMContentLoaded", function () {
  var revealItems = document.querySelectorAll("[data-reveal]");
  if ("IntersectionObserver" in window) {
    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add("is-visible");
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.08, rootMargin: "0px 0px -20px 0px" });
    revealItems.forEach(function (item) { observer.observe(item); });
  } else {
    revealItems.forEach(function (item) { item.classList.add("is-visible"); });
  }

  // При смене большой сферы обновляем список вложенных направлений.
  document.querySelectorAll("[data-auto-submit]").forEach(function (field) {
    field.addEventListener("change", function () {
      if (field.form) {
        var categoryField = field.form.querySelector('[name="category"]');
        if (categoryField) categoryField.value = "";
        field.form.submit();
      }
    });
  });
});

// Быстрое избранное прямо из карточки: интерфейс реагирует без перезагрузки.
document.addEventListener("DOMContentLoaded", function () {
  document.querySelectorAll("[data-favorite-form]").forEach(function (form) {
    form.addEventListener("submit", function (event) {
      if (!window.fetch) return;
      event.preventDefault();
      var button = form.querySelector("button");
      var data = new FormData(form);
      fetch(form.action, {
        method: "POST",
        body: data,
        headers: {"X-Requested-With": "XMLHttpRequest"},
        credentials: "same-origin"
      }).then(function (response) { return response.json(); }).then(function (payload) {
        if (!payload.ok || !button) return;
        button.classList.toggle("is-active", payload.favorite);
        if (button.classList.contains("favorite-detail")) {
          button.textContent = payload.favorite ? "♥ В избранном" : "♡ Сохранить";
        } else {
          button.textContent = payload.favorite ? "♥" : "♡";
        }
      }).catch(function () { form.submit(); });
    });
  });
});

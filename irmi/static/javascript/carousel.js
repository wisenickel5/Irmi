let carouselPosition = 0;
const carouselItems = document.querySelectorAll(".carousel-item");
const totalItems = carouselItems.length;

function moveCarousel(direction) {
    carouselPosition += direction;

    if (carouselPosition < 0) {
        carouselPosition = totalItems - 1;
    } else if (carouselPosition >= totalItems) {
        carouselPosition = 0;
    }

    document.querySelector(".carousel-inner").style.transform = `translateX(-${carouselPosition * 100}%)`;
}

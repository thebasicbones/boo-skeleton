// Simple JavaScript for the static frontend
console.log('FastAPI CRUD Backend - Ready!');

// Add smooth scroll behavior
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth'
            });
        }
    });
});

// Add animation on load
window.addEventListener('load', () => {
    document.querySelector('.container').style.opacity = '0';
    document.querySelector('.container').style.transform = 'translateY(20px)';
    
    setTimeout(() => {
        document.querySelector('.container').style.transition = 'all 0.5s ease';
        document.querySelector('.container').style.opacity = '1';
        document.querySelector('.container').style.transform = 'translateY(0)';
    }, 100);
});

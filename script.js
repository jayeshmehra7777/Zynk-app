document.addEventListener('DOMContentLoaded', function() {
    const button = document.getElementById('clickMe');
    
    button.addEventListener('click', function() {
        alert('Hello from Zynk App! 🚀');
        
        // Add some visual feedback
        button.style.background = 'linear-gradient(135deg, #4CAF50 0%, #45a049 100%)';
        button.textContent = 'Clicked!';
        
        setTimeout(() => {
            button.style.background = 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)';
            button.textContent = 'Click Me';
        }, 1000);
    });
});

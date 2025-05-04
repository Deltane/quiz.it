const h2Element = document.getElementById("text");
const text = h2Element.textContent; // Use the content inside the <h2> as the text
const typingSpeed = 100; // Speed in milliseconds
let index = 0;

function typeText() {
  if (index < text.length) {
    h2Element.innerHTML = text.substring(0, index) + '<span class="cursor">_</span>'; // Add the blinking underscore
    index++;
    setTimeout(typeText, typingSpeed);
  } else {
    h2Element.innerHTML = text + '<span class="cursor">_</span>'; // Keep the underscore after typing
  }
}

// Clear the existing content and start the typing effect
window.onload = () => {
  h2Element.textContent = ""; // Clear the existing text
  typeText();
};

// Add event listener to the "Learn More" button
document.getElementById("learn-more-button").addEventListener("click", function(event) {
  event.preventDefault(); // Prevent the default link behavior
  document.getElementById("learn-more-section").scrollIntoView({ behavior: "smooth" }); // Smooth scroll to the learn more section
});


document.addEventListener("DOMContentLoaded", () => {
    const userImage = document.querySelector(".user-info img");
    const userName = document.querySelector(".user-info span");

    if (userImage && userName) {
        const img = new Image();
        img.crossOrigin = "Anonymous"; // Ensure cross-origin requests are allowed
        img.src = userImage.src;

        img.onload = () => {
            const colorThief = new ColorThief();
            const dominantColor = colorThief.getColor(img);
            const rgbColor = `rgb(${dominantColor[0]}, ${dominantColor[1]}, ${dominantColor[2]})`;

            // Apply the dominant color to the user's name
            userName.style.color = rgbColor;
        };
    }
});

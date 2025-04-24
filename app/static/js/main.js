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
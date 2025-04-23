const h2Element = document.getElementById("typing-text");
const text = h2Element.textContent; // Use the content inside the <h2> as the text
const typingSpeed = 100; // Speed in milliseconds
let index = 0;

function typeText() {
  if (index < text.length) {
    h2Element.textContent += text.charAt(index);
    index++;
    setTimeout(typeText, typingSpeed);
  }
}

// Clear the existing content and start the typing effect
window.onload = () => {
  h2Element.textContent = ""; // Clear the existing text
  typeText();
};
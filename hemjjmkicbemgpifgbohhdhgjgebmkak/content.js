const style = document.createElement('style');
style.innerHTML = `
  body { 
    background-color: green !important; 
    background-image: none !important;
    background-repeat: no-repeat !important;
  }
`;
document.head.appendChild(style);
console.log("Site Styler: Applied green background.");

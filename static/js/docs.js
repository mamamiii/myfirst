// Initialize syntax highlighting
document.addEventListener('DOMContentLoaded', (event) => {
    Prism.highlightAll();
});

// Add copy functionality to code blocks
document.querySelectorAll('pre').forEach(block => {
    const button = document.createElement('button');
    button.className = 'copy-button';
    button.textContent = 'Copy';
    
    button.addEventListener('click', () => {
        const code = block.querySelector('code');
        navigator.clipboard.writeText(code.textContent).then(() => {
            button.textContent = 'Copied!';
            setTimeout(() => {
                button.textContent = 'Copy';
            }, 2000);
        });
    });
    
    block.appendChild(button);
});

// Add terminal-like typing effect to the title
const terminalTitle = document.querySelector('.terminal-title');
const text = terminalTitle.textContent;
terminalTitle.textContent = '';

let i = 0;
const typeWriter = () => {
    if (i < text.length) {
        terminalTitle.textContent += text.charAt(i);
        i++;
        setTimeout(typeWriter, 50);
    }
};

typeWriter();

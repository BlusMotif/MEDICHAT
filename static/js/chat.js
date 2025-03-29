// Doctor Chatbot - Main JavaScript File

// DOM Elements
const chatMessages = document.getElementById('chatMessages');
const messageForm = document.getElementById('messageForm');
const userInput = document.getElementById('userInput');
const typingIndicator = document.getElementById('typingIndicator');
const resetChatButton = document.getElementById('resetChat');
const toggleDarkModeButton = document.getElementById('toggleDarkMode');
const quickSymptomButtons = document.querySelectorAll('.quick-symptom');
const welcomeModal = new bootstrap.Modal(document.getElementById('welcomeModal'));

// Show welcome modal on first visit
if (!localStorage.getItem('doctorBotWelcomeSeen')) {
    setTimeout(() => {
        welcomeModal.show();
        localStorage.setItem('doctorBotWelcomeSeen', 'true');
    }, 1000);
}

// Toggle dark/light mode
toggleDarkModeButton.addEventListener('click', () => {
    const html = document.documentElement;
    if (html.getAttribute('data-bs-theme') === 'dark') {
        html.setAttribute('data-bs-theme', 'light');
        localStorage.setItem('doctorBotTheme', 'light');
    } else {
        html.setAttribute('data-bs-theme', 'dark');
        localStorage.setItem('doctorBotTheme', 'dark');
    }
});

// Apply saved theme preference
const savedTheme = localStorage.getItem('doctorBotTheme');
if (savedTheme) {
    document.documentElement.setAttribute('data-bs-theme', savedTheme);
}

// Initialize the chat with a greeting
document.addEventListener('DOMContentLoaded', () => {
    // Add quick symptom button functionality
    quickSymptomButtons.forEach(button => {
        button.addEventListener('click', () => {
            userInput.value = button.textContent;
            messageForm.dispatchEvent(new Event('submit'));
        });
    });
    
    // Request initial greeting from the bot
    fetchBotResponse('');
});

// Reset chat
resetChatButton.addEventListener('click', () => {
    // Clear chat messages
    chatMessages.innerHTML = `
        <div class="d-flex justify-content-center my-4">
            <div class="alert alert-info text-center">
                <i class="fas fa-info-circle me-2"></i>
                This chatbot provides general information only and is not a substitute for professional medical advice.
            </div>
        </div>
    `;
    
    // Fetch new greeting
    fetchBotResponse('restart');
});

// Form submission handler
messageForm.addEventListener('submit', (e) => {
    e.preventDefault();
    
    const message = userInput.value.trim();
    if (!message) return;
    
    // Add user message to chat
    addMessage(message, 'user');
    
    // Clear input
    userInput.value = '';
    
    // Show typing indicator
    showTypingIndicator();
    
    // Fetch bot response
    fetchBotResponse(message);
});

/**
 * Add a message to the chat
 * @param {string} message - The message text
 * @param {string} sender - 'user' or 'bot'
 */
function addMessage(message, sender) {
    const messageElement = document.createElement('div');
    messageElement.classList.add('message', `${sender}-message`);
    
    // Format the message - convert newlines to <br> and handle bullet points
    let formattedMessage = message;
    
    // For bot messages, add proper formatting
    if (sender === 'bot') {
        // Replace bullet points with proper HTML
        formattedMessage = formattedMessage.replace(/•\s(.*?)(?=(\n•|\n\n|$))/g, '<li>$1</li>');
        if (formattedMessage.includes('<li>')) {
            formattedMessage = formattedMessage.replace(/(<li>.*?<\/li>)/gs, '<ul>$1</ul>');
        }
        
        // Replace newlines with breaks
        formattedMessage = formattedMessage.replace(/\n\n/g, '</p><p>');
        formattedMessage = `<p>${formattedMessage}</p>`;
        
        // Highlight important warnings
        formattedMessage = formattedMessage.replace(/IMPORTANT:/g, '<strong>IMPORTANT:</strong>');
    } else {
        // Simple newline replacement for user messages
        formattedMessage = formattedMessage.replace(/\n/g, '<br>');
    }
    
    messageElement.innerHTML = formattedMessage;
    
    // Add timestamp
    const timestamp = document.createElement('span');
    timestamp.classList.add('timestamp');
    timestamp.textContent = getFormattedTime();
    messageElement.appendChild(timestamp);
    
    chatMessages.appendChild(messageElement);
    
    // Scroll to bottom
    scrollToBottom();
}

/**
 * Show typing indicator
 */
function showTypingIndicator() {
    typingIndicator.classList.remove('d-none');
}

/**
 * Hide typing indicator
 */
function hideTypingIndicator() {
    typingIndicator.classList.add('d-none');
}

/**
 * Get formatted time string
 * @returns {string} Time in format HH:MM
 */
function getFormattedTime() {
    const now = new Date();
    return now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

/**
 * Scroll chat to the bottom
 */
function scrollToBottom() {
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

/**
 * Fetch response from the bot
 * @param {string} message - The user's message
 */
function fetchBotResponse(message) {
    // If it's an empty message, it's the initial greeting
    const endpoint = '/get_response';
    
    fetch(endpoint, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: message }),
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => {
        // Add delay to simulate typing
        const typingDelay = Math.min(1000, data.response.length * 10);
        
        setTimeout(() => {
            hideTypingIndicator();
            addMessage(data.response, 'bot');
        }, typingDelay);
    })
    .catch(error => {
        console.error('Error:', error);
        hideTypingIndicator();
        addMessage('Sorry, I encountered an error while processing your request. Please try again.', 'bot');
    });
}

// Make user input autofocus when user starts typing
document.addEventListener('keydown', (e) => {
    // Ignore if we're in an input already
    if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
        return;
    }
    
    // Ignore special keys
    if (e.ctrlKey || e.altKey || e.metaKey) {
        return;
    }
    
    // Focus the input if user types a letter or number
    if (e.key.length === 1) {
        userInput.focus();
    }
});

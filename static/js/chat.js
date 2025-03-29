document.addEventListener('DOMContentLoaded', function() {
    // Elements
    const chatMessages = document.getElementById('chatMessages');
    const messageForm = document.getElementById('messageForm');
    const userInput = document.getElementById('userInput');
    const typingIndicator = document.getElementById('typingIndicator');
    const quickSymptomButtons = document.querySelectorAll('.quick-symptom');
    const resetChatButton = document.getElementById('resetChat');
    const toggleDarkModeButton = document.getElementById('toggleDarkMode');
    
    // Apply animation order to symptom buttons for staggered appearance
    quickSymptomButtons.forEach((button, index) => {
        button.style.setProperty('--animation-order', index);
    });
    
    // Show welcome modal on first visit
    if (!localStorage.getItem('welcomed')) {
        const welcomeModal = new bootstrap.Modal(document.getElementById('welcomeModal'));
        setTimeout(() => welcomeModal.show(), 800); // Delay modal to let page animations finish
        localStorage.setItem('welcomed', 'true');
    }
    
    // Send initial empty message to get greeting
    sendMessage('');
    
    // Form submission
    messageForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const message = userInput.value.trim();
        if (message) {
            addMessage(message, 'user');
            sendMessage(message);
            userInput.value = '';
        }
    });
    
    // Quick symptom buttons
    quickSymptomButtons.forEach(button => {
        button.addEventListener('click', function() {
            const symptom = this.textContent;
            addMessage('I have ' + symptom.toLowerCase(), 'user');
            sendMessage('I have ' + symptom.toLowerCase());
        });
    });
    
    // Reset chat
    resetChatButton.addEventListener('click', function() {
        // Clear the chat UI
        while (chatMessages.firstChild) {
            chatMessages.removeChild(chatMessages.firstChild);
        }
        
        // Add disclaimer
        chatMessages.innerHTML = `
            <div class="d-flex justify-content-center my-4">
                <div class="alert alert-info text-center">
                    <i class="fas fa-info-circle me-2"></i>
                    This chatbot provides general information only and is not a substitute for professional medical advice.
                </div>
            </div>
        `;
        
        // Send empty message to get greeting
        sendMessage('restart');
    });
    
    // Toggle dark mode
    toggleDarkModeButton.addEventListener('click', function() {
        const html = document.documentElement;
        if (html.getAttribute('data-bs-theme') === 'dark') {
            html.setAttribute('data-bs-theme', 'light');
            localStorage.setItem('theme', 'light');
        } else {
            html.setAttribute('data-bs-theme', 'dark');
            localStorage.setItem('theme', 'dark');
        }
    });
    
    // Add a message to the chat with enhanced animations
    function addMessage(message, sender) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}-message mb-3`;
        
        const time = getFormattedTime();
        
        if (sender === 'user') {
            messageDiv.innerHTML = `
                <div class="d-flex align-items-start justify-content-end">
                    <div class="message-content bg-primary text-white p-3 rounded-3">
                        <div class="message-text">${message}</div>
                        <div class="message-time text-end text-white-75 small">${time}</div>
                    </div>
                    <div class="message-avatar ms-2">
                        <div class="avatar bg-light rounded-circle d-flex align-items-center justify-content-center">
                            <i class="fas fa-user"></i>
                        </div>
                    </div>
                </div>
            `;
        } else {
            // For bot messages, we can add a slight delay to make it feel more natural
            // and to let the typing indicator show for a more realistic time
            messageDiv.style.animationDelay = `${Math.min(message.length / 50, 1)}s`;
            
            messageDiv.innerHTML = `
                <div class="d-flex align-items-start">
                    <div class="message-avatar me-2">
                        <div class="avatar bg-primary rounded-circle d-flex align-items-center justify-content-center">
                            <i class="fas fa-user-md text-white"></i>
                        </div>
                    </div>
                    <div class="message-content bg-secondary bg-opacity-10 text-dark p-3 rounded-3">
                        <div class="message-text">${formatBotMessage(message)}</div>
                        <div class="message-time text-dark opacity-75 small">${time}</div>
                    </div>
                </div>
            `;
            
            // If the message is long, add a progressive reveal animation
            if (message.length > 100) {
                const textElement = messageDiv.querySelector('.message-text');
                textElement.style.opacity = '0';
                
                // Progressive text reveal
                setTimeout(() => {
                    textElement.style.transition = 'opacity 0.5s ease-out';
                    textElement.style.opacity = '1';
                }, 100);
            }
        }
        
        chatMessages.appendChild(messageDiv);
        scrollToBottom();
    }
    
    // Format bot message with markdown-like syntax
    function formatBotMessage(message) {
        // Replace newlines with <br>
        let formatted = message.replace(/\n/g, '<br>');
        
        // Format bullet points
        formatted = formatted.replace(/•\s(.*?)(?=<br>|$)/g, '<li>$1</li>');
        
        // Wrap consecutive list items in ul
        if (formatted.includes('<li>')) {
            formatted = formatted.replace(/(<li>.*?<\/li>)+/g, '<ul class="ps-3 mb-0">$&</ul>');
        }
        
        // Bold text
        formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong class="text-primary">$1</strong>');
        
        // Italics
        formatted = formatted.replace(/\*(.*?)\*/g, '<em>$1</em>');
        
        // Format disease names in all caps (common in the African diseases text file)
        formatted = formatted.replace(/\b([A-Z]{2,}(?:\s[A-Z]{2,})*)\b/g, '<span class="text-danger fw-bold">$1</span>');
        
        // Enhance symptom lists
        formatted = formatted.replace(/(Symptoms|Diagnosis|Treatment):/g, '<strong class="text-primary">$1:</strong>');
        
        return formatted;
    }
    
    // Show typing indicator
    function showTypingIndicator() {
        typingIndicator.classList.remove('d-none');
        scrollToBottom();
    }
    
    // Hide typing indicator
    function hideTypingIndicator() {
        typingIndicator.classList.add('d-none');
    }
    
    // Get formatted time string
    function getFormattedTime() {
        const now = new Date();
        return now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }
    
    // Scroll chat to the bottom with smooth animation
    function scrollToBottom() {
        chatMessages.scrollTo({
            top: chatMessages.scrollHeight,
            behavior: 'smooth'
        });
    }
    
    // Send message to backend
    function sendMessage(message) {
        // Show typing indicator
        showTypingIndicator();
        
        // Disable input while waiting for response
        userInput.disabled = true;
        
        // Send request to backend
        fetch('/get_response', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ message: message })
        })
        .then(response => response.json())
        .then(data => {
            // Hide typing indicator
            hideTypingIndicator();
            
            // Enable input
            userInput.disabled = false;
            userInput.focus();
            
            // Add response to chat
            if (data.response) {
                addMessage(data.response, 'bot');
            } else if (data.error) {
                addMessage('Sorry, I encountered an error: ' + data.error, 'bot');
            }
        })
        .catch(error => {
            // Hide typing indicator
            hideTypingIndicator();
            
            // Enable input
            userInput.disabled = false;
            
            // Add error message
            addMessage('Sorry, I encountered a technical issue. Please try again.', 'bot');
            console.error('Error fetching response:', error);
        });
    }
    
    // Initialize theme from localStorage
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme) {
        document.documentElement.setAttribute('data-bs-theme', savedTheme);
    }
});
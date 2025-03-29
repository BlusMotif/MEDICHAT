document.addEventListener('DOMContentLoaded', function() {
    // Elements
    const chatMessages = document.getElementById('chatMessages');
    const messageForm = document.getElementById('messageForm');
    const userInput = document.getElementById('userInput');
    const typingIndicator = document.getElementById('typingIndicator');
    const quickSymptomButtons = document.querySelectorAll('.quick-symptom');
    const resetChatButton = document.getElementById('resetChat');
    const toggleDarkModeButton = document.getElementById('toggleDarkMode');
    
    // Show welcome modal on first visit
    if (!localStorage.getItem('welcomed')) {
        const welcomeModal = new bootstrap.Modal(document.getElementById('welcomeModal'));
        welcomeModal.show();
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
    
    // Add a message to the chat
    function addMessage(message, sender) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}-message mb-3`;
        
        const time = getFormattedTime();
        
        if (sender === 'user') {
            messageDiv.innerHTML = `
                <div class="d-flex align-items-start justify-content-end">
                    <div class="message-content bg-primary text-white p-3 rounded-3">
                        <div class="message-text">${message}</div>
                        <div class="message-time text-end opacity-75 small">${time}</div>
                    </div>
                    <div class="message-avatar ms-2">
                        <div class="avatar bg-light rounded-circle d-flex align-items-center justify-content-center">
                            <i class="fas fa-user"></i>
                        </div>
                    </div>
                </div>
            `;
        } else {
            messageDiv.innerHTML = `
                <div class="d-flex align-items-start">
                    <div class="message-avatar me-2">
                        <div class="avatar bg-primary rounded-circle d-flex align-items-center justify-content-center">
                            <i class="fas fa-user-md text-white"></i>
                        </div>
                    </div>
                    <div class="message-content bg-light p-3 rounded-3">
                        <div class="message-text">${formatBotMessage(message)}</div>
                        <div class="message-time opacity-75 small">${time}</div>
                    </div>
                </div>
            `;
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
            formatted = formatted.replace(/(<li>.*?<\/li>)+/g, '<ul>$&</ul>');
        }
        
        // Bold text
        formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        
        // Italics
        formatted = formatted.replace(/\*(.*?)\*/g, '<em>$1</em>');
        
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
    
    // Scroll chat to the bottom
    function scrollToBottom() {
        chatMessages.scrollTop = chatMessages.scrollHeight;
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
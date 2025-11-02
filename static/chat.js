document.addEventListener("DOMContentLoaded", function(){

    const chatBox = document.getElementById("chat-box");
    const messageInput = document.getElementById("message");
    const sendBtn = document.getElementById("send-btn");

    let chatHistory = [];

    function renderChat(){
        chatBox.innerHTML = "";
        chatHistory.forEach(msg => {
            const div = document.createElement("div");
            div.className = msg.sender === "user" ? "user-msg" : "bot-msg";
            div.textContent = msg.text;
            chatBox.appendChild(div);
        });
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    function sendMessage(){
        const user_input = messageInput.value.trim();
        if(!user_input) return;

        chatHistory.push({ sender: "user", text: user_input });
        renderChat();
        messageInput.value = "";

        fetch("/ask", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: user_input })
        })
        .then(res => res.json())
        .then(data => {
            chatHistory.push({ sender: "bot", text: data.reply });
            renderChat();
        })
        .catch(() => {
            chatHistory.push({ sender: "bot", text: "Error: Could not get response." });
            renderChat();
        });
    }

    // Send button
    sendBtn.addEventListener("click", sendMessage);

    // Enter key
    messageInput.addEventListener("keypress", function(e){
        if(e.key === "Enter") sendMessage();
    });

        // Common question buttons functionality
    document.querySelectorAll(".option-btn").forEach(btn => {
    btn.addEventListener("click", () => {
        const input = document.getElementById("user-input");
        input.value = btn.textContent;
        sendMessage();
    });
    });
});

/* ─── AI Chatbot Modülü ─── */
const ChatModule = {
    sessionId: null,
    isOpen: false,

    init() {
        this.sessionId = 'chat-' + Date.now().toString(36);
        document.getElementById('chat-fab').addEventListener('click', () => this.toggle());
        document.getElementById('chat-close').addEventListener('click', () => this.toggle());
        document.getElementById('chat-send').addEventListener('click', () => this.send());
        document.getElementById('chat-input').addEventListener('keypress', e => { if (e.key === 'Enter') this.send(); });
        document.querySelectorAll('.chat-suggestion').forEach(btn => {
            btn.addEventListener('click', () => {
                document.getElementById('chat-input').value = btn.dataset.text;
                this.send();
            });
        });
    },

    toggle() {
        this.isOpen = !this.isOpen;
        document.getElementById('chat-panel').style.display = this.isOpen ? 'flex' : 'none';
        if (this.isOpen) document.getElementById('chat-input').focus();
    },

    addMessage(content, role) {
        const container = document.getElementById('chat-messages');
        // İlk mesajda hoş geldin ekranını kaldır
        const welcome = container.querySelector('.chat-welcome');
        if (welcome) welcome.style.display = 'none';

        const msg = document.createElement('div');
        msg.className = `chat-msg ${role}`;
        // Markdown-like bold işleme
        msg.innerHTML = content.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>').replace(/\n/g, '<br>');
        container.appendChild(msg);
        container.scrollTop = container.scrollHeight;
    },

    showTyping() {
        const container = document.getElementById('chat-messages');
        const typing = document.createElement('div');
        typing.className = 'chat-typing';
        typing.id = 'chat-typing';
        typing.innerHTML = '<span>●</span><span>●</span><span>●</span>';
        container.appendChild(typing);
        container.scrollTop = container.scrollHeight;
    },

    hideTyping() {
        const t = document.getElementById('chat-typing');
        if (t) t.remove();
    },

    async send() {
        const input = document.getElementById('chat-input');
        const message = input.value.trim();
        if (!message) return;

        input.value = '';
        this.addMessage(message, 'user');
        this.showTyping();

        try {
            const res = await api.post('/chat/smart', { message, session_id: this.sessionId });
            this.hideTyping();
            this.addMessage(res.response, 'assistant');
        } catch (e) {
            this.hideTyping();
            this.addMessage('Üzgünüm, bir hata oluştu. Lütfen tekrar deneyin.', 'assistant');
        }
    }
};

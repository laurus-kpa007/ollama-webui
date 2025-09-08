class OllamaChat {
    constructor() {
        this.currentModel = null;
        this.currentSdModel = null;
        this.currentMode = 'chat';
        this.uploadedImageUrl = null;
        this.messages = [];
        this.sdConnected = false;
        this.init();
    }

    init() {
        this.loadModels();
        this.loadSdModels();
        this.bindEvents();
        this.checkConnection();
        this.updateUI();
    }

    async loadModels() {
        try {
            const response = await fetch('/api/models');
            const data = await response.json();
            
            const modelSelect = document.getElementById('modelSelect');
            modelSelect.innerHTML = '<option value="">모델을 선택하세요...</option>';
            
            if (data.data && data.data.length > 0) {
                data.data.forEach(model => {
                    const option = document.createElement('option');
                    option.value = model.id;
                    option.textContent = model.id;
                    modelSelect.appendChild(option);
                });
                document.getElementById('connectionStatus').textContent = '연결됨';
                document.getElementById('connectionStatus').className = 'badge bg-success ms-2';
            } else {
                document.getElementById('connectionStatus').textContent = '모델 없음';
                document.getElementById('connectionStatus').className = 'badge bg-warning ms-2';
            }
        } catch (error) {
            console.error('모델 로드 실패:', error);
            document.getElementById('connectionStatus').textContent = '연결 실패';
            document.getElementById('connectionStatus').className = 'badge bg-danger ms-2';
        }
    }

    async checkConnection() {
        try {
            const response = await fetch('/api/models');
            if (response.ok) {
                document.getElementById('connectionStatus').textContent = '연결됨';
                document.getElementById('connectionStatus').className = 'badge bg-success ms-2';
            } else {
                throw new Error('연결 실패');
            }
        } catch (error) {
            document.getElementById('connectionStatus').textContent = '연결 실패';
            document.getElementById('connectionStatus').className = 'badge bg-danger ms-2';
        }
    }

    async loadSdModels() {
        try {
            const response = await fetch('/api/sd_models');
            const data = await response.json();
            
            const sdModelSelect = document.getElementById('sdModelSelect');
            sdModelSelect.innerHTML = '<option value="">모델을 선택하세요...</option>';
            
            if (data.connected && data.data && data.data.length > 0) {
                this.sdConnected = true;
                data.data.forEach(model => {
                    const option = document.createElement('option');
                    option.value = model.model_name;
                    option.textContent = model.model_name;
                    sdModelSelect.appendChild(option);
                });
            } else {
                this.sdConnected = false;
            }
        } catch (error) {
            console.error('SD 모델 로드 실패:', error);
            this.sdConnected = false;
        }
    }

    updateUI() {
        const mode = this.currentMode;
        
        // 섹션 표시/숨김
        document.getElementById('chatModelSection').style.display = mode === 'chat' ? 'block' : 'none';
        document.getElementById('sdModelSection').style.display = mode !== 'chat' ? 'block' : 'none';
        document.getElementById('chatSettings').style.display = mode === 'chat' ? 'block' : 'none';
        document.getElementById('imageGenSettings').style.display = mode === 'image_gen' ? 'block' : 'none';
        document.getElementById('img2imgSettings').style.display = mode === 'img2img' ? 'block' : 'none';
        
        // 입력 플레이스홀더 변경
        const messageInput = document.getElementById('messageInput');
        const sendIcon = document.getElementById('sendIcon');
        const sendText = document.getElementById('sendText');
        
        switch(mode) {
            case 'chat':
                messageInput.placeholder = '메시지를 입력하세요...';
                sendIcon.className = 'fas fa-paper-plane';
                sendText.textContent = '';
                break;
            case 'image_gen':
                messageInput.placeholder = '생성할 이미지를 설명하세요... (예: beautiful landscape with mountains)';
                sendIcon.className = 'fas fa-image';
                sendText.textContent = ' 생성';
                break;
            case 'img2img':
                messageInput.placeholder = '변환할 내용을 설명하세요... (먼저 이미지를 업로드하세요)';
                sendIcon.className = 'fas fa-magic';
                sendText.textContent = ' 변환';
                break;
        }
        
        // 전송 버튼 활성화 조건
        this.updateSendButton();
    }

    updateSendButton() {
        const sendBtn = document.getElementById('sendBtn');
        const messageInput = document.getElementById('messageInput');
        const hasMessage = messageInput.value.trim().length > 0;
        
        let shouldEnable = false;
        
        switch(this.currentMode) {
            case 'chat':
                shouldEnable = hasMessage && this.currentModel;
                break;
            case 'image_gen':
                shouldEnable = hasMessage && this.sdConnected;
                break;
            case 'img2img':
                shouldEnable = hasMessage && this.uploadedImageUrl && this.sdConnected;
                break;
        }
        
        sendBtn.disabled = !shouldEnable;
    }

    bindEvents() {
        // 모드 선택
        document.getElementById('modeSelect').addEventListener('change', (e) => {
            this.currentMode = e.target.value;
            this.updateUI();
        });
        // 채팅 모델 선택
        document.getElementById('modelSelect').addEventListener('change', (e) => {
            this.currentModel = e.target.value;
            document.getElementById('currentModel').textContent = 
                e.target.value || '모델을 선택하세요';
            this.updateSendButton();
        });

        // SD 모델 선택
        document.getElementById('sdModelSelect').addEventListener('change', (e) => {
            this.currentSdModel = e.target.value;
            this.updateSendButton();
        });

        // 슬라이더들
        document.getElementById('temperature').addEventListener('input', (e) => {
            document.getElementById('tempValue').textContent = e.target.value;
        });

        document.getElementById('samplingSteps').addEventListener('input', (e) => {
            document.getElementById('stepsValue').textContent = e.target.value;
        });

        document.getElementById('cfgScale').addEventListener('input', (e) => {
            document.getElementById('cfgValue').textContent = e.target.value;
        });

        document.getElementById('denoisingStrength').addEventListener('input', (e) => {
            document.getElementById('denoisingValue').textContent = e.target.value;
        });

        // 메시지 전송
        document.getElementById('sendBtn').addEventListener('click', () => {
            this.sendMessage();
        });

        // 입력 필드 업데이트
        document.getElementById('messageInput').addEventListener('input', () => {
            this.updateSendButton();
        });

        // 엔터키로 전송
        document.getElementById('messageInput').addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        // 새 채팅
        document.getElementById('newChatBtn').addEventListener('click', () => {
            this.newChat();
        });

        // 파일 업로드
        document.getElementById('fileInput').addEventListener('change', (e) => {
            this.handleFileUpload(e.target.files[0]);
        });

        // 이미지 제거
        document.getElementById('removeImage').addEventListener('click', () => {
            this.removeImage();
        });
    }

    async handleFileUpload(file) {
        if (!file) return;

        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch('/api/upload', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (result.success) {
                this.uploadedImageUrl = result.url;
                document.getElementById('previewImage').src = result.url;
                document.getElementById('uploadedImage').style.display = 'block';
            } else {
                alert('파일 업로드 실패: ' + result.error);
            }
        } catch (error) {
            console.error('업로드 오류:', error);
            alert('파일 업로드 중 오류가 발생했습니다.');
        }
    }

    removeImage() {
        this.uploadedImageUrl = null;
        document.getElementById('uploadedImage').style.display = 'none';
        document.getElementById('fileInput').value = '';
    }

    async sendMessage() {
        const messageInput = document.getElementById('messageInput');
        const message = messageInput.value.trim();

        if (!message) return;

        switch(this.currentMode) {
            case 'chat':
                if (!this.currentModel) return;
                await this.handleChatMessage(message);
                break;
            case 'image_gen':
                if (!this.sdConnected) return;
                await this.handleImageGeneration(message);
                break;
            case 'img2img':
                if (!this.sdConnected || !this.uploadedImageUrl) return;
                await this.handleImg2Img(message);
                break;
        }

        messageInput.value = '';
        this.updateSendButton();
    }

    async handleChatMessage(message) {
        // 사용자 메시지 추가
        this.addMessage('user', message, this.uploadedImageUrl);

        // 메시지 배열 업데이트
        this.messages.push({
            role: 'user',
            content: message
        });

        // 이미지 분석인지 확인
        if (this.uploadedImageUrl) {
            await this.analyzeImage(message);
            this.removeImage();
            return;
        }

        // 일반 채팅
        const streamMode = document.getElementById('streamMode').checked;
        if (streamMode) {
            await this.sendStreamMessage();
        } else {
            await this.sendNormalMessage();
        }
    }

    async handleImageGeneration(prompt) {
        // 프롬프트 메시지 추가
        this.addMessage('user', `🎨 이미지 생성: ${prompt}`);
        
        // 진행률 표시
        this.showProgress('이미지 생성 중...');

        const [width, height] = document.getElementById('imageSize').value.split('x').map(Number);
        
        try {
            const response = await fetch('/api/generate_image', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    prompt: prompt,
                    negative_prompt: document.getElementById('negativePrompt').value,
                    width: width,
                    height: height,
                    steps: parseInt(document.getElementById('samplingSteps').value),
                    cfg_scale: parseFloat(document.getElementById('cfgScale').value),
                    model: this.currentSdModel
                })
            });

            const result = await response.json();
            
            if (result.success) {
                this.addMessage('assistant', '이미지가 생성되었습니다!', result.image_url);
            } else {
                this.addMessage('assistant', `이미지 생성 실패: ${result.error}`);
            }
        } catch (error) {
            console.error('이미지 생성 오류:', error);
            this.addMessage('assistant', '이미지 생성 중 오류가 발생했습니다.');
        } finally {
            this.hideProgress();
        }
    }

    async handleImg2Img(prompt) {
        // 프롬프트 메시지 추가
        this.addMessage('user', `🖼️ 이미지 변환: ${prompt}`, this.uploadedImageUrl);
        
        // 진행률 표시
        this.showProgress('이미지 변환 중...');

        try {
            const response = await fetch('/api/img2img', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    init_image_url: this.uploadedImageUrl,
                    prompt: prompt,
                    negative_prompt: document.getElementById('negativePrompt').value,
                    denoising_strength: parseFloat(document.getElementById('denoisingStrength').value),
                    steps: parseInt(document.getElementById('samplingSteps').value),
                    cfg_scale: parseFloat(document.getElementById('cfgScale').value)
                })
            });

            const result = await response.json();
            
            if (result.success) {
                this.addMessage('assistant', '이미지가 변환되었습니다!', result.image_url);
            } else {
                this.addMessage('assistant', `이미지 변환 실패: ${result.error}`);
            }
        } catch (error) {
            console.error('이미지 변환 오류:', error);
            this.addMessage('assistant', '이미지 변환 중 오류가 발생했습니다.');
        } finally {
            this.hideProgress();
            this.removeImage();
        }
    }

    showProgress(text) {
        document.getElementById('progressContainer').style.display = 'block';
        document.getElementById('progressText').textContent = text;
        document.getElementById('progressBar').style.width = '0%';
        
        // 가짜 진행률 애니메이션
        let progress = 0;
        const interval = setInterval(() => {
            progress += Math.random() * 15;
            if (progress > 90) progress = 90;
            document.getElementById('progressBar').style.width = progress + '%';
        }, 500);
        
        this.progressInterval = interval;
    }

    hideProgress() {
        if (this.progressInterval) {
            clearInterval(this.progressInterval);
            this.progressInterval = null;
        }
        document.getElementById('progressBar').style.width = '100%';
        setTimeout(() => {
            document.getElementById('progressContainer').style.display = 'none';
        }, 500);
    }

    async analyzeImage(prompt) {
        const loadingMessage = this.addMessage('assistant', '', null, true);

        try {
            const response = await fetch('/api/analyze_image', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    image_url: this.uploadedImageUrl,
                    prompt: prompt,
                    model: this.currentModel
                })
            });

            const result = await response.json();
            
            if (result.choices && result.choices[0]) {
                const content = result.choices[0].message.content;
                this.updateMessage(loadingMessage, content);
                this.messages.push({
                    role: 'assistant',
                    content: content
                });
            } else {
                this.updateMessage(loadingMessage, '이미지 분석에 실패했습니다.');
            }
        } catch (error) {
            console.error('이미지 분석 오류:', error);
            this.updateMessage(loadingMessage, '이미지 분석 중 오류가 발생했습니다.');
        }
    }

    async sendNormalMessage() {
        const loadingMessage = this.addMessage('assistant', '', null, true);

        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    messages: this.messages,
                    model: this.currentModel,
                    stream: false,
                    temperature: parseFloat(document.getElementById('temperature').value),
                    max_tokens: parseInt(document.getElementById('maxTokens').value) || null
                })
            });

            const result = await response.json();
            
            if (result.choices && result.choices[0]) {
                const content = result.choices[0].message.content;
                this.updateMessage(loadingMessage, content);
                this.messages.push({
                    role: 'assistant',
                    content: content
                });
            } else {
                this.updateMessage(loadingMessage, '응답을 받을 수 없습니다.');
            }
        } catch (error) {
            console.error('메시지 전송 오류:', error);
            this.updateMessage(loadingMessage, '메시지 전송 중 오류가 발생했습니다.');
        }
    }

    async sendStreamMessage() {
        const messageElement = this.addMessage('assistant', '');
        const contentElement = messageElement.querySelector('.message-text');
        let fullContent = '';

        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    messages: this.messages,
                    model: this.currentModel,
                    stream: true,
                    temperature: parseFloat(document.getElementById('temperature').value),
                    max_tokens: parseInt(document.getElementById('maxTokens').value) || null
                })
            });

            const reader = response.body.getReader();
            const decoder = new TextDecoder();

            while (true) {
                const { done, value } = await reader.read();
                
                if (done) break;

                const chunk = decoder.decode(value);
                const lines = chunk.split('\n');

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        const data = line.slice(6);
                        if (data.trim() === '[DONE]') continue;

                        try {
                            const parsed = JSON.parse(data);
                            if (parsed.choices && parsed.choices[0].delta.content) {
                                fullContent += parsed.choices[0].delta.content;
                                contentElement.textContent = fullContent;
                                this.scrollToBottom();
                            }
                        } catch (e) {
                            // JSON 파싱 에러 무시
                        }
                    }
                }
            }

            this.messages.push({
                role: 'assistant',
                content: fullContent
            });

        } catch (error) {
            console.error('스트림 메시지 오류:', error);
            contentElement.textContent = '메시지 전송 중 오류가 발생했습니다.';
        }
    }

    addMessage(role, content, imageUrl = null, isLoading = false) {
        const chatMessages = document.getElementById('chatMessages');
        
        // welcome message 제거
        const welcomeMsg = chatMessages.querySelector('.welcome-message');
        if (welcomeMsg) {
            welcomeMsg.remove();
        }

        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}`;

        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.innerHTML = role === 'user' ? '<i class="fas fa-user"></i>' : '<i class="fas fa-robot"></i>';

        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';

        if (imageUrl) {
            const img = document.createElement('img');
            img.src = imageUrl;
            img.className = 'img-thumbnail mb-2';
            img.style.maxWidth = '200px';
            img.style.maxHeight = '200px';
            contentDiv.appendChild(img);
        }

        const textDiv = document.createElement('div');
        textDiv.className = 'message-text';
        
        if (isLoading) {
            textDiv.innerHTML = '<div class="typing-indicator"><div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div></div>';
        } else {
            textDiv.textContent = content;
        }

        contentDiv.appendChild(textDiv);

        if (role === 'user') {
            messageDiv.appendChild(contentDiv);
            messageDiv.appendChild(avatar);
        } else {
            messageDiv.appendChild(avatar);
            messageDiv.appendChild(contentDiv);
        }

        chatMessages.appendChild(messageDiv);
        this.scrollToBottom();

        return messageDiv;
    }

    updateMessage(messageElement, content) {
        const textElement = messageElement.querySelector('.message-text');
        textElement.textContent = content;
        this.scrollToBottom();
    }

    newChat() {
        this.messages = [];
        const chatMessages = document.getElementById('chatMessages');
        chatMessages.innerHTML = `
            <div class="welcome-message text-center text-muted">
                <i class="fas fa-robot fa-3x mb-3"></i>
                <h4>새 채팅을 시작하세요!</h4>
                <p>선택된 모델: ${this.currentModel || '모델을 선택하세요'}</p>
            </div>
        `;
        this.removeImage();
    }

    scrollToBottom() {
        const chatMessages = document.getElementById('chatMessages');
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
}

// 앱 초기화
document.addEventListener('DOMContentLoaded', () => {
    window.ollamaChat = new OllamaChat();
});
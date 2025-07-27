// app/static/js/main.js - Fixed working version

// Global variables
let isRecording = false;
let recognition;
let currentLanguage = 'hi';
let speechSynthesis = window.speechSynthesis;
let audioContext;
let analyser;
let microphone;
let dataArray;
let canvasContext;
let recordingStartTime;
let timerInterval;
let uploadedFiles = [];
let currentAnalysis = null;

// WebSocket connection
let ws = null;
let isConnected = false;
let reconnectAttempts = 0;
let maxReconnectAttempts = 5;
// Global speech queue and state
let isSpeaking = false;
let speechQueue = [];

// Modified WebSocket message handler
ws.onmessage = async function(event) {
    try {
        const data = JSON.parse(event.data);
        console.log('📨 Received WS message:', data);

        if (data.type === 'thinking') {
            addTypingIndicator(data.content);
        }
        else if (data.type === 'response') {
            removeTypingIndicator();
            addMessage(data.content, 'assistant');

            // Add to speech queue and process
            speechQueue.push({
                text: data.content,
                lang: currentLanguage
            });
            processSpeechQueue();
        }
        else if (data.type === 'analysis_result') {
            removeTypingIndicator();
            const analysisMessage = formatAnalysisMessage(data);
            addMessage(analysisMessage, 'assistant');

            speechQueue.push({
                text: analysisMessage,
                lang: currentLanguage
            });
            processSpeechQueue();
        }
    } catch (error) {
        console.error('WS message error:', error);
    }
};

// Process speech queue sequentially
async function processSpeechQueue() {
    if (isSpeaking || speechQueue.length === 0) return;

    isSpeaking = true;
    const { text, lang } = speechQueue.shift();

    try {
        await speakText(text, lang);
    } catch (error) {
        console.error('Speech error:', error);
    } finally {
        isSpeaking = false;
        setTimeout(processSpeechQueue, 300);
    }
}

// Enhanced speakText function with proper voice selection
async function speakText(text, lang = 'hi') {
    return new Promise((resolve) => {
        if (!window.speechSynthesis) {
            console.warn('Speech synthesis not available');
            return resolve();
        }

        // Cancel any ongoing speech
        speechSynthesis.cancel();

        const utterance = new SpeechSynthesisUtterance(text);
        utterance.lang = `${lang}-IN`;
        utterance.rate = 0.85;
        utterance.pitch = 1;
        utterance.volume = 1;

        // Voice selection logic
        const voices = speechSynthesis.getVoices();
        const langVoices = voices.filter(v => v.lang.startsWith(lang));

        if (langVoices.length > 0) {
            // Prefer female voice if available
            const femaleVoice = langVoices.find(v => v.name.includes('Female'));
            utterance.voice = femaleVoice || langVoices[0];
            console.log(`Using voice: ${utterance.voice.name}`);
        } else {
            console.warn('No matching voices found, using default');
        }

        utterance.onend = resolve;
        utterance.onerror = (err) => {
            console.error('Speech error:', err);
            resolve();
        };

        speechSynthesis.speak(utterance);
    });
}
function formatAnalysisMessage(data) {
    return `📊 विश्लेषण परिणाम:

निदान: ${data.diagnosis} (${data.confidence}% सटीक)
लक्षण: ${data.symptoms}
उपचार: ${data.treatment}

बचाव के उपाय:
${data.preventive_measures.map(m => `• ${m}`).join('\n')}`;
}

function addMessage(text, sender) {
    const messagesContainer = document.getElementById('chatMessages');
    if (!messagesContainer) return;

    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}`;

    if (sender === 'assistant') {
        messageDiv.innerHTML = `
            <div class="message-content">${text.replace(/\n/g, '<br>')}</div>
            <button class="speaker-btn" onclick="speakMessage(this)">
                <svg viewBox="0 0 24 24">
                    <path d="M3 9v6h4l5 5V4L7 9H3zm13.5 3c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02zM14 3.23v2.06c2.89.86 5 3.54 5 6.71s-2.11 5.85-5 6.71v2.06c4.01-.91 7-4.49 7-8.77s-2.99-7.86-7-8.77z"/>
                </svg>
            </button>
        `;
    } else {
        messageDiv.innerHTML = `<div class="message-content">${text.replace(/\n/g, '<br>')}</div>`;
    }

    messagesContainer.appendChild(messageDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}
// Initialize speech synthesis when voices are loaded
function initializeVoices() {
    return new Promise((resolve) => {
        const voices = speechSynthesis.getVoices();
        if (voices.length > 0) {
            resolve(voices);
        } else {
            speechSynthesis.onvoiceschanged = () => {
                resolve(speechSynthesis.getVoices());
                speechSynthesis.onvoiceschanged = null;
            };
        }
    });
}


// Enhanced localization
const translations = {
    hi: {
        listening: 'सुन रहे हैं...',
        click_to_speak: 'बोलने के लिए स्टार्ट दबाएं',
        recording: 'रिकॉर्डिंग हो रही है... स्टॉप दबाएं जब हो जाए',
        connection_error: 'कनेक्शन की समस्या। कृपया दोबारा कोशिश करें।',
        upload_success: 'फाइलें सफलतापूर्वक अपलोड हुईं',
        location_detected: 'आपका स्थान मिल गया',
        processing: 'विश्लेषण कर रहे हैं...',
        welcome: 'प्रोजेक्ट किसान में आपका स्वागत है! आपका AI कृषि सहायक तैयार है।',
        speak_clearly: 'कृपया स्पष्ट बोलें',
        mic_permission: 'माइक्रोफोन की अनुमति दें',
        no_speech: 'कोई आवाज़ नहीं सुनाई दी',
        voice_error: 'आवाज़ पहचानने में समस्या',
        recording_stopped: 'रिकॉर्डिंग बंद की गई',
        connected: 'AI सहायक कनेक्ट हो गया',
        disconnected: 'AI सहायक डिसकनेक्ट हो गया'
    }
};

function getLocalizedText(key) {
    return translations[currentLanguage]?.[key] || translations['hi'][key];
}

// ============================================================================
// WebSocket Functions - MAIN CONNECTION
// ============================================================================

function connectWebSocket() {
    try {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/chat`;

        console.log('🔌 Connecting to WebSocket:', wsUrl);

        ws = new WebSocket(wsUrl);

        ws.onopen = function() {
            console.log('✅ WebSocket connected');
            isConnected = true;
            reconnectAttempts = 0;
            updateConnectionStatus(true);
            showNotification(getLocalizedText('connected'), 'success');

            // Send welcome message
            addMessage('नमस्ते! मैं आपका AI कृषि सहायक हूं। मैं आपकी फसल, मौसम, मंडी भाव और सरकारी योजनाओं के बारे में मदद कर सकता हूं। 🌾', 'assistant');
        };

        ws.onmessage = function(event) {
            try {
                const data = JSON.parse(event.data);
                console.log('📨 Received:', data);

                if (data.type === 'thinking') {
                    addTypingIndicator(data.content);
                } else if (data.type === 'response') {
                    removeTypingIndicator();
                    addMessage(data.content, 'assistant');

                    // Auto-speak the response
                    speakText(data.content, currentLanguage);

                    // Show which agent was used
                    if (data.agent_used) {
                        console.log('🤖 Agent used:', data.agent_used);
                    }
                }
            } catch (error) {
                console.error('❌ Error parsing message:', error);
            }
        };

        ws.onerror = function(error) {
            console.error('❌ WebSocket error:', error);
            showNotification('कनेक्शन में समस्या', 'error');
        };

        ws.onclose = function(event) {
            console.log('🔌 WebSocket closed:', event.code);
            isConnected = false;
            updateConnectionStatus(false);

            // Try to reconnect
            if (reconnectAttempts < maxReconnectAttempts) {
                reconnectAttempts++;
                console.log(`🔄 Reconnecting... Attempt ${reconnectAttempts}`);
                setTimeout(connectWebSocket, 2000 * reconnectAttempts);
            } else {
                showNotification('कनेक्शन टूट गया - पेज रिफ्रेश करें', 'error');
            }
        };

    } catch (error) {
        console.error('❌ WebSocket connection failed:', error);
        updateConnectionStatus(false);
    }
}

function sendWebSocketMessage(content, type = 'text', additionalData = {}) {
    if (ws && isConnected) {
        const message = {
            type: type,
            content: content,
            session_id: `session_${Date.now()}`,
            ...additionalData
        };

        console.log('📤 Sending:', message);
        ws.send(JSON.stringify(message));
        return true;
    } else {
        console.log('❌ WebSocket not connected, using fallback');
        return false;
    }
}

function updateConnectionStatus(connected) {
    const statusElement = document.getElementById('connectionStatus');
    if (statusElement) {
        statusElement.textContent = connected ? '🟢 Connected' : '🔴 Disconnected';
        statusElement.className = connected ? 'status-connected' : 'status-disconnected';
    }
}

// ============================================================================
// UI Helper Functions
// ============================================================================

function showNotification(message, type = 'success') {
    const notification = document.getElementById('notification');
    if (!notification) return;

    notification.textContent = message;
    notification.className = `notification ${type} show`;

    setTimeout(() => {
        notification.classList.remove('show');
    }, 4000);
}

function addMessage(text, sender) {
    const messagesContainer = document.getElementById('chatMessages');
    if (!messagesContainer) return;

    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}`;

    if (sender === 'assistant') {
        messageDiv.innerHTML = `
            ${text}
            <button class="speaker-btn" onclick="speakMessage(this)">
                <svg viewBox="0 0 24 24"><path d="M3 9v6h4l5 5V4L7 9H3zm13.5 3c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02zM14 3.23v2.06c2.89.86 5 3.54 5 6.71s-2.11 5.85-5 6.71v2.06c4.01-.91 7-4.49 7-8.77s-2.99-7.86-7-8.77z"/></svg>
            </button>
        `;
    } else {
        messageDiv.textContent = text;
    }

    messagesContainer.appendChild(messageDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function addTypingIndicator(message = 'टाइप कर रहे हैं...') {
    const messagesContainer = document.getElementById('chatMessages');
    if (!messagesContainer) return;

    // Remove existing typing indicator
    removeTypingIndicator();

    const typingDiv = document.createElement('div');
    typingDiv.className = 'message assistant typing-indicator';
    typingDiv.id = 'typingIndicator';
    typingDiv.innerHTML = `
        <div class="loading"></div>
        <span style="margin-left: 0.5rem;">${message}</span>
    `;
    messagesContainer.appendChild(typingDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function removeTypingIndicator() {
    const typingIndicator = document.getElementById('typingIndicator');
    if (typingIndicator) {
        typingIndicator.remove();
    }
}

// ============================================================================
// Voice Recognition Functions - FIXED
// ============================================================================

function initializeVoiceRecognition() {
    if ('webkitSpeechRecognition' in window) {
        recognition = new webkitSpeechRecognition();
    } else if ('SpeechRecognition' in window) {
        recognition = new SpeechRecognition();
    } else {
        showNotification(getLocalizedText('voice_error'), 'error');
        return false;
    }

    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.maxAlternatives = 1;
    recognition.lang = currentLanguage + '-IN';

    let finalTranscript = '';
    let silenceTimer;

    recognition.onstart = function() {
        isRecording = true;
        finalTranscript = '';
        updateVoiceButtons();
        const recordingIndicator = document.getElementById('recordingIndicator');
        if (recordingIndicator) recordingIndicator.classList.add('active');
        const voiceStatus = document.getElementById('voiceStatus');
        if (voiceStatus) voiceStatus.textContent = getLocalizedText('recording');
        console.log('🎤 Voice recording started');
    };

    recognition.onresult = function(event) {
        let interimTranscript = '';

        for (let i = event.resultIndex; i < event.results.length; i++) {
            const transcript = event.results[i][0].transcript;
            if (event.results[i].isFinal) {
                finalTranscript += transcript;
                clearTimeout(silenceTimer);

                silenceTimer = setTimeout(() => {
                    if (finalTranscript.trim()) {
                        stopRecording();
                        processVoiceInput(finalTranscript.trim());
                    }
                }, 1000);
            } else {
                interimTranscript += transcript;
            }
        }

        const voiceStatus = document.getElementById('voiceStatus');
        if (interimTranscript && voiceStatus) {
            voiceStatus.textContent = 'सुन रहे हैं: ' + interimTranscript;
        }
    };

    recognition.onerror = function(event) {
        console.error('Voice recognition error:', event.error);
        if (event.error === 'no-speech') {
            showNotification('कुछ नहीं सुनाई दिया, कृपया दोबारा कोशिश करें', 'warning');
        } else if (event.error === 'audio-capture') {
            showNotification('माइक्रोफोन की समस्या', 'error');
        } else {
            showNotification(getLocalizedText('voice_error'), 'error');
        }
        stopRecording();
    };

    recognition.onend = function() {
        if (isRecording && finalTranscript.trim()) {
            processVoiceInput(finalTranscript.trim());
        }
        stopRecording();
    };

    return true;
}

function processVoiceInput(text) {
    console.log('🎤 Voice input:', text);
    addMessage(text, 'user');

    // Send through WebSocket or fallback to REST
    if (!sendWebSocketMessage(text, 'voice')) {
        // Fallback to REST API
        fetch('/voice-query', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: `query=${encodeURIComponent(text)}`
        })
        .then(response => response.json())
        .then(data => {
            addMessage(data.response, 'assistant');
            speakText(data.response, currentLanguage);
        })
        .catch(error => {
            console.error('Voice query error:', error);
            addMessage('मुझे खेद है, मैं अभी आपकी मदद करने में असमर्थ हूं।', 'assistant');
        });
    }
}

function startRecording() {
    console.log('🎤 Starting recording...');

    if (!recognition) {
        if (!initializeVoiceRecognition()) return;
    }

    try {
        // Setup audio visualization
        setupVoiceVisualizer();

        navigator.mediaDevices.getUserMedia({ audio: true, video: false })
            .then(stream => {
                if (audioContext && analyser) {
                    microphone = audioContext.createMediaStreamSource(stream);
                    microphone.connect(analyser);
                }

                recordingStartTime = new Date().getTime();
                timerInterval = setInterval(updateTimer, 1000);

                const voiceVisualizer = document.getElementById('voiceVisualizer');
                if (voiceVisualizer) voiceVisualizer.classList.add('active');
                drawVisualizer();

                recognition.lang = currentLanguage + '-IN';
                recognition.start();
            })
            .catch(err => {
                console.error('Microphone access error:', err);
                showNotification(getLocalizedText('mic_permission'), 'error');
            });
    } catch (error) {
        console.error('Failed to start recognition:', error);
        showNotification(getLocalizedText('mic_permission'), 'error');
    }
}

function stopRecording() {
    console.log('🎤 Stopping recording...');

    if (recognition && isRecording) {
        recognition.stop();
    }

    if (microphone) {
        microphone.disconnect();
    }

    clearInterval(timerInterval);
    const voiceVisualizer = document.getElementById('voiceVisualizer');
    if (voiceVisualizer) voiceVisualizer.classList.remove('active');

    isRecording = false;
    updateVoiceButtons();
    const recordingIndicator = document.getElementById('recordingIndicator');
    if (recordingIndicator) recordingIndicator.classList.remove('active');
    const voiceStatus = document.getElementById('voiceStatus');
    if (voiceStatus) voiceStatus.textContent = getLocalizedText('click_to_speak');
    showNotification(getLocalizedText('recording_stopped'), 'success');
}

// ============================================================================
// Chat Functions - FIXED
// ============================================================================

function sendMessage() {
    const input = document.getElementById('chatInput');
    if (!input) return;

    const message = input.value.trim();

    if (message) {
        console.log('💬 Sending text message:', message);
        addMessage(message, 'user');
        input.value = '';

        // Send through WebSocket or fallback
        if (!sendWebSocketMessage(message, 'text')) {
            // Fallback to REST API
            addTypingIndicator();

            fetch('/voice-query', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: `query=${encodeURIComponent(message)}`
            })
            .then(response => response.json())
            .then(data => {
                removeTypingIndicator();
                addMessage(data.response, 'assistant');
                speakText(data.response, currentLanguage);
            })
            .catch(error => {
                removeTypingIndicator();
                console.error('Message send error:', error);
                addMessage('मुझे खेद है, मैं अभी आपकी मदद करने में असमर्थ हूं।', 'assistant');
            });
        }
    }
}

// ============================================================================
// File Upload Functions - FIXED
// ============================================================================

function handleFileUpload(event) {
    const files = Array.from(event.target.files);
    console.log('📁 Files selected:', files.length);

    files.forEach(file => {
        if (file.type.startsWith('image/') || file.type.startsWith('video/')) {
            uploadedFiles.push(file);
            addFilePreview(file);
        }
    });

    if (files.length > 0) {
        const uploadPreviewGrid = document.getElementById('uploadPreviewGrid');
        if (uploadPreviewGrid) uploadPreviewGrid.style.display = 'grid';
        showNotification(`${files.length} फाइल(ें) अपलोड की गईं`, 'success');

        // Analyze uploaded files
        setTimeout(() => {
            analyzeUploadedFiles();
        }, 1500);
    }
}

function analyzeUploadedFiles() {
    if (uploadedFiles.length === 0) return;

    console.log('🔍 Analyzing files...');

    // Try WebSocket first, then fallback to REST
    if (isConnected && uploadedFiles.length > 0) {
        const file = uploadedFiles[0]; // Process first file
        const reader = new FileReader();

        reader.onload = function(e) {
            const imageData = e.target.result;

            addMessage('📸 फसल की तस्वीर का विश्लेषण कर रहे हैं...', 'user');

            sendWebSocketMessage(
                'फसल की छवि का विश्लेषण करें',
                'image',
                { image_data: imageData }
            );
        };

        reader.readAsDataURL(file);
    } else {
        // Fallback to REST API
        const formData = new FormData();
        uploadedFiles.forEach(file => {
            formData.append('files', file);
        });

        fetch('/upload-image', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                displayAnalysisResults(data.analyses);
            } else {
                showNotification('विश्लेषण में समस्या', 'error');
            }
        })
        .catch(error => {
            console.error('Upload error:', error);
            showNotification('अपलोड में समस्या', 'error');
        });
    }
}

function displayAnalysisResults(analyses) {
    const analysisResults = document.getElementById('analysisResults');
    const analysisContent = document.getElementById('analysisContent');
    const downloadButton = document.getElementById('downloadPrescription');

    if (!analysisResults || !analysisContent) return;

    let content = '';
    analyses.forEach((analysis, index) => {
        currentAnalysis = analysis;
        content += `
            <div class="analysis-item">
                <h4>📸 फाइल ${index + 1} का विश्लेषण:</h4>
                <p><strong>🔍 निदान:</strong> ${analysis.disease_name}</p>
                <p><strong>📊 सटीकता:</strong> ${analysis.confidence}%</p>
                <p><strong>📝 विवरण:</strong> ${analysis.description}</p>
                <p><strong>💊 उपचार:</strong> ${analysis.treatment}</p>
                ${analysis.preventive_measures ? `
                    <div class="preventive-measures">
                        <strong>🛡️ बचाव के उपाय:</strong>
                        <ul>
                            ${analysis.preventive_measures.map(measure => `<li>${measure}</li>`).join('')}
                        </ul>
                    </div>
                ` : ''}
            </div>
        `;
    });

    analysisContent.innerHTML = content;
    analysisResults.style.display = 'block';
    if (downloadButton) downloadButton.style.display = 'block';

    // Add to chat
    const analysisMessage = `📸 ${uploadedFiles.length} फाइल(ों) का विश्लेषण पूरा:\n\n${analyses[0].disease_name} की पहचान की गई (${analyses[0].confidence}% सटीकता)\n\nउपचार: ${analyses[0].treatment}`;
    addMessage(analysisMessage, 'assistant');
    speakText(`आपकी फसल में ${analyses[0].disease_name} है। ${analyses[0].treatment}`, currentLanguage);
}

// ============================================================================
// Quick Actions - FIXED
// ============================================================================

function quickQuery(topic) {
    const queries = {
        weather: "आज का मौसम कैसा है? सिंचाई के लिए सलाह दें।",
        fertilizer: "मेरी फसल के लिए कौन सी खाद अच्छी होगी?",
        irrigation: "सिंचाई कब और कितना पानी देना चाहिए?",
        schemes: "किसानों के लिए कौन सी सरकारी योजनाएं हैं?"
    };

    const query = queries[topic] || "मुझे खेती के बारे में जानकारी चाहिए।";

    console.log('⚡ Quick query:', topic);
    addMessage(query, 'user');

    // Send through WebSocket or fallback
    if (!sendWebSocketMessage(query, 'text')) {
        // Fallback
        fetch('/voice-query', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: `query=${encodeURIComponent(query)}`
        })
        .then(response => response.json())
        .then(data => {
            addMessage(data.response, 'assistant');
            speakText(data.response, currentLanguage);
        })
        .catch(error => {
            console.error('Quick query error:', error);
            addMessage('मुझे खेद है, मैं अभी आपकी मदद करने में असमर्थ हूं।', 'assistant');
        });
    }
}

// ============================================================================
// Voice Visualization Functions
// ============================================================================

function setupVoiceVisualizer() {
    const canvas = document.getElementById('visualizerCanvas');
    if (!canvas) return;

    try {
        audioContext = new (window.AudioContext || window.webkitAudioContext)();
        analyser = audioContext.createAnalyser();
        analyser.fftSize = 256;

        canvasContext = canvas.getContext('2d');
        canvas.width = canvas.offsetWidth;
        canvas.height = canvas.offsetHeight;

        dataArray = new Uint8Array(analyser.frequencyBinCount);
    } catch (error) {
        console.error('Audio context setup error:', error);
    }
}

function drawVisualizer() {
    if (!isRecording || !analyser) return;

    requestAnimationFrame(drawVisualizer);

    analyser.getByteFrequencyData(dataArray);

    const canvas = document.getElementById('visualizerCanvas');
    if (!canvas || !canvasContext) return;

    canvasContext.clearRect(0, 0, canvas.width, canvas.height);

    const barWidth = (canvas.width / analyser.frequencyBinCount) * 2.5;
    let x = 0;

    for (let i = 0; i < analyser.frequencyBinCount; i++) {
        const barHeight = (dataArray[i] / 255) * canvas.height;

        const hue = i * 360 / analyser.frequencyBinCount;
        canvasContext.fillStyle = `hsla(${hue}, 80%, 50%, 0.8)`;
        canvasContext.fillRect(x, canvas.height - barHeight, barWidth, barHeight);

        x += barWidth + 1;
    }
}

function updateTimer() {
    const now = new Date().getTime();
    const elapsed = Math.floor((now - recordingStartTime) / 1000);
    const minutes = Math.floor(elapsed / 60).toString().padStart(2, '0');
    const seconds = (elapsed % 60).toString().padStart(2, '0');
    const recordingTimer = document.getElementById('recordingTimer');
    if (recordingTimer) {
        recordingTimer.textContent = `${minutes}:${seconds}`;
    }
}

function updateVoiceButtons() {
    const startButton = document.getElementById('startButton');
    const stopButton = document.getElementById('stopButton');

    if (startButton && stopButton) {
        if (isRecording) {
            startButton.disabled = true;
            startButton.style.opacity = '0.5';
            stopButton.disabled = false;
            stopButton.style.opacity = '1';
        } else {
            startButton.disabled = false;
            startButton.style.opacity = '1';
            stopButton.disabled = true;
            stopButton.style.opacity = '0.5';
        }
    }
}

// ============================================================================
// Text-to-Speech Functions
// ============================================================================

function speakText(text, lang = 'hi') {
    if (speechSynthesis) {
        speechSynthesis.cancel();

        const utterance = new SpeechSynthesisUtterance(text);
        utterance.lang = lang + '-IN';
        utterance.rate = 0.8;
        utterance.pitch = 1;
        utterance.volume = 1;

        const voices = speechSynthesis.getVoices();
        const selectedVoice = voices.find(voice =>
            voice.lang.includes(lang) || voice.lang.includes('hi')
        );
        if (selectedVoice) {
            utterance.voice = selectedVoice;
        }

        speechSynthesis.speak(utterance);
    }
}

function speakMessage(button) {
    const message = button.parentElement;
    const text = message.textContent.replace('🔊', '').trim();
    speakText(text, currentLanguage);
}

// ============================================================================
// File Helper Functions
// ============================================================================

function addFilePreview(file) {
    const previewGrid = document.getElementById('uploadPreviewGrid');
    if (!previewGrid) return;

    const previewDiv = document.createElement('div');
    previewDiv.className = 'upload-preview';

    const reader = new FileReader();
    reader.onload = function(e) {
        if (file.type.startsWith('image/')) {
            previewDiv.innerHTML = `
                <img src="${e.target.result}" alt="Preview">
                <button class="remove-btn" onclick="removeFile('${file.name}')">×</button>
            `;
        } else if (file.type.startsWith('video/')) {
            previewDiv.innerHTML = `
                <video src="${e.target.result}" controls></video>
                <button class="remove-btn" onclick="removeFile('${file.name}')">×</button>
            `;
        }
    };
    reader.readAsDataURL(file);

    previewGrid.appendChild(previewDiv);
}

function removeFile(filename) {
    uploadedFiles = uploadedFiles.filter(file => file.name !== filename);

    const previews = document.querySelectorAll('.upload-preview');
    previews.forEach(preview => {
        const button = preview.querySelector('.remove-btn');
        if (button && button.getAttribute('onclick').includes(filename)) {
            preview.remove();
        }
    });

    const uploadPreviewGrid = document.getElementById('uploadPreviewGrid');
    if (uploadedFiles.length === 0 && uploadPreviewGrid) {
        uploadPreviewGrid.style.display = 'none';
    }
}

// ============================================================================
// PDF Download Function
// ============================================================================

function downloadPrescription() {
    if (!currentAnalysis) {
        showNotification('कोई विश्लेषण उपलब्ध नहीं', 'error');
        return;
    }

    fetch('/generate-prescription', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(currentAnalysis)
    })
    .then(response => {
        if (response.ok) {
            return response.blob();
        }
        throw new Error('Prescription generation failed');
    })
    .then(blob => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        a.download = `prescription_${new Date().getTime()}.pdf`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        showNotification('प्रिस्क्रिप्शन डाउनलोड हो गया', 'success');
    })
    .catch(error => {
        console.error('Download error:', error);
        showNotification('डाउनलोड में समस्या', 'error');
    });
}

// ============================================================================
// Drag and Drop Setup
// ============================================================================

function setupDragDrop() {
    const uploadArea = document.getElementById('uploadArea');
    if (!uploadArea) return;

    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('dragover');
    });

    uploadArea.addEventListener('dragleave', () => {
        uploadArea.classList.remove('dragover');
    });

    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('dragover');

        const files = e.dataTransfer.files;
        if (files.length > 0) {
            const fileInput = document.getElementById('fileInput');
            if (fileInput) {
                fileInput.files = files;
                handleFileUpload({ target: { files: files } });
            }
        }
    });
}

// ============================================================================
// Initialization - MAIN ENTRY POINT
// ============================================================================

function initializeApp() {
    console.log('🚀 Initializing FarmBot App...');

    console.log('🚀 Initializing app...');

    // Initialize voices first
    await initializeVoices();
    console.log('🔊 Voices loaded');

    // Then connect WebSocket
    connectWebSocket();

    // Initialize voice recognition
    initializeVoiceRecognition();

    // Setup drag and drop
    setupDragDrop();

    // Update UI
    updateVoiceButtons();

    // Show welcome message
    setTimeout(() => {
        showNotification(getLocalizedText('welcome'), 'success');
    }, 1000);

    console.log('✅ FarmBot App initialized');
}

// ============================================================================
// Event Listeners
// ============================================================================

document.addEventListener('DOMContentLoaded', function() {
    initializeApp();

    // Language selector
    const languageSelect = document.getElementById('languageSelect');
    if (languageSelect) {
        languageSelect.addEventListener('change', (e) => {
            currentLanguage = e.target.value;
            if (recognition) {
                recognition.lang = currentLanguage + '-IN';
            }
            showNotification(`भाषा बदली गई: ${e.target.options[e.target.selectedIndex].text}`, 'success');
        });
    }

    // Chat input
    const chatInput = document.getElementById('chatInput');
    if (chatInput) {
        chatInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });
    }

    // Initialize speech synthesis voices
    speechSynthesis.onvoiceschanged = () => {
        console.log('🔊 Speech voices loaded');
    };

    // Keyboard shortcuts
    document.addEventListener('keydown', (e) => {
        if (e.ctrlKey && e.key === ' ') {
            e.preventDefault();
            if (isRecording) {
                stopRecording();
            } else {
                startRecording();
            }
        }
    });
});

// Handle page visibility changes
document.addEventListener('visibilitychange', function() {
    if (!document.hidden && !isConnected) {
        console.log('🔄 Page visible, reconnecting...');
        connectWebSocket();
    }
});

// Handle window beforeunload
window.addEventListener('beforeunload', function() {
    if (ws) {
        ws.close();
    }
});

// Handle file upload from chat window
function handleChatFileUpload(event) {
    const files = Array.from(event.target.files);
    if (files.length === 0) return;

    // Add to main upload list
    files.forEach(file => {
        if (file.type.startsWith('image/') || file.type.startsWith('video/')) {
            uploadedFiles.push(file);
        }
    });

    // Show in chat
    addMessage(`📁 ${files.length} फाइल(ें) अपलोड की गईं`, 'user');

    // Analyze files
    setTimeout(() => {
        analyzeUploadedFiles();
    }, 500);

    // Clear the input
    event.target.value = '';
}

// Modify the analyzeUploadedFiles function to show results in chat
function analyzeUploadedFiles() {
    if (uploadedFiles.length === 0) return;

    console.log('🔍 Analyzing files...');
    addTypingIndicator('फाइलों का विश्लेषण कर रहे हैं...');

    // Try WebSocket first, then fallback to REST
    if (isConnected && uploadedFiles.length > 0) {
        const file = uploadedFiles[0]; // Process first file
        const reader = new FileReader();

        reader.onload = function(e) {
            const imageData = e.target.result;
            sendWebSocketMessage(
                'फसल की छवि का विश्लेषण करें',
                'image',
                { image_data: imageData }
            );
        };
        reader.readAsDataURL(file);
    } else {
        // Fallback to REST API
        const formData = new FormData();
        uploadedFiles.forEach(file => {
            formData.append('files', file);
        });

        fetch('/upload-image', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            removeTypingIndicator();
            if (data.status === 'success') {
                displayAnalysisResults(data.analyses);
            } else {
                addMessage('विश्लेषण में समस्या आई', 'assistant');
            }
        })
        .catch(error => {
            removeTypingIndicator();
            console.error('Upload error:', error);
            addMessage('अपलोड में समस्या आई', 'assistant');
        });
    }
}

// Update displayAnalysisResults to show in chat
function displayAnalysisResults(analyses) {
    const analysisResults = document.getElementById('analysisResults');
    const analysisContent = document.getElementById('analysisContent');
    const downloadButton = document.getElementById('downloadPrescription');

    if (!analysisResults || !analysisContent) return;

    let content = '';
    analyses.forEach((analysis, index) => {
        currentAnalysis = analysis;
        content += `
            <div class="analysis-item">
                <h4>📸 फाइल ${index + 1} का विश्लेषण:</h4>
                <p><strong>🔍 निदान:</strong> ${analysis.disease_name}</p>
                <p><strong>📊 सटीकता:</strong> ${analysis.confidence}%</p>
                <p><strong>📝 विवरण:</strong> ${analysis.description}</p>
                <p><strong>💊 उपचार:</strong> ${analysis.treatment}</p>
                ${analysis.preventive_measures ? `
                    <div class="preventive-measures">
                        <strong>🛡️ बचाव के उपाय:</strong>
                        <ul>
                            ${analysis.preventive_measures.map(measure => `<li>${measure}</li>`).join('')}
                        </ul>
                    </div>
                ` : ''}
            </div>
        `;
    });

    analysisContent.innerHTML = content;
    analysisResults.style.display = 'block';
    if (downloadButton) downloadButton.style.display = 'block';

    // Add to chat
    const analysisMessage = `📸 ${uploadedFiles.length} फाइल(ों) का विश्लेषण पूरा:\n\n${analyses[0].disease_name} की पहचान की गई (${analyses[0].confidence}% सटीकता)\n\nउपचार: ${analyses[0].treatment}`;
    addMessage(analysisMessage, 'assistant');
    speakText(`आपकी फसल में ${analyses[0].disease_name} है। ${analyses[0].treatment}`, currentLanguage);

    // Show download button in chat
    const chatDownloadBtn = document.createElement('button');
    chatDownloadBtn.className = 'btn-primary';
    chatDownloadBtn.innerHTML = '📄 प्रिस्क्रिप्शन डाउनलोड करें';
    chatDownloadBtn.onclick = downloadPrescription;

    const messageDiv = document.createElement('div');
    messageDiv.className = 'message assistant';
    messageDiv.appendChild(chatDownloadBtn);

    const chatMessages = document.getElementById('chatMessages');
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}
// Initialize ticker animation
function initMandiTicker() {
    const ticker = document.getElementById('mandiTicker');
    if (!ticker) return;

    // Duplicate items for seamless looping
    const items = ticker.innerHTML;
    ticker.innerHTML = items + items;

    // Pause animation on hover
    ticker.addEventListener('mouseenter', () => {
        ticker.style.animationPlayState = 'paused';
    });

    ticker.addEventListener('mouseleave', () => {
        ticker.style.animationPlayState = 'running';
    });
}

// Enhanced message display function
function addMessage(text, sender, options = {}) {
    const messagesContainer = document.getElementById('chatMessages');
    if (!messagesContainer) return;

    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}`;

    if (sender === 'assistant') {
        let content = text;

        if (options.isAnalysis) {
            content = `
                <div class="analysis-response">
                    <div class="analysis-header">
                        <span class="diagnosis">${options.diagnosis || 'Diagnosis'}</span>
                        <span class="confidence">${options.confidence || '0'}% सटीकता</span>
                    </div>
                    <div class="analysis-content">
                        <p><strong>लक्षण:</strong> ${options.symptoms || 'N/A'}</p>
                        <p><strong>उपचार:</strong> ${options.treatment || 'N/A'}</p>
                        ${options.preventiveMeasures ? `
                            <div class="preventive-measures">
                                <strong>बचाव के उपाय:</strong>
                                <ul>
                                    ${options.preventiveMeasures.map(m => `<li>${m}</li>`).join('')}
                                </ul>
                            </div>
                        ` : ''}
                    </div>
                    <button class="download-prescription" onclick="generatePrescription(${JSON.stringify(options)})">
                        📄 प्रिस्क्रिप्शन डाउनलोड करें
                    </button>
                </div>
            `;
        }

        messageDiv.innerHTML = `
            ${content}
            <button class="speaker-btn" onclick="speakMessage(this)">
                <svg viewBox="0 0 24 24"><path d="M3 9v6h4l5 5V4L7 9H3zm13.5 3c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02zM14 3.23v2.06c2.89.86 5 3.54 5 6.71s-2.11 5.85-5 6.71v2.06c4.01-.91 7-4.49 7-8.77s-2.99-7.86-7-8.77z"/></svg>
            </button>
        `;
    } else {
        messageDiv.textContent = text;
    }

    messagesContainer.appendChild(messageDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

// Generate prescription PDF
function generatePrescription(analysisData) {
    addTypingIndicator('प्रिस्क्रिप्शन जनरेट कर रहे हैं...');

    const prescriptionData = {
        diagnosis: analysisData.diagnosis,
        confidence: analysisData.confidence,
        symptoms: analysisData.symptoms,
        treatment: analysisData.treatment,
        preventiveMeasures: analysisData.preventiveMeasures,
        timestamp: new Date().toLocaleString('hi-IN'),
        farmerInfo: {
            name: 'किसान का नाम',
            location: 'स्थान',
            contact: 'संपर्क नंबर'
        }
    };

    fetch('/generate-prescription', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(prescriptionData)
    })
    .then(response => {
        if (!response.ok) throw new Error('Failed to generate');
        return response.blob();
    })
    .then(blob => {
        removeTypingIndicator();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `kisan_prescription_${Date.now()}.pdf`;
        document.body.appendChild(a);
        a.click();
        URL.revokeObjectURL(url);
        a.remove();
        showNotification('प्रिस्क्रिप्शन डाउनलोड हो गया', 'success');
    })
    .catch(error => {
        removeTypingIndicator();
        console.error('Prescription error:', error);
        showNotification('प्रिस्क्रिप्शन जनरेट करने में समस्या', 'error');
    });
}

// Update displayAnalysisResults to use new format
function displayAnalysisResults(analyses) {
    const analysis = analyses[0];
    currentAnalysis = analysis;

    // Show in chat
    addMessage('फसल विश्लेषण परिणाम', 'assistant', {
        isAnalysis: true,
        diagnosis: analysis.disease_name,
        confidence: analysis.confidence,
        symptoms: analysis.description,
        treatment: analysis.treatment,
        preventiveMeasures: analysis.preventive_measures
    });

    // Speak the diagnosis
    speakText(`आपकी फसल में ${analysis.disease_name} है। उपचार: ${analysis.treatment}`, currentLanguage);

    // Also show in analysis section (optional)
    const analysisResults = document.getElementById('analysisResults');
    if (analysisResults) {
        analysisResults.style.display = 'block';
        document.getElementById('analysisContent').innerHTML = `
            <div class="analysis-item">
                <p><strong>निदान:</strong> ${analysis.disease_name}</p>
                <p><strong>सटीकता:</strong> ${analysis.confidence}%</p>
                <p><strong>लक्षण:</strong> ${analysis.description}</p>
                <p><strong>उपचार:</strong> ${analysis.treatment}</p>
                ${analysis.preventive_measures ? `
                    <div class="preventive-measures">
                        <strong>बचाव के उपाय:</strong>
                        <ul>
                            ${analysis.preventive_measures.map(measure => `<li>${measure}</li>`).join('')}
                        </ul>
                    </div>
                ` : ''}
            </div>
            <button class="btn-primary" onclick="generatePrescription(${JSON.stringify({
                diagnosis: analysis.disease_name,
                confidence: analysis.confidence,
                symptoms: analysis.description,
                treatment: analysis.treatment,
                preventiveMeasures: analysis.preventive_measures
            })})">
                📄 प्रिस्क्रिप्शन डाउनलोड करें
            </button>
        `;
    }
}

// Initialize everything when DOM loads
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
    initMandiTicker();
    // ... rest of your existing initialization code
});

// Global functions for HTML onclick handlers
window.startRecording = startRecording;
window.stopRecording = stopRecording;
window.speakMessage = speakMessage;
window.sendMessage = sendMessage;
window.quickQuery = quickQuery;
window.handleFileUpload = handleFileUpload;
window.removeFile = removeFile;
window.downloadPrescription = downloadPrescription;

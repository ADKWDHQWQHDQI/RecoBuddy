import React, { useState, useEffect, useRef, useCallback } from 'react';
import { createRoot } from 'react-dom/client';
import { auth } from './firebase';
import { signInWithEmailAndPassword, createUserWithEmailAndPassword, signOut } from 'firebase/auth';
import './App.css';

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [language, setLanguage] = useState('en');
  const [theme, setTheme] = useState('light');
  const [user, setUser] = useState(null);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLogin, setIsLogin] = useState(true);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const [isTranslating, setIsTranslating] = useState(false);
  const [showHistory, setShowHistory] = useState(false);
  const [chatHistory, setChatHistory] = useState([]);
  const [chatHistoryFetched, setChatHistoryFetched] = useState(false);
  const messagesEndRef = useRef(null);
  const recognitionRef = useRef(null);

  const scrollToBottom = () => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  };
  
  // Helper function to fetch chat history with retry logic, now wrapped in useCallback
  const attemptFetchChatHistory = useCallback(async (maxRetries) => {
    for (let attempt = 1; attempt <= maxRetries; attempt++) {
      try {
        const response = await fetch('http://127.0.0.1:5000/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ message: '', language, user_id: user ? user.uid : 'anonymous' }),
        });

        if (!response.ok) {
          throw new Error(`Server error: ${response.status}`);
        }

        const data = await response.json();
        console.log("🔹 Fetched Chat History:", data.chat_history);
        if (data.chat_history) {
          const historyMessages = data.chat_history.map((entry) => [
            { text: entry.user, sender: 'user', timestamp: entry.timestamp, topic: entry.topic },
            { text: entry.bot, sender: 'bot', timestamp: entry.timestamp, topic: entry.topic },
          ]).flat();
          if (messages.length === 0) {
            setMessages(historyMessages.filter((msg) => msg.text && msg.text.trim()));
          }
          setChatHistory(data.chat_history.filter((entry) => entry.user && entry.bot && entry.user.trim() && entry.bot.trim()));
        }
        if (data.response && messages.length === 0) {
          setMessages([{ text: data.response, sender: 'bot', timestamp: new Date().toISOString() }]);
        }
        setChatHistoryFetched(true);
        return true;
      } catch (error) {
        console.error(`Error fetching chat history (attempt ${attempt}):`, error);
        if (attempt === maxRetries) {
          setMessages((prev) => [...prev, { text: 'Failed to fetch chat history after multiple attempts.', sender: 'bot', timestamp: new Date().toISOString() }]);
          setChatHistoryFetched(true);
          return false;
        }
        await new Promise(resolve => setTimeout(resolve, Math.pow(2, attempt) * 1000));
      }
    }
    return false;
  }, [language, user, messages.length, setMessages, setChatHistory, setChatHistoryFetched]);

  // fetchChatHistory now uses the memoized attemptFetchChatHistory
  // eslint-disable-next-line react-hooks/exhaustive-deps
  const fetchChatHistory = useCallback(async () => {
    if (user) {
      const maxRetries = 3;
      console.log(`Fetching chat history for language: ${language}`);
      await attemptFetchChatHistory(maxRetries);
    }
  }, [user, language, attemptFetchChatHistory]);

  const sendMessage = useCallback(async (message = input) => {
    if (!message.trim() || isLoading) return;

    setIsLoading(true);
    setIsTyping(true);
    setIsTranslating(language !== 'en');
    const userMessage = { text: message, sender: 'user', timestamp: new Date().toISOString() };
    setMessages((prev) => [...prev, userMessage]);
    setInput('');

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 30000);

    try {
      const response = await fetch('http://127.0.0.1:5000/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message, language, user_id: user ? user.uid : 'anonymous' }),
        signal: controller.signal,
      });
      clearTimeout(timeoutId);

      if (!response.ok) throw new Error(`Server error: ${response.status}`);
      const data = await response.json();
      console.log("🔹 Full API Response:", data);
      if (!data.response) throw new Error("Empty response received");
      const botMessage = { text: data.response, sender: 'bot', timestamp: new Date().toISOString() };
      setMessages((prev) => [...prev, botMessage]);

      if (data.chat_history) {
        setChatHistory(data.chat_history.filter((entry) => entry.user && entry.bot && entry.user.trim() && entry.bot.trim()));
      }
      if ('speechSynthesis' in window) {
        const utterance = new SpeechSynthesisUtterance(data.response);
        utterance.lang = language;
        speechSynthesis.speak(utterance);
      }
    } catch (error) {
      if (error.name === 'AbortError') {
        setMessages((prev) => [...prev, { text: 'Error: Request timed out. Please try again later.', sender: 'bot', timestamp: new Date().toISOString() }]);
      } else {
        setMessages((prev) => [...prev, { text: `Error: ${error.message}`, sender: 'bot', timestamp: new Date().toISOString() }]);
      }
    } finally {
      setIsLoading(false);
      setIsTyping(false);
      setIsTranslating(false);
    }
  }, [input, isLoading, language, user]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    document.documentElement.className = theme;
  }, [theme]);

  useEffect(() => {
    if (user && !chatHistoryFetched) {
      fetchChatHistory();
    }
  }, [user, fetchChatHistory, chatHistoryFetched]);

  useEffect(() => {
    if ('webkitSpeechRecognition' in window) {
      recognitionRef.current = new window.webkitSpeechRecognition();
      recognitionRef.current.continuous = false;
      recognitionRef.current.lang = language;
      recognitionRef.current.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        setInput(transcript);
        sendMessage(transcript);
      };
      recognitionRef.current.onerror = () => {
        setIsSpeaking(false);
        setIsLoading(false);
        alert('Voice recognition failed. Please try again.');
      };
    }
  }, [language, sendMessage]);

  const handleLogin = async () => {
    try {
      if (isLogin) {
        await signInWithEmailAndPassword(auth, email, password);
      } else {
        await createUserWithEmailAndPassword(auth, email, password);
      }
      setUser(auth.currentUser);
      setEmail('');
      setPassword('');
    } catch (error) {
      alert('Error: ' + error.message);
    }
  };

  const handleLogout = async () => {
    await signOut(auth);
    setUser(null);
    setMessages([]);
    setChatHistory([]);
    setChatHistoryFetched(false);
  };

  const handleFeedback = async (recommendation, rating) => {
    try {
      await fetch('http://127.0.0.1:5000/feedback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: user ? user.uid : 'anonymous', recommendation, rating }),
      });
    } catch (error) {
      console.error('Error submitting feedback:', error);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !isLoading) sendMessage();
  };

  const startVoiceInput = () => {
    if (!recognitionRef.current || isSpeaking || isLoading) return;

    setIsSpeaking(true);
    setIsLoading(true);
    recognitionRef.current.start();

    const timeout = setTimeout(() => {
      recognitionRef.current.stop();
      setIsSpeaking(false);
      setIsLoading(false);
      alert('Voice input timed out. Please try again.');
    }, 10000);

    recognitionRef.current.onend = () => {
      clearTimeout(timeout);
      setIsSpeaking(false);
      setIsLoading(false);
    };
  };

  return (
    <div className={`app ${theme}`}>
      {!user ? (
        <div className="auth-container">
          <h1>RecoBuddy</h1>
          <div className="auth-form">
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="auth-input"
              placeholder="Email"
              aria-label="Email"
            />
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="auth-input"
              placeholder="Password"
              aria-label="Password"
            />
            <button
              onClick={handleLogin}
              className="auth-button"
              aria-label={isLogin ? 'Login' : 'Sign Up'}
            >
              {isLogin ? 'Login' : 'Sign Up'}
            </button>
            <button
              onClick={() => setIsLogin(!isLogin)}
              className="toggle-auth"
            >
              {isLogin ? 'Need an account? Sign Up' : 'Have an account? Login'}
            </button>
          </div>
        </div>
      ) : (
        <div className="chat-container">
          <div className="chat-header">
            <h1>RecoBuddy</h1>
            <button
              onClick={handleLogout}
              className="logout-button"
              aria-label="Logout"
            >
              Logout
            </button>
          </div>
          <div className="options">
            <div>
              <label>Language:</label>
              <select
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
                className="select"
                aria-label="Select language"
              >
                <option value="en">English</option>
                <option value="es">Spanish</option>
                <option value="fr">French</option>
                <option value="hi">Hindi</option>
              </select>
            </div>
            <div>
              <label>Theme:</label>
              <select
                value={theme}
                onChange={(e) => setTheme(e.target.value)}
                className="select"
                aria-label="Select theme"
              >
                <option value="light">Light</option>
                <option value="dark">Dark</option>
              </select>
            </div>
          </div>
          <div className="history-section">
            <button
              onClick={() => setShowHistory(!showHistory)}
              className="history-toggle"
            >
              {showHistory ? 'Hide History' : 'Show History'}
            </button>
            {showHistory && (
              <div className="history-list">
                {chatHistory.length > 0 ? (
                  chatHistory.map((entry, index) => (
                    <div key={index} className="history-item">
                      <div className="history-meta">
                        <span>{entry.timestamp}</span>
                        <span>Topic: {entry.topic}</span>
                      </div>
                      <div className="history-content">
                        <p><strong>You:</strong> {entry.user}</p>
                        <p><strong>Bot:</strong> {entry.bot}</p>
                      </div>
                    </div>
                  ))
                ) : (
                  <p>No chat history available.</p>
                )}
              </div>
            )}
          </div>
          <div className="chat-area">
            {messages.map((msg, index) => (
              <div
                key={index}
                className={`message ${msg.sender === 'user' ? 'user-message' : 'bot-message'} message-animate`}
              >
                {msg.text}
                {msg.sender === 'bot' && msg.text.includes('I recommend') && (
                  <div className="feedback-buttons">
                    <button
                      onClick={() => handleFeedback(msg.text, 'like')}
                      className="interactive-button"
                      aria-label="Like recommendation"
                    >
                      <span role="img" aria-label="thumbs up">👍</span>
                    </button>
                    <button
                      onClick={() => handleFeedback(msg.text, 'dislike')}
                      className="interactive-button"
                      aria-label="Dislike recommendation"
                    >
                      <span role="img" aria-label="thumbs down">👎</span>
                    </button>
                  </div>
                )}
              </div>
            ))}
            {isSpeaking && (
              <div className="listening">Listening...</div>
            )}
            {isLoading && (
              <div className="loading">Processing your request, please wait...</div>
            )}
            {isTranslating && (
              <div className="translating">
                <div className="spinner"></div>
                Translating...
              </div>
            )}
            {isTyping && (
              <div className="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
          <div className="input-area">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyPress}
              className="chat-input"
              placeholder="Ask for a recommendation! 😊"
              aria-label="Type a message"
              disabled={isLoading}
            />
            <button
              onClick={() => sendMessage()}
              className="send-button interactive-button"
              aria-label="Send message"
              disabled={isLoading}
            >
              {isLoading ? 'Processing...' : 'Send'}
            </button>
            <button
              onClick={startVoiceInput}
              className={`voice-button ${isSpeaking ? 'speaking' : ''} interactive-button`}
              aria-label="Voice input"
              disabled={isLoading}
            >
              <span role="img" aria-label="microphone">🎤</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

const root = createRoot(document.getElementById('root'));
root.render(<App />);
export default App;
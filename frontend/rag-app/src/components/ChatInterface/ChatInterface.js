// src/components/ChatInterface/ChatInterface.js
import React, { useState, useEffect, useRef, useCallback } from 'react';
import './ChatInterface.css';
import { fetchEventSource } from '@microsoft/fetch-event-source';

// Thay thế bằng URL backend FastAPI của bạn
const API_BASE_URL = 'http://localhost:8000'; // Hoặc cổng khác nếu bạn cấu hình

function ChatInterface() {
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [threadId, setThreadId] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const eventSourceRef = useRef(null);
  const messageListRef = useRef(null);

  // Tạo threadId duy nhất khi component mount
  useEffect(() => {
    setThreadId(`thread_${Date.now()}_${Math.random().toString(36).substring(7)}`);
  }, []);

  // Cuộn xuống dưới cùng khi có tin nhắn mới
  useEffect(() => {
    if (messageListRef.current) {
      messageListRef.current.scrollTop = messageListRef.current.scrollHeight;
    }
  }, [messages]);

  // Hàm đóng EventSource (nếu đang mở)
  const closeEventSource = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
      setIsLoading(false); // Đảm bảo tắt loading khi đóng
      console.log("EventSource closed.");
    }
  }, []);


  // Cleanup: Đóng EventSource khi component unmount
   useEffect(() => {
        return () => {
            closeEventSource();
        };
    }, [closeEventSource]);

  const handleInputChange = (event) => {
    setInputValue(event.target.value);
  };

  const handleSendMessage = () => {
    const ctrl = new AbortController(); // Để có thể hủy request'

    if (!inputValue.trim() || !threadId || isLoading) return;

    const userMessage = { sender: 'user', text: inputValue };
    setMessages(prevMessages => [...prevMessages, userMessage]);
    setInputValue('');
    setError(null); // Clear lỗi cũ
    setIsLoading(true);

    // --- Sử dụng Streaming Endpoint ---
    const assistantMessageTemplate = { sender: 'assistant', text: '', id: Date.now() }; // ID tạm để cập nhật
    setMessages(prevMessages => [...prevMessages, assistantMessageTemplate]);

    // Đóng kết nối cũ nếu có
    closeEventSource();

    const queryData = {
      query: inputValue,
      thread_id: threadId,
    };

    fetchEventSource(`${API_BASE_URL}/api/chat/stream`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Accept': 'text/event-stream', // Quan trọng
        },
        body: JSON.stringify(queryData),
        signal: ctrl.signal, // Để có thể cancel
        onopen(response) {
            if (response.ok && response.headers.get('content-type')?.includes('text/event-stream')) {
                console.log("SSE Connection established (fetchEventSource).");
                return; // All good
            } else {
                throw new Error(`Failed to connect. Status: ${response.status}, Content-Type: ${response.headers.get('content-type')}`);
            }
        },
        onmessage(event) {
            console.log("SSE Data received (fetchEventSource):", event.data);
            try {
                const parsedData = JSON.parse(event.data);
    
                if (parsedData.error) {
                    console.error('Backend stream error:', parsedData.error);
                    setError(`Lỗi từ server: ${parsedData.error}`);
                    setMessages(prev => prev.filter(msg => msg.id !== assistantMessageTemplate.id)); // Xóa message tạm
                    closeEventSource(); // Đóng kết nối khi có lỗi từ backend
                    return;
                }
    
                if (parsedData.context) {
                     // Cập nhật message cuối cùng (của assistant)
                     setMessages(prevMessages => {
                        const lastMessageIndex = prevMessages.length - 1;
                        if (lastMessageIndex >= 0 && prevMessages[lastMessageIndex].sender === 'assistant' && prevMessages[lastMessageIndex].id === assistantMessageTemplate.id) {
                            const updatedMessages = [...prevMessages];
                            updatedMessages[lastMessageIndex] = {
                                 ...updatedMessages[lastMessageIndex],
                                 text: updatedMessages[lastMessageIndex].text + parsedData.context
                             };
                             return updatedMessages;
                         }
                         // Trường hợp không tìm thấy message assistant cuối cùng (ít xảy ra)
                         return [...prevMessages, { sender: 'assistant', text: parsedData.context, id: assistantMessageTemplate.id }];
                     });
                }
            } catch (e) {
                 console.error("Failed to parse SSE data:", e);
                 setError("Lỗi xử lý dữ liệu từ server.");
                 // Không đóng EventSource ở đây trừ khi chắc chắn lỗi này là kết thúc stream
            }
        },
        onclose() {
            console.log("SSE Connection closed by server (fetchEventSource).");
            setIsLoading(false);
            // Không cần gọi ctrl.abort() ở đây vì kết nối đã đóng
        },
        onerror(err) {
            console.error("SSE Error (fetchEventSource):", err);
            setError("Lỗi kết nối stream. Vui lòng thử lại.");
            setIsLoading(false);
            ctrl.abort(); // Hủy request khi có lỗi nghiêm trọng
            throw err; // Ném lại lỗi để dừng stream
        }
    });

     // === Sử dụng Non-Streaming Endpoint (thay thế nếu không cần stream) ===
    /*
    const sendMessageNonStream = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/api/chat`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ query: inputValue, thread_id: threadId }),
        });

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        const assistantMessage = { sender: 'assistant', text: data.answer };
        setMessages(prevMessages => [...prevMessages, assistantMessage]);

      } catch (err) {
        console.error("Failed to fetch chat response:", err);
        setError(err.message || "Không thể kết nối đến server chat.");
      } finally {
        setIsLoading(false);
      }
    };
    // sendMessageNonStream(); // Gọi hàm này thay vì thiết lập EventSource
    */
  };

  const handleKeyDown = (event) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault(); // Ngăn xuống dòng trong textarea
      handleSendMessage();
    }
  };

  return (
    <div className="chat-container">
      <div className="message-list" ref={messageListRef}>
        {messages.map((msg, index) => (
          <div key={index} className={`message ${msg.sender}`}>
            <span className="message-sender">{msg.sender === 'user' ? 'You' : 'Assistant'}</span>
            {/* Xử lý xuống dòng nếu backend trả về \n */}
            {typeof msg.text === 'string' && msg.text.split('\n').map((line, i) => (
                 <React.Fragment key={i}>
                     {line}
                     <br />
                 </React.Fragment>
             ))}
          </div>
        ))}
         {/* Chỉ hiển thị loading khi đang chờ chunk đầu tiên hoặc lỗi */}
         {isLoading && messages[messages.length - 1]?.sender !== 'assistant' && (
            <div className="loading-indicator">Assistant is thinking...</div>
        )}
      </div>
      {error && <div className="error-message">{error}</div>}
      <div className="chat-input-area">
        <textarea
          className="chat-input"
          value={inputValue}
          onChange={handleInputChange}
          onKeyDown={handleKeyDown}
          placeholder="Type your message..."
          rows="1" // Tự động điều chỉnh chiều cao nếu cần
          disabled={isLoading}
        />
        <button
          className="send-button"
          onClick={handleSendMessage}
          disabled={isLoading || !inputValue.trim()}
        >
          Send
        </button>
      </div>
    </div>
  );
}

export default ChatInterface;
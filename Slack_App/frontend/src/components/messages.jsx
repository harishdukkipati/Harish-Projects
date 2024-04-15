import {useState, useEffect} from 'react';
import {useParams, useLocation, useNavigate} from 'react-router-dom';
import './messages.css';
// Replace with your actual API endpoint

/**
 * @return {object} JSX Table
 */
function Messages() {
  const nav = useNavigate();
  const {channelId} = useParams(); // Extract channelId from URL
  // console.log(channelId);
  const defaultData = {
    accessToken: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpX',
    name: 'donkey',
  };
  const [messages, setMessages] = useState([]);
  let userData = JSON.parse(localStorage.getItem('user')) ||
  JSON.parse(sessionStorage.getItem('user'));
  if (userData === null) {
    userData = defaultData;
  }
  const [newMessage, setNewMessage] = useState('');
  const location = useLocation();
  const {channelName} = location.state || {};
  console.log(channelName);
  // console.log(userData.accessToken);

  useEffect(() => {
    // Fetch messages when channelId changes
    const fetchMessages = async () => {
      try {
        const response = await fetch(`http://localhost:3010/v0/channels/${channelId}/messages`, {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${userData.accessToken}`,
            'Content-Type': 'application/json',
          },
        });
        if (!response.ok) {
          throw new Error('Failed to fetch channels.');
        }
        console.log(response.body);
        const data = await response.json();
        console.log(data);
        setMessages(data);
      } catch (error) {
        console.error('Failed to fetch messages:', error);
      }
    };

    fetchMessages();
  }, [channelId, userData.accessToken]);

  const handleSendMessage = async () => {
    // Prevent sending empty messages
    const messageData = {
      user: userData.name,
      text: newMessage,
      timestamp: new Date().toISOString(),
    };
    // setMessages((prevMessages) => [...prevMessages, messageData]);
    try {
      const response = await fetch(`http://localhost:3010/v0/channels/${channelId}/messages`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${userData.accessToken}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(messageData),
      });
      if (!response.ok) {
        throw new Error('Failed to send the message.');
      }
      const savedMessage = await response.json();
      setMessages((prevMessages) => [...prevMessages, savedMessage]);
      setNewMessage('');
    } catch (error) {
      console.error('Failed to send message:', error);
      // Handle the error, e.g., by showing an error message to the user
    }
  };

  const handleLogout = () => {
    // Clear user authentication data, e.g., remove JWT from localStorage
    localStorage.removeItem('user');
    nav('/login');
  };

  const isHome = location.pathname === '/home';

  return (
    <div className='message-page'>
      <div className="navbar">
        <button onClick={() => nav('/home')}
          className="back-button"
          data-testid="back-button"
          aria-label = "Back">
    &#x2190; Back
        </button>
        <span>{channelName}</span></div>
      <div className="message-container">
        {messages.length > 0 ? (
        messages.map((message, index) => (
          <div key={index} className="message">
            <div className="message-header">
              <span className="sender">{message.user}</span>
              <span className="timestamp">
                {message.timestamp}</span>
            </div>
            <p className="message-content">{message.text}</p>
          </div>
        ))
      ) : (
        <p>No messages found.</p>
      )}
      </div>
      <div className='message-input-container'>
        <input
          type="text"
          placeholder="Type a message..."
          value={newMessage}
          onChange={(e) => setNewMessage(e.target.value)}
          className="message-input"
        />
        <button onClick={handleSendMessage}
          className="send-message-button"
          aria-label="Send Message">Send</button>
      </div>
      <button onClick={handleLogout} className="logout-button"
        data-testid="logout-button">
        Logout
      </button>
      <button
        onClick={() => nav('/home')}
        disabled={isHome}
        className="home-button"
        data-testid="home-button"
        aria-label = "Home"
      >
          Home
      </button>
    </div>
  );
}

export default Messages;

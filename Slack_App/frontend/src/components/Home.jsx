import {useState, useEffect} from 'react';
import {useNavigate, useLocation} from 'react-router-dom';
import './Home.css';
/**
 * @return {object} JSX Table
 */
function Home() {
  const navigate = useNavigate();
  const location = useLocation();
  const defaultData = {
    accessToken: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpX',
    name: 'donkey',
  };
  let userData = JSON.parse(localStorage.getItem('user'));
  if (userData === null) {
    userData = defaultData;
  }
  const [workspaces, setWorkspaces] = useState([]);
  const [selectedWorkspace, setSelectedWorkspace] = useState('');
  const [channels, setChannels] = useState([]);

  const handleWorkspaceChange = async (e) => {
    const workspaceId = e.target.value;
    setSelectedWorkspace(workspaceId);

    // Clear any existing channels before fetching new ones
    setChannels([]);

    // Proceed to fetch channels only if a valid workspaceId is selected
    if (workspaceId) {
      const response = await fetch(`http://localhost:3010/v0/workspaces/${workspaceId}/channels`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${userData.accessToken}`,
          'Content-Type': 'application/json',
        },
      });
      const channelsData = await response.json();
      setChannels(channelsData);
    }
    // Fetch channels based on the selected workspace
    // Add your logic here
  };
  const handleChannelClick = (channelId, channelName) => {
    // Here you could navigate to a route, or set state to show channel content
    console.log(`Channel ${channelId} was clicked.`);
    console.log(channelName);
    navigate(`/messages/${channelId}`, {state: {channelName: channelName}});
    // Example: navigate(`/channels/${channelId}`);
  };
  useEffect(() => {
    const fetchWorkspaces = async () => {
      try {
        const response = await fetch('http://localhost:3010/v0/workspace', {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${userData.accessToken}`,
            'Content-Type': 'application/json',
          },
        });
        if (!response.ok) {
          throw new Error('Failed to fetch workspaces.');
        }
        const data = await response.json();
        setWorkspaces(data);
      } catch (error) {
        console.error('Error fetching workspaces:', error);
        // For instance, if a token is invalid or expired
      }
    };
    // Execute the fetch operation
    fetchWorkspaces();
  }, [userData.accessToken, navigate]);

  const handleLogout = () => {
    // Clear user authentication data, e.g., remove JWT from localStorage
    localStorage.removeItem('user');
    navigate('/Login');
  };

  const isHome = location.pathname === '/home';

  return (
    <div className="homepage">
      <header className="navbar">
        <span className="user-name"> {userData.name} </span>
      </header>
      <div className="homepage-content">
        <h1>Select Workspace</h1>
        <select
          className="workspace-dropdown"
          value={selectedWorkspace}
          onChange={handleWorkspaceChange}
        >
          <option value="" disabled>Select Workspace</option>
          {workspaces.map((workspace) => (
            <option key={workspace.workspaceId} value={workspace.workspaceId}>
              {workspace.name}
            </option>
          ))}
        </select>
        <div className="channels-list">
          {channels.length > 0 ? (
    <ul>
      {channels.map((channel) => (
        <li key={channel.channelId}>
          <button onClick={() =>
            handleChannelClick(channel.channelId, channel.name)}>
            #{channel.name}
          </button>
        </li>
      ))}
    </ul>
  ) : (
    <p>No channels available</p>
  )}
        </div>
      </div>
      <button onClick={handleLogout} className="logout-button"
        data-testid="logout-button"
        aria-label="Logout">
        Logout
      </button>
      <button
        onClick={() => navigate('/home')}
        disabled={isHome}
        className="home-button"
        data-testid="home-button"
      >
          Home
      </button>
    </div>
  );
}

export default Home;

import {it, beforeAll, afterAll, afterEach, expect} from 'vitest';
import {render, screen, fireEvent, waitFor} from '@testing-library/react';
import {MemoryRouter, Route, Routes} from 'react-router-dom';
import {http, HttpResponse} from 'msw';
import {setupServer} from 'msw/node';
import Messages from '../components/messages';
const server = setupServer();

beforeAll(() => {
  server.listen();
  setupLocalStorageMock();
});

afterEach(() => {
  server.resetHandlers();
  cleanupLocalStorageMock();
});

afterAll(() => {
  server.close();
});

const setupLocalStorageMock = () => {
  const mockUserData = {
    name: 'donkey monkey',
    accessToken:
      'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.' +
      'eyJ1c2VySWQiOjEsIm5hbWUiOiJUZXN0IFVzZXIiLCJpYXQiOjE2' +
      'MTYyMzkwMjIsImV4cCI6MTYxNjI0MjYyMn0.' +
      'SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c',
  };
  localStorage.setItem('user', JSON.stringify(mockUserData));
};

const cleanupLocalStorageMock = () => {
  localStorage.removeItem('user');
};

it('handles receiving messages from channels ', async () => {
  const chanId = 'cf0d38b5-86ee-48f9-83d3-f54ee84fb606';
  console.log('monkey');
  server.use(
      http.get(`http://localhost:3010/v0/channels/${chanId}/messages`, async () => {
        const messages = [
          {
            channel_id: 'cf0d38b5-86ee-48f9-83d3-f54ee84fb606',
            id: '11e9c70b-6cc2-4639-a4ad-ea4350cdb76e',
            text: 'Little darling, its been a long cold lonely winter',
            timestamp: '2022-07-09T17:52:00Z',
            user: 'George Harrison',
            user_id: 'df49393d-1dc1-416c-bf71-f7c7a1a1ec5',
          },
          {
            channel_id: 'cf0d38b5-86ee-48f9-83d3-f54ee84fb606',
            id: '634efba5-d7ec-4907-8d99-f04f70af3529',
            text: 'Little darling, it feels like years since its been here',
            timestamp: '2022-07-09T17:53:00Z',
            user: 'George Harrison',
            user_id: 'df49393d-1dc1-416c-bf71-f7c7a1a1ec5',
          },
        ];
        const filterByChannelId = (channelId, messages) => {
          console.log(channelId);
          const filteredMessages = messages.filter((message) =>
            message.channel_id === channelId);
          return filteredMessages;
        };
        return HttpResponse.json(
            filterByChannelId(chanId, messages),
            {status: 200});
      }),
  );
  render(
      <MemoryRouter
        initialEntries={[`/messages/cf0d38b5-86ee-48f9-83d3-f54ee84fb606`]}>
        <Routes>
          <Route path="/messages/:channelId" element={<Messages />} />
        </Routes>
      </MemoryRouter>,
  );
  await waitFor(() => {
    const messageElements = document.querySelectorAll('.message');
    expect(messageElements).not.toHaveLength(0);
  });
});

it('handles logout', async () => {
  render(
      <MemoryRouter
        initialEntries={[`/messages/cf0d38b5-86ee-48f9-83d3-f54ee84fb606`]}>
        <Routes>
          <Route path="/messages/:channelId" element={<Messages />} />
        </Routes>
      </MemoryRouter>,
  );
  const logoutButton = screen.getByTestId('logout-button');
  fireEvent.click(logoutButton);
});

it('handles home page', async () => {
  render(
      <MemoryRouter
        initialEntries={[`/messages/cf0d38b5-86ee-48f9-83d3-f54ee84fb606`]}>
        <Routes>
          <Route path="/messages/:channelId" element={<Messages />} />
        </Routes>
      </MemoryRouter>,
  );
  const homeButton = screen.getByTestId('home-button');
  fireEvent.click(homeButton);
});

it('handles back button', async () => {
  render(
      <MemoryRouter>
        <Messages />
      </MemoryRouter>,
  );
  const backButton = screen.getByTestId('back-button');
  fireEvent.click(backButton);
});

it('non-ok response for retrieving channels', async () => {
  const chanId = 'cf0d38b5-86ee-48f9-83d3-f54ee84fb606';
  console.log('monkey');
  server.use(
      http.get(`http://localhost:3010/v0/channels/${chanId}/messages`, async () => {
        return HttpResponse.json(undefined,
            {status: 400});
      }),
  );
  render(
      <MemoryRouter
        initialEntries={[`/messages/cf0d38b5-86ee-48f9-83d3-f54ee84fb606`]}>
        <Routes>
          <Route path="/messages/:channelId" element={<Messages />} />
        </Routes>
      </MemoryRouter>,
  );
  await waitFor(() => {
    document.querySelectorAll('.message');
  });
});

it('handles sending messages', async () => {
  const chanId = 'cf0d38b5-86ee-48f9-83d3-f54ee84fb606';
  console.log('donkey');
  server.use(
      http.post(`http://localhost:3010/v0/channels/${chanId}/messages`, async () => {
        const messageData = {
          user: 'donkey',
          text: 'monkey inky pinky ponkey',
          timestamp: new Date().toISOString(),
        };
        return HttpResponse.json(messageData, {status: 201});
      }),
  );
  render(
      <MemoryRouter
        initialEntries={[`/messages/cf0d38b5-86ee-48f9-83d3-f54ee84fb606`]}>
        <Routes>
          <Route path="/messages/:channelId" element={<Messages />} />
        </Routes>
      </MemoryRouter>,
  );
  fireEvent.change(screen.getByPlaceholderText('Type a message...'), {
    target: {value: 'monkey inky pinky ponkey'},
  });
  fireEvent.click(screen.getByText('Send'));
  await waitFor(() => {
    expect(screen.getByText('monkey inky pinky ponkey')).toBeInTheDocument();
  });
});

it('handles sending the wrong message', async () => {
  const chanId = 'cf0d38b5-86ee-48f9-83d3-f54ee84fb606';
  console.log('donkey');
  server.use(
      http.post(`http://localhost:3010/v0/channels/${chanId}/messages`, async () => {
        return HttpResponse.json(undefined, {status: 400});
      }),
  );
  render(
      <MemoryRouter
        initialEntries={[`/messages/cf0d38b5-86ee-48f9-83d3-f54ee84fb606`]}>
        <Routes>
          <Route path="/messages/:channelId" element={<Messages />} />
        </Routes>
      </MemoryRouter>,
  );
  fireEvent.change(screen.getByPlaceholderText('Type a message...'), {
    target: {value: 'monkey inky pinky ponkey'},
  });
  fireEvent.click(screen.getByText('Send'));
});


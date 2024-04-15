import {it, beforeAll, afterAll, afterEach, expect} from 'vitest';
import {render, screen, fireEvent} from '@testing-library/react';
import {MemoryRouter} from 'react-router-dom';
import {http, HttpResponse} from 'msw';
import {setupServer} from 'msw/node';
import Home from '../components/Home';


const URL = 'http://localhost:3010/v0/workspace';

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

it('handles receiving workspaces', async () => {
  server.use(
      http.get(URL, async () => {
        console.log('monkey');
        return HttpResponse.json([
          {workspaceId: '79515c03-9f52-4443-945c-02545d948e68',
            name: 'workspace 1'},
          {workspaceId: 'c99a66ce-fdd8-4a5c-8edf-d7310ce7199f',
            name: 'workspace 2'},
        ], {status: 200});
      }),
  );
  render(
      <MemoryRouter>
        <Home />
      </MemoryRouter>,
  );

  const workspaceOption = await screen.findByText('workspace 1');
  expect(workspaceOption).toBeInTheDocument();
  // Test the logout button functionality
  const logoutButton = screen.getByTestId('logout-button');
  fireEvent.click(logoutButton);
  const homeButton = screen.getByTestId('home-button');
  fireEvent.click(homeButton);
});

it('fetches workspaces with a non-ok response and error', async () => {
  // Setup the server to return a non-ok response
  server.use(
      http.get(URL, async () => {
        return HttpResponse.json(undefined, {status: 400});
      }),
  );

  // Attempt to perform the action that triggers the fetch
  render(<MemoryRouter><Home /></MemoryRouter>);
  const logoutButton = screen.getByTestId('logout-button');
  fireEvent.click(logoutButton);
});

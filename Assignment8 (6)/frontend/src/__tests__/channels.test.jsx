import {it, beforeAll, afterAll, afterEach, expect} from 'vitest';
import {render, screen, fireEvent, waitFor} from '@testing-library/react';
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

it('handles receiving channels when a workspace is selected', async () => {
  // First, we mock the server's response to the workspace fetch
  const hardcodedWorkspaceId = 'c99a66ce-fdd8-4a5c-8edf-d7310ce7199f';
  server.use(
      http.get(URL, async () => {
        console.log('donkey');
        return HttpResponse.json([
          {workspaceId: 'c99a66ce-fdd8-4a5c-8edf-d7310ce7199f',
            name: 'workspace 1'},
          {workspaceId: '2ce9406b-94b0-4e9c-ab23-e16b24480e1a',
            name: 'workspace 2'},
        ], {status: 200});
      }),
      // Then, we mock the server's response to the channels fetch
      http.get(`http://localhost:3010/v0/workspaces/${hardcodedWorkspaceId}/channels`, async () => {
        console.log('donkey monkey');
        const channelsByWorkspace = {
          'c99a66ce-fdd8-4a5c-8edf-d7310ce7199f':
          [{channelId: '8159a745-d808-4036-9b23-6e64640deb1f',
            name: 'general'},
          {channelId: '2ef7719f-7c37-45aa-b031-a5856d313064', name: 'random'}],
          '1da047d6-0bc2-45bc-b3e1-d31ac20878bc':
          [{channelId: 'dd35d9f4-fe5d-40d3-84c1-cb6e6eefaa94',
            name: 'discussion'},
          {channelId: '49a2135b-bb69-4d77-9793-28c4aba038f7',
            name: 'projects'}],
        };
        console.log(channelsByWorkspace[hardcodedWorkspaceId]);
        return HttpResponse.json(channelsByWorkspace[hardcodedWorkspaceId],
            {status: 200});
      }),
  );
  // Render the Home component
  render(
      <MemoryRouter>
        <Home />
      </MemoryRouter>,
  );
  // We wait for the workspaces to be loaded
  const workspaceOption = await screen.findByText('workspace 1');
  expect(workspaceOption).toBeInTheDocument();

  fireEvent.change(screen.getByRole('combobox'), {
    target: {value: 'c99a66ce-fdd8-4a5c-8edf-d7310ce7199f'},
  });
  console.log('monkey');
  // Simulate selecting a workspace to trigger channels fetch
  // Now, we wait for the channels of the selected workspace to be loaded
  await waitFor(() => expect(screen.getByText('#general')).toBeInTheDocument());
  screen.debug();
  const generalChannelButton = await screen.findByText('#general');
  fireEvent.click(generalChannelButton);
});

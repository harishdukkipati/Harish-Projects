import {it, beforeAll, afterAll, afterEach} from 'vitest';
import {render, screen, fireEvent} from '@testing-library/react';
import {MemoryRouter} from 'react-router-dom';
import {http, HttpResponse} from 'msw';
import {setupServer} from 'msw/node';
import Login from '../components/Login';

const URL = 'http://localhost:3010/v0/login';


const server = setupServer();

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

it('handles login submission', async () => {
  // Mock the server response for the POST request
  server.use(
      http.post(URL, async () => {
        return HttpResponse.json(
            {name: 'Test User', accessToken: 'abc123'},
            {status: 200},
        );
      }),
  );

  render(
      <MemoryRouter>
        <Login />
      </MemoryRouter>,
  );

  fireEvent.change(screen.getByPlaceholderText('EMail'), {
    target: {value: 'user@example.com'},
  });
  fireEvent.change(screen.getByPlaceholderText('Password'), {
    target: {value: 'password123'},
  });

  fireEvent.click(screen.getByRole('button', {name: /Sign In/i}));
});

it('handles login submission', async () => {
  server.use(
      http.post(URL, async () => {
        return HttpResponse.json(
            {name: 'Test User', accessToken: 'abc123'},
            {status: 200},
        );
      }),
  );

  // Render the Login component
  render(
      <MemoryRouter>
        <Login />
      </MemoryRouter>,
  );
  // Simulate user input for email and password fields
  fireEvent.change(screen.getByPlaceholderText('EMail'), {
    target: {value: 'user@example.com'},
  });
  fireEvent.change(screen.getByPlaceholderText('Password'), {
    target: {value: 'password123'},
  });

  // Simulate form submission
  fireEvent.click(screen.getByRole('button', {name: /Sign In/i}));
});

it('throws an error for non-OK server responses', async () => {
  server.use(
      http.post(URL, async () => {
        return HttpResponse.json({}, {status: 401}); // Simulate error
      }),
  );
  render(
      <MemoryRouter>
        <Login />
      </MemoryRouter>,
  );
  fireEvent.change(screen.getByPlaceholderText('EMail'), {
    target: {value: 'user@example.com'},
  });
  fireEvent.change(screen.getByPlaceholderText('Password'), {
    target: {value: 'wrongPassword'},
  });
  fireEvent.click(screen.getByRole('button', {name: /Sign In/i}));
});


import {it, beforeAll, afterAll, afterEach} from 'vitest';
import {render, screen, fireEvent} from '@testing-library/react';
import {http, HttpResponse} from 'msw';
import {setupServer} from 'msw/node';

import Dummy from '../components/Dummy';

const URL='http://localhost:3010/v0/dummy';

const server = setupServer();

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

/**
 * Send back known text and OK to check UI displays text as expected
 */
it('Has Clickable Button', async () => {
  server.use(
      http.get(URL, async () => {
        return HttpResponse.json({message: 'Hello CSE186'}, {status: 200});
      }),
  );
  render(<Dummy />);
  fireEvent.click(screen.getByText('Get Dummy'));
  await screen.findByText('Hello CSE186');
});

/**
 * Generate a 500 to check UI diaplays error correctly
 */
it('Handles Server Error', async () => {
  server.use(
      http.get(URL, async () => {
        return HttpResponse.json({message: 'Server Error'}, {status: 500});
      }),
  );
  render(<Dummy />);
  fireEvent.click(screen.getByText('Get Dummy'));
  await screen.findByText('ERROR: ', {exact: false});
});



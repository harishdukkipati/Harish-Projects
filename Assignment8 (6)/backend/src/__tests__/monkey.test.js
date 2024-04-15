const supertest = require('supertest');
const http = require('http');

const db = require('./db');
const app = require('../app');

let server;

beforeAll(() => {
  server = http.createServer(app);
  server.listen();
  request = supertest(server);
  return db.reset();
});

afterAll((done) => {
  server.close(done);
  db.shutdown();
});

test('POST Login succeeds with correct credentials', async () => {
  const testUser = {
    email: 'molly@books.com',
    password: 'monkey',
  };
  await request.post('/v0/login')
    .send(testUser)
    .expect(200)
    .then((res) => {
      expect(res.body).toHaveProperty('name');
      expect(res.body).toHaveProperty('accessToken');
    });
});


test('POST Login fails with incorrect password', async () => {
  const invalidLoginCredentials = {
    email: 'molly@books.com', // Assuming this is a valid email in your system
    password: 'wrongPassword',
  };

  await request.post('/v0/login')
    .send(invalidLoginCredentials)
    .expect(401) // Expecting a 401 Unauthorized status code
    .then((res) => {
      expect(res.text).toEqual('Invalid credentials');
    });
});

test('POST Login fails with non-existent email', async () => {
  const nonExistentEmailCredentials = {
    email: 'doesnotexist@books.com', // Non-existent email
    password: 'anyPassword',
  };

  await request.post('/v0/login')
    .send(nonExistentEmailCredentials)
    .expect(401) // Expecting a 401 Unauthorized status code
    .then((res) => {
      expect(res.text).toEqual('Invalid credentials');
    });
});


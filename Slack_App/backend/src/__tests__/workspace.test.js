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


test('Fetch workspaces after successful login', async () => {
  // Step 1: Log in to get an access token
  const loginResponse = await request.post('/v0/login')
    .send({
      email: 'donkey@books.com',
      password: 'donkey',
    })
    .expect(200);
  const accessToken = loginResponse.body.accessToken;
  expect(accessToken).toBeDefined();
  // Step 2: Use the access token to fetch workspaces
  const workspaceResponse = await request.get('/v0/workspace')
    .set('Authorization', `Bearer ${accessToken}`)
    .expect(200);
    // Assuming the response should be an array of workspaces
  expect(Array.isArray(workspaceResponse.body)).toBeTruthy();
  expect(workspaceResponse.body.length).toBeGreaterThan(0);
});


test('Attempt to fetch workspaces with invalid access token', async () => {
  // Use an invalid access token
  const invalidAccessToken = 'someInvalidToken';

  // Attempt to fetch workspaces with the invalid token
  const workspaceResponse = await request.get('/v0/workspace')
    .set('Authorization', `Bearer ${invalidAccessToken}`)
    .expect(400); // Expecting a 404 Not Found response due to invalid token
  expect(workspaceResponse.text).toEqual('Invalid Token');
});

test('Fetch channels after getting workspaces', async () => {
  // Step 1: Log in to get an access token
  const loginResponse = await request.post('/v0/login')
    .send({
      email: 'donkey@books.com',
      password: 'donkey',
    })
    .expect(200);
  const accessToken = loginResponse.body.accessToken;
  expect(accessToken).toBeDefined();
  // Step 2: Use the access token to fetch workspaces
  const workspaceResponse = await request.get('/v0/workspace')
    .set('Authorization', `Bearer ${accessToken}`)
    .expect(200);
  const workspaces = workspaceResponse.body;
  for (const workspace of workspaces) {
    const workspaceId = workspace.workspaceId;
    const channel = await request.get(`/v0/workspaces/${workspaceId}/channels`)
      .set('Authorization', `Bearer ${accessToken}`)
      .expect(200);
    const channels = channel.body;
    console.log(`Channels for Workspace ID ${workspaceId}:`, channels);
    expect(Array.isArray(channels)).toBeTruthy();
  }
});

test('Fetch messages from channels after getting workspaces', async () => {
  // Step 1: Log in to get an access token
  const loginResponse = await request.post('/v0/login')
    .send({
      email: 'donkey@books.com',
      password: 'donkey',
    })
    .expect(200);
  const accessToken = loginResponse.body.accessToken;
  expect(accessToken).toBeDefined();

  // Step 2: Use the access token to fetch workspaces
  const workspaceResponse = await request.get('/v0/workspace')
    .set('Authorization', `Bearer ${accessToken}`)
    .expect(200);
  const workspaces = workspaceResponse.body;
  console.log('donkey');
  console.log(workspaces);
  expect(Array.isArray(workspaces)).toBeTruthy();
  const firstWorkspace = workspaces[0];
  const chan = await
  request.get(`/v0/workspaces/${firstWorkspace.workspaceId}/channels`)
    .set('Authorization', `Bearer ${accessToken}`)
    .expect(200);
  const channels = chan.body;
  expect(Array.isArray(channels)).toBeTruthy();

  const firstChannel = channels[0];
  console.log(firstChannel);
  const messagesResponse =
  await request.get(`/v0/channels/${firstChannel.channelId}/messages`)
    .set('Authorization', `Bearer ${accessToken}`)
    .expect(200);
  const messages = messagesResponse.body;
  // console.log(`Message for Channel ID ${firstChannel.channelId}:`, messages);
  expect(Array.isArray(messages)).toBeTruthy();
  expect(messages.length).toBeGreaterThan(0);
});

test('Post a new message to a channel and verify', async () => {
  const loginResponse = await request.post('/v0/login')
    .send({
      email: 'donkey@books.com',
      password: 'donkey',
    })
    .expect(200);
  const accessToken = loginResponse.body.accessToken;
  expect(accessToken).toBeDefined();

  const workspaceResponse = await request.get('/v0/workspace')
    .set('Authorization', `Bearer ${accessToken}`)
    .expect(200);
  const workspaces = workspaceResponse.body;
  console.log('donkey');
  console.log(workspaces);
  expect(Array.isArray(workspaces)).toBeTruthy();
  const firstWorkspace = workspaces[0];
  const chan = await
  request.get(`/v0/workspaces/${firstWorkspace.workspaceId}/channels`)
    .set('Authorization', `Bearer ${accessToken}`)
    .expect(200);
  const channels = chan.body;
  expect(Array.isArray(channels)).toBeTruthy();

  const firstChannel = channels[0];
  console.log(firstChannel);
  const messagesResponse =
  await request.get(`/v0/channels/${firstChannel.channelId}/messages`)
    .set('Authorization', `Bearer ${accessToken}`)
    .expect(200);
  const messages = messagesResponse.body;
  // console.log(`Message for Channel ID ${firstChannel.channelId}:`, messages);
  expect(Array.isArray(messages)).toBeTruthy();
  expect(messages.length).toBeGreaterThan(0);

  const channelId = 'cf0d38b5-86ee-48f9-83d3-f54ee84fb606';
  const newMessageData = {
    user: 'donkey monkey',
    text: 'Hello, world!',
    timestamp: new Date().toISOString(),
  };
  await request.post(`/v0/channels/${channelId}/messages`)
    .set('Authorization', `Bearer ${accessToken}`)
    .send(newMessageData)
    .expect(201);

  const messagesRespons = await
  request.get(`/v0/channels/${channelId}/messages`)
    .set('Authorization', `Bearer ${accessToken}`)
    .expect(200);

  const message = messagesRespons.body;
  expect(Array.isArray(messages)).toBeTruthy();
  expect(messages.length).toBeGreaterThan(0);
  const messageExists =
  message.some((messag) => messag.text === newMessageData.text);
  expect(messageExists).toBe(true);
});


test('Post the wrong message to a channel and verify', async () => {
  const loginResponse = await request.post('/v0/login')
    .send({
      email: 'donkey@books.com',
      password: 'donkey',
    })
    .expect(200);
  const accessToken = loginResponse.body.accessToken;
  expect(accessToken).toBeDefined();

  const workspaceResponse = await request.get('/v0/workspace')
    .set('Authorization', `Bearer ${accessToken}`)
    .expect(200);
  const workspaces = workspaceResponse.body;
  console.log('donkey');
  console.log(workspaces);
  expect(Array.isArray(workspaces)).toBeTruthy();
  const firstWorkspace = workspaces[0];
  const chan = await
  request.get(`/v0/workspaces/${firstWorkspace.workspaceId}/channels`)
    .set('Authorization', `Bearer ${accessToken}`)
    .expect(200);
  const channels = chan.body;
  expect(Array.isArray(channels)).toBeTruthy();

  const firstChannel = channels[0];
  console.log(firstChannel);
  const messagesResponse =
  await request.get(`/v0/channels/${firstChannel.channelId}/messages`)
    .set('Authorization', `Bearer ${accessToken}`)
    .expect(200);
  const messages = messagesResponse.body;
  // console.log(`Message for Channel ID ${firstChannel.channelId}:`, messages);
  expect(Array.isArray(messages)).toBeTruthy();
  expect(messages.length).toBeGreaterThan(0);

  const channelId = 'cf0d38b5-86ee-48f9-83d3-f54ee84fb606';
  const newMessageData = {
    user: 'don',
    text: 'Hello, world!',
    timestamp: new Date().toISOString(),
  };
  await request.post(`/v0/channels/${channelId}/messages`)
    .set('Authorization', `Bearer ${accessToken}`)
    .send(newMessageData)
    .expect(400);
});


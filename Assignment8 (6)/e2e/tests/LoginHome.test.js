const puppeteer = require('puppeteer');
const http = require('http');
const path = require('path');
const express = require('express');

require('dotenv').config();
const app = require('../../backend/src/app');

let backend;
let frontend;
let browser;

beforeAll(async () => {
  backend = http.createServer(app);
  backend.listen(3010, () => {
    console.log('Backend Running at http://localhost:3010');
  });
  frontend = http.createServer(
    express()
      .use(
        '/assets',
        express.static(
          path.join(__dirname, '..', '..', 'frontend', 'dist', 'assets'),
        ),
      )
      .get('*', (req, res) => {
        res.sendFile(
          'index.html',
          {
            root: path.join(__dirname, '..', '..', 'frontend', 'dist'),
          },
        );
      }),
  );
  frontend.listen(3000, () => {
    console.log('Frontend Running at http://localhost:3000');
  });

  // Setup Puppeteer
  browser = await puppeteer.launch({headless: false});
  page = await browser.newPage();
});

afterAll(async () => {
  // Wrap the server close in a promise to properly await it
  await new Promise((resolve, reject) => {
    backend.close((err) => {
      if (err) reject(err);
      else resolve();
    });
  });

  await new Promise((resolve, reject) => {
    frontend.close((err) => {
      if (err) reject(err);
      else resolve();
    });
  });

  // Assuming `browser.close()` returns a promise, await it directly
  await browser.close();
  console.log('All resources closed');
});

test('Login succeeds with correct credentials', async () => {
  // console.log('donkey');
  await page.goto('http://localhost:3000/login'); // Adjust URL path if necessary

  // Fill in the login form
  await page.type('input[name="email"]', 'anna@books.com');
  await page.type('input[name="password"]', 'funky');

  // Submit the form
  await page.click('input[type="submit"]');
  await page.waitForNavigation();
  // Example: Check if we're redirected to the expected page after login
  const url = await page.url();
  expect(url).toContain('/home'); // Adjust according to your app's behavior
});

test('Login succeeds with correct credentials', async () => {
  // console.log('donkey');
  await page.goto('http://localhost:3000/login'); // Adjust URL path if necessary

  // Fill in the login form
  await page.type('input[name="email"]', 'anna@books.com');
  await page.type('input[name="password"]', 'funky');

  // Submit the form
  await page.click('input[type="submit"]');
  await page.waitForNavigation();
  // Example: Check if we're redirected to the expected page after login
  await page.url(); // Adjust according to your app's behavior
  await page.click('[aria-label="Logout"]');
  // await page.waitForNavigation();
  // Verify we're redirected back to the login page
  const don = await page.url();
  expect(don).toContain('/Login');
});

test('Testing if workspaces are fetched', async () => {
  console.log('donkey');
  await page.goto('http://localhost:3000/login'); // Adjust URL path if necessary

  // Fill in the login form
  await page.type('input[name="email"]', 'anna@books.com');
  await page.type('input[name="password"]', 'funky');

  // Submit the form
  await page.click('input[type="submit"]');
  await page.waitForNavigation();
  // Example: Check if we're redirected to the expected page after login
  const url = await page.url();
  expect(url).toContain('/home'); // Adjust according to your app's behavior
  await page.waitForFunction(() =>
    document.querySelectorAll('.workspace-dropdown option').length > 0);

  // Further assertions can be made here
  // For example, verify that the workspace dropdown is not empty
  const workspaceOptionsCount = await page.evaluate(() => {
    const dropdown = document.querySelector('.workspace-dropdown');
    return dropdown ? dropdown.options.length : 0;
  });
  expect(workspaceOptionsCount).toBeGreaterThan(0);
});

test('Testing if channels are fetched for a workspace', async () => {
  // console.log('donkey');
  await page.goto('http://localhost:3000/login'); // Go to the login page
  // Fill in the login form
  await page.type('input[name="email"]', 'anna@books.com');
  await page.type('input[name="password"]', 'funky');
  // Submit the form and wait for navigation to the home page
  await page.click('input[type="submit"]');
  await page.waitForNavigation();
  // Confirm that we're redirected to the expected page after login
  await page.url();
  // Wait for the workspaces dropdown to be populated
  await page.waitForFunction(() =>
    document.querySelectorAll('.workspace-dropdown option').length > 1);
  // Select a workspace to trigger channels fetch
  // Assuming the value for the workspace option is the workspace ID
  console.log('donkey monkey');
  await page.select('.workspace-dropdown',
    '0e177213-4f9e-416b-9824-fd5b06ebb080');
  await page.waitForFunction(() =>
    document.querySelectorAll('.channels-list li').length > 0);
  // Verify that the channels list is not empty
  const channelsCount = await page.evaluate(() => {
    const channelsList = document.querySelectorAll('.channels-list li');
    return channelsList ? channelsList.length : 0;
  });
  expect(channelsCount).toBeGreaterThan(0);
  // Further tests here, like clicking on a channel and verifying content
});

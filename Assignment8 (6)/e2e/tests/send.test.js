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

test('Testing if you can send messages in a channel', async () => {
  await page.goto('http://localhost:3000/login'); // Go to the login page
  // Fill in the login form
  await page.type('input[name="email"]', 'anna@books.com');
  await page.type('input[name="password"]', 'funky');
  // Submit the form and wait for navigation to the home page
  await page.click('input[type="submit"]');
  // await page.waitForNavigation();
  await page.waitForFunction(() =>
    document.querySelectorAll('.workspace-dropdown option').length > 1);
  // Select a workspace to trigger channels fetch
  // Assuming the value for the workspace option is the workspace ID
  await page.select('.workspace-dropdown',
    '0e177213-4f9e-416b-9824-fd5b06ebb080');
  await page.waitForFunction(() =>
    document.querySelectorAll('.channels-list li').length > 0);
  // Verify that the channels list is not empty
  await page.evaluate(() => {
    const channelsList = document.querySelectorAll('.channels-list li');
    return channelsList ? channelsList.length : 0;
  });
  // Further tests here, like clicking on a channel and verifying content
  const assignmentName = '#assignment1';
  await page.evaluate((name) => {
    // Query all buttons within the channels list
    const buttons = [...document.querySelectorAll('.channels-list li button')];
    // Find the button that has the exact text content
    const targetButton = buttons.find((button) => button.innerText === name);
    // If the button is found, click it
    if (targetButton) {
      targetButton.click();
    } else {
      throw new Error(`Button with text "${name}" not found`);
    }
  }, assignmentName);
  // console.log('hi');
  // await page.url();
  // console.log('Messages Text Content:', messagesText);
  // Check if any of the messages contain the expected text 'Little darling'
  const messageToSend = 'came to monkey';
  await page.evaluate((message) => {
    const input = document.querySelector('.message-input');
    const nativeInputValueSetter =
      Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,
        'value').
        set;
    nativeInputValueSetter.call(input, message);
    input.dispatchEvent(new Event('input', {bubbles: true}));
  }, messageToSend);
  const inputValue = await page.$eval('.message-input', (el) => el.value);
  await page.click('[aria-label="Send Message"]');
  await page.waitForFunction(
    (msgContent) => {
      const messages = Array.from(document.querySelectorAll('.message'));
      return messages.some((message) => message.innerText.includes(msgContent));
    },
    {timeout: 30000},
    inputValue,
  );
  const updatedMessagesText = await page.evaluate(() => {
    const messages = Array.from(document.querySelectorAll('.message'));
    return messages.map((message) => message.innerText.trim());
  });
  const containsNewText =
      updatedMessagesText.some((text) => text.includes('came to monkey'));
  expect(containsNewText).toBe(true);
  // Ensure the list of messages has grown by at least one
});

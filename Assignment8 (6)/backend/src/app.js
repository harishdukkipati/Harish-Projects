/*
 * Copyright (C) 2022-2024 David C. Harrison. All right reserved.
 *
 * You may not use, distribute, publish, or modify this code without
 * the express written permission of the copyright holder.
 */
const express = require('express');
const cors = require('cors');
const yaml = require('js-yaml');
const swaggerUi = require('swagger-ui-express');
const fs = require('fs');
const path = require('path');
const OpenApiValidator = require('express-openapi-validator');
const authenticate = require('./authenticate');

const donkey = require('./donkey');
const dummy = require('./dummy');

const app = express();
app.use(cors());
app.use(express.json());
app.use(express.urlencoded({extended: false}));

const apiSpec = path.join(__dirname, '../api/openapi.yaml');
const apidoc = yaml.load(fs.readFileSync(apiSpec, 'utf8'));

app.use(
  '/v0/api-docs',
  swaggerUi.serve,
  swaggerUi.setup(apidoc),
);

app.use(
  OpenApiValidator.middleware({
    apiSpec: apiSpec,
    validateRequests: true,
    validateResponses: true,
  }),
);

app.post('/v0/login', donkey.login);
app.get('/v0/dummy', dummy.get);
app.get('/v0/workspace', authenticate, donkey.getWorkspaces);
app.get('/v0/workspaces/:workspaceId/channels', authenticate,
  donkey.getChannelsByWorkspace);
app.get('/v0/channels/:channelId/messages', authenticate,
  donkey.getMessagesByChannel);
app.post('/v0/channels/:channelId/messages', authenticate,
  donkey.postMessagesByChannel);
// Your routes go here

app.use((err, req, res, next) => {
  res.status(err.status).json({
    message: err.message,
    errors: err.errors,
    status: err.status,
  });
});

module.exports = app;

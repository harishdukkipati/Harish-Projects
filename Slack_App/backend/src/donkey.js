const bcrypt = require('bcryptjs');
const secrets = require('./secrets');
const jwt = require('jsonwebtoken');
const db = require('./email');

exports.login = async (req, res) => {
  const {email, password} = req.body;

  try {
    const user = await db.selectEmails(email);
    if (!bcrypt.compareSync(password, user.user_data.password)) {
      // If password does not match, directly throw an error
      throw new Error('Invalid credentials');
    }
    const accessToken = jwt.sign(
      {userId: user.id, email: user.user_data.email, role: user.user_data.role},
      secrets.accessToken,
      {expiresIn: '30m', algorithm: 'HS256'},
    );
    res.status(200).json({name: user.user_data.name, accessToken: accessToken});
  } catch (error) {
    // Handle any errors that occurred during the process
    res.status(401).send(error.message);
  }
};

exports.getWorkspaces = async (req, res) => {
  // The user ID is now available in req.userId
  const workspaces = await db.selectUserWorkspaces(req.userId);
  // console.log(workspaces);
  res.status(200).json(workspaces);
};


exports.getChannelsByWorkspace = async (req, res) => {
  const {workspaceId} = req.params;
  const channels = await db.getChannelsByWorkspaceId(workspaceId);
  // console.log(channels);
  res.status(200).json(channels);
};

exports.getMessagesByChannel = async (req, res) => {
  const {channelId} = req.params;
  const messages = await db.getMessagesByChannelId(channelId);
  res.status(200).json(messages);
};

exports.postMessagesByChannel = async (req, res) => {
  const channelId = req.params.channelId;
  const {user, text, timestamp} = req.body;
  // console.log(req.body);

  // Fetch the userID based on the username
  const userId = await db.getUserIDByName(user);
  if (!userId) {
    return res.status(400).send('User not found.');
  }
  const messageData = JSON.stringify({
    user: user,
    text: text,
    timestamp: timestamp,
  });
    // Now you can insert the message using userId, channelId, and messageData
  const savedMessage = await db.insertMessage(channelId, userId, messageData);
  res.status(201).json(savedMessage);
};

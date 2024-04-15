const secrets = require('./secrets');
const jwt = require('jsonwebtoken');
const db = require('./email'); // Adjust path as necessary

const authenticate = async (req, res, next) => {
  console.log('donkey monkey');
  const token = req.headers.authorization?.split(' ')[1]; // Bearer <token>

  try {
    console.log(secrets.accessToken);
    const verified = jwt.verify(token, secrets.accessToken);
    req.userId = verified.userId; // Extracted user ID from token
    // console.log('Extracted userId from JWT:', req.userId);

    // Optionally fetch full user object from the database
    const user = await db.getUserById(req.userId);
    req.user = user; // Attach the full user object to the request

    next();
  } catch (error) {
    console.log('wrong token');
    res.status(400).send('Invalid Token');
  }
};

module.exports = authenticate;


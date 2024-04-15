const {Pool} = require('pg');

require('dotenv').config();
process.env.POSTGRES_DB='test';

const pool = new Pool({
  host: 'localhost',
  port: 5432,
  database: process.env.POSTGRES_DB,
  user: process.env.POSTGRES_USER,
  password: process.env.POSTGRES_PASSWORD,
});

exports.selectEmails = async (email) => {
  const res = await pool.query(
    'SELECT * FROM users WHERE user_data->>\'email\' = $1',
    [email],
  );
  if (res.rows.length === 0) {
    throw new Error('Invalid credentials'); // No user found, throw an error
  }
  // console.log(res.rows[0]);
  return res.rows[0];
};

exports.selectUserWorkspaces = async (userId) => {
  const queryText = `
    SELECT w.id as workspace_id, w.workspace_data
    FROM workspaces w
    INNER JOIN users_workspaces uw ON w.id = uw.workspace_id
    WHERE uw.user_id = $1
  `;
  const {rows} = await pool.query(queryText, [userId]);
  // console.log('Workspace data rows:', rows);
  const formattedRows = rows.map((row) => {
    const workspaceData = row.workspace_data;
    // Assuming workspace_data contains a JSON object with a "name" property
    return {
      workspaceId: row.workspace_id,
      name: workspaceData.name, // Directly accessing the name property
      ...workspaceData,
      // Spreads the rest of the workspace_data properties
    };
  });
  return formattedRows;
};

exports.getUserById = async (userId) => {
  const query = 'SELECT * FROM users WHERE id = $1';
  const {rows} = await pool.query(query, [userId]);
  // console.log('Fetched user by ID:', rows[0]);
  return rows[0]; // Assuming `id` is a unique identifier
};

exports.getChannelsByWorkspaceId = async (workspaceId) => {
  const queryText = `
    SELECT c.id as channel_id, c.channel_data
    FROM channels c
    WHERE c.workspace_id = $1
  `;
  const {rows} = await pool.query(queryText, [workspaceId]);
  // console.log('Channel data rows:', rows);

  return rows.map((row) => ({
    ...row.channel_data,
    channelId: row.channel_id,
  }));
};

exports.getMessagesByChannelId = async (channelId) => {
  const queryText = `
    SELECT 
      m.id,
      m.channel_id,
      m.user_id,
      m.message_data
    FROM 
      messages m
    WHERE 
      m.channel_id = $1
    ORDER BY 
      m.message_data ->> 'timestamp' ASC;
  `;

  const {rows} = await pool.query(queryText, [channelId]);


  return rows.map((row) => {
    const messageData = row.message_data;
    return {
      id: row.id,
      channel_id: row.channel_id,
      user_id: row.user_id,
      text: messageData.text,
      user: messageData.user,
      timestamp: messageData.timestamp,
    };
  });
};

exports.getUserIDByName = async (name) => {
  const queryText = `
    SELECT id 
    FROM users 
    WHERE user_data ->> 'name' = $1
  `;
  const {rows} = await pool.query(queryText, [name]);
  if (rows.length > 0) {
    return rows[0].id; // Assuming 'id' is the column name for the userID
  } else {
    return null;
  }
};

exports.insertMessage = async (channelId, userId, messageData) => {
  const queryText = `
    INSERT INTO messages (id, channel_id, user_id, message_data) 
    VALUES (gen_random_uuid(), $1, $2, $3)
    RETURNING message_data;
  `;
  const {rows} =
    await pool.query(queryText, [channelId, userId, messageData]);
  return rows[0].message_data;
};

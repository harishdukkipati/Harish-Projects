/*
 * Copyright (C) 2022-2024 David C. Harrison. All right reserved.
 *
 * You may not use, distribute, publish, or modify this code without
 * the express written permission of the copyright holder.
 */
/*
 * *****************************************************
 * YOU CAN DELETE, BUT DO NOT MODIFY THIS FILE
 * *****************************************************
 */
const {Pool} = require('pg');

const pool = new Pool({
  host: 'localhost',
  port: 5432,
  database: process.env.POSTGRES_DB,
  user: process.env.POSTGRES_USER,
  password: process.env.POSTGRES_PASSWORD,
});

const selectDummy = async () => {
  const select = 'SELECT * FROM dummy';
  const query = {
    text: select,
    values: [],
  };
  const {rows} = await pool.query(query);
  return rows[0].created;
};

exports.get = async (req, res) => {
  res.status(200).json({message:
    `Hello CSE186 @ ${new Date().toString()} ` +
    `[ Database created ${await selectDummy()} ]`});
};

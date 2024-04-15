--
-- All SQL statements must be on a single line and end in a semicolon.
--

-- Dummy Data --
INSERT INTO dummy (created) VALUES (current_timestamp);
-- Populate Your Tables Here --
INSERT INTO users (id, user_data) VALUES ('123e4567-e89b-12d3-a456-426614174000','{"email": "molly@books.com", "password": "$2a$10$TSAg8EaNMwsHzkjqAdR5OO6M62qMXFlBHYdH2xHAohdUBLniw9dSy", "role": "member", "name": "Molly Member"}');
INSERT INTO users (id, user_data) VALUES ('591b428e-1b99-4a56-b653-dab17210b3b7', '{"email": "anna@books.com", "password": "$2a$10$HB32wMB9wcd41TFdtu9BTev6GLq9POM5ewFHOPfPipYT0gwx4EkYO", "role": "admin", "name": "Anna Admin"}');
INSERT INTO users (id, user_data) VALUES ('df49393d-1dc1-416c-bf71-f7cf7a1a1ec5', '{"email": "donkey@books.com", "password": "$2a$10$dVh1s7IWIcZmt/CWMZgv1eApf/uoEUZ3LS9e4LPKxq5yT6C/lhJj2", "role": "member", "name": "donkey monkey"}');
INSERT INTO users (id, user_data) VALUES ('c794a841-643e-43db-8a50-5b700a277935', '{"email": "sarah@books.com", "password": "$2a$10$t/w9Kpbpukf.ctw2Fk2QQOAqBKyQ75lMHhUbfUtz0MW4rA9fjYr4W", "role": "member", "name": "monkey donkey"}');


INSERT INTO workspaces (id, workspace_data) VALUES ('0e177213-4f9e-416b-9824-fd5b06ebb080', '{"name": "CSE-186"}');
INSERT INTO workspaces (id, workspace_data) VALUES ('68669a4b-2b04-4224-9cec-4197f2556de3', '{"name": "Donkey Culture"}');
INSERT INTO workspaces (id, workspace_data) VALUES ('badb3495-1142-4134-ac3b-e90f7b1cf77b', '{"name": "Monkey Future"}');
INSERT INTO workspaces (id, workspace_data) VALUES ('38e477ad-9f32-4e02-8114-b533a91973d6', '{"name": "NBA"}')

INSERT INTO users_workspaces (user_id, workspace_id) VALUES ('df49393d-1dc1-416c-bf71-f7cf7a1a1ec5', '0e177213-4f9e-416b-9824-fd5b06ebb080');
INSERT INTO users_workspaces (user_id, workspace_id) VALUES ('df49393d-1dc1-416c-bf71-f7cf7a1a1ec5', '68669a4b-2b04-4224-9cec-4197f2556de3');
INSERT INTO users_workspaces (user_id, workspace_id) VALUES ('df49393d-1dc1-416c-bf71-f7cf7a1a1ec5', 'badb3495-1142-4134-ac3b-e90f7b1cf77b');
INSERT INTO users_workspaces (user_id, workspace_id) VALUES ('591b428e-1b99-4a56-b653-dab17210b3b7', '0e177213-4f9e-416b-9824-fd5b06ebb080');
INSERT INTO users_workspaces (user_id, workspace_id) VALUES ('591b428e-1b99-4a56-b653-dab17210b3b7', '68669a4b-2b04-4224-9cec-4197f2556de3');
INSERT INTO users_workspaces (user_id, workspace_id) VALUES ('591b428e-1b99-4a56-b653-dab17210b3b7', 'badb3495-1142-4134-ac3b-e90f7b1cf77b');
INSERT INTO users_workspaces (user_id, workspace_id) VALUES ('123e4567-e89b-12d3-a456-426614174000', '0e177213-4f9e-416b-9824-fd5b06ebb080');
INSERT INTO users_workspaces (user_id, workspace_id) VALUES ('123e4567-e89b-12d3-a456-426614174000', '68669a4b-2b04-4224-9cec-4197f2556de3');
INSERT INTO users_workspaces (user_id, workspace_id) VALUES ('123e4567-e89b-12d3-a456-426614174000', 'badb3495-1142-4134-ac3b-e90f7b1cf77b');

INSERT INTO channels (id, workspace_id, channel_data) VALUES ('cf0d38b5-86ee-48f9-83d3-f54ee84fb606', '0e177213-4f9e-416b-9824-fd5b06ebb080', '{"name": "assignment1"}');
INSERT INTO channels (id, workspace_id, channel_data) VALUES ('8159a745-d808-4036-9b23-6e64640deb1f', '0e177213-4f9e-416b-9824-fd5b06ebb080', '{"name": "assignment2"}');
INSERT INTO channels (id, workspace_id, channel_data) VALUES ('8d849885-7e01-4ddc-a08d-6b47ab488093', '0e177213-4f9e-416b-9824-fd5b06ebb080', '{"name": "assignment3"}');
INSERT INTO channels (id, workspace_id, channel_data) VALUES ('8d849885-7e01-4ddc-a08d-6b47ab488092', '0e177213-4f9e-416b-9824-fd5b06ebb080', '{"name": "assignment4"}');
INSERT INTO channels (id, workspace_id, channel_data) VALUES ('99466809-0e30-41e7-a90e-b3aab1c78e77', '0e177213-4f9e-416b-9824-fd5b06ebb080', '{"name": "workspace"}');
INSERT INTO channels (id, workspace_id, channel_data) VALUES ('7ad35d9d-094f-4a55-97ac-57eefeaaa9bc', '68669a4b-2b04-4224-9cec-4197f2556de3', '{"name": "donkey"}');
INSERT INTO channels (id, workspace_id, channel_data) VALUES ('0a746869-0d66-48dd-b8d9-2bdd2d8b3322', '68669a4b-2b04-4224-9cec-4197f2556de3', '{"name": "monkey"}');
INSERT INTO channels (id, workspace_id, channel_data) VALUES ('0067c50a-55a3-4ad4-9d59-bb041d5fe2f4', '68669a4b-2b04-4224-9cec-4197f2556de3', '{"name": "funky"}');
INSERT INTO channels (id, workspace_id, channel_data) VALUES ('64b0f48b-5302-46a1-9693-53ffdb157a75', '68669a4b-2b04-4224-9cec-4197f2556de3', '{"name": "funk"}');
INSERT INTO channels (id, workspace_id, channel_data) VALUES ('cf2cee57-8096-42f4-a84b-cfdf5be17043', 'badb3495-1142-4134-ac3b-e90f7b1cf77b', '{"name": "Homo Sapiens"}');
INSERT INTO channels (id, workspace_id, channel_data) VALUES ('8230b82a-aec7-4053-9693-5000a6c02d9c', 'badb3495-1142-4134-ac3b-e90f7b1cf77b', '{"name": "Humans"}');
INSERT INTO channels (id, workspace_id, channel_data) VALUES ('53c2480d-1bbb-4c8d-b956-2db7561d2512', 'badb3495-1142-4134-ac3b-e90f7b1cf77b', '{"name": "Evolution"}');
INSERT INTO channels (id, workspace_id, channel_data) VALUES ('6e2b7dde-86ca-4478-8374-3883185ca587', 'badb3495-1142-4134-ac3b-e90f7b1cf77b', '{"name": "POOKIE"}');
INSERT INTO channels (id, workspace_id, channel_data) VALUES ('ff8dbd5d-db22-437b-a197-36e3b6abce24', '38e477ad-9f32-4e02-8114-b533a91973d6', '{"name": "Bronny"}');
INSERT INTO channels (id, workspace_id, channel_data) VALUES ('c9e8ff9c-fcc0-4941-8e74-35fdddc15d6a', '38e477ad-9f32-4e02-8114-b533a91973d6', '{"name": "LePookie James"}');

INSERT INTO messages (id, channel_id, user_id, message_data) VALUES ('11e9c70b-6cc2-4639-a4ad-ea4350cdb76e', 'cf0d38b5-86ee-48f9-83d3-f54ee84fb606', 'df49393d-1dc1-416c-bf71-f7cf7a1a1ec5', '{"user":"HARRY HARRISON","text":"Little darling, its been a long cold lonely winter","timestamp":"2022-07-09T17:52:00Z"}');
INSERT INTO messages (id, channel_id, user_id, message_data) VALUES ('634efba5-d7ec-4907-8d99-f04f70af3529', 'cf0d38b5-86ee-48f9-83d3-f54ee84fb606', 'df49393d-1dc1-416c-bf71-f7cf7a1a1ec5', '{"user":"LePookie James","text":"Little darling, it feels like years since its been here","timestamp":"2022-07-09T17:53:00Z"}');
INSERT INTO messages (id, channel_id, user_id, message_data) VALUES ('76180baa-1f1c-485a-a094-d60f6c06e79b', 'cf0d38b5-86ee-48f9-83d3-f54ee84fb606', 'df49393d-1dc1-416c-bf71-f7cf7a1a1ec5', '{"user":"Steph McFlurry","text":"Here comes the sun, here comes the sun","timestamp":"2022-07-09T17:54:00Z"}');
INSERT INTO messages (id, channel_id, user_id, message_data) VALUES ('d500babd-26a8-44c3-b382-7b5226f9aef9', 'cf0d38b5-86ee-48f9-83d3-f54ee84fb606', 'df49393d-1dc1-416c-bf71-f7cf7a1a1ec5', '{"user":"JOSH ALLLENNNN","text":"And I say its all right","timestamp":"2022-07-09T17:55:00Z"}');
INSERT INTO messages (id, channel_id, user_id, message_data) VALUES ('42a104ff-6aa6-4fde-ba8c-8baf1b9c8a7e', '8159a745-d808-4036-9b23-6e64640deb1f', 'df49393d-1dc1-416c-bf71-f7cf7a1a1ec5', '{"user":"Bob Dylan","text":"How many roads must a man walk down?","timestamp":"2022-07-10T07:30:00Z"}');
INSERT INTO messages (id, channel_id, user_id, message_data) VALUES ('d21ae81c-ecb7-4cf2-b98b-3751c1379668', '8d849885-7e01-4ddc-a08d-6b47ab488093', 'df49393d-1dc1-416c-bf71-f7cf7a1a1ec5', '{"user":"Joni Mitchell","text":"They paved paradise, put up a parking lot","timestamp":"2022-07-10T13:27:00Z"}');
INSERT INTO messages (id, channel_id, user_id, message_data) VALUES ('b1b3f2f1-7951-457c-9fd6-4e91f7bc79cf', '8d849885-7e01-4ddc-a08d-6b47ab488093', 'df49393d-1dc1-416c-bf71-f7cf7a1a1ec5', '{"user":"Joni Mitchell","text":"With a pink hotel, a boutique, and a swingin hot spot","timestamp":"2022-07-10T13:28:00Z"}');
INSERT INTO messages (id, channel_id, user_id, message_data) VALUES ('32912bf7-be86-4902-97a0-27e9b6520b84', '7ad35d9d-094f-4a55-97ac-57eefeaaa9bc', 'df49393d-1dc1-416c-bf71-f7cf7a1a1ec5', '{"user":"George Harrison","text":"Little darling, its been a long cold lonely winter","timestamp":"2022-07-09T17:52:00Z"}');
INSERT INTO messages (id, channel_id, user_id, message_data) VALUES ('7504e3f3-30f6-47a8-890c-284461c70c0d', '7ad35d9d-094f-4a55-97ac-57eefeaaa9bc', 'df49393d-1dc1-416c-bf71-f7cf7a1a1ec5', '{"user":"Le Pookie James","text":"Little darling, it feels like years since its been here","timestamp":"2022-07-09T17:53:00Z"}');
INSERT INTO messages (id, channel_id, user_id, message_data) VALUES ('e5c651df-eb11-4013-bdfc-0de42a1c5b73', '7ad35d9d-094f-4a55-97ac-57eefeaaa9bc', 'df49393d-1dc1-416c-bf71-f7cf7a1a1ec5', '{"user":"Le Monkey Shames","text":"Here comes the sun, here comes the sun","timestamp":"2022-07-09T17:54:00Z"}');
INSERT INTO messages (id, channel_id, user_id, message_data) VALUES ('9184aceb-b2df-4cd8-84f0-9963b406f012', '7ad35d9d-094f-4a55-97ac-57eefeaaa9bc', 'df49393d-1dc1-416c-bf71-f7cf7a1a1ec5', '{"user":"Le Sweaty Flames","text":"And I say its all right","timestamp":"2022-07-09T17:55:00Z"}');
INSERT INTO messages (id, channel_id, user_id, message_data) VALUES ('00cc62e6-d687-481a-b85f-1ad0bec72eed', '0a746869-0d66-48dd-b8d9-2bdd2d8b3322', 'df49393d-1dc1-416c-bf71-f7cf7a1a1ec5', '{"user":"The Dollar Dames","text":"How many roads must a man walk down?","timestamp":"2022-07-10T07:30:00Z"}');
INSERT INTO messages (id, channel_id, user_id, message_data) VALUES ('1de48606-54b7-4cbd-8a9a-f64be52ec3ec', '0067c50a-55a3-4ad4-9d59-bb041d5fe2f4', 'df49393d-1dc1-416c-bf71-f7cf7a1a1ec5', '{"user":"Joni Mitchell","text":"They paved paradise, put up a parking lot","timestamp":"2022-07-10T13:27:00Z"}');
INSERT INTO messages (id, channel_id, user_id, message_data) VALUES ('598a294d-0416-4b70-b6b2-238e1d72f3a8', '0067c50a-55a3-4ad4-9d59-bb041d5fe2f4', 'df49393d-1dc1-416c-bf71-f7cf7a1a1ec5', '{"user":"Joni Mitchell","text":"With a pink hotel, a boutique, and a swingin hot spot","timestamp":"2022-07-10T13:28:00Z"}');
INSERT INTO messages (id, channel_id, user_id, message_data) VALUES ('86e07e53-afb9-47d0-a5c6-30e21097fd1c', 'cf2cee57-8096-42f4-a84b-cfdf5be17043', 'df49393d-1dc1-416c-bf71-f7cf7a1a1ec5', '{"user":"George Harrison","text":"Little darling, its been a long cold lonely winter","timestamp":"2022-07-09T17:52:00Z"}');
INSERT INTO messages (id, channel_id, user_id, message_data) VALUES ('d4f34f21-e60a-4c3d-832d-ef751238b487', 'cf2cee57-8096-42f4-a84b-cfdf5be17043', 'df49393d-1dc1-416c-bf71-f7cf7a1a1ec5', '{"user":"George Harrison","text":"Little darling, it feels like years since its been here","timestamp":"2022-07-09T17:53:00Z"}');
INSERT INTO messages (id, channel_id, user_id, message_data) VALUES ('2ae0c1dd-af3e-42f2-ae02-51c48d548854', 'cf2cee57-8096-42f4-a84b-cfdf5be17043', 'df49393d-1dc1-416c-bf71-f7cf7a1a1ec5', '{"user":"George Harrison","text":"Here comes the sun, here comes the sun","timestamp":"2022-07-09T17:54:00Z"}');
INSERT INTO messages (id, channel_id, user_id, message_data) VALUES ('71f502a3-fe6e-4812-b145-6fb5ab824cb5', 'cf2cee57-8096-42f4-a84b-cfdf5be17043', 'df49393d-1dc1-416c-bf71-f7cf7a1a1ec5', '{"user":"George Harrison","text":"And I say its all right","timestamp":"2022-07-09T17:55:00Z"}');
INSERT INTO messages (id, channel_id, user_id, message_data) VALUES ('661d7f3b-d068-4f0c-91e6-dff3076061e2', '8230b82a-aec7-4053-9693-5000a6c02d9c', 'df49393d-1dc1-416c-bf71-f7cf7a1a1ec5', '{"user":"Bob Dylan","text":"How many roads must a man walk down?","timestamp":"2022-07-10T07:30:00Z"}');
INSERT INTO messages (id, channel_id, user_id, message_data) VALUES ('f1da22f0-0c4a-47b3-b19f-68ff37089a2b', '53c2480d-1bbb-4c8d-b956-2db7561d2512', 'df49393d-1dc1-416c-bf71-f7cf7a1a1ec5', '{"user":"Joni Mitchell","text":"They paved paradise, put up a parking lot","timestamp":"2022-07-10T13:27:00Z"}');
INSERT INTO messages (id, channel_id, user_id, message_data) VALUES ('79515c03-9f52-4443-945c-02545d948e68', '53c2480d-1bbb-4c8d-b956-2db7561d2512', 'df49393d-1dc1-416c-bf71-f7cf7a1a1ec5', '{"user":"Joni Mitchell","text":"With a pink hotel, a boutique, and a swingin hot spot","timestamp":"2022-07-10T13:28:00Z"}');
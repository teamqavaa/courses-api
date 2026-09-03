--
-- PostgreSQL database dump
--

\restrict rqkcUxREgqjRZEQu5Y9hu2eRvsJfqnZerL7dTbITVrhmBSNQwMWczXtht4TEpvC

-- Dumped from database version 17.6
-- Dumped by pg_dump version 18.4

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Data for Name: skill; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.skill (id, title, slug, description, icon, "order", is_active, created_at) FROM stdin;
ea41b3e7-59f1-4f9d-a486-4b423fb5802d	Python Fundamentals	python-fundamentals	Learn Python at your pace		0	t	2026-08-25 10:53:51.709672+00
\.


--
-- Data for Name: lab; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.lab (id, title, description, language, status, created_at, starter_code, difficulty, skill_id) FROM stdin;
0e8081ef-c020-4e07-b654-e07dd2ce3dbe	Intro to Javascript		typescript	published	2026-07-11 14:12:54.111522+00	const name = "Awa";\r\nconst age = 24;\r\nconst height = 1.65;\r\nconst isStudent = true;\r\n\r\n// TODO: log each variable and its type	guided	\N
22c18de9-ebf5-44f3-80c2-099998d68f19	Intro to Python	Learn about Python Programming	python	published	2026-07-18 14:58:20.406619+00	name = "Awa"\r\nage = 24\r\nheight = 1.65\r\nis_student = True\r\n\r\n# TODO: print each variable and its type	guided	ea41b3e7-59f1-4f9d-a486-4b423fb5802d
\.


--
-- Data for Name: lab_objective; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.lab_objective (id, "order", title, content, hint, lab_id, starter_code) FROM stdin;
4dc093d9-0fc4-4a31-8f91-98f350b0e06f	1	Variables & Data Types	Welcome!\r\nPython is one of the most popular programming languages in the world — used for web development, data science, automation, and more. In this lesson, you'll learn how to store and work with data using variables.\r\n\r\nWhat is a Variable?\r\nA variable is like a labeled box where you store a piece of information. You create one by giving it a name and assigning it a value using the = sign.\r\n\r\nname = "Alex"\r\nage = 25\r\nheight = 5.9\r\nis_student = True\r\n\r\nPython figures out the type automatically — you don't have to declare it yourself. This is called dynamic typing.\r\n\r\n📝 Exercise\r\n1. city — a string with the name of your favorite city\r\n2. population — an integer representing its population (approximate is fine)\r\n3. is_capital — a boolean indicating whether it's a capital city\r\n\r\n# Your code here. Copy and paste in code editor\r\ncity = \r\npopulation = \r\nis_capital = \r\n\r\nprint(...)\r\n\r\nNext lesson: Lists — how to store multiple values in a single variable! 🚀	1: Strings need quotes, integers don't, and booleans are True or False with a capital letter.\r\n\r\n2: To combine different types in one print statement, either use commas inside print():\r\nprint(city, "has a population of", population).\r\nor convert everything to a string using str() and +.	22c18de9-ebf5-44f3-80c2-099998d68f19	
69997416-0555-4600-82b9-0b43c24a046f	1	Variables & Data Types	What is a Variable?A variable is like a labeled box where you store a piece of information. In modern JavaScript, you create one using let or const.\r\n\r\nlet name = "Alex";\r\nlet age = 25;\r\nlet height = 5.9;\r\nlet isStudent = true;\r\n\r\n📝 Exercise\r\nCreate three variables:\r\n\r\n1. city — a string with the name of your favorite city\r\n2. population — a number representing its population (approximate is fine)\r\n3. isCapital — a boolean indicating whether it's a capital city	Remember: strings need quotes, numbers don't, and booleans are lowercase true/false.	0e8081ef-c020-4e07-b654-e07dd2ce3dbe	STEP 1 STARTER CODE\r\n\r\nconst name = "Awa";\r\nconst age = 24;\r\nconst height = 1.65;\r\nconst isStudent = true;\r\n\r\n// TODO: log each variable and its type
f978b31f-09c2-488c-9f62-8bb8166af58e	2	Variables & Data Types	What is a Variable?A variable is like a labeled box where you store a piece of information. In modern JavaScript, you create one using let or const.\r\n\r\nlet name = "Alex";\r\nlet age = 25;\r\nlet height = 5.9;\r\nlet isStudent = true;\r\n\r\n📝 Exercise\r\nCreate three variables:\r\n\r\n1. city — a string with the name of your favorite city\r\n2. population — a number representing its population (approximate is fine)\r\n3. isCapital — a boolean indicating whether it's a capital city	Remember: strings need quotes, numbers don't, and booleans are lowercase true/false.	0e8081ef-c020-4e07-b654-e07dd2ce3dbe	STEP 2 STARTER CODE\r\n\r\nconst name = "Awa";\r\nconst age = 24;\r\nconst height = 1.65;\r\nconst isStudent = true;\r\n\r\n// TODO: log each variable and its type
4faf02ba-e32d-49e8-9138-dd2dab019bc8	3	Variables & Data Types	What is a Variable?A variable is like a labeled box where you store a piece of information. In modern JavaScript, you create one using let or const.\r\n\r\nlet name = "Alex";\r\nlet age = 25;\r\nlet height = 5.9;\r\nlet isStudent = true;\r\n\r\n📝 Exercise\r\nCreate three variables:\r\n\r\n1. city — a string with the name of your favorite city\r\n2. population — a number representing its population (approximate is fine)\r\n3. isCapital — a boolean indicating whether it's a capital city	Remember: strings need quotes, numbers don't, and booleans are lowercase true/false.	0e8081ef-c020-4e07-b654-e07dd2ce3dbe	STEP 3 STARTER CODE\r\n\r\nconst name = "Awa";\r\nconst age = 24;\r\nconst height = 1.65;\r\nconst isStudent = true;\r\n\r\n// TODO: log each variable and its type
\.


--
-- Data for Name: lab_session; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.lab_session (id, user_id, lab_id, status, current_code, started_at, last_active_at, completed_at) FROM stdin;
5f38efd4-520f-4dfc-af52-6b69011de8ee	65e8ac6a-8738-4593-a97b-afee9d27bbd6	0e8081ef-c020-4e07-b654-e07dd2ce3dbe	active	# Write your Python code here\ndef greet(name):\n    print(f"Hello, {name} from Piston!")\n\ngreet("Developer")\n\n\n\n\n	2026-07-18 15:16:16.556474+00	2026-07-18 15:35:54.581431+00	\N
3b28c96a-0310-4344-89d2-003600cbfcbd	3968e9d3-32ef-405e-a398-ff3d812b2420	0e8081ef-c020-4e07-b654-e07dd2ce3dbe	completed	STEP 1 STARTER CODE\r\n\r\nconst name = "Awa";\r\nconst age = 24;\r\nconst height = 1.65;\r\nconst isStudent = true;\r\n\r\n// TODO: log each variable and its type	2026-07-16 13:07:37.768685+00	2026-08-21 09:47:40.117958+00	2026-08-19 08:22:45.322904+00
58c1f3ba-ad24-4b1d-882d-cf5208c05d76	2e9f7f57-d7ee-40ad-b80e-96b32e000424	0e8081ef-c020-4e07-b654-e07dd2ce3dbe	active	\N	2026-08-13 08:03:35.937312+00	2026-08-13 08:04:19.049684+00	\N
05cae733-ef60-465e-b873-09e8adadccc1	9d2fcad3-0f3d-4ff1-9195-61ecef7effba	0e8081ef-c020-4e07-b654-e07dd2ce3dbe	active	\N	2026-08-22 14:33:25.638779+00	2026-08-22 14:33:25.639269+00	\N
c3aa6a09-0308-44d1-af69-e32ae13263b1	3968e9d3-32ef-405e-a398-ff3d812b2420	22c18de9-ebf5-44f3-80c2-099998d68f19	completed		2026-08-13 07:11:40.893702+00	2026-08-19 09:04:15.083419+00	2026-08-19 08:30:10.931171+00
9f3762f1-dd02-44c1-b804-e6e2ebd47fb9	2e9f7f57-d7ee-40ad-b80e-96b32e000424	95879ffe-4b10-49a4-8e61-5777adb686f7	active	# Write your Python code here\ndef greet(name):\n    print(f"Hello, {name} from Piston!")\n\ngreet("Linda Developer")\n	2026-07-11 15:48:47.066905+00	2026-07-13 10:09:47.259415+00	\N
73188cbd-22a2-4f4b-a024-7dca5231311f	3968e9d3-32ef-405e-a398-ff3d812b2420	95879ffe-4b10-49a4-8e61-5777adb686f7	active	# Write your Python code here\ndef greet(name):\n    print(f"Hello, {name} from Piston!")\n\ngreet("Chima Developer")\n\n\n\n\n\n\n	2026-07-09 16:11:50.288283+00	2026-07-18 13:18:50.046051+00	2026-07-18 12:53:05.496483+00
\.


--
-- Data for Name: rate_limits; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.rate_limits (session_key, request_count, window_start) FROM stdin;
d7fe5f41-fc7c-409b-a09d-a29d5756e9ac	2	2026-06-27 12:32:13.214161+00
79624feb-06f8-4d9c-8e04-046992520eba	1	2026-07-02 18:16:23.305029+00
7a2dd0a4-b047-4bda-a881-758a5d6100d9	3	2026-07-04 14:47:25.100596+00
72f94667-4d07-45bc-b7db-ebf180ad893d	1	2026-07-09 10:47:24.660565+00
2e9f7f57-d7ee-40ad-b80e-96b32e000424	1	2026-07-11 15:50:42.356294+00
65e8ac6a-8738-4593-a97b-afee9d27bbd6	1	2026-07-18 15:34:24.877228+00
3968e9d3-32ef-405e-a398-ff3d812b2420	3	2026-08-17 15:46:11.268069+00
\.


--
-- Data for Name: user_progress; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.user_progress (id, user_id, lab_id, status, attempts, completed_at, seconds_practiced, completed_steps) FROM stdin;
51963578-11e6-437a-86c0-99b622170c9b	e3de2164-3fdb-53ba-a66c-d063b9180d77	00000000-0000-0000-0000-000000000001	in_progress	1	\N	0	0
76c55051-1076-4e2a-9861-ceef7d559305	d7fe5f41-fc7c-409b-a09d-a29d5756e9ac	00000000-0000-0000-0000-000000000001	in_progress	1	\N	0	0
5a9237f2-614c-4f55-81ee-c47d87ebabce	7a2dd0a4-b047-4bda-a881-758a5d6100d9	00000000-0000-0000-0000-000000000001	in_progress	1	\N	0	0
4a570e8b-634a-4e40-a3c0-ef75fc03486a	79624feb-06f8-4d9c-8e04-046992520eba	00000000-0000-0000-0000-000000000001	in_progress	1	\N	0	0
42d184da-a879-4b26-82e0-fcfdd1696410	72f94667-4d07-45bc-b7db-ebf180ad893d	00000000-0000-0000-0000-000000000001	in_progress	1	\N	0	0
5a0042d2-2c2a-40dd-96f1-ad2b4ec2c385	2e9f7f57-d7ee-40ad-b80e-96b32e000424	95879ffe-4b10-49a4-8e61-5777adb686f7	in_progress	1	\N	0	0
fade1f23-3f1b-45a0-9a18-7052d88ce5c7	3968e9d3-32ef-405e-a398-ff3d812b2420	95879ffe-4b10-49a4-8e61-5777adb686f7	in_progress	1	\N	0	0
965acb14-2c1d-414c-9124-42747e2efd02	65e8ac6a-8738-4593-a97b-afee9d27bbd6	0e8081ef-c020-4e07-b654-e07dd2ce3dbe	in_progress	1	\N	0	0
a8dbca0c-b852-4d3d-97e4-93ef32018d06	2e9f7f57-d7ee-40ad-b80e-96b32e000424	0e8081ef-c020-4e07-b654-e07dd2ce3dbe	in_progress	0	\N	0	0
129fa01c-2f04-47eb-b90b-7dedfe70e73d	3968e9d3-32ef-405e-a398-ff3d812b2420	0e8081ef-c020-4e07-b654-e07dd2ce3dbe	completed	0	2026-08-19 08:22:45.322904+00	7736	3
cc6203c8-d560-4bbc-962e-064516b56d5d	9d2fcad3-0f3d-4ff1-9195-61ecef7effba	0e8081ef-c020-4e07-b654-e07dd2ce3dbe	in_progress	1	\N	0	0
30390db4-744f-4cdd-905e-f289c0a1f0db	3968e9d3-32ef-405e-a398-ff3d812b2420	22c18de9-ebf5-44f3-80c2-099998d68f19	completed	0	2026-08-19 08:30:10.931171+00	2397	1
\.


--
-- PostgreSQL database dump complete
--

\unrestrict rqkcUxREgqjRZEQu5Y9hu2eRvsJfqnZerL7dTbITVrhmBSNQwMWczXtht4TEpvC


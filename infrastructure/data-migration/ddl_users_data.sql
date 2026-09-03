--
-- PostgreSQL database dump
--

\restrict uFf3ZrCOmA1b4XwGSmpzg9RLLDi5V8sH3wcHioVohDlsodeOUXB2EoIk37fc6h7

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
-- Data for Name: auth_group; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.auth_group (id, name) FROM stdin;
\.


--
-- Data for Name: auth_permission; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.auth_permission (id, name, content_type_id, codename) FROM stdin;
1	Can add content type	1	add_contenttype
2	Can change content type	1	change_contenttype
3	Can delete content type	1	delete_contenttype
4	Can view content type	1	view_contenttype
5	Can add permission	3	add_permission
6	Can change permission	3	change_permission
7	Can delete permission	3	delete_permission
8	Can view permission	3	view_permission
9	Can add group	2	add_group
10	Can change group	2	change_group
11	Can delete group	2	delete_group
12	Can view group	2	view_group
13	Can add user	4	add_user
14	Can change user	4	change_user
15	Can delete user	4	delete_user
16	Can view user	4	view_user
17	Can add lab session	5	add_labsession
18	Can change lab session	5	change_labsession
19	Can delete lab session	5	delete_labsession
20	Can view lab session	5	view_labsession
21	Can add rate limit	6	add_ratelimit
22	Can change rate limit	6	change_ratelimit
23	Can delete rate limit	6	delete_ratelimit
24	Can view rate limit	6	view_ratelimit
25	Can add user	7	add_user
26	Can change user	7	change_user
27	Can delete user	7	delete_user
28	Can view user	7	view_user
29	Can add lab	8	add_lab
30	Can change lab	8	change_lab
31	Can delete lab	8	delete_lab
32	Can view lab	8	view_lab
33	Can add log entry	9	add_logentry
34	Can change log entry	9	change_logentry
35	Can delete log entry	9	delete_logentry
36	Can view log entry	9	view_logentry
37	Can add session	10	add_session
38	Can change session	10	change_session
39	Can delete session	10	delete_session
40	Can view session	10	view_session
41	Can add lab objective	11	add_labobjective
42	Can change lab objective	11	change_labobjective
43	Can delete lab objective	11	delete_labobjective
44	Can view lab objective	11	view_labobjective
45	Can add user progress	12	add_userprogress
46	Can change user progress	12	change_userprogress
47	Can delete user progress	12	delete_userprogress
48	Can view user progress	12	view_userprogress
49	Can add skill	13	add_skill
50	Can change skill	13	change_skill
51	Can delete skill	13	delete_skill
52	Can view skill	13	view_skill
\.


--
-- Data for Name: auth_group_permissions; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.auth_group_permissions (id, group_id, permission_id) FROM stdin;
\.


--
-- Data for Name: users_user; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.users_user (password, last_login, is_superuser, id, full_name, display_name, bio, birth_date, city, country, language, role, email, phone, is_active, is_staff, date_joined) FROM stdin;
pbkdf2_sha256$1200000$Bx9FVflg0Gnxvw34UA8W5w$lkPdzZQsv1U7pO84miNGecGp5j2bgHYOo8sMZE5CXtQ=	\N	f	33d8d5a1-fb8b-4287-a9ee-7cb5f2ff825a	Phone User	\N	\N	\N	\N	\N	en	student	\N	+15551234567	t	f	2026-07-07 07:15:36.180193+00
pbkdf2_sha256$1200000$A1394xUOZgYr1DOPl3ntCA$QAVIHSudtx+miiWQH1Of7GOER5ECWMpyulwMimqiZxo=	\N	f	f63d4e0f-0b2c-4f04-8865-0667cf3f0702	Chimaobi Iwu	\N	\N	\N	\N	\N	en	student	chimaobi@test.com	\N	t	f	2026-07-07 07:49:55.465727+00
pbkdf2_sha256$1200000$N2anLRIJyMF7ctzttXtevA$5xZS7V0/pqoFeXJA9PyK2NyOR3vWRcPX615/g38zyGg=	\N	f	9cfd2c4d-6e99-456d-819d-79669e573ff0	Test User	\N	\N	\N	\N	\N	en	student	\N	+2348012345678	t	f	2026-07-07 07:52:45.937126+00
pbkdf2_sha256$1200000$hNR565EoSgx3ej26pkmj8v$8iddvFYTbr2rjLahk/0cyPrqkeOIIgGnmlDSTjBoaU4=	\N	f	bc573f21-ce05-44b3-9f8c-581efdf181a1	test name	\N	\N	\N	\N	\N	en	student	testname@gmail.com	08064159413	t	f	2026-07-07 14:09:52.200464+00
pbkdf2_sha256$1200000$b7APy26Y9Rj67QuMepdJpO$8W+J6nsHGFu8HaKBpuTBMvsgPZNInyROc9t/zkCnIDE=	\N	f	2e9f7f57-d7ee-40ad-b80e-96b32e000424	Archibong Eyo	\N	\N	\N	\N	\N	en	student	\N	080123456789	t	f	2026-07-11 15:43:35.65493+00
pbkdf2_sha256$1200000$9v7Qb2VeYOCTNzdlFydngt$r2nNY1c7K0QrOzRTTpj+qGcv8Q5ELQyc3/QzvipKkG4=	\N	f	65e8ac6a-8738-4593-a97b-afee9d27bbd6	Chimaobi Wisdom	\N	\N	\N	\N	\N	en	student	wiztherealist@gmail.com	\N	t	f	2026-07-18 15:12:29.016537+00
pbkdf2_sha256$1200000$11YN4Sklrve7Jybl4ZWR9p$ZVHbzaj0CJjhn9NwgERHYPTubAhKFzGqiXI1yHORDOU=	2026-08-25 21:43:57.788886+00	t	3968e9d3-32ef-405e-a398-ff3d812b2420	Chimaobi Ubani	Chimaobi	Cool Kid	\N	\N	\N	en	admin	wisdomchimaobi7@gmail.com	\N	t	t	2026-07-09 14:31:23.35066+00
pbkdf2_sha256$1200000$ZpDV2v3OevOOq3VQ4y66xj$8rPApzpV8ncjKwBcgEIQ/6DWCc71V5RfBmQBwocphIE=	\N	f	9d2fcad3-0f3d-4ff1-9195-61ecef7effba	Test User	Tester	Hello	\N	\N	\N	en	student	test@example.com	\N	f	f	2026-07-07 07:14:14.161272+00
pbkdf2_sha256$1200000$1ZyH0kMJ99egyF4wM2Llti$S/OJnemRWLCA2KIvQzct981r0HmuFMAYmes2No8Fd+k=	\N	f	6b1886d0-bf28-4bba-94b8-02dfc51fc6e7	Wisdom Ubani	Wisdom	\N	\N	\N	\N	en	student	Wiztherealist@gmail.com	+2348101793127	t	f	2026-08-26 11:59:45.889081+00
pbkdf2_sha256$1200000$ClInyIDoy0rOWpgZNSsB3l$68ESTcPpDhuh//0jm9+WDoWNJGHKddBHQpta5pxPe70=	\N	f	614a87d4-cf73-441c-a128-f816c8b62864	Wisdom Ubani	\N	\N	\N	\N	\N	en	student	cubani67@uniport.edu.ng	\N	t	f	2026-08-28 13:47:38.605016+00
pbkdf2_sha256$1200000$mA4loaDMdfSSz08NfxmHFJ$xwVYIwjexF0LFKkrqR62sLUyaQop7chgem/+AHYY6hA=	\N	f	b7839849-5e6b-4b24-8a1c-7ee7e078911f	Eve Will	Eve	\N	\N	\N	\N	en	student	Evewill394@gmail.com	\N	t	f	2026-08-29 12:35:45.812346+00
\.


--
-- Data for Name: users_user_groups; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.users_user_groups (id, user_id, group_id) FROM stdin;
\.


--
-- Data for Name: users_user_user_permissions; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.users_user_user_permissions (id, user_id, permission_id) FROM stdin;
\.


--
-- Name: auth_group_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.auth_group_id_seq', 1, false);


--
-- Name: auth_group_permissions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.auth_group_permissions_id_seq', 1, false);


--
-- Name: auth_permission_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.auth_permission_id_seq', 52, true);


--
-- Name: users_user_groups_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.users_user_groups_id_seq', 1, false);


--
-- Name: users_user_user_permissions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.users_user_user_permissions_id_seq', 1, false);


--
-- PostgreSQL database dump complete
--

\unrestrict uFf3ZrCOmA1b4XwGSmpzg9RLLDi5V8sH3wcHioVohDlsodeOUXB2EoIk37fc6h7


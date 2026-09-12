--
-- PostgreSQL database dump
--

\restrict L0OMWs37ZGegfrrLvsb73iidr5RDq02cdLLyJVFu0Qd9XCAVrfnmVrtSXxCO593

-- Dumped from database version 17.11
-- Dumped by pg_dump version 17.11

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

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


ALTER TABLE public.alembic_version OWNER TO postgres;

--
-- Name: assigned_type; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.assigned_type (
    assigned_type_id integer NOT NULL,
    name character varying(100) NOT NULL
);


ALTER TABLE public.assigned_type OWNER TO postgres;

--
-- Name: assigned_type_assigned_type_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.assigned_type_assigned_type_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.assigned_type_assigned_type_id_seq OWNER TO postgres;

--
-- Name: assigned_type_assigned_type_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.assigned_type_assigned_type_id_seq OWNED BY public.assigned_type.assigned_type_id;


--
-- Name: lead_arrival_rotation_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.lead_arrival_rotation_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.lead_arrival_rotation_seq OWNER TO postgres;

--
-- Name: lead_assignments; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.lead_assignments (
    id integer NOT NULL,
    lead_id integer NOT NULL,
    user_id integer NOT NULL,
    assigned_type_id integer NOT NULL,
    assigned_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    unassigned_at timestamp without time zone,
    comments text
);


ALTER TABLE public.lead_assignments OWNER TO postgres;

--
-- Name: lead_assignments_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.lead_assignments_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.lead_assignments_id_seq OWNER TO postgres;

--
-- Name: lead_assignments_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.lead_assignments_id_seq OWNED BY public.lead_assignments.id;


--
-- Name: leads; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.leads (
    lead_id integer NOT NULL,
    company character varying(255),
    name character varying(255),
    email character varying(255),
    phone character varying(100),
    source character varying(100),
    message text,
    campaign_id character varying(100),
    location character varying(255),
    priority_id integer,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    market_source_id integer,
    meta_leadgen_id text
);


ALTER TABLE public.leads OWNER TO postgres;

--
-- Name: leads_lead_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.leads_lead_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.leads_lead_id_seq OWNER TO postgres;

--
-- Name: leads_lead_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.leads_lead_id_seq OWNED BY public.leads.lead_id;


--
-- Name: market_sources; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.market_sources (
    market_source_id integer NOT NULL,
    name character varying(100) NOT NULL
);


ALTER TABLE public.market_sources OWNER TO postgres;

--
-- Name: market_sources_market_source_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.market_sources_market_source_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.market_sources_market_source_id_seq OWNER TO postgres;

--
-- Name: market_sources_market_source_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.market_sources_market_source_id_seq OWNED BY public.market_sources.market_source_id;


--
-- Name: market_types; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.market_types (
    market_type_id integer NOT NULL,
    name character varying(150) NOT NULL
);


ALTER TABLE public.market_types OWNER TO postgres;

--
-- Name: market_types_market_type_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.market_types_market_type_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.market_types_market_type_id_seq OWNER TO postgres;

--
-- Name: market_types_market_type_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.market_types_market_type_id_seq OWNED BY public.market_types.market_type_id;


--
-- Name: meta_leads; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.meta_leads (
    leadgen_id text NOT NULL,
    page_id text NOT NULL,
    form_id text NOT NULL,
    name text NOT NULL,
    phone text,
    email text,
    enquiry text,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


ALTER TABLE public.meta_leads OWNER TO postgres;

--
-- Name: notification_table; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.notification_table (
    n_id integer NOT NULL,
    sales_person_id integer NOT NULL,
    lead_id integer NOT NULL,
    created_datetime timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    title character varying(255),
    message text,
    type integer NOT NULL,
    is_read boolean DEFAULT false NOT NULL,
    read_at timestamp without time zone
);


ALTER TABLE public.notification_table OWNER TO postgres;

--
-- Name: notification_table_n_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.notification_table_n_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.notification_table_n_id_seq OWNER TO postgres;

--
-- Name: notification_table_n_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.notification_table_n_id_seq OWNED BY public.notification_table.n_id;


--
-- Name: notification_types; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.notification_types (
    id integer NOT NULL,
    name character varying(100) NOT NULL
);


ALTER TABLE public.notification_types OWNER TO postgres;

--
-- Name: notification_types_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.notification_types_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.notification_types_id_seq OWNER TO postgres;

--
-- Name: notification_types_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.notification_types_id_seq OWNED BY public.notification_types.id;


--
-- Name: priority; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.priority (
    priority_id integer NOT NULL,
    name character varying(100) NOT NULL
);


ALTER TABLE public.priority OWNER TO postgres;

--
-- Name: priority_priority_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.priority_priority_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.priority_priority_id_seq OWNER TO postgres;

--
-- Name: priority_priority_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.priority_priority_id_seq OWNED BY public.priority.priority_id;


--
-- Name: user_types; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.user_types (
    user_type_id integer NOT NULL,
    name character varying(100) NOT NULL
);


ALTER TABLE public.user_types OWNER TO postgres;

--
-- Name: user_types_user_type_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.user_types_user_type_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.user_types_user_type_id_seq OWNER TO postgres;

--
-- Name: user_types_user_type_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.user_types_user_type_id_seq OWNED BY public.user_types.user_type_id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.users (
    user_id integer NOT NULL,
    first_name character varying(100) NOT NULL,
    last_name character varying(100),
    email character varying(100) NOT NULL,
    phone character varying(100),
    password text NOT NULL,
    user_type_id integer NOT NULL,
    status integer DEFAULT 1 NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    created_by integer,
    updated_by integer
);


ALTER TABLE public.users OWNER TO postgres;

--
-- Name: users_user_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.users_user_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.users_user_id_seq OWNER TO postgres;

--
-- Name: users_user_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.users_user_id_seq OWNED BY public.users.user_id;


--
-- Name: assigned_type assigned_type_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.assigned_type ALTER COLUMN assigned_type_id SET DEFAULT nextval('public.assigned_type_assigned_type_id_seq'::regclass);


--
-- Name: lead_assignments id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.lead_assignments ALTER COLUMN id SET DEFAULT nextval('public.lead_assignments_id_seq'::regclass);


--
-- Name: leads lead_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.leads ALTER COLUMN lead_id SET DEFAULT nextval('public.leads_lead_id_seq'::regclass);


--
-- Name: market_sources market_source_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.market_sources ALTER COLUMN market_source_id SET DEFAULT nextval('public.market_sources_market_source_id_seq'::regclass);


--
-- Name: market_types market_type_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.market_types ALTER COLUMN market_type_id SET DEFAULT nextval('public.market_types_market_type_id_seq'::regclass);


--
-- Name: notification_table n_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.notification_table ALTER COLUMN n_id SET DEFAULT nextval('public.notification_table_n_id_seq'::regclass);


--
-- Name: notification_types id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.notification_types ALTER COLUMN id SET DEFAULT nextval('public.notification_types_id_seq'::regclass);


--
-- Name: priority priority_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.priority ALTER COLUMN priority_id SET DEFAULT nextval('public.priority_priority_id_seq'::regclass);


--
-- Name: user_types user_type_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_types ALTER COLUMN user_type_id SET DEFAULT nextval('public.user_types_user_type_id_seq'::regclass);


--
-- Name: users user_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users ALTER COLUMN user_id SET DEFAULT nextval('public.users_user_id_seq'::regclass);


--
-- Data for Name: alembic_version; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.alembic_version (version_num) FROM stdin;
20260907_04
\.


--
-- Data for Name: assigned_type; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.assigned_type (assigned_type_id, name) FROM stdin;
1	MANUAL
2	ROUND ROBIN
3	RULE BASED
4	AI
\.


--
-- Data for Name: lead_assignments; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.lead_assignments (id, lead_id, user_id, assigned_type_id, assigned_at, unassigned_at, comments) FROM stdin;
1	2	2	2	2026-09-10 14:31:16.853406	\N	\N
68	69	2	2	2026-09-12 11:08:28.636111	\N	\N
69	70	2	2	2026-09-12 11:08:28.790603	\N	\N
70	71	2	2	2026-09-12 11:08:28.889739	\N	\N
71	72	2	2	2026-09-12 11:08:28.989774	\N	\N
72	73	9	2	2026-09-12 11:08:29.105955	\N	\N
73	74	9	2	2026-09-12 11:08:29.222859	\N	\N
74	75	9	2	2026-09-12 11:08:29.320808	\N	\N
75	76	9	2	2026-09-12 11:08:29.432102	\N	\N
76	77	10	2	2026-09-12 11:08:29.546795	\N	\N
48	49	2	2	2026-09-11 17:07:21.867923	\N	\N
\.


--
-- Data for Name: leads; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.leads (lead_id, company, name, email, phone, source, message, campaign_id, location, priority_id, created_at, updated_at, market_source_id, meta_leadgen_id) FROM stdin;
1	\N	Sajila Test	sajilaanil@gmail.com	9995146157	WhatsApp	\N	\N	\N	\N	2026-09-09 06:19:34.933507	2026-09-09 06:19:34.933507	4	TEST123
2	\N	Sajila Test	sajilaanil@gmail.com	9995146157	WhatsApp	\N	\N	\N	\N	2026-09-10 09:01:16.718503	2026-09-10 09:01:16.718503	4	TEST124
69	\N	Test Lead One	lead001@example.com	9995000001	WhatsApp	\N	\N	\N	\N	2026-09-12 05:38:28.480966	2026-09-12 05:38:28.480966	4	TEST001
70	\N	Test Lead Two	lead002@example.com	9995000002	WhatsApp	\N	\N	\N	\N	2026-09-12 05:38:28.710257	2026-09-12 05:38:28.710257	4	TEST002
71	\N	Test Lead Three	lead003@example.com	9995000003	WhatsApp	\N	\N	\N	\N	2026-09-12 05:38:28.821136	2026-09-12 05:38:28.821136	4	TEST003
72	\N	Test Lead Four	lead004@example.com	9995000004	WhatsApp	\N	\N	\N	\N	2026-09-12 05:38:28.922858	2026-09-12 05:38:28.922858	4	TEST004
73	\N	Test Lead Five	lead005@example.com	9995000005	WhatsApp	\N	\N	\N	\N	2026-09-12 05:38:29.021325	2026-09-12 05:38:29.021325	4	TEST005
74	\N	Test Lead Six	lead006@example.com	9995000006	WhatsApp	\N	\N	\N	\N	2026-09-12 05:38:29.141179	2026-09-12 05:38:29.141179	4	TEST006
75	\N	Test Lead Seven	lead007@example.com	9995000007	WhatsApp	\N	\N	\N	\N	2026-09-12 05:38:29.253458	2026-09-12 05:38:29.253458	4	TEST007
76	\N	Test Lead Eight	lead008@example.com	9995000008	WhatsApp	\N	\N	\N	\N	2026-09-12 05:38:29.35305	2026-09-12 05:38:29.35305	4	TEST008
77	\N	Test Lead Nine	lead009@example.com	9995000009	WhatsApp	\N	\N	\N	\N	2026-09-12 05:38:29.467093	2026-09-12 05:38:29.467093	4	TEST009
49	\N	Trace Lead	trace@example.com	1234567890	WhatsApp	\N	\N	\N	\N	2026-09-11 11:37:21.657513	2026-09-11 11:37:21.657513	4	TRACE001
\.


--
-- Data for Name: market_sources; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.market_sources (market_source_id, name) FROM stdin;
1	Meta Ads
2	Google Ads
3	Website forms
4	WhatsApp
5	Instagram
6	Email
7	Manual Lead imports
\.


--
-- Data for Name: market_types; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.market_types (market_type_id, name) FROM stdin;
1	Real Estate Companies
2	Educational Institutions
3	Digital Marketing Agencies
4	Dental Clinics
5	Hospitals and Clinics
6	Automobile Dealers
7	Construction Companies
8	Interior Design Companies
9	Solar Companies
10	Travel Agencies
11	Insurance Agencies
12	B2B Companies
13	E-commerce Businesses
\.


--
-- Data for Name: meta_leads; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.meta_leads (leadgen_id, page_id, form_id, name, phone, email, enquiry, created_at) FROM stdin;
1400475425563232	1300823233119934	1058304700329276	<test lead: dummy data for FULL_NAME>	<test lead: dummy data for PHONE>	test@meta.com	<test lead: dummy data for 0>	2026-09-04 09:50:35.299803+05:30
\.


--
-- Data for Name: notification_table; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.notification_table (n_id, sales_person_id, lead_id, created_datetime, title, message, type, is_read, read_at) FROM stdin;
1	2	2	2026-09-10 14:31:16.853406	New Lead Assigned	You have 3 new leads assigned to you.	1	f	\N
26	2	69	2026-09-12 11:08:28.636111	New Lead Assigned	You have 1 new lead assigned to you.	1	f	\N
27	2	70	2026-09-12 11:08:28.790603	New Lead Assigned	You have 1 new lead assigned to you.	1	f	\N
28	2	71	2026-09-12 11:08:28.889739	New Lead Assigned	You have 1 new lead assigned to you.	1	f	\N
29	2	72	2026-09-12 11:08:28.989774	New Lead Assigned	You have 1 new lead assigned to you.	1	f	\N
30	9	73	2026-09-12 11:08:29.105955	New Lead Assigned	You have 1 new lead assigned to you.	1	f	\N
31	9	74	2026-09-12 11:08:29.222859	New Lead Assigned	You have 1 new lead assigned to you.	1	f	\N
32	9	75	2026-09-12 11:08:29.320808	New Lead Assigned	You have 1 new lead assigned to you.	1	f	\N
33	9	76	2026-09-12 11:08:29.432102	New Lead Assigned	You have 1 new lead assigned to you.	1	f	\N
34	10	77	2026-09-12 11:08:29.546795	New Lead Assigned	You have 1 new lead assigned to you.	1	f	\N
17	2	49	2026-09-11 17:07:21.867923	New Lead Assigned	You have 1 new lead assigned to you.	1	f	\N
\.


--
-- Data for Name: notification_types; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.notification_types (id, name) FROM stdin;
1	lead_assigned
2	follo_up
3	task_assigned
\.


--
-- Data for Name: priority; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.priority (priority_id, name) FROM stdin;
1	HOT
2	WARM
3	COLD
\.


--
-- Data for Name: user_types; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.user_types (user_type_id, name) FROM stdin;
1	ADMIN
2	BUSINESS_MANAGER
3	SALES_AGENT
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.users (user_id, first_name, last_name, email, phone, password, user_type_id, status, created_at, updated_at, created_by, updated_by) FROM stdin;
4	Basheer	K	basheerk@gmail.com	8606542812	$argon2id$v=19$m=65536,t=3,p=4$8yCDjYbqy+lgyi/m7gQYug$SRe60nMmL9/NOA3zLXd/a0Jn3sx153v9iNZgmi3xqvQ	3	0	2026-09-08 06:39:01.241092	2026-09-08 14:00:08.880377	1	1
6	Alfas	U	alfasussainar2001@gmail.com	9809577803	$argon2id$v=19$m=65536,t=3,p=4$dwz6jPcyyJT2DeZvjoFMmw$ClzszlUSWkH6wDSfZxoZO7EHnsqjc8fULnidFaz6B7s	3	0	2026-09-08 06:43:57.777074	2026-09-08 14:46:39.091005	1	1
7	rifa	k	ayisharifa@gmail.com	8075937241	$argon2id$v=19$m=65536,t=3,p=4$8Fg23FngAqgXJDiYYeCLJA$gMOtSDrnME5HsrAPEOrn28F6QptEbZNRgvFLvCMo9iQ	3	0	2026-09-08 06:45:05.202999	2026-09-08 14:46:51.000988	1	1
5	Jaseena	P	jaseenajasi@gamil.com	9562457626	$argon2id$v=19$m=65536,t=3,p=4$dP8dEWMPnn8HjIKZA8p4cw$MrAKqBWqCzOG1JHyNmroIS2YwAryiLR9xEey9dz+LiE	3	0	2026-09-08 06:42:26.905166	2026-09-08 14:46:58.945427	1	1
8	rifa	k	ayisharifak@gamil.com	9562457626	$argon2id$v=19$m=65536,t=3,p=4$ASG8JR1/ESKbJcol/D3F2Q$oqFKwqwFuSN9lkiieU0PZ90BLBNmwIyCrSBYALMjOeY	3	0	2026-09-08 14:49:51.180017	2026-09-08 14:53:19.386133	1	1
9	rifa	k	rifak123@gmail.com	9562457626	$argon2id$v=19$m=65536,t=3,p=4$NxT3ANeKbRik+jIqPnEAQA$Z+UNENQE4lYcwm5uwDe20sJv3qqtIM502F/M8nhy6xg	3	1	2026-09-08 14:54:57.118606	2026-09-08 14:54:57.118606	1	1
2	Fida	K	fathimathfidak849@gmail.com	9567891905	$argon2id$v=19$m=65536,t=3,p=4$BwoYe/BdxiC0yjiyqatl8A$gFS3arVJAnMB3opsjCLmSCkhH3NFOkwW0sYw6BIrFvQ	3	1	2026-09-07 05:06:54.426943	2026-09-08 15:02:27.017266	1	1
10	fiza	k	fathimafiza@gmail.com	8606542812	$argon2id$v=19$m=65536,t=3,p=4$Fg4iSJFjEGJzGMTIcdJl8w$PKkTuQ9nWDCh+dYb9LSEPEBT5QViVObaI+qEBd1AKV8	3	1	2026-09-08 15:03:09.773785	2026-09-08 15:03:09.773785	1	1
1	Admin	User	admin@example.com	9744822101	$argon2id$v=19$m=65536,t=3,p=4$nWrLy9GAM+0G4B2LTlVwBw$ciKb7sDIpC0f1zAII+mVg7b9oD+W5Tp70YMGLGzzmzk	1	1	2026-09-05 10:08:15.796801	2026-09-08 15:04:09.57899	\N	1
\.


--
-- Name: assigned_type_assigned_type_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.assigned_type_assigned_type_id_seq', 1, false);


--
-- Name: lead_arrival_rotation_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.lead_arrival_rotation_seq', 9, true);


--
-- Name: lead_assignments_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.lead_assignments_id_seq', 76, true);


--
-- Name: leads_lead_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.leads_lead_id_seq', 77, true);


--
-- Name: market_sources_market_source_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.market_sources_market_source_id_seq', 1, false);


--
-- Name: market_types_market_type_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.market_types_market_type_id_seq', 1, false);


--
-- Name: notification_table_n_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.notification_table_n_id_seq', 34, true);


--
-- Name: notification_types_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.notification_types_id_seq', 1, false);


--
-- Name: priority_priority_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.priority_priority_id_seq', 1, false);


--
-- Name: user_types_user_type_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.user_types_user_type_id_seq', 1, false);


--
-- Name: users_user_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.users_user_id_seq', 10, true);


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: assigned_type assigned_type_name_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.assigned_type
    ADD CONSTRAINT assigned_type_name_key UNIQUE (name);


--
-- Name: assigned_type assigned_type_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.assigned_type
    ADD CONSTRAINT assigned_type_pkey PRIMARY KEY (assigned_type_id);


--
-- Name: lead_assignments lead_assignments_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.lead_assignments
    ADD CONSTRAINT lead_assignments_pkey PRIMARY KEY (id);


--
-- Name: leads leads_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.leads
    ADD CONSTRAINT leads_pkey PRIMARY KEY (lead_id);


--
-- Name: market_sources market_sources_name_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.market_sources
    ADD CONSTRAINT market_sources_name_key UNIQUE (name);


--
-- Name: market_sources market_sources_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.market_sources
    ADD CONSTRAINT market_sources_pkey PRIMARY KEY (market_source_id);


--
-- Name: market_types market_types_name_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.market_types
    ADD CONSTRAINT market_types_name_key UNIQUE (name);


--
-- Name: market_types market_types_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.market_types
    ADD CONSTRAINT market_types_pkey PRIMARY KEY (market_type_id);


--
-- Name: meta_leads meta_leads_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.meta_leads
    ADD CONSTRAINT meta_leads_pkey PRIMARY KEY (leadgen_id);


--
-- Name: notification_table notification_table_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.notification_table
    ADD CONSTRAINT notification_table_pkey PRIMARY KEY (n_id);


--
-- Name: notification_types notification_types_name_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.notification_types
    ADD CONSTRAINT notification_types_name_key UNIQUE (name);


--
-- Name: notification_types notification_types_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.notification_types
    ADD CONSTRAINT notification_types_pkey PRIMARY KEY (id);


--
-- Name: priority priority_name_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.priority
    ADD CONSTRAINT priority_name_key UNIQUE (name);


--
-- Name: priority priority_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.priority
    ADD CONSTRAINT priority_pkey PRIMARY KEY (priority_id);


--
-- Name: leads uq_leads_meta_leadgen_id; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.leads
    ADD CONSTRAINT uq_leads_meta_leadgen_id UNIQUE (meta_leadgen_id);


--
-- Name: user_types user_types_name_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_types
    ADD CONSTRAINT user_types_name_key UNIQUE (name);


--
-- Name: user_types user_types_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_types
    ADD CONSTRAINT user_types_pkey PRIMARY KEY (user_type_id);


--
-- Name: users users_email_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_email_key UNIQUE (email);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (user_id);


--
-- Name: lead_assignments fk_lead_assignments_lead; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.lead_assignments
    ADD CONSTRAINT fk_lead_assignments_lead FOREIGN KEY (lead_id) REFERENCES public.leads(lead_id);


--
-- Name: lead_assignments fk_lead_assignments_type; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.lead_assignments
    ADD CONSTRAINT fk_lead_assignments_type FOREIGN KEY (assigned_type_id) REFERENCES public.assigned_type(assigned_type_id);


--
-- Name: lead_assignments fk_lead_assignments_user; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.lead_assignments
    ADD CONSTRAINT fk_lead_assignments_user FOREIGN KEY (user_id) REFERENCES public.users(user_id);


--
-- Name: leads fk_leads_market_source_id_market_sources; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.leads
    ADD CONSTRAINT fk_leads_market_source_id_market_sources FOREIGN KEY (market_source_id) REFERENCES public.market_sources(market_source_id);


--
-- Name: leads fk_leads_priority; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.leads
    ADD CONSTRAINT fk_leads_priority FOREIGN KEY (priority_id) REFERENCES public.priority(priority_id);


--
-- Name: notification_table fk_notification_lead; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.notification_table
    ADD CONSTRAINT fk_notification_lead FOREIGN KEY (lead_id) REFERENCES public.leads(lead_id);


--
-- Name: notification_table fk_notification_sales_person; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.notification_table
    ADD CONSTRAINT fk_notification_sales_person FOREIGN KEY (sales_person_id) REFERENCES public.users(user_id);


--
-- Name: notification_table fk_notification_type; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.notification_table
    ADD CONSTRAINT fk_notification_type FOREIGN KEY (type) REFERENCES public.notification_types(id);


--
-- Name: users fk_users_created_by; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT fk_users_created_by FOREIGN KEY (created_by) REFERENCES public.users(user_id);


--
-- Name: users fk_users_updated_by; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT fk_users_updated_by FOREIGN KEY (updated_by) REFERENCES public.users(user_id);


--
-- Name: users fk_users_user_type; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT fk_users_user_type FOREIGN KEY (user_type_id) REFERENCES public.user_types(user_type_id);


--
-- PostgreSQL database dump complete
--

\unrestrict L0OMWs37ZGegfrrLvsb73iidr5RDq02cdLLyJVFu0Qd9XCAVrfnmVrtSXxCO593


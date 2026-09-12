--
-- PostgreSQL database dump
--

\restrict QvJlPcRubuWfCfK4rNFn61IetFcMb9u3kgSPpU1fRAoMX55Y5viVTEZqvTp9FEg

-- Dumped from database version 17.11
-- Dumped by pg_dump version 17.11

-- Started on 2026-09-07 22:04:14

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
-- TOC entry 219 (class 1259 OID 32779)
-- Name: user_types; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.user_types (
    user_type_id integer NOT NULL,
    name character varying(100) NOT NULL
);


ALTER TABLE public.user_types OWNER TO postgres;

--
-- TOC entry 218 (class 1259 OID 32778)
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
-- TOC entry 4831 (class 0 OID 0)
-- Dependencies: 218
-- Name: user_types_user_type_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.user_types_user_type_id_seq OWNED BY public.user_types.user_type_id;


--
-- TOC entry 4674 (class 2604 OID 32782)
-- Name: user_types user_type_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_types ALTER COLUMN user_type_id SET DEFAULT nextval('public.user_types_user_type_id_seq'::regclass);


--
-- TOC entry 4825 (class 0 OID 32779)
-- Dependencies: 219
-- Data for Name: user_types; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.user_types (user_type_id, name) FROM stdin;
1	ADMIN
2	BUSINESS_MANAGER
3	SALES_AGENT
\.


--
-- TOC entry 4832 (class 0 OID 0)
-- Dependencies: 218
-- Name: user_types_user_type_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.user_types_user_type_id_seq', 1, false);


--
-- TOC entry 4676 (class 2606 OID 32786)
-- Name: user_types user_types_name_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_types
    ADD CONSTRAINT user_types_name_key UNIQUE (name);


--
-- TOC entry 4678 (class 2606 OID 32784)
-- Name: user_types user_types_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_types
    ADD CONSTRAINT user_types_pkey PRIMARY KEY (user_type_id);


-- Completed on 2026-09-07 22:04:14

--
-- PostgreSQL database dump complete
--

\unrestrict QvJlPcRubuWfCfK4rNFn61IetFcMb9u3kgSPpU1fRAoMX55Y5viVTEZqvTp9FEg


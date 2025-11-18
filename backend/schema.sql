-- WARNING: This schema is for context only and is not meant to be run.
-- Table order and constraints may not be valid for execution.

CREATE TABLE public.alerts (
  id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
  media_id bigint NOT NULL,
  type text NOT NULL,
  severite text NOT NULL CHECK (severite = ANY (ARRAY['critical'::text, 'high'::text, 'medium'::text, 'low'::text])),
  titre text NOT NULL,
  message text,
  date timestamp with time zone DEFAULT now(),
  is_resolved boolean DEFAULT false,
  created_at timestamp with time zone DEFAULT now(),
  CONSTRAINT alerts_pkey PRIMARY KEY (id),
  CONSTRAINT alerts_media_id_fkey FOREIGN KEY (media_id) REFERENCES public.medias(id)
);
CREATE TABLE public.articles (
  id text NOT NULL,
  media_id bigint NOT NULL,
  categorie_id bigint,
  titre text NOT NULL,
  contenu text,
  url text,
  date timestamp with time zone,
  created_at timestamp with time zone DEFAULT now(),
  CONSTRAINT articles_pkey PRIMARY KEY (id),
  CONSTRAINT articles_media_id_fkey FOREIGN KEY (media_id) REFERENCES public.medias(id),
  CONSTRAINT articles_categorie_id_fkey FOREIGN KEY (categorie_id) REFERENCES public.categories(id)
);
CREATE TABLE public.categories (
  id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
  nom text NOT NULL UNIQUE,
  couleur text DEFAULT '#6B7280'::text,
  created_at timestamp with time zone DEFAULT now(),
  CONSTRAINT categories_pkey PRIMARY KEY (id)
);
CREATE TABLE public.engagements (
  id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
  likes integer DEFAULT 0,
  commentaires integer DEFAULT 0,
  partages integer DEFAULT 0,
  type_source text,
  plateforme text,
  created_at timestamp with time zone DEFAULT now(),
  article_id text NOT NULL UNIQUE,
  commentaire_text jsonb,
  CONSTRAINT engagements_pkey PRIMARY KEY (id),
  CONSTRAINT engagements_article_id_fkey FOREIGN KEY (article_id) REFERENCES public.articles(id)
);
CREATE TABLE public.media_stats (
  id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
  media_id bigint NOT NULL,
  date date NOT NULL,
  total_articles integer DEFAULT 0,
  total_likes integer DEFAULT 0,
  total_commentaires integer DEFAULT 0,
  total_partages integer DEFAULT 0,
  total_engagement integer DEFAULT 0,
  influence_score numeric DEFAULT 0.0,
  created_at timestamp with time zone DEFAULT now(),
  CONSTRAINT media_stats_pkey PRIMARY KEY (id),
  CONSTRAINT media_stats_media_id_fkey FOREIGN KEY (media_id) REFERENCES public.medias(id)
);
CREATE TABLE public.medias (
  id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
  name text NOT NULL UNIQUE,
  type text CHECK (type = ANY (ARRAY['web'::text, 'social_media'::text])),
  couleur text DEFAULT '#3B82F6'::text,
  icon text,
  is_active boolean DEFAULT true,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  facebook_id text,
  followers integer DEFAULT 0,
  email text,
  phone text,
  website text,
  rating numeric,
  rating_count integer DEFAULT 0,
  address text,
  profile_photo_url text,
  facebook_url text,
  intro text,
  page_name text,
  creation_date date,
  CONSTRAINT medias_pkey PRIMARY KEY (id)
);
CREATE TABLE public.scraping_logs (
  id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
  started_at timestamp with time zone NOT NULL,
  completed_at timestamp with time zone,
  duration_seconds integer,
  status text NOT NULL CHECK (status = ANY (ARRAY['running'::text, 'completed'::text, 'failed'::text])),
  total_scraped integer DEFAULT 0,
  total_inserted integer DEFAULT 0,
  total_skipped integer DEFAULT 0,
  total_errors integer DEFAULT 0,
  error_message text,
  details jsonb,
  created_at timestamp with time zone DEFAULT now(),
  CONSTRAINT scraping_logs_pkey PRIMARY KEY (id)
);
CREATE TABLE public.scraping_media_details (
  id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
  scraping_log_id bigint NOT NULL,
  media_id bigint NOT NULL,
  articles_scraped integer DEFAULT 0,
  articles_inserted integer DEFAULT 0,
  articles_skipped integer DEFAULT 0,
  last_article_date timestamp with time zone,
  created_at timestamp with time zone DEFAULT now(),
  CONSTRAINT scraping_media_details_pkey PRIMARY KEY (id),
  CONSTRAINT scraping_media_details_scraping_log_id_fkey FOREIGN KEY (scraping_log_id) REFERENCES public.scraping_logs(id),
  CONSTRAINT scraping_media_details_media_id_fkey FOREIGN KEY (media_id) REFERENCES public.medias(id)
);
CREATE TABLE public.users (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  nom text,
  prenom text,
  role text NOT NULL DEFAULT 'user'::text CHECK (role = ANY (ARRAY['user'::text, 'admin'::text])),
  telephone text,
  actif boolean DEFAULT true,
  updated_at timestamp with time zone DEFAULT now(),
  derniere_connexion timestamp with time zone,
  email text UNIQUE,
  password_hash text,
  created_at timestamp with time zone DEFAULT now(),
  CONSTRAINT users_pkey PRIMARY KEY (id)
);
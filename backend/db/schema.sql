CREATE EXTENSION IF NOT EXISTS "uuid-ossp";


CREATE TABLE IF NOT EXISTS public.users (
    user_id         uuid PRIMARY KEY REFERENCES auth.users ON DELETE CASCADE,
    email           text NOT NULL,
    display_name    text,
    created_at      timestamptz NOT NULL DEFAULT now(),
    debate_count    integer NOT NULL DEFAULT 0,
    last_active     timestamptz
);

ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;

CREATE POLICY "users_select_own"
    ON public.users FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "users_update_own"
    ON public.users FOR UPDATE
    USING (auth.uid() = user_id);

CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER AS $$
BEGIN
    INSERT INTO public.users (user_id, email, display_name)
    VALUES (
        NEW.id,
        NEW.email,
        COALESCE(NEW.raw_user_meta_data->>'display_name', split_part(NEW.email, '@', 1))
    )
    ON CONFLICT (user_id) DO NOTHING;
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();


CREATE TABLE IF NOT EXISTS public.sessions (
    session_id      uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         uuid NOT NULL REFERENCES public.users ON DELETE CASCADE,
    created_at      timestamptz NOT NULL DEFAULT now(),
    last_seen       timestamptz NOT NULL DEFAULT now(),
    device_info     jsonb
);

ALTER TABLE public.sessions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "sessions_select_own"
    ON public.sessions FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "sessions_insert_own"
    ON public.sessions FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "sessions_delete_own"
    ON public.sessions FOR DELETE
    USING (auth.uid() = user_id);


CREATE TABLE IF NOT EXISTS public.debates (
    debate_id       uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         uuid NOT NULL REFERENCES public.users ON DELETE CASCADE,
    topic           text NOT NULL,
    status          text NOT NULL DEFAULT 'running'
                        CHECK (status IN ('running', 'completed', 'failed', 'disconnected')),
    created_at      timestamptz NOT NULL DEFAULT now(),
    completed_at    timestamptz,
    total_rounds    integer,
    winner          text,
    quality_score   float
);

ALTER TABLE public.debates ENABLE ROW LEVEL SECURITY;

CREATE POLICY "debates_select_own"
    ON public.debates FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "debates_insert_own"
    ON public.debates FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "debates_update_own"
    ON public.debates FOR UPDATE
    USING (auth.uid() = user_id);


CREATE TABLE IF NOT EXISTS public.sub_debates (
    sub_debate_id   uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    debate_id       uuid NOT NULL REFERENCES public.debates ON DELETE CASCADE,
    sub_topic       text NOT NULL,
    stance_a        text,
    stance_b        text,
    rounds_run      integer NOT NULL DEFAULT 0,
    winner          text,
    final_score_a   float,
    final_score_b   float
);

ALTER TABLE public.sub_debates ENABLE ROW LEVEL SECURITY;

CREATE POLICY "sub_debates_select_own"
    ON public.sub_debates FOR SELECT
    USING (
        debate_id IN (SELECT debate_id FROM public.debates WHERE user_id = auth.uid())
    );

CREATE POLICY "sub_debates_insert_own"
    ON public.sub_debates FOR INSERT
    WITH CHECK (
        debate_id IN (SELECT debate_id FROM public.debates WHERE user_id = auth.uid())
    );

CREATE POLICY "sub_debates_update_own"
    ON public.sub_debates FOR UPDATE
    USING (
        debate_id IN (SELECT debate_id FROM public.debates WHERE user_id = auth.uid())
    );


CREATE TABLE IF NOT EXISTS public.rounds (
    round_id            uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    sub_debate_id       uuid NOT NULL REFERENCES public.sub_debates ON DELETE CASCADE,
    round_number        integer NOT NULL,
    argument_a          text,
    argument_b          text,
    score_a             float,
    score_b             float,
    bias_flags          jsonb,
    fact_check_results  jsonb,
    rubric_version      integer,
    audience_reaction   text,
    judge_reasoning     jsonb,
    UNIQUE (sub_debate_id, round_number)
);

ALTER TABLE public.rounds ENABLE ROW LEVEL SECURITY;

CREATE POLICY "rounds_select_own"
    ON public.rounds FOR SELECT
    USING (
        sub_debate_id IN (
            SELECT sd.sub_debate_id FROM public.sub_debates sd
            JOIN public.debates d ON d.debate_id = sd.debate_id
            WHERE d.user_id = auth.uid()
        )
    );

CREATE POLICY "rounds_insert_own"
    ON public.rounds FOR INSERT
    WITH CHECK (
        sub_debate_id IN (
            SELECT sd.sub_debate_id FROM public.sub_debates sd
            JOIN public.debates d ON d.debate_id = sd.debate_id
            WHERE d.user_id = auth.uid()
        )
    );


CREATE TABLE IF NOT EXISTS public.rubric_versions (
    version_id          uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    debate_id           uuid NOT NULL REFERENCES public.debates ON DELETE CASCADE,
    version_number      integer NOT NULL,
    rubric_json         jsonb NOT NULL,
    created_at          timestamptz NOT NULL DEFAULT now(),
    critic_reasoning    text,
    UNIQUE (debate_id, version_number)
);

ALTER TABLE public.rubric_versions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "rubric_versions_select_own"
    ON public.rubric_versions FOR SELECT
    USING (
        debate_id IN (SELECT debate_id FROM public.debates WHERE user_id = auth.uid())
    );

CREATE POLICY "rubric_versions_insert_own"
    ON public.rubric_versions FOR INSERT
    WITH CHECK (
        debate_id IN (SELECT debate_id FROM public.debates WHERE user_id = auth.uid())
    );


CREATE TABLE IF NOT EXISTS public.reports (
    report_id       uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    debate_id       uuid NOT NULL REFERENCES public.debates ON DELETE CASCADE,
    user_id         uuid NOT NULL REFERENCES public.users ON DELETE CASCADE,
    pdf_url         text,
    json_url        text,
    markdown_url    text,
    created_at      timestamptz NOT NULL DEFAULT now()
);

ALTER TABLE public.reports ENABLE ROW LEVEL SECURITY;

CREATE POLICY "reports_select_own"
    ON public.reports FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "reports_insert_own"
    ON public.reports FOR INSERT
    WITH CHECK (auth.uid() = user_id);


CREATE TABLE IF NOT EXISTS public.rate_limits (
    user_id                 uuid PRIMARY KEY REFERENCES public.users ON DELETE CASCADE,
    debates_this_hour       integer NOT NULL DEFAULT 0,
    debates_today           integer NOT NULL DEFAULT 0,
    last_reset_hour         timestamptz NOT NULL DEFAULT now(),
    last_reset_day          timestamptz NOT NULL DEFAULT now()
);

ALTER TABLE public.rate_limits ENABLE ROW LEVEL SECURITY;

CREATE POLICY "rate_limits_select_own"
    ON public.rate_limits FOR SELECT
    USING (auth.uid() = user_id);


CREATE TABLE IF NOT EXISTS public.checkpoints (
    debate_id       uuid NOT NULL REFERENCES public.debates ON DELETE CASCADE,
    sub_debate_id   uuid NOT NULL REFERENCES public.sub_debates ON DELETE CASCADE,
    round_number    integer NOT NULL,
    state_json      jsonb NOT NULL,
    saved_at        timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (debate_id, round_number)
);

ALTER TABLE public.checkpoints ENABLE ROW LEVEL SECURITY;

CREATE POLICY "checkpoints_select_own"
    ON public.checkpoints FOR SELECT
    USING (
        debate_id IN (SELECT debate_id FROM public.debates WHERE user_id = auth.uid())
    );


CREATE INDEX IF NOT EXISTS idx_debates_user_id ON public.debates (user_id);
CREATE INDEX IF NOT EXISTS idx_debates_status ON public.debates (status);
CREATE INDEX IF NOT EXISTS idx_sub_debates_debate_id ON public.sub_debates (debate_id);
CREATE INDEX IF NOT EXISTS idx_rounds_sub_debate_id ON public.rounds (sub_debate_id);
CREATE INDEX IF NOT EXISTS idx_reports_user_id ON public.reports (user_id);
CREATE INDEX IF NOT EXISTS idx_checkpoints_debate_id ON public.checkpoints (debate_id);
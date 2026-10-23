-- RetailGrowthAI Part 2 — social publishing persistence (SOURCE ONLY).
-- DO NOT apply on hosted Supabase without separate explicit approval.
-- Preserves all Part 1 tables, quotas and 11 previously applied migrations.
begin;

create table public.social_accounts (
  id uuid primary key default gen_random_uuid(),
  shop_id uuid not null references public.shops(id) on delete cascade,
  provider text not null check (provider in ('instagram','facebook','linkedin','youtube')),
  provider_account_id text not null check (length(provider_account_id) between 1 and 200),
  display_name text not null check (length(display_name) between 1 and 200),
  connection_status text not null default 'CONNECTED'
    check (connection_status in ('CONNECTED','REAUTH_REQUIRED','DISCONNECTED')),
  connected_by uuid not null references auth.users(id),
  granted_scopes text[] not null default '{}',
  connected_at timestamptz not null default now(),
  disconnected_at timestamptz,
  unique(shop_id,id),
  unique(shop_id,provider,provider_account_id),
  unique(shop_id,id,provider),
  constraint social_account_disconnect_time check (
    (connection_status <> 'DISCONNECTED' and disconnected_at is null)
    or (connection_status = 'DISCONNECTED' and disconnected_at is not null))
);
create index social_accounts_shop_idx on public.social_accounts(shop_id,provider);

-- Provider secrets, OAuth state, and upload sessions NEVER appear in a public schema.
-- The backend encrypts tokens using an isolated environment key before storage.
-- Encrypted fields must contain AES-GCM envelope bytes; never plaintext credentials.
create table retail_private.social_account_credentials (
  social_account_id uuid primary key references public.social_accounts(id) on delete cascade,
  encryption_key_version integer not null check (encryption_key_version > 0),
  access_token_ciphertext bytea not null,
  refresh_token_ciphertext bytea,
  expires_at timestamptz,
  updated_at timestamptz not null default now(),
  check (octet_length(access_token_ciphertext) >= 40),
  check (refresh_token_ciphertext is null or octet_length(refresh_token_ciphertext) >= 40)
);
create table retail_private.social_oauth_states (
  state_digest bytea primary key,
  shop_id uuid not null references public.shops(id) on delete cascade,
  requested_by uuid not null references auth.users(id),
  provider text not null check(provider in ('instagram','facebook','linkedin','youtube')),
  verifier_ciphertext bytea,
  exact_redirect_uri text not null,
  expires_at timestamptz not null,
  consumed_at timestamptz,
  created_at timestamptz not null default now(),
  check(octet_length(state_digest)=32),
  check(verifier_ciphertext is null or octet_length(verifier_ciphertext)>=40)
);
create index social_oauth_expiry_idx on retail_private.social_oauth_states(expires_at);

-- A draft is never a publish request. Only an authorized backend transition
-- may bind an explicit human approval to the reviewed immutable content digest.
create table public.social_publish_jobs (
  id uuid primary key default gen_random_uuid(),
  shop_id uuid not null references public.shops(id) on delete cascade,
  social_account_id uuid not null,
  campaign_day_id uuid not null,
  provider text not null check(provider in ('instagram','facebook','linkedin','youtube')),
  revision integer not null default 1 check(revision > 0),
  requested_by uuid not null references auth.users(id),
  approved_by uuid references auth.users(id),
  approved_at timestamptz,
  approved_content_sha256 bytea,
  scheduled_at timestamptz not null,
  timezone text not null check(length(timezone) between 1 and 64),
  caption text not null check(length(caption) between 1 and 5000),
  media_asset_id uuid,
  status text not null default 'DRAFT'
    check(status in ('DRAFT','APPROVED','QUEUED','SENDING','PROCESSING',
                     'PUBLISHED','RETRYABLE','RECONCILE','FAILED','CANCELED')),
  idempotency_key text not null check(length(idempotency_key) between 1 and 128),
  remote_post_id text,
  attempts integer not null default 0 check(attempts between 0 and 5),
  last_error_code text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique(shop_id,id),
  unique(shop_id,social_account_id,idempotency_key),
  foreign key(shop_id,social_account_id,provider) references public.social_accounts(shop_id,id,provider),
  foreign key(shop_id,campaign_day_id) references public.campaign_days(shop_id,id),
  foreign key(shop_id,media_asset_id) references public.media_assets(shop_id,id),
  check (approved_content_sha256 is null or octet_length(approved_content_sha256)=32),
  check (status in ('DRAFT','CANCELED','FAILED') or
         (approved_by is not null and approved_at is not null and
          approved_content_sha256 is not null)),
  check (status <> 'PUBLISHED' or remote_post_id is not null)
);
create index social_publish_due_idx on public.social_publish_jobs(status,scheduled_at)
  where status in ('APPROVED','QUEUED','RETRYABLE');
create index social_publish_shop_idx on public.social_publish_jobs(shop_id,created_at desc);

create table retail_private.social_publish_attempts (
  job_id uuid not null references public.social_publish_jobs(id) on delete cascade,
  attempt_no integer not null check(attempt_no between 1 and 5),
  claim_token uuid not null,
  started_at timestamptz not null default now(),
  finished_at timestamptz,
  result_code text,
  primary key(job_id,attempt_no),
  unique(job_id,claim_token)
);
create table public.social_publish_audit (
  id uuid primary key default gen_random_uuid(),
  shop_id uuid not null references public.shops(id) on delete cascade,
  job_id uuid,
  actor_user_id uuid references auth.users(id),
  event_code text not null check(length(event_code) between 1 and 80),
  recorded_at timestamptz not null default now(),
  foreign key(shop_id,job_id) references public.social_publish_jobs(shop_id,id)
);
create index social_publish_audit_idx on public.social_publish_audit(shop_id,recorded_at desc);

-- Unique, internal-only reservations: no double consumption on retry/replay.
-- Publishing remains disabled until an explicit Part 2 quota policy is approved.
create table retail_private.social_publish_quota_ledger (
  publish_job_id uuid primary key references public.social_publish_jobs(id) on delete cascade,
  shop_id uuid not null references public.shops(id) on delete cascade,
  period_start timestamptz not null,
  reserved_at timestamptz not null default now()
);
create index social_publish_meter_idx on retail_private.social_publish_quota_ledger(shop_id,period_start);

alter table public.social_accounts enable row level security;
alter table public.social_publish_jobs enable row level security;
alter table public.social_publish_audit enable row level security;
alter table retail_private.social_account_credentials enable row level security;
alter table retail_private.social_oauth_states enable row level security;
alter table retail_private.social_publish_attempts enable row level security;
alter table retail_private.social_publish_quota_ledger enable row level security;

revoke all on public.social_accounts,public.social_publish_jobs,public.social_publish_audit
  from public,anon,authenticated;
grant select on public.social_accounts,public.social_publish_jobs,public.social_publish_audit
  to authenticated;
grant all on public.social_accounts,public.social_publish_jobs,public.social_publish_audit
  to service_role;

create policy social_accounts_member_read on public.social_accounts
  for select to authenticated
  using(retail_private.has_role(shop_id,array['OWNER','EDITOR','VIEWER']));
create policy social_jobs_member_read on public.social_publish_jobs
  for select to authenticated
  using(retail_private.has_role(shop_id,array['OWNER','EDITOR','VIEWER']));
create policy social_audit_member_read on public.social_publish_audit
  for select to authenticated
  using(retail_private.has_role(shop_id,array['OWNER','EDITOR','VIEWER']));

revoke all on retail_private.social_account_credentials,
  retail_private.social_oauth_states,
  retail_private.social_publish_attempts,
  retail_private.social_publish_quota_ledger
  from public,anon,authenticated;
grant usage on schema retail_private to service_role;
grant all on retail_private.social_account_credentials,
  retail_private.social_oauth_states,
  retail_private.social_publish_attempts,
  retail_private.social_publish_quota_ledger to service_role;

commit;

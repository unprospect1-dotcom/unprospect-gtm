-- Keep the GTM profiling queue synchronized while the crawler is still writing.

create or replace function public.sync_company_gtm_profile_source()
returns trigger
language plpgsql
security invoker
set search_path = public, extensions
as $$
declare
  clean_chars integer;
  clean_hash text;
  next_status text;
  next_reason text;
begin
  clean_chars := length(btrim(coalesce(new.clean_text, '')));
  clean_hash := case
    when clean_chars = 0 then null
    else encode(extensions.digest(new.clean_text, 'sha256'), 'hex')
  end;
  next_status := case when clean_chars < 300 then 'not_profileable' else 'pending' end;
  next_reason := case
    when clean_chars = 0 then 'no_clean_text'
    when clean_chars < 300 then 'thin_text'
    else null
  end;

  insert into public.company_gtm_profiles as existing (
    domain,
    profile_status,
    profileability_reason,
    source_crawl_ok,
    source_clean_chars,
    current_source_hash,
    source_crawled_at
  )
  values (
    new.domain,
    next_status,
    next_reason,
    coalesce(new.ok, false),
    clean_chars,
    clean_hash,
    new.crawled_at
  )
  on conflict (domain) do update
  set
    profile_status = case
      when excluded.profile_status = 'not_profileable' then 'not_profileable'
      when existing.current_source_hash is distinct from excluded.current_source_hash
        then case when existing.profiled_source_hash is null then 'pending' else 'stale' end
      when existing.profile_status = 'not_profileable' then 'pending'
      else existing.profile_status
    end,
    profileability_reason = excluded.profileability_reason,
    source_crawl_ok = excluded.source_crawl_ok,
    source_clean_chars = excluded.source_clean_chars,
    current_source_hash = excluded.current_source_hash,
    source_crawled_at = excluded.source_crawled_at,
    needs_review = case
      when existing.current_source_hash is distinct from excluded.current_source_hash then false
      else existing.needs_review
    end,
    claimed_at = case
      when existing.current_source_hash is distinct from excluded.current_source_hash then null
      else existing.claimed_at
    end,
    last_error = case
      when existing.current_source_hash is distinct from excluded.current_source_hash then null
      else existing.last_error
    end,
    updated_at = case
      when existing.current_source_hash is distinct from excluded.current_source_hash
        or existing.source_crawl_ok is distinct from excluded.source_crawl_ok
        or existing.source_crawled_at is distinct from excluded.source_crawled_at
      then now()
      else existing.updated_at
    end;

  return new;
end;
$$;

revoke all on function public.sync_company_gtm_profile_source() from public, anon, authenticated;
grant execute on function public.sync_company_gtm_profile_source() to service_role;

drop trigger if exists site_crawls_sync_company_gtm_profiles on public.site_crawls;
create trigger site_crawls_sync_company_gtm_profiles
after insert or update of domain, ok, clean_text, crawled_at
on public.site_crawls
for each row
execute function public.sync_company_gtm_profile_source();

-- Catch rows inserted between the first seed and trigger creation.
insert into public.company_gtm_profiles as existing (
  domain,
  profile_status,
  profileability_reason,
  source_crawl_ok,
  source_clean_chars,
  current_source_hash,
  source_crawled_at
)
select
  sc.domain,
  case when length(btrim(coalesce(sc.clean_text, ''))) < 300 then 'not_profileable' else 'pending' end,
  case
    when length(btrim(coalesce(sc.clean_text, ''))) = 0 then 'no_clean_text'
    when length(btrim(sc.clean_text)) < 300 then 'thin_text'
    else null
  end,
  coalesce(sc.ok, false),
  length(btrim(coalesce(sc.clean_text, ''))),
  case
    when nullif(btrim(sc.clean_text), '') is null then null
    else encode(extensions.digest(sc.clean_text, 'sha256'), 'hex')
  end,
  sc.crawled_at
from public.site_crawls sc
on conflict (domain) do update
set
  profile_status = case
    when excluded.profile_status = 'not_profileable' then 'not_profileable'
    when existing.current_source_hash is distinct from excluded.current_source_hash
      then case when existing.profiled_source_hash is null then 'pending' else 'stale' end
    when existing.profile_status = 'not_profileable' then 'pending'
    else existing.profile_status
  end,
  profileability_reason = excluded.profileability_reason,
  source_crawl_ok = excluded.source_crawl_ok,
  source_clean_chars = excluded.source_clean_chars,
  current_source_hash = excluded.current_source_hash,
  source_crawled_at = excluded.source_crawled_at,
  updated_at = now()
where
  existing.current_source_hash is distinct from excluded.current_source_hash
  or existing.source_crawl_ok is distinct from excluded.source_crawl_ok
  or existing.source_crawled_at is distinct from excluded.source_crawled_at
  or existing.profile_status = 'not_profileable' and excluded.profile_status = 'pending';

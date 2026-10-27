-- This is a disposable-PostgreSQL-only reversible scope check.
-- NEVER run on hosted DEV. Requires explicit CLI loopback environment guard.
BEGIN;
DO $
BEGIN
 IF current_setting('application_name') <> 'rgai_feature2_disposable_rollback_ci'
 THEN RAISE EXCEPTION 'DISPOSABLE_ONLY_FEATURE2_ROLLBACK_REFUSED'; END IF;
END $;
DO $
BEGIN
 IF to_regclass('public.shop_ai_budget_controls') is null
    OR to_regclass('public.shop_ai_spend_reservations') is null
    OR to_regprocedure('public.feature2_reserve_ai_budget(uuid,uuid,text,numeric,uuid)') is null
    OR to_regprocedure('public.feature2_settle_ai_budget(uuid,numeric)') is null
    THEN RAISE EXCEPTION 'Feature2 objects missing before rollback rehearsal'; END IF;
END $$;
DROP FUNCTION public.feature2_reserve_ai_budget(uuid,uuid,text,numeric,uuid);
DROP FUNCTION public.feature2_settle_ai_budget(uuid,numeric);
DROP TABLE public.shop_ai_spend_reservations;
DROP TABLE public.shop_ai_budget_controls;
DO $$
BEGIN
 IF to_regclass('public.shop_ai_budget_controls') is not null
    OR to_regclass('public.shop_ai_spend_reservations') is not null
    OR to_regprocedure('public.feature2_reserve_ai_budget(uuid,uuid,text,numeric,uuid)') is not null
    OR to_regprocedure('public.feature2_settle_ai_budget(uuid,numeric)') is not null
 THEN RAISE EXCEPTION 'Feature2 objects survived isolated rollback'; END IF;
 IF to_regclass('public.shops') is null OR to_regclass('public.shop_subscriptions') is null
 THEN RAISE EXCEPTION 'Pre-existing tables were affected'; END IF;
END $$;
ROLLBACK;
DO $$
BEGIN
 IF to_regclass('public.shop_ai_budget_controls') is null
    OR to_regclass('public.shop_ai_spend_reservations') is null
    OR to_regprocedure('public.feature2_reserve_ai_budget(uuid,uuid,text,numeric,uuid)') is null
    OR to_regprocedure('public.feature2_settle_ai_budget(uuid,numeric)') is null
 THEN RAISE EXCEPTION 'Transaction rollback did not restore Feature2 schema'; END IF;
 RAISE NOTICE 'FEATURE2_DISPOSABLE_REVERSIBLE_DDL_REHEARSAL=PASS';
END $$;

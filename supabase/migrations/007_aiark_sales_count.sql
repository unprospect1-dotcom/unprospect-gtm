-- Rescate de blind-spots de GetLeads con AI Ark: conteo de master_sales por dominio.
-- Se llena solo para sospechosos (sales_bucket=0-sin-señal + staff_linkedin>50) vía
-- scripts/aiark_rescue.py. La priorización usa max(sales_count, aiark_sales_count).
alter table list_companies add column if not exists aiark_sales_count integer;

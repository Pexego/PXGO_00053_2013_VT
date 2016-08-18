-- Borramos todas las lineas de venta
ALTER TABLE sale_order_line DISABLE TRIGGER ALL;
delete from sale_order_line;
ALTER TABLE sale_order_line ENABLE TRIGGER ALL;
-- Borramos todos los movimientos
ALTER TABLE stock_move DISABLE TRIGGER ALL;
delete from stock_move;
ALTER TABLE stock_move ENABLE TRIGGER ALL;
-- Borramos todos los quants
delete from stock_quant;
-- Borramos todas las operaciones
delete from stock_pack_operation;
-- Borramos todos los albaranes
delete from stock_picking;
-- Borramos todas las lineas de inventario
delete from stock_inventory_line;
-- Borramos todos los inventarios
delete from stock_inventory;
-- Borramos todas las lineas de factura
delete from account_invoice_line;
-- Borramos todos las facturas
delete from account_invoice;
-- Borramos las ventas que no tienen id en ir_model_data
delete from sale_order where id not in (select distinct res_id from ir_model_data where model = 'sale.order' and module = '');
-- Borramos empresas y direcciones sin id en ir_model_data y que no sean pruebas ni tengan ventas asociadas como direcciones de envío
ALTER TABLE res_partner DISABLE TRIGGER ALL;
delete from res_partner where name not ilike '%PR-%' and id not in (select distinct res_id from ir_model_data where model = 'res.partner' and module = '') and parent_id not in (select id from res_partner where name ilike '%PR-%') and id not in (select distinct partner_shipping_id from sale_order);
ALTER TABLE res_partner ENABLE TRIGGER ALL;
-- Borramos todos los abastecimientos
delete from procurement_order;
-- Borramos todos los grupos de abastecimientos
delete from procurement_group;
-- Borramos todos los números de serie
delete from stock_production_lot;
-- Borramos todas las producciones
delete from mrp_production;
-- Borramos todas las listas de materiales
delete from mrp_bom;
-- Consultamos que productos están metidos a mano y no son pruebas y eliminamos manualmente los que nos interesen
select id,default_code from product_product where id not in (select res_id from ir_model_data where model = 'product.product' and module = '') and default_code not ilike '%PR-%';
delete from product_product where id in (X);
delete from product_template where id not in (select product_tmpl_id from product_product);
-- Borramos todas las reclamaciones (Esto hay que hacerlo en el middleware también).
delete from crm_claim;
delete from claim_line;
-- Borramos pagos y cobros
delete from account_voucher;
delete from payment_return;
delete from payment_order;
delete from account_bank_statement_line;
delete from account_bank_statement;
-- Borramos apuntes y asientos
delete from account_move_line;
delete from account_move;
-- Borramos los cierres de año
delete from account_fiscalyear_closing;
-- Borramos documentación de contabilidad
delete from account_balance_reporting;
delete from l10n_es_aeat_mod303_report;
delete from l10n_es_aeat_mod340_report;
delete from l10n_es_aeat_mod347_report;
delete from l10n_es_aeat_mod349_report;
-- Borramos lineas de compra y compras que no se importaron
delete from purchase_order_line;
delete from purchase_order where id not in (select res_id from ir_model_data where model = 'purchase.order' and module = '');
-- Borramos costes en destino
delete from stock_landed_cost;
-- Borramos modelos personalizados
delete from outlet_loss;
delete from stock_reservation;
delete from stock_deposit;
-- Borramos reparaciones
delete from mrp_repair;
-- Borramos los proveedores de los productos
delete from product_supplierinfo;
-- Borramos las cuentas bancarias y mandatos
delete from res_partner_bank where partner_id != 1;
delete from account_banking_mandate;

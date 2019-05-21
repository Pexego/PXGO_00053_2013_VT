

def parse_many2one_vals(model, vals):
    """
        Por xmlrpc se reciben campos many2one con odoo_id,
        la funcion busca los registros en base de datos y cambia esos valores
        por ids de bd.
        Si hay algún foreignkey que no sea un modelo con odoo_id fallaria.
    """
    from peewee import ForeignKeyField, DateTimeField
    for field_name in list(vals.keys()):
        field = eval('model.%s' % field_name)
        if isinstance(field, DateTimeField):
            if not vals[field_name]:
                del vals[field_name]
                continue
        if isinstance(field, ForeignKeyField):
            model_relation = field.rel_model
            if not vals[field_name]:
                del vals[field_name]
                continue
            rel_rec = model_relation.get(
                model_relation.odoo_id == vals[field_name])
            if rel_rec:
                vals[field_name] = rel_rec.id

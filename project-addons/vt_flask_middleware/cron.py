from sync_log import SyncLog

def check_sync_data():
    to_sync_objs = SyncLog.select().where(SyncLog.to_sync == True).\
        order_by(SyncLog.sync_date.desc()).limit(100)
    for sync_obj in to_sync_objs:
        if sync_obj.to_sync:
            res = sync_obj.sync_client()
            if res:
                other_sync_objs = SyncLog.select().\
                    where(SyncLog.to_sync == True,
                          SyncLog.model == sync_obj.model,
                          SyncLog.odoo_id == sync_obj.odoo_id,
                          SyncLog.id != sync_obj.id)
                for oth in other_sync_objs:
                    oth.sync = True
                    oth.to_sync = False
                    oth.save()

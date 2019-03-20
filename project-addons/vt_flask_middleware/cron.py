from sync_log import SyncLog


def check_sync_data():
    print("DENTRO")
    to_sync_objs = []
    for x in SyncLog.select().where(SyncLog.to_sync == True).\
            order_by(SyncLog.sync_date).limit(100):
        to_sync_objs.append(x)
    print("LEN: ", len(to_sync_objs))
    if to_sync_objs:
        res = to_sync_objs[0].multisync_client(to_sync_objs)
        print("RES: ", res)
        if res:
            for sync_obj in to_sync_objs:
                for oth in SyncLog.select().\
                        where(SyncLog.to_sync == True,
                              SyncLog.model == sync_obj.model,
                              SyncLog.odoo_id == sync_obj.odoo_id,
                              SyncLog.id != sync_obj.id):
                    oth.sync = True
                    oth.to_sync = False
                    oth.save()

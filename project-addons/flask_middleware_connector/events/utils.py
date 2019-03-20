from ..connector import get_environment

def _get_exporter(session, model_name, record_id, class_exporter):
    backend = session.env["middleware.backend"].search([])[0]
    env = get_environment(session, model_name, backend.id)
    return env.get_connector_unit(class_exporter)

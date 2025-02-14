import { api_with_report_date, fetch_server_api } from "./fetch_server_api";

export function add_subject(report_uuid, subjectType, reload) {
    return fetch_server_api('post', `subject/new/${report_uuid}`, { type: subjectType }).then(reload)
}

export function copy_subject(subject_uuid, report_uuid, reload) {
    return fetch_server_api('post', `subject/${subject_uuid}/copy/${report_uuid}`, {}).then(reload)
}

export function move_subject(subject_uuid, report_uuid, reload) {
    return fetch_server_api('post', `subject/${subject_uuid}/move/${report_uuid}`, {}).then(reload)
}

export function delete_subject(subject_uuid, reload) {
    return fetch_server_api('delete', `subject/${subject_uuid}`, {}).then(reload)
}

export function set_subject_attribute(subject_uuid, attribute, value, reload) {
    return fetch_server_api('post', `subject/${subject_uuid}/attribute/${attribute}`, { [attribute]: value }).then(reload)
}

export function get_subject_measurements(subject_uuid, date, minDate) {
    const minReportDate = minDate.toISOString().split("T")[0] + "T00:00:00.000Z" // Ignore the time so we get all measurements for the min date
    let api = api_with_report_date(`subject/${subject_uuid}/measurements`, date)
    const sep = api.indexOf("?") < 0 ? "?" : "&"
    return fetch_server_api('get', api + `${sep}min_report_date=${minReportDate}`)
}

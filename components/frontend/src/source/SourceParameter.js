import React, { useState } from 'react';
import { Icon, Popup } from '../semantic_ui_react_wrappers';
import { StringInput } from '../fields/StringInput';
import { MultipleChoiceInput } from '../fields/MultipleChoiceInput';
import { DateInput } from '../fields/DateInput';
import { IntegerInput } from '../fields/IntegerInput';
import { PasswordInput } from '../fields/PasswordInput';
import { set_source_parameter } from '../api/source';
import { SingleChoiceInput } from '../fields/SingleChoiceInput';
import { LabelWithDropdown } from '../widgets/LabelWithDropdown';
import { HyperLink } from '../widgets/HyperLink';
import { dropdownOptions } from '../utils';

function SourceParameterLabel({
    source_type_name,
    parameter_short_name,
    edit_scope,
    setEditScope,
    index,
    label,
}) {
    const scope_options = [
        { key: "source", value: "source", text: "Apply change to source", description: `Change the ${parameter_short_name} of this ${source_type_name} source only`, label: { color: 'grey', empty: true, circular: true } },
        { key: "metric", value: "metric", text: "Apply change to metric", description: `Change the ${parameter_short_name} of ${source_type_name} sources in this metric that have the same ${parameter_short_name}`, label: { color: 'black', empty: true, circular: true } },
        { key: "subject", value: "subject", text: "Apply change to subject", description: `Change the ${parameter_short_name} of ${source_type_name} sources in this subject that have the same ${parameter_short_name}`, label: { color: 'yellow', empty: true, circular: true } },
        { key: "report", value: "report", text: "Apply change to report", description: `Change the ${parameter_short_name} of ${source_type_name} sources in this report that have the same ${parameter_short_name}`, label: { color: 'orange', empty: true, circular: true } },
        { key: "reports", value: "reports", text: "Apply change to all reports", description: `Change the ${parameter_short_name} of ${source_type_name} sources in all reports that have the same ${parameter_short_name}`, label: { color: 'red', empty: true, circular: true } }];
    return (
        <LabelWithDropdown
            color={{ source: "grey", metric: "black", subject: "gold", report: "orange", reports: "red" }[edit_scope]}
            direction={index % 2 === 0 ? "right" : "left"}
            label={label}
            onChange={(_event, data) => setEditScope(data.value)}
            options={scope_options}
            value={edit_scope} />
    )
}

export function SourceParameter({
        report,
        source,
        source_uuid,
        source_type_name,
        parameter_key,
        parameter_type,
        parameter_name,
        parameter_short_name,
        parameter_unit,
        parameter_min,
        parameter_max,
        parameter_value,
        parameter_values,
        help_url,
        help,
        requiredPermissions,
        placeholder,
        required,
        warning,
        reload,
        index,
    }) {
    const [edit_scope, setEditScope] = useState("source");
    function options() {
        let values = new Set();
        // Collect all values in the current report used for this parameter, for this source type:
        Object.values(report.subjects).forEach((subject) => {
            Object.values(subject.metrics).forEach((metric) => {
                Object.values(metric.sources).forEach((metric_source) => {
                    if (metric_source.type === source.type && metric_source.parameters) {
                        const value = metric_source.parameters[parameter_key];
                        if (value) {
                            if (Array.isArray(value)) {
                                value.forEach((item) => values.add(item))
                            } else {
                                values.add(value)
                            }
                        }
                    }
                })
            })
        });
        return Array.from(values);
    }
    let label = parameter_name;
    if (help_url) {
        label = <label>{parameter_name} <HyperLink url={help_url}><Icon name="help circle" link /></HyperLink></label>
    }
    if (help) {
        label = <label>{parameter_name} <Popup on={['hover', 'focus']} content={help} trigger={<Icon data-testid="help-icon" tabIndex="0" name="help circle" />} /></label>
    }
    let parameter_props = {
        requiredPermissions: requiredPermissions,
        editableLabel: <SourceParameterLabel
            edit_scope={edit_scope}
            label={label}
            setEditScope={setEditScope}
            source_type_name={source_type_name}
            parameter_short_name={parameter_short_name}
            index={index}/>,
        label: label,
        placeholder: placeholder,
        required: required,
        set_value: ((value) => {
            set_source_parameter(source_uuid, parameter_key, value, edit_scope, reload)
            setEditScope("source")  // Reset the edit scope of the parameter to source only
        }),
        value: parameter_value
    };
    if (parameter_type === "date") {
        return (<DateInput {...parameter_props} />)
    }
    if (parameter_type === "password") {
        return (<PasswordInput {...parameter_props} />)
    }
    if (parameter_type === "integer") {
        return (<IntegerInput {...parameter_props} max={parameter_max} min={parameter_min} unit={parameter_unit} />)
    }
    if (parameter_type === "single_choice") {
        return (<SingleChoiceInput {...parameter_props} options={dropdownOptions(parameter_values)} />)
    }
    if (parameter_type === "multiple_choice") {
        return (<MultipleChoiceInput {...parameter_props} options={dropdownOptions(parameter_values)} />)
    }
    if (parameter_type === "multiple_choice_with_addition") {
        return (<MultipleChoiceInput {...parameter_props} options={dropdownOptions(parameter_values)} allowAdditions />)
    }
    parameter_props["options"] = options();
    if (parameter_type === "string") {
        return (<StringInput {...parameter_props} />)
    }
    if (parameter_type === "url") {
        return (<StringInput {...parameter_props} error={warning} />)
    }
    return null;
}

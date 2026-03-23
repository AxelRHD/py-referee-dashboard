import json

from htpy import (
    a,
    button,
    div,
    form,
    input,
    label,
    option,
    select,
    table,
    tbody,
    td,
    textarea,
    th,
    thead,
    tr,
)
from markupsafe import Markup


def form_field(field_label: str, field_input, error: str = ""):
    """Bootstrap form group with label, input, and optional error message."""
    parts = [
        label(".form-label")[field_label],
        field_input,
    ]
    if error:
        parts.append(div(".invalid-feedback.d-block")[error])
    return div(".mb-3")[parts]


def form_row(*fields):
    """Place multiple form_fields side by side in a Bootstrap row."""
    return div(".row")[[div(".col")[field] for field in fields]]


def _invalid_cls(error: str) -> str:
    """Return .is-invalid suffix if there's an error."""
    return ".is-invalid" if error else ""


def text_input(name: str, value: str = "", required: bool = False, error: str = "", **attrs):
    """Bootstrap text input."""
    return input(
        f".form-control{_invalid_cls(error)}",
        type="text",
        name=name,
        value=value,
        required=required,
        **attrs,
    )


def datalist_input(
    name: str,
    value: str = "",
    datalist_id: str = "",
    options: list[str] | None = None,
    required: bool = False,
    error: str = "",
    **attrs,
):
    """Text input with inline autofill (type-ahead completion)."""
    options = options or []
    input_id = f"ac-{name}"
    opts_json = json.dumps(options)

    js = Markup(
        f"<script>"
        f"(function(){{"
        f"var el=document.getElementById('{input_id}'),opts={opts_json};"
        f"el.addEventListener('input',function(e){{"
        f"if(e.inputType&&e.inputType.indexOf('delete')>=0)return;"
        f"var v=el.value;"
        f"if(!v)return;"
        f"var m=opts.find(function(o){{return o.toLowerCase().startsWith(v.toLowerCase())}});"
        f"if(m){{el.value=m;el.setSelectionRange(v.length,m.length)}}"
        f"}});"
        f"el.addEventListener('keydown',function(e){{"
        f"if(e.key==='Tab'&&el.selectionStart!==el.selectionEnd)"
        f"{{el.setSelectionRange(el.value.length,el.value.length)}}"
        f"}});"
        f"}})()"
        f"</script>"
    )

    return [
        input(
            f".form-control{_invalid_cls(error)}",
            type="text",
            id=input_id,
            name=name,
            value=value,
            autocomplete="off",
            required=required,
            **attrs,
        ),
        js,
    ]


def number_input(
    name: str, value: str = "", step: str = "any", required: bool = False, error: str = "", **attrs
):
    """Bootstrap number input."""
    return input(
        f".form-control{_invalid_cls(error)}",
        type="number",
        name=name,
        value=value,
        step=step,
        required=required,
        **attrs,
    )


def date_input(name: str, value: str = "", required: bool = False, error: str = ""):
    """Bootstrap date input."""
    return input(
        f".form-control{_invalid_cls(error)}",
        type="date",
        name=name,
        value=value,
        required=required,
    )


def time_input(name: str, value: str = ""):
    """Bootstrap time input."""
    return input(".form-control", type="time", name=name, value=value)


def textarea_input(name: str, value: str = "", rows: int = 3, error: str = ""):
    """Bootstrap textarea."""
    return textarea(f".form-control{_invalid_cls(error)}", name=name, rows=str(rows))[value]


def select_field(
    name: str,
    options: list[tuple[str, str]],
    selected: str = "",
    required: bool = False,
    error: str = "",
):
    """Bootstrap select dropdown. Options as list of (value, label) tuples."""
    return select(f".form-select{_invalid_cls(error)}", name=name, required=required)[
        option(value="")["— Bitte wählen —"],
        [option(value=val, selected=(val == selected))[lbl] for val, lbl in options],
    ]


def checkbox_input(name: str, checked: bool = False, field_label: str = ""):
    """Bootstrap form-check with checkbox."""
    return div(".mb-3.form-check")[
        input(
            ".form-check-input",
            type="checkbox",
            name=name,
            id=name,
            checked=checked,
            value="1",
        ),
        label(".form-check-label", for_=name)[field_label],
    ]


def submit_button(label_text: str = "Speichern", cancel_url: str = ""):
    """Bootstrap primary submit button with optional cancel link."""
    parts = [button(".btn.btn-primary", type="submit")[label_text]]
    if cancel_url:
        parts.append(a(".btn.btn-outline-danger.ms-2", href=cancel_url)["Abbrechen"])
    return div(".mt-3")[parts]


def delete_button(url: str):
    """Small form with POST delete button and JS confirm."""
    return form(
        method="post",
        action=url,
        onsubmit="return confirm('Wirklich löschen?')",
        style="display:inline",
    )[button(".btn.btn-sm.btn-outline-danger", type="submit")["Löschen"],]


def data_table(headers: list[str], rows):
    """Bootstrap striped table with responsive wrapper."""
    return div(".table-responsive")[
        table(".table.table-striped.table-hover.table-sm")[
            thead[tr[[th(".text-nowrap")[h] for h in headers]],],
            tbody[rows],
        ]
    ]


def action_links(edit_url: str, delete_url: str):
    """Edit link + delete button for table rows."""
    return td[
        a(".btn.btn-sm.btn-outline-primary.me-1", href=edit_url)["Bearbeiten"],
        delete_button(delete_url),
    ]

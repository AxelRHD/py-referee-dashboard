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


def form_field(field_label: str, field_input):
    """Bootstrap form group with label and input."""
    return div(".mb-3")[
        label(".form-label")[field_label],
        field_input,
    ]


def form_row(*fields):
    """Place multiple form_fields side by side in a Bootstrap row."""
    return div(".row")[[div(".col")[field] for field in fields]]


def text_input(name: str, value: str = "", required: bool = False, **attrs):
    """Bootstrap text input."""
    return input(
        ".form-control",
        type="text",
        name=name,
        value=value,
        required=required,
        **attrs,
    )


def number_input(name: str, value: str = "", step: str = "any", required: bool = False, **attrs):
    """Bootstrap number input."""
    return input(
        ".form-control",
        type="number",
        name=name,
        value=value,
        step=step,
        required=required,
        **attrs,
    )


def date_input(name: str, value: str = "", required: bool = False):
    """Bootstrap date input."""
    return input(".form-control", type="date", name=name, value=value, required=required)


def time_input(name: str, value: str = ""):
    """Bootstrap time input."""
    return input(".form-control", type="time", name=name, value=value)


def textarea_input(name: str, value: str = "", rows: int = 3):
    """Bootstrap textarea."""
    return textarea(".form-control", name=name, rows=str(rows))[value]


def select_field(
    name: str,
    options: list[tuple[str, str]],
    selected: str = "",
    required: bool = False,
):
    """Bootstrap select dropdown. Options as list of (value, label) tuples."""
    return select(".form-select", name=name, required=required)[
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


def submit_button(label_text: str = "Speichern"):
    """Bootstrap primary submit button."""
    return button(".btn.btn-primary", type="submit")[label_text]


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

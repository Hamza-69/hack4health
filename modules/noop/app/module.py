from h4h import Module

module = Module(
    "noop",
    title="Noop",
    instructions=(
        "Opens a request for the user; a supplier answers it from the admin panel. "
        "Use open_request when the user asks for something a supplier has to handle, "
        "and request_status to check on it."
    ),
)

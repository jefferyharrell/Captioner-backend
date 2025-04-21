from typing import Any

def encode(
    header: dict[str, Any],
    payload: dict[str, Any],
    key: str,
    check: bool = True,
) -> str | bytes: ...

def decode(
    token: str,
    key: str,
    claims_cls: Any | None = ...,
    claims_options: Any | None = ...,
    claims_params: Any | None = ...,
) -> Any: ...

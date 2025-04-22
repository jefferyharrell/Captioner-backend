from typing import Any

def encode(
    header: dict[str, Any],
    payload: dict[str, Any],
    key: str,
    check: bool = True,
) -> Any: ...  # noqa: ANN401
def decode(
    token: str,
    key: str,
    claims_cls: Any | None = ...,  # noqa: ANN401
    claims_options: Any | None = ...,  # noqa: ANN401
    claims_params: Any | None = ...,  # noqa: ANN401
) -> Any: ...  # noqa: ANN401

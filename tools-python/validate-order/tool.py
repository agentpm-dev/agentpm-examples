"""A small dependency-bearing Tool; stdout contains only its JSON result."""

import json
import sys

from pydantic import BaseModel, ConfigDict, Field, ValidationError


class Order(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)

    quantity: int = Field(gt=0, strict=True)
    unit_price: float = Field(gt=0, strict=True)


def calculate(payload: str) -> dict[str, float]:
    order = Order.model_validate_json(payload)
    return {"total": round(order.quantity * order.unit_price, 2)}


def main() -> int:
    try:
        result = calculate(sys.stdin.read())
    except ValidationError as error:
        print(error, file=sys.stderr)
        return 1
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

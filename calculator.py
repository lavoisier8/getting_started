import ast
import math
import operator
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field


STATIC_DIR = Path(__file__).parent / "static"

app = FastAPI(title="Orbit Calculator")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


class CalculationRequest(BaseModel):
	expression: str = Field(min_length=1, max_length=256)


OPERATORS = {
	ast.Add: operator.add,
	ast.Sub: operator.sub,
	ast.Mult: operator.mul,
	ast.Div: operator.truediv,
	ast.FloorDiv: operator.floordiv,
	ast.Mod: operator.mod,
	ast.Pow: operator.pow,
}
UNARY_OPERATORS = {ast.UAdd: operator.pos, ast.USub: operator.neg}


def evaluate(node: ast.AST) -> int | float:
	if isinstance(node, ast.Constant) and type(node.value) in (int, float):
		value = node.value
		if not math.isfinite(value) or abs(value) > 1e100:
			raise ValueError("Number is outside the supported range")
		return value

	if isinstance(node, ast.BinOp) and type(node.op) in OPERATORS:
		left = evaluate(node.left)
		right = evaluate(node.right)
		if isinstance(node.op, ast.Pow) and abs(right) > 100:
			raise ValueError("Exponent is outside the supported range")
		result = OPERATORS[type(node.op)](left, right)
		if type(result) not in (int, float):
			raise ValueError("Only real-number results are supported")
		if isinstance(result, float) and not math.isfinite(result):
			raise ValueError("Result is outside the supported range")
		if isinstance(result, int) and result.bit_length() > 332:
			raise ValueError("Result is outside the supported range")
		return result

	if isinstance(node, ast.UnaryOp) and type(node.op) in UNARY_OPERATORS:
		return UNARY_OPERATORS[type(node.op)](evaluate(node.operand))

	raise ValueError("Only basic arithmetic is supported")


@app.get("/")
def calculator_page() -> FileResponse:
	return FileResponse(STATIC_DIR / "index.html")


@app.post("/api/calc")
def calculate(request: CalculationRequest) -> dict[str, Any]:
	expression = request.expression.strip()
	if not expression:
		raise HTTPException(status_code=400, detail="Enter an expression")

	try:
		tree = ast.parse(expression, mode="eval")
		if sum(1 for _ in ast.walk(tree)) > 64:
			raise ValueError("Expression is too complex")
		result = evaluate(tree.body)
	except (SyntaxError, ValueError, ZeroDivisionError, OverflowError) as error:
		raise HTTPException(status_code=400, detail=str(error) or "Invalid expression") from error

	return {"expression": expression, "result": result}
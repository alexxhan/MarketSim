from typing import Annotated, Literal

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.market.validation import SimulationDomainError
from app.simulation.engine import SimulationEngine
from app.simulation.experiment import run_experiment
from app.simulation.sweep import run_sweep
from app.simulation.scenario import Regime, run_scenario


app = FastAPI(
    title="MarketSim API",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


@app.exception_handler(SimulationDomainError)
async def simulation_domain_error(request, error):
    return JSONResponse(status_code=422, content={"detail": str(error)})


@app.exception_handler(RequestValidationError)
async def request_validation_error(request, error):
    details = [
        {"loc": item["loc"], "msg": item["msg"], "type": item["type"]}
        for item in error.errors()
    ]
    return JSONResponse(status_code=422, content={"detail": details})


class MarketParameters(BaseModel):
    model_config = ConfigDict(strict=True, allow_inf_nan=False)

    ticks: int = Field(default=1000, ge=1, le=100000)
    starting_price: float = Field(default=100.0, gt=0)
    volatility: int = Field(default=1, ge=0, le=20)
    buy_pressure: float = Field(default=0.50, ge=0, le=1)
    order_arrival_rate: int = Field(default=1, ge=1, le=100)
    spread: float = Field(default=0.04, gt=0)
    order_size: int = Field(default=10, ge=1)
    inventory_risk_factor: float = Field(default=0.001, ge=0)


class SimulationRequest(MarketParameters):
    strategy: Literal["basic", "inventory"] = "inventory"
    seed: int | None = Field(default=None, ge=-9007199254740991, le=9007199254740991)


class ExperimentRequest(MarketParameters):
    number_of_simulations: int = Field(default=10, ge=1, le=100, strict=True)
    starting_seed: int = Field(default=42, ge=-9007199254740991, le=9007199254740991, strict=True)
    ticks: int = Field(default=1000, ge=1, le=5000)
    order_arrival_rate: int = Field(default=3, ge=1, le=10)

    @model_validator(mode="after")
    def validate_workload(self):
        if 2 * self.number_of_simulations * self.ticks * self.order_arrival_rate > 1_000_000:
            raise ValueError("Experiment exceeds 1,000,000 external orders across both strategies; reduce simulations, ticks, or market activity")
        if self.starting_seed + self.number_of_simulations - 1 > 9007199254740991:
            raise ValueError("Final seed exceeds the maximum safe integer")
        return self


class SweepRequest(MarketParameters):
    sweep_parameter: Literal["volatility", "buy_pressure", "order_arrival_rate", "spread", "inventory_risk_factor"]
    sweep_values: list[Annotated[float, Field(strict=True, allow_inf_nan=False)]] = Field(min_length=1, max_length=10)
    simulations_per_value: int = Field(default=10, ge=1, le=100, strict=True)
    starting_seed: int = Field(default=42, ge=-9007199254740991, le=9007199254740991, strict=True)
    ticks: int = Field(default=1000, ge=1, le=5000)
    order_arrival_rate: int = Field(default=3, ge=1, le=10)

    @model_validator(mode="after")
    def validate_sweep(self):
        market_config = self.model_dump(exclude={"sweep_parameter", "sweep_values", "simulations_per_value"})
        workload = 0
        for index, value in enumerate(self.sweep_values):
            if self.sweep_parameter in ("volatility", "order_arrival_rate"):
                if not value.is_integer():
                    raise ValueError(f"{self.sweep_parameter} values must be integers")
                value = int(value)
            point = ExperimentRequest(
                **{**market_config, self.sweep_parameter: value},
                number_of_simulations=self.simulations_per_value
            )
            workload += 2 * self.simulations_per_value * point.ticks * point.order_arrival_rate
            self.sweep_values[index] = getattr(point, self.sweep_parameter)
        if workload > 1_000_000:
            raise ValueError("Sweep exceeds 1,000,000 external orders across all values and both strategies; reduce values, simulations, ticks, or market activity")
        return self


class ScenarioRequest(BaseModel):
    model_config = ConfigDict(strict=True, allow_inf_nan=False)

    regimes: list[Regime] = Field(min_length=1, max_length=10)
    strategy: Literal["basic", "inventory", "comparison"] = "comparison"
    starting_price: float = Field(default=100.0, gt=0, allow_inf_nan=False)
    seed: int = Field(default=42, ge=-9007199254740991, le=9007199254740991, strict=True)
    spread: float = Field(default=0.04, gt=0, allow_inf_nan=False)
    order_size: int = Field(default=10, ge=1, strict=True)
    inventory_risk_factor: float = Field(default=0.001, ge=0, allow_inf_nan=False)

    @model_validator(mode="after")
    def validate_duration(self):
        if sum(regime.duration_ticks for regime in self.regimes) > 5000:
            raise ValueError("Scenario must not exceed 5,000 total ticks")
        return self


@app.get("/")
def root():
    return {
        "name": "MarketSim API",
        "status": "running"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


@app.post("/simulation/run")
def run_simulation(config: SimulationRequest):
    engine = SimulationEngine(
        strategy=config.strategy,
        starting_price=config.starting_price,
        volatility=config.volatility,
        buy_pressure=config.buy_pressure,
        order_arrival_rate=config.order_arrival_rate,
        spread=config.spread,
        order_size=config.order_size,
        inventory_risk_factor=config.inventory_risk_factor,
        seed=config.seed
    )

    pnl_history = []
    inventory_history = []
    midprice_history = []
    reference_price_history = []
    mark_price_history = []

    state = None

    for _ in range(config.ticks):
        state = engine.step()

        pnl_history.append(state["pnl"])
        inventory_history.append(state["inventory"])
        midprice_history.append(state["midprice"])
        reference_price_history.append(state["reference_price"])
        mark_price_history.append(state["mark_price"])

    return {
        "config": config.model_dump(),
        "results": {
            **state["metrics"],
            "ticks": config.ticks,
            "total_trades": len(engine.trades),
            "final_cash": state["cash"],
            "final_inventory": state["inventory"],
            "final_portfolio_value": state["portfolio_value"],
            "final_pnl": state["pnl"],
            "final_midprice": state["midprice"],
            "final_reference_price": state["reference_price"],
            "final_mark_price": state["mark_price"]
        },
        "history": {
            "pnl": pnl_history,
            "inventory": inventory_history,
            "midprice": midprice_history,
            "reference_price": reference_price_history,
            "mark_price": mark_price_history
        }
    }


@app.post("/experiments/run")
def run_multi_seed_experiment(config: ExperimentRequest):
    return {
        "config": config.model_dump(),
        **run_experiment(**config.model_dump())
    }


@app.post("/sweeps/run")
def run_parameter_sweep(config: SweepRequest):
    return {
        "config": config.model_dump(),
        **run_sweep(**config.model_dump())
    }


@app.post("/scenarios/run")
def run_market_scenario(config: ScenarioRequest):
    return {"config": config.model_dump(), **run_scenario(**config.model_dump())}

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, model_validator

from app.simulation.engine import SimulationEngine
from app.simulation.experiment import run_experiment


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


class MarketParameters(BaseModel):
    ticks: int = Field(default=1000, ge=1, le=100000)
    starting_price: float = Field(default=100.0, gt=0)
    volatility: int = Field(default=1, ge=0, le=20)
    buy_pressure: float = Field(default=0.50, ge=0, le=1)
    order_arrival_rate: int = Field(default=1, ge=1, le=100)
    spread: float = Field(default=0.04, gt=0)
    order_size: int = Field(default=10, ge=1)
    inventory_risk_factor: float = Field(default=0.001, ge=0)


class SimulationRequest(MarketParameters):
    strategy: str = "inventory"
    seed: int | None = None


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

    state = None

    for _ in range(config.ticks):
        state = engine.step()

        pnl_history.append(state["pnl"])
        inventory_history.append(state["inventory"])
        midprice_history.append(state["midprice"])

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
            "final_midprice": state["midprice"]
        },
        "history": {
            "pnl": pnl_history,
            "inventory": inventory_history,
            "midprice": midprice_history
        }
    }


@app.post("/experiments/run")
def run_multi_seed_experiment(config: ExperimentRequest):
    return {
        "config": config.model_dump(),
        **run_experiment(**config.model_dump())
    }

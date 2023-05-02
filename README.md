# Forecasting Tool for LangChain AI

This tool adds a simple exponential moving average forecast to the langchain AI. When used with an SQL tool it allows the agent to fetch history data from a database, forecast a future value and then reason with that information.

## Installation

Clone this repository then run:

```
$ python -m pip install .
```

## Usage

The following code will create an agent that has the forecast tool. First export to the shell the OPENAI_API_KEY and your database connection string as DB_CONN.

```
import os

llm = OpenAI(temperature=0)
db = SQLDatabase.from_uri(os.environ["DB_CONN"])

toolkit = ForecastToolkit(db=db, llm=llm)

agent_executor = create_forecast_agent(
    llm=llm,
    toolkit=toolkit,
    verbose=True
)

agent_executor.run("Forecast the invoice total for next month based on the last 12 months of history")
```

Example output for this agent run.

```
> Entering new AgentExecutor chain...
Action: list_tables_sql_db
Action Input: ""
Observation: <list of db tables>

Thought: I should check the schema of the Invoice table to see what columns I can query
Action: schema_sql_db
Action Input: "Invoice"

Thought: I should query the Invoice table for the total invoice amount for the last 12 months
Action: query_sql_db
Action Input: SELECT DATE_FORMAT(createdAt, '%Y-%m') AS month, SUM(total) AS total FROM Invoice WHERE createdAt > DATE_SUB(NOW(), INTERVAL 12 MONTH) GROUP BY month ORDER BY month DESC LIMIT 10

Thought: I should use the EMA forecasting tool to predict the total invoice amount for June 2023
Action: ema_forecast

Observation: {'forecast_date': '2023-05-31', 'value': 3219.1}
Thought: I now know the final answer
Final Answer: The forecasted invoice total is 3219.1
```
# flake8: noqa
"""Tools for interacting with a SQL database."""
from pydantic import BaseModel, Extra, Field, validator, root_validator
from typing import Any, Dict, Union
import json
from langchain.tools.base import BaseTool
import re
from datetime import datetime
import pandas as pd


RawDateType = Union[str, datetime]


class EmaForecastTool(BaseTool):
    """Tool for forecasting with SQL results."""

    name = "ema_forecast"
    description = """
    Input to this tool is a valid json object with keys date and values. The date has a sequence 
    of dates and values has the corresponding values for the metric to forecast. This is the data 
    returned from the SQL query. This tool will return a forecast for the next period.
    
    If an error is returned, rewrite the inputs and try again.
    """

    def _run(self, data: str) -> Dict:
        """ exponential moving average forecast"""
        import traceback

        if "'" in data:
            # Trying hack to replace double quotes
            data = data.replace("'", '"')

        try:
            data = json.loads(data)
            dates = data["date"]
            sequence = data["values"]
            seq = []
            for val in sequence:
                if type(val) == str and re.match(r"Decimal\('[\d\.]+'\)", val):
                    seq.append(eval(val))
                elif type(val) in (list, tuple) and len(val) == 2:
                    seq.append(val[1])
                else:
                    seq.append(val)
            dates = [conv_date(d) for d in dates]
            df = pd.DataFrame(zip(dates, seq), columns=["timestamp", "values"])
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            df = df.sort_values("timestamp")
            df = remove_last_period(df)
            ydf = create_forecast_range_single(df)
            res = do_ewm(df, ydf)
            return {"forecast_date": str(res.timestamp.values[0]), "value": res["values"].values[0]}
        except:
            traceback.print_exc()
            return {"forecast_date": "?", "value": "unknown"}

    async def _arun(self, query: str) -> str:
        raise NotImplementedError("EmaForecastTool does not support async")


def remove_last_period(df, timecol: str="timestamp"):
    # quick workaround, always remove the last period that may be incomplete
    last = list(sorted(df[timecol].values))[-1]
    return df[df[timecol] != last].copy()


def conv_date(dt):
    if re.match(r"\d{4}-\d{2}", dt):
        return dt + "-01"
    return dt


def estimate_period(df: pd.DataFrame, timecol: str="timestamp") -> str:
    """ simple estimation of period supporting daily, weekly and monthly """
    avg_days = df[timecol].diff().mean().days
    if avg_days in [29,30,31]:
        return "M"
    elif avg_days in [6,7]:
        return "W"
    elif avg_days == 1:
        avg_hr = df[timecol].diff().mean().seconds / (60*60)
        if avg_hr > 23:
            return "D"
    return ""


def create_forecast_range_single(df: pd.DataFrame, timecol:str="timestamp") -> pd.DataFrame:
    """ generate a dataframe with a single next period to forecast """
    freq = estimate_period(df)
    rng = pd.date_range(df[timecol].values[-1], periods=2, freq=freq)
    return pd.DataFrame(rng[1:], columns=[timecol])


def create_forecast_range(df: pd.DataFrame, end_date: RawDateType, timecol:str="timestamp", min_periods:int=1) -> pd.DataFrame:
    """ generate a dataframe with dates to forecast """
    freq = estimate_period(df)
    end_date = pd.to_datetime(end_date)
    rng = pd.date_range(df.timestamp.values[-1], end=end_date, freq=freq)
    # if only the start period, then make a new range with two periods
    if len(rng) < min_periods + 1:
        rng = pd.date_range(df[timecol].values[-1], periods=min_periods + 1, freq=freq)
    return pd.DataFrame(rng[1:], columns=[timecol])


def do_ewm(df: pd.DataFrame, ydf: pd.DataFrame, timecol: str="timestamp", valcol: str="values", include_history: bool=False) -> pd.DataFrame:
    """ execute EMA forecast """
    resdf = df.copy()
    
    for ts in sorted(ydf[timecol].values):
        yhat = resdf[valcol].ewm(com=0.8).mean().values[-1]
        resdf = pd.concat([resdf, pd.DataFrame([{timecol: ts, valcol: yhat}])])
    if include_history:
        return resdf
    else:
        return resdf[resdf[timecol].isin(ydf[timecol].values)].copy()

#!/usr/bin/env python3
from typing import List, Dict, Optional, Tuple
from loguru import logger
import datetime
import requests
import json
import os

# Configure logger
logger.add(
    "function_logs.log",
    rotation="10 MB",
    retention="1 week",
    level="DEBUG",
    enqueue=True,
)
logger.info("Starting LLM Global Spend function")


class LiteLLMAPIClient:
    """Handles API communication with LiteLLM service"""

    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None):
        self.base_url = base_url or os.getenv("LITELLM_API_BASE_URL")
        api_key = api_key or os.getenv("LITELLM_API_KEY")
        if not self.base_url or not api_key:
            logger.error("Base URL and API key must be provided")
            raise ValueError("Base URL and API key must be provided")

        self.headers = {
            "accept": "application/json",
            "x-goog-api-key": api_key,
        }
        logger.debug(
            f"LiteLLMAPIClient initialized with base URL: {self.base_url}")

    def fetch_spending_logs(
        self, user_id=None, start_date="2024-06-01", end_date="2025-12-31"
    ) -> List[Dict]:
        """
        Fetches spending logs from the API.

        Args:
            user_id (str): The user ID for which to fetch logs
            start_date (str): The start date in YYYY-MM-DD format
            end_date (str): The end date in YYYY-MM-DD format

        Returns:
            List[Dict]: The fetched spending logs

        Raises:
            requests.exceptions.RequestException: If the API request fails
        """
        spending_logs_endpoint = f"{self.base_url}/spend/logs"
        params = {"user_id": user_id,
                  "start_date": start_date, "end_date": end_date}

        logger.info(
            f"Fetching spend logs for user {user_id} from {start_date} to {end_date}"
        )
        logger.debug(
            f"API request to {spending_logs_endpoint} with params: {params}")

        try:
            response = requests.get(
                spending_logs_endpoint, headers=self.headers, params=params
            )
            response.raise_for_status()
            data = response.json()
            logger.success(
                f"Successfully fetched {len(data)} spending log entries")
            return data
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch spending logs: {str(e)}")
            raise


class SpendAnalyzer:
    """Analyzes spending data from API responses"""

    def __init__(self, spend_data: List[Dict]):
        """
        Initialize with spending data

        Args:
            spend_data: List of spending records
        """
        self.spend_data = spend_data
        logger.debug(
            f"SpendAnalyzer initialized with {len(spend_data)} records")

    def get_total_spend(self) -> float:
        """Calculate the total spend across all records"""
        total = sum(entry.get("spend", 0) for entry in self.spend_data)
        logger.info(f"Total global spend calculated: {total}")
        return total

    def get_filtered_spend(
        self, start_date: datetime.datetime, end_date: datetime.datetime
    ) -> float:
        """
        Calculate spend for a specific date range

        Args:
            start_date: Start date (inclusive)
            end_date: End date (exclusive)

        Returns:
            float: Total spend in the specified date range
        """
        logger.debug(
            f"Calculating filtered spend from {start_date} to {end_date}")
        filtered_spend = 0
        valid_entries = 0
        invalid_entries = 0

        for entry in self.spend_data:
            date_string = entry.get("startTime", "")
            try:
                entry_date = datetime.datetime.strptime(
                    date_string, "%Y-%m-%d")
                if start_date <= entry_date < end_date:
                    spend_amount = entry.get("spend", 0)
                    filtered_spend += spend_amount
                    valid_entries += 1
                    logger.debug(
                        f"Added spend entry: {date_string} = {spend_amount}")
            except ValueError:
                logger.warning(f"Invalid date format in entry: {date_string}")
                invalid_entries += 1
                continue

        logger.info(
            f"Filtered spend: {filtered_spend} (from {valid_entries} valid entries, {invalid_entries} invalid entries)"
        )
        return filtered_spend

    def get_current_month_spend(self) -> float:
        """Calculate spend for the current month"""
        now = datetime.datetime.now()
        first_day = now.replace(day=1)
        next_month = (now.replace(day=28) +
                      datetime.timedelta(days=4)).replace(day=1)

        logger.info(
            f"Calculating current month spend ({first_day.strftime('%Y-%m-%d')} to {next_month.strftime('%Y-%m-%d')})"
        )
        return self.get_filtered_spend(first_day, next_month)

    def get_today_spend(self) -> float:
        """Calculate spend for today"""
        now = datetime.datetime.now()
        today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow = today + datetime.timedelta(days=1)

        logger.info(
            f"Calculating today's spend ({today.strftime('%Y-%m-%d')})")
        return self.get_filtered_spend(today, tomorrow)


def get_spend_data() -> Tuple[float, float, float]:
    """
    Fetch and calculate spend metrics

    Returns:
        Tuple containing global, monthly and daily spend as floats

    Raises:
        requests.exceptions.RequestException: If API request fails
    """
    logger.info("Beginning spend data retrieval and analysis")
    try:
        api_client = LiteLLMAPIClient()
        spend_data = api_client.fetch_spending_logs()

        analyzer = SpendAnalyzer(spend_data)
        global_spend = float(analyzer.get_total_spend())
        current_month_spend = float(analyzer.get_current_month_spend())
        today_spend = float(analyzer.get_today_spend())

        logger.success(
            f"Successfully calculated all spend metrics: global={global_spend}, month={current_month_spend}, today={today_spend}"
        )
        return (global_spend, current_month_spend, today_spend)
    except Exception as e:
        logger.exception(f"Error in get_spend_data: {str(e)}")
        raise


def handle(event, context):
    """OpenFaaS handler function"""
    logger.info(f"Function invoked with event: {event}")

    try:
        logger.debug("Retrieving spend data...")
        global_spend, current_month_spend, today_spend = get_spend_data()

        # Ensure all values are floats for consistent JSON serialization
        response = {
            "global_spend": float(global_spend),
            "current_month_spend": float(current_month_spend),
            "today_spend": float(today_spend),
        }

        logger.success(
            f"Successfully processed request, returning data: {response}")
        return {
            "statusCode": 200,
            "body": json.dumps(response),
            "headers": {"Content-Type": "application/json"},
        }

    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": f"API request failed: {str(e)}"}),
            "headers": {"Content-Type": "application/json"},
        }
    except Exception as e:
        logger.exception(f"Unexpected error in handler function: {str(e)}"),
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Internal server error"}),
            "headers": {"Content-Type": "application/json"},
        }

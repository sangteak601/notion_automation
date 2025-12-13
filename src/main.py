import os
import datetime

from notion_client import Client
from update_mermaid_chart import update_mermaid_pie_chart, update_mermaid_line_chart_accumulation


def main():
    notion_client = Client(auth=os.environ.get('NOTION_TOKEN'))
    page_id = os.environ.get('NOTION_EXPENSE_CHART_PAGE_ID')
    database_id = os.environ.get('NOTION_EXPENSE_CHART_DATA_DB_ID')
    category_name = os.environ.get('NOTION_EXPENSE_CHART_DB_PROPERTY_CATEGORY')
    categories_to_ignore = os.environ.get('NOTION_EXPENSE_CHART_DB_CATEGORIES_TO_IGNORE', '').split(':')
    value_name = os.environ.get('NOTION_EXPENSE_CHART_DB_PROPERTY_VALUE')
    date_property = os.environ.get('NOTION_EXPENSE_CHART_DB_PROPERTY_DATE')

    balance_db_id = os.environ.get('NOTION_BALANCE_CHART_DATA_DB_ID')
    balance_value_name = os.environ.get('NOTION_BALANCE_CHART_DB_PROPERTY_VALUE')
    balance_date_property = os.environ.get('NOTION_BALANCE_CHART_DB_PROPERTY_DATE')
    # Update the chart for this month
    chart_title_this_month = 'This Month Expenses'
    next_month = datetime.date.today().month + 1
    next_month_year = datetime.date.today().year
    if next_month == 13:
        next_month = 1
        next_month_year += 1
    first_date_this_month = datetime.date.today().replace(day=1)
    last_date_this_month = datetime.date(next_month_year, next_month, 1) - datetime.timedelta(days=1)
    filter_this_month = {
        'and': [
            {
                'property': date_property,
                'date': {
                    'on_or_after': first_date_this_month.isoformat(),
                },
            },
            {
                'property': date_property,
                'date': {
                    'on_or_before': last_date_this_month.isoformat(),
                },
            },
        ]
    }

    update_mermaid_pie_chart(
        notion_client=notion_client,
        page_id=page_id,
        chart_title=chart_title_this_month,
        db_id=database_id,
        db_filter=filter_this_month,
        db_property_category=category_name,
        db_categories_to_ignore=categories_to_ignore,
        db_property_value=value_name
    )

    # Update the chart for last month
    chart_title_last_month = 'Last Month Expenses'
    first_date_last_month = (datetime.date.today().replace(day=1) - datetime.timedelta(days=1)).replace(day=1)
    last_date_last_month = datetime.date.today().replace(day=1) - datetime.timedelta(days=1)
    filter_last_month = {
        'and': [
            {
                'property': date_property,
                'date': {
                    'on_or_after': first_date_last_month.isoformat(),
                },
            },
            {
                'property': date_property,
                'date': {
                    'on_or_before': last_date_last_month.isoformat(),
                }
            },
        ]
    }

    update_mermaid_pie_chart(
        notion_client=notion_client,
        page_id=page_id,
        chart_title=chart_title_last_month,
        db_id=database_id,
        db_filter=filter_last_month,
        db_property_category=category_name,
        db_categories_to_ignore=categories_to_ignore,
        db_property_value=value_name
    )

    # Update the line chart for last 24 months
    chart_title_line_chart = 'Balance Over Time'
    filter_24_month = {
        'property': balance_date_property,
        'date': {
            'on_or_before': last_date_this_month.isoformat(),
        }

    }

    update_mermaid_line_chart_accumulation(
        notion_client=notion_client,
        page_id=page_id,
        chart_title=chart_title_line_chart,
        db_id=balance_db_id,
        db_filter=filter_24_month,
        db_property_index=balance_date_property,
        db_property_value=balance_value_name
    )

if __name__ == '__main__':
    main()

import os
import datetime

from notion_client import Client
from update_mermaid_chart import update_mermaid_pie_chart


def main():
    notion_client = Client(auth=os.environ.get('NOTION_TOKEN'))
    page_id = os.environ.get('NOTION_EXPENSE_CHART_PAGE_ID')
    database_id = os.environ.get('NOTION_EXPENSE_CHART_DATA_DB_ID')
    category_name = os.environ.get('NOTION_EXPENSE_CHART_DB_PROPERTY_CATEGORY')
    value_name = os.environ.get('NOTION_EXPENSE_CHART_DB_PROPERTY_VALUE')
    date_property = os.environ.get('NOTION_EXPENSE_CHART_DB_PROPERTY_DATE')

    # Update the chart for this month
    chart_title_this_month = 'This Month Expenses'
    next_month = datetime.date.today().month % 12 + 1
    first_date_this_month = datetime.date.today().replace(day=1)
    last_date_this_month = datetime.date.today().replace(day=1, month=next_month) - datetime.timedelta(days=1)
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
        db_property_value=value_name
    )

if __name__ == '__main__':
    main()

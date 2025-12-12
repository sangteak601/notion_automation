from notion_client import Client


def get_nested_children(notion_client : Client, block_id : str):
    """
    Get all nested children of a block.

    Args:
        notion_client (Client): Notion client object
        block_id (str): Block ID to get children from

    Returns:
        list: List of all nested children
    """
    # Get children of the block
    children = notion_client.blocks.children.list(
        **{
            'block_id': block_id,
        }
    )

    # Get nested children of the block
    all_children = []
    all_children += children['results']
    for result in children['results']:
        if result['has_children']:
            all_children += get_nested_children(notion_client, result['id'])

    return all_children

def update_mermaid_pie_chart(
    notion_client : Client,
    page_id : str,
    chart_title : str,
    db_id : str,
    db_filter : dict,
    db_property_category : str,
    db_property_value : str):
    """
    Update a Mermaid chart with data from a Notion database.

    Args:
        notion_client (Client): Notion client object
        page_id (str): Page ID where the chart is located
        chart_title (str): Title of the chart
        db_id (str): Database ID to get data from
        db_filter (dict): Database filter to apply
        db_property_category (str): Database property name to use for categories in the chart. Must be a select property.
        db_property_value (str): Database property name to use for values in the chart. Must be a number or a formula property.
    """
    # Get database info
    db_info = notion_client.databases.retrieve(
        **{
            'database_id': db_id,
        }
    )

    # Create dictionary to store chart data
    chart_data = {}
    categories = db_info['properties'][db_property_category]['select']['options']
    for category in categories:
        chart_data[category['name']] = 0

    # Get data from database
    db_data = notion_client.databases.query(
        **{
            'database_id': db_id,
            'filter': db_filter
        }
    )

    # Put data into chart_data
    for result in db_data['results']:
        if result['properties'][db_property_value]['type'] == 'number':
            chart_data[result['properties'][db_property_category]['select']['name']] += abs(result['properties'][db_property_value]['number'])
        elif result['properties'][db_property_value]['type'] == 'formula':
            chart_data[result['properties'][db_property_category]['select']['name']] += abs(result['properties'][db_property_value]['formula']['number'])
        else:
            raise Exception(f'Property {db_property_value} must be a number or formula property. Property type is {result["properties"][db_property_value]["type"]}')

    # Round values to 2 decimal places
    for category in chart_data:
        chart_data[category] = round(chart_data[category], 2)

    # Get children of the page
    page_children = get_nested_children(notion_client, page_id)

    # Get the block ID of the chart using the title
    chart_block_id = None
    for result in page_children:
        if result['type'] == 'code':
            if chart_title in result['code']['rich_text'][0]['text']['content']:
                chart_block_id = result['id']
                break

    # Check if chart was found
    if chart_block_id is None:
        raise Exception(f'Chart with title {chart_title} not found on page')

    # Update the chart
    mermaid_script = "%%{init: {'theme':'default'}}%%\n" + f'pie showData title {chart_title}\n'
    tab = ' ' * 4
    for category, value in chart_data.items():
        mermaid_script += f'{tab}"{category}": {value}\n'

    # Update the chart block
    notion_client.blocks.update(
        **{
            'block_id': chart_block_id,
            'code': {
                'rich_text': [
                    {
                        'text': {
                            'content': mermaid_script,
                        },
                    },
                ]
            }
        }
    )

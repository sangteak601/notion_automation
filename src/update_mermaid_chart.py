from notion_client import Client


def get_nested_children(notion_client : Client, block_id : str) -> list:
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

def filter_by_type(items : list, type_name : str) -> list:
    """
    Filter a list of Notion blocks by type.

    Args:
        items (list): List of Notion blocks
        type_name (str): Type name to filter by

    Returns:
        list: List of Notion blocks of the specified type
    """
    filtered_items = []
    for item in items:
        if item['type'] == type_name:
            filtered_items.append(item)
    return filtered_items

def find_code_block_by_title(notion_client : Client, block_id : str, title : str) -> dict:
    """
    Find a code block by title.

    Args:
        notion_client (Client): Notion client object
        block_id (str): Block ID to search in
        title (str): Title to search for
    Returns:
        dict: Code block with the specified title, or None if not found
    """
    code_blocks = filter_by_type(get_nested_children(notion_client, block_id), 'code')
    for code_block in code_blocks:
        if title in code_block['code']['rich_text'][0]['text']['content']:
            return code_block

    return None

def update_mermaid_pie_chart(
    notion_client : Client,
    page_id : str,
    chart_title : str,
    db_id : str,
    db_filter : dict,
    db_property_category : str,
    db_categories_to_ignore : list,
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
        db_categories_to_ignore (list): List of categories to ignore in the chart.
        db_property_value (str): Database property name to use for values in the chart. Must be a number or a formula property.
    """
    # Get database info
    db_info = notion_client.data_sources.retrieve(
        **{
            'data_source_id': db_id,
        }
    )

    # Create dictionary to store chart data
    chart_data = {}
    categories = db_info['properties'][db_property_category]['select']['options']
    for category in categories:
        chart_data[category['name']] = 0

    # Get data from database
    db_data = notion_client.data_sources.query(
        **{
            'data_source_id': db_id,
            'filter': db_filter
        }
    )

    # Put data into chart_data
    for result in db_data['results']:
        data = 0
        if result['properties'][db_property_value]['type'] == 'number':
            data = result['properties'][db_property_value]['number']
        elif result['properties'][db_property_value]['type'] == 'formula':
            data = result['properties'][db_property_value]['formula']['number']
        else:
            raise Exception(f'Property {db_property_value} must be a number or formula property. Property type is {result["properties"][db_property_value]["type"]}')
        chart_data[result['properties'][db_property_category]['select']['name']] -= data

    # Remove categories to ignore
    for category in db_categories_to_ignore:
        if category in chart_data:
            del chart_data[category]

    # Round values to 2 decimal places
    for category in chart_data:
        chart_data[category] = round(chart_data[category], 2)

    # Get the code block by title
    chart_block = find_code_block_by_title(notion_client, page_id, chart_title)

    # Check if chart was found
    if chart_block is None:
        raise Exception(f'Chart with title {chart_title} not found on page')

    # Update the chart
    mermaid_script = "%%{init: {'theme':'default'}}%%\n" + f'pie showData title {chart_title}\n'
    tab = ' ' * 4
    for category, value in chart_data.items():
        mermaid_script += f'{tab}"{category}": {value}\n'

    # Update the chart block
    notion_client.blocks.update(
        **{
            'block_id': chart_block['id'],
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

def update_mermaid_line_chart_accumulation(
    notion_client : Client,
    page_id : str,
    chart_title : str,
    db_id : str,
    db_filter : dict,
    db_property_index : str,
    db_property_value : str,
    max_points : int = 24):
    """
    Update a Mermaid line chart with accumulated data from a Notion database.
    Args:
        notion_client (Client): Notion client object
        page_id (str): Page ID where the chart is located
        chart_title (str): Title of the chart
        db_id (str): Database ID to get data from
        db_filter (dict): Database filter to apply
        db_property_index (str): Database property name to use for the index in the chart. Must be a date property.
        db_property_value (str): Database property name to use for values in the chart. Must be a number or a formula property.
        max_points (int): Maximum number of points to display on the chart. Defaults to 24.
    """
    # Get data from database
    db_data = notion_client.data_sources.query(
        **{
            'data_source_id': db_id,
            'filter': db_filter
        }
    )

    # Create dictionary to store chart data
    chart_data = {}
    for result in db_data['results']:
        data = 0
        if result['properties'][db_property_value]['type'] == 'number':
            data = result['properties'][db_property_value]['number']
        elif result['properties'][db_property_value]['type'] == 'formula':
            data = result['properties'][db_property_value]['formula']['number']
        else:
            raise Exception(f'Property {db_property_value} must be a number or formula property. Property type is {result["properties"][db_property_value]["type"]}')
        index = result['properties'][db_property_index]['date']['start']
        if index not in chart_data:
            chart_data[index] = 0
        chart_data[index] += data

    # Sort chart data by index
    chart_data = dict(sorted(chart_data.items()))

    # Accumulate chart data
    accumulated_value = 0
    for index in chart_data:
        accumulated_value += chart_data[index]
        chart_data[index] = round(accumulated_value, 2)

    # Limit number of points to max_points
    if len(chart_data) > max_points:
        chart_data = dict(list(chart_data.items())[-max_points:])

    # Get the code block by title
    chart_block = find_code_block_by_title(notion_client, page_id, chart_title)

    # Check if chart was found
    if chart_block is None:
        raise Exception(f'Chart with title {chart_title} not found on page')

    # Update the chart
    tab = ' ' * 4
    mermaid_script = f"---\nconfig:\n{tab}xyChart:\n{tab}{tab}width: 1200\n{tab}{tab}height: 600\n{tab}themeVariables:\n{tab}{tab}xyChart:\n{tab}{tab}{tab}plotColorPalette: '#0000FF'\n---\n"
    mermaid_script += f'xychart title "{chart_title}"\n'
    mermaid_script += f'{tab}x-axis ['
    mermaid_script += ', '.join([f'"{index.split("-")[0][2:] + "-" + index.split("-")[1]}"' for index in chart_data.keys()]) + ']\n'
    mermaid_script += f'{tab}y-axis "Balance in £"\n'
    mermaid_script += f'{tab}line ['
    mermaid_script += ', '.join([str(value) for value in chart_data.values()]) + ']\n'

    # Update the chart block
    notion_client.blocks.update(
        **{
            'block_id': chart_block['id'],
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
from app.agents.contracts import get_tool_contract, list_tool_contracts


def test_tool_contract_names_are_unique():
    contracts = list_tool_contracts()
    names = [contract.name for contract in contracts]

    assert len(names) == len(set(names))


def test_core_mcp_tool_contracts_are_defined():
    names = {contract.name for contract in list_tool_contracts()}

    assert {
        'get_market_overview',
        'get_large_cap_movers',
        'get_top_market_movers',
        'get_ticker_snapshot',
        'get_historical_candles',
        'get_company_news',
        'get_recent_news',
        'generate_recommendation',
        'list_recent_recommendations',
        'list_watchlist',
        'upsert_watchlist_item',
        'delete_watchlist_item',
    } <= names


def test_write_tool_contracts_require_confirmation():
    upsert = get_tool_contract('upsert_watchlist_item')
    delete = get_tool_contract('delete_watchlist_item')

    assert upsert is not None
    assert delete is not None
    assert upsert.read_only is False
    assert delete.read_only is False
    assert upsert.requires_confirmation is True
    assert delete.requires_confirmation is True


def test_contracts_expose_json_schemas_and_audit_events():
    contract = get_tool_contract('get_ticker_snapshot')

    assert contract is not None
    assert contract.input_schema['properties']['ticker']['pattern']
    assert contract.output_schema['properties']['ok']
    assert contract.audit_event == 'agent.tool.get_ticker_snapshot'

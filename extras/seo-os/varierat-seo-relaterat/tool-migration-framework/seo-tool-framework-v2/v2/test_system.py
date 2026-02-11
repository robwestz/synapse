"""
Full System Test for SEO Tool Framework
"""

import asyncio
from core.framework import ToolFramework

async def full_test():
    print('=== FRAMEWORK TEST ===\n')

    fw = ToolFramework()

    # Ladda manifests
    manifest_count = fw.load_manifests('manifests')
    print(f'Manifests laddade: {manifest_count}')

    # Auto-discover tools
    discover_count = fw.auto_discover('tools/test_tools', 'tools.test_tools')
    print(f'Verktyg upptäckta: {discover_count}')

    # Lista alla verktyg
    tools = fw.list_tools()
    print(f'\nRegistrerade verktyg: {len(tools)}')
    for t in tools:
        print(f'  {t["archetype"][:3].upper()} | {t["id"]}')

    # Testa varje verktyg
    print('\n=== KÖR ALLA VERKTYG ===\n')

    test_data = {
        'keyword_clustering': {'keywords': 'seo tools\nkeyword research\nbacklink checker'},
        'content_gap_discovery': {'domain': 'example.com', 'competitors': ['comp.com']},
        'serp_volatility': {'lookback_days': 7},
        'internal_link_optimizer': {'site_url': 'https://example.com'},
        'rag_content_brief': {'keyword': 'seo guide', 'content_type': 'guide'},
    }

    success_count = 0
    for tool_id, data in test_data.items():
        result = await fw.execute(tool_id, data)
        status = '[OK]' if result.success else '[FAIL]'
        time_ms = f'{result.execution_time_ms:.0f}ms'
        print(f'{status} {tool_id}: {time_ms}')
        if result.success:
            success_count += 1
        else:
            print(f'   Error: {result.error}')

    print(f'\n=== RESULTAT: {success_count}/5 LYCKADES ===')

    await fw.shutdown()

    if success_count == 5:
        print('\n[SUCCESS] ALLT FUNGERAR! Redo att starta server.')
        return True
    else:
        print('\n[WARNING] Vissa verktyg misslyckades. Kolla felmeddelanden.')
        return False

if __name__ == "__main__":
    success = asyncio.run(full_test())
    exit(0 if success else 1)
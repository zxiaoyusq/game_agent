"""解析 Unity 对象引用、业务脚本配置和节点层级，不按产品名猜测业务结构。"""
import argparse
from collections import Counter
from pathlib import Path
from common import local_path, read_json, write_json


def references(value, prefix=''):
    """遍历任意配置，保留字段路径，明确区分空引用和未解析引用。"""
    if isinstance(value, dict):
        if 'm_FileID' in value and 'm_PathID' in value:
            yield prefix, value
        else:
            for name, child in value.items():
                yield from references(child, f'{prefix}.{name}'.strip('.'))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from references(child, f'{prefix}[{index}]')


def run(args):
    root = args.workspace.resolve()
    objects = read_json(root / 'unity_objects.json')
    external = read_json(root / 'analysis/serialized_files.json')
    lookup = {(item['source'], item['path_id']): item for item in objects}
    file_names = {name.lower(): name for name in external}

    def resolve(source, pointer):
        """FileID 为零引用当前序列化文件，非零引用外部文件表，编号从一开始。"""
        if not pointer['m_PathID']:
            return {'status': '空引用'}
        target_source = source
        if pointer['m_FileID']:
            index = pointer['m_FileID'] - 1
            paths = external.get(source, [])
            if not 0 <= index < len(paths):
                return {'status': '外部文件索引缺失'}
            target_source = paths[index].replace('\\', '/').rsplit('/', 1)[-1]
            target_source = file_names.get(target_source.lower(), target_source)
        target = lookup.get((target_source, pointer['m_PathID']))
        if target is None:
            return {'status': '未解析', 'source': target_source, 'path_id': pointer['m_PathID']}
        return {'status': '已解析', 'source': target_source, 'path_id': pointer['m_PathID'],
                'type': target['type'], 'name': target.get('name', ''), 'exports': target['exports'],
                'script_type': target.get('script_type')}

    data_map, links, configs = {}, [], []
    for item in objects:
        if item['status'] != '已导出':
            continue
        config_file = next((name for name in item['exports'] if name.endswith('.json')), None)
        if not config_file:
            continue
        data = read_json(local_path(root, config_file))
        if not isinstance(data, dict):
            continue
        data_map[(item['source'], item['path_id'])] = data
        if item['type'] in ('MonoBehaviour', 'Material', 'Sprite', 'SpriteAtlas', 'GameObject', 'Transform', 'RectTransform', 'SpriteRenderer'):
            for field, pointer in references(data):
                if pointer['m_PathID']:
                    links.append({'owner_source': item['source'], 'owner_path_id': item['path_id'],
                                  'owner_name': item.get('name', ''), 'field': field, 'reference': pointer,
                                  'target': resolve(item['source'], pointer)})
        if item['type'] == 'MonoBehaviour':
            fields = {name: {'kind': type(value).__name__, 'length': len(value)} if isinstance(value, (list, dict)) else value
                      for name, value in data.items() if not name.startswith('m_')}
            configs.append({'name': item.get('name'), 'script_type': item.get('script_type'), 'script_assembly': item.get('script_assembly'),
                            'source': item['source'], 'path_id': item['path_id'], 'file': config_file, 'fields': fields})
    nodes = []
    for item in objects:
        if item['type'] not in ('Transform', 'RectTransform'):
            continue
        data = data_map.get((item['source'], item['path_id']))
        if not data:
            continue
        game_object = resolve(item['source'], data['m_GameObject'])
        go_data = data_map.get((game_object.get('source'), game_object.get('path_id')), {})
        components = [resolve(game_object['source'], component['component']) for component in go_data.get('m_Component', [])]
        nodes.append({'source': item['source'], 'path_id': item['path_id'], 'name': game_object.get('name', ''),
                      'game_object': game_object, 'parent': resolve(item['source'], data['m_Father']),
                      'children': [resolve(item['source'], child) for child in data['m_Children']],
                      'components': components, 'transform_file': item['exports'][0]})
    node_lookup = {(node['source'], node['path_id']): node for node in nodes}
    lines = ['此清单包含场景与预制体，不代表运行时同时实例化。']
    def visit(node, depth=0, visited=None):
        visited = set() if visited is None else visited
        key = node['source'], node['path_id']
        if key in visited:
            lines.append('  ' * depth + '重复或循环引用'); return
        visited.add(key)
        names = [part.get('script_type') or part.get('type') for part in node['components']]
        lines.append('  ' * depth + node['name'] + ' [' + ', '.join(filter(None, names)) + ']')
        for child in node['children']:
            target = node_lookup.get((child.get('source'), child.get('path_id')))
            if target:
                visit(target, depth + 1, visited)
    for node in nodes:
        if node['parent']['status'] == '空引用':
            lines.append('\n所属文件：' + node['source']); visit(node)
    write_json(root / 'analysis/config_index.json', configs)
    write_json(root / 'analysis/resource_links.json', links)
    write_json(root / 'analysis/node_graph.json', nodes)
    (root / 'analysis/node_hierarchy.txt').write_text('\n'.join(lines), encoding='utf-8')
    summary = {'references': dict(Counter(link['target']['status'] for link in links)), 'configs': len(configs), 'nodes': len(nodes)}
    write_json(root / 'analysis/relationship_summary.json', summary)
    print(f'引用与结构索引完成：{summary}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace', type=Path, required=True)
    run(parser.parse_args())
